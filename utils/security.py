"""
Shared Security Utilities for DevSkyy Platform

This module consolidates security-related functionality including:
- JWT token creation and verification
- Password hashing (bcrypt/argon2)
- AES-256-GCM encryption/decryption
- PBKDF2 key derivation

Extracted from main.py and sqlite_auth_system.py to eliminate duplication.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext


class SecurityManager:
    """
    Unified security manager for the DevSkyy platform.
    
    Provides enterprise-grade security operations:
    - Password hashing with bcrypt
    - JWT token management
    - AES-256-GCM encryption
    - Secure key derivation
    """
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30
    ):
        """
        Initialize security manager.
        
        Args:
            secret_key: JWT secret key (auto-generated if not provided)
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Token expiration time
        """
        self.secret_key = secret_key or os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        
        # Password hashing context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Encryption key
        self.encryption_key = self._derive_key()
    
    def _derive_key(self) -> bytes:
        """
        Derive encryption key using PBKDF2.
        
        Returns:
            32-byte encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'devskyy-salt',  # In production, use unique salt per installation
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self.secret_key.encode())
    
    # ===========================
    # Password Operations
    # ===========================
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password to verify against
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    # ===========================
    # JWT Token Operations
    # ===========================
    
    def create_access_token(
        self,
        data: Dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in token (e.g., {"sub": username, "user_id": 1})
            expires_delta: Custom expiration time (optional)
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
    
    # ===========================
    # Encryption Operations
    # ===========================
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data using AES-256-GCM.
        
        Args:
            data: Plain text data to encrypt
            
        Returns:
            Hex-encoded encrypted data (nonce + ciphertext)
        """
        aesgcm = AESGCM(self.encryption_key)
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = aesgcm.encrypt(nonce, data.encode(), None)
        return (nonce + ciphertext).hex()
    
    def decrypt_data(self, encrypted: str) -> str:
        """
        Decrypt data encrypted with AES-256-GCM.
        
        Args:
            encrypted: Hex-encoded encrypted data
            
        Returns:
            Decrypted plain text data
        """
        data = bytes.fromhex(encrypted)
        nonce = data[:12]
        ciphertext = data[12:]
        aesgcm = AESGCM(self.encryption_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()


# Global security manager instance
_global_security_manager: Optional[SecurityManager] = None


def get_security_manager(
    secret_key: Optional[str] = None,
    algorithm: str = "HS256",
    access_token_expire_minutes: int = 30
) -> SecurityManager:
    """
    Get or create the global security manager instance.
    
    Args:
        secret_key: JWT secret key (only used on first call)
        algorithm: JWT algorithm (only used on first call)
        access_token_expire_minutes: Token expiration (only used on first call)
        
    Returns:
        Global SecurityManager instance
    """
    global _global_security_manager
    
    if _global_security_manager is None:
        _global_security_manager = SecurityManager(
            secret_key=secret_key,
            algorithm=algorithm,
            access_token_expire_minutes=access_token_expire_minutes
        )
    
    return _global_security_manager
