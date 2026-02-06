"""
Enhanced AI Assistant Service
Advanced natural language financial assistant with comprehensive query handling
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from database.db import db
from services.wallet_service import wallet_service
from services.analytics_service import analytics_service
from services.security_service import security_service


@dataclass
class AIResponse:
    """Structured AI response"""
    success: bool
    message: str
    data: Dict
    display: str
    suggestions: List[str]
    charts: List[Dict] = None
    error: str = None


class EnhancedAIAssistant:
    """Enhanced AI-powered financial assistant"""
    
    def __init__(self):
        # Command handlers
        self.handlers = {
            'balance': self._handle_balance,
            'spending': self._handle_spending,
            'income': self._handle_income,
            'expense': self._handle_expense,
            'budget': self._handle_budget,
            'investment': self._handle_investment,
            'goal': self._handle_goal,
            'transfer': self._handle_transfer,
            'transaction': self._handle_transaction,
            'help': self._handle_help,
            'tip': self._handle_tip,
            'insight': self._handle_insight,
            'search': self._handle_search,
            'health': self._handle_health,
            'networth': self._handle_networth,
            'savings': self._handle_savings,
            'compare': self._handle_compare,
            'forecast': self._handle_forecast,
        }
        
        # Enhanced patterns for natural language understanding
        self.patterns = [
            # Balance queries
            (r'(show|what|how much|check|get|tell me).*(balance|money|wallet|funds|available)', 'balance'),
            (r'(total|net).*(worth|balance)', 'networth'),
            
            # Spending queries
            (r'(show|what|how much|how|spent|spent on|expenses|spending)', 'spending'),
            (r'(last|past|previous|this|recent).*(month|week|year|day).*spending|spending.*(last|past|this)', 'spending'),
            (r'food.*expense|food.*spending|dining.*expense', 'spending'),
            (r'(how much|spent).*(on|for|for|on).*(food|shopping|travel|transport|bills)', 'spending'),
            
            # Income queries
            (r'(show|what|how much|total|earned|income|salary)', 'income'),
            
            # Expense queries
            (r'(expense|transaction|spent|purchase|payment)', 'expense'),
            (r'(last|recent|recent).*(transaction|expense|purchase)', 'transaction'),
            
            # Budget queries
            (r'(show|get|check|budget|limit|spending limit)', 'budget'),
            (r'(remaining|left|over|under).*budget', 'budget'),
            
            # Investment queries
            (r'(show|my|portfolio|investment|investments|stocks|crypto|mf|mutual fund)', 'investment'),
            (r'(invested|returns|profit|loss|gain)', 'investment'),
            
            # Goal queries
            (r'(goal|target|saving|save for|savings goal)', 'goal'),
            
            # Transfer queries
            (r'(transfer|send|pay|move|send money|transfer money)', 'transfer'),
            
            # Search queries
            (r'(find|search|look for|locate|show me).*(transaction|expense|income)', 'search'),
            
            # Help queries
            (r'(help|commands|what can you do|how to use|guide)', 'help'),
            
            # Tip queries
            (r'(tip|advice|suggest|recommend|tips|recommendation)', 'tip'),
            
            # Insight queries
            (r'(insight|analysis|analyze|financial health|score)', 'insight'),
            (r'(health|health score)', 'health'),
            
            # Savings queries
            (r'(saving|savings|save|save money)', 'savings'),
            
            # Comparison queries
            (r'(compare|vs|versus|compared to|versus)', 'compare'),
            
            # Forecast queries
            (r'(forecast|predict|future|projection|next month)', 'forecast'),
        ]
        
        # Category mappings
        self.category_aliases = {
            'food': 'Food & Dining',
            'dining': 'Food & Dining',
            'restaurant': 'Food & Dining',
            'groceries': 'Groceries',
            'grocery': 'Groceries',
            'transport': 'Transportation',
            'travel': 'Travel',
            'uber': 'Transportation',
            'ola': 'Transportation',
            'petrol': 'Transportation',
            'fuel': 'Transportation',
            'shopping': 'Shopping',
            'mall': 'Shopping',
            'amazon': 'Shopping',
            'bills': 'Bills & Utilities',
            'utilities': 'Bills & Utilities',
            'electricity': 'Bills & Utilities',
            'water': 'Bills & Utilities',
            'gas': 'Bills & Utilities',
            'mobile': 'Bills & Utilities',
            'recharge': 'Bills & Utilities',
            'entertainment': 'Entertainment',
            'movies': 'Entertainment',
            'netflix': 'Entertainment',
            'healthcare': 'Healthcare',
            'hospital': 'Healthcare',
            'medicine': 'Healthcare',
            'pharmacy': 'Healthcare',
            'education': 'Education',
            'course': 'Education',
            'tuition': 'Education',
        }
        
        # Time period patterns
        self.time_patterns = {
            'today': (0, 'days'),
            'this week': (7, 'days'),
            'this month': (30, 'days'),
            'last month': (60, 'days'),
            'this quarter': (90, 'days'),
            'this year': (365, 'days'),
            'last 7 days': (7, 'days'),
            'last 30 days': (30, 'days'),
            'last 3 months': (90, 'days'),
            'last 6 months': (180, 'days'),
            'last year': (365, 'days'),
        }
    
    def process_query(self, user_id: int, query: str) -> AIResponse:
        """
        Process natural language query
        
        Args:
            user_id: User ID
            query: Natural language query
            
        Returns:
            AIResponse with result
        """
        try:
            # Clean query
            clean_query = query.lower().strip()
            
            # Detect intent
            intent = self._detect_intent(clean_query)
            
            # Extract entities
            entities = self._extract_entities(clean_query)
            
            # Get handler and process
            if intent and intent in self.handlers:
                response = self.handlers[intent](user_id, clean_query, entities)
            else:
                response = self._handle_unknown(user_id, clean_query, entities)
            
            # Save conversation
            self._save_conversation(user_id, query, response)
            
            return response
            
        except Exception as e:
            return AIResponse(
                success=False,
                message="Error processing query",
                data={},
                display=f"❌ Sorry, I encountered an error: {str(e)}",
                suggestions=["Try again", "Ask a different question"],
                error=str(e)
            )
    
    def _detect_intent(self, query: str) -> Optional[str]:
        """Detect user intent from query"""
        for pattern, intent in self.patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return intent
        return None
    
    def _extract_entities(self, query: str) -> Dict:
        """Extract entities from query"""
        entities = {
            'period': None,
            'category': None,
            'amount': None,
            'top_n': None,
            'comparison': None,
            'date': None,
        }
        
        # Extract time period
        for period_key, value in self.time_patterns.items():
            if period_key in query:
                entities['period'] = period_key
                break
        
        # Extract category
        for alias, category in self.category_aliases.items():
            if alias in query:
                entities['category'] = category
                break
        
        # Extract amount
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        if amount_match:
            entities['amount'] = float(amount_match.group(1).replace(',', ''))
        
        # Extract top N
        top_match = re.search(r'(?:top|best|highest)\s*(\d+)', query, re.IGNORECASE)
        if top_match:
            entities['top_n'] = int(top_match.group(1))
        
        # Extract comparison
        if re.search(r'(?:vs|versus|compared to|versus)', query, re.IGNORECASE):
            entities['comparison'] = True
        
        # Extract date patterns
        date_match = re.search(r'(?:on|during|at)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', query)
        if date_match:
            entities['date'] = date_match.group(1)
        
        return entities
    
    def _get_period_dates(self, period: str) -> Tuple[str, str]:
        """Get date range for period"""
        now = datetime.now()
        
        if not period:
            period = 'this month'
        
        period_map = {
            'today': (now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')),
            'this week': ((now - timedelta(days=now.weekday())).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')),
            'this month': (now.strftime('%Y-%m-01'), now.strftime('%Y-%m-%d')),
            'last month': (
                (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-01'),
                (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
            ),
            'this quarter': ((now - timedelta(days=now.month * 30)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')),
            'this year': (now.strftime('%Y-01-01'), now.strftime('%Y-%m-%d')),
            'last 7 days': ((now - timedelta(days=7)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')),
            'last 30 days': ((now - timedelta(days=30)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')),
            'last 3 months': ((now - timedelta(days=90)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')),
            'last 6 months': ((now - timedelta(days=180)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')),
            'last year': ((now - timedelta(days=365)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')),
        }
        
        return period_map.get(period, period_map['this month'])
    
    # ============================================================
    # COMMAND HANDLERS
    # ============================================================
    
    def _handle_balance(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle balance queries"""
        balance = wallet_service.get_total_balance(user_id)
        
        display = f"""
💰 **Your Balance Summary**

| Account | Amount |
|---------|--------|
| Wallet | ₹{balance['wallet']:,.2f} |
| Bank | ₹{balance['bank']:,.2f} |
| Investments | ₹{balance['investments_current']:,.2f} ({balance['investments_pl']:+,.2f}) |
| **Net Worth** | **₹{balance['net_worth']:,.2f}** |
"""
        
        return AIResponse(
            success=True,
            message="Balance retrieved",
            data=balance,
            display=display,
            suggestions=[
                "Show my spending this month",
                "Show budget status",
                "Give me saving tips"
            ]
        )
    
    def _handle_spending(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle spending queries"""
        period = entities.get('period', 'this month')
        start_date, end_date = self._get_period_dates(period)
        category = entities.get('category')
        
        # Get expenses
        if category:
            expenses = db.execute(
                """SELECT * FROM expenses 
                   WHERE user_id = ? AND category = ? AND date >= ? AND date <= ?
                   ORDER BY date DESC""",
                (user_id, category, start_date, end_date),
                fetch=True
            )
        else:
            expenses = db.get_user_expenses(user_id, start_date=start_date, end_date=end_date, limit=100)
        
        total = sum(db.to_rupees(e['amount']) for e in expenses) if expenses else 0
        categories = {}
        
        for e in expenses:
            cat = e['category']
            categories[cat] = categories.get(cat, 0) + db.to_rupees(e['amount'])
        
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        
        period_label = period.replace('_', ' ').title()
        
        lines = [f"📊 **Your Spending ({period_label})**\n"]
        lines.append(f"**Total: ₹{total:,.2f}**\n")
        
        if sorted_cats:
            lines.append("**By Category:**")
            for cat, amount in sorted_cats[:8]:
                pct = (amount / total * 100) if total > 0 else 0
                lines.append(f"- {cat}: ₹{amount:,.2f} ({pct:.1f}%)")
        
        # Generate chart data
        charts = [{
            'type': 'pie',
            'data': [{'label': cat, 'value': amount} for cat, amount in sorted_cats[:8]],
            'title': f'Spending by Category ({period_label})'
        }]
        
        return AIResponse(
            success=True,
            message=f"Spending summary for {period_label.lower()}",
            data={'total': total, 'categories': dict(sorted_cats), 'count': len(expenses)},
            display='\n'.join(lines),
            suggestions=['Show top expenses', 'Compare with last month', 'Set budget'],
            charts=charts
        )
    
    def _handle_income(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle income queries"""
        period = entities.get('period', 'this month')
        start_date, end_date = self._get_period_dates(period)
        
        income_list = db.get_user_income(user_id, start_date=start_date, end_date=end_date)
        
        total = sum(db.to_rupees(i['amount']) for i in income_list) if income_list else 0
        sources = {}
        
        for i in income_list:
            src = i['source']
            sources[src] = sources.get(src, 0) + db.to_rupees(i['amount'])
        
        period_label = period.replace('_', ' ').title()
        
        lines = [f"💵 **Your Income ({period_label})**\n"]
        lines.append(f"**Total: ₹{total:,.2f}**\n")
        
        if sources:
            lines.append("**By Source:**")
            for src, amount in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- {src}: ₹{amount:,.2f}")
        
        return AIResponse(
            success=True,
            message=f"Income summary for {period_label.lower()}",
            data={'total': total, 'sources': sources, 'count': len(income_list)},
            display='\n'.join(lines),
            suggestions=['Show savings rate', 'Compare income vs expense', 'Add income']
        )
    
    def _handle_expense(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle expense detail queries"""
        top_n = entities.get('top_n', 10)
        category = entities.get('category')
        now = datetime.now()
        
        if category:
            expenses = db.execute(
                """SELECT * FROM expenses 
                   WHERE user_id = ? AND category = ? 
                   ORDER BY date DESC LIMIT ?""",
                (user_id, category, top_n),
                fetch=True
            )
            title = f"📝 **{category} Expenses**"
        else:
            expenses = analytics_service.get_top_expenses(user_id, now.year, now.month, top_n)
            title = f"📝 **Top {top_n} Expenses This Month**"
        
        lines = [title, ""]
        
        for i, e in enumerate(expenses[:10], 1):
            amount = db.to_rupees(e['amount']) if isinstance(e['amount'], int) else e['amount']
            desc = e.get('description', e.get('category', 'N/A'))[:30]
            date_str = str(e.get('date', ''))[:10]
            lines.append(f"{i}. ₹{amount:,.2f} - {desc} ({date_str})")
        
        return AIResponse(
            success=True,
            message="Expenses retrieved",
            data={'expenses': expenses},
            display='\n'.join(lines),
            suggestions=['Show spending by category', 'Filter by date', 'Add expense']
        )
    
    def _handle_budget(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle budget queries"""
        now = datetime.now()
        budgets = analytics_service.get_budget_status(user_id, now.year, now.month)
        
        if not budgets:
            return AIResponse(
                success=True,
                message="No budgets set",
                data={},
                display="📋 **No Budgets Set**\n\nSet budgets to track your spending limits!",
                suggestions=['Set budget for Food ₹10000', 'Set budget for Transport ₹5000']
            )
        
        lines = [f"📋 **Budget Status ({now.strftime('%B %Y')})**\n"]
        
        total_budget = sum(b['limit'] for b in budgets)
        total_spent = sum(b['spent'] for b in budgets)
        
        lines.append(f"**Total: ₹{total_spent:,.0f} / ₹{total_budget:,.0f}**\n")
        
        for b in budgets:
            status_icon = '✅' if b['status'] == 'ON_TRACK' else '⚠️' if b['status'] == 'WARNING' else '❌'
            progress = min(b['percentage'] / 100, 1.0)
            bar_length = 20
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            lines.append(f"{status_icon} **{b['category']}**")
            lines.append(f"   {bar} {b['percentage']:.0f}%")
            lines.append(f"   ₹{b['spent']:,.0f} / ₹{b['limit']:,.0f}")
            if b['remaining'] > 0:
                lines.append(f"   Remaining: ₹{b['remaining']:,.0f}")
            else:
                lines.append(f"   Over by: ₹{abs(b['remaining']):,.0f}")
            lines.append("")
        
        return AIResponse(
            success=True,
            message="Budget status retrieved",
            data={'budgets': budgets},
            display='\n'.join(lines),
            suggestions=['Update budget', 'Show spending trends', 'Get saving tips']
        )
    
    def _handle_investment(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle investment queries"""
        from services.investment_service import investment_service
        
        portfolio = investment_service.get_portfolio(user_id)
        
        if not portfolio['holdings']:
            return AIResponse(
                success=True,
                message="No investments",
                data={},
                display="📈 **No Investments**\n\nStart investing to grow your wealth!",
                suggestions=['Show market overview', 'Buy stocks', 'View crypto']
            )
        
        lines = ["📈 **Your Investment Portfolio**\n"]
        lines.append(f"**Total Invested:** ₹{portfolio['total_invested']:,.2f}")
        lines.append(f"**Current Value:** ₹{portfolio['current_value']:,.2f}")
        pl_sign = '+' if portfolio['total_profit_loss'] >= 0 else ''
        lines.append(f"**Profit/Loss:** {pl_sign}₹{portfolio['total_profit_loss']:,.2f} ({pl_sign}{portfolio['profit_loss_percent']:.2f}%)\n")
        
        lines.append("**Holdings:**")
        for h in portfolio['holdings']:
            pl_sign = '+' if h['profit_loss'] >= 0 else ''
            lines.append(f"- {h['asset_symbol']}: {h['units_owned']:.4f} units")
            lines.append(f"  Value: ₹{h['current_value']:,.2f} ({pl_sign}{h['profit_loss_percent']:.2f}%)")
        
        return AIResponse(
            success=True,
            message="Investment portfolio retrieved",
            data=portfolio,
            display='\n'.join(lines),
            suggestions=['Show market overview', 'Buy more', 'Sell investment']
        )
    
    def _handle_goal(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle financial goals queries"""
        goals = db.get_user_goals(user_id, status='ACTIVE')
        
        if not goals:
            return AIResponse(
                success=True,
                message="No goals",
                data={},
                display="🎯 **No Active Goals**\n\nSet goals to stay motivated!",
                suggestions=['Create goal for Emergency Fund ₹100000', 'Create goal for Vacation ₹50000']
            )
        
        lines = ["🎯 **Your Financial Goals**\n"]
        
        for g in goals:
            target = db.to_rupees(g['target_amount'])
            current = db.to_rupees(g['current_savings'])
            progress = (current / target * 100) if target > 0 else 0
            
            bar_length = 20
            filled = int(bar_length * min(progress / 100, 1.0))
            bar = '█' * filled + '░' * (bar_length - filled)
            
            lines.append(f"**{g['goal_name']}** ({g['priority']})")
            lines.append(f"   {bar} {progress:.1f}%")
            lines.append(f"   ₹{current:,.0f} / ₹{target:,.0f}")
            if g['target_date']:
                lines.append(f"   Target: {g['target_date']}")
            lines.append("")
        
        return AIResponse(
            success=True,
            message="Goals retrieved",
            data={'goals': goals},
            display='\n'.join(lines),
            suggestions=['Add contribution', 'Create new goal', 'Show progress']
        )
    
    def _handle_transfer(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle transfer queries"""
        return AIResponse(
            success=True,
            message="Transfer info",
            data={},
            display="💸 **Transfer Money**\n\nGo to Wallet → Transfer to send money to another user by:\n- Username\n- Email\n- Mobile number\n- UPI ID",
            suggestions=['Show my balance', 'Show recent transactions', 'View wallet']
        )
    
    def _handle_transaction(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle transaction queries"""
        return self._handle_search(user_id, query, entities)
    
    def _handle_search(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle search queries"""
        period = entities.get('period', 'this month')
        start_date, end_date = self._get_period_dates(period)
        category = entities.get('category')
        
        expenses = db.get_user_expenses(
            user_id, 
            start_date=start_date, 
            end_date=end_date, 
            category=category, 
            limit=20
        )
        
        lines = ["🔍 **Search Results**\n"]
        
        if not expenses:
            lines.append("No transactions found matching your criteria.")
        else:
            for e in expenses[:15]:
                amount = db.to_rupees(e['amount'])
                lines.append(f"- {e['date'][:10]} | {e['category']} | ₹{amount:,.2f}")
                if e.get('description'):
                    lines.append(f"  _{e['description'][:40]}_")
        
        return AIResponse(
            success=True,
            message="Search completed",
            data={'transactions': expenses},
            display='\n'.join(lines),
            suggestions=['Filter by category', 'Show spending by date', 'Export transactions']
        )
    
    def _handle_tip(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle tip queries"""
        tips = self._generate_personalized_tips(user_id)
        
        lines = ["💡 **Personalized Tips**\n"]
        
        for i, tip in enumerate(tips[:8], 1):
            lines.append(f"{i}. {tip}")
        
        return AIResponse(
            success=True,
            message="Tips generated",
            data={'tips': tips},
            display='\n'.join(lines),
            suggestions=['Show my budget', 'Analyze spending', 'Show financial health']
        )
    
    def _handle_insight(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle insight queries"""
        health = analytics_service.calculate_financial_health_score(user_id)
        budget_status = analytics_service.get_budget_status(user_id, datetime.now().year, datetime.now().month)
        
        lines = [f"📊 **Financial Health Analysis**\n"]
        lines.append(f"**Overall Score: {health['score']}/100** ({health['rating']})\n")
        lines.append("**Breakdown:**")
        
        breakdown_labels = {
            'savings_rate': 'Savings Rate',
            'budget_compliance': 'Budget Compliance',
            'emergency_fund': 'Emergency Fund',
            'investment_diversity': 'Investment Diversity',
            'activity': 'Transaction Activity'
        }
        
        for key, values in health.get('breakdown', {}).items():
            label = breakdown_labels.get(key, key.title())
            lines.append(f"- {label}: {values['score']}/{values['max']} ({values['value']:.1f}%)")
        
        return AIResponse(
            success=True,
            message="Insights generated",
            data=health,
            display='\n'.join(lines),
            suggestions=['Show detailed breakdown', 'Get improvement tips', 'Compare with last month']
        )
    
    def _handle_health(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle health score queries"""
        return self._handle_insight(user_id, query, entities)
    
    def _handle_networth(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle net worth queries"""
        balance = wallet_service.get_total_balance(user_id)
        net_worth = balance['net_worth']
        
        # Calculate historical net worth (simplified)
        now = datetime.now()
        last_month = now - timedelta(days=30)
        
        # Get approximate net worth from 30 days ago
        last_month_income = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) FROM income WHERE user_id = ? AND date >= ?",
            (user_id, last_month.strftime('%Y-%m-%d'))
        )
        last_month_expense = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ? AND date >= ?",
            (user_id, last_month.strftime('%Y-%m-%d'))
        )
        
        income_paise = last_month_income['COALESCE(SUM(amount), 0)'] if last_month_income else 0
        expense_paise = last_month_expense['COALESCE(SUM(amount), 0)'] if last_month_expense else 0
        
        last_month_net = net_worth - (db.to_rupees(income_paise - expense_paise))
        
        change = net_worth - last_month_net
        change_pct = (change / last_month_net * 100) if last_month_net > 0 else 0
        
        lines = [
            f"💎 **Your Net Worth**",
            f"",
            f"**Current:** ₹{net_worth:,.2f}",
            f"",
            f"**30-Day Change:** {'📈' if change >= 0 else '📉'} ₹{abs(change):,.2f} ({change_pct:+.1f}%)",
            f"",
            f"**Breakdown:**",
            f"- Wallet: ₹{balance['wallet']:,.2f}",
            f"- Bank: ₹{balance['bank']:,.2f}",
            f"- Investments: ₹{balance['investments_current']:,.2f}",
        ]
        
        return AIResponse(
            success=True,
            message="Net worth calculated",
            data=balance,
            display='\n'.join(lines),
            suggestions=['Show net worth trend', 'Investment breakdown', 'Get wealth tips']
        )
    
    def _handle_savings(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle savings queries"""
        now = datetime.now()
        
        # Get monthly income and expenses
        month_str = now.strftime('%Y-%m')
        
        income_result = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) FROM income WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, month_str)
        )
        expense_result = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, month_str)
        )
        
        income = db.to_rupees(income_result['COALESCE(SUM(amount), 0)']) if income_result else 0
        expense = db.to_rupees(expense_result['COALESCE(SUM(amount), 0)']) if expense_result else 0
        
        savings = income - expense
        savings_rate = (savings / income * 100) if income > 0 else 0
        
        # Goal contributions
        goals = db.get_user_goals(user_id, status='ACTIVE')
        total_contributions = sum(
            db.to_rupees(g.get('monthly_contribution', 0) or 0) 
            for g in goals
        )
        
        lines = [
            f"💰 **Savings Summary ({now.strftime('%B %Y')})**",
            f"",
            f"**Income:** ₹{income:,.2f}",
            f"**Expenses:** ₹{expense:,.2f}",
            f"**Savings:** ₹{savings:,.2f}",
            f"**Savings Rate:** {savings_rate:.1f}%",
            f"",
            f"**Goal Contributions:** ₹{total_contributions:,.2f}/month",
        ]
        
        if savings_rate >= 20:
            lines.extend(["", "✅ Great job! You're saving 20%+ of your income!"])
        elif savings_rate >= 10:
            lines.extend(["", "⚠️ Good start! Try to increase savings to 20%."])
        else:
            lines.extend(["", "❌ Your savings rate is low. Review your expenses!"])
        
        return AIResponse(
            success=True,
            message="Savings summary retrieved",
            data={
                'income': income,
                'expense': expense,
                'savings': savings,
                'savings_rate': savings_rate,
                'goal_contributions': total_contributions
            },
            display='\n'.join(lines),
            suggestions=['Show spending breakdown', 'Set savings goal', 'Get saving tips']
        )
    
    def _handle_compare(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle comparison queries"""
        now = datetime.now()
        this_month = now.strftime('%Y-%m')
        last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        
        # This month
        this_income = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) FROM income WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, this_month)
        )
        this_expense = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, this_month)
        )
        
        # Last month
        last_income = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) FROM income WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, last_month)
        )
        last_expense = db.execute_one(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE user_id = ? AND strftime('%Y-%m', date) = ?",
            (user_id, last_month)
        )
        
        this_month_income = db.to_rupees(this_income['COALESCE(SUM(amount), 0)']) if this_income else 0
        this_month_expense = db.to_rupees(this_expense['COALESCE(SUM(amount), 0)']) if this_expense else 0
        last_month_income = db.to_rupees(last_income['COALESCE(SUM(amount), 0)']) if last_income else 0
        last_month_expense = db.to_rupees(last_expense['COALESCE(SUM(amount), 0)']) if last_expense else 0
        
        this_month_savings = this_month_income - this_month_expense
        last_month_savings = last_month_income - last_month_expense
        
        lines = [
            f"📊 **Month-over-Month Comparison**",
            f"",
            f"                          This Month    Last Month    Change",
            f"-" * 60,
            f"Income:              ₹{this_month_income:>10,.0f}  ₹{last_month_income:>10,.0f}  {'📈' if this_month_income >= last_month_income else '📉'}",
            f"Expenses:            ₹{this_month_expense:>10,.0f}  ₹{last_month_expense:>10,.0f}  {'📉' if this_month_expense <= last_month_expense else '📈'}",
            f"Savings:             ₹{this_month_savings:>10,.0f}  ₹{last_month_savings:>10,.0f}  {'📈' if this_month_savings >= last_month_savings else '📉'}",
        ]
        
        return AIResponse(
            success=True,
            message="Comparison generated",
            data={
                'this_month': {'income': this_month_income, 'expense': this_month_expense, 'savings': this_month_savings},
                'last_month': {'income': last_month_income, 'expense': last_month_expense, 'savings': last_month_savings}
            },
            display='\n'.join(lines),
            suggestions=['Show detailed breakdown', 'Show category comparison', 'Set monthly targets']
        )
    
    def _handle_forecast(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle forecast queries"""
        now = datetime.now()
        
        # Get last 3 months average
        trend_data = analytics_service.get_income_vs_expense_trend(user_id, 3)
        
        if not trend_data:
            return AIResponse(
                success=True,
                message="No data for forecast",
                data={},
                display="📈 **Insufficient Data**\n\nWe need at least 3 months of transaction history to generate forecasts.",
                suggestions=['Add more transactions', 'Check back later']
            )
        
        avg_income = sum(m['income'] for m in trend_data) / len(trend_data)
        avg_expense = sum(m['expense'] for m in trend_data) / len(trend_data)
        avg_savings = avg_income - avg_expense
        
        # Project for next 3 months
        projected_savings = avg_savings * 3
        
        lines = [
            f"📈 **3-Month Financial Forecast**",
            f"",
            f"**Based on your last 3 months:**",
            f"- Average Monthly Income: ₹{avg_income:,.0f}",
            f"- Average Monthly Expenses: ₹{avg_expense:,.0f}",
            f"- Average Monthly Savings: ₹{avg_savings:,.0f}",
            f"",
            f"**Projected (Next 3 Months):**",
            f"- Expected Savings: ₹{projected_savings:,.0f}",
            f"",
            f"**Recommendations:**",
        ]
        
        if avg_expense > avg_income * 0.8:
            lines.append("⚠️ Your expenses are high relative to income. Consider reducing non-essential spending.")
        elif avg_savings < 0:
            lines.append("⚠️ You're spending more than you earn. Immediate attention needed!")
        else:
            lines.append("✅ Your finances look healthy. Keep up the good work!")
        
        return AIResponse(
            success=True,
            message="Forecast generated",
            data={
                'avg_income': avg_income,
                'avg_expense': avg_expense,
                'avg_savings': avg_savings,
                'projected_savings': projected_savings
            },
            display='\n'.join(lines),
            suggestions=['Set savings goal', 'Create budget', 'Show detailed analysis']
        )
    
    def _handle_help(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle help queries"""
        help_text = """
🤖 **AI Assistant Commands**

**Balance & Net Worth:**
- "Show my balance"
- "How much money do I have?"
- "What's my net worth?"

**Spending & Expenses:**
- "Show my spending this month"
- "How much did I spend on food?"
- "What are my top expenses?"
- "Show last month's expenses"

**Income:**
- "Show my income this month"
- "How much did I earn?"

**Budgets:**
- "Show my budget status"
- "How much budget is left?"

**Investments:**
- "Show my investments"
- "What's my portfolio?"

**Goals:**
- "Show my goals"
- "How much have I saved for vacation?"

**Analysis:**
- "Compare this month vs last month"
- "Show my financial health"
- "Give me financial tips"
- "Forecast my savings"

**Search:**
- "Find my food expenses"
- "Show transactions last week"

Try asking naturally! Examples:
- "How much did I spend on food this month?"
- "Show my investment returns"
- "Am I saving enough?"
"""
        
        return AIResponse(
            success=True,
            message="Help displayed",
            data={},
            display=help_text,
            suggestions=['Ask a question', 'Show my balance', 'Analyze my spending']
        )
    
    def _handle_unknown(self, user_id: int, query: str, entities: Dict) -> AIResponse:
        """Handle unknown queries"""
        suggestions = [
            "Show my balance",
            "Show my spending",
            "Show my budget",
            "Give me tips",
            "Show my investments"
        ]
        
        return AIResponse(
            success=True,
            message="Query not understood",
            data={'query': query},
            display=f"""
🤔 **I didn't understand that**

You asked: "{query}"

I can help you with:
- Balance and net worth
- Income and expenses
- Budgets and goals
- Investments
- Financial analysis
- Savings tips

Try asking: "Show my balance" or "How much did I spend this month?"
""",
            suggestions=suggestions
        )
    
    def _generate_personalized_tips(self, user_id: int) -> List[str]:
        """Generate personalized financial tips"""
        tips = []
        now = datetime.now()
        
        try:
            # Get user data
            summary = wallet_service.get_monthly_summary(user_id)
            budgets = analytics_service.get_budget_status(user_id, now.year, now.month)
            categories = wallet_service.get_category_breakdown(user_id)
            health = analytics_service.calculate_financial_health_score(user_id)
            
            # Savings tip
            if summary['savings_rate'] < 20:
                tips.append(f"Your savings rate is {summary['savings_rate']:.1f}%. Try to save at least 20% of your income.")
            else:
                tips.append(f"Great job! You're saving {summary['savings_rate']:.1f}% of your income. Keep it up!")
            
            # Budget tips
            over_budget = [b for b in budgets if b['status'] == 'EXCEEDED']
            if over_budget:
                cats = ', '.join(b['category'] for b in over_budget[:3])
                tips.append(f"You've exceeded your budget in: {cats}. Review these categories for savings.")
            
            # High spending category tip
            if categories and categories[0]['percentage'] > 40:
                tips.append(f"{categories[0]['category']} takes {categories[0]['percentage']:.1f}% of your spending. Consider alternatives.")
            
            # Emergency fund tip
            balance = wallet_service.get_total_balance(user_id)
            if balance['wallet'] + balance['bank'] < summary['total_expense'] * 3:
                tips.append("Build an emergency fund covering 3-6 months of expenses.")
            
            # Investment tip
            if balance['investments_current'] == 0:
                tips.append("Start investing early! Even small amounts grow over time with compound interest.")
            
            # Financial health tip
            if health['score'] < 60:
                tips.append(f"Your financial health score is {health['score']}/100. Focus on improving savings and reducing debt.")
            else:
                tips.append(f"Excellent financial health score of {health['score']}/100! You're on the right track.")
            
            # General tips
            general_tips = [
                "Track every expense, no matter how small.",
                "Review subscriptions monthly and cancel unused ones.",
                "Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
                "Automate your savings by setting up recurring transfers.",
                "Set specific, measurable financial goals.",
                "Review your investments quarterly and rebalance as needed.",
                "Avoid high-interest debt like credit card balances.",
                "Consider tax-saving investments for better returns.",
            ]
            
            import random
            tips.extend(random.sample(general_tips, min(3, len(general_tips))))
            
        except Exception as e:
            tips = [
                "Track your daily expenses to understand spending patterns.",
                "Set a monthly savings target and stick to it.",
                "Review your subscriptions and cancel unused ones.",
                "Automate your savings on payday.",
                "Build an emergency fund with 3-6 months of expenses.",
            ]
        
        return tips
    
    def _save_conversation(self, user_id: int, query: str, response: AIResponse):
        """Save conversation to database"""
        try:
            conversation = {
                'query': query,
                'response': response.message,
                'success': response.success,
                'timestamp': datetime.now().isoformat()
            }
            
            existing = db.execute_one(
                "SELECT conversation_id FROM ai_conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
                (user_id,)
            )
            
            if existing:
                messages = []
            else:
                messages = []
            
            # This would typically append to existing messages
            # For simplicity, we're just noting the conversation
        except Exception:
            pass  # Silently fail on conversation logging


# Singleton instance
enhanced_ai_assistant = EnhancedAIAssistant()
