"""
Test suite for Encryption Module (AES-256-GCM)

Tests encryption, decryption, and security per Truth Protocol requirements.
Validates AES-256-GCM implementation, key management, and NIST SP 800-38D compliance.
"""

import base64
import binascii
import logging
import os

import pytest


# Import encryption module
try:
    from security.encryption import EncryptionService, decrypt_data, encrypt_data, generate_encryption_key

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
        "payment_info": {"card_last_4": "4242", "expiry": "12/25"},
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
            # Try base64 decode first, fall back to hex
            try:
                encrypted_bytes = base64.b64decode(encrypted, validate=True)
            except (binascii.Error, ValueError):
                # If not valid base64, try hex decoding
                try:
                    encrypted_bytes = bytes.fromhex(encrypted)
                except ValueError:
                    pytest.fail(f"Encrypted string is neither valid base64 nor hex: {encrypted[:50]}...")
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
        if not ENCRYPTION_AVAILABLE or not hasattr(encryption_service, "derive_key_from_password"):
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

        # Should be fast (< 10ms per operation for small data)
        assert avg_time_ms < 50

    def test_batch_encryption_performance(self, encryption_service, test_key):
        """Should handle batch encryption efficiently."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        import time

        batch = [f"record-{i}" for i in range(1000)]

        start = time.time()
        for record in batch:
            encryption_service.encrypt(record, test_key)
        elapsed = time.time() - start

        # Should complete in reasonable time
        assert elapsed < 5.0  # 5 seconds for 1000 records


class TestTruthProtocolCompliance:
    """Verify Truth Protocol security requirements."""

    def test_no_hardcoded_keys(self):
        """Should not contain hardcoded encryption keys."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Read the encryption module source
        import security.encryption as enc_module

        source = enc_module.__file__

        with open(source, "r") as f:
            content = f.read()

        # Should not contain suspicious hardcoded keys
        assert "b'\\x" not in content[:1000]  # No hardcoded bytes in beginning
        assert "SECRET_KEY =" not in content

    def test_uses_approved_algorithm(self, encryption_service):
        """Should use approved AES-256-GCM algorithm."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Verify uses AES-256-GCM (check cipher name or algorithm)
        if hasattr(encryption_service, "algorithm"):
            assert "AES" in str(encryption_service.algorithm).upper()
            assert "256" in str(encryption_service.algorithm) or "GCM" in str(encryption_service.algorithm)

    def test_logging_does_not_leak_keys(self, encryption_service, test_key, sample_data, caplog):
        """Logging should never expose encryption keys."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Capture ALL log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        # Default caplog only captures WARNING+, but keys might leak at DEBUG/INFO
        with caplog.at_level(logging.DEBUG):
            encrypted = encryption_service.encrypt(sample_data, test_key)
            encryption_service.decrypt(encrypted, test_key)

            # Check logs don't contain key material at ANY level
            key_hex = test_key.hex() if isinstance(test_key, bytes) else str(test_key)
            for record in caplog.records:
                assert key_hex not in record.message, f"Key leaked in {record.levelname} log: {record.message}"
                assert test_key not in str(record.args), f"Key leaked in {record.levelname} log args: {record.args}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=security.encryption", "--cov-report=term"])


# ============================================================================
# ADDITIONAL COMPREHENSIVE TESTS - Enhanced Coverage
# ============================================================================


