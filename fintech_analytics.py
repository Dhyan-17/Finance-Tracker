"""
Fintech Analytics Engine
Comprehensive analytics for the finance tracker platform
"""

from datetime import datetime, timedelta
from collections import defaultdict


class FintechAnalytics:
    """Advanced analytics for fintech platform"""
    
    def __init__(self, db):
        self.db = db
    
    # ==================================================
    # USER ANALYTICS
    # ==================================================
    
    def get_user_spending_analysis(self, user_id, months=6):
        """Detailed spending analysis for a user"""
        # Category breakdown
        categories = self.db.execute_query(
            """SELECT category, SUM(amount) as total, COUNT(*) as count,
                      AVG(amount) as avg_amount
               FROM expenses
               WHERE user_id = %s AND date >= DATE_SUB(NOW(), INTERVAL %s MONTH)
               GROUP BY category
               ORDER BY total DESC""",
            (user_id, months), fetch=True
        )
        
        # Monthly trend
        monthly = self.db.execute_query(
            """SELECT DATE_FORMAT(date, '%%Y-%%m') as month,
                      SUM(amount) as total
               FROM expenses
               WHERE user_id = %s AND date >= DATE_SUB(NOW(), INTERVAL %s MONTH)
               GROUP BY month
               ORDER BY month""",
            (user_id, months), fetch=True
        )
        
        # Payment mode distribution
        payment_modes = self.db.execute_query(
            """SELECT payment_mode, SUM(amount) as total, COUNT(*) as count
               FROM expenses
               WHERE user_id = %s AND date >= DATE_SUB(NOW(), INTERVAL %s MONTH)
               GROUP BY payment_mode""",
            (user_id, months), fetch=True
        )
        
        return {
            'categories': categories,
            'monthly_trend': monthly,
            'payment_modes': payment_modes
        }
    
    def get_income_vs_expense_trend(self, user_id, months=12):
        """Income vs expense comparison over time"""
        trend = []
        
        for i in range(months, -1, -1):
            date = datetime.now() - timedelta(days=i*30)
            month_key = date.strftime("%Y-%m")
            
            income = self.db.execute_query(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM income WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s""",
                (user_id, month_key), fetch=True
            )
            
            expense = self.db.execute_query(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM expenses WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s""",
                (user_id, month_key), fetch=True
            )
            
            trend.append({
                'month': month_key,
                'income': float(income[0]['total']) if income else 0,
                'expense': float(expense[0]['total']) if expense else 0
            })
        
        return trend
    
    def get_budget_compliance_score(self, user_id):
        """Calculate how well user follows their budgets"""
        current_month = datetime.now()
        year, month = current_month.year, current_month.month
        
        budgets = self.db.execute_query(
            """SELECT b.category, b.limit_amount,
                      COALESCE(SUM(e.amount), 0) as spent
               FROM budget b
               LEFT JOIN expenses e ON b.user_id = e.user_id 
                   AND b.category = e.category
                   AND DATE_FORMAT(e.date, '%%Y-%%m') = %s
               WHERE b.user_id = %s AND b.year = %s AND b.month = %s
               GROUP BY b.budget_id""",
            (f"{year}-{month:02d}", user_id, year, month), fetch=True
        )
        
        if not budgets:
            return {'score': 100, 'categories': []}
        
        total_score = 0
        category_details = []
        
        for b in budgets:
            limit = float(b['limit_amount'])
            spent = float(b['spent'])
            
            if spent <= limit:
                score = 100
                status = 'ON_TRACK'
            elif spent <= limit * 1.1:
                score = 70
                status = 'SLIGHTLY_OVER'
            elif spent <= limit * 1.25:
                score = 40
                status = 'OVER_BUDGET'
            else:
                score = 0
                status = 'CRITICAL'
            
            total_score += score
            category_details.append({
                'category': b['category'],
                'limit': limit,
                'spent': spent,
                'percent_used': (spent / limit * 100) if limit > 0 else 0,
                'status': status
            })
        
        avg_score = total_score / len(budgets) if budgets else 100
        
        return {
            'score': round(avg_score, 1),
            'categories': category_details
        }
    
    # ==================================================
    # SYSTEM-WIDE ANALYTICS (ADMIN)
    # ==================================================
    
    def get_platform_summary(self):
        """Complete platform statistics"""
        # User stats
        user_stats = self.db.execute_query(
            """SELECT 
                   COUNT(*) as total_users,
                   SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_users,
                   SUM(CASE WHEN status = 'BLOCKED' THEN 1 ELSE 0 END) as blocked_users,
                   SUM(CASE WHEN last_active >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) as active_7d,
                   SUM(CASE WHEN last_active >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 ELSE 0 END) as active_30d
               FROM users""",
            fetch=True
        )[0]
        
        # Financial stats
        wallet_total = self.db.execute_query(
            "SELECT COALESCE(SUM(wallet_balance), 0) as total FROM users",
            fetch=True
        )[0]['total']
        
        bank_total = self.db.execute_query(
            "SELECT COALESCE(SUM(balance), 0) as total FROM bank_accounts",
            fetch=True
        )[0]['total']
        
        expense_stats = self.db.execute_query(
            """SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count
               FROM expenses""",
            fetch=True
        )[0]
        
        income_stats = self.db.execute_query(
            """SELECT COALESCE(SUM(amount), 0) as total, COUNT(*) as count
               FROM income""",
            fetch=True
        )[0]
        
        # Investment stats
        investment_stats = self.db.execute_query(
            """SELECT 
                   COALESCE(SUM(invested_amount), 0) as total_invested,
                   COALESCE(SUM(units_owned * ma.current_price), 0) as current_value,
                   COUNT(DISTINCT user_id) as investors
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id""",
            fetch=True
        )[0]
        
        return {
            'users': user_stats,
            'finances': {
                'wallet_total': float(wallet_total or 0),
                'bank_total': float(bank_total or 0),
                'total_expenses': float(expense_stats['total'] or 0),
                'expense_count': expense_stats['count'],
                'total_income': float(income_stats['total'] or 0),
                'income_count': income_stats['count']
            },
            'investments': {
                'total_invested': float(investment_stats['total_invested'] or 0),
                'current_value': float(investment_stats['current_value'] or 0),
                'total_investors': investment_stats['investors']
            }
        }
    
    def get_top_spending_categories_system(self, limit=10):
        """Top spending categories across all users"""
        return self.db.execute_query(
            """SELECT category, 
                      SUM(amount) as total,
                      COUNT(*) as transaction_count,
                      COUNT(DISTINCT user_id) as unique_users,
                      AVG(amount) as avg_amount
               FROM expenses
               GROUP BY category
               ORDER BY total DESC
               LIMIT %s""",
            (limit,), fetch=True
        )
    
    def get_monthly_platform_growth(self, months=12):
        """Platform growth metrics over time"""
        growth = []
        
        for i in range(months, -1, -1):
            date = datetime.now() - timedelta(days=i*30)
            month_key = date.strftime("%Y-%m")
            year, month = map(int, month_key.split('-'))
            
            # New users that month
            new_users = self.db.execute_query(
                """SELECT COUNT(*) as cnt FROM users 
                   WHERE DATE_FORMAT(join_date, '%%Y-%%m') = %s""",
                (month_key,), fetch=True
            )[0]['cnt']
            
            # Transaction volume
            volume = self.db.execute_query(
                """SELECT COALESCE(SUM(amount), 0) as total
                   FROM expenses WHERE DATE_FORMAT(date, '%%Y-%%m') = %s""",
                (month_key,), fetch=True
            )[0]['total']
            
            growth.append({
                'month': month_key,
                'new_users': new_users,
                'transaction_volume': float(volume or 0)
            })
        
        return growth
    
    def get_investment_distribution(self):
        """Distribution of investments across asset types"""
        return self.db.execute_query(
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
    
    def get_top_investors(self, limit=10):
        """Users with highest investment portfolios"""
        return self.db.execute_query(
            """SELECT u.user_id, u.username, u.email,
                      SUM(ui.invested_amount) as total_invested,
                      SUM(ui.units_owned * ma.current_price) as current_value,
                      (SUM(ui.units_owned * ma.current_price) - SUM(ui.invested_amount)) as profit_loss
               FROM users u
               JOIN user_investments ui ON u.user_id = ui.user_id
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               GROUP BY u.user_id
               ORDER BY current_value DESC
               LIMIT %s""",
            (limit,), fetch=True
        )
    
    def get_active_vs_inactive_users(self):
        """User activity distribution"""
        return self.db.execute_query(
            """SELECT 
                   CASE 
                       WHEN last_active >= DATE_SUB(NOW(), INTERVAL 1 DAY) THEN 'Active Today'
                       WHEN last_active >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'Active This Week'
                       WHEN last_active >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 'Active This Month'
                       ELSE 'Inactive'
                   END as activity_status,
                   COUNT(*) as user_count
               FROM users
               WHERE status = 'ACTIVE'
               GROUP BY activity_status""",
            fetch=True
        )
    
    def get_average_user_metrics(self):
        """Calculate average metrics per user"""
        # Average net worth
        avg_networth = self.db.execute_query(
            """SELECT AVG(net_worth) as avg_networth
               FROM user_analytics_cache
               WHERE net_worth > 0""",
            fetch=True
        )
        
        # Average monthly spending
        avg_spending = self.db.execute_query(
            """SELECT AVG(monthly_total) as avg_spending FROM (
                   SELECT user_id, SUM(amount) / 
                       GREATEST(TIMESTAMPDIFF(MONTH, MIN(date), NOW()), 1) as monthly_total
                   FROM expenses
                   GROUP BY user_id
               ) as monthly_avgs""",
            fetch=True
        )
        
        # Average investments
        avg_investment = self.db.execute_query(
            """SELECT AVG(total) as avg_investment FROM (
                   SELECT user_id, SUM(invested_amount) as total
                   FROM user_investments
                   GROUP BY user_id
               ) as inv_totals""",
            fetch=True
        )
        
        return {
            'avg_net_worth': float(avg_networth[0]['avg_networth'] or 0) if avg_networth else 0,
            'avg_monthly_spending': float(avg_spending[0]['avg_spending'] or 0) if avg_spending else 0,
            'avg_investment': float(avg_investment[0]['avg_investment'] or 0) if avg_investment else 0
        }
    
    # ==================================================
    # RISK & FRAUD DETECTION
    # ==================================================
    
    def detect_unusual_transactions(self, threshold_multiplier=3):
        """Detect transactions that are unusually large for each user"""
        return self.db.execute_query(
            """SELECT e.expense_id, u.username, u.email, e.category, 
                      e.amount, e.date, user_avg.avg_amount,
                      (e.amount / user_avg.avg_amount) as multiplier
               FROM expenses e
               JOIN users u ON e.user_id = u.user_id
               JOIN (
                   SELECT user_id, AVG(amount) as avg_amount
                   FROM expenses
                   GROUP BY user_id
               ) user_avg ON e.user_id = user_avg.user_id
               WHERE e.amount > user_avg.avg_amount * %s
               ORDER BY multiplier DESC
               LIMIT 20""",
            (threshold_multiplier,), fetch=True
        )
    
    def get_users_exceeding_budgets(self):
        """Find all users currently exceeding their budgets"""
        current = datetime.now()
        return self.db.execute_query(
            """SELECT u.user_id, u.username, u.email, 
                      b.category, b.limit_amount,
                      COALESCE(SUM(e.amount), 0) as spent,
                      (COALESCE(SUM(e.amount), 0) - b.limit_amount) as overspent
               FROM budget b
               JOIN users u ON b.user_id = u.user_id
               LEFT JOIN expenses e ON b.user_id = e.user_id 
                   AND b.category = e.category
                   AND DATE_FORMAT(e.date, '%%Y-%%m') = %s
               WHERE b.year = %s AND b.month = %s
               GROUP BY b.budget_id
               HAVING spent > b.limit_amount
               ORDER BY overspent DESC""",
            (f"{current.year}-{current.month:02d}", current.year, current.month), fetch=True
        )
