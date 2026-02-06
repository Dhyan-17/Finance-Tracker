"""
Smart Finance Tracker - Main Streamlit Application
Production-level Fintech Dashboard
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import db
from services.auth_service import auth_service

# Page configuration
st.set_page_config(
    page_title="Smart Finance Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .metric-card-green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    
    .metric-card-orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    .metric-card-blue {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* Success/Error messages */
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 8px;
        color: #155724;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        padding: 1rem;
        border-radius: 8px;
        color: #721c24;
    }
    
    /* Tables */
    .dataframe {
        font-size: 0.9rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'admin' not in st.session_state:
        st.session_state.admin = None
    if 'page' not in st.session_state:
        st.session_state.page = 'home'


def show_login_page():
    """Display login/register page"""
    st.title("💰 Smart Finance Tracker")
    st.markdown("### Your Personal Financial Dashboard")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2, tab3 = st.tabs(["🔐 User Login", "📝 Register", "👨‍💼 Admin Login"])
        
        # User Login Tab
        with tab1:
            st.markdown("#### Welcome Back!")
            
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input("Password", type="password", placeholder="••••••••")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    submit = st.form_submit_button("Login", use_container_width=True)
                
                if submit:
                    if email and password:
                        success, message, user_data = auth_service.login_user(email, password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user = user_data
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter email and password")
        
        # Register Tab
        with tab2:
            st.markdown("#### Create Account")
            
            with st.form("register_form"):
                username = st.text_input("Username", placeholder="johndoe")
                email = st.text_input("Email", placeholder="your@email.com", key="reg_email")
                mobile = st.text_input("Mobile", placeholder="9876543210")
                password = st.text_input("Password", type="password", placeholder="Min 8 characters", key="reg_pass")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="••••••••")
                
                submit = st.form_submit_button("Register", use_container_width=True)
                
                if submit:
                    success, message, user_id = auth_service.register_user(
                        username, email, mobile, password, confirm_password
                    )
                    if success:
                        st.success(message + " Please login.")
                    else:
                        st.error(message)
        
        # Admin Login Tab
        with tab3:
            st.markdown("#### Admin Access")
            
            with st.form("admin_login_form"):
                admin_email = st.text_input("Admin Email", placeholder="admin@example.com")
                admin_password = st.text_input("Password", type="password", placeholder="••••••••", key="admin_pass")
                
                submit = st.form_submit_button("Admin Login", use_container_width=True)
                
                if submit:
                    if admin_email and admin_password:
                        success, message, admin_data = auth_service.login_admin(admin_email, admin_password)
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.admin = admin_data
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter email and password")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>Smart Finance Tracker v2.0 | Secure & Private</p>",
        unsafe_allow_html=True
    )


def show_sidebar():
    """Display navigation sidebar"""
    with st.sidebar:
        if st.session_state.user:
            st.markdown(f"### 👤 {st.session_state.user['username']}")
            st.markdown(f"*{st.session_state.user['email']}*")
            st.markdown("---")
            
            # Navigation
            st.markdown("### 📍 Navigation")
            
            if st.button("🏠 Dashboard", use_container_width=True):
                st.session_state.page = 'dashboard'
                st.rerun()
            
            if st.button("💳 Wallet", use_container_width=True):
                st.session_state.page = 'wallet'
                st.rerun()
            
            if st.button("📊 Transactions", use_container_width=True):
                st.session_state.page = 'transactions'
                st.rerun()
            
            if st.button("📋 Budgets", use_container_width=True):
                st.session_state.page = 'budgets'
                st.rerun()
            
            if st.button("📈 Investments", use_container_width=True):
                st.session_state.page = 'investments'
                st.rerun()
            
            if st.button("🎯 Goals", use_container_width=True):
                st.session_state.page = 'goals'
                st.rerun()
            
            if st.button("📉 Analytics", use_container_width=True):
                st.session_state.page = 'analytics'
                st.rerun()
            
            if st.button("🤖 AI Assistant", use_container_width=True):
                st.session_state.page = 'ai_assistant'
                st.rerun()
            
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.page = 'settings'
                st.rerun()
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                auth_service.logout(st.session_state.user['user_id'])
                st.session_state.clear()
                st.rerun()
        
        elif st.session_state.admin:
            st.markdown(f"### 👨‍💼 {st.session_state.admin['name']}")
            st.markdown(f"*{st.session_state.admin['role']}*")
            st.markdown("---")
            
            # Admin Navigation
            st.markdown("### 📍 Admin Panel")
            
            if st.button("🏠 Dashboard", use_container_width=True, key="admin_dash"):
                st.session_state.page = 'admin_dashboard'
                st.rerun()
            
            if st.button("👥 Users", use_container_width=True):
                st.session_state.page = 'admin_users'
                st.rerun()
            
            if st.button("💰 Transactions", use_container_width=True, key="admin_txn"):
                st.session_state.page = 'admin_transactions'
                st.rerun()
            
            if st.button("🚨 Fraud Detection", use_container_width=True):
                st.session_state.page = 'admin_fraud'
                st.rerun()
            
            if st.button("📊 Analytics", use_container_width=True, key="admin_analytics"):
                st.session_state.page = 'admin_analytics'
                st.rerun()
            
            if st.button("📈 Market", use_container_width=True):
                st.session_state.page = 'admin_market'
                st.rerun()
            
            if st.button("📜 Logs", use_container_width=True):
                st.session_state.page = 'admin_logs'
                st.rerun()
            
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True, key="admin_logout"):
                auth_service.logout(st.session_state.admin['admin_id'], 'ADMIN')
                st.session_state.clear()
                st.rerun()


def main():
    """Main application entry point"""
    init_session_state()
    
    # Check authentication
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Show sidebar
    show_sidebar()
    
    # Route to appropriate page
    if st.session_state.user:
        # User pages
        if st.session_state.page == 'dashboard':
            from pages.dashboard import show_dashboard
            show_dashboard()
        elif st.session_state.page == 'wallet':
            from pages.wallet import show_wallet
            show_wallet()
        elif st.session_state.page == 'transactions':
            from pages.transactions import show_transactions
            show_transactions()
        elif st.session_state.page == 'budgets':
            from pages.budgets import show_budgets
            show_budgets()
        elif st.session_state.page == 'investments':
            from pages.investments import show_investments
            show_investments()
        elif st.session_state.page == 'goals':
            from pages.goals import show_goals
            show_goals()
        elif st.session_state.page == 'analytics':
            from pages.user_analytics import show_user_analytics
            show_user_analytics()
        elif st.session_state.page == 'ai_assistant':
            from pages.ai_chat import show_ai_assistant
            show_ai_assistant()
        elif st.session_state.page == 'settings':
            from pages.settings import show_settings
            show_settings()
        else:
            from pages.dashboard import show_dashboard
            show_dashboard()
    
    elif st.session_state.admin:
        # Admin pages
        if st.session_state.page == 'admin_dashboard':
            from pages.admin_dashboard import show_admin_dashboard
            show_admin_dashboard()
        elif st.session_state.page == 'admin_users':
            from pages.admin_users import show_admin_users
            show_admin_users()
        elif st.session_state.page == 'admin_transactions':
            from pages.admin_transactions import show_admin_transactions
            show_admin_transactions()
        elif st.session_state.page == 'admin_fraud':
            from pages.admin_fraud import show_admin_fraud
            show_admin_fraud()
        elif st.session_state.page == 'admin_analytics':
            from pages.admin_analytics import show_admin_analytics
            show_admin_analytics()
        elif st.session_state.page == 'admin_market':
            from pages.admin_market import show_admin_market
            show_admin_market()
        elif st.session_state.page == 'admin_logs':
            from pages.admin_logs import show_admin_logs
            show_admin_logs()
        else:
            from pages.admin_dashboard import show_admin_dashboard
            show_admin_dashboard()


if __name__ == "__main__":
    main()
