-- ============================================================
-- FINTECH FINANCE TRACKER - PRODUCTION SCHEMA v2.0
-- Production-grade banking + investment platform
-- ============================================================

-- Enable foreign keys and WAL mode for performance
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;

-- ============================================================
-- PART 1: USER SYSTEM (Hardened)
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL CHECK (length(username) >= 3 AND length(username) <= 30),
    password_hash TEXT NOT NULL CHECK (length(password_hash) >= 60),
    email TEXT UNIQUE NOT NULL COLLATE NOCASE CHECK (email LIKE '%@%.%'),
    mobile TEXT UNIQUE NOT NULL CHECK (length(mobile) = 10 AND mobile GLOB '[6-9][0-9]*'),
    wallet_balance INTEGER DEFAULT 0 CHECK (wallet_balance >= 0),
    wallet_uuid TEXT UNIQUE,
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'BLOCKED', 'SUSPENDED', 'PENDING_KYC')),
    kyc_verified INTEGER DEFAULT 0 CHECK (kyc_verified IN (0, 1)),
    kyc_level INTEGER DEFAULT 0 CHECK (kyc_level >= 0 AND kyc_level <= 3),
    profile_picture TEXT,
    email_verified INTEGER DEFAULT 0 CHECK (email_verified IN (0, 1)),
    mobile_verified INTEGER DEFAULT 0 CHECK (mobile_verified IN (0, 1)),
    two_factor_enabled INTEGER DEFAULT 0 CHECK (two_factor_enabled IN (0, 1)),
    created_at TEXT DEFAULT (datetime('now')),
    last_login TEXT,
    failed_login_attempts INTEGER DEFAULT 0 CHECK (failed_login_attempts >= 0),
    locked_until TEXT,
    last_activity TEXT,
    timezone TEXT DEFAULT 'Asia/Kolkata',
    notification_preferences TEXT,  -- JSON
    privacy_settings TEXT,  -- JSON
    created_by TEXT
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_mobile ON users(mobile);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_uuid ON users(uuid);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- ============================================================
-- PART 2: ADMIN SYSTEM
-- ============================================================

CREATE TABLE IF NOT EXISTS admins (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL CHECK (length(name) >= 2),
    email TEXT UNIQUE NOT NULL COLLATE NOCASE CHECK (email LIKE '%@%.%'),
    password_hash TEXT NOT NULL CHECK (length(password_hash) >= 60),
    role TEXT DEFAULT 'ADMIN' CHECK (role IN ('SUPER_ADMIN', 'ADMIN', 'ANALYST', 'SUPPORT', 'READONLY')),
    permissions TEXT,  -- JSON array
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_login TEXT,
    login_ip TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);

-- ============================================================
-- PART 3: BANK ACCOUNTS (Hardened)
-- ============================================================

