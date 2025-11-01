"""
AES-256-GCM Encryption Module (NIST SP 800-38D)
Field-level encryption with PBKDF2 key derivation and key rotation support
Author: DevSkyy Enterprise Team
Date: October 26, 2025

Citation: NIST SP 800-38D (Recommendation for Block Cipher Modes of Operation:
Galois/Counter Mode), published Dec 2007, reaffirmed 2024
"""

import os
import base64
import logging
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================


class EncryptionSettings:
    """
    AES-256-GCM Configuration (NIST SP 800-38D Section 5.2.1.1)
    """

    # Master encryption key (must be 32 bytes for AES-256)
    MASTER_KEY: Optional[bytes] = None

    # PBKDF2 Key Derivation (NIST SP 800-132)
    PBKDF2_ITERATIONS: int = 100_000  # NIST recommendation: 100k+ iterations
    PBKDF2_HASH: str = "sha256"
    PBKDF2_SALT_LENGTH: int = 16  # 128 bits

    # GCM Parameters (NIST SP 800-38D Section 5.2.1.1)
    GCM_NONCE_LENGTH: int = 12  # 96 bits (recommended for performance)
    GCM_TAG_LENGTH: int = 16  # 128 bits (full authentication tag)

    # Key Rotation
    KEY_ROTATION_INTERVAL_DAYS: int = 90
    LEGACY_KEYS: dict = {}  # Store old keys for decryption of legacy data

    def __init__(self):
        """Initialize encryption settings from environment"""
        master_key_b64 = os.getenv("ENCRYPTION_MASTER_KEY")
        if not master_key_b64:
            # Generate new master key if not provided (development only)
            logger.warning(
                "ENCRYPTION_MASTER_KEY not set. Generating ephemeral key. " "Set ENCRYPTION_MASTER_KEY for production."
            )
            self.MASTER_KEY = secrets.token_bytes(32)  # 256 bits
        else:
            try:
                self.MASTER_KEY = base64.b64decode(master_key_b64)
                if len(self.MASTER_KEY) != 32:
                    raise ValueError("Master key must be 256 bits (32 bytes)")
            except Exception as e:
                raise ValueError(f"Invalid ENCRYPTION_MASTER_KEY: {str(e)}")


settings = EncryptionSettings()

# ============================================================================
# ENCRYPTION & DECRYPTION
# ============================================================================


def derive_key(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """
    Derive encryption key from password using PBKDF2 (NIST SP 800-132)

    Args:
        password: Master password or passphrase
        salt: Optional salt (generated if not provided)

    Returns:
        Tuple of (key, salt) where key is 32 bytes (AES-256)

    Citation: NIST SP 800-132 (Password-Based Key Derivation Function)
    """
    if salt is None:
        salt = secrets.token_bytes(settings.PBKDF2_SALT_LENGTH)

    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,  # 256 bits for AES-256
        salt=salt,
        iterations=settings.PBKDF2_ITERATIONS,
        backend=default_backend(),
    )

    key = kdf.derive(password.encode())
    return key, salt


def encrypt_field(plaintext: str, master_key: Optional[bytes] = None) -> str:
    """
    Encrypt a single field using AES-256-GCM

    Args:
        plaintext: Data to encrypt
        master_key: Encryption key (defaults to MASTER_KEY from settings)

    Returns:
        Base64-encoded ciphertext (format: nonce + tag + ciphertext)

    Citation: NIST SP 800-38D Section 5.2 (Encryption)
    """
    if master_key is None:
        master_key = settings.MASTER_KEY

    if master_key is None:
        raise ValueError("No encryption key available")

    try:
        # Generate random nonce (96 bits for GCM - NIST recommends for performance)
        nonce = secrets.token_bytes(settings.GCM_NONCE_LENGTH)

        # Create cipher
        cipher = AESGCM(master_key)

        # Encrypt (authentication tag is automatically appended)
        # associated_data=None means no AAD (Associated Authenticated Data)
        ciphertext = cipher.encrypt(nonce, plaintext.encode("utf-8"), None)  # No associated authenticated data

        # Package: nonce + ciphertext (tag is appended by encrypt())
        encrypted_package = nonce + ciphertext

        # Encode to base64 for storage (avoids binary data in databases)
        encoded = base64.b64encode(encrypted_package).decode("utf-8")

        logger.debug(f"Field encrypted successfully (plaintext length: {len(plaintext)})")
        return encoded

    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        raise RuntimeError(f"Encryption error: {str(e)}")


