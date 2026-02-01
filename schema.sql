-- Smart Wallet & Finance Management System Database Schema

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    mobile VARCHAR(10) UNIQUE NOT NULL,
    wallet_balance DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('ACTIVE', 'BLOCKED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin table
CREATE TABLE IF NOT EXISTS admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

-- Wallet transactions table
CREATE TABLE IF NOT EXISTS wallet_transactions (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    type ENUM('INCOME', 'EXPENSE', 'TRANSFER') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    balance_after DECIMAL(10,2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Expenses table
CREATE TABLE IF NOT EXISTS expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    category VARCHAR(50) NOT NULL,
    payment_mode ENUM('CASH', 'UPI', 'CARD') NOT NULL,
    description TEXT,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Income table
CREATE TABLE IF NOT EXISTS income (
    income_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    source VARCHAR(100) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Transfers table
CREATE TABLE IF NOT EXISTS transfers (
    transfer_id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Budget table
CREATE TABLE IF NOT EXISTS budget (
    budget_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(50) NOT NULL,
    limit_amount DECIMAL(10,2) NOT NULL,
    month YEAR NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_budget (user_id, category, month)
);

-- System logs table
CREATE TABLE IF NOT EXISTS system_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    actor VARCHAR(100) NOT NULL,
    action TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bank accounts table
CREATE TABLE IF NOT EXISTS bank_accounts (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    bank_name VARCHAR(100),
    account_holder VARCHAR(100),
    ifsc_code VARCHAR(15),
    last_four_digits VARCHAR(4),
    balance DECIMAL(10,2),
    nickname VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Investment accounts table
CREATE TABLE IF NOT EXISTS investment_accounts (
    investment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    investment_name VARCHAR(100),
    investment_type VARCHAR(50),   -- Stock / MF / Crypto / FD
    platform VARCHAR(100),          -- Zerodha, Groww, Coin, Bank
    quantity DECIMAL(10,4) DEFAULT 0,  -- Number of shares/units
    price_per_share DECIMAL(10,2) DEFAULT 0,  -- Price per share/unit at purchase
    invested_amount DECIMAL(10,2),
    current_value DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Ensure columns exist (for backward compatibility)
ALTER TABLE investment_accounts ADD COLUMN IF NOT EXISTS quantity DECIMAL(10,4) DEFAULT 0;
ALTER TABLE investment_accounts ADD COLUMN IF NOT EXISTS price_per_share DECIMAL(10,2) DEFAULT 0;

-- Imported transactions table
CREATE TABLE IF NOT EXISTS imported_transactions (
    import_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    account_id INT,
    txn_date DATE,
    description VARCHAR(255),
    txn_type VARCHAR(20),   -- INCOME / EXPENSE
    amount DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Manual accounts table
CREATE TABLE IF NOT EXISTS manual_accounts (
    manual_account_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    account_name VARCHAR(100),
    opening_balance DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Bank transactions table
CREATE TABLE IF NOT EXISTS bank_transactions (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    type ENUM('INCOME', 'EXPENSE') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    balance_after DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),
    source VARCHAR(100),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES bank_accounts(account_id) ON DELETE CASCADE
);

-- Investment transactions table
CREATE TABLE IF NOT EXISTS investment_transactions (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    type ENUM('INCOME', 'EXPENSE') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    value_after DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),
    source VARCHAR(100),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES investment_accounts(investment_id) ON DELETE CASCADE
);

-- Manual account transactions table
CREATE TABLE IF NOT EXISTS manual_account_transactions (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT NOT NULL,
    type ENUM('INCOME', 'EXPENSE') NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    balance_after DECIMAL(10,2) NOT NULL,
    category VARCHAR(50),
    source VARCHAR(100),
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES manual_accounts(manual_account_id) ON DELETE CASCADE
);

-- Financial goals table
CREATE TABLE IF NOT EXISTS financial_goals (
    goal_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_type VARCHAR(50) NOT NULL, -- 'wallet', 'bank', 'investment'
    account_id INT, -- NULL for wallet, account_id for bank/investment
    goal_name VARCHAR(100) NOT NULL,
    target_amount DECIMAL(10,2) NOT NULL,
    months_to_achieve INT NOT NULL,
    monthly_savings DECIMAL(10,2) NOT NULL,
    current_savings DECIMAL(10,2) DEFAULT 0.00,
    status ENUM('ACTIVE', 'COMPLETED', 'STOPPED') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Goal contributions table
CREATE TABLE IF NOT EXISTS goal_contributions (
    contribution_id INT AUTO_INCREMENT PRIMARY KEY,
    goal_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL, -- 'Monthly Savings', 'Business', 'Bonus', etc.
    source VARCHAR(255), -- Description of where the money came from
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (goal_id) REFERENCES financial_goals(goal_id) ON DELETE CASCADE
);

-- Insert default admin
INSERT IGNORE INTO admin (admin_id, name, password, email) VALUES
(1000, 'System Admin', 'admin123', 'admin@wallet.com');
