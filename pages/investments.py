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
                    st.plotly_chart(fig, use_container_width=True)
            
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
                    st.plotly_chart(fig, use_container_width=True)
            
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
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("You don't have any investments yet. Start investing to grow your wealth!")
    
    # Buy Tab
    with tab2:
        st.subheader("Buy Investment")
        
        # Market assets
        market = investment_service.get_market_overview()
        
        with st.form("buy_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Asset type filter
                asset_type = st.selectbox("Asset Type", ["STOCK", "CRYPTO", "MUTUAL_FUND", "GOLD", "ETF"])
                
                # Get assets of selected type
                assets = market['by_type'].get(asset_type, [])
                
                if assets:
                    asset_options = {f"{a['name']} ({a['symbol']}) - ₹{a['price']:,.2f}": a['asset_id'] 
                                   for a in assets}
                    selected_asset = st.selectbox("Select Asset", list(asset_options.keys()))
                    asset_id = asset_options[selected_asset]
                else:
                    st.warning(f"No {asset_type} assets available")
                    asset_id = None
            
            with col2:
                amount = st.number_input("Investment Amount (₹)", min_value=100.0, step=500.0, format="%.2f")
                
                source = st.selectbox("Pay From", ["Wallet", "Bank Account"])
                
                source_account_id = None
                if source == "Bank Account":
                    bank_accounts = db.get_user_bank_accounts(user_id)
                    if bank_accounts:
                        bank_options = {f"{a['bank_name']} (₹{db.to_rupees(a['balance']):,.0f})": a['account_id'] 
                                       for a in bank_accounts}
                        selected_bank = st.selectbox("Select Bank", list(bank_options.keys()))
                        source_account_id = bank_options[selected_bank]
            
            submit = st.form_submit_button("Buy Now", use_container_width=True)
            
            if submit and asset_id:
                success, message, result = investment_service.buy_asset(
                    user_id=user_id,
                    asset_id=asset_id,
                    amount=amount,
                    source_account_type='WALLET' if source == "Wallet" else 'BANK',
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
            with st.form("sell_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Select from holdings
                    holding_options = {
                        f"{h['asset_name']} ({h['units_owned']:.4f} units @ ₹{h['current_price']:,.2f})": 
                        (h['asset_id'], h['units_owned'], h['current_price'])
                        for h in portfolio['holdings']
                    }
                    
                    selected_holding = st.selectbox("Select Holding", list(holding_options.keys()))
                    asset_id, max_units, current_price = holding_options[selected_holding]
                    
                    units_to_sell = st.number_input(
                        "Units to Sell",
                        min_value=0.0001,
                        max_value=float(max_units),
                        value=float(max_units),
                        step=0.0001,
                        format="%.4f"
                    )
                
                with col2:
                    estimated_value = units_to_sell * current_price
                    st.metric("Estimated Value", f"₹{estimated_value:,.2f}")
                    
                    target = st.selectbox("Credit To", ["Wallet", "Bank Account"])
                    
                    target_account_id = None
                    if target == "Bank Account":
                        bank_accounts = db.get_user_bank_accounts(user_id)
                        if bank_accounts:
                            bank_options = {f"{a['bank_name']}": a['account_id'] for a in bank_accounts}
                            selected_bank = st.selectbox("Select Bank", list(bank_options.keys()), key="sell_bank")
                            target_account_id = bank_options[selected_bank]
                
                submit = st.form_submit_button("Sell Now", use_container_width=True)
                
                if submit:
                    success, message, result = investment_service.sell_asset(
                        user_id=user_id,
                        asset_id=asset_id,
                        units_to_sell=units_to_sell,
                        target_account_type='WALLET' if target == "Wallet" else 'BANK',
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
                st.dataframe(df, use_container_width=True, hide_index=True)
    
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
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No investment transactions yet.")
