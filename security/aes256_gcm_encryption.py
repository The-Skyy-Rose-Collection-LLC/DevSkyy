"""
AES-256-GCM Authenticated Encryption
====================================

Production-grade encryption following NIST guidelines.

Standards:
- NIST SP 800-38D: GCM Mode Specification
- NIST SP 800-132: Password-Based Key Derivation
- NIST SP 800-57: Key Management Guidelines

Features:
- AES-256-GCM with 128-bit authentication tag
- PBKDF2-HMAC-SHA256 key derivation (600,000 iterations)
- Unique 96-bit IV per encryption (NIST recommended)
- Key versioning for rotation
- Field-level encryption for PII/PCI
- Data masking for logs

Security Properties:
- Confidentiality: AES-256 encryption
- Integrity: GMAC authentication
- Authenticity: AAD binding

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import secrets
from dataclasses import dataclass
from enum import Enum
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================


class EncryptionError(Exception):
    """Base exception for encryption errors."""

    pass


class DecryptionError(EncryptionError):
    """Raised when decryption fails."""

    pass


class KeyError(EncryptionError):
    """Raised when key operations fail."""

    pass


# =============================================================================
# Configuration
# =============================================================================


@dataclass(frozen=True)
class EncryptionConfig:
    """
    Immutable encryption configuration following NIST guidelines.

    References:
    - NIST SP 800-38D Section 5.2.1.1: 96-bit IV recommended
    - NIST SP 800-38D Section 5.2.1.2: 128-bit auth tag recommended
    - NIST SP 800-132: 10,000+ iterations for PBKDF2
    - OWASP 2023: 600,000+ iterations recommended
    """

    # AES-256 requires 256-bit (32 byte) key
    key_length_bytes: int = 32  # 256 bits

    # NIST recommends 96-bit (12 byte) IV for GCM
    iv_length_bytes: int = 12

    # Authentication tag length (128 bits for maximum security)
    tag_length_bytes: int = 16  # 128 bits

    # PBKDF2 iterations (OWASP 2023: 600,000+)
    pbkdf2_iterations: int = 600_000

    # Salt length for key derivation
    salt_length_bytes: int = 32

    # Additional authenticated data (AAD) for context binding
    default_aad: bytes = b"devskyy-platform-v3"


class KeyVersion(str, Enum):
    """Key versions for rotation tracking."""

    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


# =============================================================================
# Secure Key Derivation
# =============================================================================


class KeyDerivation:
    """
    Key derivation using PBKDF2-HMAC-SHA256.

    Reference: NIST SP 800-132
    """

    def __init__(self, config: EncryptionConfig | None = None) -> None:
        self.config = config or EncryptionConfig()

    def derive_key(
        self,
        password: str,
        salt: bytes | None = None,
        iterations: int | None = None,
    ) -> tuple[bytes, bytes]:
        """
        Derive encryption key from password.

        Args:
            password: User password or master key phrase
            salt: Optional salt (generated if not provided)
            iterations: Optional iteration count

        Returns:
            Tuple of (derived_key, salt)

        Raises:
            KeyError: If key derivation fails
        """
        if not password:
            raise KeyError("Password cannot be empty")

        if salt is None:
            salt = secrets.token_bytes(self.config.salt_length_bytes)

        iterations = iterations or self.config.pbkdf2_iterations

        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.config.key_length_bytes,
                salt=salt,
                iterations=iterations,
                backend=default_backend(),
            )

            key = kdf.derive(password.encode("utf-8"))
            return key, salt
        except Exception as e:
            raise KeyError(f"Key derivation failed: {e}") from e

    def generate_random_key(self) -> bytes:
        """Generate cryptographically secure random key."""
        return secrets.token_bytes(self.config.key_length_bytes)

    def verify_key_strength(self, key: bytes) -> bool:
        """Verify key meets minimum strength requirements."""
        return len(key) >= self.config.key_length_bytes


# =============================================================================
# AES-256-GCM Encryption
# =============================================================================


class AESGCMEncryption:
    """
    AES-256-GCM Authenticated Encryption.

    GCM provides both confidentiality and authenticity:
    - Encryption: AES-256 in Counter mode
    - Authentication: GMAC for integrity verification

    Reference: NIST SP 800-38D

    Usage:
        enc = AESGCMEncryption()

        # Encrypt
        ciphertext = enc.encrypt("sensitive data")

        # Decrypt
        plaintext = enc.decrypt_to_string(ciphertext)

        # With custom AAD
        ciphertext = enc.encrypt("data", aad=b"user:123")
    """

    def __init__(self, config: EncryptionConfig | None = None) -> None:
        self.config = config or EncryptionConfig()
        self._key_versions: dict[str, bytes] = {}
        self._current_version: str = KeyVersion.V1.value

        # Load master key from environment
        self._initialize_master_key()

    def _initialize_master_key(self) -> None:
        """Initialize master key from environment or generate ephemeral."""
        master_key_b64 = os.getenv("ENCRYPTION_MASTER_KEY")

        if master_key_b64:
            try:
                self._master_key = base64.b64decode(master_key_b64)
                if len(self._master_key) != self.config.key_length_bytes:
                    raise ValueError(
                        f"Key must be {self.config.key_length_bytes} bytes, "
                        f"got {len(self._master_key)}"
                    )
                logger.info("Master encryption key loaded from environment")
            except Exception as e:
                logger.error(f"Invalid master key format: {e}")
                raise EncryptionError("Invalid ENCRYPTION_MASTER_KEY format") from e
        else:
            logger.warning(
                "ENCRYPTION_MASTER_KEY not set. "
                "Generating ephemeral key - data will be lost on restart. "
                "Set ENCRYPTION_MASTER_KEY for production."
            )
            self._master_key = secrets.token_bytes(self.config.key_length_bytes)

        self._key_versions[self._current_version] = self._master_key

    def encrypt(
        self,
        plaintext: str | bytes | dict[str, Any],
        aad: bytes | None = None,
        key: bytes | None = None,
    ) -> str:
        """
        Encrypt data with AES-256-GCM.

        Args:
            plaintext: Data to encrypt (string, bytes, or dict)
            aad: Additional authenticated data (optional)
            key: Encryption key (uses master key if not provided)

        Returns:
            Base64-encoded encrypted data with format: version:iv:ciphertext

        Raises:
            EncryptionError: If encryption fails
        """
        # Convert input to bytes
        if isinstance(plaintext, dict):
            # Stable JSON serialization for deterministic encryption
            plaintext = json.dumps(plaintext, sort_keys=True, separators=(",", ":"))

        plaintext_bytes = plaintext.encode("utf-8") if isinstance(plaintext, str) else plaintext

        # Use provided key or current version key
        key = key or self._key_versions.get(self._current_version, self._master_key)

        # Validate key length
        if len(key) != self.config.key_length_bytes:
            raise EncryptionError(f"Key must be {self.config.key_length_bytes} bytes")

        # Use default AAD if not provided
        aad = aad or self.config.default_aad

        # Generate random IV (NIST: must be unique for each encryption)
        iv = secrets.token_bytes(self.config.iv_length_bytes)

        try:
            # Create cipher
            aesgcm = AESGCM(key)

            # Encrypt (ciphertext includes auth tag)
            ciphertext = aesgcm.encrypt(iv, plaintext_bytes, aad)

            # Format: version:iv:ciphertext (all base64 encoded)
            result = (
                f"{self._current_version}:"
                f"{base64.b64encode(iv).decode()}:"
                f"{base64.b64encode(ciphertext).decode()}"
            )

            return result
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}") from e

    def decrypt(
        self,
        encrypted_data: str,
        aad: bytes | None = None,
        key: bytes | None = None,
    ) -> bytes:
        """
        Decrypt data encrypted with AES-256-GCM.

        Args:
            encrypted_data: Base64-encoded encrypted data
            aad: Additional authenticated data (must match encryption)
            key: Decryption key (uses versioned key if not provided)

        Returns:
            Decrypted bytes

        Raises:
            DecryptionError: If decryption or authentication fails
        """
        # Parse encrypted data
        parts = encrypted_data.split(":")
        if len(parts) != 3:
            raise DecryptionError("Invalid encrypted data format. Expected version:iv:ciphertext")

        version, iv_b64, ciphertext_b64 = parts

        try:
            # Decode components
            iv = base64.b64decode(iv_b64)
            ciphertext = base64.b64decode(ciphertext_b64)
        except Exception as e:
            raise DecryptionError(f"Invalid base64 encoding: {e}") from e

        # Validate IV length
        if len(iv) != self.config.iv_length_bytes:
            raise DecryptionError(
                f"Invalid IV length: expected {self.config.iv_length_bytes}, got {len(iv)}"
            )

        # Get key for version
        if key is None:
            if version not in self._key_versions:
                raise DecryptionError(f"Unknown key version: {version}")
            key = self._key_versions[version]

        # Use default AAD if not provided
        aad = aad or self.config.default_aad

        try:
            # Create cipher and decrypt
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(iv, ciphertext, aad)
            return plaintext
        except InvalidTag:
            logger.error(
                "Decryption failed: authentication tag mismatch. "
                "Data may have been tampered with."
            )
            raise DecryptionError("Authentication failed - data may be corrupted")
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e}") from e

    def decrypt_to_string(
        self,
        encrypted_data: str,
        aad: bytes | None = None,
    ) -> str:
        """Decrypt and return as UTF-8 string."""
        return self.decrypt(encrypted_data, aad).decode("utf-8")

    def decrypt_to_dict(
        self,
        encrypted_data: str,
        aad: bytes | None = None,
    ) -> dict[str, Any]:
        """Decrypt and return as dictionary."""
        plaintext = self.decrypt_to_string(encrypted_data, aad)
        return json.loads(plaintext)

    def rotate_key(self, new_key: bytes | None = None) -> str:
        """
        Rotate encryption key.

        Args:
            new_key: New key (generated if not provided)

        Returns:
            New version identifier
        """
        if new_key is None:
            new_key = secrets.token_bytes(self.config.key_length_bytes)
        elif len(new_key) != self.config.key_length_bytes:
            raise KeyError(f"Key must be {self.config.key_length_bytes} bytes")

        # Determine new version
        version_num = len(self._key_versions) + 1
        new_version = f"v{version_num}"

        # Store new key
        self._key_versions[new_version] = new_key
        self._current_version = new_version

        logger.info(f"Key rotated to version {new_version}")
        return new_version

    def re_encrypt_with_current_key(
        self,
        encrypted_data: str,
        aad: bytes | None = None,
    ) -> str:
        """Re-encrypt data with current key version."""
        plaintext = self.decrypt(encrypted_data, aad)
        return self.encrypt(plaintext, aad)


# =============================================================================
# Field-Level Encryption
# =============================================================================


class FieldEncryption:
    """
    Field-level encryption for sensitive data (PII, PCI).

    Use Cases:
    - Encrypt specific database columns
    - Protect PII in logs
    - Secure API responses

    Usage:
        fe = FieldEncryption()

        # Encrypt single field
        encrypted = fe.encrypt_field("ssn", "123-45-6789", context="user:123")

        # Encrypt sensitive fields in dict
        encrypted_dict = fe.encrypt_dict({"name": "John", "ssn": "123-45-6789"})
    """

    # Fields that should always be encrypted (case-insensitive)
    SENSITIVE_FIELDS: set[str] = {
        "ssn",
        "social_security_number",
        "credit_card",
        "card_number",
        "cvv",
        "password",
        "secret",
        "api_key",
        "token",
        "date_of_birth",
        "dob",
        "bank_account",
        "routing_number",
        "drivers_license",
        "passport_number",
        "phone",
        "phone_number",
        "address",
        "street_address",
        "email",
    }

    def __init__(self, encryption: AESGCMEncryption | None = None) -> None:
        self.encryption = encryption or AESGCMEncryption()

    def encrypt_field(
        self,
        field_name: str,
        value: str,
        context: str | None = None,
    ) -> str:
        """
        Encrypt a single field with context binding.

        Args:
            field_name: Name of the field (used in AAD)
            value: Value to encrypt
            context: Additional context (e.g., user_id)

        Returns:
            Encrypted value
        """
        # Build AAD with field name and optional context
        aad = f"field:{field_name.lower()}"
        if context:
            aad += f":ctx:{context}"

        return self.encryption.encrypt(value, aad.encode())

    def decrypt_field(
        self,
        field_name: str,
        encrypted_value: str,
        context: str | None = None,
    ) -> str:
        """Decrypt a field with context verification."""
        aad = f"field:{field_name.lower()}"
        if context:
            aad += f":ctx:{context}"

        return self.encryption.decrypt_to_string(encrypted_value, aad.encode())

    def is_sensitive_field(self, field_name: str) -> bool:
        """Check if field name indicates sensitive data."""
        return field_name.lower() in self.SENSITIVE_FIELDS

    def encrypt_dict(
        self,
        data: dict[str, Any],
        fields_to_encrypt: set[str] | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        """
        Encrypt sensitive fields in a dictionary.

        Args:
            data: Dictionary with potentially sensitive data
            fields_to_encrypt: Fields to encrypt (uses SENSITIVE_FIELDS if not provided)
            context: Additional context for AAD

        Returns:
            Dictionary with sensitive fields encrypted
        """
        fields = fields_to_encrypt or self.SENSITIVE_FIELDS
        result = {}

        for key, value in data.items():
            if key.lower() in fields and isinstance(value, str) and value:
                result[key] = self.encrypt_field(key, value, context)
            elif isinstance(value, dict):
                result[key] = self.encrypt_dict(value, fields, context)
            else:
                result[key] = value

        return result

    def decrypt_dict(
        self,
        data: dict[str, Any],
        fields_to_decrypt: set[str] | None = None,
        context: str | None = None,
    ) -> dict[str, Any]:
        """Decrypt sensitive fields in a dictionary."""
        fields = fields_to_decrypt or self.SENSITIVE_FIELDS
        result = {}

        for key, value in data.items():
            if key.lower() in fields and isinstance(value, str) and value and ":" in value:
                try:
                    result[key] = self.decrypt_field(key, value, context)
                except DecryptionError:
                    # Leave encrypted if decryption fails
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self.decrypt_dict(value, fields, context)
            else:
                result[key] = value

        return result


# =============================================================================
# Data Masking
# =============================================================================


class DataMasker:
    """
    Data masking for logs and debugging.

    Masks sensitive data patterns without encryption.
    """

    # Regex patterns for sensitive data
    PATTERNS = {
        "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
        "ssn": re.compile(r"\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b"),
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone": re.compile(r"\b\+?1?[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b"),
        "api_key": re.compile(r"\b[A-Za-z0-9_-]{32,}\b"),
    }

    def mask_string(self, text: str, mask_char: str = "*") -> str:
        """Mask sensitive patterns in a string."""
        result = text

        for pattern_name, pattern in self.PATTERNS.items():
            # Capture pattern_name in closure to avoid B023
            def make_replacer(pname: str):
                return lambda m: self._mask_match(m.group(), mask_char, pname)

            result = pattern.sub(make_replacer(pattern_name), result)

        return result

    def _mask_match(self, value: str, mask_char: str, pattern_type: str) -> str:
        """Mask a matched pattern, preserving some characters for identification."""
        length = len(value)

        if pattern_type == "email":
            # Mask email but show domain
            parts = value.split("@")
            if len(parts) == 2:
                return f"{mask_char * 3}***@{parts[1]}"

        if pattern_type == "credit_card":
            # Show last 4 digits
            clean = value.replace(" ", "").replace("-", "")
            return f"{mask_char * 12}{clean[-4:]}"

        if length <= 4:
            return mask_char * length

        # Show first and last character
        return value[0] + mask_char * (length - 2) + value[-1]

    def mask_email(self, email: str, mask_char: str = "*") -> str:
        """Mask an email address, preserving the domain."""
        if not email or "@" not in email:
            return mask_char * len(email) if email else ""
        parts = email.split("@")
        if len(parts) == 2:
            return f"{mask_char * 3}***@{parts[1]}"
        return self.mask_string(email, mask_char)

    def mask_phone(self, phone: str, mask_char: str = "*") -> str:
        """Mask a phone number, preserving the last 4 digits."""
        if not phone:
            return ""
        # Remove non-digit characters for processing
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) >= 4:
            return f"{mask_char * (len(digits) - 4)}{digits[-4:]}"
        return mask_char * len(phone)

    def mask_dict(
        self,
        data: dict[str, Any],
        sensitive_keys: set[str] | None = None,
    ) -> dict[str, Any]:
        """Mask sensitive fields in a dictionary."""
        sensitive = sensitive_keys or FieldEncryption.SENSITIVE_FIELDS
        result = {}

        for key, value in data.items():
            if key.lower() in sensitive:
                if isinstance(value, str):
                    result[key] = self.mask_string(value)
                else:
                    result[key] = "[MASKED]"
            elif isinstance(value, dict):
                result[key] = self.mask_dict(value, sensitive)
            elif isinstance(value, str):
                result[key] = self.mask_string(value)
            else:
                result[key] = value

        return result


# =============================================================================
# Module-level Instances
# =============================================================================

# Default instances for convenience
encryption = AESGCMEncryption()
field_encryption = FieldEncryption(encryption)
data_masker = DataMasker()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Config
    "EncryptionConfig",
    "KeyVersion",
    # Classes
    "KeyDerivation",
    "AESGCMEncryption",
    "FieldEncryption",
    "DataMasker",
    # Exceptions
    "EncryptionError",
    "DecryptionError",
    "KeyError",
    # Instances
    "encryption",
    "field_encryption",
    "data_masker",
]
