"""
Services Package
All fintech services with unified AI agent
"""

# Core services
from .db import db
from .auth_service import auth_service
from .wallet_service import wallet_service
from .analytics_service import analytics_service
from .fraud_service import fraud_service
from .investment_service import investment_service

# Security
from .security_service import security_service

# AI Services (Unified)
from .unified_ai_agent import unified_ai_agent

# Keep for compatibility
from .enhanced_ai_assistant import enhanced_ai_assistant

__all__ = [
    'db',
    'auth_service',
    'wallet_service',
    'analytics_service',
    'fraud_service',
    'investment_service',
    'security_service',
    'unified_ai_agent',  # Main AI agent
    'enhanced_ai_assistant',  # Keep for compatibility
]
