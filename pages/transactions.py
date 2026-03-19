"""
Transactions Page
Transaction history and filtering
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

from database.db import db


def show_transactions():
    """Display transactions page"""
    user = st.session_state.user
    user_id = user['user_id']
    
    st.title("📊 Transactions")
    
    # Filter Options
    st.subheader("🔍 Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        txn_type = st.selectbox(
            "Transaction Type",
            ["All", "Expenses", "Income"]
        )
    
    with col2:
        date_range = st.selectbox(
            "Date Range",
            ["This Month", "Last Month", "Last 3 Months", "Last 6 Months", "This Year", "Custom"]
        )
    
    # Date range calculation
    now = datetime.now()
    if date_range == "This Month":
        start_date = now.replace(day=1).strftime('%Y-%m-%d')
        # Add one day to end_date to include today's transactions (date stored with time)
        end_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_range == "Last Month":
        last_month = now.replace(day=1) - timedelta(days=1)
        start_date = last_month.replace(day=1).strftime('%Y-%m-%d')
        end_date = last_month.strftime('%Y-%m-%d')
    elif date_range == "Last 3 Months":
        start_date = (now - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_range == "Last 6 Months":
        start_date = (now - timedelta(days=180)).strftime('%Y-%m-%d')
        end_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_range == "This Year":
        start_date = now.strftime('%Y-01-01')
        end_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
    else:
        start_date = None
        end_date = None
    
    with col3:
        if date_range == "Custom":
            start_date = st.date_input("From", value=now - timedelta(days=30)).strftime('%Y-%m-%d')
        else:
            st.text_input("From", value=start_date, disabled=True)
    
    with col4:
        if date_range == "Custom":
            end_date = st.date_input("To", value=now + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            st.text_input("To", value=end_date, disabled=True)
    
    # Category filter for expenses
    category_filter = None
    if txn_type in ["All", "Expenses"]:
        categories = db.get_expense_categories()
        category_names = ["All Categories"] + [c['name'] for c in categories]
        selected_category = st.selectbox("Category", category_names)
        if selected_category != "All Categories":
            category_filter = selected_category
    
    st.markdown("---")
    
    # Fetch transactions based on filters
    all_transactions = []
    
    if txn_type in ["All", "Expenses"]:
        expenses = db.get_user_expenses(
            user_id, 
            start_date=start_date, 
            end_date=end_date,
            category=category_filter,
            limit=200
        )
        for e in expenses:
            all_transactions.append({
                'id': e['expense_id'],
                'date': e['date'],
                'type': 'Expense',
                'category': e['category'],
                'subcategory': e.get('subcategory', ''),
                'amount': -db.to_rupees(e['amount']),
                'description': e.get('description', ''),
                'payment_mode': e.get('payment_mode', ''),
                'merchant': e.get('merchant', ''),
                'icon': '🔴'
            })
    
    if txn_type in ["All", "Income"]:
        income = db.get_user_income(user_id, start_date=start_date, end_date=end_date, limit=200)
        for i in income:
            all_transactions.append({
                'id': i['income_id'],
                'date': i['date'],
                'type': 'Income',
                'category': i.get('category', ''),
                'subcategory': i.get('source', ''),
                'amount': db.to_rupees(i['amount']),
                'description': i.get('description', ''),
                'payment_mode': '',
                'merchant': '',
                'icon': '🟢'
            })
    

    
    # Sort by date
    all_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    # Summary
    st.subheader("📈 Summary")
    
    total_income = sum(t['amount'] for t in all_transactions if t['amount'] > 0)
    total_expense = abs(sum(t['amount'] for t in all_transactions if t['amount'] < 0))
    net = total_income - total_expense
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Transactions", len(all_transactions))
    with col2:
        st.metric("Total Income", f"₹{total_income:,.2f}")
    with col3:
        st.metric("Total Expense", f"₹{total_expense:,.2f}")
    with col4:
        st.metric("Net", f"₹{net:,.2f}", delta_color="normal" if net >= 0 else "inverse")
    
    st.markdown("---")
    
    # Visualization
    if all_transactions:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Daily Trend")
            
            # Group by date
            df = pd.DataFrame(all_transactions)
            df['date_only'] = pd.to_datetime(df['date']).dt.date
            
            daily = df.groupby('date_only').agg({
                'amount': 'sum'
            }).reset_index()
            
            fig = px.area(
                daily, x='date_only', y='amount',
                title='',
                labels={'date_only': 'Date', 'amount': 'Amount (₹)'}
            )
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.subheader("By Type")
            
            type_summary = df.groupby('type').agg({
                'amount': lambda x: abs(x).sum()
            }).reset_index()
            
            fig = px.pie(
                type_summary, values='amount', names='type',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, width='stretch')
    
    st.markdown("---")
    
    # Transaction Table
    st.subheader("📜 Transaction History")
    
    if all_transactions:
        # Search
        search = st.text_input("🔍 Search transactions", placeholder="Search by category, description, or merchant...")
        
        filtered_transactions = all_transactions
        if search:
            search_lower = search.lower()
            filtered_transactions = [
                t for t in all_transactions
                if search_lower in t['category'].lower() or
                   search_lower in str(t['description']).lower() or
                   search_lower in str(t['merchant']).lower() or
                   search_lower in str(t['subcategory']).lower()
            ]
        
        # Display
        if filtered_transactions:
            df_data = []
            for t in filtered_transactions:
                df_data.append({
                    'Date': t['date'][:16],
                    'Type': f"{t['icon']} {t['type']}",
                    'Category': t['category'],
                    'Description': t['description'] or t['subcategory'] or '-',
                    'Amount': f"₹{abs(t['amount']):,.2f}" if t['amount'] < 0 else f"+₹{t['amount']:,.2f}",
                    'Payment': t['payment_mode'] or '-'
                })
            
            df = pd.DataFrame(df_data)
            
            # Pagination
            items_per_page = 20
            total_pages = max(1, (len(df) + items_per_page - 1) // items_per_page)
            
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            st.dataframe(df.iloc[start_idx:end_idx], width='stretch', hide_index=True)
            st.caption(f"Showing {start_idx + 1}-{min(end_idx, len(df))} of {len(df)} transactions")
            
            # Export
            if st.button("📥 Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"transactions_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No transactions match your search.")
    else:
        st.info("No transactions found for the selected filters.")
