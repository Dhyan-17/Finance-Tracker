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
            
            # Budget vs Actual Chart
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
        else:
            st.info("No budgets set for this month. Create budgets to track your spending!")
    
    # Manage Budgets Tab - Simple Version
    with tab2:
        st.subheader("Set Budget")
        
        # Get expense categories
        categories = db.get_expense_categories()
        category_names = [c['name'] for c in categories] if categories else [
            "Food & Dining", "Transportation", "Shopping", "Entertainment",
            "Bills & Utilities", "Healthcare", "Education", "Travel",
            "Groceries", "Personal Care", "Others"
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            category = st.selectbox("Category", category_names)
        
        with col2:
            budget_month = st.selectbox(
                "Month",
                options=list(range(1, 13)),
                index=selected_month - 1,
                format_func=lambda x: datetime(2000, x, 1).strftime('%B')
            )
        
        budget_year = selected_year
        
        # Check if budget exists
        existing = db.get_budget_exists(user_id, category, budget_year, budget_month)
        
        if existing:
            current = db.to_rupees(existing['limit_amount'])
            st.info(f"Current budget: ₹{current:,.2f}")
            amount = st.number_input("New Amount (₹)", min_value=100.0, value=float(current), step=100.0)
            if st.button("Update Budget"):
                db.set_budget(user_id, category, db.to_paise(amount), budget_year, budget_month, 80, "replace")
                st.success("Budget updated!")
                st.rerun()
        else:
            amount = st.number_input("Budget Amount (₹)", min_value=100.0, value=5000.0, step=100.0)
            if st.button("Create Budget"):
                db.set_budget(user_id, category, db.to_paise(amount), budget_year, budget_month, 80, "replace")
                st.success("Budget created!")
                st.rerun()
        
        st.markdown("---")
        
        # Show all budgets
        st.subheader("All Budgets")
        all_budgets = db.get_user_budgets(user_id)
        
        if all_budgets:
            for b in all_budgets:
                st.write(f"• {b['category']} - ₹{db.to_rupees(b['limit_amount']):,.2f} ({datetime(2000, b['month'], 1).strftime('%B')} {b['year']})")
        else:
            st.info("No budgets yet")
