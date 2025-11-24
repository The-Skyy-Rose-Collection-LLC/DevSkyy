from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac
import logging
import secrets
from typing import Any


"""
Enterprise Security Manager for Agent System
Provides authentication, authorization, encryption, and audit logging

Features:
- Agent authentication and API key management
- Role-based access control (RBAC)
- Data encryption at rest and in transit
- Audit logging and compliance
- Rate limiting and DDoS protection
- Secrets management and rotation
- Security scanning and threat detection
"""

logger = logging.getLogger(__name__)


class SecurityRole(Enum):
    """Security roles for agents"""

    ADMIN = "admin"  # Full access
    OPERATOR = "operator"  # Read/write operations
    ANALYST = "analyst"  # Read-only access
    SERVICE = "service"  # Service-to-service communication
    GUEST = "guest"  # Limited access


class PermissionLevel(Enum):
    """Permission levels"""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"


class SecurityManager:
    """
    Enterprise security manager for multi-agent system.

    Provides:
    - Authentication and authorization
    - API key management
    - Encryption and secrets management
    - Audit logging
    - Rate limiting
    - Threat detection
    """

    def __init__(self):
        # Authentication
        self.api_keys: dict[str, dict[str, Any]] = {}  # key_id -> key_info
        self.agent_credentials: dict[str, str] = {}  # agent_name -> api_key_id

        # Authorization (RBAC)
        self.agent_roles: dict[str, SecurityRole] = {}
        self.role_permissions: dict[SecurityRole, set[str]] = {
            SecurityRole.ADMIN: {"read", "write", "execute", "admin", "delete"},
            SecurityRole.OPERATOR: {"read", "write", "execute"},
            SecurityRole.ANALYST: {"read"},
            SecurityRole.SERVICE: {"read", "write", "execute"},
            SecurityRole.GUEST: {"read"},
        }

        # Resource permissions
        self.resource_acl: dict[str, set[str]] = {}  # resource -> set of allowed agents

        # Audit logging
        self.audit_log: list[dict[str, Any]] = []

        # Rate limiting
        self.rate_limits: dict[str, list[datetime]] = {}

        # Secrets management
        self.secrets: dict[str, str] = {}

        # Threat detection
        self.suspicious_activity: dict[str, int] = {}
        self.blocked_agents: set[str] = set()

        logger.info("🔒 Enterprise Security Manager initialized")

    # ============================================================================
    # AUTHENTICATION
    # ============================================================================

    def generate_api_key(self, agent_name: str, role: SecurityRole, expires_days: int = 365) -> str:
        """
        Generate a secure API key for an agent.

        Args:
            agent_name: Name of the agent
            role: Security role
            expires_days: Days until key expires

        Returns:
            API key string
        """
        # Generate secure random key
        key_id = secrets.token_urlsafe(16)
        api_key = secrets.token_urlsafe(32)

        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Store key information
        self.api_keys[key_id] = {
            "key_hash": key_hash,
            "agent_name": agent_name,
            "role": role,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(days=expires_days),
            "last_used": None,
            "usage_count": 0,
        }

        # Associate with agent
        self.agent_credentials[agent_name] = key_id
        self.agent_roles[agent_name] = role

        self._audit_log("api_key_created", agent_name, {"key_id": key_id, "role": role.value})

        return f"{key_id}.{api_key}"

    def validate_api_key(self, api_key: str) -> dict[str, Any] | None:
        """
        Validate an API key.

        Returns:
            Key information if valid, None otherwise
        """
        try:
            # Parse key
            parts = api_key.split(".")
            if len(parts) != 2:
                return None

            key_id, key_secret = parts

            # Check if key exists
            if key_id not in self.api_keys:
                return None

            key_info = self.api_keys[key_id]

            # Verify hash
            key_hash = hashlib.sha256(key_secret.encode()).hexdigest()
            if key_hash != key_info["key_hash"]:
                self._audit_log("invalid_api_key", "unknown", {"key_id": key_id})
                return None

            # Check expiration
            if datetime.now() > key_info["expires_at"]:
                self._audit_log("expired_api_key", key_info["agent_name"], {"key_id": key_id})
                return None

            # Update usage
            key_info["last_used"] = datetime.now()
            key_info["usage_count"] += 1

            return key_info

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return None

    def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key"""
        if key_id in self.api_keys:
            agent_name = self.api_keys[key_id]["agent_name"]
            del self.api_keys[key_id]
            self._audit_log("api_key_revoked", agent_name, {"key_id": key_id})
            return True
        return False

    def rotate_api_key(self, agent_name: str) -> str | None:
        """Rotate an agent's API key"""
        if agent_name not in self.agent_credentials:
            return None

        # Revoke old key
        old_key_id = self.agent_credentials[agent_name]
        role = self.api_keys[old_key_id]["role"]
        self.revoke_api_key(old_key_id)

        # Generate new key
        new_key = self.generate_api_key(agent_name, role)
        self._audit_log("api_key_rotated", agent_name, {})

        return new_key

    # ============================================================================
    # AUTHORIZATION (RBAC)
    # ============================================================================

    def check_permission(self, agent_name: str, resource: str, permission: str) -> bool:
        """
        Check if an agent has permission to access a resource.

        Args:
            agent_name: Name of the agent
            resource: Resource being accessed
            permission: Permission type (read, write, execute, etc.)

        Returns:
            bool: True if authorized
        """
        # Check if agent is blocked
        if agent_name in self.blocked_agents:
            self._audit_log("blocked_agent_access_attempt", agent_name, {"resource": resource})
            return False

        # Get agent role
        role = self.agent_roles.get(agent_name)
        if not role:
            self._audit_log(
                "unauthorized_access",
                agent_name,
                {"resource": resource, "reason": "no_role"},
            )
            return False

        # Check role permissions
        if permission not in self.role_permissions[role]:
            self._audit_log(
                "unauthorized_access",
                agent_name,
                {"resource": resource, "permission": permission, "role": role.value},
            )
            return False

        # Check resource ACL
        if resource in self.resource_acl and agent_name not in self.resource_acl[resource]:
            self._audit_log(
                "unauthorized_access",
                agent_name,
                {"resource": resource, "reason": "not_in_acl"},
            )
            return False

        self._audit_log(
            "authorized_access",
            agent_name,
            {"resource": resource, "permission": permission},
        )
        return True

    def grant_resource_access(self, resource: str, agent_name: str):
        """Grant an agent access to a specific resource"""
        if resource not in self.resource_acl:
            self.resource_acl[resource] = set()
        self.resource_acl[resource].add(agent_name)
        self._audit_log("access_granted", agent_name, {"resource": resource})

    def revoke_resource_access(self, resource: str, agent_name: str):
        """Revoke an agent's access to a resource"""
        if resource in self.resource_acl and agent_name in self.resource_acl[resource]:
            self.resource_acl[resource].remove(agent_name)
            self._audit_log("access_revoked", agent_name, {"resource": resource})

    # ============================================================================
    # ENCRYPTION & SECRETS
    # ============================================================================
    # NOTE: For data encryption, use the security.encryption module which provides
    # AES-256-GCM encryption (NIST SP 800-38D compliant).
    #
    # Example usage:
    #   from security.encryption import encrypt_field, decrypt_field
    #   encrypted = encrypt_field("sensitive_data")
    #   decrypted = decrypt_field(encrypted)
    #
    # The security.encryption module provides:
    # - AES-256-GCM authenticated encryption
    # - PBKDF2 key derivation (NIST SP 800-132)
    # - Automatic nonce generation
    # - Key rotation support
    # - Field-level and dictionary encryption

    def store_secret(self, secret_name: str, secret_value: str):
        """Store a secret securely"""
        # In production, use a proper secrets manager like HashiCorp Vault
        secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()
        self.secrets[secret_name] = secret_hash
        self._audit_log("secret_stored", "system", {"secret_name": secret_name})

    def verify_secret(self, secret_name: str, secret_value: str) -> bool:
        """Verify a secret"""
        if secret_name not in self.secrets:
            return False

        secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()
        return hmac.compare_digest(secret_hash, self.secrets[secret_name])

    # ============================================================================
    # RATE LIMITING
    # ============================================================================

    def check_rate_limit(self, agent_name: str, limit: int = 100, window_seconds: int = 60) -> bool:
        """
        Check if an agent has exceeded rate limits.

        Args:
            agent_name: Name of the agent
            limit: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            bool: True if under limit, False if exceeded
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window_seconds)

        # Initialize if not exists
        if agent_name not in self.rate_limits:
            self.rate_limits[agent_name] = []

        # Clean old entries
        self.rate_limits[agent_name] = [ts for ts in self.rate_limits[agent_name] if ts > window_start]

        # Check limit
        if len(self.rate_limits[agent_name]) >= limit:
            self._audit_log(
                "rate_limit_exceeded",
                agent_name,
                {"limit": limit, "window": window_seconds},
            )
            self._flag_suspicious_activity(agent_name)
            return False

        # Add current request
        self.rate_limits[agent_name].append(now)
        return True

    # ============================================================================
    # THREAT DETECTION
    # ============================================================================

    def _flag_suspicious_activity(self, agent_name: str, threshold: int = 5):
        """Flag and potentially block suspicious agents"""
        if agent_name not in self.suspicious_activity:
            self.suspicious_activity[agent_name] = 0

        self.suspicious_activity[agent_name] += 1

        if self.suspicious_activity[agent_name] >= threshold:
            self.block_agent(agent_name)
            logger.warning(f"🚨 Agent blocked due to suspicious activity: {agent_name}")

    def block_agent(self, agent_name: str):
        """Block an agent from making requests"""
        self.blocked_agents.add(agent_name)
        self._audit_log("agent_blocked", agent_name, {})

    def unblock_agent(self, agent_name: str):
        """Unblock an agent"""
        if agent_name in self.blocked_agents:
            self.blocked_agents.remove(agent_name)
            self.suspicious_activity[agent_name] = 0
            self._audit_log("agent_unblocked", agent_name, {})

    # ============================================================================
    # AUDIT LOGGING
    # ============================================================================

    def _audit_log(self, event_type: str, agent_name: str, details: dict[str, Any]):
        """Log security events for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "agent_name": agent_name,
            "details": details,
        }

        self.audit_log.append(log_entry)

        # Keep only last 10000 entries
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-10000:]

        # Log critical events
        if event_type in [
            "unauthorized_access",
            "agent_blocked",
            "rate_limit_exceeded",
        ]:
            logger.warning(f"🔐 Security event: {event_type} - {agent_name}")

    def get_audit_log(
        self,
        agent_name: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get audit log entries.

        Args:
            agent_name: Filter by agent name
            event_type: Filter by event type
            limit: Maximum entries to return

        Returns:
            List of audit log entries
        """
        filtered_logs = self.audit_log

        if agent_name:
            filtered_logs = [log for log in filtered_logs if log["agent_name"] == agent_name]

        if event_type:
            filtered_logs = [log for log in filtered_logs if log["event_type"] == event_type]

        return filtered_logs[-limit:]

    def get_security_summary(self) -> dict[str, Any]:
        """Get security summary statistics"""
        return {
            "total_api_keys": len(self.api_keys),
            "active_agents": len(self.agent_roles),
            "blocked_agents": len(self.blocked_agents),
            "suspicious_activity_count": sum(self.suspicious_activity.values()),
            "audit_log_entries": len(self.audit_log),
            "resources_protected": len(self.resource_acl),
        }


# Global security manager instance
security_manager = SecurityManager()
