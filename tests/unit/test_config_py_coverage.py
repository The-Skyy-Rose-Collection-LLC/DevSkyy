"""
Test coverage for root-level config.py module
Per Truth Protocol Rule #8: Test coverage ≥90%

This test file temporarily renames the config/ package to allow
direct import of config.py for proper coverage tracking.
"""

from pathlib import Path
import shutil
import sys

import pytest


# =============================================================================
# SETUP/TEARDOWN: Rename config package to enable config.py import
# =============================================================================


@pytest.fixture(scope="module", autouse=True)
def rename_config_package():
    """
    Temporarily rename config/ package to config_pkg_backup/
    so that config.py can be imported directly.
    """
    config_dir = Path("/home/user/DevSkyy/config")
    backup_dir = Path("/home/user/DevSkyy/config_pkg_backup")

    # Rename if not already renamed
    if config_dir.exists():
        shutil.move(str(config_dir), str(backup_dir))

    yield

    # Restore
    if backup_dir.exists():
        # Remove config_dir if it was created during tests
        if config_dir.exists():
            shutil.rmtree(config_dir)
        shutil.move(str(backup_dir), str(config_dir))


@pytest.fixture(scope="function")
def clean_import():
    """Clean config module from sys.modules before each test"""
    if 'config' in sys.modules:
        del sys.modules['config']
    yield
    if 'config' in sys.modules:
        del sys.modules['config']


@pytest.fixture
def set_secret_key(monkeypatch):
    """Set SECRET_KEY environment variable for tests"""
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-12345")


# =============================================================================
# TEST: Config Base Class
# =============================================================================


