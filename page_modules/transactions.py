"""
Transactions Page
Transaction history and filtering
"""

import streamlit as st
import plotly.express as px
import pandas as pd
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


def transaction_row(date, category, description, amount, txn_type, payment_mode="-"):
    border_color = "#43A87B" if txn_type == "Income" else "#F26C6C"
    amount_color = "#43A87B" if amount > 0 else "#F26C6C"
    amount_prefix = "+" if amount > 0 else "-"

    st.markdown(
        f"""
    <div style="background:#FFFFFF; border-radius:12px; padding:1rem; border-left:4px solid {border_color}; margin-bottom:0.5rem; box-shadow:0 1px 4px rgba(0,0,0,0.04); border:1px solid #E8ECF0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#6B7280; font-size:0.8rem;">{date[:10]}</div>
                <div style="color:#1A1A2E; font-size:1rem; font-weight:600; margin:0.2rem 0;">{category}</div>
                <div style="color:#6B7280; font-size:0.85rem;">{description if description else "-"}</div>
            </div>
            <div style="text-align:right;">
                <div style="color:#1A1A2E; font-size:1.1rem; font-weight:700; color:{amount_color};">{amount_prefix}₹{abs(amount):,.2f}</div>
                <div style="color:#6B7280; font-size:0.8rem;">{payment_mode}</div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def show_transactions():
    """Display transactions page"""
    user = st.session_state.user
    user_id = user["user_id"]

    st.markdown(
        """
    <div style="padding: 1rem 0 2rem 0;">
        <h1 style="color:#1A1A2E; font-size:1.8rem; font-weight:700; margin:0;">📊 Transactions</h1>
        <p style="color:#6B7280; font-size:1rem; margin-top:0.5rem;">Track your income and expenses</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Filter Options
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.1rem; font-weight:600; margin:1rem 0 1rem 0;">🔍 Filters</h3>',
        unsafe_allow_html=True,
    )

    # Filter bar
    

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        txn_type = st.selectbox("Transaction Type", ["All", "Expenses", "Income"])

    with col2:
        date_range = st.selectbox(
            "Date Range",
            [
                "This Month",
                "Last Month",
                "Last 3 Months",
                "Last 6 Months",
                "This Year",
                "Custom",
            ],
        )

    # Date range calculation
    now = datetime.now()
    if date_range == "This Month":
        start_date = now.replace(day=1).strftime("%Y-%m-%d")
        end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_range == "Last Month":
        last_month = now.replace(day=1) - timedelta(days=1)
        start_date = last_month.replace(day=1).strftime("%Y-%m-%d")
        end_date = last_month.strftime("%Y-%m-%d")
    elif date_range == "Last 3 Months":
        start_date = (now - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_range == "Last 6 Months":
        start_date = (now - timedelta(days=180)).strftime("%Y-%m-%d")
        end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    elif date_range == "This Year":
        start_date = now.strftime("%Y-01-01")
        end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        start_date = None
        end_date = None

    with col3:
        if date_range == "Custom":
            start_date = st.date_input("From", value=now - timedelta(days=30)).strftime(
                "%Y-%m-%d"
            )
        else:
            st.text_input("From", value=start_date, disabled=True)

    with col4:
        if date_range == "Custom":
            end_date = st.date_input("To", value=now + timedelta(days=1)).strftime(
                "%Y-%m-%d"
            )
        else:
            st.text_input("To", value=end_date, disabled=True)

    # Category filter for expenses
    category_filter = None
    if txn_type in ["All", "Expenses"]:
        categories = db.get_expense_categories()
        category_names = ["All Categories"] + [c["name"] for c in categories]
        selected_category = st.selectbox("Category", category_names)
        if selected_category != "All Categories":
            category_filter = selected_category

    # Fetch transactions based on filters
    all_transactions = []

    if txn_type in ["All", "Expenses"]:
        expenses = db.get_user_expenses(
            user_id,
            start_date=start_date,
            end_date=end_date,
            category=category_filter,
            limit=200,
        )
        for e in expenses:
            all_transactions.append(
                {
                    "id": e["expense_id"],
                    "date": e["date"],
                    "type": "Expense",
                    "category": e["category"],
                    "subcategory": e.get("subcategory", ""),
                    "amount": -db.to_rupees(e["amount"]),
                    "description": e.get("description", ""),
                    "payment_mode": e.get("payment_mode", ""),
                    "merchant": e.get("merchant", ""),
                    "icon": "📤",
                }
            )

    if txn_type in ["All", "Income"]:
        income = db.get_user_income(
            user_id, start_date=start_date, end_date=end_date, limit=200
        )
        for i in income:
            all_transactions.append(
                {
                    "id": i["income_id"],
                    "date": i["date"],
                    "type": "Income",
                    "category": i.get("category", ""),
                    "subcategory": i.get("source", ""),
                    "amount": db.to_rupees(i["amount"]),
                    "description": i.get("description", ""),
                    "payment_mode": "",
                    "merchant": "",
                    "icon": "📥",
                }
            )

    # Sort by date
    all_transactions.sort(key=lambda x: x["date"], reverse=True)

    # Summary
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.1rem; font-weight:600; margin:1rem 0 1rem 0;">📈 Summary</h3>',
        unsafe_allow_html=True,
    )

    total_income = sum(t["amount"] for t in all_transactions if t["amount"] > 0)
    total_expense = abs(sum(t["amount"] for t in all_transactions if t["amount"] < 0))
    net = total_income - total_expense

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        metric_card(
            title="Transactions",
            value=str(len(all_transactions)),
            subtitle="Total records",
            color="#5B8DEF",
            bg="#EEF4FF",
            icon="📋",
        )
    with col2:
        metric_card(
            title="Total Income",
            value=f"₹{total_income:,.2f}",
            subtitle="Received",
            color="#43A87B",
            bg="#EEFAF4",
            icon="📥",
        )
    with col3:
        metric_card(
            title="Total Expense",
            value=f"₹{total_expense:,.2f}",
            subtitle="Spent",
            color="#F26C6C",
            bg="#FFF4EE",
            icon="📤",
        )
    with col4:
        net_color = "#43A87B" if net >= 0 else "#F26C6C"
        net_bg = "#EEFAF4" if net >= 0 else "#FFF4EE"
        metric_card(
            title="Net",
            value=f"₹{net:,.2f}",
            subtitle="Savings" if net >= 0 else "Deficit",
            color=net_color,
            bg=net_bg,
            icon="💰",
        )

    st.markdown("---")

    # Visualization
    if all_transactions:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                '<h3 style="color:#1A1A2E; font-size:1.1rem; font-weight:600; margin:1rem 0 1rem 0;">📉 Daily Trend</h3>',
                unsafe_allow_html=True,
            )

            # Group by date
            df = pd.DataFrame(all_transactions)
            df["date_only"] = pd.to_datetime(df["date"]).dt.date

            daily = df.groupby("date_only").agg({"amount": "sum"}).reset_index()

            fig = px.area(
                daily,
                x="date_only",
                y="amount",
                title="",
                labels={"date_only": "Date", "amount": "Amount (₹)"},
                color_discrete_sequence=["#5B8DEF"],
            )
            fig.update_layout(
                height=300, margin=dict(l=20, r=20, t=20, b=20), template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(
                '<h3 style="color:#1A1A2E; font-size:1.1rem; font-weight:600; margin:1rem 0 1rem 0;">📊 By Type</h3>',
                unsafe_allow_html=True,
            )

            type_summary = (
                df.groupby("type").agg({"amount": lambda x: abs(x).sum()}).reset_index()
            )

            fig = px.pie(
                type_summary,
                values="amount",
                names="type",
                color_discrete_sequence=["#43A87B", "#F26C6C"],
            )
            fig.update_layout(
                height=300, margin=dict(l=20, r=20, t=20, b=20), template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Transaction Table
    st.markdown(
        '<h3 style="color:#1A1A2E; font-size:1.1rem; font-weight:600; margin:1rem 0 1rem 0;">📜 Transaction History</h3>',
        unsafe_allow_html=True,
    )

    if all_transactions:
        # Search
        search = st.text_input(
            "🔍 Search transactions",
            placeholder="Search by category, description, or merchant...",
        )

        filtered_transactions = all_transactions
        if search:
            search_lower = search.lower()
            filtered_transactions = [
                t
                for t in all_transactions
                if search_lower in t["category"].lower()
                or search_lower in str(t["description"]).lower()
                or search_lower in str(t["merchant"]).lower()
                or search_lower in str(t["subcategory"]).lower()
            ]

        # Display
        if filtered_transactions:
            df_data = []
            for t in filtered_transactions:
                df_data.append(
                    {
                        "Date": t["date"][:16],
                        "Type": f"{t['icon']} {t['type']}",
                        "Category": t["category"],
                        "Description": t["description"] or t["subcategory"] or "-",
                        "Amount": f"₹{abs(t['amount']):,.2f}"
                        if t["amount"] < 0
                        else f"+₹{t['amount']:,.2f}",
                        "Payment": t["payment_mode"] or "-",
                    }
                )

            df = pd.DataFrame(df_data)

            # Pagination
            items_per_page = 20
            total_pages = max(1, (len(df) + items_per_page - 1) // items_per_page)

            page = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page

            st.dataframe(df.iloc[start_idx:end_idx], width="stretch", hide_index=True)
            st.caption(
                f"Showing {start_idx + 1}-{min(end_idx, len(df))} of {len(df)} transactions"
            )

            # Export
            st.markdown("---")
            if st.button("📥 Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"transactions_{start_date}_to_{end_date}.csv",
                    mime="text/csv",
                )
        else:
            st.info("No transactions match your search.")
    else:
        st.markdown(
            """
        <div style="background:#FFFFFF; border-radius:16px; padding:3rem; text-align:center; box-shadow:0 2px 12px rgba(0,0,0,0.07); border:1px solid #E8ECF0;">
            <div style="font-size:2rem;">📊</div>
            <p style="color:#6B7280; margin-top:0.5rem;">No transactions found</p>
            <p style="color:#6B7280; font-size:0.9rem;">Try adjusting your filters</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
