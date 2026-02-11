"""
DevSkyy Encryption Service
==========================

Enterprise-grade AES-256-GCM encryption with:
- Unique random salts per encryption (NIST SP 800-38D compliant)
- Support for str, bytes, and dict inputs
- Stable JSON serialization for deterministic encryption
- Explicit error hierarchy
- Optional binary workflow support

Security References:
- NIST SP 800-38D: Galois/Counter Mode (GCM) and GMAC
- RFC 5116: Authenticated Encryption with Associated Data
"""

from __future__ import annotations

import json
import secrets
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionErrorCode(Enum):
    """Explicit error codes for encryption operations."""

    INVALID_INPUT_TYPE = "INVALID_INPUT_TYPE"
    SERIALIZATION_FAILED = "SERIALIZATION_FAILED"
    ENCRYPTION_FAILED = "ENCRYPTION_FAILED"
    DECRYPTION_FAILED = "DECRYPTION_FAILED"
    INVALID_CIPHERTEXT = "INVALID_CIPHERTEXT"
    KEY_DERIVATION_FAILED = "KEY_DERIVATION_FAILED"
    INTEGRITY_CHECK_FAILED = "INTEGRITY_CHECK_FAILED"


class EncryptionError(Exception):
    """Base exception for encryption operations."""

    def __init__(self, message: str, code: EncryptionErrorCode, details: Optional[str] = None):
        self.code = code
        self.details = details
        super().__init__(f"[{code.value}] {message}")


class DecryptionError(EncryptionError):
    """Exception for decryption failures."""

    pass


@dataclass(frozen=True)
class EncryptionConfig:
    """Immutable encryption configuration.

    Attributes:
        salt_length: Length of random salt in bytes (default: 16)
        nonce_length: Length of AES-GCM nonce in bytes (must be 12 per NIST)
        key_length: Derived key length in bytes (32 for AES-256)
        iterations: PBKDF2 iterations (100,000 minimum per OWASP)
    """

    salt_length: int = 16
    nonce_length: int = 12  # NIST recommended for GCM
    key_length: int = 32  # AES-256
    iterations: int = 100_000  # OWASP recommendation


