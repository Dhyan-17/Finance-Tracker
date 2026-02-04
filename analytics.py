from datetime import datetime, timedelta
import calendar

class Analytics:
    """Text-based analytics for wallet system"""

    def __init__(self, db):
        self.db = db

    def generate_user_analytics(self, user_id, month=None):
        """Generate comprehensive analytics for a user"""
        if not month:
            month = datetime.now().strftime("%Y-%m")

        analytics = {
            'monthly_summary': self.get_monthly_summary(user_id, month),
            'category_breakdown': self.get_category_breakdown(user_id, month),
            'spending_trends': self.get_spending_trends(user_id),
            'budget_analysis': self.get_budget_analysis(user_id, month),
            'income_vs_expense': self.get_income_vs_expense_comparison(user_id, month)
        }

        return analytics

    def get_monthly_summary(self, user_id, month):
        """Get monthly financial summary"""
        try:
            # Income
            income_query = """
                SELECT SUM(amount) as total_income, COUNT(*) as income_count
                FROM income
                WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s
            """
            income_result = self.db.execute_query(income_query, (user_id, month), fetch=True)
            total_income = income_result[0]['total_income'] if income_result[0]['total_income'] else 0
            income_count = income_result[0]['income_count'] if income_result[0]['income_count'] else 0

            # Expenses
            expense_query = """
                SELECT SUM(amount) as total_expense, COUNT(*) as expense_count
                FROM expenses
                WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s
            """
            expense_result = self.db.execute_query(expense_query, (user_id, month), fetch=True)
            total_expense = expense_result[0]['total_expense'] if expense_result[0]['total_expense'] else 0
            expense_count = expense_result[0]['expense_count'] if expense_result[0]['expense_count'] else 0

            # Net savings
            net_savings = total_income - total_expense

            # Savings rate
            savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

            return {
                'month': month,
                'total_income': total_income,
                'total_expense': total_expense,
                'net_savings': net_savings,
                'savings_rate': savings_rate,
                'income_transactions': income_count,
                'expense_transactions': expense_count
            }

        except Exception as e:
            return {'error': str(e)}

    def get_category_breakdown(self, user_id, month):
        """Get expense breakdown by category"""
        try:
            query = """
                SELECT category, SUM(amount) as total_amount, COUNT(*) as transaction_count,
                       AVG(amount) as avg_amount, MAX(amount) as max_amount
                FROM expenses
                WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s
                GROUP BY category
                ORDER BY total_amount DESC
            """
            results = self.db.execute_query(query, (user_id, month), fetch=True)

            if not results:
                return []

            # Calculate percentages
            total_expense = sum(item['total_amount'] for item in results)
            for item in results:
                item['percentage'] = (item['total_amount'] / total_expense * 100) if total_expense > 0 else 0

            return results

        except Exception as e:
            return {'error': str(e)}

    def get_spending_trends(self, user_id, months=6):
        """Get spending trends over last N months"""
        try:
            trends = []
            current_date = datetime.now()

            for i in range(months):
                month_date = current_date - timedelta(days=i*30)
                month_str = month_date.strftime("%Y-%m")

                summary = self.get_monthly_summary(user_id, month_str)
                if 'error' not in summary:
                    trends.append({
                        'month': month_str,
                        'income': summary['total_income'],
                        'expense': summary['total_expense'],
                        'savings': summary['net_savings']
                    })

            return trends[::-1]  # Reverse to chronological order

        except Exception as e:
            return {'error': str(e)}

    def get_budget_analysis(self, user_id, month):
        """Analyze budget vs actual spending"""
        try:
            # Parse month string (YYYY-MM) into year and month integers
            year_int, month_int = map(int, month.split('-'))
            
            # Get budgets for the month using correct year/month columns
            budget_query = """
                SELECT category, limit_amount
                FROM budget
                WHERE user_id = %s AND year = %s AND month = %s
            """
            budgets = self.db.execute_query(
                budget_query,
                (user_id, year_int, month_int),
                fetch=True
            )
            if not budgets:
                return []

            analysis = []
            for budget in budgets:
                category = budget['category']
                limit = budget['limit_amount']

                # Get actual spending
                spend_query = """
                    SELECT SUM(amount) as spent
                    FROM expenses
                    WHERE user_id = %s AND category = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s
                """
                spend_result = self.db.execute_query(spend_query, (user_id, category, month), fetch=True)
                spent = spend_result[0]['spent'] if spend_result[0]['spent'] else 0

                remaining = limit - spent
                percentage_used = (spent / limit * 100) if limit > 0 else 0
                if percentage_used <= 70:
                    status = "✅ On Track"
                elif percentage_used <= 100:
                    status = "🟡 Approaching Limit"
                else:
                    status = "❌ Over Budget"

                analysis.append({
                    'category': category,
                    'budget_limit': limit,
                    'spent': spent,
                    'remaining': remaining,
                    'percentage_used': percentage_used,
                    'status': status
                })

            return analysis

        except Exception as e:
            return {'error': str(e)}

    def get_income_vs_expense_comparison(self, user_id, month):
        """Compare income vs expense patterns"""
        try:
            # Daily breakdown for the month
            days_in_month = calendar.monthrange(int(month.split('-')[0]), int(month.split('-')[1]))[1]

            daily_data = []
            for day in range(1, days_in_month + 1):
                day_str = f"{month}-{day:02d}"

                # Income for the day
                income_query = """
                    SELECT SUM(amount) as daily_income
                    FROM income
                    WHERE user_id = %s AND DATE(date) = %s
                """
                income_result = self.db.execute_query(income_query, (user_id, day_str), fetch=True)
                daily_income = income_result[0]['daily_income'] if income_result[0]['daily_income'] else 0

                # Expense for the day
                expense_query = """
                    SELECT SUM(amount) as daily_expense
                    FROM expenses
                    WHERE user_id = %s AND DATE(date) = %s
                """
                expense_result = self.db.execute_query(expense_query, (user_id, day_str), fetch=True)
                daily_expense = expense_result[0]['daily_expense'] if expense_result[0]['daily_expense'] else 0

                if daily_income > 0 or daily_expense > 0:
                    daily_data.append({
                        'day': day,
                        'income': daily_income,
                        'expense': daily_expense,
                        'net': daily_income - daily_expense
                    })

            return daily_data

        except Exception as e:
            return {'error': str(e)}

    def display_analytics_report(self, user_id, month=None):
        """Display formatted analytics report"""
        analytics = self.generate_user_analytics(user_id, month)

        if not month:
            month = datetime.now().strftime("%Y-%m")

        print("+------------------------------------------------+")
        print("|           FINANCIAL ANALYTICS REPORT           |")
        print("+------------------------------------------------+")
        print(f"| Report Month: {month}")
        print("+------------------------------------------------+")

        # Monthly Summary
        summary = analytics.get('monthly_summary', {})
        if 'error' not in summary:
            print("MONTHLY SUMMARY:")
            print("+------------------------------------------------+")
            print(f"| Total Income: ₹{summary.get('total_income', 0):.2f}")
            print(f"| Total Expenses: ₹{summary.get('total_expense', 0):.2f}")
            print(f"| Net Savings: ₹{summary.get('net_savings', 0):.2f}")
            print(f"| Savings Rate: {summary.get('savings_rate', 0):.1f}%")
            print(f"| Income Transactions: {summary.get('income_transactions', 0)}")
            print(f"| Expense Transactions: {summary.get('expense_transactions', 0)}")
            print("+------------------------------------------------+")

        # Category Breakdown
        categories = analytics.get('category_breakdown', [])
        if categories and 'error' not in categories:
            print("CATEGORY BREAKDOWN:")
            print("+------------------------------------------------+")
            for cat in categories[:5]:  # Top 5 categories
                print(f"| {cat['category']:<12}: ₹{cat['total_amount']:<8.2f} ({cat['percentage']:.1f}%)")
            print("+------------------------------------------------+")

        # Budget Analysis
        budgets = analytics.get('budget_analysis', [])
        if budgets and 'error' not in budgets:
            print("BUDGET ANALYSIS:")
            print("+------------------------------------------------+")
            for budget in budgets:
                status_icon = "✅" if "On Track" in budget['status'] else "⚠️" if "Approaching" in budget['status'] else "❌"
                print(f"| {status_icon} {budget['category']:<10}: ₹{budget['spent']:<6.2f}/₹{budget['budget_limit']:<6.2f} ({budget['percentage_used']:.1f}%)")
            print("+------------------------------------------------+")

        # Spending Trends
        trends = analytics.get('spending_trends', [])
        if trends and 'error' not in trends and len(trends) > 1:
            print("SPENDING TRENDS (Last 6 Months):")
            print("+------------------------------------------------+")
            for trend in trends[-3:]:  # Last 3 months
                print(f"| {trend['month']}: Income ₹{trend['income']:<6.2f}, Expense ₹{trend['expense']:<6.2f}, Savings ₹{trend['savings']:<6.2f}")
            print("+------------------------------------------------+")

    def get_highest_spending_category(self, user_id, month):
        """Get the category with highest spending"""
        categories = self.get_category_breakdown(user_id, month)
        if categories and 'error' not in categories:
            return categories[0]['category'] if categories else None
        return None

    def get_savings_percentage(self, user_id, month):
        """Get savings percentage for the month"""
        summary = self.get_monthly_summary(user_id, month)
        if 'error' not in summary:
            return summary.get('savings_rate', 0)
        return 0
