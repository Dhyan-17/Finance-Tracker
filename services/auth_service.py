"""
Authentication Service
Secure authentication with bcrypt password hashing and session management
"""

import bcrypt
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import streamlit as st

from database.db import db


class AuthService:
    """Secure authentication service"""
    
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15
    SESSION_DURATION_HOURS = 24
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    MOBILE_PATTERN = re.compile(r'^[6-9]\d{9}$')  # Indian mobile
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure session token"""
        return secrets.token_urlsafe(32)
    
    # ============================================================
    # VALIDATION
    # ============================================================
    
    @classmethod
    def validate_email(cls, email: str) -> Tuple[bool, str]:
        """Validate email format"""
        if not email:
            return False, "Email is required"
        if not cls.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"
        return True, ""
    
    @classmethod
    def validate_mobile(cls, mobile: str) -> Tuple[bool, str]:
        """Validate mobile number"""
        if not mobile:
            return False, "Mobile number is required"
        if not cls.MOBILE_PATTERN.match(mobile):
            return False, "Invalid mobile number. Must be 10 digits starting with 6-9"
        return True, ""
    
    @classmethod
    def validate_username(cls, username: str) -> Tuple[bool, str]:
        """Validate username"""
        if not username:
            return False, "Username is required"
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > 30:
            return False, "Username must be at most 30 characters"
        if not cls.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, ""
    
    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        return True, ""
    
    # ============================================================
    # USER AUTHENTICATION
    # ============================================================
    
    def register_user(
        self,
        username: str,
        email: str,
        mobile: str,
        password: str,
        confirm_password: str
    ) -> Tuple[bool, str, Optional[int]]:
        """Register a new user"""
        # Validate inputs
        valid, msg = self.validate_username(username)
        if not valid:
            return False, msg, None
        
        valid, msg = self.validate_email(email)
        if not valid:
            return False, msg, None
        
        valid, msg = self.validate_mobile(mobile)
        if not valid:
            return False, msg, None
        
        valid, msg = self.validate_password(password)
        if not valid:
            return False, msg, None
        
        if password != confirm_password:
            return False, "Passwords do not match", None
        
        # Check for existing user
        if db.user_exists(username=username):
            return False, "Username already taken", None
        if db.user_exists(email=email):
            return False, "Email already registered", None
        if db.user_exists(mobile=mobile):
            return False, "Mobile number already registered", None
        
        # Create user
        password_hash = self.hash_password(password)
        user_id = db.create_user(username, password_hash, email.lower(), mobile)
        
        if user_id:
            db.log_action('SYSTEM', 0, f'User registered: {username}', 'USER', user_id)
            return True, "Registration successful", user_id
        
        return False, "Registration failed. Please try again.", None
    
    def login_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate a user"""
        if not email or not password:
            return False, "Email and password are required", None
        
        user = db.get_user_by_email(email.lower())
        
        if not user:
            self._log_login_attempt(email, False)
            return False, "Invalid email or password", None
        
        # Check if account is locked
        if user['locked_until']:
            lock_time = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < lock_time:
                remaining = (lock_time - datetime.now()).seconds // 60
                return False, f"Account locked. Try again in {remaining} minutes", None
            else:
                # Unlock account
                db.execute(
                    "UPDATE users SET locked_until = NULL, failed_login_attempts = 0 WHERE user_id = ?",
                    (user['user_id'],)
                )
                user = db.get_user_by_id(user['user_id'])
        
        # Check account status
        if user['status'] != 'ACTIVE':
            return False, "Your account has been suspended. Contact support.", None
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            self._handle_failed_login(user)
            return False, "Invalid email or password", None
        
        # Successful login
        db.execute(
            "UPDATE users SET last_login = ?, failed_login_attempts = 0 WHERE user_id = ?",
            (db.now(), user['user_id'])
        )
        
        self._log_login_attempt(email, True)
        db.log_action('USER', user['user_id'], 'User logged in', 'USER', user['user_id'])
        
        # Return user data (excluding sensitive fields)
        return True, "Login successful", {
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'mobile': user['mobile'],
            'wallet_balance': user['wallet_balance'],
            'status': user['status'],
            'kyc_verified': user['kyc_verified']
        }
    
    def _handle_failed_login(self, user: Dict):
        """Handle failed login attempt"""
        attempts = (user.get('failed_login_attempts') or 0) + 1
        
        if attempts >= self.MAX_LOGIN_ATTEMPTS:
            lock_until = (datetime.now() + timedelta(minutes=self.LOCKOUT_MINUTES)).isoformat()
            db.execute(
                "UPDATE users SET failed_login_attempts = ?, locked_until = ? WHERE user_id = ?",
                (attempts, lock_until, user['user_id'])
            )
            db.log_action(
                'SYSTEM', 0,
                f"Account locked after {attempts} failed attempts",
                'USER', user['user_id'],
                severity='WARNING'
            )
        else:
            db.execute(
                "UPDATE users SET failed_login_attempts = ? WHERE user_id = ?",
                (attempts, user['user_id'])
            )
    
    def _log_login_attempt(self, email: str, success: bool):
        """Log login attempt"""
        db.execute_insert(
            "INSERT INTO login_attempts (email, success) VALUES (?, ?)",
            (email, 1 if success else 0)
        )
    
    # ============================================================
    # ADMIN AUTHENTICATION
    # ============================================================
    
    def login_admin(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """Authenticate an admin"""
        if not email or not password:
            return False, "Email and password are required", None
        
        admin = db.get_admin_by_email(email.lower())
        
        if not admin:
            return False, "Invalid credentials", None
        
        if not self.verify_password(password, admin['password_hash']):
            return False, "Invalid credentials", None
        
        # Update last login
        db.execute(
            "UPDATE admins SET last_login = ? WHERE admin_id = ?",
            (db.now(), admin['admin_id'])
        )
        
        db.log_action('ADMIN', admin['admin_id'], 'Admin logged in', 'ADMIN', admin['admin_id'])
        
        return True, "Login successful", {
            'admin_id': admin['admin_id'],
            'name': admin['name'],
            'email': admin['email'],
            'role': admin['role']
        }
    
    def create_admin(
        self,
        name: str,
        email: str,
        password: str,
        role: str = 'ADMIN',
        created_by: int = None
    ) -> Tuple[bool, str, Optional[int]]:
        """Create a new admin account"""
        valid, msg = self.validate_email(email)
        if not valid:
            return False, msg, None
        
        valid, msg = self.validate_password(password)
        if not valid:
            return False, msg, None
        
        if db.get_admin_by_email(email):
            return False, "Email already registered", None
        
        password_hash = self.hash_password(password)
        admin_id = db.create_admin(name, email.lower(), password_hash, role)
        
        if admin_id:
            db.log_action(
                'ADMIN' if created_by else 'SYSTEM',
                created_by or 0,
                f'Admin created: {email}',
                'ADMIN', admin_id
            )
            return True, "Admin created successfully", admin_id
        
        return False, "Failed to create admin", None
    
    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================
    
    def create_session(self, user_id: int, user_type: str = 'USER') -> str:
        """Create a new session"""
        session_id = self.generate_session_token()
        expires_at = (datetime.now() + timedelta(hours=self.SESSION_DURATION_HOURS)).isoformat()
        
        db.execute_insert(
            "INSERT INTO sessions (session_id, user_id, user_type, expires_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, user_type, expires_at)
        )
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict]:
        """Validate a session and return user info"""
        session = db.execute_one(
            "SELECT * FROM sessions WHERE session_id = ? AND is_active = 1",
            (session_id,)
        )
        
        if not session:
            return None
        
        # Check expiration
        if datetime.now() > datetime.fromisoformat(session['expires_at']):
            self.invalidate_session(session_id)
            return None
        
        return session
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        result = db.execute(
            "UPDATE sessions SET is_active = 0 WHERE session_id = ?",
            (session_id,)
        )
        return result > 0
    
    def logout(self, user_id: int = None, user_type: str = 'USER'):
        """Logout user and clear session"""
        if user_id:
            db.log_action(user_type, user_id, f'{user_type} logged out')
        
        # Clear streamlit session
        if 'user' in st.session_state:
            del st.session_state['user']
        if 'admin' in st.session_state:
            del st.session_state['admin']
        if 'authenticated' in st.session_state:
            del st.session_state['authenticated']
    
    # ============================================================
    # PASSWORD MANAGEMENT
    # ============================================================
    
    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        user_type: str = 'USER'
    ) -> Tuple[bool, str]:
        """Change user password"""
        # Get current user
        if user_type == 'USER':
            user = db.get_user_by_id(user_id)
        else:
            user = db.get_admin_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not self.verify_password(current_password, user['password_hash']):
            return False, "Current password is incorrect"
        
        # Validate new password
        valid, msg = self.validate_password(new_password)
        if not valid:
            return False, msg
        
        # Update password
        new_hash = self.hash_password(new_password)
        
        if user_type == 'USER':
            db.execute(
                "UPDATE users SET password_hash = ? WHERE user_id = ?",
                (new_hash, user_id)
            )
        else:
            db.execute(
                "UPDATE admins SET password_hash = ? WHERE admin_id = ?",
                (new_hash, user_id)
            )
        
        db.log_action(user_type, user_id, 'Password changed')
        return True, "Password changed successfully"
    
    def reset_user_password(
        self,
        user_id: int,
        new_password: str,
        admin_id: int
    ) -> Tuple[bool, str]:
        """Admin resets user password"""
        valid, msg = self.validate_password(new_password)
        if not valid:
            return False, msg
        
        user = db.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        new_hash = self.hash_password(new_password)
        db.execute(
            "UPDATE users SET password_hash = ?, failed_login_attempts = 0, locked_until = NULL WHERE user_id = ?",
            (new_hash, user_id)
        )
        
        db.log_action('ADMIN', admin_id, f'Reset password for user {user["username"]}', 'USER', user_id)
        
        # Notify user
        db.add_notification(
            user_id,
            "Password Reset",
            "Your password has been reset by an administrator. Please change it immediately.",
            "WARNING"
        )
        
        return True, "Password reset successfully"


# Singleton instance
auth_service = AuthService()
