"""
Enhanced Database Service
Production-grade database operations with duplicate checking and UUID support
"""

import sqlite3
import os
import uuid
import threading
import json
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from database.db import db
from utils.validators import ValidationUtils, ValidationResult


@dataclass
class DuplicateCheckResult:
    """Result of duplicate checking"""
    is_duplicate: bool
    duplicate_field: str = None
    existing_value: str = None
    error_message: str = None


class DuplicateChecker:
    """Real-time duplicate checking for all unique fields"""
    
    @staticmethod
    def check_email(email: str, exclude_user_id: int = None) -> DuplicateCheckResult:
        """
        Check if email already exists
        
        Args:
            email: Email to check
            exclude_user_id: User ID to exclude (for updates)
            
        Returns:
            DuplicateCheckResult
        """
        result = ValidationUtils.validate_email(email)
        
        if not result.is_valid:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=result.error_message
            )
        
        sanitized_email = result.sanitized_value
        
        try:
            if exclude_user_id:
                existing = db.execute_one(
                    "SELECT user_id, email FROM users WHERE email = ? COLLATE NOCASE AND user_id != ?",
                    (sanitized_email, exclude_user_id)
                )
            else:
                existing = db.execute_one(
                    "SELECT user_id, email FROM users WHERE email = ? COLLATE NOCASE",
                    (sanitized_email,)
                )
            
            if existing:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    duplicate_field='email',
                    existing_value=ValidationUtils.mask_email(existing['email'])
                )
            
            return DuplicateCheckResult(is_duplicate=False)
            
        except Exception as e:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def check_mobile(mobile: str, exclude_user_id: int = None) -> DuplicateCheckResult:
        """
        Check if mobile number already exists
        
        Args:
            mobile: Mobile number to check
            exclude_user_id: User ID to exclude
            
        Returns:
            DuplicateCheckResult
        """
        result = ValidationUtils.validate_mobile(mobile)
        
        if not result.is_valid:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=result.error_message
            )
        
        sanitized_mobile = result.sanitized_value
        
        try:
            if exclude_user_id:
                existing = db.execute_one(
                    "SELECT user_id, mobile FROM users WHERE mobile = ? AND user_id != ?",
                    (sanitized_mobile, exclude_user_id)
                )
            else:
                existing = db.execute_one(
                    "SELECT user_id, mobile FROM users WHERE mobile = ?",
                    (sanitized_mobile,)
                )
            
            if existing:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    duplicate_field='mobile',
                    existing_value=ValidationUtils.mask_mobile(existing['mobile'])
                )
            
            return DuplicateCheckResult(is_duplicate=False)
            
        except Exception as e:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def check_username(username: str, exclude_user_id: int = None) -> DuplicateCheckResult:
        """
        Check if username already exists
        
        Args:
            username: Username to check
            exclude_user_id: User ID to exclude
            
        Returns:
            DuplicateCheckResult
        """
        result = ValidationUtils.validate_username(username)
        
        if not result.is_valid:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=result.error_message
            )
        
        sanitized_username = result.sanitized_value
        
        try:
            if exclude_user_id:
                existing = db.execute_one(
                    "SELECT user_id, username FROM users WHERE username = ? COLLATE NOCASE AND user_id != ?",
                    (sanitized_username, exclude_user_id)
                )
            else:
                existing = db.execute_one(
                    "SELECT user_id, username FROM users WHERE username = ? COLLATE NOCASE",
                    (sanitized_username,)
                )
            
            if existing:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    duplicate_field='username',
                    existing_value=existing['username']
                )
            
            return DuplicateCheckResult(is_duplicate=False)
            
        except Exception as e:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def check_bank_account(account_number: str, exclude_account_id: int = None) -> DuplicateCheckResult:
        """
        Check if bank account number already exists
        
        Args:
            account_number: Account number to check
            exclude_account_id: Account ID to exclude
            
        Returns:
            DuplicateCheckResult
        """
        result = ValidationUtils.validate_bank_account(account_number)
        
        if not result.is_valid:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=result.error_message
            )
        
        clean_account = re.sub(r'[\s-]', '', result.sanitized_value)
        
        try:
            if exclude_account_id:
                existing = db.execute_one(
                    "SELECT account_id, account_number FROM bank_accounts WHERE account_number = ? AND account_id != ?",
                    (clean_account, exclude_account_id)
                )
            else:
                existing = db.execute_one(
                    "SELECT account_id, account_number FROM bank_accounts WHERE account_number = ?",
                    (clean_account,)
                )
            
            if existing:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    duplicate_field='bank_account_number',
                    existing_value=ValidationUtils.mask_bank_number(existing['account_number'])
                )
            
            return DuplicateCheckResult(is_duplicate=False)
            
        except Exception as e:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def check_upi_id(upi_id: str, exclude_account_id: int = None) -> DuplicateCheckResult:
        """
        Check if UPI ID already exists
        
        Args:
            upi_id: UPI ID to check
            exclude_account_id: Account ID to exclude
            
        Returns:
            DuplicateCheckResult
        """
        result = ValidationUtils.validate_upi_id(upi_id)
        
        if not result.is_valid:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=result.error_message
            )
        
        sanitized_upi = result.sanitized_value.lower()
        
        try:
            if exclude_account_id:
                existing = db.execute_one(
                    "SELECT account_id, upi_id FROM bank_accounts WHERE upi_id = ? COLLATE NOCASE AND account_id != ?",
                    (sanitized_upi, exclude_account_id)
                )
            else:
                existing = db.execute_one(
                    "SELECT account_id, upi_id FROM bank_accounts WHERE upi_id = ? COLLATE NOCASE",
                    (sanitized_upi,)
                )
            
            if existing:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    duplicate_field='upi_id',
                    existing_value=ValidationUtils.mask_upi_id(existing['upi_id'])
                )
            
            return DuplicateCheckResult(is_duplicate=False)
            
        except Exception as e:
            return DuplicateCheckResult(
                is_duplicate=False,
                error_message=f"Database error: {str(e)}"
            )
    
    @staticmethod
    def check_all_user_fields(
        username: str = None,
        email: str = None,
        mobile: str = None,
        exclude_user_id: int = None
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Check all user unique fields at once
        
        Args:
            username: Username to check
            email: Email to check
            mobile: Mobile to check
            exclude_user_id: User ID to exclude
            
        Returns:
            Tuple of (has_duplicates, error_dict)
        """
        errors = {}
        
        if username:
            result = DuplicateChecker.check_username(username, exclude_user_id)
            if result.is_duplicate:
                errors['username'] = "Username already taken"
            elif result.error_message:
                errors['username'] = result.error_message
        
        if email:
            result = DuplicateChecker.check_email(email, exclude_user_id)
            if result.is_duplicate:
                errors['email'] = "Email already registered"
            elif result.error_message:
                errors['email'] = result.error_message
        
        if mobile:
            result = DuplicateChecker.check_mobile(mobile, exclude_user_id)
            if result.is_duplicate:
                errors['mobile'] = "Mobile number already registered"
            elif result.error_message:
                errors['mobile'] = result.error_message
        
        return len(errors) > 0, errors
    
    @staticmethod
    def check_all_bank_fields(
        account_number: str = None,
        upi_id: str = None,
        exclude_account_id: int = None
    ) -> Tuple[bool, Dict[str, str]]:
        """
        Check all bank account unique fields at once
        
        Args:
            account_number: Account number to check
            upi_id: UPI ID to check
            exclude_account_id: Account ID to exclude
            
        Returns:
            Tuple of (has_duplicates, error_dict)
        """
        errors = {}
        
        if account_number:
            result = DuplicateChecker.check_bank_account(account_number, exclude_account_id)
            if result.is_duplicate:
                errors['account_number'] = "Bank account number already registered"
            elif result.error_message:
                errors['account_number'] = result.error_message
        
        if upi_id:
            result = DuplicateChecker.check_upi_id(upi_id, exclude_account_id)
            if result.is_duplicate:
                errors['upi_id'] = "UPI ID already linked"
            elif result.error_message:
                errors['upi_id'] = result.error_message
        
        return len(errors) > 0, errors


class UUIDGenerator:
    """UUID4 generation for secure IDs"""
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a new UUID4 string"""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_uuid(length: int = 16) -> str:
        """Generate a shortened UUID"""
        full_uuid = uuid.uuid4().hex
        return full_uuid[:length]
    
    @staticmethod
    def generate_transaction_id() -> str:
        """Generate a transaction ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_part = secrets.token_hex(6)
        return f"TXN{timestamp}{random_part}".upper()
    
    @staticmethod
    def generate_wallet_id() -> str:
        """Generate a wallet ID"""
        return f"WL{secure_hash(uuid.uuid4().hex)[:16].upper()}"
    
    @staticmethod
    def generate_investment_id() -> str:
        """Generate an investment ID"""
        timestamp = datetime.now().strftime('%Y%m%d')
        random_part = secrets.token_hex(4)
        return f"INV{timestamp}{random_part}".upper()
    
    @staticmethod
    def generate_log_id() -> str:
        """Generate a log ID"""
        return f"LOG{uuid.uuid4().hex[:16].upper()}"


def secure_hash(data: str) -> str:
    """Create a secure hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()


import secrets as _secrets
import hashlib as _hashlib


# Singleton instances
duplicate_checker = DuplicateChecker()
uuid_generator = UUIDGenerator()