CREATE TABLE IF NOT EXISTS master_banks (
    bank_id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank_name TEXT NOT NULL,
    ifsc_code TEXT UNIQUE NOT NULL CHECK (length(ifsc_code) = 11),
    branch_name TEXT,
    city TEXT,
    state TEXT,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    logo_url TEXT,
    website TEXT,
    customer_care TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_banks_ifsc ON master_banks(ifsc_code);
CREATE INDEX IF NOT EXISTS idx_banks_name ON master_banks(bank_name);

CREATE TABLE IF NOT EXISTS bank_accounts (
    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    bank_id INTEGER,
    bank_account_number TEXT UNIQUE NOT NULL CHECK (length(bank_account_number) BETWEEN 9 AND 18),
    account_holder TEXT NOT NULL,
    account_type TEXT DEFAULT 'SAVINGS' CHECK (account_type IN ('SAVINGS', 'CURRENT', 'SALARY', 'NRE', 'NRO')),
    balance INTEGER DEFAULT 0 CHECK (balance >= 0),
    upi_id TEXT UNIQUE COLLATE NOCASE CHECK (upi_id LIKE '%@%'),
    debit_card_last4 TEXT CHECK (length(debit_card_last4) = 4 OR debit_card_last4 IS NULL),
    credit_card_last4 TEXT CHECK (length(credit_card_last4) = 4 OR credit_card_last4 IS NULL),
    credit_card_limit INTEGER DEFAULT 0 CHECK (credit_card_limit >= 0),
    is_primary INTEGER DEFAULT 0 CHECK (is_primary IN (0, 1)),
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    verified_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (bank_id) REFERENCES master_banks(bank_id)
);

CREATE INDEX IF NOT EXISTS idx_bank_accounts_user ON bank_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_number ON bank_accounts(bank_account_number);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_upi ON bank_accounts(upi_id);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_primary ON bank_accounts(user_id, is_primary);

-- ============================================================
-- PART 4: MARKET & INVESTMENTS (Hardened)
-- ============================================================

CREATE TABLE IF NOT EXISTS market_assets (
    asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    asset_name TEXT UNIQUE NOT NULL,
    asset_symbol TEXT UNIQUE NOT NULL CHECK (length(asset_symbol) BETWEEN 2 AND 10),
    asset_type TEXT NOT NULL CHECK (asset_type IN ('STOCK', 'MUTUAL_FUND', 'CRYPTO', 'ETF', 'BOND', 'GOLD', 'SILVER', 'COMMODITY', 'REAL_ESTATE')),
    current_price INTEGER NOT NULL CHECK (current_price > 0),
    previous_price INTEGER,
    day_change_percent REAL DEFAULT 0 CHECK (day_change_percent >= -100 AND day_change_percent <= 1000),
    week_high INTEGER,
    week_low INTEGER,
    month_high INTEGER,
    month_low INTEGER,
    volatility_percent REAL DEFAULT 5.0 CHECK (volatility_percent >= 0),
    market_cap INTEGER,
    volume INTEGER,
    pe_ratio REAL,
    dividend_yield REAL CHECK (dividend_yield >= 0),
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    last_updated TEXT DEFAULT (datetime('now')),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_market_assets_type ON market_assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_market_assets_symbol ON market_assets(asset_symbol);
CREATE INDEX IF NOT EXISTS idx_market_assets_active ON market_assets(is_active, asset_type);

CREATE TABLE IF NOT EXISTS market_price_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    price INTEGER NOT NULL CHECK (price > 0),
    volume INTEGER DEFAULT 0,
    high INTEGER,
    low INTEGER,
    open_price INTEGER,
    recorded_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_price_history_asset ON market_price_history(asset_id, recorded_at);

CREATE TABLE IF NOT EXISTS user_investments (
    investment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    units_owned REAL NOT NULL CHECK (units_owned > 0),
    buy_price INTEGER NOT NULL CHECK (buy_price > 0),
    average_cost INTEGER NOT NULL CHECK (average_cost > 0),
    invested_amount INTEGER NOT NULL CHECK (invested_amount > 0),
    current_value INTEGER DEFAULT 0,
    profit_loss INTEGER DEFAULT 0,
    profit_loss_percent REAL DEFAULT 0,
    purchase_date TEXT DEFAULT (datetime('now')),
    last_price_update TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id)
);

CREATE INDEX IF NOT EXISTS idx_user_investments ON user_investments(user_id, asset_id);
CREATE INDEX IF NOT EXISTS idx_user_investments_uuid ON user_investments(uuid);

CREATE TABLE IF NOT EXISTS investment_transactions (
    txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    asset_id INTEGER NOT NULL,
    investment_id INTEGER,
    txn_type TEXT NOT NULL CHECK (txn_type IN ('BUY', 'SELL', 'DIVIDEND', 'BONUS', 'SPLIT', 'TRANSFER_IN', 'TRANSFER_OUT')),
    units REAL NOT NULL CHECK (units != 0),
    price_per_unit INTEGER NOT NULL CHECK (price_per_unit > 0),
    total_amount INTEGER NOT NULL CHECK (total_amount != 0),
    brokerage INTEGER DEFAULT 0,
    taxes INTEGER DEFAULT 0,
    source_account_type TEXT CHECK (source_account_type IN ('WALLET', 'BANK', 'UPI')),
    source_account_id INTEGER,
    settlement_date TEXT,
    txn_date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id),
    FOREIGN KEY (investment_id) REFERENCES user_investments(investment_id)
);

CREATE INDEX IF NOT EXISTS idx_investment_txn ON investment_transactions(user_id, txn_date);
CREATE INDEX IF NOT EXISTS idx_investment_txn_uuid ON investment_transactions(uuid);

