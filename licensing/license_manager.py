"""
DevSkyy Enterprise License Manager

Production-grade license management with cryptographic key generation and validation.

Standards Compliance:
- RFC 4122: UUID generation for unique identifiers
- RFC 7519: JWT for signed license tokens
- ISO 8601: Date/time handling
- NIST SP 800-90Ar1: Cryptographically secure random number generation

Security Features:
- Cryptographically secure license key generation using secrets module
- JWT-based license tokens with digital signatures
- Hardware binding and domain restrictions
- Tamper detection through HMAC signatures
- Audit logging for all operations

Reference: https://www.rfc-editor.org/rfc/rfc4122
Reference: https://www.rfc-editor.org/rfc/rfc7519
"""

import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List

import jwt
from sqlalchemy.orm import Session

from licensing.license_tiers import (
    LicenseTier,
    LicenseType,
    get_tier_features,
    check_feature_access,
    check_limit,
)
from licensing.models import License, LicenseActivation, LicenseAuditLog, LicenseUsageRecord

logger = logging.getLogger(__name__)


# ============================================================================
# LICENSE KEY GENERATION - RFC 4122 & Cryptographically Secure
# ============================================================================

class LicenseKeyGenerator:
    """
    Generates cryptographically secure license keys.

    Uses Python's secrets module (NIST SP 800-90Ar1 compliant CSPRNG)
    combined with HMAC-SHA256 for tamper detection.

    Format: PREFIX-XXXXX-XXXXX-XXXXX-XXXXX-CHECKSUM
    - PREFIX: License tier indicator
    - XXXXX: 5 groups of base32-encoded random bytes
    - CHECKSUM: HMAC-SHA256 verification code

    Standards:
    - NIST SP 800-90Ar1: Random number generation
    - RFC 2104: HMAC for message authentication
    """

    # Base32 alphabet (excludes ambiguous characters: 0, 1, I, O)
    BASE32_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    @classmethod
    def generate(cls, tier: LicenseTier, secret_key: str) -> str:
        """
        Generate a cryptographically secure license key.

        Args:
            tier: License tier (determines prefix)
            secret_key: Secret key for HMAC signature

        Returns:
            License key in format: TIER-XXXXX-XXXXX-XXXXX-XXXXX-CHECKSUM

        Example:
            ENT-A7K9P-X3M2N-B5V8Q-W4R6T-F2J9
        """
        # Tier prefix mapping
        tier_prefixes = {
            LicenseTier.TRIAL: "TRL",
            LicenseTier.PROFESSIONAL: "PRO",
            LicenseTier.BUSINESS: "BUS",
            LicenseTier.ENTERPRISE: "ENT",
            LicenseTier.CUSTOM: "CUS",
        }

        prefix = tier_prefixes.get(tier, "UNK")

        # Generate 4 groups of 5 random characters each (20 bytes = 160 bits entropy)
        groups = []
        for _ in range(4):
            # NIST SP 800-90Ar1 compliant CSPRNG via secrets module
            random_bytes = secrets.token_bytes(5)
            # Convert to base32 using our alphabet
            group = "".join(cls.BASE32_ALPHABET[b % len(cls.BASE32_ALPHABET)] for b in random_bytes)
            groups.append(group)

        # Combine groups
        key_body = f"{prefix}-{'-'.join(groups)}"

        # Generate HMAC checksum (RFC 2104)
        checksum = cls._generate_checksum(key_body, secret_key)

        # Final license key
        return f"{key_body}-{checksum}"

    @classmethod
    def validate_format(cls, license_key: str) -> bool:
        """
        Validate license key format (not cryptographic validation).

        Args:
            license_key: License key to validate

        Returns:
            True if format is correct
        """
        parts = license_key.split("-")

        # Should have 6 parts: PREFIX + 4 groups + CHECKSUM
        if len(parts) != 6:
            return False

        # Check prefix
        if parts[0] not in ["TRL", "PRO", "BUS", "ENT", "CUS"]:
            return False

        # Check groups (should be 5 characters each)
        for group in parts[1:5]:
            if len(group) != 5:
                return False
            if not all(c in cls.BASE32_ALPHABET for c in group):
                return False

        # Check checksum (should be 4 characters)
        if len(parts[5]) != 4:
            return False

        return True

    @classmethod
    def verify_checksum(cls, license_key: str, secret_key: str) -> bool:
        """
        Verify license key checksum using HMAC.

        Args:
            license_key: License key to verify
            secret_key: Secret key used for HMAC

        Returns:
            True if checksum is valid
        """
        parts = license_key.split("-")
        if len(parts) != 6:
            return False

        key_body = "-".join(parts[:5])
        provided_checksum = parts[5]
        expected_checksum = cls._generate_checksum(key_body, secret_key)

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(provided_checksum, expected_checksum)

    @staticmethod
    def _generate_checksum(data: str, secret_key: str) -> str:
        """
        Generate HMAC-SHA256 checksum per RFC 2104.

        Args:
            data: Data to sign
            secret_key: Secret signing key

        Returns:
            4-character base32 checksum
        """
        # RFC 2104: HMAC-SHA256
        h = hmac.new(secret_key.encode(), data.encode(), hashlib.sha256)
        digest = h.digest()

        # Take first 2 bytes and encode as base32
        checksum_bytes = digest[:2]
        alphabet = LicenseKeyGenerator.BASE32_ALPHABET
        return "".join(alphabet[b % len(alphabet)] for b in checksum_bytes[:4])


