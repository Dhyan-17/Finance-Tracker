"""
Security Service
Production-grade security utilities for masking, encryption, and data protection
"""

import hashlib
import secrets
import re
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import streamlit as st

from database.db import db
from utils.validators import ValidationUtils


class SecurityService:
    """Production-grade security service"""
    
    # Session settings
    SESSION_DURATION_HOURS = 24
    MAX_SESSIONS_PER_USER = 5
    SESSION_RENEWAL_HOURS = 4
    
    # Rate limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 3600  # 1 hour
    
    # Password settings
    PASSWORD_MAX_AGE_DAYS = 90
    PASSWORD_HISTORY_SIZE = 12
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(48)
    
    @staticmethod
    def generate_secure_id(prefix: str = '') -> str:
        """Generate secure unique ID"""
        random_part = secrets.token_urlsafe(12)
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{prefix}{timestamp}{random_part}" if prefix else f"{timestamp}{random_part}"
    
    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data (one-way)"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def mask_account_number(account_number: str) -> str:
        """
        Mask bank account number for display
        Shows only last 4 digits
        
        Args:
            account_number: Full account number
            
        Returns:
            Masked account number (e.g., XXXXXX1234)
        """
        if not account_number:
            return "****"
        
        clean_account = re.sub(r'[\s-]', '', str(account_number))
        
        if len(clean_account) <= 4:
            return "X" * len(clean_account)
        
        return "X" * (len(clean_account) - 4) + clean_account[-4:]
    
    @staticmethod
    def mask_upi_id(upi_id: str) -> str:
        """
        Mask UPI ID for display
        Shows first 3 chars of name and domain
        
        Args:
            upi_id: Full UPI ID
            
        Returns:
            Masked UPI ID (e.g., john@upi → joh***@upi)
        """
        if not upi_id:
            return "****"
        
        if '@' not in upi_id:
            return "****@****"
        
        name, domain = upi_id.split('@', 1)
        
        if len(name) <= 3:
            masked_name = "X" * len(name)
        else:
            masked_name = name[:3] + "X" * (len(name) - 3)
        
        # Mask domain slightly
        if len(domain) > 4:
            masked_domain = domain[:2] + "X" * (len(domain) - 4) + domain[-2:]
        else:
            masked_domain = "X" * len(domain)
        
        return f"{masked_name}@{masked_domain}"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask email for display
        Shows first 3 chars and domain
        
        Args:
            email: Full email address
            
        Returns:
            Masked email (e.g., john.doe@gmail.com → joh***@gmail.com)
        """
        if not email or '@' not in email:
            return "****@****"
        
        local, domain = email.split('@', 1)
        
        if len(local) <= 3:
            masked_local = "X" * len(local)
        else:
            masked_local = local[:3] + "X" * (len(local) - 3)
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_mobile(mobile: str) -> str:
        """
        Mask mobile number for display
        
        Args:
            mobile: Full 10-digit mobile number
            
        Returns:
            Masked mobile (e.g., 9876543210 → 9876XXXXX0)
        """
        if not mobile or len(mobile) != 10:
            return "**********"
        
        return mobile[:4] + "X" * 4 + mobile[-2:]
    
    @staticmethod
    def mask_amount(amount: float, show_last: int = 2) -> str:
        """
        Mask amount for partial display
        
        Args:
            amount: Amount in rupees
            show_last: Number of digits to show at end
            
        Returns:
            Masked amount string
        """
        amount_str = f"{amount:,.2f}"
        parts = amount_str.split('.')
        
        if len(parts[0]) <= show_last:
            return "X" * len(parts[0]) + "." + parts[1]
        
        masked_integer = "X" * (len(parts[0]) - show_last) + parts[0][-show_last:]
        return masked_integer + "." + parts[1]
    
    @staticmethod
    def sanitize_for_display(value: str, mask_type: str = 'none') -> str:
        """
        Sanitize and mask value for display
        
        Args:
            value: Value to sanitize
            mask_type: Type of masking ('account', 'upi', 'email', 'mobile', 'amount', 'none')
            
        Returns:
            Sanitized and masked value
        """
        if value is None:
            return ""
        
        sanitized = ValidationUtils.sanitize_string(value)
        
        if not sanitized:
            return ""
        
        mask_functions = {
            'account': SecurityService.mask_account_number,
            'upi': SecurityService.mask_upi_id,
            'email': SecurityService.mask_email,
            'mobile': SecurityService.mask_mobile,
            'amount': SecurityService.mask_amount,
            'none': lambda x: x,
        }
        
        mask_func = mask_functions.get(mask_type, mask_functions['none'])
        return mask_func(sanitized)
    
    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================
    
    @staticmethod
    def create_session(user_id: int, user_type: str = 'USER', 
                       ip_address: str = None, user_agent: str = None) -> Dict:
        """
        Create a new user session
        
        Args:
            user_id: User ID
            user_type: Type of user (USER, ADMIN)
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Session data dict
        """
        session_id = SecurityService.generate_session_token()
        expires_at = (datetime.now() + timedelta(hours=SecurityService.SESSION_DURATION_HOURS)).isoformat()
        
        try:
            db.execute_insert(
                """INSERT INTO sessions 
                   (session_id, user_id, user_type, ip_address, user_agent, expires_at, last_activity)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, user_id, user_type, ip_address, user_agent, expires_at, datetime.now().isoformat())
            )
            
            return {
                'session_id': session_id,
                'user_id': user_id,
                'user_type': user_type,
                'expires_at': expires_at
            }
        except Exception as e:
            print(f"Error creating session: {e}")
            return None
    
    @staticmethod
    def validate_session(session_id: str) -> Optional[Dict]:
        """
        Validate session and return user info
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            Session data or None if invalid
        """
        if not session_id:
            return None
        
        try:
            session = db.execute_one(
                """SELECT s.*, u.username, u.email, u.status, u.wallet_balance
                   FROM sessions s
                   JOIN users u ON s.user_id = u.user_id
                   WHERE s.session_id = ? AND s.is_active = 1""",
                (session_id,)
            )
            
            if not session:
                return None
            
            # Check expiration
            if datetime.now() > datetime.fromisoformat(session['expires_at']):
                SecurityService.invalidate_session(session_id)
                return None
            
            # Update last activity
            db.execute(
                "UPDATE sessions SET last_activity = ? WHERE session_id = ?",
                (datetime.now().isoformat(), session_id)
            )
            
            return session
        except Exception as e:
            print(f"Error validating session: {e}")
            return None
    
    @staticmethod
    def invalidate_session(session_id: str) -> bool:
        """Invalidate a session"""
        try:
            result = db.execute(
                "UPDATE sessions SET is_active = 0 WHERE session_id = ?",
                (session_id,)
            )
            return result > 0
        except Exception:
            return False
    
    @staticmethod
    def invalidate_all_user_sessions(user_id: int, keep_session_id: str = None) -> int:
        """
        Invalidate all sessions for a user
        
        Args:
            user_id: User ID
            keep_session_id: Session ID to keep (optional)
            
        Returns:
            Number of sessions invalidated
        """
        try:
            if keep_session_id:
                result = db.execute(
                    "UPDATE sessions SET is_active = 0 WHERE user_id = ? AND session_id != ?",
                    (user_id, keep_session_id)
                )
            else:
                result = db.execute(
                    "UPDATE sessions SET is_active = 0 WHERE user_id = ?",
                    (user_id,)
                )
            return result
        except Exception:
            return 0
    
    # ============================================================
    # RATE LIMITING
    # ============================================================
    
    @staticmethod
    def check_rate_limit(identifier: str, request_count: int = None) -> Dict:
        """
        Check rate limit for an identifier
        
        Args:
            identifier: Unique identifier (IP, user_id, etc.)
            request_count: Current request count
            
        Returns:
            Rate limit status dict
        """
        if request_count is None:
            request_count = SecurityService.RATE_LIMIT_REQUESTS
        
        return {
            'allowed': request_count < SecurityService.RATE_LIMIT_REQUESTS,
            'remaining': max(0, SecurityService.RATE_LIMIT_REQUESTS - request_count),
            'reset_time': (datetime.now() + timedelta(seconds=SecurityService.RATE_LIMIT_WINDOW)).isoformat()
        }
    
    # ============================================================
    # INPUT SANITIZATION
    # ============================================================
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """
        Sanitize HTML content to prevent XSS
        
        Args:
            content: Raw content
            
        Returns:
            Sanitized content
        """
        if not content:
            return ""
        
        # Remove potentially dangerous HTML tags
        dangerous_tags = ['<script', '<iframe', '<object', '<embed', '<link', '<style']
        sanitized = content
        
        for tag in dangerous_tags:
            sanitized = sanitized.replace(tag, '')
        
        # Remove event handlers
        sanitized = re.sub(r'\s*on\w+\s*=', ' data-removed=', sanitized)
        
        return sanitized.strip()
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """
        Sanitize search query to prevent injection
        
        Args:
            query: Raw search query
            
        Returns:
            Sanitized query
        """
        if not query:
            return ""
        
        # Remove SQL injection patterns
        sql_patterns = [
            r"(\b)(SELECT|INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|EXEC|UNION|JOIN)\b",
            r"['\";--]",
            r"\/\*",
            r"\*\/",
            r"@",
            r"#",
            r"\$",
        ]
        
        sanitized = query
        for pattern in sql_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        max_length = 200
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized.strip()
    
    # ============================================================
    # SECURITY LOGGING
    # ============================================================
    
    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: int = None,
        details: Dict = None,
        ip_address: str = None,
        severity: str = 'INFO'
    ):
        """
        Log security event for audit
        
        Args:
            event_type: Type of event
            user_id: User ID involved
            details: Additional details
            ip_address: Client IP
            severity: Event severity
        """
        try:
            import json
            
            db.execute_insert(
                """INSERT INTO audit_logs 
                   (actor_type, actor_id, action, old_values, ip_address, severity)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    'SYSTEM' if not user_id else 'USER',
                    user_id,
                    event_type,
                    json.dumps(details) if details else None,
                    ip_address,
                    severity
                )
            )
        except Exception as e:
            print(f"Error logging security event: {e}")
    
    # ============================================================
    # PASSWORD UTILITIES
    # ============================================================
    
    @staticmethod
    def check_password_expiry(password_hash: str) -> Dict:
        """
        Check if password needs to be changed
        
        Args:
            password_hash: Current password hash
            
        Returns:
            Password expiry status
        """
        # This would typically check against a password_change_date field
        # For now, return neutral status
        return {
            'expired': False,
            'days_until_expiry': SecurityService.PASSWORD_MAX_AGE_DAYS,
            'should_change': False
        }
    
    # ============================================================
    # DATA EXPORT MASKING
    # ============================================================
    
    @staticmethod
    def mask_user_data(user_data: Dict, include_sensitive: bool = False) -> Dict:
        """
        Mask user data for export/display
        
        Args:
            user_data: Raw user data dict
            include_sensitive: Whether to include sensitive data
            
        Returns:
            Masked user data
        """
        masked = {
            'user_id': user_data.get('user_id'),
            'username': user_data.get('username'),
            'email': SecurityService.mask_email(user_data.get('email', '')),
            'mobile': SecurityService.mask_mobile(user_data.get('mobile', '')) if user_data.get('mobile') else None,
            'wallet_balance': user_data.get('wallet_balance'),
            'status': user_data.get('status'),
            'created_at': user_data.get('created_at'),
        }
        
        if include_sensitive:
            masked['email'] = user_data.get('email')
            masked['mobile'] = user_data.get('mobile')
            masked['kyc_verified'] = user_data.get('kyc_verified')
        
        return masked
    
    @staticmethod
    def mask_transaction_data(tx_data: Dict) -> Dict:
        """
        Mask transaction data for display
        
        Args:
            tx_data: Raw transaction data
            
        Returns:
            Masked transaction data
        """
        return {
            'txn_id': tx_data.get('txn_id'),
            'uuid': tx_data.get('uuid', '')[:8] + '...' if tx_data.get('uuid') else None,
            'txn_type': tx_data.get('txn_type'),
            'amount': tx_data.get('amount'),
            'description': tx_data.get('description'),
            'date': tx_data.get('date'),
        }
    
    @staticmethod
    def mask_bank_account_data(ba_data: Dict) -> Dict:
        """
        Mask bank account data for display
        
        Args:
            ba_data: Raw bank account data
            
        Returns:
            Masked bank account data
        """
        return {
            'account_id': ba_data.get('account_id'),
            'bank_name': ba_data.get('bank_name'),
            'account_number': SecurityService.mask_account_number(ba_data.get('account_number', '')),
            'upi_id': SecurityService.mask_upi_id(ba_data.get('upi_id', '')) if ba_data.get('upi_id') else None,
            'balance': ba_data.get('balance'),
            'is_primary': ba_data.get('is_primary'),
        }
    
    @staticmethod
    def mask_investment_data(inv_data: Dict) -> Dict:
        """
        Mask investment data for display
        
        Args:
            inv_data: Raw investment data
            
        Returns:
            Masked investment data
        """
        return {
            'investment_id': inv_data.get('investment_id'),
            'asset_symbol': inv_data.get('asset_symbol'),
            'asset_name': inv_data.get('asset_name'),
            'units_owned': inv_data.get('units_owned'),
            'current_value': inv_data.get('current_value'),
            'profit_loss': inv_data.get('profit_loss'),
            'profit_loss_percent': inv_data.get('profit_loss_percent'),
        }


# Singleton instance
security_service = SecurityService()