-- ============================================================
-- PART 5: INCOME & EXPENSES (Hardened)
-- ============================================================

CREATE TABLE IF NOT EXISTS income (
    income_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    source TEXT NOT NULL,
    category TEXT,
    description TEXT,
    account_type TEXT DEFAULT 'WALLET' CHECK (account_type IN ('WALLET', 'BANK', 'UPI', 'CASH', 'INVESTMENT')),
    account_id INTEGER,
    date TEXT DEFAULT (datetime('now')),
    is_recurring INTEGER DEFAULT 0 CHECK (is_recurring IN (0, 1)),
    recurring_frequency TEXT CHECK (recurring_frequency IN ('DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')),
    reference_number TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_income_user_date ON income(user_id, date);
CREATE INDEX IF NOT EXISTS idx_income_source ON income(user_id, source);
CREATE INDEX IF NOT EXISTS idx_income_uuid ON income(uuid);

CREATE TABLE IF NOT EXISTS expense_categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    icon TEXT,
    color TEXT,
    budget_default INTEGER CHECK (budget_default >= 0),
    is_system INTEGER DEFAULT 1 CHECK (is_system IN (0, 1)),
    parent_category TEXT,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    category TEXT NOT NULL,
    subcategory TEXT,
    description TEXT,
    payment_mode TEXT DEFAULT 'UPI' CHECK (payment_mode IN ('CASH', 'UPI', 'DEBIT_CARD', 'CREDIT_CARD', 'NET_BANKING', 'WALLET', 'OTHER')),
    account_type TEXT DEFAULT 'WALLET' CHECK (account_type IN ('WALLET', 'BANK', 'UPI', 'CASH')),
    account_id INTEGER,
    merchant TEXT,
    location TEXT,
    latitude REAL CHECK (latitude >= -90 AND latitude <= 90),
    longitude REAL CHECK (longitude >= -180 AND longitude <= 180),
    date TEXT DEFAULT (datetime('now')),
    is_recurring INTEGER DEFAULT 0 CHECK (is_recurring IN (0, 1)),
    recurring_frequency TEXT CHECK (recurring_frequency IN ('DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY')),
    receipt_url TEXT,
    tags TEXT,  -- JSON array
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(user_id, category, date);
CREATE INDEX IF NOT EXISTS idx_expenses_uuid ON expenses(uuid);
CREATE INDEX IF NOT EXISTS idx_expenses_merchant ON expenses(merchant);

-- ============================================================
-- PART 6: BUDGETS & GOALS
-- ============================================================

CREATE TABLE IF NOT EXISTS budgets (
    budget_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    limit_amount INTEGER NOT NULL CHECK (limit_amount > 0),
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    alert_threshold REAL DEFAULT 80.0 CHECK (alert_threshold >= 0 AND alert_threshold <= 100),
    notifications_enabled INTEGER DEFAULT 1 CHECK (notifications_enabled IN (0, 1)),
    carryover_unused INTEGER DEFAULT 0 CHECK (carryover_unused IN (0, 1)),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE(user_id, category, year, month)
);

CREATE INDEX IF NOT EXISTS idx_budgets_user ON budgets(user_id, year, month);
CREATE INDEX IF NOT EXISTS idx_budgets_uuid ON budgets(uuid);

CREATE TABLE IF NOT EXISTS financial_goals (
    goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    goal_name TEXT NOT NULL CHECK (length(goal_name) >= 3),
    target_amount INTEGER NOT NULL CHECK (target_amount > 0),
    current_savings INTEGER DEFAULT 0 CHECK (current_savings >= 0),
    monthly_contribution INTEGER CHECK (monthly_contribution >= 0),
    target_date TEXT,
    priority TEXT DEFAULT 'MEDIUM' CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'COMPLETED', 'PAUSED', 'CANCELLED', 'EXPIRED')),
    icon TEXT,
    color TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_goals_user ON financial_goals(user_id, status);
CREATE INDEX IF NOT EXISTS idx_goals_uuid ON financial_goals(uuid);

