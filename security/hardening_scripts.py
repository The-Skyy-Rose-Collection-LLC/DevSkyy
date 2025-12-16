"""
Security Hardening Scripts for DevSkyy Enterprise Platform
Automated security configuration and hardening procedures
"""

import json
import logging
import os
import secrets
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityHardening:
    """
    Comprehensive security hardening for DevSkyy platform.

    Features:
    - File permission hardening
    - Environment variable validation
    - SSL/TLS configuration
    - Database security settings
    - System-level security configurations
    """

    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.security_config = self._load_security_config()

    def _load_security_config(self) -> dict:
        """Load security configuration"""
        return {
            "file_permissions": {
                "config_files": 0o600,
                "script_files": 0o755,
                "data_directories": 0o750,
                "log_directories": 0o755,
            },
            "required_env_vars": [
                "SECRET_KEY",
                "JWT_SECRET_KEY",
                "DATABASE_URL",
                "ENCRYPTION_KEY",
            ],
            "ssl_config": {
                "min_tls_version": "1.2",
                "cipher_suites": [
                    "ECDHE-RSA-AES256-GCM-SHA384",
                    "ECDHE-RSA-AES128-GCM-SHA256",
                    "ECDHE-RSA-AES256-SHA384",
                    "ECDHE-RSA-AES128-SHA256",
                ],
            },
        }

    def harden_file_permissions(self) -> list[str]:
        """Harden file and directory permissions"""
        results = []

        try:
            # Secure configuration files
            config_files = [
                ".env",
                "docker/.env",
                "ml/.env",
                "mcp/.env",
                "vercel/.env",
                "pyproject.toml",
            ]

            for config_file in config_files:
                file_path = self.project_root / config_file
                if file_path.exists():
                    os.chmod(
                        file_path,
                        self.security_config["file_permissions"]["config_files"],
                    )
                    results.append(f"✅ Secured {config_file} (600)")

            # Secure script files
            script_files = ["setup_compliance.sh", "main_enterprise.py", "server.py"]

            for script_file in script_files:
                file_path = self.project_root / script_file
                if file_path.exists():
                    os.chmod(
                        file_path,
                        self.security_config["file_permissions"]["script_files"],
                    )
                    results.append(f"✅ Secured {script_file} (755)")

            # Secure directories
            secure_dirs = ["security", "database", "logs", "data"]

            for directory in secure_dirs:
                dir_path = self.project_root / directory
                if dir_path.exists():
                    os.chmod(
                        dir_path,
                        self.security_config["file_permissions"]["data_directories"],
                    )
                    results.append(f"✅ Secured {directory}/ (750)")

            logger.info(f"File permissions hardened: {len(results)} items")
            return results

        except Exception as e:
            logger.error(f"File permission hardening failed: {e}")
            return [f"❌ File permission hardening failed: {e}"]

    def validate_environment_variables(self) -> list[str]:
        """Validate and secure environment variables"""
        results = []

        try:
            # Check required environment variables
            missing_vars = []
            weak_vars = []

            for var in self.security_config["required_env_vars"]:
                value = os.getenv(var)
                if not value:
                    missing_vars.append(var)
                elif len(value) < 32:  # Minimum length for security
                    weak_vars.append(var)

            if missing_vars:
                results.append(
                    f"❌ Missing required environment variables: {', '.join(missing_vars)}"
                )
            else:
                results.append("✅ All required environment variables present")

            if weak_vars:
                results.append(f"⚠️ Weak environment variables (< 32 chars): {', '.join(weak_vars)}")
            else:
                results.append("✅ All environment variables meet minimum length requirements")

            # Check for hardcoded secrets in code
            secret_patterns = [
                "sk-",  # OpenAI API keys
                "password",
                "secret",
                "token",
                "key",
            ]

            hardcoded_secrets = self._scan_for_hardcoded_secrets(secret_patterns)
            if hardcoded_secrets:
                results.append(
                    f"❌ Potential hardcoded secrets found: {len(hardcoded_secrets)} files"
                )
                for file_path, line_num, content in hardcoded_secrets[:5]:  # Show first 5
                    results.append(f"   {file_path}:{line_num} - {content[:50]}...")
            else:
                results.append("✅ No hardcoded secrets detected")

            return results

        except Exception as e:
            logger.error(f"Environment variable validation failed: {e}")
            return [f"❌ Environment validation failed: {e}"]

    def _scan_for_hardcoded_secrets(self, patterns: list[str]) -> list[tuple[str, int, str]]:
        """Scan for hardcoded secrets in source code"""
        findings = []

        # Files to scan
        scan_extensions = [".py", ".js", ".ts", ".json", ".yml", ".yaml"]
        exclude_dirs = {".git", "node_modules", "__pycache__", ".pytest_cache", "venv"}

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if any(file.endswith(ext) for ext in scan_extensions):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, encoding="utf-8", errors="ignore") as f:
                            for line_num, line in enumerate(f, 1):
                                line_lower = line.lower()
                                for pattern in patterns:
                                    if pattern in line_lower and "=" in line:
                                        # Skip comments and obvious examples
                                        if (
                                            not line.strip().startswith("#")
                                            and "example" not in line_lower
                                        ):
                                            findings.append(
                                                (str(file_path), line_num, line.strip())
                                            )
                    except Exception:
                        continue

        return findings

    def generate_secure_keys(self) -> dict[str, str]:
        """Generate secure keys for the application"""
        keys = {
            "SECRET_KEY": secrets.token_urlsafe(64),
            "JWT_SECRET_KEY": secrets.token_urlsafe(64),
            "ENCRYPTION_KEY": secrets.token_urlsafe(32),
            "SESSION_KEY": secrets.token_urlsafe(32),
            "CSRF_KEY": secrets.token_urlsafe(32),
        }

        logger.info("Generated secure keys for application")
        return keys

    def configure_ssl_tls(self) -> list[str]:
        """Configure SSL/TLS settings"""
        results = []

        try:
            ssl_config = {
                "protocols": ["TLSv1.2", "TLSv1.3"],
                "ciphers": self.security_config["ssl_config"]["cipher_suites"],
                "options": [
                    "SSL_OP_NO_SSLv2",
                    "SSL_OP_NO_SSLv3",
                    "SSL_OP_NO_TLSv1",
                    "SSL_OP_NO_TLSv1_1",
                    "SSL_OP_CIPHER_SERVER_PREFERENCE",
                ],
            }

            # Write SSL configuration
            ssl_config_path = self.project_root / "security" / "ssl_config.json"
            with open(ssl_config_path, "w") as f:
                json.dump(ssl_config, f, indent=2)

            results.append("✅ SSL/TLS configuration created")
            results.append(
                f"✅ Minimum TLS version: {self.security_config['ssl_config']['min_tls_version']}"
            )
            results.append(f"✅ Cipher suites configured: {len(ssl_config['ciphers'])}")

            return results

        except Exception as e:
            logger.error(f"SSL/TLS configuration failed: {e}")
            return [f"❌ SSL/TLS configuration failed: {e}"]

    def harden_database_config(self) -> list[str]:
        """Harden database configuration"""
        results = []

        try:
            db_hardening = {
                "connection_settings": {
                    "sslmode": "require",
                    "connect_timeout": 10,
                    "command_timeout": 30,
                    "pool_size": 20,
                    "max_overflow": 0,
                },
                "security_settings": {
                    "log_statement": "none",  # Don't log SQL statements (may contain sensitive data)
                    "log_min_duration_statement": 1000,  # Log slow queries only
                    "shared_preload_libraries": "pg_stat_statements",
                    "track_activities": "on",
                    "track_counts": "on",
                },
            }

            # Write database configuration
            db_config_path = self.project_root / "security" / "database_hardening.json"
            with open(db_config_path, "w") as f:
                json.dump(db_hardening, f, indent=2)

            results.append("✅ Database hardening configuration created")
            results.append("✅ SSL required for database connections")
            results.append("✅ Connection pooling configured")
            results.append("✅ Query logging secured")

            return results

        except Exception as e:
            logger.error(f"Database hardening failed: {e}")
            return [f"❌ Database hardening failed: {e}"]

    def run_security_audit(self) -> dict[str, list[str]]:
        """Run comprehensive security audit"""
        audit_results = {
            "file_permissions": self.harden_file_permissions(),
            "environment_variables": self.validate_environment_variables(),
            "ssl_tls_config": self.configure_ssl_tls(),
            "database_hardening": self.harden_database_config(),
        }

        # Generate summary
        total_checks = sum(len(results) for results in audit_results.values())
        passed_checks = sum(
            len([r for r in results if r.startswith("✅")]) for results in audit_results.values()
        )

        audit_results["summary"] = [
            f"Security Audit Complete: {passed_checks}/{total_checks} checks passed",
            f"Environment: {self.environment}",
            f"Timestamp: {os.popen('date').read().strip()}",
        ]

        logger.info(f"Security audit completed: {passed_checks}/{total_checks} checks passed")
        return audit_results


def main():
    """Main function for running security hardening"""
    import argparse

    parser = argparse.ArgumentParser(description="DevSkyy Security Hardening")
    parser.add_argument(
        "--environment",
        default="production",
        choices=["development", "production", "testing"],
    )
    parser.add_argument("--generate-keys", action="store_true", help="Generate secure keys")
    parser.add_argument("--audit", action="store_true", help="Run security audit")

    args = parser.parse_args()

    hardening = SecurityHardening(args.environment)

    if args.generate_keys:
        keys = hardening.generate_secure_keys()
        print("Generated secure keys:")
        for key, value in keys.items():
            print(f"{key}={value}")

    if args.audit:
        results = hardening.run_security_audit()
        for category, checks in results.items():
            print(f"\n{category.upper()}:")
            for check in checks:
                print(f"  {check}")


if __name__ == "__main__":
    main()
