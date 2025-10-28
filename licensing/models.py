"""
License Database Models for DevSkyy Enterprise Platform

SQLAlchemy models for license management, activation tracking, and usage monitoring.

Standards Compliance:
- ISO 8601: Date/time storage and formatting
- RFC 4122: UUID primary keys
- SQL: ANSI SQL standards for data types
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    DateTime,
    Float,
    JSON,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from licensing.license_tiers import LicenseTier, LicenseType

Base = declarative_base()


# ============================================================================
# LICENSE MODEL
# ============================================================================

class License(Base):
    """
    Core license model tracking all license information.

    Each license represents a contract between DevSkyy and a customer,
    defining access rights, limits, and validity period.

    Standards:
    - RFC 4122: UUID for license_id
    - ISO 8601: Date/time fields
    """

    __tablename__ = "licenses"

    # Primary Key (RFC 4122 UUID v4)
    license_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # License Key (Cryptographically Secure)
    license_key = Column(String(512), unique=True, nullable=False, index=True)

    # Customer Information
    customer_id = Column(String(36), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    organization = Column(String(255))

    # License Configuration
    tier = Column(String(50), nullable=False, default=LicenseTier.TRIAL)
    license_type = Column(String(50), nullable=False, default=LicenseType.TRIAL)

    # Validity Period (ISO 8601)
    issued_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    activated_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))

    # Status
    is_active = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    is_revoked = Column(Boolean, default=False)

    # Limits & Quotas (copied from tier for performance)
    max_users = Column(Integer, default=1)
    max_ai_agents = Column(Integer, default=3)
    max_concurrent_agents = Column(Integer, default=1)
    api_requests_per_month = Column(Integer, default=10000)

    # Hardware/Domain Binding
    bound_hardware_id = Column(String(255))  # MAC address, CPU ID, etc.
    bound_domain = Column(String(255))  # example.com
    allowed_ips = Column(JSON)  # List of allowed IP addresses

    # Concurrent License Tracking
    max_concurrent_activations = Column(Integer, default=1)
    current_activations = Column(Integer, default=0)

    # Metadata
    metadata = Column(JSON)  # Custom fields per customer
    notes = Column(Text)  # Internal notes

    # Audit Trail
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(255))  # User who created the license
    last_checked_at = Column(DateTime(timezone=True))  # Last validation check

    # Relationships
    activations = relationship("LicenseActivation", back_populates="license", cascade="all, delete-orphan")
    usage_records = relationship("LicenseUsageRecord", back_populates="license", cascade="all, delete-orphan")

    # Indexes for performance
    __table_args__ = (
        Index("idx_customer_id_tier", "customer_id", "tier"),
        Index("idx_expires_at_active", "expires_at", "is_active"),
        Index("idx_license_type_tier", "license_type", "tier"),
    )

    def is_valid(self) -> bool:
        """
        Check if license is currently valid.

        A license is valid if:
        - It is active (activated)
        - Not suspended or revoked
        - Not expired (if expiration date exists)

        Returns:
            True if license is valid for use
        """
        if not self.is_active:
            return False

        if self.is_suspended or self.is_revoked:
            return False

        if self.expires_at:
            if datetime.now(timezone.utc) > self.expires_at:
                return False

        return True

    def days_until_expiration(self) -> Optional[int]:
        """Calculate days until license expires."""
        if not self.expires_at:
            return None  # Perpetual license

        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, delta.days)

    def to_dict(self) -> Dict[str, Any]:
        """Convert license to dictionary for API responses."""
        return {
            "license_id": self.license_id,
            "license_key": self.license_key[:20] + "..." if self.license_key else None,  # Redacted
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "organization": self.organization,
            "tier": self.tier,
            "license_type": self.license_type,
            "is_active": self.is_active,
            "is_valid": self.is_valid(),
            "issued_at": self.issued_at.isoformat() if self.issued_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "days_until_expiration": self.days_until_expiration(),
            "max_users": self.max_users,
            "max_ai_agents": self.max_ai_agents,
            "current_activations": self.current_activations,
            "max_concurrent_activations": self.max_concurrent_activations,
        }


# ============================================================================
# LICENSE ACTIVATION MODEL
# ============================================================================

class LicenseActivation(Base):
    """
    Tracks individual license activations (devices/servers).

    For concurrent licenses, multiple activations can exist simultaneously
    up to max_concurrent_activations limit.
    """

    __tablename__ = "license_activations"

    # Primary Key
    activation_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Key to License
    license_id = Column(String(36), ForeignKey("licenses.license_id"), nullable=False, index=True)

    # Activation Details
    hardware_id = Column(String(255), nullable=False)  # MAC address, CPU ID, fingerprint
    machine_name = Column(String(255))
    os_info = Column(String(255))
    ip_address = Column(String(45))  # IPv6 support

    # Status
    is_active = Column(Boolean, default=True)
    activated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    deactivated_at = Column(DateTime(timezone=True))
    last_heartbeat_at = Column(DateTime(timezone=True))  # Last check-in

    # Metadata
    metadata = Column(JSON)
    user_agent = Column(String(500))

    # Relationships
    license = relationship("License", back_populates="activations")

    # Indexes
    __table_args__ = (
        Index("idx_license_active", "license_id", "is_active"),
        Index("idx_hardware_id", "hardware_id"),
    )

    def is_stale(self, max_age_hours: int = 24) -> bool:
        """
        Check if activation is stale (no recent heartbeat).

        Args:
            max_age_hours: Maximum hours since last heartbeat

        Returns:
            True if activation appears inactive
        """
        if not self.last_heartbeat_at:
            return False  # Never checked in

        age = datetime.now(timezone.utc) - self.last_heartbeat_at
        return age > timedelta(hours=max_age_hours)


# ============================================================================
# LICENSE USAGE TRACKING MODEL
# ============================================================================

class LicenseUsageRecord(Base):
    """
    Tracks license usage for analytics, billing, and compliance.

    Records API calls, agent usage, storage consumption, and other metrics.
    """

    __tablename__ = "license_usage_records"

    # Primary Key
    record_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign Key
    license_id = Column(String(36), ForeignKey("licenses.license_id"), nullable=False, index=True)

    # Time Period
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)

    # Usage Metrics
    api_requests_count = Column(Integer, default=0)
    ai_agents_used = Column(Integer, default=0)
    concurrent_agents_peak = Column(Integer, default=0)
    storage_used_gb = Column(Float, default=0.0)
    bandwidth_used_gb = Column(Float, default=0.0)

    # User Metrics
    active_users = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)

    # Metadata
    metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    license = relationship("License", back_populates="usage_records")

    # Indexes
    __table_args__ = (
        Index("idx_license_period", "license_id", "period_start", "period_end"),
    )


# ============================================================================
# AUDIT LOG MODEL
# ============================================================================

class LicenseAuditLog(Base):
    """
    Audit trail for all license-related operations.

    Tracks creation, modification, activation, deactivation, and validation events.
    Critical for compliance and security auditing.
    """

    __tablename__ = "license_audit_logs"

    # Primary Key
    log_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Related License
    license_id = Column(String(36), ForeignKey("licenses.license_id"), index=True)

    # Event Details
    event_type = Column(String(50), nullable=False)  # created, activated, validated, suspended, etc.
    event_timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Actor
    actor_id = Column(String(255))  # User/system that performed action
    actor_ip = Column(String(45))
    actor_user_agent = Column(String(500))

    # Event Data
    event_data = Column(JSON)  # Additional context
    message = Column(Text)

    # Indexes
    __table_args__ = (
        Index("idx_license_event_time", "license_id", "event_timestamp"),
        Index("idx_event_type_time", "event_type", "event_timestamp"),
    )
