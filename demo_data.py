"""
Demo Data Insertion Script for Finance Tracker
Run this script to populate the database with sample data for testing.

Usage: python demo_data.py
"""

import mysql.connector
from datetime import datetime, timedelta
import hashlib


class DemoDataManager:
    """Manages demo data insertion with consistent user_id mapping"""

    def __init__(self):
        self.connection = None
        self.demo_user_id = None
        self.connect()

    def connect(self):
        """Connect to database"""
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
                database='finance_tracker'
            )
            print("[OK] Connected to database")
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            raise

    def execute(self, query, params=None, fetch=False):
        """Execute query with parameters"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            cursor.close()
            return result
        self.connection.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return last_id

    # ========================================
    # INSERT METHODS
    # ========================================

    def create_user(self, username, email, password, mobile, wallet_balance=0):
        """Create a new user"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        query = """
            INSERT INTO users (username, email, password, mobile, wallet_balance)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE wallet_balance = VALUES(wallet_balance)
        """
        self.execute(query, (username, email, hashed_password, mobile, wallet_balance))
        
        # Get the user_id
        result = self.execute(
            "SELECT user_id FROM users WHERE username = %s",
            (username,), fetch=True
        )
        return result[0]['user_id'] if result else None

    def add_bank_account(self, user_id, bank_name, account_holder, balance, nickname):
        """Add bank account for user"""
        query = """
            INSERT INTO bank_accounts 
            (user_id, bank_name, account_holder, balance, nickname, ifsc_code, last_four_digits)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute(query, (user_id, bank_name, account_holder, balance, nickname, 'DEMO0001234', '1234'))

    def add_manual_account(self, user_id, account_name, opening_balance):
        """Add manual account for user"""
        query = """
            INSERT INTO manual_accounts (user_id, account_name, opening_balance)
            VALUES (%s, %s, %s)
        """
        return self.execute(query, (user_id, account_name, opening_balance))

    def add_income(self, user_id, source, amount, date=None):
        """Add income record"""
        if date is None:
            date = datetime.now()
        query = """
            INSERT INTO income (user_id, source, amount, date)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute(query, (user_id, source, amount, date))

    def add_expense(self, user_id, category, amount, description, payment_mode='UPI', subtype=None, date=None):
        """Add expense record"""
        if date is None:
            date = datetime.now()
        query = """
            INSERT INTO expenses (user_id, category, subtype, amount, description, payment_mode, date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute(query, (user_id, category, subtype, amount, description, payment_mode, date))

    def set_budget(self, user_id, category, limit_amount, month_key):
        """Set budget for category and month (YYYY-MM format)"""
        year, month = map(int, month_key.split('-'))
        query = """
            INSERT INTO budget (user_id, category, limit_amount, year, month)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE limit_amount = VALUES(limit_amount)
        """
        return self.execute(query, (user_id, category, limit_amount, year, month))

    def set_goal(self, user_id, goal_name, target_amount, current_savings=0, months=12):
        """Set financial goal"""
        monthly_savings = (target_amount - current_savings) / months if months > 0 else 0
        query = """
            INSERT INTO financial_goals 
            (user_id, account_type, goal_name, target_amount, current_savings, months_to_achieve, monthly_savings)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute(query, (user_id, 'wallet', goal_name, target_amount, current_savings, months, monthly_savings))

    def add_wallet_transaction(self, user_id, txn_type, amount, balance_after, date=None):
        """Add wallet transaction record"""
        if date is None:
            date = datetime.now()
        query = """
            INSERT INTO wallet_transactions (user_id, type, amount, balance_after, date)
            VALUES (%s, %s, %s, %s, %s)
        """
        return self.execute(query, (user_id, txn_type, amount, balance_after, date))

    # ========================================
    # DEMO DATA INSERTION
    # ========================================

    def insert_demo_data(self):
        """Insert complete demo data for testing"""
        print("\n" + "="*50)
        print("INSERTING DEMO DATA")
        print("="*50)

        # Current date for reference
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        last_month = (now.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

        # -------- 1. CREATE DEMO USER --------
        print("\n[1] Creating demo user...")
        self.demo_user_id = self.create_user(
            username="Dhyan",
            email="dhyan12@gmail.com",
            password="demo123",
            mobile="9876543210",
            wallet_balance=5000.00
        )
        print(f"    User created: Dhyan (ID: {self.demo_user_id})")

        # -------- 2. ADD ACCOUNTS --------
        print("\n[2] Adding accounts...")
        bank_id = self.add_bank_account(
            user_id=self.demo_user_id,
            bank_name="HDFC Bank",
            account_holder="Dhyan",
            balance=50000.00,
            nickname="HDFC Savings"
        )
        print(f"    Bank Account: HDFC Savings - Rs.50,000")

        manual_id = self.add_manual_account(
            user_id=self.demo_user_id,
            account_name="Cash Wallet",
            opening_balance=2000.00
        )
        print(f"    Manual Account: Cash Wallet - Rs.2,000")

        # -------- 3. ADD INCOME --------
        print("\n[3] Adding income records...")
        incomes = [
            ("Salary", 60000, now),
            ("Freelance", 15000, now - timedelta(days=5)),
            ("Interest", 500, now - timedelta(days=10)),
            ("Salary", 60000, now - timedelta(days=30)),
        ]
        for source, amount, date in incomes:
            self.add_income(self.demo_user_id, source, amount, date)
            print(f"    Income: {source} - Rs.{amount:,}")

        # -------- 4. ADD EXPENSES --------
        print("\n[4] Adding expense records...")
        expenses = [
            # (category, amount, description, payment_mode, subtype, days_ago)
            ("Food & Drinks", 2500, "Zomato Order", "UPI", None, 0),
            ("Food & Drinks", 1800, "Swiggy Order", "UPI", None, 2),
            ("Food & Drinks", 500, "Coffee Shop", "CARD", None, 5),
            ("Shopping", 5000, "Amazon Purchase", "CARD", None, 1),
            ("Shopping", 80000, "iPhone Purchase", "CARD", None, 3),
            ("Shopping", 2500, "Clothes", "UPI", None, 7),
            ("Housing", 15000, "Monthly Rent", "UPI", None, 5),
            ("Housing", 2000, "Electricity Bill", "UPI", None, 8),
            ("Transportation", 3000, "Uber Rides", "UPI", None, 0),
            ("Transportation", 500, "Metro Card", "CASH", None, 10),
            ("Healthcare", 1500, "Medicines", "UPI", None, 4),
            ("Others", 1500, "Dog Food", "UPI", "Pet Care", 2),
            ("Others", 2000, "Birthday Gift", "CASH", "Gifts", 6),
            ("Others", 800, "Laptop Repair", "UPI", "Repairs", 9),
            ("Life & Entertainment", 999, "Netflix Subscription", "CARD", None, 1),
            ("Life & Entertainment", 2500, "Movie Night", "UPI", None, 4),
            ("Education", 5000, "Online Course", "UPI", None, 7),
        ]
        
        for cat, amt, desc, mode, subtype, days_ago in expenses:
            date = now - timedelta(days=days_ago)
            self.add_expense(self.demo_user_id, cat, amt, desc, mode, subtype, date)
            subtype_str = f" ({subtype})" if subtype else ""
            print(f"    Expense: {desc}{subtype_str} [{cat}] - Rs.{amt:,}")

        # -------- 5. SET BUDGETS --------
        print("\n[5] Setting budgets...")
        budgets = [
            ("Food & Drinks", 15000, current_month),
            ("Shopping", 20000, current_month),
            ("Housing", 18000, current_month),
            ("Transportation", 5000, current_month),
            ("Healthcare", 3000, current_month),
            ("Others", 5000, current_month),
            ("Food & Drinks", 12000, last_month),
        ]
        for cat, limit, month in budgets:
            self.set_budget(self.demo_user_id, cat, limit, month)
            print(f"    Budget: {cat} - Rs.{limit:,} for {month}")

        # -------- 6. SET FINANCIAL GOALS --------
        print("\n[6] Setting financial goals...")
        goals = [
            ("Buy Laptop", 100000, 10000, 10),
            ("Emergency Fund", 200000, 50000, 12),
            ("Vacation", 50000, 5000, 6),
        ]
        for name, target, saved, months in goals:
            self.set_goal(self.demo_user_id, name, target, saved, months)
            print(f"    Goal: {name} - Rs.{target:,} (saved: Rs.{saved:,})")

        # -------- 7. ADD WALLET TRANSACTIONS --------
        print("\n[7] Adding wallet transactions...")
        balance = 5000
        transactions = [
            ("INCOME", 60000),
            ("EXPENSE", 5000),
            ("EXPENSE", 2500),
            ("INCOME", 15000),
        ]
        for txn_type, amount in transactions:
            if txn_type == "INCOME":
                balance += amount
            else:
                balance -= amount
            self.add_wallet_transaction(self.demo_user_id, txn_type, amount, balance)
            print(f"    Transaction: {txn_type} Rs.{amount:,} -> Balance: Rs.{balance:,}")

        print("\n" + "="*50)
        print("DEMO DATA INSERTED SUCCESSFULLY!")
        print("="*50)

    # ========================================
    # VERIFICATION QUERIES
    # ========================================

    def verify_data(self):
        """Run verification queries to confirm data insertion"""
        print("\n" + "="*50)
        print("VERIFYING INSERTED DATA")
        print("="*50)

        queries = [
            ("Users", "SELECT user_id, username, email, wallet_balance FROM users WHERE username = 'Dhyan'"),
            ("Bank Accounts", "SELECT account_id, bank_name, nickname, balance FROM bank_accounts WHERE user_id = %s"),
            ("Manual Accounts", "SELECT manual_account_id, account_name, opening_balance FROM manual_accounts WHERE user_id = %s"),
            ("Income (Recent 5)", "SELECT income_id, source, amount, DATE_FORMAT(date, '%Y-%m-%d') as date FROM income WHERE user_id = %s ORDER BY date DESC LIMIT 5"),
            ("Expenses (Top 5)", "SELECT expense_id, category, subtype, description, amount FROM expenses WHERE user_id = %s ORDER BY amount DESC LIMIT 5"),
            ("Budgets", "SELECT budget_id, category, limit_amount, CONCAT(year, '-', LPAD(month, 2, '0')) as month FROM budget WHERE user_id = %s"),
            ("Financial Goals", "SELECT goal_id, goal_name, target_amount, current_savings, status FROM financial_goals WHERE user_id = %s"),
        ]

        for name, query in queries:
            print(f"\n[{name}]")
            if '%s' in query:
                results = self.execute(query, (self.demo_user_id,), fetch=True)
            else:
                results = self.execute(query, fetch=True)
            
            if results:
                for row in results:
                    print(f"  {row}")
            else:
                print("  No data found")

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("\n[OK] Database connection closed")


def main():
    """Main entry point"""
    print("\n" + "="*50)
    print("FINANCE TRACKER - DEMO DATA SCRIPT")
    print("="*50)

    manager = DemoDataManager()

    try:
        # Insert demo data
        manager.insert_demo_data()

        # Verify insertion
        manager.verify_data()

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

    finally:
        manager.close()


if __name__ == "__main__":
    main()
