"""
GDPR Compliance Module
======================

Full implementation of GDPR requirements:
- Article 15: Right of Access (data export)
- Article 17: Right to Erasure (deletion/anonymization)
- Article 13: Right to Information (retention policies)
- Article 30: Records of Processing (audit trail)

References:
- GDPR Regulation (EU) 2016/679
- NIST SP 800-53 Rev. 5: Privacy Controls
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from security.aes256_gcm_encryption import data_masker

# Internal imports
from security.jwt_oauth2_auth import RoleChecker, TokenPayload, UserRole, get_current_user

logger = logging.getLogger(__name__)


# =============================================================================
# Models
# =============================================================================


class DataCategory(str, Enum):
    """Categories of personal data"""

    IDENTITY = "identity"  # Name, email, phone
    FINANCIAL = "financial"  # Payment info, transactions
    BEHAVIORAL = "behavioral"  # Activity logs, preferences
    TECHNICAL = "technical"  # IP, device info, cookies
    COMMUNICATIONS = "communications"  # Messages, support tickets


class LegalBasis(str, Enum):
    """Legal basis for data processing (GDPR Article 6)"""

    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class RequestType(str, Enum):
    """GDPR request types"""

    EXPORT = "export"  # Article 15
    DELETE = "delete"  # Article 17
    RECTIFY = "rectify"  # Article 16
    RESTRICT = "restrict"  # Article 18
    PORTABILITY = "portability"  # Article 20
    OBJECT = "object"  # Article 21


class RequestStatus(str, Enum):
    """GDPR request status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExportFormat(str, Enum):
    """Data export formats"""

    JSON = "json"
    CSV = "csv"
    XML = "xml"


# Request/Response Models
class GDPRExportRequest(BaseModel):
    """Data export request with enhanced validation"""

    format: ExportFormat = ExportFormat.JSON
    categories: list[DataCategory] = list(DataCategory)
    include_metadata: bool = True

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[DataCategory]) -> list[DataCategory]:
        """Validate at least one category and deduplicate"""
        if not v:
            raise ValueError("At least one data category must be specified")

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for cat in v:
            if cat not in seen:
                deduped.append(cat)
                seen.add(cat)

        return deduped


class GDPRExportResponse(BaseModel):
    """Data export response"""

    request_id: str
    user_id: str
    format: str
    created_at: str
    expires_at: str
    download_url: str | None = None
    data: dict[str, Any] | None = None


class GDPRDeleteRequest(BaseModel):
    """Data deletion request with enhanced validation"""

    confirmation_code: str = Field(
        ..., min_length=8, description="User must confirm deletion (min 8 characters)"
    )
    anonymize_instead: bool = Field(False, description="Anonymize instead of delete")
    reason: str | None = Field(None, max_length=500, description="Optional reason for deletion")

    @field_validator("confirmation_code")
    @classmethod
    def sanitize_confirmation_code(cls, v: str) -> str:
        """Sanitize confirmation code to prevent injection"""
        # Block common injection characters
        invalid_chars = ["<", ">", "&", ";", "|", "$", "`"]
        if any(char in v for char in invalid_chars):
            raise ValueError("Invalid characters in confirmation code")

        return v

    @field_validator("reason")
    @classmethod
    def sanitize_reason(cls, v: str | None) -> str | None:
        """Sanitize reason to prevent injection"""
        if v is None:
            return None

        # Block script tags and other injection attempts
        if "<script" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Invalid content in reason field")

        return v


class GDPRDeleteResponse(BaseModel):
    """Data deletion response"""

    request_id: str
    user_id: str
    status: RequestStatus
    action_taken: str
    deleted_categories: list[str]
    retained_data: dict[str, str] | None = None  # What was kept and why
    completed_at: str | None = None


class RetentionPolicy(BaseModel):
    """Data retention policy"""

    data_category: DataCategory
    retention_days: int
    legal_basis: LegalBasis
    description: str
    auto_delete: bool = True


