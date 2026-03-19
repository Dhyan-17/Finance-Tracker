# Smart Finance Tracker

A personal finance management application built with Python, SQLite3, and Streamlit.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9+ |
| Database | SQLite3 (WAL mode) |
| Frontend | Streamlit |
| Charts | Plotly |
| Authentication | bcrypt |
| Data Processing | pandas, numpy |

## Features

### User
- Secure login with bcrypt password hashing (12 rounds) and account lockout after 5 failed attempts
- Wallet management — add income and track expenses
- Transaction history with filtering and search
- Category-wise budget management with alerts
- Financial goals with savings tracking and contributions
- Investment portfolio — buy/sell stocks, crypto, mutual funds, ETFs, bonds, and gold with simulated prices
- Personal analytics — spending trends, category breakdown, and financial health score

### Admin
- User management — view and search registered users
- Market management — add assets, update prices, manage volatility
- Audit logs — complete system activity logging

## Project Structure

```
fintech_app/
├── app.py                      # Main Streamlit entry point
├── setup.py                    # Database initialization
├── requirements.txt            # Python dependencies
├── run.bat                     # Windows startup script
│
├── database/
│   ├── db.py                   # Thread-safe SQLite3 database manager
│   ├── schema.sql              # Full database schema (17 tables)
│   ├── seed_data.py            # Market asset seed data
│   ├── seed_demo.py            # Demo user creation
│   └── migrate_schema.py       # Schema migration script
│
├── services/
│   ├── auth_service.py         # Authentication, sessions, input validation
│   ├── wallet_service.py       # Atomic financial operations
│   ├── investment_service.py   # Investment and market price simulation
│   └── analytics_service.py    # User and admin analytics
│
├── pages/
│   ├── dashboard.py            # User dashboard with balance summary
│   ├── wallet.py               # Add income and expenses
│   ├── transactions.py         # Transaction history with filters
│   ├── budgets.py              # Budget management with alerts
│   ├── goals.py                # Financial goals tracking
│   ├── investments.py          # Investment portfolio management
│   ├── user_analytics.py       # Personal analytics
│   ├── settings.py             # User settings
│   ├── admin_users.py          # Admin — user management
│   ├── admin_market.py         # Admin — market asset management
│   └── admin_logs.py           # Admin — audit logs
│
├── utils/
│   └── dsa_utils.py            # Stack implementation for income tracking
│
└── .streamlit/
    └── config.toml             # Streamlit theme configuration
```

## Quick Start

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Initialize the database**
```bash
python setup.py
```

This creates the SQLite database, default admin account, a demo user with ₹50,000 balance, and market assets.

**3. Run the application**
```bash
streamlit run app.py
```

Or use the provided batch file:
```bash
run.bat
```

Open `http://localhost:8501` in your browser.

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@fintrack.com | Admin@123 |
| Demo User | demo@fintrack.com | Demo@123 |

## Database Schema

17 tables covering all application domains:

| Category | Tables |
|----------|--------|
| Accounts | `users`, `admins`, `sessions`, `login_attempts` |
| Wallet | `income`, `expenses`, `expense_categories`, `wallet_transactions` |
| Budgets & Goals | `budgets`, `financial_goals`, `goal_contributions` |
| Investments | `market_assets`, `market_price_history`, `user_investments`, `investment_transactions` |
| System | `audit_logs`, `notifications` |

All monetary amounts are stored in **paise** (integer) and converted to rupees only at display time. Timestamps use ISO format.

## Security

- Passwords hashed with bcrypt (12 rounds); minimum 8 characters with uppercase, lowercase, and digit requirements
- Account lockout for 3 minutes after 5 failed login attempts
- Session tokens are 32-character URL-safe strings with a 24-hour expiry
- Parameterized SQL queries throughout — no SQL injection surface
- Atomic database operations with balance integrity checks
- Full audit logging of all system actions
