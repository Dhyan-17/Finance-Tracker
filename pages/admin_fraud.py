"""
Admin Fraud Detection Page
Fraud monitoring and alerts
"""

import streamlit as st
import plotly.express as px
import pandas as pd

from database.db import db
from services.analytics_service import analytics_service


def show_admin_fraud():
    """Display admin fraud detection page"""
    admin = st.session_state.admin
    admin_id = admin['admin_id']
    
    st.title("🚨 Fraud Detection")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Alerts", "💸 Large Transactions", "📊 Overspending", "⚙️ Rules"])
    
    # Alerts Tab
    with tab1:
        st.subheader("Fraud Alerts")
        
        # Filter
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_filter = st.selectbox("Status", ["All", "PENDING", "REVIEWED", "CLEARED", "CONFIRMED"])
        with col2:
            severity_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
        with col3:
            limit = st.selectbox("Show", [25, 50, 100], key="alert_limit")
        
        # Get fraud flags
        flags = db.get_fraud_flags(
            status=status_filter if status_filter != "All" else None,
            severity=severity_filter if severity_filter != "All" else None,
            limit=limit
        )
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        
        pending = sum(1 for f in flags if f['status'] == 'PENDING')
        critical = sum(1 for f in flags if f['severity'] == 'CRITICAL')
        high = sum(1 for f in flags if f['severity'] == 'HIGH')
        
        with col1:
            st.metric("Total Alerts", len(flags))
        with col2:
            st.metric("Pending Review", pending)
        with col3:
            st.metric("Critical", critical)
        with col4:
            st.metric("High", high)
        
        st.markdown("---")
        
        # Alerts List
        if flags:
            for flag in flags:
                severity_colors = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }
                severity_icon = severity_colors.get(flag['severity'], '⚪')
                
                with st.expander(
                    f"{severity_icon} {flag['rule_name']} - {flag['username']} ({flag['status']})",
                    expanded=flag['status'] == 'PENDING'
                ):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User:** {flag['username']} ({flag['email']})")
                        st.write(f"**Rule:** {flag['rule_name']}")
                        st.write(f"**Severity:** {flag['severity']}")
                        st.write(f"**Description:** {flag['description']}")
                    
                    with col2:
                        if flag['amount']:
                            st.write(f"**Amount:** ₹{db.to_rupees(flag['amount']):,.2f}")
                        st.write(f"**Date:** {flag['created_at'][:16]}")
                        st.write(f"**Status:** {flag['status']}")
                    
                    # Actions
                    if flag['status'] == 'PENDING':
                        st.markdown("---")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("✅ Clear", key=f"clear_{flag['flag_id']}"):
                                db.execute(
                                    """UPDATE fraud_flags 
                                       SET status = 'CLEARED', reviewed_by = ?, reviewed_at = datetime('now')
                                       WHERE flag_id = ?""",
                                    (admin_id, flag['flag_id'])
                                )
                                db.log_action('ADMIN', admin_id, f"Cleared fraud flag {flag['flag_id']}")
                                st.rerun()
                        
                        with col2:
                            if st.button("⚠️ Confirm Fraud", key=f"confirm_{flag['flag_id']}"):
                                db.execute(
                                    """UPDATE fraud_flags 
                                       SET status = 'CONFIRMED', reviewed_by = ?, reviewed_at = datetime('now')
                                       WHERE flag_id = ?""",
                                    (admin_id, flag['flag_id'])
                                )
                                db.log_action('ADMIN', admin_id, f"Confirmed fraud flag {flag['flag_id']}", severity='WARNING')
                                st.rerun()
                        
                        with col3:
                            if st.button("🔍 View User", key=f"view_{flag['flag_id']}"):
                                st.session_state.view_user_id = flag['user_id']
                                st.session_state.page = 'admin_users'
                                st.rerun()
        else:
            st.success("No fraud alerts! 🎉")
    
    # Large Transactions Tab
    with tab2:
        st.subheader("Large Transactions")
        
        threshold = st.number_input("Threshold (₹)", min_value=10000, value=100000, step=10000)
        
        large_txns = analytics_service.get_large_transactions(threshold, limit=50)
        
        if large_txns:
            df_data = []
            for t in large_txns:
                df_data.append({
                    'Date': t['date'][:16],
                    'User': t['username'],
                    'Email': t['email'],
                    'Category': t['category'],
                    'Amount': f"₹{t['amount']:,.2f}",
                    'Description': t['description'][:30] if t['description'] else '-'
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Amount distribution
            amounts = [t['amount'] for t in large_txns]
            fig = px.histogram(
                x=amounts,
                nbins=20,
                labels={'x': 'Amount (₹)', 'y': 'Count'},
                title='Transaction Amount Distribution'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No transactions above ₹{threshold:,.0f}")
    
    # Overspending Tab
    with tab3:
        st.subheader("Users Exceeding Budgets")
        
        over_budget = analytics_service.get_users_over_budget()
        
        if over_budget:
            df_data = []
            for o in over_budget:
                df_data.append({
                    'User': o['username'],
                    'Email': o['email'],
                    'Category': o['category'],
                    'Budget': f"₹{o['limit']:,.0f}",
                    'Spent': f"₹{o['spent']:,.0f}",
                    'Overspent': f"₹{o['overspent']:,.0f}",
                    'Percentage': f"{(o['spent'] / o['limit'] * 100):.0f}%"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Visualization
            fig = px.bar(
                df,
                x='User',
                y=[float(o['overspent']) for o in over_budget],
                color='Category',
                title='Overspending by User'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No users over budget! 🎉")
    
    # Rules Tab
    with tab4:
        st.subheader("Fraud Detection Rules")
        
        rules = db.get_fraud_rules(active_only=False)
        
        if rules:
            for rule in rules:
                with st.expander(f"{'✅' if rule['is_active'] else '❌'} {rule['rule_name']}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** {rule['rule_type']}")
                        st.write(f"**Threshold:** {rule['threshold_value']} ({rule['threshold_type']})")
                        st.write(f"**Severity:** {rule['severity']}")
                    
                    with col2:
                        st.write(f"**Description:** {rule['description']}")
                        st.write(f"**Status:** {'Active' if rule['is_active'] else 'Inactive'}")
                    
                    # Toggle
                    if st.button(
                        "Disable" if rule['is_active'] else "Enable",
                        key=f"toggle_{rule['rule_id']}"
                    ):
                        db.execute(
                            "UPDATE fraud_rules SET is_active = ? WHERE rule_id = ?",
                            (0 if rule['is_active'] else 1, rule['rule_id'])
                        )
                        db.log_action('ADMIN', admin_id, f"Toggled fraud rule: {rule['rule_name']}")
                        st.rerun()
        
        st.markdown("---")
        st.subheader("➕ Add New Rule")
        
        with st.form("add_rule"):
            col1, col2 = st.columns(2)
            
            with col1:
                rule_name = st.text_input("Rule Name")
                rule_type = st.selectbox("Rule Type", ["AMOUNT", "FREQUENCY", "BUDGET", "TRANSFER"])
            
            with col2:
                threshold_value = st.number_input("Threshold Value", min_value=0.0, step=1.0)
                threshold_type = st.selectbox("Threshold Type", ["ABSOLUTE", "MULTIPLIER", "PERCENTAGE", "COUNT_PER_HOUR", "COUNT_PER_DAY"])
            
            severity = st.selectbox("Severity", ["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            description = st.text_area("Description")
            
            if st.form_submit_button("Add Rule"):
                if rule_name and threshold_value > 0:
                    db.execute_insert(
                        """INSERT INTO fraud_rules 
                           (rule_name, rule_type, threshold_value, threshold_type, severity, description)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (rule_name, rule_type, threshold_value, threshold_type, severity, description)
                    )
                    db.log_action('ADMIN', admin_id, f"Added fraud rule: {rule_name}")
                    st.success("Rule added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in required fields")
