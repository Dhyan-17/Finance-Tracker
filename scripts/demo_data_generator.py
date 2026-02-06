"""
Production-Grade Demo Data Generator
Generates 50+ realistic Indian users with transactions, budgets, and investments
"""

import sys
import os
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import sqlite3

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import db


class DemoDataGenerator:
    """Generate realistic demo data for testing"""
    
    def __init__(self):
        self.num_users = 60  # Generate 60 users
        self.categories = [
            ('Food & Dining', '🍽️', '#FF6B6B', 10000),
            ('Transportation', '🚗', '#4ECDC4', 5000),
            ('Shopping', '🛍️', '#45B7D1', 8000),
            ('Entertainment', '🎬', '#96CEB4', 3000),
            ('Bills & Utilities', '📱', '#FFEAA7', 5000),
            ('Healthcare', '🏥', '#DDA0DD', 3000),
            ('Education', '📚', '#98D8C8', 5000),
            ('Travel', '✈️', '#F7DC6F', 10000),
            ('Groceries', '🛒', '#82E0AA', 8000),
            ('Personal Care', '💅', '#F8B500', 2000),
            ('Subscriptions', '📺', '#A569BD', 2000),
            ('Others', '📦', '#BDC3C7', 5000),
        ]
        
        self.indian_first_names = [
            'Aarav', 'Aditya', 'Amit', 'Ankit', 'Arjun', 'Ashok', 'Bharat', 'Chetan',
            'Deepak', 'Divyansh', 'Gaurav', 'Harsh', 'Hemant', 'Ishan', 'Jatin', 'Karan',
            'Kartik', 'Kunal', 'Lakshya', 'Madhav', 'Manish', 'Mohit', 'Naman', 'Nikhil',
            'Om', 'Parth', 'Prateek', 'Praveen', 'Rahul', 'Raj', 'Rakesh', 'Ravi',
            'Rohit', 'Sahil', 'Sanjay', 'Shivam', 'Siddharth', 'Sneha', 'Suresh',
            'Tarun', 'Umesh', 'Varun', 'Vikas', 'Vivek', 'Yash', 'Abhishek', 'Akshay',
            'Anil', 'Apoorv', 'Aryan', 'Ayush', 'Brijesh', 'Chirag', 'Darshan', 'Dhruv',
            'Riya', 'Priya', 'Ananya', 'Diya', 'Sara', 'Aisha', 'Neha', 'Pooja',
            'Kavya', 'Manvi', 'Anika', 'Radha', 'Meera', 'Tanvi', 'Ishita', 'Anjali'
        ]
        
        self.indian_last_names = [
            'Sharma', 'Patel', 'Kumar', 'Singh', 'Gupta', 'Shah', 'Mehta', 'Joshi',
            'Desai', 'Kapoor', 'Malhotra', 'Garg', 'Agarwal', 'Jain', 'Mishra',
            'Verma', 'Reddy', 'Nair', 'Menon', 'Iyer', 'Bhat', 'Rao', 'Pillai',
            'Chatterjee', 'Banerjee', 'Dutta', 'Choudhary', 'Yadav', 'Thakur', 'Pandey',
            'Chauhan', 'Srivastava', 'Tripathi', 'Mishra', 'Dubey', 'Bajpai', 'Kashyap',
            'Maheshwari', 'Lodha', 'Soni', 'Saxena', 'Singhal', 'Ghosh', 'Nandi', 'Das',
            'Biswas', 'Dhar', 'Chakraborty', 'Kar', 'Mitra', 'Sengupta', 'Bhattacharya'
        ]
        
        self.cities = [
            ('Mumbai', 'Maharashtra', 'SBIN'),
            ('Delhi', 'Delhi', 'UTIB'),
            ('Bangalore', 'Karnataka', 'HDFC'),
            ('Hyderabad', 'Telangana', 'ICIC'),
            ('Chennai', 'Tamil Nadu', 'IOBA'),
            ('Kolkata', 'West Bengal', 'PUNB'),
            ('Pune', 'Maharashtra', 'PGBP'),
            ('Ahmedabad', 'Gujarat', 'BARB'),
            ('Jaipur', 'Rajasthan', 'SBIN'),
            ('Lucknow', 'Uttar Pradesh', 'PUNB'),
            ('Kanpur', 'Uttar Pradesh', 'UTIB'),
            ('Nagpur', 'Maharashtra', 'HDFC'),
            ('Indore', 'Madhya Pradesh', 'ICIC'),
            ('Thane', 'Maharashtra', 'SBIN'),
            ('Bhopal', 'Madhya Pradesh', 'BARB'),
        ]
        
        self.companies = [
            'TCS', 'Infosys', 'Wipro', 'HCL Technologies', 'Tech Mahindra',
            'Reliance Industries', 'HDFC Bank', 'ICICI Bank', 'State Bank of India',
            'Tata Motors', 'Mahindra & Mahindra', 'Bajaj Auto', 'Hero MotoCorp',
            'Amazon India', 'Flipkart', 'Paytm', 'Zomato', 'Swiggy',
            'OYO', 'Byju\'s', 'Druva', 'Freshworks', 'InMobi',
            'Ola', 'Policybazaar', 'Razorpay', 'Cred', 'Dream11'
        ]
        
        self.income_sources = [
            'Salary', 'Freelance', 'Business', 'Investments', 'Rental Income',
            'Dividend', 'Interest', 'Gift', 'Commission', 'Bonus'
        ]
        
        self.merchants = {
            'Food & Dining': [
                'Zomato', 'Swiggy', 'Domino\'s', 'McDonald\'s', 'KFC',
                'Pizza Hut', 'Subway', 'Burger King', 'Starbucks', 'Cafe Coffee Day',
                'Local Restaurant', 'Food Court', 'Hotel', 'Tiffin Service'
            ],
            'Transportation': [
                'Uber', 'Ola', 'Rapido', 'Uber Auto', 'Metro',
                'Petrol Pump', 'Car Service', 'Bike Service', 'Parking',
                'Toll', 'Railway Station', 'Bus Stand', 'Flight Booking'
            ],
            'Shopping': [
                'Amazon', 'Flipkart', 'Myntra', 'Ajio', 'Snapdeal',
                'Reliance Fresh', 'Big Bazaar', 'DMart', 'Lifestyle', 'Shoppers Stop',
                'Local Market', 'Mall', 'Convenience Store', 'Kirana Store'
            ],
            'Entertainment': [
                'PVR', 'INOX', 'Cinepolis', 'BookMyShow', 'Netflix',
                'Amazon Prime', 'Hotstar', 'Sony Live', 'Zee5',
                'Gaming', 'Amusement Park', 'Concert', 'Sports Event'
            ],
            'Bills & Utilities': [
                'Electricity Bill', 'Water Bill', 'Gas Bill', 'Mobile Recharge',
                'DTH Recharge', 'Internet Bill', 'Cable TV', 'Property Tax',
                'Municipality', 'Broadband', 'Phone Bill', 'Data Card'
            ],
            'Healthcare': [
                'Pharmacy', 'Apollo Hospitals', 'Fortis Healthcare', 'Max Healthcare',
                'Doctor Visit', 'Diagnostic Lab', 'Medical Store', 'Pathology',
                'Dental Care', 'Eye Care', 'Fitness Center', 'Gym'
            ],
            'Education': [
                'Tuition Fees', 'School Fees', 'College Fees', 'Online Course',
                'Coursera', 'Udemy', 'Byju\'s', 'Vedantu', 'Books',
                'Stationery', 'Library', 'Coaching', 'Training'
            ],
            'Travel': [
                'IRCTC', 'MakeMyTrip', 'Yatra', 'Cleartrip', 'Flight Booking',
                'Hotel Booking', 'Bus Ticket', 'Train Ticket', 'Taxi',
                'Resort', 'Holiday Package', 'Travel Insurance', 'Tour Operator'
            ],
            'Groceries': [
                'Reliance Fresh', 'DMart', 'Big Basket', 'Grofers', 'Flipkart Grocery',
                'Local Mandi', 'Supermarket', 'Hypermarket', 'Organic Store',
                'Vegetable Shop', 'Fruit Market', 'Milk Dairy', 'Bakery'
            ],
            'Personal Care': [
                'Salon', 'Spa', 'Beauty Parlor', 'Haircut', 'Massage',
                ' cosmetics', 'Skincare', 'Grooming', 'Waxing', 'Manicure',
                'Pedicure', 'Tattoo', 'Piercing', 'Barber Shop'
            ],
            'Subscriptions': [
                'Netflix', 'Amazon Prime', 'Hotstar', 'Spotify', 'Gaana',
                'YouTube Premium', 'Apple Music', 'LinkedIn Premium', 'Adobe',
                'Microsoft 365', 'Google One', 'Dropbox', 'Evernote', 'Notion'
            ],
            'Others': [
                'Charity', 'Donation', 'Gift', 'Tips', 'Miscellaneous',
                'Pocket Money', 'Emergency', 'Contingency', 'Others'
            ]
        }
        
        self.stocks = [
            ('RELIANCE', 'STOCK', 245000),
            ('TCS', 'STOCK', 385000),
            ('INFY', 'STOCK', 152000),
            ('HDFCBANK', 'STOCK', 168000),
            ('ICICIBANK', 'STOCK', 105000),
            ('BHARTIARTL', 'STOCK', 142000),
            ('ITC', 'STOCK', 46500),
            ('HINDUNILVR', 'STOCK', 258000),
            ('WIPRO', 'STOCK', 45000),
            ('ASIANPAINT', 'STOCK', 285000),
        ]
        
        self.crypto = [
            ('BTC', 'CRYPTO', 750000000),
            ('ETH', 'CRYPTO', 35000000),
            ('SOL', 'CRYPTO', 2200000),
            ('ADA', 'CRYPTO', 8500),
            ('MATIC', 'CRYPTO', 12000),
        ]
        
        self.mutual_funds = [
            ('AXISBF', 'MUTUAL_FUND', 5250),
            ('SBISCF', 'MUTUAL_FUND', 14580),
            ('MIRALC', 'MUTUAL_FUND', 8925),
            ('HDFCFC', 'MUTUAL_FUND', 158000),
            ('PPFAS', 'MUTUAL_FUND', 7500),
        ]
    
    def generate_mobile(self, used_mobiles: set) -> str:
        """Generate unique Indian mobile number"""
        prefix = random.choice(['6', '7', '8', '9'])
        number = prefix + ''.join(random.choices('0123456789', k=9))
        while number in used_mobiles:
            number = prefix + ''.join(random.choices('0123456789', k=9))
        used_mobiles.add(number)
        return number
    
    def generate_email(self, first_name: str, last_name: str, used_emails: set) -> str:
        """Generate unique email"""
        domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'rediffmail.com', 
                   'icloud.com', 'protonmail.com', 'yahoo.co.in', 'hotmail.com']
        
        patterns = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}_{last_name.lower()}",
            f"{first_name[0].lower()}{last_name.lower()}",
            f"{first_name.lower()}{random.randint(1, 99)}",
        ]
        
        email_pattern = random.choice(patterns)
        domain = random.choice(domains)
        email = f"{email_pattern}@{domain}"
        
        counter = 1
        while email in used_emails:
            email = f"{email_pattern}{counter}@{domain}"
            counter += 1
        
        used_emails.add(email)
        return email
    
    def generate_username(self, first_name: str, used_usernames: set) -> str:
        """Generate unique username"""
        patterns = [
            f"{first_name.lower()}",
            f"{first_name.lower()}{random.randint(1, 999)}",
            f"{first_name.lower()}_",
            f"the_{first_name.lower()}",
            f"{first_name[0].lower()}{random.choice(self.indian_last_names).lower()}",
        ]
        
        username = random.choice(patterns)
        counter = 1
        while username in used_usernames:
            username = f"{username}{counter}"
            counter += 1
        
        used_usernames.add(username)
        return username
    
    def generate_bank_account(self, used_accounts: set) -> str:
        """Generate unique bank account number"""
        account = ''.join(random.choices('0123456789', k=random.randint(9, 18)))
        while account in used_accounts:
            account = ''.join(random.choices('0123456789', k=random.randint(9, 18)))
        used_accounts.add(account)
        return account
    
    def generate_upi_id(self, username: str, used_upis: set) -> str:
        """Generate unique UPI ID"""
        providers = ['upi', 'okhdfcbank', 'okicici', 'oksbi', 'paytm', 'phonepe', 'gpay']
        upi = f"{username.lower().replace(' ', '').replace('_', '')}@{random.choice(providers)}"
        
        counter = 1
        while upi in used_upis:
            upi = f"{username.lower().replace(' ', '').replace('_', '')}{counter}@{random.choice(providers)}"
            counter += 1
        
        used_upis.add(upi)
        return upi
    
    def hash_password(self, password: str) -> str:
        """Hash password for storage"""
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def generate_income(self, user_id: int, months: int = 6) -> List[Tuple]:
        """Generate realistic income records"""
        incomes = []
        
        # Monthly salary
        salary = random.randint(25000, 250000)
        base_date = datetime.now()
        
        for i in range(months):
            date = base_date - timedelta(days=i * 30)
            
            # Main salary
            incomes.append((
                user_id,
                self.to_paise(salary),
                'Salary',
                'Monthly Salary',
                random.choice(self.income_sources),
                'WALLET',
                None,
                date.strftime('%Y-%m-%d')
            ))
            
            # Occasional side income
            if random.random() > 0.5:
                side_amount = random.randint(5000, 50000)
                side_source = random.choice([s for s in self.income_sources if s != 'Salary'])
                incomes.append((
                    user_id,
                    self.to_paise(side_amount),
                    side_source,
                    random.choice(['Freelance Work', 'Consulting', 'Commission', 'Bonus']),
                    random.choice(self.income_sources),
                    'WALLET',
                    None,
                    (date + timedelta(days=random.randint(1, 28))).strftime('%Y-%m-%d')
                ))
        
        return incomes
    
    def generate_expenses(self, user_id: int, months: int = 6) -> List[Tuple]:
        """Generate realistic expense records"""
        expenses = []
        
        # Calculate monthly budget based on income
        monthly_budget = random.randint(15000, 150000)
        base_date = datetime.now()
        
        for i in range(months):
            month_date = base_date - timedelta(days=i * 30)
            remaining_budget = monthly_budget
            
            # Generate daily expenses
            num_expenses = random.randint(20, 60)
            
            for _ in range(num_expenses):
                if remaining_budget <= 500:
                    break
                
                category_info = random.choice(self.categories)
                category = category_info[0]
                
                # Higher weight to essential categories
                if category in ['Food & Dining', 'Groceries', 'Bills & Utilities']:
                    amount = random.randint(100, 1500)
                elif category in ['Transportation', 'Healthcare', 'Education']:
                    amount = random.randint(200, 3000)
                elif category == 'Shopping':
                    amount = random.randint(500, 10000)
                else:
                    amount = random.randint(50, 5000)
                
                amount = min(amount, remaining_budget)
                
                merchants = self.merchants.get(category, ['Unknown'])
                merchant = random.choice(merchants)
                
                payment_modes = ['UPI', 'DEBIT_CARD', 'CREDIT_CARD', 'NET_BANKING', 'WALLET']
                payment_mode = random.choices(payment_modes, weights=[40, 20, 15, 15, 10])[0]
                
                expense_date = month_date + timedelta(days=random.randint(0, 27))
                
                expenses.append((
                    user_id,
                    self.to_paise(amount),
                    category,
                    None,
                    f"{category} - {merchant}",
                    payment_mode,
                    'WALLET',
                    None,
                    merchant,
                    None,
                    expense_date.strftime('%Y-%m-%d')
                ))
                
                remaining_budget -= amount
        
        return expenses
    
    def generate_budgets(self, user_id: int) -> List[Tuple]:
        """Generate budget records for user"""
        budgets = []
        now = datetime.now()
        
        for i in range(3):  # Last 3 months
            month_date = now - timedelta(days=i * 30)
            
            # Create budget for random categories
            for _ in range(random.randint(4, 8)):
                category_info = random.choice(self.categories)
                budget_amount = category_info[3] * random.randint(1, 3)
                
                budgets.append((
                    user_id,
                    category_info[0],
                    self.to_paise(budget_amount),
                    month_date.year,
                    month_date.month,
                    80.0,
                    1
                ))
        
        return budgets
    
    def generate_investments(self, user_id: int) -> List[Tuple]:
        """Generate investment records"""
        investments = []
        
        # Decide if user invests
        if random.random() > 0.4:  # 60% chance to have investments
            num_investments = random.randint(1, 5)
            
            # Mix of stocks, crypto, and mutual funds
            all_assets = self.stocks + self.crypto + self.mutual_funds
            selected_assets = random.sample(all_assets, min(num_investments, len(all_assets)))
            
            for symbol, asset_type, price in selected_assets:
                # Get asset ID
                asset = db.execute_one(
                    "SELECT asset_id FROM market_assets WHERE asset_symbol = ?",
                    (symbol,)
                )
                
                if not asset:
                    continue
                
                units = round(random.uniform(1, 100), 4)
                buy_price = price * random.uniform(0.7, 0.95)  # Buy at discount
                
                investments.append((
                    user_id,
                    asset['asset_id'],
                    units,
                    self.to_paise(buy_price),
                    self.to_paise(buy_price * units),
                    self.to_paise(price * units),
                    self.to_paise(price * units) - self.to_paise(buy_price * units),
                    None,
                    (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')
                ))
        
        return investments
    
    def generate_goals(self, user_id: int) -> List[Tuple]:
        """Generate financial goals"""
        goals = []
        
        goal_templates = [
            ('Emergency Fund', 100000, 500000),
            ('Vacation', 50000, 200000),
            ('New Phone', 20000, 100000),
            ('Car Down Payment', 100000, 300000),
            ('Home Renovation', 200000, 500000),
            ('Wedding', 500000, 2000000),
            ('Child Education', 1000000, 5000000),
            ('Retirement Fund', 1000000, 10000000),
            ('Buy a Bike', 50000, 150000),
            ('World Tour', 500000, 1500000),
            ('Stock Market Investment', 25000, 500000),
            ('Gold Purchase', 50000, 300000),
        ]
        
        num_goals = random.randint(1, 4)
        selected_goals = random.sample(goal_templates, min(num_goals, len(goal_templates)))
        
        priorities = ['HIGH', 'MEDIUM', 'LOW']
        
        for name, min_target, max_target in selected_goals:
            target_amount = random.randint(min_target, max_target)
            current_savings = random.randint(0, min(target_amount // 2, 100000))
            monthly_contribution = random.randint(2000, min(50000, target_amount // 12))
            
            # Set target date
            months_to_target = random.randint(6, 36)
            target_date = (datetime.now() + timedelta(days=months_to_target * 30)).strftime('%Y-%m-%d')
            
            goals.append((
                user_id,
                name,
                self.to_paise(target_amount),
                self.to_paise(current_savings),
                self.to_paise(monthly_contribution),
                target_date,
                random.choice(priorities),
                'ACTIVE',
                '🎯',
                '#3498db',
                None,
                None
            ))
        
        return goals
    
    def generate_bank_accounts(self, user_id: int, used_accounts: set, used_upis: set) -> List[Tuple]:
        """Generate bank account for user"""
        bank_accounts = []
        
        # Get master banks
        banks = db.execute("SELECT bank_id, bank_name FROM master_banks LIMIT 5", fetch=True)
        
        if not banks:
            banks = [(1, 'State Bank of India')]
        
        # 70% chance to have a bank account
        if random.random() > 0.3:
            bank = random.choice(banks)
            account_number = self.generate_bank_account(used_accounts)
            upi_id = self.generate_upi_id(f"user{user_id}", used_upis)
            balance = random.randint(10000, 500000)
            
            bank_accounts.append((
                user_id,
                bank['bank_id'],
                account_number,
                random.choice(self.indian_first_names) + ' ' + random.choice(self.indian_last_names),
                'SAVINGS',
                self.to_paise(balance),
                upi_id,
                str(random.randint(1000, 9999)),
                None,
                self.to_paise(random.randint(50000, 500000)),
                1,  # is_primary
                1,  # is_active
                None,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        return bank_accounts
    
    def to_paise(self, amount: float) -> int:
        """Convert rupees to paise"""
        return int(round(amount * 100))
    
    def to_rupees(self, paise: int) -> float:
        """Convert paise to rupees"""
        return paise / 100.0
    
    def generate(self) -> Dict:
        """Generate complete demo data"""
        print("=" * 60)
        print("DEMO DATA GENERATOR")
        print("=" * 60)
        
        print(f"\nGenerating {self.num_users} realistic Indian users...")
        
        # Track used values for uniqueness
        used_mobiles = set()
        used_emails = set()
        used_usernames = set()
        used_accounts = set()
        used_upis = set()
        
        stats = {
            'users_created': 0,
            'bank_accounts': 0,
            'income_records': 0,
            'expense_records': 0,
            'budget_records': 0,
            'investment_records': 0,
            'goals': 0,
        }
        
        for i in range(1, self.num_users + 1):
            if i % 10 == 0:
                print(f"Progress: {i}/{self.num_users} users...")
            
            # Generate user details
            first_name = random.choice(self.indian_first_names)
            last_name = random.choice(self.indian_last_names)
            
            username = self.generate_username(first_name, used_usernames)
            email = self.generate_email(first_name, last_name, used_emails)
            mobile = self.generate_mobile(used_mobiles)
            
            # Create user
            password_hash = self.hash_password("Demo@123")
            wallet_balance = random.randint(5000, 100000)
            
            try:
                # Generate UUID for user
                import uuid
                user_uuid = str(uuid.uuid4())

                # Insert user
                db.execute(
                    """INSERT INTO users (uuid, username, password_hash, email, mobile, wallet_balance, wallet_uuid, status, kyc_verified, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)""",
                    (user_uuid, username, password_hash, email, mobile, self.to_paise(wallet_balance), wallet_uuid, 1, datetime.now().isoformat())
                )
                user_id = db.execute("SELECT last_insert_rowid() as id", fetch=True, single=True)['id']

                if not user_id:
                    print(f"Warning: Could not get user_id for {username}")
                    continue
                
                stats['users_created'] += 1
                
                # Generate wallet UUID
                wallet_uuid = hashlib.md5(f"{user_id}_{username}".encode()).hexdigest()[:16]
                db.execute("UPDATE users SET wallet_uuid = ? WHERE user_id = ?", (wallet_uuid, user_id))
                
                # Generate bank accounts
                bank_accounts = self.generate_bank_accounts(user_id, used_accounts, used_upis)
                if bank_accounts:
                    for ba in bank_accounts:
                        db.execute(
                            """INSERT INTO bank_accounts 
                               (user_id, bank_id, account_number, account_holder, account_type, balance, 
                                upi_id, debit_card_last4, credit_card_last4, credit_card_limit, 
                                is_primary, is_active, created_at, updated_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            ba
                        )
                        stats['bank_accounts'] += 1
                
                # Generate income
                incomes = self.generate_income(user_id, months=6)
                for inc in incomes:
                    db.execute(
                        """INSERT INTO income 
                           (user_id, amount, source, category, description, account_type, account_id, date)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        inc
                    )
                    stats['income_records'] += 1
                
                # Generate expenses
                expenses = self.generate_expenses(user_id, months=6)
                for exp in expenses:
                    db.execute(
                        """INSERT INTO expenses 
                           (user_id, amount, category, subcategory, description, payment_mode, 
                            account_type, account_id, merchant, location, date)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        exp
                    )
                    stats['expense_records'] += 1
                
                # Generate budgets
                budgets = self.generate_budgets(user_id)
                for bud in budgets:
                    db.execute(
                        """INSERT INTO budgets 
                           (user_id, category, limit_amount, year, month, alert_threshold, notifications_enabled)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        bud
                    )
                    stats['budget_records'] += 1
                
                # Generate investments
                investments = self.generate_investments(user_id)
                for inv in investments:
                    db.execute(
                        """INSERT INTO user_investments 
                           (user_id, asset_id, units_owned, buy_price, average_cost, invested_amount, 
                            current_value, profit_loss, purchase_date)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        inv
                    )
                    stats['investment_records'] += 1
                
                # Generate goals
                goals = self.generate_goals(user_id)
                for goal in goals:
                    db.execute(
                        """INSERT INTO financial_goals 
                           (user_id, goal_name, target_amount, current_savings, monthly_contribution, 
                            target_date, priority, status, icon, color, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        goal
                    )
                    stats['goals'] += 1
                
            except Exception as e:
                print(f"Error creating user {username}: {e}")
                continue
        
        print("\n" + "=" * 60)
        print("GENERATION COMPLETE!")
        print("=" * 60)
        print(f"\n📊 Statistics:")
        print(f"   Users Created: {stats['users_created']}")
        print(f"   Bank Accounts: {stats['bank_accounts']}")
        print(f"   Income Records: {stats['income_records']}")
        print(f"   Expense Records: {stats['expense_records']}")
        print(f"   Budget Records: {stats['budget_records']}")
        print(f"   Investment Records: {stats['investment_records']}")
        print(f"   Goals Created: {stats['goals']}")
        print(f"\n✅ Demo data generation successful!")
        print(f"\n📝 Test Credentials:")
        print(f"   Username: demo_user1")
        print(f"   Password: Demo@123")
        
        return stats


def clear_existing_data():
    """Clear existing demo data"""
    print("\nClearing existing data...")
    
    tables = [
        'goal_contributions',
        'financial_goals',
        'budgets',
        'investment_transactions',
        'user_investments',
        'expenses',
        'income',
        'bank_transactions',
        'transfers',
        'wallet_transactions',
        'bank_accounts',
        'sessions',
        'login_attempts',
        'audit_logs',
        'ai_conversations',
        'ai_insights',
        'notifications',
        'fraud_flags',
        'user_analytics_cache',
        'users',
    ]
    
    for table in tables:
        try:
            db.execute(f"DELETE FROM {table}")
            print(f"   Cleared {table}")
        except Exception as e:
            print(f"   Warning: Could not clear {table}: {e}")
    
    print("\n✅ Existing data cleared!")


def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("FINTECH APP - DEMO DATA GENERATOR")
    print("=" * 60)
    
    # Initialize database
    db_instance = Database()
    
    # Ask user preference
    print("\nOptions:")
    print("1. Generate new demo data (appends to existing)")
    print("2. Clear all data and generate fresh demo data")
    print("3. Exit")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        generator = DemoDataGenerator()
        generator.generate()
    elif choice == '2':
        clear_existing_data()
        generator = DemoDataGenerator()
        generator.generate()
    else:
        print("Exiting...")
        return


if __name__ == "__main__":
    main()
