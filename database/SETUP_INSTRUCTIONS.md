# Database Setup Instructions

## Quick Reset (Recommended)

Since the database may be locked, follow these steps:

### Step 1: Close all Python processes
```bash
# Close any running Streamlit apps or Python scripts
```

### Step 2: Delete database files manually
```bash
# Navigate to data folder and delete:
del data\fintech.db
del data\fintech.db-shm  
del data\fintech.db-wal
```

### Step 3: Run the app to create fresh database
```bash
streamlit run app.py
```

### Step 4: Run seed data
```bash
python database/seed_data.py
```

---

## Schema Details

The minimal schema includes only columns actually used in your code:

### Users Table
- user_id, username, password_hash, email, mobile, wallet_balance, status, created_at, last_login, failed_login_attempts, locked_until

### Bank Accounts
- account_id, user_id, bank_id, account_number_last4, account_holder, balance, account_type, nickname, is_primary, created_at

**Removed unused:** upi_id, debit_card_last4, credit_card_last4, credit_card_limit

### Market Assets
- asset_id, asset_name, asset_symbol, asset_type, current_price, previous_price, day_change_percent, volatility_percent, is_active, last_updated

**Removed unused:** market_cap, week_high, week_low

---

## Login Credentials

After running seed_data.py:
- **Admin:** admin@fintech.com / Admin@123
- **User:** (any user from the 50 created, password format: Pass@<number>123)

---

## Files Created

1. **database/schema.sql** - Clean minimal schema
2. **database/seed_data.py** - Seed data generator
3. **database/SETUP_INSTRUCTIONS.md** - This file
