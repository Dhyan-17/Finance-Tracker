"""
Production-Grade Validation Utilities
RFC-compliant email, phone, UPI, and bank account validation
"""

import re
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    error_message: str
    sanitized_value: str = None


class ValidationUtils:
    """Production-grade validation utilities"""
    
    # RFC 5322 inspired email pattern (simplified for practical use)
    EMAIL_PATTERN = re.compile(
        r"^(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
        r"|(?:\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")"
        r"@(?:(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
        r"|(?:\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\]))$",
        re.IGNORECASE
    )
    
    # Indian mobile number (10 digits, starts with 6-9)
    MOBILE_PATTERN = re.compile(r'^[6-9]\d{9}$')
    
    # UPI ID pattern (name@bank or name@provider)
    UPI_PATTERN = re.compile(
        r'^[a-zA-Z][a-zA-Z0-9._-]{2,30}@[a-zA-Z]{2,20}$',
        re.IGNORECASE
    )
    
    # Bank account number (9-18 digits)
    BANK_ACCOUNT_PATTERN = re.compile(r'^\d{9,18}$')
    
    # IFSC code (4 letters + 7 alphanumeric)
    IFSC_PATTERN = re.compile(r'^[A-Z]{4}0[A-Z0-9]{6}$')
    
    # Password strength pattern (minimum requirements)
    PASSWORD_PATTERN = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    )
    
    # Username pattern (3-30 alphanumeric + underscore)
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
    
    # Amount validation (positive number with up to 2 decimal places)
    AMOUNT_PATTERN = re.compile(r'^\d+(?:\.\d{1,2})?$')
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Remove potentially dangerous characters and trim"""
        if value is None:
            return ""
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(value))
        # Trim whitespace
        return sanitized.strip()
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize and normalize email"""
        email = ValidationUtils.sanitize_string(email)
        return email.lower().strip()
    
    @staticmethod
    def sanitize_mobile(mobile: str) -> str:
        """Sanitize mobile number (remove non-digits)"""
        mobile = ValidationUtils.sanitize_string(mobile)
        return re.sub(r'\D', '', mobile)
    
    @classmethod
    def validate_email(cls, email: str) -> ValidationResult:
        """
        Validate email address with RFC-compliant checks
        
        Args:
            email: Email address to validate
            
        Returns:
            ValidationResult with status and sanitized value
        """
        # Sanitize input
        email = cls.sanitize_string(email)
        
        # Check if empty
        if not email:
            return ValidationResult(
                is_valid=False,
                error_message="Email is required",
                sanitized_value=""
            )
        
        # Length check
        if len(email) < 5 or len(email) > 254:
            return ValidationResult(
                is_valid=False,
                error_message="Email must be between 5 and 254 characters",
                sanitized_value=email.lower()
            )
        
        # Pattern check
        if not cls.EMAIL_PATTERN.match(email):
            return ValidationResult(
                is_valid=False,
                error_message="Invalid email format",
                sanitized_value=email.lower()
            )
        
        # Normalize and return
        normalized_email = email.lower().strip()
        return ValidationResult(
            is_valid=True,
            error_message="",
            sanitized_value=normalized_email
        )
    
    @classmethod
    def validate_mobile(cls, mobile: str) -> ValidationResult:
        """
        Validate Indian mobile number (10 digits)
        
        Args:
            mobile: Mobile number to validate
            
        Returns:
            ValidationResult with status and sanitized value
        """
        # Sanitize input
        mobile = cls.sanitize_mobile(mobile)
        
        # Check if empty
        if not mobile:
            return ValidationResult(
                is_valid=False,
                error_message="Mobile number is required",
                sanitized_value=""
            )
        
        # Length check
        if len(mobile) != 10:
            return ValidationResult(
                is_valid=False,
                error_message="Mobile number must be exactly 10 digits",
                sanitized_value=mobile
            )
        
        # Pattern check
        if not cls.MOBILE_PATTERN.match(mobile):
            return ValidationResult(
                is_valid=False,
                error_message="Mobile number must start with 6, 7, 8, or 9",
                sanitized_value=mobile
            )
        
        # All checks passed
        return ValidationResult(
            is_valid=True,
            error_message="",
            sanitized_value=mobile
        )
    
    @classmethod
    def validate_upi_id(cls, upi_id: str) -> ValidationResult:
        """
        Validate UPI ID format (name@bank or name@provider)
        
        Args:
            upi_id: UPI ID to validate
            
        Returns:
            ValidationResult with status and sanitized value
        """
        # Sanitize input
        upi_id = cls.sanitize_string(upi_id)
        
        # Check if empty
        if not upi_id:
            return ValidationResult(
                is_valid=False,
                error_message="UPI ID is required",
                sanitized_value=""
            )
        
        # Length check
        if len(upi_id) < 5 or len(upi_id) > 50:
            return ValidationResult(
                is_valid=False,
                error_message="UPI ID must be between 5 and 50 characters",
                sanitized_value=upi_id.lower()
            )
        
        # Pattern check
        if not cls.UPI_PATTERN.match(upi_id):
            return ValidationResult(
                is_valid=False,
                error_message="Invalid UPI ID format. Use format: name@bank",
                sanitized_value=upi_id.lower()
            )
        
        # Normalize (lowercase)
        normalized_upi = upi_id.lower().strip()
        return ValidationResult(
            is_valid=True,
            error_message="",
            sanitized_value=normalized_upi
        )
    
    @classmethod
    def validate_bank_account(cls, account_number: str) -> ValidationResult:
        """
        Validate bank account number (9-18 digits)
        
        Args:
            account_number: Bank account number to validate
            
        Returns:
            ValidationResult with status and sanitized value
        """
        # Sanitize input
        account_number = cls.sanitize_string(account_number)
        
        # Check if empty
        if not account_number:
            return ValidationResult(
                is_valid=False,
                error_message="Bank account number is required",
                sanitized_value=""
            )
        
        # Remove any spaces or dashes
        clean_account = re.sub(r'[\s-]', '', account_number)
        
        # Length check
        if len(clean_account) < 9 or len(clean_account) > 18:
            return ValidationResult(
                is_valid=False,
                error_message="Bank account number must be between 9 and 18 digits",
                sanitized_value=clean_account
            )
        
        # Numeric only check
        if not clean_account.isdigit():
            return ValidationResult(
                is_valid=False,
                error_message="Bank account number must contain only digits",
                sanitized_value=clean_account
            )
        
        return ValidationResult(
            is_valid=True,
            error_message="",
            sanitized_value=clean_account
        )
    
    @classmethod
    def validate_ifsc(cls, ifsc_code: str) -> ValidationResult:
        """
        Validate IFSC code
        
        Args:
            ifsc_code: IFSC code to validate
            
        Returns:
            ValidationResult with status and sanitized value
        """
        # Sanitize input
        ifsc_code = cls.sanitize_string(ifsc_code).upper()
        
        # Check if empty
        if not ifsc_code:
            return ValidationResult(
                is_valid=False,
                error_message="IFSC code is required",
                sanitized_value=""
            )
        
        # Pattern check
        if not cls.IFSC_PATTERN.match(ifsc_code):
            return ValidationResult(
                is_valid=False,
                error_message="Invalid IFSC code format (e.g., SBIN0001234)",
                sanitized_value=ifsc_code
            )
        
        return ValidationResult(
            is_valid=True,
            error_message="",
            sanitized_value=ifsc_code
        )
    
    @classmethod
    def validate_password(cls, password: str) -> ValidationResult:
        """
        Validate password strength
        
        Requirements:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character (@$!%*?&)
        
        Args:
            password: Password to validate
            
        Returns:
            ValidationResult with status and error details
        """
        # Check if empty
        if not password:
            return ValidationResult(
                is_valid=False,
                error_message="Password is required",
                sanitized_value=""
            )
        
        # Length check
        if len(password) < 8:
            return ValidationResult(
                is_valid=False,
                error_message="Password must be at least 8 characters long",
                sanitized_value=""
            )
        
        if len(password) > 128:
            return ValidationResult(
                is_valid=False,
                error_message="Password cannot exceed 128 characters",
                sanitized_value=""
            )
        
        # Strength checks
        errors = []
        
        if not re.search(r'[A-Z]', password):
            errors.append("uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("digit")
        
        if not re.search(r'[@$!%*?&]', password):
            errors.append("special character (@$!%*?&)")
        
        if errors:
            error_msg = "Password must contain at least one: " + ", ".join(errors)
            return ValidationResult(
                is_valid=False,
                error_message=error_msg,
                sanitized_value=""
            )
        
        return ValidationResult(
            is_valid=True,
            error_message="",
            sanitized_value=""
        )
    
    @classmethod
    def validate_username(cls, username: str) -> ValidationResult:
        """
        Validate username
        
        Args:
            username: Username to validate
            
        Returns:
            ValidationResult with status and sanitized value
        """
        # Sanitize input
        username = cls.sanitize_string(username)
        
        # Check if empty
        if not username:
            return ValidationResult(
                is_valid=False,
                error_message="Username is required",
                sanitized_value=""
            )
        
        # Length check
        if len(username) < 3:
            return ValidationResult(
                is_valid=False,
                error_message="Username must be at least 3 characters",
                sanitized_value=username.lower()
            )
        
        if len(username) > 30:
            return ValidationResult(
                is_valid=False,
                error_message="Username cannot exceed 30 characters",
                sanitized_value=username.lower()
            )
        
        # Pattern check
        if not cls.USERNAME_PATTERN.match(username):
            return ValidationResult(
                is_valid=False,
                error_message="Username can only contain letters, numbers, and underscores",
                sanitized_value=username.lower()
            )
        
        return ValidationResult(
            is_valid=True,
            error_message="",
            sanitized_value=username.lower()
        )
    
    @classmethod
    def validate_amount(cls, amount: str) -> ValidationResult:
        """
        Validate monetary amount
        
        Args:
            amount: Amount string to validate
            
        Returns:
            ValidationResult with status and float value
        """
        # Sanitize input
        amount = cls.sanitize_string(amount)
        
        # Check if empty
        if not amount:
            return ValidationResult(
                is_valid=False,
                error_message="Amount is required",
                sanitized_value=""
            )
        
        # Try to parse as float
        try:
            value = float(amount)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid amount format",
                sanitized_value=""
            )
        
        # Range check
        if value <= 0:
            return ValidationResult(
                is_valid=False,
                error_message="Amount must be positive",
                sanitized_value=""
            )
        
        if value > 999999999:  # Max 999 million
            return ValidationResult(
                is_valid=False,
                error_message="Amount exceeds maximum limit",
                sanitized_value=""
            )
        
        return ValidationResult(
            is_valid=True,
            error_message="",
            sanitized_value=str(round(value, 2))
        )
    
    @classmethod
    def validate_date(cls, date_str: str, format_str: str = '%Y-%m-%d') -> ValidationResult:
        """
        Validate date string
        
        Args:
            date_str: Date string to validate
            format_str: Expected format (default: YYYY-MM-DD)
            
        Returns:
            ValidationResult with status and normalized date
        """
        from datetime import datetime
        
        date_str = cls.sanitize_string(date_str)
        
        if not date_str:
            return ValidationResult(
                is_valid=False,
                error_message="Date is required",
                sanitized_value=""
            )
        
        try:
            parsed_date = datetime.strptime(date_str, format_str)
            return ValidationResult(
                is_valid=True,
                error_message="",
                sanitized_value=parsed_date.strftime(format_str)
            )
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid date format. Expected: {format_str}",
                sanitized_value=""
            )
    
    @staticmethod
    def mask_bank_number(account_number: str) -> str:
        """
        Mask bank account number for display
        
        Args:
            account_number: Full account number
            
        Returns:
            Masked account number (e.g., XXXX1234)
        """
        if not account_number or len(account_number) < 4:
            return "****"
        
        clean_account = re.sub(r'[\s-]', '', account_number)
        visible_last4 = clean_account[-4:]
        masked = "X" * (len(clean_account) - 4) + visible_last4
        
        # Add spaces for readability if long
        if len(masked) > 8:
            masked = " ".join([masked[i:i+4] for i in range(0, len(masked), 4)])
        
        return masked
    
    @staticmethod
    def mask_upi_id(upi_id: str) -> str:
        """
        Mask UPI ID for display
        
        Args:
            upi_id: Full UPI ID
            
        Returns:
            Masked UPI ID (e.g., jo***@upi)
        """
        if not upi_id:
            return "****"
        
        parts = upi_id.split('@')
        if len(parts) != 2:
            return "****@****"
        
        name, domain = parts
        if len(name) <= 3:
            masked_name = "X" * len(name)
        else:
            masked_name = name[:3] + "X" * (len(name) - 3)
        
        return f"{masked_name}@{domain}"
    
    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask email for display
        
        Args:
            email: Full email address
            
        Returns:
            Masked email (e.g., j***@gmail.com)
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
            mobile: Full mobile number
            
        Returns:
            Masked mobile (e.g., 98765*****0)
        """
        if not mobile or len(mobile) != 10:
            return "****"
        
        return mobile[:5] + "XXXXX" + mobile[-1]


# Singleton instance
validator = ValidationUtils()
