"""
Enhanced UI Components
Production-grade Streamlit UI components with modern design
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from database.db import db


class ModernUIComponents:
    """Production-grade UI components"""
    
    # Color schemes
    COLORS = {
        'primary': '#667eea',
        'secondary': '#764ba2',
        'success': '#11998e',
        'danger': '#e74c3c',
        'warning': '#f39c12',
        'info': '#3498db',
        'background': '#f8f9fa',
        'card': '#ffffff',
    }
    
    GRADIENTS = {
        'blue': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'green': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
        'orange': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        'purple': 'linear-gradient(135deg, #5B247A 0%, #1BCEED 100%)',
        'dark': 'linear-gradient(135deg, #2C3E50 0%, #4CA1AF 100%)',
    }
    
    @staticmethod
    def render_metric_card(
        title: str,
        value: str,
        delta: str = None,
        delta_color: str = "normal",
        icon: str = None,
        help_text: str = None
    ):
        """
        Render a modern metric card
        
        Args:
            title: Metric title
            value: Metric value
            delta: Change indicator
            delta_color: Color for delta (normal, inverse, off)
            icon: Optional icon
            help_text: Tooltip text
        """
        col = st.container()
        with col:
            st.metric(
                label=title,
                value=value,
                delta=delta,
                delta_color=delta_color,
                help=help_text
            )
    
    @staticmethod
    def render_balance_card(balance: Dict):
        """
        Render balance summary card
        
        Args:
            balance: Balance data dict
        """
        st.markdown(f"""
        <div style="
            background: {ModernUIComponents.GRADIENTS['blue']};
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1rem;
        ">
            <h3 style="margin: 0 0 1rem 0;">💰 Net Worth</h3>
            <h1 style="margin: 0; font-size: 2.5rem;">₹{balance.get('net_worth', 0):,.2f}</h1>
            <div style="
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                margin-top: 1rem;
            ">
                <div>
                    <p style="margin: 0; opacity: 0.8;">Wallet</p>
                    <p style="margin: 0; font-weight: bold;">₹{balance.get('wallet', 0):,.2f}</p>
                </div>
                <div>
                    <p style="margin: 0; opacity: 0.8;">Bank</p>
                    <p style="margin: 0; font-weight: bold;">₹{balance.get('bank', 0):,.2f}</p>
                </div>
                <div>
                    <p style="margin: 0; opacity: 0.8;">Investments</p>
                    <p style="margin: 0; font-weight: bold;">₹{balance.get('investments', 0):,.2f}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_monthly_summary_card(monthly: Dict):
        """
        Render monthly summary card
        
        Args:
            monthly: Monthly data dict
        """
        savings_rate = monthly.get('savings_rate', 0)
        savings_color = "green" if savings_rate >= 20 else "orange" if savings_rate >= 10 else "red"
        
        st.markdown(f"""
        <div style="
            background: {ModernUIComponents.GRADIENTS['green']};
            padding: 1.5rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 1rem;
        ">
            <h3 style="margin: 0 0 1rem 0;">📊 This Month</h3>
            <div style="
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 1rem;
                text-align: center;
            ">
                <div>
                    <p style="margin: 0; opacity: 0.8;">Income</p>
                    <p style="margin: 0; font-weight: bold; font-size: 1.2rem;">₹{monthly.get('income', 0):,.0f}</p>
                </div>
                <div>
                    <p style="margin: 0; opacity: 0.8;">Expenses</p>
                    <p style="margin: 0; font-weight: bold; font-size: 1.2rem;">₹{monthly.get('expense', 0):,.0f}</p>
                </div>
                <div>
                    <p style="margin: 0; opacity: 0.8;">Savings</p>
                    <p style="margin: 0; font-weight: bold; font-size: 1.2rem;">₹{monthly.get('savings', 0):,.0f}</p>
                </div>
                <div>
                    <p style="margin: 0; opacity: 0.8;">Rate</p>
                    <p style="margin: 0; font-weight: bold; font-size: 1.2rem; color: {savings_color};">{savings_rate:.1f}%</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_budget_progress(budgets: List[Dict]):
        """
        Render budget progress bars
        
        Args:
            budgets: List of budget dicts
        """
        if not budgets:
            st.info("No budgets set. Set budgets to track your spending!")
            return
        
        for budget in budgets:
            percentage = min(budget['percentage'] / 100, 1.0)
            
            # Color based on status
            if budget['status'] == 'ON_TRACK':
                color = '#27ae60'
            elif budget['status'] == 'WARNING':
                color = '#f39c12'
            else:
                color = '#e74c3c'
            
            st.markdown(f"**{budget['category']}**")
            
            # Progress bar
            progress_value = min(budget['percentage'] / 100, 1.0)
            st.progress(progress_value)
            
            # Stats
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                st.caption(f"Spent: ₹{budget['spent']:,.0f}")
            with col2:
                st.caption(f"Limit: ₹{budget['limit']:,.0f}")
            with col3:
                st.caption(f"{budget['percentage']:.0f}%")
            
            st.markdown("")
    
    @staticmethod
    def render_spending_pie_chart(categories: List[Dict], title: str = "Spending by Category"):
        """
        Render spending pie chart
        
        Args:
            categories: List of category data
            title: Chart title
        """
        if not categories:
            st.info("No spending data available")
            return
        
        df = pd.DataFrame(categories)
        
        # Create color map
        color_map = {}
        for cat in categories:
            color_map[cat['category']] = cat.get('color', '#667eea')
        
        fig = px.pie(
            df,
            values='total',
            names='category',
            hole=0.4,
            color='category',
            color_discrete_map=color_map,
            title=title
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='%{label}: ₹%{value:,.0f} (%{percent})'
        )
        
        fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_income_expense_trend(trend_data: List[Dict], months: int = 6):
        """
        Render income vs expense trend chart
        
        Args:
            trend_data: List of monthly data
            months: Number of months to show
        """
        if not trend_data:
            st.info("No trend data available")
            return
        
        df = pd.DataFrame(trend_data)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Bar chart for income and expenses
        fig.add_trace(
            go.Bar(
                x=df['month'],
                y=df['income'],
                name='Income',
                marker_color='#27ae60',
                hovertemplate='Income: ₹%{y:,.0f}'
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Bar(
                x=df['month'],
                y=df['expense'],
                name='Expense',
                marker_color='#e74c3c',
                hovertemplate='Expense: ₹%{y:,.0f}'
            ),
            secondary_y=False
        )
        
        # Line for savings
        df['savings'] = df['income'] - df['expense']
        fig.add_trace(
            go.Scatter(
                x=df['month'],
                y=df['savings'],
                name='Savings',
                mode='lines+markers',
                line=dict(color='#3498db', width=3),
                hovertemplate='Savings: ₹%{y:,.0f}'
            ),
            secondary_y=True
        )
        
        fig.update_layout(
            barmode='group',
            height=400,
            title='Income vs Expense Trend',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_yaxes(title_text="Amount (₹)", secondary_y=False)
        fig.update_yaxes(title_text="Savings (₹)", secondary_y=True)
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_daily_spending_chart(daily_data: List[Dict], days: int = 30):
        """
        Render daily spending bar chart
        
        Args:
            daily_data: List of daily spending data
            days: Number of days to show
        """
        if not daily_data:
            st.info("No daily data available")
            return
        
        df = pd.DataFrame(daily_data)
        
        fig = px.bar(
            df,
            x='date',
            y='amount',
            title=f'Daily Spending (Last {days} Days)',
            color='amount',
            color_continuous_scale='RdYlGn_r'
        )
        
        fig.update_traces(
            hovertemplate='%{x}: ₹%{y:,.0f}'
        )
        
        fig.update_layout(
            height=350,
            xaxis_title='Date',
            yaxis_title='Amount (₹)',
            coloraxis_showscale=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_health_gauge(score: int, breakdown: Dict):
        """
        Render financial health gauge
        
        Args:
            score: Health score (0-100)
            breakdown: Score breakdown dict
        """
        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': ModernUIComponents._get_health_rating(score)},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#3498db"},
                'steps': [
                    {'range': [0, 40], 'color': "#f8d7da"},
                    {'range': [40, 60], 'color': "#fff3cd"},
                    {'range': [60, 80], 'color': "#d4edda"},
                    {'range': [80, 100], 'color': "#28a745"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': score
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Breakdown metrics
        if breakdown:
            ModernUIComponents._render_health_breakdown(breakdown)
    
    @staticmethod
    def _get_health_rating(score: int) -> str:
        """Get health rating text"""
        if score >= 80:
            return "🌟 Excellent"
        elif score >= 60:
            return "✅ Good"
        elif score >= 40:
            return "⚠️ Fair"
        else:
            return "❌ Needs Work"
    
    @staticmethod
    def _render_health_breakdown(breakdown: Dict):
        """Render health score breakdown"""
        labels = {
            'savings_rate': 'Savings Rate',
            'budget_compliance': 'Budget Compliance',
            'emergency_fund': 'Emergency Fund',
            'investment_diversity': 'Investment Diversity',
            'activity': 'Transaction Activity'
        }
        
        cols = st.columns(5)
        
        for i, (key, values) in enumerate(breakdown.items()):
            label = labels.get(key, key.title())
            with cols[i]:
                st.metric(
                    label=label,
                    value=f"{values['score']}/{values['max']}",
                    delta=f"{values['value']:.1f}%"
                )
    
    @staticmethod
    def render_transactions_table(transactions: List[Dict], max_rows: int = 10):
        """
        Render transactions in a formatted table
        
        Args:
            transactions: List of transaction dicts
            max_rows: Maximum rows to show
        """
        if not transactions:
            st.info("No transactions found")
            return
        
        # Create DataFrame
        df = pd.DataFrame(transactions[:max_rows])
        
        # Format columns
        if 'amount' in df.columns:
            df['amount'] = df['amount'].apply(lambda x: f"₹{x:,.0f}")
        
        if 'date' in df.columns:
            df['date'] = df['date'].apply(lambda x: str(x)[:10])
        
        # Display
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
    
    @staticmethod
    def render_investment_portfolio(holdings: List[Dict]):
        """
        Render investment portfolio with charts
        
        Args:
            holdings: List of investment holdings
        """
        if not holdings:
            st.info("No investments yet")
            return
        
        # Summary metrics
        total_invested = sum(h.get('invested_amount', 0) for h in holdings)
        total_value = sum(h.get('current_value', 0) for h in holdings)
        total_pl = total_value - total_invested
        pl_pct = (total_pl / total_invested * 100) if total_invested > 0 else 0
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Invested", f"₹{total_invested:,.0f}")
        
        with col2:
            st.metric("Current Value", f"₹{total_value:,.0f}")
        
        with col3:
            st.metric("Profit/Loss", f"₹{total_pl:+,.0f}", delta=f"{pl_pct:+.2f}%")
        
        with col4:
            st.metric("Holdings", len(holdings))
        
        # Holdings table
        st.subheader("📊 Holdings")
        
        holdings_df = pd.DataFrame(holdings)
        if not holdings_df.empty:
            # Format columns
            holdings_df['invested_amount'] = holdings_df['invested_amount'].apply(lambda x: f"₹{x:,.0f}")
            holdings_df['current_value'] = holdings_df['current_value'].apply(lambda x: f"₹{x:,.0f}")
            holdings_df['profit_loss'] = holdings_df['profit_loss'].apply(lambda x: f"₹{x:+,.0f}")
            
            st.dataframe(
                holdings_df[['asset_symbol', 'asset_name', 'units_owned', 'invested_amount', 'current_value', 'profit_loss', 'profit_loss_percent']],
                use_container_width=True,
                hide_index=True
            )
        
        # Pie chart by asset type
        if holdings:
            df = pd.DataFrame(holdings)
            if 'asset_type' in df.columns:
                fig = px.pie(
                    df,
                    values='current_value',
                    names='asset_type',
                    title='Portfolio by Asset Type',
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_goal_progress(goals: List[Dict]):
        """
        Render financial goals with progress
        
        Args:
            goals: List of goal dicts
        """
        if not goals:
            st.info("No goals set. Set financial goals to stay motivated!")
            return
        
        for goal in goals:
            target = goal.get('target_amount', 0)
            current = goal.get('current_savings', 0)
            progress = (current / target * 100) if target > 0 else 0
            
            # Priority badge
            priority = goal.get('priority', 'MEDIUM')
            priority_colors = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}
            priority_badge = priority_colors.get(priority, '⚪')
            
            with st.expander(f"{priority_badge} {goal.get('goal_name', 'Goal')}", expanded=True):
                # Progress
                progress_val = min(progress / 100, 1.0)
                st.progress(progress_val)
                
                # Stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption("Current")
                    st.markdown(f"**₹{current:,.0f}**")
                with col2:
                    st.caption("Target")
                    st.markdown(f"**₹{target:,.0f}**")
                with col3:
                    st.caption("Remaining")
                    remaining = target - current
                    st.markdown(f"**₹{remaining:,.0f}**")
                
                # Target date
                if goal.get('target_date'):
                    st.caption(f"Target Date: {goal['target_date']}")
    
    @staticmethod
    def render_recent_transactions(transactions: List[Dict]):
        """
        Render recent transactions list
        
        Args:
            transactions: List of recent transactions
        """
        if not transactions:
            st.info("No recent transactions")
            return
        
        for txn in transactions[:5]:
            amount = txn.get('amount', 0)
            is_income = txn.get('type') == 'Income' or txn.get('txn_type') in ['INCOME', 'TRANSFER_IN']
            
            color = "green" if is_income else "red"
            icon = "🟢" if is_income else "🔴"
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{icon} **{txn.get('category', txn.get('description', 'Transaction'))}**")
                st.caption(txn.get('date', '')[:10])
            with col2:
                st.markdown(
                    f"<span style='color:{color}; font-weight:bold;'>₹{abs(amount):,.0f}</span>",
                    unsafe_allow_html=True
                )
            
            st.markdown("---")
    
    @staticmethod
    def render_admin_metrics(metrics: Dict):
        """
        Render admin dashboard metrics
        
        Args:
            metrics: Admin metrics dict
        """
        st.markdown("### 📊 Platform Overview")
        
        # User metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Users",
                metrics.get('total_users', 0),
                delta=metrics.get('new_users_7d', 0),
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "Active Users",
                metrics.get('active_users', 0)
            )
        
        with col3:
            st.metric(
                "Total Transactions",
                metrics.get('total_transactions', 0)
            )
        
        with col4:
            st.metric(
                "Total Volume",
                f"₹{metrics.get('total_volume', 0):,.0f}"
            )
        
        # Financial metrics
        st.markdown("### 💰 Financial Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Wallet Total",
                f"₹{metrics.get('wallet_total', 0):,.0f}"
            )
        
        with col2:
            st.metric(
                "Bank Total",
                f"₹{metrics.get('bank_total', 0):,.0f}"
            )
        
        with col3:
            st.metric(
                "Investments",
                f"₹{metrics.get('investment_total', 0):,.0f}"
            )
        
        with col4:
            st.metric(
                "Pending Flags",
                metrics.get('pending_fraud_flags', 0),
                delta_color="inverse"
            )


# Singleton instance
ui_components = ModernUIComponents()
