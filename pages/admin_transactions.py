"""
Admin Transactions Page
View and monitor all platform transactions
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

from database.db import db


def show_admin_transactions():
    """Display admin transactions page"""
    admin = st.session_state.admin
    
    st.title("💰 Transaction Monitor")
    
    # Filters
    st.subheader("🔍 Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        txn_type = st.selectbox("Type", ["All", "Expenses", "Income", "Transfers"])
    
    with col2:
        date_range = st.selectbox("Period", ["Today", "This Week", "This Month", "Last Month", "Custom"])
    
    # Calculate date range
    now = datetime.now()
    if date_range == "Today":
        start_date = now.strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
    elif date_range == "This Week":
        start_date = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        end_date = now.strftime('%Y-%m-%d')
    elif date_range == "This Month":
        start_date = now.strftime('%Y-%m-01')
        end_date = now.strftime('%Y-%m-%d')
    elif date_range == "Last Month":
        last_month = now.replace(day=1) - timedelta(days=1)
        start_date = last_month.strftime('%Y-%m-01')
        end_date = last_month.strftime('%Y-%m-%d')
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
            end_date = st.date_input("To", value=now).strftime('%Y-%m-%d')
        else:
            st.text_input("To", value=end_date, disabled=True)
    
    # Second row of filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_amount = st.number_input("Min Amount (₹)", min_value=0, value=0, step=1000)
    
    with col2:
        user_filter = st.text_input("User (email/username)", placeholder="Leave empty for all")
    
    with col3:
        limit = st.selectbox("Show", [50, 100, 200, 500], index=0)
    
    st.markdown("---")
    
    # Fetch transactions based on filters
    all_transactions = []
    
    # Get user_id if filter specified
    user_id_filter = None
    if user_filter:
        user = db.get_user_by_email(user_filter) or db.get_user_by_username(user_filter)
        if user:
            user_id_filter = user['user_id']
    
    # Get expenses
    if txn_type in ["All", "Expenses"]:
        if user_id_filter:
            expenses = db.execute(
                """SELECT e.*, u.username, u.email 
                   FROM expenses e
                   JOIN users u ON e.user_id = u.user_id
                   WHERE e.user_id = ? AND e.date >= ? AND e.date <= ? AND e.amount >= ?
                   ORDER BY e.date DESC LIMIT ?""",
                (user_id_filter, start_date, end_date + " 23:59:59", db.to_paise(min_amount), limit),
                fetch=True
            )
        else:
            expenses = db.execute(
                """SELECT e.*, u.username, u.email 
                   FROM expenses e
                   JOIN users u ON e.user_id = u.user_id
                   WHERE e.date >= ? AND e.date <= ? AND e.amount >= ?
                   ORDER BY e.date DESC LIMIT ?""",
                (start_date, end_date + " 23:59:59", db.to_paise(min_amount), limit),
                fetch=True
            )
        
        for e in expenses:
            all_transactions.append({
                'id': e['expense_id'],
                'date': e['date'],
                'type': 'Expense',
                'user': e['username'],
                'email': e['email'],
                'category': e['category'],
                'amount': db.to_rupees(e['amount']),
                'description': e.get('description', ''),
                'icon': '🔴'
            })
    
    # Get income
    if txn_type in ["All", "Income"]:
        if user_id_filter:
            income = db.execute(
                """SELECT i.*, u.username, u.email 
                   FROM income i
                   JOIN users u ON i.user_id = u.user_id
                   WHERE i.user_id = ? AND i.date >= ? AND i.date <= ? AND i.amount >= ?
                   ORDER BY i.date DESC LIMIT ?""",
                (user_id_filter, start_date, end_date + " 23:59:59", db.to_paise(min_amount), limit),
                fetch=True
            )
        else:
            income = db.execute(
                """SELECT i.*, u.username, u.email 
                   FROM income i
                   JOIN users u ON i.user_id = u.user_id
                   WHERE i.date >= ? AND i.date <= ? AND i.amount >= ?
                   ORDER BY i.date DESC LIMIT ?""",
                (start_date, end_date + " 23:59:59", db.to_paise(min_amount), limit),
                fetch=True
            )
        
        for i in income:
            all_transactions.append({
                'id': i['income_id'],
                'date': i['date'],
                'type': 'Income',
                'user': i['username'],
                'email': i['email'],
                'category': i.get('source', 'N/A'),
                'amount': db.to_rupees(i['amount']),
                'description': i.get('description', ''),
                'icon': '🟢'
            })
    
    # Get transfers
    if txn_type in ["All", "Transfers"]:
        if user_id_filter:
            transfers = db.execute(
                """SELECT t.*, 
                          s.username as sender_name, s.email as sender_email,
                          r.username as receiver_name, r.email as receiver_email
                   FROM transfers t
                   JOIN users s ON t.sender_id = s.user_id
                   JOIN users r ON t.receiver_id = r.user_id
                   WHERE (t.sender_id = ? OR t.receiver_id = ?) 
                   AND t.date >= ? AND t.date <= ? AND t.amount >= ?
                   ORDER BY t.date DESC LIMIT ?""",
                (user_id_filter, user_id_filter, start_date, end_date + " 23:59:59", 
                 db.to_paise(min_amount), limit),
                fetch=True
            )
        else:
            transfers = db.execute(
                """SELECT t.*, 
                          s.username as sender_name, s.email as sender_email,
                          r.username as receiver_name, r.email as receiver_email
                   FROM transfers t
                   JOIN users s ON t.sender_id = s.user_id
                   JOIN users r ON t.receiver_id = r.user_id
                   WHERE t.date >= ? AND t.date <= ? AND t.amount >= ?
                   ORDER BY t.date DESC LIMIT ?""",
                (start_date, end_date + " 23:59:59", db.to_paise(min_amount), limit),
                fetch=True
            )
        
        for t in transfers:
            all_transactions.append({
                'id': t['transfer_id'],
                'date': t['date'],
                'type': 'Transfer',
                'user': f"{t['sender_name']} → {t['receiver_name']}",
                'email': t['sender_email'],
                'category': 'Transfer',
                'amount': db.to_rupees(t['amount']),
                'description': t.get('note', ''),
                'icon': '💸'
            })
    
    # Sort by date
    all_transactions.sort(key=lambda x: x['date'], reverse=True)
    
    # Summary
    st.subheader("📊 Summary")
    
    total_amount = sum(t['amount'] for t in all_transactions)
    expense_total = sum(t['amount'] for t in all_transactions if t['type'] == 'Expense')
    income_total = sum(t['amount'] for t in all_transactions if t['type'] == 'Income')
    transfer_total = sum(t['amount'] for t in all_transactions if t['type'] == 'Transfer')
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Transactions", len(all_transactions))
    with col2:
        st.metric("Total Volume", f"₹{total_amount:,.0f}")
    with col3:
        st.metric("Expenses", f"₹{expense_total:,.0f}")
    with col4:
        st.metric("Income", f"₹{income_total:,.0f}")
    with col5:
        st.metric("Transfers", f"₹{transfer_total:,.0f}")
    
    st.markdown("---")
    
    # Visualization
    if all_transactions:
        col1, col2 = st.columns(2)
        
        with col1:
            # By type
            type_data = pd.DataFrame(all_transactions).groupby('type').agg({
                'amount': 'sum'
            }).reset_index()
            
            fig = px.pie(
                type_data, values='amount', names='type',
                title='Transaction Volume by Type',
                color_discrete_sequence=['#e74c3c', '#2ecc71', '#3498db']
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # By category (for expenses)
            expense_cats = [t for t in all_transactions if t['type'] == 'Expense']
            if expense_cats:
                cat_df = pd.DataFrame(expense_cats).groupby('category').agg({
                    'amount': 'sum'
                }).reset_index().nlargest(10, 'amount')
                
                fig = px.bar(
                    cat_df, x='amount', y='category', orientation='h',
                    title='Top Expense Categories'
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Transaction Table
    st.subheader("📜 Transaction List")
    
    if all_transactions:
        # Search
        search = st.text_input("🔍 Search", placeholder="Search by user, category, or description...")
        
        filtered = all_transactions
        if search:
            search_lower = search.lower()
            filtered = [t for t in all_transactions if 
                       search_lower in t['user'].lower() or
                       search_lower in t['category'].lower() or
                       search_lower in str(t['description']).lower()]
        
        if filtered:
            df_data = []
            for t in filtered:
                df_data.append({
                    'Date': t['date'][:16],
                    'Type': f"{t['icon']} {t['type']}",
                    'User': t['user'],
                    'Category': t['category'],
                    'Amount': f"₹{t['amount']:,.2f}",
                    'Description': (t['description'] or '-')[:40]
                })
            
            df = pd.DataFrame(df_data)
            
            # Pagination
            items_per_page = 25
            total_pages = max(1, (len(df) + items_per_page - 1) // items_per_page)
            
            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True, hide_index=True)
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
