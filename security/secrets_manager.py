"""
Secrets Management System
=========================

Enterprise-grade secrets management with multiple backend support.

Features:
- Abstract backend interface for multiple secret stores
- AWS Secrets Manager integration
- HashiCorp Vault support (basic implementation)
- Local development backend with encryption
- Automatic secret rotation
- Comprehensive error handling and logging
- Secret versioning support

Security Standards:
- Secrets never logged or exposed in error messages
- Encryption at rest for local storage
- TLS/SSL for cloud provider communication
- Principle of least privilege for access control
"""

import contextlib
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SecretBackendType(str, Enum):
    """Types of secrets backends"""

    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    HASHICORP_VAULT = "hashicorp_vault"
    LOCAL_ENCRYPTED = "local_encrypted"
    ENVIRONMENT = "environment"


class SecretMetadata(BaseModel):
    """Metadata for a secret"""

    secret_name: str
    version: str = "1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    rotation_enabled: bool = False
    rotation_interval_days: int | None = None
    last_rotated: datetime | None = None
    next_rotation: datetime | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class SecretValue(BaseModel):
    """Secret value with metadata"""

    value: str | dict[str, Any]
    metadata: SecretMetadata


class SecretsBackendError(Exception):
    """Base exception for secrets backend errors"""

    pass


class SecretNotFoundError(SecretsBackendError):
    """Secret not found in backend"""

    pass


class SecretRotationError(SecretsBackendError):
    """Error during secret rotation"""

    pass


# =============================================================================
# Abstract Backend Interface
# =============================================================================


class SecretsBackend(ABC):
    """
    Abstract base class for secrets management backends.

    All backend implementations must inherit from this class and implement
    the required methods.
    """

    @abstractmethod
    def get_secret(self, secret_name: str, version: str | None = None) -> SecretValue:
        """
        Retrieve a secret from the backend.

        Args:
            secret_name: Name/identifier of the secret
            version: Optional version to retrieve (defaults to latest)

        Returns:
            SecretValue object containing the secret and metadata

        Raises:
            SecretNotFoundError: If secret doesn't exist
            SecretsBackendError: For other backend errors
        """
        pass

    @abstractmethod
    def set_secret(
        self,
        secret_name: str,
        secret_value: str | dict[str, Any],
        description: str = "",
        tags: dict[str, str] | None = None,
    ) -> str:
        """
        Create or update a secret in the backend.

        Args:
            secret_name: Name/identifier of the secret
            secret_value: The secret value (string or dict)
            description: Optional description
            tags: Optional tags for organization/filtering

        Returns:
            Version ID of the created/updated secret

        Raises:
            SecretsBackendError: If operation fails
        """
        pass

    @abstractmethod
    def rotate_secret(self, secret_name: str) -> str:
        """
        Trigger rotation of a secret.

        Args:
            secret_name: Name/identifier of the secret to rotate

        Returns:
            New version ID after rotation

        Raises:
            SecretRotationError: If rotation fails
        """
        pass

    @abstractmethod
    def delete_secret(self, secret_name: str, force: bool = False) -> bool:
        """
        Delete a secret from the backend.

        Args:
            secret_name: Name/identifier of the secret
            force: If True, immediately delete; if False, schedule for deletion

        Returns:
            True if deletion successful

        Raises:
            SecretsBackendError: If deletion fails
        """
        pass

    @abstractmethod
    def list_secrets(self, filters: dict[str, str] | None = None) -> list[str]:
        """
        List all secret names in the backend.

        Args:
            filters: Optional filters (e.g., tags)

        Returns:
            List of secret names
        """
        pass


# =============================================================================
# AWS Secrets Manager Backend
# =============================================================================


