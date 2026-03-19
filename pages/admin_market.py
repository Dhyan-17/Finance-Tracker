"""
Admin Market Page
Market asset management and price updates
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from database.db import db
from services.investment_service import investment_service


def show_admin_market():
    """Display admin market management page"""
    if 'admin' not in st.session_state or not st.session_state.admin:
        st.error("Please login as admin")
        return
    
    admin = st.session_state.admin
    admin_id = admin['admin_id']
    
    st.title("📈 Market Management")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🔄 Update Prices", "➕ Add Asset", "📜 History"])
    
    # Overview Tab
    with tab1:
        st.subheader("Market Overview")
        
        # Get all assets
        assets = db.get_market_assets()
        
        # Calculate stats
        total_assets = len(assets) if assets else 0
        gainers = len([a for a in assets if (a.get('day_change_percent') or 0) > 0])
        losers = len([a for a in assets if (a.get('day_change_percent') or 0) < 0])
        unchanged = total_assets - gainers - losers
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Assets", total_assets)
        with col2:
            st.metric("Gainers 🟢", gainers)
        with col3:
            st.metric("Losers 🔴", losers)
        with col4:
            st.metric("Unchanged ⚪", unchanged)
        
        st.markdown("---")
        
        # All Assets Table with Gain/Loss Status
        st.subheader("📊 All Assets")
        
        if assets:
            df_data = []
            for a in assets:
                change = a.get('day_change_percent') or 0
                
                # Determine status icon
                if change > 0:
                    status = "🟢"
                elif change < 0:
                    status = "🔴"
                else:
                    status = "⚪"
                
                df_data.append({
                    'Status': status,
                    'Symbol': a['asset_symbol'],
                    'Name': a['asset_name'],
                    'Type': a['asset_type'],
                    'Price': f"₹{db.to_rupees(a['current_price']):,.2f}",
                    'Change': f"{change:+.2f}%",
                    'Volatility': f"{a['volatility_percent']:.1f}%"
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.caption(f"Showing all {total_assets} assets")
    
    # Update Prices Tab
    with tab2:
        st.subheader("Update Market Prices")
        
        st.warning("⚠️ This will update ALL asset prices and affect all user portfolios!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Simulate Market Update", use_container_width=True):
                with st.spinner("Updating prices..."):
                    updated = investment_service.update_market_prices()
                
                if updated:
                    st.success(f"✅ Updated {len(updated)} assets!")
                    
                    # Show changes
                    df_data = []
                    for u in updated:
                        df_data.append({
                            'Asset': u['symbol'],
                            'Old Price': f"₹{u['old_price']:,.2f}",
                            'New Price': f"₹{u['new_price']:,.2f}"
                        })
                    
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    db.log_action('ADMIN', admin_id, f"Updated market prices for {len(updated)} assets")
                else:
                    st.info("No price changes")
        
        with col2:
            st.markdown("""
            **How it works:**
            - Prices are simulated based on volatility
            - Higher volatility = larger price swings
            - Crypto has highest volatility (~10%)
            - Stocks moderate (~3%)
            - Mutual Funds lowest (~2%)
            """)
        
        st.markdown("---")
        
        # Manual Price Update
        st.subheader("Manual Price Update")
        
        assets = db.get_market_assets()
        
        if assets:
            asset_options = {f"{a['asset_symbol']} - {a['asset_name']}": a for a in assets}
            selected = st.selectbox("Select Asset", list(asset_options.keys()))
            asset = asset_options[selected]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Current Price:** ₹{db.to_rupees(asset['current_price']):,.2f}")
                st.write(f"**Day Change:** {asset['day_change_percent'] or 0:+.2f}%")
                st.write(f"**Volatility:** {asset['volatility_percent']}%")
            
            with col2:
                new_price = st.number_input(
                    "New Price (₹)",
                    min_value=0.01,
                    value=db.to_rupees(asset['current_price']),
                    step=10.0
                )
                
                if st.button("Update Price"):
                    old_price = asset['current_price']
                    new_price_paise = db.to_paise(new_price)
                    change_pct = ((new_price_paise - old_price) / old_price) * 100 if old_price > 0 else 0
                    
                    db.update_asset_price(asset['asset_id'], new_price_paise, change_pct)
                    
                    # Record history
                    db.execute_insert(
                        "INSERT INTO market_price_history (asset_id, price) VALUES (?, ?)",
                        (asset['asset_id'], new_price_paise)
                    )
                    
                    db.log_action(
                        'ADMIN', admin_id,
                        f"Updated {asset['asset_symbol']} price to ₹{new_price:.2f}",
                        'market_assets', asset['asset_id']
                    )
                    
                    st.success(f"Price updated! Change: {change_pct:+.2f}%")
                    st.rerun()
    
    # Add Asset Tab
    with tab3:
        st.subheader("Add New Asset")
        
        with st.form("add_asset"):
            col1, col2 = st.columns(2)
            
            with col1:
                asset_name = st.text_input("Asset Name", placeholder="e.g., Tata Motors")
                asset_symbol = st.text_input("Symbol", placeholder="e.g., TATAMOTORS")
                asset_type = st.selectbox("Type", ["STOCK", "CRYPTO", "MUTUAL_FUND", "ETF", "BOND", "GOLD"])
            
            with col2:
                current_price = st.number_input("Initial Price (₹)", min_value=0.0, step=10.0)
                volatility = st.slider("Volatility (%)", 0.5, 20.0, 5.0, 0.5)
            
            submit = st.form_submit_button("Add Asset", use_container_width=True)
            
            if submit:
                if asset_name and asset_symbol and current_price > 0:
                    # Check if symbol exists
                    existing = db.execute_one(
                        "SELECT asset_id FROM market_assets WHERE asset_symbol = ?",
                        (asset_symbol.upper(),)
                    )
                    
                    if existing:
                        st.error("Symbol already exists!")
                    else:
                        asset_id = db.execute_insert(
                            """INSERT INTO market_assets 
                               (asset_name, asset_symbol, asset_type, current_price, volatility_percent)
                               VALUES (?, ?, ?, ?, ?)""",
                            (asset_name, asset_symbol.upper(), asset_type, 
                             db.to_paise(current_price), volatility)
                        )
                        
                        if asset_id:
                            db.log_action('ADMIN', admin_id, f"Added asset: {asset_symbol}", 'market_assets', asset_id)
                            st.success(f"Asset {asset_symbol} added successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to add asset")
                else:
                    st.error("Please fill in all required fields")
        
        st.markdown("---")
        
        # Manage Existing Assets
        st.subheader("Manage Assets")
        
        asset_to_manage = st.selectbox(
            "Select Asset to Manage",
            options=[(a['asset_id'], f"{a['asset_symbol']} - {a['asset_name']}") for a in assets],
            format_func=lambda x: x[1]
        )
        
        if asset_to_manage:
            asset = db.get_asset_by_id(asset_to_manage[0])
            
            if asset:
                col1 = st.columns(1)
                
                with col1[0]:
                    new_volatility = st.slider(
                        "Volatility (%)",
                        0.5, 20.0,
                        float(asset['volatility_percent']),
                        0.5,
                        key="manage_vol"
                    )
                    
                    if st.button("Update Volatility"):
                        db.execute(
                            "UPDATE market_assets SET volatility_percent = ? WHERE asset_id = ?",
                            (new_volatility, asset['asset_id'])
                        )
                        st.success("Volatility updated!")
                        st.rerun()
    
    # History Tab
    with tab4:
        st.subheader("Price History")
        
        # Select asset
        asset_for_history = st.selectbox(
            "Select Asset",
            options=[(a['asset_id'], f"{a['asset_symbol']} - {a['asset_name']}") for a in assets],
            format_func=lambda x: x[1],
            key="history_asset"
        )
        
        if asset_for_history:
            history = investment_service.get_price_history(asset_for_history[0], days=30)
            
            if history:
                df = pd.DataFrame(history)
                
                fig = px.line(
                    df, x='date', y='price',
                    title=f"Price History",
                    labels={'date': 'Date', 'price': 'Price (₹)'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                
                prices = [h['price'] for h in history]
                
                with col1:
                    st.metric("Current", f"₹{prices[-1]:,.2f}")
                with col2:
                    st.metric("High", f"₹{max(prices):,.2f}")
                with col3:
                    st.metric("Low", f"₹{min(prices):,.2f}")
                with col4:
                    change = ((prices[-1] - prices[0]) / prices[0] * 100) if prices[0] > 0 else 0
                    st.metric("30d Change", f"{change:+.2f}%")
            else:
                st.info("No price history available")
