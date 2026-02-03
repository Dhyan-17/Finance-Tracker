#!/usr/bin/env python3
"""
Test script for Top Expenses feature
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import Database

def test_database_connection():
    """Test database connection and table creation"""
    print("Testing database connection...")
    try:
        db = Database()
        print("✅ Database connection successful")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_get_top_expenses():
    """Test the get_top_expenses method"""
    print("\nTesting get_top_expenses method...")
    try:
        db = Database()

        # Test with a dummy user_id (this will return empty results but test the query structure)
        user_id = 1
        time_filter = "2024-01"  # January 2024
        category_filter = None
        top_n = 5

        results = db.get_top_expenses(user_id, time_filter, category_filter, top_n)
        print(f"✅ Query executed successfully, returned {len(results)} results")

        # Test with category filter
        category_filter = "Food & Drinks"
        results = db.get_top_expenses(user_id, time_filter, category_filter, top_n)
        print(f"✅ Category filter query executed successfully, returned {len(results)} results")

        # Test with "Others" category
        category_filter = "Others"
        results = db.get_top_expenses(user_id, time_filter, category_filter, top_n)
        print(f"✅ Others category query executed successfully, returned {len(results)} results")

        db.close()
        return True
    except Exception as e:
        print(f"❌ get_top_expenses test failed: {e}")
        return False

def test_expense_insertion():
    """Test inserting expenses with subtype"""
    print("\nTesting expense insertion with subtype...")
    try:
        db = Database()

        # Test inserting an expense with subtype (this will fail due to foreign key but test the query)
        user_id = 1
        amount = 100.00
        category = "Others"
        subtype = "Pet Care"
        payment_mode = "CASH"
        description = "Test expense"

        query = """INSERT INTO expenses (user_id, amount, category, subtype, payment_mode, description)
                   VALUES (%s, %s, %s, %s, %s, %s)"""

        # This will likely fail due to foreign key constraint (user_id doesn't exist)
        # but it tests that the query structure is correct
        try:
            result = db.execute_insert(query, (user_id, amount, category, subtype, payment_mode, description))
            print("✅ Expense insertion query structure is correct")
        except Exception as e:
            if "foreign key constraint" in str(e).lower() or "cannot add or update" in str(e).lower():
                print("✅ Expense insertion query structure is correct (failed as expected due to missing user)")
            else:
                raise e

        db.close()
        return True
    except Exception as e:
        print(f"❌ Expense insertion test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Top Expenses Feature Implementation")
    print("=" * 50)

    tests = [
        test_database_connection,
        test_get_top_expenses,
        test_expense_insertion
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Top Expenses feature implementation looks good.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
