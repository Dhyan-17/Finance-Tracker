"""
AI Assistant Service
Natural language financial assistant with smart insights
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from database.db import db
from services.wallet_service import wallet_service
from services.analytics_service import analytics_service


class AIAssistant:
    """AI-powered financial assistant"""
    
    def __init__(self):
        self.commands = {
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
        }
        
        # Pattern matchers for natural language
        self.patterns = [
            (r'(show|what|how much).*(balance|money|have)', 'balance'),
            (r'(show|get|list).*(expense|spending|spent)', 'expense'),
            (r'(show|get|list).*(income|earned|salary)', 'income'),
            (r'(show|get).*(budget|limit)', 'budget'),
            (r'(show|get|list).*(investment|portfolio|stock|crypto)', 'investment'),
            (r'(show|get|list).*(goal|target|saving for)', 'goal'),
            (r'(transfer|send|pay).*(money|₹|\d+)', 'transfer'),
            (r'(find|search|show).*(transaction)', 'search'),
            (r'(tip|advice|suggest|recommend)', 'tip'),
            (r'(insight|analysis|analyze)', 'insight'),
            (r'(help|what can you do|commands)', 'help'),
            (r'top.*(expense|spending)', 'expense'),
            (r'(food|grocery|transport|shopping|bills).*(expense|spending|spent)', 'expense'),
            (r'(last|this) month.*(expense|spending|income)', 'spending'),
        ]
    
    def process_query(self, user_id: int, query: str) -> Dict:
        """Process a natural language query using Ollama"""
        try:
            # Get user context
            user_data = db.get_user_by_id(user_id)
            if not user_data:
                return {
                    'success': False,
                    'message': 'User not found',
                    'response': 'Unable to process query - user data not available'
                }

            # Get financial context
            balance = user_data['wallet_balance']
            recent_expenses = db.get_user_expenses(user_id, limit=5)
            recent_income = db.get_user_income(user_id, limit=5)

            # Build context for Ollama
            context = f"""
            User Financial Context:
            - Current Wallet Balance: ₹{balance}
            - Recent Expenses: {len(recent_expenses)} transactions
            - Recent Income: {len(recent_income)} transactions

            User Query: {query}

            Please provide helpful financial advice based on the user's context and query.
            Be concise but informative. Use Indian Rupees (₹) for currency.
            """

            # Call Ollama API
            ollama_response = self._call_ollama(context)

            if not ollama_response:
                return {
                    'success': False,
                    'message': 'AI service unavailable',
                    'response': 'Sorry, the AI assistant is currently unavailable. Please try again later.'
                }

            response = ollama_response.strip()

            # Store conversation
            self._store_conversation(user_id, query, response)

            return {
                'success': True,
                'message': 'Query processed successfully',
                'response': response
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing query: {str(e)}',
                'response': 'Sorry, I encountered an error while processing your query. Please try again.'
            }

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama API for AI response"""
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "llama2",  # or any available model
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 200
                }
            }

            response = requests.post(url, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                print(f"Ollama API error: {response.status_code} - {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Ollama connection error: {e}")
            return None
        except Exception as e:
            print(f"Ollama error: {e}")
            return None

    def _store_conversation(self, user_id: int, query: str, response: str):
        """Store conversation in database"""
        try:
            message = {
                'timestamp': datetime.now().isoformat(),
                'query': query,
                'response': response
            }

            # Check if conversation exists
            existing = db.execute(
                "SELECT conversation_id, messages FROM ai_conversations WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
                (user_id,),
                fetch=True,
                single=True
            )

            if existing:
                messages = json.loads(existing['messages'])
                messages.append(message)
                # Keep last 50 messages
                messages = messages[-50:]

                db.execute(
                    """UPDATE ai_conversations
                       SET messages = ?, updated_at = datetime('now')
                       WHERE conversation_id = ?""",
                    (json.dumps(messages), existing['conversation_id'])
                )
            else:
                db.execute_insert(
                    "INSERT INTO ai_conversations (user_id, messages) VALUES (?, ?)",
                    (user_id, json.dumps([message]))
                )
        except Exception as e:
            print(f"Error storing conversation: {e}")
    
    def _detect_intent(self, query: str) -> Optional[str]:
        """Detect the intent of the query"""
        for pattern, intent in self.patterns:
            if re.search(pattern, query):
                return intent
        return None
    
    def _extract_entities(self, query: str) -> Dict:
        """Extract entities from query"""
        entities = {}
        
        # Extract amount
        amount_match = re.search(r'₹?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', query)
        if amount_match:
            entities['amount'] = float(amount_match.group(1).replace(',', ''))
        
        # Extract time period
        if 'last month' in query:
            entities['period'] = 'last_month'
        elif 'this month' in query:
            entities['period'] = 'this_month'
        elif 'this week' in query:
            entities['period'] = 'this_week'
        elif 'today' in query:
            entities['period'] = 'today'
        elif 'last year' in query:
            entities['period'] = 'last_year'
        elif 'this year' in query:
            entities['period'] = 'this_year'
        
        # Extract category
        categories = ['food', 'transport', 'shopping', 'entertainment', 'bills', 
                     'healthcare', 'education', 'travel', 'groceries', 'personal']
        for cat in categories:
            if cat in query:
                entities['category'] = cat.title()
                break
        
        # Extract top N
        top_match = re.search(r'top\s*(\d+)', query)
        if top_match:
            entities['top_n'] = int(top_match.group(1))
        
        return entities
    
    def _get_period_dates(self, period: str) -> Tuple[str, str]:
        """Get date range for a period"""
        now = datetime.now()
        
        if period == 'today':
            start = end = now.strftime('%Y-%m-%d')
        elif period == 'this_week':
            start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
            end = now.strftime('%Y-%m-%d')
        elif period == 'this_month':
            start = now.strftime('%Y-%m-01')
            end = now.strftime('%Y-%m-%d')
        elif period == 'last_month':
            last_month = now.replace(day=1) - timedelta(days=1)
            start = last_month.strftime('%Y-%m-01')
            end = last_month.strftime('%Y-%m-%d')
        elif period == 'this_year':
            start = now.strftime('%Y-01-01')
            end = now.strftime('%Y-%m-%d')
        elif period == 'last_year':
            start = f"{now.year - 1}-01-01"
            end = f"{now.year - 1}-12-31"
        else:
            start = now.strftime('%Y-%m-01')
            end = now.strftime('%Y-%m-%d')
        
        return start, end
    
    # ============================================================
    # COMMAND HANDLERS
    # ============================================================
    
    def _handle_balance(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle balance queries"""
        balance = wallet_service.get_total_balance(user_id)
        
        return {
            'type': 'balance',
            'message': f"Here's your balance summary:",
            'data': {
                'wallet': balance['wallet'],
                'bank': balance['bank'],
                'investments': balance['investments_current'],
                'investment_pl': balance['investments_pl'],
                'net_worth': balance['net_worth']
            },
            'display': f"""
💰 **Your Balance Summary**

- Wallet: ₹{balance['wallet']:,.2f}
- Bank Accounts: ₹{balance['bank']:,.2f}
- Investments: ₹{balance['investments_current']:,.2f} ({'+' if balance['investments_pl'] >= 0 else ''}₹{balance['investments_pl']:,.2f})
- **Net Worth: ₹{balance['net_worth']:,.2f}**
""",
            'suggestions': ['Show my spending this month', 'Show budget status', 'Give me saving tips']
        }
    
    def _handle_spending(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle spending queries"""
        period = entities.get('period', 'this_month')
        start, end = self._get_period_dates(period)
        
        expenses = db.get_user_expenses(user_id, start_date=start, end_date=end, limit=100)
        
        total = sum(db.to_rupees(e['amount']) for e in expenses)
        categories = {}
        
        for e in expenses:
            cat = e['category']
            categories[cat] = categories.get(cat, 0) + db.to_rupees(e['amount'])
        
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
        
        period_label = period.replace('_', ' ').title()
        
        display_lines = [f"📊 **Your Spending ({period_label})**\n"]
        display_lines.append(f"**Total: ₹{total:,.2f}**\n")
        display_lines.append("Top Categories:")
        
        for cat, amount in sorted_cats:
            pct = (amount / total * 100) if total > 0 else 0
            display_lines.append(f"- {cat}: ₹{amount:,.2f} ({pct:.1f}%)")
        
        return {
            'type': 'spending',
            'message': f"Here's your spending summary for {period_label.lower()}:",
            'data': {
                'total': total,
                'categories': dict(sorted_cats),
                'count': len(expenses)
            },
            'display': '\n'.join(display_lines),
            'suggestions': ['Show top expenses', 'Show budget status', 'Compare with last month']
        }
    
    def _handle_expense(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle expense queries"""
        now = datetime.now()
        category = entities.get('category')
        top_n = entities.get('top_n', 10)
        
        if category:
            # Show expenses for specific category
            expenses = db.execute(
                """SELECT * FROM expenses 
                   WHERE user_id = ? AND category = ? 
                   ORDER BY date DESC LIMIT ?""",
                (user_id, category, top_n),
                fetch=True
            )
            title = f"📝 **{category} Expenses**"
        else:
            # Show top expenses
            expenses = analytics_service.get_top_expenses(user_id, now.year, now.month, top_n)
            title = f"📝 **Top {top_n} Expenses This Month**"
        
        display_lines = [title, ""]
        
        for i, e in enumerate(expenses, 1):
            if isinstance(e, dict) and 'amount' in e:
                amount = e['amount'] if isinstance(e['amount'], float) else db.to_rupees(e['amount'])
                desc = e.get('description', e.get('category', 'N/A'))
                date_str = e.get('date', '')[:10]
                display_lines.append(f"{i}. ₹{amount:,.2f} - {desc} ({date_str})")
        
        return {
            'type': 'expense',
            'message': 'Here are your expenses:',
            'data': {'expenses': expenses},
            'display': '\n'.join(display_lines),
            'suggestions': ['Show spending by category', 'Show budget status', 'Add expense']
        }
    
    def _handle_income(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle income queries"""
        period = entities.get('period', 'this_month')
        start, end = self._get_period_dates(period)
        
        income_list = db.get_user_income(user_id, start_date=start, end_date=end)
        
        total = sum(db.to_rupees(i['amount']) for i in income_list)
        sources = {}
        
        for i in income_list:
            src = i['source']
            sources[src] = sources.get(src, 0) + db.to_rupees(i['amount'])
        
        period_label = period.replace('_', ' ').title()
        
        display_lines = [f"💵 **Your Income ({period_label})**\n"]
        display_lines.append(f"**Total: ₹{total:,.2f}**\n")
        display_lines.append("Sources:")
        
        for src, amount in sorted(sources.items(), key=lambda x: x[1], reverse=True):
            display_lines.append(f"- {src}: ₹{amount:,.2f}")
        
        return {
            'type': 'income',
            'message': f"Here's your income summary for {period_label.lower()}:",
            'data': {
                'total': total,
                'sources': sources,
                'count': len(income_list)
            },
            'display': '\n'.join(display_lines),
            'suggestions': ['Compare income vs expense', 'Show savings rate', 'Add income']
        }
    
    def _handle_budget(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle budget queries"""
        now = datetime.now()
        budgets = analytics_service.get_budget_status(user_id, now.year, now.month)
        
        if not budgets:
            return {
                'type': 'budget',
                'message': "You haven't set any budgets yet.",
                'data': {'budgets': []},
                'display': "📋 **No budgets set**\n\nSet budgets to track your spending limits!",
                'suggestions': ['Set budget for Food ₹10000', 'Set budget for Transport ₹5000']
            }
        
        display_lines = [f"📋 **Budget Status ({now.strftime('%B %Y')})**\n"]
        
        for b in budgets:
            status_icon = '✅' if b['status'] == 'ON_TRACK' else '⚠️' if b['status'] == 'WARNING' else '❌'
            display_lines.append(f"{status_icon} **{b['category']}**")
            display_lines.append(f"   ₹{b['spent']:,.2f} / ₹{b['limit']:,.2f} ({b['percentage']:.1f}%)")
            display_lines.append(f"   Remaining: ₹{b['remaining']:,.2f}\n")
        
        return {
            'type': 'budget',
            'message': 'Here is your budget status:',
            'data': {'budgets': budgets},
            'display': '\n'.join(display_lines),
            'suggestions': ['Show spending by category', 'Update budget', 'Get saving tips']
        }
    
    def _handle_investment(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle investment queries"""
        from services.investment_service import investment_service
        
        portfolio = investment_service.get_portfolio(user_id)
        
        if not portfolio['holdings']:
            return {
                'type': 'investment',
                'message': "You don't have any investments yet.",
                'data': portfolio,
                'display': "📈 **No Investments**\n\nStart investing to grow your wealth!",
                'suggestions': ['Show market overview', 'Buy stocks', 'Buy crypto']
            }
        
        display_lines = [f"📈 **Your Investment Portfolio**\n"]
        display_lines.append(f"**Total Invested:** ₹{portfolio['total_invested']:,.2f}")
        display_lines.append(f"**Current Value:** ₹{portfolio['current_value']:,.2f}")
        pl_sign = '+' if portfolio['total_profit_loss'] >= 0 else ''
        display_lines.append(f"**Profit/Loss:** {pl_sign}₹{portfolio['total_profit_loss']:,.2f} ({pl_sign}{portfolio['profit_loss_percent']:.2f}%)\n")
        
        display_lines.append("**Holdings:**")
        for h in portfolio['holdings'][:5]:
            pl_sign = '+' if h['profit_loss'] >= 0 else ''
            display_lines.append(f"- {h['asset_symbol']}: {h['units_owned']:.4f} units @ ₹{h['current_price']:,.2f}")
            display_lines.append(f"  Value: ₹{h['current_value']:,.2f} ({pl_sign}{h['profit_loss_percent']:.2f}%)")
        
        return {
            'type': 'investment',
            'message': 'Here is your investment portfolio:',
            'data': portfolio,
            'display': '\n'.join(display_lines),
            'suggestions': ['Show market overview', 'Buy more', 'Sell investment']
        }
    
    def _handle_goal(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle financial goals queries"""
        goals = db.get_user_goals(user_id, status='ACTIVE')
        
        if not goals:
            return {
                'type': 'goal',
                'message': "You haven't set any financial goals yet.",
                'data': {'goals': []},
                'display': "🎯 **No Active Goals**\n\nSet goals to stay motivated!",
                'suggestions': ['Create goal for Emergency Fund ₹100000', 'Create goal for Vacation ₹50000']
            }
        
        display_lines = ["🎯 **Your Financial Goals**\n"]
        
        for g in goals:
            target = db.to_rupees(g['target_amount'])
            current = db.to_rupees(g['current_savings'])
            progress = (current / target * 100) if target > 0 else 0
            
            display_lines.append(f"**{g['goal_name']}** ({g['priority']} Priority)")
            display_lines.append(f"   Progress: ₹{current:,.2f} / ₹{target:,.2f} ({progress:.1f}%)")
            if g['target_date']:
                display_lines.append(f"   Target: {g['target_date']}")
            display_lines.append("")
        
        return {
            'type': 'goal',
            'message': 'Here are your financial goals:',
            'data': {'goals': goals},
            'display': '\n'.join(display_lines),
            'suggestions': ['Add to goal', 'Create new goal', 'Show saving tips']
        }
    
    def _handle_transfer(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle transfer queries (informational only)"""
        return {
            'type': 'transfer',
            'message': "To transfer money, use the Transfer feature in the wallet section.",
            'data': {},
            'display': "💸 **Transfer Money**\n\nGo to Wallet → Transfer to send money to another user.",
            'suggestions': ['Show my balance', 'Show recent transactions']
        }
    
    def _handle_transaction(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle transaction history queries"""
        return self._handle_search(user_id, query, entities)
    
    def _handle_search(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle search queries"""
        category = entities.get('category')
        period = entities.get('period', 'this_month')
        start, end = self._get_period_dates(period)
        
        expenses = db.get_user_expenses(user_id, start_date=start, end_date=end, category=category, limit=20)
        
        display_lines = ["🔍 **Search Results**\n"]
        
        if not expenses:
            display_lines.append("No transactions found matching your criteria.")
        else:
            for e in expenses:
                amount = db.to_rupees(e['amount'])
                display_lines.append(f"- {e['date'][:10]} | {e['category']} | ₹{amount:,.2f}")
                if e['description']:
                    display_lines.append(f"  _{e['description']}_")
        
        return {
            'type': 'search',
            'message': 'Search results:',
            'data': {'transactions': expenses},
            'display': '\n'.join(display_lines),
            'suggestions': ['Show spending by category', 'Filter by date']
        }
    
    def _handle_tip(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle saving tips and advice"""
        # Generate personalized tips based on user data
        tips = self._generate_personalized_tips(user_id)
        
        display_lines = ["💡 **Financial Tips for You**\n"]
        
        for i, tip in enumerate(tips[:5], 1):
            display_lines.append(f"{i}. {tip}")
        
        return {
            'type': 'tip',
            'message': 'Here are some personalized tips:',
            'data': {'tips': tips},
            'display': '\n'.join(display_lines),
            'suggestions': ['Show my budget', 'Analyze my spending', 'Show financial health score']
        }
    
    def _generate_personalized_tips(self, user_id: int) -> List[str]:
        """Generate personalized financial tips"""
        tips = []
        now = datetime.now()
        
        # Get user data
        summary = wallet_service.get_monthly_summary(user_id)
        budgets = analytics_service.get_budget_status(user_id, now.year, now.month)
        categories = wallet_service.get_category_breakdown(user_id)
        
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
        
        # General tips
        general_tips = [
            "Track every expense, no matter how small.",
            "Review subscriptions monthly and cancel unused ones.",
            "Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
            "Automate your savings by setting up recurring transfers.",
            "Set specific, measurable financial goals.",
        ]
        
        import random
        tips.extend(random.sample(general_tips, min(2, len(general_tips))))
        
        return tips
    
    def _handle_insight(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle insight and analysis queries"""
        health = analytics_service.calculate_financial_health_score(user_id)
        
        display_lines = [f"📊 **Financial Health Analysis**\n"]
        display_lines.append(f"**Overall Score: {health['score']}/100** ({health['rating']})\n")
        display_lines.append("**Breakdown:**")
        
        for key, data in health['breakdown'].items():
            label = key.replace('_', ' ').title()
            display_lines.append(f"- {label}: {data['score']}/{data['max']} points")
        
        # Add recommendations
        display_lines.append("\n**Recommendations:**")
        if health['breakdown']['savings_rate']['score'] < 20:
            display_lines.append("• Increase your savings rate")
        if health['breakdown']['investment_diversity']['score'] < 10:
            display_lines.append("• Diversify your investments")
        if health['breakdown']['emergency_fund']['score'] < 15:
            display_lines.append("• Build your emergency fund")
        
        return {
            'type': 'insight',
            'message': 'Here is your financial analysis:',
            'data': health,
            'display': '\n'.join(display_lines),
            'suggestions': ['Show saving tips', 'Show budget status', 'Show investment portfolio']
        }
    
    def _handle_help(self, user_id: int, query: str, entities: Dict) -> Dict:
        """Handle help queries"""
        return {
            'type': 'help',
            'message': 'Here\'s what I can help you with:',
            'data': {},
            'display': """
🤖 **AI Assistant Help**

I can help you with:

**💰 Balance & Money**
- "Show my balance"
- "What's my net worth?"

**📊 Spending & Expenses**
- "Show my spending this month"
- "Top 10 expenses"
- "Food expenses last month"

**💵 Income**
- "Show my income this month"
- "Compare income vs expense"

**📋 Budget**
- "Show my budget status"
- "Am I over budget?"

**📈 Investments**
- "Show my portfolio"
- "How are my investments?"

**🎯 Goals**
- "Show my goals"
- "Goal progress"

**💡 Tips & Insights**
- "Give me saving tips"
- "Analyze my finances"
- "Financial health score"

Just type naturally and I'll understand!
""",
            'suggestions': ['Show my balance', 'Give me tips', 'Analyze my finances']
        }
    
    def _handle_unknown(self, user_id: int, query: str) -> Dict:
        """Handle unknown queries"""
        return {
            'type': 'unknown',
            'message': "I'm not sure what you're asking. Here's what I can help with:",
            'data': {},
            'display': f"""
🤔 I didn't quite understand "{query}".

Try asking things like:
- "Show my balance"
- "How much did I spend this month?"
- "Show my budget status"
- "Give me saving tips"

Type "help" to see all commands.
""",
            'suggestions': ['Show my balance', 'Help', 'Show spending']
        }
    
    def _save_conversation(self, user_id: int, query: str, response: Dict):
        """Save conversation to database"""
        import json
        
        # Get existing conversation or create new
        existing = db.execute_one(
            """SELECT conversation_id, messages FROM ai_conversations 
               WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1""",
            (user_id,)
        )
        
        message = {
            'timestamp': db.now(),
            'query': query,
            'response_type': response['type'],
            'response_message': response['message']
        }
        
        if existing:
            messages = json.loads(existing['messages'])
            messages.append(message)
            # Keep last 50 messages
            messages = messages[-50:]
            
            db.execute(
                """UPDATE ai_conversations 
                   SET messages = ?, updated_at = datetime('now')
                   WHERE conversation_id = ?""",
                (json.dumps(messages), existing['conversation_id'])
            )
        else:
            db.execute_insert(
                "INSERT INTO ai_conversations (user_id, messages) VALUES (?, ?)",
                (user_id, json.dumps([message]))
            )
    
    def get_quick_insights(self, user_id: int) -> List[Dict]:
        """Get quick insights for dashboard"""
        insights = []
        now = datetime.now()
        
        # Check budget status
        budgets = analytics_service.get_budget_status(user_id, now.year, now.month)
        over_budget = [b for b in budgets if b['status'] == 'EXCEEDED']
        if over_budget:
            insights.append({
                'type': 'WARNING',
                'title': 'Budget Alert',
                'message': f"You've exceeded budget in {len(over_budget)} categories",
                'icon': '⚠️'
            })
        
        # Check spending trend
        current_spending = wallet_service.get_monthly_summary(user_id)
        if now.day > 15 and current_spending['total_expense'] > current_spending['total_income'] * 0.8:
            insights.append({
                'type': 'INFO',
                'title': 'Spending Alert',
                'message': 'High spending relative to income this month',
                'icon': '📊'
            })
        
        # Check savings rate
        if current_spending['savings_rate'] < 10:
            insights.append({
                'type': 'TIP',
                'title': 'Saving Tip',
                'message': 'Try to save at least 20% of your income',
                'icon': '💡'
            })
        
        # Positive insight
        if current_spending['savings_rate'] > 30:
            insights.append({
                'type': 'SUCCESS',
                'title': 'Great Savings!',
                'message': f"You're saving {current_spending['savings_rate']:.1f}% this month!",
                'icon': '🎉'
            })
        
        return insights[:4]  # Max 4 insights


# Singleton instance
ai_assistant = AIAssistant()
