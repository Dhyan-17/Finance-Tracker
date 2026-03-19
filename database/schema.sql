-- ============================================================
-- FINTECH FINANCE TRACKER - CLEAN MINIMAL SCHEMA
-- Only columns actually used in the code
-- WALLET ONLY - NO BANK ACCOUNTS
-- ============================================================

-- Enable foreign keys and WAL mode
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    mobile TEXT UNIQUE NOT NULL,
    wallet_balance INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'BLOCKED', 'SUSPENDED')),
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile);

-- ============================================================
-- ADMINS
-- ============================================================

CREATE TABLE IF NOT EXISTS admins (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'ADMIN',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT
);

-- ============================================================
-- SESSIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('USER', 'ADMIN')),
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================
-- LOGIN ATTEMPTS
-- ============================================================

CREATE TABLE IF NOT EXISTS login_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    success INTEGER NOT NULL,
    attempt_time TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- MARKET ASSETS
-- ============================================================

CREATE TABLE IF NOT EXISTS market_assets (
    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_name TEXT UNIQUE NOT NULL,
    asset_symbol TEXT UNIQUE NOT NULL,
    asset_type TEXT NOT NULL CHECK (asset_type IN ('STOCK', 'MUTUAL_FUND', 'CRYPTO', 'ETF', 'BOND', 'GOLD')),
    current_price INTEGER NOT NULL,
    previous_price INTEGER,
    day_change_percent REAL DEFAULT 0,
    volatility_percent REAL DEFAULT 5.0,
    is_active INTEGER DEFAULT 1,
    last_updated TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_market_assets_type ON market_assets(asset_type);

-- ============================================================
-- MARKET PRICE HISTORY
-- ============================================================

CREATE TABLE IF NOT EXISTS market_price_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    price INTEGER NOT NULL,
    recorded_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id) ON DELETE CASCADE
);

-- ============================================================
-- USER INVESTMENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS user_investments (
    investment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    units_owned REAL NOT NULL,
    buy_price INTEGER NOT NULL,
    invested_amount INTEGER NOT NULL,
    purchase_date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id)
);

CREATE INDEX IF NOT EXISTS idx_user_investments ON user_investments(user_id, asset_id);

-- ============================================================
-- INVESTMENT TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS investment_transactions (
    txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    txn_type TEXT NOT NULL CHECK (txn_type IN ('BUY', 'SELL', 'DIVIDEND')),
    units REAL NOT NULL,
    price_per_unit INTEGER NOT NULL,
    total_amount INTEGER NOT NULL,
    source_account_type TEXT,
    source_account_id INTEGER,
    txn_date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id)
);

-- ============================================================
-- INCOME
-- ============================================================

CREATE TABLE IF NOT EXISTS income (
    income_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    source TEXT NOT NULL,
    category TEXT,
    description TEXT,
    account_type TEXT DEFAULT 'WALLET' CHECK (account_type IN ('WALLET')),
    date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_income_user_date ON income(user_id, date);

-- ============================================================
-- EXPENSE CATEGORIES
-- ============================================================

CREATE TABLE IF NOT EXISTS expense_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    icon TEXT,
    color TEXT,
    is_system INTEGER DEFAULT 1
);

-- ============================================================
-- EXPENSES
-- ============================================================

CREATE TABLE IF NOT EXISTS expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT,
    description TEXT,
    payment_mode TEXT DEFAULT 'UPI',
    account_type TEXT DEFAULT 'WALLET' CHECK (account_type IN ('WALLET')),
    merchant TEXT,
    date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(user_id, category, date);

-- ============================================================
-- BUDGETS
-- ============================================================

CREATE TABLE IF NOT EXISTS budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    limit_amount INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    alert_threshold REAL DEFAULT 80.0,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, category, year, month)
);

CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id, year, month);

-- ============================================================
-- FINANCIAL GOALS
-- ============================================================

CREATE TABLE IF NOT EXISTS financial_goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    goal_name TEXT NOT NULL,
    target_amount INTEGER NOT NULL,
    current_savings INTEGER DEFAULT 0,
    monthly_contribution INTEGER,
    target_date TEXT,
    priority TEXT DEFAULT 'MEDIUM',
    status TEXT DEFAULT 'ACTIVE',
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_goals_user ON financial_goals(user_id, status);

