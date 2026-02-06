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
    tab1, tab2, tab3 = st.tabs(["👤 Profile", "🔐 Security", "🔔 Notifications"])
    
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
        
        # Account Status
        st.markdown("---")
        st.subheader("Account Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_color = "🟢" if user_data['status'] == 'ACTIVE' else "🔴"
            st.metric("Status", f"{status_color} {user_data['status']}")
        
        with col2:
            kyc = "✅ Verified" if user_data['kyc_verified'] else "❌ Pending"
            st.metric("KYC Status", kyc)
        
        with col3:
            st.metric("Last Login", user_data.get('last_login', 'N/A')[:16] if user_data.get('last_login') else 'N/A')
        
        # Update Profile
        st.markdown("---")
        st.subheader("Update Profile")
        
        with st.form("update_profile"):
            new_mobile = st.text_input("New Mobile Number", placeholder="10 digit mobile number")
            
            submit = st.form_submit_button("Update Mobile", use_container_width=True)
            
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
            
            submit = st.form_submit_button("Change Password", use_container_width=True)
            
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
        
        st.markdown("---")
        st.subheader("Active Sessions")
        
        sessions = db.execute(
            """SELECT * FROM sessions 
               WHERE user_id = ? AND is_active = 1
               ORDER BY created_at DESC""",
            (user_id,),
            fetch=True
        )
        
        if sessions:
            for session in sessions:
                st.write(f"🔐 Session active since {session['created_at'][:16]}")
                if st.button("Revoke", key=f"revoke_{session['session_id'][:8]}"):
                    auth_service.invalidate_session(session['session_id'])
                    st.success("Session revoked")
                    st.rerun()
        else:
            st.info("No active sessions")
    
    # Notifications Tab
    with tab3:
        st.subheader("Notification Preferences")
        
        st.markdown("*Notification settings coming soon!*")
        
        # Show recent notifications
        st.markdown("---")
        st.subheader("Recent Notifications")
        
        notifications = db.get_user_notifications(user_id, limit=20)
        
        if notifications:
            for notif in notifications:
                with st.expander(f"{'🔵' if not notif['is_read'] else '⚪'} {notif['title']}", expanded=not notif['is_read']):
                    st.write(notif['message'])
                    st.caption(notif['created_at'][:16])
                    
                    if not notif['is_read']:
                        if st.button("Mark as Read", key=f"read_{notif['notification_id']}"):
                            db.mark_notification_read(notif['notification_id'], user_id)
                            st.rerun()
            
            if st.button("Mark All as Read", use_container_width=True):
                db.execute(
                    "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
                    (user_id,)
                )
                st.success("All notifications marked as read")
                st.rerun()
        else:
            st.info("No notifications")
    
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
