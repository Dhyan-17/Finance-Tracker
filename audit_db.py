"""
Database Integrity Audit Script
Checks for data inconsistencies and logical errors
"""

import mysql.connector

def run_audit():
    conn = mysql.connector.connect(
        host='localhost', user='root', password='', database='finance_tracker'
    )
    cursor = conn.cursor(dictionary=True)

    print('=' * 60)
    print('DATABASE INTEGRITY AUDIT')
    print('=' * 60)

    issues_found = []

    # 1. Check for orphan expenses
    cursor.execute('''
        SELECT COUNT(*) as cnt FROM expenses e 
        LEFT JOIN users u ON e.user_id = u.user_id 
        WHERE u.user_id IS NULL
    ''')
    result = cursor.fetchone()
    print(f"[1] Orphan expenses: {result['cnt']}")
    if result['cnt'] > 0:
        issues_found.append("Orphan expenses found")

    # 2. Check for orphan income
    cursor.execute('''
        SELECT COUNT(*) as cnt FROM income i 
        LEFT JOIN users u ON i.user_id = u.user_id 
        WHERE u.user_id IS NULL
    ''')
    result = cursor.fetchone()
    print(f"[2] Orphan income: {result['cnt']}")

    # 3. Check for duplicate budgets
    cursor.execute('''
        SELECT user_id, category, year, month, COUNT(*) as cnt 
        FROM budget 
        GROUP BY user_id, category, year, month 
        HAVING cnt > 1
    ''')
    duplicates = cursor.fetchall()
    print(f"[3] Duplicate budgets: {len(duplicates)}")
    for d in duplicates:
        print(f"    - User {d['user_id']}, {d['category']}, {d['year']}-{d['month']:02d}")
        issues_found.append(f"Duplicate budget: {d['category']}")

    # 4. Check for invalid year/month
    cursor.execute('''
        SELECT budget_id, year, month FROM budget 
        WHERE year < 2000 OR year > 2100 OR month < 1 OR month > 12
    ''')
    invalid = cursor.fetchall()
    print(f"[4] Invalid budget dates: {len(invalid)}")
    for i in invalid:
        print(f"    - ID {i['budget_id']}: year={i['year']}, month={i['month']}")
        issues_found.append(f"Invalid budget date: ID {i['budget_id']}")

    # 5. Negative amounts
    cursor.execute('SELECT COUNT(*) as cnt FROM expenses WHERE amount < 0')
    result = cursor.fetchone()
    print(f"[5] Negative expense amounts: {result['cnt']}")

    cursor.execute('SELECT COUNT(*) as cnt FROM income WHERE amount < 0')
    result = cursor.fetchone()
    print(f"[6] Negative income amounts: {result['cnt']}")

    cursor.execute('SELECT COUNT(*) as cnt FROM budget WHERE limit_amount < 0')
    result = cursor.fetchone()
    print(f"[7] Negative budget limits: {result['cnt']}")

    # 6. NULL checks
    cursor.execute('SELECT COUNT(*) as cnt FROM expenses WHERE user_id IS NULL')
    result = cursor.fetchone()
    print(f"[8] NULL user_id in expenses: {result['cnt']}")

    # 7. Financial goals check
    cursor.execute('''
        SELECT goal_id, goal_name, target_amount, current_savings 
        FROM financial_goals 
        WHERE current_savings > target_amount AND status = 'ACTIVE'
    ''')
    over_saved = cursor.fetchall()
    print(f"[9] Goals with savings > target (should be COMPLETED): {len(over_saved)}")

    # 8. Empty descriptions in expenses
    cursor.execute('''
        SELECT COUNT(*) as cnt FROM expenses 
        WHERE description IS NULL OR description = ''
    ''')
    result = cursor.fetchone()
    print(f"[10] Expenses with empty description: {result['cnt']}")

    # 9. Check for future expenses
    cursor.execute('''
        SELECT COUNT(*) as cnt FROM expenses 
        WHERE DATE(date) > CURDATE()
    ''')
    result = cursor.fetchone()
    print(f"[11] Future-dated expenses: {result['cnt']}")

    # 10. Users summary
    cursor.execute('SELECT COUNT(*) as cnt FROM users')
    result = cursor.fetchone()
    print(f"[12] Total users: {result['cnt']}")

    cursor.execute('SELECT COUNT(*) as cnt FROM expenses')
    result = cursor.fetchone()
    print(f"[13] Total expenses: {result['cnt']}")

    cursor.execute('SELECT COUNT(*) as cnt FROM budget')
    result = cursor.fetchone()
    print(f"[14] Total budgets: {result['cnt']}")

    print('=' * 60)
    
    if issues_found:
        print("ISSUES FOUND:")
        for issue in issues_found:
            print(f"  - {issue}")
    else:
        print("NO CRITICAL ISSUES FOUND")

    print('=' * 60)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    run_audit()
