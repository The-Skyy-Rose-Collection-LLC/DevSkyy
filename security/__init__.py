"""
DevSkyy Security Module
========================

Enterprise-grade security components:
- JWT/OAuth2 authentication
- AES-256-GCM encryption
- RBAC authorization
- Password management
"""

from .aes256_gcm_encryption import (  # Config; Classes; Instances
    AESGCMEncryption,
    DataMasker,
    EncryptionConfig,
    EncryptionMigration,
    EnvelopeEncryption,
    FieldEncryption,
    KeyDerivation,
    data_masker,
    encryption,
    envelope_encryption,
    field_encryption,
    key_derivation,
)
from .jwt_oauth2_auth import (  # Config; Classes; Instances; Dependencies; Router; Utilities
    JWTConfig,
    PasswordManager,
    RoleChecker,
    TokenManager,
    TokenPayload,
    TokenResponse,
    TokenType,
    UserCreate,
    UserInDB,
    UserRole,
    auth_router,
    create_api_key,
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
    password_manager,
    require_roles,
    token_manager,
    verify_api_key,
)

__all__ = [
    # JWT/OAuth2
    "JWTConfig",
    "UserRole",
    "TokenType",
    "TokenPayload",
    "TokenResponse",
    "UserCreate",
    "UserInDB",
    "PasswordManager",
    "TokenManager",
    "RoleChecker",
    "password_manager",
    "token_manager",
    "oauth2_scheme",
    "get_current_user",
    "get_current_active_user",
    "require_roles",
    "auth_router",
    "create_api_key",
    "verify_api_key",
    # Encryption
    "EncryptionConfig",
    "KeyDerivation",
    "AESGCMEncryption",
    "FieldEncryption",
    "EnvelopeEncryption",
    "DataMasker",
    "EncryptionMigration",
    "encryption",
    "field_encryption",
    "envelope_encryption",
    "key_derivation",
    "data_masker",
]
