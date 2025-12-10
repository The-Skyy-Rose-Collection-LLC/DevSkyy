"""
DevSkyy Enterprise AES-256-GCM Encryption Module
=================================================

Production-grade encryption following:
- NIST SP 800-38D: Galois/Counter Mode (GCM)
- NIST SP 800-132: Key Derivation (PBKDF2)
- NIST SP 800-90A: Random Number Generation

Features:
- AES-256-GCM authenticated encryption
- Secure key derivation with PBKDF2
- Automatic IV generation (96-bit as recommended)
- Key rotation support
- Envelope encryption for large data
- Field-level encryption for PII

Dependencies (verified from PyPI December 2024):
- cryptography==41.0.7
"""

import os
import base64
import secrets
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
import json

# Verified PyPI package
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class EncryptionConfig:
    """
    Encryption configuration following NIST guidelines
    
    References:
    - NIST SP 800-38D Section 5.2.1.1: 96-bit IV recommended
    - NIST SP 800-38D Section 5.2.1.2: 128-bit auth tag recommended
    - NIST SP 800-132: 10,000+ iterations for PBKDF2
    """
    
    # AES-256 requires 256-bit (32 byte) key
    key_length_bytes: int = 32  # 256 bits
    
    # NIST recommends 96-bit (12 byte) IV for GCM
    iv_length_bytes: int = 12
    
    # Authentication tag length (128 bits for maximum security)
    tag_length_bytes: int = 16  # 128 bits
    
    # PBKDF2 iterations (NIST minimum: 10,000, OWASP recommends 600,000+)
    pbkdf2_iterations: int = 600_000
    
    # Salt length for key derivation
    salt_length_bytes: int = 32
    
    # Additional authenticated data (AAD) for context binding
    default_aad: bytes = b"devskyy-platform-v1"


class KeyVersion(Enum):
    """Key versions for rotation tracking"""
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


# =============================================================================
# Secure Key Derivation
# =============================================================================

class KeyDerivation:
    """
    Key derivation using PBKDF2-HMAC-SHA256
    
    Reference: NIST SP 800-132
    """
    
    def __init__(self, config: EncryptionConfig = None):
        self.config = config or EncryptionConfig()
    
    def derive_key(
        self,
        password: str,
        salt: bytes = None,
        iterations: int = None
    ) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password
        
        Args:
            password: User password or master key phrase
            salt: Optional salt (generated if not provided)
            iterations: Optional iteration count
            
        Returns:
            (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(self.config.salt_length_bytes)
        
        iterations = iterations or self.config.pbkdf2_iterations
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.config.key_length_bytes,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode('utf-8'))
        return key, salt
    
    def generate_random_key(self) -> bytes:
        """Generate cryptographically secure random key"""
        return secrets.token_bytes(self.config.key_length_bytes)


# =============================================================================
# AES-256-GCM Encryption
# =============================================================================

