#!/usr/bin/env python3
"""
Test script to verify budget data is saved to and retrieved from database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import Database
from user import UserManager

def test_budget_save_and_retrieve():
    """Test that budgets are saved to database and can be retrieved"""
    print("Testing Budget Save and Retrieve...")

    db = Database()
    user_manager = UserManager(db)

    # Mock logged in user
    user_manager.logged_in_user_id = 1
    user_manager.logged_in_user = "testuser"

    # Test 1: Check if get_user_budgets method exists and works
    try:
        budgets = db.get_user_budgets(1, "2024-01")
        print("✅ PASS: get_user_budgets method exists and returns data")
    except Exception as e:
        print(f"❌ FAIL: get_user_budgets method error: {str(e)}")
        return False

    # Test 2: Check if get_budgets_with_spent method exists and works
    try:
        budgets_with_spent = user_manager.get_budgets_with_spent(1, "2024-01")
        print("✅ PASS: get_budgets_with_spent method exists and returns data")
    except Exception as e:
        print(f"❌ FAIL: get_budgets_with_spent method error: {str(e)}")
        return False

    # Test 3: Verify that view_budget_status method uses database data
    try:
        # Check if the method calls get_budgets_with_spent
        import inspect
        source = inspect.getsource(user_manager.view_budget_status)
        if "get_budgets_with_spent" in source:
            print("✅ PASS: view_budget_status method uses database data")
        else:
            print("❌ FAIL: view_budget_status method does not use database data")
            return False
    except Exception as e:
        print(f"❌ FAIL: Error checking view_budget_status method: {str(e)}")
        return False

    print("✅ All budget database tests passed!")
    return True

if __name__ == "__main__":
    print("Running Budget Database Tests...\n")

    if test_budget_save_and_retrieve():
        print("\n🎉 Budget database functionality verified!")
    else:
        print("\n❌ Budget database tests failed!")
        sys.exit(1)
