-- ============================================================
-- FINTECH FINANCE TRACKER - ENHANCED DATABASE SCHEMA
-- Production-grade mini banking + investment platform
-- ============================================================

-- ============================================================
-- PART 1: USER SYSTEM (Enhanced)
-- ============================================================

-- Users table with fintech fields
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    mobile VARCHAR(15) UNIQUE NOT NULL,
    wallet_balance DECIMAL(15,2) DEFAULT 0.00,
    status ENUM('ACTIVE', 'BLOCKED', 'SUSPENDED') DEFAULT 'ACTIVE',
    kyc_verified BOOLEAN DEFAULT FALSE,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_email (email),
    INDEX idx_last_active (last_active)
);

-- Admin table
CREATE TABLE IF NOT EXISTS admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('SUPER_ADMIN', 'ADMIN', 'ANALYST') DEFAULT 'ADMIN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- PART 2: CENTRALIZED BANKING SYSTEM
-- ============================================================

-- Master banks table (centralized - shared across all users)
CREATE TABLE IF NOT EXISTS master_banks (
    bank_id INT AUTO_INCREMENT PRIMARY KEY,
    bank_name VARCHAR(100) NOT NULL,
    ifsc_code VARCHAR(11) UNIQUE NOT NULL,
    branch_name VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ifsc (ifsc_code),
    INDEX idx_bank_name (bank_name)
);

-- User bank accounts (links users to master banks)
CREATE TABLE IF NOT EXISTS bank_accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bank_id INT NOT NULL,
    account_number_last4 VARCHAR(4),
    account_holder VARCHAR(100),
    balance DECIMAL(15,2) DEFAULT 0.00,
    account_type ENUM('SAVINGS', 'CURRENT', 'SALARY') DEFAULT 'SAVINGS',
    nickname VARCHAR(100),
    upi_id VARCHAR(50),
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (bank_id) REFERENCES master_banks(bank_id),
    INDEX idx_user_bank (user_id, bank_id)
);

-- Manual/Cash accounts
CREATE TABLE IF NOT EXISTS manual_accounts (
    manual_account_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    balance DECIMAL(15,2) DEFAULT 0.00,
    account_type ENUM('CASH', 'WALLET', 'OTHER') DEFAULT 'CASH',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================
-- PART 3: GLOBAL MARKET SYSTEM (Realistic Investment)
-- ============================================================

-- Master assets table (GLOBAL - affects all users equally)
CREATE TABLE IF NOT EXISTS market_assets (
    asset_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_name VARCHAR(100) UNIQUE NOT NULL,
    asset_symbol VARCHAR(20) UNIQUE NOT NULL,
    asset_type ENUM('STOCK', 'MUTUAL_FUND', 'CRYPTO', 'ETF', 'BOND') NOT NULL,
    current_price DECIMAL(15,4) NOT NULL,
    previous_price DECIMAL(15,4),
    day_change_percent DECIMAL(8,4) DEFAULT 0,
    week_high DECIMAL(15,4),
    week_low DECIMAL(15,4),
    volatility_percent DECIMAL(5,2) DEFAULT 5.00,
    market_cap DECIMAL(20,2),
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_asset_type (asset_type),
    INDEX idx_symbol (asset_symbol)
);

-- Market price history (for trends/charts)
CREATE TABLE IF NOT EXISTS market_price_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id) ON DELETE CASCADE,
    INDEX idx_asset_date (asset_id, recorded_at)
);

-- User investments (portfolio)
CREATE TABLE IF NOT EXISTS user_investments (
    investment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    asset_id INT NOT NULL,
    units_owned DECIMAL(15,6) NOT NULL,
    buy_price DECIMAL(15,4) NOT NULL,
    invested_amount DECIMAL(15,2) NOT NULL,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id),
    INDEX idx_user_asset (user_id, asset_id)
);

-- Investment transactions log
CREATE TABLE IF NOT EXISTS investment_transactions (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    asset_id INT NOT NULL,
    txn_type ENUM('BUY', 'SELL', 'DIVIDEND') NOT NULL,
    units DECIMAL(15,6) NOT NULL,
    price_per_unit DECIMAL(15,4) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    txn_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES market_assets(asset_id),
    INDEX idx_user_txn (user_id, txn_date)
);

-- ============================================================
-- PART 4: INCOME & EXPENSES
-- ============================================================

CREATE TABLE IF NOT EXISTS income (
    income_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    source VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    account_type ENUM('WALLET', 'BANK', 'MANUAL') DEFAULT 'WALLET',
    account_id INT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_date (user_id, date)
);

CREATE TABLE IF NOT EXISTS expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    subtype VARCHAR(100),
    description TEXT,
    payment_mode ENUM('CASH', 'UPI', 'CARD', 'NET_BANKING') DEFAULT 'UPI',
    account_type ENUM('WALLET', 'BANK', 'MANUAL') DEFAULT 'WALLET',
    account_id INT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_category (user_id, category),
    INDEX idx_date (date)
);

-- ============================================================
-- PART 5: BUDGETS & GOALS
-- ============================================================