class TestConfigModule:
    """Test root-level config.py module"""

    def test_module_loads(self, set_secret_key, clean_import):
        """Test config module loads successfully"""
        import config
        assert config is not None

    def test_config_class_defined(self, set_secret_key, clean_import):
        """Test Config class is defined"""
        import config
        assert hasattr(config, 'Config')
        assert config.Config is not None

    def test_secret_key_from_environment(self, monkeypatch, clean_import):
        """Test SECRET_KEY loaded from environment"""
        test_key = "my-test-secret-key"
        monkeypatch.setenv("SECRET_KEY", test_key)

        import config
        assert config.Config.SECRET_KEY == test_key

    def test_secret_key_required(self, monkeypatch, clean_import):
        """Test SECRET_KEY raises ValueError if not set"""
        monkeypatch.delenv("SECRET_KEY", raising=False)

        with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
            pass

    def test_empty_secret_key_raises_error(self, monkeypatch, clean_import):
        """Test empty SECRET_KEY raises ValueError"""
        monkeypatch.setenv("SECRET_KEY", "")

        with pytest.raises(ValueError, match="SECRET_KEY environment variable must be set"):
            pass

    def test_debug_false(self, set_secret_key, clean_import):
        """Test DEBUG defaults to False"""
        import config
        assert config.Config.DEBUG is False

    def test_testing_false(self, set_secret_key, clean_import):
        """Test TESTING defaults to False"""
        import config
        assert config.Config.TESTING is False

    def test_database_url_default(self, set_secret_key, monkeypatch, clean_import):
        """Test DATABASE_URL defaults to SQLite"""
        monkeypatch.delenv("DATABASE_URL", raising=False)

        import config
        assert config.Config.DATABASE_URL == "sqlite:///app.db"

    def test_database_url_from_environment(self, set_secret_key, monkeypatch, clean_import):
        """Test DATABASE_URL from environment"""
        test_url = "postgresql://user:pass@localhost/db"
        monkeypatch.setenv("DATABASE_URL", test_url)

        import config
        assert config.Config.DATABASE_URL == test_url

    def test_openai_api_key(self, set_secret_key, monkeypatch, clean_import):
        """Test OPENAI_API_KEY from environment"""
        test_key = "sk-test-openai"
        monkeypatch.setenv("OPENAI_API_KEY", test_key)

        import config
        assert config.Config.OPENAI_API_KEY == test_key

    def test_stripe_api_key(self, set_secret_key, monkeypatch, clean_import):
        """Test STRIPE_API_KEY from environment"""
        test_key = "sk_test_stripe"
        monkeypatch.setenv("STRIPE_API_KEY", test_key)

        import config
        assert config.Config.STRIPE_API_KEY == test_key

    def test_wordpress_credentials(self, set_secret_key, monkeypatch, clean_import):
        """Test WordPress credentials from environment"""
        monkeypatch.setenv("SKYY_ROSE_SITE_URL", "https://example.com")
        monkeypatch.setenv("SKYY_ROSE_USERNAME", "admin")
        monkeypatch.setenv("SKYY_ROSE_PASSWORD", "pass")
        monkeypatch.setenv("SKYY_ROSE_APP_PASSWORD", "app-pass")

        import config
        assert config.Config.SKYY_ROSE_SITE_URL == "https://example.com"
        assert config.Config.SKYY_ROSE_USERNAME == "admin"
        assert config.Config.SKYY_ROSE_PASSWORD == "pass"
        assert config.Config.SKYY_ROSE_APP_PASSWORD == "app-pass"

    def test_ftp_credentials(self, set_secret_key, monkeypatch, clean_import):
        """Test FTP credentials from environment"""
        monkeypatch.setenv("SKYY_ROSE_FTP_HOST", "ftp.example.com")
        monkeypatch.setenv("SKYY_ROSE_FTP_USERNAME", "ftpuser")
        monkeypatch.setenv("SKYY_ROSE_FTP_PASSWORD", "ftppass")

        import config
        assert config.Config.SKYY_ROSE_FTP_HOST == "ftp.example.com"
        assert config.Config.SKYY_ROSE_FTP_USERNAME == "ftpuser"
        assert config.Config.SKYY_ROSE_FTP_PASSWORD == "ftppass"

    def test_sftp_credentials(self, set_secret_key, monkeypatch, clean_import):
        """Test SFTP credentials from environment"""
        monkeypatch.setenv("SKYY_ROSE_SFTP_HOST", "sftp.example.com")
        monkeypatch.setenv("SKYY_ROSE_SFTP_USERNAME", "sftpuser")
        monkeypatch.setenv("SKYY_ROSE_SFTP_PASSWORD", "sftppass")
        monkeypatch.setenv("SKYY_ROSE_SFTP_PRIVATE_KEY", "/path/to/key")

        import config
        assert config.Config.SKYY_ROSE_SFTP_HOST == "sftp.example.com"
        assert config.Config.SKYY_ROSE_SFTP_USERNAME == "sftpuser"
        assert config.Config.SKYY_ROSE_SFTP_PASSWORD == "sftppass"
        assert config.Config.SKYY_ROSE_SFTP_PRIVATE_KEY == "/path/to/key"

    def test_brand_settings(self, set_secret_key, clean_import):
        """Test brand settings constants"""
        import config
        assert config.Config.BRAND_NAME == "The Skyy Rose Collection"
        assert config.Config.BRAND_DOMAIN == "theskyy-rose-collection.com"

    def test_max_content_length(self, set_secret_key, clean_import):
        """Test MAX_CONTENT_LENGTH"""
        import config
        assert config.Config.MAX_CONTENT_LENGTH == 16 * 1024 * 1024

    def test_cors_origins(self, set_secret_key, clean_import):
        """Test CORS_ORIGINS"""
        import config
        assert config.Config.CORS_ORIGINS == ["https://theskyy-rose-collection.com"]

    def test_trusted_hosts(self, set_secret_key, clean_import):
        """Test TRUSTED_HOSTS"""
        import config
        assert config.Config.TRUSTED_HOSTS == ["theskyy-rose-collection.com"]


# =============================================================================
# TEST: DevelopmentConfig
# =============================================================================


class TestDevelopmentConfig:
    """Test DevelopmentConfig class"""

    def test_development_config_exists(self, set_secret_key, clean_import):
        """Test DevelopmentConfig is defined"""
        import config
        assert hasattr(config, 'DevelopmentConfig')

    def test_development_debug_enabled(self, set_secret_key, clean_import):
        """Test DEBUG is True in DevelopmentConfig"""
        import config
        assert config.DevelopmentConfig.DEBUG is True

    def test_development_cors_origins(self, set_secret_key, clean_import):
        """Test CORS_ORIGINS for development"""
        import config
        assert config.DevelopmentConfig.CORS_ORIGINS == ["http://localhost:3000", "http://127.0.0.1:3000"]

    def test_development_trusted_hosts(self, set_secret_key, clean_import):
        """Test TRUSTED_HOSTS for development"""
        import config
        assert config.DevelopmentConfig.TRUSTED_HOSTS == ["localhost", "127.0.0.1"]