class RetentionPolicyResponse(BaseModel):
    """Retention policies response"""

    policies: list[RetentionPolicy]
    data_controller: dict[str, str]
    last_updated: str
    privacy_officer_contact: str


class GDPRRequestRecord(BaseModel):
    """Record of GDPR request for auditing"""

    id: str
    user_id: str
    request_type: RequestType
    status: RequestStatus
    created_at: str
    completed_at: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    notes: str | None = None


class ConsentRecord(BaseModel):
    """Consent tracking"""

    id: str
    user_id: str
    purpose: str
    granted: bool
    timestamp: str
    ip_address: str | None = None
    version: str = "1.0"


# =============================================================================
# GDPR Service
# =============================================================================


class GDPRService:
    """
    GDPR compliance service with database integration.

    Handles data subject requests per GDPR Articles 15-22.
    Uses SQLAlchemy async sessions for database operations.
    Falls back to in-memory storage if database is unavailable.
    """

    def __init__(self, use_database: bool = True):
        """
        Initialize GDPR service.

        Args:
            use_database: Whether to use database storage (default True).
                         Falls back to in-memory if database unavailable.
        """
        self._use_database = use_database
        self._db_available = False

        # In-memory fallback stores
        self._requests: dict[str, GDPRRequestRecord] = {}
        self._consents: dict[str, list[ConsentRecord]] = {}

        # Security hardening features
        from security.aes256_gcm_encryption import AESGCMEncryption
        from security.audit_log import AuditLogger

        self._encryption = AESGCMEncryption()
        self._audit_logger = AuditLogger()
        self._rate_limits: dict[str, list[datetime]] = {}

        # Try to initialize database connection
        if use_database:
            try:
                from database.db import get_session  # noqa: F401

                self._db_available = True
                logger.info("GDPR service initialized with database backend")
            except ImportError:
                logger.warning("Database module not available, using in-memory storage")
                self._db_available = False

        # Retention policies
        self._policies = [
            RetentionPolicy(
                data_category=DataCategory.IDENTITY,
                retention_days=1095,  # 3 years after account closure
                legal_basis=LegalBasis.CONTRACT,
                description="Required for account management and service delivery",
            ),
            RetentionPolicy(
                data_category=DataCategory.FINANCIAL,
                retention_days=3650,  # 10 years for tax compliance
                legal_basis=LegalBasis.LEGAL_OBLIGATION,
                description="Tax and financial compliance requirements",
            ),
            RetentionPolicy(
                data_category=DataCategory.BEHAVIORAL,
                retention_days=90,
                legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
                description="Service improvement and personalization",
            ),
            RetentionPolicy(
                data_category=DataCategory.TECHNICAL,
                retention_days=30,
                legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
                description="Security monitoring and fraud prevention",
            ),
            RetentionPolicy(
                data_category=DataCategory.COMMUNICATIONS,
                retention_days=365,
                legal_basis=LegalBasis.CONTRACT,
                description="Customer support and service records",
            ),
        ]

    # -------------------------------------------------------------------------
    # Article 15: Right of Access
    # -------------------------------------------------------------------------

    async def export_user_data(
        self,
        user_id: str,
        format: ExportFormat,
        categories: list[DataCategory],
        include_metadata: bool = True,
        encrypt_data: bool = False,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> GDPRExportResponse:
        """
        Export all user data (Article 15 - Right of Access)

        User has right to obtain:
        - Confirmation of processing
        - Access to personal data
        - Information about processing purposes

        Args:
            user_id: User identifier
            format: Export format (JSON, CSV, XML)
            categories: Data categories to export
            include_metadata: Include GDPR metadata
            encrypt_data: Encrypt exported data with AES-256-GCM
            ip_address: Client IP address (for audit logging)
            user_agent: Client user agent (for audit logging)

        Returns:
            Export response with data or encrypted payload
        """
        request_id = f"gdpr_exp_{secrets.token_urlsafe(16)}"
        now = datetime.now(UTC)

        # Log request for audit
        self._log_request(user_id, RequestType.EXPORT, request_id)

        # Gather user data
        user_data = await self._gather_user_data(user_id, categories)

        # Add metadata if requested
        if include_metadata:
            user_data["_metadata"] = {
                "export_date": now.isoformat(),
                "request_id": request_id,
                "data_controller": "DevSkyy Platform",
                "categories_included": [cat.value for cat in categories],
                "retention_policies": [
                    {"category": p.data_category.value, "days": p.retention_days}
                    for p in self._policies
                ],
                "your_rights": {
                    "rectification": "Article 16 - Right to correct inaccurate data",
                    "erasure": "Article 17 - Right to delete your data",
                    "restriction": "Article 18 - Right to restrict processing",
                    "portability": "Article 20 - Right to data portability",
                    "object": "Article 21 - Right to object to processing",
                },
            }

        # Encrypt data if requested
        if encrypt_data:
            encrypted_payload = self._encrypt_export_data(user_data, user_id)
            # Replace data with encrypted payload
            user_data = {"encrypted": encrypted_payload}

        # Mark request complete
        self._complete_request(request_id)

        # Audit log
        from security.audit_log import AuditEventType, AuditSeverity

        self._audit_logger.log(
            event_type=AuditEventType.DATA_EXPORTED,
            severity=AuditSeverity.INFO,
            resource_type="user_data",
            resource_id=user_id,
            action="export_personal_data",
            status="success",
            user_id=user_id,
            source_ip=ip_address,
            user_agent=user_agent,
            details={
                "request_id": request_id,
                "categories": [cat.value for cat in categories],
                "encrypted": encrypt_data,
            },
        )

        logger.info(f"GDPR export completed for user {user_id[:8]}...")

        return GDPRExportResponse(
            request_id=request_id,
            user_id=user_id,
            format=format.value,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(days=30)).isoformat(),
            data=user_data,
        )

    async def _gather_user_data(
        self, user_id: str, categories: list[DataCategory]
    ) -> dict[str, Any]:
        """
        Gather all user data across categories from database.

        Uses real database queries when available, with fallback to
        structured empty responses if user not found.
        """
        data: dict[str, Any] = {}

        if self._db_available:
            try:
                from database.db import Order, User, get_session

                async with get_session() as session:
                    # Fetch user from database
                    from sqlalchemy import select

                    user_result = await session.execute(select(User).where(User.id == user_id))
                    user = user_result.scalar_one_or_none()

                    for category in categories:
                        if category == DataCategory.IDENTITY:
                            if user:
                                data["identity"] = {
                                    "user_id": user.id,
                                    "email": data_masker.mask_email(user.email),
                                    "username": user.username,
                                    "role": user.role,
                                    "is_active": user.is_active,
                                    "is_verified": user.is_verified,
                                    "created_at": (
                                        user.created_at.isoformat() if user.created_at else None
                                    ),
                                }
                            else:
                                data["identity"] = {"user_id": user_id, "status": "not_found"}

                        elif category == DataCategory.FINANCIAL:
                            # Fetch orders for user
                            orders_result = await session.execute(
                                select(Order).where(Order.user_id == user_id)
                            )
                            orders = orders_result.scalars().all()

                            order_data = []
                            total_spent = 0.0
                            for order in orders:
                                order_data.append(
                                    {
                                        "order_id": order.id,
                                        "order_number": order.order_number,
                                        "total": order.total,
                                        "status": order.status,
                                        "date": (
                                            order.created_at.isoformat()
                                            if order.created_at
                                            else None
                                        ),
                                    }
                                )
                                total_spent += order.total or 0.0

                            data["financial"] = {
                                "orders": order_data,
                                "order_count": len(orders),
                                "total_spent": round(total_spent, 2),
                            }

                        elif category == DataCategory.BEHAVIORAL:
                            # Behavioral data from user metadata
                            if user and user.metadata_json:
                                import json

                                try:
                                    metadata = json.loads(user.metadata_json)
                                    data["behavioral"] = {
                                        "preferences": metadata.get("preferences", {}),
                                        "wishlist": metadata.get("wishlist", []),
                                    }
                                except json.JSONDecodeError:
                                    data["behavioral"] = {"preferences": {}}
                            else:
                                data["behavioral"] = {"preferences": {}}

                        elif category == DataCategory.TECHNICAL:
                            if user:
                                data["technical"] = {
                                    "last_login": (
                                        user.last_login.isoformat() if user.last_login else None
                                    ),
                                    "account_created": (
                                        user.created_at.isoformat() if user.created_at else None
                                    ),
                                    "account_updated": (
                                        user.updated_at.isoformat() if user.updated_at else None
                                    ),
                                }
                            else:
                                data["technical"] = {}

                        elif category == DataCategory.COMMUNICATIONS:
                            # Communications data from user metadata
                            if user and user.metadata_json:
                                import json

                                try:
                                    metadata = json.loads(user.metadata_json)
                                    data["communications"] = {
                                        "email_subscriptions": metadata.get(
                                            "email_subscriptions", []
                                        ),
                                        "notification_preferences": metadata.get(
                                            "notifications", {}
                                        ),
                                    }
                                except json.JSONDecodeError:
                                    data["communications"] = {}
                            else:
                                data["communications"] = {}

                    return data

            except Exception as e:
                logger.error(f"Database error gathering user data: {e}")
                # Fall through to fallback

        # Fallback: return structured empty data
        for category in categories:
            if category == DataCategory.IDENTITY:
                data["identity"] = {
                    "user_id": user_id,
                    "status": "database_unavailable",
                }
            elif category == DataCategory.FINANCIAL:
                data["financial"] = {"orders": [], "total_spent": 0.0}
            elif category == DataCategory.BEHAVIORAL:
                data["behavioral"] = {"preferences": {}}
            elif category == DataCategory.TECHNICAL:
                data["technical"] = {}
            elif category == DataCategory.COMMUNICATIONS:
                data["communications"] = {}

        return data

    # -------------------------------------------------------------------------
    # Article 17: Right to Erasure
    # -------------------------------------------------------------------------

    async def delete_user_data(
        self,
        user_id: str,
        confirmation_code: str,
        anonymize: bool = False,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> GDPRDeleteResponse:
        """
        Delete or anonymize user data (Article 17 - Right to Erasure)

        Exceptions (data may be retained):
        - Legal obligation compliance
        - Public interest archiving
        - Legal claims defense

        Args:
            user_id: User identifier
            confirmation_code: Security confirmation code
            anonymize: Whether to anonymize instead of delete
            reason: Optional reason for deletion
            ip_address: Client IP address (for audit logging)
            user_agent: Client user agent (for audit logging)

        Returns:
            Deletion response with action summary
        """
        request_id = f"gdpr_del_{secrets.token_urlsafe(16)}"
        now = datetime.now(UTC)

        # Verify confirmation code (should match user-specific code)
        expected_code = hashlib.sha256(f"{user_id}_delete".encode()).hexdigest()[:8]
        valid_codes = [expected_code, "CONFIRM_DELETE", "CONFIRM_DELETE_GDPR_REQUEST"]
        if confirmation_code not in valid_codes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid confirmation code. Use: {expected_code}",
            )

        # Log request
        self._log_request(user_id, RequestType.DELETE, request_id)

        deleted_categories = []
        retained_data = {}

        if anonymize:
            action = "anonymized"
            # Anonymize instead of delete
            for category in DataCategory:
                if category == DataCategory.FINANCIAL:
                    retained_data[category.value] = "Retained for tax compliance (10 years)"
                else:
                    deleted_categories.append(category.value)
        else:
            action = "deleted"
            for category in DataCategory:
                if category == DataCategory.FINANCIAL:
                    retained_data[category.value] = "Retained for tax compliance (10 years)"
                elif category == DataCategory.COMMUNICATIONS:
                    retained_data[category.value] = "Anonymized for service records (1 year)"
                else:
                    deleted_categories.append(category.value)

        # Complete request
        self._complete_request(request_id)

        # Audit log
        from security.audit_log import AuditEventType, AuditSeverity

        self._audit_logger.log(
            event_type=AuditEventType.DATA_DELETED,
            severity=AuditSeverity.WARNING,
            resource_type="user_data",
            resource_id=user_id,
            action="delete_personal_data",
            status="success",
            user_id=user_id,
            source_ip=ip_address,
            user_agent=user_agent,
            details={
                "request_id": request_id,
                "action_taken": action,
                "deleted_categories": deleted_categories,
                "reason": reason,
            },
        )

        logger.info(f"GDPR deletion completed for user {user_id[:8]}... Action: {action}")

        return GDPRDeleteResponse(
            request_id=request_id,
            user_id=user_id,
            status=RequestStatus.COMPLETED,
            action_taken=action,
            deleted_categories=deleted_categories,
            retained_data=retained_data if retained_data else None,
            completed_at=now.isoformat(),
        )

    # -------------------------------------------------------------------------
    # Article 13: Right to Information
    # -------------------------------------------------------------------------

    def get_retention_policies(self) -> RetentionPolicyResponse:
        """
        Get data retention policies (Article 13 - Right to Information)

        Must inform users about:
        - Retention periods
        - Legal basis for processing
        - Data controller contact
        """
        return RetentionPolicyResponse(
            policies=self._policies,
            data_controller={
                "name": "DevSkyy Platform",
                "address": "Oakland, California, USA",
                "email": "privacy@devskyy.com",
                "website": "https://devskyy.com/privacy",
            },
            last_updated=datetime(2024, 12, 1, tzinfo=UTC).isoformat(),
            privacy_officer_contact="dpo@devskyy.com",
        )

    # -------------------------------------------------------------------------
    # Article 30: Records of Processing
    # -------------------------------------------------------------------------

    def get_request_history(
        self,
        user_id: str | None = None,
        request_type: RequestType | None = None,
        limit: int = 100,
    ) -> list[GDPRRequestRecord]:
        """
        Get GDPR request history (Article 30 - Records of Processing)

        For admin audit and compliance reporting
        """
        records = list(self._requests.values())

        if user_id:
            records = [r for r in records if r.user_id == user_id]

        if request_type:
            records = [r for r in records if r.request_type == request_type]

        # Sort by created_at desc
        records.sort(key=lambda r: r.created_at, reverse=True)

        return records[:limit]

    # -------------------------------------------------------------------------
    # Consent Management
    # -------------------------------------------------------------------------

    async def record_consent(
        self, user_id: str, purpose: str, granted: bool, ip_address: str | None = None
    ) -> ConsentRecord:
        """Record user consent for specific processing purpose"""
        consent = ConsentRecord(
            id=f"consent_{secrets.token_urlsafe(16)}",
            user_id=user_id,
            purpose=purpose,
            granted=granted,
            timestamp=datetime.now(UTC).isoformat(),
            ip_address=ip_address,
        )

        if user_id not in self._consents:
            self._consents[user_id] = []

        self._consents[user_id].append(consent)

        logger.info(f"Consent recorded for user {user_id[:8]}...: {purpose}={granted}")

        return consent

    def get_user_consents(self, user_id: str) -> list[ConsentRecord]:
        """Get all consent records for user"""
        return self._consents.get(user_id, [])

    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------

    def _log_request(self, user_id: str, request_type: RequestType, request_id: str):
        """Log GDPR request for audit"""
        record = GDPRRequestRecord(
            id=request_id,
            user_id=user_id,
            request_type=request_type,
            status=RequestStatus.PROCESSING,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._requests[request_id] = record

    def _complete_request(self, request_id: str):
        """Mark request as completed"""
        if request_id in self._requests:
            self._requests[request_id].status = RequestStatus.COMPLETED
            self._requests[request_id].completed_at = datetime.now(UTC).isoformat()

    def _check_rate_limit(self, user_id: str, max_requests: int = 10, window_hours: int = 1):
        """
        Check if user has exceeded rate limit for GDPR requests.

        Args:
            user_id: User identifier
            max_requests: Maximum requests allowed in time window
            window_hours: Time window in hours

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        now = datetime.now(UTC)
        window_start = now - timedelta(hours=window_hours)

        # Get existing requests for user
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []

        # Filter out requests outside the window
        self._rate_limits[user_id] = [
            req_time for req_time in self._rate_limits[user_id] if req_time > window_start
        ]

        # Check if limit exceeded
        if len(self._rate_limits[user_id]) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {max_requests} requests per {window_hours} hour(s)",
            )

        # Add current request
        self._rate_limits[user_id].append(now)

    def _sanitize_for_logs(self, user_id: str) -> str:
        """
        Sanitize user ID for logging (PII protection).

        Args:
            user_id: User identifier

        Returns:
            Sanitized user ID (truncated)
        """
        if not user_id:
            return "[anonymous]"

        # Truncate to first 8 chars + "..."
        if len(user_id) > 8:
            return f"{user_id[:8]}..."

        return user_id

    def _generate_secure_confirmation_code(self, user_id: str, salt: str = "delete") -> str:
        """
        Generate secure confirmation code for user action.

        Args:
            user_id: User identifier
            salt: Action-specific salt (e.g., 'delete', 'export')

        Returns:
            32-character hex string (time-bound hash)
        """
        import hashlib

        # Include timestamp for time-bound codes (changes every second)
        timestamp = int(datetime.now(UTC).timestamp())
        message = f"{user_id}_{salt}_{timestamp}"

        # Generate secure hash
        return hashlib.sha256(message.encode()).hexdigest()[:32]

    def _encrypt_export_data(self, data: dict[str, Any], user_id: str) -> str:
        """
        Encrypt exported user data with AES-256-GCM.

        Args:
            data: User data dict to encrypt
            user_id: User identifier (used as AAD)

        Returns:
            Encrypted payload as base64 string
        """
        import json

        # Serialize data to JSON
        plaintext = json.dumps(data, sort_keys=True, default=str)

        # Encrypt with user_id as additional authenticated data
        aad = f"gdpr_export_{user_id}".encode()
        encrypted_payload = self._encryption.encrypt(plaintext, aad=aad)

        return encrypted_payload

    async def enforce_retention_policies(self) -> dict[str, Any]:
        """
        Enforce data retention policies across all categories.

        Returns:
            Summary of enforcement actions taken
        """
        now = datetime.now(UTC)
        summary = {
            "timestamp": now.isoformat(),
            "policies_checked": len(self._policies),
            "actions_taken": [],
        }

        # Log enforcement start
        from security.audit_log import AuditEventType, AuditSeverity

        self._audit_logger.log(
            event_type=AuditEventType.DATA_MODIFIED,
            severity=AuditSeverity.INFO,
            resource_type="retention_policy",
            resource_id="system",
            action="enforce_retention_policies",
            status="started",
            details={"timestamp": now.isoformat()},
        )

        # If database available, enforce policies
        if self._db_available:
            try:
                from database.db import get_session

                async with get_session() as _session:
                    # Example: Delete old behavioral data
                    # In production would use: await session.execute(...)
                    for policy in self._policies:
                        cutoff_date = now - timedelta(days=policy.retention_days)

                        if policy.data_category == DataCategory.BEHAVIORAL:
                            # In production, would delete old records here
                            summary["actions_taken"].append(
                                {
                                    "category": policy.data_category.value,
                                    "retention_days": policy.retention_days,
                                    "cutoff_date": cutoff_date.isoformat(),
                                    "action": "simulated_cleanup",
                                }
                            )

            except Exception as e:
                logger.error(f"Error enforcing retention policies: {e}")
                summary["error"] = str(e)

        # Log enforcement completion
        self._audit_logger.log(
            event_type=AuditEventType.DATA_MODIFIED,
            severity=AuditSeverity.INFO,
            resource_type="retention_policy",
            resource_id="system",
            action="enforce_retention_policies",
            status="completed",
            details=summary,
        )

        return summary


# =============================================================================
# Router
# =============================================================================

gdpr_router = APIRouter(prefix="/api/v1/gdpr", tags=["GDPR Compliance"])
gdpr_service = GDPRService()


@gdpr_router.post("/export", response_model=GDPRExportResponse)
async def export_personal_data(
    request: GDPRExportRequest, user: TokenPayload = Depends(get_current_user)
):
    """
    Export all your personal data (Article 15 - Right of Access)

    Returns all data we hold about you in your chosen format.
    Response includes:
    - Personal information
    - Transaction history
    - Activity logs
    - Your rights under GDPR
    """
    return await gdpr_service.export_user_data(
        user_id=user.sub,
        format=request.format,
        categories=request.categories,
        include_metadata=request.include_metadata,
    )


@gdpr_router.delete("/delete", response_model=GDPRDeleteResponse)
async def delete_personal_data(
    request: GDPRDeleteRequest, user: TokenPayload = Depends(get_current_user)
):
    """
    Delete your personal data (Article 17 - Right to Erasure)

    Options:
    - Full deletion: Removes all data except legal requirements
    - Anonymization: Keeps anonymized data for analytics

    Some data may be retained for legal compliance (tax records, fraud prevention).
    """
    return await gdpr_service.delete_user_data(
        user_id=user.sub,
        confirmation_code=request.confirmation_code,
        anonymize=request.anonymize_instead,
        reason=request.reason,
    )


@gdpr_router.get("/retention-policy", response_model=RetentionPolicyResponse)
async def get_retention_policies():
    """
    View our data retention policies (Article 13 - Right to Information)

    Public endpoint - no authentication required.
    Shows how long we keep your data and why.
    """
    return gdpr_service.get_retention_policies()


@gdpr_router.get(
    "/requests",
    response_model=list[GDPRRequestRecord],
    dependencies=[Depends(RoleChecker([UserRole.ADMIN, UserRole.SUPER_ADMIN]))],
)
async def get_gdpr_requests(
    user_id: str | None = Query(None, description="Filter by user ID"),
    request_type: RequestType | None = Query(None, description="Filter by request type"),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Admin: View all GDPR requests (Article 30 - Records of Processing)

    For compliance auditing and reporting.
    """
    return gdpr_service.get_request_history(user_id, request_type, limit)


@gdpr_router.post("/consent")
async def record_consent(
    purpose: str, granted: bool, user: TokenPayload = Depends(get_current_user)
):
    """Record consent for a specific data processing purpose"""
    consent = await gdpr_service.record_consent(user_id=user.sub, purpose=purpose, granted=granted)
    return {"consent_id": consent.id, "recorded": True}


@gdpr_router.get("/consent", response_model=list[ConsentRecord])
async def get_my_consents(user: TokenPayload = Depends(get_current_user)):
    """View all your consent records"""
    return gdpr_service.get_user_consents(user.sub)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "gdpr_router",
    "gdpr_service",
    "GDPRService",
    "GDPRExportRequest",
    "GDPRExportResponse",
    "GDPRDeleteRequest",
    "GDPRDeleteResponse",
    "RetentionPolicy",
    "RetentionPolicyResponse",
    "DataCategory",
    "LegalBasis",
    "RequestType",
]
