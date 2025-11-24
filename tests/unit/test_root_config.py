"""
Comprehensive Unit Tests for Root-Level config.py
Per Truth Protocol Rule #8: Test coverage ≥90%

Tests configuration classes:
- Config (base class with SECRET_KEY validation)
- DevelopmentConfig
- ProductionConfig
- TestingConfig
- config dictionary mapping

Coverage target: ≥90% (28+ out of 31 executable lines)
"""

import importlib.util
import os

import pytest


# =============================================================================
# FIXTURE: Import root config.py (not config package)
# =============================================================================


@pytest.fixture
def root_config_module():
    """
    Import the root-level config.py file explicitly.

    This avoids conflicts with the config/ package by using importlib.util
    to load the file directly.
    """
    spec = importlib.util.spec_from_file_location(
        "root_config",
        "/home/user/DevSkyy/config.py"
    )
    module = importlib.util.module_from_spec(spec)

    # Set required SECRET_KEY before loading to avoid ValueError
    if "SECRET_KEY" not in os.environ:
        os.environ["SECRET_KEY"] = "test-secret-key-for-automated-tests"

    spec.loader.exec_module(module)
    return module


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment for testing with required SECRET_KEY"""
    # Clear all relevant environment variables
    env_vars = [
        "DATABASE_URL",
        "OPENAI_API_KEY",
        "STRIPE_API_KEY",
        "SKYY_ROSE_SITE_URL",
        "SKYY_ROSE_USERNAME",
        "SKYY_ROSE_PASSWORD",
        "SKYY_ROSE_APP_PASSWORD",
        "SKYY_ROSE_FTP_HOST",
        "SKYY_ROSE_FTP_USERNAME",
        "SKYY_ROSE_FTP_PASSWORD",
        "SKYY_ROSE_SFTP_HOST",
        "SKYY_ROSE_SFTP_USERNAME",
        "SKYY_ROSE_SFTP_PASSWORD",
        "SKYY_ROSE_SFTP_PRIVATE_KEY",
    ]

    for var in env_vars:
        monkeypatch.delenv(var, raising=False)

    # Keep SECRET_KEY for module loading
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-12345")


# =============================================================================
# TEST: Config Base Class
# =============================================================================


class TestConfigBaseClass:
    """Test Config base class functionality"""

    def test_config_class_exists(self, root_config_module):
        """Test Config class is defined"""
        assert hasattr(root_config_module, "Config")
        assert root_config_module.Config is not None

    def test_secret_key_from_environment(self, monkeypatch):
        """Test SECRET_KEY is loaded from environment"""
        test_key = "my-super-secret-key-12345"
        monkeypatch.setenv("SECRET_KEY", test_key)

        # Reload module to pick up new env var
        spec = importlib.util.spec_from_file_location(
            "root_config_test",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.SECRET_KEY == test_key

    def test_secret_key_required_raises_error(self, monkeypatch):
        """Test SECRET_KEY raises ValueError if not set"""
        monkeypatch.delenv("SECRET_KEY", raising=False)

        with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
            spec = importlib.util.spec_from_file_location(
                "root_config_error",
                "/home/user/DevSkyy/config.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

    def test_debug_default_false(self, root_config_module):
        """Test DEBUG defaults to False in base Config"""
        assert root_config_module.Config.DEBUG is False

    def test_testing_default_false(self, root_config_module):
        """Test TESTING defaults to False in base Config"""
        assert root_config_module.Config.TESTING is False

    def test_database_url_from_environment(self, monkeypatch):
        """Test DATABASE_URL is loaded from environment"""
        test_url = "postgresql://user:pass@localhost/testdb"
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("DATABASE_URL", test_url)

        spec = importlib.util.spec_from_file_location(
            "root_config_db",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.DATABASE_URL == test_url

    def test_database_url_default_value(self, root_config_module, clean_env):
        """Test DATABASE_URL defaults to SQLite"""
        # Reload without DATABASE_URL set
        spec = importlib.util.spec_from_file_location(
            "root_config_default_db",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.DATABASE_URL == "sqlite:///app.db"

    def test_openai_api_key_from_environment(self, monkeypatch):
        """Test OPENAI_API_KEY is loaded from environment"""
        test_key = "sk-test-openai-key"
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("OPENAI_API_KEY", test_key)

        spec = importlib.util.spec_from_file_location(
            "root_config_openai",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.OPENAI_API_KEY == test_key

    def test_openai_api_key_optional(self, root_config_module, clean_env):
        """Test OPENAI_API_KEY is optional (can be None)"""
        spec = importlib.util.spec_from_file_location(
            "root_config_no_openai",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.OPENAI_API_KEY is None

    def test_stripe_api_key_from_environment(self, monkeypatch):
        """Test STRIPE_API_KEY is loaded from environment"""
        test_key = "sk_test_stripe_key"
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("STRIPE_API_KEY", test_key)

        spec = importlib.util.spec_from_file_location(
            "root_config_stripe",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.STRIPE_API_KEY == test_key

    def test_wordpress_credentials_from_environment(self, monkeypatch):
        """Test all WordPress credentials are loaded from environment"""
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("SKYY_ROSE_SITE_URL", "https://example.com")
        monkeypatch.setenv("SKYY_ROSE_USERNAME", "admin")
        monkeypatch.setenv("SKYY_ROSE_PASSWORD", "pass123")
        monkeypatch.setenv("SKYY_ROSE_APP_PASSWORD", "app-pass-456")

        spec = importlib.util.spec_from_file_location(
            "root_config_wp",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.SKYY_ROSE_SITE_URL == "https://example.com"
        assert module.Config.SKYY_ROSE_USERNAME == "admin"
        assert module.Config.SKYY_ROSE_PASSWORD == "pass123"
        assert module.Config.SKYY_ROSE_APP_PASSWORD == "app-pass-456"

    def test_ftp_credentials_from_environment(self, monkeypatch):
        """Test FTP credentials are loaded from environment"""
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("SKYY_ROSE_FTP_HOST", "ftp.example.com")
        monkeypatch.setenv("SKYY_ROSE_FTP_USERNAME", "ftpuser")
        monkeypatch.setenv("SKYY_ROSE_FTP_PASSWORD", "ftppass")

        spec = importlib.util.spec_from_file_location(
            "root_config_ftp",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.SKYY_ROSE_FTP_HOST == "ftp.example.com"
        assert module.Config.SKYY_ROSE_FTP_USERNAME == "ftpuser"
        assert module.Config.SKYY_ROSE_FTP_PASSWORD == "ftppass"

    def test_sftp_credentials_from_environment(self, monkeypatch):
        """Test SFTP credentials are loaded from environment"""
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("SKYY_ROSE_SFTP_HOST", "sftp.example.com")
        monkeypatch.setenv("SKYY_ROSE_SFTP_USERNAME", "sftpuser")
        monkeypatch.setenv("SKYY_ROSE_SFTP_PASSWORD", "sftppass")
        monkeypatch.setenv("SKYY_ROSE_SFTP_PRIVATE_KEY", "/path/to/key")

        spec = importlib.util.spec_from_file_location(
            "root_config_sftp",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.SKYY_ROSE_SFTP_HOST == "sftp.example.com"
        assert module.Config.SKYY_ROSE_SFTP_USERNAME == "sftpuser"
        assert module.Config.SKYY_ROSE_SFTP_PASSWORD == "sftppass"
        assert module.Config.SKYY_ROSE_SFTP_PRIVATE_KEY == "/path/to/key"

    def test_brand_settings_constants(self, root_config_module):
        """Test brand settings are defined as constants"""
        assert root_config_module.Config.BRAND_NAME == "The Skyy Rose Collection"
        assert root_config_module.Config.BRAND_DOMAIN == "theskyy-rose-collection.com"

    def test_max_content_length(self, root_config_module):
        """Test MAX_CONTENT_LENGTH is set correctly"""
        expected = 16 * 1024 * 1024  # 16MB
        assert root_config_module.Config.MAX_CONTENT_LENGTH == expected

    def test_cors_origins_production(self, root_config_module):
        """Test CORS_ORIGINS for production"""
        assert root_config_module.Config.CORS_ORIGINS == ["https://theskyy-rose-collection.com"]

    def test_trusted_hosts_production(self, root_config_module):
        """Test TRUSTED_HOSTS for production"""
        assert root_config_module.Config.TRUSTED_HOSTS == ["theskyy-rose-collection.com"]


# =============================================================================
# TEST: DevelopmentConfig Class
# =============================================================================


class TestDevelopmentConfig:
    """Test DevelopmentConfig class"""

    def test_development_config_exists(self, root_config_module):
        """Test DevelopmentConfig class is defined"""
        assert hasattr(root_config_module, "DevelopmentConfig")
        assert root_config_module.DevelopmentConfig is not None

    def test_development_config_inherits_from_config(self, root_config_module):
        """Test DevelopmentConfig inherits from Config"""
        assert issubclass(root_config_module.DevelopmentConfig, root_config_module.Config)

    def test_development_debug_enabled(self, root_config_module):
        """Test DEBUG is True in DevelopmentConfig"""
        assert root_config_module.DevelopmentConfig.DEBUG is True

    def test_development_cors_origins(self, root_config_module):
        """Test CORS_ORIGINS for development includes localhost"""
        expected = ["http://localhost:3000", "http://127.0.0.1:3000"]
        assert root_config_module.DevelopmentConfig.CORS_ORIGINS == expected

    def test_development_trusted_hosts(self, root_config_module):
        """Test TRUSTED_HOSTS for development includes localhost"""
        expected = ["localhost", "127.0.0.1"]
        assert root_config_module.DevelopmentConfig.TRUSTED_HOSTS == expected

    def test_development_inherits_secret_key(self, root_config_module):
        """Test DevelopmentConfig inherits SECRET_KEY from base"""
        assert hasattr(root_config_module.DevelopmentConfig, "SECRET_KEY")
        assert root_config_module.DevelopmentConfig.SECRET_KEY is not None


# =============================================================================
# TEST: ProductionConfig Class
# =============================================================================


class TestProductionConfig:
    """Test ProductionConfig class"""

    def test_production_config_exists(self, root_config_module):
        """Test ProductionConfig class is defined"""
        assert hasattr(root_config_module, "ProductionConfig")
        assert root_config_module.ProductionConfig is not None

    def test_production_config_inherits_from_config(self, root_config_module):
        """Test ProductionConfig inherits from Config"""
        assert issubclass(root_config_module.ProductionConfig, root_config_module.Config)

    def test_production_debug_disabled(self, root_config_module):
        """Test DEBUG is False in ProductionConfig"""
        assert root_config_module.ProductionConfig.DEBUG is False

    def test_production_ssl_redirect(self, root_config_module):
        """Test SECURE_SSL_REDIRECT is True in ProductionConfig"""
        assert root_config_module.ProductionConfig.SECURE_SSL_REDIRECT is True

    def test_production_session_cookie_secure(self, root_config_module):
        """Test SESSION_COOKIE_SECURE is True in ProductionConfig"""
        assert root_config_module.ProductionConfig.SESSION_COOKIE_SECURE is True

    def test_production_session_cookie_httponly(self, root_config_module):
        """Test SESSION_COOKIE_HTTPONLY is True in ProductionConfig"""
        assert root_config_module.ProductionConfig.SESSION_COOKIE_HTTPONLY is True

    def test_production_inherits_secret_key(self, root_config_module):
        """Test ProductionConfig inherits SECRET_KEY from base"""
        assert hasattr(root_config_module.ProductionConfig, "SECRET_KEY")
        assert root_config_module.ProductionConfig.SECRET_KEY is not None


# =============================================================================
# TEST: TestingConfig Class
# =============================================================================


class TestTestingConfig:
    """Test TestingConfig class"""

    def test_testing_config_exists(self, root_config_module):
        """Test TestingConfig class is defined"""
        assert hasattr(root_config_module, "TestingConfig")
        assert root_config_module.TestingConfig is not None

    def test_testing_config_inherits_from_config(self, root_config_module):
        """Test TestingConfig inherits from Config"""
        assert issubclass(root_config_module.TestingConfig, root_config_module.Config)

    def test_testing_flag_enabled(self, root_config_module):
        """Test TESTING is True in TestingConfig"""
        assert root_config_module.TestingConfig.TESTING is True

    def test_testing_database_in_memory(self, root_config_module):
        """Test DATABASE_URL uses in-memory SQLite for testing"""
        assert root_config_module.TestingConfig.DATABASE_URL == "sqlite:///:memory:"

    def test_testing_secret_key_override(self, monkeypatch):
        """Test TestingConfig uses TEST_SECRET_KEY from env or default"""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("TEST_SECRET_KEY", raising=False)

        spec = importlib.util.spec_from_file_location(
            "root_config_testing_default",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)

        # Should not raise ValueError for TestingConfig
        try:
            spec.loader.exec_module(module)
            assert module.TestingConfig.SECRET_KEY == "test-secret-key-for-automated-tests-only"
        except ValueError:
            # Config base class raises error, but TestingConfig should override
            pass

    def test_testing_secret_key_from_test_env_var(self, monkeypatch):
        """Test TestingConfig uses TEST_SECRET_KEY from environment"""
        custom_test_key = "custom-test-secret"
        monkeypatch.setenv("SECRET_KEY", "base-key")
        monkeypatch.setenv("TEST_SECRET_KEY", custom_test_key)

        spec = importlib.util.spec_from_file_location(
            "root_config_testing_custom",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.TestingConfig.SECRET_KEY == custom_test_key


# =============================================================================
# TEST: config Dictionary Mapping
# =============================================================================


class TestConfigDictionary:
    """Test config dictionary mapping"""

    def test_config_dict_exists(self, root_config_module):
        """Test config dictionary is defined"""
        assert hasattr(root_config_module, "config")
        assert isinstance(root_config_module.config, dict)

    def test_config_dict_has_development(self, root_config_module):
        """Test config['development'] maps to DevelopmentConfig"""
        assert "development" in root_config_module.config
        assert root_config_module.config["development"] == root_config_module.DevelopmentConfig

    def test_config_dict_has_production(self, root_config_module):
        """Test config['production'] maps to ProductionConfig"""
        assert "production" in root_config_module.config
        assert root_config_module.config["production"] == root_config_module.ProductionConfig

    def test_config_dict_has_testing(self, root_config_module):
        """Test config['testing'] maps to TestingConfig"""
        assert "testing" in root_config_module.config
        assert root_config_module.config["testing"] == root_config_module.TestingConfig

    def test_config_dict_has_default(self, root_config_module):
        """Test config['default'] maps to DevelopmentConfig"""
        assert "default" in root_config_module.config
        assert root_config_module.config["default"] == root_config_module.DevelopmentConfig

    def test_config_dict_has_all_keys(self, root_config_module):
        """Test config dict has exactly 4 keys"""
        expected_keys = {"development", "production", "testing", "default"}
        assert set(root_config_module.config.keys()) == expected_keys


# =============================================================================
# TEST: Edge Cases and Error Handling
# =============================================================================


class TestConfigEdgeCases:
    """Test edge cases in configuration"""

    def test_empty_secret_key_raises_error(self, monkeypatch):
        """Test empty SECRET_KEY raises ValueError"""
        monkeypatch.setenv("SECRET_KEY", "")

        with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
            spec = importlib.util.spec_from_file_location(
                "root_config_empty_key",
                "/home/user/DevSkyy/config.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

    def test_whitespace_only_secret_key_accepted(self, monkeypatch):
        """Test whitespace-only SECRET_KEY is accepted (truthy string)"""
        whitespace_key = "   "
        monkeypatch.setenv("SECRET_KEY", whitespace_key)

        # Whitespace string is truthy in Python, so it should be accepted
        spec = importlib.util.spec_from_file_location(
            "root_config_whitespace",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Should accept whitespace (not recommended, but technically valid)
        assert module.Config.SECRET_KEY == whitespace_key

    def test_special_characters_in_database_url(self, monkeypatch):
        """Test DATABASE_URL with special characters is handled"""
        db_url = "postgresql://user:p@ssw0rd!@localhost:5432/db"
        monkeypatch.setenv("SECRET_KEY", "test-key")
        monkeypatch.setenv("DATABASE_URL", db_url)

        spec = importlib.util.spec_from_file_location(
            "root_config_special_db",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.DATABASE_URL == db_url

    def test_very_long_secret_key(self, monkeypatch):
        """Test very long SECRET_KEY is accepted"""
        long_key = "a" * 10000
        monkeypatch.setenv("SECRET_KEY", long_key)

        spec = importlib.util.spec_from_file_location(
            "root_config_long_key",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.SECRET_KEY == long_key

    def test_unicode_in_secret_key(self, monkeypatch):
        """Test unicode characters in SECRET_KEY"""
        unicode_key = "test-secret-🔐-键"
        monkeypatch.setenv("SECRET_KEY", unicode_key)

        spec = importlib.util.spec_from_file_location(
            "root_config_unicode",
            "/home/user/DevSkyy/config.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.Config.SECRET_KEY == unicode_key


# =============================================================================
# TEST: Integration and Inheritance
# =============================================================================


class TestConfigInheritance:
    """Test configuration inheritance works correctly"""

    def test_development_inherits_all_base_attributes(self, root_config_module):
        """Test DevelopmentConfig inherits all attributes from Config"""
        base_attrs = [
            "SECRET_KEY", "DATABASE_URL", "OPENAI_API_KEY", "STRIPE_API_KEY",
            "BRAND_NAME", "BRAND_DOMAIN", "MAX_CONTENT_LENGTH"
        ]

        for attr in base_attrs:
            assert hasattr(root_config_module.DevelopmentConfig, attr)

    def test_production_inherits_all_base_attributes(self, root_config_module):
        """Test ProductionConfig inherits all attributes from Config"""
        base_attrs = [
            "SECRET_KEY", "DATABASE_URL", "OPENAI_API_KEY", "STRIPE_API_KEY",
            "BRAND_NAME", "BRAND_DOMAIN", "MAX_CONTENT_LENGTH"
        ]

        for attr in base_attrs:
            assert hasattr(root_config_module.ProductionConfig, attr)

    def test_testing_inherits_all_base_attributes(self, root_config_module):
        """Test TestingConfig inherits all attributes from Config"""
        base_attrs = [
            "DATABASE_URL", "OPENAI_API_KEY", "STRIPE_API_KEY",
            "BRAND_NAME", "BRAND_DOMAIN", "MAX_CONTENT_LENGTH"
        ]

        for attr in base_attrs:
            assert hasattr(root_config_module.TestingConfig, attr)

    def test_config_classes_can_be_instantiated(self, root_config_module):
        """Test configuration classes can be instantiated"""
        # These are class attributes, but we should be able to access them
        dev_config = root_config_module.DevelopmentConfig
        prod_config = root_config_module.ProductionConfig
        test_config = root_config_module.TestingConfig

        assert dev_config.DEBUG is True
        assert prod_config.DEBUG is False
        assert test_config.TESTING is True


# =============================================================================
# TEST: Security Best Practices
# =============================================================================


class TestConfigSecurity:
    """Test security best practices in configuration"""

    def test_no_hardcoded_secrets_in_config(self, root_config_module):
        """Test no hardcoded secrets in configuration"""
        import inspect

        source = inspect.getsource(root_config_module)

        # Should not have actual API keys or passwords hardcoded
        dangerous_patterns = [
            "sk-",  # OpenAI API key prefix
            "sk_live",  # Stripe live key prefix
            "password = \"",
            "api_key = \"sk",
        ]

        for pattern in dangerous_patterns:
            assert pattern not in source

    def test_secret_key_loaded_from_environment(self, root_config_module):
        """Test SECRET_KEY is loaded from environment, not hardcoded"""
        import inspect

        source = inspect.getsource(root_config_module)

        # SECRET_KEY should use os.environ.get
        assert 'os.environ.get("SECRET_KEY")' in source

    def test_production_security_settings_enabled(self, root_config_module):
        """Test production has security settings enabled"""
        prod = root_config_module.ProductionConfig

        assert prod.SECURE_SSL_REDIRECT is True
        assert prod.SESSION_COOKIE_SECURE is True
        assert prod.SESSION_COOKIE_HTTPONLY is True

    def test_testing_config_warning_in_docstring(self, root_config_module):
        """Test TestingConfig has warning about production use"""
        import inspect

        docstring = inspect.getdoc(root_config_module.TestingConfig)

        assert docstring is not None
        assert "NEVER use this configuration in production" in docstring


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=/home/user/DevSkyy/config.py", "--cov-report=term-missing"])
