"""
Wallet Service
Transaction-safe financial operations with atomic updates
"""

from typing import Tuple, Dict, Optional, List
from datetime import datetime
from database.db import db
from utils import Stack

# Module-level stack for tracking recent income operations
_recent_income_stack = Stack(max_size=20)


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
                
                # Track income using Stack (DSA)
                _recent_income_stack.push({
                    'income_id': income_id,
                    'user_id': user_id,
                    'amount': amount,
                    'timestamp': datetime.now().isoformat()
                })
                
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
        Add expense with atomic balance update and budget checking.
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
            
            # After transaction: check budget (non-blocking)
            budget_warning = None
            if check_budget:
                budget_warning = self._check_budget_status(user_id, category, amount_paise)
            
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
    
    # ============================================================
    # BALANCE & SUMMARY OPERATIONS
    # ============================================================
    
    def get_total_balance(self, user_id: int) -> Dict:
        """Get complete balance summary for user"""
        wallet = db.get_user_balance(user_id)
        investment = db.get_total_investment_value(user_id)
        
        return {
            'wallet': db.to_rupees(wallet),
            'investments_invested': db.to_rupees(investment['total_invested']),
            'investments_current': db.to_rupees(investment['current_value']),
            'investments_pl': db.to_rupees(investment['current_value'] - investment['total_invested']),
            'net_worth': db.to_rupees(wallet + investment['current_value'])
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