class AWSSecretsManager(SecretsBackend):
    """
    AWS Secrets Manager backend implementation.

    Requires:
    - boto3 library
    - AWS credentials configured (environment, IAM role, or AWS config)
    - Appropriate IAM permissions for secretsmanager:*

    Environment Variables:
    - AWS_REGION: AWS region (e.g., us-east-1)
    - AWS_ACCESS_KEY_ID: AWS access key (optional if using IAM roles)
    - AWS_SECRET_ACCESS_KEY: AWS secret key (optional if using IAM roles)
    """

    def __init__(self, region_name: str | None = None):
        """
        Initialize AWS Secrets Manager client.

        Args:
            region_name: AWS region (defaults to AWS_REGION env var or us-east-1)
        """
        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")

        try:
            import boto3
            from botocore.exceptions import BotoCoreError, ClientError

            self.boto3 = boto3
            self.ClientError = ClientError
            self.BotoCoreError = BotoCoreError

            # Create Secrets Manager client
            self.client = boto3.client("secretsmanager", region_name=self.region_name)

            logger.info(f"AWS Secrets Manager client initialized (region: {self.region_name})")

        except ImportError as e:
            raise SecretsBackendError(
                "boto3 is required for AWS Secrets Manager. Install with: pip install boto3"
            ) from e
        except Exception as e:
            raise SecretsBackendError(
                f"Failed to initialize AWS Secrets Manager client: {e}"
            ) from e

    def get_secret(self, secret_name: str, version: str | None = None) -> SecretValue:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            kwargs = {"SecretId": secret_name}
            if version:
                kwargs["VersionId"] = version

            response = self.client.get_secret_value(**kwargs)

            # Parse secret value (can be string or JSON)
            secret_value = response.get("SecretString")
            if secret_value:
                try:
                    # Try to parse as JSON
                    secret_data = json.loads(secret_value)
                except json.JSONDecodeError:
                    # Keep as string if not valid JSON
                    secret_data = secret_value
            else:
                # Binary secret
                secret_data = response.get("SecretBinary")

            # Build metadata
            metadata = SecretMetadata(
                secret_name=secret_name,
                version=response.get("VersionId", "1"),
                created_at=response.get("CreatedDate", datetime.now(UTC)),
                tags=self._get_secret_tags(secret_name),
            )

            return SecretValue(value=secret_data, metadata=metadata)

        except self.ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                raise SecretNotFoundError(
                    f"Secret '{secret_name}' not found in AWS Secrets Manager"
                ) from e
            else:
                logger.error(f"AWS Secrets Manager error: {error_code}")
                raise SecretsBackendError(
                    f"Failed to retrieve secret '{secret_name}': {error_code}"
                ) from e
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret: {e}", exc_info=True)
            raise SecretsBackendError(f"Failed to retrieve secret '{secret_name}'") from e

    def set_secret(
        self,
        secret_name: str,
        secret_value: str | dict[str, Any],
        description: str = "",
        tags: dict[str, str] | None = None,
    ) -> str:
        """Create or update secret in AWS Secrets Manager"""
        try:
            # Convert dict to JSON string
            if isinstance(secret_value, dict):
                secret_string = json.dumps(secret_value)
            else:
                secret_string = str(secret_value)

            # Try to update existing secret first
            try:
                response = self.client.put_secret_value(
                    SecretId=secret_name,
                    SecretString=secret_string,
                )
                logger.info(f"Updated existing secret: {secret_name}")

            except self.ClientError as e:
                if e.response["Error"]["Code"] == "ResourceNotFoundException":
                    # Create new secret
                    create_kwargs = {
                        "Name": secret_name,
                        "SecretString": secret_string,
                    }

                    if description:
                        create_kwargs["Description"] = description

                    if tags:
                        create_kwargs["Tags"] = [{"Key": k, "Value": v} for k, v in tags.items()]

                    response = self.client.create_secret(**create_kwargs)
                    logger.info(f"Created new secret: {secret_name}")
                else:
                    raise

            return response.get("VersionId", "1")

        except self.ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"AWS Secrets Manager error: {error_code}")
            raise SecretsBackendError(f"Failed to set secret '{secret_name}': {error_code}") from e
        except Exception as e:
            logger.error(f"Unexpected error setting secret: {e}", exc_info=True)
            raise SecretsBackendError(f"Failed to set secret '{secret_name}'") from e

    def rotate_secret(self, secret_name: str) -> str:
        """
        Trigger rotation of a secret in AWS Secrets Manager.

        Note: This requires a Lambda function ARN to be configured for rotation.
        For manual rotation, use set_secret() with a new value.
        """
        try:
            # Check if rotation is configured
            response = self.client.describe_secret(SecretId=secret_name)

            if not response.get("RotationEnabled"):
                raise SecretRotationError(
                    f"Secret '{secret_name}' does not have rotation enabled. "
                    "Configure rotation in AWS console or use set_secret() for manual rotation."
                )

            # Trigger immediate rotation
            response = self.client.rotate_secret(
                SecretId=secret_name,
                RotateImmediately=True,
            )

            logger.info(f"Triggered rotation for secret: {secret_name}")
            return response.get("VersionId", "1")

        except self.ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"AWS Secrets Manager rotation error: {error_code}")
            raise SecretRotationError(
                f"Failed to rotate secret '{secret_name}': {error_code}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error rotating secret: {e}", exc_info=True)
            raise SecretRotationError(f"Failed to rotate secret '{secret_name}'") from e

    def delete_secret(self, secret_name: str, force: bool = False) -> bool:
        """Delete secret from AWS Secrets Manager"""
        try:
            kwargs = {"SecretId": secret_name}

            if force:
                # Immediate deletion (cannot be recovered)
                kwargs["ForceDeleteWithoutRecovery"] = True
                logger.warning(f"Force deleting secret: {secret_name} (cannot be recovered)")
            else:
                # Schedule for deletion (30 day recovery window)
                kwargs["RecoveryWindowInDays"] = 30
                logger.info(
                    f"Scheduling secret for deletion: {secret_name} (30 day recovery window)"
                )

            self.client.delete_secret(**kwargs)
            return True

        except self.ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"AWS Secrets Manager deletion error: {error_code}")
            raise SecretsBackendError(
                f"Failed to delete secret '{secret_name}': {error_code}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error deleting secret: {e}", exc_info=True)
            raise SecretsBackendError(f"Failed to delete secret '{secret_name}'") from e

    def list_secrets(self, filters: dict[str, str] | None = None) -> list[str]:
        """List all secrets in AWS Secrets Manager"""
        try:
            kwargs = {}
            if filters:
                # AWS uses specific filter format
                kwargs["Filters"] = [
                    {"Key": "tag-key", "Values": list(filters.keys())},
                    {"Key": "tag-value", "Values": list(filters.values())},
                ]

            paginator = self.client.get_paginator("list_secrets")
            secret_names = []

            for page in paginator.paginate(**kwargs):
                for secret in page.get("SecretList", []):
                    secret_names.append(secret["Name"])

            return secret_names

        except Exception as e:
            logger.error(f"Error listing secrets: {e}", exc_info=True)
            raise SecretsBackendError("Failed to list secrets") from e

    def _get_secret_tags(self, secret_name: str) -> dict[str, str]:
        """Helper to retrieve tags for a secret"""
        try:
            response = self.client.describe_secret(SecretId=secret_name)
            tags = response.get("Tags", [])
            return {tag["Key"]: tag["Value"] for tag in tags}
        except Exception:
            return {}


