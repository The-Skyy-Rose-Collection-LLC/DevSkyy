"""
Enterprise-Grade Encryption System
AES-256-GCM encryption replacing XOR cipher per NIST SP 800-38D
Includes key derivation (NIST SP 800-132), secure random generation, and encryption helpers

Standards Compliance:
- NIST SP 800-38D: Recommendation for Block Cipher Modes of Operation: GCM and GMAC
  - AES-256-GCM for authenticated encryption
  - 96-bit (12-byte) IV per NIST recommendations
  - 128-bit (16-byte) authentication tag

- NIST SP 800-132: Recommendation for Password-Based Key Derivation
  - PBKDF2-HMAC-SHA256 for key derivation
  - Minimum 100,000 iterations per OWASP 2023 recommendations
  - 32-byte (256-bit) salt for cryptographic operations

- NIST SP 800-90Ar1: Recommendation for Random Number Generation
  - secrets module for CSPRNG (cryptographically secure pseudo-random number generator)

Reference: https://csrc.nist.gov/publications/detail/sp/800-38d/final
Reference: https://csrc.nist.gov/publications/detail/sp/800-132/final
"""

import base64
import hashlib
import logging
import os
import secrets
from typing import Any, Dict, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

# ============================================================================
# CRYPTOGRAPHIC CONSTANTS - Per NIST & OWASP Standards
# ============================================================================

# NIST SP 800-132 & OWASP 2023 Password Storage Cheat Sheet
# https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
PBKDF2_ITERATIONS = 100000  # Minimum recommended by OWASP 2023
PBKDF2_ALGORITHM = "sha256"  # HMAC-SHA256 per NIST SP 800-132

# NIST SP 800-38D: GCM Mode requirements
AES_KEY_SIZE = 32  # 256 bits for AES-256
GCM_IV_SIZE = 12   # 96 bits (12 bytes) per NIST SP 800-38D Section 8.2.1
GCM_TAG_SIZE = 16  # 128 bits (16 bytes) authentication tag

# NIST SP 800-132: Salt requirements
SALT_SIZE = 32  # 256 bits (32 bytes) minimum for cryptographic operations


# ============================================================================
# KEY MANAGEMENT
# ============================================================================


class KeyManager:
    """Secure key management with key rotation support"""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize key manager

        Args:
            master_key: Master encryption key (from environment or generated)
        """
        self.master_key = master_key or os.getenv("ENCRYPTION_MASTER_KEY", self._generate_master_key())
        self.active_keys: Dict[str, bytes] = {}
        self.key_versions: Dict[str, int] = {}

    @staticmethod
    def _generate_master_key() -> str:
        """Generate a new master key"""
        key = Fernet.generate_key()
        logger.warning("⚠️  Generated new master key - SAVE THIS IN YOUR .env FILE!")
        logger.warning(f"ENCRYPTION_MASTER_KEY={key.decode()}")
        return key.decode()

    def derive_key(
        self, password: str, salt: Optional[bytes] = None, key_size: int = AES_KEY_SIZE
    ) -> tuple[bytes, bytes]:
        """
        Derive an encryption key from a password using PBKDF2 per NIST SP 800-132.

        Implements NIST SP 800-132 Section 5.3 recommendations:
        - PBKDF2-HMAC-SHA256 algorithm
        - Minimum 100,000 iterations (OWASP 2023 guidance)
        - 32-byte salt (256 bits) for cryptographic operations
        - Configurable key size (default: 32 bytes for AES-256)

        Reference: NIST SP 800-132 "Recommendation for Password-Based Key Derivation"
        Reference: OWASP Password Storage Cheat Sheet (2023)

        Args:
            password: Password to derive key from
            salt: Salt for key derivation (auto-generated if not provided per NIST SP 800-132)
            key_size: Size of derived key in bytes (default: AES_KEY_SIZE = 32)

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            # NIST SP 800-132: Salt should be at least 128 bits; we use 256 bits
            salt = secrets.token_bytes(SALT_SIZE)

        # NIST SP 800-132 Section 5.3: PBKDF2 with HMAC-SHA256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_size,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,  # Per OWASP 2023 recommendations
            backend=default_backend(),
        )

        key = kdf.derive(password.encode())
        return key, salt

    def get_key(self, key_id: str = "default") -> bytes:
        """Get or create an encryption key"""
        if key_id not in self.active_keys:
            # Derive key from master key
            key, _ = self.derive_key(self.master_key)
            self.active_keys[key_id] = key
            self.key_versions[key_id] = 1

        return self.active_keys[key_id]


# ============================================================================
# AES-256-GCM ENCRYPTION
# ============================================================================


