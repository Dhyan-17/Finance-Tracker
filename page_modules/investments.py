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


def show_investments():
    """Display investments page"""
    user = st.session_state.user
    user_id = user["user_id"]

    st.markdown(
        """
    <div style="padding: 1rem 0 2rem 0;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">📈 Investments</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Grow your wealth with smart investments</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Get portfolio data
    portfolio = investment_service.get_portfolio(user_id)

    # Portfolio Summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            title="Total Invested",
            value=f"₹{portfolio['total_invested']:,.2f}",
            subtitle="All time",
            color="#5B8DEF",
            bg="#EEF4FF",
            icon="💰",
        )

    with col2:
        metric_card(
            title="Current Value",
            value=f"₹{portfolio['current_value']:,.2f}",
            subtitle="Present worth",
            color="#AB8EE8",
            bg="#F5F0FF",
            icon="💎",
        )

    with col3:
        pl_color = "#43A87B" if portfolio["total_profit_loss"] >= 0 else "#F26C6C"
        pl_bg = "#EEFAF4" if portfolio["total_profit_loss"] >= 0 else "#FFF4EE"
        metric_card(
            title="Profit/Loss",
            value=f"₹{portfolio['total_profit_loss']:,.2f}",
            subtitle=f"{portfolio['profit_loss_percent']:+.2f}%",
            color=pl_color,
            bg=pl_bg,
            icon="📊",
        )

    with col4:
        ret_color = "#43A87B" if portfolio["profit_loss_percent"] >= 0 else "#F26C6C"
        ret_bg = "#EEFAF4" if portfolio["profit_loss_percent"] >= 0 else "#FFF4EE"
        returns = portfolio["profit_loss_percent"]
        status = "Great" if returns > 10 else "Good" if returns > 0 else "Loss"
        metric_card(
            title="Returns",
            value=f"{returns:+.2f}%",
            subtitle=status,
            color=ret_color,
            bg=ret_bg,
            icon="📈",
        )

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Portfolio", "🛒 Buy", "💰 Sell", "📈 Market"])

    # Portfolio Tab
    with tab1:
        if portfolio["holdings"]:
            # Portfolio by type pie chart
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    '<h3 style="color:#1A1A2E; font-size:1.1rem; font-weight:600; margin:1rem 0 1rem 0;">📊 Portfolio Allocation</h3>',
                    unsafe_allow_html=True,
                )

                type_data = []
                for asset_type, data in portfolio["by_type"].items():
                    type_data.append(
                        {
                            "Type": asset_type,
                            "Value": data["current"],
                            "Count": data["count"],
                        }
                    )

                if type_data:
                    df = pd.DataFrame(type_data)
                    fig = px.pie(
                        df,
                        values="Value",
                        names="Type",
                        color_discrete_sequence=[
                            "#5B8DEF",
                            "#43A87B",
                            "#AB8EE8",
                            "#F26C6C",
                            "#F5A623",
                        ],
                    )
                    fig.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=20, b=20),
                        template="plotly_white",
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown(
                    '<h3 style="color:#1A1A2E; font-size:1.1rem; font-weight:600; margin:1rem 0 1rem 0;">📈 Holdings Performance</h3>',
                    unsafe_allow_html=True,
                )

                # Bar chart of holdings
                holdings_df = pd.DataFrame(
                    [
                        {"Asset": h["asset_symbol"], "P/L %": h["profit_loss_percent"]}
                        for h in portfolio["holdings"][:10]
                    ]
                )

                if not holdings_df.empty:
                    colors = [
                        "#43A87B" if x >= 0 else "#F26C6C" for x in holdings_df["P/L %"]
                    ]

                    fig = go.Figure(
                        data=[
                            go.Bar(
                                x=holdings_df["Asset"],
                                y=holdings_df["P/L %"],
                                marker_color=colors,
                            )
                        ]
                    )
                    fig.update_layout(
                        height=350,
                        margin=dict(l=20, r=20, t=20, b=20),
                        yaxis_title="Return %",
                        template="plotly_white",
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Holdings Table
            st.markdown("---")
            st.markdown(
                '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">📋 Your Holdings</h3>',
                unsafe_allow_html=True,
            )

            holdings_data = []
            for h in portfolio["holdings"]:
                holdings_data.append(
                    {
                        "Asset": f"{h['asset_name']} ({h['asset_symbol']})",
                        "Type": h["asset_type"],
                        "Units": f"{h['units_owned']:.4f}",
                        "Buy Price": f"₹{h['buy_price']:,.2f}",
                        "Current Price": f"₹{h['current_price']:,.2f}",
                        "Invested": f"₹{h['invested_amount']:,.2f}",
                        "Current Value": f"₹{h['current_value']:,.2f}",
                        "P/L": f"₹{h['profit_loss']:+,.2f}",
                        "Return": f"{h['profit_loss_percent']:+.2f}%",
                        "Day Change": f"{h['day_change']:+.2f}%"
                        if h["day_change"]
                        else "0.00%",
                    }
                )

            df = pd.DataFrame(holdings_data)
            st.dataframe(df, width="stretch", hide_index=True)
        else:
            st.markdown(
                """
            <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
                <div style="font-size:2rem;">📈</div>
                <p style="color:#6B7280; margin-top:0.5rem;">No investments yet</p>
                <p style="color:#6B7280; font-size:0.9rem;">Start investing to grow your wealth!</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Buy Tab
    with tab2:
        

        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">🛒 Buy Investment</h3>',
            unsafe_allow_html=True,
        )

        # Market assets
        market = investment_service.get_market_overview()

        # Investment method selection
        invest_method = st.radio(
            "Investment Method",
            ["💰 By Amount", "📊 By Quantity/Units"],
            horizontal=True,
            key="invest_method",
        )

        col1, col2 = st.columns(2)

        with col1:
            asset_type = st.selectbox(
                "Asset Type",
                ["STOCK", "CRYPTO", "MUTUAL_FUND", "GOLD", "ETF"],
                key="asset_type_select",
            )

            # Get assets of selected type
            assets = market["by_type"].get(asset_type, [])

            if assets:
                asset_options = {
                    f"{a['name']} ({a['symbol']}) - ₹{a['price']:,.2f}": a["asset_id"]
                    for a in assets
                }
                selected_asset = st.selectbox(
                    "Select Asset", list(asset_options.keys()), key="asset_select"
                )
                asset_id = asset_options[selected_asset]

                # Get current price
                current_price = 0.0
                for a in assets:
                    if a["asset_id"] == asset_id:
                        current_price = a["price"]
                        break

                st.success(f"Current Price: ₹{current_price:,.2f} per unit")
            else:
                st.warning(f"No {asset_type} assets available")
                asset_id = None
                current_price = 0.0

        with col2:
            if invest_method == "💰 By Amount":
                amount = st.number_input(
                    "Investment Amount (₹)",
                    min_value=100.0,
                    step=100.0,
                    value=100.0,
                    format="%.2f",
                    key="amount_input",
                )
                if amount and current_price > 0:
                    quantity = amount / current_price
                    st.info(f"You will get: **{quantity:.6f} units**")
                else:
                    quantity = 0.0
            else:
                quantity = st.number_input(
                    "Quantity (Units)",
                    min_value=0.0001,
                    step=0.001,
                    value=0.001,
                    format="%.6f",
                    key="quantity_input",
                )
                if quantity and current_price > 0:
                    total_price = quantity * current_price
                    st.metric(
                        "Total Price",
                        f"₹{total_price:,.2f}",
                        delta=f"@ ₹{current_price:,.2f} per unit",
                    )
                amount = 0.0

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.selectbox("Pay From", ["💳 Wallet"], key="pay_from")
            source = "WALLET"
            source_account_id = None

        with col2:
            purchase_amount = amount if amount > 0 else (quantity * current_price)
            st.metric("Total Investment", f"₹{purchase_amount:,.2f}")

        if st.button("Buy Now", use_container_width=True):
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
                    source_account_id=source_account_id,
                )

                if success:
                    st.success(f"✅ {message}")
                    st.info(
                        f"Bought {result['units']:.4f} units of {result['symbol']} @ ₹{result['price_per_unit']:,.2f}"
                    )
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

    # Sell Tab
    with tab3:
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">💰 Sell Investment</h3>',
            unsafe_allow_html=True,
        )

        if portfolio["holdings"]:
            col1, col2 = st.columns(2)

            with col1:
                holding_options = {
                    f"{h['asset_name']} ({h['units_owned']:.4f} units @ ₹{h['current_price']:,.2f})": (
                        h["asset_id"],
                        h["units_owned"],
                        h["current_price"],
                    )
                    for h in portfolio["holdings"]
                }

                selected_holding = st.selectbox(
                    "Select Holding", list(holding_options.keys()), key="sell_holding"
                )
                asset_id, max_units, current_price = holding_options[selected_holding]

                units_to_sell = st.number_input(
                    "Units to Sell",
                    min_value=0.0001,
                    max_value=float(max_units),
                    value=float(max_units),
                    step=0.0001,
                    format="%.4f",
                    key="units_to_sell",
                )

            with col2:
                estimated_value = units_to_sell * current_price
                st.metric("Estimated Value", f"₹{estimated_value:,.2f}")

                st.selectbox("Credit To", ["💳 Wallet"], key="sell_credit")
                target = "WALLET"
                target_account_id = None

            if st.button("Sell Now", use_container_width=True, key="sell_btn"):
                success, message, result = investment_service.sell_asset(
                    user_id=user_id,
                    asset_id=asset_id,
                    units_to_sell=units_to_sell,
                    target_account_type=target,
                    target_account_id=target_account_id,
                )

                if success:
                    st.success(f"✅ {message}")
                    pl_text = "Profit" if result["profit_loss"] >= 0 else "Loss"
                    st.info(
                        f"Sold {result['units_sold']:.4f} units for ₹{result['total_amount']:,.2f} ({pl_text}: ₹{abs(result['profit_loss']):,.2f})"
                    )
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        else:
            st.markdown(
                """
            <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
                <p style="color:#6B7280; margin-top:0.5rem;">No holdings to sell</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Market Tab
    with tab4:
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">📈 Market Overview</h3>',
            unsafe_allow_html=True,
        )

        market = investment_service.get_market_overview()

        # Top Gainers and Losers
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                """
            <div style="background:#EEFAF4; border-radius:16px; padding:1.5rem; border-left:4px solid #43A87B;">
                <div style="font-weight:600; color:#1A1A2E; margin-bottom:1rem;">🟢 Top Gainers</div>
            """,
                unsafe_allow_html=True,
            )
            for asset in market["top_gainers"][:5]:
                change = asset.get("day_change_percent", 0) or 0
                st.markdown(
                    f"**{asset['asset_symbol']}** - ₹{db.to_rupees(asset['current_price']):,.2f} ({change:+.2f}%)"
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(
                """
            <div style="background:#FFF4EE; border-radius:16px; padding:1.5rem; border-left:4px solid #F26C6C;">
                <div style="font-weight:600; color:#1A1A2E; margin-bottom:1rem;">🔴 Top Losers</div>
            """,
                unsafe_allow_html=True,
            )
            for asset in market["top_losers"][:5]:
                change = asset.get("day_change_percent", 0) or 0
                st.markdown(
                    f"**{asset['asset_symbol']}** - ₹{db.to_rupees(asset['current_price']):,.2f} ({change:+.2f}%)"
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # All Assets by Type
        for asset_type, assets in market["by_type"].items():
            with st.expander(f"📊 {asset_type} ({len(assets)} assets)", expanded=False):
                data = []
                for a in assets:
                    data.append(
                        {
                            "Symbol": a["symbol"],
                            "Name": a["name"],
                            "Price": f"₹{a['price']:,.2f}",
                            "Day Change": f"{a['change']:+.2f}%"
                            if a["change"]
                            else "0.00%",
                            "Volatility": f"{a['volatility']:.1f}%",
                        }
                    )

                df = pd.DataFrame(data)
                st.dataframe(df, width="stretch", hide_index=True)

    # Transaction History
    st.markdown("---")
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">📜 Investment History</h3>',
        unsafe_allow_html=True,
    )

    history = investment_service.get_investment_history(user_id, limit=20)

    if history:
        df_data = []
        for h in history:
            df_data.append(
                {
                    "Date": h["date"][:16],
                    "Type": h["type"],
                    "Asset": h["symbol"],
                    "Units": f"{h['units']:.4f}",
                    "Price": f"₹{h['price_per_unit']:,.2f}",
                    "Total": f"₹{h['total_amount']:,.2f}",
                }
            )

        df = pd.DataFrame(df_data)
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.markdown(
            """
        <div style="background:#FFFFFF; border-radius:16px; padding:2rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
            <p style="color:#6B7280; margin-top:0.5rem;">No investment transactions yet</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
