import re
import hashlib
import requests
from datetime import datetime, date, timedelta
from validations import Validation
from stack_queue_utils import StackQueueManager
from wallet import Wallet
import time, os, random
import requests

class UserManager:
    def __init__(self, db):
        self.db = db
        self.validation = Validation()
        self.stack_queue = StackQueueManager()
        self.wallet = Wallet(self.db, self.stack_queue)
        self.logged_in_user = None
        self.logged_in_user_id = None

    def user_login(self):
        """Secure user login functionality"""
        box_width = 50
        print("+" + "-" * box_width + "+")
        print(f"| {'USER LOGIN':<48} |")
        print("+" + "-" * box_width + "+")

        try:
            email = self.validation.get_valid_input(
                "| Enter Email (@gmail.com): ",
                lambda x: re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', x.lower()),
                "❌ Invalid Gmail address!"
            ).strip().lower()

            password = self.validation.get_valid_input(
                "| Enter Password: ",
                lambda x: len(x.strip()) > 0,
                "❌ Password cannot be empty!"
            )

            print("+" + "-" * box_width + "+")

            user = self.db.get_user_by_email(email)

            if not user:
                print("+" + "-" * box_width + "+")
                print(f"| {'❌ Invalid email or password!':<48} |")
                print("+" + "-" * box_width + "+")
                return False

            # Check if user is blocked
            if user.get("status", "ACTIVE") != "ACTIVE":
                print("+" + "-" * box_width + "+")
                print(f"| {'❌ Your account is blocked by admin!':<48} |")
                print("+" + "-" * box_width + "+")
                return False

            # Hash password and compare
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            if user["password"] != hashed_password:
                print("+" + "-" * box_width + "+")
                print(f"| {'❌ Invalid email or password!':<48} |")
                print("+" + "-" * box_width + "+")
                return False

            # Set session
            self.logged_in_user = user["username"]
            self.logged_in_user_id = user["user_id"]
            self.wallet_balance = user["wallet_balance"]

            # Log login
            self.db.log_action(
                actor=f"User:{self.logged_in_user}",
                action="User logged in"
            )

            print("+" + "-" * box_width + "+")
            print(f"| {'✅ Welcome Back, ' + self.logged_in_user + '!':<48} |")
            print("+" + "-" * box_width + "+")

            return True

        except Exception as e:
            print("+" + "-" * box_width + "+")
            print(f"| {'❌ Login Error: ' + str(e):<48} |")
            print("+" + "-" * box_width + "+")
            return False


    def user_signup(self):
        """Secure user signup functionality"""
        box_width = 60
        print("+" + "-" * box_width + "+")
        print(f"| {'REGISTRATION FORM':<58} |")
        print("+" + "-" * box_width + "+")

        try:
            username = self.validation.get_valid_input(
                "| Enter Username: ",
                lambda x: re.match(r'^[a-zA-Z0-9_]{3,}$', x.strip()),
                "❌ Username must be at least 3 characters (letters, numbers, _)"
            ).strip()

            password = self.validation.get_valid_input(
                "| Enter Password: ",
                lambda x: len(x.strip()) >= 6,
                "❌ Password must be at least 6 characters!"
            )

            confirm_password = self.validation.get_valid_input(
                "| Confirm Password: ",
                lambda x: x == password,
                "❌ Passwords do not match!"
            )

            email = self.validation.get_valid_input(
                "| Enter Email (@gmail.com): ",
                lambda x: re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', x.lower()),
                "❌ Invalid Gmail address!"
            ).strip().lower()

            mobile = self.validation.get_valid_input(
                "| Enter Mobile (10 digits): ",
                lambda x: re.match(r'^[6-9]\d{9}$', x),
                "❌ Invalid mobile number!"
            ).strip()

            print("+" + "-" * box_width + "+")

            # Duplicate check
            if self.db.user_exists(username=username, email=email, mobile=mobile):
                print("+" + "-" * box_width + "+")
                print(f"| {'❌ Username / Email / Mobile already exists!':<58} |")
                print("+" + "-" * box_width + "+")
                return False

            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            created_at = datetime.now()

            query = """
                INSERT INTO users
                (username, password, email, mobile, wallet_balance, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            result = self.db.execute_insert(
                query,
                (username, hashed_password, email, mobile, 0.00, "ACTIVE", created_at)
            )

            if result:
                print("+" + "-" * box_width + "+")
                print(f"| {'✅ Registration Successful!':<58} |")
                print("+" + "-" * box_width + "+")

                self.db.log_action(
                    actor=f"User:{username}",
                    action="User registered successfully"
                )
                return True

            print("+" + "-" * box_width + "+")
            print(f"| {'❌ Registration Failed!':<58} |")
            print("+" + "-" * box_width + "+")
            return False

        except Exception as e:
            print("+" + "-" * box_width + "+")
            print(f"| {'❌ Error: ' + str(e):<58} |")
            print("+" + "-" * box_width + "+")
            return False

    def display_user_wallet_menu(self):
        print("+%------------------------------------------------+%")
        print("|              USER WALLET MENU                  |")
        print("+%------------------------------------------------+%")
        print("| Case 1  | Add / Manage Accounts               |")
        print("|-----------------------------------------------|")
        print("| Case 2  | Add Income                          |")
        print("| Case 3  | Add Expense                         |")
        print("| Case 4  | Wallet Balance                     |")
        print("| Case 5  | Monthly Summary                    |")
        print("| Case 6  | Set Budget                         |")
        print("| Case 7  | Budget Status                      |")
        print("| Case 8  | Top Expenses                       |")
        print("| Case 9  | Transaction History                |")
        print("| Case 10 | Financial Goals                    |")
        print("| Case 11 | Update Profile                     |")
        print("| Case 0  | Exit                               |")
        print("+------------------------------------------------+")
        print("👉 Enter your choice: ", end="")


    def user_wallet_menu_loop(self):
        """User wallet menu loop (Advanced with Add/Manage Accounts)"""
        while True:
            try:
                self.display_user_wallet_menu()
                choice = input().strip()

                if not choice.isdigit():
                    print("+-----------------------------+")
                    print("|       INVALID CHOICE        |")
                    print("+-----------------------------+")
                    continue

                choice = int(choice)

                # -------- ADD / MANAGE ACCOUNTS --------
                if choice == 1:
                    self.add_manage_accounts_menu()

                # -------- DAILY WALLET OPERATIONS --------
                elif choice == 2:
                    self.add_income()

                elif choice == 3:
                    self.add_expense()

                elif choice == 4:
                    self.view_wallet_balance()

                elif choice == 5:
                    self.monthly_summary()

                elif choice == 6:
                    self.set_budget()

                elif choice == 7:
                    self.budget_status()

                elif choice == 8:
                    self.top_expenses()

                elif choice == 9:
                    self.transaction_history()

                elif choice == 10:
                    self.financial_goals_menu()

                elif choice == 11:
                    self.update_profile()

                # -------- EXIT --------
                elif choice == 0:
                    print("+-----------------------------+")
                    print("|         EXITING...          |")
                    print("+-----------------------------+")

                    # Clear session + stack/queue data
                    self.stack_queue.clear_user_data(self.logged_in_user_id)
                    self.logged_in_user = None
                    self.logged_in_user_id = None
                    break

                else:
                    print("+-----------------------------+")
                    print("|       INVALID CHOICE        |")
                    print("+-----------------------------+")

            except KeyboardInterrupt:
                print("\n+-------------------------------------------+")
                print("| ✅ Exiting Wallet Menu...                 |")
                print("+-------------------------------------------+")
                break

            except Exception as e:
                print("+-----------------------------------------------+")
                print(f"| ❌ Error: {str(e)[:43]:<43} |")
                print("+-----------------------------------------------+")


    def add_manage_accounts_menu(self):
        """Add / Manage Accounts sub-menu"""
        while True:
            print("+-----------------------------------------------+")
            print("|           ADD / MANAGE ACCOUNTS               |")
            print("+-----------------------------------------------+")
            print("| Case 1 | Bank Account Sync                    |")
            print("| Case 2 | Investment Account Setup             |")
            print("| Case 3 | Manual Account Setup                 |")
            print("| Case 4 | View Investment Performance          |")
            print("| Case 5 | Sell/Remove Investment Account       |")
            print("| Case 0 | Back                                 |")
            print("+-----------------------------------------------+")
            print("👉 Enter your choice: ", end="")

            choice = input().strip()

            if not choice.isdigit():
                print("❌ Invalid choice!")
                continue

            choice = int(choice)

            if choice == 1:
                self.bank_account_sync()        # 🔜 later
            elif choice == 2:
                self.investment_account_setup() # 🔜 later
            elif choice == 3:
                self.manual_account_setup()     # 🔜 later
            elif choice == 4:
                self.display_investment_performance_live()
            elif choice == 5:
                self.sell_remove_investment_account()
            elif choice == 0:
                break
            else:
                print("+-----------------------------------------------+")
                print("| ❌ Invalid choice!                            |")
                print("+-----------------------------------------------+")

    def bank_account_sync(self):
        """Bank account sync functionality with predefined Indian banks"""
        print("+-----------------------------------------------+")
        print("|           BANK ACCOUNT SYNC                   |")
        print("+-----------------------------------------------+")

        try:
            # -------- SELECT BANK FROM PREDEFINED LIST --------
            indian_banks = {
                1: "State Bank of India (SBI)",
                2: "HDFC Bank",
                3: "ICICI Bank",
                4: "Axis Bank",
                5: "Punjab National Bank (PNB)",
                6: "Bank of Baroda",
                7: "Other"
            }

            print("| Select Your Bank:                             |")
            for k, v in indian_banks.items():
                print(f"| {k}. {v:<38}|")
            print("+-----------------------------------------------+")

            bank_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in indian_banks,
                "❌ Invalid bank selection!"
            )

            if bank_choice == 7:  # Other
                bank_name = self.validation.get_valid_input(
                    "Enter Bank Name: ",
                    lambda x: len(x.strip()) > 0,
                    "❌ Bank name cannot be empty!"
                ).strip()
            else:
                bank_name = indian_banks[bank_choice]

            # -------- ACCOUNT HOLDER --------
            account_holder = self.validation.get_valid_input(
                "Enter Account Holder Name: ",
                lambda x: len(x.strip()) > 0,
                "❌ Account holder name cannot be empty!"
            ).strip()

            # -------- IFSC CODE --------
            ifsc_code = self.validation.get_valid_input(
                "Enter IFSC Code (11 characters): ",
                lambda x: re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', x.upper()),
                "❌ Invalid IFSC code format!"
            ).upper()

            # -------- LAST FOUR DIGITS --------
            last_four_digits = self.validation.get_valid_input(
                "Enter Last 4 Digits of Account Number: ",
                lambda x: re.match(r'^\d{4}$', x),
                "❌ Must be exactly 4 digits!"
            )

            # -------- BALANCE --------
            balance = self.validation.get_valid_float(
                "Enter Current Account Balance (₹): ",
                lambda x: x >= 0,
                "❌ Balance cannot be negative!"
            )

            # -------- NICKNAME --------
            nickname = f"{bank_name} - {last_four_digits}"

            # -------- CONFIRM --------
            print("+-----------------------------------------------+")
            print(f"| Bank Name      : {bank_name:<28}|")
            print(f"| Account Holder : {account_holder:<28}|")
            print(f"| IFSC Code      : {ifsc_code:<28}|")
            print(f"| Last 4 Digits  : {last_four_digits:<28}|")
            print(f"| Balance        : ₹{balance:<26.2f}|")
            print("+-----------------------------------------------+")

            confirm = input("Confirm add bank account? (y/n): ").lower().strip()
            if confirm != 'y':
                print("+-----------------------------------------------+")
                print("| ❌ Operation cancelled.                       |")
                print("+-----------------------------------------------+")
                return

            # -------- SAVE TO DATABASE --------
            result = self.db.add_bank_account(
                self.logged_in_user_id,
                bank_name,
                account_holder,
                ifsc_code,
                last_four_digits,
                balance,
                nickname
            )

            if result:
                print("+-----------------------------------------------+")
                print("| ✅ Bank Account Added Successfully!          |")
                print("+-----------------------------------------------+")

                # Log action
                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Added bank account: {bank_name} ({last_four_digits})"
                )
            else:
                print("+-----------------------------------------------+")
                print("| ❌ Failed to add bank account!               |")
                print("+-----------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error: {str(e)[:38]:<38}|")
            print("+-----------------------------------------------+")

    def is_bank_linked(self):
        """Check if user has linked bank accounts"""
        accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)
        return accounts is not None and len(accounts) > 0

    def get_bank_balance(self):
        """Get total bank balance"""
        return self.db.get_bank_balance(self.logged_in_user_id)

    def is_investment_added(self):
        """Check if user has added investment accounts"""
        accounts = self.db.get_user_investment_accounts(self.logged_in_user_id)
        return accounts is not None and len(accounts) > 0

    def get_investment_balance(self):
        """Get total investment balance"""
        return self.db.get_investment_value(self.logged_in_user_id)

    def investment_account_setup(self):
        """Investment account setup functionality with combined name and type selection"""
        print("+-----------------------------------------------+")
        print("|        INVESTMENT ACCOUNT SETUP               |")
        print("+-----------------------------------------------+")

        try:
            # -------- SELECT INVESTMENT OPTION (NAME + TYPE) --------
            investment_options = {
                1: ("HDFC Equity Fund", "Mutual Fund"),
                2: ("SBI Large Cap Fund", "Mutual Fund"),
                3: ("ICICI Bluechip Fund", "Mutual Fund"),
                4: ("TCS Share", "Stock"),
                5: ("Reliance Share", "Stock"),
                6: ("Infosys Share", "Stock"),
                7: ("Bitcoin", "Crypto"),
                8: ("Ethereum", "Crypto"),
                9: ("Solana", "Crypto"),
                10: "Other"
            }

            print("+-----------------------------------------------+")
            print("|        Select Investment Option               |")
            print("+-----------------------------------------------+")
            for k, v in investment_options.items():
                if isinstance(v, tuple):
                    name, typ = v
                    print(f"| {k}. {name:<38}|")
                else:
                    print(f"| {k}. {v:<38}|")
            print("+-----------------------------------------------+")

            option_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in investment_options,
                "❌ Invalid investment option selection!"
            )

            if option_choice == 10:  # Other
                investment_name = self.validation.get_valid_input(
                    "Enter Investment Name: ",
                    lambda x: len(x.strip()) > 0,
                    "❌ Investment name cannot be empty!"
                ).strip()

                investment_types = {
                    1: "Stock",
                    2: "Mutual Fund",
                    3: "Crypto",
                    4: "FD",
                    5: "Other"
                }

                print("+-----------------------------------------------+")
                print("| Select Investment Type:                       |")
                for k, v in investment_types.items():
                    print(f"| {k}. {v:<38}|")
                print("+-----------------------------------------------+")

                type_choice = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: x in investment_types,
                    "❌ Invalid investment type!"
                )
                investment_type = investment_types[type_choice]
            else:
                investment_name, investment_type = investment_options[option_choice]

            # -------- SELECT PLATFORM (FILTERED BY INVESTMENT TYPE) --------
            platform_support = {
                "Mutual Fund": ["Zerodha", "Groww"],
                "Stock": ["Zerodha", "Groww", "Upstox", "Angel One"],
                "Crypto": ["Groww"],
                "FD": ["Other"],
                "Other": ["Other"]
            }

            supported_platforms = platform_support.get(investment_type, ["Other"])

            # Create numbered options
            platforms = {}
            for i, plat in enumerate(supported_platforms, 1):
                platforms[i] = plat

            print("+-----------------------------------------------+")
            print("| Select Platform:                              |")
            for k, v in platforms.items():
                print(f"| {k}. {v:<38}|")
            print("+-----------------------------------------------+")

            platform_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in platforms,
                "❌ Invalid platform selection!"
            )

            platform = platforms[platform_choice]

            if platform == "Other":
                platform = self.validation.get_valid_input(
                    "Enter Platform Name: ",
                    lambda x: len(x.strip()) > 0,
                    "❌ Platform name cannot be empty!"
                ).strip()

            # -------- QUANTITY AND PRICE --------
            if investment_type in ['Stock', 'Crypto']:
                # Symbol mapping for API calls
                symbol_map = {
                    "TCS Share": "TCS.NS",
                    "Reliance Share": "RELIANCE.NS",
                    "Infosys Share": "INFY.NS",
                    "Bitcoin": "BTC",
                    "Ethereum": "ETH",
                    "Solana": "SOL"
                }

                # Get real-time price from API first
                symbol = symbol_map.get(investment_name, "")
                current_price = None

                if symbol:
                    try:
                        function = "DIGITAL_CURRENCY_DAILY" if investment_type == 'Crypto' else "TIME_SERIES_DAILY"
                        url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&market=USD&apikey=demo"

                        response = requests.get(url, timeout=10)
                        data = response.json()

                        if 'Time Series (Daily)' in data or 'Time Series (Digital Currency Daily)' in data:
                            time_series_key = 'Time Series (Digital Currency Daily)' if investment_type == 'Crypto' else 'Time Series (Daily)'
                            dates = list(data[time_series_key].keys())
                            latest_date = max(dates)
                            latest_data = data[time_series_key][latest_date]

                            if investment_type == 'Crypto':
                                current_price = float(latest_data['4a. close (USD)'])
                            else:
                                current_price = float(latest_data['4. close'])

                            print("+-----------------------------------------------+")
                            print(f"| Current Price: ₹{current_price:.2f} per share/unit |")
                            print("+-----------------------------------------------+")
                        else:
                            print("+-----------------------------------------------+")
                            print("| ⚠️  Could not fetch real-time price. Using manual entry. |")
                            print("+-----------------------------------------------+")
                    except Exception as e:
                        print("+-----------------------------------------------+")
                        print("| ⚠️  API Error. Using manual entry.             |")
                        print("+-----------------------------------------------+")

                if current_price is None:
                    # Manual entry if API fails or symbol not found
                    current_price = self.validation.get_valid_float(
                        "Enter Current Price per Share/Unit (₹): ",
                        lambda x: x > 0,
                        "❌ Price must be positive!"
                    )

                # Now ask for quantity
                quantity = self.validation.get_valid_float(
                    "Enter Quantity (number of shares/units): ",
                    lambda x: x > 0,
                    "❌ Quantity must be positive!"
                )

                # Calculate amounts
                price_per_share = current_price
                invested_amount = quantity * current_price
                current_value = invested_amount

                print("+-----------------------------------------------+")
                print(f"| Quantity: {quantity:.0f} shares/units |")
                print(f"| Price per Share/Unit: ₹{price_per_share:.2f} |")
                print(f"| Total Invested: ₹{invested_amount:.2f} |")
                print("+-----------------------------------------------+")
            else:
                # For Mutual Funds and other investments
                quantity = 1  # Default for non-stock investments
                price_per_share = 0  # Not applicable

                invested_amount = self.validation.get_valid_float(
                    "Enter Invested Amount (₹): ",
                    lambda x: x >= 0,
                    "❌ Invested amount cannot be negative!"
                )
                current_value = invested_amount

            # -------- CONFIRM --------
            print("+-----------------------------------------------+")
            print(f"| Name      : {investment_name:<28}|")
            print(f"| Type      : {investment_type:<28}|")
            print(f"| Platform  : {platform:<28}|")
            print(f"| Invested  : ₹{invested_amount:<26.2f}|")
            print(f"| Current   : ₹{current_value:<26.2f}|")
            print("+-----------------------------------------------+")

            confirm = input("Confirm add investment account? (y/n): ").lower().strip()
            if confirm != 'y':
                print("+-----------------------------------------------+")
                print("| ❌ Operation cancelled.                       |")
                print("+-----------------------------------------------+")
                return

            # -------- SAVE TO DATABASE --------
            result = self.db.add_investment_account(
                self.logged_in_user_id,
                investment_name,
                investment_type,
                platform,
                invested_amount,
                current_value,
                quantity,
                price_per_share
            )

            if result:
                print("+-----------------------------------------------+")
                print("| ✅ Investment Account Added Successfully!    |")
                print("+-----------------------------------------------+")

                # Log action
                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Added investment: {investment_name} ({investment_type})"
                )
            else:
                print("+-----------------------------------------------+")
                print("| ❌ Failed to add investment account!          |")
                print("+-----------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error: {str(e)[:38]:<38}|")
            print("+-----------------------------------------------+")

    def display_investment_performance_live(self):

        investments = self.db.get_user_investment_accounts(self.logged_in_user_id)

        if not investments:
            print("No investments found")
            return

        # memory copy
        live_vals = {
            inv['investment_id']: float(inv['current_value'])
            for inv in investments
        }

        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')

                print("=== LIVE PORTFOLIO (Ctrl+C to save) ===")

                total_i = 0
                total_c = 0

                for inv in investments:
                    iid = inv['investment_id']
                    invested = float(inv['invested_amount'])

                    # 🔥 bounded fluctuation
                    pct = random.uniform(-0.05, 0.05)

                    # min move 0.15%
                    if abs(pct) < 0.0015:
                        pct = 0.0015 if pct > 0 else -0.0015

                    live_vals[iid] *= (1 + pct)

                    curr = live_vals[iid]
                    pl = curr - invested
                    p = (pl / invested * 100) if invested > 0 else 0

                    total_i += invested
                    total_c += curr

                    print(f"{inv['investment_name']}: ₹{curr:.2f}  P/L {p:.2f}%")

                print("\nPortfolio:",
                    f"₹{total_c-total_i:.2f}",
                    f"({(total_c-total_i)/total_i*100:.2f}%)")

                time.sleep(1)

        except KeyboardInterrupt:
            print("\nSaving values to DB...")

            for iid, val in live_vals.items():
                self.db.update_investment_account_value(iid, val)

            print("✅ Saved.")

    def reset_investment_values_to_invested(self):
        """Reset all investment current values to their invested amounts"""
        try:
            investments = self.db.get_user_investment_accounts(self.logged_in_user_id)

            if not investments:
                print("+------------------------------------------------+")
                print("| No investments found to reset.                 |")
                print("+------------------------------------------------+")
                return

            for inv in investments:
                invested_amount = inv['invested_amount']
                self.db.update_investment_account_value(inv['investment_id'], invested_amount)

            print("+------------------------------------------------+")
            print("| ✅ All investment values reset to invested amounts! |")
            print("+------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error resetting investment values: {str(e)[:15]:<15}|")
            print("+------------------------------------------------+")

    def get_live_or_simulated_price(self, inv):

        API_KEY = "demo"

        symbol_map = {
            "TCS Share": "TCS.NS",
            "Reliance Share": "RELIANCE.NS",
            "Infosys Share": "INFY.NS",
            "Bitcoin": "BTC",
            "Ethereum": "ETH",
            "Solana": "SOL"
        }

        invested_amount = inv['invested_amount']
        quantity = inv.get('quantity', 1)

        # ✅ Try API if mapped
        if inv['investment_name'] in symbol_map:
            try:
                symbol = symbol_map[inv['investment_name']]
                url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={API_KEY}"

                r = requests.get(url, timeout=5)
                data = r.json()

                ts = data.get("Time Series (Daily)")
                if ts:
                    latest = ts[max(ts.keys())]
                    price = float(latest["4. close"])
                    return quantity * price
            except:
                pass

        # ✅ Fallback simulation
        change_pct = random.uniform(-0.05, 0.05)
        return invested_amount * (1 + change_pct)


    def sell_remove_investment_account(self):
        """Sell/Remove investment account and credit proceeds to wallet"""
        try:
            investments = self.db.get_user_investment_accounts(self.logged_in_user_id)

            if not investments:
                print("+-----------------------------------------------+")
                print("| ❌ No investment accounts found!              |")
                print("+-----------------------------------------------+")
                return

            print("+-----------------------------------------------+")
            print("| Select Investment Account to Sell/Remove:     |")
            for i, inv in enumerate(investments, 1):
                print(f"| {i}. {inv['investment_name']} ({inv['investment_type']}) |")
                print(f"|    Current Value: ₹{inv['current_value']:.2f} |")
            print("+-----------------------------------------------+")

            choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: 1 <= x <= len(investments),
                "❌ Invalid investment selection!"
            )

            selected_investment = investments[choice - 1]
            current_value = selected_investment['current_value']

            print("+-----------------------------------------------+")
            print(f"| Investment: {selected_investment['investment_name']:<25}|")
            print(f"| Type: {selected_investment['investment_type']:<25}|")
            print(f"| Current Value: ₹{current_value:<23.2f}|")
            print("+-----------------------------------------------+")

            confirm = input("Confirm sell/remove this investment? (y/n): ").lower().strip()
            if confirm != 'y':
                print("+-----------------------------------------------+")
                print("| ❌ Operation cancelled.                       |")
                print("+-----------------------------------------------+")
                return

            # Add proceeds to wallet
            current_wallet_balance = self.db.get_user_balance(self.logged_in_user_id)
            new_wallet_balance = current_wallet_balance + current_value
            self.db.update_user_balance(self.logged_in_user_id, new_wallet_balance)

            # Remove investment account
            result = self.db.remove_investment_account(selected_investment['investment_id'])

            if result:
                print("+-----------------------------------------------+")
                print("| ✅ Investment sold/removed successfully!      |")
                print(f"| Proceeds added to wallet: ₹{current_value:<12.2f}|")
                print(f"| New wallet balance: ₹{new_wallet_balance:<12.2f}|")
                print("+-----------------------------------------------+")

                # Log action
                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Sold/removed investment: {selected_investment['investment_name']} (₹{current_value})"
                )
            else:
                print("+-----------------------------------------------+")
                print("| ❌ Failed to sell/remove investment!          |")
                print("+-----------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error selling/removing investment: {str(e)[:15]:<15}|")
            print("+-----------------------------------------------+")

    def update_investment_values_real_time(self):
        """Update investment values with random real-time fluctuations (0.1% to 0.12% up)"""
        try:
            investments = self.db.get_user_investment_accounts(self.logged_in_user_id)

            if not investments:
                return

            import random

            for inv in investments:
                current_value = inv['current_value']
                invested_amount = inv['invested_amount']

                # Apply 0.1% to 0.12% random fluctuation (always positive)
                change_pct = random.uniform(0.001, 0.0012)  # 0.1% to 0.12%

                # Calculate new value
                new_value = current_value * (1 + change_pct)

                # Ensure minimum value (can't go below 10% of invested amount)
                min_value = invested_amount * 0.1
                new_value = max(new_value, min_value)

                # Update in database
                self.db.update_investment_account_value(inv['investment_id'], new_value)

        except Exception as e:
            # Silently handle errors to avoid disrupting user experience
            pass

    def update_investment_values_once(self):
        investments = self.db.get_user_investment_accounts(self.logged_in_user_id)

        for inv in investments:
            new_value = self.get_live_or_simulated_price(inv)

            min_value = inv['invested_amount'] * 0.1
            new_value = max(new_value, min_value)

            self.db.update_investment_account_value(
                inv['investment_id'],
                new_value
            )

    def import_transactions_file(self):
        """Import transactions from CSV file"""
        print("+-----------------------------------------------+")
        print("|        IMPORT TRANSACTIONS (FILE)             |")
        print("+-----------------------------------------------+")

        try:
            # -------- FILE PATH --------
            file_path = self.validation.get_valid_input(
                "Enter CSV file path (e.g., transactions.csv): ",
                lambda x: len(x.strip()) > 0,
                "❌ File path cannot be empty!"
            ).strip()

            # -------- CHECK IF FILE EXISTS --------
            import os
            if not os.path.exists(file_path):
                print("+-----------------------------------------------+")
                print("| ❌ File not found!                            |")
                print("+-----------------------------------------------+")
                return

            # -------- SELECT ACCOUNT --------
            accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)
            if not accounts:
                print("+-----------------------------------------------+")
                print("| ❌ No bank accounts found!                    |")
                print("| Please add a bank account first.              |")
                print("+-----------------------------------------------+")
                return

            print("+-----------------------------------------------+")
            print("| Select Account for Import:                    |")
            for i, acc in enumerate(accounts, 1):
                print(f"| {i}. {acc['bank_name']} - {acc['last_four_digits']:<38}|")
            print("+-----------------------------------------------+")

            acc_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: 1 <= x <= len(accounts),
                "❌ Invalid account selection!"
            )
            selected_account = accounts[acc_choice - 1]

            # -------- CONFIRM --------
            print("+-----------------------------------------------+")
            print(f"| File     : {file_path:<28}|")
            print(f"| Account  : {selected_account['bank_name']} - {selected_account['last_four_digits']:<28}|")
            print("+-----------------------------------------------+")

            confirm = input("Confirm import? (y/n): ").lower().strip()
            if confirm != 'y':
                print("+-----------------------------------------------+")
                print("| ❌ Import cancelled.                          |")
                print("+-----------------------------------------------+")
                return

            # -------- IMPORT TRANSACTIONS --------
            import csv
            imported_count = 0
            skipped_count = 0

            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)

                for row in csv_reader:
                    try:
                        # Expected CSV format: date,description,type,amount
                        txn_date = row.get('date', '').strip()
                        description = row.get('description', '').strip()
                        txn_type = row.get('type', '').strip().upper()
                        amount_str = row.get('amount', '').strip()

                        # Validate data
                        if not txn_date or not description or not txn_type or not amount_str:
                            skipped_count += 1
                            continue

                        # Parse amount
                        amount = float(amount_str)

                        # Validate transaction type
                        if txn_type not in ['INCOME', 'EXPENSE']:
                            skipped_count += 1
                            continue

                        # Add transaction
                        result = self.db.add_imported_transaction(
                            self.logged_in_user_id,
                            selected_account['account_id'],
                            txn_date,
                            description,
                            txn_type,
                            amount
                        )

                        if result:
                            imported_count += 1
                        else:
                            skipped_count += 1

                    except (ValueError, KeyError):
                        skipped_count += 1
                        continue

            # -------- RESULT --------
            print("+-----------------------------------------------+")
            print("| ✅ Import Completed!                          |")
            print(f"| Imported : {imported_count:<28}|")
            print(f"| Skipped  : {skipped_count:<28}|")
            print("+-----------------------------------------------+")

            if imported_count > 0:
                # Log action
                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Imported {imported_count} transactions from {file_path}"
                )

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error importing file: {str(e)[:25]:<25}|")
            print("+-----------------------------------------------+")

    def manual_account_setup(self):
        """Manual account setup functionality"""
        print("+-----------------------------------------------+")
        print("|          MANUAL ACCOUNT SETUP                 |")
        print("+-----------------------------------------------+")

        try:
            # -------- ACCOUNT NAME --------
            account_name = self.validation.get_valid_input(
                "Enter Account Name (e.g., Cash, Petty Cash): ",
                lambda x: len(x.strip()) > 0,
                "❌ Account name cannot be empty!"
            ).strip()

            # -------- OPENING BALANCE --------
            opening_balance = self.validation.get_valid_float(
                "Enter Opening Balance (₹): ",
                lambda x: x >= 0,
                "❌ Opening balance cannot be negative!"
            )

            # -------- CONFIRM --------
            print("+-----------------------------------------------+")
            print(f"| Account Name   : {account_name:<28}|")
            print(f"| Opening Balance: ₹{opening_balance:<26.2f}|")
            print("+-----------------------------------------------+")

            confirm = input("Confirm add manual account? (y/n): ").lower().strip()
            if confirm != 'y':
                print("+-----------------------------------------------+")
                print("| ❌ Operation cancelled.                       |")
                print("+-----------------------------------------------+")
                return

            # -------- SAVE TO DATABASE --------
            result = self.db.add_manual_account(
                self.logged_in_user_id,
                account_name,
                opening_balance
            )

            if result:
                print("+-----------------------------------------------+")
                print("| ✅ Manual Account Added Successfully!        |")
                print("+-----------------------------------------------+")

                # Log action
                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Added manual account: {account_name} (₹{opening_balance})"
                )
            else:
                print("+-----------------------------------------------+")
                print("| ❌ Failed to add manual account!              |")
                print("+-----------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error: {str(e)[:38]:<38}|")
            print("+-----------------------------------------------+")


    def add_income(self):
        """Add income to selected account (UI wrapper)"""
        print("+------------------------------------------------+")
        print("|               ADD INCOME                      |")
        print("+------------------------------------------------+")

        try:
            # -------- SELECT ACCOUNT --------
            accounts = {
                1: "Bank Account",
                2: "Investment Account",
                3: "Other"
            }

            print("| Select Account Source:                        |")
            for k, v in accounts.items():
                print(f"| {k}. {v:<38}|")
            print("+------------------------------------------------+")

            acc_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in accounts,
                "❌ Invalid account selection!"
            )
            selected_account = accounts[acc_choice]

            # -------- SELECT SPECIFIC ACCOUNT IF BANK/INVESTMENT/OTHER --------
            account_id = None
            if acc_choice == 2:  # Bank Account
                bank_accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)
                if not bank_accounts:
                    print("+------------------------------------------------+")
                    print("| ❌ No bank accounts found! Please add a bank account first. |")
                    print("+------------------------------------------------+")
                    return

                print("+------------------------------------------------+")
                print("| Select Bank Account:                           |")
                for i, acc in enumerate(bank_accounts, 1):
                    print(f"| {i}. {acc['bank_name']} - {acc['last_four_digits']:<10} |")
                print("+------------------------------------------------+")

                acc_idx = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= len(bank_accounts),
                    "❌ Invalid account selection!"
                )
                account_id = bank_accounts[acc_idx - 1]['account_id']

            elif acc_choice == 3:  # Investment Account
                invest_accounts = self.db.get_user_investment_accounts(self.logged_in_user_id)
                if not invest_accounts:
                    print("+------------------------------------------------+")
                    print("| ❌ No investment accounts found! Please add an investment account first. |")
                    print("+------------------------------------------------+")
                    return

                print("+------------------------------------------------+")
                print("| Select Investment Account:                     |")
                for i, acc in enumerate(invest_accounts, 1):
                    print(f"| {i}. {acc['investment_name']} ({acc['investment_type']}) |")
                print("+------------------------------------------------+")

                acc_idx = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= len(invest_accounts),
                    "❌ Invalid account selection!"
                )
                account_id = invest_accounts[acc_idx - 1]['investment_id']

            elif acc_choice == 4:  # Other (Manual Account)
                manual_accounts = self.db.get_user_manual_accounts(self.logged_in_user_id)

                print("+------------------------------------------------+")
                print("| Select Manual Account:                         |")
                print("| 1. Create New Manual Account                  |")

                if manual_accounts:
                    for i, acc in enumerate(manual_accounts, 2):
                        print(f"| {i}. {acc['account_name']} (₹{acc['balance']:.2f}) |")
                print("+------------------------------------------------+")

                max_choice = len(manual_accounts) + 1 if manual_accounts else 1
                acc_choice_manual = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= max_choice,
                    "❌ Invalid account selection!"
                )

                if acc_choice_manual == 1:
                    # Create new manual account
                    account_name = self.validation.get_valid_input(
                        "Enter Account Name: ",
                        lambda x: len(x.strip()) > 0,
                        "❌ Account name cannot be empty!"
                    ).strip()

                    opening_balance = 0.00  # Start with zero for new accounts

                    result = self.db.add_manual_account(
                        self.logged_in_user_id,
                        account_name,
                        opening_balance
                    )

                    if result:
                        account_id = result
                        print("+------------------------------------------------+")
                        print("| ✅ Manual Account Created Successfully!       |")
                        print("+------------------------------------------------+")
                    else:
                        print("+------------------------------------------------+")
                        print("| ❌ Failed to create manual account!           |")
                        print("+------------------------------------------------+")
                        return
                else:
                    # Select existing account (choice 2, 3, etc. map to index 0, 1, etc.)
                    account_id = manual_accounts[acc_choice_manual - 2]['manual_account_id']

            # -------- SELECT INCOME CATEGORY --------
            categories = {
                1: "Salary",
                2: "Business",
                3: "Investment Income",
                4: "Rental Income",
                5: "Bonus / Gift",
                6: "Other Income"
            }

            print("+------------------------------------------------+")
            print("| Select Income Category:                       |")
            for k, v in categories.items():
                print(f"| {k}. {v:<38}|")
            print("+------------------------------------------------+")

            cat_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in categories,
                "❌ Invalid category selection!"
            )
            selected_category = categories[cat_choice]

            # -------- AMOUNT --------
            amount = self.validation.get_valid_float(
                "Enter Income Amount (₹): ",
                lambda x: x > 0,
                "❌ Amount must be positive!"
            )

            # -------- SOURCE --------
            source = self.validation.get_valid_input(
                "Enter Source: ",
                lambda x: len(x.strip()) > 0,
                "❌ Source cannot be empty!"
            )

            # -------- CONFIRM --------
            print("+------------------------------------------------+")
            if acc_choice == 4:  # Manual Account
                manual_accounts = self.db.get_user_manual_accounts(self.logged_in_user_id)
                selected_manual = next((acc for acc in manual_accounts if acc['manual_account_id'] == account_id), None)
                if selected_manual:
                    print(f"| Account  : {selected_manual['account_name']:<30}|")
                else:
                    print(f"| Account  : Manual Account (ID: {account_id})")
            else:
                print(f"| Account  : {selected_account:<30}|")
            print(f"| Category : {selected_category:<30}|")
            print(f"| Amount   : ₹{amount:<28.2f}|")
            print(f"| Note     : {source:<30}|")
            print("+------------------------------------------------+")

            confirm = input("Confirm add income? (y/n): ").lower().strip()
            if confirm != 'y':
                print("+------------------------------------------------+")
                print("| ❌ Operation cancelled.                       |")
                print("+------------------------------------------------+")
                return

            # -------- DELEGATE TO WALLET --------
            account_type = selected_account.lower().replace(" ", "_")
            if acc_choice == 4:  # Manual Account
                account_type = "manual_account"

            success, new_balance, message = self.wallet.process_income(
                self.logged_in_user_id,
                account_type,
                account_id,
                amount,
                selected_category,
                source,
                self.logged_in_user
            )

            if success:
                print("+------------------------------------------------+")
                print(f"| ✅ {message:<41}|")
                if acc_choice == 1:  # Only show balance for Wallet
                    print(f"| New Wallet Balance: ₹{new_balance:<12.2f}|")
                print("+------------------------------------------------+")
            else:
                print("+------------------------------------------------+")
                print(f"| ❌ {message:<45}|")
                print("+------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error adding income: {str(e)[:25]:<25}|")
            print("+------------------------------------------------+")
    

    def add_expense(self):
        """Add expense or redeem/withdraw (UI wrapper)"""
        try:
            # -------- SELECT ACCOUNT --------
            accounts = {
                1: "Bank Account",
                2: "Investment Account",
                3: "Other",
                4: "Add Investment Account"
            }

            print("+-----------------------------------------------+")
            print("| Select Account for Transaction:               |")
            for k, v in accounts.items():
                print(f"| {k}. {v:<38}|")
            print("+-----------------------------------------------+")

            acc_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in accounts,
                "❌ Invalid account selection!"
            )

            # Handle investment account setup
            if acc_choice == 5:
                self.investment_account_setup()
                return

            selected_account = accounts[acc_choice]
            account_id = None

            # -------- DETERMINE TRANSACTION TYPE --------
            if acc_choice == 3:  # Investment Account
                transaction_type = "REDEEM / WITHDRAW"
                amount_label = "Redeem/Withdraw Amount (₹)"
                category_label = "Select Redeem Category"
                confirm_message = "Confirm redeem/withdraw?"
                success_message = "Redeem/Withdraw Successful!"
            else:
                transaction_type = "ADD EXPENSE"
                amount_label = "Expense Amount (₹)"
                category_label = "Select Expense Category"
                confirm_message = "Confirm add expense?"
                success_message = "Expense Added Successfully!"

            print("+-----------------------------------------------+")
            print(f"|               {transaction_type:<29}|")
            print("+-----------------------------------------------+")

            # -------- SELECT SPECIFIC ACCOUNT IF BANK/INVESTMENT/OTHER --------
            if acc_choice == 2:  # Bank Account
                bank_accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)
                if not bank_accounts:
                    print("+-----------------------------------------------+")
                    print("| ❌ No bank accounts found! Please add a bank account first. |")
                    print("+-----------------------------------------------+")
                    return

                print("+-----------------------------------------------+")
                print("| Select Bank Account:                           |")
                for i, acc in enumerate(bank_accounts, 1):
                    print(f"| {i}. {acc['bank_name']} - {acc['last_four_digits']:<10} |")
                print("+-----------------------------------------------+")

                acc_idx = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= len(bank_accounts),
                    "❌ Invalid account selection!"
                )
                selected_bank = bank_accounts[acc_idx - 1]
                account_id = selected_bank['account_id']

                # Display balance
                balance = self.db.get_bank_account_balance(account_id)
                print("+-----------------------------------------------+")
                print(f"| Account Balance: ₹{balance:<26.2f}|")
                print("+-----------------------------------------------+")

            elif acc_choice == 3:  # Investment Account
                invest_accounts = self.db.get_user_investment_accounts(self.logged_in_user_id)
                if not invest_accounts:
                    print("+-----------------------------------------------+")
                    print("| ❌ No investment accounts found! Please add an investment account first. |")
                    print("+-----------------------------------------------+")
                    return

                print("+-----------------------------------------------+")
                print("| Select Investment Account:                     |")
                for i, acc in enumerate(invest_accounts, 1):
                    print(f"| {i}. {acc['investment_name']} ({acc['investment_type']}) |")
                print("+-----------------------------------------------+")

                acc_idx = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= len(invest_accounts),
                    "❌ Invalid account selection!"
                )
                account_id = invest_accounts[acc_idx - 1]['investment_id']

            elif acc_choice == 4:  # Other (Manual Account)
                manual_accounts = self.db.get_user_manual_accounts(self.logged_in_user_id)

                print("+-----------------------------------------------+")
                print("| Select Manual Account:                         |")
                print("| 1. Create New Manual Account                  |")

                if manual_accounts:
                    for i, acc in enumerate(manual_accounts, 2):
                        print(f"| {i}. {acc['account_name']} (₹{acc['balance']:.2f}) |")
                print("+-----------------------------------------------+")

                max_choice = len(manual_accounts) + 1 if manual_accounts else 1
                acc_choice_manual = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= max_choice,
                    "❌ Invalid account selection!"
                )

                if acc_choice_manual == 1:
                    # Create new manual account
                    account_name = self.validation.get_valid_input(
                        "Enter Account Name: ",
                        lambda x: len(x.strip()) > 0,
                        "❌ Account name cannot be empty!"
                    ).strip()

                    opening_balance = 0.00  # Start with zero for new accounts

                    notes = self.validation.get_valid_input(
                        "Enter Notes (optional, press enter to skip): ",
                        lambda x: True,
                        ""
                    ).strip()

                    result = self.db.add_manual_account(
                        self.logged_in_user_id,
                        account_name,
                        opening_balance,
                        notes
                    )

                    if result:
                        account_id = result
                        print("+-----------------------------------------------+")
                        print("| ✅ Manual Account Created Successfully!       |")
                        print("+-----------------------------------------------+")
                    else:
                        print("+-----------------------------------------------+")
                        print("| ❌ Failed to create manual account!           |")
                        print("+-----------------------------------------------+")
                        return
                else:
                    # Select existing account (choice 2, 3, etc. map to index 0, 1, etc.)
                    account_id = manual_accounts[acc_choice_manual - 2]['manual_account_id']

            # -------- AMOUNT --------
            amount = self.validation.get_valid_float(
                f"Enter {amount_label}: ",
                lambda x: x > 0,
                "❌ Amount must be positive!"
            )

            # -------- CHECK BALANCE FOR BANK ACCOUNT --------
            if acc_choice == 2:  # Bank Account
                balance = self.db.get_bank_account_balance(account_id)
                if amount > balance:
                    print("+-----------------------------------------------+")
                    print("| ❌ Insufficient balance!                      |")
                    print("+-----------------------------------------------+")
                    return

            # -------- CATEGORY --------
            categories = {
                1: "Food & Drinks",
                2: "Shopping",
                3: "Housing",
                4: "Transportation",
                5: "Vehicle",
                6: "Life & Entertainment",
                7: "Communication",
                8: "Healthcare",
                9: "Finance Expense",
                10: "Investments",
                11: "Education",
                12: "Others"
            }

            print("+-----------------------------------------------+")
            print(f"| {category_label:<45}|")
            for k, v in categories.items():
                print(f"| {k}. {v:<38}|")
            print("+-----------------------------------------------+")

            cat_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in categories,
                "❌ Invalid category!"
            )
            category = categories[cat_choice]

            # -------- DESCRIPTION --------
            description = self.validation.get_valid_input(
                "Enter Description: ",
                lambda x: len(x.strip()) > 0,
                "❌ Description cannot be empty!"
            )

            # -------- PAYMENT MODE (ONLY FOR WALLET, BANK, OTHER) --------
            if acc_choice in [1, 2, 4]:  # Wallet, Bank Account, Other
                if acc_choice == 1:  # Wallet
                    payment_modes = {
                        1: "Cash",
                        7: "Other"
                    }
                elif acc_choice == 2:  # Bank Account
                    payment_modes = {
                        1: "Cash",
                        2: "UPI",
                        3: "Debit Card",
                        4: "Credit Card",
                        5: "Net Banking",
                        7: "Other"
                    }
                else:  # Other (acc_choice == 4)
                    payment_modes = {
                        1: "Cash",
                        2: "UPI",
                        3: "Debit Card",
                        4: "Credit Card",
                        5: "Net Banking",
                        6: "Wallet",
                        7: "Other"
                    }
                print("+-----------------------------------------------+")
                print("| Select Payment Mode:                          |")
                for k, v in payment_modes.items():
                    print(f"| {k}. {v:<38}|")
                print("+-----------------------------------------------+")

                pm_choice = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: x in payment_modes,
                    "❌ Invalid payment mode!"
                )
                payment_mode = payment_modes[pm_choice]
            else:
                payment_mode = "N/A"  # Not applicable for Investment

            # -------- CONFIRM --------
            print("+-----------------------------------------------+")
            print(f"| Account   : {selected_account:<30}|")
            print(f"| Category  : {category:<30}|")
            print(f"| Amount    : ₹{amount:<28.2f}|")
            if acc_choice in [1, 2, 4]:
                print(f"| Pay Mode  : {payment_mode:<30}|")
            print(f"| Note      : {description:<30}|")
            print("+-----------------------------------------------+")

            if input(f"{confirm_message} (y/n): ").lower() != 'y':
                print("+-----------------------------------------------+")
                print("| ❌ Operation cancelled.                       |")
                print("+-----------------------------------------------+")
                return

            # -------- DELEGATE TO WALLET --------
            account_type = selected_account.lower().replace(" ", "_")
            if acc_choice == 4:  # Manual Account
                account_type = "manual_account"

            success, new_balance, message = self.wallet.process_expense(
                self.logged_in_user_id, account_type, account_id, amount, category, payment_mode, description, self.logged_in_user
            )

            if success:
                print("+-----------------------------------------------+")
                print(f"| ✅ {success_message:<41}|")
                if acc_choice == 1:  # Only show balance for Wallet
                    print(f"| New Wallet Balance: ₹{new_balance:<12.2f}|")
                print("+-----------------------------------------------+")
            else:
                print("+-----------------------------------------------+")
                print(f"| ❌ {message:<45}|")
                print("+-----------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error: {str(e)[:40]:<40}|")
            print("+-----------------------------------------------+")




    def transfer_money(self):
        """Transfer money to another user (UI wrapper)"""
        print("+-----------------------------------------------+")
        print("|              TRANSFER MONEY                   |")
        print("+-----------------------------------------------+")

        try:
            # -------- RECEIVER USERNAME --------
            receiver_username = self.validation.get_valid_input(
                "Enter Receiver Username: ",
                lambda x: x.strip() and x.strip() != self.logged_in_user,
                "❌ Invalid receiver username!"
            )

            receiver = self.db.get_user_by_username(receiver_username)
            if not receiver:
                print("+-----------------------------------------------+")
                print("| ❌ Receiver not found!                        |")
                print("+-----------------------------------------------+")
                return

            # -------- AMOUNT --------
            amount = self.validation.get_valid_float(
                "Enter Transfer Amount (₹): ",
                lambda x: x > 0,
                "❌ Amount must be positive!"
            )

            # -------- CONFIRM --------
            print("+-----------------------------------------------+")
            print(f"| From     : {self.logged_in_user:<28}|")
            print(f"| To       : {receiver_username:<28}|")
            print(f"| Amount   : ₹{amount:<26.2f}|")
            print("| Mode     : Wallet Transfer                   |")
            print("+-----------------------------------------------+")

            if input("Confirm transfer? (y/n): ").lower() != 'y':
                print("+-----------------------------------------------+")
                print("| ❌ Transfer cancelled.                        |")
                print("+-----------------------------------------------+")
                return

            # -------- DELEGATE TO WALLET --------
            success, message = self.wallet.process_transfer(
                self.logged_in_user_id, receiver["user_id"], amount, self.logged_in_user, receiver_username
            )

            if success:
                print("+-----------------------------------------------+")
                print("| ✅ Transfer Successful!                       |")
                print("+-----------------------------------------------+")
            else:
                print("+-----------------------------------------------+")
                print(f"| ❌ {message:<45}|")
                print("+-----------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Transfer Error: {str(e)[:40]:<40}|")
            print("+-----------------------------------------------+")


    def view_wallet_balance(self):
        """View balance of selected account with proper boxed UI"""
        try:
            BOX_WIDTH = 48

            def border():
                print("+" + "-" * (BOX_WIDTH - 2) + "+")

            def line(text=""):
                print(f"| {text.ljust(BOX_WIDTH - 4)} |")

            border()
            line("VIEW BALANCE")
            border()

            # -------- FETCH AVAILABLE ACCOUNTS --------
            available_accounts = {1: "Wallet"}

            if self.is_bank_linked():
                available_accounts[2] = "Bank Account"

            if self.is_investment_added():
                available_accounts[3] = "Investment Account"

            available_accounts[4] = "All Accounts (Net Worth)"

            line("Select Account to View Balance:")
            for k, v in available_accounts.items():
                line(f"{k}. {v}")
            border()

            choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in available_accounts,
                "❌ Invalid choice!"
            )

            border()

            # -------- WALLET --------
            if choice == 1:
                balance = self.db.get_user_total_balance(self.logged_in_user_id)
                line(f"Wallet Balance : ₹{balance:.2f}")

            # -------- BANK ACCOUNTS --------
            elif choice == 2:
                bank_accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)

                if bank_accounts:
                    line("Bank Accounts")
                    bank_total = 0

                    for acc in bank_accounts:
                        line(f"└─ {acc['bank_name']} - {acc['last_four_digits']}")
                        line(f"   Balance : ₹{acc['balance']:.2f}")
                        bank_total += acc['balance']

                    line(f"Bank Total : ₹{bank_total:.2f}")
                else:
                    line("No bank accounts found")

            # -------- INVESTMENT ACCOUNTS --------
            elif choice == 3:
                invest_accounts = self.db.get_user_investment_accounts(self.logged_in_user_id)

                if invest_accounts:
                    line("Investment Accounts")
                    invest_total = 0

                    for acc in invest_accounts:
                        line(f"└─ {acc['investment_name']} ({acc['investment_type']})")
                        line(f"   Value : ₹{acc['current_value']:.2f}")
                        invest_total += acc['current_value']

                    line(f"Investment Total : ₹{invest_total:.2f}")
                else:
                    line("No investment accounts found")

            # -------- NET WORTH --------
            elif choice == 4:
                wallet = self.db.get_user_balance(self.logged_in_user_id)
                total = wallet

                line(f"Wallet Balance : ₹{wallet:.2f}")

                # Bank breakdown
                if self.is_bank_linked():
                    bank_accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)
                    bank_total = 0

                    line("Bank Accounts")
                    for acc in bank_accounts:
                        line(f"└─ {acc['bank_name']} - {acc['last_four_digits']}")
                        line(f"   Balance : ₹{acc['balance']:.2f}")
                        bank_total += acc['balance']

                    line(f"Bank Total : ₹{bank_total:.2f}")
                    total += bank_total

                # Investment breakdown
                if self.is_investment_added():
                    invest_accounts = self.db.get_user_investment_accounts(self.logged_in_user_id)
                    invest_total = 0

                    line("Investment Accounts")
                    for acc in invest_accounts:
                        line(f"└─ {acc['investment_name']} ({acc['investment_type']})")
                        line(f"   Value : ₹{acc['current_value']:.2f}")
                        invest_total += acc['current_value']

                    line(f"Investment Total : ₹{invest_total:.2f}")
                    total += invest_total

                border()
                line(f"Total Net Worth : ₹{total:.2f}")

            border()

        except Exception as e:
            print("+" + "-" * 47 + "+")
            print(f"| ❌ Error: {str(e)[:37].ljust(37)} |")
            print("+" + "-" * 47 + "+")



    def monthly_summary(self):
        """Display monthly financial summary (Professional Version)"""
        try:
            print("+------------------------------------------------+")
            print("|              MONTHLY SUMMARY                   |")
            print("+------------------------------------------------+")

            # -------- SELECT MONTH --------
            current_date = datetime.now()
            while True:
                month_input = self.validation.get_valid_input(
                    "Enter month (YYYY-MM) [e.g. 2024-01]: ",
                    lambda x: len(x) == 7 and x[4] == '-',
                    "❌ Invalid month format! Use YYYY-MM"
                )

                try:
                    year, month = map(int, month_input.split('-'))
                    if month < 1 or month > 12:
                        print("+-----------------------------------------------+")
                        print("| ❌ Month must be between 1 and 12!            |")
                        print("+-----------------------------------------------+")
                        continue

                    selected_date = datetime(year, month, 1)
                    if selected_date > current_date:
                        print("+-----------------------------------------------+")
                        print("| ❌ Cannot select future dates!                |")
                        print("+-----------------------------------------------+")
                        continue

                    break
                except ValueError:
                    print("+-----------------------------------------------+")
                    print("| ❌ Invalid year or month!                     |")
                    print("+-----------------------------------------------+")
                    continue

            month = month_input

            # -------- INCOME --------
            income_query = """
                SELECT SUM(amount) AS total_income
                FROM income
                WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s
            """
            income = self.db.execute_query(
                income_query,
                (self.logged_in_user_id, month),
                fetch=True
            )[0]["total_income"] or 0

            # -------- EXPENSE --------
            expense_query = """
                SELECT SUM(amount) AS total_expense
                FROM expenses
                WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s
            """
            expense = self.db.execute_query(
                expense_query,
                (self.logged_in_user_id, month),
                fetch=True
            )[0]["total_expense"] or 0

            # -------- CATEGORY BREAKUP --------
            category_query = """
                SELECT category, SUM(amount) AS amount
                FROM expenses
                WHERE user_id = %s AND DATE_FORMAT(date, '%%Y-%%m') = %s
                GROUP BY category ORDER BY amount DESC
            """
            categories = self.db.execute_query(
                category_query,
                (self.logged_in_user_id, month),
                fetch=True
            )

            # -------- DISPLAY --------
            print("+------------------------------------------------+")
            print(f"| Month          : {month:<28}|")
            print(f"| Total Income   : ₹{income:<26.2f}|")
            print(f"| Total Expense  : ₹{expense:<26.2f}|")
            print(f"| Net Savings    : ₹{income - expense:<26.2f}|")
            print("+------------------------------------------------+")

            if categories:
                print("| Category-wise Expenses:                        |")
                for row in categories:
                    print(f"| {row['category']:<20}: ₹{row['amount']:<15.2f}|")
                print("+------------------------------------------------+")

            if income > 0:
                savings_pct = ((income - expense) / income) * 100
                print(f"| Savings Rate   : {savings_pct:<26.1f}|")
                print("+------------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error generating summary: {str(e)[:36]:<36}|")
            print("+-----------------------------------------------+")


    def set_budget(self):
        """Set monthly budget for a category (Professional Version)"""
        print("+------------------------------------------------+")
        print("|                SET BUDGET                      |")
        print("+------------------------------------------------+")

        try:
            # -------- SELECT MONTH --------
            month_key = self.validation.get_valid_input(
                "Enter budget month (YYYY-MM): ",
                lambda x: len(x) == 7 and x[4] == '-',
                "❌ Invalid month format! Use YYYY-MM"
            )

            # -------- VALIDATE MONTH (ONLY FUTURE) --------
            try:
                year, month = map(int, month_key.split('-'))
                selected_date = datetime(year, month, 1)
                current_date = datetime.now().replace(day=1)
                if selected_date <= current_date:
                    print("+-----------------------------------------------+")
                    print("| ❌ Can only set budget for future months!     |")
                    print("+-----------------------------------------------+")
                    return
            except ValueError:
                print("+-----------------------------------------------+")
                print("| ❌ Invalid year or month!                     |")
                print("+-----------------------------------------------+")
                return

            # -------- SELECT CATEGORY --------
            categories = {
                1: "Food & Drinks",
                2: "Shopping",
                3: "Housing",
                4: "Transportation",
                5: "Vehicle",
                6: "Life & Entertainment",
                7: "Communication",
                8: "Healthcare",
                9: "Finance Expense",
                10: "Education",
                11: "Utilities",
                12: "Others"
            }

            print("+------------------------------------------------+")
            print("| Select Category:                               |")
            for k, v in categories.items():
                print(f"| {k}. {v:<38}|")
            print("+------------------------------------------------+")

            cat_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in categories,
                "❌ Invalid category!"
            )
            category = categories[cat_choice]

            # -------- AMOUNT --------
            limit_amount = self.validation.get_valid_float(
                "Enter budget limit (₹): ",
                lambda x: x > 0,
                "❌ Budget must be positive!"
            )

            # -------- CHECK EXISTING BUDGET --------
            existing = self.get_existing_budget(category, month_key)

            if existing is not None:
                print("+------------------------------------------------+")
                print(f"| Existing Budget: ₹{existing:<26.2f}|")
                print("+------------------------------------------------+")
                if input("Overwrite existing budget? (y/n): ").lower() != 'y':
                    print("❌ Budget update cancelled.")
                    return

            # -------- DB UPDATE --------
            query = """
                INSERT INTO budget (user_id, category, month, limit_amount)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE limit_amount = %s
            """
            self.db.execute_query(
                query,
                (self.logged_in_user_id, category, month_key, limit_amount, limit_amount)
            )

            # -------- DSA UPDATE --------
            self.stack_queue.set_budget(
                self.logged_in_user_id,
                category,
                limit_amount,
                month_key
            )

            # -------- LOG --------
            self.db.log_action(
                f"User:{self.logged_in_user}",
                f"Set budget ₹{limit_amount} for {category} ({month_key})"
            )

            print("+------------------------------------------------+")
            print("| ✅ Budget Set Successfully!                   |")
            print("+------------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error setting budget: {str(e)[:36]:<36}|")
            print("+-----------------------------------------------+")

    def get_existing_budget(self, category, month_key):
        """Fetch existing budget for category & month (helper)"""
        query = """
            SELECT limit_amount FROM budget
            WHERE user_id = %s AND category = %s AND month = %s
        """
        result = self.db.execute_query(
            query,
            (self.logged_in_user_id, category, month_key),
            fetch=True
        )
        return result[0]["limit_amount"] if result else None


    def budget_status(self):
        """View budget status (Professional Version)"""
        try:
            print("+------------------------------------------------+")
            print("|              BUDGET STATUS                    |")
            print("+------------------------------------------------+")

            # -------- SELECT MONTH --------
            month_key = self.validation.get_valid_input(
                "Enter month (YYYY-MM): ",
                lambda x: len(x) == 7 and x[4] == '-',
                "❌ Invalid month format!"
            )

            budgets = self.stack_queue.get_all_budgets(
                self.logged_in_user_id,
                month_key
            )

            if not budgets:
                print("+------------------------------------------------+")
                print("| No budgets set for this month.                |")
                print("+------------------------------------------------+")
                return

            for category, data in budgets.items():
                spent = data.get("spent", 0)
                limit = data.get("limit", 0)
                remaining = limit - spent if limit > 0 else 0

                # -------- STATUS --------
                if spent < limit * 0.7:
                    status = "SAFE ✅"
                elif spent < limit:
                    status = "WARNING ⚠️"
                else:
                    status = "EXCEEDED ❌"

                print("+------------------------------------------------+")
                print(f"| Category   : {category:<30}|")
                print(f"| Budget     : ₹{limit:<26.2f}|")
                print(f"| Spent      : ₹{spent:<26.2f}|")
                print(f"| Remaining  : ₹{remaining:<26.2f}|")
                print(f"| Status     : {status:<26}|")

            print("+------------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error fetching budget status: {str(e)[:32]:<32}|")
            print("+-----------------------------------------------+")


    def top_expenses(self):
        """Display top expenses with period selection"""
        try:
            print("+------------------------------------------------+")
            print("|            TOP EXPENSES                        |")
            print("+------------------------------------------------+")
            print("| View Top Expenses For:                         |")
            print("| 1. This Month                                  |")
            print("| 2. Last Month                                  |")
            print("| 3. This Year                                   |")
            print("| 4. Custom (Month & Year)                       |")
            print("+------------------------------------------------+")

            choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in [1, 2, 3, 4],
                "❌ Invalid choice!"
            )

            current_date = datetime.now()
            month_key = None

            if choice == 1:  # This Month
                month_key = current_date.strftime("%Y-%m")
            elif choice == 2:  # Last Month
                last_month = current_date.replace(day=1) - timedelta(days=1)
                month_key = last_month.strftime("%Y-%m")
            elif choice == 3:  # This Year
                year = current_date.year
                # Get top expenses for the year (we'll need to modify get_top_expenses to handle year)
                month_key = f"{year}"
            elif choice == 4:  # Custom
                year = self.validation.get_valid_int(
                    "Enter year (YYYY): ",
                    lambda x: 2000 <= x <= current_date.year,
                    "❌ Invalid year!"
                )
                month = self.validation.get_valid_int(
                    "Enter month (1-12): ",
                    lambda x: 1 <= x <= 12,
                    "❌ Invalid month!"
                )
                month_key = f"{year}-{month:02d}"

                # Prevent future dates
                selected_date = datetime(year, month, 1)
                if selected_date > current_date:
                    print("+------------------------------------------------+")
                    print("| ❌ Cannot select future dates!                |")
                    print("+------------------------------------------------+")
                    return

            top_expenses = self.stack_queue.get_top_expenses(month_key)

            if not top_expenses:
                print("+------------------------------------------------+")
                print("| No expenses found for selected period.        |")
                print("+------------------------------------------------+")
                return

            for i, exp in enumerate(top_expenses, 1):
                print("+------------------------------------------------+")
                print(f"| {i}. Amount   : ₹{exp['amount']:<15.2f}|")
                print(f"|    Category : {exp['category']:<18}|")
                print(f"|    Note     : {exp.get('note', 'N/A'):<18}|")
                print(f"|    Date     : {exp['date'].strftime('%Y-%m-%d'):<18}|")

            print("+------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error fetching top expenses: {str(e)[:20]:<20}|")
            print("+------------------------------------------------+")


    def undo_last_transaction(self):
        """Undo last transaction (Account-aware, Professional)"""
        try:
            last_txn = self.stack_queue.undo_last_transaction()

            if not last_txn:
                print("+-----------------------------------------------+")
                print("| No transactions to undo.                      |")
                print("+-----------------------------------------------+")
                return

            print("+-----------------------------------------------+")
            print("|        UNDO LAST TRANSACTION                  |")
            print("+-----------------------------------------------+")
            print(f"| Type    : {last_txn['type']:<30}|")
            print(f"| Amount  : ₹{last_txn['amount']:<26.2f}|")

            # -------- EXPENSE UNDO --------
            if last_txn["type"] == "EXPENSE":
                current_balance = self.db.get_user_balance(self.logged_in_user_id)
                new_balance = current_balance + last_txn["amount"]

                if self.db.update_user_balance(self.logged_in_user_id, new_balance):
                    self.db.log_action(
                        f"User:{self.logged_in_user}",
                        f"Undo EXPENSE ₹{last_txn['amount']}"
                    )
                    print("| ✅ Expense undone successfully!              |")
                    print(f"| Restored Balance: ₹{new_balance:<14.2f}|")

            # -------- INCOME UNDO --------
            elif last_txn["type"] == "INCOME":
                current_balance = self.db.get_user_balance(self.logged_in_user_id)
                new_balance = current_balance - last_txn["amount"]

                if new_balance < 0:
                    print("+-----------------------------------------------+")
                    print("| ❌ Cannot undo income (negative balance).    |")
                    print("+-----------------------------------------------+")
                    return

                if self.db.update_user_balance(self.logged_in_user_id, new_balance):
                    self.db.log_action(
                        f"User:{self.logged_in_user}",
                        f"Undo INCOME ₹{last_txn['amount']}"
                    )
                    print("| ✅ Income undone successfully!               |")
                    print(f"| Updated Balance: ₹{new_balance:<14.2f}|")

            # -------- TRANSFER UNDO --------
            elif last_txn["type"] == "TRANSFER":
                # NOTE: Transfer record not deleted, only balance rollback
                sender_id = last_txn["sender_id"]
                receiver_id = last_txn["receiver_id"]
                amount = last_txn["amount"]

                receiver_balance = self.db.get_user_balance(receiver_id)
                if receiver_balance < amount:
                    print("+-----------------------------------------------+")
                    print("| ❌ Cannot undo transfer (receiver spent money)|")
                    print("+-----------------------------------------------+")
                    return

                # Rollback balances
                self.db.update_user_balance(sender_id,
                    self.db.get_user_balance(sender_id) + amount
                )
                self.db.update_user_balance(receiver_id,
                    receiver_balance - amount
                )

                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Undo TRANSFER ₹{amount}"
                )

                print("| ✅ Transfer undone successfully!             |")

            else:
                print("| ❌ Unknown transaction type.                 |")

            print("+-----------------------------------------------+")

        except Exception as e:
            print("+-----------------------------------------------+")
            print(f"| ❌ Error undoing transaction: {str(e)[:36]:<36}|")
            print("+-----------------------------------------------+")


    def update_profile(self):
        """Update user profile"""
        print("+-----------------------------------+")
        print("|      UPDATE PROFILE               |")
        print("+-----------------------------------+")
        print("| 1. Change Email                   |")
        print("| 2. Change Password                |")
        print("| 3. Change Mobile Number           |")
        print("| 0. Back                           |")
        print("+-----------------------------------+")

        try:
            choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: 0 <= x <= 3,
                "❌ Invalid choice!"
            )

            if choice == 1:
                self.update_email()
            elif choice == 2:
                self.update_password()
            elif choice == 3:
                self.update_mobile()
            elif choice == 0:
                return

        except Exception as e:
            print("+-----------------------------------+")
            print(f"| ❌ Error updating profile: {str(e)[:25]:<25}|")
            print("+-----------------------------------+")

    def update_email(self):
        """Update user email (Professional Version)"""
        try:
            # -------- GET CURRENT EMAIL --------
            user = self.db.get_user_by_id(self.logged_in_user_id)
            current_email = user["email"]

            print("+-----------------------------------+")
            print("|        UPDATE EMAIL               |")
            print("+-----------------------------------+")
            print(f"| Current Email: {current_email}")
            print("+-----------------------------------+")

            # -------- NEW EMAIL INPUT --------
            new_email = self.validation.get_valid_input(
                "Enter new email (@gmail.com): ",
                lambda x: re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', x.lower()),
                "❌ Invalid Gmail address!"
            ).lower()

            # -------- SAME EMAIL CHECK --------
            if new_email == current_email:
                print("+-----------------------------------+")
                print("| ❌ New email cannot be same as current email! |")
                print("+-----------------------------------+")
                return

            # -------- DUPLICATE EMAIL CHECK --------
            existing_user = self.db.get_user_by_email(new_email)
            if existing_user:
                print("+-----------------------------------+")
                print("| ❌ This email is already linked to another account! |")
                print("+-----------------------------------+")
                return

            # -------- CONFIRM --------
            print("+-----------------------------------+")
            print(f"| New Email: {new_email}")
            print("+-----------------------------------+")
            confirm = input("Confirm update? (y/n): ").lower().strip()
            if confirm != 'y':
                print("+-----------------------------------+")
                print("| ❌ Update cancelled.              |")
                print("+-----------------------------------+")
                return

            # -------- UPDATE DATABASE --------
            query = "UPDATE users SET email = %s WHERE user_id = %s"
            self.db.execute_query(query, (new_email, self.logged_in_user_id))

            # -------- LOG --------
            self.db.log_action(
                f"User:{self.logged_in_user}",
                f"Updated email from {current_email} to {new_email}"
            )

            print("+-----------------------------------+")
            print("| ✅ Email updated successfully!    |")
            print("+-----------------------------------+")

        except Exception as e:
            print("+-----------------------------------+")
            print(f"| ❌ Error updating email: {str(e)[:25]:<25}|")
            print("+-----------------------------------+")


    def update_password(self):
        """Update user password (Hashed + Secure)"""
        try:
            old_password = self.validation.get_valid_input(
                "Enter current password: ",
                lambda x: len(x) > 0,
                "❌ Password cannot be empty!"
            )

            user = self.db.get_user_by_id(self.logged_in_user_id)

            # HASH old password before compare
            old_hash = hashlib.sha256(old_password.encode()).hexdigest()

            if user["password"] != old_hash:
                print("+-----------------------------------+")
                print("| ❌ Incorrect current password!    |")
                print("+-----------------------------------+")
                return

            new_password = self.validation.get_valid_input(
                "Enter new password: ",
                lambda x: len(x) >= 6,
                "❌ Password must be at least 6 characters!"
            )

            if old_password == new_password:
                print("+-----------------------------------+")
                print("| ❌ New password cannot be same as old password! |")
                print("+-----------------------------------+")
                return

            if input("Confirm update? (y/n): ").lower() != 'y':
                print("+-----------------------------------+")
                print("| ❌ Update cancelled.              |")
                print("+-----------------------------------+")
                return

            new_hash = hashlib.sha256(new_password.encode()).hexdigest()

            query = "UPDATE users SET password = %s WHERE user_id = %s"
            self.db.execute_query(query, (new_hash, self.logged_in_user_id))

            self.db.log_action(
                f"User:{self.logged_in_user}",
                "Updated password"
            )

            print("+-----------------------------------+")
            print("| ✅ Password updated successfully! |")
            print("+-----------------------------------+")

        except Exception as e:
            print("+-----------------------------------+")
            print(f"| ❌ Error updating password: {str(e)[:25]:<25}|")
            print("+-----------------------------------+")



    def update_mobile(self):
        """Update user mobile"""
        try:
            new_mobile = self.validation.get_valid_input(
                "Enter new mobile number:",
                lambda x: re.match(r'^[6-9]\d{9}$', x),
                "❌ Invalid mobile number!"
            )

            confirm = input("Confirm update? (y/n): ").lower().strip()
            if confirm != 'y':
                print("+-----------------------------------+")
                print("| ❌ Update cancelled.              |")
                print("+-----------------------------------+")
                return

            query = "UPDATE users SET mobile = %s WHERE user_id = %s"
            if self.db.execute_query(query, (new_mobile, self.logged_in_user_id)):
                print("+-----------------------------------+")
                print("| ✅ Mobile updated successfully!   |")
                print("+-----------------------------------+")
                self.db.log_action(f"User: {self.logged_in_user}", "Updated mobile")
            else:
                print("+-----------------------------------+")
                print("| ❌ Failed to update mobile!       |")
                print("+-----------------------------------+")

        except Exception as e:
            print("+-----------------------------------+")
            print(f"| ❌ Error updating mobile: {str(e)[:25]:<25}|")
            print("+-----------------------------------+")

    def transaction_history(self):
        """Display comprehensive transaction history with detailed metadata"""
        try:
            print("+------------------------------------------------+")
            print("|        COMPREHENSIVE TRANSACTION HISTORY       |")
            print("+------------------------------------------------+")
            print("| View Transactions For:                         |")
            print("| 1. This Month                                  |")
            print("| 2. Last Month                                  |")
            print("| 3. This Year                                   |")
            print("| 4. Custom (Month & Year)                       |")
            print("| 5. All Time                                    |")
            print("+------------------------------------------------+")

            choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in [1, 2, 3, 4, 5],
                "❌ Invalid choice!"
            )

            current_date = datetime.now()
            date_filter = None

            if choice == 1:  # This Month
                date_filter = current_date.strftime("%Y-%m")
            elif choice == 2:  # Last Month
                last_month = current_date.replace(day=1) - timedelta(days=1)
                date_filter = last_month.strftime("%Y-%m")
            elif choice == 3:  # This Year
                date_filter = str(current_date.year)
            elif choice == 4:  # Custom
                year = self.validation.get_valid_int(
                    "Enter year (YYYY): ",
                    lambda x: 2000 <= x <= current_date.year,
                    "❌ Invalid year!"
                )
                month = self.validation.get_valid_int(
                    "Enter month (1-12): ",
                    lambda x: 1 <= x <= 12,
                    "❌ Invalid month!"
                )
                date_filter = f"{year}-{month:02d}"

                # Prevent future dates
                selected_date = datetime(year, month, 1)
                if selected_date > current_date:
                    print("+------------------------------------------------+")
                    print("| ❌ Cannot select future dates!                |")
                    print("+------------------------------------------------+")
                    return
            elif choice == 5:  # All Time
                date_filter = None

            # Get all transactions
            transactions = self.db.get_user_transaction_history(self.logged_in_user_id, date_filter)

            if not transactions:
                print("+------------------------------------------------+")
                print("| No transactions found for selected period.    |")
                print("+------------------------------------------------+")
                return

            # Display comprehensive transaction details
            print("+------------------------------------------------------------------------------------------------------------------------------------------------+")
            print("| DETAILED TRANSACTION RECORD FILE                                                                                                              |")
            print("+------------------------------------------------------------------------------------------------------------------------------------------------+")
            print("| #  | Date & Time       | Account Type | Account Details               | Purpose/Category         | Amount      | Balance After | Type     |")
            print("+------------------------------------------------------------------------------------------------------------------------------------------------+")

            for i, txn in enumerate(transactions[:20], 1):  # Show last 20 transactions for better detail
                if txn is None:
                    continue

                txn_type = txn.get('type', '')
                amount = txn.get('amount', 0)

                # Handle None date
                txn_date = txn.get('date')
                if txn_date is not None:
                    date_time_str = txn_date.strftime('%Y-%m-%d %H:%M')
                else:
                    date_time_str = ''

                # Account details
                account_type = txn.get('account_type', 'Unknown').title()
                account_name = txn.get('account_name', '')

                # Category and source details
                category = txn.get('category', '')
                source = txn.get('source', '')

                # Balance after
                balance_after = txn.get('balance_after')
                if balance_after is not None and isinstance(balance_after, (int, float)):
                    balance_after_str = f"₹{balance_after:>10.2f}"
                else:
                    balance_after_str = ""

                # Determine investment/goal destination
                destination = ""
                if txn_type == 'INCOME' and category == 'Business Income':
                    destination = " (Towards Goal)"
                elif txn.get('account_type') == 'investment' and txn_type == 'EXPENSE':
                    destination = f" (Invested in {account_name})" if account_name else " (Investment)"
                elif txn_type == 'EXPENSE' and category in ['Investments', 'Finance Expense']:
                    destination = " (Investment Related)"

                # Format amount with sign and type
                if txn_type == 'INCOME':
                    amount_str = f"+₹{amount:>10.2f}"
                    type_indicator = "📈"
                    purpose_category = f"{category}/{source}" if category else source
                elif txn_type == 'EXPENSE':
                    amount_str = f"-₹{amount:>10.2f}"
                    type_indicator = "📉"
                    purpose_category = f"{category}/{source}" if category else category
                elif txn_type == 'TRANSFER':
                    direction = "To" if txn.get('sender_id') == self.logged_in_user_id else "From"
                    receiver = txn.get('receiver_username', 'Unknown')
                    amount_str = f"-₹{amount:>10.2f}" if txn.get('sender_id') == self.logged_in_user_id else f"+₹{amount:>10.2f}"
                    type_indicator = "🔄"
                    purpose_category = f"Transfer {direction} {receiver}"
                else:
                    amount_str = f"₹{amount:>11.2f}"
                    type_indicator = "❓"
                    purpose_category = ""

                # Truncate long strings for display
                account_name = account_name[:28] if len(account_name) > 28 else account_name
                purpose_category = purpose_category[:22] if len(purpose_category) > 22 else purpose_category

                print(f"| {i:2d} | {date_time_str:<15} | {account_type:<11} | {account_name:<29} | {purpose_category:<22} | {amount_str:<11} | {balance_after_str:<12} | {type_indicator} {txn_type:<6} |")

                # Add detailed information for investment transactions
                if txn.get('account_type') == 'investment':
                    # Get additional investment details
                    investment_details = self.db.get_investment_account_details(txn.get('transaction_id'))
                    if investment_details:
                        inv_type = investment_details.get('investment_type', '')
                        platform = investment_details.get('platform', '')
                        quantity = investment_details.get('quantity', '')
                        price_per_share = investment_details.get('price_per_share', '')

                        print(f"|    | Investment Details: Type={inv_type}, Platform={platform}, Qty={quantity}, Price=₹{price_per_share} |")
                        print("+------------------------------------------------------------------------------------------------------------------------------------------------+")

            print("+------------------------------------------------------------------------------------------------------------------------------------------------+")

            # Summary statistics (filter out None transactions)
            valid_transactions = [txn for txn in transactions if txn is not None]
            total_income = sum(txn['amount'] for txn in valid_transactions if txn['type'] == 'INCOME')
            total_expense = sum(txn['amount'] for txn in valid_transactions if txn['type'] == 'EXPENSE')
            total_transfers = sum(txn['amount'] for txn in valid_transactions if txn['type'] == 'TRANSFER' and txn.get('sender_id') == self.logged_in_user_id)
            net_flow = total_income - total_expense - total_transfers

            print("+------------------------------------------------------------------------------------------------------------------------------------------------+")
            print(f"| SUMMARY: {len(transactions):<3d} transactions | Income: ₹{total_income:>10.2f} | Expenses: ₹{total_expense:>10.2f} | Transfers: ₹{total_transfers:>10.2f} | Net: ₹{net_flow:>10.2f} |")
            print("+------------------------------------------------------------------------------------------------------------------------------------------------+")

            # Additional details for investment transactions
            investment_txns = [t for t in transactions if t.get('account_type') == 'investment']
            if investment_txns:
                print("| 📊 INVESTMENT TRANSACTIONS BREAKDOWN:                                                                                                         |")
                for txn in investment_txns[:5]:  # Show first 5 investment transactions
                    inv_details = txn.get('account_name', 'N/A')
                    print(f"|   - {inv_details:<110} |")
                if len(investment_txns) > 5:
                    print(f"|   ... and {len(investment_txns) - 5} more investment transactions                                                                                |")
                print("+------------------------------------------------------------------------------------------------------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error fetching transaction history: {str(e)[:20]:<20}|")
            print("+------------------------------------------------+")

    def financial_goals_menu(self):
        """Financial goals management menu"""
        while True:
            print("+------------------------------------------------+")
            print("|            FINANCIAL GOALS                     |")
            print("+------------------------------------------------+")
            print("| 1. Set New Goal                                |")
            print("| 2. View Active Goals                           |")
            print("| 3. Update Goal Progress                        |")
            print("| 4. Change Goal Target Amount                   |")
            print("| 5. Stop/Cancel Goal                            |")
            print("| 6. Adjust Goal for Price Change                |")
            print("| 0. Back                                        |")
            print("+------------------------------------------------+")

            choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: 0 <= x <= 6,
                "❌ Invalid choice!"
            )

            if choice == 1:
                self.set_financial_goal()
            elif choice == 2:
                self.view_financial_goals()
            elif choice == 3:
                self.update_goal_progress()
            elif choice == 4:
                self.change_goal_target_amount()
            elif choice == 5:
                self.stop_financial_goal()
            elif choice == 6:
                self.adjust_goal_for_price_change()
            elif choice == 0:
                break

    def set_financial_goal(self):
        """Set a new financial goal"""
        try:
            print("+------------------------------------------------+")
            print("|            SET FINANCIAL GOAL                  |")
            print("+------------------------------------------------+")

            # Goal name
            goal_name = self.validation.get_valid_input(
                "Enter goal name (e.g., New Car, Vacation): ",
                lambda x: len(x.strip()) > 0,
                "❌ Goal name cannot be empty!"
            ).strip()

            # Target amount
            target_amount = self.validation.get_valid_float(
                "Enter target amount (₹): ",
                lambda x: x > 0,
                "❌ Target amount must be positive!"
            )

            # Account type selection
            print("+------------------------------------------------+")
            print("| Select Account Type:                           |")
            print("| 1. Wallet                                      |")
            print("| 2. Bank Account                                |")
            print("| 3. Investment Account                          |")
            print("+------------------------------------------------+")

            acc_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in [1, 2, 3],
                "❌ Invalid account selection!"
            )

            account_type = {1: "wallet", 2: "bank", 3: "investment"}[acc_choice]
            account_id = None

            # If bank or investment, select specific account
            if account_type == "bank":
                bank_accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)
                if not bank_accounts:
                    print("+------------------------------------------------+")
                    print("| ❌ No bank accounts found! Please add a bank account first. |")
                    print("+------------------------------------------------+")
                    return

                print("+------------------------------------------------+")
                print("| Select Bank Account:                           |")
                for i, acc in enumerate(bank_accounts, 1):
                    print(f"| {i}. {acc['bank_name']} - {acc['last_four_digits']:<10} |")
                print("+------------------------------------------------+")

                acc_idx = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= len(bank_accounts),
                    "❌ Invalid account selection!"
                )
                account_id = bank_accounts[acc_idx - 1]['account_id']

            elif account_type == "investment":
                invest_accounts = self.db.get_user_investment_accounts(self.logged_in_user_id)
                if not invest_accounts:
                    print("+------------------------------------------------+")
                    print("| ❌ No investment accounts found! Please add an investment account first. |")
                    print("+------------------------------------------------+")
                    return

                print("+------------------------------------------------+")
                print("| Select Investment Account:                     |")
                for i, acc in enumerate(invest_accounts, 1):
                    print(f"| {i}. {acc['investment_name']} ({acc['investment_type']}) |")
                print("+------------------------------------------------+")

                acc_idx = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= len(invest_accounts),
                    "❌ Invalid account selection!"
                )
                account_id = invest_accounts[acc_idx - 1]['investment_id']

            # Months to achieve
            months_to_achieve = self.validation.get_valid_int(
                "Enter months to achieve goal: ",
                lambda x: x > 0,
                "❌ Months must be positive!"
            )

            # Calculate monthly savings
            monthly_savings = target_amount / months_to_achieve

            # Confirm
            print("+------------------------------------------------+")
            print(f"| Goal Name      : {goal_name:<30}|")
            print(f"| Target Amount  : ₹{target_amount:<26.2f}|")
            print(f"| Account Type   : {account_type:<30}|")
            print(f"| Months         : {months_to_achieve:<30}|")
            print(f"| Monthly Savings: ₹{monthly_savings:<26.2f}|")
            print("+------------------------------------------------+")

            if input("Confirm create goal? (y/n): ").lower() != 'y':
                print("+------------------------------------------------+")
                print("| ❌ Goal creation cancelled.                    |")
                print("+------------------------------------------------+")
                return

            # Save to database
            result = self.db.add_financial_goal(
                self.logged_in_user_id,
                account_type,
                account_id,
                goal_name,
                target_amount,
                months_to_achieve,
                monthly_savings
            )

            if result:
                print("+------------------------------------------------+")
                print("| ✅ Financial Goal Created Successfully!       |")
                print("+------------------------------------------------+")

                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Created financial goal: {goal_name} (₹{target_amount})"
                )
            else:
                print("+------------------------------------------------+")
                print("| ❌ Failed to create financial goal!           |")
                print("+------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error creating financial goal: {str(e)[:25]:<25}|")
            print("+------------------------------------------------+")

    def view_financial_goals(self):
        """View active financial goals"""
        try:
            goals = self.db.get_user_financial_goals(self.logged_in_user_id)

            if not goals:
                print("+------------------------------------------------+")
                print("| No financial goals found.                      |")
                print("+------------------------------------------------+")
                return

            print("+------------------------------------------------+")
            print("|            YOUR FINANCIAL GOALS                |")
            print("+------------------------------------------------+")

            for goal in goals:
                progress_pct = (goal['current_savings'] / goal['target_amount']) * 100
                status = goal['status']

                print(f"| Goal: {goal['goal_name']:<35}|")
                print(f"| Target: ₹{goal['target_amount']:<28.2f}|")
                print(f"| Current: ₹{goal['current_savings']:<27.2f}|")
                print(f"| Progress: {progress_pct:<27.1f}%|")
                print(f"| Monthly: ₹{goal['monthly_savings']:<27.2f}|")
                print(f"| Status: {status:<32}|")
                print("+------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error fetching financial goals: {str(e)[:20]:<20}|")
            print("+------------------------------------------------+")

    def update_goal_progress(self):
        """Update progress on a financial goal with monthly savings check and business income option"""
        try:
            goals = self.db.get_user_financial_goals(self.logged_in_user_id)

            if not goals:
                print("+------------------------------------------------+")
                print("| ❌ No active goals found!                      |")
                print("+------------------------------------------------+")
                return

            print("+------------------------------------------------+")
            print("| Select Goal to Update:                         |")
            for i, goal in enumerate(goals, 1):
                print(f"| {i}. {goal['goal_name']:<35}|")
            print("+------------------------------------------------+")

            goal_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: 1 <= x <= len(goals),
                "❌ Invalid goal selection!"
            )

            selected_goal = goals[goal_choice - 1]

            print("+------------------------------------------------+")
            print("| Update Goal Progress:                          |")
            print("| 1. Add Monthly Savings                         |")
            print("| 2. Add Income from Account                     |")
            print("| 3. Change Goal Target Amount                   |")
            print("| 4. Change Monthly Savings Amount               |")
            print("| 5. Adjust Target for Price Change              |")
            print("+------------------------------------------------+")

            update_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: x in [1, 2, 3, 4, 5, 6],
                "❌ Invalid choice!"
            )

            if update_choice == 1:  # Monthly Savings
                monthly_amount = selected_goal['monthly_savings']

                # Always ask user to select account for payment
                print("+------------------------------------------------+")
                print("| Select Account for Payment:                    |")
                print("| 1. Wallet                                      |")
                print("| 2. Bank Account                                |")
                print("| 3. Investment Account                          |")
                print("| 4. Cash                                        |")
                print("+------------------------------------------------+")

                payment_choice = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: 1 <= x <= 4,
                    "❌ Invalid choice!"
                )

                # Handle different payment modes
                if payment_choice == 1:  # Wallet
                    wallet_balance = self.db.get_user_balance(self.logged_in_user_id)
                    if wallet_balance < monthly_amount:
                        print("+------------------------------------------------+")
                        print("| ❌ Insufficient wallet balance!                |")
                        print("+------------------------------------------------+")
                        return

                    new_wallet_balance = wallet_balance - monthly_amount
                    self.db.update_user_balance(self.logged_in_user_id, new_wallet_balance)

                elif payment_choice == 2:  # Bank Account
                    bank_accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)
                    if not bank_accounts:
                        print("+------------------------------------------------+")
                        print("| ❌ No bank accounts found!                     |")
                        print("+------------------------------------------------+")
                        return

                    print("+------------------------------------------------+")
                    print("| Select Bank Account:                           |")
                    for i, acc in enumerate(bank_accounts, 1):
                        print(f"| {i}. {acc['bank_name']} - {acc['last_four_digits']:<10} |")
                    print("+------------------------------------------------+")

                    acc_idx = self.validation.get_valid_int(
                        "Enter choice: ",
                        lambda x: 1 <= x <= len(bank_accounts),
                        "❌ Invalid account selection!"
                    )
                    selected_bank = bank_accounts[acc_idx - 1]
                    bank_balance = self.db.get_bank_account_balance(selected_bank['account_id'])

                    if bank_balance < monthly_amount:
                        print("+------------------------------------------------+")
                        print("| ❌ Insufficient bank balance!                  |")
                        print("+------------------------------------------------+")
                        return

                    # Deduct from bank account
                    new_bank_balance = bank_balance - monthly_amount
                    self.db.update_bank_account_balance(selected_bank['account_id'], new_bank_balance)

                elif payment_choice == 3:  # Investment Account
                    invest_accounts = self.db.get_user_investment_accounts(self.logged_in_user_id)
                    if not invest_accounts:
                        print("+------------------------------------------------+")
                        print("| ❌ No investment accounts found!               |")
                        print("+------------------------------------------------+")
                        return

                    print("+------------------------------------------------+")
                    print("| Select Investment Account:                     |")
                    for i, acc in enumerate(invest_accounts, 1):
                        print(f"| {i}. {acc['investment_name']} ({acc['investment_type']}) |")
                    print("+------------------------------------------------+")

                    acc_idx = self.validation.get_valid_int(
                        "Enter choice: ",
                        lambda x: 1 <= x <= len(invest_accounts),
                        "❌ Invalid account selection!"
                    )
                    selected_investment = invest_accounts[acc_idx - 1]
                    investment_balance = self.db.get_investment_account_value(selected_investment['investment_id'])

                    if investment_balance < monthly_amount:
                        print("+------------------------------------------------+")
                        print("| ❌ Insufficient investment balance!            |")
                        print("+------------------------------------------------+")
                        return

                    # Deduct from investment account
                    new_investment_balance = investment_balance - monthly_amount
                    self.db.update_investment_account_value(selected_investment['investment_id'], new_investment_balance)

                elif payment_choice == 4:  # Cash
                    # For cash, we assume the payment is made and deduct from wallet
                    wallet_balance = self.db.get_user_balance(self.logged_in_user_id)
                    if wallet_balance < monthly_amount:
                        print("+------------------------------------------------+")
                        print("| ❌ Insufficient wallet balance for cash payment! |")
                        print("+------------------------------------------------+")
                        return

                    new_wallet_balance = wallet_balance - monthly_amount
                    self.db.update_user_balance(self.logged_in_user_id, new_wallet_balance)

                # Add monthly savings to goal
                result = self.db.update_goal_progress(selected_goal['goal_id'], monthly_amount)
                if result:
                    # Record the contribution
                    payment_modes = {1: "Wallet", 2: "Bank Account", 3: "Investment Account", 4: "Cash"}
                    mode_name = payment_modes.get(payment_choice, "Unknown")
                    self.db.add_goal_contribution(selected_goal['goal_id'], monthly_amount, "Monthly Savings", f"Paid via {mode_name}")

                    print("+------------------------------------------------+")
                    print("| ✅ Monthly savings added to goal!             |")
                    print(f"| Amount: ₹{monthly_amount:<28.2f}|")
                    print(f"| Payment Mode: {mode_name:<25}|")
                    print(f"| Date: {datetime.now().strftime('%Y-%m-%d %H:%M'):<20}|")
                    print("+------------------------------------------------+")

                    self.db.log_action(
                        f"User:{self.logged_in_user}",
                        f"Added monthly savings ₹{monthly_amount} to goal: {selected_goal['goal_name']} via {mode_name}"
                    )
                return

            elif update_choice == 2:  # Add Income from Account
                # -------- SELECT ACCOUNT --------
                accounts = {
                    1: "Wallet",
                    2: "Bank Account",
                    3: "Investment Account",
                    4: "Cash"
                }

                print("+------------------------------------------------+")
                print("| Select Account Source:                         |")
                for k, v in accounts.items():
                    print(f"| {k}. {v:<38}|")
                print("+------------------------------------------------+")

                acc_choice = self.validation.get_valid_int(
                    "Enter choice: ",
                    lambda x: x in accounts,
                    "❌ Invalid account selection!"
                )
                selected_account = accounts[acc_choice]

                # -------- SELECT SPECIFIC ACCOUNT IF BANK/INVESTMENT/OTHER --------
                account_id = None
                if acc_choice == 2:  # Bank Account
                    bank_accounts = self.db.get_user_bank_accounts(self.logged_in_user_id)
                    if not bank_accounts:
                        print("+------------------------------------------------+")
                        print("| ❌ No bank accounts found! Please add a bank account first. |")
                        print("+------------------------------------------------+")
                        return

                    print("+------------------------------------------------+")
                    print("| Select Bank Account:                           |")
                    for i, acc in enumerate(bank_accounts, 1):
                        print(f"| {i}. {acc['bank_name']} - {acc['last_four_digits']:<10} |")
                    print("+------------------------------------------------+")

                    acc_idx = self.validation.get_valid_int(
                        "Enter choice: ",
                        lambda x: 1 <= x <= len(bank_accounts),
                        "❌ Invalid account selection!"
                    )
                    account_id = bank_accounts[acc_idx - 1]['account_id']

                elif acc_choice == 3:  # Investment Account
                    invest_accounts = self.db.get_user_investment_accounts(self.logged_in_user_id)
                    if not invest_accounts:
                        print("+------------------------------------------------+")
                        print("| ❌ No investment accounts found! Please add an investment account first. |")
                        print("+------------------------------------------------+")
                        return

                    print("+------------------------------------------------+")
                    print("| Select Investment Account:                     |")
                    for i, acc in enumerate(invest_accounts, 1):
                        print(f"| {i}. {acc['investment_name']} ({acc['investment_type']}) |")
                    print("+------------------------------------------------+")

                    acc_idx = self.validation.get_valid_int(
                        "Enter choice: ",
                        lambda x: 1 <= x <= len(invest_accounts),
                        "❌ Invalid account selection!"
                    )
                    account_id = invest_accounts[acc_idx - 1]['investment_id']

                elif acc_choice == 4:  # Other (Manual Account)
                    manual_accounts = self.db.get_user_manual_accounts(self.logged_in_user_id)

                    print("+------------------------------------------------+")
                    print("| Select Manual Account:                         |")
                    print("| 1. Create New Manual Account                  |")

                    if manual_accounts:
                        for i, acc in enumerate(manual_accounts, 2):
                            print(f"| {i}. {acc['account_name']} (₹{acc['balance']:.2f}) |")
                    print("+------------------------------------------------+")

                    max_choice = len(manual_accounts) + 1 if manual_accounts else 1
                    acc_choice_manual = self.validation.get_valid_int(
                        "Enter choice: ",
                        lambda x: 1 <= x <= max_choice,
                        "❌ Invalid account selection!"
                    )

                    if acc_choice_manual == 1:
                        # Create new manual account
                        account_name = self.validation.get_valid_input(
                            "Enter Account Name: ",
                            lambda x: len(x.strip()) > 0,
                            "❌ Account name cannot be empty!"
                        ).strip()

                        opening_balance = 0.00  # Start with zero for new accounts

                        notes = self.validation.get_valid_input(
                            "Enter Notes (optional, press enter to skip): ",
                            lambda x: True,
                            ""
                        ).strip()

                        result = self.db.add_manual_account(
                            self.logged_in_user_id,
                            account_name,
                            opening_balance,
                            notes
                        )

                        if result:
                            account_id = result
                            print("+------------------------------------------------+")
                            print("| ✅ Manual Account Created Successfully!       |")
                            print("+------------------------------------------------+")
                        else:
                            print("+------------------------------------------------+")
                            print("| ❌ Failed to create manual account!           |")
                            print("+------------------------------------------------+")
                            return
                    else:
                        # Select existing account (choice 2, 3, etc. map to index 0, 1, etc.)
                        account_id = manual_accounts[acc_choice_manual - 2]['manual_account_id']

                # -------- AMOUNT --------
                amount_to_add = self.validation.get_valid_float(
                    "Enter amount to add to goal (₹): ",
                    lambda x: x > 0,
                    "❌ Amount must be positive!"
                )

                # -------- SOURCE --------
                source = self.validation.get_valid_input(
                    "Enter Source: ",
                    lambda x: len(x.strip()) > 0,
                    "❌ Source cannot be empty!"
                )

                # Use default category for goal contributions
                selected_category = "Business Income"

                # -------- CONFIRM --------
                print("+------------------------------------------------+")
                if acc_choice == 4:  # Manual Account
                    manual_accounts = self.db.get_user_manual_accounts(self.logged_in_user_id)
                    selected_manual = next((acc for acc in manual_accounts if acc['manual_account_id'] == account_id), None)
                    if selected_manual:
                        print(f"| Account  : {selected_manual['account_name']:<30}|")
                    else:
                        print(f"| Account  : Manual Account (ID: {account_id})")
                else:
                    print(f"| Account  : {selected_account:<30}|")
                print(f"| Category : {selected_category:<30}|")
                print(f"| Amount   : ₹{amount_to_add:<28.2f}|")
                print(f"| Note     : {source:<30}|")
                print("+------------------------------------------------+")

                if input("Confirm add this income to goal? (y/n): ").lower() != 'y':
                    print("+------------------------------------------------+")
                    print("| ❌ Update cancelled.                           |")
                    print("+------------------------------------------------+")
                    return

                # -------- DELEGATE TO WALLET --------
                account_type = selected_account.lower().replace(" ", "_")
                if acc_choice == 4:  # Manual Account
                    account_type = "manual_account"

                success, new_balance, message = self.wallet.process_income(
                    self.logged_in_user_id,
                    account_type,
                    account_id,
                    amount_to_add,
                    selected_category,
                    source,
                    self.logged_in_user
                )

                if success:
                    # Update goal progress
                    result = self.db.update_goal_progress(selected_goal['goal_id'], amount_to_add)

                    if result:
                        # Record the contribution
                        self.db.add_goal_contribution(selected_goal['goal_id'], amount_to_add, selected_category, source)

                        print("+------------------------------------------------+")
                        print("| ✅ Income added to goal successfully!         |")
                        print(f"| Amount: ₹{amount_to_add:<28.2f}|")
                        print(f"| Category: {selected_category:<26}|")
                        print(f"| Source: {source:<28}|")
                        print(f"| Date: {datetime.now().strftime('%Y-%m-%d %H:%M'):<20}|")
                        print("+------------------------------------------------+")

                        self.db.log_action(
                            f"User:{self.logged_in_user}",
                            f"Added {selected_category} ₹{amount_to_add} to goal: {selected_goal['goal_name']}"
                        )
                    else:
                        print("+------------------------------------------------+")
                        print("| ❌ Failed to update goal progress!            |")
                        print("+------------------------------------------------+")
                else:
                    print("+------------------------------------------------+")
                    print(f"| ❌ {message:<45}|")
                    print("+------------------------------------------------+")

            elif update_choice == 3:  # Change Goal Target Amount
                self.change_goal_target_amount()
                return

            elif update_choice == 4:  # Change Monthly Savings Amount
                print("+------------------------------------------------+")
                print(f"| Goal: {selected_goal['goal_name']:<35}|")
                print(f"| Current Monthly Savings: ₹{selected_goal['monthly_savings']:<20.2f}|")
                print("+------------------------------------------------+")

                new_monthly_savings = self.validation.get_valid_float(
                    "Enter new monthly savings amount (₹): ",
                    lambda x: x > 0,
                    "❌ Monthly savings must be positive!"
                )

                # Confirm change
                print("+------------------------------------------------+")
                print(f"| New Monthly Savings: ₹{new_monthly_savings:<20.2f}|")
                print("+------------------------------------------------+")

                if input("Confirm change monthly savings? (y/n): ").lower() != 'y':
                    print("+------------------------------------------------+")
                    print("| ❌ Operation cancelled.                        |")
                    print("+------------------------------------------------+")
                    return

                # Update the monthly savings
                result = self.db.update_goal_monthly_savings(selected_goal['goal_id'], new_monthly_savings)

                if result:
                    print("+------------------------------------------------+")
                    print("| ✅ Monthly savings updated successfully!       |")
                    print(f"| New Monthly Savings: ₹{new_monthly_savings:<20.2f}|")
                    print("+------------------------------------------------+")

                    self.db.log_action(
                        f"User:{self.logged_in_user}",
                        f"Changed monthly savings for goal '{selected_goal['goal_name']}' from ₹{selected_goal['monthly_savings']} to ₹{new_monthly_savings}"
                    )
                else:
                    print("+------------------------------------------------+")
                    print("| ❌ Failed to update monthly savings!           |")
                    print("+------------------------------------------------+")
                return

            elif update_choice == 5:  # Adjust Target for Price Change
                print("+------------------------------------------------+")
                print(f"| Goal: {selected_goal['goal_name']:<35}|")
                print(f"| Current Target: ₹{selected_goal['target_amount']:<20.2f}|")
                print("+------------------------------------------------+")

                new_target_amount = self.validation.get_valid_float(
                    "Enter new target amount due to price change (₹): ",
                    lambda x: x > 0,
                    "❌ Target amount must be positive!"
                )

                # Confirm change
                print("+------------------------------------------------+")
                print(f"| New Target Amount: ₹{new_target_amount:<20.2f}|")
                print("+------------------------------------------------+")

                if input("Confirm adjust target for price change? (y/n): ").lower() != 'y':
                    print("+------------------------------------------------+")
                    print("| ❌ Operation cancelled.                        |")
                    print("+------------------------------------------------+")
                    return

                # Update the target amount
                result = self.db.update_goal_target_amount(selected_goal['goal_id'], new_target_amount)

                if result:
                    print("+------------------------------------------------+")
                    print("| ✅ Goal target adjusted for price change!      |")
                    print(f"| New Target: ₹{new_target_amount:<26.2f}|")
                    print("+------------------------------------------------+")

                    self.db.log_action(
                        f"User:{self.logged_in_user}",
                        f"Adjusted target amount for goal '{selected_goal['goal_name']}' from ₹{selected_goal['target_amount']} to ₹{new_target_amount} due to price change"
                    )
                else:
                    print("+------------------------------------------------+")
                    print("| ❌ Failed to adjust goal target!               |")
                    print("+------------------------------------------------+")
                return

            elif update_choice == 6:  # Change Goal Target Amount
                self.change_goal_target_amount()
                return

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error updating goal progress: {str(e)[:20]:<20}|")
            print("+------------------------------------------------+")

    def stop_financial_goal(self):
        """Stop or reactivate a financial goal"""
        try:
            goals = self.db.get_user_financial_goals(self.logged_in_user_id)

            if not goals:
                print("+------------------------------------------------+")
                print("| ❌ No goals found!                             |")
                print("+------------------------------------------------+")
                return

            print("+------------------------------------------------+")
            print("| Select Goal to Manage:                         |")
            for i, goal in enumerate(goals, 1):
                status_indicator = "🟢" if goal['status'] == 'ACTIVE' else "🔴"
                print(f"| {i}. {status_indicator} {goal['goal_name']:<32}|")
            print("+------------------------------------------------+")

            goal_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: 1 <= x <= len(goals),
                "❌ Invalid goal selection!"
            )

            selected_goal = goals[goal_choice - 1]

            # Check if goal is already stopped
            if selected_goal['status'] == 'STOPPED':
                # Offer to reactivate
                if input(f"Goal '{selected_goal['goal_name']}' is stopped. Reactivate it? (y/n): ").lower() != 'y':
                    print("+------------------------------------------------+")
                    print("| ❌ Operation cancelled.                        |")
                    print("+------------------------------------------------+")
                    return

                # Reactivate goal
                result = self.db.reactivate_financial_goal(selected_goal['goal_id'])

                if result:
                    print("+------------------------------------------------+")
                    print("| ✅ Goal Reactivated Successfully!             |")
                    print("+------------------------------------------------+")

                    self.db.log_action(
                        f"User:{self.logged_in_user}",
                        f"Reactivated goal: {selected_goal['goal_name']}"
                    )
                else:
                    print("+------------------------------------------------+")
                    print("| ❌ Failed to reactivate goal!                  |")
                    print("+------------------------------------------------+")
            else:
                # Stop active goal
                if input(f"Confirm stop goal '{selected_goal['goal_name']}'? (y/n): ").lower() != 'y':
                    print("+------------------------------------------------+")
                    print("| ❌ Operation cancelled.                        |")
                    print("+------------------------------------------------+")
                    return

                # Stop goal
                result = self.db.stop_financial_goal(selected_goal['goal_id'])

                if result:
                    print("+------------------------------------------------+")
                    print("| ✅ Goal Stopped Successfully!                 |")
                    print("+------------------------------------------------+")

                    self.db.log_action(
                        f"User:{self.logged_in_user}",
                        f"Stopped goal: {selected_goal['goal_name']}"
                    )
                else:
                    print("+------------------------------------------------+")
                    print("| ❌ Failed to stop goal!                        |")
                    print("+------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error managing goal: {str(e)[:25]:<25}|")
            print("+------------------------------------------------+")

    def change_goal_target_amount(self):
        """Change the target amount of a financial goal"""
        try:
            goals = self.db.get_user_financial_goals(self.logged_in_user_id)

            if not goals:
                print("+------------------------------------------------+")
                print("| ❌ No goals found!                             |")
                print("+------------------------------------------------+")
                return

            print("+------------------------------------------------+")
            print("| Select Goal to Change Target Amount:           |")
            for i, goal in enumerate(goals, 1):
                print(f"| {i}. {goal['goal_name']:<35}|")
                print(f"|    Current Target: ₹{goal['target_amount']:<20.2f}|")
            print("+------------------------------------------------+")

            goal_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: 1 <= x <= len(goals),
                "❌ Invalid goal selection!"
            )

            selected_goal = goals[goal_choice - 1]

            print("+------------------------------------------------+")
            print(f"| Goal: {selected_goal['goal_name']:<35}|")
            print(f"| Current Target: ₹{selected_goal['target_amount']:<20.2f}|")
            print("+------------------------------------------------+")

            new_target_amount = self.validation.get_valid_float(
                "Enter new target amount (₹): ",
                lambda x: x > 0,
                "❌ Target amount must be positive!"
            )

            # Confirm change
            print("+------------------------------------------------+")
            print(f"| New Target Amount: ₹{new_target_amount:<20.2f}|")
            print("+------------------------------------------------+")

            if input("Confirm change target amount? (y/n): ").lower() != 'y':
                print("+------------------------------------------------+")
                print("| ❌ Operation cancelled.                        |")
                print("+------------------------------------------------+")
                return

            # Update the target amount
            result = self.db.update_goal_target_amount(selected_goal['goal_id'], new_target_amount)

            if result:
                print("+------------------------------------------------+")
                print("| ✅ Goal target amount updated successfully!    |")
                print(f"| New Target: ₹{new_target_amount:<26.2f}|")
                print("+------------------------------------------------+")

                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Changed target amount for goal '{selected_goal['goal_name']}' from ₹{selected_goal['target_amount']} to ₹{new_target_amount}"
                )
            else:
                print("+------------------------------------------------+")
                print("| ❌ Failed to update goal target amount!        |")
                print("+------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error changing goal target: {str(e)[:20]:<20}|")
            print("+------------------------------------------------+")

    def adjust_goal_for_price_change(self):
        """Adjust goal target amount due to price changes (increase or decrease)"""
        try:
            goals = self.db.get_user_financial_goals(self.logged_in_user_id)

            if not goals:
                print("+------------------------------------------------+")
                print("| ❌ No goals found!                             |")
                print("+------------------------------------------------+")
                return

            print("+------------------------------------------------+")
            print("| Select Goal to Adjust for Price Change:        |")
            for i, goal in enumerate(goals, 1):
                print(f"| {i}. {goal['goal_name']:<35}|")
                print(f"|    Current Target: ₹{goal['target_amount']:<20.2f}|")
            print("+------------------------------------------------+")

            goal_choice = self.validation.get_valid_int(
                "Enter choice: ",
                lambda x: 1 <= x <= len(goals),
                "❌ Invalid goal selection!"
            )

            selected_goal = goals[goal_choice - 1]

            print("+------------------------------------------------+")
            print(f"| Goal: {selected_goal['goal_name']:<35}|")
            print(f"| Current Target: ₹{selected_goal['target_amount']:<20.2f}|")
            print("+------------------------------------------------+")

            new_target_amount = self.validation.get_valid_float(
                "Enter new target amount due to price change (₹): ",
                lambda x: x > 0,
                "❌ Target amount must be positive!"
            )

            # Confirm change
            print("+------------------------------------------------+")
            print(f"| New Target Amount: ₹{new_target_amount:<20.2f}|")
            print("+------------------------------------------------+")

            if input("Confirm adjust target for price change? (y/n): ").lower() != 'y':
                print("+------------------------------------------------+")
                print("| ❌ Operation cancelled.                        |")
                print("+------------------------------------------------+")
                return

            # Update the target amount
            result = self.db.update_goal_target_amount(selected_goal['goal_id'], new_target_amount)

            if result:
                print("+------------------------------------------------+")
                print("| ✅ Goal target adjusted for price change!      |")
                print(f"| New Target: ₹{new_target_amount:<26.2f}|")
                print("+------------------------------------------------+")

                self.db.log_action(
                    f"User:{self.logged_in_user}",
                    f"Adjusted target amount for goal '{selected_goal['goal_name']}' from ₹{selected_goal['target_amount']} to ₹{new_target_amount} due to price change"
                )
            else:
                print("+------------------------------------------------+")
                print("| ❌ Failed to adjust goal target!               |")
                print("+------------------------------------------------+")

        except Exception as e:
            print("+------------------------------------------------+")
            print(f"| ❌ Error adjusting goal target: {str(e)[:20]:<20}|")
            print("+------------------------------------------------+")
