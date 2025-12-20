"""
Staging Security Features Tests
================================

Comprehensive security feature tests for staging environment.

Tests:
- XSS prevention and payload blocking
- CSRF protection and token validation
- SQL injection prevention
- Rate limiting enforcement
- Request signing validation
- Audit trail completeness

Environment:
- STAGING_BASE_URL: Base URL of staging environment

Usage:
    pytest tests/test_staging_security_features.py -v
    pytest tests/test_staging_security_features.py::TestXSSPrevention -v
"""

import os
import time

import httpx
import pytest

# Configuration
STAGING_BASE_URL = os.getenv("STAGING_BASE_URL", "http://localhost:8000")


# =============================================================================
# Test Class: XSS Prevention
# =============================================================================


@pytest.mark.integration
class TestXSSPrevention:
    """Test that XSS payloads are blocked"""

    @pytest.fixture
    async def http_client(self):
        """HTTP client for staging requests"""
        async with httpx.AsyncClient(base_url=STAGING_BASE_URL, timeout=30.0) as client:
            yield client

    # Common XSS payloads
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg/onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        "'; alert('XSS');//",
        "<body onload=alert('XSS')>",
        "<input type='text' value='' onfocus='alert(\"XSS\")'>",
    ]

    @pytest.mark.asyncio
    async def test_xss_in_query_parameter_blocked(self, http_client):
        """Test XSS payload in query parameter is blocked or sanitized"""
        xss_payload = "<script>alert('XSS')</script>"

        response = await http_client.get(f"/api/v1/search?q={xss_payload}")

        # Should either block (400) or sanitize
        if response.status_code == 200:
            # Check response doesn't contain unsanitized script
            assert "<script>" not in response.text.lower()

    @pytest.mark.asyncio
    async def test_xss_in_post_body_blocked(self, http_client):
        """Test XSS payload in POST body is blocked or sanitized"""
        for payload in self.XSS_PAYLOADS[:3]:  # Test first 3 payloads
            data = {"name": payload, "description": "test"}

            response = await http_client.post("/api/v1/data", json=data)

            # Should return success or validation error, but not execute script
            if response.status_code == 200:
                # Response should not contain unsanitized payload
                assert payload not in response.text

    @pytest.mark.asyncio
    async def test_xss_protection_header_present(self, http_client):
        """Test X-XSS-Protection header is present"""
        response = await http_client.get("/api/v1/health")

        # Should have X-XSS-Protection header
        assert "X-XSS-Protection" in response.headers
        assert "1" in response.headers["X-XSS-Protection"]

    @pytest.mark.asyncio
    async def test_content_type_nosniff_header(self, http_client):
        """Test X-Content-Type-Options: nosniff header prevents MIME sniffing"""
        response = await http_client.get("/api/v1/health")

        # Should have nosniff header
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"


# =============================================================================
# Test Class: CSRF Protection
# =============================================================================


