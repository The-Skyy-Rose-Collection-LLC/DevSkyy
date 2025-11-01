#!/usr/bin/env python3
"""
WordPress Credentials Management for DevSkyy Platform
Secure credential handling with environment variables and validation
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class WordPressCredentials:
    """Secure WordPress credentials with validation."""
    site_url: str
    username: str
    password: str
    application_password: Optional[str] = None
    ftp_host: Optional[str] = None
    ftp_username: Optional[str] = None
    ftp_password: Optional[str] = None
    ftp_port: int = 21
    sftp_host: Optional[str] = None
    sftp_username: Optional[str] = None
    sftp_password: Optional[str] = None
    sftp_private_key_path: Optional[str] = None
    sftp_port: int = 22
    
    def __post_init__(self):
        """Validate credentials after initialization."""
        if not self.site_url:
            raise ValueError("WordPress site URL is required")
        if not self.username:
            raise ValueError("WordPress username is required")
        if not self.password:
            raise ValueError("WordPress password is required")
        
        # Ensure site URL has proper format
        if not self.site_url.startswith(('http://', 'https://')):
            self.site_url = f"https://{self.site_url}"
        
        # Remove trailing slash
        self.site_url = self.site_url.rstrip('/')
    
    def get_rest_api_url(self) -> str:
        """Get WordPress REST API base URL."""
        return f"{self.site_url}/wp-json/wp/v2"
    
    def has_ftp_credentials(self) -> bool:
        """Check if FTP credentials are available."""
        return bool(self.ftp_host and self.ftp_username and self.ftp_password)
    
    def has_sftp_credentials(self) -> bool:
        """Check if SFTP credentials are available."""
        return bool(self.sftp_host and self.sftp_username and 
                   (self.sftp_password or self.sftp_private_key_path))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "site_url": self.site_url,
            "username": self.username,
            "has_application_password": bool(self.application_password),
            "has_ftp_credentials": self.has_ftp_credentials(),
            "has_sftp_credentials": self.has_sftp_credentials(),
            "ftp_host": self.ftp_host,
            "ftp_port": self.ftp_port,
            "sftp_host": self.sftp_host,
            "sftp_port": self.sftp_port
        }

class WordPressCredentialsManager:
    """
    Manages WordPress credentials securely using environment variables.
    Supports multiple WordPress sites and credential types.
    """
    
    def __init__(self):
        self._credentials_cache = {}
        self._load_default_credentials()
    
    def _load_default_credentials(self):
        """Load default Skyy Rose Collection credentials from environment."""
        try:
            # Primary Skyy Rose Collection site
            skyy_rose_credentials = self._load_credentials_from_env("SKYY_ROSE")
            if skyy_rose_credentials:
                self._credentials_cache["skyy_rose"] = skyy_rose_credentials
                logger.info("✅ Skyy Rose Collection credentials loaded")
            
            # Secondary/staging site if configured
            staging_credentials = self._load_credentials_from_env("SKYY_ROSE_STAGING")
            if staging_credentials:
                self._credentials_cache["skyy_rose_staging"] = staging_credentials
                logger.info("✅ Skyy Rose staging credentials loaded")
            
        except Exception as e:
            logger.error(f"❌ Failed to load default credentials: {e}")
    
    def _load_credentials_from_env(self, prefix: str) -> Optional[WordPressCredentials]:
        """Load credentials from environment variables with given prefix."""
        site_url = os.getenv(f"{prefix}_SITE_URL")
        username = os.getenv(f"{prefix}_USERNAME")
        password = os.getenv(f"{prefix}_PASSWORD")
        
        if not all([site_url, username, password]):
            return None
        
        return WordPressCredentials(
            site_url=site_url,
            username=username,
            password=password,
            application_password=os.getenv(f"{prefix}_APP_PASSWORD"),
            ftp_host=os.getenv(f"{prefix}_FTP_HOST"),
            ftp_username=os.getenv(f"{prefix}_FTP_USERNAME"),
            ftp_password=os.getenv(f"{prefix}_FTP_PASSWORD"),
            ftp_port=int(os.getenv(f"{prefix}_FTP_PORT", "21")),
            sftp_host=os.getenv(f"{prefix}_SFTP_HOST"),
            sftp_username=os.getenv(f"{prefix}_SFTP_USERNAME"),
            sftp_password=os.getenv(f"{prefix}_SFTP_PASSWORD"),
            sftp_private_key_path=os.getenv(f"{prefix}_SFTP_PRIVATE_KEY"),
            sftp_port=int(os.getenv(f"{prefix}_SFTP_PORT", "22"))
        )
    
    def get_credentials(self, site_key: str = "skyy_rose") -> Optional[WordPressCredentials]:
        """Get credentials for a specific site."""
        return self._credentials_cache.get(site_key)
    
    def add_credentials(self, site_key: str, credentials: WordPressCredentials):
        """Add credentials for a site."""
        self._credentials_cache[site_key] = credentials
        logger.info(f"✅ Added credentials for site: {site_key}")
    
    def list_available_sites(self) -> list:
        """List all available site keys."""
        return list(self._credentials_cache.keys())
    
    def validate_credentials(self, site_key: str) -> Dict[str, Any]:
        """Validate credentials for a site."""
        credentials = self.get_credentials(site_key)
        if not credentials:
            return {"valid": False, "error": "Credentials not found"}
        
        validation_result = {
            "valid": True,
            "site_url": credentials.site_url,
            "username": credentials.username,
            "has_application_password": bool(credentials.application_password),
            "has_ftp_credentials": credentials.has_ftp_credentials(),
            "has_sftp_credentials": credentials.has_sftp_credentials(),
            "rest_api_url": credentials.get_rest_api_url()
        }
        
        return validation_result
    
    def get_default_credentials(self) -> Optional[WordPressCredentials]:
        """Get default Skyy Rose Collection credentials."""
        return self.get_credentials("skyy_rose")

# Global credentials manager instance
wordpress_credentials_manager = WordPressCredentialsManager()

# Convenience functions
def get_skyy_rose_credentials() -> Optional[WordPressCredentials]:
    """Get Skyy Rose Collection credentials."""
    return wordpress_credentials_manager.get_default_credentials()

def get_credentials_for_site(site_key: str) -> Optional[WordPressCredentials]:
    """Get credentials for any configured site."""
    return wordpress_credentials_manager.get_credentials(site_key)

def validate_site_credentials(site_key: str = "skyy_rose") -> Dict[str, Any]:
    """Validate credentials for a site."""
    return wordpress_credentials_manager.validate_credentials(site_key)

def list_configured_sites() -> list:
    """List all configured WordPress sites."""
    return wordpress_credentials_manager.list_available_sites()

# Environment variable validation
def validate_environment_setup() -> Dict[str, Any]:
    """Validate that required environment variables are set."""
    required_vars = [
        "SKYY_ROSE_SITE_URL",
        "SKYY_ROSE_USERNAME", 
        "SKYY_ROSE_PASSWORD"
    ]
    
    optional_vars = [
        "SKYY_ROSE_APP_PASSWORD",
        "SKYY_ROSE_FTP_HOST",
        "SKYY_ROSE_FTP_USERNAME",
        "SKYY_ROSE_FTP_PASSWORD",
        "SKYY_ROSE_SFTP_HOST",
        "SKYY_ROSE_SFTP_USERNAME",
        "SKYY_ROSE_SFTP_PASSWORD",
        "SKYY_ROSE_SFTP_PRIVATE_KEY"
    ]
    
    result = {
        "valid": True,
        "missing_required": [],
        "missing_optional": [],
        "configured_vars": []
    }
    
    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            result["missing_required"].append(var)
            result["valid"] = False
        else:
            result["configured_vars"].append(var)
    
    # Check optional variables
    for var in optional_vars:
        if not os.getenv(var):
            result["missing_optional"].append(var)
        else:
            result["configured_vars"].append(var)
    
    return result

# Configuration templates for easy setup
def generate_env_template() -> str:
    """Generate .env template with WordPress credentials."""
    return """
