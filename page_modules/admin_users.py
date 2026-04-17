"""
Admin Users Page
View and search users (read-only, no financial data)
"""

import streamlit as st
import pandas as pd

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


def show_admin_users():
    """Display admin users page - READ ONLY, NO FINANCIAL DATA"""
    if "admin" not in st.session_state or not st.session_state.admin:
        st.error("Please login as admin")
        return

    admin = st.session_state.admin

    st.markdown(
        """
    <div style="background:#F0F4FF; border-radius:16px; padding:1.5rem; border:1px solid #AB8EE8; margin-bottom:2rem;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">👥 Users</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">View registered users</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Search
    search = st.text_input(
        "🔍 Search Users", placeholder="Search by email, username, or mobile..."
    )

    # Get all users
    users = db.get_all_users(limit=100)

    # Apply search filter
    if search:
        search_lower = search.lower()
        users = [
            u
            for u in users
            if search_lower in u["username"].lower()
            or search_lower in u["email"].lower()
            or search_lower in str(u["mobile"])
        ]

    # Summary
    col1, col2 = st.columns(2)

    with col1:
        total_users = len(users)
        metric_card(
            title="Total Users",
            value=str(total_users),
            subtitle="Registered",
            color="#5B8DEF",
            bg="#EEF4FF",
            icon="👥",
        )

    st.markdown("---")

    # Users Table
    if users:
        df_data = []
        for u in users:
            joined = u.get("created_at", "N/A")
            if joined:
                joined = joined[:10] if " " in joined else joined
            else:
                joined = "N/A"

            last_login = u.get("last_login", "Never")
            if last_login:
                last_login = last_login[:16] if " " in last_login else last_login
            else:
                last_login = "Never"

            df_data.append(
                {
                    "ID": u["user_id"],
                    "Username": u["username"],
                    "Email": u["email"],
                    "Mobile": u["mobile"],
                    "Joined": joined,
                    "Last Login": last_login,
                }
            )

        df = pd.DataFrame(df_data)

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown(
            f"""
        <div style="color:#6B7280; font-size:0.85rem; margin-top:0.5rem;">
            Showing {len(users)} users
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
        <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
            <div style="font-size:2rem;">👥</div>
            <p style="color:#6B7280; margin-top:0.5rem;">No users found</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
