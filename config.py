import os

from dotenv import load_dotenv

"""
Production Configuration for The Skyy Rose Collection Platform
"""

load_dotenv()

class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set for security")
    DEBUG = False
    TESTING = False

    # Database
    DATABASE_URL = os.environ.get("DATABASE_URL") or "sqlite:///app.db"

    # API Keys
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

    # WordPress Credentials (Skyy Rose Collection)
    SKYY_ROSE_SITE_URL = os.environ.get("SKYY_ROSE_SITE_URL")
    SKYY_ROSE_USERNAME = os.environ.get("SKYY_ROSE_USERNAME")
    SKYY_ROSE_PASSWORD = os.environ.get("SKYY_ROSE_PASSWORD")
    SKYY_ROSE_APP_PASSWORD = os.environ.get("SKYY_ROSE_APP_PASSWORD")

    # FTP/SFTP Credentials
    SKYY_ROSE_FTP_HOST = os.environ.get("SKYY_ROSE_FTP_HOST")
    SKYY_ROSE_FTP_USERNAME = os.environ.get("SKYY_ROSE_FTP_USERNAME")
    SKYY_ROSE_FTP_PASSWORD = os.environ.get("SKYY_ROSE_FTP_PASSWORD")
    SKYY_ROSE_SFTP_HOST = os.environ.get("SKYY_ROSE_SFTP_HOST")
    SKYY_ROSE_SFTP_USERNAME = os.environ.get("SKYY_ROSE_SFTP_USERNAME")
    SKYY_ROSE_SFTP_PASSWORD = os.environ.get("SKYY_ROSE_SFTP_PASSWORD")
    SKYY_ROSE_SFTP_PRIVATE_KEY = os.environ.get("SKYY_ROSE_SFTP_PRIVATE_KEY")

    # Brand Settings
    BRAND_NAME = "The Skyy Rose Collection"
    BRAND_DOMAIN = "theskyy-rose-collection.com"

    # Performance
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Security
    CORS_ORIGINS = ["https://theskyy-rose-collection.com"]
    TRUSTED_HOSTS = ["theskyy-rose-collection.com"]

class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    TRUSTED_HOSTS = ["localhost", "127.0.0.1"]

class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False

    # Enhanced security for production
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-key"  # Allow test secret key

# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
