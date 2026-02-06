"""
Analytics Service
Comprehensive analytics for users and admin dashboard
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database.db import db


class AnalyticsService:
    """Analytics and reporting service"""
    
    # ============================================================
    # USER ANALYTICS
    # ============================================================
    
    def get_user_dashboard_data(self, user_id: int) -> Dict:
        """Get comprehensive dashboard data for a user"""
        now = datetime.now()
        
        # Balance summary
        user = db.get_user_by_id(user_id)
        wallet_balance = db.to_rupees(user['wallet_balance']) if user else 0
        bank_balance = db.to_rupees(db.get_total_bank_balance(user_id))
        investment_data = db.get_total_investment_value(user_id)
        
        # Monthly summary
        month_str = now.strftime('%Y-%m')
        income_result = db.execute_one(
            """SELECT COALESCE(SUM(amount), 0) as total
               FROM income WHERE user_id = ? AND strftime('%Y-%m', date) = ?""",
            (user_id, month_str)
        )
        expense_result = db.execute_one(
            """SELECT COALESCE(SUM(amount), 0) as total
               FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?""",
            (user_id, month_str)
        )
        
        monthly_income = db.to_rupees(income_result['total']) if income_result else 0
        monthly_expense = db.to_rupees(expense_result['total']) if expense_result else 0
        
        # Recent transactions
        recent_expenses = db.get_user_expenses(user_id, limit=5)
        recent_income = db.get_user_income(user_id, limit=5)
        
        # Budget status
        budgets = self.get_budget_status(user_id, now.year, now.month)
        
        # Notifications count
        notifications = db.get_user_notifications(user_id, unread_only=True)
        
        return {
            'balance': {
                'wallet': wallet_balance,
                'bank': bank_balance,
                'investments': db.to_rupees(investment_data['current_value']),
                'investment_pl': db.to_rupees(investment_data['current_value'] - investment_data['total_invested']),
                'net_worth': wallet_balance + bank_balance + db.to_rupees(investment_data['current_value'])
            },
            'monthly': {
                'income': monthly_income,
                'expense': monthly_expense,
                'savings': monthly_income - monthly_expense,
                'savings_rate': ((monthly_income - monthly_expense) / monthly_income * 100) if monthly_income > 0 else 0
            },
            'recent_expenses': [
                {
                    'category': e['category'],
                    'amount': db.to_rupees(e['amount']),
                    'date': e['date'],
                    'description': e['description']
                } for e in recent_expenses
            ],
            'recent_income': [
                {
                    'source': i['source'],
                    'amount': db.to_rupees(i['amount']),
                    'date': i['date']
                } for i in recent_income
            ],
            'budgets': budgets,
            'unread_notifications': len(notifications)
        }
    
    def get_budget_status(self, user_id: int, year: int, month: int) -> List[Dict]:
        """Get budget status for all categories"""
        budgets = db.get_user_budgets(user_id, year, month)
        
        result = []
        for budget in budgets:
            spent = db.get_budget_spending(user_id, budget['category'], year, month)
            limit = budget['limit_amount']
            percentage = (spent / limit * 100) if limit > 0 else 0
            
            if percentage >= 100:
                status = 'EXCEEDED'
            elif percentage >= budget['alert_threshold']:
                status = 'WARNING'
            else:
                status = 'ON_TRACK'
            
            result.append({
                'category': budget['category'],
                'limit': db.to_rupees(limit),
                'spent': db.to_rupees(spent),
                'remaining': db.to_rupees(max(0, limit - spent)),
                'percentage': percentage,
                'status': status
            })
        
        return result
    
    def get_spending_by_category(self, user_id: int, months: int = 1) -> List[Dict]:
        """Get spending breakdown by category"""
        start_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')
        
        categories = db.execute(
            """SELECT category, 
                      SUM(amount) as total,
                      COUNT(*) as count
               FROM expenses
               WHERE user_id = ? AND date >= ?
               GROUP BY category
               ORDER BY total DESC""",
            (user_id, start_date),
            fetch=True
        )
        
        total = sum(c['total'] for c in categories) if categories else 0
        
        return [{
            'category': c['category'],
            'total': db.to_rupees(c['total']),
            'count': c['count'],
            'percentage': (c['total'] / total * 100) if total > 0 else 0
        } for c in categories]
    
    def get_income_vs_expense_trend(self, user_id: int, months: int = 12) -> List[Dict]:
        """Get income vs expense comparison over time"""
        trend = []
        now = datetime.now()
        
        for i in range(months - 1, -1, -1):
            date = now - timedelta(days=i * 30)
            month_str = date.strftime('%Y-%m')
            
            income = db.execute_one(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM income WHERE user_id = ? AND strftime('%Y-%m', date) = ?""",
                (user_id, month_str)
            )
            expense = db.execute_one(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?""",
                (user_id, month_str)
            )
            
            trend.append({
                'month': month_str,
                'income': db.to_rupees(income['total']) if income else 0,
                'expense': db.to_rupees(expense['total']) if expense else 0
            })
        
        return trend
    
    def get_daily_spending(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get daily spending for the last N days"""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        daily = db.execute(
            """SELECT date(date) as day, SUM(amount) as total
               FROM expenses
               WHERE user_id = ? AND date >= ?
               GROUP BY day
               ORDER BY day""",
            (user_id, start_date),
            fetch=True
        )
        
        return [{
            'date': d['day'],
            'amount': db.to_rupees(d['total'])
        } for d in daily]
    
    def get_top_expenses(self, user_id: int, year: int, month: int, limit: int = 10) -> List[Dict]:
        """Get top individual expenses"""
        month_str = f"{year}-{month:02d}"
        
        expenses = db.execute(
            """SELECT expense_id, amount, category, subcategory, description, date
               FROM expenses
               WHERE user_id = ? AND strftime('%Y-%m', date) = ?
               ORDER BY amount DESC
               LIMIT ?""",
            (user_id, month_str, limit),
            fetch=True
        )
        
        return [{
            'expense_id': e['expense_id'],
            'amount': db.to_rupees(e['amount']),
            'category': e['category'],
            'subcategory': e['subcategory'],
            'description': e['description'],
            'date': e['date']
        } for e in expenses]
    
    def calculate_financial_health_score(self, user_id: int) -> Dict:
        """Calculate financial health score (0-100)"""
        now = datetime.now()
        month_str = now.strftime('%Y-%m')
        
        score = 0
        breakdown = {}
        
        # 1. Savings Rate (30 points)
        income = db.execute_one(
            """SELECT COALESCE(SUM(amount), 0) as total
               FROM income WHERE user_id = ? AND strftime('%Y-%m', date) = ?""",
            (user_id, month_str)
        )
        expense = db.execute_one(
            """SELECT COALESCE(SUM(amount), 0) as total
               FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?""",
            (user_id, month_str)
        )
        
        total_income = income['total'] if income else 0
        total_expense = expense['total'] if expense else 0
        savings_rate = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0
        
        if savings_rate >= 30:
            savings_score = 30
        elif savings_rate >= 20:
            savings_score = 25
        elif savings_rate >= 10:
            savings_score = 15
        elif savings_rate >= 0:
            savings_score = 10
        else:
            savings_score = 0
        
        score += savings_score
        breakdown['savings_rate'] = {'value': savings_rate, 'score': savings_score, 'max': 30}
        
        # 2. Budget Compliance (25 points)
        budgets = self.get_budget_status(user_id, now.year, now.month)
        if budgets:
            on_track = sum(1 for b in budgets if b['status'] == 'ON_TRACK')
            compliance = (on_track / len(budgets)) * 25
        else:
            compliance = 25  # No budgets = neutral
        
        score += compliance
        breakdown['budget_compliance'] = {'value': compliance / 25 * 100, 'score': compliance, 'max': 25}
        
        # 3. Emergency Fund (20 points)
        user = db.get_user_by_id(user_id)
        wallet = user['wallet_balance'] if user else 0
        bank = db.get_total_bank_balance(user_id)
        liquid_assets = wallet + bank
        
        # Check if user has 3 months of expenses saved
        avg_monthly_expense = db.execute_one(
            """SELECT AVG(monthly_total) as avg FROM (
                   SELECT strftime('%Y-%m', date) as month, SUM(amount) as monthly_total
                   FROM expenses WHERE user_id = ?
                   GROUP BY month
               )""",
            (user_id,)
        )
        
        target_emergency = (avg_monthly_expense['avg'] or 0) * 3
        emergency_ratio = (liquid_assets / target_emergency) if target_emergency > 0 else 1
        emergency_score = min(20, int(emergency_ratio * 20))
        
        score += emergency_score
        breakdown['emergency_fund'] = {'value': emergency_ratio * 100, 'score': emergency_score, 'max': 20}
        
        # 4. Investment Diversification (15 points)
        investments = db.get_user_investments(user_id)
        if investments:
            asset_types = set(i['asset_type'] for i in investments)
            diversity_score = min(15, len(asset_types) * 5)
        else:
            diversity_score = 0
        
        score += diversity_score
        breakdown['investment_diversity'] = {'value': len(set(i['asset_type'] for i in investments) if investments else []), 'score': diversity_score, 'max': 15}
        
        # 5. Transaction Activity (10 points)
        recent_count = db.execute_one(
            """SELECT COUNT(*) as count FROM (
                   SELECT 1 FROM expenses WHERE user_id = ? AND date >= date('now', '-30 days')
                   UNION ALL
                   SELECT 1 FROM income WHERE user_id = ? AND date >= date('now', '-30 days')
               )""",
            (user_id, user_id)
        )
        
        activity_count = recent_count['count'] if recent_count else 0
        if activity_count >= 20:
            activity_score = 10
        elif activity_count >= 10:
            activity_score = 7
        elif activity_count >= 5:
            activity_score = 5
        else:
            activity_score = 2
        
        score += activity_score
        breakdown['activity'] = {'value': activity_count, 'score': activity_score, 'max': 10}
        
        # Overall rating
        if score >= 80:
            rating = 'Excellent'
        elif score >= 60:
            rating = 'Good'
        elif score >= 40:
            rating = 'Fair'
        else:
            rating = 'Needs Improvement'
        
        return {
            'score': round(score),
            'rating': rating,
            'breakdown': breakdown
        }
    
    # ============================================================
    # ADMIN ANALYTICS
    # ============================================================
    
    def get_platform_summary(self) -> Dict:
        """Get platform-wide statistics"""
        # User stats
        user_stats = db.execute_one(
            """SELECT 
                   COUNT(*) as total_users,
                   SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_users,
                   SUM(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END) as blocked_users,
                   SUM(CASE WHEN datetime(created_at) >= datetime('now', '-7 days') THEN 1 ELSE 0 END) as new_7d,
                   SUM(CASE WHEN datetime(created_at) >= datetime('now', '-30 days') THEN 1 ELSE 0 END) as new_30d
               FROM users"""
        )
        
        # Financial stats
        wallet_total = db.execute_one(
            "SELECT COALESCE(SUM(wallet_balance), 0) as total FROM users"
        )
        bank_total = db.execute_one(
            "SELECT COALESCE(SUM(balance), 0) as total FROM bank_accounts"
        )
        expense_stats = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count FROM expenses"
        )
        income_stats = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count FROM income"
        )
        
        # Investment stats
        investment_stats = db.execute_one(
            """SELECT 
                   COALESCE(SUM(invested_amount), 0) as total_invested,
                   COUNT(DISTINCT user_id) as investors
               FROM user_investments"""
        )
        investment_value = db.execute_one(
            """SELECT COALESCE(SUM(ui.units_owned * ma.current_price), 0) as current_value
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id"""
        )
        
        return {
            'users': {
                'total': user_stats['total_users'] or 0,
                'active': user_stats['active_users'] or 0,
                'blocked': user_stats['blocked_users'] or 0,
                'new_7d': user_stats['new_7d'] or 0,
                'new_30d': user_stats['new_30d'] or 0
            },
            'finances': {
                'wallet_total': db.to_rupees(wallet_total['total']) if wallet_total else 0,
                'bank_total': db.to_rupees(bank_total['total']) if bank_total else 0,
                'total_expenses': db.to_rupees(expense_stats['total']) if expense_stats else 0,
                'expense_count': expense_stats['count'] if expense_stats else 0,
                'total_income': db.to_rupees(income_stats['total']) if income_stats else 0,
                'income_count': income_stats['count'] if income_stats else 0
            },
            'investments': {
                'total_invested': db.to_rupees(investment_stats['total_invested']) if investment_stats else 0,
                'current_value': db.to_rupees(investment_value['current_value']) if investment_value else 0,
                'investors': investment_stats['investors'] if investment_stats else 0
            }
        }
    
    def get_top_spending_categories(self, limit: int = 10) -> List[Dict]:
        """Get top spending categories platform-wide"""
        categories = db.execute(
            """SELECT category,
                      SUM(amount) as total,
                      COUNT(*) as count,
                      COUNT(DISTINCT user_id) as users
               FROM expenses
               GROUP BY category
               ORDER BY total DESC
               LIMIT ?""",
            (limit,),
            fetch=True
        )
        
        total = sum(c['total'] for c in categories) if categories else 0
        
        return [{
            'category': c['category'],
            'total': db.to_rupees(c['total']),
            'count': c['count'],
            'users': c['users'],
            'percentage': (c['total'] / total * 100) if total > 0 else 0
        } for c in categories]
    
    def get_monthly_platform_growth(self, months: int = 12) -> List[Dict]:
        """Get platform growth metrics over time"""
        growth = []
        now = datetime.now()
        
        for i in range(months - 1, -1, -1):
            date = now - timedelta(days=i * 30)
            month_str = date.strftime('%Y-%m')
            
            new_users = db.execute_one(
                """SELECT COUNT(*) as count FROM users
                   WHERE strftime('%Y-%m', created_at) = ?""",
                (month_str,)
            )
            
            volume = db.execute_one(
                """SELECT COALESCE(SUM(amount), 0) as total FROM expenses
                   WHERE strftime('%Y-%m', date) = ?""",
                (month_str,)
            )
            
            growth.append({
                'month': month_str,
                'new_users': new_users['count'] if new_users else 0,
                'transaction_volume': db.to_rupees(volume['total']) if volume else 0
            })
        
        return growth
    
    def get_top_investors(self, limit: int = 10) -> List[Dict]:
        """Get users with highest investment portfolios"""
        investors = db.execute(
            """SELECT u.user_id, u.username, u.email,
                      SUM(ui.invested_amount) as total_invested,
                      SUM(ui.units_owned * ma.current_price) as current_value
               FROM users u
               JOIN user_investments ui ON u.user_id = ui.user_id
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               GROUP BY u.user_id
               ORDER BY current_value DESC
               LIMIT ?""",
            (limit,),
            fetch=True
        )
        
        return [{
            'user_id': i['user_id'],
            'username': i['username'],
            'email': i['email'],
            'invested': db.to_rupees(i['total_invested']),
            'current_value': db.to_rupees(i['current_value']),
            'profit_loss': db.to_rupees(i['current_value'] - i['total_invested'])
        } for i in investors]
    
    def get_investment_distribution(self) -> List[Dict]:
        """Get investment distribution by asset type"""
        distribution = db.execute(
            """SELECT ma.asset_type,
                      COUNT(DISTINCT ui.user_id) as investors,
                      SUM(ui.invested_amount) as total_invested,
                      SUM(ui.units_owned * ma.current_price) as current_value
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               GROUP BY ma.asset_type
               ORDER BY current_value DESC""",
            fetch=True
        )
        
        return [{
            'type': d['asset_type'],
            'investors': d['investors'],
            'invested': db.to_rupees(d['total_invested']),
            'current_value': db.to_rupees(d['current_value'])
        } for d in distribution]
    
    def get_large_transactions(self, threshold: float = 100000, limit: int = 50) -> List[Dict]:
        """Get large transactions for fraud monitoring"""
        threshold_paise = db.to_paise(threshold)
        
        transactions = db.execute(
            """SELECT e.expense_id, e.user_id, u.username, u.email,
                      e.amount, e.category, e.description, e.date
               FROM expenses e
               JOIN users u ON e.user_id = u.user_id
               WHERE e.amount >= ?
               ORDER BY e.date DESC
               LIMIT ?""",
            (threshold_paise, limit),
            fetch=True
        )
        
        return [{
            'expense_id': t['expense_id'],
            'user_id': t['user_id'],
            'username': t['username'],
            'email': t['email'],
            'amount': db.to_rupees(t['amount']),
            'category': t['category'],
            'description': t['description'],
            'date': t['date']
        } for t in transactions]
    
    def get_users_over_budget(self) -> List[Dict]:
        """Get users currently exceeding their budgets"""
        now = datetime.now()
        
        over_budget = db.execute(
            """SELECT u.user_id, u.username, u.email,
                      b.category, b.limit_amount,
                      COALESCE(SUM(e.amount), 0) as spent
               FROM budgets b
               JOIN users u ON b.user_id = u.user_id
               LEFT JOIN expenses e ON b.user_id = e.user_id 
                   AND b.category = e.category
                   AND strftime('%Y-%m', e.date) = ?
               WHERE b.year = ? AND b.month = ?
               GROUP BY b.budget_id
               HAVING spent > b.limit_amount
               ORDER BY (spent - b.limit_amount) DESC""",
            (f"{now.year}-{now.month:02d}", now.year, now.month),
            fetch=True
        )
        
        return [{
            'user_id': o['user_id'],
            'username': o['username'],
            'email': o['email'],
            'category': o['category'],
            'limit': db.to_rupees(o['limit_amount']),
            'spent': db.to_rupees(o['spent']),
            'overspent': db.to_rupees(o['spent'] - o['limit_amount'])
        } for o in over_budget]


# Singleton instance
analytics_service = AnalyticsService()