class AESGCMEncryption:
    """
    AES-256-GCM Authenticated Encryption
    
    GCM provides both confidentiality and authenticity:
    - Encryption: AES-256 in Counter mode
    - Authentication: GMAC for integrity verification
    
    Reference: NIST SP 800-38D
    """
    
    def __init__(self, config: EncryptionConfig = None):
        self.config = config or EncryptionConfig()
        
        # Load master key from environment
        master_key_b64 = os.getenv("ENCRYPTION_MASTER_KEY")
        if master_key_b64:
            self._master_key = base64.b64decode(master_key_b64)
        else:
            # Generate for development (NOT for production!)
            logger.warning(
                "ENCRYPTION_MASTER_KEY not set! "
                "Generating ephemeral key. Set environment variable for production."
            )
            self._master_key = secrets.token_bytes(32)
        
        # Key versioning for rotation
        self._key_versions: Dict[str, bytes] = {
            KeyVersion.V1.value: self._master_key
        }
        self._current_version = KeyVersion.V1.value
    
    def encrypt(
        self,
        plaintext: Union[str, bytes],
        aad: bytes = None,
        key: bytes = None
    ) -> str:
        """
        Encrypt data with AES-256-GCM
        
        Args:
            plaintext: Data to encrypt (string or bytes)
            aad: Additional authenticated data (optional)
            key: Encryption key (uses master key if not provided)
            
        Returns:
            Base64-encoded encrypted data with format:
            version:iv:ciphertext:tag
        """
        # Convert string to bytes
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # Use provided key or master key
        key = key or self._master_key
        
        # Use default AAD if not provided
        aad = aad or self.config.default_aad
        
        # Generate random IV (NIST: must be unique for each encryption)
        iv = secrets.token_bytes(self.config.iv_length_bytes)
        
        # Create cipher
        aesgcm = AESGCM(key)
        
        # Encrypt (ciphertext includes auth tag at the end in cryptography lib)
        ciphertext = aesgcm.encrypt(iv, plaintext, aad)
        
        # Format: version:iv:ciphertext (all base64 encoded)
        result = f"{self._current_version}:{base64.b64encode(iv).decode()}:{base64.b64encode(ciphertext).decode()}"
        
        return result
    
    def decrypt(
        self,
        encrypted_data: str,
        aad: bytes = None,
        key: bytes = None
    ) -> bytes:
        """
        Decrypt data encrypted with AES-256-GCM
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            aad: Additional authenticated data (must match encryption)
            key: Decryption key (uses versioned key if not provided)
            
        Returns:
            Decrypted bytes
            
        Raises:
            InvalidTag: If authentication fails (tampering detected)
        """
        # Parse encrypted data
        parts = encrypted_data.split(':')
        if len(parts) != 3:
            raise ValueError("Invalid encrypted data format")
        
        version, iv_b64, ciphertext_b64 = parts
        
        # Decode components
        iv = base64.b64decode(iv_b64)
        ciphertext = base64.b64decode(ciphertext_b64)
        
        # Get key for version
        if key is None:
            if version not in self._key_versions:
                raise ValueError(f"Unknown key version: {version}")
            key = self._key_versions[version]
        
        # Use default AAD if not provided
        aad = aad or self.config.default_aad
        
        # Create cipher and decrypt
        aesgcm = AESGCM(key)
        
        try:
            plaintext = aesgcm.decrypt(iv, ciphertext, aad)
            return plaintext
        except InvalidTag:
            logger.error("Decryption failed: authentication tag mismatch (tampering detected)")
            raise
    
    def decrypt_to_string(
        self,
        encrypted_data: str,
        aad: bytes = None
    ) -> str:
        """Decrypt and return as UTF-8 string"""
        return self.decrypt(encrypted_data, aad).decode('utf-8')
    
    def rotate_key(self, new_key: bytes = None) -> str:
        """
        Rotate encryption key
        
        Args:
            new_key: New key (generated if not provided)
            
        Returns:
            New version identifier
        """
        if new_key is None:
            new_key = secrets.token_bytes(self.config.key_length_bytes)
        
        # Determine new version
        version_num = len(self._key_versions) + 1
        new_version = f"v{version_num}"
        
        # Store new key
        self._key_versions[new_version] = new_key
        self._current_version = new_version
        
        logger.info(f"Key rotated to version {new_version}")
        return new_version
    
    def re_encrypt_with_new_key(
        self,
        encrypted_data: str,
        aad: bytes = None
    ) -> str:
        """Re-encrypt data with current key version"""
        plaintext = self.decrypt(encrypted_data, aad)
        return self.encrypt(plaintext, aad)


# =============================================================================
# Field-Level Encryption for PII
# =============================================================================

