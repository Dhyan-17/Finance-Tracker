"""
Setup Script for Smart Finance Tracker
Initializes database and creates default admin account
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import Database, db
from services.auth_service import AuthService


def setup():
    """Initialize the application"""
    print("=" * 60)
    print("Smart Finance Tracker - Setup")
    print("=" * 60)
    
    # Initialize database
    print("\n📦 Initializing database...")
    
    # Force database initialization
    database = Database()
    
    print("✅ Database initialized successfully!")
    print(f"📁 Database location: {database.db_path}")
    
    # Check if admin exists
    print("\n👤 Checking admin account...")
    
    admin = db.get_admin_by_email("admin@fintrack.com")
    
    if not admin:
        print("Creating default admin account...")
        
        auth = AuthService()
        success, message, admin_id = auth.create_admin(
            name="System Admin",
            email="admin@fintrack.com",
            password="Admin@123",
            role="SUPER_ADMIN"
        )
        
        if success:
            print("✅ Default admin created!")
            print("   Email: admin@fintrack.com")
            print("   Password: Admin@123")
            print("   ⚠️  Please change the password after first login!")
        else:
            print(f"❌ Failed to create admin: {message}")
    else:
        print("✅ Admin account already exists")
    
    # Create demo user (optional)
    print("\n👤 Checking demo user...")
    
    demo_user = db.get_user_by_email("demo@fintrack.com")
    
    if not demo_user:
        print("Creating demo user account...")
        
        auth = AuthService()
        success, message, user_id = auth.register_user(
            username="demo_user",
            email="demo@fintrack.com",
            mobile="9876543210",
            password="Demo@123",
            confirm_password="Demo@123"
        )
        
        if success:
            # Add some initial balance
            db.execute(
                "UPDATE users SET wallet_balance = ? WHERE user_id = ?",
                (db.to_paise(50000), user_id)
            )
            
            print("✅ Demo user created!")
            print("   Email: demo@fintrack.com")
            print("   Password: Demo@123")
            print("   Wallet Balance: ₹50,000")
        else:
            print(f"❌ Failed to create demo user: {message}")
    else:
        print("✅ Demo user already exists")
    
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nTo start the application, run:")
    print("  streamlit run app.py")
    print("\nDefault Credentials:")
    print("  Admin: admin@fintrack.com / Admin@123")
    print("  User:  demo@fintrack.com / Demo@123")
    print("=" * 60)


if __name__ == "__main__":
    setup()
