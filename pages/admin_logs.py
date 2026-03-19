"""
Admin Logs Page
Shows only user login/logout and admin market changes
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from database.db import db


def show_admin_logs():
    """Display admin logs page - SIMPLE VIEW"""
    if 'admin' not in st.session_state or not st.session_state.admin:
        st.error("Please login as admin")
        return
    
    admin = st.session_state.admin
    
    st.title("📜 System Logs")
    st.info("🔍 User login/logout & Admin market changes")
    
    st.markdown("---")
    
    # Time Range
    col1, col2 = st.columns([1, 3])
    
    with col1:
        days = st.selectbox("Time Range", [1, 7, 14, 30, 60, 90], index=3, 
                           format_func=lambda x: f"Last {x} days")
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # User Login/Logout Logs
    st.subheader("🔐 User Login/Logout")
    
    user_logs = db.execute(
        """SELECT created_at, actor_type, action 
           FROM audit_logs 
           WHERE created_at >= ? AND action LIKE '%logged%'
           ORDER BY created_at DESC LIMIT 100""",
        (start_date,),
        fetch=True
    )
    
    if user_logs:
        for log in user_logs:
            action_lower = log['action'].lower()
            if 'logged in' in action_lower or 'logged out' in action_lower:
                icon = "✅" if 'in' in action_lower else "🚪"
                st.markdown(
                    f"""
                    <div style='padding: 8px; margin: 3px 0; border-left: 4px solid #27ae60; background: #f8f9fa;'>
                        <strong>{log['created_at'][:19]}</strong> {icon}
                        <br/>
                        <span style='color: #333;'>{log['action']}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    else:
        st.info("No login/logout records found")
    
    st.markdown("---")
    
    # Admin Market Changes
    st.subheader("📈 Admin Market Price Changes")
    
    market_logs = db.execute(
        """SELECT created_at, action 
           FROM audit_logs 
           WHERE created_at >= ? AND (action LIKE '%price%' OR action LIKE '%market%' OR action LIKE '%updated%asset%')
           ORDER BY created_at DESC LIMIT 100""",
        (start_date,),
        fetch=True
    )
    
    if market_logs:
        for log in market_logs:
            st.markdown(
                f"""
                <div style='padding: 8px; margin: 3px 0; border-left: 4px solid #3498db; background: #f8f9fa;'>
                    <strong>{log['created_at'][:19]}</strong> 📊
                    <br/>
                    <span style='color: #333;'>{log['action']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No market changes recorded")
    
    st.markdown("---")
    
    # Summary counts
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Login/Logout Events", len(user_logs) if user_logs else 0)
    with col2:
        st.metric("Market Changes", len(market_logs) if market_logs else 0)
