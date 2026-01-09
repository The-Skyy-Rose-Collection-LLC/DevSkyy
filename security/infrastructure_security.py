"""
Infrastructure Security Hardening
=================================

Enterprise-grade infrastructure security for DevSkyy Platform:
- Docker security configuration
- Environment variable protection
- Secrets management
- Security monitoring
- Container hardening
- Network security
"""

import logging
import os
import secrets
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecretType(str, Enum):
    """Types of secrets"""

    API_KEY = "api_key"
    DATABASE_URL = "database_url"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    OAUTH_SECRET = "oauth_secret"
    WEBHOOK_SECRET = "webhook_secret"
    SERVICE_ACCOUNT = "service_account"


class SecretMetadata(BaseModel):
    """Metadata for managed secrets"""

    name: str
    secret_type: SecretType
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_rotated: datetime | None = None
    rotation_count: int = 0
    expires_at: datetime | None = None
    is_encrypted: bool = True
    source: str = "environment"  # environment, vault, file


class EnvironmentSecurityConfig(BaseModel):
    """Environment security configuration"""

    required_secrets: list[str] = Field(
        default_factory=lambda: ["JWT_SECRET_KEY", "ENCRYPTION_MASTER_KEY", "DATABASE_URL"]
    )
    optional_secrets: list[str] = Field(
        default_factory=lambda: ["OPENAI_API_KEY", "REDIS_URL", "SENTRY_DSN"]
    )
    forbidden_in_logs: list[str] = Field(
        default_factory=lambda: ["password", "secret", "key", "token", "credential", "auth"]
    )
    min_secret_length: int = 32
    require_encryption: bool = True


class DockerSecurityConfig(BaseModel):
    """Docker security configuration"""

    run_as_non_root: bool = True
    read_only_root_fs: bool = True
    no_new_privileges: bool = True
    drop_capabilities: list[str] = Field(default_factory=lambda: ["ALL"])
    add_capabilities: list[str] = Field(default_factory=list)
    security_opt: list[str] = Field(default_factory=lambda: ["no-new-privileges:true"])
    resource_limits: dict[str, Any] = Field(
        default_factory=lambda: {"memory": "512m", "cpus": "1.0", "pids": 100}
    )


