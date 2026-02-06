"""
Admin Users Page
User management for administrators
"""

import streamlit as st
import pandas as pd

from database.db import db
from services.auth_service import auth_service


def show_admin_users():
    """Display admin users management page"""
    admin = st.session_state.admin
    admin_id = admin['admin_id']
    
    st.title("👥 User Management")
    
    # Search and Filter
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search = st.text_input("🔍 Search", placeholder="Search by email, username, or mobile...")
    
    with col2:
        status_filter = st.selectbox("Status", ["All", "ACTIVE", "BLOCKED", "SUSPENDED"])
    
    with col3:
        limit = st.selectbox("Show", [25, 50, 100], index=0)
    
    # Get users
    if status_filter == "All":
        users = db.get_all_users(limit=limit)
    else:
        users = db.get_all_users(status=status_filter, limit=limit)
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        users = [u for u in users if 
                 search_lower in u['username'].lower() or
                 search_lower in u['email'].lower() or
                 search_lower in str(u['mobile'])]
    
    st.markdown("---")
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", len(users))
    with col2:
        active = sum(1 for u in users if u['status'] == 'ACTIVE')
        st.metric("Active", active)
    with col3:
        blocked = sum(1 for u in users if u['status'] == 'BLOCKED')
        st.metric("Blocked", blocked)
    with col4:
        total_balance = sum(db.to_rupees(u['wallet_balance'] or 0) for u in users)
        st.metric("Total Wallets", f"₹{total_balance:,.0f}")
    
    st.markdown("---")
    
    # Users Table
    if users:
        df_data = []
        for u in users:
            df_data.append({
                'ID': u['user_id'],
                'Username': u['username'],
                'Email': u['email'],
                'Mobile': u['mobile'],
                'Balance': f"₹{db.to_rupees(u['wallet_balance'] or 0):,.2f}",
                'Status': u['status'],
                'KYC': '✅' if u['kyc_verified'] else '❌',
                'Joined': u['created_at'][:10] if u['created_at'] else 'N/A'
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No users found")
    
    st.markdown("---")
    
    # User Actions
    st.subheader("⚡ User Actions")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 View User", "🔒 Block/Unblock", "🔑 Reset Password", "🗑️ Delete User"])
    
    # View User Tab
    with tab1:
        user_id_view = st.number_input("User ID", min_value=1, step=1, key="view_id")
        
        if st.button("View Details"):
            user = db.get_user_by_id(user_id_view)
            
            if user:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"👤 {user['username']}")
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Mobile:** {user['mobile']}")
                    st.write(f"**Status:** {user['status']}")
                    st.write(f"**KYC:** {'Verified' if user['kyc_verified'] else 'Pending'}")
                    st.write(f"**Joined:** {user['created_at'][:10]}")
                    st.write(f"**Last Login:** {user.get('last_login', 'Never')[:16] if user.get('last_login') else 'Never'}")
                
                with col2:
                    st.write(f"**Wallet Balance:** ₹{db.to_rupees(user['wallet_balance'] or 0):,.2f}")
                    
                    bank_balance = db.get_total_bank_balance(user_id_view)
                    st.write(f"**Bank Balance:** ₹{db.to_rupees(bank_balance):,.2f}")
                    
                    investment = db.get_total_investment_value(user_id_view)
                    st.write(f"**Investments:** ₹{db.to_rupees(investment['current_value']):,.2f}")
                    
                    net_worth = user['wallet_balance'] + bank_balance + investment['current_value']
                    st.write(f"**Net Worth:** ₹{db.to_rupees(net_worth):,.2f}")
                
                # Recent Activity
                st.markdown("---")
                st.subheader("Recent Activity")
                
                expenses = db.get_user_expenses(user_id_view, limit=5)
                if expenses:
                    st.write("**Recent Expenses:**")
                    for e in expenses:
                        st.write(f"  • {e['date'][:10]} | {e['category']} | ₹{db.to_rupees(e['amount']):,.0f}")
            else:
                st.error("User not found")
    
    # Block/Unblock Tab
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            user_id_block = st.number_input("User ID", min_value=1, step=1, key="block_id")
        
        with col2:
            action = st.selectbox("Action", ["BLOCK", "UNBLOCK"])
        
        reason = st.text_input("Reason (required)")
        
        if st.button("Execute", key="block_btn"):
            if reason:
                user = db.get_user_by_id(user_id_block)
                
                if user:
                    new_status = "BLOCKED" if action == "BLOCK" else "ACTIVE"
                    db.update_user_status(user_id_block, new_status)
                    
                    db.log_action(
                        'ADMIN', admin_id,
                        f"{action} user {user['username']}: {reason}",
                        'USER', user_id_block,
                        severity='WARNING'
                    )
                    
                    # Notify user
                    db.add_notification(
                        user_id_block,
                        f"Account {action.lower()}ed",
                        f"Your account has been {action.lower()}ed. Reason: {reason}",
                        "WARNING" if action == "BLOCK" else "SUCCESS"
                    )
                    
                    st.success(f"User {user['username']} has been {action.lower()}ed")
                else:
                    st.error("User not found")
            else:
                st.error("Please provide a reason")
    
    # Reset Password Tab
    with tab3:
        user_id_reset = st.number_input("User ID", min_value=1, step=1, key="reset_id")
        new_password = st.text_input("New Password", type="password")
        
        if st.button("Reset Password"):
            if new_password:
                success, message = auth_service.reset_user_password(
                    user_id_reset, new_password, admin_id
                )
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("Please enter a new password")
    
    # Delete User Tab
    with tab4:
        st.warning("⚠️ This action is irreversible!")
        
        user_id_delete = st.number_input("User ID", min_value=1, step=1, key="delete_id")
        confirm = st.text_input("Type 'DELETE' to confirm")
        
        if st.button("Delete User", type="secondary"):
            if confirm == "DELETE":
                user = db.get_user_by_id(user_id_delete)
                
                if user:
                    # Check if user has balance
                    if user['wallet_balance'] > 0:
                        st.error("Cannot delete user with non-zero balance")
                    else:
                        db.execute(
                            "DELETE FROM users WHERE user_id = ?",
                            (user_id_delete,)
                        )
                        
                        db.log_action(
                            'ADMIN', admin_id,
                            f"Deleted user {user['username']}",
                            'USER', user_id_delete,
                            severity='CRITICAL'
                        )
                        
                        st.success(f"User {user['username']} deleted")
                else:
                    st.error("User not found")
            else:
                st.error("Please type 'DELETE' to confirm")
    
    # Create Admin (Super Admin only)
    if admin['role'] == 'SUPER_ADMIN':
        st.markdown("---")
        st.subheader("➕ Create New Admin")
        
        with st.form("create_admin"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name")
                email = st.text_input("Email", key="admin_email")
            
            with col2:
                password = st.text_input("Password", type="password", key="admin_pass")
                role = st.selectbox("Role", ["ADMIN", "ANALYST"])
            
            if st.form_submit_button("Create Admin"):
                if name and email and password:
                    success, message, new_id = auth_service.create_admin(
                        name, email, password, role, admin_id
                    )
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
