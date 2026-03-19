"""
Financial Goals Page
Goal creation and tracking
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

from database.db import db


def show_goals():
    """Display financial goals page"""
    user = db.get_user_by_id(st.session_state.user['user_id'])
    st.session_state.user = user
    user_id = user['user_id']
    
    st.title("🎯 Financial Goals")
    
    # Get goals
    active_goals = db.get_user_goals(user_id, status='ACTIVE')
    completed_goals = db.get_user_goals(user_id, status='COMPLETED')
    
    # Summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Goals", len(active_goals))
    with col2:
        st.metric("Completed Goals", len(completed_goals))
    with col3:
        total_target = sum(db.to_rupees(g['target_amount']) for g in active_goals)
        total_saved = sum(db.to_rupees(g['current_savings']) for g in active_goals)
        st.metric("Total Saved", f"₹{total_saved:,.0f}", delta=f"of ₹{total_target:,.0f}")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Active Goals", "➕ Create Goal", "✅ Completed"])
    
    # Active Goals Tab
    with tab1:
        if active_goals:
            for goal in active_goals:
                target = db.to_rupees(goal['target_amount'])
                current = db.to_rupees(goal['current_savings'])
                progress = (current / target * 100) if target > 0 else 0
                remaining = target - current
                
                with st.expander(f"🎯 {goal['goal_name']} ({progress:.0f}%)", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Progress bar
                        st.progress(min(progress / 100, 1.0))
                        st.caption(f"₹{current:,.0f} / ₹{target:,.0f}")
                        
                        # Show remaining amount
                        if remaining > 0:
                            st.warning(f"💰 Remaining: ₹{remaining:,.0f}")
                        else:
                            st.success("🎉 Goal completed!")
                        
                        # Monthly contribution - dynamically recalculated
                        if goal['monthly_contribution'] and goal.get('target_date'):
                            # Calculate months remaining to target date
                            try:
                                target_dt = datetime.strptime(goal['target_date'], '%Y-%m-%d')
                                now = datetime.now()
                                months_remaining = max(1, (target_dt.year - now.year) * 12 + (target_dt.month - now.month))
                                # Recalculate monthly contribution based on remaining amount and remaining months
                                recalculated_monthly = remaining / months_remaining if months_remaining > 0 else remaining
                                st.info(f"Monthly: ₹{recalculated_monthly:,.0f} | {months_remaining} months left")
                                
                                # Update stored monthly contribution if it changed significantly
                                new_monthly_paise = db.to_paise(recalculated_monthly)
                                if abs(new_monthly_paise - goal['monthly_contribution']) > 100:  # > ₹1 difference
                                    db.execute(
                                        "UPDATE financial_goals SET monthly_contribution = ? WHERE goal_id = ?",
                                        (new_monthly_paise, goal['goal_id'])
                                    )
                            except (ValueError, TypeError):
                                monthly = db.to_rupees(goal['monthly_contribution'])
                                months_left = remaining / monthly if monthly > 0 else 0
                                st.info(f"Monthly: ₹{monthly:,.0f} | {months_left:.0f} months left")
                        elif goal['monthly_contribution']:
                            monthly = db.to_rupees(goal['monthly_contribution'])
                            months_left = remaining / monthly if monthly > 0 else 0
                            st.info(f"Monthly: ₹{monthly:,.0f} | {months_left:.0f} months left")
                    
                    with col2:
                        # Gauge
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=progress,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "#2ecc71"},
                                'steps': [
                                    {'range': [0, 50], 'color': "#fff3cd"},
                                    {'range': [50, 80], 'color': "#d4edda"},
                                    {'range': [80, 100], 'color': "#c3e6cb"}
                                ]
                            },
                            number={'suffix': '%'}
                        ))
                        fig.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig, width='stretch', key=f"gauge_{goal['goal_id']}")
                    
                    # Actions
                    st.markdown("---")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        add_amount = st.number_input(
                            "Add Savings (₹)",
                            min_value=0.0,
                            max_value=float(remaining) if remaining > 0 else 0.0,
                            step=100.0,
                            key=f"add_{goal['goal_id']}"
                        )
                    
                    with col2:
                        if remaining > 0:
                            if st.button(f"🎯 Fill All (₹{remaining:,.0f})", key=f"btn_fill_{goal['goal_id']}", width='stretch'):
                                add_amount = remaining
                                amount_paise = db.to_paise(add_amount)
                                
                                # Check balance first
                                if user['wallet_balance'] < amount_paise:
                                    st.error(f"❌ Insufficient wallet balance!")
                                    st.stop()
                                
                                # FIRST: Add to goal (safer order)
                                new_savings = goal['current_savings'] + amount_paise
                                
                                if new_savings >= goal['target_amount']:
                                    db.execute("UPDATE financial_goals SET current_savings = ?, status = 'COMPLETED', completed_at = datetime('now') WHERE goal_id = ?", (new_savings, goal['goal_id']))
                                    st.success(f"🎉 Goal completed!")
                                    st.balloons()
                                else:
                                    db.update_goal_savings(goal['goal_id'], new_savings, user_id)
                                    st.success(f"Added ₹{add_amount:,.0f}")
                                
                                # THEN: Deduct from wallet
                                new_wallet = user['wallet_balance'] - amount_paise
                                db.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (new_wallet, user_id))
                                
                                # Record contribution
                                db.execute_insert(
                                    "INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)",
                                    (goal['goal_id'], amount_paise, "WALLET")
                                )
                                
                                # Refresh
                                updated_user = db.get_user_by_id(user_id)
                                st.session_state.user['wallet_balance'] = updated_user['wallet_balance']
                                st.rerun()
                        
                        if st.button("💰 Add", key=f"btn_add_{goal['goal_id']}", width='stretch'):
                            if add_amount > 0 and add_amount <= remaining:
                                amount_paise = db.to_paise(add_amount)
                                
                                # Check balance first
                                if user['wallet_balance'] < amount_paise:
                                    st.error(f"❌ Insufficient wallet balance!")
                                    st.stop()
                                
                                # FIRST: Add to goal (safer order)
                                new_savings = goal['current_savings'] + amount_paise
                                
                                if new_savings >= goal['target_amount']:
                                    db.execute("UPDATE financial_goals SET current_savings = ?, status = 'COMPLETED', completed_at = datetime('now') WHERE goal_id = ?", (new_savings, goal['goal_id']))
                                    st.success(f"🎉 Goal completed!")
                                    st.balloons()
                                else:
                                    db.update_goal_savings(goal['goal_id'], new_savings, user_id)
                                    st.success(f"Added ₹{add_amount:,.0f}")
                                
                                # THEN: Deduct from wallet
                                new_wallet = user['wallet_balance'] - amount_paise
                                db.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (new_wallet, user_id))
                                
                                # Record contribution
                                db.execute_insert(
                                    "INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)",
                                    (goal['goal_id'], amount_paise, "WALLET")
                                )
                                
                                # Refresh
                                updated_user = db.get_user_by_id(user_id)
                                st.session_state.user['wallet_balance'] = updated_user['wallet_balance']
                                st.rerun()
                            else:
                                st.error(f"❌ Please enter between ₹1 and ₹{remaining:,.0f}")
                    
                    with col3:
                        if st.button("⏸️ Pause & Refund", key=f"pause_{goal['goal_id']}", width='stretch'):
                            # Get current savings
                            current_savings = goal['current_savings']
                            
                            if current_savings > 0:
                                # Refund to wallet by default
                                new_wallet = user['wallet_balance'] + current_savings
                                db.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (new_wallet, user_id))
                            
                            # Pause the goal (set saved amount to 0)
                            db.execute("UPDATE financial_goals SET status = 'PAUSED', current_savings = 0 WHERE goal_id = ? AND user_id = ?", (goal['goal_id'], user_id))
                            
                            st.success("✅ Goal paused and money refunded to wallet!")
                            st.rerun()
                    
                    # Transaction History
                    st.markdown("---")
                    st.subheader("📜 Transaction History")
                    
                    contributions = db.execute(
                        "SELECT amount, source, created_at FROM goal_contributions WHERE goal_id = ? ORDER BY created_at DESC LIMIT 10",
                        (goal['goal_id'],),
                        fetch=True
                    )
                    
                    if contributions:
                        for c in contributions:
                            amount = db.to_rupees(c['amount'])
                            source = c.get('source', '-')
                            date = c.get('created_at', '')[:16] if c.get('created_at') else 'N/A'
                            source_icon = "💳" if source == "WALLET" else "🏦"
                            st.write(f"{source_icon} +₹{amount:,.0f} on {date}")
                    else:
                        st.info("No transactions yet")
        else:
            st.info("No active goals. Create a goal to start saving!")
    
    # Create Goal Tab
    with tab2:
        st.subheader("Create New Goal")
        
        # Preset goals
        st.markdown("**Quick Templates:**")
        presets = {
            "🏠 Emergency Fund": {"name": "Emergency Fund", "target": 100000, "months": 12},
            "✈️ Vacation": {"name": "Dream Vacation", "target": 50000, "months": 6},
            "🎓 Education": {"name": "Education Fund", "target": 200000, "months": 24},
            "🚗 Car": {"name": "New Car", "target": 500000, "months": 36},
            "🏡 House Down Payment": {"name": "House Down Payment", "target": 1000000, "months": 60},
            "💻 Gadgets": {"name": "Gadget Upgrade", "target": 80000, "months": 8}
        }
        
        preset_cols = st.columns(3)
        for i, (label, preset) in enumerate(presets.items()):
            with preset_cols[i % 3]:
                if st.button(label, key=f"preset_{i}", width='stretch'):
                    st.session_state.preset_goal = preset
                    st.rerun()
        
        st.markdown("---")
        
        # Goal form
        with st.form("goal_form"):
            col1, col2 = st.columns(2)
            
            preset = st.session_state.get('preset_goal', {})
            
            with col1:
                goal_name = st.text_input("Goal Name", value=preset.get('name', ''), placeholder="e.g., Dream Vacation")
                target_amount = st.number_input("Target Amount (₹)", min_value=1000.0, value=float(preset.get('target', 50000)), step=5000.0)
            
            with col2:
                months_to_achieve = st.number_input("Months to Achieve", min_value=1, max_value=120, value=preset.get('months', 12))
            
            monthly_contribution = target_amount / months_to_achieve if months_to_achieve > 0 else 0
            st.info(f"💰 Monthly savings needed: ₹{monthly_contribution:,.0f}")
            
            target_date = (datetime.now() + timedelta(days=months_to_achieve * 30)).strftime('%Y-%m-%d')
            st.write(f"📅 Estimated completion: {target_date}")
            
            submit = st.form_submit_button("Create Goal", width='stretch')
            
            if submit:
                if goal_name and target_amount >= 1000:
                    goal_id = db.create_goal(user_id=user_id, goal_name=goal_name, target_amount=db.to_paise(target_amount), monthly_contribution=db.to_paise(monthly_contribution), target_date=target_date)
                    if goal_id:
                        st.success(f"✅ Goal '{goal_name}' created successfully!")
                        if 'preset_goal' in st.session_state:
                            del st.session_state.preset_goal
                        st.rerun()
                    else:
                        st.error("Failed to create goal")
                else:
                    st.error("Please enter a goal name and target amount (min ₹1,000)")
    
    # Completed Goals Tab
    with tab3:
        if completed_goals:
            st.subheader("🏆 Completed Goals")
            
            for goal in completed_goals:
                target = db.to_rupees(goal['target_amount'])
                completed_date = goal.get('completed_at', '')[:10] if goal.get('completed_at') else 'Unknown'
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**✅ {goal['goal_name']}**")
                    st.caption(f"Completed on {completed_date}")
                
                with col2:
                    st.metric("Saved", f"₹{target:,.0f}")
                
                with col3:
                    if st.button("🔄 Restart", key=f"restart_{goal['goal_id']}"):
                        db.execute("UPDATE financial_goals SET status = 'ACTIVE', current_savings = 0, completed_at = NULL WHERE goal_id = ?", (goal['goal_id'],))
                        st.rerun()
            
            st.markdown("---")
            total_achieved = sum(db.to_rupees(g['target_amount']) for g in completed_goals)
            st.success(f"🎉 Total saved across completed goals: ₹{total_achieved:,.0f}")
        else:
            st.info("No completed goals yet. Keep saving!")