class InfrastructureSecurityManager:
    """
    Infrastructure security manager for DevSkyy Platform.

    Features:
    - Environment variable validation and protection
    - Secrets management and rotation
    - Docker security configuration
    - Security monitoring and alerting
    - Compliance checking
    """

    def __init__(self):
        self.env_config = EnvironmentSecurityConfig()
        self.docker_config = DockerSecurityConfig()
        self.secrets_metadata: dict[str, SecretMetadata] = {}
        self.security_violations: list[dict[str, Any]] = []

    def validate_environment(self) -> dict[str, Any]:
        """Validate environment security configuration"""
        result = {
            "valid": True,
            "missing_required": [],
            "weak_secrets": [],
            "warnings": [],
            "recommendations": [],
        }

        # Check required secrets
        for secret_name in self.env_config.required_secrets:
            value = os.getenv(secret_name)
            if not value:
                result["valid"] = False
                result["missing_required"].append(secret_name)
            elif len(value) < self.env_config.min_secret_length:
                result["weak_secrets"].append(secret_name)
                result["warnings"].append(f"{secret_name} is shorter than recommended minimum")

        # Check for development mode in production
        if os.getenv("ENVIRONMENT", "").lower() == "production":
            if os.getenv("DEBUG", "").lower() == "true":
                result["valid"] = False
                result["warnings"].append("DEBUG mode enabled in production")

            if os.getenv("TESTING", "").lower() == "true":
                result["warnings"].append("TESTING mode enabled in production")

        # Check for insecure defaults
        jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        if jwt_secret and ("secret" in jwt_secret.lower() or "changeme" in jwt_secret.lower()):
            result["valid"] = False
            result["warnings"].append("JWT_SECRET_KEY appears to be a default/insecure value")

        # Recommendations
        if not os.getenv("SENTRY_DSN"):
            result["recommendations"].append("Consider adding SENTRY_DSN for error monitoring")

        if not os.getenv("REDIS_URL"):
            result["recommendations"].append("Consider adding Redis for session/cache management")

        return result

    def sanitize_for_logging(self, data: dict[str, Any]) -> dict[str, Any]:
        """Sanitize data for safe logging (remove secrets)"""
        sanitized = {}

        for key, value in data.items():
            key_lower = key.lower()

            # Check if key contains forbidden patterns
            is_sensitive = any(
                pattern in key_lower for pattern in self.env_config.forbidden_in_logs
            )

            if is_sensitive:
                if isinstance(value, str) and len(value) > 4:
                    sanitized[key] = f"{value[:2]}***{value[-2:]}"
                else:
                    sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_for_logging(value)
            else:
                sanitized[key] = value

        return sanitized

    def generate_secure_secret(self, secret_type: SecretType, length: int = 64) -> str:
        """Generate a cryptographically secure secret"""
        if secret_type == SecretType.JWT_SECRET:
            # URL-safe base64 for JWT
            return secrets.token_urlsafe(length)

        elif secret_type == SecretType.ENCRYPTION_KEY:
            # Base64-encoded bytes for encryption
            import base64

            return base64.b64encode(secrets.token_bytes(32)).decode()

        elif secret_type == SecretType.API_KEY:
            # Prefixed API key
            return f"sk_{secrets.token_hex(length // 2)}"

        elif secret_type == SecretType.WEBHOOK_SECRET:
            # Hex string for webhook signatures
            return secrets.token_hex(length // 2)

        else:
            # Default secure token
            return secrets.token_urlsafe(length)

    def generate_docker_security_config(self) -> str:
        """Generate secure Docker Compose configuration"""
        config = f"""# DevSkyy Secure Docker Configuration
# Generated: {datetime.now(UTC).isoformat()}

version: '3.8'

services:
  devskyy-api:
    image: devskyy/api:latest
    user: "1000:1000"  # Non-root user
    read_only: true
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    deploy:
      resources:
        limits:
          memory: {self.docker_config.resource_limits["memory"]}
          cpus: '{self.docker_config.resource_limits["cpus"]}'
        reservations:
          memory: 256m
    environment:
      - ENVIRONMENT=production
    secrets:
      - jwt_secret
      - encryption_key
      - database_url
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - internal
    tmpfs:
      - /tmp:size=100M,mode=1777

secrets:
  jwt_secret:
    external: true
  encryption_key:
    external: true
  database_url:
    external: true

networks:
  internal:
    driver: bridge
    internal: true
"""
        return config

    def generate_dockerfile_security(self) -> str:
        """Generate secure Dockerfile"""
        dockerfile = """# DevSkyy Secure Dockerfile
# Multi-stage build for minimal attack surface

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim AS production

# Security: Create non-root user
RUN groupadd -r devskyy && useradd -r -g devskyy devskyy

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /root/.local /home/devskyy/.local

# Copy application code
COPY --chown=devskyy:devskyy . .

# Security: Set proper permissions
RUN chmod -R 755 /app && \\
    chown -R devskyy:devskyy /app

# Security: Switch to non-root user
USER devskyy

# Security: Set PATH for user-installed packages
ENV PATH=/home/devskyy/.local/bin:$PATH

# Security: Disable Python bytecode and buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main_enterprise:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        return dockerfile

    def check_security_compliance(self) -> dict[str, Any]:
        """Check infrastructure security compliance"""
        compliance = {
            "timestamp": datetime.now(UTC).isoformat(),
            "overall_score": 0,
            "checks": [],
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }

        checks = [
            ("Environment secrets configured", self._check_env_secrets()),
            ("Non-root container user", self.docker_config.run_as_non_root),
            ("Read-only filesystem", self.docker_config.read_only_root_fs),
            ("Capabilities dropped", len(self.docker_config.drop_capabilities) > 0),
            ("Resource limits set", bool(self.docker_config.resource_limits)),
            ("No new privileges", self.docker_config.no_new_privileges),
            ("Debug mode disabled", os.getenv("DEBUG", "").lower() != "true"),
            ("HTTPS enforced", os.getenv("FORCE_HTTPS", "true").lower() == "true"),
        ]

        for check_name, passed in checks:
            status = "passed" if passed else "failed"
            compliance["checks"].append({"name": check_name, "status": status})

            if passed:
                compliance["passed"] += 1
            else:
                compliance["failed"] += 1

        total_checks = len(checks)
        compliance["overall_score"] = int((compliance["passed"] / total_checks) * 100)

        return compliance

    def _check_env_secrets(self) -> bool:
        """Check if required environment secrets are configured"""
        return all(os.getenv(secret) for secret in self.env_config.required_secrets)

    def log_security_violation(self, violation_type: str, details: dict[str, Any]):
        """Log a security violation"""
        violation = {
            "timestamp": datetime.now(UTC).isoformat(),
            "type": violation_type,
            "details": self.sanitize_for_logging(details),
        }

        self.security_violations.append(violation)
        logger.warning(f"Security violation: {violation}")

    def get_security_report(self) -> dict[str, Any]:
        """Generate comprehensive security report"""
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "environment_validation": self.validate_environment(),
            "compliance_check": self.check_security_compliance(),
            "recent_violations": self.security_violations[-100:],  # Last 100
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate security recommendations"""
        recommendations = []

        env_result = self.validate_environment()
        if env_result["missing_required"]:
            recommendations.append(
                f"Configure missing secrets: {', '.join(env_result['missing_required'])}"
            )

        if env_result["weak_secrets"]:
            recommendations.append(
                f"Strengthen weak secrets: {', '.join(env_result['weak_secrets'])}"
            )

        if not os.getenv("SENTRY_DSN"):
            recommendations.append("Enable error monitoring with Sentry")

        if not os.getenv("REDIS_URL"):
            recommendations.append("Add Redis for improved session management")

        return recommendations


# Global instance
infrastructure_security = InfrastructureSecurityManager()
