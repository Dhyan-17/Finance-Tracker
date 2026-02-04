"""
Admin Panel for Finance Tracker
Complete admin management system for fintech application
"""

import hashlib
from datetime import datetime, timedelta
from validations import Validation
from market_engine import MarketEngine
from fintech_analytics import FintechAnalytics


class AdminManager:
    """Complete Admin Panel Management"""

    def __init__(self, db):
        self.db = db
        self.validation = Validation()
        self.market_engine = MarketEngine(db)
        self.analytics = FintechAnalytics(db)
        self.logged_in_admin = None
        self.logged_in_admin_id = None
        self.max_login_attempts = 3

    # ==================================================
    # ADMIN LOGIN (Email + Password, Max 3 Attempts)
    # ==================================================
    def admin_login(self):
        """Secure admin login with email and password"""
        box = 60
        print("+" + "-" * box + "+")
        print(f"| {'ADMIN LOGIN':<58} |")
        print("+" + "-" * box + "+")

        attempts = 0
        while attempts < self.max_login_attempts:
            try:
                # Email input (case-insensitive)
                email = self.validation.get_valid_input(
                    "Enter Admin Email: ",
                    lambda x: '@' in x and len(x) > 5,
                    "❌ Invalid email format!"
                ).strip().lower()

                # Password input
                password = self.validation.get_valid_input(
                    "Enter Password: ",
                    lambda x: len(x.strip()) > 0,
                    "❌ Password cannot be empty!"
                )

                # Query admin by email (parameterized query)
                admin = self.db.execute_query(
                    "SELECT * FROM admin WHERE LOWER(email) = %s",
                    (email,),
                    fetch=True
                )

                if not admin:
                    attempts += 1
                    remaining = self.max_login_attempts - attempts
                    print(f"❌ Invalid credentials! {remaining} attempts remaining.")
                    if remaining == 0:
                        print("🔒 Account locked. Please try again later.")
                        self.db.log_action("System", f"Admin login blocked after 3 failed attempts for {email}")
                        return False
                    continue

                admin = admin[0]

                # Verify password (hashed comparison)
                hashed = hashlib.sha256(password.encode()).hexdigest()
                
                # Support both hashed and plain passwords for backward compatibility
                if admin["password"] != hashed and admin["password"] != password:
                    attempts += 1
                    remaining = self.max_login_attempts - attempts
                    print(f"❌ Invalid credentials! {remaining} attempts remaining.")
                    if remaining == 0:
                        print("🔒 Account locked. Please try again later.")
                        return False
                    continue

                # Successful login
                self.logged_in_admin = admin["name"]
                self.logged_in_admin_id = admin["admin_id"]

                self.db.log_action(
                    actor=f"Admin:{self.logged_in_admin}",
                    action="Admin logged in successfully"
                )

                print("+" + "-" * box + "+")
                print(f"| ✅ Welcome, {self.logged_in_admin:<45} |")
                print("+" + "-" * box + "+")
                return True

            except KeyboardInterrupt:
                print("\n❌ Login cancelled.")
                return False
            except Exception as e:
                print(f"❌ Login Error: {e}")
                return False

        return False

    # ==================================================
    # ADMIN DASHBOARD MENU
    # ==================================================
    def admin_menu_loop(self):
        """Main admin dashboard loop"""
        while True:
            try:
                self.display_admin_menu()
                choice = input("👉 Enter choice: ").strip()

                if not choice.isdigit():
                    self._invalid()
                    continue

                choice = int(choice)

                # User Management
                if choice == 1:
                    self.view_all_users()
                elif choice == 2:
                    self.search_user()
                elif choice == 3:
                    self.delete_user()
                elif choice == 4:
                    self.block_unblock_user()
                elif choice == 5:
                    self.reset_user_password()
                # Financial Monitoring
                elif choice == 6:
                    self.view_all_transactions()
                elif choice == 7:
                    self.view_all_budgets()
                elif choice == 8:
                    self.view_large_transactions()
                elif choice == 9:
                    self.view_overspending_users()
                # Investment & Market
                elif choice == 10:
                    self.view_market_overview()
                elif choice == 11:
                    self.update_market_prices()
                elif choice == 12:
                    self.view_top_investors()
                elif choice == 13:
                    self.view_net_worth_leaderboard()
                # Analytics & Reports
                elif choice == 14:
                    self.view_platform_dashboard()
                elif choice == 15:
                    self.view_top_categories()
                elif choice == 16:
                    self.view_monthly_growth()
                elif choice == 17:
                    self.view_system_logs()
                elif choice == 0:
                    print("\n👋 Logging out from Admin Panel...")
                    self.db.log_action(f"Admin:{self.logged_in_admin}", "Admin logged out")
                    self.logged_in_admin = None
                    self.logged_in_admin_id = None
                    break
                else:
                    self._invalid()

            except KeyboardInterrupt:
                print("\n👋 Admin session closed.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def display_admin_menu(self):
        """Display admin dashboard menu"""
        print("\n" + "=" * 60)
        print(f"{'FINTECH ADMIN PANEL':^60}")
        print(f"{'Logged in as: ' + self.logged_in_admin:^60}")
        print("=" * 60)
        print("+------+----------------------------------------------------+")
        print("|  #   | Option                                             |")
        print("+------+----------------------------------------------------+")
        print("|      | USER MANAGEMENT                                    |")
        print("+------+----------------------------------------------------+")
        print("|  1   | View All Users                                     |")
        print("|  2   | Search User by Email/ID                            |")
        print("|  3   | Delete User                                        |")
        print("|  4   | Block / Unblock User                               |")
        print("|  5   | Reset User Password                                |")
        print("+------+----------------------------------------------------+")
        print("|      | FINANCIAL MONITORING                               |")
        print("+------+----------------------------------------------------+")
        print("|  6   | View All Transactions                              |")
        print("|  7   | View All Budgets                                   |")
        print("|  8   | View Large Transactions (Fraud Detection)          |")
        print("|  9   | View Overspending Users                            |")
        print("+------+----------------------------------------------------+")
        print("|      | INVESTMENT & MARKET                                |")
        print("+------+----------------------------------------------------+")
        print("| 10   | View Market Overview                               |")
        print("| 11   | Update Market Prices (Simulate)                    |")
        print("| 12   | View Top Investors                                 |")
        print("| 13   | View Net Worth Leaderboard                         |")
        print("+------+----------------------------------------------------+")
        print("|      | ANALYTICS & REPORTS                                |")
        print("+------+----------------------------------------------------+")
        print("| 14   | Platform Summary Dashboard                         |")
        print("| 15   | Top Spending Categories                            |")
        print("| 16   | Monthly Growth Report                              |")
        print("| 17   | View System Logs                                   |")
        print("+------+----------------------------------------------------+")
        print("|  0   | Logout                                             |")
        print("+------+----------------------------------------------------+")

    # ==================================================
    # USER MANAGEMENT
    # ==================================================
    def view_all_users(self):
        """View all registered users"""
        users = self.db.execute_query(
            """SELECT user_id, username, email, mobile, wallet_balance, status, created_at
               FROM users ORDER BY user_id""",
            fetch=True
        )

        if not users:
            print("\n❌ No users found in the system.")
            return

        print("\n" + "=" * 100)
        print(f"{'ALL REGISTERED USERS':^100}")
        print("=" * 100)
        print(f"| {'ID':<4} | {'Username':<15} | {'Email':<28} | {'Mobile':<12} | {'Balance':>10} | {'Status':<8} |")
        print("-" * 100)
        
        for u in users:
            balance = float(u['wallet_balance'] or 0)
            print(f"| {u['user_id']:<4} | {u['username']:<15} | {u['email']:<28} | "
                  f"{u['mobile']:<12} | ₹{balance:>8.2f} | {u['status']:<8} |")
        
        print("=" * 100)
        print(f"Total Users: {len(users)}")

    def search_user(self):
        """Search user by email or ID"""
        print("\n+----------------------------------------+")
        print("|          SEARCH USER                   |")
        print("+----------------------------------------+")
        print("| 1. Search by User ID                   |")
        print("| 2. Search by Email                     |")
        print("+----------------------------------------+")

        choice = self.validation.get_valid_int(
            "Enter choice: ",
            lambda x: x in [1, 2],
            "❌ Invalid choice!"
        )

        user = None
        if choice == 1:
            user_id = self.validation.get_valid_int(
                "Enter User ID: ",
                lambda x: x > 0,
                "❌ Invalid User ID!"
            )
            user = self.db.get_user_by_id(user_id)
        else:
            email = input("Enter Email: ").strip().lower()
            user = self.db.get_user_by_email(email)

        if not user:
            print("❌ User not found.")
            return

        # Display user details
        print("\n" + "=" * 50)
        print(f"{'USER DETAILS':^50}")
        print("=" * 50)
        print(f"| User ID    : {user['user_id']}")
        print(f"| Username   : {user['username']}")
        print(f"| Email      : {user['email']}")
        print(f"| Mobile     : {user['mobile']}")
        print(f"| Balance    : ₹{float(user['wallet_balance'] or 0):.2f}")
        print(f"| Status     : {user['status']}")
        print(f"| Created    : {user['created_at']}")
        print("=" * 50)

        # Show user's accounts
        bank_accounts = self.db.get_user_bank_accounts(user['user_id'])
        if bank_accounts:
            print(f"\nBank Accounts ({len(bank_accounts)}):")
            for acc in bank_accounts:
                print(f"  - {acc['bank_name']}: ₹{float(acc['balance'] or 0):.2f}")

        # Show recent expenses
        expenses = self.db.execute_query(
            """SELECT category, SUM(amount) as total FROM expenses 
               WHERE user_id = %s GROUP BY category ORDER BY total DESC LIMIT 5""",
            (user['user_id'],), fetch=True
        )
        if expenses:
            print(f"\nTop Expense Categories:")
            for e in expenses:
                print(f"  - {e['category']}: ₹{float(e['total']):.2f}")

    def delete_user(self):
        """Delete a user from the system"""
        print("\n+----------------------------------------+")
        print("|          DELETE USER                   |")
        print("+----------------------------------------+")
        print("| ⚠️  WARNING: This action is permanent! |")
        print("+----------------------------------------+")

        user_id = self.validation.get_valid_int(
            "Enter User ID to delete: ",
            lambda x: x > 0,
            "❌ Invalid User ID!"
        )

        user = self.db.get_user_by_id(user_id)
        if not user:
            print("❌ User not found.")
            return

        print(f"\nUser to delete: {user['username']} ({user['email']})")
        print(f"Wallet Balance: ₹{float(user['wallet_balance'] or 0):.2f}")

        confirm = input("\n⚠️  Type 'DELETE' to confirm: ").strip()
        if confirm != 'DELETE':
            print("❌ Deletion cancelled.")
            return

        # Delete user (cascade will remove related records)
        self.db.execute_query(
            "DELETE FROM users WHERE user_id = %s",
            (user_id,)
        )

        self.db.log_action(
            f"Admin:{self.logged_in_admin}",
            f"Deleted user: {user['username']} (ID: {user_id})"
        )

        print(f"✅ User '{user['username']}' deleted successfully.")

    def block_unblock_user(self):
        """Block or unblock a user"""
        print("\n+----------------------------------------+")
        print("|       BLOCK / UNBLOCK USER             |")
        print("+----------------------------------------+")

        user_id = self.validation.get_valid_int(
            "Enter User ID: ",
            lambda x: x > 0,
            "❌ Invalid User ID!"
        )

        user = self.db.get_user_by_id(user_id)
        if not user:
            print("❌ User not found.")
            return

        current_status = user['status']
        new_status = "BLOCKED" if current_status == "ACTIVE" else "ACTIVE"

        print(f"\nUser: {user['username']}")
        print(f"Current Status: {current_status}")
        print(f"New Status: {new_status}")

        confirm = input(f"Change status to {new_status}? (y/n): ").lower().strip()
        if confirm != 'y':
            print("❌ Operation cancelled.")
            return

        self.db.execute_query(
            "UPDATE users SET status = %s WHERE user_id = %s",
            (new_status, user_id)
        )

        self.db.log_action(
            f"Admin:{self.logged_in_admin}",
            f"Changed user {user['username']} status: {current_status} -> {new_status}"
        )

        print(f"✅ User status updated to {new_status}")

    def reset_user_password(self):
        """Reset a user's password"""
        print("\n+----------------------------------------+")
        print("|       RESET USER PASSWORD              |")
        print("+----------------------------------------+")

        user_id = self.validation.get_valid_int(
            "Enter User ID: ",
            lambda x: x > 0,
            "❌ Invalid User ID!"
        )

        user = self.db.get_user_by_id(user_id)
        if not user:
            print("❌ User not found.")
            return

        print(f"\nUser: {user['username']} ({user['email']})")

        new_password = self.validation.get_valid_input(
            "Enter new password (min 6 chars): ",
            lambda x: len(x) >= 6,
            "❌ Password must be at least 6 characters!"
        )

        confirm = input("Confirm password reset? (y/n): ").lower().strip()
        if confirm != 'y':
            print("❌ Operation cancelled.")
            return

        hashed = hashlib.sha256(new_password.encode()).hexdigest()
        self.db.execute_query(
            "UPDATE users SET password = %s WHERE user_id = %s",
            (hashed, user_id)
        )

        self.db.log_action(
            f"Admin:{self.logged_in_admin}",
            f"Reset password for user: {user['username']}"
        )

        print(f"✅ Password reset successfully for {user['username']}")

    # ==================================================
    # TRANSACTION MONITORING
    # ==================================================
    def view_all_transactions(self):
        """View all system transactions"""
        print("\n+----------------------------------------+")
        print("|     VIEW ALL TRANSACTIONS              |")
        print("+----------------------------------------+")
        print("| 1. All Transactions (Last 50)          |")
        print("| 2. Filter by User ID                   |")
        print("| 3. Filter by Date Range                |")
        print("+----------------------------------------+")

        choice = self.validation.get_valid_int(
            "Enter choice: ",
            lambda x: x in [1, 2, 3],
            "❌ Invalid choice!"
        )

        if choice == 1:
            # All transactions
            query = """
                SELECT e.expense_id, u.username, e.category, e.amount, e.description, e.date
                FROM expenses e
                JOIN users u ON e.user_id = u.user_id
                ORDER BY e.date DESC LIMIT 50
            """
            txns = self.db.execute_query(query, fetch=True)
        elif choice == 2:
            # By user
            user_id = self.validation.get_valid_int("Enter User ID: ", lambda x: x > 0, "❌ Invalid!")
            query = """
                SELECT e.expense_id, u.username, e.category, e.amount, e.description, e.date
                FROM expenses e
                JOIN users u ON e.user_id = u.user_id
                WHERE e.user_id = %s
                ORDER BY e.date DESC LIMIT 50
            """
            txns = self.db.execute_query(query, (user_id,), fetch=True)
        else:
            # By date range
            start = input("Enter start date (YYYY-MM-DD): ").strip()
            end = input("Enter end date (YYYY-MM-DD): ").strip()
            query = """
                SELECT e.expense_id, u.username, e.category, e.amount, e.description, e.date
                FROM expenses e
                JOIN users u ON e.user_id = u.user_id
                WHERE DATE(e.date) BETWEEN %s AND %s
                ORDER BY e.date DESC
            """
            txns = self.db.execute_query(query, (start, end), fetch=True)

        if not txns:
            print("❌ No transactions found.")
            return

        print("\n" + "=" * 95)
        print(f"| {'ID':<4} | {'User':<12} | {'Category':<18} | {'Amount':>10} | {'Description':<20} | {'Date':<16} |")
        print("-" * 95)
        
        total = 0
        for t in txns:
            amount = float(t['amount'])
            total += amount
            desc = (t['description'] or 'N/A')[:20]
            date_str = t['date'].strftime('%Y-%m-%d %H:%M') if t['date'] else 'N/A'
            print(f"| {t['expense_id']:<4} | {t['username']:<12} | {t['category']:<18} | "
                  f"₹{amount:>8.2f} | {desc:<20} | {date_str:<16} |")
        
        print("=" * 95)
        print(f"Total: ₹{total:,.2f} ({len(txns)} transactions)")

    def view_large_transactions(self):
        """View transactions above threshold (fraud detection)"""
        print("\n+----------------------------------------+")
        print("|    LARGE TRANSACTIONS (>₹10,000)       |")
        print("+----------------------------------------+")

        threshold = 10000
        txns = self.db.execute_query(
            """
            SELECT e.expense_id, u.username, u.email, e.category, e.amount, e.date
            FROM expenses e
            JOIN users u ON e.user_id = u.user_id
            WHERE e.amount > %s
            ORDER BY e.amount DESC
            """,
            (threshold,), fetch=True
        )

        if not txns:
            print(f"✅ No transactions above ₹{threshold:,} found.")
            return

        print(f"\n⚠️  Found {len(txns)} large transactions:")
        print("-" * 85)
        for t in txns:
            print(f"| {t['username']:<15} | {t['email']:<25} | {t['category']:<15} | "
                  f"₹{float(t['amount']):>10,.2f} |")
        print("-" * 85)

    # ==================================================
    # BUDGET MONITORING
    # ==================================================
    def view_all_budgets(self):
        """View all user budgets"""
        budgets = self.db.execute_query(
            """
            SELECT b.budget_id, u.username, b.category, b.limit_amount, 
                   b.year, b.month
            FROM budget b
            JOIN users u ON b.user_id = u.user_id
            ORDER BY b.year DESC, b.month DESC, u.username
            """,
            fetch=True
        )

        if not budgets:
            print("❌ No budgets found.")
            return

        print("\n" + "=" * 80)
        print(f"{'ALL USER BUDGETS':^80}")
        print("=" * 80)
        print(f"| {'ID':<4} | {'User':<15} | {'Category':<18} | {'Limit':>12} | {'Period':<10} |")
        print("-" * 80)
        
        for b in budgets:
            period = f"{b['year']}-{b['month']:02d}"
            print(f"| {b['budget_id']:<4} | {b['username']:<15} | {b['category']:<18} | "
                  f"₹{float(b['limit_amount']):>10,.2f} | {period:<10} |")
        
        print("=" * 80)

    def view_overspending_users(self):
        """Detect users who exceeded their budgets"""
        print("\n+----------------------------------------+")
        print("|     OVERSPENDING USERS                 |")
        print("+----------------------------------------+")

        current_month = datetime.now().strftime("%Y-%m")
        year, month = map(int, current_month.split('-'))

        # Get budgets with spending comparison
        query = """
            SELECT u.username, u.email, b.category, b.limit_amount,
                   COALESCE(SUM(e.amount), 0) as spent
            FROM budget b
            JOIN users u ON b.user_id = u.user_id
            LEFT JOIN expenses e ON e.user_id = b.user_id 
                AND e.category = b.category 
                AND DATE_FORMAT(e.date, '%%Y-%%m') = %s
            WHERE b.year = %s AND b.month = %s
            GROUP BY u.user_id, b.category, b.limit_amount
            HAVING spent > b.limit_amount
        """
        
        overspenders = self.db.execute_query(query, (current_month, year, month), fetch=True)

        if not overspenders:
            print(f"✅ No overspending detected for {current_month}.")
            return

        print(f"\n⚠️  Found {len(overspenders)} overspending cases:")
        print("-" * 90)
        print(f"| {'User':<15} | {'Email':<25} | {'Category':<15} | {'Budget':>10} | {'Spent':>10} |")
        print("-" * 90)
        
        for o in overspenders:
            print(f"| {o['username']:<15} | {o['email']:<25} | {o['category']:<15} | "
                  f"₹{float(o['limit_amount']):>8,.0f} | ₹{float(o['spent']):>8,.0f} |")
        
        print("-" * 90)

    # ==================================================
    # SYSTEM ANALYTICS
    # ==================================================
    def view_system_summary(self):
        """View complete system analytics"""
        print("\n" + "=" * 60)
        print(f"{'SYSTEM SUMMARY':^60}")
        print("=" * 60)

        # Total users
        users = self.db.execute_query("SELECT COUNT(*) as cnt FROM users", fetch=True)
        active = self.db.execute_query("SELECT COUNT(*) as cnt FROM users WHERE status='ACTIVE'", fetch=True)
        blocked = self.db.execute_query("SELECT COUNT(*) as cnt FROM users WHERE status='BLOCKED'", fetch=True)

        print(f"\n📊 USER STATISTICS")
        print(f"   Total Users    : {users[0]['cnt']}")
        print(f"   Active Users   : {active[0]['cnt']}")
        print(f"   Blocked Users  : {blocked[0]['cnt']}")

        # Total transactions
        expenses = self.db.execute_query(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM expenses",
            fetch=True
        )
        income = self.db.execute_query(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(amount), 0) as total FROM income",
            fetch=True
        )

        print(f"\n💰 TRANSACTION STATISTICS")
        print(f"   Total Expenses : {expenses[0]['cnt']} (₹{float(expenses[0]['total'] or 0):,.2f})")
        print(f"   Total Income   : {income[0]['cnt']} (₹{float(income[0]['total'] or 0):,.2f})")

        # Total balances
        wallet_sum = self.db.execute_query(
            "SELECT COALESCE(SUM(wallet_balance), 0) as total FROM users",
            fetch=True
        )
        bank_sum = self.db.execute_query(
            "SELECT COALESCE(SUM(balance), 0) as total FROM bank_accounts",
            fetch=True
        )

        print(f"\n🏦 ACCOUNT BALANCES")
        print(f"   Total Wallet   : ₹{float(wallet_sum[0]['total'] or 0):,.2f}")
        print(f"   Total Bank     : ₹{float(bank_sum[0]['total'] or 0):,.2f}")

        # Top categories
        print(f"\n📈 TOP SPENDING CATEGORIES")
        categories = self.db.execute_query(
            """SELECT category, SUM(amount) as total, COUNT(*) as cnt
               FROM expenses GROUP BY category ORDER BY total DESC LIMIT 5""",
            fetch=True
        )
        for c in categories:
            print(f"   {c['category']:<20}: ₹{float(c['total']):>10,.2f} ({c['cnt']} txns)")

        # Goals
        goals = self.db.execute_query(
            "SELECT COUNT(*) as cnt FROM financial_goals WHERE status='ACTIVE'",
            fetch=True
        )
        print(f"\n🎯 ACTIVE GOALS: {goals[0]['cnt']}")

        print("\n" + "=" * 60)

    def view_top_spenders(self):
        """View users with highest spending"""
        print("\n" + "=" * 70)
        print(f"{'TOP USERS BY SPENDING':^70}")
        print("=" * 70)

        spenders = self.db.execute_query(
            """
            SELECT u.user_id, u.username, u.email,
                   COALESCE(SUM(e.amount), 0) as total_spent,
                   COUNT(e.expense_id) as txn_count
            FROM users u
            LEFT JOIN expenses e ON u.user_id = e.user_id
            GROUP BY u.user_id
            ORDER BY total_spent DESC
            LIMIT 10
            """,
            fetch=True
        )

        if not spenders:
            print("❌ No spending data found.")
            return

        print(f"| {'Rank':<4} | {'User':<15} | {'Email':<25} | {'Total Spent':>12} | {'Txns':>5} |")
        print("-" * 70)
        
        for i, s in enumerate(spenders, 1):
            print(f"| {i:<4} | {s['username']:<15} | {s['email']:<25} | "
                  f"₹{float(s['total_spent']):>10,.2f} | {s['txn_count']:>5} |")
        
        print("=" * 70)

    def view_system_logs(self):
        """View system activity logs"""
        print("\n" + "=" * 100)
        print(f"{'SYSTEM LOGS (Last 30)':^100}")
        print("=" * 100)

        logs = self.db.execute_query(
            "SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 30",
            fetch=True
        )

        if not logs:
            print("❌ No logs found.")
            return

        print(f"| {'ID':<4} | {'Actor':<20} | {'Action':<50} | {'Time':<18} |")
        print("-" * 100)
        
        for log in logs:
            action = (log['action'] or '')[:50]
            time_str = log['timestamp'].strftime('%Y-%m-%d %H:%M') if log['timestamp'] else 'N/A'
            print(f"| {log['log_id']:<4} | {log['actor']:<20} | {action:<50} | {time_str:<18} |")
        
        print("=" * 100)

    # ==================================================
    # INVESTMENT & MARKET (FINTECH)
    # ==================================================
    
    def view_market_overview(self):
        """View all market assets and current prices"""
        print("\n" + "=" * 90)
        print(f"{'MARKET OVERVIEW':^90}")
        print("=" * 90)
        
        assets = self.market_engine.get_market_overview()
        
        if not assets:
            print("❌ No market assets found.")
            return
        
        # Group by asset type
        current_type = None
        for asset in assets:
            if asset['asset_type'] != current_type:
                current_type = asset['asset_type']
                print(f"\n--- {current_type} ---")
                print(f"| {'Symbol':<10} | {'Name':<25} | {'Price':>12} | {'Change':>8} |")
                print("-" * 65)
            
            change = float(asset['day_change_percent'] or 0)
            change_str = f"{change:+.2f}%" if change != 0 else "0.00%"
            indicator = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"
            
            print(f"| {asset['asset_symbol']:<10} | {asset['asset_name']:<25} | "
                  f"₹{float(asset['current_price']):>10,.2f} | {indicator} {change_str:>6} |")
        
        print("\n" + "=" * 90)
    
    def update_market_prices(self):
        """Trigger global market price update"""
        print("\n+----------------------------------------+")
        print("|     UPDATE MARKET PRICES               |")
        print("+----------------------------------------+")
        print("| This will update ALL asset prices.     |")
        print("| All user portfolios will be affected.  |")
        print("+----------------------------------------+")
        
        confirm = input("Proceed with market update? (y/n): ").lower().strip()
        if confirm != 'y':
            print("❌ Update cancelled.")
            return
        
        print("\n⏳ Updating market prices...")
        updated = self.market_engine.update_all_market_prices()
        
        if not updated:
            print("✅ No price changes detected.")
            return
        
        print(f"\n✅ Updated {len(updated)} assets:")
        print("-" * 70)
        for asset in updated:
            change = asset['change_percent']
            indicator = "🟢" if change > 0 else "🔴"
            print(f"| {indicator} {asset['name']:<30} | ₹{asset['old_price']:>10,.2f} → "
                  f"₹{asset['new_price']:>10,.2f} ({change:+.2f}%) |")
        print("-" * 70)
        
        self.db.log_action(
            f"Admin:{self.logged_in_admin}",
            f"Updated market prices for {len(updated)} assets"
        )
    
    def view_top_investors(self):
        """View users with highest investment portfolios"""
        print("\n" + "=" * 85)
        print(f"{'TOP INVESTORS':^85}")
        print("=" * 85)
        
        investors = self.analytics.get_top_investors(15)
        
        if not investors:
            print("❌ No investment data found.")
            return
        
        print(f"| {'Rank':<4} | {'User':<15} | {'Email':<25} | {'Invested':>12} | "
              f"{'Current':>12} | {'P/L':>10} |")
        print("-" * 85)
        
        for i, inv in enumerate(investors, 1):
            pl = float(inv['profit_loss'] or 0)
            pl_str = f"₹{pl:+,.0f}"
            indicator = "🟢" if pl > 0 else "🔴" if pl < 0 else "⚪"
            
            print(f"| {i:<4} | {inv['username']:<15} | {inv['email']:<25} | "
                  f"₹{float(inv['total_invested'] or 0):>10,.0f} | "
                  f"₹{float(inv['current_value'] or 0):>10,.0f} | {indicator} {pl_str:>8} |")
        
        print("=" * 85)
    
    def view_net_worth_leaderboard(self):
        """View users ranked by net worth"""
        print("\n" + "=" * 75)
        print(f"{'NET WORTH LEADERBOARD':^75}")
        print("=" * 75)
        
        leaderboard = self.market_engine.get_net_worth_leaderboard(15)
        
        if not leaderboard:
            print("❌ No data available.")
            return
        
        print(f"| {'Rank':<4} | {'User':<15} | {'Email':<28} | {'Net Worth':>15} |")
        print("-" * 75)
        
        for i, user in enumerate(leaderboard, 1):
            nw = float(user['net_worth'] or 0)
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "  "
            print(f"| {medal}{i:<3} | {user['username']:<15} | {user['email']:<28} | ₹{nw:>13,.2f} |")
        
        print("=" * 75)
    
    # ==================================================
    # ANALYTICS & REPORTS (FINTECH)
    # ==================================================
    
    def view_platform_dashboard(self):
        """Comprehensive platform analytics dashboard"""
        print("\n" + "=" * 70)
        print(f"{'PLATFORM ANALYTICS DASHBOARD':^70}")
        print("=" * 70)
        
        summary = self.analytics.get_platform_summary()
        
        # User Statistics
        users = summary['users']
        print("\n📊 USER STATISTICS")
        print("-" * 40)
        print(f"   Total Users        : {users['total_users']}")
        print(f"   Active Users       : {users['active_users']}")
        print(f"   Blocked Users      : {users['blocked_users']}")
        print(f"   Active (7 days)    : {users['active_7d']}")
        print(f"   Active (30 days)   : {users['active_30d']}")
        
        # Financial Statistics
        fin = summary['finances']
        print("\n💰 FINANCIAL OVERVIEW")
        print("-" * 40)
        print(f"   Total in Wallets   : ₹{fin['wallet_total']:>15,.2f}")
        print(f"   Total in Banks     : ₹{fin['bank_total']:>15,.2f}")
        print(f"   Total Expenses     : ₹{fin['total_expenses']:>15,.2f} ({fin['expense_count']} txns)")
        print(f"   Total Income       : ₹{fin['total_income']:>15,.2f} ({fin['income_count']} txns)")
        print(f"   Net Money Flow     : ₹{fin['total_income'] - fin['total_expenses']:>15,.2f}")
        
        # Investment Statistics
        inv = summary['investments']
        print("\n📈 INVESTMENT OVERVIEW")
        print("-" * 40)
        print(f"   Total Invested     : ₹{inv['total_invested']:>15,.2f}")
        print(f"   Current Value      : ₹{inv['current_value']:>15,.2f}")
        print(f"   Total P/L          : ₹{inv['current_value'] - inv['total_invested']:>+15,.2f}")
        print(f"   Active Investors   : {inv['total_investors']}")
        
        # Average Metrics
        avg = self.analytics.get_average_user_metrics()
        print("\n📉 AVERAGE METRICS")
        print("-" * 40)
        print(f"   Avg Net Worth      : ₹{avg['avg_net_worth']:>15,.2f}")
        print(f"   Avg Monthly Spend  : ₹{avg['avg_monthly_spending']:>15,.2f}")
        print(f"   Avg Investment     : ₹{avg['avg_investment']:>15,.2f}")
        
        print("\n" + "=" * 70)
    
    def view_top_categories(self):
        """View top spending categories system-wide"""
        print("\n" + "=" * 80)
        print(f"{'TOP SPENDING CATEGORIES (SYSTEM-WIDE)':^80}")
        print("=" * 80)
        
        categories = self.analytics.get_top_spending_categories_system(10)
        
        if not categories:
            print("❌ No spending data found.")
            return
        
        total = sum(float(c['total']) for c in categories)
        
        print(f"| {'#':<3} | {'Category':<20} | {'Total':>14} | {'% Share':>8} | "
              f"{'Txns':>6} | {'Users':>6} |")
        print("-" * 80)
        
        for i, c in enumerate(categories, 1):
            cat_total = float(c['total'])
            share = (cat_total / total * 100) if total > 0 else 0
            print(f"| {i:<3} | {c['category']:<20} | ₹{cat_total:>12,.0f} | {share:>7.1f}% | "
                  f"{c['transaction_count']:>6} | {c['unique_users']:>6} |")
        
        print("-" * 80)
        print(f"| {'TOTAL':<26} | ₹{total:>12,.0f} | 100.0% |")
        print("=" * 80)
    
    def view_monthly_growth(self):
        """View platform growth over time"""
        print("\n" + "=" * 60)
        print(f"{'MONTHLY PLATFORM GROWTH':^60}")
        print("=" * 60)
        
        growth = self.analytics.get_monthly_platform_growth(12)
        
        if not growth:
            print("❌ No growth data available.")
            return
        
        print(f"| {'Month':<10} | {'New Users':>10} | {'Transaction Volume':>18} |")
        print("-" * 60)
        
        for g in growth:
            print(f"| {g['month']:<10} | {g['new_users']:>10} | ₹{g['transaction_volume']:>16,.0f} |")
        
        print("=" * 60)
        
        # Investment distribution
        print(f"\n{'INVESTMENT DISTRIBUTION BY ASSET TYPE':^60}")
        print("-" * 60)
        
        inv_dist = self.analytics.get_investment_distribution()
        if inv_dist:
            print(f"| {'Type':<15} | {'Investors':>10} | {'Invested':>14} | {'Current':>14} |")
            print("-" * 60)
            for d in inv_dist:
                print(f"| {d['asset_type']:<15} | {d['investors']:>10} | "
                      f"₹{float(d['total_invested'] or 0):>12,.0f} | "
                      f"₹{float(d['current_value'] or 0):>12,.0f} |")
        
        print("=" * 60)
    
    # ==================================================
    # UTILITY
    # ==================================================
    def _invalid(self):
        """Display invalid choice message"""
        print("❌ Invalid choice! Please try again.")
