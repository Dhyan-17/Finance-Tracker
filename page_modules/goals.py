"""
Financial Goals Page
Goal creation and tracking
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

from database.db import db


def metric_card(title, value, subtitle="", color="#5B8DEF", bg="#EEF4FF", icon="💰"):
    st.markdown(
        f"""
    <div style="background:{bg}; border-radius:16px; padding:1.5rem; border-left:4px solid {color}; margin-bottom:0.5rem;">
        <div style="font-size:1.5rem;">{icon}</div>
        <div style="color:#6B7280; font-size:0.85rem; font-weight:500; margin:0.4rem 0;">{title}</div>
        <div style="color:#1A1A2E; font-size:1.6rem; font-weight:700;">{value}</div>
        <div style="color:{color}; font-size:0.8rem;">{subtitle}</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def goal_card(name, icon, current, target, progress, remaining, target_date=""):
    if progress >= 100:
        color = "#43A87B"
        bg = "#EEFAF4"
        status = "✅ Completed"
    elif progress >= 80:
        color = "#43A87B"
        bg = "#EEFAF4"
        status = "Almost there!"
    elif progress >= 50:
        color = "#5B8DEF"
        bg = "#EEF4FF"
        status = "On track"
    else:
        color = "#F5A623"
        bg = "#FFF8E8"
        status = "Getting started"

    st.markdown(
        f"""
    <div style="background:#FFFFFF; border-radius:16px; padding:1.5rem; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0; margin-bottom:1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
            <div style="display:flex; align-items:center; gap:10px;">
                <div style="font-size:1.5rem;">{icon}</div>
                <div>
                    <div style="font-weight:600; color:#1A1A2E; font-size:1.1rem;">{name}</div>
                    <div style="color:{color}; font-size:0.8rem;">{status}</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-weight:700; font-size:1.3rem; color:#1A1A2E;">{progress:.0f}%</div>
            </div>
        </div>
        <div style="background:#F0F0F0; border-radius:10px; height:12px; overflow:hidden;">
            <div style="background:{color}; width:{min(progress, 100)}%; border-radius:10px; height:12px; transition:width 0.3s;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:0.8rem; font-size:0.85rem;">
            <div style="color:#6B7280;">Saved: <span style="color:#1A1A2E; font-weight:600;">₹{current:,.0f}</span></div>
            <div style="color:#6B7280;">Target: <span style="color:#1A1A2E; font-weight:600;">₹{target:,.0f}</span></div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_goals():
    """Display financial goals page"""
    user = db.get_user_by_id(st.session_state.user["user_id"])
    st.session_state.user = user
    user_id = user["user_id"]

    st.markdown(
        """
    <div style="padding: 1rem 0 2rem 0;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">🎯 Financial Goals</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Track your savings milestones</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Get goals
    active_goals = db.get_user_goals(user_id, status="ACTIVE")
    completed_goals = db.get_user_goals(user_id, status="COMPLETED")

    # Summary
    col1, col2, col3 = st.columns(3)

    with col1:
        metric_card(
            title="Active Goals",
            value=str(len(active_goals)),
            subtitle="In progress",
            color="#5B8DEF",
            bg="#EEF4FF",
            icon="🎯",
        )
    with col2:
        metric_card(
            title="Completed",
            value=str(len(completed_goals)),
            subtitle="Achieved",
            color="#43A87B",
            bg="#EEFAF4",
            icon="✅",
        )
    with col3:
        total_target = sum(db.to_rupees(g["target_amount"]) for g in active_goals)
        total_saved = sum(db.to_rupees(g["current_savings"]) for g in active_goals)
        metric_card(
            title="Total Saved",
            value=f"₹{total_saved:,.0f}",
            subtitle=f"of ₹{total_target:,.0f}",
            color="#AB8EE8",
            bg="#F5F0FF",
            icon="💰",
        )

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Active Goals", "➕ Create Goal", "✅ Completed"])

    # Active Goals Tab
    with tab1:
        if active_goals:
            for goal in active_goals:
                target = db.to_rupees(goal["target_amount"])
                current = db.to_rupees(goal["current_savings"])
                progress = (current / target * 100) if target > 0 else 0
                remaining = target - current

                icon_map = {
                    "Emergency": "🏠",
                    "Vacation": "✈️",
                    "Education": "🎓",
                    "Car": "🚗",
                    "House": "🏡",
                    "Gadget": "💻",
                    "Wedding": "💒",
                    "Bike": "🏍️",
                    "Phone": "📱",
                    "Laptop": "💻",
                    "TV": "📺",
                    "Watch": "⌚",
                }
                icon = "🎯"
                for key, val in icon_map.items():
                    if key.lower() in goal["goal_name"].lower():
                        icon = val
                        break

                goal_card(
                    name=goal["goal_name"],
                    icon=icon,
                    current=current,
                    target=target,
                    progress=progress,
                    remaining=remaining,
                    target_date=goal.get("target_date", ""),
                )

                # Actions
                col1, col2 = st.columns([2, 1])

                with col1:
                    add_amount = st.number_input(
                        "Add Savings (₹)",
                        min_value=0.0,
                        max_value=float(remaining) if remaining > 0 else 0.0,
                        step=100.0,
                        key=f"add_{goal['goal_id']}",
                    )

                with col2:
                    if remaining > 0:
                        if st.button(
                            f"💰 Add ₹{add_amount:,.0f}",
                            key=f"btn_add_{goal['goal_id']}",
                            use_container_width=True,
                        ):
                            if add_amount > 0 and add_amount <= remaining:
                                amount_paise = db.to_paise(add_amount)

                                if user["wallet_balance"] < amount_paise:
                                    st.error("Insufficient wallet balance!")
                                    st.stop()

                                new_savings = goal["current_savings"] + amount_paise

                                if new_savings >= goal["target_amount"]:
                                    db.execute(
                                        "UPDATE financial_goals SET current_savings = ?, status = 'COMPLETED', completed_at = datetime('now') WHERE goal_id = ?",
                                        (new_savings, goal["goal_id"]),
                                    )
                                    st.success("Goal completed!")
                                    st.balloons()
                                else:
                                    db.update_goal_savings(
                                        goal["goal_id"], new_savings, user_id
                                    )
                                    st.success(f"Added ₹{add_amount:,.0f}")

                                new_wallet = user["wallet_balance"] - amount_paise
                                db.execute(
                                    "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
                                    (new_wallet, user_id),
                                )

                                db.execute_insert(
                                    "INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)",
                                    (goal["goal_id"], amount_paise, "WALLET"),
                                )

                                updated_user = db.get_user_by_id(user_id)
                                st.session_state.user["wallet_balance"] = updated_user[
                                    "wallet_balance"
                                ]
                                st.rerun()
                            else:
                                st.error(
                                    f"Please enter between ₹1 and ₹{remaining:,.0f}"
                                )

                # Contribution history
                with st.expander("📜 View Contributions"):
                    contributions = db.execute(
                        "SELECT amount, source, created_at FROM goal_contributions WHERE goal_id = ? ORDER BY created_at DESC LIMIT 10",
                        (goal["goal_id"],),
                        fetch=True,
                    )

                    if contributions:
                        for c in contributions:
                            amount = db.to_rupees(c["amount"])
                            source = c.get("source", "-")
                            date = (
                                c.get("created_at", "")[:16]
                                if c.get("created_at")
                                else "N/A"
                            )
                            source_icon = "💳" if source == "WALLET" else "🏦"
                            st.write(f"{source_icon} +₹{amount:,.0f} on {date}")
                    else:
                        st.info("No transactions yet")
        else:
            st.markdown(
                """
            <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
                <div style="font-size:2rem;">🎯</div>
                <p style="color:#6B7280; margin-top:0.5rem;">No active goals</p>
                <p style="color:#6B7280; font-size:0.9rem;">Create a goal to start saving!</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Create Goal Tab
    with tab2:
        

        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Create New Goal</h3>',
            unsafe_allow_html=True,
        )

        # Preset goals
        st.markdown("**Quick Templates:**")
        presets = {
            "🏠 Emergency Fund": {
                "name": "Emergency Fund",
                "target": 100000,
                "months": 12,
            },
            "✈️ Vacation": {"name": "Dream Vacation", "target": 50000, "months": 6},
            "🎓 Education": {"name": "Education Fund", "target": 200000, "months": 24},
            "🚗 Car": {"name": "New Car", "target": 500000, "months": 36},
            "🏡 House": {"name": "House Down Payment", "target": 1000000, "months": 60},
            "💻 Gadgets": {"name": "Gadget Upgrade", "target": 80000, "months": 8},
        }

        preset_cols = st.columns(3)
        for i, (label, preset) in enumerate(presets.items()):
            with preset_cols[i % 3]:
                if st.button(label, key=f"preset_{i}", width="stretch"):
                    st.session_state.preset_goal = preset
                    st.rerun()

        st.markdown("---")

        with st.form("goal_form"):
            col1, col2 = st.columns(2)

            preset = st.session_state.get("preset_goal", {})

            with col1:
                goal_name = st.text_input(
                    "Goal Name",
                    value=preset.get("name", ""),
                    placeholder="e.g., Dream Vacation",
                )
                target_amount = st.number_input(
                    "Target Amount (₹)",
                    min_value=1000.0,
                    value=float(preset.get("target", 50000)),
                    step=5000.0,
                )

            with col2:
                months_to_achieve = st.number_input(
                    "Months to Achieve",
                    min_value=1,
                    max_value=120,
                    value=preset.get("months", 12),
                )

            monthly_contribution = (
                target_amount / months_to_achieve if months_to_achieve > 0 else 0
            )
            st.info(f"Monthly savings needed: ₹{monthly_contribution:,.0f}")

            target_date = (
                datetime.now() + timedelta(days=months_to_achieve * 30)
            ).strftime("%Y-%m-%d")
            st.write(f"Target date: {target_date}")

            submit = st.form_submit_button("Create Goal", use_container_width=True)

            if submit:
                if goal_name and target_amount >= 1000:
                    goal_id = db.create_goal(
                        user_id=user_id,
                        goal_name=goal_name,
                        target_amount=db.to_paise(target_amount),
                        monthly_contribution=db.to_paise(monthly_contribution),
                        target_date=target_date,
                    )
                    if goal_id:
                        st.success(f"Goal '{goal_name}' created!")
                        if "preset_goal" in st.session_state:
                            del st.session_state.preset_goal
                        st.rerun()
                    else:
                        st.error("Failed to create goal")
                else:
                    st.error("Please enter goal name and target (min ₹1,000)")

    # Completed Goals Tab
    with tab3:
        if completed_goals:
            st.markdown(
                '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">🏆 Completed Goals</h3>',
                unsafe_allow_html=True,
            )

            for goal in completed_goals:
                target = db.to_rupees(goal["target_amount"])
                completed_date = (
                    goal.get("completed_at", "")[:10]
                    if goal.get("completed_at")
                    else "Unknown"
                )

                st.markdown(
                    f"""
                <div style="background:#EEFAF4; border-radius:16px; padding:1.5rem; border-left:4px solid #43A87B; margin-bottom:1rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div style="font-weight:600; color:#1A1A2E; font-size:1.1rem;">✅ {goal["goal_name"]}</div>
                            <div style="color:#6B7280; font-size:0.85rem;">Completed on {completed_date}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-weight:700; color:#43A87B; font-size:1.2rem;">₹{target:,.0f}</div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button(f"🔄 Restart", key=f"restart_{goal['goal_id']}"):
                    db.execute(
                        "UPDATE financial_goals SET status = 'ACTIVE', current_savings = 0, completed_at = NULL WHERE goal_id = ?",
                        (goal["goal_id"],),
                    )
                    st.rerun()

            st.markdown("---")
            total_achieved = sum(
                db.to_rupees(g["target_amount"]) for g in completed_goals
            )
            st.markdown(
                f"""
            <div style="background:#43A87B; color:white; border-radius:16px; padding:1.5rem; text-align:center;">
                <div style="font-size:1.2rem;">Total saved: ₹{total_achieved:,.0f}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
            <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
                <div style="font-size:2rem;">🎯</div>
                <p style="color:#6B7280; margin-top:0.5rem;">No completed goals yet</p>
                <p style="color:#6B7280; font-size:0.9rem;">Keep saving!</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
