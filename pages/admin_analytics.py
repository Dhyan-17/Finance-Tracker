"""
Admin Analytics Page
Platform-wide analytics and reporting
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

from database.db import db
from services.analytics_service import analytics_service


def show_admin_analytics():
    """Display admin analytics page"""
    admin = st.session_state.admin
    
    st.title("📊 Platform Analytics")
    
    # Date Range
    col1, col2 = st.columns([1, 3])
    with col1:
        months = st.selectbox("Time Period", [3, 6, 12, 24], index=1, format_func=lambda x: f"Last {x} months")
    
    st.markdown("---")
    
    # Platform Summary
    summary = analytics_service.get_platform_summary()
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", summary['users']['total'])
    with col2:
        total_money = summary['finances']['wallet_total'] + summary['finances']['bank_total']
        st.metric("Total Money", f"₹{total_money:,.0f}")
    with col3:
        st.metric("Total Transactions", summary['finances']['expense_count'] + summary['finances']['income_count'])
    with col4:
        st.metric("Active Investors", summary['investments']['investors'])
    
    st.markdown("---")
    
    # Growth Charts
    st.subheader("📈 Platform Growth")
    
    growth = analytics_service.get_monthly_platform_growth(months)
    
    if growth:
        df = pd.DataFrame(growth)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                df, x='month', y='new_users',
                markers=True,
                title='New User Registrations'
            )
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.area(
                df, x='month', y='transaction_volume',
                title='Transaction Volume (₹)'
            )
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        # Growth Rate
        if len(df) > 1:
            df['user_growth'] = df['new_users'].pct_change() * 100
            df['volume_growth'] = df['transaction_volume'].pct_change() * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                avg_user_growth = df['user_growth'].mean()
                st.metric("Avg User Growth", f"{avg_user_growth:+.1f}% per month")
            
            with col2:
                avg_volume_growth = df['volume_growth'].mean()
                st.metric("Avg Volume Growth", f"{avg_volume_growth:+.1f}% per month")
    
    st.markdown("---")
    
    # Category Analysis
    st.subheader("🍕 Spending Category Analysis")
    
    categories = analytics_service.get_top_spending_categories(15)
    
    if categories:
        col1, col2 = st.columns(2)
        
        with col1:
            df = pd.DataFrame(categories)
            
            fig = px.pie(
                df, values='total', names='category',
                title='Spending Distribution',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                df.head(10),
                x='total', y='category',
                orientation='h',
                color='users',
                color_continuous_scale='Blues',
                title='Top Categories by Volume',
                labels={'total': 'Amount (₹)', 'users': 'Users'}
            )
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        # Category Table
        st.markdown("**Category Details:**")
        df_display = df.copy()
        df_display['total'] = df_display['total'].apply(lambda x: f"₹{x:,.0f}")
        df_display['percentage'] = df_display['percentage'].apply(lambda x: f"{x:.1f}%")
        df_display.columns = ['Category', 'Total', 'Transactions', 'Users', 'Share']
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Investment Analysis
    st.subheader("📈 Investment Analysis")
    
    distribution = analytics_service.get_investment_distribution()
    investors = analytics_service.get_top_investors(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if distribution:
            df = pd.DataFrame(distribution)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df['type'],
                y=df['invested'],
                name='Invested',
                marker_color='#3498db'
            ))
            fig.add_trace(go.Bar(
                x=df['type'],
                y=df['current_value'],
                name='Current Value',
                marker_color='#2ecc71'
            ))
            
            fig.update_layout(
                barmode='group',
                height=400,
                title='Investment by Asset Type',
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if investors:
            st.markdown("**Top Investors:**")
            
            for i, inv in enumerate(investors[:10], 1):
                col_a, col_b, col_c = st.columns([2, 1, 1])
                
                with col_a:
                    medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                    st.write(f"{medal} {inv['username']}")
                with col_b:
                    st.write(f"₹{inv['current_value']:,.0f}")
                with col_c:
                    color = "green" if inv['profit_loss'] >= 0 else "red"
                    st.markdown(f"<span style='color:{color}'>₹{inv['profit_loss']:+,.0f}</span>",
                               unsafe_allow_html=True)
    
    st.markdown("---")
    
    # User Behavior Analysis
    st.subheader("👥 User Behavior")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Active users by time
        active_users = db.execute(
            """SELECT strftime('%H', date) as hour, COUNT(DISTINCT user_id) as users
               FROM expenses
               WHERE date >= date('now', '-30 days')
               GROUP BY hour
               ORDER BY hour""",
            fetch=True
        )
        
        if active_users:
            df = pd.DataFrame(active_users)
            
            fig = px.bar(
                df, x='hour', y='users',
                title='Active Users by Hour',
                labels={'hour': 'Hour of Day', 'users': 'Active Users'}
            )
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Transactions by day of week
        daily_txns = db.execute(
            """SELECT strftime('%w', date) as dow, COUNT(*) as count, SUM(amount) as total
               FROM expenses
               WHERE date >= date('now', '-30 days')
               GROUP BY dow
               ORDER BY dow""",
            fetch=True
        )
        
        if daily_txns:
            days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            df = pd.DataFrame(daily_txns)
            df['day'] = df['dow'].apply(lambda x: days[int(x)])
            df['total'] = df['total'].apply(db.to_rupees)
            
            fig = px.bar(
                df, x='day', y='total',
                title='Spending by Day of Week',
                labels={'day': 'Day', 'total': 'Amount (₹)'}
            )
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Reports
    st.subheader("📄 Export Reports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 User Report", use_container_width=True):
            users = db.get_all_users(limit=1000)
            df = pd.DataFrame(users)
            df['wallet_balance'] = df['wallet_balance'].apply(db.to_rupees)
            csv = df.to_csv(index=False)
            st.download_button(
                "Download User Report",
                csv,
                f"users_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
    
    with col2:
        if st.button("📥 Transaction Report", use_container_width=True):
            # Get all expenses
            expenses = db.execute(
                """SELECT e.*, u.username, u.email
                   FROM expenses e
                   JOIN users u ON e.user_id = u.user_id
                   ORDER BY e.date DESC LIMIT 5000""",
                fetch=True
            )
            if expenses:
                df = pd.DataFrame(expenses)
                df['amount'] = df['amount'].apply(db.to_rupees)
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download Transaction Report",
                    csv,
                    f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
    
    with col3:
        if st.button("📥 Investment Report", use_container_width=True):
            investments = db.execute(
                """SELECT ui.*, u.username, u.email, ma.asset_name, ma.asset_symbol, ma.current_price
                   FROM user_investments ui
                   JOIN users u ON ui.user_id = u.user_id
                   JOIN market_assets ma ON ui.asset_id = ma.asset_id
                   ORDER BY ui.invested_amount DESC""",
                fetch=True
            )
            if investments:
                df = pd.DataFrame(investments)
                df['invested_amount'] = df['invested_amount'].apply(db.to_rupees)
                df['current_price'] = df['current_price'].apply(db.to_rupees)
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download Investment Report",
                    csv,
                    f"investments_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
