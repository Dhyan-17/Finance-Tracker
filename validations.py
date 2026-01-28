import re
from datetime import datetime

class Validation:
    """Input validation utilities"""

    def get_valid_input(self, prompt, validator, error_msg):
        """Get validated input from user"""
        while True:
            try:
                user_input = input(prompt).strip()
                if validator(user_input):
                    return user_input
                else:
                    print(f"+-----------------------------------+")
                    print(f"| {error_msg}")
                    print("+-----------------------------------+")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user.")
                raise
            except Exception as e:
                print(f"❌ Input error: {str(e)}")

    def get_valid_int(self, prompt, validator, error_msg):
        """Get validated integer input"""
        while True:
            try:
                user_input = input(prompt).strip()
                if not user_input.isdigit():
                    print("+-----------------------------------+")
                    print("| ❌ Please enter a valid number!   |")
                    print("+-----------------------------------+")
                    continue

                num = int(user_input)
                if validator(num):
                    return num
                else:
                    print("+-----------------------------------+")
                    print(f"| {error_msg}")
                    print("+-----------------------------------+")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user.")
                raise
            except ValueError:
                print("+-----------------------------------+")
                print("| ❌ Please enter a valid number!   |")
                print("+-----------------------------------+")
            except Exception as e:
                print(f"❌ Input error: {str(e)}")

    def get_valid_float(self, prompt, validator, error_msg):
        """Get validated float input"""
        while True:
            try:
                user_input = input(prompt).strip()
                try:
                    num = float(user_input)
                except ValueError:
                    print("+-----------------------------------+")
                    print("| ❌ Please enter a valid amount!   |")
                    print("+-----------------------------------+")
                    continue

                if validator(num):
                    return num
                else:
                    print("+-----------------------------------+")
                    print(f"| {error_msg}")
                    print("+-----------------------------------+")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user.")
                raise
            except Exception as e:
                print(f"❌ Input error: {str(e)}")

    def validate_email(self, email):
        """Validate Gmail email address"""
        return re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', email.lower())

    def validate_mobile(self, mobile):
        """Validate Indian mobile number (10 digits, starts with 6-9)"""
        return re.match(r'^[6-9]\d{9}$', mobile)

    def validate_amount(self, amount):
        """Validate positive amount"""
        try:
            return float(amount) > 0
        except:
            return False

    def validate_username(self, username):
        """Validate username (alphanumeric, 3-20 chars)"""
        return re.match(r'^[a-zA-Z0-9]{3,20}$', username)

    def validate_password(self, password):
        """Validate password (minimum 6 characters)"""
        return len(password) >= 6

    def validate_date(self, date_str):
        """Validate date in YYYY-MM-DD format"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def validate_admin_id(self, admin_id):
        """Validate admin ID (4 digits)"""
        return isinstance(admin_id, int) and 1000 <= admin_id <= 9999



    def sanitize_string(self, text):
        """Sanitize string input (remove extra spaces, special chars)"""
        if not text:
            return ""
        # Remove leading/trailing whitespace and multiple spaces
        return re.sub(r'\s+', ' ', text.strip())

    def validate_category(self, category, valid_categories):
        """Validate category against allowed list"""
        return category in valid_categories

    def validate_payment_mode(self, mode, valid_modes):
        """Validate payment mode"""
        return mode.upper() in valid_modes

    def format_currency(self, amount):
        """Format amount as currency"""
        try:
            return f"₹{float(amount):.2f}"
        except:
            return "₹0.00"

    def format_percentage(self, value):
        """Format value as percentage"""
        try:
            return f"{float(value):.1f}%"
        except:
            return "0.0%"

    def validate_month_year(self, month_year):
        """Validate month-year format (YYYY-MM)"""
        try:
            datetime.strptime(month_year + "-01", '%Y-%m-%d')
            return True
        except ValueError:
            return False
