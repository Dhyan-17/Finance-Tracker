"""
User Analytics Page
Comprehensive personal financial analytics
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from database.db import db
from services.analytics_service import analytics_service
from services.wallet_service import wallet_service


def metric_card(title, value, subtitle="", color="#5B8DEF", bg="#EEF4FF", icon="money"):
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


def show_user_analytics():
    """Display user analytics page"""
    user = st.session_state.user
    user_id = user["user_id"]

    st.markdown(
        """
    <div style="padding: 1rem 0 2rem 0;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">Analytics</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Your financial insights</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Date Range Selector
    col1, col2 = st.columns(2)
    with col1:
        months = st.selectbox(
            "Time Period", [3, 6, 12], index=1, format_func=lambda x: f"Last {x} months"
        )

    st.markdown("---")

    # Quick Stats
    trend = analytics_service.get_income_vs_expense_trend(user_id, months) or []
    total_income = sum(t["income"] for t in trend)
    total_expense = sum(t["expense"] for t in trend)
    savings = total_income - total_expense
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            title="Total Income",
            value=f"Rs.{total_income:,.0f}",
            subtitle="All time",
            color="#43A87B",
            bg="#EEFAF4",
            icon="down",
        )
    with col2:
        metric_card(
            title="Total Expense",
            value=f"Rs.{total_expense:,.0f}",
            subtitle="All time",
            color="#F26C6C",
            bg="#FFF4EE",
            icon="up",
        )
    with col3:
        metric_card(
            title="Savings",
            value=f"Rs.{savings:,.0f}",
            subtitle="Saved",
            color="#5B8DEF",
            bg="#EEF4FF",
            icon="save",
        )
    with col4:
        sr_color = "#43A87B" if savings_rate >= 20 else "#F5A623"
        sr_bg = "#EEFAF4" if savings_rate >= 20 else "#FFF8E8"
        metric_card(
            title="Savings Rate",
            value=f"{savings_rate:.1f}%",
            subtitle="of income",
            color=sr_color,
            bg=sr_bg,
            icon="chart",
        )

    st.markdown("---")

    # Income vs Expense Trend
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">Income vs Expense Trend</h3>',
        unsafe_allow_html=True,
    )

    if trend:
        df = pd.DataFrame(trend)

        df["Savings"] = df["income"] - df["expense"]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=df["income"],
                mode="lines+markers",
                name="Income",
                line=dict(color="#43A87B", width=3),
                marker=dict(size=8),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["month"],
                y=df["expense"],
                mode="lines+markers",
                name="Expense",
                line=dict(color="#F26C6C", width=3),
                marker=dict(size=8),
            )
        )

        fig.add_trace(
            go.Bar(
                x=df["month"],
                y=df["Savings"],
                name="Savings",
                marker_color=[
                    "#5B8DEF" if s >= 0 else "#F26C6C" for s in df["Savings"]
                ],
                opacity=0.5,
            )
        )

        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            xaxis_title="Month",
            yaxis_title="Amount (Rs.)",
            template="plotly_white",
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Category Analysis
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">Spending by Category</h3>',
        unsafe_allow_html=True,
    )

    categories = analytics_service.get_spending_by_category(user_id, months)

    if categories:
        df = pd.DataFrame(categories)

        col1, col2 = st.columns([2, 1])

        with col1:
            fig = px.treemap(
                df,
                path=["category"],
                values="total",
                color="percentage",
                color_continuous_scale=["#EEF4FF", "#5B8DEF", "#43A87B"],
            )
            fig.update_layout(
                height=400, margin=dict(l=20, r=20, t=20, b=20), template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            df_display = df[["category", "total", "count", "percentage"]].copy()
            df_display["total"] = df_display["total"].apply(lambda x: f"Rs.{x:,.0f}")
            df_display["percentage"] = df_display["percentage"].apply(
                lambda x: f"{x:.1f}%"
            )
            df_display.columns = ["Category", "Total", "Txns", "%"]
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.markdown(
            """
        <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
            <p style="color:#6B7280; margin-top:0.5rem;">No expense data available</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
