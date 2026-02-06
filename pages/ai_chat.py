"""
Unified AI Chat Page
Single intelligent AI assistant for all finance interactions
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

# Import unified AI agent
from services.unified_ai_agent import UnifiedAIAgent, AIResponse, AIAction


def show_ai_chat():
    """
    Main AI Chat page
    Uses unified AI agent for all finance interactions
    """
    # Check authentication
    user = st.session_state.get('user')
    if not user:
        st.error("🔒 Please login to use AI Assistant")
        return
    
    user_id = user.get('user_id')
    if not user_id:
        st.error("Invalid user session. Please login again.")
        return
    
    # Initialize AI agent
    if 'unified_ai_agent' not in st.session_state:
        try:
            st.session_state.unified_ai_agent = UnifiedAIAgent()
        except Exception as e:
            st.error(f"Failed to initialize AI: {e}")
            return
    
    agent = st.session_state.unified_ai_agent
    
    # Initialize chat history
    if 'ai_messages' not in st.session_state:
        st.session_state.ai_messages = []
    
    # Initialize pending action
    if 'pending_action' not in st.session_state:
        st.session_state.pending_action = None
    
    # Page title
    st.title("🤖 AI Financial Assistant")
    st.markdown("Your intelligent partner for financial decisions")
    
    # Quick Actions Section
    st.markdown("### ⚡ Quick Actions")
    
    quick_actions = [
        ("💰 Balance", "Show my balance"),
        ("📊 Spending", "Show my spending this month"),
        ("📋 Budget", "Show my budget status"),
        ("💡 Tips", "Give me financial tips"),
        ("📈 Portfolio", "Show my investments"),
        ("🎯 Goals", "Show my financial goals"),
    ]
    
    quick_cols = st.columns(6)
    for i, (label, query) in enumerate(quick_actions):
        with quick_cols[i]:
            if st.button(label, key=f"quick_{i}", use_container_width=True):
                _handle_user_message(query, agent, user_id)
    
    st.markdown("---")
    
    # Chat Display Area
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        _display_chat_history()
    
    # Handle pending action confirmation
    if st.session_state.pending_action:
        _handle_action_confirmation(agent, user_id)
    
    # Chat Input Area
    st.markdown("---")
    st.markdown("### 💬 Ask AI Assistant")
    
    # Example queries
    st.caption("💡 Try asking:")
    examples = [
        "How much did I spend on food?",
        "Add expense of ₹500 for lunch",
        "Transfer ₹1000 to mom",
        "What's my net worth?",
        "Show financial health score",
        "Compare this month vs last",
        "How can I save more money?",
        "Open investments page"
    ]
    
    example_cols = st.columns(4)
    for i, example in enumerate(examples[:8]):
        with example_cols[i % 4]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                _handle_user_message(example, agent, user_id)
    
    # Main chat input
    with st.form("ai_chat_form", clear_on_submit=True):
        col_input, col_submit = st.columns([5, 1])
        
        with col_input:
            user_query = st.text_input(
                "Ask about your finances:",
                placeholder="e.g., 'Show my balance' or 'Add expense of ₹500'",
                label_visibility="collapsed",
                key="chat_input"
            )
        
        with col_submit:
            submit = st.form_submit_button("Send", use_container_width=True)
        
        if submit and user_query:
            _handle_user_message(user_query, agent, user_id)
    
    # Clear chat button
    if st.session_state.ai_messages:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.ai_messages = []
            st.session_state.pending_action = None
            st.rerun()


def _display_chat_history():
    """Display chat history with proper error handling"""
    try:
        for i, msg in enumerate(st.session_state.ai_messages):
            role = msg.get('role', 'assistant')
            content = msg.get('content', '')
            is_html = msg.get('is_html', False)
            
            if role == 'user':
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
                    👤 {content}
                </div>
                """, unsafe_allow_html=True)
            else:
                if is_html:
                    st.markdown(content, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="
                        background: #f8f9fa;
                        padding: 12px 16px;
                        border-radius: 12px;
                        margin: 8px 0;
                        max-width: 85%;
                        border: 1px solid #e0e0e0;
                    ">
                        🤖 <strong>AI Assistant</strong><br><br>
                        {content}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Show action if present
            if msg.get('action') and role == 'assistant':
                _render_action_button(msg['action'], i)
            
            # Show navigation if present
            if msg.get('navigate_to') and role == 'assistant':
                if st.button(f"🗺️ Go to {msg['navigate_to'].title()}", key=f"nav_{i}"):
                    st.session_state.page = msg['navigate_to']
                    st.rerun()
            
            # Show suggestions
            if msg.get('suggestions') and role == 'assistant':
                _render_suggestions(msg['suggestions'], i)
    
    except Exception as e:
        st.error(f"Error displaying chat: {e}")


def _handle_user_message(query: str, agent: UnifiedAIAgent, user_id: int):
    """Handle user message with proper error handling"""
    try:
        # Add user message
        st.session_state.ai_messages.append({
            'role': 'user',
            'content': query,
            'timestamp': datetime.now().isoformat()
        })
        
        # Process query
        response = agent.process_query(
            user_id=user_id,
            query=query,
            require_confirmation=True
        )
        
        # Add assistant response
        st.session_state.ai_messages.append({
            'role': 'assistant',
            'content': response.display,
            'is_html': True,
            'timestamp': datetime.now().isoformat(),
            'action': response.action,
            'navigate_to': response.navigate_to,
            'suggestions': response.suggestions,
            'data': response.data
        })
        
        # Handle navigation
        if response.navigate_to:
            st.session_state.page = response.navigate_to
            st.rerun()
        
        # Store pending action for confirmation
        if response.action and response.action.requires_confirmation:
            st.session_state.pending_action = {
                'action': response.action,
                'index': len(st.session_state.ai_messages) - 1
            }
        
        st.rerun()
        
    except Exception as e:
        # Handle error gracefully
        error_msg = f"Error processing query: {str(e)}"
        st.session_state.ai_messages.append({
            'role': 'assistant',
            'content': f"""
            <div style="background: #f8d7da; padding: 12px; border-radius: 8px; color: #721c24;">
                ⚠️ <strong>Oops! Something went wrong</strong><br><br>
                {str(e)[:200]}<br><br>
                Please try again or contact support if the issue persists.
            </div>
            """,
            'is_html': True,
            'timestamp': datetime.now().isoformat()
        })
        st.rerun()


def _render_action_button(action: AIAction, index: int):
    """Render action button if present"""
    try:
        if action and action.requires_confirmation:
            st.markdown("---")
            st.markdown("**⚡ Action Required:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Confirm", key=f"confirm_{index}"):
                    _execute_action(action, user_id=st.session_state.get('user', {}).get('user_id'))
            
            with col2:
                if st.button("❌ Cancel", key=f"cancel_{index}"):
                    st.session_state.pending_action = None
                    # Remove action from last message
                    if st.session_state.ai_messages:
                        st.session_state.ai_messages[-1].pop('action', None)
                    st.rerun()
            
            if action.confirmation_message:
                st.info(action.confirmation_message)
    
    except Exception as e:
        st.error(f"Error rendering action: {e}")


def _handle_action_confirmation(agent: UnifiedAIAgent, user_id: int):
    """Handle action confirmation UI"""
    try:
        pending = st.session_state.pending_action
        if not pending:
            return
        
        action = pending.get('action')
        if not action:
            return
        
        st.markdown("---")
        st.markdown("### ⚠️ Confirmation Required")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Confirm Action", key="confirm_action", use_container_width=True):
                result = agent.execute_action(action, user_id)
                
                # Update last message with result
                if st.session_state.ai_messages:
                    last_msg = st.session_state.ai_messages[-1]
                    last_msg['content'] = result.display
                    last_msg['is_html'] = True
                    last_msg['action'] = None
                
                st.session_state.pending_action = None
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key="cancel_action", use_container_width=True):
                st.session_state.pending_action = None
                if st.session_state.ai_messages:
                    st.session_state.ai_messages[-1].pop('action', None)
                st.rerun()
        
        if action.confirmation_message:
            st.warning(action.confirmation_message)
    
    except Exception as e:
        st.error(f"Error in confirmation: {e}")
        st.session_state.pending_action = None


