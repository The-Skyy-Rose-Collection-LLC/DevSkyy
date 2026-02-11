"""
DevSkyy Security Module
=======================

Enterprise-grade security with:
- AES-256-GCM encryption with unique salts
- JWT authentication (RFC 7519)
- Argon2 password hashing
"""

from devskyy.security.encryption import (
    EncryptionService,
    EncryptionConfig,
    EncryptionError,
    DecryptionError,
    EncryptionErrorCode,
)
from devskyy.security.auth import (
    SecurityManager,
    TokenPayload,
    AuthenticationError,
)

__all__ = [
    "EncryptionService",
    "EncryptionConfig",
    "EncryptionError",
    "DecryptionError",
    "EncryptionErrorCode",
    "SecurityManager",
    "TokenPayload",
    "AuthenticationError",
]
