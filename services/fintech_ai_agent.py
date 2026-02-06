"""
Advanced AI Agent for Fintech
Production-grade AI agent with voice, OCR, navigation, and action capabilities
"""

import re
import json
import base64
import io
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from PIL import Image
import pytesseract

from database.db import db
from services.wallet_service import wallet_service
from services.analytics_service import analytics_service
from services.security_service import security_service
from services.auth_service import auth_service
from utils.validators import ValidationUtils, ValidationResult


class TransactionType(Enum):
    """Transaction types"""
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    INVESTMENT = "INVESTMENT"
    DEPOSIT = "DEPOSIT"  # Bank → Wallet
    WITHDRAW = "WITHDRAW"  # Wallet → Bank


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
class AIAction:
    """AI action to perform"""
    action_type: ActionType
    target: str
    parameters: Dict = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_message: str = None
    on_confirm: Callable = None


@dataclass
class AIResponse:
    """Structured AI response"""
    success: bool
    message: str
    action: AIAction = None
    data: Dict = field(default_factory=dict)
    display: str = ""
    suggestions: List[str] = field(default_factory=list)
    error: str = None
    navigate_to: str = None


class FintechAIAgent:
    """
    Advanced AI Agent for Fintech
    
    Capabilities:
    - Natural language understanding
    - Voice input processing
    - OCR for receipts
    - Page navigation
    - Transaction execution
    - Smart insights
    - Error handling
    - Security validation
    """
    
    def __init__(self):
        # Navigation mappings
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
        }
        
        # Category aliases for OCR and NL
        self.category_aliases = {
            'food': 'Food & Dining',
            'restaurant': 'Food & Dining',
            'grocery': 'Groceries',
            'groceries': 'Groceries',
            'transport': 'Transportation',
            'uber': 'Transportation',
            'ola': 'Transportation',
            'taxi': 'Transportation',
            'fuel': 'Transportation',
            'petrol': 'Transportation',
            'shopping': 'Shopping',
            'amazon': 'Shopping',
            'flipkart': 'Shopping',
            'bills': 'Bills & Utilities',
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
            'travel': 'Travel',
            'flight': 'Travel',
            'hotel': 'Travel',
            'train': 'Travel',
            'personal': 'Personal Care',
            'salon': 'Personal Care',
        }
        
        # Supported assets for investment
        self.investment_assets = {
            'bitcoin': 'BTC',
            'btc': 'BTC',
            'ethereum': 'ETH',
            'eth': 'ETH',
            'solana': 'SOL',
            'sol': 'SOL',
            'reliance': 'RELIANCE',
            'tcs': 'TCS',
            'infosys': 'INFY',
            'hdfc': 'HDFCBANK',
            'icici': 'ICICIBANK',
            'gold': 'GOLD',
            'mutual fund': 'MUTUAL_FUND',
            'sip': 'MUTUAL_FUND',
        }
        
        # Intent patterns
        self.intent_patterns = [
            # Navigation
            (r'(?:go to|open|show|view|navigate to|launch)\s+(?:the\s+)?(\w+)', 'NAVIGATE'),
            
            # Balance queries
            (r'(?:show|what|how much|check|get|tell me).*(?:balance|wallet|money|funds)', 'BALANCE'),
            
            # Spending queries
            (r'(?:show|what|how much|spending|spent|expenses)', 'SPENDING'),
            
            # Income queries
            (r'(?:show|what|how much|income|earned|salary)', 'INCOME'),
            
            # Transaction queries
            (r'(?:transaction|recent|last|payment|purchase)', 'TRANSACTION'),
            
            # Budget queries
            (r'(?:budget|spending limit|limit)', 'BUDGET'),
            
            # Investment queries
            (r'(?:invest|investment|portfolio|stocks?|crypto|mf|mutual fund)', 'INVESTMENT'),
            
            # Transfer queries
            (r'(?:transfer|send|pay|move)', 'TRANSFER'),
            
            # Goal queries
            (r'(?:goal|target|saving|save for)', 'GOAL'),
            
            # Help queries
            (r'(?:help|what can you do|commands|guide)', 'HELP'),
            
            # Insight queries
            (r'(?:insight|tip|advice|recommend|suggest)', 'INSIGHT'),
            
            # Analysis queries
            (r'(?:analyze|analysis|health|score|compare)', 'ANALYSIS'),
            
            # Forecast queries
            (r'(?:forecast|predict|future|projection)', 'FORECAST'),
        ]
        
        # Action patterns
        self.action_patterns = [
            # Add expense
            (r'(?:add|record|log|create)\s+(?:an?\s+)?(?:expense|spending|purchase|payment)', 'ADD_EXPENSE'),
            (r'spend\s+(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', 'ADD_EXPENSE'),
            
            # Add income
            (r'(?:add|record|log|receive)\s+(?:an?\s+)?(?:income|salary|earning|payment)', 'ADD_INCOME'),
            (r'(?:received|got|earned)\s+(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', 'ADD_INCOME'),
            
            # Transfer
            (r'(?:transfer|send|pay)\s+(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', 'TRANSFER'),
            
            # Invest
            (r'(?:invest|buy|purchase)\s+(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', 'INVEST'),
            
            # Set budget
            (r'(?:set|create|make)\s+(?:a\s+)?budget', 'SET_BUDGET'),
            
            # Withdraw
            (r'(?:withdraw|cash out|take out)', 'WITHDRAW'),
            
            # Deposit
            (r'(?:deposit|add money|put money)', 'DEPOSIT'),
        ]
    
    def process_query(
        self,
        user_id: int,
        query: str,
        context: Dict = None,
        require_confirmation: bool = True
    ) -> AIResponse:
        """
        Process user query with AI agent
        
        Args:
            user_id: User ID
            query: User query (text or voice converted)
            context: Current context (page, recent actions, etc.)
            require_confirmation: Whether to require confirmation for actions
            
        Returns:
            AIResponse with result and potential action
        """
        try:
            # Clean query
            clean_query = query.lower().strip()
            
            # Detect intent
            intent = self._detect_intent(clean_query)
            
            # Extract entities
            entities = self._extract_entities(clean_query)
            
            # Check for action patterns
            action_result = self._detect_action(clean_query, entities, require_confirmation)
            
            if action_result:
                return action_result
            
            # Handle by intent
            if intent in ['BALANCE', 'SPENDING', 'INCOME', 'TRANSACTION', 'BUDGET', 
                         'INVESTMENT', 'GOAL', 'HELP', 'INSIGHT', 'ANALYSIS', 'FORECAST']:
                return self._handle_intent(user_id, intent, entities, clean_query)
            
            # Default to help
            return self._handle_help(user_id, clean_query)
            
        except Exception as e:
            return self._handle_error(e, user_id, query)
    
    def process_voice(self, audio_data: bytes) -> Tuple[bool, str]:
        """
        Process voice input
        
        Args:
            audio_data: Audio bytes
            
        Returns:
            Tuple of (success, transcribed text)
        """
        try:
            # In production, use speech-to-text service
            # For demo, return placeholder
            # This would integrate with:
            # - Google Cloud Speech-to-Text
            # - AWS Transcribe
            # - Azure Speech Services
            # - OpenAI Whisper
            
            # Placeholder - in production, call actual STT API
            return False, "Voice input not configured. Please type your query."
            
        except Exception as e:
            return False, f"Voice processing error: {str(e)}"
    
    def process_ocr(self, image_data: bytes, image_type: str = 'receipt') -> Dict:
        """
        Process image for OCR (receipts, bills)
        
        Args:
            image_data: Image bytes
            image_type: Type of image (receipt, bill, etc.)
            
        Returns:
            Dict with extracted information
        """
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Extract text using pytesseract
            extracted_text = pytesseract.image_to_string(image)
            
            # Parse receipt
            result = self._parse_receipt(extracted_text)
            
            return {
                'success': True,
                'raw_text': extracted_text,
                'amount': result.get('amount'),
                'date': result.get('date'),
                'merchant': result.get('merchant'),
                'category': result.get('category'),
                'confidence': result.get('confidence', 0.8),
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': "Could not read the image. Please try a clearer photo."
            }
    
    def _parse_receipt(self, text: str) -> Dict:
        """Parse receipt text and extract key information"""
        result = {
            'amount': None,
            'date': None,
            'merchant': None,
            'category': None,
            'confidence': 0.5,
        }
        
        # Extract amount (look for total patterns)
        amount_patterns = [
            r'(?:total|amount|sum|due)[:\s]*₹?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
            r'₹\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{1,2})?)\s*(?:rs\.?|rupees?)',
        ]
        
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amounts.append(float(match.replace(',', '')))
                except:
                    pass
        
        if amounts:
            # Usually the largest amount is the total
            result['amount'] = max(amounts)
        
        # Extract date
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['date'] = match.group(1)
                break
        
        # Extract merchant (first substantial line)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if lines:
            # Skip common receipt headers
            for line in lines[:5]:
                if len(line) > 3 and not any(x in line.lower() for x in ['receipt', 'invoice', 'date', 'total']):
                    result['merchant'] = line
                    break
        
        # Extract category
        text_lower = text.lower()
        for alias, category in self.category_aliases.items():
            if alias in text_lower:
                result['category'] = category
                result['confidence'] = 0.9
                break
        
        return result
    
    def _detect_intent(self, query: str) -> str:
        """Detect user intent from query"""
        for pattern, intent in self.intent_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return intent
        return 'UNKNOWN'
    
    def _detect_action(
        self,
        query: str,
        entities: Dict,
        require_confirmation: bool
    ) -> Optional[AIResponse]:
        """Detect and handle actionable queries"""
        for pattern, action_type in self.action_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if action_type == 'ADD_EXPENSE':
                    return self._handle_add_expense(query, entities, require_confirmation)
                elif action_type == 'ADD_INCOME':
                    return self._handle_add_income(query, entities, require_confirmation)
                elif action_type == 'TRANSFER':
                    return self._handle_transfer(query, entities, require_confirmation)
                elif action_type == 'INVEST':
                    return self._handle_invest(query, entities, require_confirmation)
                elif action_type == 'SET_BUDGET':
                    return self._handle_set_budget(query, entities, require_confirmation)
                elif action_type == 'WITHDRAW':
                    return self._handle_withdraw(query, entities, require_confirmation)
                elif action_type == 'DEPOSIT':
                    return self._handle_deposit(query, entities, require_confirmation)
        
        return None
    
    def _handle_add_expense(
        self,
        query: str,
        entities: Dict,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle adding an expense"""
        # Extract amount
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        if not amount_match:
            return AIResponse(
                success=False,
                message="I couldn't find an amount. Please specify how much you spent.",
                display="❓ **Amount Not Found**\n\nPlease tell me how much you spent, e.g., 'Add expense of ₹500'",
                suggestions=["Add expense of ₹500", "Record spending of ₹1000", "Log ₹2500 purchase"]
            )
        
        amount = float(amount_match.group(1).replace(',', ''))
        
        # Extract category
        category = entities.get('category', 'Others')
        if not category:
            for alias, cat in self.category_aliases.items():
                if alias in query.lower():
                    category = cat
                    break
        
        # Extract merchant
        merchant = None
        for word in query.split():
            if len(word) > 3 and word[0].isupper():
                merchant = word
                break
        
        # Create action
        requires_confirmation = require_confirmation and amount > 1000
        
        action = AIAction(
            action_type=ActionType.TRANSACTION,
            target="add_expense",
            parameters={
                'amount': amount,
                'category': category,
                'merchant': merchant,
                'payment_mode': 'UPI',
            },
            requires_confirmation=requires_confirmation,
            confirmation_message=f"Add expense of ₹{amount:,.2f} for {category}?",
            on_confirm=lambda: self._execute_add_expense(
                st.session_state.user['user_id'],
                amount,
                category,
                merchant
            )
        )
        
        display = f"""
💸 **Add Expense**
- Amount: ₹{amount:,.2f}
- Category: {category}
- Merchant: {merchant or 'Not specified'}
"""
        
        return AIResponse(
            success=True,
            message="Ready to add expense",
            action=action,
            display=display,
            suggestions=[f"Add ₹{amount} for {category}", "Change category", "Cancel"]
        )
    
    def _handle_add_income(
        self,
        query: str,
        entities: Dict,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle adding income"""
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        
        if not amount_match:
            return AIResponse(
                success=False,
                message="I couldn't find an amount.",
                display="❓ **Amount Not Found**\n\nPlease tell me how much you received.",
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
        else:
            source = 'Other Income'
        
        action = AIAction(
            action_type=ActionType.TRANSACTION,
            target="add_income",
            parameters={
                'amount': amount,
                'source': source,
            },
            requires_confirmation=require_confirmation,
            confirmation_message=f"Add income of ₹{amount:,.2f} from {source}?",
            on_confirm=lambda: self._execute_add_income(
                st.session_state.user['user_id'],
                amount,
                source
            )
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
    
    def _handle_transfer(
        self,
        query: str,
        entities: Dict,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle transfer"""
        # Check if bank transfer
        if 'bank' in query.lower():
            action_type = ActionType.TRANSFER
            target = "withdraw_to_bank"
            message = "Transfer to bank"
        else:
            action_type = ActionType.TRANSFER
            target = "transfer_user"
            message = "Transfer to user"
        
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        
        if not amount_match:
            return AIResponse(
                success=False,
                message="Please specify the amount to transfer.",
                display="❓ **Amount Required**\n\nHow much do you want to transfer?",
                suggestions=["Transfer ₹5000", "Send ₹10000", "Transfer ₹2500 to bank"]
            )
        
        amount = float(amount_match.group(1).replace(',', ''))
        
        # Check balance
        user_id = st.session_state.user['user_id'] if hasattr(st, 'session_state') else None
        if user_id:
            balance = db.get_user_balance(user_id)
            if amount > db.to_rupees(balance):
                return AIResponse(
                    success=False,
                    message="Insufficient balance for transfer",
                    display=f"❌ **Insufficient Balance**\n\nAvailable: ₹{db.to_rupees(balance):,.2f}\nRequested: ₹{amount:,.2f}",
                    suggestions=["Check balance", "Deposit money", "Transfer less"]
                )
        
        action = AIAction(
            action_type=action_type,
            target=target,
            parameters={'amount': amount},
            requires_confirmation=True,
            confirmation_message=f"Transfer ₹{amount:,.2f}?",
        )
        
        display = f"""
💸 **Transfer Money**
- Amount: ₹{amount:,.2f}
- To: {'Bank Account' if 'bank' in query.lower() else 'User'}
"""
        
        return AIResponse(
            success=True,
            message="Ready to transfer",
            action=action,
            display=display,
            suggestions=[f"Transfer ₹{amount}", "Cancel", "Add recipient"]
        )
    
    def _handle_invest(
        self,
        query: str,
        entities: Dict,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle investment"""
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        
        if not amount_match:
            return AIResponse(
                success=False,
                message="Please specify the amount to invest.",
                display="❓ **Amount Required**\n\nHow much do you want to invest?",
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
                message="Please specify what to invest in.",
                display="❓ **Asset Required**\n\nWhat would you like to invest in?\n\nOptions:\n- Stocks: RELIANCE, TCS, HDFC, ICICI\n- Crypto: BTC, ETH, SOL\n- Mutual Funds\n- Gold",
                suggestions=["Invest in bitcoin", "Buy HDFC stock", "Invest in gold"]
            )
        
        action = AIAction(
            action_type=ActionType.INVESTMENT,
            target="buy_asset",
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
    
    def _handle_set_budget(
        self,
        query: str,
        entities: Dict,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle setting budget"""
        # Extract amount
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        
        # Extract category
        category = None
        for alias, cat in self.category_aliases.items():
            if alias in query.lower():
                category = cat
                break
        
        if not amount_match or not category:
            return AIResponse(
                success=False,
                message="Please specify amount and category.",
                display="❓ **Budget Details Required**\n\nPlease tell me:\n1. Category (e.g., Food, Shopping)\n2. Amount (e.g., ₹10000)",
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
    
    def _handle_withdraw(
        self,
        query: str,
        entities: Dict,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle bank withdrawal"""
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        
        if not amount_match:
            return AIResponse(
                success=False,
                message="Please specify the amount to withdraw.",
                display="❓ **Amount Required**\n\nHow much do you want to withdraw to your bank?",
                suggestions=["Withdraw ₹5000", "Transfer ₹10000 to bank", "Withdraw ₹2500"]
            )
        
        amount = float(amount_match.group(1).replace(',', ''))
        
        # Check balance
        user_id = st.session_state.user['user_id'] if hasattr(st, 'session_state') else None
        if user_id:
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
            target="withdraw_to_bank",
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
    
    def _handle_deposit(
        self,
        query: str,
        entities: Dict,
        require_confirmation: bool
    ) -> AIResponse:
        """Handle bank deposit"""
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        
        if not amount_match:
            return AIResponse(
                success=False,
                message="Please specify the amount to deposit.",
                display="❓ **Amount Required**\n\nHow much do you want to deposit from your bank?",
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
    
    def _handle_intent(
        self,
        user_id: int,
        intent: str,
        entities: Dict,
        query: str
    ) -> AIResponse:
        """Handle query by intent"""
        from services.enhanced_ai_assistant import EnhancedAIAssistant
        
        assistant = EnhancedAIAssistant()
        
        if intent == 'BALANCE':
            return assistant._handle_balance(user_id, query, entities)
        elif intent == 'SPENDING':
            return assistant._handle_spending(user_id, query, entities)
        elif intent == 'INCOME':
            return assistant._handle_income(user_id, query, entities)
        elif intent == 'TRANSACTION':
            return assistant._handle_transaction(user_id, query, entities)
        elif intent == 'BUDGET':
            return assistant._handle_budget(user_id, query, entities)
        elif intent == 'INVESTMENT':
            return assistant._handle_investment(user_id, query, entities)
        elif intent == 'GOAL':
            return assistant._handle_goal(user_id, query, entities)
        elif intent == 'HELP':
            return assistant._handle_help(user_id, query, entities)
        elif intent == 'INSIGHT':
            return assistant._handle_tip(user_id, query, entities)
        elif intent == 'ANALYSIS':
            return assistant._handle_insight(user_id, query, entities)
        elif intent == 'FORECAST':
            return assistant._handle_forecast(user_id, query, entities)
        
        return assistant._handle_unknown(user_id, query, entities)
    
    def _handle_help(self, user_id: int, query: str) -> AIResponse:
        """Handle help queries"""
        help_text = """
🤖 **AI Agent Commands**

**💰 Balance & Money:**
- "Show my balance"
- "How much do I have?"
- "What's my net worth?"

**💸 Transactions:**
- "Add expense of ₹500"
- "Record ₹1000 spending"
- "Show recent transactions"

**📈 Investments:**
- "Invest ₹5000 in bitcoin"
- "Buy HDFC stock"
- "Show my portfolio"

**🏦 Transfers:**
- "Transfer ₹2000 to John"
- "Withdraw ₹10000 to bank"
- "Deposit ₹5000 from bank"

**📊 Analytics:**
- "Show spending this month"
- "Compare with last month"
- "Financial health score"

**💡 Insights:**
- "How can I save more?"
- "Am I overspending?"
- "Give me tips"

**🗺️ Navigation:**
- "Open investments page"
- "Go to budget"
- "Show dashboard"

**🎤 Voice:**
- Click the microphone to speak

**📷 Receipts:**
- Upload receipt photo to auto-add expense

Try saying naturally: "I spent ₹500 on food yesterday"
"""
        
        return AIResponse(
            success=True,
            message="Help displayed",
            display=help_text,
            suggestions=["Show my balance", "Add expense", "Open investments"]
        )
    
    def _handle_error(self, error: Exception, user_id: int, query: str) -> AIResponse:
        """Handle errors gracefully"""
        # Log error
        try:
            db.log_action(
                actor_type='AI_AGENT',
                actor_id=user_id,
                action='AI_ERROR',
                entity_type='error',
                old_values={'error': str(error), 'query': query}
            )
        except:
            pass
        
        error_messages = {
            'balance': "Let me check your balance...",
            'transaction': "There was an issue with the transaction. Let me retry...",
            'navigation': "I couldn't navigate there. Let me try again...",
            'generic': "Something went wrong. Let me help you with that."
        }
        
        return AIResponse(
            success=False,
            message="Error occurred",
            error=str(error),
            display=f"""
⚠️ **Oops! Something went wrong**

{str(error)}

**What I can do:**
- Try rephrasing your request
- Check your connection
- Try again in a moment

**If this keeps happening:**
- Contact support
- Check your account status
""",
            suggestions=["Try again", "Contact support", "Show my balance"]
        )
    
    def _extract_entities(self, query: str) -> Dict:
        """Extract entities from query"""
        entities = {
            'period': None,
            'category': None,
            'amount': None,
            'top_n': None,
            'date': None,
        }
        
        # Time period
        periods = {
            'today': 'today',
            'this week': 'this week',
            'this month': 'this month',
            'last month': 'last month',
            'this year': 'this year',
            'yesterday': 'yesterday',
        }
        
        for period_key, period_value in periods.items():
            if period_key in query:
                entities['period'] = period_value
                break
        
        # Amount
        amount_match = re.search(r'(?:₹|rs\.?|rupees?)?\s*(\d+(?:,\d{3})*(?:\.\d{1,2})?)', query, re.IGNORECASE)
        if amount_match:
            try:
                entities['amount'] = float(amount_match.group(1).replace(',', ''))
            except:
                pass
        
        # Top N
        top_match = re.search(r'(?:top|best|highest)\s*(\d+)', query, re.IGNORECASE)
        if top_match:
            entities['top_n'] = int(top_match.group(1))
        
        return entities
    
    # ============================================================
    # ACTION EXECUTION
    # ============================================================
    
    def execute_action(self, action: AIAction) -> AIResponse:
        """Execute a confirmed action"""
        if not action.on_confirm:
            return AIResponse(
                success=False,
                message="Action cannot be executed",
                display="❌ **Action Not Available**\n\nThis action cannot be performed.",
            )
        
        try:
            result = action.on_confirm()
            return AIResponse(
                success=True,
                message="Action completed",
                data=result or {},
                display=f"✅ **Action Completed**\n\n{action.confirmation_message}",
            )
        except Exception as e:
            return self._handle_error(e, st.session_state.user['user_id'] if hasattr(st, 'session_state') else 0, "")
    
    def _execute_add_expense(
        self,
        user_id: int,
        amount: float,
        category: str,
        merchant: str = None
    ) -> Dict:
        """Execute add expense"""
        result = wallet_service.add_expense(
            user_id=user_id,
            amount=amount,
            category=category,
            merchant=merchant,
            description=f"Added via AI Agent"
        )
        return result
    
    def _execute_add_income(
        self,
        user_id: int,
        amount: float,
        source: str
    ) -> Dict:
        """Execute add income"""
        result = wallet_service.add_income(
            user_id=user_id,
            amount=amount,
            source=source,
            description=f"Added via AI Agent"
        )
        return result
    
    def navigate_to(self, target: str) -> str:
        """Get navigation target"""
        return self.page_map.get(target.lower(), 'dashboard')
    
    def confirm_action(self, action: AIAction) -> bool:
        """Get user confirmation for action"""
        # In Streamlit, this would show a confirmation dialog
        return True


# Singleton instance
ai_agent = FintechAIAgent()
