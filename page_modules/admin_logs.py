"""
Admin Logs Page
Shows only user login/logout and admin market changes
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from database.db import db


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


def show_admin_logs():
    """Display admin logs page - SIMPLE VIEW"""
    if "admin" not in st.session_state or not st.session_state.admin:
        st.error("Please login as admin")
        return

    admin = st.session_state.admin

    st.markdown(
        """
    <div style="background:#F0F4FF; border-radius:16px; padding:1.5rem; border:1px solid #AB8EE8; margin-bottom:2rem;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">📜 System Logs</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">User login/logout & Admin market changes</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Time Range
    col1, col2 = st.columns([1, 3])

    with col1:
        days = st.selectbox(
            "Time Range",
            [1, 7, 14, 30, 60, 90],
            index=3,
            format_func=lambda x: f"Last {x} days",
        )

    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    # Summary counts
    user_logs = db.execute(
        """SELECT created_at, actor_type, action 
           FROM audit_logs 
           WHERE created_at >= ? AND action LIKE '%logged%'
           ORDER BY created_at DESC LIMIT 100""",
        (start_date,),
        fetch=True,
    )

    market_logs = db.execute(
        """SELECT created_at, action 
           FROM audit_logs 
           WHERE created_at >= ? AND (action LIKE '%price%' OR action LIKE '%market%' OR action LIKE '%updated%asset%')
           ORDER BY created_at DESC LIMIT 100""",
        (start_date,),
        fetch=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        metric_card(
            title="Login/Logout Events",
            value=str(len(user_logs) if user_logs else 0),
            subtitle="User activity",
            color="#5B8DEF",
            bg="#EEF4FF",
            icon="🔐",
        )
    with col2:
        metric_card(
            title="Market Changes",
            value=str(len(market_logs) if market_logs else 0),
            subtitle="Admin activity",
            color="#AB8EE8",
            bg="#F5F0FF",
            icon="📈",
        )

    st.markdown("---")

    # User Login/Logout Logs
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">🔐 User Login/Logout</h3>',
        unsafe_allow_html=True,
    )

    if user_logs:
        for log in user_logs:
            action_lower = log["action"].lower()
            if "logged in" in action_lower or "logged out" in action_lower:
                icon = "✅" if "in" in action_lower else "🚪"
                st.markdown(
                    f"""
                    <div style='background:#FAFAFA; border-radius:8px; padding:1rem; margin-bottom:0.5rem; border-left:4px solid #43A87B;'>
                        <span style='color:#1A1A2E; font-weight:600;'>{log["created_at"][:19]}</span> {icon}
                        <div style='color:#6B7280; margin-top:0.3rem;'>{log["action"]}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.markdown(
            """
        <div style="background:#FFFFFF; border-radius:16px; padding:2rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
            <p style="color:#6B7280;">No login/logout records found</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Admin Market Changes
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">📈 Admin Market Price Changes</h3>',
        unsafe_allow_html=True,
    )

    if market_logs:
        for log in market_logs:
            st.markdown(
                f"""
                <div style='background:#EEF4FF; border-radius:8px; padding:1rem; margin-bottom:0.5rem; border-left:4px solid #5B8DEF;'>
                    <span style='color:#1A1A2E; font-weight:600;'>{log["created_at"][:19]}</span> 📊
                    <div style='color:#6B7280; margin-top:0.3rem;'>{log["action"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
        <div style="background:#FFFFFF; border-radius:16px; padding:2rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
            <p style="color:#6B7280;">No market changes recorded</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
