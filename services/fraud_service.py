"""
Fraud Detection Service
Real-time fraud detection and alerting
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from database.db import db


class FraudService:
    """Fraud detection and monitoring service"""
    
    def __init__(self):
        self.rules = None
        self._load_rules()
    
    def _load_rules(self):
        """Load fraud detection rules from database"""
        self.rules = db.get_fraud_rules(active_only=True)
    
    def check_transaction(
        self,
        user_id: int,
        amount: int,
        txn_type: str,
        reference_type: str = None,
        reference_id: int = None
    ) -> List[Dict]:
        """
        Check a transaction against all fraud rules.
        Returns list of triggered alerts.
        """
        alerts = []
        
        for rule in self.rules:
            alert = self._check_rule(user_id, amount, txn_type, rule)
            if alert:
                # Save to database
                flag_id = db.add_fraud_flag(
                    user_id=user_id,
                    rule_name=rule['rule_name'],
                    severity=rule['severity'],
                    description=alert['description'],
                    reference_type=reference_type,
                    reference_id=reference_id,
                    amount=amount
                )
                
                alert['flag_id'] = flag_id
                alerts.append(alert)
                
                # Notify user if high severity
                if rule['severity'] in ['HIGH', 'CRITICAL']:
                    db.add_notification(
                        user_id,
                        f"Security Alert: {rule['rule_name']}",
                        alert['description'],
                        "WARNING",
                        "security"
                    )
        
        return alerts
    
    def _check_rule(
        self,
        user_id: int,
        amount: int,
        txn_type: str,
        rule: Dict
    ) -> Optional[Dict]:
        """Check a single rule against transaction"""
        
        rule_type = rule['rule_type']
        threshold = rule['threshold_value']
        threshold_type = rule['threshold_type']
        
        # Large transaction check
        if rule_type == 'AMOUNT' and threshold_type == 'ABSOLUTE':
            if amount >= db.to_paise(threshold):
                return {
                    'rule': rule['rule_name'],
                    'severity': rule['severity'],
                    'description': f"Large transaction of ₹{db.to_rupees(amount):,.2f} detected"
                }
        
        # Unusual amount (multiplier of average)
        elif rule_type == 'AMOUNT' and threshold_type == 'MULTIPLIER':
            avg = self._get_user_average_transaction(user_id)
            if avg > 0 and amount > avg * threshold:
                return {
                    'rule': rule['rule_name'],
                    'severity': rule['severity'],
                    'description': f"Transaction is {amount/avg:.1f}x above your average"
                }
        
        # Rapid transactions
        elif rule_type == 'FREQUENCY' and threshold_type == 'COUNT_PER_HOUR':
            count = self._get_recent_transaction_count(user_id, hours=1)
            if count >= threshold:
                return {
                    'rule': rule['rule_name'],
                    'severity': rule['severity'],
                    'description': f"Unusual activity: {count} transactions in the last hour"
                }
        
        # Multiple transfers per day
        elif rule_type == 'TRANSFER' and threshold_type == 'COUNT_PER_DAY':
            if txn_type == 'transfer':
                count = self._get_daily_transfer_count(user_id)
                if count >= threshold:
                    return {
                        'rule': rule['rule_name'],
                        'severity': rule['severity'],
                        'description': f"Multiple transfers detected: {count} today"
                    }
        
        # New account large transfer
        elif rule_type == 'TRANSFER' and threshold_type == 'NEW_ACCOUNT':
            if txn_type == 'transfer' and amount >= db.to_paise(threshold):
                if self._is_new_account(user_id):
                    return {
                        'rule': rule['rule_name'],
                        'severity': rule['severity'],
                        'description': f"Large transfer from newly created account"
                    }
        
        return None
    
    def _get_user_average_transaction(self, user_id: int) -> float:
        """Get average transaction amount for user"""
        result = db.execute_one(
            "SELECT AVG(amount) as avg FROM expenses WHERE user_id = ?",
            (user_id,)
        )
        return result['avg'] if result and result['avg'] else 0
    
    def _get_recent_transaction_count(self, user_id: int, hours: int = 1) -> int:
        """Get count of transactions in last N hours"""
        result = db.execute_one(
            """SELECT COUNT(*) as count FROM (
                   SELECT 1 FROM expenses WHERE user_id = ? AND datetime(date) >= datetime('now', ? || ' hours')
                   UNION ALL
                   SELECT 1 FROM income WHERE user_id = ? AND datetime(date) >= datetime('now', ? || ' hours')
               )""",
            (user_id, f"-{hours}", user_id, f"-{hours}")
        )
        return result['count'] if result else 0
    
    def _get_daily_transfer_count(self, user_id: int) -> int:
        """Get count of transfers today"""
        result = db.execute_one(
            """SELECT COUNT(*) as count FROM transfers 
               WHERE sender_id = ? AND date(date) = date('now')""",
            (user_id,)
        )
        return result['count'] if result else 0
    
    def _is_new_account(self, user_id: int, hours: int = 24) -> bool:
        """Check if account was created within last N hours"""
        result = db.execute_one(
            """SELECT 1 FROM users 
               WHERE user_id = ? AND datetime(created_at) >= datetime('now', ? || ' hours')""",
            (user_id, f"-{hours}")
        )
        return result is not None
    
    def get_user_risk_score(self, user_id: int) -> Dict:
        """Calculate risk score for a user"""
        score = 0
        factors = []
        
        # Check pending fraud flags
        pending_flags = db.execute(
            "SELECT COUNT(*) as count, MAX(severity) as max_severity FROM fraud_flags WHERE user_id = ? AND status = 'PENDING'",
            (user_id,),
            fetch=True
        )
        
        if pending_flags and pending_flags[0]['count'] > 0:
            count = pending_flags[0]['count']
            max_sev = pending_flags[0]['max_severity']
            
            severity_scores = {'LOW': 5, 'MEDIUM': 15, 'HIGH': 30, 'CRITICAL': 50}
            score += severity_scores.get(max_sev, 10) * min(count, 3)
            factors.append(f"{count} pending fraud alerts")
        
        # Check login failures
        failures = db.execute_one(
            """SELECT COUNT(*) as count FROM login_attempts 
               WHERE email = (SELECT email FROM users WHERE user_id = ?)
               AND success = 0 AND datetime(attempt_time) >= datetime('now', '-7 days')""",
            (user_id,)
        )
        
        if failures and failures['count'] > 3:
            score += min(failures['count'] * 5, 25)
            factors.append(f"{failures['count']} failed login attempts")
        
        # Check unusual spending pattern
        avg_spending = self._get_user_average_transaction(user_id)
        recent_max = db.execute_one(
            "SELECT MAX(amount) as max FROM expenses WHERE user_id = ? AND date >= date('now', '-7 days')",
            (user_id,)
        )
        
        if recent_max and recent_max['max'] and avg_spending > 0:
            if recent_max['max'] > avg_spending * 5:
                score += 20
                factors.append("Unusual high-value transaction")
        
        # Determine risk level
        if score >= 70:
            risk_level = 'HIGH'
        elif score >= 40:
            risk_level = 'MEDIUM'
        elif score >= 20:
            risk_level = 'LOW'
        else:
            risk_level = 'MINIMAL'
        
        return {
            'score': min(score, 100),
            'level': risk_level,
            'factors': factors
        }
    
    def get_platform_risk_summary(self) -> Dict:
        """Get platform-wide risk summary"""
        # Pending alerts by severity
        alerts = db.execute(
            """SELECT severity, COUNT(*) as count 
               FROM fraud_flags WHERE status = 'PENDING'
               GROUP BY severity""",
            fetch=True
        )
        
        alert_summary = {a['severity']: a['count'] for a in alerts} if alerts else {}
        
        # High-risk users
        high_risk_users = db.execute(
            """SELECT DISTINCT user_id FROM fraud_flags 
               WHERE status = 'PENDING' AND severity IN ('HIGH', 'CRITICAL')""",
            fetch=True
        )
        
        # Recent suspicious activity
        recent_flags = db.execute(
            """SELECT ff.*, u.username 
               FROM fraud_flags ff
               JOIN users u ON ff.user_id = u.user_id
               WHERE ff.created_at >= datetime('now', '-24 hours')
               ORDER BY ff.created_at DESC LIMIT 10""",
            fetch=True
        )
        
        return {
            'pending_by_severity': alert_summary,
            'high_risk_user_count': len(high_risk_users) if high_risk_users else 0,
            'recent_flags': recent_flags or [],
            'total_pending': sum(alert_summary.values())
        }


# Singleton instance
fraud_service = FraudService()