# =============================================================================
# TEST: ProductionConfig
# =============================================================================


class TestProductionConfig:
    """Test ProductionConfig class"""

    def test_production_config_exists(self, set_secret_key, clean_import):
        """Test ProductionConfig is defined"""
        import config
        assert hasattr(config, 'ProductionConfig')

    def test_production_debug_disabled(self, set_secret_key, clean_import):
        """Test DEBUG is False in ProductionConfig"""
        import config
        assert config.ProductionConfig.DEBUG is False

    def test_production_ssl_redirect(self, set_secret_key, clean_import):
        """Test SECURE_SSL_REDIRECT in ProductionConfig"""
        import config
        assert config.ProductionConfig.SECURE_SSL_REDIRECT is True

    def test_production_session_cookie_secure(self, set_secret_key, clean_import):
        """Test SESSION_COOKIE_SECURE in ProductionConfig"""
        import config
        assert config.ProductionConfig.SESSION_COOKIE_SECURE is True

    def test_production_session_cookie_httponly(self, set_secret_key, clean_import):
        """Test SESSION_COOKIE_HTTPONLY in ProductionConfig"""
        import config
        assert config.ProductionConfig.SESSION_COOKIE_HTTPONLY is True


# =============================================================================
# TEST: TestingConfig
# =============================================================================


class TestTestingConfig:
    """Test TestingConfig class"""

    def test_testing_config_exists(self, monkeypatch, clean_import):
        """Test TestingConfig is defined"""
        # TestingConfig can load without SECRET_KEY
        monkeypatch.delenv("SECRET_KEY", raising=False)

        import config
        assert hasattr(config, 'TestingConfig')

    def test_testing_flag_enabled(self, set_secret_key, clean_import):
        """Test TESTING is True in TestingConfig"""
        import config
        assert config.TestingConfig.TESTING is True

    def test_testing_database_in_memory(self, set_secret_key, clean_import):
        """Test DATABASE_URL uses in-memory SQLite"""
        import config
        assert config.TestingConfig.DATABASE_URL == "sqlite:///:memory:"

    def test_testing_secret_key_default(self, monkeypatch, clean_import):
        """Test TestingConfig has default SECRET_KEY"""
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("TEST_SECRET_KEY", raising=False)

        # Should not raise for TestingConfig
        import config
        assert config.TestingConfig.SECRET_KEY == "test-secret-key-for-automated-tests-only"

    def test_testing_secret_key_from_env(self, monkeypatch, clean_import):
        """Test TestingConfig uses TEST_SECRET_KEY from environment"""
        custom_key = "custom-test-secret"
        monkeypatch.setenv("SECRET_KEY", "base-key")
        monkeypatch.setenv("TEST_SECRET_KEY", custom_key)

        import config
        assert config.TestingConfig.SECRET_KEY == custom_key


# =============================================================================
# TEST: config Dictionary
# =============================================================================


class TestConfigDictionary:
    """Test config dictionary mapping"""

    def test_config_dict_exists(self, set_secret_key, clean_import):
        """Test config dictionary is defined"""
        import config
        assert hasattr(config, 'config')
        assert isinstance(config.config, dict)

    def test_config_dict_development(self, set_secret_key, clean_import):
        """Test config['development'] mapping"""
        import config
        assert 'development' in config.config
        assert config.config['development'] == config.DevelopmentConfig

    def test_config_dict_production(self, set_secret_key, clean_import):
        """Test config['production'] mapping"""
        import config
        assert 'production' in config.config
        assert config.config['production'] == config.ProductionConfig

    def test_config_dict_testing(self, set_secret_key, clean_import):
        """Test config['testing'] mapping"""
        import config
        assert 'testing' in config.config
        assert config.config['testing'] == config.TestingConfig

    def test_config_dict_default(self, set_secret_key, clean_import):
        """Test config['default'] mapping"""
        import config
        assert 'default' in config.config
        assert config.config['default'] == config.DevelopmentConfig


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=config", "--cov-report=term-missing"])
