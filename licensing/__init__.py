"""
DevSkyy Enterprise Licensing System

Production-grade software licensing with cryptographic validation and feature gating.

Standards Compliance:
- RFC 4122: UUID generation for license keys
- RFC 7519: JWT for license tokens
- ISO 8601: Date/time formats
- NIST SP 800-90Ar1: Cryptographically secure random generation

Features:
- Multiple license tiers (Trial, Professional, Enterprise, Custom)
- Time-based and perpetual licenses
- Hardware binding and domain restrictions
- Feature gating and usage limits
- License activation/deactivation
- Concurrent user management
- Automated expiration handling
- Audit logging

References:
- RFC 4122: https://www.rfc-editor.org/rfc/rfc4122
- RFC 7519: https://www.rfc-editor.org/rfc/rfc7519
"""

from licensing.license_manager import LicenseManager
from licensing.license_tiers import LicenseTier, LicenseType
from licensing.models import License, LicenseActivation, LicenseUsageRecord

__all__ = [
    "LicenseManager",
    "LicenseTier",
    "LicenseType",
    "License",
    "LicenseActivation",
    "LicenseUsageRecord",
]

__version__ = "1.0.0"
