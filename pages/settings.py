"""
Settings Page
User profile and account settings
"""

import streamlit as st

from database.db import db
from services.auth_service import auth_service


def show_settings():
    """Display settings page"""
    user = st.session_state.user
    user_id = user['user_id']
    
    st.title("⚙️ Settings")
    
    # Tabs
    tab1, tab2 = st.tabs(["👤 Profile", "🔐 Security"])
    
    # Profile Tab
    with tab1:
        st.subheader("Profile Information")
        
        # Get fresh user data
        user_data = db.get_user_by_id(user_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Username", value=user_data['username'], disabled=True)
            st.text_input("Email", value=user_data['email'], disabled=True)
        
        with col2:
            st.text_input("Mobile", value=user_data['mobile'], disabled=True)
            st.text_input("Member Since", value=user_data['created_at'][:10], disabled=True)
        
        # Balance Overview
        st.markdown("---")
        st.subheader("Balance Overview")
        
        wallet_balance = user_data['wallet_balance']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Wallet Balance", f"₹{db.to_rupees(wallet_balance):,.2f}")
        
        # Update Profile
        st.markdown("---")
        st.subheader("Update Profile")
        
        with st.form("update_profile"):
            new_mobile = st.text_input("New Mobile Number", placeholder="10 digit mobile number")
            
            submit = st.form_submit_button("Update Mobile", width='stretch')
            
            if submit:
                if new_mobile:
                    valid, msg = auth_service.validate_mobile(new_mobile)
                    if valid:
                        # Check if mobile exists
                        if db.get_user_by_mobile(new_mobile):
                            st.error("Mobile number already registered")
                        else:
                            db.execute(
                                "UPDATE users SET mobile = ? WHERE user_id = ?",
                                (new_mobile, user_id)
                            )
                            st.success("Mobile number updated successfully!")
                            db.log_action('USER', user_id, 'Updated mobile number')
                    else:
                        st.error(msg)
    
    # Security Tab
    with tab2:
        st.subheader("Change Password")
        
        with st.form("change_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            submit = st.form_submit_button("Change Password", width='stretch')
            
            if submit:
                if current_password and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = auth_service.change_password(
                            user_id, current_password, new_password, 'USER'
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")
        
        st.markdown("---")
        st.subheader("Login Activity")
        
        # Recent login attempts
        attempts = db.execute(
            """SELECT * FROM login_attempts 
               WHERE email = ? 
               ORDER BY attempt_time DESC 
               LIMIT 10""",
            (user_data['email'],),
            fetch=True
        )
        
        if attempts:
            for attempt in attempts:
                status = "✅ Success" if attempt['success'] else "❌ Failed"
                st.write(f"{attempt['attempt_time'][:16]} - {status}")
        else:
            st.info("No login attempts recorded")
        
    
    # Danger Zone
    st.markdown("---")
    st.subheader("⚠️ Danger Zone")
    
    with st.expander("Delete Account", expanded=False):
        st.warning("This action cannot be undone. All your data will be permanently deleted.")
        
        confirm = st.text_input("Type 'DELETE' to confirm", key="delete_confirm")
        
        if st.button("Delete My Account", type="secondary"):
            if confirm == "DELETE":
                # In production, this would soft-delete or schedule deletion
                st.error("Account deletion is disabled in demo mode")
            else:
                st.error("Please type 'DELETE' to confirm")
