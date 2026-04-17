"""
Budgets Page
Budget management and tracking
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from database.db import db
from services.analytics_service import analytics_service


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


def progress_bar_html(category, spent, total, percentage, status):
    if status == "ON_TRACK":
        color = "#43A87B"
        icon = "✅"
    elif status == "WARNING":
        color = "#F5A623"
        icon = "⚠️"
    else:
        color = "#F26C6C"
        icon = "❌"

    progress = min(percentage / 100, 1.0)

    st.markdown(
        f"""
    <div style="background:#FFFFFF; border-radius:16px; padding:1.5rem; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0; margin-bottom:1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem;">
            <div style="font-weight:600; color:#1A1A2E; font-size:1rem;">{icon} {category}</div>
            <div style="font-weight:700; color:{color}; font-size:1.1rem;">{percentage:.0f}%</div>
        </div>
        <div style="background:#F0F0F0; border-radius:10px; height:12px; overflow:hidden;">
            <div style="background:{color}; width:{progress * 100}%; border-radius:10px; height:12px; transition:width 0.3s;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:0.8rem; font-size:0.85rem;">
            <div style="color:#6B7280;">Spent: <span style="color:#1A1A2E; font-weight:600;">₹{spent:,.0f}</span></div>
            <div style="color:#6B7280;">Budget: <span style="color:#1A1A2E; font-weight:600;">₹{total:,.0f}</span></div>
            <div style="color:{color}; font-weight:600;">Rem: ₹{total - spent:,.0f}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_budgets():
    """Display budgets page"""
    user = st.session_state.user
    user_id = user["user_id"]

    st.markdown(
        """
    <div style="padding: 1rem 0 2rem 0;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">📋 Budgets</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Track and manage your spending limits</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # Month/Year Selector
    col1, col2 = st.columns([2, 1])

    with col1:
        selected_month = st.selectbox(
            "Select Month",
            options=list(range(1, 13)),
            index=current_month - 1,
            format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
        )

    with col2:
        selected_year = st.selectbox(
            "Select Year",
            options=list(range(current_year - 2, current_year + 1)),
            index=2,
        )

    # Get budget status
    budgets = analytics_service.get_budget_status(
        user_id, selected_year, selected_month
    )

    st.markdown("---")

    # Tabs
    tab1, tab2 = st.tabs(["📊 Budget Status", "➕ Manage Budgets"])

    # Budget Status Tab
    with tab1:
        if budgets:
            # Summary Cards
            total_limit = sum(b["limit"] for b in budgets)
            total_spent = sum(b["spent"] for b in budgets)
            total_remaining = total_limit - total_spent

            col1, col2, col3 = st.columns(3)

            with col1:
                metric_card(
                    title="Total Budget",
                    value=f"₹{total_limit:,.2f}",
                    subtitle="This month",
                    color="#5B8DEF",
                    bg="#EEF4FF",
                    icon="📋",
                )
            with col2:
                metric_card(
                    title="Total Spent",
                    value=f"₹{total_spent:,.2f}",
                    subtitle="Spent so far",
                    color="#F26C6C",
                    bg="#FFF4EE",
                    icon="📤",
                )
            with col3:
                pct_left = (
                    (total_remaining / total_limit * 100) if total_limit > 0 else 0
                )
                rem_color = "#43A87B" if pct_left >= 20 else "#F26C6C"
                rem_bg = "#EEFAF4" if pct_left >= 20 else "#FFF4EE"
                metric_card(
                    title="Remaining",
                    value=f"₹{total_remaining:,.2f}",
                    subtitle=f"{pct_left:.0f}% left",
                    color=rem_color,
                    bg=rem_bg,
                    icon="💰",
                )

            st.markdown("---")

            # Budget Progress Bars
            st.markdown(
                '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">📊 Category Budgets</h3>',
                unsafe_allow_html=True,
            )

            for budget in budgets:
                progress_bar_html(
                    category=budget["category"],
                    spent=budget["spent"],
                    total=budget["limit"],
                    percentage=budget["percentage"],
                    status=budget["status"],
                )

            st.markdown("---")

            # Budget vs Actual Chart
            st.markdown(
                '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">📊 Budget vs Actual</h3>',
                unsafe_allow_html=True,
            )

            df = pd.DataFrame(
                [
                    {
                        "Category": b["category"],
                        "Budget": b["limit"],
                        "Spent": b["spent"],
                    }
                    for b in budgets
                ]
            )

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=df["Category"],
                    y=df["Budget"],
                    name="Budget",
                    marker_color="#5B8DEF",
                )
            )
            fig.add_trace(
                go.Bar(
                    x=df["Category"],
                    y=df["Spent"],
                    name="Spent",
                    marker_color="#F26C6C",
                )
            )

            fig.update_layout(
                barmode="group",
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                template="plotly_white",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown(
                """
            <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
                <div style="font-size:2rem;">📋</div>
                <p style="color:#6B7280; margin-top:0.5rem;">No budgets set for this month</p>
                <p style="color:#6B7280; font-size:0.9rem;">Create budgets to track your spending!</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Manage Budgets Tab
    with tab2:
        

        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Set Budget</h3>',
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

        col1, col2 = st.columns(2)

        with col1:
            category = st.selectbox("Category", category_names)

        with col2:
            budget_month = st.selectbox(
                "Month",
                options=list(range(1, 13)),
                index=selected_month - 1,
                format_func=lambda x: datetime(2000, x, 1).strftime("%B"),
            )

        budget_year = selected_year

        # Check if budget exists
        existing = db.get_budget_exists(user_id, category, budget_year, budget_month)

        if existing:
            current = db.to_rupees(existing["limit_amount"])
            st.info(f"Current budget: ₹{current:,.2f}")
            amount = st.number_input(
                "New Amount (₹)", min_value=100.0, value=float(current), step=100.0
            )
            if st.button("Update Budget"):
                db.set_budget(
                    user_id,
                    category,
                    db.to_paise(amount),
                    budget_year,
                    budget_month,
                    80,
                    "replace",
                )
                st.success("Budget updated!")
                st.rerun()
        else:
            amount = st.number_input(
                "Budget Amount (₹)", min_value=100.0, value=5000.0, step=100.0
            )
            if st.button("Create Budget"):
                db.set_budget(
                    user_id,
                    category,
                    db.to_paise(amount),
                    budget_year,
                    budget_month,
                    80,
                    "replace",
                )
                st.success("Budget created!")
                st.rerun()

        st.markdown("---")

        # Show all budgets
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">📋 All Budgets</h3>',
            unsafe_allow_html=True,
        )

        all_budgets = db.get_user_budgets(user_id)

        if all_budgets:
            for b in all_budgets:
                st.markdown(
                    f"""
                <div style="background:#FFFFFF; border-radius:12px; padding:1rem; margin-bottom:0.5rem; box-shadow:0 1px 4px rgba(0,0,0,0.04); border:1px solid #E8ECF0;">
                    <span style="font-weight:600; color:#1A1A2E;">{b["category"]}</span>
                    <span style="color:#6B7280; margin-left:1rem;">₹{db.to_rupees(b["limit_amount"]):,.2f}</span>
                    <span style="color:#6B7280; font-size:0.85rem; margin-left:0.5rem;">({datetime(2000, b["month"], 1).strftime("%B")} {b["year"]})</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
            <div style="background:#FFFFFF; border-radius:16px; padding:2rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
                <div style="font-size:2rem;">📋</div>
                <p style="color:#6B7280; margin-top:0.5rem;">No budgets yet</p>
                <p style="color:#6B7280; font-size:0.9rem;">Create your first budget above</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
