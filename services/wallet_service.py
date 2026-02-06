"""
Wallet Service
Transaction-safe financial operations with atomic updates
"""

from typing import Tuple, Dict, Optional, List
from datetime import datetime
from database.db import db


class WalletService:
    """Transaction-safe wallet operations"""
    
    # ============================================================
    # ATOMIC INCOME OPERATIONS
    # ============================================================
    
    def add_income(
        self,
        user_id: int,
        amount: float,
        source: str,
        category: str = None,
        account_type: str = 'WALLET',
        account_id: int = None,
        description: str = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Add income with atomic balance update and transaction logging.
        Amount is in rupees, stored in paise.
        """
        if amount <= 0:
            return False, "Amount must be positive", None
        
        amount_paise = db.to_paise(amount)
        
        try:
            with db.transaction() as conn:
                cursor = conn.cursor()
                
                if account_type == 'WALLET':
                    # Get current balance
                    cursor.execute(
                        "SELECT wallet_balance FROM users WHERE user_id = ?",
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    if not result:
                        return False, "User not found", None
                    
                    current_balance = result[0]
                    new_balance = current_balance + amount_paise
                    
                    # Update balance
                    cursor.execute(
                        "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
                        (new_balance, user_id)
                    )
                    
                    # Add wallet transaction
                    cursor.execute(
                        """INSERT INTO wallet_transactions 
                           (user_id, txn_type, amount, balance_after, reference_type, description)
                           VALUES (?, 'INCOME', ?, ?, 'income', ?)""",
                        (user_id, amount_paise, new_balance, description or source)
                    )
                    
                elif account_type == 'BANK':
                    if not account_id:
                        return False, "Bank account ID required", None
                    
                    # Verify ownership and get balance
                    cursor.execute(
                        "SELECT balance FROM bank_accounts WHERE account_id = ? AND user_id = ?",
                        (account_id, user_id)
                    )
                    result = cursor.fetchone()
                    if not result:
                        return False, "Bank account not found", None
                    
                    current_balance = result[0]
                    new_balance = current_balance + amount_paise
                    
                    # Update balance
                    cursor.execute(
                        "UPDATE bank_accounts SET balance = ? WHERE account_id = ?",
                        (new_balance, account_id)
                    )
                    
                    # Add bank transaction
                    cursor.execute(
                        """INSERT INTO bank_transactions 
                           (account_id, user_id, txn_type, amount, balance_after, category, description)
                           VALUES (?, ?, 'INCOME', ?, ?, ?, ?)""",
                        (account_id, user_id, amount_paise, new_balance, category, description)
                    )
                else:
                    return False, "Invalid account type", None
                
                # Add income record
                cursor.execute(
                    """INSERT INTO income 
                       (user_id, amount, source, category, description, account_type, account_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, amount_paise, source, category, description, account_type, account_id)
                )
                
                income_id = cursor.lastrowid
                
                # Log action
                db.log_action(
                    'USER', user_id,
                    f"Added income: ₹{amount:.2f} from {source}",
                    'income', income_id
                )
                
                return True, "Income added successfully", {
                    'income_id': income_id,
                    'amount': amount,
                    'new_balance': db.to_rupees(new_balance)
                }
                
        except Exception as e:
            return False, f"Failed to add income: {str(e)}", None
    
    # ============================================================
    # ATOMIC EXPENSE OPERATIONS
    # ============================================================
    
    def add_expense(
        self,
        user_id: int,
        amount: float,
        category: str,
        payment_mode: str = 'UPI',
        account_type: str = 'WALLET',
        account_id: int = None,
        description: str = None,
        subcategory: str = None,
        merchant: str = None,
        check_budget: bool = True
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Add expense with atomic balance update, budget checking, and fraud detection.
        Amount is in rupees, stored in paise.
        """
        if amount <= 0:
            return False, "Amount must be positive", None
        
        amount_paise = db.to_paise(amount)
        
        try:
            with db.transaction() as conn:
                cursor = conn.cursor()
                
                if account_type == 'WALLET':
                    # Get current balance
                    cursor.execute(
                        "SELECT wallet_balance FROM users WHERE user_id = ?",
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    if not result:
                        return False, "User not found", None
                    
                    current_balance = result[0]
                    
                    # Check sufficient balance
                    if amount_paise > current_balance:
                        return False, f"Insufficient balance. Available: ₹{db.to_rupees(current_balance):.2f}", None
                    
                    new_balance = current_balance - amount_paise
                    
                    # Update balance
                    cursor.execute(
                        "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
                        (new_balance, user_id)
                    )
                    
                    # Add wallet transaction
                    cursor.execute(
                        """INSERT INTO wallet_transactions 
                           (user_id, txn_type, amount, balance_after, reference_type, description)
                           VALUES (?, 'EXPENSE', ?, ?, 'expense', ?)""",
                        (user_id, amount_paise, new_balance, description or category)
                    )
                    
                elif account_type == 'BANK':
                    if not account_id:
                        return False, "Bank account ID required", None
                    
                    # Verify ownership and get balance
                    cursor.execute(
                        "SELECT balance FROM bank_accounts WHERE account_id = ? AND user_id = ?",
                        (account_id, user_id)
                    )
                    result = cursor.fetchone()
                    if not result:
                        return False, "Bank account not found", None
                    
                    current_balance = result[0]
                    
                    # Check sufficient balance
                    if amount_paise > current_balance:
                        return False, f"Insufficient balance. Available: ₹{db.to_rupees(current_balance):.2f}", None
                    
                    new_balance = current_balance - amount_paise
                    
                    # Update balance
                    cursor.execute(
                        "UPDATE bank_accounts SET balance = ? WHERE account_id = ?",
                        (new_balance, account_id)
                    )
                    
                    # Add bank transaction
                    cursor.execute(
                        """INSERT INTO bank_transactions 
                           (account_id, user_id, txn_type, amount, balance_after, category, description)
                           VALUES (?, ?, 'EXPENSE', ?, ?, ?, ?)""",
                        (account_id, user_id, amount_paise, new_balance, category, description)
                    )
                else:
                    return False, "Invalid account type", None
                
                # Add expense record
                cursor.execute(
                    """INSERT INTO expenses 
                       (user_id, amount, category, subcategory, description, 
                        payment_mode, account_type, account_id, merchant)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, amount_paise, category, subcategory, description,
                     payment_mode, account_type, account_id, merchant)
                )
                
                expense_id = cursor.lastrowid
            
            # After transaction: check budget and fraud (non-blocking)
            budget_warning = None
            if check_budget:
                budget_warning = self._check_budget_status(user_id, category, amount_paise)
            
            # Fraud detection
            self._check_fraud_rules(user_id, amount_paise, expense_id)
            
            # Log action
            db.log_action(
                'USER', user_id,
                f"Added expense: ₹{amount:.2f} for {category}",
                'expense', expense_id
            )
            
            result = {
                'expense_id': expense_id,
                'amount': amount,
                'new_balance': db.to_rupees(new_balance),
                'category': category
            }
            
            if budget_warning:
                result['budget_warning'] = budget_warning
            
            return True, "Expense added successfully", result
            
        except Exception as e:
            return False, f"Failed to add expense: {str(e)}", None
    
    def _check_budget_status(self, user_id: int, category: str, amount_paise: int) -> Optional[str]:
        """Check if expense affects budget and return warning if needed"""
        now = datetime.now()
        budget = db.execute_one(
            "SELECT * FROM budgets WHERE user_id = ? AND category = ? AND year = ? AND month = ?",
            (user_id, category, now.year, now.month)
        )
        
        if not budget:
            return None
        
        # Get current spending
        spent = db.get_budget_spending(user_id, category, now.year, now.month)
        total_spent = spent + amount_paise
        limit = budget['limit_amount']
        
        percentage = (total_spent / limit) * 100 if limit > 0 else 0
        
        if percentage >= 100:
            # Over budget - add notification
            db.add_notification(
                user_id,
                f"Budget Exceeded: {category}",
                f"You've exceeded your {category} budget. Spent: ₹{db.to_rupees(total_spent):.2f} / Limit: ₹{db.to_rupees(limit):.2f}",
                "WARNING",
                "budget"
            )
            return f"Over budget! ({percentage:.1f}%)"
        elif percentage >= budget['alert_threshold']:
            # Approaching limit
            db.add_notification(
                user_id,
                f"Budget Alert: {category}",
                f"You've used {percentage:.1f}% of your {category} budget.",
                "INFO",
                "budget"
            )
            return f"Approaching limit ({percentage:.1f}%)"
        
        return None
    
    def _check_fraud_rules(self, user_id: int, amount_paise: int, expense_id: int):
        """Check fraud detection rules"""
        rules = db.get_fraud_rules(active_only=True)
        
        for rule in rules:
            if rule['rule_type'] == 'AMOUNT' and rule['threshold_type'] == 'ABSOLUTE':
                # Large transaction check
                if amount_paise >= db.to_paise(rule['threshold_value']):
                    db.add_fraud_flag(
                        user_id,
                        rule['rule_name'],
                        rule['severity'],
                        f"Transaction of ₹{db.to_rupees(amount_paise):.2f} exceeds threshold",
                        'expense', expense_id, amount_paise
                    )
            
            elif rule['rule_type'] == 'AMOUNT' and rule['threshold_type'] == 'MULTIPLIER':
                # Unusual spending check - compare to user average
                avg_result = db.execute_one(
                    "SELECT AVG(amount) as avg_amount FROM expenses WHERE user_id = ?",
                    (user_id,)
                )
                if avg_result and avg_result['avg_amount']:
                    avg = avg_result['avg_amount']
                    if amount_paise > avg * rule['threshold_value']:
                        db.add_fraud_flag(
                            user_id,
                            rule['rule_name'],
                            rule['severity'],
                            f"Transaction is {amount_paise/avg:.1f}x above average",
                            'expense', expense_id, amount_paise
                        )
    
    # ============================================================
    # TRANSFER OPERATIONS
    # ============================================================
    
    def transfer_funds(
        self,
        sender_id: int,
        receiver_identifier: str,
        amount: float,
        note: str = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Transfer funds between users with atomic operation.
        receiver_identifier can be username, email, or mobile.
        """
        if amount <= 0:
            return False, "Amount must be positive", None
        
        amount_paise = db.to_paise(amount)
        
        # Find receiver
        receiver = (
            db.get_user_by_email(receiver_identifier) or
            db.get_user_by_mobile(receiver_identifier) or
            db.get_user_by_username(receiver_identifier)
        )
        
        if not receiver:
            return False, "Recipient not found", None
        
        if receiver['user_id'] == sender_id:
            return False, "Cannot transfer to yourself", None
        
        if receiver['status'] != 'ACTIVE':
            return False, "Recipient account is not active", None
        
        try:
            with db.transaction() as conn:
                cursor = conn.cursor()
                
                # Get sender balance
                cursor.execute(
                    "SELECT wallet_balance FROM users WHERE user_id = ?",
                    (sender_id,)
                )
                sender_result = cursor.fetchone()
                if not sender_result:
                    return False, "Sender not found", None
                
                sender_balance = sender_result[0]
                
                # Check sufficient balance
                if amount_paise > sender_balance:
                    return False, f"Insufficient balance. Available: ₹{db.to_rupees(sender_balance):.2f}", None
                
                # Get receiver balance
                cursor.execute(
                    "SELECT wallet_balance FROM users WHERE user_id = ?",
                    (receiver['user_id'],)
                )
                receiver_result = cursor.fetchone()
                receiver_balance = receiver_result[0]
                
                # Update balances
                new_sender_balance = sender_balance - amount_paise
                new_receiver_balance = receiver_balance + amount_paise
                
                cursor.execute(
                    "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
                    (new_sender_balance, sender_id)
                )
                cursor.execute(
                    "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
                    (new_receiver_balance, receiver['user_id'])
                )
                
                # Create transfer record
                cursor.execute(
                    "INSERT INTO transfers (sender_id, receiver_id, amount, note) VALUES (?, ?, ?, ?)",
                    (sender_id, receiver['user_id'], amount_paise, note)
                )
                transfer_id = cursor.lastrowid
                
                # Add wallet transactions for both parties
                cursor.execute(
                    """INSERT INTO wallet_transactions 
                       (user_id, txn_type, amount, balance_after, reference_type, reference_id, description)
                       VALUES (?, 'TRANSFER_OUT', ?, ?, 'transfer', ?, ?)""",
                    (sender_id, amount_paise, new_sender_balance, transfer_id, f"To {receiver['username']}")
                )
                cursor.execute(
                    """INSERT INTO wallet_transactions 
                       (user_id, txn_type, amount, balance_after, reference_type, reference_id, description)
                       VALUES (?, 'TRANSFER_IN', ?, ?, 'transfer', ?, ?)""",
                    (receiver['user_id'], amount_paise, new_receiver_balance, transfer_id, f"From sender")
                )
            
            # Notify receiver
            db.add_notification(
                receiver['user_id'],
                "Money Received",
                f"You received ₹{amount:.2f}" + (f" - {note}" if note else ""),
                "SUCCESS",
                "transfer"
            )
            
            # Log action
            db.log_action(
                'USER', sender_id,
                f"Transferred ₹{amount:.2f} to {receiver['username']}",
                'transfer', transfer_id
            )
            
            return True, "Transfer successful", {
                'transfer_id': transfer_id,
                'amount': amount,
                'receiver': receiver['username'],
                'new_balance': db.to_rupees(new_sender_balance)
            }
            
        except Exception as e:
            return False, f"Transfer failed: {str(e)}", None
    
    # ============================================================
    # BALANCE & SUMMARY OPERATIONS
    # ============================================================
    
    def get_total_balance(self, user_id: int) -> Dict:
        """Get complete balance summary for user"""
        wallet = db.get_user_balance(user_id)
        bank = db.get_total_bank_balance(user_id)
        investment = db.get_total_investment_value(user_id)
        
        return {
            'wallet': db.to_rupees(wallet),
            'bank': db.to_rupees(bank),
            'investments_invested': db.to_rupees(investment['total_invested']),
            'investments_current': db.to_rupees(investment['current_value']),
            'investments_pl': db.to_rupees(investment['current_value'] - investment['total_invested']),
            'net_worth': db.to_rupees(wallet + bank + investment['current_value'])
        }
    
    def get_monthly_summary(self, user_id: int, year: int = None, month: int = None) -> Dict:
        """Get monthly financial summary"""
        if not year or not month:
            now = datetime.now()
            year = now.year
            month = now.month
        
        month_str = f"{year}-{month:02d}"
        
        # Income
        income_result = db.execute_one(
            """SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count
               FROM income WHERE user_id = ? AND strftime('%Y-%m', date) = ?""",
            (user_id, month_str)
        )
        
        # Expenses
        expense_result = db.execute_one(
            """SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count
               FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?""",
            (user_id, month_str)
        )
        
        total_income = income_result['total'] if income_result else 0
        total_expense = expense_result['total'] if expense_result else 0
        net_savings = total_income - total_expense
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
        
        return {
            'year': year,
            'month': month,
            'total_income': db.to_rupees(total_income),
            'total_expense': db.to_rupees(total_expense),
            'net_savings': db.to_rupees(net_savings),
            'savings_rate': savings_rate,
            'income_count': income_result['count'] if income_result else 0,
            'expense_count': expense_result['count'] if expense_result else 0
        }
    
    def get_category_breakdown(self, user_id: int, year: int = None, month: int = None) -> List[Dict]:
        """Get expense breakdown by category"""
        if not year or not month:
            now = datetime.now()
            year = now.year
            month = now.month
        
        month_str = f"{year}-{month:02d}"
        
        categories = db.execute(
            """SELECT category, 
                      SUM(amount) as total,
                      COUNT(*) as count,
                      AVG(amount) as avg_amount
               FROM expenses 
               WHERE user_id = ? AND strftime('%Y-%m', date) = ?
               GROUP BY category
               ORDER BY total DESC""",
            (user_id, month_str),
            fetch=True
        )
        
        # Calculate percentages
        total = sum(c['total'] for c in categories) if categories else 0
        
        result = []
        for cat in categories:
            result.append({
                'category': cat['category'],
                'total': db.to_rupees(cat['total']),
                'count': cat['count'],
                'avg_amount': db.to_rupees(cat['avg_amount']),
                'percentage': (cat['total'] / total * 100) if total > 0 else 0
            })
        
        return result
    
    def get_spending_trend(self, user_id: int, months: int = 6) -> List[Dict]:
        """Get spending trend over last N months"""
        trend = db.execute(
            """SELECT strftime('%Y-%m', date) as month,
                      SUM(amount) as total
               FROM expenses
               WHERE user_id = ? 
               AND date >= date('now', ? || ' months')
               GROUP BY month
               ORDER BY month""",
            (user_id, f"-{months}"),
            fetch=True
        )
        
        return [
            {'month': t['month'], 'total': db.to_rupees(t['total'])}
            for t in trend
        ]
    
    def get_income_trend(self, user_id: int, months: int = 6) -> List[Dict]:
        """Get income trend over last N months"""
        trend = db.execute(
            """SELECT strftime('%Y-%m', date) as month,
                      SUM(amount) as total
               FROM income
               WHERE user_id = ? 
               AND date >= date('now', ? || ' months')
               GROUP BY month
               ORDER BY month""",
            (user_id, f"-{months}"),
            fetch=True
        )
        
        return [
            {'month': t['month'], 'total': db.to_rupees(t['total'])}
            for t in trend
        ]


# Singleton instance
wallet_service = WalletService()
