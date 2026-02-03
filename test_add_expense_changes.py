#!/usr/bin/env python3
"""
Test script to verify the changes in add_expense method for Bank Account and Manual Account options
"""

import sys
import os
import io
from contextlib import redirect_stdin
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import Database
from user import UserManager
from validations import Validation

def test_add_expense_bank_account():
    """Test add_expense with Bank Account selection"""
    print("Testing add_expense with Bank Account selection...")

    try:
        # Initialize components
        db = Database()
        user_manager = UserManager(db)

        # Create a test user if not exists
        test_user = "testuser_expense"
        test_email = "testexpense@example.com"
        test_password = "test123"

        # Check if test user exists
        existing_user = db.get_user_by_username(test_user)
        if not existing_user:
            # Create test user
            import hashlib
            hashed_password = hashlib.sha256(test_password.encode()).hexdigest()
            from datetime import datetime
            query = """
                INSERT INTO users
                (username, password, email, mobile, wallet_balance, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            db.execute_insert(query, (test_user, hashed_password, test_email, "9999999999", 10000.00, "ACTIVE", datetime.now()))
            user_id = db.get_user_by_username(test_user)["user_id"]
        else:
            user_id = existing_user["user_id"]

        # Set logged in user
        user_manager.logged_in_user = test_user
        user_manager.logged_in_user_id = user_id

        # Create a test bank account if not exists
        bank_accounts = db.get_user_bank_accounts(user_id)
        if not bank_accounts:
            # Add a test bank account
            db.add_bank_account(
                user_id=user_id,
                bank_name="Test Bank",
                account_holder="Test User",
                ifsc_code="TEST0001234",
                last_four_digits="1234",
                balance=50000.00,
                nickname="Test Account",
                upi_id="test@paytm",
                debit_card_last_four="5678",
                credit_card_last_four="9012",
                credit_card_limit=100000.00
            )
            bank_accounts = db.get_user_bank_accounts(user_id)

        # Simulate user inputs for Bank Account selection
        # 1. Select Bank Account (choice 1)
        # 2. Select first bank account (choice 1)
        # 3. Enter amount (500.00)
        # 4. Select category (1 for Food & Drinks)
        # 5. Enter description (Test expense)
        # 6. Select payment mode (1 for UPI)
        # 7. Confirm (y)
        inputs = "1\n1\n500.00\n1\nTest expense\n1\ny\n"

        # Capture output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            with redirect_stdin(io.StringIO(inputs)):
                user_manager.add_expense()
        finally:
            sys.stdout = old_stdout

        output = captured_output.getvalue()
        print("Captured output:")
        print(output)

        # Check if the method displayed Bank Account options
        if "Select Account for Transaction:" in output and "1. Bank Account" in output and "2. Manual Account" in output:
            print("✅ Account selection displayed correctly")
        else:
            print("❌ Account selection not displayed correctly")
            return False

        # Check if payment modes were prompted for Bank Account
        if "Select Payment Mode:" in output and "1. UPI" in output and "2. Debit Card" in output and "3. Credit Card" in output:
            print("✅ Payment modes prompted correctly for Bank Account")
        else:
            print("❌ Payment modes not prompted correctly for Bank Account")
            return False

        # Check if expense was added successfully
        if "Expense Added Successfully!" in output:
            print("✅ Expense added successfully for Bank Account")
        else:
            print("❌ Expense not added successfully for Bank Account")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        if 'db' in locals():
            db.close()

def test_add_expense_manual_account():
    """Test add_expense with Manual Account selection"""
    print("\nTesting add_expense with Manual Account selection...")

    try:
        # Initialize components
        db = Database()
        user_manager = UserManager(db)

        # Create a test user if not exists
        test_user = "testuser_expense"
        test_email = "testexpense@example.com"

        user_id = db.get_user_by_username(test_user)["user_id"]

        # Set logged in user
        user_manager.logged_in_user = test_user
        user_manager.logged_in_user_id = user_id

        # Create a test manual account if not exists
        manual_accounts = db.get_user_manual_accounts(user_id)
        if not manual_accounts:
            # Add a test manual account
            db.add_manual_account(
                user_id=user_id,
                account_name="Test Manual Account",
                opening_balance=10000.00,
                notes="Test account"
            )
            manual_accounts = db.get_user_manual_accounts(user_id)

        # Simulate user inputs for Manual Account selection
        # 1. Select Manual Account (choice 2)
        # 2. Select first manual account (choice 1)
        # 3. Enter amount (200.00)
        # 4. Select category (2 for Shopping)
        # 5. Enter description (Test manual expense)
        # 6. Confirm (y)
        inputs = "2\n1\n200.00\n2\nTest manual expense\ny\n"

        # Capture output
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()

        try:
            with redirect_stdin(io.StringIO(inputs)):
                user_manager.add_expense()
        finally:
            sys.stdout = old_stdout

        output = captured_output.getvalue()
        print("Captured output:")
        print(output)

        # Check if the method displayed Manual Account options
        if "Select Account for Transaction:" in output and "1. Bank Account" in output and "2. Manual Account" in output:
            print("✅ Account selection displayed correctly")
        else:
            print("❌ Account selection not displayed correctly")
            return False

        # Check if payment modes were NOT prompted for Manual Account (should be Cash)
        if "Select Payment Mode:" not in output and "Pay Mode  : Cash" in output:
            print("✅ Payment mode correctly set to Cash for Manual Account")
        else:
            print("❌ Payment mode not set correctly for Manual Account")
            return False

        # Check if expense was added successfully
        if "Expense Added Successfully!" in output:
            print("✅ Expense added successfully for Manual Account")
        else:
            print("❌ Expense not added successfully for Manual Account")
            return False

        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        if 'db' in locals():
            db.close()

def main():
    """Run all tests"""
    print("Running tests for add_expense method changes...\n")

    test1_passed = test_add_expense_bank_account()
    test2_passed = test_add_expense_manual_account()

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The changes to add_expense method are working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