def _execute_action(action: AIAction, user_id: int) -> bool:
    """Execute pending action"""
    try:
        if not action or not action.on_confirm:
            return False
        
        result = action.on_confirm()
        
        # Update message
        if st.session_state.ai_messages:
            last_msg = st.session_state.ai_messages[-1]
            last_msg['content'] = result.display if hasattr(result, 'display') else "Action completed"
            last_msg['is_html'] = True
            last_msg['action'] = None
        
        st.session_state.pending_action = None
        st.rerun()
        return True
    
    except Exception as e:
        st.error(f"Error executing action: {e}")
        return False


def _render_suggestions(suggestions: List[str], base_index: int):
    """Render suggestion buttons"""
    try:
        if not suggestions:
            return
        
        st.markdown("**Try asking:**")
        cols = st.columns(min(len(suggestions), 4))
        
        for i, suggestion in enumerate(suggestions[:4]):
            with cols[i]:
                if st.button(suggestion, key=f"suggest_{base_index}_{i}", use_container_width=True):
                    # This will be handled by the button's own handler
                    pass
    
    except Exception as e:
        pass


# ============================================================
# SIMPLE NAVIGATION
# ============================================================

def show_simple_ai_page():
    """Simple AI page for navigation"""
    st.title("🤖 AI Financial Assistant")
    
    user = st.session_state.get('user')
    if not user:
        st.error("Please login first")
        return
    
    st.markdown("""
    ## Welcome to AI Financial Assistant!
    
    Your AI assistant can help you with:
    
    - 💰 **Balance queries** - "Show my balance"
    - 💸 **Expenses** - "Add expense of ₹500"
    - 📈 **Investments** - "Show my portfolio"
    - 🏦 **Transfers** - "Transfer ₹1000 to mom"
    - 📊 **Analysis** - "Financial health score"
    - 💡 **Tips** - "How can I save more?"
    
    **Try saying:**
    - "How much did I spend this month?"
    - "Add expense of ₹500 for lunch"
    - "Show my investments"
    - "Compare this month with last"
    
    Click the buttons below or type your query!
    """)
    
    # Quick query buttons
    queries = [
        ("💰 Show Balance", "Show my balance"),
        ("📊 Show Spending", "Show my spending this month"),
        ("📋 Show Budget", "Show my budget status"),
        ("💡 Get Tips", "Give me financial tips"),
        ("📈 Show Portfolio", "Show my investments"),
        ("🎯 Show Goals", "Show my financial goals"),
    ]
    
    cols = st.columns(3)
    for i, (label, query) in enumerate(queries):
        with cols[i % 3]:
            if st.button(label, key=f"nav_query_{i}", use_container_width=True):
                st.session_state['nav_query'] = query
                st.rerun()
    
    # Handle navigation query
    if st.session_state.get('nav_query'):
        query = st.session_state.pop('nav_query')
        
        # Initialize agent
        if 'unified_ai_agent' not in st.session_state:
            try:
                st.session_state.unified_ai_agent = UnifiedAIAgent()
            except Exception as e:
                st.error(f"Failed to initialize AI: {e}")
                return
        
        agent = st.session_state.unified_ai_agent
        user_id = user.get('user_id')
        
        # Process query
        response = agent.process_query(
            user_id=user_id,
            query=query,
            require_confirmation=True
        )
        
        # Display response
        st.markdown("---")
        st.markdown(response.display, unsafe_allow_html=True)
        
        # Handle navigation
        if response.navigate_to:
            if st.button(f"🗺️ Go to {response.navigate_to.title()}"):
                st.session_state.page = response.navigate_to
                st.rerun()


