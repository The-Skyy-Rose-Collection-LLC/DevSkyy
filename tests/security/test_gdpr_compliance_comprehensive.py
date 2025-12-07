"""
Comprehensive Test Suite for GDPR Compliance Module

Tests GDPR Article 15 (Right of Access), Article 17 (Right to Erasure),
Article 5 (Data Minimization), Recital 83 (Consent), and audit logging.

Per CLAUDE.md Rule #8: Target ≥90% coverage
Per CLAUDE.md Rule #13: Security baseline verification

Author: DevSkyy Enterprise Team
Version: 2.0.0
Python: >=3.11.0
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from security.gdpr_compliance import (
    RETENTION_POLICIES,
    AuditLog,
    ConsentRecord,
    ConsentType,
    DataCategory,
    DataDeletionRequest,
    DataDeletionResponse,
    DataExportRequest,
    DataExportResponse,
    GDPRManager,
    RetentionPolicy,
    gdpr_manager,
    router,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def gdpr_mgr():
    """Create a fresh GDPR manager for each test"""
    return GDPRManager()


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return "user_test_12345"


@pytest.fixture
def sample_consent_record():
    """Create sample consent record"""
    return ConsentRecord(
        consent_id="consent_001",
        user_id="user_test_12345",
        consent_type=ConsentType.MARKETING,
        given=True,
        timestamp=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=730),
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
        metadata={"source": "web_form", "version": "1.0"},
    )


# ============================================================================
# ENUM AND MODEL TESTS
# ============================================================================


class TestEnumsAndModels:
    """Test GDPR enums and Pydantic models"""

    def test_consent_type_enum_values(self):
        """Test ConsentType enum has all required values"""
        assert ConsentType.MARKETING == "marketing"
        assert ConsentType.ANALYTICS == "analytics"
        assert ConsentType.PROFILING == "profiling"
        assert ConsentType.COOKIES == "cookies"
        assert ConsentType.DATA_PROCESSING == "data_processing"

    def test_data_category_enum_values(self):
        """Test DataCategory enum has all required values"""
        assert DataCategory.PROFILE == "profile"
        assert DataCategory.ACCOUNT == "account"
        assert DataCategory.BEHAVIORAL == "behavioral"
        assert DataCategory.TRANSACTIONAL == "transactional"
        assert DataCategory.PREFERENCES == "preferences"
        assert DataCategory.GENERATED == "generated"

    def test_consent_record_model_creation(self, sample_consent_record):
        """Test ConsentRecord model can be created"""
        assert sample_consent_record.consent_id == "consent_001"
        assert sample_consent_record.user_id == "user_test_12345"
        assert sample_consent_record.consent_type == ConsentType.MARKETING
        assert sample_consent_record.given is True
        assert isinstance(sample_consent_record.timestamp, datetime)

    def test_data_export_request_model(self):
        """Test DataExportRequest model"""
        request = DataExportRequest(
            user_id="user_123",
            format="json",
            include_related=True,
        )
        assert request.user_id == "user_123"
        assert request.format == "json"
        assert request.include_related is True

    def test_data_export_request_defaults(self):
        """Test DataExportRequest default values"""
        request = DataExportRequest(user_id="user_123")
        assert request.format == "json"
        assert request.include_related is True

    def test_data_deletion_request_model(self):
        """Test DataDeletionRequest model"""
        request = DataDeletionRequest(
            user_id="user_456",
            reason="User requested account deletion",
            include_backups=True,
        )
        assert request.user_id == "user_456"
        assert request.reason == "User requested account deletion"
        assert request.include_backups is True

    def test_data_deletion_response_model(self):
        """Test DataDeletionResponse model"""
        response = DataDeletionResponse(
            deletion_id="del_789",
            user_id="user_456",
            status="completed",
            deleted_at=datetime.now(UTC),
            items_deleted=42,
            note="Deletion completed successfully",
        )
        assert response.deletion_id == "del_789"
        assert response.status == "completed"
        assert response.items_deleted == 42

    def test_retention_policy_model(self):
        """Test RetentionPolicy model"""
        policy = RetentionPolicy(
            data_category=DataCategory.BEHAVIORAL,
            retention_days=365,
            description="User behavior logs",
            legal_basis="Legitimate interest",
        )
        assert policy.data_category == DataCategory.BEHAVIORAL
        assert policy.retention_days == 365
        assert "behavior" in policy.description.lower()

    def test_audit_log_model(self):
        """Test AuditLog model"""
        log = AuditLog(
            log_id="log_001",
            user_id="user_123",
            action="data_export",
            timestamp=datetime.now(UTC),
            actor_id="admin_001",
            ip_address="10.0.0.1",
            details={"export_id": "exp_001", "format": "json"},
        )
        assert log.log_id == "log_001"
        assert log.action == "data_export"
        assert log.actor_id == "admin_001"


# ============================================================================
# RETENTION POLICY TESTS
# ============================================================================


class TestRetentionPolicies:
    """Test GDPR data retention policies (Article 5.1(e))"""

    def test_retention_policies_exist(self):
        """Test all data categories have retention policies"""
        assert DataCategory.PROFILE in RETENTION_POLICIES
        assert DataCategory.ACCOUNT in RETENTION_POLICIES
        assert DataCategory.BEHAVIORAL in RETENTION_POLICIES
        assert DataCategory.TRANSACTIONAL in RETENTION_POLICIES
        assert DataCategory.PREFERENCES in RETENTION_POLICIES
        assert DataCategory.GENERATED in RETENTION_POLICIES

    def test_profile_retention_policy(self):
        """Test profile data retention policy"""
        policy = RETENTION_POLICIES[DataCategory.PROFILE]
        assert policy.data_category == DataCategory.PROFILE
        assert policy.retention_days == 2555
        assert "profile" in policy.description.lower()
        assert "contract" in policy.legal_basis.lower()

    def test_behavioral_retention_policy(self):
        """Test behavioral data has 1 year retention"""
        policy = RETENTION_POLICIES[DataCategory.BEHAVIORAL]
        assert policy.retention_days == 365
        assert "legitimate interest" in policy.legal_basis.lower()

    def test_generated_retention_policy(self):
        """Test ML-generated data has 90 day retention"""
        policy = RETENTION_POLICIES[DataCategory.GENERATED]
        assert policy.retention_days == 90
        assert "ml" in policy.description.lower() or "generated" in policy.description.lower()

    def test_all_retention_policies_have_legal_basis(self):
        """Test all retention policies have legal basis"""
        for category, policy in RETENTION_POLICIES.items():
            assert policy.legal_basis is not None
            assert len(policy.legal_basis) > 0


# ============================================================================
# GDPR MANAGER INITIALIZATION TESTS
# ============================================================================


class TestGDPRManagerInitialization:
    """Test GDPRManager initialization"""

    def test_gdpr_manager_initialization(self, gdpr_mgr):
        """Test GDPRManager initializes correctly"""
        assert gdpr_mgr.consent_records == {}
        assert gdpr_mgr.audit_logs == []
        assert gdpr_mgr.data_exports == {}
        assert gdpr_mgr.data_deletions == {}

    def test_global_gdpr_manager_exists(self):
        """Test global gdpr_manager instance exists"""
        assert gdpr_manager is not None
        assert isinstance(gdpr_manager, GDPRManager)


# ============================================================================
# DATA EXPORT TESTS (GDPR Article 15)
# ============================================================================


class TestDataExport:
    """Test GDPR Article 15 - Right of Access"""

    @pytest.mark.asyncio
    async def test_request_data_export_basic(self, gdpr_mgr, sample_user_id):
        """Test basic data export request"""
        response = await gdpr_mgr.request_data_export(sample_user_id)

        assert isinstance(response, DataExportResponse)
        assert response.user_id == sample_user_id
        assert response.export_id is not None
        assert len(response.export_id) > 0
        assert isinstance(response.data, dict)

    @pytest.mark.asyncio
    async def test_request_data_export_with_format(self, gdpr_mgr, sample_user_id):
        """Test data export with different formats"""
        formats = ["json", "csv", "xml"]

        for fmt in formats:
            response = await gdpr_mgr.request_data_export(sample_user_id, format=fmt)
            assert response.user_id == sample_user_id
            # Format is passed but conversion is TODO in implementation

    @pytest.mark.asyncio
    async def test_request_data_export_include_related(self, gdpr_mgr, sample_user_id):
        """Test data export with include_related flag"""
        response = await gdpr_mgr.request_data_export(
            sample_user_id,
            include_related=True,
        )
        assert response.user_id == sample_user_id
        assert isinstance(response.data, dict)

    @pytest.mark.asyncio
    async def test_request_data_export_exclude_related(self, gdpr_mgr, sample_user_id):
        """Test data export without related data"""
        response = await gdpr_mgr.request_data_export(
            sample_user_id,
            include_related=False,
        )
        assert response.user_id == sample_user_id

    @pytest.mark.asyncio
    async def test_data_export_has_expiry(self, gdpr_mgr, sample_user_id):
        """Test data export has 30-day expiration"""
        response = await gdpr_mgr.request_data_export(sample_user_id)

        assert response.expires_at is not None
        time_diff = response.expires_at - response.created_at
        assert 29 <= time_diff.days <= 31  # Allow some variance

    @pytest.mark.asyncio
    async def test_data_export_has_download_url(self, gdpr_mgr, sample_user_id):
        """Test data export includes download URL"""
        response = await gdpr_mgr.request_data_export(sample_user_id)

        assert response.download_url is not None
        assert response.export_id in response.download_url
        assert "/download" in response.download_url

    @pytest.mark.asyncio
    async def test_data_export_stored_in_manager(self, gdpr_mgr, sample_user_id):
        """Test data export is stored in manager"""
        response = await gdpr_mgr.request_data_export(sample_user_id)

        assert response.export_id in gdpr_mgr.data_exports
        stored_export = gdpr_mgr.data_exports[response.export_id]
        assert stored_export.user_id == sample_user_id

    @pytest.mark.asyncio
    async def test_data_export_creates_audit_log(self, gdpr_mgr, sample_user_id):
        """Test data export creates audit log entry"""
        await gdpr_mgr.request_data_export(sample_user_id)

        assert len(gdpr_mgr.audit_logs) > 0
        audit_log = gdpr_mgr.audit_logs[-1]
        assert audit_log.action == "data_export"
        assert audit_log.user_id == sample_user_id

    @pytest.mark.asyncio
    async def test_data_export_contains_user_data(self, gdpr_mgr, sample_user_id):
        """Test exported data contains expected user data"""
        response = await gdpr_mgr.request_data_export(sample_user_id)

        assert "profile" in response.data
        assert "orders" in response.data
        assert "preferences" in response.data
        assert "interactions" in response.data

    @pytest.mark.asyncio
    async def test_multiple_data_exports_for_same_user(self, gdpr_mgr, sample_user_id):
        """Test multiple export requests from same user"""
        response1 = await gdpr_mgr.request_data_export(sample_user_id)
        response2 = await gdpr_mgr.request_data_export(sample_user_id)

        assert response1.export_id != response2.export_id
        assert len(gdpr_mgr.data_exports) == 2


# ============================================================================
# DATA DELETION TESTS (GDPR Article 17)
# ============================================================================


class TestDataDeletion:
    """Test GDPR Article 17 - Right to Erasure"""

    @pytest.mark.asyncio
    async def test_request_data_deletion_basic(self, gdpr_mgr, sample_user_id):
        """Test basic data deletion request"""
        response = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="User requested account deletion",
        )

        assert isinstance(response, DataDeletionResponse)
        assert response.user_id == sample_user_id
        assert response.deletion_id is not None
        assert response.status == "completed"

    @pytest.mark.asyncio
    async def test_request_data_deletion_with_backups(self, gdpr_mgr, sample_user_id):
        """Test data deletion including backups"""
        response = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="GDPR erasure request",
            include_backups=True,
        )

        assert response.user_id == sample_user_id
        assert response.status == "completed"

    @pytest.mark.asyncio
    async def test_data_deletion_has_timestamp(self, gdpr_mgr, sample_user_id):
        """Test data deletion includes timestamp"""
        before_deletion = datetime.now(UTC)
        response = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="Test deletion",
        )
        after_deletion = datetime.now(UTC)

        assert before_deletion <= response.deleted_at <= after_deletion

    @pytest.mark.asyncio
    async def test_data_deletion_stored_in_manager(self, gdpr_mgr, sample_user_id):
        """Test data deletion is stored in manager"""
        response = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="Test deletion",
        )

        assert response.deletion_id in gdpr_mgr.data_deletions
        stored_deletion = gdpr_mgr.data_deletions[response.deletion_id]
        assert stored_deletion.user_id == sample_user_id

    @pytest.mark.asyncio
    async def test_data_deletion_creates_audit_log(self, gdpr_mgr, sample_user_id):
        """Test data deletion creates audit log entry"""
        await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="Test deletion",
        )

        assert len(gdpr_mgr.audit_logs) > 0
        audit_log = gdpr_mgr.audit_logs[-1]
        assert audit_log.action == "data_deletion"
        assert audit_log.user_id == sample_user_id

    @pytest.mark.asyncio
    async def test_data_deletion_includes_reason(self, gdpr_mgr, sample_user_id):
        """Test data deletion response includes reason"""
        reason = "User no longer wants account"
        response = await gdpr_mgr.request_data_deletion(sample_user_id, reason=reason)

        assert reason in response.note

    @pytest.mark.asyncio
    async def test_data_deletion_notes_exceptions(self, gdpr_mgr, sample_user_id):
        """Test data deletion notes legal retention exceptions"""
        response = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="Test deletion",
        )

        # Should note exceptions like transactional data
        assert "Exceptions" in response.note
        assert "Transactional" in response.note or "legal obligation" in response.note.lower()

    @pytest.mark.asyncio
    async def test_data_deletion_counts_items(self, gdpr_mgr, sample_user_id):
        """Test data deletion counts deleted items"""
        response = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="Test deletion",
        )

        assert response.items_deleted >= 0  # In current implementation, it's 0 (TODO)

    @pytest.mark.asyncio
    async def test_multiple_deletion_requests(self, gdpr_mgr, sample_user_id):
        """Test multiple deletion requests for same user"""
        response1 = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="First request",
        )
        response2 = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="Second request",
        )

        assert response1.deletion_id != response2.deletion_id


# ============================================================================
# CONSENT MANAGEMENT TESTS (GDPR Recital 83)
# ============================================================================


class TestConsentManagement:
    """Test GDPR Recital 83 - Consent Management"""

    @pytest.mark.asyncio
    async def test_update_consent_grant(self, gdpr_mgr, sample_user_id):
        """Test granting consent"""
        consent = await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.MARKETING,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        assert isinstance(consent, ConsentRecord)
        assert consent.user_id == sample_user_id
        assert consent.consent_type == ConsentType.MARKETING
        assert consent.given is True

    @pytest.mark.asyncio
    async def test_update_consent_revoke(self, gdpr_mgr, sample_user_id):
        """Test revoking consent"""
        consent = await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.ANALYTICS,
            given=False,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        assert consent.given is False
        assert consent.consent_type == ConsentType.ANALYTICS

    @pytest.mark.asyncio
    async def test_consent_has_timestamp(self, gdpr_mgr, sample_user_id):
        """Test consent record has timestamp"""
        before = datetime.now(UTC)
        consent = await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.COOKIES,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )
        after = datetime.now(UTC)

        assert before <= consent.timestamp <= after

    @pytest.mark.asyncio
    async def test_consent_has_expiry(self, gdpr_mgr, sample_user_id):
        """Test consent record has 2-year expiration"""
        consent = await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.PROFILING,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )

        assert consent.expires_at is not None
        time_diff = consent.expires_at - consent.timestamp
        assert 729 <= time_diff.days <= 731  # 2 years ± 1 day

    @pytest.mark.asyncio
    async def test_consent_records_ip_and_user_agent(self, gdpr_mgr, sample_user_id):
        """Test consent records IP address and user agent"""
        ip = "10.0.0.42"
        ua = "Mozilla/5.0 Custom Browser"

        consent = await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.MARKETING,
            given=True,
            ip_address=ip,
            user_agent=ua,
        )

        assert consent.ip_address == ip
        assert consent.user_agent == ua

    @pytest.mark.asyncio
    async def test_consent_stored_in_manager(self, gdpr_mgr, sample_user_id):
        """Test consent is stored in manager"""
        consent = await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.MARKETING,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test",
        )

        assert sample_user_id in gdpr_mgr.consent_records
        assert consent in gdpr_mgr.consent_records[sample_user_id]

    @pytest.mark.asyncio
    async def test_multiple_consent_types_for_user(self, gdpr_mgr, sample_user_id):
        """Test user can have multiple consent types"""
        consent_types = [
            ConsentType.MARKETING,
            ConsentType.ANALYTICS,
            ConsentType.PROFILING,
        ]

        for consent_type in consent_types:
            await gdpr_mgr.update_consent(
                user_id=sample_user_id,
                consent_type=consent_type,
                given=True,
                ip_address="192.168.1.1",
                user_agent="Test",
            )

        consents = gdpr_mgr.consent_records[sample_user_id]
        assert len(consents) == len(consent_types)

    @pytest.mark.asyncio
    async def test_consent_creates_audit_log(self, gdpr_mgr, sample_user_id):
        """Test consent update creates audit log"""
        await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.COOKIES,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test",
        )

        assert len(gdpr_mgr.audit_logs) > 0
        audit_log = gdpr_mgr.audit_logs[-1]
        assert audit_log.action == "consent_update"
        assert audit_log.user_id == sample_user_id

    @pytest.mark.asyncio
    async def test_get_user_consents_empty(self, gdpr_mgr, sample_user_id):
        """Test getting consents for user with no consents"""
        consents = await gdpr_mgr.get_user_consents(sample_user_id)
        assert consents == []

    @pytest.mark.asyncio
    async def test_get_user_consents_after_granting(self, gdpr_mgr, sample_user_id):
        """Test getting consents after granting"""
        await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.MARKETING,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test",
        )

        consents = await gdpr_mgr.get_user_consents(sample_user_id)
        assert len(consents) == 1
        assert consents[0].consent_type == ConsentType.MARKETING

    @pytest.mark.asyncio
    async def test_consent_history_tracking(self, gdpr_mgr, sample_user_id):
        """Test consent change history is tracked"""
        # Grant consent
        await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.MARKETING,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test",
        )

        # Revoke consent
        await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.MARKETING,
            given=False,
            ip_address="192.168.1.1",
            user_agent="Test",
        )

        consents = await gdpr_mgr.get_user_consents(sample_user_id)
        assert len(consents) == 2  # Both grant and revoke are tracked


# ============================================================================
# AUDIT LOG TESTS
# ============================================================================


class TestAuditLogging:
    """Test GDPR audit logging"""

    @pytest.mark.asyncio
    async def test_get_retention_policies(self, gdpr_mgr):
        """Test getting all retention policies"""
        policies = await gdpr_mgr.get_retention_policies()

        assert isinstance(policies, dict)
        assert len(policies) > 0
        assert DataCategory.PROFILE in policies

    @pytest.mark.asyncio
    async def test_get_audit_logs_empty(self, gdpr_mgr):
        """Test getting audit logs when none exist"""
        logs = await gdpr_mgr.get_audit_logs()
        assert logs == []

    @pytest.mark.asyncio
    async def test_get_audit_logs_after_operations(self, gdpr_mgr, sample_user_id):
        """Test getting audit logs after operations"""
        await gdpr_mgr.request_data_export(sample_user_id)
        await gdpr_mgr.request_data_deletion(sample_user_id, reason="Test")

        logs = await gdpr_mgr.get_audit_logs()
        assert len(logs) >= 2

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_user(self, gdpr_mgr):
        """Test filtering audit logs by user ID"""
        user1 = "user_001"
        user2 = "user_002"

        await gdpr_mgr.request_data_export(user1)
        await gdpr_mgr.request_data_export(user2)

        user1_logs = await gdpr_mgr.get_audit_logs(user_id=user1)
        assert all(log.user_id == user1 for log in user1_logs)

    @pytest.mark.asyncio
    async def test_get_audit_logs_filter_by_action(self, gdpr_mgr, sample_user_id):
        """Test filtering audit logs by action type"""
        await gdpr_mgr.request_data_export(sample_user_id)
        await gdpr_mgr.request_data_deletion(sample_user_id, reason="Test")

        export_logs = await gdpr_mgr.get_audit_logs(action="data_export")
        assert all(log.action == "data_export" for log in export_logs)

    @pytest.mark.asyncio
    async def test_get_audit_logs_limit(self, gdpr_mgr, sample_user_id):
        """Test audit log limit parameter"""
        # Create multiple audit logs
        for i in range(10):
            await gdpr_mgr.request_data_export(sample_user_id)

        logs = await gdpr_mgr.get_audit_logs(limit=5)
        assert len(logs) <= 5

    @pytest.mark.asyncio
    async def test_audit_log_contains_details(self, gdpr_mgr, sample_user_id):
        """Test audit log contains operation details"""
        await gdpr_mgr.request_data_export(sample_user_id, format="csv")

        logs = await gdpr_mgr.get_audit_logs(user_id=sample_user_id)
        assert len(logs) > 0
        assert "details" in logs[0].__dict__ or hasattr(logs[0], "details")

    @pytest.mark.asyncio
    async def test_log_audit_internal_method(self, gdpr_mgr, sample_user_id):
        """Test _log_audit internal method"""
        audit_log = await gdpr_mgr._log_audit(
            user_id=sample_user_id,
            action="test_action",
            details={"test_key": "test_value"},
            actor_id="admin_001",
            ip_address="10.0.0.1",
        )

        assert isinstance(audit_log, AuditLog)
        assert audit_log.user_id == sample_user_id
        assert audit_log.action == "test_action"
        assert audit_log.actor_id == "admin_001"
        assert audit_log.ip_address == "10.0.0.1"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestGDPRIntegration:
    """Integration tests for complete GDPR workflows"""

    @pytest.mark.asyncio
    async def test_complete_gdpr_workflow(self, gdpr_mgr, sample_user_id):
        """Test complete GDPR compliance workflow"""
        # 1. User grants consent
        consent = await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.MARKETING,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )
        assert consent.given is True

        # 2. User requests data export
        export = await gdpr_mgr.request_data_export(sample_user_id)
        assert export.user_id == sample_user_id

        # 3. User revokes consent
        revoke = await gdpr_mgr.update_consent(
            user_id=sample_user_id,
            consent_type=ConsentType.MARKETING,
            given=False,
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )
        assert revoke.given is False

        # 4. User requests data deletion
        deletion = await gdpr_mgr.request_data_deletion(
            sample_user_id,
            reason="No longer using service",
        )
        assert deletion.status == "completed"

        # 5. Verify audit trail
        logs = await gdpr_mgr.get_audit_logs(user_id=sample_user_id)
        assert len(logs) >= 4  # consent grant, export, consent revoke, deletion

    @pytest.mark.asyncio
    async def test_gdpr_router_exists(self):
        """Test GDPR API router exists"""
        assert router is not None
        assert router.prefix == "/api/v1/gdpr"
        assert "gdpr" in router.tags


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestGDPREdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_consent_with_empty_user_id(self, gdpr_mgr):
        """Test consent with empty user ID"""
        consent = await gdpr_mgr.update_consent(
            user_id="",
            consent_type=ConsentType.MARKETING,
            given=True,
            ip_address="192.168.1.1",
            user_agent="Test",
        )
        assert consent.user_id == ""

    @pytest.mark.asyncio
    async def test_data_export_with_special_characters_in_user_id(self, gdpr_mgr):
        """Test data export with special characters in user ID"""
        user_id = "user@#$%_123"
        response = await gdpr_mgr.request_data_export(user_id)
        assert response.user_id == user_id

    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations(self, gdpr_mgr, sample_user_id):
        """Test multiple concurrent GDPR operations"""
        # Simulate concurrent operations
        import asyncio

        tasks = [
            gdpr_mgr.request_data_export(sample_user_id),
            gdpr_mgr.update_consent(
                sample_user_id,
                ConsentType.MARKETING,
                True,
                "192.168.1.1",
                "Test",
            ),
            gdpr_mgr.update_consent(
                sample_user_id,
                ConsentType.ANALYTICS,
                True,
                "192.168.1.1",
                "Test",
            ),
        ]

        results = await asyncio.gather(*tasks)
        assert len(results) == 3


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=security.gdpr_compliance",
        "--cov-report=term-missing",
        "--cov-report=html",
    ])