class AESEncryption:
    """AES-256-GCM encryption (Authenticated Encryption with Associated Data)"""

    def __init__(self, key_manager: Optional[KeyManager] = None):
        """
        Initialize AES encryption

        Args:
            key_manager: Key manager instance (created if not provided)
        """
        self.key_manager = key_manager or KeyManager()

    def encrypt(self, plaintext: Union[str, bytes], key_id: str = "default") -> str:
        """
        Encrypt data using AES-256-GCM

        Args:
            plaintext: Data to encrypt
            key_id: Key identifier to use

        Returns:
            Base64-encoded encrypted data with IV and tag
        """
        # Convert to bytes if string
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()

        # Get encryption key
        key = self.key_manager.get_key(key_id)

        # Generate a random IV (12 bytes for GCM)
        iv = secrets.token_bytes(12)

        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Encrypt and get tag
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        tag = encryptor.tag

        # Combine IV + tag + ciphertext
        encrypted_data = iv + tag + ciphertext

        # Return base64 encoded
        return base64.b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str, key_id: str = "default") -> str:
        """
        Decrypt data using AES-256-GCM

        Args:
            encrypted_data: Base64-encoded encrypted data
            key_id: Key identifier to use

        Returns:
            Decrypted plaintext

        Raises:
            Exception: If decryption fails or authentication tag is invalid
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)

            # Extract IV, tag, and ciphertext
            iv = encrypted_bytes[:12]
            tag = encrypted_bytes[12:28]
            ciphertext = encrypted_bytes[28:]

            # Get decryption key
            key = self.key_manager.get_key(key_id)

            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()

            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            return plaintext.decode()

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption failed - data may be corrupted or key is incorrect")


# ============================================================================
# FERNET ENCRYPTION (Simpler alternative)
# ============================================================================


class FernetEncryption:
    """Fernet encryption (simpler, built-in authentication)"""

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize Fernet encryption

        Args:
            key: Encryption key (generated if not provided)
        """
        if key is None:
            key = Fernet.generate_key()
            logger.warning(f"Generated new Fernet key: {key.decode()}")

        self.cipher = Fernet(key)

    def encrypt(self, plaintext: Union[str, bytes]) -> str:
        """Encrypt data using Fernet"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()

        encrypted = self.cipher.encrypt(plaintext)
        return encrypted.decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using Fernet"""
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        return decrypted.decode()


# ============================================================================
# FIELD-LEVEL ENCRYPTION
# ============================================================================


class FieldEncryption:
    """Field-level encryption for sensitive database fields"""

    def __init__(self, encryption_engine: Optional[AESEncryption] = None):
        """
        Initialize field encryption

        Args:
            encryption_engine: AES encryption instance
        """
        self.engine = encryption_engine or AESEncryption()

    def encrypt_field(self, value: Any, field_name: str) -> Dict[str, Any]:
        """
        Encrypt a field value

        Args:
            value: Value to encrypt
            field_name: Name of the field (used for key derivation)

        Returns:
            Dictionary with encrypted value and metadata
        """
        if value is None:
            return {"encrypted": False, "value": None}

        # Convert value to string
        str_value = str(value)

        # Encrypt
        encrypted = self.engine.encrypt(str_value, key_id=f"field_{field_name}")

        return {"encrypted": True, "value": encrypted, "field": field_name, "encrypted_at": str(hash(field_name))}

    def decrypt_field(self, encrypted_data: Dict[str, Any]) -> Any:
        """
        Decrypt a field value

        Args:
            encrypted_data: Dictionary with encrypted value and metadata

        Returns:
            Decrypted value
        """
        if not encrypted_data.get("encrypted"):
            return encrypted_data.get("value")

        field_name = encrypted_data.get("field")
        encrypted_value = encrypted_data.get("value")

        # Decrypt
        decrypted = self.engine.decrypt(encrypted_value, key_id=f"field_{field_name}")

        return decrypted


# ============================================================================
# PASSWORD HASHING (One-way) - DEPRECATED
# ============================================================================
#
# ⚠️  DEPRECATED: The custom PasswordHasher class has been removed.
#
# Truth Protocol Violation: Custom password hashing violates OWASP 2023
# Password Storage Cheat Sheet and NIST SP 800-63B recommendations.
#
# ✅ RECOMMENDED: Use passlib.context.CryptContext (see security/jwt_auth.py)
#
# References:
# - OWASP: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
# - NIST SP 800-63B Section 5.1.1.2: https://pages.nist.gov/800-63-3/sp800-63b.html
# ============================================================================


# SECURE RANDOM GENERATION
# ============================================================================


class SecureRandom:
    """Cryptographically secure random generation"""

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        prefix = "sk_live_"
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}{random_part}"

    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """Generate a secret key"""
        return secrets.token_hex(length)


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

# Global encryption instances
key_manager = KeyManager()
aes_encryption = AESEncryption(key_manager)
field_encryption = FieldEncryption(aes_encryption)
# password_hasher = PasswordHasher()  # DEPRECATED - Use passlib instead
secure_random = SecureRandom()

logger.info("🔐 Enterprise AES-256 Encryption System initialized")