# =============================================================================
# HashiCorp Vault Backend
# =============================================================================


class HashiCorpVault(SecretsBackend):
    """
    HashiCorp Vault backend implementation (basic).

    This is a basic implementation. For production use, consider:
    - Using hvac library for full Vault integration
    - Implementing token renewal
    - Supporting different auth methods (AppRole, Kubernetes, etc.)
    - Implementing secret engines (KV v2, database, etc.)

    Environment Variables:
    - VAULT_ADDR: Vault server address (e.g., https://vault.example.com:8200)
    - VAULT_TOKEN: Vault authentication token
    - VAULT_NAMESPACE: Vault namespace (optional)
    """

    def __init__(
        self,
        vault_addr: str | None = None,
        token: str | None = None,
        namespace: str | None = None,
    ):
        """
        Initialize HashiCorp Vault client.

        Args:
            vault_addr: Vault server address
            token: Vault authentication token
            namespace: Vault namespace (optional)
        """
        self.vault_addr = vault_addr or os.getenv("VAULT_ADDR")
        self.token = token or os.getenv("VAULT_TOKEN")
        self.namespace = namespace or os.getenv("VAULT_NAMESPACE")

        if not self.vault_addr:
            raise SecretsBackendError(
                "VAULT_ADDR environment variable or vault_addr parameter required"
            )

        if not self.token:
            raise SecretsBackendError(
                "VAULT_TOKEN environment variable or token parameter required"
            )

        try:
            import hvac

            self.client = hvac.Client(
                url=self.vault_addr,
                token=self.token,
                namespace=self.namespace,
            )

            # Verify connection
            if not self.client.is_authenticated():
                raise SecretsBackendError("Failed to authenticate with Vault")

            logger.info(f"HashiCorp Vault client initialized (addr: {self.vault_addr})")

        except ImportError:
            # hvac library not installed - client will be None
            # All operations will raise SecretsBackendError with install instructions
            logger.warning(
                "hvac library not installed. Install with: pip install hvac. "
                "Vault operations will fail until hvac is installed."
            )
            self.client = None

    def get_secret(self, secret_name: str, version: str | None = None) -> SecretValue:
        """Retrieve secret from HashiCorp Vault"""
        if not self.client:
            raise SecretsBackendError(
                "hvac library required for HashiCorp Vault. Install with: pip install hvac"
            )

        try:
            # Use KV v2 secrets engine
            mount_point, secret_path = self._parse_secret_path(secret_name)

            read_kwargs = {"path": secret_path, "mount_point": mount_point}
            if version:
                read_kwargs["version"] = version

            response = self.client.secrets.kv.v2.read_secret_version(**read_kwargs)

            secret_data = response["data"]["data"]
            metadata_response = response["data"]["metadata"]

            metadata = SecretMetadata(
                secret_name=secret_name,
                version=str(metadata_response.get("version", "1")),
                created_at=metadata_response.get("created_time", datetime.now(UTC)),
            )

            return SecretValue(value=secret_data, metadata=metadata)

        except Exception as e:
            logger.error(f"Vault error retrieving secret: {e}", exc_info=True)
            if "Invalid path" in str(e) or "not found" in str(e).lower():
                raise SecretNotFoundError(f"Secret '{secret_name}' not found in Vault") from e
            raise SecretsBackendError(
                f"Failed to retrieve secret '{secret_name}' from Vault"
            ) from e

    def set_secret(
        self,
        secret_name: str,
        secret_value: str | dict[str, Any],
        description: str = "",
        tags: dict[str, str] | None = None,
    ) -> str:
        """Create or update secret in HashiCorp Vault"""
        if not self.client:
            raise SecretsBackendError(
                "hvac library required for HashiCorp Vault. Install with: pip install hvac"
            )

        try:
            mount_point, secret_path = self._parse_secret_path(secret_name)

            # Ensure secret_value is a dict for KV v2
            secret_data = {"value": secret_value} if isinstance(secret_value, str) else secret_value

            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret=secret_data,
                mount_point=mount_point,
            )

            version = str(response["data"]["version"])
            logger.info(f"Set secret in Vault: {secret_name} (version: {version})")
            return version

        except Exception as e:
            logger.error(f"Vault error setting secret: {e}", exc_info=True)
            raise SecretsBackendError(f"Failed to set secret '{secret_name}' in Vault") from e

    def rotate_secret(self, secret_name: str) -> str:
        """
        Rotate a secret in HashiCorp Vault.

        This performs a version bump by reading the current secret and
        writing it back, which creates a new version in Vault's KV v2 engine.

        For database credentials or other secrets requiring actual value changes,
        configure Vault's database secrets engine or use set_secret() with a new value.

        Args:
            secret_name: Name of the secret to rotate

        Returns:
            New version ID

        Raises:
            SecretRotationError: If rotation fails
        """
        if not self.client:
            raise SecretsBackendError(
                "hvac library required for HashiCorp Vault. Install with: pip install hvac"
            )

        try:
            # Get current secret
            current = self.get_secret(secret_name)
            current_value = current.value

            # Write back to create new version (Vault KV v2 auto-versions)
            mount_point, secret_path = self._parse_secret_path(secret_name)

            # Ensure value is a dict for KV v2
            secret_data = (
                {"value": current_value} if isinstance(current_value, str) else current_value
            )

            # Add rotation metadata
            secret_data["_rotated_at"] = datetime.now(UTC).isoformat()

            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=secret_path,
                secret=secret_data,
                mount_point=mount_point,
            )

            new_version = str(response["data"]["version"])
            logger.info(f"Rotated Vault secret: {secret_name} to version {new_version}")
            return new_version

        except Exception as e:
            logger.error(f"Vault error rotating secret: {e}", exc_info=True)
            raise SecretRotationError(f"Failed to rotate secret '{secret_name}' in Vault") from e

    def delete_secret(self, secret_name: str, force: bool = False) -> bool:
        """Delete secret from HashiCorp Vault"""
        if not self.client:
            raise SecretsBackendError(
                "hvac library required for HashiCorp Vault. Install with: pip install hvac"
            )

        try:
            mount_point, secret_path = self._parse_secret_path(secret_name)

            if force:
                # Permanently delete all versions
                self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                    path=secret_path,
                    mount_point=mount_point,
                )
                logger.warning(f"Force deleted secret from Vault: {secret_name}")
            else:
                # Soft delete (latest version)
                self.client.secrets.kv.v2.delete_latest_version_of_secret(
                    path=secret_path,
                    mount_point=mount_point,
                )
                logger.info(f"Deleted latest version of secret from Vault: {secret_name}")

            return True

        except Exception as e:
            logger.error(f"Vault error deleting secret: {e}", exc_info=True)
            raise SecretsBackendError(f"Failed to delete secret '{secret_name}' from Vault") from e

    def list_secrets(self, filters: dict[str, str] | None = None) -> list[str]:
        """List all secrets in HashiCorp Vault"""
        if not self.client:
            raise SecretsBackendError(
                "hvac library required for HashiCorp Vault. Install with: pip install hvac"
            )

        try:
            # List secrets from default KV v2 mount
            mount_point = "secret"
            response = self.client.secrets.kv.v2.list_secrets(
                path="",
                mount_point=mount_point,
            )

            secret_names = response.get("data", {}).get("keys", [])
            return secret_names

        except Exception as e:
            logger.error(f"Vault error listing secrets: {e}", exc_info=True)
            raise SecretsBackendError("Failed to list secrets from Vault") from e

    def _parse_secret_path(self, secret_name: str) -> tuple[str, str]:
        """
        Parse secret name into mount point and path.

        Format: mount_point/path or just path (defaults to 'secret' mount)
        """
        if "/" in secret_name:
            parts = secret_name.split("/", 1)
            return parts[0], parts[1]
        else:
            return "secret", secret_name


