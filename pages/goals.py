"""
Financial Goals Page
Goal creation and tracking
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

from database.db import db


def show_goals():
    """Display financial goals page"""
    user = st.session_state.user
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
                
                # Priority color
                priority_colors = {
                    'HIGH': '🔴',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }
                priority_icon = priority_colors.get(goal['priority'], '⚪')
                
                with st.expander(f"{priority_icon} {goal['goal_name']} ({progress:.0f}%)", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Progress bar
                        st.progress(min(progress / 100, 1.0))
                        st.caption(f"₹{current:,.0f} / ₹{target:,.0f} ({progress:.1f}%)")
                        
                        # Monthly contribution
                        if goal['monthly_contribution']:
                            monthly = db.to_rupees(goal['monthly_contribution'])
                            months_left = remaining / monthly if monthly > 0 else 0
                            st.info(f"Monthly: ₹{monthly:,.0f} | Est. {months_left:.0f} months to goal")
                        
                        # Target date
                        if goal['target_date']:
                            target_date = datetime.fromisoformat(goal['target_date'])
                            days_left = (target_date - datetime.now()).days
                            if days_left > 0:
                                st.write(f"📅 Target: {target_date.strftime('%B %d, %Y')} ({days_left} days left)")
                            else:
                                st.warning(f"📅 Target date passed! ({abs(days_left)} days ago)")
                    
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
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Actions
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        add_amount = st.number_input(
                            "Add Savings (₹)",
                            min_value=0.0,
                            step=100.0,
                            key=f"add_{goal['goal_id']}"
                        )
                    
                    with col2:
                        if st.button("💰 Add", key=f"btn_add_{goal['goal_id']}", use_container_width=True):
                            if add_amount > 0:
                                new_savings = goal['current_savings'] + db.to_paise(add_amount)
                                
                                # Check if goal is completed
                                if new_savings >= goal['target_amount']:
                                    db.execute(
                                        """UPDATE financial_goals 
                                           SET current_savings = ?, status = 'COMPLETED', completed_at = datetime('now')
                                           WHERE goal_id = ?""",
                                        (new_savings, goal['goal_id'])
                                    )
                                    st.success(f"🎉 Goal completed! You saved ₹{target:,.0f}!")
                                    st.balloons()
                                else:
                                    db.update_goal_savings(goal['goal_id'], new_savings, user_id)
                                    st.success(f"Added ₹{add_amount:,.0f} to {goal['goal_name']}")
                                
                                # Add contribution record
                                db.execute_insert(
                                    "INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)",
                                    (goal['goal_id'], db.to_paise(add_amount), "Manual addition")
                                )
                                
                                db.log_action('USER', user_id, f"Added ₹{add_amount} to goal: {goal['goal_name']}")
                                st.rerun()
                    
                    with col3:
                        if st.button("⏸️ Pause", key=f"pause_{goal['goal_id']}", use_container_width=True):
                            db.execute(
                                "UPDATE financial_goals SET status = 'PAUSED' WHERE goal_id = ? AND user_id = ?",
                                (goal['goal_id'], user_id)
                            )
                            st.rerun()
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
                if st.button(label, key=f"preset_{i}", use_container_width=True):
                    st.session_state.preset_goal = preset
        
        st.markdown("---")
        
        # Goal form
        with st.form("goal_form"):
            col1, col2 = st.columns(2)
            
            preset = st.session_state.get('preset_goal', {})
            
            with col1:
                goal_name = st.text_input("Goal Name", value=preset.get('name', ''), placeholder="e.g., Dream Vacation")
                target_amount = st.number_input(
                    "Target Amount (₹)",
                    min_value=1000.0,
                    value=float(preset.get('target', 50000)),
                    step=5000.0
                )
            
            with col2:
                priority = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"], index=1)
                months_to_achieve = st.number_input(
                    "Months to Achieve",
                    min_value=1,
                    max_value=120,
                    value=preset.get('months', 12)
                )
            
            # Calculate monthly contribution
            monthly_contribution = target_amount / months_to_achieve if months_to_achieve > 0 else 0
            st.info(f"💰 Monthly savings needed: ₹{monthly_contribution:,.0f}")
            
            # Target date
            target_date = (datetime.now() + timedelta(days=months_to_achieve * 30)).strftime('%Y-%m-%d')
            st.write(f"📅 Estimated completion: {target_date}")
            
            submit = st.form_submit_button("Create Goal", use_container_width=True)
            
            if submit:
                if goal_name and target_amount >= 1000:
                    goal_id = db.create_goal(
                        user_id=user_id,
                        goal_name=goal_name,
                        target_amount=db.to_paise(target_amount),
                        monthly_contribution=db.to_paise(monthly_contribution),
                        target_date=target_date,
                        priority=priority
                    )
                    
                    if goal_id:
                        st.success(f"✅ Goal '{goal_name}' created successfully!")
                        db.log_action('USER', user_id, f"Created goal: {goal_name}", 'financial_goals', goal_id)
                        
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
                        db.execute(
                            "UPDATE financial_goals SET status = 'ACTIVE', current_savings = 0, completed_at = NULL WHERE goal_id = ?",
                            (goal['goal_id'],)
                        )
                        st.rerun()
                
                st.markdown("---")
            
            # Stats
            total_achieved = sum(db.to_rupees(g['target_amount']) for g in completed_goals)
            st.success(f"🎉 Total saved across completed goals: ₹{total_achieved:,.0f}")
        else:
            st.info("No completed goals yet. Keep saving!")
    
    # Goal Progress Over Time (if any active goals)
    if active_goals:
        st.markdown("---")
        st.subheader("📈 Contribution History")
        
        selected_goal = st.selectbox(
            "Select Goal",
            options=[(g['goal_id'], g['goal_name']) for g in active_goals],
            format_func=lambda x: x[1]
        )
        
        if selected_goal:
            contributions = db.execute(
                """SELECT amount, source, created_at 
                   FROM goal_contributions 
                   WHERE goal_id = ? 
                   ORDER BY created_at""",
                (selected_goal[0],),
                fetch=True
            )
            
            if contributions:
                df_data = []
                cumulative = 0
                for c in contributions:
                    cumulative += db.to_rupees(c['amount'])
                    df_data.append({
                        'Date': c['created_at'][:10],
                        'Amount': db.to_rupees(c['amount']),
                        'Cumulative': cumulative,
                        'Source': c.get('source', '-')
                    })
                
                df = pd.DataFrame(df_data)
                
                import plotly.express as px
                fig = px.line(
                    df, x='Date', y='Cumulative',
                    markers=True,
                    title='Savings Progress'
                )
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True)
                
                # Table
                st.dataframe(df[['Date', 'Amount', 'Source']], use_container_width=True, hide_index=True)
            else:
                st.info("No contributions recorded yet.")
