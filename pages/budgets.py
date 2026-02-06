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


def show_budgets():
    """Display budgets page"""
    user = st.session_state.user
    user_id = user['user_id']
    
    st.title("📋 Budgets")
    
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
            format_func=lambda x: datetime(2000, x, 1).strftime('%B')
        )
    
    with col2:
        selected_year = st.selectbox(
            "Select Year",
            options=list(range(current_year - 2, current_year + 1)),
            index=2
        )
    
    # Get budget status
    budgets = analytics_service.get_budget_status(user_id, selected_year, selected_month)
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2 = st.tabs(["📊 Budget Status", "➕ Manage Budgets"])
    
    # Budget Status Tab
    with tab1:
        if budgets:
            # Summary Cards
            total_limit = sum(b['limit'] for b in budgets)
            total_spent = sum(b['spent'] for b in budgets)
            total_remaining = total_limit - total_spent
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Budget", f"₹{total_limit:,.2f}")
            with col2:
                st.metric("Total Spent", f"₹{total_spent:,.2f}")
            with col3:
                st.metric(
                    "Remaining",
                    f"₹{total_remaining:,.2f}",
                    delta=f"{(total_remaining/total_limit*100):.0f}% left" if total_limit > 0 else None
                )
            
            st.markdown("---")
            
            # Budget Progress Bars
            st.subheader("Category Budgets")
            
            for budget in budgets:
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Determine color based on status
                    if budget['status'] == 'ON_TRACK':
                        status_icon = "✅"
                        color = "green"
                    elif budget['status'] == 'WARNING':
                        status_icon = "⚠️"
                        color = "orange"
                    else:
                        status_icon = "❌"
                        color = "red"
                    
                    st.markdown(f"**{status_icon} {budget['category']}**")
                    
                    # Progress bar
                    progress = min(budget['percentage'] / 100, 1.0)
                    st.progress(progress)
                    
                    st.caption(
                        f"Spent: ₹{budget['spent']:,.0f} / Limit: ₹{budget['limit']:,.0f} "
                        f"({budget['percentage']:.1f}%) | Remaining: ₹{budget['remaining']:,.0f}"
                    )
                
                with col2:
                    st.write("")
                    st.write(f"**{budget['percentage']:.0f}%**")
                
                st.markdown("---")
            
            # Visualization
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Budget vs Actual")
                
                df = pd.DataFrame([{
                    'Category': b['category'],
                    'Budget': b['limit'],
                    'Spent': b['spent']
                } for b in budgets])
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['Category'],
                    y=df['Budget'],
                    name='Budget',
                    marker_color='#3498db'
                ))
                fig.add_trace(go.Bar(
                    x=df['Category'],
                    y=df['Spent'],
                    name='Spent',
                    marker_color='#e74c3c'
                ))
                
                fig.update_layout(
                    barmode='group',
                    height=400,
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Budget Utilization")
                
                # Gauge for overall budget
                overall_pct = (total_spent / total_limit * 100) if total_limit > 0 else 0
                
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=overall_pct,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Overall Utilization"},
                    delta={'reference': 80},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 70], 'color': "#d4edda"},
                            {'range': [70, 90], 'color': "#fff3cd"},
                            {'range': [90, 100], 'color': "#f8d7da"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 100
                        }
                    }
                ))
                fig.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No budgets set for this month. Create budgets to track your spending!")
    
    # Manage Budgets Tab
    with tab2:
        st.subheader("Create/Update Budget")
        
        # Get expense categories
        categories = db.get_expense_categories()
        category_names = [c['name'] for c in categories] if categories else [
            "Food & Dining", "Transportation", "Shopping", "Entertainment",
            "Bills & Utilities", "Healthcare", "Education", "Travel",
            "Groceries", "Personal Care", "Others"
        ]
        
        with st.form("budget_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                category = st.selectbox("Category", category_names)
                limit_amount = st.number_input("Budget Limit (₹)", min_value=100.0, step=500.0, format="%.2f")
            
            with col2:
                budget_month = st.selectbox(
                    "Month",
                    options=list(range(1, 13)),
                    index=selected_month - 1,
                    format_func=lambda x: datetime(2000, x, 1).strftime('%B'),
                    key="budget_month"
                )
                budget_year = st.selectbox(
                    "Year",
                    options=list(range(current_year, current_year + 2)),
                    key="budget_year"
                )
            
            alert_threshold = st.slider("Alert Threshold (%)", 50, 95, 80)
            st.caption("You'll be alerted when spending reaches this percentage")
            
            submit = st.form_submit_button("Set Budget", use_container_width=True)
            
            if submit:
                if limit_amount >= 100:
                    result = db.set_budget(
                        user_id=user_id,
                        category=category,
                        limit_amount=db.to_paise(limit_amount),
                        year=budget_year,
                        month=budget_month,
                        alert_threshold=alert_threshold
                    )
                    
                    if result:
                        st.success(f"✅ Budget set for {category}: ₹{limit_amount:,.2f}")
                        db.log_action('USER', user_id, f'Set budget: {category} = ₹{limit_amount}', 'budgets', result)
                        st.rerun()
                    else:
                        st.error("Failed to set budget")
                else:
                    st.error("Budget limit must be at least ₹100")
        
        st.markdown("---")
        
        # Current Budgets
        st.subheader("Current Budgets")
        
        all_budgets = db.get_user_budgets(user_id)
        
        if all_budgets:
            df_data = []
            for b in all_budgets:
                df_data.append({
                    'Category': b['category'],
                    'Limit': f"₹{db.to_rupees(b['limit_amount']):,.2f}",
                    'Month': f"{datetime(2000, b['month'], 1).strftime('%B')} {b['year']}",
                    'Alert At': f"{b['alert_threshold']}%"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Delete budget option
            st.markdown("---")
            st.subheader("Delete Budget")
            
            budget_to_delete = st.selectbox(
                "Select Budget to Delete",
                options=[f"{b['category']} - {datetime(2000, b['month'], 1).strftime('%B')} {b['year']}" for b in all_budgets]
            )
            
            if st.button("Delete Budget", type="secondary"):
                # Find the budget
                parts = budget_to_delete.split(" - ")
                cat = parts[0]
                month_year = parts[1].split()
                month_name = month_year[0]
                year = int(month_year[1])
                month = list(range(1, 13))[['January', 'February', 'March', 'April', 'May', 'June',
                                            'July', 'August', 'September', 'October', 'November', 'December'].index(month_name)]
                
                result = db.execute(
                    "DELETE FROM budgets WHERE user_id = ? AND category = ? AND year = ? AND month = ?",
                    (user_id, cat, year, month)
                )
                
                if result:
                    st.success(f"✅ Budget for {cat} deleted")
                    st.rerun()
        else:
            st.info("No budgets created yet.")
        
        # Quick Set Multiple Budgets
        st.markdown("---")
        st.subheader("Quick Budget Template")
        
        templates = {
            "Balanced": {
                "Food & Dining": 15000,
                "Transportation": 5000,
                "Shopping": 10000,
                "Entertainment": 5000,
                "Bills & Utilities": 8000,
                "Groceries": 8000,
                "Others": 5000
            },
            "Frugal": {
                "Food & Dining": 8000,
                "Transportation": 3000,
                "Shopping": 3000,
                "Entertainment": 2000,
                "Bills & Utilities": 5000,
                "Groceries": 6000,
                "Others": 3000
            },
            "Comfortable": {
                "Food & Dining": 25000,
                "Transportation": 10000,
                "Shopping": 20000,
                "Entertainment": 10000,
                "Bills & Utilities": 12000,
                "Groceries": 15000,
                "Travel": 15000,
                "Others": 10000
            }
        }
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            template = st.selectbox("Select Template", list(templates.keys()))
        
        with col2:
            if st.button("Apply Template", use_container_width=True):
                for category, amount in templates[template].items():
                    db.set_budget(
                        user_id=user_id,
                        category=category,
                        limit_amount=db.to_paise(amount),
                        year=selected_year,
                        month=selected_month
                    )
                st.success(f"✅ Applied '{template}' template!")
                st.rerun()
        
        # Show template preview
        st.caption(f"Template: {template}")
        for cat, amt in templates[template].items():
            st.write(f"• {cat}: ₹{amt:,}")
