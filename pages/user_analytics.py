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
    
    # Financial Health Score
    st.subheader("💪 Financial Health Score")
    
    health = analytics_service.calculate_financial_health_score(user_id)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Gauge
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
                ]
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**Score Breakdown:**")
        
        breakdown_data = []
        for key, values in health['breakdown'].items():
            label = key.replace('_', ' ').title()
            breakdown_data.append({
                'Category': label,
                'Score': values['score'],
                'Max': values['max'],
                'Percentage': (values['score'] / values['max'] * 100) if values['max'] > 0 else 0
            })
        
        df = pd.DataFrame(breakdown_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['Category'],
            y=df['Score'],
            name='Your Score',
            marker_color='#3498db'
        ))
        fig.add_trace(go.Bar(
            x=df['Category'],
            y=df['Max'] - df['Score'],
            name='Room for Improvement',
            marker_color='#ecf0f1',
            base=df['Score']
        ))
        
        fig.update_layout(
            barmode='stack',
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Income vs Expense Trend
    st.subheader("📈 Income vs Expense Trend")
    
    trend = analytics_service.get_income_vs_expense_trend(user_id, months)
    
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
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🍕 Spending by Category")
        
        categories = analytics_service.get_spending_by_category(user_id, months)
        
        if categories:
            df = pd.DataFrame(categories)
            
            fig = px.treemap(
                df,
                path=['category'],
                values='total',
                color='percentage',
                color_continuous_scale='RdYlGn_r'
            )
            fig.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
            # Table
            df_display = df[['category', 'total', 'count', 'percentage']].copy()
            df_display['total'] = df_display['total'].apply(lambda x: f"₹{x:,.0f}")
            df_display['percentage'] = df_display['percentage'].apply(lambda x: f"{x:.1f}%")
            df_display.columns = ['Category', 'Total', 'Transactions', 'Share']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No expense data available.")
    
    with col2:
        st.subheader("📅 Daily Spending Pattern")
        
        daily = analytics_service.get_spending_by_category(user_id, 1)
        
        # Get daily data
        daily_spending = db.execute(
            """SELECT strftime('%w', date) as day_of_week, SUM(amount) as total
               FROM expenses
               WHERE user_id = ? AND date >= date('now', '-30 days')
               GROUP BY day_of_week
               ORDER BY day_of_week""",
            (user_id,),
            fetch=True
        )
        
        if daily_spending:
            days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            df = pd.DataFrame(daily_spending)
            df['day_name'] = df['day_of_week'].apply(lambda x: days[int(x)])
            df['amount'] = df['total'].apply(db.to_rupees)
            
            fig = px.bar(
                df,
                x='day_name',
                y='amount',
                color='amount',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                height=400,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis_title="Day of Week",
                yaxis_title="Average Spending (₹)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data for daily pattern.")
    
    st.markdown("---")
    
    # Top Expenses
    st.subheader("💸 Top Expenses This Month")
    
    now = datetime.now()
    top_expenses = analytics_service.get_top_expenses(user_id, now.year, now.month, 10)
    
    if top_expenses:
        df_data = []
        for i, exp in enumerate(top_expenses, 1):
            df_data.append({
                'Rank': i,
                'Date': exp['date'][:10],
                'Category': exp['category'],
                'Description': exp['description'] or '-',
                'Amount': f"₹{exp['amount']:,.2f}"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No expenses this month.")
    
    st.markdown("---")
    
    # Savings Rate Trend
    st.subheader("💰 Savings Rate Trend")
    
    savings_trend = []
    for t in trend:
        if t['income'] > 0:
            rate = ((t['income'] - t['expense']) / t['income']) * 100
        else:
            rate = 0
        savings_trend.append({
            'month': t['month'],
            'rate': rate
        })
    
    if savings_trend:
        df = pd.DataFrame(savings_trend)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df['rate'],
            mode='lines+markers+text',
            text=[f"{r:.0f}%" for r in df['rate']],
            textposition="top center",
            line=dict(color='#9b59b6', width=3),
            marker=dict(size=10)
        ))
        
        # Add target line at 20%
        fig.add_hline(y=20, line_dash="dash", line_color="green", 
                     annotation_text="Target: 20%", annotation_position="right")
        
        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Month",
            yaxis_title="Savings Rate (%)",
            yaxis=dict(range=[-20, 60])
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.markdown("---")
    st.subheader("💡 Recommendations")
    
    recommendations = []
    
    # Based on savings rate
    if savings_trend and savings_trend[-1]['rate'] < 20:
        recommendations.append("📊 **Improve Savings Rate**: Your current savings rate is below the recommended 20%. Consider reducing discretionary spending.")
    
    # Based on categories
    if categories and categories[0]['percentage'] > 40:
        recommendations.append(f"⚠️ **High Category Concentration**: {categories[0]['category']} accounts for {categories[0]['percentage']:.0f}% of spending. Consider diversifying.")
    
    # Based on health score
    if health['score'] < 60:
        recommendations.append("🎯 **Financial Health**: Your score indicates room for improvement. Focus on budgeting and building an emergency fund.")
    
    # General tips
    if not recommendations:
        recommendations = [
            "✅ You're doing well! Keep maintaining your current habits.",
            "💡 Consider increasing your investments for long-term growth.",
            "🎯 Set specific financial goals to stay motivated."
        ]
    
    for rec in recommendations:
        st.markdown(rec)
