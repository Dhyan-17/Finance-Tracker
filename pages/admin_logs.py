"""
Admin Logs Page
System audit logs and activity monitoring
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

from database.db import db


def show_admin_logs():
    """Display admin logs page"""
    admin = st.session_state.admin
    
    st.title("📜 System Logs")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        actor_type = st.selectbox("Actor Type", ["All", "USER", "ADMIN", "SYSTEM"])
    
    with col2:
        severity = st.selectbox("Severity", ["All", "INFO", "WARNING", "ERROR", "CRITICAL"])
    
    with col3:
        days = st.selectbox("Time Range", [1, 7, 30, 90], index=1, format_func=lambda x: f"Last {x} days")
    
    with col4:
        limit = st.selectbox("Show", [50, 100, 200, 500])
    
    # Build query
    conditions = []
    params = []
    
    if actor_type != "All":
        conditions.append("actor_type = ?")
        params.append(actor_type)
    
    if severity != "All":
        conditions.append("severity = ?")
        params.append(severity)
    
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    conditions.append("created_at >= ?")
    params.append(start_date)
    
    params.append(limit)
    
    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    
    logs = db.execute(
        f"""SELECT * FROM audit_logs 
            {where_clause}
            ORDER BY created_at DESC LIMIT ?""",
        tuple(params),
        fetch=True
    )
    
    st.markdown("---")
    
    # Summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Logs", len(logs))
    with col2:
        warnings = sum(1 for l in logs if l['severity'] == 'WARNING')
        st.metric("Warnings", warnings)
    with col3:
        errors = sum(1 for l in logs if l['severity'] == 'ERROR')
        st.metric("Errors", errors)
    with col4:
        critical = sum(1 for l in logs if l['severity'] == 'CRITICAL')
        st.metric("Critical", critical)
    
    st.markdown("---")
    
    # Visualization
    if logs:
        col1, col2 = st.columns(2)
        
        with col1:
            # By severity
            severity_data = {}
            for log in logs:
                sev = log['severity']
                severity_data[sev] = severity_data.get(sev, 0) + 1
            
            fig = px.pie(
                names=list(severity_data.keys()),
                values=list(severity_data.values()),
                title='Logs by Severity',
                color=list(severity_data.keys()),
                color_discrete_map={
                    'INFO': '#3498db',
                    'WARNING': '#f39c12',
                    'ERROR': '#e74c3c',
                    'CRITICAL': '#8e44ad'
                }
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # By actor type
            actor_data = {}
            for log in logs:
                actor = log['actor_type']
                actor_data[actor] = actor_data.get(actor, 0) + 1
            
            fig = px.bar(
                x=list(actor_data.keys()),
                y=list(actor_data.values()),
                title='Logs by Actor Type',
                labels={'x': 'Actor Type', 'y': 'Count'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Logs Table
    st.subheader("📋 Log Entries")
    
    # Search
    search = st.text_input("🔍 Search logs", placeholder="Search by action...")
    
    filtered_logs = logs
    if search:
        search_lower = search.lower()
        filtered_logs = [l for l in logs if search_lower in l['action'].lower()]
    
    if filtered_logs:
        for log in filtered_logs:
            severity_icons = {
                'INFO': '📝',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }
            icon = severity_icons.get(log['severity'], '📝')
            
            severity_colors = {
                'INFO': '#3498db',
                'WARNING': '#f39c12',
                'ERROR': '#e74c3c',
                'CRITICAL': '#8e44ad'
            }
            color = severity_colors.get(log['severity'], '#666')
            
            st.markdown(
                f"""
                <div style='padding: 10px; margin: 5px 0; border-left: 4px solid {color}; background: #f8f9fa;'>
                    <strong>{icon} {log['created_at'][:19]}</strong> | 
                    <span style='color: {color}'>{log['severity']}</span> | 
                    {log['actor_type']}:{log['actor_id']}
                    <br/>
                    <span style='color: #333;'>{log['action']}</span>
                    {f"<br/><small>Entity: {log['entity_type']}:{log['entity_id']}</small>" if log['entity_type'] else ""}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Export
        st.markdown("---")
        if st.button("📥 Export Logs"):
            df_data = []
            for log in filtered_logs:
                df_data.append({
                    'Timestamp': log['created_at'],
                    'Severity': log['severity'],
                    'Actor Type': log['actor_type'],
                    'Actor ID': log['actor_id'],
                    'Action': log['action'],
                    'Entity Type': log.get('entity_type', ''),
                    'Entity ID': log.get('entity_id', '')
                })
            
            df = pd.DataFrame(df_data)
            csv = df.to_csv(index=False)
            
            st.download_button(
                "Download CSV",
                csv,
                f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    else:
        st.info("No logs found matching your criteria.")
    
    # Login Attempts
    st.markdown("---")
    st.subheader("🔐 Recent Login Attempts")
    
    login_attempts = db.execute(
        """SELECT * FROM login_attempts 
           ORDER BY attempt_time DESC LIMIT 50""",
        fetch=True
    )
    
    if login_attempts:
        df_data = []
        for attempt in login_attempts:
            df_data.append({
                'Time': attempt['attempt_time'][:19],
                'Email': attempt['email'],
                'Status': '✅ Success' if attempt['success'] else '❌ Failed',
                'IP': attempt.get('ip_address', 'N/A'),
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Stats
        total = len(login_attempts)
        failed = sum(1 for a in login_attempts if not a['success'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Attempts", total)
        with col2:
            st.metric("Failed", failed)
        with col3:
            st.metric("Failure Rate", f"{(failed/total*100):.1f}%" if total > 0 else "0%")
    else:
        st.info("No login attempts recorded.")
    
    # Fraud Alerts Summary
    st.markdown("---")
    st.subheader("🚨 Recent Fraud Alerts")
    
    fraud_alerts = db.execute(
        """SELECT ff.*, u.username 
           FROM fraud_flags ff
           JOIN users u ON ff.user_id = u.user_id
           ORDER BY ff.created_at DESC LIMIT 10""",
        fetch=True
    )
    
    if fraud_alerts:
        for alert in fraud_alerts:
            severity_colors = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }
            icon = severity_colors.get(alert['severity'], '⚪')
            
            st.write(
                f"{icon} {alert['created_at'][:16]} | **{alert['username']}** | "
                f"{alert['rule_name']} | {alert['status']}"
            )
    else:
        st.success("No recent fraud alerts")