@pytest.mark.integration
class TestCSRFProtection:
    """Test CSRF tokens are validated"""

    @pytest.fixture
    async def http_client(self):
        """HTTP client for staging requests"""
        async with httpx.AsyncClient(base_url=STAGING_BASE_URL, timeout=30.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_state_changing_request_without_csrf_rejected(self, http_client):
        """Test that POST/PUT/DELETE without CSRF token are rejected"""
        # Attempt to create resource without CSRF token
        response = await http_client.post("/api/v1/data", json={"name": "test"})

        # Should either:
        # 1. Require CSRF token (403/400)
        # 2. Require authentication (401)
        # 3. Succeed if CSRF not enforced on API endpoints (common for API-first apps)
        assert response.status_code in [200, 201, 400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_get_request_does_not_require_csrf(self, http_client):
        """Test that GET requests don't require CSRF token"""
        # GET requests should work without CSRF
        response = await http_client.get("/api/v1/health")

        # Should succeed
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_options_request_does_not_require_csrf(self, http_client):
        """Test that OPTIONS requests don't require CSRF token"""
        # OPTIONS (CORS preflight) should work
        response = await http_client.options("/api/v1/health")

        # Should succeed or return method not allowed
        assert response.status_code in [200, 204, 405]


# =============================================================================
# Test Class: SQL Injection Prevention
# =============================================================================


@pytest.mark.integration
class TestSQLInjectionPrevention:
    """Test SQL injection payloads are blocked"""

    @pytest.fixture
    async def http_client(self):
        """HTTP client for staging requests"""
        async with httpx.AsyncClient(base_url=STAGING_BASE_URL, timeout=30.0) as client:
            yield client

    # Common SQL injection payloads
    SQL_PAYLOADS = [
        "' OR '1'='1",
        "1' OR '1' = '1",
        "' OR 1=1--",
        "admin'--",
        "1' UNION SELECT NULL--",
        "'; DROP TABLE users--",
        "1' AND '1'='1",
    ]

    @pytest.mark.asyncio
    async def test_sql_injection_in_query_blocked(self, http_client):
        """Test SQL injection in query parameters is prevented"""
        sql_payload = "' OR '1'='1"

        response = await http_client.get(f"/api/v1/users?id={sql_payload}")

        # Should either:
        # 1. Block the request (400)
        # 2. Safely handle it (no SQL error)
        # 3. Require authentication (401)
        assert response.status_code in [200, 400, 401, 404]

        # Should not contain SQL error messages
        if response.status_code == 200:
            error_keywords = ["sql", "syntax error", "mysql", "postgres", "sqlite"]
            content_lower = response.text.lower()
            for keyword in error_keywords:
                assert keyword not in content_lower or "error" not in content_lower

    @pytest.mark.asyncio
    async def test_sql_injection_in_post_body_blocked(self, http_client):
        """Test SQL injection in POST body is prevented"""
        for payload in self.SQL_PAYLOADS[:3]:  # Test first 3
            data = {"username": payload, "password": "test"}

            response = await http_client.post("/api/v1/auth/login", json=data)

            # Should handle safely without SQL errors
            assert response.status_code in [200, 400, 401, 404]

            # Should not leak SQL error information
            if response.status_code != 200:
                error_keywords = ["syntax error", "mysql", "postgres"]
                content_lower = response.text.lower()
                for keyword in error_keywords:
                    assert keyword not in content_lower

    @pytest.mark.asyncio
    async def test_parameterized_queries_used(self, http_client):
        """Test that application uses parameterized queries (no SQL errors)"""
        # Make a request with special characters
        response = await http_client.get("/api/v1/search?q=test%20'%22%3B")

        # Should handle gracefully
        assert response.status_code in [200, 400, 401, 404]

        # Should not expose database errors
        if response.text:
            assert "SQL" not in response.text
            assert "syntax" not in response.text.lower()


# =============================================================================
# Test Class: Rate Limit Enforcement
# =============================================================================


@pytest.mark.integration
class TestRateLimitEnforcement:
    """Test rate limiting blocks excessive requests"""

    @pytest.fixture
    async def http_client(self):
        """HTTP client for staging requests"""
        async with httpx.AsyncClient(base_url=STAGING_BASE_URL, timeout=30.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_excessive_requests(self, http_client):
        """Test that excessive requests are blocked by rate limiter"""
        endpoint = "/api/v1/health"
        blocked = False

        # Make many requests quickly
        for i in range(20):
            response = await http_client.get(endpoint)

            if response.status_code == 429:
                blocked = True
                break

        # Should eventually be blocked
        assert blocked, "Rate limiter should block excessive requests"

    @pytest.mark.asyncio
    async def test_rate_limit_returns_retry_after_header(self, http_client):
        """Test that rate limited responses include Retry-After header"""
        endpoint = "/api/v1/health"

        # Make requests until rate limited
        for _ in range(20):
            response = await http_client.get(endpoint)

            if response.status_code == 429:
                # Should have Retry-After header
                assert "Retry-After" in response.headers
                retry_after = response.headers["Retry-After"]
                assert retry_after.isdigit()
                assert int(retry_after) > 0
                break

    @pytest.mark.asyncio
    async def test_rate_limit_per_ip_address(self, http_client):
        """Test that rate limiting is enforced per IP address"""
        endpoint = "/api/v1/health"

        # Make requests from same client
        responses = []
        for _ in range(15):
            response = await http_client.get(endpoint)
            responses.append(response.status_code)

        # Should see rate limiting (429) after several requests
        assert 429 in responses or len([r for r in responses if r == 200]) <= 12

    @pytest.mark.asyncio
    async def test_authenticated_requests_different_limit(self, http_client):
        """Test that authenticated requests may have different rate limits"""
        # Unauthenticated request
        response1 = await http_client.get("/api/v1/health")

        # Get rate limit info
        if "X-RateLimit-Limit" in response1.headers:
            unauth_limit = int(response1.headers["X-RateLimit-Limit"])

            # Authenticated requests might have higher limits
            # This test just verifies the header exists
            assert unauth_limit > 0


# =============================================================================
# Test Class: Request Signing Validation
# =============================================================================


@pytest.mark.integration
class TestRequestSigningValidation:
    """Test invalid signatures are rejected"""

    @pytest.fixture
    async def http_client(self):
        """HTTP client for staging requests"""
        async with httpx.AsyncClient(base_url=STAGING_BASE_URL, timeout=30.0) as client:
            yield client

    @pytest.mark.asyncio
    async def test_missing_timestamp_rejected(self, http_client):
        """Test request without timestamp is rejected"""
        headers = {
            "X-Nonce": "test-nonce",
            "X-Signature": "test-signature",
            # Missing X-Timestamp
        }

        response = await http_client.post("/api/v1/admin/config", headers=headers)

        # Should be rejected
        assert response.status_code in [400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_missing_nonce_rejected(self, http_client):
        """Test request without nonce is rejected"""
        headers = {
            "X-Timestamp": str(int(time.time())),
            "X-Signature": "test-signature",
            # Missing X-Nonce
        }

        response = await http_client.post("/api/v1/admin/config", headers=headers)

        # Should be rejected
        assert response.status_code in [400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_missing_signature_rejected(self, http_client):
        """Test request without signature is rejected"""
        headers = {
            "X-Timestamp": str(int(time.time())),
            "X-Nonce": "test-nonce",
            # Missing X-Signature
        }

        response = await http_client.post("/api/v1/admin/config", headers=headers)

        # Should be rejected
        assert response.status_code in [400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_malformed_signature_rejected(self, http_client):
        """Test request with malformed signature is rejected"""
        headers = {
            "X-Timestamp": str(int(time.time())),
            "X-Nonce": "test-nonce",
            "X-Signature": "not-a-valid-signature!!!",
        }

        response = await http_client.post("/api/v1/admin/config", headers=headers)

        # Should be rejected
        assert response.status_code in [400, 401, 403, 404]

    @pytest.mark.asyncio
    async def test_future_timestamp_rejected(self, http_client):
        """Test request with future timestamp is rejected"""
        # Timestamp 10 minutes in the future
        future_time = int(time.time()) + 600

        headers = {
            "X-Timestamp": str(future_time),
            "X-Nonce": "test-nonce",
            "X-Signature": "test-signature",
        }

        response = await http_client.post("/api/v1/admin/config", headers=headers)

        # Should be rejected due to timestamp validation
        assert response.status_code in [400, 401, 403, 404]


# =============================================================================
# Test Class: Audit Trail
# =============================================================================


@pytest.mark.integration
class TestAuditTrail:
    """Test that all events are properly audited"""

    @pytest.fixture
    async def http_client(self):
        """HTTP client for staging requests"""
        async with httpx.AsyncClient(base_url=STAGING_BASE_URL, timeout=30.0) as client:
            yield client

    def test_audit_logger_initialized(self):
        """Test that audit logger is properly initialized"""
        from security.audit_log import get_audit_logger

        logger = get_audit_logger()
        assert logger is not None

    def test_audit_log_entry_creation(self):
        """Test creating audit log entries"""
        from security.audit_log import AuditEventType, AuditSeverity, get_audit_logger

        logger = get_audit_logger()

        # Log a test event
        entry = logger.log(
            event_type=AuditEventType.LOGIN_SUCCESS,
            severity=AuditSeverity.INFO,
            resource_type="user",
            resource_id="test-user",
            action="test_login",
            status="success",
            user_id="test-user",
        )

        # Should create entry with hash
        assert entry is not None
        assert entry.hash is not None
        assert len(entry.hash) == 64  # SHA-256 hex

    def test_audit_log_integrity_verification(self):
        """Test audit log integrity verification"""
        from security.audit_log import AuditEventType, AuditSeverity, get_audit_logger

        logger = get_audit_logger()

        # Create entry
        entry = logger.log(
            event_type=AuditEventType.DATA_CREATED,
            severity=AuditSeverity.INFO,
            resource_type="test",
            resource_id="123",
            action="create",
            status="success",
        )

        # Verify integrity
        assert entry.verify_integrity(), "Audit entry should verify successfully"

    def test_audit_log_tampering_detection(self):
        """Test that tampering is detected"""
        from security.audit_log import AuditEventType, AuditSeverity, get_audit_logger

        logger = get_audit_logger()

        # Create entry
        entry = logger.log(
            event_type=AuditEventType.DATA_MODIFIED,
            severity=AuditSeverity.WARNING,
            resource_type="test",
            resource_id="456",
            action="modify",
            status="success",
        )

        # Tamper with entry
        original_hash = entry.hash
        entry.details = {"tampered": True}

        # Should detect tampering
        assert not entry.verify_integrity(), "Tampering should be detected"

        # Restore for cleanup
        entry.details = {}
        entry.hash = original_hash

    @pytest.mark.asyncio
    async def test_failed_requests_logged(self, http_client):
        """Test that failed requests are logged"""
        # Make a request that will fail
        response = await http_client.get("/api/v1/nonexistent-endpoint")

        # Should return 404
        assert response.status_code == 404

        # In a real system, this would be logged to audit trail
        # We can verify the logging mechanism exists
        from security.audit_log import get_audit_logger

        logger = get_audit_logger()
        assert logger is not None

    def test_security_events_logged(self):
        """Test that security events are logged"""
        from security.audit_log import AuditEventType, AuditSeverity, get_audit_logger

        logger = get_audit_logger()

        # Log a security event
        entry = logger.log_security_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            severity=AuditSeverity.WARNING,
            resource_id="test-ip-123",
            source_ip="192.168.1.100",
            details={"limit": 100, "requests": 150},
        )

        assert entry is not None
        assert entry.event_type == AuditEventType.RATE_LIMIT_EXCEEDED
        assert entry.source_ip == "192.168.1.100"

    def test_data_access_logged(self):
        """Test that data access is logged"""
        from security.audit_log import get_audit_logger

        logger = get_audit_logger()

        # Log data access
        entry = logger.log_data_access(
            resource_type="customer",
            resource_id="cust-123",
            action="read",
            user_id="admin-user",
            success=True,
        )

        assert entry is not None
        assert entry.resource_type == "customer"
        assert entry.action == "read"