CREATE TABLE IF NOT EXISTS goal_contributions (
    contribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    goal_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    source TEXT,
    note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (goal_id) REFERENCES financial_goals(goal_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_goal_contributions ON goal_contributions(goal_id);
CREATE INDEX IF NOT EXISTS idx_goal_contributions_uuid ON goal_contributions(uuid);

-- ============================================================
-- PART 7: TRANSACTIONS & TRANSFERS (Hardened)
-- ============================================================

CREATE TABLE IF NOT EXISTS wallet_transactions (
    txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    txn_type TEXT NOT NULL CHECK (txn_type IN ('INCOME', 'EXPENSE', 'TRANSFER_IN', 'TRANSFER_OUT', 'INVESTMENT', 'REFUND', 'FEES', 'ADJUSTMENT', 'BONUS')),
    amount INTEGER NOT NULL CHECK (amount != 0),
    balance_after INTEGER NOT NULL CHECK (balance_after >= 0),
    reference_type TEXT,
    reference_id INTEGER,
    reference_uuid TEXT,
    description TEXT,
    idempotency_key TEXT UNIQUE,
    date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_wallet_txn_user ON wallet_transactions(user_id, date);
CREATE INDEX IF NOT EXISTS idx_wallet_txn_uuid ON wallet_transactions(uuid);
CREATE INDEX IF NOT EXISTS idx_wallet_txn_type ON wallet_transactions(user_id, txn_type);
CREATE INDEX IF NOT EXISTS idx_wallet_idempotency ON wallet_transactions(idempotency_key);

CREATE TABLE IF NOT EXISTS transfers (
    transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    amount INTEGER NOT NULL CHECK (amount > 0),
    note TEXT,
    status TEXT DEFAULT 'COMPLETED' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'REVERSED', 'CANCELLED')),
    upi_ref_id TEXT,
    bank_ref_id TEXT,
    transfer_mode TEXT DEFAULT 'INTERNAL' CHECK (transfer_mode IN ('INTERNAL', 'UPI', 'IMPS', 'NEFT', 'RTGS')),
    fees INTEGER DEFAULT 0 CHECK (fees >= 0),
    initiated_at TEXT DEFAULT (datetime('now')),
    completed_at TEXT,
    failed_reason TEXT,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_transfers_sender ON transfers(sender_id, date);
CREATE INDEX IF NOT EXISTS idx_transfers_receiver ON transfers(receiver_id, date);
CREATE INDEX IF NOT EXISTS idx_transfers_uuid ON transfers(uuid);
CREATE INDEX IF NOT EXISTS idx_transfers_status ON transfers(status);

CREATE TABLE IF NOT EXISTS bank_transactions (
    txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    account_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    txn_type TEXT NOT NULL CHECK (txn_type IN ('INCOME', 'EXPENSE', 'TRANSFER_IN', 'TRANSFER_OUT', 'FEE', 'INTEREST', 'REVERSAL')),
    amount INTEGER NOT NULL CHECK (amount != 0),
    balance_after INTEGER NOT NULL CHECK (balance_after >= 0),
    category TEXT,
    description TEXT,
    reference_number TEXT,
    bank_reference TEXT,
    date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (account_id) REFERENCES bank_accounts(account_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bank_txn ON bank_transactions(account_id, date);
CREATE INDEX IF NOT EXISTS idx_bank_txn_uuid ON bank_transactions(uuid);
CREATE INDEX IF NOT EXISTS idx_bank_txn_user ON bank_transactions(user_id, date);

-- ============================================================
-- PART 8: AUDIT & SECURITY (Hardened)
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    actor_type TEXT NOT NULL CHECK (actor_type IN ('USER', 'ADMIN', 'SYSTEM', 'API', 'SCHEDULER')),
    actor_id INTEGER,
    actor_uuid TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    entity_uuid TEXT,
    old_values TEXT,
    new_values TEXT,
    ip_address TEXT,
    user_agent TEXT,
    device_id TEXT,
    location TEXT,
    severity TEXT DEFAULT 'INFO' CHECK (severity IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'SECURITY')),
    created_at TEXT DEFAULT (datetime('now')),
    indexed_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_type, actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_audit_uuid ON audit_logs(uuid);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);

CREATE TABLE IF NOT EXISTS login_attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    success INTEGER NOT NULL CHECK (success IN (0, 1)),
    ip_address TEXT,
    user_agent TEXT,
    device_id TEXT,
    location TEXT,
    failure_reason TEXT,
    attempt_time TEXT DEFAULT (datetime('now')),
    captcha_verified INTEGER DEFAULT 0 CHECK (captcha_verified IN (0, 1))
);

CREATE INDEX IF NOT EXISTS idx_login_attempts ON login_attempts(email, attempt_time);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address, attempt_time);
CREATE INDEX IF NOT EXISTS idx_login_attempts_uuid ON login_attempts(uuid);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    user_id INTEGER NOT NULL,
    user_type TEXT NOT NULL CHECK (user_type IN ('USER', 'ADMIN')),
    ip_address TEXT,
    user_agent TEXT,
    device_id TEXT,
    location TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    last_activity TEXT,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

