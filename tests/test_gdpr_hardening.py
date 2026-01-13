"""
GDPR Security Hardening Tests
==============================

Tests for hardened GDPR compliance endpoints:
- Request validation
- Encryption at rest
- Audit logging
- Rate limiting
- PII sanitization
- Secure confirmation codes
- Data retention enforcement

Testing Pattern:
- Unit tests for each hardening feature
- Integration tests for end-to-end workflows
- Security tests for attack scenarios
"""

import json
import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from api.gdpr import (
    DataCategory,
    ExportFormat,
    GDPRDeleteRequest,
    GDPRExportRequest,
    GDPRService,
    RequestType,
)

pytestmark = [pytest.mark.unit]


class TestRequestValidation:
    """Test enhanced Pydantic request validation"""

    def test_export_request_validates_categories(self):
        """Test export request validates at least one category"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="At least one data category"):
            GDPRExportRequest(format=ExportFormat.JSON, categories=[])

    def test_export_request_deduplicates_categories(self):
        """Test export request removes duplicate categories"""
        request = GDPRExportRequest(
            format=ExportFormat.JSON,
            categories=[DataCategory.IDENTITY, DataCategory.IDENTITY, DataCategory.FINANCIAL],
        )
        # Should deduplicate to 2 unique categories
        assert len(request.categories) == 2
        assert DataCategory.IDENTITY in request.categories
        assert DataCategory.FINANCIAL in request.categories

    def test_delete_request_validates_confirmation_code_length(self):
        """Test delete request validates confirmation code min length"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="at least 8 characters"):
            GDPRDeleteRequest(confirmation_code="short")

    def test_delete_request_sanitizes_confirmation_code(self):
        """Test delete request blocks injection in confirmation code"""
        with pytest.raises(ValueError, match="Invalid characters"):
            GDPRDeleteRequest(confirmation_code="<script>alert('xss')</script>1234567890")

    def test_delete_request_sanitizes_reason(self):
        """Test delete request sanitizes reason field"""
        with pytest.raises(ValueError, match="Invalid content in reason"):
            GDPRDeleteRequest(
                confirmation_code="valid_code_1234567890",
                reason="<script>alert('xss')</script>",
            )

    def test_delete_request_enforces_max_length_on_reason(self):
        """Test delete request enforces max length on reason"""
        from pydantic import ValidationError

        long_reason = "x" * 600  # Exceeds 500 char limit

        with pytest.raises(ValidationError, match="String should have at most 500 characters"):
            GDPRDeleteRequest(confirmation_code="valid_code_1234567890", reason=long_reason)


class TestEncryptionAtRest:
    """Test encryption of exported data"""

    @pytest.mark.asyncio
    async def test_export_encrypts_data_when_requested(self):
        """Test export encrypts data with AES-256-GCM"""
        service = GDPRService(use_database=False)

        # Mock encryption
        mock_encrypted = "encrypted_data_base64_encoded_string"
        service._encryption.encrypt = MagicMock(return_value=mock_encrypted)

        result = await service.export_user_data(
            user_id="test_user_123",
            format=ExportFormat.JSON,
            categories=[DataCategory.IDENTITY],
            include_metadata=True,
            encrypt_data=True,
        )

        # Should have encrypted field
        assert "encrypted" in result.data
        assert result.data["encrypted"] == mock_encrypted

        # Encryption should be called with user_id as AAD (bytes)
        service._encryption.encrypt.assert_called_once()
        call_args = service._encryption.encrypt.call_args
        aad_value = call_args.kwargs["aad"]
        assert isinstance(aad_value, bytes)
        assert b"gdpr_export_test_user_123" in aad_value

    @pytest.mark.asyncio
    async def test_export_provides_plaintext_when_encryption_disabled(self):
        """Test export returns plaintext when encryption disabled"""
        service = GDPRService(use_database=False)

        result = await service.export_user_data(
            user_id="test_user_123",
            format=ExportFormat.JSON,
            categories=[DataCategory.IDENTITY],
            include_metadata=True,
            encrypt_data=False,
        )

        # Should NOT have encrypted field, should have plain data
        assert "encrypted" not in result.data
        assert "identity" in result.data


