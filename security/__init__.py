"""
DevSkyy Security Package

Enterprise-grade security implementation following Truth Protocol standards:
- JWT authentication (RFC 7519 compliant)
- AES-256-GCM encryption (NIST SP 800-38D)
- RBAC with 5-tier role system
- Input validation with Pydantic
- GDPR compliance utilities
- XXE protection via defusedxml

Modules:
    jwt_auth: JWT token generation, validation, and refresh
    encryption: AES-256-GCM encryption for sensitive data
    rbac: Role-based access control with 5-tier roles
    input_validation: Pydantic-based input sanitization
    gdpr_compliance: GDPR data handling utilities
    defused_xml_config: XXE attack prevention
    secure_headers: Security header middleware
    log_sanitizer: PII redaction for logs

Security Standards:
    - RFC 7519: JWT implementation
    - NIST SP 800-38D: AES-GCM encryption
    - NIST SP 800-132: PBKDF2 password hashing
    - OWASP Top 10: Addressed in input validation

Example:
    from security import JWTManager, EncryptionManager

    # JWT authentication
    jwt = JWTManager()
    token = jwt.create_access_token(user_id="123", roles=["admin"])

    # Data encryption
    enc = EncryptionManager()
    encrypted = enc.encrypt("sensitive data")
"""

__version__ = "1.0.0"

__all__ = [
    "JWTManager",
    "EncryptionManager",
    "GDPRManager",
    "validation_middleware",
]


def __getattr__(name: str):
    """
    Lazy import of security modules for performance.

    Args:
        name: The attribute name to import.

    Returns:
        The requested module or class.

    Raises:
        AttributeError: If the attribute is not found.
    """
    if name == "JWTManager":
        from security.jwt_auth import JWTManager
        return JWTManager
    elif name == "EncryptionManager":
        from security.encryption import EncryptionManager
        return EncryptionManager
    elif name == "GDPRManager":
        from security.gdpr_compliance import GDPRManager
        return GDPRManager
    elif name == "validation_middleware":
        from security.input_validation import validation_middleware
        return validation_middleware
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
