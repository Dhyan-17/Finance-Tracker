"""
SQLite3 Database Manager
Production-grade database layer with connection pooling and transactions
"""

import sqlite3
import os
import threading
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json

class Database:
    """Thread-safe SQLite database manager with connection pooling"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
            
        self.db_path = db_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'fintech.db'
        )
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Thread-local storage for connections
        self._local = threading.local()
        
        # Initialize database
        self._init_database()
        self._initialized = True
    
    def _init_database(self):
        """Initialize database with schema"""
        schema_path = os.path.join(
            os.path.dirname(__file__),
            'schema.sql'
        )
        
        with self.get_connection() as conn:
            # Enable foreign keys and WAL mode
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA busy_timeout = 5000")
            
            # Load and execute schema
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema = f.read()
                conn.executescript(schema)
                conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection (thread-safe)"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
        
        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            raise
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
    
    def execute(self, query: str, params: tuple = None, fetch: bool = False) -> Union[List[Dict], int]:
        """Execute a query with optional parameters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                
                if fetch:
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
                else:
                    conn.commit()
                    return cursor.rowcount
            finally:
                cursor.close()
    
    def execute_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Execute a query and return single result"""
        result = self.execute(query, params, fetch=True)
        return result[0] if result else None
    
    def execute_insert(self, query: str, params: tuple = None) -> Optional[int]:
        """Execute an insert query and return last row id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.lastrowid
            finally:
                cursor.close()
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute a query with multiple parameter sets"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount
            finally:
                cursor.close()
    
    # ============================================================
    # UTILITY METHODS
    # ============================================================
    
    @staticmethod
    def to_paise(amount: float) -> int:
        """Convert rupees to paise (integer storage)"""
        return int(round(amount * 100))
    
    @staticmethod
    def to_rupees(paise: int) -> float:
        """Convert paise to rupees for display"""
        return paise / 100.0 if paise else 0.0
    
    @staticmethod
    def now() -> str:
        """Get current datetime as ISO string"""
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def today() -> str:
        """Get current date as ISO string"""
        return datetime.now().strftime('%Y-%m-%d')
    
    # ============================================================
    # AUDIT LOGGING
    # ============================================================
    
    def log_action(
        self,
        actor_type: str,
        actor_id: int,
        action: str,
        entity_type: str = None,
        entity_id: int = None,
        old_values: Dict = None,
        new_values: Dict = None,
        severity: str = 'INFO'
    ):
        """Log an action to the audit log"""
        query = """
            INSERT INTO audit_logs 
            (actor_type, actor_id, action, entity_type, entity_id, 
             old_values, new_values, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.execute_insert(query, (
            actor_type,
            actor_id,
            action,
            entity_type,
            entity_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            severity
        ))
    
    # ============================================================
    # USER OPERATIONS
    # ============================================================
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return self.execute_one(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,)
        )
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email (case-insensitive)"""
        return self.execute_one(
            "SELECT * FROM users WHERE email = ? COLLATE NOCASE",
            (email,)
        )
    
    def get_user_by_mobile(self, mobile: str) -> Optional[Dict]:
        """Get user by mobile number"""
        return self.execute_one(
            "SELECT * FROM users WHERE mobile = ?",
            (mobile,)
        )
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        return self.execute_one(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
            (username,)
        )
    
    def user_exists(self, username: str = None, email: str = None, mobile: str = None) -> bool:
        """Check if user exists with given credentials"""
        conditions = []
        params = []
        
        if username:
            conditions.append("username = ? COLLATE NOCASE")
            params.append(username)
        if email:
            conditions.append("email = ? COLLATE NOCASE")
            params.append(email)
        if mobile:
            conditions.append("mobile = ?")
            params.append(mobile)
        
        if not conditions:
            return False
        
        query = f"SELECT 1 FROM users WHERE {' OR '.join(conditions)} LIMIT 1"
        result = self.execute_one(query, tuple(params))
        return result is not None
    
    def create_user(
        self,
        username: str,
        password_hash: str,
        email: str,
        mobile: str
    ) -> Optional[int]:
        """Create a new user"""
        query = """
            INSERT INTO users (username, password_hash, email, mobile)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_insert(query, (username, password_hash, email, mobile))
    
    def update_user_balance(self, user_id: int, new_balance: int) -> bool:
        """Update user wallet balance (in paise)"""
        result = self.execute(
            "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
            (new_balance, user_id)
        )
        return result > 0
    
    def get_user_balance(self, user_id: int) -> int:
        """Get user wallet balance in paise"""
        result = self.execute_one(
            "SELECT wallet_balance FROM users WHERE user_id = ?",
            (user_id,)
        )
        return result['wallet_balance'] if result else 0
    
    def update_user_status(self, user_id: int, status: str) -> bool:
        """Update user account status"""
        result = self.execute(
            "UPDATE users SET status = ? WHERE user_id = ?",
            (status, user_id)
        )
        return result > 0
    
    def get_all_users(self, status: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all users with optional status filter"""
        if status:
            return self.execute(
                """SELECT user_id, username, email, mobile, wallet_balance, 
                          status, kyc_verified, created_at, last_login
                   FROM users WHERE status = ?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                (status, limit, offset),
                fetch=True
            )
        return self.execute(
            """SELECT user_id, username, email, mobile, wallet_balance,
                      status, kyc_verified, created_at, last_login
               FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (limit, offset),
            fetch=True
        )
    
    # ============================================================
    # ADMIN OPERATIONS
    # ============================================================
    
    def get_admin_by_email(self, email: str) -> Optional[Dict]:
        """Get admin by email"""
        return self.execute_one(
            "SELECT * FROM admins WHERE email = ? COLLATE NOCASE AND is_active = 1",
            (email,)
        )
    
    def get_admin_by_id(self, admin_id: int) -> Optional[Dict]:
        """Get admin by ID"""
        return self.execute_one(
            "SELECT * FROM admins WHERE admin_id = ?",
            (admin_id,)
        )
    
    def create_admin(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str = 'ADMIN'
    ) -> Optional[int]:
        """Create a new admin"""
        query = """
            INSERT INTO admins (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """
        return self.execute_insert(query, (name, email, password_hash, role))
    
    # ============================================================
    # BANK ACCOUNT OPERATIONS
    # ============================================================
    
    def get_user_bank_accounts(self, user_id: int) -> List[Dict]:
        """Get all bank accounts for a user"""
        return self.execute(
            """SELECT ba.*, mb.bank_name, mb.ifsc_code 
               FROM bank_accounts ba
               LEFT JOIN master_banks mb ON ba.bank_id = mb.bank_id
               WHERE ba.user_id = ?
               ORDER BY ba.is_primary DESC, ba.created_at DESC""",
            (user_id,),
            fetch=True
        )
    
    def get_bank_account_by_id(self, account_id: int, user_id: int = None) -> Optional[Dict]:
        """Get bank account by ID with optional user validation"""
        if user_id:
            return self.execute_one(
                """SELECT ba.*, mb.bank_name, mb.ifsc_code 
                   FROM bank_accounts ba
                   LEFT JOIN master_banks mb ON ba.bank_id = mb.bank_id
                   WHERE ba.account_id = ? AND ba.user_id = ?""",
                (account_id, user_id)
            )
        return self.execute_one(
            """SELECT ba.*, mb.bank_name, mb.ifsc_code 
               FROM bank_accounts ba
               LEFT JOIN master_banks mb ON ba.bank_id = mb.bank_id
               WHERE ba.account_id = ?""",
            (account_id,)
        )
    
    def get_total_bank_balance(self, user_id: int) -> int:
        """Get total bank balance for user in paise"""
        result = self.execute_one(
            "SELECT COALESCE(SUM(balance), 0) as total FROM bank_accounts WHERE user_id = ?",
            (user_id,)
        )
        return result['total'] if result else 0
    
    def update_bank_account_balance(self, account_id: int, new_balance: int, user_id: int = None) -> bool:
        """Update bank account balance with optional ownership check"""
        if user_id:
            result = self.execute(
                "UPDATE bank_accounts SET balance = ? WHERE account_id = ? AND user_id = ?",
                (new_balance, account_id, user_id)
            )
        else:
            result = self.execute(
                "UPDATE bank_accounts SET balance = ? WHERE account_id = ?",
                (new_balance, account_id)
            )
        return result > 0
    
    def get_master_banks(self) -> List[Dict]:
        """Get all master banks"""
        return self.execute(
            "SELECT * FROM master_banks WHERE is_active = 1 ORDER BY bank_name",
            fetch=True
        )
    
    # ============================================================
    # EXPENSE & INCOME OPERATIONS
    # ============================================================
    
    def add_expense(
        self,
        user_id: int,
        amount: int,
        category: str,
        payment_mode: str = 'UPI',
        account_type: str = 'WALLET',
        account_id: int = None,
        description: str = None,
        subcategory: str = None,
        merchant: str = None,
        date: str = None
    ) -> Optional[int]:
        """Add an expense record"""
        query = """
            INSERT INTO expenses 
            (user_id, amount, category, subcategory, description, 
             payment_mode, account_type, account_id, merchant, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (
            user_id, amount, category, subcategory, description,
            payment_mode, account_type, account_id, merchant,
            date or self.now()
        ))
    
    def add_income(
        self,
        user_id: int,
        amount: int,
        source: str,
        category: str = None,
        account_type: str = 'WALLET',
        account_id: int = None,
        description: str = None,
        date: str = None
    ) -> Optional[int]:
        """Add an income record"""
        query = """
            INSERT INTO income 
            (user_id, amount, source, category, description, account_type, account_id, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (
            user_id, amount, source, category, description,
            account_type, account_id, date or self.now()
        ))
    
    def get_user_expenses(
        self,
        user_id: int,
        start_date: str = None,
        end_date: str = None,
        category: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get user expenses with optional filters"""
        conditions = ["user_id = ?"]
        params = [user_id]
        
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        params.append(limit)
        
        query = f"""
            SELECT * FROM expenses 
            WHERE {' AND '.join(conditions)}
            ORDER BY date DESC LIMIT ?
        """
        return self.execute(query, tuple(params), fetch=True)
    
    def get_user_income(
        self,
        user_id: int,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get user income with optional filters"""
        conditions = ["user_id = ?"]
        params = [user_id]
        
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        
        params.append(limit)
        
        query = f"""
            SELECT * FROM income 
            WHERE {' AND '.join(conditions)}
            ORDER BY date DESC LIMIT ?
        """
        return self.execute(query, tuple(params), fetch=True)
    
    def get_expense_categories(self) -> List[Dict]:
        """Get all expense categories"""
        return self.execute(
            "SELECT * FROM expense_categories ORDER BY name",
            fetch=True
        )
    
    # ============================================================
    # BUDGET OPERATIONS
    # ============================================================
    
    def get_user_budgets(self, user_id: int, year: int = None, month: int = None) -> List[Dict]:
        """Get user budgets with optional year/month filter"""
        if year and month:
            return self.execute(
                "SELECT * FROM budgets WHERE user_id = ? AND year = ? AND month = ?",
                (user_id, year, month),
                fetch=True
            )
        return self.execute(
            "SELECT * FROM budgets WHERE user_id = ? ORDER BY year DESC, month DESC",
            (user_id,),
            fetch=True
        )
    
    def set_budget(
        self,
        user_id: int,
        category: str,
        limit_amount: int,
        year: int,
        month: int,
        alert_threshold: float = 80.0
    ) -> Optional[int]:
        """Set or update a budget"""
        query = """
            INSERT INTO budgets (user_id, category, limit_amount, year, month, alert_threshold)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, category, year, month) 
            DO UPDATE SET limit_amount = excluded.limit_amount, 
                          alert_threshold = excluded.alert_threshold
        """
        return self.execute_insert(query, (
            user_id, category, limit_amount, year, month, alert_threshold
        ))
    
    def get_budget_spending(self, user_id: int, category: str, year: int, month: int) -> int:
        """Get actual spending for a budget category"""
        month_str = f"{year}-{month:02d}"
        result = self.execute_one(
            """SELECT COALESCE(SUM(amount), 0) as spent 
               FROM expenses 
               WHERE user_id = ? AND category = ? 
               AND strftime('%Y-%m', date) = ?""",
            (user_id, category, month_str)
        )
        return result['spent'] if result else 0
    
    # ============================================================
    # FINANCIAL GOALS OPERATIONS
    # ============================================================
    
    def get_user_goals(self, user_id: int, status: str = None) -> List[Dict]:
        """Get user financial goals"""
        if status:
            return self.execute(
                "SELECT * FROM financial_goals WHERE user_id = ? AND status = ? ORDER BY priority, target_date",
                (user_id, status),
                fetch=True
            )
        return self.execute(
            "SELECT * FROM financial_goals WHERE user_id = ? ORDER BY status, priority, target_date",
            (user_id,),
            fetch=True
        )
    
    def create_goal(
        self,
        user_id: int,
        goal_name: str,
        target_amount: int,
        monthly_contribution: int = None,
        target_date: str = None,
        priority: str = 'MEDIUM'
    ) -> Optional[int]:
        """Create a new financial goal"""
        query = """
            INSERT INTO financial_goals 
            (user_id, goal_name, target_amount, monthly_contribution, target_date, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (
            user_id, goal_name, target_amount, monthly_contribution, target_date, priority
        ))
    
    def update_goal_savings(self, goal_id: int, new_savings: int, user_id: int = None) -> bool:
        """Update goal current savings with ownership check"""
        if user_id:
            result = self.execute(
                "UPDATE financial_goals SET current_savings = ? WHERE goal_id = ? AND user_id = ?",
                (new_savings, goal_id, user_id)
            )
        else:
            result = self.execute(
                "UPDATE financial_goals SET current_savings = ? WHERE goal_id = ?",
                (new_savings, goal_id)
            )
        return result > 0
    
    # ============================================================
    # INVESTMENT OPERATIONS
    # ============================================================
    
    def get_market_assets(self, asset_type: str = None) -> List[Dict]:
        """Get market assets with optional type filter"""
        if asset_type:
            return self.execute(
                "SELECT * FROM market_assets WHERE asset_type = ? AND is_active = 1 ORDER BY asset_name",
                (asset_type,),
                fetch=True
            )
        return self.execute(
            "SELECT * FROM market_assets WHERE is_active = 1 ORDER BY asset_type, asset_name",
            fetch=True
        )
    
    def get_asset_by_id(self, asset_id: int) -> Optional[Dict]:
        """Get market asset by ID"""
        return self.execute_one(
            "SELECT * FROM market_assets WHERE asset_id = ?",
            (asset_id,)
        )
    
    def get_user_investments(self, user_id: int) -> List[Dict]:
        """Get user investment portfolio"""
        return self.execute(
            """SELECT ui.*, ma.asset_name, ma.asset_symbol, ma.asset_type,
                      ma.current_price, ma.day_change_percent,
                      (ui.units_owned * ma.current_price) as current_value,
                      ((ui.units_owned * ma.current_price) - ui.invested_amount) as profit_loss
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               WHERE ui.user_id = ?
               ORDER BY current_value DESC""",
            (user_id,),
            fetch=True
        )
    
    def get_total_investment_value(self, user_id: int) -> Dict:
        """Get total investment summary for user"""
        result = self.execute_one(
            """SELECT 
                   COALESCE(SUM(ui.invested_amount), 0) as total_invested,
                   COALESCE(SUM(ui.units_owned * ma.current_price), 0) as current_value
               FROM user_investments ui
               JOIN market_assets ma ON ui.asset_id = ma.asset_id
               WHERE ui.user_id = ?""",
            (user_id,)
        )
        return result if result else {'total_invested': 0, 'current_value': 0}
    
    def update_asset_price(self, asset_id: int, new_price: int, change_percent: float = 0) -> bool:
        """Update market asset price"""
        result = self.execute(
            """UPDATE market_assets 
               SET previous_price = current_price,
                   current_price = ?,
                   day_change_percent = ?,
                   last_updated = datetime('now')
               WHERE asset_id = ?""",
            (new_price, change_percent, asset_id)
        )
        return result > 0
    
    # ============================================================
    # TRANSACTION HISTORY
    # ============================================================
    
    def add_wallet_transaction(
        self,
        user_id: int,
        txn_type: str,
        amount: int,
        balance_after: int,
        reference_type: str = None,
        reference_id: int = None,
        description: str = None
    ) -> Optional[int]:
        """Add a wallet transaction record"""
        query = """
            INSERT INTO wallet_transactions 
            (user_id, txn_type, amount, balance_after, reference_type, reference_id, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (
            user_id, txn_type, amount, balance_after, reference_type, reference_id, description
        ))
    
    def get_wallet_transactions(
        self,
        user_id: int,
        txn_type: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get wallet transaction history"""
        conditions = ["user_id = ?"]
        params = [user_id]
        
        if txn_type:
            conditions.append("txn_type = ?")
            params.append(txn_type)
        if start_date:
            conditions.append("date >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("date <= ?")
            params.append(end_date)
        
        params.append(limit)
        
        query = f"""
            SELECT * FROM wallet_transactions 
            WHERE {' AND '.join(conditions)}
            ORDER BY date DESC LIMIT ?
        """
        return self.execute(query, tuple(params), fetch=True)
    
    # ============================================================
    # FRAUD DETECTION
    # ============================================================
    
    def add_fraud_flag(
        self,
        user_id: int,
        rule_name: str,
        severity: str,
        description: str,
        reference_type: str = None,
        reference_id: int = None,
        amount: int = None
    ) -> Optional[int]:
        """Add a fraud flag"""
        query = """
            INSERT INTO fraud_flags 
            (user_id, rule_name, severity, description, reference_type, reference_id, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (
            user_id, rule_name, severity, description, reference_type, reference_id, amount
        ))
    
    def get_fraud_flags(
        self,
        user_id: int = None,
        status: str = None,
        severity: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get fraud flags with optional filters"""
        conditions = []
        params = []
        
        if user_id:
            conditions.append("ff.user_id = ?")
            params.append(user_id)
        if status:
            conditions.append("ff.status = ?")
            params.append(status)
        if severity:
            conditions.append("ff.severity = ?")
            params.append(severity)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        params.append(limit)
        
        query = f"""
            SELECT ff.*, u.username, u.email 
            FROM fraud_flags ff
            JOIN users u ON ff.user_id = u.user_id
            {where_clause}
            ORDER BY ff.created_at DESC LIMIT ?
        """
        return self.execute(query, tuple(params), fetch=True)
    
    def get_fraud_rules(self, active_only: bool = True) -> List[Dict]:
        """Get fraud detection rules"""
        if active_only:
            return self.execute(
                "SELECT * FROM fraud_rules WHERE is_active = 1",
                fetch=True
            )
        return self.execute("SELECT * FROM fraud_rules", fetch=True)
    
    # ============================================================
    # NOTIFICATIONS
    # ============================================================
    
    def add_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = 'INFO',
        category: str = None,
        action_url: str = None
    ) -> Optional[int]:
        """Add a notification"""
        query = """
            INSERT INTO notifications 
            (user_id, title, message, notification_type, category, action_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        return self.execute_insert(query, (
            user_id, title, message, notification_type, category, action_url
        ))
    
    def get_user_notifications(self, user_id: int, unread_only: bool = False, limit: int = 50) -> List[Dict]:
        """Get user notifications"""
        if unread_only:
            return self.execute(
                "SELECT * FROM notifications WHERE user_id = ? AND is_read = 0 ORDER BY created_at DESC LIMIT ?",
                (user_id, limit),
                fetch=True
            )
        return self.execute(
            "SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
            fetch=True
        )
    
    def mark_notification_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        result = self.execute(
            "UPDATE notifications SET is_read = 1 WHERE notification_id = ? AND user_id = ?",
            (notification_id, user_id)
        )
        return result > 0


# Singleton instance
db = Database()
