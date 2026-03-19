"""
Demo Data Seed Script for FinTech App
Creates 2 demo users with realistic financial data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from datetime import datetime, timedelta

from database.db import db


def to_paise(rupees):
    return int(rupees * 100)


def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_demo_users():
    print("Creating demo users...")
    
    # Delete existing demo users if they exist
    existing = db.execute("SELECT user_id FROM users WHERE email IN ('ram@mail.com', 'dhyan@mail.com')", fetch=True)
    for u in existing:
        db.execute("DELETE FROM goal_contributions WHERE goal_id IN (SELECT goal_id FROM financial_goals WHERE user_id = ?)", (u['user_id'],))
        db.execute("DELETE FROM financial_goals WHERE user_id = ?", (u['user_id'],))
        db.execute("DELETE FROM budgets WHERE user_id = ?", (u['user_id'],))
        db.execute("DELETE FROM expenses WHERE user_id = ?", (u['user_id'],))
        db.execute("DELETE FROM income WHERE user_id = ?", (u['user_id'],))
        db.execute("DELETE FROM investment_transactions WHERE asset_id IN (SELECT investment_id FROM user_investments WHERE user_id = ?)", (u['user_id'],))
        db.execute("DELETE FROM user_investments WHERE user_id = ?", (u['user_id'],))
        db.execute("DELETE FROM users WHERE user_id = ?", (u['user_id'],))
    
    # ============ USER 1: RAM ============
    print("Creating user: Ram (ram@mail.com)")
    
    ram_id = db.execute_insert(
        "INSERT INTO users (username, password_hash, email, mobile, wallet_balance, status) VALUES (?, ?, ?, ?, ?, ?)",
        ("ram", hash_password("Ram@123"), "ram@mail.com", "9876543210", to_paise(50000), "ACTIVE")
    )
    
    # Ram's income (salary)
    base_date = datetime.now() - timedelta(days=90)
    for i in range(3):
        db.execute_insert(
            "INSERT INTO income (user_id, amount, source, category, description, account_type, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ram_id, to_paise(85000), "Salary", "Monthly Salary", "Monthly salary", "WALLET", (base_date + timedelta(days=i*30)).strftime('%Y-%m-%d'))
        )
    
    # Ram's expenses
    expenses_data = [
        ("Food", "Groceries", "Big Basket", 2500),
        ("Food", "Restaurants", "Swiggy", 800),
        ("Travel", "Fuel", "Shell", 1500),
        ("Shopping", "Clothing", "Myntra", 2500),
        ("Bills", "Electricity", "BSES", 1200),
        ("Bills", "Mobile", "Jio", 599),
        ("Bills", "Rent", "Owner", 15000),
    ]
    
    expense_date = datetime.now() - timedelta(days=60)
    for i, (cat, subcat, merch, amt) in enumerate(expenses_data):
        db.execute_insert(
            "INSERT INTO expenses (user_id, amount, category, subcategory, description, payment_mode, account_type, account_id, merchant, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ram_id, to_paise(amt), cat, subcat, f"{cat} expense", "UPI", "WALLET" if i % 2 == 0 else "BANK", ram_bank1 if i % 2 == 0 else ram_bank2, merch, (expense_date + timedelta(days=i*5)).strftime('%Y-%m-%d'))
        )
    
    # Ram's budgets
    db.execute_insert("INSERT INTO budgets (user_id, category, limit_amount, year, month, alert_threshold) VALUES (?, ?, ?, ?, ?, ?)", (ram_id, "Food", to_paise(15000), 2026, 2, 80))
    db.execute_insert("INSERT INTO budgets (user_id, category, limit_amount, year, month, alert_threshold) VALUES (?, ?, ?, ?, ?, ?)", (ram_id, "Travel", to_paise(5000), 2026, 2, 80))
    db.execute_insert("INSERT INTO budgets (user_id, category, limit_amount, year, month, alert_threshold) VALUES (?, ?, ?, ?, ?, ?)", (ram_id, "Shopping", to_paise(10000), 2026, 2, 80))
    
    # Ram's goals
    car_goal = db.execute_insert(
        "INSERT INTO financial_goals (user_id, goal_name, target_amount, current_savings, monthly_contribution, target_date, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (ram_id, "Car Fund", to_paise(500000), to_paise(125000), to_paise(15000), "2027-02-18", "HIGH", "ACTIVE")
    )
    
    vacation_goal = db.execute_insert(
        "INSERT INTO financial_goals (user_id, goal_name, target_amount, current_savings, monthly_contribution, target_date, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (ram_id, "Vacation Fund", to_paise(100000), to_paise(35000), to_paise(8000), "2026-08-18", "MEDIUM", "ACTIVE")
    )
    
    # Goal contributions
    db.execute_insert("INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)", (car_goal, to_paise(50000), "WALLET"))
    db.execute_insert("INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)", (car_goal, to_paise(75000), f"BANK_{ram_bank1}"))
    db.execute_insert("INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)", (vacation_goal, to_paise(20000), "WALLET"))
    db.execute_insert("INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)", (vacation_goal, to_paise(15000), f"BANK_{ram_bank2}"))
    
    # Ram investments - TCS
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (ram_id, 2, 5, to_paise(3500), to_paise(17500), "2025-06-15"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ram_id, 2, "BUY", 5, to_paise(3500), to_paise(17500), "BANK", ram_bank1, "2025-06-15"))
    
    # Ram investments - Reliance
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (ram_id, 1, 10, to_paise(2400), to_paise(24000), "2025-08-20"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ram_id, 1, "BUY", 10, to_paise(2400), to_paise(24000), "BANK", ram_bank1, "2025-08-20"))
    
    # Ram investments - Bitcoin
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (ram_id, 11, 0.01, to_paise(600000), to_paise(6000), "2025-10-05"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ram_id, 11, "BUY", 0.01, to_paise(600000), to_paise(6000), "WALLET", None, "2025-10-05"))
    
    # Ram investments - Mutual Fund
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (ram_id, 16, 50, to_paise(5000), to_paise(250000), "2025-04-10"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ram_id, 16, "BUY", 50, to_paise(5000), to_paise(250000), "BANK", ram_bank1, "2025-04-10"))
    
    # Ram investments - Gold
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (ram_id, 21, 0.5, to_paise(680000), to_paise(340000), "2025-01-20"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (ram_id, 21, "BUY", 0.5, to_paise(680000), to_paise(340000), "BANK", ram_bank2, "2025-01-20"))
    
    print(f"Ram created with ID: {ram_id}")
    
    # ============ USER 2: DHYAN ============
    print("Creating user: Dhyan (dhyan@mail.com)")
    
    dhyan_id = db.execute_insert(
        "INSERT INTO users (username, password_hash, email, mobile, wallet_balance, status) VALUES (?, ?, ?, ?, ?, ?)",
        ("dhyan", hash_password("Dhyan@123"), "dhyan@mail.com", "9876543211", to_paise(75000), "ACTIVE")
    )
    
    # Dhyan's bank accounts
    dhyan_bank1 = db.execute_insert(
        "INSERT INTO bank_accounts (user_id, bank_id, account_number_last4, account_holder, balance, account_type, nickname, is_primary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (dhyan_id, 3, "5678", "Dhyan Patel", to_paise(200000), "SAVINGS", "Primary", 1)
    )
    
    dhyan_bank2 = db.execute_insert(
        "INSERT INTO bank_accounts (user_id, bank_id, account_number_last4, account_holder, balance, account_type, nickname, is_primary) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (dhyan_id, 5, "3456", "Dhyan Patel", to_paise(100000), "SAVINGS", "Savings", 0)
    )
    
    # Dhyan's income
    for i in range(3):
        db.execute_insert(
            "INSERT INTO income (user_id, amount, source, category, description, account_type, account_id, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (dhyan_id, to_paise(120000), "Salary", "Monthly Salary", "Monthly salary", "BANK", dhyan_bank1, (base_date + timedelta(days=i*30)).strftime('%Y-%m-%d'))
        )
    
    # Dhyan's expenses
    for i, (cat, subcat, merch, amt) in enumerate(expenses_data):
        db.execute_insert(
            "INSERT INTO expenses (user_id, amount, category, subcategory, description, payment_mode, account_type, account_id, merchant, date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (dhyan_id, to_paise(amt * 1.5), cat, subcat, f"{cat} expense", "UPI", "WALLET" if i % 2 == 0 else "BANK", dhyan_bank1 if i % 2 == 0 else dhyan_bank2, merch, (expense_date + timedelta(days=i*5)).strftime('%Y-%m-%d'))
        )
    
    # Dhyan's budgets
    db.execute_insert("INSERT INTO budgets (user_id, category, limit_amount, year, month, alert_threshold) VALUES (?, ?, ?, ?, ?, ?)", (dhyan_id, "Food", to_paise(20000), 2026, 2, 80))
    db.execute_insert("INSERT INTO budgets (user_id, category, limit_amount, year, month, alert_threshold) VALUES (?, ?, ?, ?, ?, ?)", (dhyan_id, "Travel", to_paise(15000), 2026, 2, 80))
    
    # Dhyan's goals
    house_goal = db.execute_insert("INSERT INTO financial_goals (user_id, goal_name, target_amount, current_savings, monthly_contribution, target_date, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (dhyan_id, "House Down Payment", to_paise(1000000), to_paise(350000), to_paise(25000), "2028-01-01", "HIGH", "ACTIVE"))
    education_goal = db.execute_insert("INSERT INTO financial_goals (user_id, goal_name, target_amount, current_savings, monthly_contribution, target_date, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (dhyan_id, "MBA Fund", to_paise(300000), to_paise(85000), to_paise(15000), "2027-06-01", "HIGH", "ACTIVE"))
    emergency_goal = db.execute_insert("INSERT INTO financial_goals (user_id, goal_name, target_amount, current_savings, monthly_contribution, target_date, priority, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (dhyan_id, "Emergency Fund", to_paise(200000), to_paise(120000), to_paise(10000), "2026-12-01", "MEDIUM", "ACTIVE"))
    
    # Goal contributions
    db.execute_insert("INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)", (house_goal, to_paise(200000), "WALLET"))
    db.execute_insert("INSERT INTO goal_contributions (goal_id, amount, source) VALUES (?, ?, ?)", (house_goal, to_paise(150000), f"BANK_{dhyan_bank1}"))
    
    # Dhyan investments - Infosys
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (dhyan_id, 3, 15, to_paise(1400), to_paise(21000), "2025-05-20"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (dhyan_id, 3, "BUY", 15, to_paise(1400), to_paise(21000), "BANK", dhyan_bank1, "2025-05-20"))
    
    # Dhyan investments - HDFC Bank
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (dhyan_id, 4, 20, to_paise(1600), to_paise(32000), "2025-07-10"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (dhyan_id, 4, "BUY", 20, to_paise(1600), to_paise(32000), "BANK", dhyan_bank1, "2025-07-10"))
    
    # Dhyan investments - Ethereum
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (dhyan_id, 12, 0.5, to_paise(30000), to_paise(15000), "2025-09-15"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (dhyan_id, 12, "BUY", 0.5, to_paise(30000), to_paise(15000), "WALLET", None, "2025-09-15"))
    
    # Dhyan investments - Mutual Fund
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (dhyan_id, 17, 100, to_paise(14000), to_paise(1400000), "2025-03-01"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (dhyan_id, 17, "BUY", 100, to_paise(14000), to_paise(1400000), "BANK", dhyan_bank1, "2025-03-01"))
    
    # Dhyan investments - Gold
    db.execute_insert("INSERT INTO user_investments (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date) VALUES (?, ?, ?, ?, ?, ?)", (dhyan_id, 21, 1.0, to_paise(650000), to_paise(650000), "2025-02-15"))
    db.execute_insert("INSERT INTO investment_transactions (user_id, asset_id, txn_type, units, price_per_unit, total_amount, source_account_type, source_account_id, txn_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (dhyan_id, 21, "BUY", 1.0, to_paise(650000), to_paise(650000), "BANK", dhyan_bank2, "2025-02-15"))
    
    print(f"Dhyan created with ID: {dhyan_id}")
    
    print("\n=== Demo data created successfully! ===")
    print("User 1: ram@mail.com / Ram@123")
    print("User 2: dhyan@mail.com / Dhyan@123")


if __name__ == "__main__":
    create_demo_users()