-- ============================================================
-- PART 9: FRAUD DETECTION (Hardened)
-- ============================================================

CREATE TABLE IF NOT EXISTS fraud_flags (
    flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    rule_name TEXT NOT NULL,
    rule_id INTEGER,
    severity TEXT DEFAULT 'MEDIUM' CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description TEXT,
    reference_type TEXT,
    reference_id INTEGER,
    reference_uuid TEXT,
    amount INTEGER,
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'REVIEWED', 'CLEARED', 'CONFIRMED', 'ESCALATED')),
    reviewed_by INTEGER,
    reviewed_at TEXT,
    review_notes TEXT,
    action_taken TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fraud_flags ON fraud_flags(user_id, status);
CREATE INDEX IF NOT EXISTS idx_fraud_flags_uuid ON fraud_flags(uuid);
CREATE INDEX IF NOT EXISTS idx_fraud_flags_severity ON fraud_flags(severity, status);

CREATE TABLE IF NOT EXISTS fraud_rules (
    rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    rule_name TEXT UNIQUE NOT NULL,
    rule_type TEXT NOT NULL CHECK (rule_type IN ('AMOUNT', 'FREQUENCY', 'PATTERN', 'VELOCITY', 'LOCATION', 'DEVICE', 'BEHAVIOR', 'BLACKLIST')),
    threshold_value REAL,
    threshold_type TEXT,
    threshold_operator TEXT DEFAULT 'GT' CHECK (threshold_operator IN ('GT', 'LT', 'EQ', 'GTE', 'LTE', 'BETWEEN')),
    severity TEXT DEFAULT 'MEDIUM',
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    description TEXT,
    remediation_action TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS blacklists (
    blacklist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK (type IN ('IP', 'DEVICE', 'EMAIL', 'PHONE', 'ACCOUNT', 'UPI', 'BANK_ACCOUNT')),
    value TEXT NOT NULL,
    reason TEXT,
    expires_at TEXT,
    created_by INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_blacklists ON blacklists(type, value);

-- ============================================================
-- PART 10: NOTIFICATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'INFO' CHECK (notification_type IN ('INFO', 'WARNING', 'ALERT', 'SUCCESS', 'ERROR')),
    category TEXT,
    priority TEXT DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
    is_read INTEGER DEFAULT 0 CHECK (is_read IN (0, 1)),
    read_at TEXT,
    action_url TEXT,
    action_text TEXT,
    metadata TEXT,  -- JSON
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_notifications ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_uuid ON notifications(uuid);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);

-- ============================================================
-- PART 11: AI ASSISTANT
-- ============================================================

CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    messages TEXT NOT NULL,  -- JSON array
    context TEXT,  -- JSON object
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ai_conversations ON ai_conversations(user_id, updated_at);

CREATE TABLE IF NOT EXISTS ai_insights (
    insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL DEFAULT (lower(hex(randomblob(16)))),
    user_id INTEGER NOT NULL,
    insight_type TEXT NOT NULL CHECK (insight_type IN ('SPENDING', 'INCOME', 'SAVINGS', 'BUDGET', 'INVESTMENT', 'GOAL', 'FRAUD', 'HEALTH', 'TIP', 'ALERT')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    priority TEXT DEFAULT 'NORMAL' CHECK (priority IN ('LOW', 'NORMAL', 'HIGH')),
    is_dismissed INTEGER DEFAULT 0 CHECK (is_dismissed IN (0, 1)),
    dismissed_at TEXT,
    action_url TEXT,
    metadata TEXT,  -- JSON
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_ai_insights ON ai_insights(user_id, is_dismissed, created_at);
CREATE INDEX IF NOT EXISTS idx_ai_insights_uuid ON ai_insights(uuid);

-- ============================================================
-- PART 12: ANALYTICS CACHE
-- ============================================================

CREATE TABLE IF NOT EXISTS user_analytics_cache (
    cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    total_income INTEGER DEFAULT 0,
    total_expenses INTEGER DEFAULT 0,
    total_investments INTEGER DEFAULT 0,
    investment_current_value INTEGER DEFAULT 0,
    investment_profit_loss INTEGER DEFAULT 0,
    net_worth INTEGER DEFAULT 0,
    monthly_avg_income INTEGER DEFAULT 0,
    monthly_avg_expense INTEGER DEFAULT 0,
    savings_rate REAL DEFAULT 0 CHECK (savings_rate >= -100),
    financial_health_score INTEGER DEFAULT 0 CHECK (financial_health_score >= 0 AND financial_health_score <= 100),
    top_category TEXT,
    last_transaction_date TEXT,
    streak_days INTEGER DEFAULT 0,
    last_calculated TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_analytics_cache ON user_analytics_cache(last_calculated);

-- ============================================================
-- PART 13: KYC & IDENTITY
-- ============================================================

CREATE TABLE IF NOT EXISTS kyc_records (
    kyc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    kyc_type TEXT NOT NULL CHECK (kyc_type IN ('AADHAR', 'PAN', 'PASSPORT', 'DRIVING_LICENSE', 'VOTER_ID', 'BANK_ACCOUNT', 'UPI')),
    document_number TEXT,  -- HASHED
    document_hash TEXT NOT NULL,
    document_front TEXT,  -- URL
    document_back TEXT,  -- URL
    selfie TEXT,  -- URL
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'IN_REVIEW', 'VERIFIED', 'REJECTED', 'EXPIRED')),
    rejection_reason TEXT,
    verified_by INTEGER,
    verified_at TEXT,
    expiry_date TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_kyc_user ON kyc_records(user_id, status);
CREATE INDEX IF NOT EXISTS idx_kyc_uuid ON kyc_records(uuid);

-- ============================================================
-- INITIAL DATA
-- ============================================================

-- Default expense categories
INSERT OR IGNORE INTO expense_categories (name, icon, color, budget_default, sort_order) VALUES
('Food & Dining', '🍽️', '#FF6B6B', 10000, 1),
('Transportation', '🚗', '#4ECDC4', 5000, 2),
('Shopping', '🛍️', '#45B7D1', 8000, 3),
('Entertainment', '🎬', '#96CEB4', 3000, 4),
('Bills & Utilities', '📱', '#FFEAA7', 5000, 5),
('Healthcare', '🏥', '#DDA0DD', 3000, 6),
('Education', '📚', '#98D8C8', 5000, 7),
('Travel', '✈️', '#F7DC6F', 10000, 8),
('Groceries', '🛒', '#82E0AA', 8000, 9),
('Personal Care', '💅', '#F8B500', 2000, 10),
('Investments', '📈', '#5DADE2', 15000, 11),
('Subscriptions', '📺', '#A569BD', 2000, 12),
('Gifts & Donations', '🎁', '#EC7063', 3000, 13),
('Others', '📦', '#BDC3C7', 5000, 14);

-- Default banks
INSERT OR IGNORE INTO master_banks (bank_name, ifsc_code, city, state, website, customer_care) VALUES
('State Bank of India', 'SBIN0000001', 'Mumbai', 'Maharashtra', 'https://sbi.co.in', '1800 1234'),
('HDFC Bank', 'HDFC0000001', 'Mumbai', 'Maharashtra', 'https://hdfcbank.com', '1800 1230'),
('ICICI Bank', 'ICIC0000001', 'Mumbai', 'Maharashtra', 'https://icicibank.com', '1800 1231'),
('Axis Bank', 'UTIB0000001', 'Mumbai', 'Maharashtra', 'https://axisbank.com', '1800 1232'),
('Kotak Mahindra Bank', 'KKBK0000001', 'Mumbai', 'Maharashtra', 'https://kotak.com', '1800 1234'),
('Punjab National Bank', 'PUNB0000001', 'New Delhi', 'Delhi', 'https://pnbindia.in', '1800 1234'),
('Bank of Baroda', 'BARB0000001', 'Vadodara', 'Gujarat', 'https://bankofbaroda.in', '1800 1234'),
('Yes Bank', 'YESB0000001', 'Mumbai', 'Maharashtra', 'https://yesbank.in', '1800 1234'),
('IndusInd Bank', 'INDB0000001', 'Mumbai', 'Maharashtra', 'https://indusind.com', '1800 1234'),
('Federal Bank', 'FDRL0000001', 'Kochi', 'Kerala', 'www.federalbank.co.in', '1800 1234'),
('Canara Bank', 'CNRB0000001', 'Bangalore', 'Karnataka', 'https://canarabank.com', '1800 1234'),
('Union Bank of India', 'UBIN0000001', 'Mumbai', 'Maharashtra', 'https://unionbankofindia.co.in', '1800 1234');

-- Default market assets (prices in paise)
INSERT OR IGNORE INTO market_assets (asset_name, asset_symbol, asset_type, current_price, volatility_percent, market_cap) VALUES
-- Indian Stocks
('Reliance Industries', 'RELIANCE', 'STOCK', 245000, 3.5, 15000000000000),
('Tata Consultancy Services', 'TCS', 'STOCK', 385000, 2.8, 14000000000000),
('Infosys', 'INFY', 'STOCK', 152000, 3.2, 6500000000000),
('HDFC Bank', 'HDFCBANK', 'STOCK', 168000, 2.5, 12000000000000),
('ICICI Bank', 'ICICIBANK', 'STOCK', 105000, 3.0, 7500000000000),
('Bharti Airtel', 'BHARTIARTL', 'STOCK', 142000, 4.0, 8000000000000),
('ITC Limited', 'ITC', 'STOCK', 46500, 2.2, 5500000000000),
('Hindustan Unilever', 'HINDUNILVR', 'STOCK', 258000, 1.8, 6000000000000),
('Wipro', 'WIPRO', 'STOCK', 45000, 3.5, 2500000000000),
('Asian Paints', 'ASIANPAINT', 'STOCK', 285000, 2.0, 3000000000000),
-- Crypto (prices in paise - INR equivalent)
('Bitcoin', 'BTC', 'CRYPTO', 750000000, 8.5, 150000000000000),
('Ethereum', 'ETH', 'CRYPTO', 35000000, 9.2, 40000000000000),
('Solana', 'SOL', 'CRYPTO', 2200000, 12.0, 10000000000000),
('Cardano', 'ADA', 'CRYPTO', 8500, 10.5, 3000000000000),
('Polygon', 'MATIC', 'CRYPTO', 12000, 11.0, 1000000000000),
-- Mutual Funds
('Axis Bluechip Fund', 'AXISBF', 'MUTUAL_FUND', 5250, 1.5, 500000000000),
('SBI Small Cap Fund', 'SBISCF', 'MUTUAL_FUND', 14580, 4.2, 300000000000),
('Mirae Asset Large Cap', 'MIRALC', 'MUTUAL_FUND', 8925, 2.0, 600000000000),
('HDFC Flexi Cap Fund', 'HDFCFC', 'MUTUAL_FUND', 158000, 2.8, 800000000000),
('Parag Parikh Flexi Cap', 'PPFAS', 'MUTUAL_FUND', 7500, 2.5, 400000000000),
-- Gold
('Digital Gold', 'GOLD', 'GOLD', 720000, 1.2, 50000000000000),
('Sovereign Gold Bond', 'SGB', 'GOLD', 750000, 1.5, 1000000000000);

-- Default fraud rules
INSERT OR IGNORE INTO fraud_rules (rule_name, rule_type, threshold_value, threshold_type, threshold_operator, severity, description, remediation_action) VALUES
('Large Transaction', 'AMOUNT', 100000, 'ABSOLUTE', 'GTE', 'HIGH', 'Transaction exceeds ₹1,00,000', 'Notify user, flag for review'),
('Very Large Transaction', 'AMOUNT', 500000, 'ABSOLUTE', 'GTE', 'CRITICAL', 'Transaction exceeds ₹5,00,000', 'Require additional verification'),
('Unusual Amount', 'AMOUNT', 5, 'MULTIPLIER', 'GTE', 'MEDIUM', 'Transaction is 5x above average', 'Log for analysis'),
('Rapid Transactions', 'FREQUENCY', 10, 'COUNT_PER_HOUR', 'GTE', 'HIGH', 'More than 10 transactions/hour', 'Temporarily block transactions'),
('Multiple Transfers', 'TRANSFER', 5, 'COUNT_PER_DAY', 'GTE', 'MEDIUM', 'More than 5 transfers/day', 'Notify user'),
('New Account Large Transfer', 'TRANSFER', 50000, 'NEW_ACCOUNT', 'GTE', 'HIGH', 'Large transfer from new account', 'Require verification'),
('High Risk Location', 'LOCATION', 0, 'COUNTRY', 'EQ', 'HIGH', 'Transaction from high-risk country', 'Block transaction'),
('Velocity Breach', 'VELOCITY', 1000000, 'AMOUNT_PER_DAY', 'GTE', 'HIGH', 'Daily transaction volume exceeds limit', 'Alert and review'),
('Unusual Time', 'BEHAVIOR', 2, 'STD_DEV', 'GTE', 'LOW', 'Transaction at unusual time', 'Log only'),
('Device Change', 'DEVICE', 1, 'NEW_DEVICE', 'EQ', 'MEDIUM', 'Login from new device', 'Send security alert');

-- Default admin account (password: Admin@123)
INSERT OR IGNORE INTO admins (name, email, password_hash, role) VALUES (
    'Super Admin',
    'admin@fintech.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4aYJGYxMnC6C5.Oy',
    'SUPER_ADMIN'
);

-- ============================================================
-- VIEWS FOR ANALYTICS
-- ============================================================

CREATE VIEW IF NOT EXISTS v_user_summary AS
SELECT 
    u.user_id,
    u.uuid as user_uuid,
    u.username,
    u.email,
    u.mobile,
    u.wallet_balance,
    u.status,
    u.kyc_verified,
    u.created_at,
    COALESCE(SUM(CASE WHEN i.amount IS NOT NULL THEN i.amount ELSE 0 END), 0) as total_income,
    COALESCE(SUM(CASE WHEN e.amount IS NOT NULL THEN e.amount ELSE 0 END), 0) as total_expenses,
    COALESCE(SUM(ui.invested_amount), 0) as total_invested
FROM users u
LEFT JOIN income i ON u.user_id = i.user_id
LEFT JOIN expenses e ON u.user_id = e.user_id
LEFT JOIN user_investments ui ON u.user_id = ui.user_id
GROUP BY u.user_id;

CREATE VIEW IF NOT EXISTS v_monthly_summary AS
SELECT 
    user_id,
    strftime('%Y-%m', date) as month,
    SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END) as income,
    SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END) as expenses
FROM (
    SELECT user_id, amount, 'INCOME' as type, date FROM income
    UNION ALL
    SELECT user_id, amount, 'EXPENSE' as type, date FROM expenses
)
GROUP BY user_id, month;

-- ============================================================
-- TRIGGERS FOR AUTO-UPDATES
-- ============================================================

CREATE TRIGGER IF NOT EXISTS update_audit_timestamp
AFTER UPDATE ON audit_logs
FOR EACH ROW
BEGIN
    UPDATE audit_logs SET indexed_at = datetime('now') WHERE log_id = NEW.log_id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_analytics
AFTER INSERT ON expenses
FOR EACH ROW
BEGIN
    DELETE FROM user_analytics_cache WHERE user_id = NEW.user_id;
END;

CREATE TRIGGER IF NOT EXISTS update_investment_value
AFTER UPDATE ON market_assets
FOR EACH ROW
BEGIN
    UPDATE user_investments SET 
        current_value = units_owned * NEW.current_price,
        profit_loss = (units_owned * NEW.current_price) - invested_amount,
        profit_loss_percent = CASE 
            WHEN invested_amount > 0 
            THEN ((units_owned * NEW.current_price) - invested_amount) * 100.0 / invested_amount 
            ELSE 0 
        END,
        last_price_update = datetime('now')
    WHERE asset_id = NEW.asset_id;
END;
