import hashlib
from datetime import datetime
from validations import Validation


class AdminManager:
    def __init__(self, db):
        self.db = db
        self.validation = Validation()
        self.logged_in_admin = None
        self.logged_in_admin_id = None

    # --------------------------------------------------
    # ADMIN LOGIN
    # --------------------------------------------------
    def admin_login(self):
        box = 60
        print("+" + "-" * box + "+")
        print(f"| {'ADMIN LOGIN':<58} |")
        print("+" + "-" * box + "+")

        try:
            admin_id = self.validation.get_valid_int(
                "Enter Administrator ID (4 digits): ",
                lambda x: 1000 <= x <= 9999,
                "❌ Admin ID must be 4 digits!"
            )

            password = self.validation.get_valid_input(
                "Enter Password: ",
                lambda x: len(x.strip()) > 0,
                "❌ Password cannot be empty!"
            )

            admin = self.db.get_admin_by_id(admin_id)
            if not admin:
                print("❌ Invalid Admin ID or Password!")
                return False

            hashed = hashlib.sha256(password.encode()).hexdigest()
            if admin["password"] != hashed:
                print("❌ Invalid Admin ID or Password!")
                return False

            self.logged_in_admin = admin["name"]
            self.logged_in_admin_id = admin_id

            self.db.log_action(
                actor=f"Admin:{self.logged_in_admin}",
                action="Admin logged in"
            )

            print("+" + "-" * box + "+")
            print(f"| ✅ Welcome, {self.logged_in_admin:<45} |")
            print("+" + "-" * box + "+")
            return True

        except Exception as e:
            print(f"❌ Admin Login Error: {e}")
            return False

    # --------------------------------------------------
    # ADMIN MENU LOOP
    # --------------------------------------------------
    def admin_menu_loop(self):
        while True:
            try:
                self.display_admin_menu()
                choice = input().strip()

                if not choice.isdigit():
                    self._invalid()
                    continue

                choice = int(choice)

                if choice == 1:
                    self.view_all_users()
                elif choice == 2:
                    self.view_system_transactions()
                elif choice == 3:
                    self.view_expense_analytics()
                elif choice == 4:
                    self.block_unblock_user()
                elif choice == 5:
                    self.credit_debit_wallet()
                elif choice == 6:
                    self.credit_debit_bank()
                elif choice == 7:
                    self.monthly_system_report()
                elif choice == 8:
                    self.manage_categories()
                elif choice == 9:
                    self.view_logs()
                elif choice == 0:
                    print("👋 Exiting Admin Panel...")
                    break
                else:
                    self._invalid()

            except KeyboardInterrupt:
                print("\n👋 Admin session closed.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    # --------------------------------------------------
    # ADMIN MENU UI
    # --------------------------------------------------
    def display_admin_menu(self):
        print("+------------------------------------------------+")
        print("|                  ADMIN MENU                   |")
        print("+------------------------------------------------+")
        print("| 1 | View All Users                             |")
        print("| 2 | View System Transactions                   |")
        print("| 3 | View Expense Analytics                     |")
        print("| 4 | Block / Unblock User                       |")
        print("| 5 | Credit / Debit User WALLET                 |")
        print("| 6 | Credit / Debit User BANK                   |")
        print("| 7 | Monthly System Financial Report            |")
        print("| 8 | Manage Expense Categories                  |")
        print("| 9 | View System Logs                           |")
        print("| 0 | Exit                                       |")
        print("+------------------------------------------------+")
        print("👉 Enter choice: ", end="")

    # --------------------------------------------------
    # CORE FEATURES
    # --------------------------------------------------
    def view_all_users(self):
        users = self.db.execute_query(
            """SELECT user_id, username, email, mobile,
                      wallet_balance, status, created_at
               FROM users ORDER BY user_id""",
            fetch=True
        )

        if not users:
            print("❌ No users found.")
            return

        print("+----------------------------------------------------------------------------------+")
        print("| ID  | Username        | Email                    | Mobile      | Balance | Status |")
        print("+----------------------------------------------------------------------------------+")
        for u in users:
            print(f"| {u['user_id']:<3} | {u['username']:<15} | {u['email']:<24} | "
                  f"{u['mobile']:<11} | ₹{u['wallet_balance']:<7.2f} | {u['status']:<6} |")
        print("+----------------------------------------------------------------------------------+")

    def view_system_transactions(self):
        txns = self.db.execute_query(
            """
            SELECT t.txn_id, u.username, t.type,
                   t.amount, t.balance_after, t.date
            FROM wallet_transactions t
            JOIN users u ON t.user_id = u.user_id
            ORDER BY t.date DESC LIMIT 50
            """,
            fetch=True
        )

        if not txns:
            print("❌ No transactions found.")
            return

        print("+--------------------------------------------------------------------------------+")
        print("| ID | User        | Type        | Amount     | Balance     | Date              |")
        print("+--------------------------------------------------------------------------------+")
        for t in txns:
            print(f"| {t['txn_id']:<2} | {t['username']:<10} | {t['type']:<10} | "
                  f"₹{t['amount']:<9.2f} | ₹{t['balance_after']:<9.2f} | "
                  f"{t['date'].strftime('%Y-%m-%d %H:%M')} |")
        print("+--------------------------------------------------------------------------------+")

    def view_expense_analytics(self):
        data = self.db.execute_query(
            """
            SELECT category, SUM(amount) AS total, COUNT(*) cnt
            FROM expenses GROUP BY category
            ORDER BY total DESC
            """,
            fetch=True
        )

        print("+-----------------------------------------------+")
        print("|            EXPENSE ANALYTICS                  |")
        print("+-----------------------------------------------+")
        for row in data:
            print(f"| {row['category']:<18} ₹{row['total']:<10.2f} ({row['cnt']} txns)")
        print("+-----------------------------------------------+")

    # --------------------------------------------------
    # ADMIN ACTIONS
    # --------------------------------------------------
    def block_unblock_user(self):
        user_id = self.validation.get_valid_int(
            "Enter User ID: ",
            lambda x: x > 0,
            "❌ Invalid User ID!"
        )

        user = self.db.get_user_by_id(user_id)
        if not user:
            print("❌ User not found.")
            return

        print(f"Current Status: {user['status']}")
        confirm = input("Change status? (y/n): ").lower()

        if confirm != 'y':
            print("❌ Operation cancelled.")
            return

        new_status = "BLOCKED" if user["status"] == "ACTIVE" else "ACTIVE"

        self.db.execute_query(
            "UPDATE users SET status = %s WHERE user_id = %s",
            (new_status, user_id)
        )

        self.db.log_action(
            f"Admin:{self.logged_in_admin}",
            f"Changed user {user['username']} status to {new_status}"
        )

        print(f"✅ User status updated to {new_status}")

    def credit_debit_wallet(self):
        print("+-----------------------------------+")
        print("|      WALLET CREDIT / DEBIT        |")
        print("+-----------------------------------+")

        user_id = self.validation.get_valid_int(
            "Enter User ID: ",
            lambda x: x > 0,
            "❌ Invalid User ID!"
        )

        user = self.db.get_user_by_id(user_id)
        if not user:
            print("❌ User not found!")
            return

        amount = self.validation.get_valid_float(
            "Enter amount: ",
            lambda x: x > 0,
            "❌ Amount must be positive!"
        )

        action = input("Type C for Credit / D for Debit: ").upper()
        balance = user["wallet_balance"]

        if action == "D" and amount > balance:
            print("❌ Insufficient balance!")
            return

        new_balance = balance + amount if action == "C" else balance - amount

        self.db.update_user_balance(user_id, new_balance)
        self.db.add_transaction(
            user_id,
            "ADMIN_CREDIT" if action == "C" else "ADMIN_DEBIT",
            amount,
            new_balance
        )

        self.db.log_action(
            f"Admin:{self.logged_in_admin}",
            f"{action} ₹{amount} for user {user['username']}"
        )

        print("✅ Wallet updated successfully!")


    def credit_debit_bank(self):
        print("🚧 Bank credit/debit will simulate linked bank accounts")

    def monthly_system_report(self):
        print("🚧 Monthly finance report (Income vs Expense vs Net) coming soon")

    def manage_categories(self):
        print("🚧 Admin category management coming soon")

    def view_logs(self):
        logs = self.db.execute_query(
            "SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 20",
            fetch=True
        )

        print("+----------------------------------------------------------------------------------+")
        print("| ID | Actor            | Action                                       | Time      |")
        print("+----------------------------------------------------------------------------------+")
        for log in logs:
            print(f"| {log['log_id']:<2} | {log['actor']:<15} | "
                  f"{log['action'][:40]:<40} | "
                  f"{log['timestamp'].strftime('%Y-%m-%d %H:%M')} |")
        print("+----------------------------------------------------------------------------------+")

    # --------------------------------------------------
    # UTIL
    # --------------------------------------------------
    def _invalid(self):
        print("❌ Invalid choice!")