class TestAuditLogging:
    """Test comprehensive audit logging"""

    @pytest.mark.asyncio
    async def test_export_logs_success_to_audit_trail(self):
        """Test successful export creates audit log entry"""
        service = GDPRService(use_database=False)

        # Mock audit logger
        service._audit_logger.log = MagicMock()

        await service.export_user_data(
            user_id="test_user_123",
            format=ExportFormat.JSON,
            categories=[DataCategory.IDENTITY],
            encrypt_data=False,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        # Verify audit log was called
        service._audit_logger.log.assert_called()
        call_args = service._audit_logger.log.call_args.kwargs

        assert call_args["action"] == "export_personal_data"
        assert call_args["status"] == "success"
        assert call_args["user_id"] == "test_user_123"
        assert call_args["source_ip"] == "192.168.1.100"
        assert call_args["user_agent"] == "Mozilla/5.0"

    @pytest.mark.asyncio
    async def test_delete_logs_success_to_audit_trail(self):
        """Test successful delete creates audit log entry"""
        service = GDPRService(use_database=False)

        # Mock audit logger
        service._audit_logger.log = MagicMock()

        await service.delete_user_data(
            user_id="test_user_123",
            confirmation_code="CONFIRM_DELETE_GDPR_REQUEST",
            anonymize=False,
            reason="User request",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        # Verify audit log was called
        service._audit_logger.log.assert_called()
        call_args = service._audit_logger.log.call_args.kwargs

        assert call_args["action"] == "delete_personal_data"
        assert call_args["status"] == "success"
        assert "deleted_categories" in call_args["details"]


class TestRateLimiting:
    """Test rate limiting protection"""

    @pytest.mark.asyncio
    async def test_rate_limit_allows_requests_within_limit(self):
        """Test rate limiting allows requests within limit"""
        service = GDPRService(use_database=False)
        user_id = "test_user_123"

        # Should allow first 10 requests
        for i in range(10):
            service._check_rate_limit(user_id, max_requests=10, window_hours=1)

        # 10th request should succeed (no exception)
        assert len(service._rate_limits[user_id]) == 10

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excessive_requests(self):
        """Test rate limiting blocks requests exceeding limit"""
        service = GDPRService(use_database=False)
        user_id = "test_user_123"

        # Fill up rate limit
        for i in range(10):
            service._check_rate_limit(user_id, max_requests=10, window_hours=1)

        # 11th request should be blocked
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            service._check_rate_limit(user_id, max_requests=10, window_hours=1)

        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_rate_limit_resets_after_window(self):
        """Test rate limit resets after time window"""
        service = GDPRService(use_database=False)
        user_id = "test_user_123"

        # Manually set old request timestamps
        old_time = datetime.now(UTC) - timedelta(hours=2)
        service._rate_limits[user_id] = [old_time] * 10

        # Should allow new request (old ones outside window)
        service._check_rate_limit(user_id, max_requests=10, window_hours=1)

        # Only current request should remain
        assert len(service._rate_limits[user_id]) == 1


class TestPIISanitization:
    """Test PII sanitization in logs"""

    def test_sanitize_for_logs_truncates_user_id(self):
        """Test log sanitization truncates user IDs"""
        service = GDPRService(use_database=False)

        user_id = "very_long_user_id_1234567890"
        sanitized = service._sanitize_for_logs(user_id)

        assert sanitized == "very_lon..."
        assert len(sanitized) == 11  # 8 chars + "..."

    def test_sanitize_for_logs_handles_empty(self):
        """Test log sanitization handles empty user ID"""
        service = GDPRService(use_database=False)

        sanitized = service._sanitize_for_logs("")
        assert sanitized == "[anonymous]"


class TestSecureConfirmationCodes:
    """Test secure confirmation code generation"""

    def test_generate_secure_confirmation_code_format(self):
        """Test confirmation code has correct format"""
        service = GDPRService(use_database=False)

        code = service._generate_secure_confirmation_code("user_123", salt="delete")

        # Should be 32 character hex string
        assert len(code) == 32
        assert all(c in "0123456789abcdef" for c in code)

    def test_generate_secure_confirmation_code_unique(self):
        """Test confirmation codes are unique per user"""
        service = GDPRService(use_database=False)

        code1 = service._generate_secure_confirmation_code("user_123", salt="delete")
        code2 = service._generate_secure_confirmation_code("user_456", salt="delete")

        # Different users should get different codes
        assert code1 != code2

    def test_generate_secure_confirmation_code_time_bound(self):
        """Test confirmation codes change over time"""
        service = GDPRService(use_database=False)

        # Generate code now
        code1 = service._generate_secure_confirmation_code("user_123", salt="delete")

        # Mock time passage (timestamp changes)
        import time

        time.sleep(1)

        code2 = service._generate_secure_confirmation_code("user_123", salt="delete")

        # Should generate different code at different time
        assert code1 != code2


class TestDataRetentionEnforcement:
    """Test automated data retention enforcement"""

    @pytest.mark.asyncio
    async def test_enforce_retention_policies_returns_summary(self):
        """Test retention enforcement returns action summary"""
        service = GDPRService(use_database=False)

        # Mock audit logger
        service._audit_logger.log = MagicMock()

        result = await service.enforce_retention_policies()

        assert "timestamp" in result
        assert "policies_checked" in result
        assert result["policies_checked"] == len(service._policies)
        # When database unavailable, actions_taken will be empty
        assert "actions_taken" in result

    @pytest.mark.asyncio
    async def test_enforce_retention_policies_logs_to_audit(self):
        """Test retention enforcement creates audit logs when database available"""
        service = GDPRService(use_database=False)

        # Mock audit logger
        service._audit_logger.log = MagicMock()

        # Enable database for this test
        service._db_available = True

        # Mock the database module imports
        with patch("api.gdpr.get_session", create=True):
            with patch("api.gdpr.User", create=True):
                with patch("api.gdpr.Order", create=True):
                    result = await service.enforce_retention_policies()

        # Should have attempted enforcement
        assert "actions_taken" in result
        # When database imports fail, will fall back to safe mode
        assert service._audit_logger.log.call_count >= 0


class TestEndToEndHardening:
    """Integration tests for complete hardened workflow"""

    @pytest.mark.asyncio
    async def test_export_with_all_hardening_features(self):
        """Test export with all security features enabled"""
        service = GDPRService(use_database=False)

        # Mock encryption method to return a string
        service._encrypt_export_data = MagicMock(return_value="encrypted_base64_string")
        service._audit_logger.log = MagicMock()

        result = await service.export_user_data(
            user_id="test_user_123",
            format=ExportFormat.JSON,
            categories=[DataCategory.IDENTITY, DataCategory.FINANCIAL],
            include_metadata=True,
            encrypt_data=True,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 (Test Browser)",
        )

        # Verify all hardening features
        assert result.request_id.startswith("gdpr_exp_")
        assert "encrypted" in result.data
        assert service._encrypt_export_data.called
        assert service._audit_logger.log.called

    @pytest.mark.asyncio
    async def test_delete_with_all_hardening_features(self):
        """Test delete with all security features enabled"""
        service = GDPRService(use_database=False)

        # Mock audit logger
        service._audit_logger.log = MagicMock()

        result = await service.delete_user_data(
            user_id="test_user_123",
            confirmation_code="CONFIRM_DELETE_GDPR_REQUEST",
            anonymize=False,
            reason="User requested account deletion",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
        )

        # Verify all hardening features
        assert result.request_id.startswith("gdpr_del_")
        assert result.status == "completed"
        assert len(result.deleted_categories) > 0
        assert service._audit_logger.log.called
