"""
Seed Data Generator for Fintech Database
Creates realistic dummy data for testing
"""

import sqlite3
import os
import random
import bcrypt
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'fintech.db')


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def generate_mobile() -> str:
    """Generate random Indian mobile number"""
    return f"9{random.randint(100000000, 999999999)}"


def paise(amount: float) -> int:
    """Convert rupees to paise"""
    return int(amount * 100)


def create_seed_data():
    """Create seed data for the database"""
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting seed data generation...")
    
    # Admin account
    print("")
    print("[1/6] Creating admin account...")
    admin_password_hash = hash_password("Admin@123")
    cursor.execute("""
        INSERT OR IGNORE INTO admins (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, ("Super Admin", "admin@fintech.com", admin_password_hash, "SUPER_ADMIN"))
    conn.commit()
    print("Admin: admin@fintech.com / Admin@123")
    
    # 50 Users
    print("")
    print("[2/6] Creating 50 dummy users...")
    
    first_names = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Raj", "Kavita", 
                  "Sanjay", "Meera", "Deepak", "Pooja", "Arun", "Divya", "Krishna",
                  "Nisha", "Vijay", "Rashmi", "Suresh", "Lakshmi", "Gaurav", "Swati",
                  "Madhav", "Kalpana", "Prashant", "Anita", "Dinesh", "Sunita", "Nikhil", "Richa",
                  "Rohit", "Shweta", "Manish", "Ritu", "Vishal", "Shikha", "Ajay", "Pallavi",
                  "Hitesh", "Arti", "Chirag", "Mona", "Parth", "Jignesh", "Kinjal", "Bhavin", 
                  "Minal", "Dhruv", "Shreya", "Kunal", "Ira"]
    
    last_names = ["Sharma", "Patel", "Singh", "Kumar", "Gupta", "Joshi", "Shah", "Mehta",
                  "Verma", "Reddy", "Rao", "Chopra", "Malhotra", "Khanna", "Bhatia",
                  "Kapoor", "Saxena", "Mishra", "Pandey", "Chandra", "Agarwal", "Banerjee",
                  "Das", "Mukherjee", "Sinha", "Iyer", "Nair", "Menon", "Pillai", "Desai"]
    
    user_ids = []
    for i in range(50):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        username = f"{first_name.lower()}{last_name.lower()}{i+1}"
        email = f"{first_name.lower()}{last_name.lower()}{i+1}@example.com"
        mobile = generate_mobile()
        wallet_balance = paise(random.uniform(1000, 50000))
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, email, mobile, wallet_balance, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, hash_password(f"Pass@{i+1}123"), email, mobile, wallet_balance, "ACTIVE"))
        
        user_ids.append(cursor.lastrowid)
    
    conn.commit()
    print(f"Created {len(user_ids)} users")
    
    # Transactions
    print("")
    print("[4/6] Creating transactions...")
    
    cursor.execute("SELECT name FROM expense_categories")
    categories = [row[0] for row in cursor.fetchall()]
    
    payment_modes = ['CASH', 'UPI', 'DEBIT_CARD', 'CREDIT_CARD', 'NET_BANKING', 'WALLET']
    income_sources = ['Salary', 'Freelance', 'Business', 'Investments', 'Gift', 'Refund']
    
    expense_count = 0
    income_count = 0
    
    for user_id in user_ids[:20]:
        cursor.execute("SELECT account_id FROM bank_accounts WHERE user_id = ?", (user_id,))
        bank_accounts = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,))
        wallet_balance = cursor.fetchone()[0]
        
        # Expenses
        for _ in range(random.randint(10, 30)):
            category = random.choice(categories)
            amount = paise(random.uniform(50, 5000))
            payment_mode = random.choice(payment_modes)
            account_type = random.choice(['WALLET', 'BANK'])
            account_id = random.choice(bank_accounts) if account_type == 'BANK' and bank_accounts else None
            
            days_ago = random.randint(0, 90)
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            if account_type == 'WALLET':
                new_balance = wallet_balance - amount
                wallet_balance = new_balance
            else:
                new_balance = None
            
            cursor.execute("""
                INSERT INTO expenses 
                (user_id, amount, category, payment_mode, account_type, account_id, merchant, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, amount, category, payment_mode, account_type, account_id, 
                  f"Merchant_{random.randint(1, 100)}", date))
            expense_count += 1
            
            if account_type == 'WALLET':
                cursor.execute("""
                    INSERT INTO wallet_transactions
                    (user_id, txn_type, amount, balance_after, reference_type, description, date)
                    VALUES (?, 'EXPENSE', ?, ?, 'expense', ?, ?)
                """, (user_id, amount, new_balance, category, date))
        
        # Income
        for _ in range(random.randint(5, 15)):
            source = random.choice(income_sources)
            amount = paise(random.uniform(5000, 100000))
            account_type = random.choice(['WALLET', 'BANK'])
            account_id = random.choice(bank_accounts) if account_type == 'BANK' and bank_accounts else None
            
            days_ago = random.randint(0, 90)
            date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
            
            if account_type == 'WALLET':
                new_balance = wallet_balance + amount
                wallet_balance = new_balance
            else:
                new_balance = None
            
            cursor.execute("""
                INSERT INTO income 
                (user_id, amount, source, account_type, account_id, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, amount, source, account_type, account_id, date))
            income_count += 1
            
            if account_type == 'WALLET':
                cursor.execute("""
                    INSERT INTO wallet_transactions
                    (user_id, txn_type, amount, balance_after, reference_type, description, date)
                    VALUES (?, 'INCOME', ?, ?, 'income', ?, ?)
                """, (user_id, amount, new_balance, source, date))
        
        cursor.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (wallet_balance, user_id))
    
    conn.commit()
    print(f"Created {expense_count} expenses and {income_count} income records")
    
    # Budgets
    print("")
    print("[5/6] Creating budgets...")
    
    budget_count = 0
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    for user_id in user_ids[:15]:
        num_budgets = random.randint(3, 5)
        budget_cats = random.sample(categories, num_budgets)
        
        for cat in budget_cats:
            limit = paise(random.uniform(5000, 30000))
            
            cursor.execute("""
                INSERT INTO budgets (user_id, category, limit_amount, year, month, alert_threshold)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, cat, limit, current_year, current_month, 80.0))
            budget_count += 1
    
    conn.commit()
    print(f"Created {budget_count} budgets")
    
    # Goals
    print("")
    print("[6/6] Creating financial goals...")
    
    goal_templates = [
        ("Emergency Fund", 100000, 12),
        ("Dream Vacation", 50000, 6),
        ("Education Fund", 200000, 24),
        ("New Car", 500000, 36),
        ("House Down Payment", 1000000, 60),
        ("Gadget Upgrade", 80000, 8),
        ("Retirement Fund", 5000000, 120),
        ("Wedding Fund", 300000, 18),
    ]
    
    priorities = ['HIGH', 'MEDIUM', 'LOW']
    goal_count = 0
    
    for user_id in user_ids[:10]:
        for _ in range(random.randint(1, 3)):
            template = random.choice(goal_templates)
            target = paise(template[1])
            months = template[2]
            monthly_contribution = paise(template[1] / months)
            priority = random.choice(priorities)
            target_date = (datetime.now() + timedelta(days=months*30)).strftime('%Y-%m-%d')
            
            current_savings = paise(random.uniform(0, template[1] * 0.5))
            status = 'COMPLETED' if current_savings >= target else 'ACTIVE'
            completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'COMPLETED' else None
            
            cursor.execute("""
                INSERT INTO financial_goals 
                (user_id, goal_name, target_amount, current_savings, monthly_contribution, 
                 target_date, priority, status, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, template[0], target, current_savings, monthly_contribution,
                  target_date, priority, status, completed_at))
            goal_count += 1
    
    conn.commit()
    print(f"Created {goal_count} financial goals")
    
    # Investments
    print("")
    print("[Bonus] Creating investments...")
    
    cursor.execute("SELECT asset_id, current_price FROM market_assets WHERE is_active = 1")
    assets = cursor.fetchall()
    
    investment_count = 0
    
    for user_id in user_ids[:15]:
        for _ in range(random.randint(0, 5)):
            if not assets:
                break
            asset_id, price = random.choice(assets)
            units = random.uniform(0.1, 50)
            invested_amount = paise(random.uniform(1000, 50000))
            buy_price = paise(invested_amount / units)
            purchase_date = (datetime.now() - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                INSERT INTO user_investments
                (user_id, asset_id, units_owned, buy_price, invested_amount, purchase_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, asset_id, units, buy_price, invested_amount, purchase_date))
            investment_count += 1
    
    conn.commit()
    print(f"Created {investment_count} investments")
    
    # Notifications
    print("")
    print("[Bonus] Creating notifications...")
    
    notification_titles = [
        "Budget Alert", "Goal Progress", "Investment Update", "New Feature Available",
        "Security Notice", "Transaction Complete", "Welcome!"
    ]
    
    notification_count = 0
    for user_id in user_ids[:20]:
        for _ in range(random.randint(0, 3)):
            title = random.choice(notification_titles)
            notification_type = random.choice(['INFO', 'WARNING', 'SUCCESS', 'ALERT'])
            message = f"Sample notification for user {user_id}. {title}"
            
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message, notification_type, is_read)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, title, message, notification_type, random.randint(0, 1)))
            notification_count += 1
    
    conn.commit()
    print(f"Created {notification_count} notifications")
    
    print("")
    print("=" * 50)
    print("SEED DATA COMPLETE!")
    print("=" * 50)
    print(f"Admin: admin@fintech.com / Admin@123")
    print(f"Users: {len(user_ids)}")
    print(f"Bank Accounts: {bank_account_count}")
    print(f"Expenses: {expense_count}")
    print(f"Income: {income_count}")
    print(f"Budgets: {budget_count}")
    print(f"Goals: {goal_count}")
    print(f"Investments: {investment_count}")
    print(f"Notifications: {notification_count}")
    
    conn.close()
    return True


if __name__ == "__main__":
    create_seed_data()
