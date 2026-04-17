"""
Settings Page
User profile and account settings
"""

import streamlit as st

from database.db import db
from services.auth_service import auth_service


def metric_card(title, value, subtitle="", color="#5B8DEF", bg="#EEF4FF", icon="💰"):
    st.markdown(
        f"""
    <div style="background:{bg}; border-radius:16px; padding:1.5rem; border-left:4px solid {color}; margin-bottom:0.5rem;">
        <div style="font-size:1.5rem;">{icon}</div>
        <div style="color:#6B7280; font-size:0.85rem; font-weight:500; margin:0.4rem 0;">{title}</div>
        <div style="color:#1A1A2E; font-size:1.6rem; font-weight:700;">{value}</div>
        <div style="color:{color}; font-size:0.8rem;">{subtitle}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_settings():
    """Display settings page"""
    user = st.session_state.user
    user_id = user["user_id"]

    st.markdown(
        """
    <div style="padding: 1rem 0 2rem 0;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">⚙️ Settings</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Manage your account</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Tabs
    tab1, tab2 = st.tabs(["👤 Profile", "🔐 Security"])

    # Profile Tab
    with tab1:
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Profile Information</h3>',
            unsafe_allow_html=True,
        )

        # Get fresh user data
        user_data = db.get_user_by_id(user_id)

        col1, col2 = st.columns(2)

        with col1:
            st.text_input("Username", value=user_data["username"], disabled=True)
            st.text_input("Email", value=user_data["email"], disabled=True)

        with col2:
            st.text_input("Mobile", value=user_data["mobile"], disabled=True)
            st.text_input(
                "Member Since", value=user_data["created_at"][:10], disabled=True
            )

        # Balance Overview
        st.markdown("---")
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Balance Overview</h3>',
            unsafe_allow_html=True,
        )

        wallet_balance = user_data["wallet_balance"]

        metric_card(
            title="Wallet Balance",
            value=f"₹{db.to_rupees(wallet_balance):,.2f}",
            subtitle="Available funds",
            color="#5B8DEF",
            bg="#EEF4FF",
            icon="💳",
        )

        # Update Profile
        st.markdown("---")
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Update Profile</h3>',
            unsafe_allow_html=True,
        )

        with st.form("update_profile"):
            new_mobile = st.text_input(
                "New Mobile Number", placeholder="10 digit mobile number"
            )

            submit = st.form_submit_button("Update Mobile", use_container_width=True)

            if submit:
                if new_mobile:
                    valid, msg = auth_service.validate_mobile(new_mobile)
                    if valid:
                        if db.get_user_by_mobile(new_mobile):
                            st.error("Mobile number already registered")
                        else:
                            db.execute(
                                "UPDATE users SET mobile = ? WHERE user_id = ?",
                                (new_mobile, user_id),
                            )
                            st.success("Mobile number updated!")
                            db.log_action("USER", user_id, "Updated mobile number")
                    else:
                        st.error(msg)

    # Security Tab
    with tab2:
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Change Password</h3>',
            unsafe_allow_html=True,
        )

        with st.form("change_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            submit = st.form_submit_button("Change Password", use_container_width=True)

            if submit:
                if current_password and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = auth_service.change_password(
                            user_id, current_password, new_password, "USER"
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")

        st.markdown("---")
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Login Activity</h3>',
            unsafe_allow_html=True,
        )

        # Recent login attempts
        attempts = db.execute(
            """SELECT * FROM login_attempts 
               WHERE email = ? 
               ORDER BY attempt_time DESC 
               LIMIT 10""",
            (user_data["email"],),
            fetch=True,
        )

        if attempts:
            for attempt in attempts:
                status = "✅ Success" if attempt["success"] else "❌ Failed"
                bg = "#EEFAF4" if attempt["success"] else "#FFF4EE"
                st.markdown(
                    f"""
                <div style="background:{bg}; border-radius:8px; padding:0.75rem; margin-bottom:0.5rem;">
                    <span style="color:#1A1A2E;">{attempt["attempt_time"][:16]}</span>
                    <span style="color:#6B7280; margin-left:1rem;">- {status}</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No login attempts recorded")

    # Danger Zone
    st.markdown("---")
    st.markdown(
        '<h3 style="color:#F26C6C; font-size:1.2rem; font-weight:600; margin-bottom:1rem;">⚠️ Danger Zone</h3>',
        unsafe_allow_html=True,
    )

    with st.expander("Delete Account", expanded=False):
        st.warning(
            "This action cannot be undone. All your data will be permanently deleted."
        )

        confirm = st.text_input("Type 'DELETE' to confirm", key="delete_confirm")

        if st.button("Delete My Account", type="secondary"):
            if confirm == "DELETE":
                st.error("Account deletion is disabled in demo mode")
            else:
                st.error("Please type 'DELETE' to confirm")