-- ============================================================
-- GOAL CONTRIBUTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS goal_contributions (
    contribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    source TEXT,
    source_account_id INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (goal_id) REFERENCES financial_goals(goal_id) ON DELETE CASCADE
);

-- ============================================================
-- WALLET TRANSACTIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS wallet_transactions (
    txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    txn_type TEXT NOT NULL CHECK (txn_type IN ('INCOME', 'EXPENSE', 'INVESTMENT', 'REFUND')),
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    reference_type TEXT,
    reference_id INTEGER,
    description TEXT,
    date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wallet_txn_user ON wallet_transactions(user_id, date);

-- ============================================================
-- AUDIT LOGS
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('USER', 'ADMIN', 'SYSTEM')),
    actor_id INTEGER,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    old_values TEXT,
    new_values TEXT,
    severity TEXT DEFAULT 'INFO',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_type, actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_logs(created_at);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'INFO',
    category TEXT,
    is_read INTEGER DEFAULT 0,
    action_url TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notifications ON notifications(user_id, is_read);

-- ============================================================
-- USER ANALYTICS CACHE
-- ============================================================

CREATE TABLE IF NOT EXISTS user_analytics_cache (
    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id UNIQUE NOT NULL,
    total_income INTEGER DEFAULT 0,
    total_expenses INTEGER DEFAULT 0,
    total_investments INTEGER DEFAULT 0,
    investment_current_value INTEGER DEFAULT 0,
    net_worth INTEGER DEFAULT 0,
    monthly_avg_income INTEGER DEFAULT 0,
    monthly_avg_expense INTEGER DEFAULT 0,
    savings_rate REAL DEFAULT 0,
    last_calculated TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================
-- INITIAL DATA
-- ============================================================

INSERT OR IGNORE INTO expense_categories (name, icon, color) VALUES
('Food & Dining', '🍔', '#FF6B6B'),
('Transportation', '🚗', '#4ECDC4'),
('Shopping', '🛒', '#45B7D1'),
('Entertainment', '🎬', '#96CEB4'),
('Bills & Utilities', '💡', '#FFEAA7'),
('Healthcare', '🏥', '#DDA0DD'),
('Education', '📚', '#98D8C8'),
('Travel', '✈️', '#F7DC6F'),
('Groceries', '🥦', '#82E0AA'),
('Personal Care', '💅', '#F8B500'),
('Investments', '📈', '#5DADE2'),
('Others', '📦', '#BDC3C7');

INSERT OR IGNORE INTO market_assets (asset_name, asset_symbol, asset_type, current_price, volatility_percent) VALUES
('Reliance Industries', 'RELIANCE', 'STOCK', 245000, 3.5),
('Tata Consultancy Services', 'TCS', 'STOCK', 385000, 2.8),
('Infosys', 'INFY', 'STOCK', 152000, 3.2),
('HDFC Bank', 'HDFCBANK', 'STOCK', 168000, 2.5),
('ICICI Bank', 'ICICIBANK', 'STOCK', 105000, 3.0),
('Bharti Airtel', 'BHARTIARTL', 'STOCK', 142000, 4.0),
('ITC Limited', 'ITC', 'STOCK', 46500, 2.2),
('Hindustan Unilever', 'HINDUNILVR', 'STOCK', 258000, 1.8),
('Wipro', 'WIPRO', 'STOCK', 45000, 3.5),
('Asian Paints', 'ASIANPAINT', 'STOCK', 285000, 2.0),
('Bitcoin', 'BTC', 'CRYPTO', 750000000, 8.5),
('Ethereum', 'ETH', 'CRYPTO', 35000000, 9.2),
('Solana', 'SOL', 'CRYPTO', 2200000, 12.0),
('Cardano', 'ADA', 'CRYPTO', 8500, 10.5),
('Polygon', 'MATIC', 'CRYPTO', 12000, 11.0),
('Axis Bluechip Fund', 'AXISBF', 'MUTUAL_FUND', 5250, 1.5),
('SBI Small Cap Fund', 'SBISCF', 'MUTUAL_FUND', 14580, 4.2),
('Mirae Asset Large Cap', 'MIRALC', 'MUTUAL_FUND', 8925, 2.0),
('HDFC Flexi Cap Fund', 'HDFCFC', 'MUTUAL_FUND', 158000, 2.8),
('Parag Parikh Flexi Cap', 'PPFAS', 'MUTUAL_FUND', 7500, 2.5),
('Digital Gold', 'GOLD', 'GOLD', 720000, 1.2);
