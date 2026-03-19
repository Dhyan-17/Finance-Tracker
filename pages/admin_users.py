"""
Admin Users Page
View and search users (read-only, no financial data)
"""

import streamlit as st
import pandas as pd

from database.db import db


def show_admin_users():
    """Display admin users page - READ ONLY, NO FINANCIAL DATA"""
    if 'admin' not in st.session_state or not st.session_state.admin:
        st.error("Please login as admin")
        return
    
    admin = st.session_state.admin
    
    st.title("👥 Users")
    st.info("📋 View and search registered users")
    
    st.markdown("---")
    
    # Search
    search = st.text_input("🔍 Search Users", placeholder="Search by email, username, or mobile...")
    
    # Get all users
    users = db.get_all_users(limit=100)
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        users = [u for u in users if 
                 search_lower in u['username'].lower() or
                 search_lower in u['email'].lower() or
                 search_lower in str(u['mobile'])]
    
    # Summary
    col1, col2 = st.columns(2)
    
    with col1:
        total_users = len(users)
        st.metric("Total Users", total_users)
    
    st.markdown("---")
    
    # Users Table
    if users:
        df_data = []
        for u in users:
            # Format joined date
            joined = u.get('created_at', 'N/A')
            if joined:
                joined = joined[:10] if ' ' in joined else joined
            else:
                joined = 'N/A'
            
            # Format last login
            last_login = u.get('last_login', 'Never')
            if last_login:
                last_login = last_login[:16] if ' ' in last_login else last_login
            else:
                last_login = 'Never'
            
            df_data.append({
                'ID': u['user_id'],
                'Username': u['username'],
                'Email': u['email'],
                'Mobile': u['mobile'],
                'Joined': joined,
                'Last Login': last_login
        })
        
        df = pd.DataFrame(df_data)
        
        # Display table
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.caption(f"Showing {len(users)} users")
    else:
        st.info("No users found")
