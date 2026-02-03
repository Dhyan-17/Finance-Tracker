from datetime import datetime
from analytics import Analytics

class Wallet:
    """Core wallet operations"""

    def __init__(self, db, stack_queue):
        self.db = db
        self.stack_queue = stack_queue
        self.analytics = Analytics(db)

    def process_income(self, user_id, account_type, account_id, amount, category, source, username):
        """Process income addition to specified account type"""
        try:
            if account_type == "wallet":
                # Update wallet balance
                current_balance = float(self.db.get_user_balance(user_id))
                new_balance = current_balance + amount

                if self.db.update_user_balance(user_id, new_balance):
                    # Add transaction record
                    self.db.add_transaction(user_id, 'INCOME', amount, new_balance)

                    # Add income record
                    query = "INSERT INTO income (user_id, amount, category, source) VALUES (%s, %s, %s, %s)"
                    self.db.execute_insert(query, (user_id, amount, category, source))

                    # Update DSA structures
                    self.stack_queue.add_transaction_to_recent({
                        'type': 'INCOME',
                        'amount': amount,
                        'category': category,
                        'source': source,
                        'date': datetime.now()
                    })

                    # Update monthly summary
                    month_key = datetime.now().strftime("%Y-%m")
                    self.stack_queue.update_monthly_summary(month_key, income=amount)

                    # Log action
                    self.db.log_action(f"User: {username}", f"Added income: ₹{amount} to wallet")

                    return True, new_balance, "Income added to wallet successfully"

                return False, current_balance, "Failed to update wallet balance"

            elif account_type == "bank_account":
                # Update bank account balance
                current_balance = float(self.db.get_bank_account_balance(account_id))
                new_balance = current_balance + amount

                if self.db.update_bank_account_balance(account_id, new_balance):
                    # Add bank transaction record
                    self.db.add_bank_transaction(account_id, 'INCOME', amount, new_balance, category, source)

                    # Log action
                    self.db.log_action(f"User: {username}", f"Added income: ₹{amount} to bank account")

                    return True, new_balance, "Income added to bank account successfully"

                return False, current_balance, "Failed to update bank account balance"

            elif account_type == "investment_account":
                # Update investment account value
                current_value = float(self.db.get_investment_account_value(account_id))
                new_value = current_value + amount

                if self.db.update_investment_account_value(account_id, new_value):
                    # Add investment transaction record
                    self.db.add_investment_transaction(account_id, 'INCOME', amount, new_value, category, source)

                    # Log action
                    self.db.log_action(f"User: {username}", f"Added income: ₹{amount} to investment account")

                    return True, new_value, "Income added to investment account successfully"

                return False, current_value, "Failed to update investment account value"

            elif account_type == "manual_account":
                # Update manual account balance
                current_balance = float(self.db.get_manual_account_balance(account_id))
                new_balance = current_balance + amount

                update_result = self.db.update_manual_account_balance(account_id, new_balance)
                if update_result:
                    # Add manual account transaction record
                    self.db.add_manual_account_transaction(account_id, 'INCOME', amount, new_balance, category, source)

                    # Log action
                    self.db.log_action(f"User: {username}", f"Added income: ₹{amount} to manual account")

                    return True, new_balance, "Income added to manual account successfully"

                # Debug: Check if account exists
                check_query = "SELECT manual_account_id FROM manual_accounts WHERE manual_account_id = %s"
                account_exists = self.db.execute_query(check_query, (account_id,), fetch=True)
                if not account_exists:
                    return False, current_balance, f"Manual account with ID {account_id} does not exist"

                return False, current_balance, f"Failed to update manual account balance (account exists but update failed)"

            else:
                return False, 0, "Invalid account type"

        except Exception as e:
            return False, 0, str(e)

    def process_expense(self, user_id, account_type, account_id, amount, category, payment_mode, description, username, subtype=None):
        """Process expense deduction from specified account type"""
        try:
            if account_type == "wallet":
                # Check balance
                current_balance = float(self.db.get_user_balance(user_id))
                if amount > current_balance:
                    return False, current_balance, "Insufficient wallet balance"

                # Check budget
                current_month = datetime.now().strftime("%Y-%m")
                budget_data = self.stack_queue.get_budget_status(user_id, category, current_month)

                if budget_data['limit'] > 0:
                    new_spent = budget_data['spent'] + amount
                    if new_spent > budget_data['limit']:
                        return False, current_balance, "Budget limit exceeded"

                # Update balance
                new_balance = current_balance - amount

                if self.db.update_user_balance(user_id, new_balance):
                    # Add transaction record
                    self.db.add_transaction(user_id, 'EXPENSE', amount, new_balance)

                    # Add expense record with subtype support
                    query = """INSERT INTO expenses (user_id, amount, category, subtype, payment_mode, description)
                               VALUES (%s, %s, %s, %s, %s, %s)"""
                    self.db.execute_insert(query, (user_id, amount, category, subtype, payment_mode, description))

                    # Update DSA structures
                    expense_data = {
                        'type': 'EXPENSE',
                        'amount': amount,
                        'category': category,
                        'subtype': subtype,
                        'payment_mode': payment_mode,
                        'description': description,
                        'date': datetime.now()
                    }
                    self.stack_queue.add_transaction_to_recent(expense_data)
                    self.stack_queue.add_to_undo_stack(expense_data)

                    # Update category totals and monthly summary
                    self.stack_queue.update_category_total(category, amount)
                    month_key = datetime.now().strftime("%Y-%m")
                    self.stack_queue.update_monthly_summary(month_key, expense=amount)

                    # Update budget tracking
                    self.stack_queue.update_budget_spent(user_id, category, current_month, amount)

                    # Log action
                    self.db.log_action(f"User: {username}", f"Added expense: ₹{amount} ({category}) from wallet")

                    return True, new_balance, "Expense added from wallet successfully"

                return False, current_balance, "Failed to update wallet balance"

            elif account_type == "bank_account":
                # Check bank account balance
                current_balance = float(self.db.get_bank_account_balance(account_id))
                if amount > current_balance:
                    return False, current_balance, "Insufficient bank account balance"

                # Check credit card limit if using credit card
                if payment_mode == "Credit Card":
                    # Get credit card limit for this account
                    credit_limit_query = "SELECT credit_card_limit FROM bank_accounts WHERE account_id = %s"
                    credit_limit_result = self.db.execute_query(credit_limit_query, (account_id,), fetch=True)

                    if credit_limit_result and credit_limit_result[0]['credit_card_limit'] > 0:
                        credit_limit = float(credit_limit_result[0]['credit_card_limit'])

                        # Get current month's credit card spending
                        current_month = datetime.now().strftime("%Y-%m")
                        credit_spend_query = """
                            SELECT COALESCE(SUM(amount), 0) as monthly_spend
                            FROM bank_transactions
                            WHERE account_id = %s AND type = 'EXPENSE' AND category = 'Credit Card Payment'
                            AND DATE_FORMAT(date, '%%Y-%%m') = %s
                        """
                        spend_result = self.db.execute_query(credit_spend_query, (account_id, current_month), fetch=True)
                        monthly_spend = float(spend_result[0]['monthly_spend']) if spend_result else 0.0

                        remaining_limit = credit_limit - monthly_spend

                        if amount > remaining_limit:
                            return False, current_balance, f"Credit card limit exceeded. Remaining limit: ₹{remaining_limit:.2f}"

                        # Show remaining limit after transaction
                        new_remaining_limit = remaining_limit - amount
                        print("+-----------------------------------------------+")
                        print(f"| Credit Card Update:                           |")
                        print(f"| Amount Used: ₹{amount:<30.2f}|")
                        print(f"| Remaining Limit: ₹{new_remaining_limit:<26.2f}|")
                        print("+-----------------------------------------------+")

                # Update bank account balance
                new_balance = current_balance - amount

                if self.db.update_bank_account_balance(account_id, new_balance):
                    # Add bank transaction record
                    self.db.add_bank_transaction(account_id, 'EXPENSE', amount, new_balance, category, description)

                    # Log action
                    self.db.log_action(f"User: {username}", f"Added expense: ₹{amount} ({category}) from bank account")

                    return True, new_balance, "Expense added from bank account successfully"

                return False, current_balance, "Failed to update bank account balance"

            elif account_type == "investment_account":
                # Check investment account value
                current_value = float(self.db.get_investment_account_value(account_id))
                if amount > current_value:
                    return False, current_value, "Insufficient investment account value"

                # Update investment account value (redeem/withdraw)
                new_value = current_value - amount

                if self.db.update_investment_account_value(account_id, new_value):
                    # Add investment transaction record
                    self.db.add_investment_transaction(account_id, 'EXPENSE', amount, new_value, category, description)

                    # Log action
                    self.db.log_action(f"User: {username}", f"Redeemed/Withdrew: ₹{amount} from investment account")

                    return True, new_value, "Redemption/Withdrawal from investment account successful"

                return False, current_value, "Failed to update investment account value"

            elif account_type == "manual_account":
                # Check manual account balance
                manual_balance = float(self.db.get_manual_account_balance(account_id))
                if amount > manual_balance:
                    return False, manual_balance, "Insufficient manual account balance"

                # Update manual account balance
                new_manual_balance = manual_balance - amount

                if self.db.update_manual_account_balance(account_id, new_manual_balance):
                    # Add manual account transaction record
                    self.db.add_manual_account_transaction(account_id, 'EXPENSE', amount, new_manual_balance, category, description)

                    # Log action
                    self.db.log_action(f"User: {username}", f"Added expense: ₹{amount} ({category}) from manual account")

                    return True, new_manual_balance, "Expense added from manual account successfully"

                return False, manual_balance, "Failed to update manual account balance"

            else:
                return False, 0, "Invalid account type"

        except Exception as e:
            return False, 0, str(e)

    def process_transfer(self, sender_id, receiver_id, amount, sender_username, receiver_username):
        """Process money transfer between users"""
        try:
            # Check sender balance
            sender_balance = float(self.db.get_user_balance(sender_id))
            if amount > sender_balance:
                return False, "Insufficient balance"

            # Get receiver balance
            receiver_balance = float(self.db.get_user_balance(receiver_id))

            # Calculate new balances
            new_sender_balance = sender_balance - amount
            new_receiver_balance = receiver_balance + amount

            # Update sender balance
            if not self.db.update_user_balance(sender_id, new_sender_balance):
                return False, "Failed to update sender balance"

            # Update receiver balance
            if not self.db.update_user_balance(receiver_id, new_receiver_balance):
                # Rollback sender balance
                self.db.update_user_balance(sender_id, sender_balance)
                return False, "Failed to update receiver balance"

            # Add transaction records
            self.db.add_transaction(sender_id, 'TRANSFER', amount, new_sender_balance)
            self.db.add_transaction(receiver_id, 'TRANSFER', amount, new_receiver_balance)

            # Add transfer record
            query = """INSERT INTO transfers (sender_id, receiver_id, amount)
                       VALUES (%s, %s, %s)"""
            self.db.execute_insert(query, (sender_id, receiver_id, amount))

            # Update DSA structures for sender
            transfer_data = {
                'type': 'TRANSFER',
                'amount': amount,
                'receiver': receiver_username,
                'date': datetime.now()
            }
            self.stack_queue.add_transaction_to_recent(transfer_data)
            self.stack_queue.add_to_undo_stack(transfer_data)

            # Log actions
            self.db.log_action(f"User: {sender_username}",
                             f"Transferred ₹{amount} to {receiver_username}")

            return True, "Transfer successful"

        except Exception as e:
            return False, str(e)

    def get_transaction_history(self, user_id, limit=10):
        """Get recent transaction history"""
        try:
            query = """
                SELECT type, amount, balance_after, date
                FROM wallet_transactions
                WHERE user_id = %s
                ORDER BY date DESC LIMIT %s
            """
            results = self.db.execute_query(query, (user_id, limit), fetch=True)
            return results if results else []
        except Exception as e:
            return []

    def get_expense_history(self, user_id, limit=10):
        """Get expense history"""
        try:
            query = """
                SELECT amount, category, payment_mode, description, date
                FROM expenses
                WHERE user_id = %s
                ORDER BY date DESC LIMIT %s
            """
            results = self.db.execute_query(query, (user_id, limit), fetch=True)
            return results if results else []
        except Exception as e:
            return []

    def get_income_history(self, user_id, limit=10):
        """Get income history"""
        try:
            query = """
                SELECT amount, source, date
                FROM income
                WHERE user_id = %s
                ORDER BY date DESC LIMIT %s
            """
            results = self.db.execute_query(query, (user_id, limit), fetch=True)
            return results if results else []
        except Exception as e:
            return []

    def get_transfer_history(self, user_id, limit=10):
        """Get transfer history"""
        try:
            # Sent transfers
            sent_query = """
                SELECT 'SENT' as direction, t.amount, u.username as other_party, t.date
                FROM transfers t
                JOIN users u ON t.receiver_id = u.user_id
                WHERE t.sender_id = %s
                ORDER BY t.date DESC LIMIT %s
            """
            sent_results = self.db.execute_query(sent_query, (user_id, limit//2), fetch=True) or []

            # Received transfers
            received_query = """
                SELECT 'RECEIVED' as direction, t.amount, u.username as other_party, t.date
                FROM transfers t
                JOIN users u ON t.sender_id = u.user_id
                WHERE t.receiver_id = %s
                ORDER BY t.date DESC LIMIT %s
            """
            received_results = self.db.execute_query(received_query, (user_id, limit//2), fetch=True) or []

            # Combine and sort
            all_transfers = sent_results + received_results
            all_transfers.sort(key=lambda x: x['date'], reverse=True)
            return all_transfers[:limit]

        except Exception as e:
            return []

    def get_monthly_budget_status(self, user_id, month):
        """Get budget status for the month"""
        try:
            budgets = self.stack_queue.get_all_budgets(user_id, month)

            status_summary = []
            for category, data in budgets.items():
                spent = data['spent']
                limit = data['limit']
                percentage = (spent / limit * 100) if limit > 0 else 0

                if percentage > 100:
                    status = "❌ Over Budget"
                elif percentage > 80:
                    status = "⚠️ Near Limit"
                else:
                    status = "✅ On Track"

                status_summary.append({
                    'category': category,
                    'spent': spent,
                    'limit': limit,
                    'percentage': percentage,
                    'status': status
                })

            return status_summary

        except Exception as e:
            return []

    def calculate_financial_health_score(self, user_id):
        """Calculate financial health score (0-100)"""
        try:
            current_month = datetime.now().strftime("%Y-%m")
            summary = self.analytics.get_monthly_summary(user_id, current_month)

            if 'error' in summary:
                return 0

            score = 0

            # Savings rate (40% weight)
            savings_rate = summary.get('savings_rate', 0)
            if savings_rate >= 20:
                score += 40
            elif savings_rate >= 10:
                score += 25
            elif savings_rate >= 0:
                score += 10

            # Budget compliance (30% weight)
            budget_status = self.get_monthly_budget_status(user_id, datetime.now().year)
            if budget_status:
                on_track_count = sum(1 for b in budget_status if "On Track" in b['status'])
                compliance_rate = (on_track_count / len(budget_status)) * 100
                score += (compliance_rate * 0.3)

            # Transaction regularity (20% weight)
            total_transactions = summary.get('income_transactions', 0) + summary.get('expense_transactions', 0)
            if total_transactions >= 10:
                score += 20
            elif total_transactions >= 5:
                score += 12
            elif total_transactions >= 1:
                score += 5

            # Income stability (10% weight) - simplified
            if summary.get('total_income', 0) > 0:
                score += 10

            return min(100, max(0, int(score)))

        except Exception as e:
            return 0

    def undo_last_transaction(self, user_id, username):
        """Undo the last transaction"""
        try:
            last_txn = self.stack_queue.undo_last_transaction()

            if not last_txn:
                return False, "No transactions to undo"

            # -------- EXPENSE UNDO --------
            if last_txn["type"] == "EXPENSE":
                current_balance = float(self.db.get_user_balance(user_id))
                new_balance = current_balance + last_txn["amount"]

                if self.db.update_user_balance(user_id, new_balance):
                    self.db.log_action(f"User:{username}", f"Undo EXPENSE ₹{last_txn['amount']}")
                    return True, f"Expense undone successfully! Restored Balance: ₹{new_balance:.2f}"

            # -------- INCOME UNDO --------
            elif last_txn["type"] == "INCOME":
                current_balance = float(self.db.get_user_balance(user_id))
                new_balance = current_balance - last_txn["amount"]

                if new_balance < 0:
                    return False, "Cannot undo income (negative balance)"

                if self.db.update_user_balance(user_id, new_balance):
                    self.db.log_action(f"User:{username}", f"Undo INCOME ₹{last_txn['amount']}")
                    return True, f"Income undone successfully! Updated Balance: ₹{new_balance:.2f}"

            # -------- TRANSFER UNDO --------
            elif last_txn["type"] == "TRANSFER":
                # NOTE: Transfer record not deleted, only balance rollback
                sender_id = last_txn["sender_id"]
                receiver_id = last_txn["receiver_id"]
                amount = last_txn["amount"]

                receiver_balance = float(self.db.get_user_balance(receiver_id))
                if receiver_balance < amount:
                    return False, "Cannot undo transfer (receiver spent money)"

                # Rollback balances
                self.db.update_user_balance(sender_id, float(self.db.get_user_balance(sender_id)) + amount)
                self.db.update_user_balance(receiver_id, receiver_balance - amount)

                self.db.log_action(f"User:{username}", f"Undo TRANSFER ₹{amount}")
                return True, "Transfer undone successfully!"

            else:
                return False, "Unknown transaction type"

        except Exception as e:
            return False, str(e)

    def check_budget_alert(self, user_id, category, month):
        """Check if budget limit is approaching (80%)"""
        budget_data = self.stack_queue.get_budget_status(user_id, category, month)
        if budget_data['limit'] > 0:
            spent_percentage = (budget_data['spent'] / budget_data['limit']) * 100
            return spent_percentage >= 80, spent_percentage
        return False, 0

    def get_wallet_insights(self, user_id):
        """Get wallet insights and recommendations"""
        try:
            current_month = datetime.now().strftime("%Y-%m")
            summary = self.analytics.get_monthly_summary(user_id, current_month)
            categories = self.analytics.get_category_breakdown(user_id, current_month)
            health_score = self.calculate_financial_health_score(user_id)

            insights = {
                'health_score': health_score,
                'recommendations': []
            }

            # Generate recommendations based on data
            if summary.get('savings_rate', 0) < 10:
                insights['recommendations'].append("💡 Consider reducing discretionary spending to improve savings.")

            if categories and len(categories) > 0:
                top_category = categories[0]['category']
                if categories[0]['percentage'] > 50:
                    insights['recommendations'].append(f"⚠️ {top_category} expenses are {categories[0]['percentage']:.1f}% of total spending. Consider optimizing.")

            budget_status = self.get_monthly_budget_status(user_id, datetime.now().year)
            over_budget = [b for b in budget_status if "Over Budget" in b['status']]
            if over_budget:
                insights['recommendations'].append(f"❌ You're over budget in {len(over_budget)} categories. Review spending.")

            if health_score < 50:
                insights['recommendations'].append("📊 Your financial health score is low. Focus on increasing savings and managing expenses.")

            return insights

        except Exception as e:
            return {'health_score': 0, 'recommendations': ["Unable to generate insights"]}
