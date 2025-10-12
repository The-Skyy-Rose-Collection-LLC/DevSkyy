"""
Security Module
Enterprise-grade security implementation for DevSkyy platform

This module provides:
- Enterprise security management
- FastAPI security configuration
- Input validation and sanitization
- Rate limiting and DDoS protection
- Encryption and secrets management
- Security monitoring and alerting
- Compliance controls (SOC2, GDPR, PCI)
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .enterprise_security import (
        ComplianceManager,
        EnterpriseSecurityManager,
        InputValidator,
        SecurityHeaders,
        create_enterprise_security,
        create_rate_limiter,
        secure_endpoint,
    )
    from .fastapi_security_config import SecurityConfig, setup_security_middleware

__all__ = [
    "EnterpriseSecurityManager",
    "SecurityHeaders",
    "secure_endpoint",
    "create_rate_limiter",
    "InputValidator",
    "ComplianceManager",
    "create_enterprise_security",
    "SecurityConfig",
    "setup_security_middleware",
]

__version__ = "2.0.0"
