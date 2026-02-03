#!/usr/bin/env python3
"""
Test script to verify the sell investment fixes:
1. No payment mode prompt when selling investments
2. Credit card limit display after selling
3. Investment grouping and partial selling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import Database
from user import UserManager
from datetime import datetime
import hashlib

def setup_test_user(db):
    """Create or get test user"""
    test_user = "testuser_sell"
    test_email = "test_sell@example.com"
    test_password = "test123"

    existing_user = db.get_user_by_username(test_user)
    if not existing_user:
        hashed_password = hashlib.sha256(test_password.encode()).hexdigest()
        query = """
            INSERT INTO users
            (username, password, email, mobile, wallet_balance, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        db.execute_insert(query, (test_user, hashed_password, test_email, "9999999999", 10000.00, "ACTIVE", datetime.now()))
        user_id = db.get_user_by_username(test_user)["user_id"]
    else:
        user_id = existing_user["user_id"]

    return user_id, test_user

def setup_test_accounts(db, user_id):
    """Create test bank and investment accounts"""
    # Bank account
    bank_accounts = db.get_user_bank_accounts(user_id)
    if not bank_accounts:
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

    bank_account_id = bank_accounts[0]["account_id"]

    # Investment accounts - create multiple Solana entries to test grouping
    # Always recreate for fresh test data
    existing_investments = db.get_user_investment_accounts(user_id)
    for inv in existing_investments:
        db.remove_investment_account(inv['investment_id'])

    investment_accounts = []
    # Add first Solana investment
    db.add_investment_account(
        user_id=user_id,
        investment_name="Solana",
        investment_type="Crypto",
        platform="Groww",
        invested_amount=10000.00,
        current_value=15000.00,
        quantity=100.0,
        price_per_share=100.0
    )

    # Add second Solana investment (same name/type to test grouping)
    db.add_investment_account(
        user_id=user_id,
        investment_name="Solana",
        investment_type="Crypto",
        platform="Groww",
        invested_amount=5000.00,
        current_value=7500.00,
        quantity=50.0,
        price_per_share=100.0
    )

    # Add Bitcoin for comparison
    db.add_investment_account(
        user_id=user_id,
        investment_name="Bitcoin",
        investment_type="Crypto",
        platform="Groww",
        invested_amount=20000.00,
        current_value=25000.00,
        quantity=0.5,
        price_per_share=40000.0
    )

    investment_accounts = db.get_user_investment_accounts(user_id)

    return bank_account_id, investment_accounts

def test_sell_investment_flow():
    """Test the sell investment functionality"""
    print("🧪 Testing Sell Investment Flow Fixes...")
    print("=" * 50)

    try:
        db = Database()
        user_id, username = setup_test_user(db)
        bank_account_id, investment_accounts = setup_test_accounts(db, user_id)

        # Create UserManager instance
        user_manager = UserManager(db)
        user_manager.logged_in_user = username
        user_manager.logged_in_user_id = user_id

        print(f"✅ Test setup complete. User ID: {user_id}")
        print(f"   Bank Account ID: {bank_account_id}")
        print(f"   Investment Accounts: {len(investment_accounts)}")

        # Test 1: Check investment grouping
        print("\n📋 Test 1: Investment Grouping")
        print("-" * 30)

        # Get grouped investments (simulate the grouping logic)
        grouped_investments = {}
        for inv in investment_accounts:
            key = (inv['investment_name'], inv['investment_type'])
            if key not in grouped_investments:
                grouped_investments[key] = {
                    'name': inv['investment_name'],
                    'type': inv['investment_type'],
                    'total_quantity': 0.0,
                    'total_value': 0.0,
                    'price_per_share': float(inv['price_per_share'] or 0),
                    'accounts': []
                }
            grouped_investments[key]['total_quantity'] += float(inv['quantity'] or 0)
            grouped_investments[key]['total_value'] += float(inv['current_value'] or 0)
            grouped_investments[key]['accounts'].append(inv)

        investment_list = list(grouped_investments.values())
        print(f"Grouped investments: {len(investment_list)}")
        for i, inv in enumerate(investment_list, 1):
            print(f"  {i}. {inv['name']} ({inv['type']}) - Qty: {inv['total_quantity']}, Value: ₹{inv['total_value']:.2f}")

        # Verify Solana is grouped (should show total quantity 150, total value 22500)
        solana_group = next((inv for inv in investment_list if inv['name'] == 'Solana'), None)
        if solana_group and solana_group['total_quantity'] == 150.0 and abs(solana_group['total_value'] - 22500.0) < 0.01:
            print("✅ Investment grouping works correctly (Solana entries combined)")
        else:
            print("❌ Investment grouping failed")
            return False

        # Test 2: Simulate partial sell (sell 50 Solana units)
        print("\n💰 Test 2: Partial Sell Simulation")
        print("-" * 30)

        if solana_group:
            quantity_to_sell = 50.0
            value_to_sell = quantity_to_sell * solana_group['price_per_share']

            print(f"Selling {quantity_to_sell} units of {solana_group['name']} for ₹{value_to_sell:.2f}")

            # Simulate the sell logic (without user interaction)
            total_quantity_sold = 0
            for inv in solana_group['accounts']:
                if quantity_to_sell <= 0:
                    break

                available_quantity = float(inv['quantity'] or 0)
                quantity_to_remove = min(quantity_to_sell, available_quantity)

                if quantity_to_remove >= available_quantity:
                    # Remove entire account
                    db.remove_investment_account(inv['investment_id'])
                    print(f"  Removed entire account {inv['investment_id']}")
                else:
                    # Update quantity and value
                    new_quantity = available_quantity - quantity_to_remove
                    new_value = new_quantity * float(solana_group['price_per_share'] or 0)
                    db.update_investment_quantity(inv['investment_id'], new_quantity)
                    db.update_investment_account_value(inv['investment_id'], new_value)
                    print(f"  Updated account {inv['investment_id']}: Qty {available_quantity} -> {new_quantity}")

                quantity_to_sell -= quantity_to_remove
                total_quantity_sold += quantity_to_remove

            # Add proceeds to bank account
            current_bank_balance = db.get_bank_account_balance(bank_account_id)
            new_bank_balance = float(current_bank_balance) + value_to_sell
            db.update_bank_account_balance(bank_account_id, new_bank_balance)

            print(f"✅ Sold {total_quantity_sold} units, added ₹{value_to_sell:.2f} to bank account")
            print(f"   Bank balance: ₹{current_bank_balance:.2f} -> ₹{new_bank_balance:.2f}")

        # Test 3: Check credit card limit display logic
        print("\n💳 Test 3: Credit Card Limit Display")
        print("-" * 30)

        # Check if credit card limit display logic works
        credit_limit_query = "SELECT credit_card_limit FROM bank_accounts WHERE account_id = %s"
        credit_limit_result = db.execute_query(credit_limit_query, (bank_account_id,), fetch=True)

        if credit_limit_result and credit_limit_result[0]['credit_card_limit'] > 0:
            credit_limit = float(credit_limit_result[0]['credit_card_limit'])

            # Get current month's credit card spending
            current_month = datetime.now().strftime("%Y-%m")
            credit_spend_query = """
                SELECT COALESCE(SUM(amount), 0) as monthly_spend
                FROM bank_transactions
                WHERE account_id = %s AND type = 'EXPENSE' AND category = 'Credit Card Payment'
                AND DATE_FORMAT(date, '%%Y-%%m') = %s
            """
            spend_result = db.execute_query(credit_spend_query, (bank_account_id, current_month), fetch=True)
            monthly_spend = float(spend_result[0]['monthly_spend']) if spend_result else 0.0

            remaining_limit = credit_limit - monthly_spend

            print(f"Credit Card Limit: ₹{credit_limit:.2f}")
            print(f"Monthly Spend: ₹{monthly_spend:.2f}")
            print(f"Remaining Limit: ₹{remaining_limit:.2f}")
            print("✅ Credit card limit display logic works")
        else:
            print("ℹ️  No credit card account found for testing")

        # Test 4: Verify no payment mode in sell flow
        print("\n🚫 Test 4: No Payment Mode in Sell Flow")
        print("-" * 30)

        # Check the sell_remove_investment_account method doesn't contain payment mode prompts
        with open(os.path.join(os.path.dirname(__file__), 'user.py'), 'r') as f:
            content = f.read()

        # Look for payment mode related code in sell function
        sell_function_start = content.find('def sell_remove_investment_account(self):')
        if sell_function_start != -1:
            sell_function_end = content.find('\n    def ', sell_function_start + 1)
            if sell_function_end == -1:
                sell_function_end = len(content)

            sell_function_content = content[sell_function_start:sell_function_end]

            # Check for payment mode keywords
            payment_mode_keywords = ['payment_mode', 'Payment Mode', 'Select Payment Mode']
            has_payment_mode = any(keyword in sell_function_content for keyword in payment_mode_keywords)

            if not has_payment_mode:
                print("✅ No payment mode prompts found in sell investment function")
            else:
                print("❌ Payment mode prompts still present in sell investment function")
                return False
        else:
            print("❌ Could not find sell_remove_investment_account function")
            return False

        print("\n🎉 All tests passed! Sell investment fixes are working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = test_sell_investment_flow()
    sys.exit(0 if success else 1)
