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
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
<style>
    /* Main App Background */
    .stApp {
        background-color: #F8F9FB;
    }
    
    /* Main container */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #FFFFFF;
        border-right: 1px solid #E8ECF0;
    }
    
    /* Buttons - Primary Style */
    .stButton>button {
        background: #FFFFFF;
        border: 1.5px solid #5B8DEF;
        color: #5B8DEF;
        border-radius: 10px;
        font-weight: 500;
        padding: 0.4rem 1rem;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background: #5B8DEF;
        color: white;
    }

    /* Buttons - Secondary Style */
    .stButton>button[kind="secondary"] {
        background: transparent;
        border: 1.5px solid #E8ECF0;
        color: #6B7280;
    }
    
    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.07);
        border: 1px solid #E8ECF0;
        margin-bottom: 1rem;
    }
    
    .metric-card-blue {
        background: linear-gradient(135deg, #EEF4FF 0%, #F5F8FF 100%);
        border-left: 4px solid #5B8DEF;
    }
    
    .metric-card-green {
        background: linear-gradient(135deg, #EEFAF4 0%, #F0FFF8 100%);
        border-left: 4px solid #43A87B;
    }
    
    .metric-card-coral {
        background: linear-gradient(135deg, #FFF4EE 0%, #FFF8F6 100%);
        border-left: 4px solid #F26C6C;
    }
    
    .metric-card-purple {
        background: linear-gradient(135deg, #F5F0FF 0%, #FAF6FF 100%);
        border-left: 4px solid #AB8EE8;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0 24px;
        border-radius: 10px 10px 0 0;
        background: transparent;
        color: #6B7280;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: #FFFFFF;
        color: #5B8DEF;
        border-bottom: 2px solid #5B8DEF;
    }
    
    /* Input fields */
    .stTextInput>div>div>input,
    .stPassword>div>div>input {
        border-radius: 8px;
        border: 1.5px solid #E8ECF0;
        background: #FAFAFA;
        padding: 0.5rem 1rem;
    }
    
    .stTextInput>div>div>input:focus,
    .stPassword>div>div>input:focus {
        border-color: #5B8DEF;
        box-shadow: 0 0 0 2px rgba(91,141,239,0.1);
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #1A1A2E;
        font-weight: 600;
    }
    
    h1 { font-size: 2rem; }
    h2 { font-size: 1.5rem; }
    h3 { font-size: 1.25rem; }
    
    /* Metrics */
    .stMetric {
        background: #FFFFFF;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #E8ECF0;
    }
    
    /* DataFrames */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Dividers */
    hr {
        border: none;
        border-top: 1px solid #E8ECF0;
        margin: 1.5rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove all empty/extra boxes and containers */
    div[data-testid="stVerticalBlock"] > div:empty {
        display: none !important;
    }
    
    /* Remove empty stBlock containers */
    div.block-container > div:empty {
        display: none !important;
    }
    
    /* Hide empty element containers */
    div[data-testid="element-container"]:empty {
        display: none !important;
    }
    
    /* Remove blank stForm borders if empty */
    div[data-testid="stForm"]:empty {
        display: none !important;
    }
    
    /* Remove extra padding from empty blocks */
    div[data-testid="stVerticalBlock"] > div > div:empty {
        height: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #EEFAF4;
        border: 1px solid #43A87B;
        color: #43A87B;
        border-radius: 10px;
    }
    
    .stError {
        background-color: #FFF4EE;
        border: 1px solid #F26C6C;
        color: #F26C6C;
        border-radius: 10px;
    }
    
    /* Form styling */
    .stForm {
        background: transparent;
    }
    
    /* Select boxes */
    .stSelectbox>div>div>div {
        border-radius: 8px;
        border: 1.5px solid #E8ECF0;
        background: #FAFAFA;
    }
    
    /* Date inputs */
    .stDateInput>div>div>input {
        border-radius: 8px;
        border: 1.5px solid #E8ECF0;
        background: #FAFAFA;
    }
    
    /* Number inputs */
    .stNumberInput>div>div>input {
        border-radius: 8px;
        border: 1.5px solid #E8ECF0;
        background: #FAFAFA;
    }
    
    /* Text area */
    .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1.5px solid #E8ECF0;
        background: #FAFAFA;
    }
    
    /* MultiSelect */
    .stMultiSelect>div>div>div {
        border-radius: 8px;
        border: 1.5px solid #E8ECF0;
        background: #FAFAFA;
    }
    
    /* Slider */
    .stSlider [data-baseweb="slider"] {
        color: #5B8DEF;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: #5B8DEF;
        border-radius: 10px;
    }
    
    /* Checkbox */
    .stCheckbox [data-baseweb="checkbox"] {
        color: #5B8DEF;
    }
    
    /* Radio */
    .stRadio [data-baseweb="radio"] {
        color: #5B8DEF;
    }
    
    /* Segmented Control */
    .stSegmentedControl [data-baseweb="segmented-control"] {
        background: #FAFAFA;
        border-radius: 10px;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "admin" not in st.session_state:
        st.session_state.admin = None
    if "page" not in st.session_state:
        st.session_state.page = "home"


def show_login_page():
    """Display login/register page"""
    # Hero Section
    st.markdown(
        """
    <div style="text-align:center; padding: 2rem 0 1rem 0;">
        <div style="font-size:3rem;">💰</div>
        <h1 style="color:#1A1A2E; font-size:2rem; font-weight:700; margin:0.5rem 0;">Smart Finance Tracker</h1>
        <p style="color:#6B7280; font-size:1rem;">Take control of your financial life</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab1, tab2, tab3 = st.tabs(["🔐 User Login", "📝 Register", "👨‍💼 Admin Login"])

        # User Login Tab
        with tab1:
            st.markdown("#### Welcome Back!")

            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input(
                    "Password", type="password", placeholder="••••••••"
                )
                submit = st.form_submit_button("Login", use_container_width=True)

                if submit:
                    if email and password:
                        success, message, user_data = auth_service.login_user(
                            email, password
                        )
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
                    email = st.text_input(
                        "Email", placeholder="your@email.com", key="reg_email"
                    )
                    mobile = st.text_input("Mobile", placeholder="9876543210")
                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Min 8 characters",
                        key="reg_pass",
                    )
                    confirm_password = st.text_input(
                        "Confirm Password", type="password", placeholder="••••••••"
                    )

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
                admin_email = st.text_input(
                    "Admin Email", placeholder="admin@example.com"
                )
                admin_password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="••••••••",
                    key="admin_pass",
                )

                submit = st.form_submit_button("Admin Login", use_container_width=True)

                if submit:
                    if admin_email and admin_password:
                        success, message, admin_data = auth_service.login_admin(
                            admin_email, admin_password
                        )
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
        "<p style='text-align: center; color: #6B7280;'>Smart Finance Tracker v2.0 | Secure & Private</p>",
        unsafe_allow_html=True,
    )


def show_sidebar():
    """Display navigation sidebar"""
    with st.sidebar:
        # Brand / Logo Section
        st.markdown(
            """
        <div style="padding: 1rem 0; border-bottom: 1px solid #E8ECF0; margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="font-size: 1.8rem;">💰</div>
                <div>
                    <div style="font-weight: 600; color: #1A1A2E; font-size: 1rem;">Finance Tracker</div>
                    <div style="color: #6B7280; font-size: 0.75rem;">Personal Dashboard</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if st.session_state.user:
            # User Profile Section
            st.markdown(
                f"""
            <div style="background: #EEF4FF; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: #5B8DEF; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.2rem;">👤</div>
                    <div>
                        <div style="font-weight: 600; color: #1A1A2E; font-size: 0.95rem;">{st.session_state.user["username"]}</div>
                        <div style="color: #6B7280; font-size: 0.75rem;">{st.session_state.user["email"]}</div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # Navigation
            st.markdown(
                '<div style="color:#6B7280; font-size:0.75rem; font-weight:600; margin-bottom:0.5rem; text-transform:uppercase;">Menu</div>',
                unsafe_allow_html=True,
            )

            pages = [
                ("🏠", "Dashboard", "dashboard"),
                ("💳", "Wallet", "wallet"),
                ("📊", "Transactions", "transactions"),
                ("📋", "Budgets", "budgets"),
                ("📈", "Investments", "investments"),
                ("🎯", "Goals", "goals"),
                ("📉", "Analytics", "analytics"),
                ("⚙️", "Settings", "settings"),
            ]

            for icon, label, page in pages:
                if st.button(f"{icon} {label}", use_container_width=True):
                    st.session_state.page = page
                    st.rerun()

            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                auth_service.logout(st.session_state.user["user_id"])
                st.session_state.clear()
                st.rerun()

        elif st.session_state.admin:
            # Admin Profile Section
            st.markdown(
                f"""
            <div style="background: #F5F0FF; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="background: #AB8EE8; border-radius: 50%; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.2rem;">👨‍💼</div>
                    <div>
                        <div style="font-weight: 600; color: #1A1A2E; font-size: 0.95rem;">{st.session_state.admin["name"]}</div>
                        <div style="color: #6B7280; font-size: 0.75rem;">{st.session_state.admin["role"]}</div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # Admin Navigation
            st.markdown(
                '<div style="color:#6B7280; font-size:0.75rem; font-weight:600; margin-bottom:0.5rem; text-transform:uppercase;">Admin Panel</div>',
                unsafe_allow_html=True,
            )

            admin_pages = [
                ("👥", "Users", "admin_users"),
                ("📈", "Market", "admin_market"),
                ("📜", "Logs", "admin_logs"),
            ]

            for icon, label, page in admin_pages:
                if st.button(f"{icon} {label}", use_container_width=True):
                    st.session_state.page = page
                    st.rerun()

            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True, key="admin_logout"):
                auth_service.logout(st.session_state.admin["admin_id"], "ADMIN")
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
        if st.session_state.page == "dashboard":
            from page_modules.dashboard import show_dashboard

            show_dashboard()
        elif st.session_state.page == "wallet":
            from page_modules.wallet import show_wallet

            show_wallet()
        elif st.session_state.page == "transactions":
            from page_modules.transactions import show_transactions

            show_transactions()
        elif st.session_state.page == "budgets":
            from page_modules.budgets import show_budgets

            show_budgets()
        elif st.session_state.page == "investments":
            from page_modules.investments import show_investments

            show_investments()
        elif st.session_state.page == "goals":
            from page_modules.goals import show_goals

            show_goals()
        elif st.session_state.page == "analytics":
            from page_modules.user_analytics import show_user_analytics

            show_user_analytics()
        elif st.session_state.page == "settings":
            from page_modules.settings import show_settings

            show_settings()
        else:
            from page_modules.dashboard import show_dashboard

            show_dashboard()

    elif st.session_state.admin:
        # Admin pages - Only Users, Market, Logs
        if st.session_state.page == "admin_users":
            from page_modules.admin_users import show_admin_users

            show_admin_users()
        elif st.session_state.page == "admin_market":
            from page_modules.admin_market import show_admin_market

            show_admin_market()
        elif st.session_state.page == "admin_logs":
            from page_modules.admin_logs import show_admin_logs

            show_admin_logs()
        else:
            from page_modules.admin_users import show_admin_users

            show_admin_users()


if __name__ == "__main__":
    main()