class EncryptionService:
    """Enterprise-grade AES-256-GCM encryption service.

    Features:
    - Unique random salt per encryption (no static salts!)
    - Support for str, bytes, and dict inputs
    - Stable JSON serialization for dict inputs
    - decrypt() returns str by default
    - decrypt_bytes() for binary workflows

    Security Properties:
    - Confidentiality: AES-256 encryption
    - Integrity: GCM authentication tag
    - Key derivation: PBKDF2-HMAC-SHA256
    - Unique salts: Prevents rainbow table attacks

    Wire Format (hex-encoded):
        [salt:16][nonce:12][ciphertext:n][tag:16]

    Example:
        >>> svc = EncryptionService(master_key="my-secret-key")
        >>> encrypted = svc.encrypt("sensitive data")
        >>> decrypted = svc.decrypt(encrypted)
        >>> assert decrypted == "sensitive data"
    """

    def __init__(
        self,
        master_key: str,
        config: Optional[EncryptionConfig] = None,
    ) -> None:
        """Initialize encryption service.

        Args:
            master_key: Base key for PBKDF2 derivation. Should be at least 32 chars.
            config: Optional encryption configuration.

        Raises:
            ValueError: If master_key is too short (< 16 chars)
        """
        if len(master_key) < 16:
            raise ValueError("Master key must be at least 16 characters for security")

        self._master_key = master_key.encode("utf-8")
        self._config = config or EncryptionConfig()

    def _derive_key(self, salt: bytes) -> bytes:
        """Derive AES key from master key and salt using PBKDF2.

        Args:
            salt: Random salt bytes

        Returns:
            32-byte derived key for AES-256

        Raises:
            EncryptionError: If key derivation fails
        """
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self._config.key_length,
                salt=salt,
                iterations=self._config.iterations,
                backend=default_backend(),
            )
            return kdf.derive(self._master_key)
        except Exception as e:
            raise EncryptionError(
                "Key derivation failed",
                EncryptionErrorCode.KEY_DERIVATION_FAILED,
                str(e),
            )

    def _serialize_input(self, data: Union[str, bytes, dict]) -> bytes:
        """Serialize input data to bytes with stable JSON for dicts.

        Args:
            data: Input data (str, bytes, or dict)

        Returns:
            UTF-8 encoded bytes

        Raises:
            EncryptionError: If input type is invalid or serialization fails
        """
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode("utf-8")
        elif isinstance(data, dict):
            try:
                # Stable JSON serialization: sorted keys, no extra whitespace
                json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
                return json_str.encode("utf-8")
            except (TypeError, ValueError) as e:
                raise EncryptionError(
                    "Failed to serialize dict to JSON",
                    EncryptionErrorCode.SERIALIZATION_FAILED,
                    str(e),
                )
        else:
            raise EncryptionError(
                f"Unsupported input type: {type(data).__name__}. Must be str, bytes, or dict.",
                EncryptionErrorCode.INVALID_INPUT_TYPE,
            )

    def encrypt(self, data: Union[str, bytes, dict]) -> str:
        """Encrypt data using AES-256-GCM with unique salt.

        Args:
            data: Data to encrypt (str, bytes, or dict)

        Returns:
            Hex-encoded ciphertext in format: salt + nonce + ciphertext + tag

        Raises:
            EncryptionError: If encryption fails

        Example:
            >>> svc.encrypt("hello world")
            'a1b2c3...'  # hex string
            >>> svc.encrypt({"key": "value"})  # dict support
            'd4e5f6...'
        """
        # Generate unique random salt for this encryption
        salt = secrets.token_bytes(self._config.salt_length)

        # Derive key from salt
        key = self._derive_key(salt)

        # Generate unique nonce
        nonce = secrets.token_bytes(self._config.nonce_length)

        # Serialize input
        plaintext = self._serialize_input(data)

        try:
            # Encrypt with AES-256-GCM
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            # Pack: salt + nonce + ciphertext (includes auth tag)
            packed = salt + nonce + ciphertext
            return packed.hex()
        except Exception as e:
            raise EncryptionError(
                "Encryption failed",
                EncryptionErrorCode.ENCRYPTION_FAILED,
                str(e),
            )

    def decrypt(self, encrypted: str) -> str:
        """Decrypt hex-encoded ciphertext to string.

        Args:
            encrypted: Hex-encoded ciphertext from encrypt()

        Returns:
            Decrypted string (UTF-8 decoded)

        Raises:
            DecryptionError: If decryption fails or data is tampered

        Note:
            For binary data, use decrypt_bytes() instead.
        """
        plaintext_bytes = self.decrypt_bytes(encrypted)
        try:
            return plaintext_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise DecryptionError(
                "Decrypted data is not valid UTF-8. Use decrypt_bytes() for binary data.",
                EncryptionErrorCode.DECRYPTION_FAILED,
                str(e),
            )

    def decrypt_bytes(self, encrypted: str) -> bytes:
        """Decrypt hex-encoded ciphertext to bytes.

        Args:
            encrypted: Hex-encoded ciphertext from encrypt()

        Returns:
            Decrypted bytes

        Raises:
            DecryptionError: If decryption fails or integrity check fails
        """
        try:
            packed = bytes.fromhex(encrypted)
        except ValueError as e:
            raise DecryptionError(
                "Invalid hex encoding in ciphertext",
                EncryptionErrorCode.INVALID_CIPHERTEXT,
                str(e),
            )

        # Minimum size: salt + nonce + tag (no plaintext)
        min_size = self._config.salt_length + self._config.nonce_length + 16
        if len(packed) < min_size:
            raise DecryptionError(
                f"Ciphertext too short. Expected at least {min_size} bytes, got {len(packed)}",
                EncryptionErrorCode.INVALID_CIPHERTEXT,
            )

        # Unpack components
        salt = packed[: self._config.salt_length]
        nonce = packed[
            self._config.salt_length : self._config.salt_length + self._config.nonce_length
        ]
        ciphertext = packed[self._config.salt_length + self._config.nonce_length :]

        # Derive key from salt
        key = self._derive_key(salt)

        try:
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext
        except Exception as e:
            raise DecryptionError(
                "Decryption failed. Data may be corrupted or tampered.",
                EncryptionErrorCode.INTEGRITY_CHECK_FAILED,
                str(e),
            )

    def decrypt_dict(self, encrypted: str) -> dict:
        """Decrypt hex-encoded ciphertext to dict.

        Args:
            encrypted: Hex-encoded ciphertext of JSON dict

        Returns:
            Decrypted dict

        Raises:
            DecryptionError: If decryption fails or JSON is invalid
        """
        plaintext = self.decrypt(encrypted)
        try:
            return json.loads(plaintext)
        except json.JSONDecodeError as e:
            raise DecryptionError(
                "Decrypted data is not valid JSON",
                EncryptionErrorCode.DECRYPTION_FAILED,
                str(e),
            )

    def encrypt_deterministic(self, data: Union[str, bytes, dict], context: str) -> str:
        """Encrypt with deterministic output for same input + context.

        WARNING: Only use for searchable encryption where you understand the
        security implications. Deterministic encryption leaks equality.

        Args:
            data: Data to encrypt
            context: Context string used to derive salt deterministically

        Returns:
            Hex-encoded ciphertext (same output for same input+context)
        """
        import hashlib

        salt = hashlib.sha256(f"{context}:{self._master_key.decode()}".encode()).digest()[
            : self._config.salt_length
        ]
        nonce = hashlib.sha256(f"nonce:{context}:{self._master_key.decode()}".encode()).digest()[
            : self._config.nonce_length
        ]

        key = self._derive_key(salt)
        plaintext = self._serialize_input(data)

        try:
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            packed = salt + nonce + ciphertext
            return packed.hex()
        except Exception as e:
            raise EncryptionError(
                "Deterministic encryption failed",
                EncryptionErrorCode.ENCRYPTION_FAILED,
                str(e),
            )
