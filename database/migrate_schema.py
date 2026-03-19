"""
Database Migration Script
Removes transfers table and updates goal_contributions schema
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'fintech.db')


def migrate():
    """Run migration to remove old tables and update schema"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting database migration...")
    
    # Drop old transfers table if exists
    try:
        cursor.execute("DROP TABLE IF EXISTS transfers")
        print("[+] Dropped 'transfers' table")
    except Exception as e:
        print("[-] Error dropping transfers table: {e}")
    
    # Update goal_contributions table to include source_account_id
    try:
        # Check if source_account_id column exists
        cursor.execute("PRAGMA table_info(goal_contributions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'source_account_id' not in columns:
            cursor.execute("ALTER TABLE goal_contributions ADD COLUMN source_account_id INTEGER")
            print("[+] Added 'source_account_id' column to goal_contributions")
        else:
            print("[+] 'source_account_id' column already exists")
        
        # Update source column to CHECK constraint
        cursor.execute("DROP TABLE IF EXISTS goal_contributions_new")
        cursor.execute("""
            CREATE TABLE goal_contributions_new (
                contribution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                source TEXT CHECK (source IN ('WALLET', 'BANK')),
                source_account_id INTEGER,
                note TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (goal_id) REFERENCES financial_goals(goal_id) ON DELETE CASCADE
            )
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO goal_contributions_new 
            (contribution_id, goal_id, amount, source, note, created_at)
            SELECT contribution_id, goal_id, amount, source, note, created_at
            FROM goal_contributions
        """)
        
        # Drop old and rename new
        cursor.execute("DROP TABLE goal_contributions")
        cursor.execute("ALTER TABLE goal_contributions_new RENAME TO goal_contributions")
        print("[+] Updated goal_contributions schema")
        
    except Exception as e:
        print("[-] Error updating goal_contributions: {e}")
    
    # Remove TRANSFER types from wallet_transactions if any exist
    try:
        cursor.execute("DELETE FROM wallet_transactions WHERE txn_type IN ('TRANSFER_IN', 'TRANSFER_OUT')")
        deleted_count = cursor.rowcount
        if deleted_count > 0:
            print("[+] Removed {deleted_count} transfer transactions from wallet_transactions")
    except Exception as e:
        print("[-] Error cleaning wallet_transactions: {e}")
    
    conn.commit()
    conn.close()
    
    print("\nMigration completed!")


if __name__ == "__main__":
    migrate()
