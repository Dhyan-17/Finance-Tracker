"""
Dashboard Page
Main user dashboard with financial overview
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from database.db import db
from services.wallet_service import wallet_service


def show_dashboard():
    """Display the main dashboard"""
    user = st.session_state.user
    user_id = user['user_id']

    # Header
    st.title(f"💰 Welcome back, {user['username']}!")

    # Balance Overview
    balance = wallet_service.get_total_balance(user_id)

    # Get investment value
    investment_data = db.get_total_investment_value(user_id)

    st.subheader("Account Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Wallet Balance",
            value=f"₹{balance['wallet']:,.2f}",
            delta=None
        )

    with col2:
        pl_delta = f"₹{balance.get('investments_pl', 0):+,.2f}"
        st.metric(
            label="Investments",
            value=f"₹{balance.get('investments_current', 0):,.2f}",
            delta=pl_delta
        )

    with col3:
        st.metric(
            label="Net Worth",
            value=f"₹{balance['net_worth']:,.2f}",
            delta=None,
            help="Total of wallet + investments"
        )

    st.markdown("---")

    # Monthly Summary
    st.subheader("📊 This Month's Summary")

    # Get current month data
    now = datetime.now()
    monthly_data = wallet_service.get_monthly_summary(user_id, now.year, now.month)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Income",
            value=f"₹{monthly_data['total_income']:,.2f}"
        )

    with col2:
        st.metric(
            label="Expenses",
            value=f"₹{monthly_data['total_expense']:,.2f}"
        )

    with col3:
        st.metric(
            label="Savings",
            value=f"₹{monthly_data['net_savings']:,.2f}",
            delta=f"{monthly_data['savings_rate']:.1f}% savings rate"
        )

    with col4:
        if monthly_data['savings_rate'] >= 20:
            st.success("✅ Good Savings!")
        elif monthly_data['savings_rate'] >= 0:
            st.warning("⚠️ Low Savings")
        else:
            st.error("🔴 Overspending!")

    # Recent Transactions
    st.markdown("---")
    st.subheader("📜 Recent Transactions")

    # Get recent expenses
    recent_expenses = db.get_user_expenses(user_id, limit=5)
    if recent_expenses:
        expense_data = []
        for e in recent_expenses:
            expense_data.append({
                'Date': e['date'][:10],
                'Category': e['category'],
                'Amount': f"₹{db.to_rupees(e['amount']):,.2f}",
                'Merchant': e.get('merchant', '-')
            })
        st.table(pd.DataFrame(expense_data))
    else:
        st.info("No recent expenses. Start tracking your spending!")
