"""
Smart Wallet & Finance Management System
Python + DSA + DBMS | Console Backend
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import Database
from user import UserManager
from admin import AdminManager
from validations import Validation
from stack_queue_utils import StackQueueManager

class SmartWallet:
    def __init__(self):
        self.db = Database()
        self.user_manager = UserManager(self.db)
        self.admin_manager = AdminManager(self.db)
        self.validation = Validation()
        self.stack_queue = StackQueueManager()

        # Session variables
        self.logged_in_user = None
        self.logged_in_admin = None
        self.user_login_status = False
        self.admin_login_status = False

    def display_welcome_menu(self):
        """Display the main welcome menu"""
        print("+------------------------------------------------+")
        print("|           SMART WALLET & FINANCE               |")
        print("|           MANAGEMENT SYSTEM                    |")
        print("|------------------------------------------------|")
        print("|           💰 Manage Your Money 💰              |")
        print("+------------------------------------------------+")
        print("| Case 1 : Admin Login                           |")
        print("| Case 2 : User Login                            |")
        print("| Case 3 : User Sign Up                          |")
        print("| Case 4 : Exit                                  |")
        print("+%------------------------------------------------+%")
        print("👉 Please select an option: ", end="")

    def main_menu_loop(self):
        """Main menu loop (Clean + Safe + Wallet Level)"""

        def print_invalid_choice():
            print("+%-----------------------------+%")
            print("|       INVALID CHOICE        |")
            print("+%-----------------------------+%")

        def print_exit_message():
            print("+----------------------------------------------------+")
            print("| Exiting..                                          |")
            print("| Thanks For Using Smart Wallet & Finance System..   |")
            print("+----------------------------------------------------+")

        while True:
            try:
                self.display_welcome_menu()
                print("👉 Enter your choice: ", end="")
                choice = input().strip()

                # ---------- VALIDATE INPUT ----------
                if not choice.isdigit():
                    print_invalid_choice()
                    continue

                choice = int(choice)

                # ---------- ADMIN LOGIN ----------
                if choice == 1:
                    self.admin_login_status = False
                    self.admin_login_status = self.admin_manager.admin_login()

                    if self.admin_login_status:
                        self.admin_manager.admin_menu_loop()

                # ---------- USER LOGIN ----------
                elif choice == 2:
                    self.user_login_status = False
                    self.user_login_status = self.user_manager.user_login()

                    if self.user_login_status:
                        self.user_manager.user_wallet_menu_loop()

                # ---------- USER SIGN UP ----------
                elif choice == 3:
                    self.user_manager.user_signup()

                # ---------- EXIT ----------
                elif choice == 4:
                    print_exit_message()
                    break

                # ---------- INVALID ----------
                else:
                    print_invalid_choice()

            except KeyboardInterrupt:
                print()
                print_exit_message()
                break

            except Exception as e:
                print("+-----------------------------------------------+")
                print(f"| ❌ Unexpected Error: {str(e)[:43]:<43} |")
                print("+-----------------------------------------------+")


def main():
    """Main entry point"""
    try:
        wallet = SmartWallet()
        wallet.main_menu_loop()
    except Exception as e:
        print("+-----------------------------------+")
        print(f"| ❌ Critical Error: {str(e)}")
        print("+-----------------------------------+")
        sys.exit(1)

if __name__ == "__main__":
    main()
