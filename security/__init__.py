"""
DevSkyy Security Module
========================

Enterprise-grade security components:
- JWT/OAuth2 authentication
- AES-256-GCM encryption
- RBAC authorization
- Password management
"""

from .jwt_oauth2_auth import (
    # Config
    JWTConfig,
    UserRole,
    TokenType,
    TokenPayload,
    TokenResponse,
    UserCreate,
    UserInDB,
    
    # Classes
    PasswordManager,
    TokenManager,
    RoleChecker,
    
    # Instances
    password_manager,
    token_manager,
    oauth2_scheme,
    
    # Dependencies
    get_current_user,
    get_current_active_user,
    require_roles,
    
    # Router
    auth_router,
    
    # Utilities
    create_api_key,
    verify_api_key,
)

from .aes256_gcm_encryption import (
    # Config
    EncryptionConfig,
    
    # Classes
    KeyDerivation,
    AESGCMEncryption,
    FieldEncryption,
    EnvelopeEncryption,
    DataMasker,
    EncryptionMigration,
    
    # Instances
    encryption,
    field_encryption,
    envelope_encryption,
    key_derivation,
    data_masker,
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
