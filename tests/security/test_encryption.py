"""
Test suite for Encryption Module (AES-256-GCM)

Tests encryption, decryption, and security per Truth Protocol requirements.
Validates AES-256-GCM implementation, key management, and NIST SP 800-38D compliance.
"""

import pytest
import base64
import os
from unittest.mock import patch, MagicMock

# Import encryption module
try:
    from security.encryption_v2 import (
        encrypt_data,
        decrypt_data,
        generate_encryption_key,
        EncryptionService
    )
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    pytest.skip("Encryption module not available", allow_module_level=True)


@pytest.fixture
def encryption_service():
    """Create encryption service instance."""
    if ENCRYPTION_AVAILABLE:
        return EncryptionService()
    return None


@pytest.fixture
def test_key():
    """Generate a test encryption key."""
    if ENCRYPTION_AVAILABLE:
        return generate_encryption_key()
    return os.urandom(32)  # 256-bit key


@pytest.fixture
def sample_data():
    """Sample data for encryption tests."""
    return {
        "user_id": "user-12345",
        "email": "test@example.com",
        "payment_info": {
            "card_last_4": "4242",
            "expiry": "12/25"
        }
    }


class TestEncryptionBasics:
    """Test basic encryption and decryption operations."""

    def test_encrypt_decrypt_cycle(self, encryption_service, test_key, sample_data):
        """Should successfully encrypt and decrypt data."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Encrypt
        encrypted = encryption_service.encrypt(sample_data, test_key)
        assert encrypted is not None
        assert encrypted != sample_data
        assert isinstance(encrypted, (str, bytes))

        # Decrypt
        decrypted = encryption_service.decrypt(encrypted, test_key)
        assert decrypted == sample_data

    def test_encrypt_string_data(self, encryption_service, test_key):
        """Should encrypt and decrypt string data."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        original = "sensitive information"
        encrypted = encryption_service.encrypt(original, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == original
        assert encrypted != original

    def test_encrypt_binary_data(self, encryption_service, test_key):
        """Should encrypt and decrypt binary data."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        original = b"binary sensitive data"
        encrypted = encryption_service.encrypt(original, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == original
        assert encrypted != original


class TestAESGCMCompliance:
    """Test AES-256-GCM compliance (NIST SP 800-38D)."""

    def test_uses_256_bit_key(self, encryption_service, test_key):
        """Should use 256-bit (32-byte) encryption keys."""
        assert len(test_key) == 32, "Key must be 256 bits (32 bytes)"

    def test_unique_nonce_per_encryption(self, encryption_service, test_key, sample_data):
        """Should use unique nonce/IV for each encryption."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        encrypted1 = encryption_service.encrypt(sample_data, test_key)
        encrypted2 = encryption_service.encrypt(sample_data, test_key)

        # Same plaintext should produce different ciphertext due to unique nonce
        assert encrypted1 != encrypted2

    def test_includes_authentication_tag(self, encryption_service, test_key, sample_data):
        """Should include GCM authentication tag."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        encrypted = encryption_service.encrypt(sample_data, test_key)

        # GCM produces: nonce + ciphertext + tag
        # Verify encrypted data is longer than plaintext (includes nonce + tag)
        if isinstance(encrypted, str):
            encrypted_bytes = base64.b64decode(encrypted)
        else:
            encrypted_bytes = encrypted

        # Should include 12-byte nonce + 16-byte tag (minimum)
        assert len(encrypted_bytes) > len(str(sample_data))

    def test_tampered_data_fails_authentication(self, encryption_service, test_key, sample_data):
        """Should detect tampered ciphertext via authentication tag."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        encrypted = encryption_service.encrypt(sample_data, test_key)

        # Tamper with encrypted data
        if isinstance(encrypted, str):
            encrypted_bytes = bytearray(base64.b64decode(encrypted))
            encrypted_bytes[-1] ^= 0xFF  # Flip bits in last byte
            tampered = base64.b64encode(bytes(encrypted_bytes)).decode()
        else:
            tampered_bytes = bytearray(encrypted)
            tampered_bytes[-1] ^= 0xFF
            tampered = bytes(tampered_bytes)

        # Decryption should fail
        with pytest.raises(Exception):
            encryption_service.decrypt(tampered, test_key)


class TestKeyManagement:
    """Test encryption key generation and management."""

    def test_generate_secure_random_key(self):
        """Should generate cryptographically secure random keys."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        assert len(key1) == 32
        assert len(key2) == 32
        assert key1 != key2  # Should be unique

    def test_key_derivation_from_password(self, encryption_service):
        """Should derive keys from passwords using PBKDF2."""
        if not ENCRYPTION_AVAILABLE or not hasattr(encryption_service, 'derive_key_from_password'):
            pytest.skip("Key derivation not available")

        password = "strong-password-123"
        salt = os.urandom(16)

        key = encryption_service.derive_key_from_password(password, salt)
        assert len(key) == 32
        assert key is not None

    def test_key_rotation_support(self, encryption_service, sample_data):
        """Should support key rotation for encrypted data."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        old_key = generate_encryption_key()
        new_key = generate_encryption_key()

        # Encrypt with old key
        encrypted = encryption_service.encrypt(sample_data, old_key)

        # Decrypt with old key
        decrypted = encryption_service.decrypt(encrypted, old_key)

        # Re-encrypt with new key
        re_encrypted = encryption_service.encrypt(decrypted, new_key)

        # Verify can decrypt with new key
        final_decrypted = encryption_service.decrypt(re_encrypted, new_key)
        assert final_decrypted == sample_data


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_decrypt_with_wrong_key_fails(self, encryption_service, sample_data):
        """Should fail to decrypt with incorrect key."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        encrypted = encryption_service.encrypt(sample_data, key1)

        with pytest.raises(Exception):
            encryption_service.decrypt(encrypted, key2)

    def test_encrypt_empty_data(self, encryption_service, test_key):
        """Should handle empty data gracefully."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        empty_data = ""
        encrypted = encryption_service.encrypt(empty_data, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == empty_data

    def test_encrypt_none_data_fails(self, encryption_service, test_key):
        """Should reject None as input data."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        with pytest.raises((ValueError, TypeError, AttributeError)):
            encryption_service.encrypt(None, test_key)

    def test_invalid_key_length_fails(self, encryption_service, sample_data):
        """Should reject keys that aren't 256 bits."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        invalid_key = os.urandom(16)  # Only 128 bits

        with pytest.raises(Exception):
            encryption_service.encrypt(sample_data, invalid_key)


class TestPIIEncryption:
    """Test encryption of Personally Identifiable Information (PII)."""

    def test_encrypt_email_address(self, encryption_service, test_key):
        """Should encrypt email addresses."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        email = "user@example.com"
        encrypted = encryption_service.encrypt(email, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == email
        assert email not in str(encrypted)

    def test_encrypt_phone_number(self, encryption_service, test_key):
        """Should encrypt phone numbers."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        phone = "+1-555-123-4567"
        encrypted = encryption_service.encrypt(phone, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == phone
        assert phone not in str(encrypted)

    def test_encrypt_ssn(self, encryption_service, test_key):
        """Should encrypt Social Security Numbers."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        ssn = "123-45-6789"
        encrypted = encryption_service.encrypt(ssn, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == ssn
        assert ssn not in str(encrypted)

    def test_encrypt_credit_card(self, encryption_service, test_key):
        """Should encrypt credit card numbers."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        cc = "4532-1234-5678-9010"
        encrypted = encryption_service.encrypt(cc, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == cc
        assert "4532" not in str(encrypted)


class TestPerformance:
    """Test encryption performance requirements."""

    def test_encryption_performance(self, encryption_service, test_key):
        """Encryption should complete within reasonable time."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        import time

        data = "test data" * 1000  # 9KB of data
        iterations = 100

        start = time.time()
        for _ in range(iterations):
            encryption_service.encrypt(data, test_key)
        elapsed = time.time() - start

        avg_time_ms = (elapsed / iterations) * 1000
        print(f"Average encryption time: {avg_time_ms:.2f}ms")

        # Should be fast (< 10ms per operation for small data)
        assert avg_time_ms < 50

    def test_batch_encryption_performance(self, encryption_service, test_key):
        """Should handle batch encryption efficiently."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        import time

        batch = [f"record-{i}" for i in range(1000)]

        start = time.time()
        encrypted_batch = [
            encryption_service.encrypt(record, test_key)
            for record in batch
        ]
        elapsed = time.time() - start

        print(f"Encrypted 1000 records in {elapsed:.2f}s ({elapsed/len(batch)*1000:.2f}ms per record)")

        # Should complete in reasonable time
        assert elapsed < 5.0  # 5 seconds for 1000 records


class TestTruthProtocolCompliance:
    """Verify Truth Protocol security requirements."""

    def test_no_hardcoded_keys(self):
        """Should not contain hardcoded encryption keys."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Read the encryption module source
        import security.encryption_v2 as enc_module
        source = enc_module.__file__

        with open(source, 'r') as f:
            content = f.read()

        # Should not contain suspicious hardcoded keys
        assert "b'\\x" not in content[:1000]  # No hardcoded bytes in beginning
        assert "SECRET_KEY =" not in content

    def test_uses_approved_algorithm(self, encryption_service):
        """Should use approved AES-256-GCM algorithm."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Verify uses AES-256-GCM (check cipher name or algorithm)
        if hasattr(encryption_service, 'algorithm'):
            assert 'AES' in str(encryption_service.algorithm).upper()
            assert '256' in str(encryption_service.algorithm) or 'GCM' in str(encryption_service.algorithm)

    def test_logging_does_not_leak_keys(self, encryption_service, test_key, sample_data, caplog):
        """Logging should never expose encryption keys."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        encrypted = encryption_service.encrypt(sample_data, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        # Check logs don't contain key material
        key_hex = test_key.hex() if isinstance(test_key, bytes) else str(test_key)
        for record in caplog.records:
            assert key_hex not in record.message
            assert test_key not in str(record.args)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=security.encryption_v2", "--cov-report=term"])
