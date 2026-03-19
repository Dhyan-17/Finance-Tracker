"""
Investments Page
Portfolio management and market overview
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from database.db import db
from services.investment_service import investment_service


def show_investments():
    """Display investments page"""
    user = st.session_state.user
    user_id = user['user_id']
    
    st.title("📈 Investments")
    
    # Get portfolio data
    portfolio = investment_service.get_portfolio(user_id)
    
    # Portfolio Summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invested", f"₹{portfolio['total_invested']:,.2f}")
    
    with col2:
        st.metric("Current Value", f"₹{portfolio['current_value']:,.2f}")
    
    with col3:
        pl_delta = f"{portfolio['profit_loss_percent']:+.2f}%"
        st.metric(
            "Profit/Loss", 
            f"₹{portfolio['total_profit_loss']:,.2f}",
            delta=pl_delta,
            delta_color="normal" if portfolio['total_profit_loss'] >= 0 else "inverse"
        )
    
    with col4:
        returns = portfolio['profit_loss_percent']
        st.metric(
            "Returns",
            f"{returns:+.2f}%",
            delta="Good" if returns > 10 else "Average" if returns > 0 else "Loss",
            delta_color="normal" if returns >= 0 else "inverse"
        )
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Portfolio", "🛒 Buy", "💰 Sell", "📈 Market"])
    
    # Portfolio Tab
    with tab1:
        if portfolio['holdings']:
            # Portfolio by type pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Portfolio Allocation")
                
                type_data = []
                for asset_type, data in portfolio['by_type'].items():
                    type_data.append({
                        'Type': asset_type,
                        'Value': data['current'],
                        'Count': data['count']
                    })
                
                if type_data:
                    df = pd.DataFrame(type_data)
                    fig = px.pie(
                        df, values='Value', names='Type',
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig, width='stretch')
            
            with col2:
                st.subheader("Holdings Performance")
                
                # Bar chart of holdings
                holdings_df = pd.DataFrame([{
                    'Asset': h['asset_symbol'],
                    'P/L %': h['profit_loss_percent']
                } for h in portfolio['holdings'][:10]])
                
                if not holdings_df.empty:
                    colors = ['green' if x >= 0 else 'red' for x in holdings_df['P/L %']]
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=holdings_df['Asset'],
                            y=holdings_df['P/L %'],
                            marker_color=colors
                        )
                    ])
                    fig.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=20, b=20),
                        yaxis_title="Return %"
                    )
                    st.plotly_chart(fig, width='stretch')
            
            # Holdings Table
            st.subheader("Your Holdings")
            
            holdings_data = []
            for h in portfolio['holdings']:
                holdings_data.append({
                    'Asset': f"{h['asset_name']} ({h['asset_symbol']})",
                    'Type': h['asset_type'],
                    'Units': f"{h['units_owned']:.4f}",
                    'Buy Price': f"₹{h['buy_price']:,.2f}",
                    'Current Price': f"₹{h['current_price']:,.2f}",
                    'Invested': f"₹{h['invested_amount']:,.2f}",
                    'Current Value': f"₹{h['current_value']:,.2f}",
                    'P/L': f"₹{h['profit_loss']:+,.2f}",
                    'Return': f"{h['profit_loss_percent']:+.2f}%",
                    'Day Change': f"{h['day_change']:+.2f}%" if h['day_change'] else "0.00%"
                })
            
            df = pd.DataFrame(holdings_data)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("You don't have any investments yet. Start investing to grow your wealth!")
    
    # Buy Tab
    with tab2:
        st.subheader("Buy Investment")
        
        # Market assets - refresh each time
        market = investment_service.get_market_overview()
        
        # Investment method selection
        invest_method = st.radio(
            "Investment Method",
            ["💰 By Amount", "📊 By Quantity/Units"],
            horizontal=True,
            key="invest_method"
        )
        
        # Asset Type and Selection (fully dynamic - no form)
        col1, col2 = st.columns(2)
        
        with col1:
            asset_type = st.selectbox(
                "Asset Type", 
                ["STOCK", "CRYPTO", "MUTUAL_FUND", "GOLD", "ETF"],
                key="asset_type_select"
            )
            
            # Get assets of selected type - this updates dynamically
            assets = market['by_type'].get(asset_type, [])
            
            if assets:
                asset_options = {f"{a['name']} ({a['symbol']}) - ₹{a['price']:,.2f}": a['asset_id'] 
                               for a in assets}
                selected_asset = st.selectbox("Select Asset", list(asset_options.keys()), key="asset_select")
                asset_id = asset_options[selected_asset]
                
                # Get current price of selected asset
                current_price = 0.0
                for a in assets:
                    if a['asset_id'] == asset_id:
                        current_price = a['price']
                        break
                
                # Show current price
                st.success(f"Current Price: ₹{current_price:,.2f} per unit")
            else:
                st.warning(f"No {asset_type} assets available")
                asset_id = None
                current_price = 0.0
        
        with col2:
            if invest_method == "💰 By Amount":
                amount = st.number_input("Investment Amount (₹)", min_value=100.0, step=100.0, value=100.0, format="%.2f", key="amount_input")
                if amount and current_price > 0:
                    quantity = amount / current_price
                    st.info(f"📊 You will get: **{quantity:.6f} units**")
                else:
                    quantity = 0.0
            else:
                # Quantity input
                quantity = st.number_input(
                    "Quantity (Units)", 
                    min_value=0.0001, 
                    step=0.001, 
                    value=0.001,
                    format="%.6f",
                    key="quantity_input"
                )
                if quantity and current_price > 0:
                    total_price = quantity * current_price
                    st.metric("Total Price", f"₹{total_price:,.2f}", delta=f"@ ₹{current_price:,.2f} per unit")
                amount = 0.0
        
        # Payment source (outside form for real-time)
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.selectbox("Pay From", ["💳 Wallet"], key="pay_from")
            source = 'WALLET'
            source_account_id = None
        
        with col2:
            # Calculate final amount
            purchase_amount = amount if amount > 0 else (quantity * current_price)
            st.metric("Total Investment", f"₹{purchase_amount:,.2f}")
        
        # Buy button (not in form for real-time updates)
        if st.button("Buy Now", type="primary", use_container_width=True):
            if not asset_id:
                st.error("Please select an asset first")
            elif purchase_amount < 100:
                st.error("Minimum investment amount is ₹100")
            else:
                success, message, result = investment_service.buy_asset(
                    user_id=user_id,
                    asset_id=asset_id,
                    amount=purchase_amount,
                    source_account_type=source,
                    source_account_id=source_account_id
                )
                
                if success:
                    st.success(f"✅ {message}")
                    st.info(f"Bought {result['units']:.4f} units of {result['symbol']} @ ₹{result['price_per_unit']:,.2f}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    # Sell Tab
    with tab3:
        st.subheader("Sell Investment")
        
        if portfolio['holdings']:
            # Select from holdings (outside form for dynamic updates)
            col1, col2 = st.columns(2)
            
            with col1:
                holding_options = {
                    f"{h['asset_name']} ({h['units_owned']:.4f} units @ ₹{h['current_price']:,.2f})": 
                    (h['asset_id'], h['units_owned'], h['current_price'])
                    for h in portfolio['holdings']
                }
                
                selected_holding = st.selectbox("Select Holding", list(holding_options.keys()), key="sell_holding")
                asset_id, max_units, current_price = holding_options[selected_holding]
                
                units_to_sell = st.number_input(
                    "Units to Sell",
                    min_value=0.0001,
                    max_value=float(max_units),
                    value=float(max_units),
                    step=0.0001,
                    format="%.4f",
                    key="units_to_sell"
                )
            
            with col2:
                estimated_value = units_to_sell * current_price
                st.metric("Estimated Value", f"₹{estimated_value:,.2f}")
                
                st.selectbox("Credit To", ["💳 Wallet"], key="sell_credit")
                target = 'WALLET'
                target_account_id = None
            
            # Sell button (not in form for real-time updates)
            if st.button("Sell Now", type="primary", use_container_width=True, key="sell_btn"):
                success, message, result = investment_service.sell_asset(
                    user_id=user_id,
                    asset_id=asset_id,
                    units_to_sell=units_to_sell,
                    target_account_type=target,
                    target_account_id=target_account_id
                )
                
                if success:
                    st.success(f"✅ {message}")
                    pl_text = "Profit" if result['profit_loss'] >= 0 else "Loss"
                    st.info(f"Sold {result['units_sold']:.4f} units for ₹{result['total_amount']:,.2f} ({pl_text}: ₹{abs(result['profit_loss']):,.2f})")
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        else:
            st.info("You don't have any holdings to sell.")
    
    # Market Tab
    with tab4:
        st.subheader("Market Overview")
        
        market = investment_service.get_market_overview()
        
        # Top Gainers and Losers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🟢 Top Gainers")
            for asset in market['top_gainers'][:5]:
                change = asset.get('day_change_percent', 0) or 0
                st.markdown(f"**{asset['asset_symbol']}** - ₹{db.to_rupees(asset['current_price']):,.2f} ({change:+.2f}%)")
        
        with col2:
            st.markdown("### 🔴 Top Losers")
            for asset in market['top_losers'][:5]:
                change = asset.get('day_change_percent', 0) or 0
                st.markdown(f"**{asset['asset_symbol']}** - ₹{db.to_rupees(asset['current_price']):,.2f} ({change:+.2f}%)")
        
        st.markdown("---")
        
        # All Assets by Type
        for asset_type, assets in market['by_type'].items():
            with st.expander(f"📊 {asset_type} ({len(assets)} assets)", expanded=False):
                data = []
                for a in assets:
                    data.append({
                        'Symbol': a['symbol'],
                        'Name': a['name'],
                        'Price': f"₹{a['price']:,.2f}",
                        'Day Change': f"{a['change']:+.2f}%" if a['change'] else "0.00%",
                        'Volatility': f"{a['volatility']:.1f}%"
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df, width='stretch', hide_index=True)
    
    # Transaction History
    st.markdown("---")
    st.subheader("📜 Investment History")
    
    history = investment_service.get_investment_history(user_id, limit=20)
    
    if history:
        df_data = []
        for h in history:
            df_data.append({
                'Date': h['date'][:16],
                'Type': h['type'],
                'Asset': h['symbol'],
                'Units': f"{h['units']:.4f}",
                'Price': f"₹{h['price_per_unit']:,.2f}",
                'Total': f"₹{h['total_amount']:,.2f}"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No investment transactions yet.")