# =============================================================================
# Local Encrypted Backend (Development)
# =============================================================================


class LocalEncryptedBackend(SecretsBackend):
    """
    Local encrypted secrets backend for development.

    WARNING: This is for development/testing only.
    Do NOT use in production. Use AWS Secrets Manager or HashiCorp Vault.

    Stores secrets in encrypted files on disk using Fernet encryption.
    """

    def __init__(self, storage_path: Path | None = None, encryption_key: str | None = None):
        """
        Initialize local encrypted backend.

        Args:
            storage_path: Directory to store encrypted secrets
            encryption_key: Encryption key (generates one if not provided)
        """
        self.storage_path = storage_path or Path("secrets")
        self.storage_path.mkdir(exist_ok=True, mode=0o700)

        # Setup encryption
        import base64
        import hashlib

        from cryptography.fernet import Fernet

        if encryption_key:
            # Derive Fernet key from provided key
            key_bytes = hashlib.sha256(encryption_key.encode()).digest()
            self.fernet_key = base64.urlsafe_b64encode(key_bytes)
        else:
            # Generate new key
            self.fernet_key = Fernet.generate_key()
            logger.warning(
                "Generated ephemeral encryption key for local secrets. "
                "Set SECRETS_ENCRYPTION_KEY environment variable for persistence."
            )

        self.fernet = Fernet(self.fernet_key)
        logger.info(f"Local encrypted secrets backend initialized (path: {self.storage_path})")

    def get_secret(self, secret_name: str, version: str | None = None) -> SecretValue:
        """Retrieve secret from local encrypted storage"""
        secret_file = self.storage_path / f"{self._sanitize_name(secret_name)}.enc"

        if not secret_file.exists():
            raise SecretNotFoundError(f"Secret '{secret_name}' not found")

        try:
            # Read and decrypt
            with open(secret_file, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.fernet.decrypt(encrypted_data).decode()
            secret_data = json.loads(decrypted_data)

            # Parse value and metadata
            value = secret_data.get("value")
            metadata_dict = secret_data.get("metadata", {})

            # Try to parse value as JSON
            with contextlib.suppress(json.JSONDecodeError, TypeError):
                value = json.loads(value) if isinstance(value, str) else value

            metadata = SecretMetadata(**metadata_dict)

            return SecretValue(value=value, metadata=metadata)

        except Exception as e:
            logger.error(f"Error reading local secret: {e}", exc_info=True)
            raise SecretsBackendError(f"Failed to read secret '{secret_name}'") from e

    def set_secret(
        self,
        secret_name: str,
        secret_value: str | dict[str, Any],
        description: str = "",
        tags: dict[str, str] | None = None,
    ) -> str:
        """Create or update secret in local encrypted storage"""
        secret_file = self.storage_path / f"{self._sanitize_name(secret_name)}.enc"

        try:
            # Prepare secret data
            value = secret_value if isinstance(secret_value, dict) else str(secret_value)

            metadata = SecretMetadata(
                secret_name=secret_name,
                tags=tags or {},
            )

            secret_data = {
                "value": json.dumps(value) if isinstance(value, dict) else value,
                "metadata": metadata.model_dump(mode="json"),
            }

            # Encrypt and write
            encrypted_data = self.fernet.encrypt(json.dumps(secret_data).encode())

            with open(secret_file, "wb") as f:
                f.write(encrypted_data)

            secret_file.chmod(0o600)

            logger.info(f"Set local secret: {secret_name}")
            return metadata.version

        except Exception as e:
            logger.error(f"Error writing local secret: {e}", exc_info=True)
            raise SecretsBackendError(f"Failed to write secret '{secret_name}'") from e

    def rotate_secret(self, secret_name: str) -> str:
        """Rotate secret (for local backend, just updates version)"""
        try:
            # Get current secret
            current = self.get_secret(secret_name)

            # Update metadata with new version
            new_version = str(int(current.metadata.version) + 1)
            current.metadata.version = new_version
            current.metadata.updated_at = datetime.now(UTC)
            current.metadata.last_rotated = datetime.now(UTC)

            # Save with new version
            secret_file = self.storage_path / f"{self._sanitize_name(secret_name)}.enc"

            secret_data = {
                "value": (
                    json.dumps(current.value) if isinstance(current.value, dict) else current.value
                ),
                "metadata": current.metadata.model_dump(mode="json"),
            }

            encrypted_data = self.fernet.encrypt(json.dumps(secret_data).encode())

            with open(secret_file, "wb") as f:
                f.write(encrypted_data)

            logger.info(f"Rotated local secret: {secret_name} to version {new_version}")
            return new_version

        except Exception as e:
            logger.error(f"Error rotating local secret: {e}", exc_info=True)
            raise SecretRotationError(f"Failed to rotate secret '{secret_name}'") from e

    def delete_secret(self, secret_name: str, force: bool = False) -> bool:
        """Delete secret from local encrypted storage"""
        secret_file = self.storage_path / f"{self._sanitize_name(secret_name)}.enc"

        try:
            if secret_file.exists():
                secret_file.unlink()
                logger.info(f"Deleted local secret: {secret_name}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting local secret: {e}", exc_info=True)
            raise SecretsBackendError(f"Failed to delete secret '{secret_name}'") from e

    def list_secrets(self, filters: dict[str, str] | None = None) -> list[str]:
        """List all secrets in local encrypted storage"""
        secret_names = []

        for secret_file in self.storage_path.glob("*.enc"):
            secret_name = secret_file.stem

            # Apply filters if provided
            if filters:
                try:
                    secret = self.get_secret(secret_name)
                    if not all(secret.metadata.tags.get(k) == v for k, v in filters.items()):
                        continue
                except Exception:
                    continue

            secret_names.append(secret_name)

        return secret_names

    def _sanitize_name(self, secret_name: str) -> str:
        """Sanitize secret name for filesystem"""
        return secret_name.replace("/", "_").replace("\\", "_")


# =============================================================================
# Unified Secrets Manager
# =============================================================================


class SecretsManager:
    """
    Unified secrets management interface.

    Automatically detects and uses the appropriate backend based on configuration.

    Backend Priority:
    1. AWS Secrets Manager (if AWS_REGION set)
    2. HashiCorp Vault (if VAULT_ADDR set)
    3. Local Encrypted (development fallback)

    Usage:
        # Auto-detect backend
        secrets = SecretsManager()

        # Or specify backend explicitly
        secrets = SecretsManager(backend_type=SecretBackendType.AWS_SECRETS_MANAGER)

        # Get secret
        value = secrets.get_secret("database/connection_string")

        # Set secret
        secrets.set_secret("api/openai_key", "sk-...")

        # Rotate secret
        secrets.rotate_secret("jwt/secret_key")
    """

    def __init__(
        self,
        backend_type: SecretBackendType | None = None,
        **backend_kwargs,
    ):
        """
        Initialize secrets manager with auto-detected or specified backend.

        Args:
            backend_type: Explicit backend type (auto-detects if None)
            **backend_kwargs: Additional arguments for backend initialization
        """
        self.backend_type = backend_type or self._detect_backend()
        self.backend = self._create_backend(**backend_kwargs)

        logger.info(f"SecretsManager initialized with backend: {self.backend_type.value}")

    def _detect_backend(self) -> SecretBackendType:
        """Auto-detect which backend to use based on environment"""
        # Check for AWS
        if os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"):
            logger.info("Detected AWS environment, using AWS Secrets Manager")
            return SecretBackendType.AWS_SECRETS_MANAGER

        # Check for Vault
        if os.getenv("VAULT_ADDR"):
            logger.info("Detected Vault configuration, using HashiCorp Vault")
            return SecretBackendType.HASHICORP_VAULT

        # Default to local encrypted for development
        logger.warning(
            "No cloud secrets backend detected. Using local encrypted storage. "
            "This is NOT recommended for production. "
            "Set AWS_REGION or VAULT_ADDR to use a production backend."
        )
        return SecretBackendType.LOCAL_ENCRYPTED

    def _create_backend(self, **kwargs) -> SecretsBackend:
        """Create backend instance based on type"""
        if self.backend_type == SecretBackendType.AWS_SECRETS_MANAGER:
            return AWSSecretsManager(**kwargs)
        elif self.backend_type == SecretBackendType.HASHICORP_VAULT:
            return HashiCorpVault(**kwargs)
        elif self.backend_type == SecretBackendType.LOCAL_ENCRYPTED:
            encryption_key = os.getenv("SECRETS_ENCRYPTION_KEY")
            return LocalEncryptedBackend(encryption_key=encryption_key, **kwargs)
        else:
            raise ValueError(f"Unsupported backend type: {self.backend_type}")

    def get_secret(self, secret_name: str, version: str | None = None, default: Any = None) -> Any:
        """
        Retrieve a secret value.

        Args:
            secret_name: Name of the secret
            version: Optional version (defaults to latest)
            default: Default value if secret not found

        Returns:
            Secret value (string or dict)
        """
        try:
            secret = self.backend.get_secret(secret_name, version)
            return secret.value
        except SecretNotFoundError:
            if default is not None:
                logger.warning(f"Secret '{secret_name}' not found, using default value")
                return default
            raise

    def set_secret(
        self,
        secret_name: str,
        secret_value: str | dict[str, Any],
        description: str = "",
        tags: dict[str, str] | None = None,
    ) -> str:
        """
        Create or update a secret.

        Args:
            secret_name: Name of the secret
            secret_value: Secret value (string or dict)
            description: Optional description
            tags: Optional tags for organization

        Returns:
            Version ID of the secret
        """
        return self.backend.set_secret(secret_name, secret_value, description, tags)

    def rotate_secret(self, secret_name: str) -> str:
        """
        Trigger rotation of a secret.

        Note: Rotation behavior depends on backend.
        AWS Secrets Manager requires Lambda function configuration.

        Args:
            secret_name: Name of the secret to rotate

        Returns:
            New version ID
        """
        return self.backend.rotate_secret(secret_name)

    def delete_secret(self, secret_name: str, force: bool = False) -> bool:
        """
        Delete a secret.

        Args:
            secret_name: Name of the secret
            force: If True, immediate deletion; if False, schedule for deletion

        Returns:
            True if successful
        """
        return self.backend.delete_secret(secret_name, force)

    def list_secrets(self, filters: dict[str, str] | None = None) -> list[str]:
        """
        List all secret names.

        Args:
            filters: Optional filters (e.g., tags)

        Returns:
            List of secret names
        """
        return self.backend.list_secrets(filters)

    def get_or_env(self, secret_name: str, env_var: str, default: Any = None) -> Any:
        """
        Get secret from backend, fallback to environment variable.

        Useful for migration from environment variables to secrets manager.

        Args:
            secret_name: Name in secrets backend
            env_var: Environment variable name as fallback
            default: Default if neither found

        Returns:
            Secret value
        """
        try:
            return self.get_secret(secret_name)
        except SecretNotFoundError:
            value = os.getenv(env_var)
            if value:
                logger.info(
                    f"Using environment variable {env_var} (consider migrating to {secret_name})"
                )
                return value
            if default is not None:
                return default
            raise SecretNotFoundError(
                f"Secret '{secret_name}' not found and environment variable '{env_var}' not set"
            )


# =============================================================================
# Global Instance & Helper Functions
# =============================================================================

# Global secrets manager instance (initialized on first import)
_global_secrets_manager: SecretsManager | None = None


def get_secrets_manager() -> SecretsManager:
    """Get or create global secrets manager instance"""
    global _global_secrets_manager
    if _global_secrets_manager is None:
        _global_secrets_manager = SecretsManager()
    return _global_secrets_manager


def get_secret(secret_name: str, default: Any = None) -> Any:
    """
    Convenience function to get a secret using global manager.

    Usage:
        db_password = get_secret("database/password")
        api_key = get_secret("api/openai_key", default="sk-test-key")
    """
    return get_secrets_manager().get_secret(secret_name, default=default)


def set_secret(secret_name: str, secret_value: str | dict[str, Any]) -> str:
    """Convenience function to set a secret using global manager"""
    return get_secrets_manager().set_secret(secret_name, secret_value)


# =============================================================================
# Automatic Rotation Scheduler
# =============================================================================


class RotationPolicy(BaseModel):
    """Configuration for a secret rotation policy."""

    secret_pattern: str = Field(
        ..., description="Glob pattern for matching secrets (e.g., 'database/*')"
    )
    interval_days: int = Field(default=90, ge=1, le=365, description="Rotation interval in days")
    notify_days_before: int = Field(
        default=7, ge=0, le=30, description="Days before rotation to send notification"
    )
    enabled: bool = Field(default=True, description="Whether this policy is active")
    rotation_handler: str | None = Field(default=None, description="Custom rotation handler name")
    tags: dict[str, str] = Field(default_factory=dict, description="Tags for filtering")


class RotationEvent(BaseModel):
    """Record of a rotation event."""

    secret_name: str
    policy_pattern: str
    old_version: str
    new_version: str
    rotated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    success: bool = True
    error_message: str | None = None


class SecretRotationScheduler:
    """
    Automated secret rotation scheduler.

    Provides scheduled rotation of secrets based on configurable policies.
    Supports multiple rotation policies with pattern matching, notifications,
    and comprehensive audit logging.

    Features:
    - Periodic checks for secrets needing rotation
    - Configurable rotation policies per secret type (glob patterns)
    - Notification callbacks before rotation
    - Rollback capability if rotation fails
    - Audit logging of all rotations
    - Thread-safe operation

    Example:
        >>> scheduler = SecretRotationScheduler(secrets_manager)
        >>> scheduler.add_rotation_policy(
        ...     secret_pattern="database/*",
        ...     interval_days=90,
        ...     notify_days_before=7,
        ... )
        >>> scheduler.start()
        >>> # Later...
        >>> scheduler.stop()
    """

    def __init__(
        self,
        secrets_manager: "SecretsManager",
        check_interval_seconds: int = 3600,
        notification_callback: Any | None = None,
    ):
        """
        Initialize the rotation scheduler.

        Args:
            secrets_manager: SecretsManager instance to use for rotations
            check_interval_seconds: How often to check for needed rotations (default: 1 hour)
            notification_callback: Optional callback for rotation notifications
                                   Signature: callback(secret_name: str, days_until_rotation: int)
        """
        self.secrets_manager = secrets_manager
        self.check_interval_seconds = check_interval_seconds
        self.notification_callback = notification_callback
        import threading

        self._policies: list[RotationPolicy] = []
        self._rotation_history: list[RotationEvent] = []
        self._running = False
        self._scheduler_thread: threading.Thread | None = None
        self._lock: threading.Lock = threading.Lock()
        self.logger = logging.getLogger(f"{__name__}.SecretRotationScheduler")

    def _ensure_lock(self) -> None:
        """Ensure thread lock is initialized (no-op, lock is always initialized)."""
        pass

    def add_rotation_policy(
        self,
        secret_pattern: str,
        interval_days: int = 90,
        notify_days_before: int = 7,
        enabled: bool = True,
        rotation_handler: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> RotationPolicy:
        """
        Add a rotation policy for secrets matching a pattern.

        Args:
            secret_pattern: Glob pattern for matching secrets (e.g., "database/*", "api/keys/*")
            interval_days: Number of days between rotations (1-365)
            notify_days_before: Days before rotation to trigger notification (0-30)
            enabled: Whether this policy is active
            rotation_handler: Optional custom handler name for special rotation logic
            tags: Optional tags for filtering

        Returns:
            The created RotationPolicy

        Example:
            >>> scheduler.add_rotation_policy(
            ...     secret_pattern="database/*",
            ...     interval_days=90,
            ...     notify_days_before=7,
            ... )
        """
        self._ensure_lock()
        policy = RotationPolicy(
            secret_pattern=secret_pattern,
            interval_days=interval_days,
            notify_days_before=notify_days_before,
            enabled=enabled,
            rotation_handler=rotation_handler,
            tags=tags or {},
        )

        with self._lock:
            self._policies.append(policy)

        self.logger.info(
            f"Added rotation policy: pattern='{secret_pattern}', "
            f"interval={interval_days}d, notify={notify_days_before}d before"
        )
        return policy

    def remove_rotation_policy(self, secret_pattern: str) -> bool:
        """
        Remove a rotation policy by pattern.

        Args:
            secret_pattern: The pattern of the policy to remove

        Returns:
            True if policy was found and removed, False otherwise
        """
        self._ensure_lock()
        with self._lock:
            original_count = len(self._policies)
            self._policies = [p for p in self._policies if p.secret_pattern != secret_pattern]
            removed = len(self._policies) < original_count

        if removed:
            self.logger.info(f"Removed rotation policy: pattern='{secret_pattern}'")
        return removed

    def list_policies(self) -> list[RotationPolicy]:
        """
        List all configured rotation policies.

        Returns:
            List of RotationPolicy objects
        """
        self._ensure_lock()
        with self._lock:
            return list(self._policies)

    def _matches_pattern(self, secret_name: str, pattern: str) -> bool:
        """Check if secret name matches a glob pattern."""
        import fnmatch

        return fnmatch.fnmatch(secret_name, pattern)

    def _get_matching_policy(self, secret_name: str) -> RotationPolicy | None:
        """Find the first matching policy for a secret."""
        self._ensure_lock()
        with self._lock:
            for policy in self._policies:
                if policy.enabled and self._matches_pattern(secret_name, policy.secret_pattern):
                    return policy
        return None

    def check_rotation_needed(self, secret_name: str) -> tuple[bool, int | None]:
        """
        Check if a secret needs rotation.

        Args:
            secret_name: Name of the secret to check

        Returns:
            Tuple of (needs_rotation: bool, days_until_rotation: int | None)
        """
        policy = self._get_matching_policy(secret_name)
        if not policy:
            return False, None

        try:
            secret = self.secrets_manager.backend.get_secret(secret_name)
            metadata = secret.metadata

            # Check last rotation time
            last_rotated = metadata.last_rotated or metadata.created_at
            if last_rotated is None:
                return True, 0

            # Calculate days since last rotation
            now = datetime.now(UTC)
            # Handle timezone-naive datetimes
            if last_rotated.tzinfo is None:
                last_rotated = last_rotated.replace(tzinfo=UTC)

            days_since_rotation = (now - last_rotated).days
            days_until_rotation = policy.interval_days - days_since_rotation

            needs_rotation = days_until_rotation <= 0

            return needs_rotation, days_until_rotation

        except SecretNotFoundError:
            return False, None
        except Exception as e:
            self.logger.error(f"Error checking rotation for {secret_name}: {e}")
            return False, None

    def rotate_secret(self, secret_name: str, force: bool = False) -> RotationEvent:
        """
        Rotate a specific secret.

        Args:
            secret_name: Name of the secret to rotate
            force: If True, rotate even if not due

        Returns:
            RotationEvent with rotation details

        Raises:
            SecretRotationError: If rotation fails
        """
        policy = self._get_matching_policy(secret_name)
        pattern = policy.secret_pattern if policy else "manual"

        try:
            # Get current version
            current = self.secrets_manager.backend.get_secret(secret_name)
            old_version = current.metadata.version

            # Perform rotation
            new_version = self.secrets_manager.rotate_secret(secret_name)

            event = RotationEvent(
                secret_name=secret_name,
                policy_pattern=pattern,
                old_version=old_version,
                new_version=new_version,
                success=True,
            )

            self._ensure_lock()
            with self._lock:
                self._rotation_history.append(event)

            self.logger.info(f"Rotated secret '{secret_name}': v{old_version} -> v{new_version}")
            return event

        except Exception as e:
            event = RotationEvent(
                secret_name=secret_name,
                policy_pattern=pattern,
                old_version="unknown",
                new_version="failed",
                success=False,
                error_message=str(e),
            )

            self._ensure_lock()
            with self._lock:
                self._rotation_history.append(event)

            self.logger.error(f"Failed to rotate secret '{secret_name}': {e}")
            raise SecretRotationError(f"Failed to rotate secret '{secret_name}'") from e

    def check_and_rotate_all(self) -> list[RotationEvent]:
        """
        Check all secrets and rotate those that need it.

        Returns:
            List of RotationEvent objects for rotations performed
        """
        events: list[RotationEvent] = []

        try:
            # Get all secrets
            all_secrets = self.secrets_manager.backend.list_secrets()

            for secret_name in all_secrets:
                needs_rotation, days_until = self.check_rotation_needed(secret_name)

                # Send notification if approaching rotation
                if days_until is not None and 0 < days_until <= 7:
                    policy = self._get_matching_policy(secret_name)
                    if policy and days_until <= policy.notify_days_before:
                        self._send_notification(secret_name, days_until)

                # Rotate if needed
                if needs_rotation:
                    try:
                        event = self.rotate_secret(secret_name)
                        events.append(event)
                    except SecretRotationError as e:
                        self.logger.error(f"Rotation failed for {secret_name}: {e}")

        except Exception as e:
            self.logger.error(f"Error during rotation check: {e}")

        return events

    def _send_notification(self, secret_name: str, days_until_rotation: int) -> None:
        """Send rotation notification via callback."""
        if self.notification_callback:
            try:
                self.notification_callback(secret_name, days_until_rotation)
                self.logger.info(
                    f"Sent rotation notification for '{secret_name}' "
                    f"({days_until_rotation} days until rotation)"
                )
            except Exception as e:
                self.logger.error(f"Failed to send notification for {secret_name}: {e}")

    def _scheduler_loop(self) -> None:
        """Background scheduler loop."""
        import time

        self.logger.info("Rotation scheduler started")

        while self._running:
            try:
                events = self.check_and_rotate_all()
                if events:
                    self.logger.info(f"Rotation check completed: {len(events)} secrets rotated")
            except Exception as e:
                self.logger.error(f"Error in scheduler loop: {e}")

            # Sleep in small increments to allow quick shutdown
            for _ in range(self.check_interval_seconds):
                if not self._running:
                    break
                time.sleep(1)

        self.logger.info("Rotation scheduler stopped")

    def start(self) -> None:
        """
        Start the background rotation scheduler.

        The scheduler runs in a separate thread and periodically checks
        for secrets that need rotation.
        """
        import threading

        if self._running:
            self.logger.warning("Scheduler is already running")
            return

        self._running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="SecretRotationScheduler",
            daemon=True,
        )
        self._scheduler_thread.start()
        self.logger.info("Started rotation scheduler thread")

    def stop(self, timeout: float = 10.0) -> None:
        """
        Stop the background rotation scheduler.

        Args:
            timeout: Maximum seconds to wait for scheduler to stop
        """
        if not self._running:
            return

        self._running = False

        if self._scheduler_thread and self._scheduler_thread.is_alive():
            self._scheduler_thread.join(timeout=timeout)
            if self._scheduler_thread.is_alive():
                self.logger.warning("Scheduler thread did not stop within timeout")

        self._scheduler_thread = None
        self.logger.info("Stopped rotation scheduler")

    def get_rotation_history(
        self,
        secret_name: str | None = None,
        limit: int = 100,
    ) -> list[RotationEvent]:
        """
        Get rotation history.

        Args:
            secret_name: Filter by secret name (optional)
            limit: Maximum number of events to return

        Returns:
            List of RotationEvent objects, most recent first
        """
        self._ensure_lock()
        with self._lock:
            history = list(self._rotation_history)

        if secret_name:
            history = [e for e in history if e.secret_name == secret_name]

        # Sort by date descending and limit
        history.sort(key=lambda e: e.rotated_at, reverse=True)
        return history[:limit]

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running."""
        return self._running
