"""
Admin Dashboard Page
Platform overview and key metrics
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from database.db import db
from services.analytics_service import analytics_service


def show_admin_dashboard():
    """Display admin dashboard"""
    admin = st.session_state.admin
    
    st.title("🏠 Admin Dashboard")
    st.markdown(f"Welcome, **{admin['name']}** ({admin['role']})")
    
    # Get platform summary
    summary = analytics_service.get_platform_summary()
    
    st.markdown("---")
    
    # User Statistics
    st.subheader("👥 User Statistics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Users", summary['users']['total'])
    with col2:
        st.metric("Active Users", summary['users']['active'])
    with col3:
        st.metric("Blocked Users", summary['users']['blocked'])
    with col4:
        st.metric("New (7 days)", summary['users']['new_7d'])
    with col5:
        st.metric("New (30 days)", summary['users']['new_30d'])
    
    st.markdown("---")
    
    # Financial Statistics
    st.subheader("💰 Financial Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total in Wallets", f"₹{summary['finances']['wallet_total']:,.0f}")
        st.metric("Total in Banks", f"₹{summary['finances']['bank_total']:,.0f}")
    
    with col2:
        st.metric("Total Expenses", f"₹{summary['finances']['total_expenses']:,.0f}")
        st.caption(f"{summary['finances']['expense_count']} transactions")
    
    with col3:
        st.metric("Total Income", f"₹{summary['finances']['total_income']:,.0f}")
        st.caption(f"{summary['finances']['income_count']} transactions")
    
    st.markdown("---")
    
    # Investment Statistics
    st.subheader("📈 Investment Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invested", f"₹{summary['investments']['total_invested']:,.0f}")
    with col2:
        st.metric("Current Value", f"₹{summary['investments']['current_value']:,.0f}")
    with col3:
        pl = summary['investments']['current_value'] - summary['investments']['total_invested']
        st.metric("Platform P/L", f"₹{pl:+,.0f}")
    with col4:
        st.metric("Active Investors", summary['investments']['investors'])
    
    st.markdown("---")
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Platform Growth")
        
        growth = analytics_service.get_monthly_platform_growth(12)
        
        if growth:
            df = pd.DataFrame(growth)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['month'],
                y=df['new_users'],
                mode='lines+markers',
                name='New Users',
                yaxis='y1'
            ))
            fig.add_trace(go.Bar(
                x=df['month'],
                y=df['transaction_volume'],
                name='Transaction Volume',
                yaxis='y2',
                opacity=0.5
            ))
            
            fig.update_layout(
                height=400,
                margin=dict(l=20, r=60, t=20, b=20),
                yaxis=dict(title='New Users', side='left'),
                yaxis2=dict(title='Volume (₹)', side='right', overlaying='y'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Top Spending Categories")
        
        categories = analytics_service.get_top_spending_categories(10)
        
        if categories:
            df = pd.DataFrame(categories)
            
            fig = px.bar(
                df,
                x='total',
                y='category',
                orientation='h',
                color='users',
                color_continuous_scale='Blues',
                labels={'total': 'Total (₹)', 'category': 'Category', 'users': 'Users'}
            )
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Investment Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Investment Distribution")
        
        distribution = analytics_service.get_investment_distribution()
        
        if distribution:
            df = pd.DataFrame(distribution)
            
            fig = px.pie(
                df,
                values='current_value',
                names='type',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💰 Top Investors")
        
        investors = analytics_service.get_top_investors(5)
        
        if investors:
            for i, inv in enumerate(investors, 1):
                col_a, col_b, col_c = st.columns([2, 1, 1])
                
                with col_a:
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    st.write(f"{medal} **{inv['username']}**")
                with col_b:
                    st.write(f"₹{inv['current_value']:,.0f}")
                with col_c:
                    color = "green" if inv['profit_loss'] >= 0 else "red"
                    st.markdown(f"<span style='color:{color}'>₹{inv['profit_loss']:+,.0f}</span>", 
                               unsafe_allow_html=True)
        else:
            st.info("No investment data")
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("📜 Recent Activity")
    
    logs = db.execute(
        """SELECT * FROM audit_logs 
           ORDER BY created_at DESC LIMIT 10""",
        fetch=True
    )
    
    if logs:
        for log in logs:
            severity_icons = {
                'INFO': '📝',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }
            icon = severity_icons.get(log['severity'], '📝')
            st.write(f"{icon} {log['created_at'][:16]} | {log['actor_type']}:{log['actor_id']} | {log['action'][:60]}")
    else:
        st.info("No recent activity")
    
    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👥 View Users", use_container_width=True):
            st.session_state.page = 'admin_users'
            st.rerun()
    
    with col2:
        if st.button("🚨 Fraud Alerts", use_container_width=True):
            st.session_state.page = 'admin_fraud'
            st.rerun()
    
    with col3:
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.page = 'admin_analytics'
            st.rerun()
    
    with col4:
        if st.button("📈 Market", use_container_width=True):
            st.session_state.page = 'admin_market'
            st.rerun()