class FieldEncryption:
    """
    Field-level encryption for sensitive data (PII, PCI)
    
    Use Cases:
    - Encrypt specific database columns
    - Protect PII in logs
    - Secure API responses
    """
    
    # Fields that should always be encrypted
    SENSITIVE_FIELDS = {
        'ssn', 'social_security_number',
        'credit_card', 'card_number', 'cvv',
        'password', 'secret', 'api_key',
        'date_of_birth', 'dob',
        'bank_account', 'routing_number',
        'drivers_license', 'passport_number',
        'phone', 'phone_number',
        'address', 'street_address',
    }
    
    def __init__(self, encryption: AESGCMEncryption = None):
        self.encryption = encryption or AESGCMEncryption()
    
    def encrypt_field(
        self,
        field_name: str,
        value: str,
        context: str = None
    ) -> str:
        """
        Encrypt a single field with context binding
        
        Args:
            field_name: Name of the field (for AAD)
            value: Value to encrypt
            context: Additional context (e.g., user_id)
            
        Returns:
            Encrypted value
        """
        # Create AAD from field name and context
        aad = f"field:{field_name}"
        if context:
            aad += f":ctx:{context}"
        
        return self.encryption.encrypt(value, aad.encode())
    
    def decrypt_field(
        self,
        field_name: str,
        encrypted_value: str,
        context: str = None
    ) -> str:
        """Decrypt a field with context verification"""
        aad = f"field:{field_name}"
        if context:
            aad += f":ctx:{context}"
        
        return self.encryption.decrypt_to_string(encrypted_value, aad.encode())
    
    def encrypt_dict(
        self,
        data: Dict[str, Any],
        fields_to_encrypt: set = None,
        context: str = None
    ) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in a dictionary
        
        Args:
            data: Dictionary with potentially sensitive data
            fields_to_encrypt: Fields to encrypt (uses SENSITIVE_FIELDS if not provided)
            context: Additional context for AAD
            
        Returns:
            Dictionary with sensitive fields encrypted
        """
        fields_to_encrypt = fields_to_encrypt or self.SENSITIVE_FIELDS
        result = {}
        
        for key, value in data.items():
            # Check if field should be encrypted
            key_lower = key.lower()
            should_encrypt = any(
                sensitive in key_lower 
                for sensitive in fields_to_encrypt
            )
            
            if should_encrypt and isinstance(value, str) and value:
                result[key] = self.encrypt_field(key, value, context)
                result[f"_{key}_encrypted"] = True  # Mark as encrypted
            elif isinstance(value, dict):
                # Recursively encrypt nested dicts
                result[key] = self.encrypt_dict(value, fields_to_encrypt, context)
            else:
                result[key] = value
        
        return result
    
    def decrypt_dict(
        self,
        data: Dict[str, Any],
        context: str = None
    ) -> Dict[str, Any]:
        """Decrypt encrypted fields in a dictionary"""
        result = {}
        
        for key, value in data.items():
            # Skip encryption markers
            if key.startswith('_') and key.endswith('_encrypted'):
                continue
            
            # Check if this field was encrypted
            if data.get(f"_{key}_encrypted"):
                result[key] = self.decrypt_field(key, value, context)
            elif isinstance(value, dict):
                result[key] = self.decrypt_dict(value, context)
            else:
                result[key] = value
        
        return result


# =============================================================================
# Envelope Encryption for Large Data
# =============================================================================

class EnvelopeEncryption:
    """
    Envelope encryption for large data
    
    Pattern:
    1. Generate random Data Encryption Key (DEK)
    2. Encrypt data with DEK
    3. Encrypt DEK with Master Key (KEK)
    4. Store encrypted DEK + encrypted data
    
    Benefits:
    - Efficient key rotation (only re-encrypt DEK)
    - Limits exposure of master key
    - Supports per-record keys
    """
    
    def __init__(self, encryption: AESGCMEncryption = None):
        self.encryption = encryption or AESGCMEncryption()
    
    def encrypt(
        self,
        data: bytes,
        aad: bytes = None
    ) -> Dict[str, str]:
        """
        Encrypt large data using envelope encryption
        
        Returns:
            {
                "encrypted_dek": "...",  # DEK encrypted with master key
                "encrypted_data": "...", # Data encrypted with DEK
                "algorithm": "AES-256-GCM",
                "version": "v1"
            }
        """
        # Generate random DEK
        dek = secrets.token_bytes(32)  # 256-bit key
        
        # Encrypt data with DEK
        dek_aesgcm = AESGCM(dek)
        iv = secrets.token_bytes(12)
        aad = aad or b"envelope-data"
        encrypted_data = dek_aesgcm.encrypt(iv, data, aad)
        
        # Encrypt DEK with master key
        encrypted_dek = self.encryption.encrypt(dek, b"envelope-dek")
        
        return {
            "encrypted_dek": encrypted_dek,
            "encrypted_data": f"{base64.b64encode(iv).decode()}:{base64.b64encode(encrypted_data).decode()}",
            "aad": base64.b64encode(aad).decode(),
            "algorithm": "AES-256-GCM",
            "version": "v1"
        }
    
    def decrypt(self, envelope: Dict[str, str]) -> bytes:
        """Decrypt envelope-encrypted data"""
        # Decrypt DEK
        dek = self.encryption.decrypt(envelope["encrypted_dek"], b"envelope-dek")
        
        # Parse encrypted data
        iv_b64, data_b64 = envelope["encrypted_data"].split(':')
        iv = base64.b64decode(iv_b64)
        encrypted_data = base64.b64decode(data_b64)
        aad = base64.b64decode(envelope.get("aad", ""))
        
        # Decrypt data
        dek_aesgcm = AESGCM(dek)
        return dek_aesgcm.decrypt(iv, encrypted_data, aad)


# =============================================================================
# Secure Data Masking
# =============================================================================

class DataMasker:
    """
    Mask sensitive data for logging and display
    
    Does NOT use encryption - just masks for visual display
    """
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email address: j***@e***.com"""
        if '@' not in email:
            return '***'
        local, domain = email.rsplit('@', 1)
        domain_parts = domain.rsplit('.', 1)
        
        masked_local = local[0] + '***' if len(local) > 1 else '***'
        masked_domain = domain_parts[0][0] + '***' if len(domain_parts[0]) > 1 else '***'
        
        return f"{masked_local}@{masked_domain}.{domain_parts[-1]}"
    
    @staticmethod
    def mask_card_number(card: str) -> str:
        """Mask credit card: ****-****-****-1234"""
        digits = ''.join(filter(str.isdigit, card))
        if len(digits) < 4:
            return '****'
        return f"****-****-****-{digits[-4:]}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Mask phone number: ***-***-1234"""
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) < 4:
            return '***'
        return f"***-***-{digits[-4:]}"
    
    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask SSN: ***-**-1234"""
        digits = ''.join(filter(str.isdigit, ssn))
        if len(digits) < 4:
            return '***-**-****'
        return f"***-**-{digits[-4:]}"


# =============================================================================
# Migration Helper: XOR to AES-256-GCM
# =============================================================================

class EncryptionMigration:
    """
    Helper to migrate from weak XOR encryption to AES-256-GCM
    
    CRITICAL: XOR encryption is NOT secure!
    - Vulnerable to known-plaintext attacks
    - Key can be recovered from ciphertext + plaintext
    - No authentication (tampering undetected)
    """
    
    @staticmethod
    def xor_decrypt_legacy(encrypted_b64: str, key: str) -> str:
        """
        Decrypt legacy XOR-encrypted data
        
        WARNING: Only use for migration, then delete this method
        """
        encrypted = base64.b64decode(encrypted_b64)
        key_bytes = key.encode()
        decrypted = bytes([
            encrypted[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(encrypted))
        ])
        return decrypted.decode('utf-8')
    
    @staticmethod
    def migrate_record(
        xor_encrypted: str,
        xor_key: str,
        aes_encryption: AESGCMEncryption
    ) -> str:
        """
        Migrate a single record from XOR to AES-256-GCM
        
        Returns: AES-encrypted data
        """
        # Decrypt with legacy XOR
        plaintext = EncryptionMigration.xor_decrypt_legacy(xor_encrypted, xor_key)
        
        # Re-encrypt with AES-256-GCM
        return aes_encryption.encrypt(plaintext)


# =============================================================================
# Global Instances
# =============================================================================

# Primary encryption instance
encryption = AESGCMEncryption()

# Field-level encryption for PII
field_encryption = FieldEncryption(encryption)

# Envelope encryption for large data
envelope_encryption = EnvelopeEncryption(encryption)

# Key derivation utility
key_derivation = KeyDerivation()

# Data masking utility
data_masker = DataMasker()


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Classes
    "EncryptionConfig",
    "KeyDerivation",
    "AESGCMEncryption",
    "FieldEncryption",
    "EnvelopeEncryption",
    "DataMasker",
    "EncryptionMigration",
    
    # Instances
    "encryption",
    "field_encryption",
    "envelope_encryption",
    "key_derivation",
    "data_masker",
]