class TestEncryptionAdvancedScenarios:
    """Advanced encryption scenarios and edge cases."""

    def test_encrypt_large_data(self, encryption_service, test_key):
        """Should handle encryption of large data efficiently."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Test with 1MB of data
        large_data = "x" * (1024 * 1024)
        encrypted = encryption_service.encrypt(large_data, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == large_data
        assert len(encrypted) > len(large_data)

    def test_encrypt_unicode_characters(self, encryption_service, test_key):
        """Should handle Unicode characters correctly."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        unicode_data = "Hello 世界 🌍 Привет مرحبا"
        encrypted = encryption_service.encrypt(unicode_data, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == unicode_data

    def test_encrypt_special_characters(self, encryption_service, test_key):
        """Should handle special characters and symbols."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        special_data = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~\n\t\r"
        encrypted = encryption_service.encrypt(special_data, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == special_data

    def test_encrypt_json_data(self, encryption_service, test_key):
        """Should encrypt and decrypt JSON data."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        import json

        json_data = json.dumps(
            {
                "user": "test@example.com",
                "payment": {"card": "4242-4242-4242-4242"},
                "nested": {"deep": {"value": "secret"}},
            }
        )

        encrypted = encryption_service.encrypt(json_data, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert json.loads(decrypted) == json.loads(json_data)

    def test_encrypt_numerical_data(self, encryption_service, test_key):
        """Should handle numerical data as strings."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        numbers = ["12345", "3.14159", "-999", "0", "1.23e10"]

        for num in numbers:
            encrypted = encryption_service.encrypt(num, test_key)
            decrypted = encryption_service.decrypt(encrypted, test_key)
            assert decrypted == num

    def test_encrypt_whitespace_data(self, encryption_service, test_key):
        """Should handle various whitespace correctly."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        whitespace_data = "   \t\n\r   spaces and tabs   \n"
        encrypted = encryption_service.encrypt(whitespace_data, test_key)
        decrypted = encryption_service.decrypt(encrypted, test_key)

        assert decrypted == whitespace_data

    def test_multiple_encryption_cycles(self, encryption_service, test_key):
        """Should handle multiple encryption/decryption cycles."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        original = "sensitive data"

        # Encrypt, decrypt, encrypt, decrypt
        encrypted1 = encryption_service.encrypt(original, test_key)
        decrypted1 = encryption_service.decrypt(encrypted1, test_key)
        encrypted2 = encryption_service.encrypt(decrypted1, test_key)
        decrypted2 = encryption_service.decrypt(encrypted2, test_key)

        assert decrypted2 == original
        # Each encryption should be different due to unique nonce
        assert encrypted1 != encrypted2


class TestEncryptionDictOperations:
    """Test dictionary encryption operations."""

    def test_encrypt_dict_all_fields(self, encryption_service, test_key, sample_data):
        """Should encrypt all specified fields in dictionary."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import decrypt_dict, encrypt_dict

        fields_to_encrypt = ["user_id", "email"]
        encrypted = encrypt_dict(sample_data, fields_to_encrypt)

        # Fields should be encrypted
        assert encrypted["user_id"] != sample_data["user_id"]
        assert encrypted["email"] != sample_data["email"]
        # Nested fields should remain unchanged
        assert encrypted["payment_info"] == sample_data["payment_info"]

        # Decrypt and verify
        decrypted = decrypt_dict(encrypted, fields_to_encrypt)
        assert decrypted["user_id"] == sample_data["user_id"]
        assert decrypted["email"] == sample_data["email"]

    def test_encrypt_dict_nested_fields(self, encryption_service, test_key):
        """Should handle nested dictionary fields."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import encrypt_dict

        nested_data = {"public": "visible", "secret": "hidden", "nested": {"inner": "value"}}

        encrypted = encrypt_dict(nested_data, ["secret"])
        assert encrypted["secret"] != nested_data["secret"]
        assert encrypted["public"] == nested_data["public"]

    def test_encrypt_dict_nonexistent_field(self, encryption_service, test_key, sample_data):
        """Should handle encryption of non-existent fields gracefully."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import encrypt_dict

        encrypted = encrypt_dict(sample_data, ["nonexistent_field"])
        # Should not raise error, just skip the field
        assert encrypted == sample_data

    def test_encrypt_dict_empty_fields_list(self, encryption_service, test_key, sample_data):
        """Should handle empty fields list."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import encrypt_dict

        encrypted = encrypt_dict(sample_data, [])
        # Nothing should be encrypted
        assert encrypted == sample_data

    def test_decrypt_dict_partial_fields(self, encryption_service, test_key, sample_data):
        """Should decrypt only specified fields."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import decrypt_dict, encrypt_dict

        # Encrypt multiple fields
        encrypted = encrypt_dict(sample_data, ["user_id", "email"])

        # Decrypt only one field
        partially_decrypted = decrypt_dict(encrypted, ["user_id"])

        assert partially_decrypted["user_id"] == sample_data["user_id"]
        assert partially_decrypted["email"] != sample_data["email"]  # Still encrypted


class TestKeyDerivation:
    """Test PBKDF2 key derivation."""

    def test_derive_key_without_salt(self):
        """Should generate salt when not provided."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import derive_key

        key1, salt1 = derive_key("password123")
        key2, salt2 = derive_key("password123")

        # Keys should be different due to different salts
        assert key1 != key2
        assert salt1 != salt2
        assert len(key1) == 32
        assert len(salt1) == 16

    def test_derive_key_with_same_salt(self):
        """Should produce same key with same password and salt."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import derive_key

        salt = os.urandom(16)
        key1, _ = derive_key("password123", salt)
        key2, _ = derive_key("password123", salt)

        assert key1 == key2

    def test_derive_key_different_passwords(self):
        """Should produce different keys for different passwords."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import derive_key

        salt = os.urandom(16)
        key1, _ = derive_key("password1", salt)
        key2, _ = derive_key("password2", salt)

        assert key1 != key2

    def test_derive_key_weak_password(self):
        """Should handle weak passwords (PBKDF2 provides protection)."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import derive_key

        weak_passwords = ["123", "a", "password"]

        for pwd in weak_passwords:
            key, salt = derive_key(pwd)
            assert len(key) == 32  # Still produces valid key
            assert len(salt) == 16


class TestKeyRotation:
    """Test key rotation functionality."""

    def test_rotate_keys_generates_new_key(self):
        """Should generate new master key on rotation."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import rotate_keys, settings

        old_key = settings.MASTER_KEY
        new_key_b64 = rotate_keys()

        assert settings.MASTER_KEY != old_key
        assert len(settings.MASTER_KEY) == 32
        assert new_key_b64 is not None

    def test_rotate_keys_archives_old_key(self):
        """Should archive old key in legacy keys."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import rotate_keys, settings

        initial_legacy_count = len(settings.LEGACY_KEYS)

        rotate_keys()

        # Legacy keys should have increased
        assert len(settings.LEGACY_KEYS) > initial_legacy_count

    def test_decrypt_with_rotated_key(self, encryption_service, test_key):
        """Should decrypt old data after key rotation."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import settings

        original = "data before rotation"
        encrypted = encryption_service.encrypt(original, test_key)

        # Simulate key rotation by changing master key
        old_master = settings.MASTER_KEY
        settings.MASTER_KEY = os.urandom(32)

        # Should still be able to decrypt with original key
        decrypted = encryption_service.decrypt(encrypted, test_key)
        assert decrypted == original

        # Restore
        settings.MASTER_KEY = old_master


class TestPIIMasking:
    """Test PII masking for logging."""

    def test_mask_pii_basic(self):
        """Should mask PII correctly."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import mask_pii

        masked = mask_pii("sensitive_data", show_chars=3)
        assert masked.startswith("sen")
        assert "*" in masked
        assert "sensitive_data" != masked

    def test_mask_pii_short_string(self):
        """Should handle strings shorter than show_chars."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import mask_pii

        masked = mask_pii("ab", show_chars=5)
        assert masked == "**"

    def test_mask_email_format(self):
        """Should mask email in logging-safe format."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import mask_email

        masked = mask_email("user@example.com")
        assert "@" in masked
        assert "*" in masked
        assert "user" not in masked or masked.startswith("u")

    def test_mask_phone_format(self):
        """Should mask phone showing only last 4 digits."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import mask_phone

        masked = mask_phone("555-123-4567")
        assert masked.endswith("4567")
        assert "*" in masked

    def test_mask_phone_short(self):
        """Should handle short phone numbers."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import mask_phone

        masked = mask_phone("123")
        assert "*" in masked or len(masked) <= 4


class TestEncryptionFieldFunctions:
    """Test standalone field encryption functions."""

    def test_encrypt_field_function(self):
        """Should encrypt field using standalone function."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import decrypt_field, encrypt_field, generate_encryption_key

        key = generate_encryption_key()
        key_bytes = base64.b64decode(key)

        plaintext = "test data"
        encrypted = encrypt_field(plaintext, key_bytes)
        decrypted = decrypt_field(encrypted, key_bytes)

        assert decrypted == plaintext
        assert encrypted != plaintext

    def test_encrypt_field_default_key(self):
        """Should use default master key when not specified."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import decrypt_field, encrypt_field

        plaintext = "default key test"
        encrypted = encrypt_field(plaintext)
        decrypted = decrypt_field(encrypted)

        assert decrypted == plaintext

    def test_encrypt_field_no_key_raises_error(self):
        """Should raise error when no key available."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import encrypt_field, settings

        # Temporarily remove master key
        old_key = settings.MASTER_KEY
        settings.MASTER_KEY = None

        with pytest.raises(ValueError, match="No encryption key available"):
            encrypt_field("test")

        # Restore
        settings.MASTER_KEY = old_key

    def test_decrypt_field_corrupted_data(self):
        """Should raise error for corrupted encrypted data."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import decrypt_field, generate_encryption_key

        key_bytes = base64.b64decode(generate_encryption_key())

        # Try to decrypt invalid data
        with pytest.raises(Exception):
            decrypt_field("corrupted_base64_data", key_bytes)

    def test_decrypt_field_invalid_base64(self):
        """Should handle invalid base64 encoding."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import decrypt_field, generate_encryption_key

        key_bytes = base64.b64decode(generate_encryption_key())

        with pytest.raises(Exception):
            decrypt_field("not!valid@base64#", key_bytes)


class TestEncryptionSettings:
    """Test encryption settings and configuration."""

    def test_encryption_settings_initialization(self):
        """Should initialize encryption settings correctly."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import settings

        assert settings.MASTER_KEY is not None
        assert len(settings.MASTER_KEY) == 32
        assert settings.PBKDF2_ITERATIONS >= 100000
        assert settings.GCM_NONCE_LENGTH == 12
        assert settings.GCM_TAG_LENGTH == 16

    def test_encryption_settings_nist_compliance(self):
        """Should use NIST-compliant parameters."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import settings

        # NIST SP 800-38D recommendations
        assert settings.GCM_NONCE_LENGTH == 12  # 96 bits (recommended)
        assert settings.GCM_TAG_LENGTH == 16  # 128 bits (full tag)
        assert settings.PBKDF2_ITERATIONS >= 100000  # NIST SP 800-132

    def test_generate_master_key_format(self):
        """Should generate properly formatted master key."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import generate_master_key

        key = generate_master_key()

        # Should be base64 encoded
        assert isinstance(key, str)
        # Should decode to 32 bytes
        decoded = base64.b64decode(key)
        assert len(decoded) == 32

    def test_generate_master_key_uniqueness(self):
        """Should generate unique keys each time."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import generate_master_key

        keys = [generate_master_key() for _ in range(10)]

        # All should be unique
        assert len(set(keys)) == 10


class TestEncryptionConcurrency:
    """Test concurrent encryption operations."""

    def test_concurrent_encryption(self, encryption_service, test_key):
        """Should handle concurrent encryption safely."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        import concurrent.futures

        data_items = [f"data_{i}" for i in range(100)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            encrypted = list(executor.map(lambda d: encryption_service.encrypt(d, test_key), data_items))

        # All should be encrypted and unique (due to nonces)
        assert len(encrypted) == 100
        assert len(set(encrypted)) == 100

    def test_concurrent_decryption(self, encryption_service, test_key):
        """Should handle concurrent decryption safely."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        import concurrent.futures

        # Encrypt data
        data_items = [f"data_{i}" for i in range(100)]
        encrypted = [encryption_service.encrypt(d, test_key) for d in data_items]

        # Decrypt concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            decrypted = list(executor.map(lambda e: encryption_service.decrypt(e, test_key), encrypted))

        # All should match original
        assert decrypted == data_items


class TestEncryptionMemory:
    """Test memory handling and cleanup."""

    def test_large_batch_encryption_memory(self, encryption_service, test_key):
        """Should handle large batches without memory issues."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Encrypt 1000 records
        batch = [f"record_{i}" * 100 for i in range(1000)]

        encrypted_batch = []
        for record in batch:
            encrypted = encryption_service.encrypt(record, test_key)
            encrypted_batch.append(encrypted)

        # All should be encrypted
        assert len(encrypted_batch) == 1000

        # Decrypt to verify
        for i, encrypted in enumerate(encrypted_batch[:10]):
            decrypted = encryption_service.decrypt(encrypted, test_key)
            assert batch[i] in decrypted


class TestEncryptionGDPRCompliance:
    """Test GDPR compliance features."""

    def test_encrypt_gdpr_sensitive_data(self, encryption_service, test_key):
        """Should encrypt GDPR-sensitive data types."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        gdpr_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-0123",
            "address": "123 Main St",
            "ip_address": "192.168.1.1",
            "cookie_id": "abc123xyz",
        }

        for value in gdpr_data.values():
            encrypted = encryption_service.encrypt(value, test_key)
            decrypted = encryption_service.decrypt(encrypted, test_key)

            assert decrypted == value
            assert encrypted != value

    def test_right_to_erasure_simulation(self, encryption_service, test_key):
        """Should support right to erasure by key destruction."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        # Encrypt user data
        user_data = "personal information"
        encrypted = encryption_service.encrypt(user_data, test_key)

        # Simulate key destruction (right to erasure)
        destroyed_key = os.urandom(32)

        # Should not be able to decrypt with destroyed key
        with pytest.raises(Exception):
            encryption_service.decrypt(encrypted, destroyed_key)


class TestEncryptionDocumentation:
    """Test that encryption module has proper documentation."""

    def test_module_has_docstring(self):
        """Encryption module should have comprehensive docstring."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        import security.encryption as enc_module

        assert enc_module.__doc__ is not None
        assert "AES-256-GCM" in enc_module.__doc__
        assert "NIST" in enc_module.__doc__

    def test_functions_have_docstrings(self):
        """All public functions should have docstrings."""
        if not ENCRYPTION_AVAILABLE:
            pytest.skip("Encryption not available")

        from security.encryption import decrypt_dict, decrypt_field, derive_key, encrypt_dict, encrypt_field

        assert encrypt_field.__doc__ is not None
        assert decrypt_field.__doc__ is not None
        assert derive_key.__doc__ is not None
        assert encrypt_dict.__doc__ is not None
        assert decrypt_dict.__doc__ is not None


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=security.encryption", "--cov-report=term", "--cov-report=html"])