# ============================================================================
# WORDPRESS CREDENTIALS FOR SKYY ROSE COLLECTION
# ============================================================================

# Primary Skyy Rose Collection Site
SKYY_ROSE_SITE_URL=https://your-wordpress-site.com
SKYY_ROSE_USERNAME=your-wp-admin-username
SKYY_ROSE_PASSWORD=your-wp-admin-password
SKYY_ROSE_APP_PASSWORD=your-application-password  # Optional but recommended

# FTP Credentials (Optional - for FTP deployment)
SKYY_ROSE_FTP_HOST=ftp.your-hosting-provider.com
SKYY_ROSE_FTP_USERNAME=your-ftp-username
SKYY_ROSE_FTP_PASSWORD=your-ftp-password
SKYY_ROSE_FTP_PORT=21

# SFTP Credentials (Optional - for SFTP deployment)
SKYY_ROSE_SFTP_HOST=sftp.your-hosting-provider.com
SKYY_ROSE_SFTP_USERNAME=your-sftp-username
SKYY_ROSE_SFTP_PASSWORD=your-sftp-password  # Use this OR private key
SKYY_ROSE_SFTP_PRIVATE_KEY=/path/to/private/key  # Use this OR password
SKYY_ROSE_SFTP_PORT=22

# Staging Site (Optional)
SKYY_ROSE_STAGING_SITE_URL=https://staging.your-wordpress-site.com
SKYY_ROSE_STAGING_USERNAME=staging-username
SKYY_ROSE_STAGING_PASSWORD=staging-password
SKYY_ROSE_STAGING_APP_PASSWORD=staging-app-password

# ============================================================================
# OTHER DEVSKYY CONFIGURATION
# ============================================================================

# DevSkyy API Configuration
DEVSKYY_API_KEY=your-devskyy-api-key
DEVSKYY_API_URL=http://localhost:8000

# Security
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///devskyy.db

# External APIs
OPENAI_API_KEY=your-openai-api-key
STRIPE_API_KEY=your-stripe-api-key

# Logging
LOG_LEVEL=INFO
DEBUG=false
"""

def save_env_template(file_path: str = ".env.template"):
    """Save environment template to file."""
    template = generate_env_template()
    with open(file_path, 'w') as f:
        f.write(template)
    logger.info(f"✅ Environment template saved to: {file_path}")

if __name__ == "__main__":
    # Test credential loading
    print("🔐 WordPress Credentials Manager Test")
    print("=" * 50)
    
    # Validate environment setup
    env_validation = validate_environment_setup()
    print(f"Environment validation: {'✅ VALID' if env_validation['valid'] else '❌ INVALID'}")
    
    if env_validation['missing_required']:
        print(f"Missing required variables: {env_validation['missing_required']}")
    
    if env_validation['configured_vars']:
        print(f"Configured variables: {len(env_validation['configured_vars'])}")
    
    # Test credential loading
    credentials = get_skyy_rose_credentials()
    if credentials:
        print(f"✅ Skyy Rose credentials loaded: {credentials.site_url}")
        print(f"   Username: {credentials.username}")
        print(f"   Has app password: {bool(credentials.application_password)}")
        print(f"   Has FTP: {credentials.has_ftp_credentials()}")
        print(f"   Has SFTP: {credentials.has_sftp_credentials()}")
    else:
        print("❌ No Skyy Rose credentials found")
    
    # List all sites
    sites = list_configured_sites()
    print(f"Configured sites: {sites}")
