"""
Wallet Page
Income and expense management
"""

import streamlit as st
from datetime import datetime
import pandas as pd

from database.db import db
from services.wallet_service import wallet_service


def show_wallet():
    """Display wallet management page"""
    user = st.session_state.user
    user_id = user['user_id']
    
    st.title("💳 Wallet")
    
    # Balance Cards
    balance = wallet_service.get_total_balance(user_id)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Wallet Balance", f"₹{balance['wallet']:,.2f}")
    
    st.markdown("---")
    
    # Tabs for different operations
    tab1, tab2 = st.tabs(["➕ Add Income", "➖ Add Expense"])
    
    # Add Income Tab
    with tab1:
        st.subheader("Add Income")
        
        with st.form("income_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
                source = st.text_input("Source", placeholder="e.g., Salary, Freelance")
            
            with col2:
                category = st.selectbox("Category", [
                    "Salary", "Freelance", "Business", "Investment Returns",
                    "Rental Income", "Interest", "Gift", "Other"
                ])
            
            account_type = 'WALLET'
            account_id = None
            
            description = st.text_area("Description (Optional)", placeholder="Additional notes...")
            
            submit = st.form_submit_button("Add Income", width='stretch')
            
            if submit:
                if amount > 0 and source:
                    success, message, result = wallet_service.add_income(
                        user_id=user_id,
                        amount=amount,
                        source=source,
                        category=category,
                        account_type='WALLET',
                        account_id=None,
                        description=description
                    )
                    
                    if success:
                        st.success(f"✅ {message} | New Balance: ₹{result['new_balance']:,.2f}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("Please fill in amount and source")
    
    # Add Expense Tab
    with tab2:
        st.subheader("Add Expense")
        
        # Get expense categories
        categories = db.get_expense_categories()
        category_names = [c['name'] for c in categories] if categories else [
            "Food & Dining", "Transportation", "Shopping", "Entertainment",
            "Bills & Utilities", "Healthcare", "Education", "Travel",
            "Groceries", "Personal Care", "Others"
        ]
        
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f", key="exp_amt")
                category = st.selectbox("Category", category_names)
            
            with col2:
                # Get all bank accounts for selection
                account_type = 'WALLET'
            account_id = None
            
            col1, col2 = st.columns(2)
            
            with col1:
                subcategory = st.text_input("Subcategory (Optional)", placeholder="e.g., Restaurant, Uber")
            with col2:
                merchant = st.text_input("Merchant (Optional)", placeholder="e.g., Swiggy, Amazon")
            
            description = st.text_area("Description (Optional)", placeholder="Additional notes...", key="exp_desc")
            
            submit = st.form_submit_button("Add Expense", width='stretch')
            
            if submit:
                if amount > 0:
                    success, message, result = wallet_service.add_expense(
                        user_id=user_id,
                        amount=amount,
                        category=category,
                        payment_mode='UPI',
                        account_type='WALLET',
                        account_id=None,
                        description=description,
                        subcategory=subcategory,
                        merchant=merchant
                    )
                    
                    if success:
                        msg = f"✅ {message} | New Balance: ₹{result['new_balance']:,.2f}"
                        if result.get('budget_warning'):
                            msg += f"\n⚠️ Budget Alert: {result['budget_warning']}"
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("Please enter a valid amount")
    
    # Recent Wallet Transactions
    st.markdown("---")
    st.subheader("📜 Recent Wallet Transactions")
    
    transactions = db.get_wallet_transactions(user_id, limit=10)
    
    if transactions:
        df_data = []
        for t in transactions:
            df_data.append({
                'Date': t['date'][:16],
                'Type': t['txn_type'],
                'Amount': f"₹{db.to_rupees(t['amount']):,.2f}",
                'Balance After': f"₹{db.to_rupees(t['balance_after']):,.2f}",
                'Description': t['description'] or '-'
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No transactions yet.")
