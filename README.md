# Smart Finance Tracker

A personal finance management application built with Python, SQLite3, and Streamlit.

## Features

### User Features
- Secure authentication with bcrypt password hashing (12 rounds)
- Account lockout after 5 failed login attempts (3-minute lockout)
- Session management with 24-hour duration
- Wallet management - add income and track expenses
- Transaction history with filtering and search
- Budget management with category-wise limits and alerts
- Financial goals with savings tracking and contributions
- Investment portfolio - buy/sell stocks, crypto, mutual funds, ETFs, bonds, gold with simulated prices
- Personal analytics with spending trends and category breakdown

### Admin Features
- User management - view and search users
- Market management - add assets, update prices, manage volatility
- Audit logs - complete system activity logging

## Tech Stack

- **Backend**: Python 3.9+
- **Database**: SQLite3 (with WAL mode for concurrency)
- **Frontend**: Streamlit
- **Charts**: Plotly
- **Auth**: bcrypt
- **Data Processing**: pandas, numpy
- **HTTP**: requests
- **DSA**: Custom Stack implementation for income transaction tracking

## Project Structure

```
fintech_app/
├── app.py                  # Main Streamlit application entry point
├── setup.py                # Database initialization script
├── requirements.txt        # Python dependencies
├── run.bat                 # Windows startup script
│
├── database/
│   ├── __init__.py
│   ├── db.py               # SQLite3 database manager with thread-safe connections
│   ├── schema.sql          # Complete database schema (17 tables)
│   ├── seed_data.py       # Seed data generator for market assets
│   ├── seed_demo.py       # Demo user creation
│   └── migrate_schema.py  # Schema migration script
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py    # Authentication with bcrypt, sessions, validation
│   ├── wallet_service.py  # Transaction-safe financial operations with atomic updates
│   ├── investment_service.py  # Investment and market operations with price simulation
│   └── analytics_service.py   # User and admin analytics
│
├── pages/
│   ├── __init__.py
│   ├── dashboard.py       # User dashboard with balance summary
│   ├── wallet.py          # Wallet operations (add income/expense)
│   ├── transactions.py    # Transaction history with filters
│   ├── budgets.py         # Budget management with alerts
│   ├── goals.py           # Financial goals tracking
│   ├── investments.py     # Investment portfolio management
│   ├── user_analytics.py  # Personal analytics and spending trends
│   ├── settings.py        # User settings
│   ├── admin_users.py     # Admin user management
│   ├── admin_market.py    # Admin market asset management
│   └── admin_logs.py     # Admin audit logs
│
├── utils/
│   ├── __init__.py
│   └── dsa_utils.py       # Stack implementation for income transaction tracking
│
├── .streamlit/
│   └── config.toml        # Streamlit configuration
│
└── data/
    └── fintech.db         # SQLite database (auto-created)
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python setup.py
```

3. Run the application:
```bash
streamlit run app.py
```

Or use the provided batch file:
```bash
run.bat
```

The application will be available at http://localhost:8501

## Default Credentials

- **Admin**: admin@fintrack.com / Admin@123
- **Demo User**: demo@fintrack.com / Demo@123 (with ₹50,000 wallet balance)

## Database Schema

### Tables
- `users` - User accounts with wallet balance
- `admins` - Admin accounts with roles
- `sessions` - User/admin sessions
- `login_attempts` - Login attempt tracking
- `market_assets` - Stocks, crypto, mutual funds, ETFs, bonds, gold
- `market_price_history` - Historical price data
- `user_investments` - User investment portfolios
- `investment_transactions` - Buy/sell/dividend transactions
- `income` - Income transactions
- `expenses` - Expense transactions
- `expense_categories` - Expense categories
- `budgets` - Category-wise budget limits
- `financial_goals` - Savings goals
- `goal_contributions` - Goal contribution history
- `wallet_transactions` - Wallet balance history
- `audit_logs` - System activity logs
- `notifications` - User notifications

### Data Storage
- All amounts stored in paise (integer) for precision
- Converted to rupees only for display
- Timestamps in ISO format

## Security Features

1. **Password Security**
   - bcrypt hashing with 12 rounds
   - Minimum 8 characters with complexity requirements (uppercase, lowercase, digit)
   - Account lockout after 5 failed attempts (3-minute duration)

2. **Session Management**
   - Secure session tokens (32-character URL-safe)
   - 24-hour session duration
   - Login activity logging

3. **Input Validation**
   - Email format validation
   - Indian mobile number validation (10 digits, starts with 6-9)
   - Username validation (alphanumeric with underscore, 3-30 chars)

4. **Transaction Safety**
   - Atomic database operations
   - Balance integrity checks
   - Stack-based income tracking