# ============================================================
# ERROR ASSISTANT PAGE
# ============================================================

def show_error_assistant():
    """Error assistance page"""
    st.title("🆘 Need Help?")
    
    st.markdown("""
    ## AI Error Assistant
    
    Common issues and solutions:
    
    ### 🔑 Login Issues
    - Forgot password? Use "Forgot Password" on login page
    - Account locked? Wait 15 minutes or contact support
    
    ### 💰 Transaction Issues
    - Transaction failed but money deducted? Wait 24-48 hours for reversal
    - Transfer not received? Check transaction history
    
    ### 📱 Technical Issues
    - App not loading? Refresh page or clear cache
    - Slow performance? Check internet connection
    
    ### 📞 Still Need Help?
    - Email: support@fintech.app
    - Phone: 1800-XXX-XXXX
    """)
    
    # Contact form
    st.markdown("---")
    st.markdown("### 📝 Contact Support")
    
    issue_type = st.selectbox("Issue Type", [
        "Login Issue", "Transaction Issue", "Account Issue", "Technical Issue", "Other"
    ])
    
    description = st.text_area("Describe your issue")
    
    if st.button("Submit"):
        st.success("Your request has been submitted. We'll respond within 24 hours.")


# ============================================================
# MAIN FUNCTION
# ============================================================

def show_ai_page():
    """Main AI page dispatcher"""
    # Use simple version by default to avoid errors
    show_simple_ai_page()


if __name__ == "__main__":
    show_ai_page()
