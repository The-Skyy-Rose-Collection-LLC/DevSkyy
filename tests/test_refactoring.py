"""
Test suite for refactored shared utilities

This ensures the refactored code maintains the same functionality
as the original duplicated code.
"""

from datetime import datetime, timedelta


def test_security_manager_imports():
    """Test that SecurityManager can be imported."""
    from utils.security import SecurityManager, get_security_manager
    
    # Create instance
    sm = SecurityManager()
    assert sm is not None
    
    # Get global instance
    global_sm = get_security_manager()
    assert global_sm is not None


def test_password_hashing():
    """Test password hashing and verification."""
    from utils.security import SecurityManager
    
    sm = SecurityManager()
    
    # Hash a password
    password = "TestPassword123!"
    hashed = sm.get_password_hash(password)
    
    # Verify correct password
    assert sm.verify_password(password, hashed) is True
    
    # Verify incorrect password
    assert sm.verify_password("WrongPassword", hashed) is False


def test_jwt_tokens():
    """Test JWT token creation and verification."""
    from utils.security import SecurityManager
    
    sm = SecurityManager()
    
    # Create token
    data = {"sub": "testuser", "user_id": 123}
    token = sm.create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    
    # Verify token
    payload = sm.verify_token(token)
    assert payload is not None
    assert payload["sub"] == "testuser"
    assert payload["user_id"] == 123
    assert "exp" in payload


def test_encryption():
    """Test AES-256-GCM encryption and decryption."""
    from utils.security import SecurityManager
    
    sm = SecurityManager()
    
    # Encrypt data
    plaintext = "Secret data to encrypt"
    encrypted = sm.encrypt_data(plaintext)
    
    assert encrypted is not None
    assert encrypted != plaintext
    assert isinstance(encrypted, str)
    
    # Decrypt data
    decrypted = sm.decrypt_data(encrypted)
    assert decrypted == plaintext


def test_config_imports():
    """Test that configuration can be imported and accessed."""
    from config.settings import (
        PlatformConfig,
        DatabaseConfig,
        SecurityConfig,
        APIConfig,
        PromptConfig,
        get_config
    )
    
    # Get config
    config = get_config()
    
    assert config is not None
    assert isinstance(config, PlatformConfig)
    assert isinstance(config.database, DatabaseConfig)
    assert isinstance(config.security, SecurityConfig)
    assert isinstance(config.api, APIConfig)
    assert isinstance(config.prompt, PromptConfig)


def test_config_defaults():
    """Test configuration default values."""
    from config.settings import get_config
    
    config = get_config()
    
    # Check defaults
    assert config.app_name == "DevSkyy Enterprise Platform"
    assert config.app_version == "5.1.0"
    assert config.debug is True
    
    # Database defaults
    assert config.database.use_wal is True
    assert config.database.timeout == 30.0
    
    # Security defaults
    assert config.security.algorithm == "HS256"
    assert config.security.access_token_expire_minutes == 30
    assert config.security.password_min_length == 8
    
    # API defaults
    assert config.api.max_retries == 3
    assert config.api.timeout_seconds == 60.0


def test_api_client_imports():
    """Test that API client utilities can be imported."""
    from utils.api_client import (
        ResponseFormat,
        make_api_request,
        handle_api_error,
        format_response
    )
    
    assert ResponseFormat.JSON is not None
    assert ResponseFormat.MARKDOWN is not None
    assert callable(make_api_request)
    assert callable(handle_api_error)
    assert callable(format_response)


def test_response_formatting():
    """Test response formatting in different formats."""
    from utils.api_client import format_response, ResponseFormat
    
    test_data = {
        "status": "success",
        "count": 42,
        "items": ["item1", "item2", "item3"]
    }
    
    # Test JSON format
    json_output = format_response(test_data, ResponseFormat.JSON)
    assert '"status": "success"' in json_output
    assert '"count": 42' in json_output
    
    # Test Markdown format
    markdown_output = format_response(test_data, ResponseFormat.MARKDOWN, "Test Results")
    assert "# Test Results" in markdown_output
    assert "**Status:** success" in markdown_output
    assert "**Count:** 42" in markdown_output


def test_error_response_formatting():
    """Test error response formatting."""
    from utils.api_client import format_response, ResponseFormat
    
    error_data = {
        "error": "Something went wrong",
        "details": "Additional error information"
    }
    
    # Test Markdown format
    output = format_response(error_data, ResponseFormat.MARKDOWN)
    assert "❌ **Error:**" in output
    assert "Something went wrong" in output
    assert "**Details:**" in output


if __name__ == "__main__":
    print("Running refactoring tests...")
    print("\n1. Testing security manager...")
    test_security_manager_imports()
    test_password_hashing()
    test_jwt_tokens()
    test_encryption()
    print("✅ Security tests passed")
    
    print("\n2. Testing configuration...")
    test_config_imports()
    test_config_defaults()
    print("✅ Configuration tests passed")
    
    print("\n3. Testing API client...")
    test_api_client_imports()
    test_response_formatting()
    test_error_response_formatting()
    print("✅ API client tests passed")
    
    print("\n✅ All refactoring tests passed!")
    print("The refactored code maintains the same functionality as the original.")
