#!/usr/bin/env python3
"""
Test script to verify the decimal/float fix in wallet.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import Database
from wallet import Wallet
from stack_queue_utils import StackQueueManager

def test_expense_processing():
    """Test expense processing with decimal values"""
    print("Testing expense processing fix...")

    try:
        # Initialize components
        db = Database()
        stack_queue = StackQueueManager()
        wallet = Wallet(db, stack_queue)

        # Create a test user if not exists
        test_user = "testuser"
        test_email = "test@example.com"
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

        account_id = bank_accounts[0]["account_id"]

        # Test expense processing
        print(f"Testing expense from bank account (ID: {account_id})...")

        # Test 1: Normal expense
        success, new_balance, message = wallet.process_expense(
            user_id=user_id,
            account_type="bank_account",
            account_id=account_id,
            amount=5000.00,
            category="Shopping",
            payment_mode="UPI",
            description="Test shopping expense",
            username=test_user
        )

        if success:
            print("✅ Test 1 PASSED: Expense processed successfully")
            print(f"   New balance: ₹{new_balance:.2f}")
            print(f"   Message: {message}")
        else:
            print("❌ Test 1 FAILED: Expense processing failed")
            print(f"   Message: {message}")
            return False

        # Test 2: Investment account expense (if exists)
        investment_accounts = db.get_user_investment_accounts(user_id)
        if investment_accounts:
            inv_account_id = investment_accounts[0]["investment_id"]
            print(f"Testing expense from investment account (ID: {inv_account_id})...")

            success, new_value, message = wallet.process_expense(
                user_id=user_id,
                account_type="investment_account",
                account_id=inv_account_id,
                amount=1000.00,
                category="Investments",
                payment_mode="N/A",
                description="Test investment withdrawal",
                username=test_user
            )

            if success:
                print("✅ Test 2 PASSED: Investment expense processed successfully")
                print(f"   New value: ₹{new_value:.2f}")
                print(f"   Message: {message}")
            else:
                print("❌ Test 2 FAILED: Investment expense processing failed")
                print(f"   Message: {message}")
                return False
        else:
            print("ℹ️  Test 2 SKIPPED: No investment accounts found")

        # Test 3: Insufficient balance check
        print("Testing insufficient balance check...")
        success, balance, message = wallet.process_expense(
            user_id=user_id,
            account_type="bank_account",
            account_id=account_id,
            amount=100000.00,  # Large amount
            category="Shopping",
            payment_mode="UPI",
            description="Test large expense",
            username=test_user
        )

        if not success and "Insufficient" in message:
            print("✅ Test 3 PASSED: Insufficient balance correctly detected")
            print(f"   Message: {message}")
        else:
            print("❌ Test 3 FAILED: Insufficient balance not detected properly")
            print(f"   Success: {success}, Message: {message}")
            return False

        print("\n🎉 All tests passed! The decimal/float fix is working correctly.")
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

if __name__ == "__main__":
    success = test_expense_processing()
    sys.exit(0 if success else 1)
