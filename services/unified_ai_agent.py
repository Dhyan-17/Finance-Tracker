"""
Unified AI Agent for Fintech
Single intelligent AI system handling chat, actions, navigation, and insights
"""

import re
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import streamlit as st

from database.db import db
from services.wallet_service import wallet_service
from services.analytics_service import analytics_service


# ============================================================
# ENUMS & DATA CLASSES
# ============================================================

class ActionType(Enum):
    """AI action types"""
    QUERY = "QUERY"
    NAVIGATE = "NAVIGATE"
    TRANSACTION = "TRANSACTION"
    BUDGET = "BUDGET"
    INVESTMENT = "INVESTMENT"
    TRANSFER = "TRANSFER"
    INSIGHT = "INSIGHT"
    TIP = "TIP"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CONFIRMATION = "CONFIRMATION"


@dataclass
class AIResponse:
    """Structured AI response"""
    success: bool
    message: str
    action: Optional['AIAction'] = None
    data: Dict = field(default_factory=dict)
    display: str = ""
    suggestions: List[str] = field(default_factory=list)
    error: Optional[str] = None
    navigate_to: Optional[str] = None


@dataclass
class AIAction:
    """AI action to perform"""
    action_type: ActionType
    target: str
    parameters: Dict = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    on_confirm: Optional[Callable] = None


# ============================================================
# UNIFIED AI AGENT
# ============================================================

