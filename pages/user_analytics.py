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


def show_user_analytics():
    """Display user analytics page"""
    user = st.session_state.user
    user_id = user['user_id']
    
    st.title("📉 Analytics")
    
    # Date Range Selector
    col1, col2 = st.columns(2)
    with col1:
        months = st.selectbox("Time Period", [3, 6, 12], index=1, format_func=lambda x: f"Last {x} months")
    
    st.markdown("---")
    
    # Quick Stats
    trend = analytics_service.get_income_vs_expense_trend(user_id, months) or []
    total_income = sum(t['income'] for t in trend)
    total_expense = sum(t['expense'] for t in trend)    
    savings = total_income - total_expense
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Income", f"₹{total_income:,.0f}")
    with col2:
        st.metric("Total Expense", f"₹{total_expense:,.0f}")
    with col3:
        st.metric("Savings", f"₹{savings:,.0f}")
    with col4:
        st.metric("Savings Rate", f"{savings_rate:.1f}%")
    
    st.markdown("---")
    
    # Income vs Expense Trend
    st.subheader("📈 Income vs Expense Trend")
    
    if trend:
        df = pd.DataFrame(trend)
        
        # Calculate savings
        df['Savings'] = df['income'] - df['expense']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df['income'],
            mode='lines+markers',
            name='Income',
            line=dict(color='#2ecc71', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df['expense'],
            mode='lines+markers',
            name='Expense',
            line=dict(color='#e74c3c', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Bar(
            x=df['month'],
            y=df['Savings'],
            name='Savings',
            marker_color=['#3498db' if s >= 0 else '#e74c3c' for s in df['Savings']],
            opacity=0.5
        ))
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis_title="Month",
            yaxis_title="Amount (₹)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Category Analysis
    st.subheader("🍕 Spending by Category")
    
    categories = analytics_service.get_spending_by_category(user_id, months)
    
    if categories:
        df = pd.DataFrame(categories)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.treemap(
                df,
                path=['category'],
                values='total',
                color='percentage',
                color_continuous_scale='RdYlGn_r'
            )
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Table
            df_display = df[['category', 'total', 'count', 'percentage']].copy()
            df_display['total'] = df_display['total'].apply(lambda x: f"₹{x:,.0f}")
            df_display['percentage'] = df_display['percentage'].apply(lambda x: f"{x:.1f}%")
            df_display.columns = ['Category', 'Total', 'Txns', '%']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No expense data available.")