CREATE TABLE IF NOT EXISTS budget (
    budget_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    limit_amount DECIMAL(15,2) NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    alert_threshold DECIMAL(5,2) DEFAULT 80.00,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_budget (user_id, category, year, month)
);

CREATE TABLE IF NOT EXISTS financial_goals (
    goal_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    goal_name VARCHAR(100) NOT NULL,
    target_amount DECIMAL(15,2) NOT NULL,
    current_savings DECIMAL(15,2) DEFAULT 0.00,
    monthly_contribution DECIMAL(15,2),
    target_date DATE,
    priority ENUM('HIGH', 'MEDIUM', 'LOW') DEFAULT 'MEDIUM',
    status ENUM('ACTIVE', 'COMPLETED', 'PAUSED', 'CANCELLED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================
-- PART 6: TRANSACTIONS & AUDIT
-- ============================================================

CREATE TABLE IF NOT EXISTS wallet_transactions (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('INCOME', 'EXPENSE', 'TRANSFER', 'INVESTMENT', 'REFUND') NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2) NOT NULL,
    reference_id VARCHAR(50),
    description TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_type (user_id, type),
    INDEX idx_date (date)
);

CREATE TABLE IF NOT EXISTS system_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    actor VARCHAR(100) NOT NULL,
    action TEXT NOT NULL,
    ip_address VARCHAR(45),
    severity ENUM('INFO', 'WARNING', 'ERROR', 'CRITICAL') DEFAULT 'INFO',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_actor (actor),
    INDEX idx_severity (severity),
    INDEX idx_timestamp (timestamp)
);

-- ============================================================
-- PART 7: ANALYTICS CACHE (for performance)
-- ============================================================

CREATE TABLE IF NOT EXISTS user_analytics_cache (
    cache_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    total_income DECIMAL(15,2) DEFAULT 0,
    total_expenses DECIMAL(15,2) DEFAULT 0,
    total_investments DECIMAL(15,2) DEFAULT 0,
    investment_current_value DECIMAL(15,2) DEFAULT 0,
    net_worth DECIMAL(15,2) DEFAULT 0,
    last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================================
-- INITIAL DATA: Master Banks
-- ============================================================

INSERT IGNORE INTO master_banks (bank_name, ifsc_code, branch_name, city, state) VALUES
('State Bank of India', 'SBIN0001234', 'Main Branch', 'Mumbai', 'Maharashtra'),
('HDFC Bank', 'HDFC0001234', 'Central Branch', 'Mumbai', 'Maharashtra'),
('ICICI Bank', 'ICIC0001234', 'Corporate Branch', 'Bangalore', 'Karnataka'),
('Axis Bank', 'UTIB0001234', 'Main Branch', 'Delhi', 'Delhi'),
('Kotak Mahindra Bank', 'KKBK0001234', 'Premium Branch', 'Mumbai', 'Maharashtra'),
('Punjab National Bank', 'PUNB0001234', 'Head Office', 'Delhi', 'Delhi'),
('Bank of Baroda', 'BARB0001234', 'Main Branch', 'Vadodara', 'Gujarat'),
('Yes Bank', 'YESB0001234', 'Corporate Branch', 'Mumbai', 'Maharashtra');

-- ============================================================
-- INITIAL DATA: Market Assets (Global)
-- ============================================================

INSERT IGNORE INTO market_assets (asset_name, asset_symbol, asset_type, current_price, volatility_percent) VALUES
-- Indian Stocks
('Reliance Industries', 'RELIANCE', 'STOCK', 2450.00, 3.5),
('Tata Consultancy Services', 'TCS', 'STOCK', 3850.00, 2.8),
('Infosys', 'INFY', 'STOCK', 1520.00, 3.2),
('HDFC Bank', 'HDFCBANK', 'STOCK', 1680.00, 2.5),
('ICICI Bank', 'ICICIBANK', 'STOCK', 1050.00, 3.0),
('Bharti Airtel', 'BHARTIARTL', 'STOCK', 1420.00, 4.0),
('ITC Limited', 'ITC', 'STOCK', 465.00, 2.2),
('Hindustan Unilever', 'HINDUNILVR', 'STOCK', 2580.00, 1.8),
-- Crypto
('Bitcoin', 'BTC', 'CRYPTO', 7500000.00, 8.5),
('Ethereum', 'ETH', 'CRYPTO', 350000.00, 9.2),
('Solana', 'SOL', 'CRYPTO', 22000.00, 12.0),
('Cardano', 'ADA', 'CRYPTO', 85.00, 10.5),
-- Mutual Funds
('Axis Bluechip Fund', 'AXISBF', 'MUTUAL_FUND', 52.50, 1.5),
('SBI Small Cap Fund', 'SBISCF', 'MUTUAL_FUND', 145.80, 4.2),
('Mirae Asset Large Cap', 'MIRALC', 'MUTUAL_FUND', 89.25, 2.0),
('HDFC Flexi Cap Fund', 'HDFCFC', 'MUTUAL_FUND', 1580.00, 2.8);

-- ============================================================
-- INITIAL DATA: Default Admin
-- ============================================================

INSERT IGNORE INTO admin (admin_id, name, email, password, role) VALUES
(1000, 'System Admin', 'admin@fintrack.com', 'admin123', 'SUPER_ADMIN');
