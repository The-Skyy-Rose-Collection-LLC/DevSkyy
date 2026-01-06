#!/usr/bin/env python3
"""
DevSkyy - Environment Configuration Validator
==============================================

Validates environment configuration before deployment to ensure all required
secrets, API keys, and configuration values are present and properly formatted.

Usage:
    python scripts/validate_environment.py [env_file]
    python scripts/validate_environment.py .env.production
    python scripts/validate_environment.py  # defaults to .env.production

Exit Codes:
    0 - Validation passed (all required vars present)
    1 - Validation failed (missing required vars or invalid format)

Validation Checks:
    - Required security secrets (JWT, encryption, session)
    - Database configuration and format
    - Redis configuration and format
    - At least one LLM provider API key
    - Optional feature-specific keys (warnings only)
    - Password strength and format
    - URL format validation
"""

import os
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
except ImportError:
    print("❌ Error: python-dotenv not installed")
    print("💡 Install with: pip install python-dotenv")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


class ValidationResult:
    """Holds validation results with errors, warnings, and info messages."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []
        self.validated_vars: list[str] = []

    def add_error(self, message: str) -> None:
        """Add a critical error that will fail validation."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a warning that won't fail validation but should be reviewed."""
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        """Add informational message about successful validation."""
        self.info.append(message)

    def add_validated(self, var_name: str) -> None:
        """Mark a variable as successfully validated."""
        self.validated_vars.append(var_name)

    def is_valid(self) -> bool:
        """Return True if no errors were found."""
        return len(self.errors) == 0

    def print_summary(self) -> None:
        """Print formatted validation summary."""
        print(f"\n{Colors.BLUE}{'=' * 80}{Colors.NC}")
        print(f"{Colors.BLUE}Validation Summary{Colors.NC}")
        print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}\n")

        # Print errors
        if self.errors:
            print(f"{Colors.RED}❌ CRITICAL ERRORS ({len(self.errors)}):{Colors.NC}")
            for error in self.errors:
                print(f"   {Colors.RED}✗{Colors.NC} {error}")
            print()

        # Print warnings
        if self.warnings:
            print(f"{Colors.YELLOW}⚠️  WARNINGS ({len(self.warnings)}):{Colors.NC}")
            for warning in self.warnings:
                print(f"   {Colors.YELLOW}!{Colors.NC} {warning}")
            print()

        # Print validated variables
        if self.validated_vars:
            print(
                f"{Colors.GREEN}✓ Validated Variables ({len(self.validated_vars)}):{Colors.NC}"
            )
            for var in self.validated_vars:
                print(f"   {Colors.GREEN}✓{Colors.NC} {var}")
            print()

        # Print info messages
        if self.info:
            print(f"{Colors.CYAN}ℹ️  Information:{Colors.NC}")
            for info in self.info:
                print(f"   {Colors.CYAN}•{Colors.NC} {info}")
            print()

        # Final result
        print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}")
        if self.is_valid():
            print(f"{Colors.GREEN}✅ VALIDATION PASSED{Colors.NC}")
            if self.warnings:
                print(
                    f"{Colors.YELLOW}⚠️  {len(self.warnings)} warning(s) - review recommended{Colors.NC}"
                )
        else:
            print(f"{Colors.RED}❌ VALIDATION FAILED{Colors.NC}")
            print(
                f"{Colors.RED}{len(self.errors)} critical error(s) must be fixed{Colors.NC}"
            )
        print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}\n")


def validate_env_var_set(var_name: str, result: ValidationResult) -> bool:
    """Check if environment variable is set and non-empty."""
    value = os.getenv(var_name)
    if not value or value.strip() == "":
        result.add_error(f"Missing required variable: {var_name}")
        return False
    result.add_validated(var_name)
    return True


def validate_secret_strength(
    var_name: str, min_length: int, result: ValidationResult
) -> bool:
    """Validate that a secret meets minimum length requirements."""
    value = os.getenv(var_name)
    if not value:
        return False

    if len(value) < min_length:
        result.add_error(
            f"{var_name} is too short (min {min_length} chars, got {len(value)})"
        )
        return False

    result.add_info(f"{var_name}: {len(value)} characters (strong)")
    return True


