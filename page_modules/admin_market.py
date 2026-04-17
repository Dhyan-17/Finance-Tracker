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


def show_admin_market():
    """Display admin market management page"""
    if "admin" not in st.session_state or not st.session_state.admin:
        st.error("Please login as admin")
        return

    admin = st.session_state.admin
    admin_id = admin["admin_id"]

    st.markdown(
        """
    <div style="background:#F0F4FF; border-radius:16px; padding:1.5rem; border:1px solid #AB8EE8; margin-bottom:2rem;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">📈 Market Management</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Manage market assets and prices</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Overview", "🔄 Update Prices", "➕ Add Asset", "📜 History"]
    )

    # Overview Tab
    with tab1:
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">Market Overview</h3>',
            unsafe_allow_html=True,
        )

        # Get all assets
        assets = db.get_market_assets()

        total_assets = len(assets) if assets else 0
        gainers = len([a for a in assets if (a.get("day_change_percent") or 0) > 0])
        losers = len([a for a in assets if (a.get("day_change_percent") or 0) < 0])
        unchanged = total_assets - gainers - losers

        # Summary
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            metric_card(
                title="Total Assets",
                value=str(total_assets),
                subtitle="All types",
                color="#5B8DEF",
                bg="#EEF4FF",
                icon="📊",
            )
        with col2:
            metric_card(
                title="Gainers",
                value=str(gainers),
                subtitle="Up today",
                color="#43A87B",
                bg="#EEFAF4",
                icon="🟢",
            )
        with col3:
            metric_card(
                title="Losers",
                value=str(losers),
                subtitle="Down today",
                color="#F26C6C",
                bg="#FFF4EE",
                icon="🔴",
            )
        with col4:
            metric_card(
                title="Unchanged",
                value=str(unchanged),
                subtitle="No change",
                color="#6B7280",
                bg="#FAFAFA",
                icon="⚪",
            )

        st.markdown("---")

        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">All Assets</h3>',
            unsafe_allow_html=True,
        )

        if assets:
            df_data = []
            for a in assets:
                change = a.get("day_change_percent") or 0

                if change > 0:
                    status = "🟢"
                elif change < 0:
                    status = "🔴"
                else:
                    status = "⚪"

                df_data.append(
                    {
                        "Status": status,
                        "Symbol": a["asset_symbol"],
                        "Name": a["asset_name"],
                        "Type": a["asset_type"],
                        "Price": f"₹{db.to_rupees(a['current_price']):,.2f}",
                        "Change": f"{change:+.2f}%",
                        "Volatility": f"{a['volatility_percent']:.1f}%",
                    }
                )

            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown(
                f'<div style="color:#6B7280; font-size:0.85rem; margin-top:0.5rem;">Showing {total_assets} assets</div>',
                unsafe_allow_html=True,
            )

    # Update Prices Tab
    with tab2:
        st.markdown(
            """
        <div style="background:#FFF8E8; border-radius:16px; padding:1.5rem; border:1px solid #F5A623; margin-bottom:1.5rem;">
            <div style="font-weight:600; color:#1A1A2E;">⚠️ Warning</div>
            <div style="color:#6B7280;">This will update ALL asset prices and affect all user portfolios!</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Simulate Market Update", use_container_width=True):
                with st.spinner("Updating prices..."):
                    updated = investment_service.update_market_prices()

                if updated:
                    st.success(f"Updated {len(updated)} assets!")

                    df_data = []
                    for u in updated:
                        df_data.append(
                            {
                                "Asset": u["symbol"],
                                "Old Price": f"₹{u['old_price']:,.2f}",
                                "New Price": f"₹{u['new_price']:,.2f}",
                            }
                        )

                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

                    db.log_action(
                        "ADMIN",
                        admin_id,
                        f"Updated market prices for {len(updated)} assets",
                    )
                else:
                    st.info("No price changes")

        with col2:
            st.markdown(
                """
            <div style="background:#FFFFFF; border-radius:12px; padding:1.5rem; border:1px solid #E8ECF0;">
                <div style="font-weight:600; color:#1A1A2E; margin-bottom:1rem;">How it works:</div>
                <ul style="color:#6B7280; padding-left:1.2rem;">
                    <li>Prices are simulated based on volatility</li>
                    <li>Higher volatility = larger price swings</li>
                    <li>Crypto has highest (~10%)</li>
                    <li>Stocks moderate (~3%)</li>
                    <li>Mutual Funds lowest (~2%)</li>
                </ul>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.1rem; font-weight:600; margin:1rem 0 1rem 0;">Manual Price Update</h3>',
            unsafe_allow_html=True,
        )

        assets = db.get_market_assets()

        if assets:
            asset_options = {
                f"{a['asset_symbol']} - {a['asset_name']}": a for a in assets
            }
            selected = st.selectbox("Select Asset", list(asset_options.keys()))
            asset = asset_options[selected]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown(
                    f"**Current Price:** ₹{db.to_rupees(asset['current_price']):,.2f}"
                )
                st.markdown(f"**Day Change:** {asset['day_change_percent'] or 0:+.2f}%")
                st.markdown(f"**Volatility:** {asset['volatility_percent']}%")

            with col2:
                new_price = st.number_input(
                    "New Price (₹)",
                    min_value=0.01,
                    value=db.to_rupees(asset["current_price"]),
                    step=10.0,
                )

                if st.button("Update Price"):
                    old_price = asset["current_price"]
                    new_price_paise = db.to_paise(new_price)
                    change_pct = (
                        ((new_price_paise - old_price) / old_price) * 100
                        if old_price > 0
                        else 0
                    )

                    db.update_asset_price(
                        asset["asset_id"], new_price_paise, change_pct
                    )

                    db.execute_insert(
                        "INSERT INTO market_price_history (asset_id, price) VALUES (?, ?)",
                        (asset["asset_id"], new_price_paise),
                    )

                    db.log_action(
                        "ADMIN",
                        admin_id,
                        f"Updated {asset['asset_symbol']} price to ₹{new_price:.2f}",
                        "market_assets",
                        asset["asset_id"],
                    )

                    st.success(f"Price updated! Change: {change_pct:+.2f}%")
                    st.rerun()

    # Add Asset Tab
    with tab3:
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin-bottom:1.5rem;">Add New Asset</h3>',
            unsafe_allow_html=True,
        )

        with st.form("add_asset"):
            col1, col2 = st.columns(2)

            with col1:
                asset_name = st.text_input(
                    "Asset Name", placeholder="e.g., Tata Motors"
                )
                asset_symbol = st.text_input("Symbol", placeholder="e.g., TATAMOTORS")
                asset_type = st.selectbox(
                    "Type", ["STOCK", "CRYPTO", "MUTUAL_FUND", "ETF", "BOND", "GOLD"]
                )

            with col2:
                current_price = st.number_input(
                    "Initial Price (₹)", min_value=0.0, step=10.0
                )
                volatility = st.slider("Volatility (%)", 0.5, 20.0, 5.0, 0.5)

            submit = st.form_submit_button("Add Asset", use_container_width=True)

            if submit:
                if asset_name and asset_symbol and current_price > 0:
                    existing = db.execute_one(
                        "SELECT asset_id FROM market_assets WHERE asset_symbol = ?",
                        (asset_symbol.upper(),),
                    )

                    if existing:
                        st.error("Symbol already exists!")
                    else:
                        asset_id = db.execute_insert(
                            """INSERT INTO market_assets 
                               (asset_name, asset_symbol, asset_type, current_price, volatility_percent)
                               VALUES (?, ?, ?, ?, ?)""",
                            (
                                asset_name,
                                asset_symbol.upper(),
                                asset_type,
                                db.to_paise(current_price),
                                volatility,
                            ),
                        )

                        if asset_id:
                            db.log_action(
                                "ADMIN",
                                admin_id,
                                f"Added asset: {asset_symbol}",
                                "market_assets",
                                asset_id,
                            )
                            st.success(f"Asset {asset_symbol} added!")
                            st.rerun()
                        else:
                            st.error("Failed to add asset")
                else:
                    st.error("Please fill in all required fields")

    # History Tab
    with tab4:
        st.markdown(
            '<h3 style="color:#1A1A2E; font-size:1.2rem; font-weight:600; margin:1rem 0 1rem 0;">Price History</h3>',
            unsafe_allow_html=True,
        )

        asset_for_history = st.selectbox(
            "Select Asset",
            options=[
                (a["asset_id"], f"{a['asset_symbol']} - {a['asset_name']}")
                for a in assets
            ],
            format_func=lambda x: x[1],
            key="history_asset",
        )

        if asset_for_history:
            history = investment_service.get_price_history(
                asset_for_history[0], days=30
            )

            if history:
                df = pd.DataFrame(history)

                fig = px.line(
                    df,
                    x="date",
                    y="price",
                    title=f"Price History",
                    labels={"date": "Date", "price": "Price (₹)"},
                )
                fig.update_layout(
                    height=400,
                    template="plotly_white",
                    margin=dict(l=20, r=20, t=20, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)

                # Statistics
                col1, col2, col3, col4 = st.columns(4)

                prices = [h["price"] for h in history]

                with col1:
                    metric_card(
                        title="Current",
                        value=f"₹{prices[-1]:,.2f}",
                        subtitle="Latest",
                        color="#5B8DEF",
                        bg="#EEF4FF",
                        icon="📊",
                    )
                with col2:
                    metric_card(
                        title="High",
                        value=f"₹{max(prices):,.2f}",
                        subtitle="Period high",
                        color="#43A87B",
                        bg="#EEFAF4",
                        icon="📈",
                    )
                with col3:
                    metric_card(
                        title="Low",
                        value=f"₹{min(prices):,.2f}",
                        subtitle="Period low",
                        color="#F26C6C",
                        bg="#FFF4EE",
                        icon="📉",
                    )
                with col4:
                    change = (
                        ((prices[-1] - prices[0]) / prices[0] * 100)
                        if prices[0] > 0
                        else 0
                    )
                    met_color = "#43A87B" if change >= 0 else "#F26C6C"
                    met_bg = "#EEFAF4" if change >= 0 else "#FFF4EE"
                    metric_card(
                        title="30d Change",
                        value=f"{change:+.2f}%",
                        subtitle="Period change",
                        color=met_color,
                        bg=met_bg,
                        icon="📊",
                    )
            else:
                st.info("No price history available")
