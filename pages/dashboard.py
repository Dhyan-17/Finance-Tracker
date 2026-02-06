"""
User Dashboard Page
Main dashboard with financial overview and charts
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

from database.db import db
from services.wallet_service import wallet_service
from services.analytics_service import analytics_service
from services.ai_assistant import ai_assistant


def show_dashboard():
    """Display user dashboard"""
    user = st.session_state.user
    user_id = user['user_id']
    
    st.title("🏠 Dashboard")
    st.markdown(f"Welcome back, **{user['username']}**!")
    
    # Get dashboard data
    data = analytics_service.get_user_dashboard_data(user_id)
    
    # Quick Insights from AI
    insights = ai_assistant.get_quick_insights(user_id)
    if insights:
        with st.expander("💡 Quick Insights", expanded=True):
            cols = st.columns(len(insights))
            for i, insight in enumerate(insights):
                with cols[i]:
                    st.markdown(f"**{insight['icon']} {insight['title']}**")
                    st.caption(insight['message'])
    
    st.markdown("---")
    
    # Balance Overview Cards
    st.subheader("💰 Balance Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Wallet Balance",
            value=f"₹{data['balance']['wallet']:,.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Bank Accounts",
            value=f"₹{data['balance']['bank']:,.2f}",
            delta=None
        )
    
    with col3:
        pl_delta = f"₹{data['balance']['investment_pl']:+,.2f}"
        st.metric(
            label="Investments",
            value=f"₹{data['balance']['investments']:,.2f}",
            delta=pl_delta
        )
    
    with col4:
        st.metric(
            label="Net Worth",
            value=f"₹{data['balance']['net_worth']:,.2f}",
            delta=None,
            help="Total of wallet + bank + investments"
        )
    
    st.markdown("---")
    
    # Monthly Summary
    st.subheader("📊 This Month's Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Income",
            value=f"₹{data['monthly']['income']:,.2f}",
            delta=f"{data['monthly']['income']:.0f}" if data['monthly']['income'] > 0 else None,
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="Expenses",
            value=f"₹{data['monthly']['expense']:,.2f}",
            delta=f"-{data['monthly']['expense']:.0f}" if data['monthly']['expense'] > 0 else None,
            delta_color="inverse"
        )
    
    with col3:
        savings_color = "normal" if data['monthly']['savings'] >= 0 else "inverse"
        st.metric(
            label="Savings",
            value=f"₹{data['monthly']['savings']:,.2f}",
            delta=f"{data['monthly']['savings_rate']:.1f}%" if data['monthly']['income'] > 0 else "N/A",
            delta_color=savings_color
        )
    
    with col4:
        st.metric(
            label="Savings Rate",
            value=f"{data['monthly']['savings_rate']:.1f}%",
            delta="Good!" if data['monthly']['savings_rate'] >= 20 else "Improve",
            delta_color="normal" if data['monthly']['savings_rate'] >= 20 else "off"
        )
    
    st.markdown("---")
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Income vs Expense Trend")
        trend_data = analytics_service.get_income_vs_expense_trend(user_id, 6)
        
        if trend_data:
            df = pd.DataFrame(trend_data)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['month'],
                y=df['income'],
                name='Income',
                marker_color='#2ecc71'
            ))
            fig.add_trace(go.Bar(
                x=df['month'],
                y=df['expense'],
                name='Expense',
                marker_color='#e74c3c'
            ))
            
            fig.update_layout(
                barmode='group',
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transaction data available yet.")
    
    with col2:
        st.subheader("🍕 Spending by Category")
        categories = analytics_service.get_spending_by_category(user_id, 1)
        
        if categories:
            df = pd.DataFrame(categories)
            
            fig = px.pie(
                df,
                values='total',
                names='category',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available yet.")
    
    st.markdown("---")
    
    # Budget Status and Recent Transactions
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Budget Status")
        
        if data['budgets']:
            for budget in data['budgets']:
                status_color = (
                    "#2ecc71" if budget['status'] == 'ON_TRACK' 
                    else "#f39c12" if budget['status'] == 'WARNING' 
                    else "#e74c3c"
                )
                
                st.markdown(f"**{budget['category']}**")
                progress = min(budget['percentage'] / 100, 1.0)
                st.progress(progress)
                st.caption(f"₹{budget['spent']:,.0f} / ₹{budget['limit']:,.0f} ({budget['percentage']:.0f}%)")
        else:
            st.info("No budgets set. Set budgets to track your spending!")
            if st.button("Set Budget", key="dash_set_budget"):
                st.session_state.page = 'budgets'
                st.rerun()
    
    with col2:
        st.subheader("🕐 Recent Transactions")
        
        # Combine and sort recent transactions
        all_recent = []
        
        for exp in data['recent_expenses']:
            all_recent.append({
                'type': 'Expense',
                'category': exp['category'],
                'amount': -exp['amount'],
                'date': exp['date'],
                'icon': '🔴'
            })
        
        for inc in data['recent_income']:
            all_recent.append({
                'type': 'Income',
                'category': inc['source'],
                'amount': inc['amount'],
                'date': inc['date'],
                'icon': '🟢'
            })
        
        # Sort by date
        all_recent.sort(key=lambda x: x['date'], reverse=True)
        
        if all_recent:
            for txn in all_recent[:5]:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"{txn['icon']} **{txn['category']}**")
                    st.caption(txn['date'][:10])
                with col_b:
                    color = "green" if txn['amount'] > 0 else "red"
                    st.markdown(f"<span style='color:{color}'>₹{abs(txn['amount']):,.0f}</span>", 
                               unsafe_allow_html=True)
                st.markdown("---")
        else:
            st.info("No recent transactions.")
    
    # Financial Health Score
    st.markdown("---")
    st.subheader("💪 Financial Health Score")
    
    health = analytics_service.calculate_financial_health_score(user_id)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Gauge chart for health score
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health['score'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': health['rating']},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#3498db"},
                'steps': [
                    {'range': [0, 40], 'color': "#e74c3c"},
                    {'range': [40, 60], 'color': "#f39c12"},
                    {'range': [60, 80], 'color': "#27ae60"},
                    {'range': [80, 100], 'color': "#2ecc71"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': health['score']
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Breakdown
    cols = st.columns(5)
    breakdown_labels = ['Savings Rate', 'Budget Compliance', 'Emergency Fund', 'Investment Diversity', 'Activity']
    
    for i, (key, values) in enumerate(health['breakdown'].items()):
        with cols[i]:
            st.metric(
                label=breakdown_labels[i],
                value=f"{values['score']}/{values['max']}"
            )
    
    # Notifications
    if data['unread_notifications'] > 0:
        st.markdown("---")
        st.info(f"📬 You have {data['unread_notifications']} unread notifications")
