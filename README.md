# 💰 Smart Finance Tracker

A production-level personal finance management application built with Python, SQLite3, and Streamlit.

## 🌟 Features

### User Features
- **🔐 Secure Authentication** - bcrypt password hashing, login attempt tracking, account lockout
- **💳 Wallet Management** - Add income, track expenses, transfer money
- **🏦 Bank Account Linking** - Connect multiple bank accounts with balance tracking
- **📊 Transaction History** - Comprehensive filtering and search
- **📋 Budget Management** - Set category-wise budgets with alerts
- **🎯 Financial Goals** - Create and track savings goals
- **📈 Investment Portfolio** - Buy/sell stocks, crypto, mutual funds with real-time simulation
- **📉 Personal Analytics** - Financial health score, spending trends, category breakdown
- **🤖 AI Assistant** - Natural language queries for financial insights

### Admin Features
- **👥 User Management** - View, search, block/unblock users
- **💰 Transaction Monitoring** - Platform-wide transaction visibility
- **🚨 Fraud Detection** - Configurable rules, alerts, and manual review
- **📊 Platform Analytics** - Growth metrics, user behavior, investment distribution
- **📈 Market Management** - Add assets, update prices, manage volatility
- **📜 Audit Logs** - Complete system activity logging

## 🛠️ Tech Stack

- **Backend**: Python 3.9+
- **Database**: SQLite3 (with WAL mode for concurrency)
- **Frontend**: Streamlit
- **Charts**: Plotly
- **Auth**: bcrypt
- **DSA**: Custom Stack/Queue implementations for transaction management

## 📁 Project Structure

```
fintech_app/
├── app.py                  # Main Streamlit application
├── setup.py                # Database initialization script
├── requirements.txt        # Python dependencies
│
├── database/
│   ├── __init__.py
│   ├── db.py              # Database manager (SQLite3)
│   └── schema.sql         # Complete database schema
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py    # Authentication & authorization
│   ├── wallet_service.py  # Transaction-safe financial operations
│   ├── investment_service.py  # Investment & market operations
│   ├── analytics_service.py   # User & admin analytics
│   └── ai_assistant.py    # Natural language assistant
│
├── pages/
│   ├── __init__.py
│   ├── dashboard.py       # User dashboard
│   ├── wallet.py          # Wallet operations
│   ├── transactions.py    # Transaction history
│   ├── budgets.py         # Budget management
│   ├── goals.py           # Financial goals
│   ├── investments.py     # Investment portfolio
│   ├── user_analytics.py  # Personal analytics
│   ├── ai_chat.py         # AI assistant interface
│   ├── settings.py        # User settings
│   ├── admin_dashboard.py # Admin overview
│   ├── admin_users.py     # User management
│   ├── admin_transactions.py  # Transaction monitor
│   ├── admin_fraud.py     # Fraud detection
│   ├── admin_analytics.py # Platform analytics
│   ├── admin_market.py    # Market management
│   └── admin_logs.py      # Audit logs
│
└── data/
    └── fintech.db         # SQLite database (auto-created)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd fintech_app
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python setup.py
```

This creates:
- SQLite database with all tables
- Default admin account
- Demo user with ₹50,000 balance
- Market assets (stocks, crypto, mutual funds)

### 3. Run the Application

```bash
streamlit run app.py
```

### 4. Access the App

Open http://localhost:8501 in your browser.

**Default Credentials:**
- **Admin**: admin@fintrack.com / Admin@123
- **Demo User**: demo@fintrack.com / Demo@123

## 🔒 Security Features

1. **Password Security**
   - bcrypt hashing with salt
   - Minimum 8 characters with complexity requirements
   - Account lockout after 5 failed attempts

2. **Session Management**
   - Secure session tokens
   - Automatic session expiration
   - Login activity logging

3. **Data Protection**
   - Parameterized SQL queries (no SQL injection)
   - User data isolation (ownership checks)
   - Audit logging for all actions

4. **Transaction Safety**
   - Atomic database operations
   - Balance integrity checks
   - Fraud detection rules

## 📊 Data Visualization

The app includes extensive charts:

### User Side
- Monthly income vs expense trend
- Spending by category (pie/treemap)
- Budget vs actual comparison
- Daily spending patterns
- Savings rate trend
- Investment portfolio allocation
- Financial health score gauge

### Admin Side
- Platform growth (users, volume)
- Top spending categories
- Investment distribution
- User behavior patterns
- Fraud alerts visualization

## 🤖 AI Assistant

Natural language queries supported:
- "Show my balance"
- "How much did I spend on food this month?"
- "Show my budget status"
- "Give me saving tips"
- "Analyze my finances"
- "Show my investment portfolio"

## 💾 Database Schema

### Key Tables
- `users` - User accounts with wallet balance
- `admins` - Admin accounts with roles
- `bank_accounts` - Linked bank accounts
- `expenses` - Expense transactions
- `income` - Income transactions
- `budgets` - Category-wise budget limits
- `financial_goals` - Savings goals
- `market_assets` - Stocks, crypto, mutual funds
- `user_investments` - User portfolios
- `fraud_flags` - Fraud alerts
- `audit_logs` - System activity logs

### Data Storage
- All amounts stored in **paise** (integer) for precision
- Converted to rupees only for display
- Timestamps in ISO format

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file:

```env
DATABASE_PATH=./data/fintech.db
DEBUG=false
```

### Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#667eea"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"

[server]
port = 8501
```

## 📈 Scaling Considerations

For production deployment:

1. **Database**: Migrate to PostgreSQL for heavy load
2. **Authentication**: Add JWT tokens, refresh tokens
3. **API Layer**: Add FastAPI backend
4. **Caching**: Use Redis for session/analytics cache
5. **Monitoring**: Add logging/APM tools

## 🧪 Testing

```bash
# Run tests (when available)
pytest tests/
```

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

For issues or questions, create a GitHub issue.

---

Built with ❤️ using Python, SQLite3, and Streamlit