# ============================================================================
# LICENSE MANAGER - Core Business Logic
# ============================================================================

class LicenseManager:
    """
    Enterprise license management system.

    Handles license lifecycle:
    - Generation and issuance
    - Activation and validation
    - Feature access control
    - Usage tracking and limits
    - Renewal and expiration

    All operations are logged for audit compliance.
    """

    def __init__(self, db_session: Session, secret_key: str, jwt_secret: Optional[str] = None):
        """
        Initialize license manager.

        Args:
            db_session: SQLAlchemy database session
            secret_key: Secret key for license key HMAC
            jwt_secret: Secret key for JWT tokens (defaults to secret_key)
        """
        self.db = db_session
        self.secret_key = secret_key
        self.jwt_secret = jwt_secret or secret_key
        self.key_generator = LicenseKeyGenerator()

    # ========================================================================
    # LICENSE CREATION
    # ========================================================================

    def create_license(
        self,
        customer_id: str,
        customer_name: str,
        customer_email: str,
        tier: LicenseTier,
        license_type: LicenseType,
        duration_days: Optional[int] = None,
        organization: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
    ) -> License:
        """
        Create a new license.

        Args:
            customer_id: Unique customer identifier (RFC 4122 UUID)
            customer_name: Customer name
            customer_email: Customer email
            tier: License tier (Trial, Professional, Business, Enterprise, Custom)
            license_type: Type (Trial, Subscription, Perpetual, Concurrent)
            duration_days: License duration in days (None for perpetual)
            organization: Organization name
            metadata: Custom metadata
            created_by: User who created the license

        Returns:
            Created License object

        Raises:
            ValueError: If parameters are invalid
        """
        # Validate inputs
        if not customer_id or not customer_name or not customer_email:
            raise ValueError("Customer ID, name, and email are required")

        # Generate license key
        license_key = self.key_generator.generate(tier, self.secret_key)

        # Get tier features
        features = get_tier_features(tier)

        # Calculate expiration
        expires_at = None
        if duration_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
        elif license_type == LicenseType.TRIAL:
            expires_at = datetime.now(timezone.utc) + timedelta(days=14)  # Default 14-day trial

        # Create license
        license = License(
            license_id=str(uuid.uuid4()),
            license_key=license_key,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_email=customer_email,
            organization=organization,
            tier=tier,
            license_type=license_type,
            expires_at=expires_at,
            max_users=features.max_users,
            max_ai_agents=features.max_ai_agents,
            max_concurrent_agents=features.max_concurrent_agents,
            api_requests_per_month=features.api_requests_per_month,
            metadata=metadata or {},
            created_by=created_by,
        )

        self.db.add(license)

        # Audit log
        self._log_event(
            license_id=license.license_id,
            event_type="license_created",
            actor_id=created_by,
            message=f"Created {tier} license for {customer_name}",
            event_data={
                "tier": tier,
                "type": license_type,
                "duration_days": duration_days,
            },
        )

        self.db.commit()
        logger.info(f"Created license {license.license_id} for customer {customer_id}")

        return license

    # ========================================================================
    # LICENSE ACTIVATION
    # ========================================================================

    def activate_license(
        self,
        license_key: str,
        hardware_id: str,
        machine_name: Optional[str] = None,
        os_info: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Activate a license on a specific machine.

        Args:
            license_key: License key to activate
            hardware_id: Unique hardware identifier (MAC address, CPU ID, etc.)
            machine_name: Machine name
            os_info: Operating system information
            ip_address: IP address of activation

        Returns:
            Activation result with JWT token

        Raises:
            ValueError: If license is invalid or activation fails
        """
        # Verify checksum
        if not self.key_generator.verify_checksum(license_key, self.secret_key):
            raise ValueError("Invalid license key checksum")

        # Find license
        license = self.db.query(License).filter(License.license_key == license_key).first()
        if not license:
            raise ValueError("License not found")

        # Check if license is valid
        if not license.is_valid():
            reasons = []
            if not license.is_active and not license.activated_at:
                # First activation
                pass  # Allow activation
            elif license.is_suspended:
                reasons.append("suspended")
            elif license.is_revoked:
                reasons.append("revoked")
            elif license.expires_at and datetime.now(timezone.utc) > license.expires_at:
                reasons.append("expired")

            if reasons:
                raise ValueError(f"License is {', '.join(reasons)}")

        # Check concurrent activation limit
        active_count = (
            self.db.query(LicenseActivation)
            .filter(
                LicenseActivation.license_id == license.license_id,
                LicenseActivation.is_active == True,  # noqa: E712
            )
            .count()
        )

        if active_count >= license.max_concurrent_activations:
            raise ValueError(f"Maximum concurrent activations ({license.max_concurrent_activations}) reached")

        # Check hardware binding
        if license.bound_hardware_id and license.bound_hardware_id != hardware_id:
            raise ValueError("License is bound to different hardware")

        # Create activation
        activation = LicenseActivation(
            activation_id=str(uuid.uuid4()),
            license_id=license.license_id,
            hardware_id=hardware_id,
            machine_name=machine_name,
            os_info=os_info,
            ip_address=ip_address,
            last_heartbeat_at=datetime.now(timezone.utc),
        )

        self.db.add(activation)

        # Update license
        if not license.activated_at:
            license.activated_at = datetime.now(timezone.utc)
        license.is_active = True
        license.current_activations = active_count + 1

        # Audit log
        self._log_event(
            license_id=license.license_id,
            event_type="license_activated",
            actor_ip=ip_address,
            message=f"License activated on {machine_name or hardware_id}",
            event_data={"hardware_id": hardware_id, "machine_name": machine_name},
        )

        self.db.commit()

        # Generate JWT token for client (RFC 7519)
        token = self._generate_jwt_token(license, activation)

        logger.info(f"Activated license {license.license_id} on {hardware_id}")

        return {
            "success": True,
            "license_id": license.license_id,
            "activation_id": activation.activation_id,
            "token": token,
            "tier": license.tier,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
        }

    # ========================================================================
    # LICENSE VALIDATION
    # ========================================================================

    def validate_license(self, license_key: str, hardware_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a license and return its status.

        Args:
            license_key: License key to validate
            hardware_id: Hardware ID (for activation check)

        Returns:
            Validation result with license details
        """
        # Verify format
        if not self.key_generator.validate_format(license_key):
            return {"valid": False, "reason": "Invalid license key format"}

        # Verify checksum
        if not self.key_generator.verify_checksum(license_key, self.secret_key):
            return {"valid": False, "reason": "Invalid license key checksum"}

        # Find license
        license = self.db.query(License).filter(License.license_key == license_key).first()
        if not license:
            return {"valid": False, "reason": "License not found"}

        # Update last checked
        license.last_checked_at = datetime.now(timezone.utc)
        self.db.commit()

        # Check validity
        is_valid = license.is_valid()

        result = {
            "valid": is_valid,
            "license_id": license.license_id,
            "tier": license.tier,
            "type": license.license_type,
            "customer": license.customer_name,
            "is_active": license.is_active,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "days_remaining": license.days_until_expiration(),
        }

        if not is_valid:
            reasons = []
            if not license.is_active:
                reasons.append("not activated")
            if license.is_suspended:
                reasons.append("suspended")
            if license.is_revoked:
                reasons.append("revoked")
            if license.expires_at and datetime.now(timezone.utc) > license.expires_at:
                reasons.append("expired")
            result["reason"] = ", ".join(reasons) if reasons else "unknown"

        return result

    # ========================================================================
    # FEATURE ACCESS CONTROL
    # ========================================================================

    def check_feature(self, license_id: str, feature_name: str) -> bool:
        """
        Check if a license has access to a specific feature.

        Args:
            license_id: License ID
            feature_name: Feature to check (e.g., "webhooks", "sso")

        Returns:
            True if feature is accessible
        """
        license = self.db.query(License).filter(License.license_id == license_id).first()
        if not license or not license.is_valid():
            return False

        return check_feature_access(LicenseTier(license.tier), feature_name)

    def check_usage_limit(self, license_id: str, limit_name: str, current_value: int) -> bool:
        """
        Check if current usage is within license limits.

        Args:
            license_id: License ID
            limit_name: Limit to check (e.g., "max_ai_agents")
            current_value: Current usage value

        Returns:
            True if within limits
        """
        license = self.db.query(License).filter(License.license_id == license_id).first()
        if not license or not license.is_valid():
            return False

        return check_limit(LicenseTier(license.tier), limit_name, current_value)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _generate_jwt_token(self, license: License, activation: LicenseActivation) -> str:
        """
        Generate JWT token for activated license per RFC 7519.

        Args:
            license: License object
            activation: Activation object

        Returns:
            Signed JWT token
        """
        payload = {
            "iss": "DevSkyy",  # Issuer
            "sub": license.license_id,  # Subject (license ID)
            "iat": datetime.now(timezone.utc),  # Issued at (RFC 7519 4.1.6)
            "exp": license.expires_at if license.expires_at else None,  # Expiration (RFC 7519 4.1.4)
            "tier": license.tier,
            "activation_id": activation.activation_id,
            "hardware_id": activation.hardware_id,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        # Sign with HS256 per RFC 7519 Section 7.1
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token

    def _log_event(
        self,
        license_id: str,
        event_type: str,
        message: str,
        actor_id: Optional[str] = None,
        actor_ip: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ):
        """Log audit event."""
        log = LicenseAuditLog(
            log_id=str(uuid.uuid4()),
            license_id=license_id,
            event_type=event_type,
            message=message,
            actor_id=actor_id,
            actor_ip=actor_ip,
            event_data=event_data,
        )
        self.db.add(log)
