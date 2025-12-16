"""
DevSkyy Security Module
=======================

Enterprise-grade security components.

Components:
- AES-256-GCM Encryption (NIST SP 800-38D compliant)
- JWT/OAuth2 Authentication (RFC 7519 compliant)
- Password Hashing (Argon2id - OWASP recommended)
- Field-level encryption for PII/PCI
- Key rotation support

Security Standards:
- NIST SP 800-38D: GCM Mode Specification
- NIST SP 800-132: Password-Based Key Derivation
- RFC 7519: JSON Web Token (JWT)
- OWASP Password Storage Cheat Sheet
"""

from .aes256_gcm_encryption import (
    AESGCMEncryption,
    DataMasker,
    DecryptionError,
    EncryptionConfig,
    EncryptionError,
    FieldEncryption,
    KeyDerivation,
    KeyVersion,
    data_masker,
    encryption,
    field_encryption,
)
from .aes256_gcm_encryption import (
    KeyError as EncryptionKeyError,  # Config; Classes; Exceptions; Instances
)
from .jwt_oauth2_auth import (  # Config; Enums; Models; Classes; Dependencies; Instances
    JWTConfig,
    JWTManager,
    PasswordManager,
    RateLimiter,
    TokenBlacklist,
    TokenPayload,
    TokenResponse,
    TokenType,
    UserCreate,
    UserInDB,
    UserRole,
    get_current_user,
    jwt_manager,
    password_manager,
    require_roles,
    token_blacklist,
)

__all__ = [
    # Encryption
    "EncryptionConfig",
    "KeyVersion",
    "KeyDerivation",
    "AESGCMEncryption",
    "FieldEncryption",
    "DataMasker",
    "EncryptionError",
    "DecryptionError",
    "EncryptionKeyError",
    "encryption",
    "field_encryption",
    "data_masker",
    # JWT/OAuth2
    "JWTConfig",
    "UserRole",
    "TokenType",
    "TokenPayload",
    "TokenResponse",
    "UserCreate",
    "UserInDB",
    "PasswordManager",
    "JWTManager",
    "TokenBlacklist",
    "RateLimiter",
    "get_current_user",
    "require_roles",
    "jwt_manager",
    "password_manager",
    "token_blacklist",
]
