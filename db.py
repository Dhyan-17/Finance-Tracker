import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.connection = None
        self.connect()

    def connect(self):
        """Establish database connection"""
        try:
            # Database configuration - adjust as needed
            self.connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',  # Empty password for local development
                database='finance_tracker'
            )

            if self.connection.is_connected():
                print("✅ Database Connected Successfully!")
                self.create_tables()
                return True

        except Error as e:
            print(f"❌ Database Connection Failed: {e}")
            # Try to create database if it doesn't exist
            self.create_database()
            return False

    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password=''
            )
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS finance_tracker")
            cursor.close()
            connection.close()
            print("✅ Database 'finance_tracker' created successfully!")
            # Reconnect to the new database
            self.connect()
        except Error as e:
            print(f"❌ Failed to create database: {e}")

    def create_tables(self):
        """Create all required tables"""
        try:
            cursor = self.connection.cursor()

            # Read schema file and execute
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            with open(schema_path, 'r') as file:
                schema_sql = file.read()

            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]

            for statement in statements:
                if statement:
                    cursor.execute(statement)



            self.connection.commit()
            cursor.close()
            print("✅ Database tables created/verified successfully!")

        except Error as e:
            print(f"❌ Failed to create tables: {e}")
        except FileNotFoundError:
            print("❌ schema.sql file not found!")

    def execute_query(self, query, params=None, fetch=False):
        """Execute a query with optional parameters"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())

            if fetch:
                result = cursor.fetchall()
            else:
                self.connection.commit()
                result = cursor.rowcount

            cursor.close()
            return result

        except Error as e:
            print(f"❌ Database Error: {e}")
            self.connection.rollback()
            return None

    def execute_insert(self, query, params=None):
        """Execute insert query and return last inserted id"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        except Error as e:
            print(f"❌ Database Insert Error: {e}")
            self.connection.rollback()
            return None
        
    def get_user_by_email(self, email):
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = %s"
        result = self.execute_query(query, (email,), fetch=True)
        return result[0] if result else None

    def get_user_by_mobile(self, mobile):
        """Get user by mobile"""
        query = "SELECT * FROM users WHERE mobile = %s"
        result = self.execute_query(query, (mobile,), fetch=True)
        return result[0] if result else None


    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Database connection closed.")

    def log_action(self, actor, action):
        """Log system actions"""
        query = "INSERT INTO system_logs (actor, action) VALUES (%s, %s)"
        self.execute_query(query, (actor, action))

    def get_user_balance(self, user_id):
        """Get current wallet balance for user"""
        query = "SELECT wallet_balance FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0]['wallet_balance'] if result else 0.0

    def get_user_total_balance(self, user_id):
        """Get total balance across all accounts (wallet + bank + investment + manual)"""
        wallet = self.get_user_balance(user_id)
        bank = self.get_bank_balance(user_id)
        investment = self.get_investment_value(user_id)
        manual = self.get_manual_accounts_balance(user_id)
        return wallet + bank + investment + manual

    def update_user_balance(self, user_id, new_balance):
        """Update user wallet balance"""
        query = "UPDATE users SET wallet_balance = %s WHERE user_id = %s"
        return self.execute_query(query, (new_balance, user_id))

    def add_transaction(self, user_id, txn_type, amount, balance_after):
        """Add wallet transaction record"""
        query = """INSERT INTO wallet_transactions
                   (user_id, type, amount, balance_after)
                   VALUES (%s, %s, %s, %s)"""
        return self.execute_insert(query, (user_id, txn_type, amount, balance_after))

    def get_user_by_username(self, username):
        """Get user details by username"""
        query = "SELECT * FROM users WHERE username = %s"
        result = self.execute_query(query, (username,), fetch=True)
        return result[0] if result else None

    def get_user_by_id(self, user_id):
        """Get user details by user_id"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None

    def get_admin_by_id(self, admin_id):
        """Get admin details by admin_id"""
        query = "SELECT * FROM admin WHERE admin_id = %s"
        result = self.execute_query(query, (admin_id,), fetch=True)
        return result[0] if result else None

    def user_exists(self, username=None, email=None, mobile=None):
        """Check if user exists with given username, email, or mobile"""
        conditions = []
        params = []

        if username:
            conditions.append("username = %s")
            params.append(username)
        if email:
            conditions.append("email = %s")
            params.append(email)
        if mobile:
            conditions.append("mobile = %s")
            params.append(mobile)

        if not conditions:
            return False

        query = f"SELECT user_id FROM users WHERE {' OR '.join(conditions)}"
        result = self.execute_query(query, tuple(params), fetch=True)
        return result is not None and len(result) > 0

    def add_bank_account(self, user_id, bank_name, account_holder, ifsc_code, last_four_digits, balance, nickname, upi_id=None, debit_card_last_four=None, credit_card_last_four=None, credit_card_limit=0.00):
        """Add a new bank account for the user"""
        query = """
            INSERT INTO bank_accounts
            (user_id, bank_name, account_holder, ifsc_code, last_four_digits, balance, nickname, upi_id, debit_card_last_four, credit_card_last_four, credit_card_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_insert(query, (user_id, bank_name, account_holder, ifsc_code, last_four_digits, balance, nickname, upi_id, debit_card_last_four, credit_card_last_four, credit_card_limit))

    def get_user_bank_accounts(self, user_id):
        """Get all bank accounts for a user"""
        query = "SELECT * FROM bank_accounts WHERE user_id = %s"
        return self.execute_query(query, (user_id,), fetch=True)

    def get_bank_balance(self, user_id):
        """Get total bank balance for a user"""
        query = "SELECT SUM(balance) AS total_balance FROM bank_accounts WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0]['total_balance'] if result and result[0]['total_balance'] else 0.0

    def add_investment_account(self, user_id, investment_name, investment_type, platform, invested_amount, current_value, quantity, price_per_share, price_change_percentage=0.00):
        """Add a new investment account for the user"""
        query = """
            INSERT INTO investment_accounts
            (user_id, investment_name, investment_type, platform, invested_amount, current_value, quantity, price_per_share, price_change_percentage, last_price_update)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        return self.execute_insert(query, (user_id, investment_name, investment_type, platform, invested_amount, current_value, quantity, price_per_share, price_change_percentage))

    def get_user_investment_accounts(self, user_id):
        """Get all investment accounts for a user"""
        query = "SELECT * FROM investment_accounts WHERE user_id = %s"
        return self.execute_query(query, (user_id,), fetch=True)

    def get_investment_value(self, user_id):
        """Get total investment value for a user"""
        query = "SELECT SUM(current_value) AS total_value FROM investment_accounts WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0]['total_value'] if result and result[0]['total_value'] else 0.0

    def add_imported_transaction(self, user_id, account_id, txn_date, description, txn_type, amount):
        """Add an imported transaction"""
        query = """
            INSERT INTO imported_transactions
            (user_id, account_id, txn_date, description, txn_type, amount)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_insert(query, (user_id, account_id, txn_date, description, txn_type, amount))

    def get_imported_transactions(self, user_id, account_id=None):
        """Get imported transactions for a user, optionally filtered by account"""
        if account_id:
            query = "SELECT * FROM imported_transactions WHERE user_id = %s AND account_id = %s ORDER BY txn_date DESC"
            return self.execute_query(query, (user_id, account_id), fetch=True)
        else:
            query = "SELECT * FROM imported_transactions WHERE user_id = %s ORDER BY txn_date DESC"
            return self.execute_query(query, (user_id,), fetch=True)

    def add_manual_account(self, user_id, account_name, opening_balance):
        """Add a manual account for the user"""
        query = """
            INSERT INTO manual_accounts
            (user_id, account_name, opening_balance)
            VALUES (%s, %s, %s)
        """
        return self.execute_insert(query, (user_id, account_name, opening_balance))

    def get_user_manual_accounts(self, user_id):
        """Get all manual accounts for a user"""
        query = "SELECT * FROM manual_accounts WHERE user_id = %s"
        return self.execute_query(query, (user_id,), fetch=True)

    def get_manual_accounts_balance(self, user_id):
        """Get total manual accounts balance for a user"""
        query = "SELECT SUM(opening_balance) AS total_balance FROM manual_accounts WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0]['total_balance'] if result and result[0]['total_balance'] else 0.0

    def get_manual_account_balance(self, account_id):
        """Get balance of a specific manual account"""
        query = "SELECT opening_balance FROM manual_accounts WHERE manual_account_id = %s"
        result = self.execute_query(query, (account_id,), fetch=True)
        return result[0]['opening_balance'] if result else 0.0

    def update_manual_account_balance(self, account_id, new_balance):
        """Update manual account balance"""
        query = "UPDATE manual_accounts SET opening_balance = %s WHERE manual_account_id = %s"
        return self.execute_query(query, (new_balance, account_id))

    def add_manual_account_transaction(self, account_id, txn_type, amount, balance_after, category, source):
        """Add transaction record for manual account"""
        query = """
            INSERT INTO manual_account_transactions
            (account_id, type, amount, balance_after, category, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_insert(query, (account_id, txn_type, amount, balance_after, category, source))

    def get_bank_account_balance(self, account_id):
        """Get balance of a specific bank account"""
        query = "SELECT balance FROM bank_accounts WHERE account_id = %s"
        result = self.execute_query(query, (account_id,), fetch=True)
        return result[0]['balance'] if result else 0.0

    def update_bank_account_balance(self, account_id, new_balance):
        """Update bank account balance"""
        query = "UPDATE bank_accounts SET balance = %s WHERE account_id = %s"
        return self.execute_query(query, (new_balance, account_id))

    def add_bank_transaction(self, account_id, txn_type, amount, balance_after, category, source):
        """Add transaction record for bank account"""
        query = """
            INSERT INTO bank_transactions
            (account_id, type, amount, balance_after, category, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_insert(query, (account_id, txn_type, amount, balance_after, category, source))

    def get_investment_account_value(self, account_id):
        """Get current value of a specific investment account"""
        query = "SELECT current_value FROM investment_accounts WHERE investment_id = %s"
        result = self.execute_query(query, (account_id,), fetch=True)
        return result[0]['current_value'] if result else 0.0

    def update_investment_account_value(self, account_id, new_value):
        """Update investment account current value"""
        query = "UPDATE investment_accounts SET current_value = %s WHERE investment_id = %s"
        return self.execute_query(query, (new_value, account_id))

    def update_investment_quantity(self, account_id, new_quantity):
        """Update investment account quantity"""
        query = "UPDATE investment_accounts SET quantity = %s WHERE investment_id = %s"
        return self.execute_query(query, (new_quantity, account_id))

    def update_investment_account(self, account_id, new_quantity, new_invested_amount, new_current_value):
        """Update investment account quantity, invested amount, and current value"""
        query = "UPDATE investment_accounts SET quantity = %s, invested_amount = %s, current_value = %s WHERE investment_id = %s"
        return self.execute_query(query, (new_quantity, new_invested_amount, new_current_value, account_id))

    def update_investment_price_data(self, account_id, new_price_per_share, price_change_percentage):
        """Update investment price data and change percentage"""
        query = "UPDATE investment_accounts SET price_per_share = %s, price_change_percentage = %s, last_price_update = NOW() WHERE investment_id = %s"
        return self.execute_query(query, (new_price_per_share, price_change_percentage, account_id))

    def remove_investment_account(self, investment_id):
        """Remove an investment account"""
        query = "DELETE FROM investment_accounts WHERE investment_id = %s"
        return self.execute_query(query, (investment_id,))

    def remove_manual_account(self, manual_account_id):
        """Remove a manual account"""
        query = "DELETE FROM manual_accounts WHERE manual_account_id = %s"
        return self.execute_query(query, (manual_account_id,))

    def add_investment_transaction(self, account_id, txn_type, amount, value_after, category, source):
        """Add transaction record for investment account"""
        query = """
            INSERT INTO investment_transactions
            (account_id, type, amount, value_after, category, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        return self.execute_insert(query, (account_id, txn_type, amount, value_after, category, source))

    def add_financial_goal(self, user_id, account_type, account_id, goal_name, target_amount, months_to_achieve, monthly_savings):
        """Add a new financial goal"""
        query = """
            INSERT INTO financial_goals
            (user_id, account_type, account_id, goal_name, target_amount, months_to_achieve, monthly_savings)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        return self.execute_insert(query, (user_id, account_type, account_id, goal_name, target_amount, months_to_achieve, monthly_savings))

    def get_user_financial_goals(self, user_id):
        """Get all financial goals for a user"""
        query = "SELECT * FROM financial_goals WHERE user_id = %s ORDER BY created_at DESC"
        return self.execute_query(query, (user_id,), fetch=True)

    def update_goal_progress(self, goal_id, new_savings):
        """Update goal current savings"""
        query = "UPDATE financial_goals SET current_savings = %s WHERE goal_id = %s"
        return self.execute_query(query, (new_savings, goal_id))

    def add_goal_contribution(self, goal_id, amount, category, source):
        """Add a contribution record to a financial goal"""
        query = """
            INSERT INTO goal_contributions
            (goal_id, amount, category, source)
            VALUES (%s, %s, %s, %s)
        """
        return self.execute_insert(query, (goal_id, amount, category, source))

    def update_goal_months(self, goal_id, additional_months):
        """Add months to a financial goal"""
        query = "UPDATE financial_goals SET months_to_achieve = months_to_achieve + %s WHERE goal_id = %s"
        return self.execute_query(query, (additional_months, goal_id))

    def stop_financial_goal(self, goal_id):
        """Stop a financial goal"""
        query = "UPDATE financial_goals SET status = 'STOPPED' WHERE goal_id = %s"
        return self.execute_query(query, (goal_id,))

    def reactivate_financial_goal(self, goal_id):
        """Reactivate a stopped financial goal"""
        query = "UPDATE financial_goals SET status = 'ACTIVE' WHERE goal_id = %s"
        return self.execute_query(query, (goal_id,))

    def update_goal_target_amount(self, goal_id, new_target_amount):
        """Update the target amount of a financial goal"""
        query = "UPDATE financial_goals SET target_amount = %s WHERE goal_id = %s"
        return self.execute_query(query, (new_target_amount, goal_id))

    def update_goal_monthly_savings(self, goal_id, new_monthly_savings):
        """Update the monthly savings amount of a financial goal"""
        query = "UPDATE financial_goals SET monthly_savings = %s WHERE goal_id = %s"
        return self.execute_query(query, (new_monthly_savings, goal_id))

    def get_user_transaction_history(self, user_id, date_filter=None, limit=50):
        """Get recent transaction history for a user across all account types"""
        # Build parameterized query to prevent SQL injection
        params = [user_id]
        
        # Build date condition with proper parameterization
        if date_filter:
            if len(date_filter) == 7:  # YYYY-MM format
                date_condition = "AND DATE_FORMAT(date, '%Y-%m') = %s"
                date_params = [date_filter] * 4  # One for each UNION section
            elif len(date_filter) == 4:  # YYYY format
                date_condition = "AND YEAR(date) = %s"
                date_params = [int(date_filter)] * 4
            else:
                date_condition = ""
                date_params = []
        else:
            date_condition = ""
            date_params = []

        query = f"""
            SELECT
                'wallet' as account_type,
                wt.txn_id as transaction_id,
                wt.type,
                wt.amount,
                wt.balance_after,
                wt.date,
                NULL as account_name,
                NULL as category,
                NULL as source
            FROM wallet_transactions wt
            WHERE wt.user_id = %s {date_condition}

            UNION ALL

            SELECT
                'bank' as account_type,
                bt.txn_id as transaction_id,
                bt.type,
                bt.amount,
                bt.balance_after,
                bt.date,
                ba.nickname as account_name,
                bt.category,
                bt.source
            FROM bank_transactions bt
            JOIN bank_accounts ba ON bt.account_id = ba.account_id
            WHERE ba.user_id = %s {date_condition}

            UNION ALL

            SELECT
                'investment' as account_type,
                it.txn_id as transaction_id,
                it.type,
                it.amount,
                it.value_after as balance_after,
                it.date,
                ia.investment_name as account_name,
                it.category,
                it.source
            FROM investment_transactions it
            JOIN investment_accounts ia ON it.account_id = ia.investment_id
            WHERE ia.user_id = %s {date_condition}

            UNION ALL

            SELECT
                'manual' as account_type,
                mat.txn_id as transaction_id,
                mat.type,
                mat.amount,
                mat.balance_after,
                mat.date,
                ma.account_name,
                mat.category,
                mat.source
            FROM manual_account_transactions mat
            JOIN manual_accounts ma ON mat.account_id = ma.manual_account_id
            WHERE ma.user_id = %s {date_condition}

            ORDER BY date DESC
            LIMIT %s
        """
        
        # Build params: user_id + optional date for each section + limit
        if date_params:
            final_params = (user_id, date_params[0], user_id, date_params[1], 
                           user_id, date_params[2], user_id, date_params[3], limit)
        else:
            final_params = (user_id, user_id, user_id, user_id, limit)
        
        return self.execute_query(query, final_params, fetch=True)

    def get_investment_account_details(self, transaction_id):
        """Get investment account details for a specific transaction"""
        query = """
            SELECT
                ia.investment_type,
                ia.platform,
                ia.quantity,
                ia.price_per_share
            FROM investment_accounts ia
            JOIN investment_transactions it ON ia.investment_id = it.account_id
            WHERE it.txn_id = %s
        """
        result = self.execute_query(query, (transaction_id,), fetch=True)
        return result[0] if result else None

    def get_investment_account_by_id(self, investment_id):
        """Get investment account details by investment_id"""
        query = "SELECT * FROM investment_accounts WHERE investment_id = %s"
        result = self.execute_query(query, (investment_id,), fetch=True)
        return result[0] if result else None

    def get_user_cash_balance(self, user_id):
        """Get cash balance for user (same as wallet balance)"""
        return self.get_user_balance(user_id)

    def create_user_cash_account(self, user_id):
        """Create cash account for user (ensure wallet exists)"""
        # Wallet is always available, so just ensure balance is set
        balance = self.get_user_balance(user_id)
        if balance is None:
            self.update_user_balance(user_id, 0.00)

    def get_user_budgets(self, user_id, month_key=None):
        """Get all budgets for a user, optionally filtered by month or year
        
        Args:
            user_id: User ID
            month_key: 'YYYY-MM' for specific month, 'YYYY' for full year, or None for all
        """
        if month_key:
            if len(month_key) == 4:  # Year format (YYYY) - return all budgets for that year
                query = """
                    SELECT *, CONCAT(year, '-', LPAD(month, 2, '0')) as month_str 
                    FROM budget 
                    WHERE user_id = %s AND year = %s 
                    ORDER BY month, category
                """
                return self.execute_query(query, (user_id, int(month_key)), fetch=True)
            else:  # Month format (YYYY-MM) - return ONLY that specific month's budgets
                year, month = month_key.split('-')
                query = """
                    SELECT *, CONCAT(year, '-', LPAD(month, 2, '0')) as month_str 
                    FROM budget 
                    WHERE user_id = %s AND year = %s AND month = %s 
                    ORDER BY category
                """
                return self.execute_query(query, (user_id, int(year), int(month)), fetch=True)
        else:
            query = """
                SELECT *, CONCAT(year, '-', LPAD(month, 2, '0')) as month_str 
                FROM budget 
                WHERE user_id = %s 
                ORDER BY year, month, category
            """
            return self.execute_query(query, (user_id,), fetch=True)

    def get_top_individual_expenses(self, user_id, time_filter, category_filter=None, subtype_filter=None, top_n=10):
        """
        Get top individual expenses (not grouped) sorted by amount DESC

        Args:
            user_id: User ID
            time_filter: 'YYYY-MM' for month, 'YYYY' for year
            category_filter: Category name or None for all
            subtype_filter: Subtype for 'Others' category
            top_n: Number of results

        Returns:
            List of individual expense records
        """
        try:
            params = [user_id]

            # Build date condition
            if len(time_filter) == 7:  # YYYY-MM
                date_condition = "DATE_FORMAT(date, '%Y-%m') = %s"
                params.append(time_filter)
            elif len(time_filter) == 4:  # YYYY
                date_condition = "YEAR(date) = %s"
                params.append(int(time_filter))
            else:
                return []

            # Build category condition
            category_condition = ""
            if category_filter:
                if category_filter.lower() == "others" and subtype_filter:
                    category_condition = "AND category = %s AND subtype = %s"
                    params.append("Others")
                    params.append(subtype_filter)
                elif category_filter.lower() == "others":
                    category_condition = "AND category = %s"
                    params.append("Others")
                else:
                    category_condition = "AND category = %s"
                    params.append(category_filter)

            params.append(top_n)

            query = f"""
                SELECT 
                    expense_id,
                    amount,
                    category,
                    COALESCE(subtype, '') as subtype,
                    COALESCE(description, 'No Description') as description,
                    DATE_FORMAT(date, '%Y-%m-%d') as expense_date
                FROM expenses
                WHERE user_id = %s
                AND {date_condition}
                {category_condition}
                ORDER BY amount DESC
                LIMIT %s
            """

            results = self.execute_query(query, tuple(params), fetch=True)

            if not results:
                return []

            expenses = []
            for row in results:
                # Build display name
                if row['category'] == 'Others' and row['subtype']:
                    display_category = f"Others - {row['subtype']}"
                else:
                    display_category = row['category']

                expenses.append({
                    'id': row['expense_id'],
                    'description': row['description'],
                    'category': display_category,
                    'amount': float(row['amount']),
                    'date': row['expense_date']
                })

            return expenses

        except Exception as e:
            print(f"Error getting top individual expenses: {e}")
            return []

    def get_top_expenses(self, user_id, time_filter, category_filter=None, top_n=10):
        """
        Get top expenses based on time and category filters

        Args:
            user_id: User ID
            time_filter: 'YYYY-MM' for month, 'YYYY' for year
            category_filter: Category name or None for all categories
            top_n: Number of top expenses to return

        Returns:
            List of expense dictionaries with total_amount and display_name
        """
        try:
            params = [user_id]
            
            # Build date condition using parameterized queries
            if len(time_filter) == 7:  # YYYY-MM format
                date_condition = "DATE_FORMAT(e.date, '%Y-%m') = %s"
                params.append(time_filter)
            elif len(time_filter) == 4:  # YYYY format
                date_condition = "YEAR(e.date) = %s"
                params.append(int(time_filter))
            else:
                return []

            # Build category condition and grouping logic
            category_condition = ""
            group_by = ""
            select_fields = ""

            if category_filter:
                if category_filter.lower() == "others":
                    # Special handling for Others - group by subtype
                    category_condition = "AND e.category = %s"
                    params.append("Others")
                    group_by = "COALESCE(e.subtype, 'General')"
                    select_fields = "COALESCE(e.subtype, 'General') as display_name"
                else:
                    # Specific category - group by description
                    category_condition = "AND e.category = %s"
                    params.append(category_filter)
                    group_by = "COALESCE(e.description, 'No Description')"
                    select_fields = "COALESCE(e.description, 'No Description') as display_name"
            else:
                # All categories - group by category
                group_by = "e.category"
                select_fields = "e.category as display_name"

            # Add limit parameter
            params.append(top_n)

            # Build query with proper parameterization
            query = f"""
                SELECT
                    {select_fields},
                    SUM(e.amount) as total_amount,
                    COUNT(*) as transaction_count
                FROM expenses e
                WHERE e.user_id = %s
                AND {date_condition}
                {category_condition}
                GROUP BY {group_by}
                HAVING SUM(e.amount) > 0
                ORDER BY total_amount DESC
                LIMIT %s
            """

            results = self.execute_query(query, tuple(params), fetch=True)

            # Handle None or empty results
            if not results:
                return []

            # Format results
            top_expenses = []
            for row in results:
                display_name = row['display_name'] or 'Unknown'
                if category_filter and category_filter.lower() == "others":
                    display_name = f"Others - {display_name}"

                top_expenses.append({
                    'display_name': display_name,
                    'total_amount': float(row['total_amount'] or 0),
                    'transaction_count': row['transaction_count'] or 0
                })

            return top_expenses

        except Exception as e:
            print(f"Error getting top expenses: {e}")
            return []
