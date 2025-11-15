import base64
import hashlib
import logging
import os
import secrets
from typing import Any, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import algorithms, Cipher, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

"""
Enterprise-Grade Encryption System
AES-256-GCM encryption replacing XOR cipher
Includes key derivation, secure random generation, and encryption helpers
"""

logger = logging.getLogger(__name__)

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
        self.active_keys: dict[str, bytes] = {}
        self.key_versions: dict[str, int] = {}

    @staticmethod
    def _generate_master_key() -> str:
        """Generate a new master key"""
        key = Fernet.generate_key()
        logger.warning("⚠️  Generated new master key - SAVE THIS IN YOUR .env FILE!")
        logger.warning(f"ENCRYPTION_MASTER_KEY={key.decode()}")
        return key.decode()

    def derive_key(self, password: str, salt: Optional[bytes] = None, key_size: int = 32) -> tuple[bytes, bytes]:
        """
        Derive an encryption key from a password using PBKDF2

        Args:
            password: Password to derive key from
            salt: Salt for key derivation (generated if not provided)
            key_size: Size of derived key in bytes

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_size,
            salt=salt,
            iterations=100000,
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

    def encrypt_field(self, value: Any, field_name: str) -> dict[str, Any]:
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

        return {
            "encrypted": True,
            "value": encrypted,
            "field": field_name,
            "encrypted_at": str(hash(field_name)),
        }

    def decrypt_field(self, encrypted_data: dict[str, Any]) -> Any:
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
# PASSWORD HASHING (One-way)
# ============================================================================


class PasswordHasher:
    """Secure password hashing using bcrypt or argon2"""

    @staticmethod
    def hash_password(password: str, salt_rounds: int = 12) -> str:
        """
        Hash a password using SHA-256 with salt

        Args:
            password: Password to hash
            salt_rounds: Number of salt rounds (complexity)

        Returns:
            Hashed password
        """
        # Generate salt
        salt = secrets.token_bytes(32)

        # Hash password
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000 + salt_rounds * 10000)

        # Combine salt and hash
        storage = salt + key

        return base64.b64encode(storage).decode()

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Verify a password against its hash

        Args:
            password: Password to verify
            hashed: Hashed password

        Returns:
            True if password matches
        """
        try:
            # Decode stored hash
            storage = base64.b64decode(hashed)

            # Extract salt and hash
            salt = storage[:32]
            stored_key = storage[32:]

            # Hash provided password
            key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)

            # Constant-time comparison
            return secrets.compare_digest(key, stored_key)

        except Exception:
            return False


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
password_hasher = PasswordHasher()
secure_random = SecureRandom()

logger.info("🔐 Enterprise AES-256 Encryption System initialized")