def validate_database_url(url: str, result: ValidationResult) -> bool:
    """Validate PostgreSQL connection string format."""
    if not url:
        result.add_error("DATABASE_URL is required")
        return False

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ["postgresql", "postgresql+asyncpg", "postgres"]:
            result.add_error(
                f"DATABASE_URL: Invalid scheme '{parsed.scheme}' (expected postgresql/postgresql+asyncpg)"
            )
            return False

        # Check host
        if not parsed.hostname:
            result.add_error("DATABASE_URL: Missing hostname")
            return False

        # Check database name
        if not parsed.path or parsed.path == "/":
            result.add_error("DATABASE_URL: Missing database name")
            return False

        # Check credentials
        if not parsed.username:
            result.add_warning("DATABASE_URL: Missing username")
        if not parsed.password:
            result.add_warning("DATABASE_URL: Missing password")

        # Security check: warn about localhost in production
        if parsed.hostname in ["localhost", "127.0.0.1"]:
            result.add_warning(
                "DATABASE_URL uses localhost - update for production deployment"
            )

        result.add_info(
            f"Database: {parsed.scheme}://{parsed.hostname}:{parsed.port or 5432}{parsed.path}"
        )
        return True

    except Exception as e:
        result.add_error(f"DATABASE_URL: Invalid format - {e}")
        return False


def validate_redis_url(url: str, result: ValidationResult) -> bool:
    """Validate Redis connection string format."""
    if not url:
        result.add_error("REDIS_URL is required")
        return False

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ["redis", "rediss"]:
            result.add_error(
                f"REDIS_URL: Invalid scheme '{parsed.scheme}' (expected redis/rediss)"
            )
            return False

        # Check host
        if not parsed.hostname:
            result.add_error("REDIS_URL: Missing hostname")
            return False

        # Warn about localhost
        if parsed.hostname in ["localhost", "127.0.0.1"]:
            result.add_warning(
                "REDIS_URL uses localhost - update for production deployment"
            )

        # Check for TLS in production
        if parsed.scheme == "redis":
            result.add_warning(
                "REDIS_URL uses unencrypted connection - consider using rediss:// for production"
            )

        result.add_info(
            f"Redis: {parsed.scheme}://{parsed.hostname}:{parsed.port or 6379}/{parsed.path.lstrip('/') or '0'}"
        )
        return True

    except Exception as e:
        result.add_error(f"REDIS_URL: Invalid format - {e}")
        return False


def validate_wordpress_url(url: str, result: ValidationResult) -> bool:
    """Validate WordPress site URL format."""
    if not url:
        result.add_warning("WORDPRESS_URL not set - WordPress integration disabled")
        return True

    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            result.add_error(
                f"WORDPRESS_URL: Invalid scheme '{parsed.scheme}' (expected http/https)"
            )
            return False

        # Check for HTTPS in production
        if parsed.scheme == "http":
            result.add_warning(
                "WORDPRESS_URL uses HTTP - use HTTPS for production deployment"
            )

        # Check host
        if not parsed.hostname:
            result.add_error("WORDPRESS_URL: Missing hostname")
            return False

        result.add_info(f"WordPress: {url}")
        return True

    except Exception as e:
        result.add_error(f"WORDPRESS_URL: Invalid format - {e}")
        return False


def validate_llm_providers(result: ValidationResult) -> bool:
    """Validate that at least one LLM provider API key is configured."""
    llm_providers = {
        "OpenAI": "OPENAI_API_KEY",
        "Anthropic": "ANTHROPIC_API_KEY",
        "Google AI": "GOOGLE_AI_API_KEY",
        "Mistral": "MISTRAL_API_KEY",
        "Cohere": "COHERE_API_KEY",
        "Groq": "GROQ_API_KEY",
    }

    configured_providers = []
    for provider_name, env_var in llm_providers.items():
        if os.getenv(env_var):
            configured_providers.append(provider_name)
            result.add_validated(env_var)

    if not configured_providers:
        result.add_error(
            "No LLM provider API keys configured - at least one is required"
        )
        result.add_info(
            f"Available providers: {', '.join(llm_providers.keys())}"
        )
        return False

    result.add_info(f"LLM Providers: {', '.join(configured_providers)}")
    return True


def validate_optional_features(result: ValidationResult) -> None:
    """Check optional feature API keys and provide warnings/info."""
    optional_keys = {
        "3D Generation": {
            "TRIPO_API_KEY": "Tripo3D (3D model generation)",
            "FASHN_API_KEY": "FASHN (virtual try-on)",
        },
        "Image Generation": {
            "STABILITY_API_KEY": "Stability AI (Stable Diffusion)",
            "REPLICATE_API_TOKEN": "Replicate (model hosting)",
        },
        "E-commerce": {
            "WOOCOMMERCE_KEY": "WooCommerce API key",
            "WOOCOMMERCE_SECRET": "WooCommerce API secret",
        },
        "Monitoring": {
            "SENTRY_DSN": "Sentry error tracking",
            "DD_API_KEY": "DataDog APM",
            "NEW_RELIC_LICENSE_KEY": "New Relic monitoring",
        },
        "Email/Notifications": {
            "SENDGRID_API_KEY": "SendGrid email",
            "TWILIO_ACCOUNT_SID": "Twilio SMS",
        },
        "Payments": {
            "STRIPE_SECRET_KEY": "Stripe payments",
        },
    }

    for category, keys in optional_keys.items():
        configured = []
        missing = []

        for key, description in keys.items():
            if os.getenv(key):
                configured.append(description)
                result.add_validated(key)
            else:
                missing.append(description)

        if configured:
            result.add_info(f"{category}: {', '.join(configured)}")

        if missing:
            result.add_warning(
                f"{category} features disabled: {', '.join(missing)}"
            )


