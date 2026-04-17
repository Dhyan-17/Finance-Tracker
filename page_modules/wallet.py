"""
Wallet Page
Income and expense management
"""

import streamlit as st
from datetime import datetime
import pandas as pd

from database.db import db
from services.wallet_service import wallet_service


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


def show_wallet():
    """Display wallet management page"""
    user = st.session_state.user
    user_id = user["user_id"]

    st.markdown(
        """
    <div style="padding: 1rem 0 2rem 0;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">💳 Wallet</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Manage your income and expenses</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Balance Cards
    balance = wallet_service.get_total_balance(user_id)

    # Main Wallet Balance Card
    st.markdown(
        f"""
    <div style="background: linear-gradient(135deg, #EEF4FF 0%, #F0FFF8 100%); border-radius:20px; padding:2.5rem; text-align:center; box-shadow:0 4px 20px rgba(0,0,0,0.08); border:1px solid #E8ECF0; margin-bottom:2rem;">
        <div style="color:#6B7280; font-size:0.9rem; font-weight:500; margin-bottom:0.5rem;">Available Balance</div>
        <div style="color:#1A1A2E; font-size:3rem; font-weight:700;">₹{balance["wallet"]:,.2f}</div>
        <div style="color:#43A87B; font-size:0.9rem; margin-top:0.5rem;">Your wallet is ready 💰</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Action Buttons

    # Tabs for different operations
    tab1, tab2 = st.tabs(["➕ Add Income", "➖ Add Expense"])

    # Add Income Tab
    with tab1:
        

        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Add Income</h3>',
            unsafe_allow_html=True,
        )

        with st.form("income_form"):
            col1, col2 = st.columns(2)

            with col1:
                amount = st.number_input(
                    "Amount (₹)", min_value=0.0, step=100.0, format="%.2f"
                )
                source = st.text_input("Source", placeholder="e.g., Salary, Freelance")

            with col2:
                category = st.selectbox(
                    "Category",
                    [
                        "Salary",
                        "Freelance",
                        "Business",
                        "Investment Returns",
                        "Rental Income",
                        "Interest",
                        "Gift",
                        "Other",
                    ],
                )

            description = st.text_area(
                "Description (Optional)", placeholder="Additional notes..."
            )

            submit = st.form_submit_button("Add Income", use_container_width=True)

            if submit:
                if amount > 0 and source:
                    success, message, result = wallet_service.add_income(
                        user_id=user_id,
                        amount=amount,
                        source=source,
                        category=category,
                        account_type="WALLET",
                        account_id=None,
                        description=description,
                    )

                    if success:
                        st.success(
                            f"✅ {message} | New Balance: ₹{result['new_balance']:,.2f}"
                        )
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("Please fill in amount and source")

    # Add Expense Tab
    with tab2:
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Add Expense</h3>',
            unsafe_allow_html=True,
        )

        # Get expense categories
        categories = db.get_expense_categories()
        category_names = (
            [c["name"] for c in categories]
            if categories
            else [
                "Food & Dining",
                "Transportation",
                "Shopping",
                "Entertainment",
                "Bills & Utilities",
                "Healthcare",
                "Education",
                "Travel",
                "Groceries",
                "Personal Care",
                "Others",
            ]
        )

        with st.form("expense_form"):
            col1, col2 = st.columns(2)

            with col1:
                amount = st.number_input(
                    "Amount (₹)",
                    min_value=0.0,
                    step=100.0,
                    format="%.2f",
                    key="exp_amt",
                )
                category = st.selectbox("Category", category_names)

            with col2:
                subcategory = st.text_input(
                    "Subcategory (Optional)", placeholder="e.g., Restaurant, Uber"
                )
                merchant = st.text_input(
                    "Merchant (Optional)", placeholder="e.g., Swiggy, Amazon"
                )

            description = st.text_area(
                "Description (Optional)",
                placeholder="Additional notes...",
                key="exp_desc",
            )

            submit = st.form_submit_button("Add Expense", use_container_width=True)

            if submit:
                if amount > 0:
                    success, message, result = wallet_service.add_expense(
                        user_id=user_id,
                        amount=amount,
                        category=category,
                        payment_mode="UPI",
                        account_type="WALLET",
                        account_id=None,
                        description=description,
                        subcategory=subcategory,
                        merchant=merchant,
                    )

                    if success:
                        msg = (
                            f"✅ {message} | New Balance: ₹{result['new_balance']:,.2f}"
                        )
                        if result.get("budget_warning"):
                            msg += f"\n⚠️ Budget Alert: {result['budget_warning']}"
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("Please enter a valid amount")

    # Recent Wallet Transactions
    st.markdown("---")
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">📜 Recent Wallet Transactions</h3>',
        unsafe_allow_html=True,
    )

    transactions = db.get_wallet_transactions(user_id, limit=10)

    if transactions:
        # Styled transaction list
        for t in transactions:
            border_color = "#43A87B" if t["txn_type"] == "CREDIT" else "#F26C6C"
            amount_color = "#43A87B" if t["txn_type"] == "CREDIT" else "#F26C6C"

            st.markdown(
                f"""
            <div style="background:#FFFFFF; border-radius:12px; padding:1rem; border-left:4px solid {border_color}; margin-bottom:0.5rem; box-shadow:0 1px 4px rgba(0,0,0,0.04); border:1px solid #E8ECF0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="color:#1A1A2E; font-size:0.95rem; font-weight:600;">{t["txn_type"]}</div>
                        <div style="color:#6B7280; font-size:0.8rem;">{t["date"][:16]} • {t["description"] or "-"}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="color:{amount_color}; font-size:1.1rem; font-weight:700;">{"+" if t["txn_type"] == "CREDIT" else "-"}₹{db.to_rupees(t["amount"]):,.2f}</div>
                        <div style="color:#6B7280; font-size:0.75rem;">Bal: ₹{db.to_rupees(t["balance_after"]):,.2f}</div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
        <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
            <div style="font-size:2rem;">💳</div>
            <p style="color:#6B7280; margin-top:0.5rem;">No transactions yet</p>
            <p style="color:#6B7280; font-size:0.9rem;">Add your first income or expense above</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
