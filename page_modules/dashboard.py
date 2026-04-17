"""
Dashboard Page
Main user dashboard with financial overview
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from database.db import db
from services.wallet_service import wallet_service


def metric_card(title, value, subtitle="", color="#5B8DEF", bg="#EEF4FF"):
    st.markdown(
        f"""
    <div style="background:{bg}; border-radius:16px; padding:1.5rem; border-left:4px solid {color}; margin-bottom:0.5rem;">
        <div style="color:#6B7280; font-size:0.85rem; font-weight:500; margin:0.4rem 0;">{title}</div>
        <div style="color:#1A1A2E; font-size:1.6rem; font-weight:700;">{value}</div>
        <div style="color:{color}; font-size:0.8rem;">{subtitle}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_dashboard():
    """Display the main dashboard"""
    user = st.session_state.user
    user_id = user["user_id"]

    # Header
    st.markdown(
        f"""
    <div style="padding: 1rem 0 2rem 0;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">Welcome back, {user["username"]}!</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Here is your financial overview</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Balance Overview
    balance = wallet_service.get_total_balance(user_id)

    # Get investment value
    investment_data = db.get_total_investment_value(user_id)

    st.markdown(
        '<h2 style="color:#1A1A2E; font-size:1.3rem; font-weight:600; margin:1.5rem 0 1rem 0;">Account Summary</h2>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card(
            title="Wallet Balance",
            value=f"Rs.{balance['wallet']:,.2f}",
            subtitle="Available funds",
            color="#5B8DEF",
            bg="#EEF4FF",
        )

    with col2:
        pl_text = (
            f"+Rs.{balance.get('investments_pl', 0):,.2f}"
            if balance.get("investments_pl", 0) >= 0
            else f"-Rs.{abs(balance.get('investments_pl', 0)):,.2f}"
        )
        metric_card(
            title="Investments",
            value=f"Rs.{balance.get('investments_current', 0):,.2f}",
            subtitle=pl_text,
            color="#43A87B",
            bg="#EEFAF4",
        )

    with col3:
        metric_card(
            title="Net Worth",
            value=f"Rs.{balance['net_worth']:,.2f}",
            subtitle="Total assets",
            color="#AB8EE8",
            bg="#F5F0FF",
        )

    st.markdown("---")

    # Monthly Summary
    st.markdown(
        '<h2 style="color:#1A1A2E; font-size:1.3rem; font-weight:600; margin:1.5rem 0 1rem 0;">This Month Summary</h2>',
        unsafe_allow_html=True,
    )

    # Get current month data
    now = datetime.now()
    monthly_data = wallet_service.get_monthly_summary(user_id, now.year, now.month)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            title="Income",
            value=f"Rs.{monthly_data['total_income']:,.2f}",
            subtitle="This month",
            color="#43A87B",
            bg="#EEFAF4",
        )

    with col2:
        metric_card(
            title="Expenses",
            value=f"Rs.{monthly_data['total_expense']:,.2f}",
            subtitle="This month",
            color="#F26C6C",
            bg="#FFF4EE",
        )

    with col3:
        metric_card(
            title="Savings",
            value=f"Rs.{monthly_data['net_savings']:,.2f}",
            subtitle=f"{monthly_data['savings_rate']:.1f}% rate",
            color="#AB8EE8",
            bg="#F5F0FF",
        )

    with col4:
        if monthly_data["savings_rate"] >= 20:
            status_text = "Great Savings!"
            status_color = "#43A87B"
            status_bg = "#EEFAF4"
        elif monthly_data["savings_rate"] >= 0:
            status_text = "Could Be Better"
            status_color = "#F5A623"
            status_bg = "#FFF8E8"
        else:
            status_text = "Overspending"
            status_color = "#F26C6C"
            status_bg = "#FFF4EE"

        metric_card(
            title="Status",
            value=status_text,
            subtitle="This month",
            color=status_color,
            bg=status_bg,
        )

    # Recent Transactions
    st.markdown("---")
    st.markdown(
        '<h2 style="color:#1A1A2E; font-size:1.3rem; font-weight:600; margin:1.5rem 0 1rem 0;">Recent Transactions</h2>',
        unsafe_allow_html=True,
    )

    # Get recent expenses
    recent_expenses = db.get_user_expenses(user_id, limit=5)
    if recent_expenses:
        # Build table HTML
        table_html = '<div style="background:#FFFFFF; border-radius:16px; padding:0; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0; overflow:hidden;"><table style="width:100%; border-collapse:collapse;"><thead><tr style="background:#FAFAFA;"><th style="padding:1rem; text-align:left; color:#6B7280; font-weight:600; font-size:0.85rem; border-bottom:1px solid #E8ECF0;">Date</th><th style="padding:1rem; text-align:left; color:#6B7280; font-weight:600; font-size:0.85rem; border-bottom:1px solid #E8ECF0;">Category</th><th style="padding:1rem; text-align:right; color:#6B7280; font-weight:600; font-size:0.85rem; border-bottom:1px solid #E8ECF0;">Amount</th><th style="padding:1rem; text-align:left; color:#6B7280; font-weight:600; font-size:0.85rem; border-bottom:1px solid #E8ECF0;">Merchant</th></tr></thead><tbody>'

        for i, e in enumerate(recent_expenses):
            bg_color = "#FAFAFA" if i % 2 == 0 else "#FFFFFF"
            table_html += f'<tr style="background:{bg_color};"><td style="padding:1rem; color:#1A1A2E; font-size:0.9rem; border-bottom:1px solid #E8ECF0;">{e["date"][:10]}</td><td style="padding:1rem; color:#1A1A2E; font-size:0.9rem; border-bottom:1px solid #E8ECF0;">{e["category"]}</td><td style="padding:1rem; color:#F26C6C; font-size:0.9rem; font-weight:600; text-align:right; border-bottom:1px solid #E8ECF0;">Rs.{db.to_rupees(e["amount"]):,.2f}</td><td style="padding:1rem; color:#6B7280; font-size:0.9rem; border-bottom:1px solid #E8ECF0;">{e.get("merchant", "-")}</td></tr>'

        table_html += "</tbody></table></div>"

        st.markdown(table_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:#FFFFFF; border-radius:16px; padding:2rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;"><p style="color:#6B7280; margin-top:0.5rem;">No recent expenses</p><p style="color:#6B7280; font-size:0.9rem;">Start tracking your spending!</p></div>',
            unsafe_allow_html=True,
        )