def validate_security_settings(result: ValidationResult) -> None:
    """Validate security-related configuration."""
    # Check DEBUG mode
    debug = os.getenv("DEBUG", "false").lower()
    if debug in ["true", "1", "yes"]:
        result.add_error(
            "DEBUG=true in production environment - MUST be false for security"
        )
    else:
        result.add_info("Debug mode: disabled (correct for production)")

    # Check environment
    env = os.getenv("ENVIRONMENT", "development")
    if env.lower() == "production":
        result.add_info("Environment: production")
    else:
        result.add_warning(f"ENVIRONMENT={env} (expected 'production')")

    # Check SSL/HTTPS settings
    ssl_redirect = os.getenv("SECURE_SSL_REDIRECT", "false").lower()
    if ssl_redirect not in ["true", "1", "yes"]:
        result.add_warning(
            "SECURE_SSL_REDIRECT not enabled - HTTPS redirects recommended for production"
        )

    session_secure = os.getenv("SESSION_COOKIE_SECURE", "false").lower()
    if session_secure not in ["true", "1", "yes"]:
        result.add_warning(
            "SESSION_COOKIE_SECURE not enabled - secure cookies recommended for production"
        )


def validate_environment(env_file: str) -> bool:
    """
    Main validation function.

    Args:
        env_file: Path to environment file to validate

    Returns:
        True if validation passed, False otherwise
    """
    result = ValidationResult()

    # Check if file exists
    env_path = Path(env_file)
    if not env_path.exists():
        print(f"{Colors.RED}❌ Error: {env_file} not found{Colors.NC}")
        print(f"{Colors.YELLOW}💡 Generate with: ./scripts/generate_secrets.sh{Colors.NC}")
        return False

    print(f"{Colors.BLUE}🔍 DevSkyy Environment Validator{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 80}{Colors.NC}")
    print(f"{Colors.CYAN}Validating: {env_file}{Colors.NC}\n")

    # Load environment file
    load_dotenv(env_file)

    # 1. Validate core security secrets
    print(f"{Colors.PURPLE}Checking security secrets...{Colors.NC}")
    validate_env_var_set("JWT_SECRET_KEY", result)
    validate_secret_strength("JWT_SECRET_KEY", 64, result)

    validate_env_var_set("ENCRYPTION_MASTER_KEY", result)
    validate_secret_strength("ENCRYPTION_MASTER_KEY", 32, result)

    validate_env_var_set("SESSION_SECRET", result)
    validate_secret_strength("SESSION_SECRET", 32, result)

    # 2. Validate database configuration
    print(f"{Colors.PURPLE}Checking database configuration...{Colors.NC}")
    database_url = os.getenv("DATABASE_URL")
    validate_database_url(database_url, result)

    # 3. Validate Redis configuration
    print(f"{Colors.PURPLE}Checking Redis configuration...{Colors.NC}")
    redis_url = os.getenv("REDIS_URL")
    validate_redis_url(redis_url, result)

    # 4. Validate LLM providers
    print(f"{Colors.PURPLE}Checking LLM providers...{Colors.NC}")
    validate_llm_providers(result)

    # 5. Validate WordPress configuration (optional)
    print(f"{Colors.PURPLE}Checking WordPress configuration...{Colors.NC}")
    wordpress_url = os.getenv("WORDPRESS_URL")
    if wordpress_url:
        validate_wordpress_url(wordpress_url, result)

    # 6. Validate optional features
    print(f"{Colors.PURPLE}Checking optional features...{Colors.NC}")
    validate_optional_features(result)

    # 7. Validate security settings
    print(f"{Colors.PURPLE}Checking security settings...{Colors.NC}")
    validate_security_settings(result)

    # Print summary
    result.print_summary()

    return result.is_valid()


def main():
    """Main entry point."""
    # Get environment file from command line or use default
    env_file = sys.argv[1] if len(sys.argv) > 1 else ".env.production"

    # Run validation
    success = validate_environment(env_file)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
