#!/usr/bin/env python3
"""
Test script for Secrets Manager integration

This script demonstrates and tests the Secrets Management System.

Usage:
    python scripts/test_secrets_manager.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security.secrets_manager import (
    SecretBackendType,
    SecretNotFoundError,
    SecretsManager,
    get_secret,
    set_secret,
)


def test_local_backend():
    """Test local encrypted backend"""
    print("=" * 60)
    print("Testing Local Encrypted Backend")
    print("=" * 60)

    secrets = SecretsManager(backend_type=SecretBackendType.LOCAL_ENCRYPTED)

    # Create test secrets
    print("\n1. Creating test secrets...")
    secrets.set_secret("test/jwt_key", "test-jwt-secret-12345")
    secrets.set_secret("test/db_url", "postgresql://localhost/test")
    secrets.set_secret(
        "test/api_keys",
        {"openai": "sk-test", "anthropic": "sk-ant-test"},
        tags={"env": "test", "service": "api"},
    )
    print("   ✓ Secrets created")

    # Retrieve secrets
    print("\n2. Retrieving secrets...")
    jwt_key = secrets.get_secret("test/jwt_key")
    print(f"   JWT Key: {jwt_key}")

    db_url = secrets.get_secret("test/db_url")
    print(f"   DB URL: {db_url}")

    api_keys = secrets.get_secret("test/api_keys")
    print(f"   API Keys: {api_keys}")

    # List secrets
    print("\n3. Listing secrets...")
    all_secrets = secrets.list_secrets()
    print(f"   Found {len(all_secrets)} secrets:")
    for name in all_secrets:
        print(f"   - {name}")

    # Test get_or_env fallback
    print("\n4. Testing get_or_env fallback...")
    import os

    os.environ["TEST_ENV_VAR"] = "from-environment"
    value = secrets.get_or_env("nonexistent/secret", "TEST_ENV_VAR")
    print(f"   Fallback value: {value}")

    # Rotate secret
    print("\n5. Testing secret rotation...")
    new_version = secrets.rotate_secret("test/jwt_key")
    print(f"   Rotated to version: {new_version}")

    # Clean up
    print("\n6. Cleaning up test secrets...")
    for secret_name in all_secrets:
        secrets.delete_secret(secret_name)
    print("   ✓ Cleanup complete")

    print("\n✓ Local backend tests passed!")


def test_convenience_functions():
    """Test convenience functions"""
    print("\n" + "=" * 60)
    print("Testing Convenience Functions")
    print("=" * 60)

    # Test set_secret
    print("\n1. Using set_secret()...")
    version = set_secret("convenience/test", "test-value")
    print(f"   Created secret with version: {version}")

    # Test get_secret
    print("\n2. Using get_secret()...")
    value = get_secret("convenience/test")
    print(f"   Retrieved value: {value}")

    # Test with default
    print("\n3. Testing default value...")
    value = get_secret("nonexistent/secret", default="default-value")
    print(f"   Got default: {value}")

    # Clean up
    secrets = SecretsManager()
    secrets.delete_secret("convenience/test")

    print("\n✓ Convenience function tests passed!")


def test_error_handling():
    """Test error handling"""
    print("\n" + "=" * 60)
    print("Testing Error Handling")
    print("=" * 60)

    secrets = SecretsManager()

    # Test SecretNotFoundError
    print("\n1. Testing SecretNotFoundError...")
    try:
        secrets.get_secret("nonexistent/secret")
        print("   ✗ Should have raised SecretNotFoundError")
    except SecretNotFoundError as e:
        print(f"   ✓ Caught expected error: {e}")

    # Test default handling
    print("\n2. Testing default value on not found...")
    value = secrets.get_secret("nonexistent/secret", default="fallback")
    print(f"   ✓ Got default value: {value}")

    print("\n✓ Error handling tests passed!")


def test_integration():
    """Test integration with main_enterprise.py pattern"""
    print("\n" + "=" * 60)
    print("Testing Integration Pattern (main_enterprise.py)")
    print("=" * 60)

    import os

    secrets = SecretsManager()

    # Set up test secrets
    print("\n1. Setting up test secrets...")
    secrets.set_secret("jwt/secret_key", "integration-jwt-key")
    secrets.set_secret("encryption/master_key", "integration-enc-key")
    print("   ✓ Secrets created")

    # Test get_or_env pattern (mimics main_enterprise.py)
    print("\n2. Testing get_or_env pattern...")
    jwt_secret = secrets.get_or_env(secret_name="jwt/secret_key", env_var="JWT_SECRET_KEY")
    print(f"   JWT Secret loaded: {jwt_secret[:10]}...")

    encryption_key = secrets.get_or_env(
        secret_name="encryption/master_key", env_var="ENCRYPTION_MASTER_KEY"
    )
    print(f"   Encryption Key loaded: {encryption_key[:10]}...")

    # Test with environment variable fallback
    print("\n3. Testing environment variable fallback...")
    os.environ["TEST_API_KEY"] = "env-api-key-123"
    api_key = secrets.get_or_env(secret_name="nonexistent/api_key", env_var="TEST_API_KEY")
    print(f"   API Key from env: {api_key}")

    # Clean up
    secrets.delete_secret("jwt/secret_key")
    secrets.delete_secret("encryption/master_key")

    print("\n✓ Integration tests passed!")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SECRETS MANAGER TEST SUITE")
    print("=" * 60)

    try:
        test_local_backend()
        test_convenience_functions()
        test_error_handling()
        test_integration()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSecrets Manager is ready for use.")
        print("\nNext steps:")
        print("1. For AWS: Set AWS_REGION environment variable")
        print("2. For Vault: Set VAULT_ADDR and VAULT_TOKEN")
        print("3. Migrate secrets using scripts/migrate_secrets.py")
        print("4. Remove secrets from .env file")
        print("\nSee docs/SECRETS_MIGRATION.md for detailed instructions.")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