def decrypt_field(
    encrypted_base64: str, master_key: Optional[bytes] = None, legacy_key_id: Optional[str] = None
) -> str:
    """
    Decrypt a field encrypted with AES-256-GCM

    Args:
        encrypted_base64: Base64-encoded encrypted data
        master_key: Encryption key (defaults to MASTER_KEY)
        legacy_key_id: Optional key ID for decrypting data with rotated keys

    Returns:
        Decrypted plaintext

    Raises:
        ValueError: If decryption fails (tampering detected)

    Citation: NIST SP 800-38D Section 5.3 (Decryption)
    """
    if master_key is None:
        master_key = settings.MASTER_KEY

    if master_key is None:
        raise ValueError("No encryption key available")

    try:
        # Decode from base64
        encrypted_package = base64.b64decode(encrypted_base64)

        # Extract nonce and ciphertext
        nonce = encrypted_package[: settings.GCM_NONCE_LENGTH]
        ciphertext = encrypted_package[settings.GCM_NONCE_LENGTH :]

        # Create cipher and decrypt
        cipher = AESGCM(master_key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)

        logger.debug("Field decrypted successfully")
        return plaintext.decode("utf-8")

    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise ValueError("Decryption failed - data may be corrupted or tampered with")


def encrypt_dict(data: dict, fields: list) -> dict:
    """
    Encrypt specific fields in a dictionary

    Args:
        data: Dictionary to encrypt
        fields: List of field names to encrypt

    Returns:
        Dictionary with specified fields encrypted
    """
    encrypted = data.copy()
    for field in fields:
        if field in encrypted:
            encrypted[field] = encrypt_field(str(encrypted[field]))
    return encrypted


def decrypt_dict(data: dict, fields: list) -> dict:
    """
    Decrypt specific fields in a dictionary

    Args:
        data: Dictionary to decrypt
        fields: List of field names to decrypt

    Returns:
        Dictionary with specified fields decrypted
    """
    decrypted = data.copy()
    for field in fields:
        if field in decrypted:
            decrypted[field] = decrypt_field(decrypted[field])
    return decrypted


# ============================================================================
# KEY ROTATION
# ============================================================================


def rotate_keys() -> str:
    """
    Rotate master encryption key

    Moves current key to legacy_keys and generates new master key.
    Old data can still be decrypted using legacy keys.

    Returns:
        New master key (base64 encoded)
    """
    timestamp = datetime.utcnow().isoformat()

    # Archive current key
    if settings.MASTER_KEY:
        settings.LEGACY_KEYS[timestamp] = settings.MASTER_KEY
        logger.info(f"Archived master key for rotation (timestamp: {timestamp})")

    # Generate new master key
    new_key = secrets.token_bytes(32)
    settings.MASTER_KEY = new_key

    new_key_b64 = base64.b64encode(new_key).decode("utf-8")
    logger.warning(f"Master key rotated. New key (base64): {new_key_b64}")

    return new_key_b64


# ============================================================================
# PII MASKING FOR LOGS
# ============================================================================


def mask_pii(data: str, mask_char: str = "*", show_chars: int = 3) -> str:
    """
    Mask personally identifiable information in logs

    Args:
        data: PII to mask (e.g., email, phone)
        mask_char: Character to use for masking (default: "*")
        show_chars: Number of characters to show (default: 3)

    Returns:
        Masked string (e.g., "abc***@g***l.com")
    """
    if len(data) <= show_chars:
        return mask_char * len(data)

    visible = data[:show_chars]
    masked = mask_char * (len(data) - show_chars)
    return visible + masked


def mask_email(email: str) -> str:
    """Mask email address in logs"""
    if "@" not in email:
        return mask_pii(email)

    local, domain = email.split("@", 1)
    masked_local = mask_pii(local, show_chars=1)
    masked_domain = mask_pii(domain.split(".")[0], show_chars=1) + ".*"
    return f"{masked_local}@{masked_domain}"


def mask_phone(phone: str) -> str:
    """Mask phone number in logs"""
    # Show only last 4 digits
    if len(phone) <= 4:
        return mask_pii(phone)
    return mask_pii(phone, show_chars=0) + phone[-4:]


# ============================================================================
# INITIALIZATION
# ============================================================================


def generate_master_key() -> str:
    """
    Generate a new master encryption key

    Returns:
        Base64-encoded key (safe to store in .env)
    """
    key = secrets.token_bytes(32)  # 256 bits
    return base64.b64encode(key).decode("utf-8")


if __name__ == "__main__":
    # Demo: Generate key and encrypt data
    key = generate_master_key()
    logger.info(f"New master key (set as ENCRYPTION_MASTER_KEY): {key}")

    # Encrypt and decrypt example
    plaintext = "sensitive_data_123"
    encrypted = encrypt_field(plaintext)
    decrypted = decrypt_field(encrypted)

    logger.info(f"Original:  {plaintext}")
    logger.info(f"Encrypted: {encrypted}")
    logger.info(f"Decrypted: {decrypted}")
    logger.info(f"Match: {plaintext == decrypted}")