class UnifiedAIAgent:
    """
    Unified AI Agent for Fintech
    
    Combines chat, copilot, navigation, and insights into one system.
    Handles all AI interactions with proper error handling.
    """
    
    def __init__(self):
        self._setup_mappings()
        self._setup_patterns()
        self._setup_aliases()
    
    def _setup_mappings(self):
        """Setup page navigation mappings"""
        self.page_map = {
            'dashboard': 'dashboard',
            'home': 'dashboard',
            'wallet': 'wallet',
            'transactions': 'transactions',
            'expenses': 'transactions',
            'income': 'transactions',
            'budget': 'budget',
            'budgets': 'budget',
            'invest': 'investments',
            'investments': 'investments',
            'portfolio': 'investments',
            'goal': 'goals',
            'goals': 'goals',
            'savings': 'goals',
            'analytics': 'user_analytics',
            'reports': 'user_analytics',
            'settings': 'settings',
            'profile': 'settings',
            'admin': 'admin_dashboard',
        }
    
    def _setup_patterns(self):
        """Setup intent and action patterns"""
        # Intent patterns
        self.intent_patterns = [
            (r'(?:go to|open|show|view|navigate to|launch)\s+(?:the\s+)?(\w+)', 'NAVIGATE'),
            (r'(?:show|what|how much|check|get|tell me).*(?:balance|wallet|money|funds)', 'BALANCE'),
            (r'(?:show|what|how much|spending|spent|expenses)', 'SPENDING'),
            (r'(?:show|what|how much|income|earned|salary)', 'INCOME'),
            (r'(?:transaction|recent|last|payment|purchase)', 'TRANSACTION'),
            (r'(?:budget|spending limit|limit)', 'BUDGET'),
            (r'(?:invest|investment|portfolio|stocks?|crypto|mf|mutual fund)', 'INVESTMENT'),
            (r'(?:transfer|send|pay|move)', 'TRANSFER'),
            (r'(?:goal|target|saving|save for)', 'GOAL'),
            (r'(?:help|what can you do|commands|guide)', 'HELP'),
            (r'(?:insight|tip|advice|recommend|suggest)', 'INSIGHT'),
            (r'(?:analyze|analysis|health|score|compare)', 'ANALYSIS'),
            (r'(?:forecast|predict|future|projection)', 'FORECAST'),
        ]
        
        # Action patterns
        self.action_patterns = [
            (r'(?:add|record|log|create)\s+(?:an?\s+)?(?:expense|spending|purchase|payment)', 'ADD_EXPENSE'),
            (r'spend\s+(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', 'ADD_EXPENSE'),
            (r'(?:add|record|log|receive)\s+(?:an?\s+)?(?:income|salary|earning|payment)', 'ADD_INCOME'),
            (r'(?:received|got|earned)\s+(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', 'ADD_INCOME'),
            (r'(?:transfer|send|pay)\s+(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', 'TRANSFER'),
            (r'(?:invest|buy|purchase)\s+(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', 'INVEST'),
            (r'(?:set|create|make)\s+(?:a\s+)?budget', 'SET_BUDGET'),
            (r'(?:withdraw|cash out|take out)', 'WITHDRAW'),
            (r'(?:deposit|add money|put money)', 'DEPOSIT'),
        ]
    
    def _setup_aliases(self):
        """Setup category aliases"""
        self.category_aliases = {
            'food': 'Food & Dining', 'restaurant': 'Food & Dining',
            'grocery': 'Groceries', 'groceries': 'Groceries',
            'transport': 'Transportation', 'uber': 'Transportation',
            'ola': 'Transportation', 'taxi': 'Transportation',
            'fuel': 'Transportation', 'petrol': 'Transportation',
            'shopping': 'Shopping', 'amazon': 'Shopping', 'flipkart': 'Shopping',
            'bills': 'Bills & Utilities', 'electricity': 'Bills & Utilities',
            'water': 'Bills & Utilities', 'gas': 'Bills & Utilities',
            'mobile': 'Bills & Utilities', 'recharge': 'Bills & Utilities',
            'entertainment': 'Entertainment', 'movies': 'Entertainment',
            'netflix': 'Entertainment',
            'healthcare': 'Healthcare', 'hospital': 'Healthcare',
            'medicine': 'Healthcare', 'pharmacy': 'Healthcare',
            'education': 'Education', 'course': 'Education',
            'tuition': 'Education',
            'travel': 'Travel', 'flight': 'Travel',
            'hotel': 'Travel', 'train': 'Travel',
            'personal': 'Personal Care', 'salon': 'Personal Care',
        }
        
        self.investment_assets = {
            'bitcoin': 'BTC', 'btc': 'BTC',
            'ethereum': 'ETH', 'eth': 'ETH',
            'solana': 'SOL', 'sol': 'SOL',
            'reliance': 'RELIANCE', 'tcs': 'TCS',
            'infosys': 'INFY', 'hdfc': 'HDFCBANK',
            'icici': 'ICICIBANK', 'gold': 'GOLD',
            'mutual fund': 'MUTUAL_FUND', 'sip': 'MUTUAL_FUND',
        }
    
    # ============================================================
    # MAIN PROCESSING
    # ============================================================
    
    def process_query(
        self,
        user_id: int,
        query: str,
        context: Optional[Dict] = None,
        require_confirmation: bool = True
    ) -> AIResponse:
        """
        Process user query with unified AI
        
        Args:
            user_id: User ID
            query: User query
            context: Current context
            require_confirmation: Whether to require confirmation for actions
            
        Returns:
            AIResponse with result and potential action
        """
        try:
            # Clean query
            clean_query = query.lower().strip()
            
            # Detect intent
            intent = self._detect_intent(clean_query)
            
            # Detect action
            action_result = self._detect_action(clean_query, user_id, require_confirmation)
            
            if action_result:
                return action_result
            
            # Handle by intent
            return self._handle_intent(user_id, intent, clean_query)
            
        except Exception as e:
            return self._handle_error(e, user_id, query)
    
    # ============================================================
    # INTENT & ACTION DETECTION
    # ============================================================
    
    def _detect_intent(self, query: str) -> str:
        """Detect user intent from query"""
        for pattern, intent in self.intent_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return intent
        return 'UNKNOWN'
    
    def _detect_action(
        self,
        query: str,
        user_id: int,
        require_confirmation: bool
    ) -> Optional[AIResponse]:
        """Detect and handle actionable queries"""
        for pattern, action_type in self.action_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if action_type == 'ADD_EXPENSE':
                    return self._handle_add_expense(query, user_id, require_confirmation)
                elif action_type == 'ADD_INCOME':
                    return self._handle_add_income(query, user_id, require_confirmation)
                elif action_type == 'TRANSFER':
                    return self._handle_transfer(query, user_id, require_confirmation)
                elif action_type == 'INVEST':
                    return self._handle_invest(query, user_id, require_confirmation)
                elif action_type == 'SET_BUDGET':
                    return self._handle_set_budget(query, user_id, require_confirmation)
                elif action_type == 'WITHDRAW':
                    return self._handle_withdraw(query, user_id, require_confirmation)
                elif action_type == 'DEPOSIT':
                    return self._handle_deposit(query, user_id, require_confirmation)
        return None
    
    # ============================================================
    # ACTION HANDLERS
    # ============================================================
    
    def _handle_add_expense(
        self,
        query: str,
        user_id: int,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle adding expense"""
        try:
            # Extract amount
            amount_match = re.search(
                r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
                query, re.IGNORECASE
            )
            
            if not amount_match:
                return AIResponse(
                    success=False,
                    message="Amount not found",
                    display="❓ **Amount Required**\n\nPlease specify how much you spent.\n\nExample: 'Add expense of ₹500'",
                    suggestions=["Add expense of ₹500", "Record ₹1000 spending", "Log ₹2500 purchase"]
                )
            
            amount = float(amount_match.group(1).replace(',', ''))
            
            # Extract category
            category = 'Others'
            for alias, cat in self.category_aliases.items():
                if alias in query.lower():
                    category = cat
                    break
            
            # Create action
            requires_confirmation = require_confirmation and amount > 1000
            
            action = AIAction(
                action_type=ActionType.TRANSACTION,
                target="add_expense",
                parameters={
                    'amount': amount,
                    'category': category,
                    'description': f"Added via AI",
                },
                requires_confirmation=requires_confirmation,
                confirmation_message=f"Add expense of ₹{amount:,.2f} for {category}?",
            )
            
            display = f"""
💸 **Add Expense**
- Amount: ₹{amount:,.2f}
- Category: {category}
"""
            
            return AIResponse(
                success=True,
                message="Ready to add expense",
                action=action,
                display=display,
                suggestions=[f"Add ₹{amount} for {category}", "Change category", "Cancel"]
            )
            
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_add_income(
        self,
        query: str,
        user_id: int,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle adding income"""
        try:
            amount_match = re.search(
                r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
                query, re.IGNORECASE
            )
            
            if not amount_match:
                return AIResponse(
                    success=False,
                    message="Amount not found",
                    display="❓ **Amount Required**\n\nPlease specify how much you received.",
                    suggestions=["Add income of ₹50000", "Record salary of ₹75000", "Log ₹10000 received"]
                )
            
            amount = float(amount_match.group(1).replace(',', ''))
            
            # Determine source
            source = 'Salary'
            if 'salary' in query.lower():
                source = 'Salary'
            elif 'freelance' in query.lower():
                source = 'Freelance'
            elif 'business' in query.lower():
                source = 'Business'
            elif 'gift' in query.lower():
                source = 'Gift'
            
            action = AIAction(
                action_type=ActionType.TRANSACTION,
                target="add_income",
                parameters={'amount': amount, 'source': source},
                requires_confirmation=False,
                confirmation_message=f"Add income of ₹{amount:,.2f}?",
            )
            
            display = f"""
💰 **Add Income**
- Amount: ₹{amount:,.2f}
- Source: {source}
"""
            
            return AIResponse(
                success=True,
                message="Ready to add income",
                action=action,
                display=display,
                suggestions=[f"Add ₹{amount} from {source}", "Change source", "Cancel"]
            )
            
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_transfer(
        self,
        query: str,
        user_id: int,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle transfer"""
        try:
            amount_match = re.search(
                r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
                query, re.IGNORECASE
            )
            
            if not amount_match:
                return AIResponse(
                    success=False,
                    message="Amount not found",
                    display="❓ **Amount Required**\n\nPlease specify the amount to transfer.",
                    suggestions=["Transfer ₹5000", "Send ₹10000", "Transfer ₹2500 to bank"]
                )
            
            amount = float(amount_match.group(1).replace(',', ''))
            
            # Check balance
            balance = db.get_user_balance(user_id)
            if amount > db.to_rupees(balance):
                return AIResponse(
                    success=False,
                    message="Insufficient balance",
                    display=f"❌ **Insufficient Balance**\n\nAvailable: ₹{db.to_rupees(balance):,.2f}",
                    suggestions=["Check balance", "Deposit money", "Transfer less"]
                )
            
            action = AIAction(
                action_type=ActionType.TRANSFER,
                target="transfer",
                parameters={'amount': amount},
                requires_confirmation=True,
                confirmation_message=f"Transfer ₹{amount:,.2f}?",
            )
            
            is_bank = 'bank' in query.lower()
            display = f"""
💸 **Transfer {'to Bank' if is_bank else 'to User'}**
- Amount: ₹{amount:,.2f}
"""
            
            return AIResponse(
                success=True,
                message="Ready to transfer",
                action=action,
                display=display,
                suggestions=[f"Transfer ₹{amount}", "Cancel", "Add recipient"]
            )
            
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_invest(
        self,
        query: str,
        user_id: int,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle investment"""
        try:
            amount_match = re.search(
                r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
                query, re.IGNORECASE
            )
            
            if not amount_match:
                return AIResponse(
                    success=False,
                    message="Amount not found",
                    display="❓ **Amount Required**\n\nPlease specify the amount to invest.",
                    suggestions=["Invest ₹5000 in bitcoin", "Buy ₹10000 HDFC", "Invest ₹2500"]
                )
            
            amount = float(amount_match.group(1).replace(',', ''))
            
            # Detect asset
            asset_symbol = None
            for alias, symbol in self.investment_assets.items():
                if alias in query.lower():
                    asset_symbol = symbol
                    break
            
            if not asset_symbol:
                return AIResponse(
                    success=False,
                    message="Asset not found",
                    display="❓ **Asset Required**\n\nWhat would you like to invest in?\n\nOptions:\n- Stocks: RELIANCE, TCS, HDFC, ICICI\n- Crypto: BTC, ETH, SOL\n- Gold\n- Mutual Funds",
                    suggestions=["Invest in bitcoin", "Buy HDFC stock", "Invest in gold"]
                )
            
            action = AIAction(
                action_type=ActionType.INVESTMENT,
                target="invest",
                parameters={'amount': amount, 'asset': asset_symbol},
                requires_confirmation=True,
                confirmation_message=f"Invest ₹{amount:,.2f} in {asset_symbol}?",
            )
            
            display = f"""
📈 **Invest**
- Amount: ₹{amount:,.2f}
- Asset: {asset_symbol}
"""
            
            return AIResponse(
                success=True,
                message="Ready to invest",
                action=action,
                display=display,
                suggestions=[f"Invest ₹{amount} in {asset_symbol}", "Change asset", "Cancel"]
            )
            
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_set_budget(
        self,
        query: str,
        user_id: int,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle setting budget"""
        try:
            amount_match = re.search(
                r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
                query, re.IGNORECASE
            )
            
            category = None
            for alias, cat in self.category_aliases.items():
                if alias in query.lower():
                    category = cat
                    break
            
            if not amount_match or not category:
                return AIResponse(
                    success=False,
                    message="Details missing",
                    display="❓ **Budget Details Required**\n\nPlease specify:\n1. Category (e.g., Food, Shopping)\n2. Amount (e.g., ₹10000)",
                    suggestions=["Set ₹10000 budget for food", "Create ₹5000 shopping budget", "Add ₹8000 transport budget"]
                )
            
            amount = float(amount_match.group(1).replace(',', ''))
            
            return AIResponse(
                success=True,
                message=f"Ready to set {category} budget to ₹{amount:,.2f}",
                navigate_to='budget',
                display=f"""
📋 **Set Budget**
- Category: {category}
- Amount: ₹{amount:,.2f}
""",
                suggestions=[f"Set ₹{amount} for {category}", "View current budgets", "Cancel"]
            )
            
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_withdraw(
        self,
        query: str,
        user_id: int,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle withdrawal to bank"""
        try:
            amount_match = re.search(
                r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
                query, re.IGNORECASE
            )
            
            if not amount_match:
                return AIResponse(
                    success=False,
                    message="Amount not found",
                    display="❓ **Amount Required**\n\nHow much do you want to withdraw?",
                    suggestions=["Withdraw ₹5000", "Transfer ₹10000 to bank", "Withdraw ₹2500"]
                )
            
            amount = float(amount_match.group(1).replace(',', ''))
            
            balance = db.get_user_balance(user_id)
            if amount > db.to_rupees(balance):
                return AIResponse(
                    success=False,
                    message="Insufficient balance",
                    display=f"❌ **Insufficient Balance**\n\nAvailable: ₹{db.to_rupees(balance):,.2f}",
                    suggestions=["Check balance", "Deposit money"]
                )
            
            action = AIAction(
                action_type=ActionType.TRANSFER,
                target="withdraw",
                parameters={'amount': amount},
                requires_confirmation=True,
                confirmation_message=f"Withdraw ₹{amount:,.2f} to bank?",
            )
            
            return AIResponse(
                success=True,
                message="Ready to withdraw",
                action=action,
                display=f"""
🏦 **Withdraw to Bank**
- Amount: ₹{amount:,.2f}
""",
                suggestions=[f"Withdraw ₹{amount}", "View linked accounts", "Cancel"]
            )
            
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_deposit(
        self,
        query: str,
        user_id: int,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle deposit from bank"""
        try:
            amount_match = re.search(
                r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
                query, re.IGNORECASE
            )
            
            if not amount_match:
                return AIResponse(
                    success=False,
                    message="Amount not found",
                    display="❓ **Amount Required**\n\nHow much do you want to deposit?",
                    suggestions=["Deposit ₹5000", "Add ₹10000 from bank", "Deposit ₹2500"]
                )
            
            amount = float(amount_match.group(1).replace(',', ''))
            
            return AIResponse(
                success=True,
                message=f"Ready to deposit ₹{amount:,.2f}",
                navigate_to='wallet',
                display=f"""
🏦 **Deposit from Bank**
- Amount: ₹{amount:,.2f}
""",
                suggestions=[f"Deposit ₹{amount}", "View linked accounts", "Cancel"]
            )
            
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    # ============================================================
    # INTENT HANDLERS
    # ============================================================
    
    def _handle_intent(
        self,
        user_id: int,
        intent: str,
        query: str
    ) -> AIResponse:
        """Handle query by intent"""
        handlers = {
            'BALANCE': self._handle_balance,
            'SPENDING': self._handle_spending,
            'INCOME': self._handle_income,
            'TRANSACTION': self._handle_transaction,
            'BUDGET': self._handle_budget,
            'INVESTMENT': self._handle_investment,
            'GOAL': self._handle_goal,
            'HELP': self._handle_help,
            'INSIGHT': self._handle_insight,
            'ANALYSIS': self._handle_analysis,
            'FORECAST': self._handle_forecast,
            'NAVIGATE': self._handle_navigate,
            'UNKNOWN': self._handle_unknown,
        }
        
        handler = handlers.get(intent, self._handle_unknown)
        return handler(user_id, query)
    
    def _handle_balance(self, user_id: int, query: str) -> AIResponse:
        """Handle balance query"""
        try:
            balance = wallet_service.get_total_balance(user_id)
            
            display = f"""
💰 **Your Balance Summary**

| Account | Amount |
|---------|--------|
| Wallet | ₹{balance['wallet']:,.2f} |
| Bank | ₹{balance['bank']:,.2f} |
| Investments | ₹{balance['investments_current']:,.2f} |
| **Net Worth** | **₹{balance['net_worth']:,.2f}** |
"""
            
            return AIResponse(
                success=True,
                message="Balance retrieved",
                data=balance,
                display=display,
                suggestions=["Show my spending this month", "Show budget status", "Give me saving tips"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_spending(self, user_id: int, query: str) -> AIResponse:
        """Handle spending query"""
        try:
            now = datetime.now()
            month_str = now.strftime('%Y-%m')
            
            expenses = db.get_user_expenses(user_id, limit=100)
            total = sum(db.to_rupees(e['amount']) for e in expenses) if expenses else 0
            
            categories = {}
            for e in expenses:
                cat = e['category']
                categories[cat] = categories.get(cat, 0) + db.to_rupees(e['amount'])
            
            sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
            
            lines = ["📊 **Your Spending (This Month)**\n", f"**Total: ₹{total:,.2f}**\n"]
            
            for cat, amount in sorted_cats[:8]:
                pct = (amount / total * 100) if total > 0 else 0
                lines.append(f"- {cat}: ₹{amount:,.2f} ({pct:.1f}%)")
            
            return AIResponse(
                success=True,
                message="Spending summary retrieved",
                data={'total': total, 'categories': dict(sorted_cats)},
                display='\n'.join(lines),
                suggestions=["Show top expenses", "Compare with last month", "Set budget"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_income(self, user_id: int, query: str) -> AIResponse:
        """Handle income query"""
        try:
            now = datetime.now()
            month_str = now.strftime('%Y-%m')
            
            income_list = db.get_user_income(user_id, limit=100)
            total = sum(db.to_rupees(i['amount']) for i in income_list) if income_list else 0
            
            lines = [f"💵 **Your Income (This Month)**\n", f"**Total: ₹{total:,.2f}**\n"]
            
            for i in income_list[:5]:
                lines.append(f"- {i['source']}: ₹{db.to_rupees(i['amount']):,.2f}")
            
            return AIResponse(
                success=True,
                message="Income retrieved",
                data={'total': total},
                display='\n'.join(lines),
                suggestions=["Compare income vs expense", "Show savings rate", "Add income"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_transaction(self, user_id: int, query: str) -> AIResponse:
        """Handle transaction query"""
        try:
            expenses = db.get_user_expenses(user_id, limit=10)
            
            lines = ["🕐 **Recent Transactions**\n"]
            
            for e in expenses[:10]:
                amount = db.to_rupees(e['amount'])
                lines.append(f"- {e['date'][:10]} | {e['category']} | ₹{amount:,.2f}")
            
            return AIResponse(
                success=True,
                message="Transactions retrieved",
                display='\n'.join(lines),
                suggestions=["Show all transactions", "Filter by category", "Add expense"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_budget(self, user_id: int, query: str) -> AIResponse:
        """Handle budget query"""
        try:
            now = datetime.now()
            budgets = analytics_service.get_budget_status(user_id, now.year, now.month)
            
            if not budgets:
                return AIResponse(
                    success=True,
                    message="No budgets set",
                    display="📋 **No Budgets Set**\n\nSet budgets to track your spending limits!",
                    suggestions=["Set budget for Food ₹10000", "Set budget for Transport ₹5000"]
                )
            
            lines = [f"📋 **Budget Status ({now.strftime('%B %Y')})**\n"]
            
            for b in budgets:
                status_icon = '✅' if b['status'] == 'ON_TRACK' else '⚠️' if b['status'] == 'WARNING' else '❌'
                lines.append(f"{status_icon} **{b['category']}**: ₹{b['spent']:,.0f} / ₹{b['limit']:,.0f} ({b['percentage']:.0f}%)")
            
            return AIResponse(
                success=True,
                message="Budget status retrieved",
                data={'budgets': budgets},
                display='\n'.join(lines),
                suggestions=["Update budget", "Show spending by category", "Get saving tips"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_investment(self, user_id: int, query: str) -> AIResponse:
        """Handle investment query"""
        try:
            from services.investment_service import investment_service
            
            portfolio = investment_service.get_portfolio(user_id)
            
            if not portfolio['holdings']:
                return AIResponse(
                    success=True,
                    message="No investments",
                    display="📈 **No Investments**\n\nStart investing to grow your wealth!",
                    suggestions=["Show market overview", "Buy stocks", "Buy crypto"]
                )
            
            lines = [
                f"📈 **Your Investment Portfolio**\n",
                f"**Invested:** ₹{portfolio['total_invested']:,.2f}",
                f"**Current Value:** ₹{portfolio['current_value']:,.2f}",
                f"**Profit/Loss:** {'+' if portfolio['total_profit_loss'] >= 0 else ''}₹{portfolio['total_profit_loss']:,.2f}\n"
            ]
            
            for h in portfolio['holdings'][:5]:
                lines.append(f"- {h['asset_symbol']}: {h['units_owned']:.4f} units @ ₹{h['current_price']:,.2f}")
            
            return AIResponse(
                success=True,
                message="Portfolio retrieved",
                data=portfolio,
                display='\n'.join(lines),
                suggestions=["Show market overview", "Buy more", "Sell investment"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_goal(self, user_id: int, query: str) -> AIResponse:
        """Handle goal query"""
        try:
            goals = db.get_user_goals(user_id, status='ACTIVE')
            
            if not goals:
                return AIResponse(
                    success=True,
                    message="No goals",
                    display="🎯 **No Active Goals**\n\nSet goals to stay motivated!",
                    suggestions=["Create goal for Emergency Fund ₹100000", "Create goal for Vacation ₹50000"]
                )
            
            lines = ["🎯 **Your Financial Goals**\n"]
            
            for g in goals:
                target = db.to_rupees(g['target_amount'])
                current = db.to_rupees(g['current_savings'])
                progress = (current / target * 100) if target > 0 else 0
                
                lines.append(f"**{g['goal_name']}** ({g['priority']})")
                lines.append(f"   Progress: ₹{current:,.0f} / ₹{target:,.0f} ({progress:.1f}%)")
                lines.append("")
            
            return AIResponse(
                success=True,
                message="Goals retrieved",
                data={'goals': goals},
                display='\n'.join(lines),
                suggestions=["Add contribution", "Create new goal", "Show saving tips"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_help(self, user_id: int, query: str) -> AIResponse:
        """Handle help query"""
        help_text = """
🤖 **AI Financial Assistant Commands**

**💰 Balance & Money:**
- "Show my balance"
- "How much do I have?"

**💸 Expenses:**
- "Add expense of ₹500"
- "Show spending this month"

**📈 Investments:**
- "Invest ₹5000 in bitcoin"
- "Show my portfolio"

**🏦 Transfers:**
- "Transfer ₹1000 to John"
- "Withdraw ₹5000 to bank"

**📊 Analytics:**
- "Show financial health"
- "Compare this month vs last"

**💡 Insights:**
- "How can I save more?"
- "Give me tips"

**🗺️ Navigation:**
- "Open investments page"
- "Go to budget"

Try asking naturally!
"""
        
        return AIResponse(
            success=True,
            message="Help displayed",
            display=help_text,
            suggestions=["Show my balance", "Add expense", "Open investments"]
        )
    
    def _handle_insight(self, user_id: int, query: str) -> AIResponse:
        """Handle insight query"""
        try:
            tips = self._generate_personalized_tips(user_id)
            
            lines = ["💡 **Personalized Tips**\n"]
            
            for i, tip in enumerate(tips[:8], 1):
                lines.append(f"{i}. {tip}")
            
            return AIResponse(
                success=True,
                message="Tips generated",
                data={'tips': tips},
                display='\n'.join(lines),
                suggestions=["Show my budget", "Analyze spending", "Show financial health"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_analysis(self, user_id: int, query: str) -> AIResponse:
        """Handle analysis query"""
        try:
            health = analytics_service.calculate_financial_health_score(user_id)
            
            lines = [f"📊 **Financial Health Analysis**\n", f"**Score: {health['score']}/100** ({health['rating']})\n"]
            
            breakdown_labels = {
                'savings_rate': 'Savings Rate',
                'budget_compliance': 'Budget Compliance',
                'emergency_fund': 'Emergency Fund',
                'investment_diversity': 'Investment Diversity',
                'activity': 'Transaction Activity'
            }
            
            for key, values in health.get('breakdown', {}).items():
                label = breakdown_labels.get(key, key.title())
                lines.append(f"- {label}: {values['score']}/{values['max']}")
            
            return AIResponse(
                success=True,
                message="Analysis generated",
                data=health,
                display='\n'.join(lines),
                suggestions=["Show detailed breakdown", "Get improvement tips", "Compare with last month"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_forecast(self, user_id: int, query: str) -> AIResponse:
        """Handle forecast query"""
        try:
            now = datetime.now()
            trend_data = analytics_service.get_income_vs_expense_trend(user_id, 3)
            
            if not trend_data:
                return AIResponse(
                    success=True,
                    message="No data",
                    display="📈 **Insufficient Data**\n\nNeed 3+ months of history for forecasts.",
                    suggestions=["Add more transactions", "Check back later"]
                )
            
            avg_income = sum(m['income'] for m in trend_data) / len(trend_data)
            avg_expense = sum(m['expense'] for m in trend_data) / len(trend_data)
            avg_savings = avg_income - avg_expense
            
            lines = [
                f"📈 **3-Month Financial Forecast**\n",
                f"**Based on last 3 months:**",
                f"- Avg Income: ₹{avg_income:,.0f}/month",
                f"- Avg Expenses: ₹{avg_expense:,.0f}/month",
                f"- Avg Savings: ₹{avg_savings:,.0f}/month\n",
                f"**Projected 3-Month Savings:** ₹{avg_savings * 3:,.0f}",
            ]
            
            if avg_savings < 0:
                lines.append("\n⚠️ You're spending more than earning. Review your expenses!")
            
            return AIResponse(
                success=True,
                message="Forecast generated",
                data={'avg_income': avg_income, 'avg_expense': avg_expense, 'avg_savings': avg_savings},
                display='\n'.join(lines),
                suggestions=["Set savings goal", "Create budget", "Show detailed analysis"]
            )
        except Exception as e:
            return AIResponse(success=False, message=str(e), error=str(e))
    
    def _handle_navigate(self, user_id: int, query: str) -> AIResponse:
        """Handle navigation"""
        match = re.search(r'(?:go to|open|show|view|navigate to|launch)\s+(?:the\s+)?(\w+)', query, re.IGNORECASE)
        
        if match:
            target = match.group(1).lower()
            page = self.page_map.get(target, 'dashboard')
            
            return AIResponse(
                success=True,
                message=f"Navigating to {page}",
                navigate_to=page,
                display=f"🗺️ **Navigating to {page.title()}...**",
                suggestions=["Show dashboard", "Go to wallet", "View transactions"]
            )
        
        return AIResponse(
            success=True,
            message="Opening dashboard",
            navigate_to='dashboard',
            display="🗺️ **Opening Dashboard...**",
        )
    
    def _handle_unknown(self, user_id: int, query: str) -> AIResponse:
        """Handle unknown query"""
        return AIResponse(
            success=True,
            message="Query not understood",
            display=f"""
🤔 **I didn't understand that**

You asked: "{query}"

Try asking:
- "Show my balance"
- "Add expense of ₹500"
- "How much did I spend this month?"
- "Show my investments"
""",
            suggestions=["Show my balance", "Add expense", "Open investments", "Help me"]
        )
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _generate_personalized_tips(self, user_id: int) -> List[str]:
        """Generate personalized tips"""
        tips = []
        
        try:
            now = datetime.now()
            summary = wallet_service.get_monthly_summary(user_id)
            
            # Savings tip
            if summary.get('savings_rate', 0) < 20:
                tips.append(f"Your savings rate is {summary['savings_rate']:.1f}%. Try to save at least 20%.")
            else:
                tips.append(f"Great job! You're saving {summary['savings_rate']:.1f}% of your income.")
            
            # General tips
            general_tips = [
                "Track every expense, no matter how small.",
                "Review subscriptions monthly and cancel unused ones.",
                "Use the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
                "Automate your savings by setting up recurring transfers.",
                "Set specific, measurable financial goals.",
            ]
            
            import random
            tips.extend(random.sample(general_tips, min(3, len(general_tips))))
            
        except Exception:
            tips = [
                "Track your daily expenses to understand spending patterns.",
                "Set a monthly savings target and stick to it.",
                "Review your subscriptions and cancel unused ones.",
                "Automate your savings on payday.",
                "Build an emergency fund with 3-6 months of expenses.",
            ]
        
        return tips
    
    def _handle_error(self, error: Exception, user_id: int, query: str) -> AIResponse:
        """Handle errors gracefully"""
        try:
            # Log error
            db.log_action(
                actor_type='AI_AGENT',
                actor_id=user_id,
                action='AI_ERROR',
                old_values={'error': str(error), 'query': query}
            )
        except:
            pass
        
        return AIResponse(
            success=False,
            message="Error occurred",
            error=str(error),
            display=f"""
⚠️ **Something went wrong**

{str(error)[:200]}

**What you can do:**
- Try rephrasing your request
- Check your connection
- Try again in a moment

**Still having issues?**
Contact support with this error.
""",
            suggestions=["Try again", "Contact support", "Show my balance"]
        )
    
    # ============================================================
    # ACTION EXECUTION
    # ============================================================
    
    def execute_action(self, action: AIAction, user_id: int) -> AIResponse:
        """Execute a confirmed action"""
        if not action:
            return AIResponse(
                success=False,
                message="No action to execute",
                display="❌ **No Action**\n\nNothing to execute."
            )
        
        try:
            if action.target == "add_expense":
                result = wallet_service.add_expense(
                    user_id=user_id,
                    amount=action.parameters.get('amount', 0),
                    category=action.parameters.get('category', 'Others'),
                    description=action.parameters.get('description', '')
                )
                
                if result and result[0]:
                    return AIResponse(
                        success=True,
                        message="Expense added",
                        display=f"✅ **Expense Added Successfully!**\n\n₹{action.parameters.get('amount', 0):,.2f} for {action.parameters.get('category', 'expense')}"
                    )
                else:
                    return AIResponse(
                        success=False,
                        message=result[1] if result else "Unknown error",
                        display="❌ **Failed to Add Expense**\n\nPlease try again."
                    )
            
            elif action.target == "add_income":
                result = wallet_service.add_income(
                    user_id=user_id,
                    amount=action.parameters.get('amount', 0),
                    source=action.parameters.get('source', 'Other')
                )
                
                if result and result[0]:
                    return AIResponse(
                        success=True,
                        message="Income added",
                        display=f"✅ **Income Added Successfully!**\n\n₹{action.parameters.get('amount', 0):,.2f} from {action.parameters.get('source', 'source')}"
                    )
                else:
                    return AIResponse(
                        success=False,
                        message=result[1] if result else "Unknown error",
                        display="❌ **Failed to Add Income**\n\nPlease try again."
                    )
            
            return AIResponse(
                success=False,
                message="Action not implemented",
                display="❌ **Action Not Available**\n\nThis action cannot be performed."
            )
            
        except Exception as e:
            return self._handle_error(e, user_id, "")


# Singleton instance
unified_ai_agent = UnifiedAIAgent()
