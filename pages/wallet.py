"""
Wallet Page
Income, expense, and transfer management
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
    with col2:
        st.metric("Bank Accounts", f"₹{balance['bank']:,.2f}")
    with col3:
        st.metric("Total Available", f"₹{balance['wallet'] + balance['bank']:,.2f}")
    
    st.markdown("---")
    
    # Tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Income", "➖ Add Expense", "💸 Transfer", "🏦 Bank Accounts"])
    
    # Add Income Tab
    with tab1:
        st.subheader("Add Income")
        
        with st.form("income_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                amount = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f")
                source = st.text_input("Source", placeholder="e.g., Salary, Freelance")
            
            with col2:
                category = st.selectbox("Category", [
                    "Salary", "Freelance", "Business", "Investment Returns",
                    "Rental Income", "Interest", "Gift", "Other"
                ])
                account_type = st.selectbox("Add to", ["Wallet", "Bank Account"])
            
            description = st.text_area("Description (Optional)", placeholder="Additional notes...")
            
            # Bank account selection if needed
            account_id = None
            if account_type == "Bank Account":
                bank_accounts = db.get_user_bank_accounts(user_id)
                if bank_accounts:
                    account_options = {f"{a['bank_name']} - {a['nickname'] or a['account_number_last4']}": a['account_id'] 
                                      for a in bank_accounts}
                    selected_account = st.selectbox("Select Bank Account", list(account_options.keys()))
                    account_id = account_options[selected_account]
                else:
                    st.warning("No bank accounts linked. Add a bank account first.")
            
            submit = st.form_submit_button("Add Income", use_container_width=True)
            
            if submit:
                if amount > 0 and source:
                    success, message, result = wallet_service.add_income(
                        user_id=user_id,
                        amount=amount,
                        source=source,
                        category=category,
                        account_type='WALLET' if account_type == "Wallet" else 'BANK',
                        account_id=account_id,
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
                amount = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f", key="exp_amt")
                category = st.selectbox("Category", category_names)
            
            with col2:
                payment_mode = st.selectbox("Payment Mode", ["UPI", "Cash", "Debit Card", "Credit Card", "Net Banking"])
                account_type = st.selectbox("Pay from", ["Wallet", "Bank Account"], key="exp_account")
            
            col1, col2 = st.columns(2)
            
            with col1:
                subcategory = st.text_input("Subcategory (Optional)", placeholder="e.g., Restaurant, Uber")
            with col2:
                merchant = st.text_input("Merchant (Optional)", placeholder="e.g., Swiggy, Amazon")
            
            description = st.text_area("Description (Optional)", placeholder="Additional notes...", key="exp_desc")
            
            # Bank account selection if needed
            account_id = None
            if account_type == "Bank Account":
                bank_accounts = db.get_user_bank_accounts(user_id)
                if bank_accounts:
                    account_options = {f"{a['bank_name']} - {a['nickname'] or a['account_number_last4']}": a['account_id'] 
                                      for a in bank_accounts}
                    selected_account = st.selectbox("Select Bank Account", list(account_options.keys()), key="exp_bank")
                    account_id = account_options[selected_account]
                else:
                    st.warning("No bank accounts linked.")
            
            submit = st.form_submit_button("Add Expense", use_container_width=True)
            
            if submit:
                if amount > 0:
                    payment_mode_map = {
                        "UPI": "UPI",
                        "Cash": "CASH",
                        "Debit Card": "DEBIT_CARD",
                        "Credit Card": "CREDIT_CARD",
                        "Net Banking": "NET_BANKING"
                    }
                    
                    success, message, result = wallet_service.add_expense(
                        user_id=user_id,
                        amount=amount,
                        category=category,
                        payment_mode=payment_mode_map[payment_mode],
                        account_type='WALLET' if account_type == "Wallet" else 'BANK',
                        account_id=account_id,
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
    
    # Transfer Tab
    with tab3:
        st.subheader("Transfer Money")
        
        with st.form("transfer_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                amount = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f", key="tr_amt")
            
            with col2:
                receiver = st.text_input("Recipient", placeholder="Username, email, or mobile")
            
            note = st.text_input("Note (Optional)", placeholder="What's this for?")
            
            submit = st.form_submit_button("Transfer", use_container_width=True)
            
            if submit:
                if amount > 0 and receiver:
                    success, message, result = wallet_service.transfer_funds(
                        sender_id=user_id,
                        receiver_identifier=receiver,
                        amount=amount,
                        note=note
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.info(f"Transferred ₹{result['amount']:,.2f} to {result['receiver']}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("Please enter amount and recipient")
    
    # Bank Accounts Tab
    with tab4:
        st.subheader("Bank Accounts")
        
        bank_accounts = db.get_user_bank_accounts(user_id)
        
        if bank_accounts:
            for acc in bank_accounts:
                with st.expander(f"🏦 {acc['bank_name']} - {acc['nickname'] or acc['account_number_last4']}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Balance", f"₹{db.to_rupees(acc['balance']):,.2f}")
                    with col2:
                        st.write(f"**Type:** {acc['account_type']}")
                        st.write(f"**Account:** ****{acc['account_number_last4']}")
                    with col3:
                        if acc['upi_id']:
                            st.write(f"**UPI:** {acc['upi_id']}")
                        if acc['is_primary']:
                            st.success("Primary Account")
        else:
            st.info("No bank accounts linked yet.")
        
        st.markdown("---")
        st.subheader("Add Bank Account")
        
        # Get master banks
        master_banks = db.get_master_banks()
        
        with st.form("add_bank_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                bank_options = {b['bank_name']: b['bank_id'] for b in master_banks}
                selected_bank = st.selectbox("Bank", list(bank_options.keys()))
                bank_id = bank_options[selected_bank]
                
                account_holder = st.text_input("Account Holder Name")
                account_last4 = st.text_input("Last 4 digits of Account", max_chars=4)
            
            with col2:
                account_type = st.selectbox("Account Type", ["SAVINGS", "CURRENT", "SALARY"])
                nickname = st.text_input("Nickname", placeholder="e.g., Salary Account")
                upi_id = st.text_input("UPI ID (Optional)", placeholder="yourname@bank")
            
            initial_balance = st.number_input("Current Balance (₹)", min_value=0.0, step=1000.0)
            is_primary = st.checkbox("Set as Primary Account")
            
            submit = st.form_submit_button("Add Bank Account", use_container_width=True)
            
            if submit:
                if account_holder and account_last4:
                    result = db.execute_insert(
                        """INSERT INTO bank_accounts 
                           (user_id, bank_id, account_holder, account_number_last4, 
                            account_type, nickname, upi_id, balance, is_primary)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (user_id, bank_id, account_holder, account_last4,
                         account_type, nickname, upi_id, db.to_paise(initial_balance),
                         1 if is_primary else 0)
                    )
                    
                    if result:
                        st.success("✅ Bank account added successfully!")
                        db.log_action('USER', user_id, f'Added bank account: {selected_bank}', 'bank_accounts', result)
                        st.rerun()
                    else:
                        st.error("Failed to add bank account")
                else:
                    st.error("Please fill in required fields")
    
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
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions yet.")
