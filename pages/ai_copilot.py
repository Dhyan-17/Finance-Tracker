"""
AI Copilot Page
Advanced AI assistant with voice input, OCR, and action capabilities
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

from database.db import db
from services.fintech_ai_agent import FintechAIAgent, AIResponse
from services.enhanced_ai_assistant import EnhancedAIAssistant
from utils.ui_components import ModernUIComponents


def show_ai_copilot():
    """Display AI Copilot interface"""
    user = st.session_state.get('user')
    if not user:
        st.error("Please login to use AI Copilot")
        return
    
    user_id = user['user_id']
    
    # Page configuration
    st.title("🤖 AI Copilot")
    st.markdown("Your intelligent financial assistant")
    
    # Initialize AI agent
    if 'ai_agent' not in st.session_state:
        st.session_state.ai_agent = FintechAIAgent()
    
    if 'ai_chat_history' not in st.session_state:
        st.session_state.ai_chat_history = []
    
    if 'ai_context' not in st.session_state:
        st.session_state.ai_context = {}
    
    # Layout: Chat on left, Quick Actions on right
    col_chat, col_actions = st.columns([2, 1])
    
    with col_chat:
        # Voice Input Section
        with st.expander("🎤 Voice Input (Beta)", expanded=False):
            st.info("🎤 Voice input uses your browser's speech recognition. Click the microphone icon in the text box below to speak.")
            
            # Audio recording placeholder
            voice_result = st.text_input(
                "Or type your voice command here:",
                placeholder="Click the microphone icon in the box above to speak...",
                key="voice_input"
            )
        
        # Chat Display
        st.markdown("### 💬 Conversation")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.ai_chat_history:
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        padding: 12px 16px;
                        border-radius: 12px;
                        color: white;
                        margin: 8px 0;
                        max-width: 85%;
                        margin-left: auto;
                    ">
                        👤 {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # AI Response
                    st.markdown(f"""
                    <div style="
                        background: #f8f9fa;
                        padding: 12px 16px;
                        border-radius: 12px;
                        margin: 8px 0;
                        max-width: 85%;
                        border: 1px solid #e0e0e0;
                    ">
                        🤖 <strong>AI Copilot</strong><br><br>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show action if present
                    if msg.get('action'):
                        _render_action(msg['action'])
        
        # OCR Receipt Upload Section
        with st.expander("📷 Upload Receipt / Bill", expanded=False):
            st.markdown("**Scan receipts or bills to automatically add expenses**")
            
            uploaded_file = st.file_uploader(
                "Choose an image...",
                type=['jpg', 'jpeg', 'png', 'bmp'],
                key="receipt_uploader"
            )
            
            if uploaded_file is not None:
                with st.spinner("Processing receipt..."):
                    # Read image
                    image_bytes = uploaded_file.getvalue()
                    
                    # Process OCR
                    result = st.session_state.ai_agent.process_ocr(image_bytes, 'receipt')
                    
                    if result.get('success'):
                        st.success("✅ Receipt processed successfully!")
                        
                        # Display extracted info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Amount", f"₹{result.get('amount', 0):,.2f}")
                        with col2:
                            st.metric("Date", result.get('date', 'Not found'))
                        with col3:
                            st.metric("Category", result.get('category', 'Uncategorized'))
                        
                        if result.get('merchant'):
                            st.markdown(f"**Merchant:** {result['merchant']}")
                        
                        # Show raw text (collapsed)
                        with st.expander("View extracted text"):
                            st.text(result.get('raw_text', ''))
                        
                        # Add to expenses button
                        if result.get('amount') and result.get('category'):
                            if st.button("➕ Add This Expense"):
                                # Execute expense addition
                                try:
                                    expense_result = st.session_state.ai_agent._execute_add_expense(
                                        user_id,
                                        result['amount'],
                                        result['category'],
                                        result.get('merchant')
                                    )
                                    
                                    if expense_result and expense_result[0]:
                                        st.success("✅ Expense added successfully!")
                                        st.session_state.ai_chat_history.append({
                                            'role': 'assistant',
                                            'content': f"✅ Added expense of ₹{result['amount']:,.2f} for {result['category']}"
                                        })
                                    else:
                                        st.error(f"Failed: {expense_result[1] if expense_result else 'Unknown error'}")
                                except Exception as e:
                                    st.error(f"Error adding expense: {e}")
                    else:
                        st.error(f"❌ {result.get('message', 'Could not read the receipt')}")
                        st.warning("Tip: Try a clearer photo with good lighting")
        
        # Input Section
        st.markdown("---")
        
        # Quick examples
        st.caption("💡 Try asking:")
        examples = [
            "Show my balance",
            "How much did I spend on food this month?",
            "Add expense of ₹500 for lunch",
            "Invest ₹2000 in bitcoin",
            "Transfer ₹1000 to mom",
            "Show my financial health",
            "How can I save more money?",
            "Compare this month with last month"
        ]
        
        example_cols = st.columns(4)
        for i, example in enumerate(examples[:8]):
            with example_cols[i % 4]:
                if st.button(example, key=f"example_{i}", use_container_width=True):
                    _handle_user_input(example, user_id)
        
        # Main input
        with st.form("ai_input_form"):
            col_input, col_submit = st.columns([5, 1])
            with col_input:
                user_query = st.text_input(
                    "Ask AI Copilot:",
                    placeholder="e.g., Show my spending last month",
                    label_visibility="collapsed"
                )
            with col_submit:
                submit_btn = st.form_submit_button("Send", use_container_width=True)
            
            if submit_btn and user_query:
                _handle_user_input(user_query, user_id)
    
    with col_actions:
        # Quick Actions Panel
        st.markdown("### ⚡ Quick Actions")
        
        st.markdown("**💰 Money**")
        if st.button("➕ Add Income", use_container_width=True, key="quick_income"):
            _handle_user_input("Add income of ₹50000", user_id)
        
        if st.button("💸 Add Expense", use_container_width=True, key="quick_expense"):
            _handle_user_input("Add expense", user_id)
        
        if st.button("🏦 Transfer", use_container_width=True, key="quick_transfer"):
            _handle_user_input("Transfer money", user_id)
        
        st.markdown("---")
        st.markdown("**📊 Insights**")
        
        if st.button("📈 Spending Analysis", use_container_width=True, key="quick_spending"):
            _handle_user_input("Analyze my spending", user_id)
        
        if st.button("💡 Get Tips", use_container_width=True, key="quick_tips"):
            _handle_user_input("Give me financial tips", user_id)
        
        if st.button("🎯 Savings Tips", use_container_width=True, key="quick_savings"):
            _handle_user_input("How can I save more?", user_id)
        
        st.markdown("---")
        st.markdown("**🗺️ Navigation**")
        
        if st.button("📊 Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state.page = 'dashboard'
            st.rerun()
        
        if st.button("💳 Wallet", use_container_width=True, key="nav_wallet"):
            st.session_state.page = 'wallet'
            st.rerun()
        
        if st.button("📈 Investments", use_container_width=True, key="nav_invest"):
            st.session_state.page = 'investments'
            st.rerun()
        
        if st.button("📋 Budgets", use_container_width=True, key="nav_budget"):
            st.session_state.page = 'budgets'
            st.rerun()
        
        # Current Stats
        st.markdown("---")
        st.markdown("**📊 Your Current Stats**")
        
        try:
            balance = wallet_service.get_total_balance(user_id)
            now = datetime.now()
            monthly = wallet_service.get_monthly_summary(user_id, now.year, now.month)
            
            st.metric("Net Worth", f"₹{balance.get('net_worth', 0):,.0f}")
            st.metric("This Month", f"₹{monthly.get('savings', 0):,.0f} saved")
            
            # Savings rate gauge
            savings_rate = monthly.get('savings_rate', 0)
            if savings_rate >= 20:
                st.success(f"✅ Good savings: {savings_rate:.1f}%")
            elif savings_rate >= 10:
                st.warning(f"⚠️ Fair savings: {savings_rate:.1f}%")
            else:
                st.error(f"❌ Low savings: {savings_rate:.1f}%")
                
        except Exception as e:
            st.info("Add some transactions to see your stats")
        
        # Error Assistant
        st.markdown("---")
        st.markdown("**🆘 Need Help?**")
        
        if st.button("❓ FAQ", use_container_width=True, key="help_faq"):
            _handle_user_input("Help me use the app", user_id)
        
        if st.button("🔧 Report Issue", use_container_width=True, key="help_issue"):
            _handle_user_input("Something is not working", user_id)


def _handle_user_input(query: str, user_id: int):
    """Process user input through AI agent"""
    # Add user message to history
    st.session_state.ai_chat_history.append({
        'role': 'user',
        'content': query
    })
    
    # Get context
    context = st.session_state.ai_context.copy()
    
    # Process with AI agent
    response = st.session_state.ai_agent.process_query(
        user_id=user_id,
        query=query,
        context=context,
        require_confirmation=True
    )
    
    # Handle navigation
    if response.navigate_to:
        nav_map = {
            'dashboard': 'dashboard',
            'wallet': 'wallet',
            'budget': 'budget',
            'investments': 'investments',
            'goals': 'goals',
        }
        target = nav_map.get(response.navigate_to, response.navigate_to)
        st.session_state.page = target
        st.session_state.ai_chat_history.append({
            'role': 'assistant',
            'content': response.display + f"\n\nNavigating to {target}..."
        })
        st.rerun()
        return
    
    # Add AI response to history
    st.session_state.ai_chat_history.append({
        'role': 'assistant',
        'content': response.display,
        'action': response.action,
        'data': response.data
    })
    
    # Update context
    if response.data:
        st.session_state.ai_context.update(response.data)
    
    # Force rerender
    st.rerun()


def _render_action(action):
    """Render action button if present"""
    if action and action.requires_confirmation:
        st.markdown("---")
        st.markdown(f"**⚡ Action Required:**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm", key=f"confirm_{hash(action.confirmation_message)}"):
                result = st.session_state.ai_agent.execute_action(action)
                if result.success:
                    st.success(result.message)
                else:
                    st.error(result.message)
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_{hash(action.confirmation_message)}"):
                st.session_state.ai_chat_history.append({
                    'role': 'assistant',
                    'content': "Action cancelled. How else can I help?"
                })
                st.rerun()
    
    elif action and action.on_confirm:
        st.markdown("---")
        if st.button(f"🚀 {action.target.replace('_', ' ').title()}", use_container_width=True):
            result = st.session_state.ai_agent.execute_action(action)
            if result.success:
                st.success(result.message)
            else:
                st.error(result.message)
            st.rerun()


def show_error_assistant():
    """Show AI-powered error assistant"""
    st.title("🆘 AI Error Assistant")
    
    # Common issues
    issues = {
        "Login Issues": [
            "Forgot password",
            "Account locked",
            "Two-factor authentication issue",
            "Session expired"
        ],
        "Transaction Issues": [
            "Transaction failed but money deducted",
            "Transfer not received",
            "Expense not recorded",
            "Duplicate transaction"
        ],
        "Account Issues": [
            "Balance not updating",
            "Bank account not linking",
            "KYC verification pending",
            "Unable to add beneficiary"
        ],
        "Technical Issues": [
            "App not loading",
            "Slow performance",
            "Error messages",
            "Data sync issues"
        ]
    }
    
    # Issue selector
    category = st.selectbox("Select Issue Category:", list(issues.keys()))
    
    if category:
        issue = st.selectbox("Select Specific Issue:", issues[category])
        
        if st.button("🔍 Get Solution"):
            # Generate solution
            solution = _get_issue_solution(category, issue)
            
            st.markdown(f"""
            ## 💡 Solution for: {issue}
            
            {solution['steps']}
            
            ### 📞 Still Need Help?
            If these steps don't resolve your issue:
            
            - 📧 Email: support@fintech.app
            - 📞 Phone: 1800-XXX-XXXX (Mon-Sat, 9AM-6PM)
            - 💬 Live Chat: Available 24/7
            """)
            
            if solution.get('escalate'):
                st.warning("⚠️ This issue requires special attention. Please contact support immediately.")


def _get_issue_solution(category: str, issue: str) -> Dict:
    """Get solution for specific issue"""
    solutions = {
        ("Login Issues", "Forgot password"): {
            "steps": """
            1. Click "Forgot Password" on login page
            2. Enter your registered email
            3. Check your email for reset link (also check spam)
            4. Create a new password following security rules
            5. Login with new password
            """,
            "escalate": False
        },
        ("Transaction Issues", "Transaction failed but money deducted"): {
            "steps": """
            1. Wait 24-48 hours for auto-reversal (common for bank delays)
            2. Check your bank statement for actual deduction
            3. Note the transaction ID from your history
            4. Contact support with:
               - Transaction ID
               - Amount
               - Date and time
               - Screenshot of deduction
            """,
            "escalate": True
        },
        ("Account Issues", "Balance not updating"): {
            "steps": """
            1. Pull down to refresh the page
            2. Check if the transaction was successful
            3. Verify you're viewing the correct account
            4. Check transaction history for recent activity
            5. Clear app cache and login again
            6. If issue persists, contact support
            """,
            "escalate": False
        }
    }
    
    return solutions.get((category, issue), {
        "steps": f"""
        1. Try refreshing the page
        2. Logout and login again
        3. Clear browser cache
        4. Try a different browser or device
        
        If the issue persists, please contact support with:
        - Description of the issue
        - Steps to reproduce
        - Screenshot if applicable
        """,
        "escalate": False
    })


def show_voice_setup():
    """Show voice input setup and instructions"""
    st.title("🎤 Voice Input Setup")
    
    st.markdown("""
    ## Voice Input for AI Copilot
    
    Your browser has built-in speech recognition that works with AI Copilot.
    
    ### How to Use:
    
    1. **In the Chat Box:**
       - Look for the microphone icon 📎 in the text input
       - Click it to start speaking
       - Click again to stop
    
    2. **Best Practices:**
       - Speak clearly and at normal pace
       - Reduce background noise
       - Use simple commands
    
    3. **Example Commands:**
       - "Show my balance"
       - "How much did I spend on food?"
       - "Add expense of 500 rupees"
       - "Open investments page"
    
    ### Supported Browsers:
    
    - ✅ Google Chrome (best experience)
    - ✅ Microsoft Edge
    - ✅ Safari (limited)
    - ❌ Firefox (may require config)
    
    ### Troubleshooting:
    
    If voice input doesn't work:
    
    1. Check microphone permissions in browser
    2. Allow microphone access when prompted
    3. Try refreshing the page
    4. Switch to Chrome for best results
    """)
    
    # Test microphone
    st.subheader("🎙️ Test Your Microphone")
    
    if st.button("Start Voice Test"):
        st.info("🎤 In a production environment, this would test your microphone and guide you through voice input setup. For now, type your commands in the chat box.")
    
    # Fallback to typing
    st.warning("""
    **Voice not working?**
    
    You can still use AI Copilot effectively by typing:
    
    - "Show my spending this month"
    - "Add expense of 500 rupees"
    - "Transfer 1000 to mom"
    - "Open budget page"
    
    AI Copilot understands natural language!
    """)


def show_ocr_setup():
    """Show OCR/receipt scanning setup"""
    st.title("📷 Receipt Scanning Setup")
    
    st.markdown("""
    ## Scan Receipts with AI
    
    Upload photos of receipts and bills to automatically extract:
    
    - 💰 Amount
    - 📅 Date
    - 🏪 Merchant
    - 🏷️ Category
    
    ### How It Works:
    
    1. Click "Choose File" to upload a photo
       - Supports JPG, PNG, BMP
       - Recommended: Clear, well-lit photo
   
    2. AI processes the image
       - Extracts text using OCR
       - Identifies key information
   
    3. Review and confirm
       - Verify extracted details
       - Add to expenses with one click
    
    ### Tips for Best Results:
    
    ✅ **Do:**
    - Use clear, well-lit photos
    - Keep receipt flat
    - Include entire receipt
    - Focus on amount and merchant name
    
    ❌ **Don't:**
    - Use blurry photos
    - Include shadows
    - Cut off edges
    - Photograph at extreme angles
    
    ### Supported Receipt Types:
    
    - 🛒 Grocery receipts
    - 🍽️ Restaurant bills
    - 🏥 Medical bills
    - ⛽ Petrol receipts
    - 🛍️ Shopping receipts
    - 📱 Mobile recharge receipts
    - 💡 Utility bills
    """)
    
    # Demo
    st.subheader("🧪 Try It Out")
    
    st.info("Upload a receipt image to see OCR in action!")
    
    uploaded_file = st.file_uploader(
        "Upload receipt image",
        type=['jpg', 'jpeg', 'png'],
        key="demo_ocr"
    )
    
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Image", width=300)
        
        if st.button("Process Receipt"):
            with st.spinner("Analyzing receipt..."):
                image_bytes = uploaded_file.getvalue()
                result = st.session_state.ai_agent.process_ocr(image_bytes, 'receipt')
                
                if result.get('success'):
                    st.success("✅ Receipt processed!")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Amount", f"₹{result.get('amount', 0):,.2f}")
                    col2.metric("Date", result.get('date', 'Not found'))
                    col3.metric("Category", result.get('category', 'Uncategorized'))
                    
                    if result.get('merchant'):
                        st.markdown(f"**Merchant:** {result['merchant']}")
                    
                    st.progress(result.get('confidence', 0.8) * 100)
                    st.caption(f"Confidence: {result.get('confidence', 0.8) * 100:.1f}%")
                else:
                    st.error(result.get('message', 'Processing failed'))


# Page mapping
page_mapping = {
    "copilot": show_ai_copilot,
    "errors": show_error_assistant,
    "voice": show_voice_setup,
    "ocr": show_ocr_setup,
}


def show_ai_pages():
    """Show AI-related pages based on selection"""
    page_options = {
        "🤖 AI Copilot": "copilot",
        "🆘 Error Assistant": "errors",
        "🎤 Voice Setup": "voice",
        "📷 OCR Setup": "ocr"
    }
    
    selected = st.sidebar.selectbox(
        "AI Features",
        list(page_options.keys()),
        index=0
    )
    
    page_func = page_mapping.get(page_options[selected], show_ai_copilot)
    
    if page_options[selected] == "copilot":
        show_ai_copilot()
    elif page_options[selected] == "errors":
        show_error_assistant()
    elif page_options[selected] == "voice":
        show_voice_setup()
    elif page_options[selected] == "ocr":
        show_ocr_setup()


# Run main function
if __name__ == "__main__":
    show_ai_copilot()
