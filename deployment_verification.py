#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies all imports, endpoints, configurations, and system health
"""
import sys
import os
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class DeploymentVerifier:
    """Comprehensive deployment verification"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def check(self, description: str, passed: bool, error: str = ""):
        """Record check result"""
        if passed:
            logger.info(f"{GREEN}✓{RESET} {description}")
            self.passed += 1
        else:
            logger.error(f"{RED}✗{RESET} {description}")
            if error:
                logger.error(f"  {RED}Error: {error}{RESET}")
            self.failed += 1

    def warn(self, description: str, message: str = ""):
        """Record warning"""
        logger.warning(f"{YELLOW}⚠{RESET} {description}")
        if message:
            logger.warning(f"  {YELLOW}{message}{RESET}")
        self.warnings += 1

    def info(self, message: str):
        """Info message"""
        logger.info(f"{BLUE}ℹ{RESET} {message}")

    def section(self, title: str):
        """Print section header"""
        logger.info(f"\n{BLUE}{'=' * 70}{RESET}")
        logger.info(f"{BLUE}{title}{RESET}")
        logger.info(f"{BLUE}{'=' * 70}{RESET}\n")

    def verify_imports(self) -> bool:
        """Verify all critical imports"""
        self.section("Verifying Imports")

        critical_modules = [
            ("fastapi", "FastAPI framework"),
            ("pydantic", "Data validation"),
            ("sqlalchemy", "Database ORM"),
            ("anthropic", "Claude AI"),
            ("redis", "Redis caching"),
            ("numpy", "Numerical computing"),
            ("pandas", "Data analysis"),
            ("scikit-learn", "Machine learning"),
            ("torch", "Deep learning"),
            ("transformers", "NLP models"),
        ]

        for module_name, description in critical_modules:
            try:
                importlib.import_module(module_name)
                self.check(f"{description} ({module_name})", True)
            except ImportError as e:
                self.check(f"{description} ({module_name})", False, str(e))

        # Verify custom modules
        custom_modules = [
            "ml.model_registry",
            "ml.redis_cache",
            "ml.explainability",
            "ml.auto_retrain",
            "ml.theme_templates",
            "api.v1.ml",
            "api.v1.gdpr",
            "security.jwt_auth",
            "security.encryption",
        ]

        self.info("\nVerifying custom modules...")
        for module_name in custom_modules:
            try:
                importlib.import_module(module_name)
                self.check(f"Custom module: {module_name}", True)
            except Exception as e:
                self.check(f"Custom module: {module_name}", False, str(e))

        return self.failed == 0

    def verify_environment(self) -> bool:
        """Verify environment variables"""
        self.section("Verifying Environment Variables")

        from dotenv import load_dotenv
        load_dotenv()

        required_vars = [
            ("DATABASE_URL", "Database connection string"),
            ("SECRET_KEY", "Application secret key"),
            ("JWT_SECRET_KEY", "JWT secret key"),
        ]

        optional_vars = [
            ("ANTHROPIC_API_KEY", "Claude AI API key"),
            ("OPENAI_API_KEY", "OpenAI API key"),
            ("REDIS_HOST", "Redis host (optional)"),
            ("REDIS_PORT", "Redis port (optional)"),
        ]

        for var_name, description in required_vars:
            value = os.getenv(var_name)
            if value:
                self.check(f"{description} ({var_name})", True)
            else:
                self.check(f"{description} ({var_name})", False, "Not set")

        for var_name, description in optional_vars:
            value = os.getenv(var_name)
            if value:
                self.check(f"{description} ({var_name})", True)
            else:
                self.warn(f"{description} ({var_name})", "Not set (optional)")

        return self.failed == 0

    def verify_database(self) -> bool:
        """Verify database connection"""
        self.section("Verifying Database")

        try:
            from dotenv import load_dotenv
            load_dotenv()

            from sqlalchemy import create_engine, text
            from sqlalchemy.pool import NullPool

            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                self.check("Database URL configured", False, "DATABASE_URL not set")
                return False

            # Create engine
            engine = create_engine(db_url, poolclass=NullPool)

            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                self.check("Database connection", True)

            # Check tables
            from sqlalchemy import inspect
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            expected_tables = ["users", "products", "customers", "orders"]
            for table in expected_tables:
                if table in tables:
                    self.check(f"Table exists: {table}", True)
                else:
                    self.warn(f"Table exists: {table}", "Not found")

            engine.dispose()
            return True

        except Exception as e:
            self.check("Database connection", False, str(e))
            return False

    def verify_ml_infrastructure(self) -> bool:
        """Verify ML infrastructure"""
        self.section("Verifying ML Infrastructure")

        try:
            from ml.model_registry import model_registry
            self.check("Model registry import", True)

            from ml.redis_cache import redis_cache
            self.check("Redis cache import", True)

            # Test cache
            redis_cache.set("test_key", "test_value")
            value = redis_cache.get("test_key")
            if value == "test_value":
                self.check("Cache operations", True)
            else:
                self.check("Cache operations", False, "Value mismatch")
            redis_cache.delete("test_key")

            # Check cache mode
            stats = redis_cache.stats()
            self.info(f"Cache mode: {stats['mode']}")

            from ml.explainability import explainer
            self.check("Explainability import", True)

            from ml.auto_retrain import auto_retrainer
            self.check("Auto-retrainer import", True)

            return True

        except Exception as e:
            self.check("ML infrastructure", False, str(e))
            return False

    def verify_api_endpoints(self) -> bool:
        """Verify API endpoints are registered"""
        self.section("Verifying API Endpoints")

        try:
            from main import app

            routes = []
            for route in app.routes:
                if hasattr(route, "path"):
                    routes.append(route.path)

            # Check critical endpoints
            expected_endpoints = [
                "/api/v1/ml/health",
                "/api/v1/ml/registry/models",
                "/api/v1/ml/cache/stats",
                "/api/v1/gdpr/export",
                "/api/v1/gdpr/delete",
                "/health",
                "/docs",
            ]

            for endpoint in expected_endpoints:
                if endpoint in routes:
                    self.check(f"Endpoint registered: {endpoint}", True)
                else:
                    self.check(f"Endpoint registered: {endpoint}", False, "Not found")

            self.info(f"Total routes registered: {len(routes)}")
            return True

        except Exception as e:
            self.check("API endpoints verification", False, str(e))
            return False

    def verify_security(self) -> bool:
        """Verify security configuration"""
        self.section("Verifying Security Configuration")

        try:
            from security.jwt_auth import create_access_token, verify_token
            self.check("JWT authentication import", True)

            # Test JWT
            test_token = create_access_token(data={"sub": "test@example.com"})
            payload = verify_token(test_token)
            if payload and payload.get("sub") == "test@example.com":
                self.check("JWT token generation and verification", True)
            else:
                self.check("JWT token generation and verification", False)

            from security.encryption import encrypt_data, decrypt_data
            self.check("Encryption import", True)

            # Test encryption
            test_data = "sensitive data"
            encrypted = encrypt_data(test_data)
            decrypted = decrypt_data(encrypted)
            if decrypted == test_data:
                self.check("AES-256-GCM encryption/decryption", True)
            else:
                self.check("AES-256-GCM encryption/decryption", False)

            return True

        except Exception as e:
            self.check("Security verification", False, str(e))
            return False

    def verify_file_structure(self) -> bool:
        """Verify critical files exist"""
        self.section("Verifying File Structure")

        critical_files = [
            "main.py",
            "requirements.txt",
            ".env",
            "ml/model_registry.py",
            "ml/redis_cache.py",
            "ml/explainability.py",
            "ml/auto_retrain.py",
            "api/v1/ml.py",
            "api/v1/gdpr.py",
            "security/jwt_auth.py",
            "security/encryption.py",
            "tests/ml/test_ml_infrastructure.py",
            "tests/security/test_security_integration.py",
        ]

        for file_path in critical_files:
            path = Path(file_path)
            if path.exists():
                self.check(f"File exists: {file_path}", True)
            else:
                self.check(f"File exists: {file_path}", False, "Not found")

        return self.failed == 0

    def print_summary(self):
        """Print verification summary"""
        self.section("Verification Summary")

        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0

        logger.info(f"{GREEN}Passed:{RESET} {self.passed}")
        logger.info(f"{RED}Failed:{RESET} {self.failed}")
        logger.info(f"{YELLOW}Warnings:{RESET} {self.warnings}")
        logger.info(f"{BLUE}Success Rate:{RESET} {success_rate:.1f}%\n")

        if self.failed == 0:
            logger.info(f"{GREEN}{'=' * 70}{RESET}")
            logger.info(f"{GREEN}✓ DEPLOYMENT READY - All critical checks passed{RESET}")
            logger.info(f"{GREEN}{'=' * 70}{RESET}\n")
            return 0
        else:
            logger.error(f"{RED}{'=' * 70}{RESET}")
            logger.error(f"{RED}✗ DEPLOYMENT NOT READY - {self.failed} critical failures{RESET}")
            logger.error(f"{RED}{'=' * 70}{RESET}\n")
            return 1


def main():
    """Run all verification checks"""
    verifier = DeploymentVerifier()

    logger.info(f"\n{BLUE}{'=' * 70}{RESET}")
    logger.info(f"{BLUE}DevSkyy Deployment Verification{RESET}")
    logger.info(f"{BLUE}{'=' * 70}{RESET}\n")

    # Run all checks
    verifier.verify_file_structure()
    verifier.verify_imports()
    verifier.verify_environment()
    verifier.verify_database()
    verifier.verify_ml_infrastructure()
    verifier.verify_api_endpoints()
    verifier.verify_security()

    # Print summary and exit
    return verifier.print_summary()


if __name__ == "__main__":
    sys.exit(main())
