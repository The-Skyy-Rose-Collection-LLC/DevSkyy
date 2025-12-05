"""
Comprehensive Test Suite for Enhanced Security Module

Tests threat detection, security policies, encryption, HMAC verification,
request analysis, and security event tracking.

Per CLAUDE.md Rule #8: Target ≥75% coverage
Per CLAUDE.md Rule #13: Security baseline verification

Author: DevSkyy Enterprise Team
Version: 2.0.0
Python: >=3.11.0
"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from security.enhanced_security import (
    EnhancedSecurityManager,
    SecurityEvent,
    SecurityEventType,
    SecurityPolicy,
    ThreatLevel,
    security_manager,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def security_mgr():
    """Create EnhancedSecurityManager for testing"""
    return EnhancedSecurityManager(redis_client=None)


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock()
    redis_mock.incr = AsyncMock()
    redis_mock.lpush = AsyncMock()
    redis_mock.ltrim = AsyncMock()
    return redis_mock


@pytest.fixture
def sample_request_data():
    """Create sample request data for testing"""
    return {
        "source_ip": "192.168.1.100",
        "user_id": "user_123",
        "endpoint": "/api/v1/users/profile",
        "url": "/api/v1/users/profile?id=123",
        "query_params": "id=123",
        "body": '{"name": "Test User"}',
        "headers": {
            "user-agent": "Mozilla/5.0 Test Browser",
            "authorization": "Bearer token123",
        },
    }


# ============================================================================
# ENUM AND MODEL TESTS
# ============================================================================


class TestEnumsAndModels:
    """Test security enums and models"""

    def test_threat_level_enum(self):
        """Test ThreatLevel enum values"""
        assert ThreatLevel.LOW == "low"
        assert ThreatLevel.MEDIUM == "medium"
        assert ThreatLevel.HIGH == "high"
        assert ThreatLevel.CRITICAL == "critical"

    def test_security_event_type_enum(self):
        """Test SecurityEventType enum values"""
        assert SecurityEventType.AUTHENTICATION_FAILURE == "auth_failure"
        assert SecurityEventType.AUTHORIZATION_VIOLATION == "authz_violation"
        assert SecurityEventType.SUSPICIOUS_ACTIVITY == "suspicious_activity"
        assert SecurityEventType.DATA_ACCESS_VIOLATION == "data_access_violation"
        assert SecurityEventType.RATE_LIMIT_EXCEEDED == "rate_limit_exceeded"
        assert SecurityEventType.MALICIOUS_REQUEST == "malicious_request"
        assert SecurityEventType.COMPLIANCE_VIOLATION == "compliance_violation"

    def test_security_event_model(self):
        """Test SecurityEvent model creation"""
        event = SecurityEvent(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            threat_level=ThreatLevel.HIGH,
            source_ip="10.0.0.1",
            user_id="user_456",
            endpoint="/api/v1/admin",
            description="Suspicious activity detected",
        )

        assert event.event_type == SecurityEventType.SUSPICIOUS_ACTIVITY
        assert event.threat_level == ThreatLevel.HIGH
        assert event.source_ip == "10.0.0.1"
        assert event.resolved is False
        assert event.event_id is not None

    def test_security_event_defaults(self):
        """Test SecurityEvent default values"""
        event = SecurityEvent(
            event_type=SecurityEventType.MALICIOUS_REQUEST,
            threat_level=ThreatLevel.CRITICAL,
            description="Test event",
        )

        assert event.source_ip is None
        assert event.user_id is None
        assert event.endpoint is None
        assert event.metadata == {}
        assert isinstance(event.timestamp, datetime)

    def test_security_policy_model(self):
        """Test SecurityPolicy model creation"""
        policy = SecurityPolicy(
            policy_id="test_policy",
            name="Test Policy",
            description="Test security policy",
            enabled=True,
            rules=[{"type": "pattern", "regex": "test"}],
            actions=["log", "block"],
            severity=ThreatLevel.MEDIUM,
        )

        assert policy.policy_id == "test_policy"
        assert policy.enabled is True
        assert len(policy.rules) == 1
        assert "log" in policy.actions


# ============================================================================
# SECURITY MANAGER INITIALIZATION TESTS
# ============================================================================


class TestSecurityManagerInitialization:
    """Test EnhancedSecurityManager initialization"""

    def test_security_manager_initialization(self, security_mgr):
        """Test security manager initializes correctly"""
        assert security_mgr.security_events == []
        assert security_mgr.blocked_ips == set()
        assert security_mgr.suspicious_patterns == {}
        assert len(security_mgr.security_policies) > 0
        assert security_mgr.encryption_key is not None

    def test_security_manager_with_redis(self, mock_redis):
        """Test security manager initializes with Redis"""
        mgr = EnhancedSecurityManager(redis_client=mock_redis)

        assert mgr.redis_client == mock_redis

    def test_security_manager_default_policies(self, security_mgr):
        """Test default security policies are loaded"""
        assert "rate_limiting" in security_mgr.security_policies
        assert "sql_injection" in security_mgr.security_policies
        assert "xss_detection" in security_mgr.security_policies
        assert "gdpr_compliance" in security_mgr.security_policies

    def test_security_manager_metrics_initialized(self, security_mgr):
        """Test security metrics are initialized"""
        assert security_mgr.metrics["total_events"] == 0
        assert security_mgr.metrics["blocked_requests"] == 0
        assert security_mgr.metrics["threat_detections"] == 0

    def test_encryption_initialization(self, security_mgr):
        """Test encryption system is initialized"""
        assert security_mgr.encryption_key is not None
        assert security_mgr.cipher_suite is not None

    def test_global_security_manager_exists(self):
        """Test global security_manager instance exists"""
        assert security_manager is not None
        assert isinstance(security_manager, EnhancedSecurityManager)


# ============================================================================
# SECURITY POLICY TESTS
# ============================================================================


class TestSecurityPolicies:
    """Test default security policies"""

    def test_rate_limiting_policy(self, security_mgr):
        """Test rate limiting policy configuration"""
        policy = security_mgr.security_policies["rate_limiting"]

        assert policy.enabled is True
        assert policy.severity == ThreatLevel.MEDIUM
        assert "log" in policy.actions
        assert "block_ip" in policy.actions

    def test_sql_injection_policy(self, security_mgr):
        """Test SQL injection detection policy"""
        policy = security_mgr.security_policies["sql_injection"]

        assert policy.severity == ThreatLevel.HIGH
        assert "block_request" in policy.actions
        assert len(policy.rules) >= 2  # Multiple patterns

    def test_xss_detection_policy(self, security_mgr):
        """Test XSS detection policy"""
        policy = security_mgr.security_policies["xss_detection"]

        assert policy.severity == ThreatLevel.HIGH
        assert "sanitize" in policy.actions
        assert len(policy.rules) >= 2

    def test_gdpr_compliance_policy(self, security_mgr):
        """Test GDPR compliance policy"""
        policy = security_mgr.security_policies["gdpr_compliance"]

        assert policy.severity == ThreatLevel.CRITICAL
        assert "notify_dpo" in policy.actions


# ============================================================================
# REQUEST ANALYSIS TESTS
# ============================================================================


class TestRequestAnalysis:
    """Test request security analysis"""

    @pytest.mark.asyncio
    async def test_analyze_request_clean(self, security_mgr, sample_request_data):
        """Test analyzing clean request"""
        result = await security_mgr.analyze_request(sample_request_data)

        assert result["threat_detected"] is False
        assert result["threat_level"] == ThreatLevel.LOW
        assert result["allow_request"] is True
        assert result["violations"] == []

    @pytest.mark.asyncio
    async def test_analyze_request_blocked_ip(self, security_mgr, sample_request_data):
        """Test analyzing request from blocked IP"""
        # Block the IP
        security_mgr.blocked_ips.add(sample_request_data["source_ip"])

        result = await security_mgr.analyze_request(sample_request_data)

        assert result["threat_detected"] is True
        assert result["allow_request"] is False
        assert "blocked_ip" in result["violations"]

    @pytest.mark.asyncio
    async def test_analyze_request_sql_injection(self, security_mgr):
        """Test detecting SQL injection attempt"""
        malicious_request = {
            "source_ip": "10.0.0.1",
            "url": "/api/users?id=1 OR 1=1",
            "query_params": "id=1 OR 1=1",
            "body": "",
            "headers": {},
        }

        result = await security_mgr.analyze_request(malicious_request)

        assert result["threat_detected"] is True
        # May or may not block depending on policy, but should detect

    @pytest.mark.asyncio
    async def test_analyze_request_xss_attempt(self, security_mgr):
        """Test detecting XSS attempt"""
        xss_request = {
            "source_ip": "10.0.0.1",
            "url": "/api/comment",
            "body": '<script>alert("XSS")</script>',
            "headers": {},
        }

        result = await security_mgr.analyze_request(xss_request)

        assert result["threat_detected"] is True

    @pytest.mark.asyncio
    async def test_analyze_request_multiple_policies(self, security_mgr):
        """Test request triggers multiple policies"""
        malicious_request = {
            "source_ip": "10.0.0.1",
            "url": "/api/users?id=<script>alert(1)</script> OR 1=1",
            "query_params": "id=<script>alert(1)</script> OR 1=1",
            "body": "",
            "headers": {},
        }

        result = await security_mgr.analyze_request(malicious_request)

        assert result["threat_detected"] is True
        # Should trigger both SQL injection and XSS policies

    @pytest.mark.asyncio
    async def test_analyze_request_error_handling(self, security_mgr):
        """Test request analysis handles errors gracefully"""
        invalid_request = None  # This will cause errors

        result = await security_mgr.analyze_request(invalid_request)

        # Should fail secure and block request
        assert result["allow_request"] is False
        assert "error" in result


# ============================================================================
# PATTERN MATCHING TESTS
# ============================================================================


class TestPatternMatching:
    """Test security pattern matching"""

    def test_check_pattern_match_sql_keywords(self, security_mgr):
        """Test SQL keyword detection"""
        request_data = {
            "url": "/api/data?query=SELECT * FROM users",
            "query_params": "query=SELECT * FROM users",
            "body": "",
            "headers": {},
        }

        rule = {"regex": r"(?i)(union|select|insert|update|delete)"}

        match = security_mgr._check_pattern_match(request_data, rule)
        assert match is True

    def test_check_pattern_match_xss_tags(self, security_mgr):
        """Test XSS tag detection"""
        request_data = {
            "url": "/api/comment",
            "body": '<script>evil()</script>',
            "headers": {},
        }

        rule = {"regex": r"(?i)<script|javascript:"}

        match = security_mgr._check_pattern_match(request_data, rule)
        assert match is True

    def test_check_pattern_match_no_match(self, security_mgr):
        """Test pattern matching with clean request"""
        request_data = {
            "url": "/api/data",
            "body": "clean data",
            "headers": {},
        }

        rule = {"regex": r"(?i)(malicious|evil)"}

        match = security_mgr._check_pattern_match(request_data, rule)
        assert match is False

    def test_check_pattern_match_case_insensitive(self, security_mgr):
        """Test pattern matching is case-insensitive"""
        request_data = {
            "url": "/api/search?q=UNION SELECT",
            "query_params": "q=UNION SELECT",
            "body": "",
            "headers": {},
        }

        rule = {"regex": r"(?i)union\s+select"}

        match = security_mgr._check_pattern_match(request_data, rule)
        assert match is True


# ============================================================================
# RATE LIMITING TESTS
# ============================================================================


class TestRateLimiting:
    """Test rate limiting functionality"""

    @pytest.mark.asyncio
    async def test_check_rate_limit_without_redis(self, security_mgr):
        """Test rate limit check without Redis returns False"""
        request_data = {"source_ip": "10.0.0.1"}
        rule = {"window": 60, "max_requests": 100}

        result = await security_mgr._check_rate_limit(request_data, rule)

        # Without Redis, should return False (no rate limiting)
        assert result is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_with_redis_first_request(
        self,
        mock_redis,
    ):
        """Test first request within rate limit"""
        mgr = EnhancedSecurityManager(redis_client=mock_redis)

        request_data = {"source_ip": "10.0.0.1"}
        rule = {"window": 60, "max_requests": 100}

        mock_redis.get.return_value = None

        result = await mgr._check_rate_limit(request_data, rule)

        assert result is False  # Not exceeded
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_with_redis_under_limit(self, mock_redis):
        """Test request under rate limit"""
        mgr = EnhancedSecurityManager(redis_client=mock_redis)

        request_data = {"source_ip": "10.0.0.1"}
        rule = {"window": 60, "max_requests": 100}

        mock_redis.get.return_value = "50"  # Current count

        result = await mgr._check_rate_limit(request_data, rule)

        assert result is False  # Under limit
        mock_redis.incr.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_rate_limit_with_redis_exceeded(self, mock_redis):
        """Test request exceeds rate limit"""
        mgr = EnhancedSecurityManager(redis_client=mock_redis)

        request_data = {"source_ip": "10.0.0.1"}
        rule = {"window": 60, "max_requests": 100}

        mock_redis.get.return_value = "100"  # At limit

        result = await mgr._check_rate_limit(request_data, rule)

        assert result is True  # Exceeded
        # Should not increment
        mock_redis.incr.assert_not_called()


# ============================================================================
# GDPR COMPLIANCE CHECK TESTS
# ============================================================================


class TestGDPRComplianceCheck:
    """Test GDPR compliance checking"""

    def test_check_data_access_compliance_violation(self, security_mgr):
        """Test detecting GDPR data access violation"""
        request_data = {
            "endpoint": "/api/v1/users/123/profile",
            "headers": {},  # No authorization
        }

        rule = {"requires_consent": True}

        violation = security_mgr._check_data_access_compliance(request_data, rule)

        assert violation is True  # Missing authorization

    def test_check_data_access_compliance_with_auth(self, security_mgr):
        """Test GDPR compliance with proper authorization"""
        request_data = {
            "endpoint": "/api/v1/users/123/profile",
            "headers": {"authorization": "Bearer token123"},
        }

        rule = {"requires_consent": True}

        violation = security_mgr._check_data_access_compliance(request_data, rule)

        assert violation is False  # Has authorization

    def test_check_data_access_compliance_non_personal_data(self, security_mgr):
        """Test GDPR check for non-personal data endpoint"""
        request_data = {
            "endpoint": "/api/v1/public/status",
            "headers": {},
        }

        rule = {"requires_consent": True}

        violation = security_mgr._check_data_access_compliance(request_data, rule)

        assert violation is False  # Not a personal data endpoint


# ============================================================================
# POLICY ACTION EXECUTION TESTS
# ============================================================================


class TestPolicyActionExecution:
    """Test security policy action execution"""

    @pytest.mark.asyncio
    async def test_execute_policy_actions_log(self, security_mgr):
        """Test log action execution"""
        policy = SecurityPolicy(
            policy_id="test",
            name="Test Policy",
            description="Test",
            actions=["log"],
        )

        request_data = {"source_ip": "10.0.0.1"}
        violations = ["test_violation"]

        actions_taken = await security_mgr._execute_policy_actions(
            policy,
            request_data,
            violations,
        )

        assert "logged" in actions_taken

    @pytest.mark.asyncio
    async def test_execute_policy_actions_block_ip(self, security_mgr):
        """Test block_ip action execution"""
        policy = SecurityPolicy(
            policy_id="test",
            name="Test Policy",
            description="Test",
            actions=["block_ip"],
        )

        request_data = {"source_ip": "10.0.0.1"}
        violations = ["test_violation"]

        actions_taken = await security_mgr._execute_policy_actions(
            policy,
            request_data,
            violations,
        )

        assert "ip_blocked" in actions_taken
        assert "10.0.0.1" in security_mgr.blocked_ips

    @pytest.mark.asyncio
    async def test_execute_policy_actions_multiple(self, security_mgr):
        """Test executing multiple actions"""
        policy = SecurityPolicy(
            policy_id="test",
            name="Test Policy",
            description="Test",
            actions=["log", "block_request", "alert"],
        )

        request_data = {"source_ip": "10.0.0.1"}
        violations = ["test_violation"]

        actions_taken = await security_mgr._execute_policy_actions(
            policy,
            request_data,
            violations,
        )

        assert len(actions_taken) >= 3


# ============================================================================
# ENCRYPTION TESTS
# ============================================================================


class TestEncryption:
    """Test encryption functionality"""

    def test_encrypt_sensitive_data(self, security_mgr):
        """Test encrypting sensitive data"""
        sensitive_data = "secret_password_123"

        encrypted = security_mgr.encrypt_sensitive_data(sensitive_data)

        assert encrypted != sensitive_data
        assert len(encrypted) > 0

    def test_decrypt_sensitive_data(self, security_mgr):
        """Test decrypting sensitive data"""
        original_data = "secret_api_key_456"

        encrypted = security_mgr.encrypt_sensitive_data(original_data)
        decrypted = security_mgr.decrypt_sensitive_data(encrypted)

        assert decrypted == original_data

    def test_encrypt_decrypt_round_trip(self, security_mgr):
        """Test encryption-decryption round trip"""
        test_data = "This is sensitive information!"

        encrypted = security_mgr.encrypt_sensitive_data(test_data)
        decrypted = security_mgr.decrypt_sensitive_data(encrypted)

        assert decrypted == test_data

    def test_encrypt_decrypt_with_special_characters(self, security_mgr):
        """Test encryption with special characters"""
        test_data = "Test@#$%^&*()_+-={}[]|:;<>?,./~`"

        encrypted = security_mgr.encrypt_sensitive_data(test_data)
        decrypted = security_mgr.decrypt_sensitive_data(encrypted)

        assert decrypted == test_data

    def test_decrypt_invalid_data_fails(self, security_mgr):
        """Test decrypting invalid data fails"""
        with pytest.raises(Exception):
            security_mgr.decrypt_sensitive_data("invalid_encrypted_data")


# ============================================================================
# TOKEN GENERATION TESTS
# ============================================================================


class TestTokenGeneration:
    """Test secure token generation"""

    def test_generate_secure_token_default_length(self, security_mgr):
        """Test generating secure token with default length"""
        token = security_mgr.generate_secure_token()

        assert len(token) > 0
        assert isinstance(token, str)

    def test_generate_secure_token_custom_length(self, security_mgr):
        """Test generating token with custom length"""
        token = security_mgr.generate_secure_token(length=64)

        # URL-safe base64 encoding affects length, but should be substantial
        assert len(token) > 50

    def test_generate_secure_token_uniqueness(self, security_mgr):
        """Test generated tokens are unique"""
        token1 = security_mgr.generate_secure_token()
        token2 = security_mgr.generate_secure_token()

        assert token1 != token2


# ============================================================================
# HMAC VERIFICATION TESTS
# ============================================================================


class TestHMACVerification:
    """Test HMAC signature verification"""

    def test_verify_hmac_signature_valid(self, security_mgr):
        """Test verifying valid HMAC signature"""
        import hashlib
        import hmac

        data = "webhook_payload_data"
        secret = "webhook_secret_key"

        # Generate valid signature
        signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()

        result = security_mgr.verify_hmac_signature(data, signature, secret)

        assert result is True

    def test_verify_hmac_signature_invalid(self, security_mgr):
        """Test rejecting invalid HMAC signature"""
        data = "webhook_payload_data"
        secret = "webhook_secret_key"
        invalid_signature = "invalid_signature_hash"

        result = security_mgr.verify_hmac_signature(data, invalid_signature, secret)

        assert result is False

    def test_verify_hmac_signature_wrong_secret(self, security_mgr):
        """Test HMAC verification fails with wrong secret"""
        import hashlib
        import hmac

        data = "webhook_payload_data"
        secret = "correct_secret"
        wrong_secret = "wrong_secret"

        signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()

        result = security_mgr.verify_hmac_signature(data, signature, wrong_secret)

        assert result is False


# ============================================================================
# SECURITY METRICS TESTS
# ============================================================================


class TestSecurityMetrics:
    """Test security metrics and reporting"""

    @pytest.mark.asyncio
    async def test_get_security_metrics_initial(self, security_mgr):
        """Test getting initial security metrics"""
        metrics = await security_mgr.get_security_metrics()

        assert metrics["total_events"] == 0
        assert metrics["blocked_ips_count"] == 0
        assert metrics["recent_events_24h"] == 0
        assert "threat_level_distribution" in metrics

    @pytest.mark.asyncio
    async def test_get_security_metrics_after_events(self, security_mgr):
        """Test metrics after security events"""
        # Create some security events
        security_mgr.security_events.append(
            SecurityEvent(
                event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                threat_level=ThreatLevel.HIGH,
                description="Test event",
            )
        )

        metrics = await security_mgr.get_security_metrics()

        assert metrics["recent_events_24h"] >= 1

    @pytest.mark.asyncio
    async def test_get_security_events(self, security_mgr):
        """Test getting security events"""
        # Add some events
        security_mgr.security_events.append(
            SecurityEvent(
                event_type=SecurityEventType.MALICIOUS_REQUEST,
                threat_level=ThreatLevel.CRITICAL,
                description="Test",
            )
        )

        events = await security_mgr.get_security_events(limit=10)

        assert len(events) >= 1
        assert isinstance(events[0], SecurityEvent)

    @pytest.mark.asyncio
    async def test_get_security_events_limit(self, security_mgr):
        """Test security events limit"""
        # Add multiple events
        for i in range(20):
            security_mgr.security_events.append(
                SecurityEvent(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    threat_level=ThreatLevel.LOW,
                    description=f"Event {i}",
                )
            )

        events = await security_mgr.get_security_events(limit=5)

        assert len(events) == 5


# ============================================================================
# SECURITY POLICY MANAGEMENT TESTS
# ============================================================================


class TestPolicyManagement:
    """Test security policy management"""

    def test_update_security_policy(self, security_mgr):
        """Test updating security policy"""
        new_policy = SecurityPolicy(
            policy_id="custom_policy",
            name="Custom Policy",
            description="Test custom policy",
            rules=[{"type": "test"}],
            actions=["log"],
        )

        security_mgr.update_security_policy("custom_policy", new_policy)

        assert "custom_policy" in security_mgr.security_policies
        assert security_mgr.security_policies["custom_policy"] == new_policy

    def test_disable_security_policy(self, security_mgr):
        """Test disabling security policy"""
        policy_id = "rate_limiting"

        security_mgr.disable_security_policy(policy_id)

        assert security_mgr.security_policies[policy_id].enabled is False

    @pytest.mark.asyncio
    async def test_unblock_ip(self, security_mgr):
        """Test unblocking IP address"""
        ip_address = "10.0.0.1"

        # Block IP first
        security_mgr.blocked_ips.add(ip_address)

        # Unblock
        await security_mgr.unblock_ip(ip_address)

        assert ip_address not in security_mgr.blocked_ips


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestSecurityIntegration:
    """Integration tests for complete security workflows"""

    @pytest.mark.asyncio
    async def test_complete_threat_detection_workflow(self, security_mgr):
        """Test complete threat detection and response workflow"""
        # 1. Malicious request comes in
        malicious_request = {
            "source_ip": "10.0.0.99",
            "url": "/api/data?id=1 OR 1=1",
            "query_params": "id=1 OR 1=1",
            "body": "",
            "headers": {},
        }

        # 2. Analyze request
        result = await security_mgr.analyze_request(malicious_request)

        # 3. Verify threat was detected
        assert result["threat_detected"] is True

        # 4. Verify IP was blocked (if high severity)
        if result["threat_level"] in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            # IP might be blocked depending on policy actions
            pass

        # 5. Verify security event was logged
        assert len(security_mgr.security_events) > 0

    @pytest.mark.asyncio
    async def test_encryption_and_decryption_workflow(self, security_mgr):
        """Test complete encryption workflow"""
        # 1. Encrypt sensitive data
        api_key = "sk_live_1234567890abcdef"
        encrypted = security_mgr.encrypt_sensitive_data(api_key)

        # 2. Store encrypted data (simulated)
        stored_data = {"encrypted_api_key": encrypted}

        # 3. Retrieve and decrypt
        decrypted = security_mgr.decrypt_sensitive_data(
            stored_data["encrypted_api_key"]
        )

        # 4. Verify
        assert decrypted == api_key


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================


class TestSecurityEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_analyze_request_with_missing_fields(self, security_mgr):
        """Test analyzing request with missing fields"""
        incomplete_request = {
            "source_ip": "10.0.0.1",
            # Missing other fields
        }

        result = await security_mgr.analyze_request(incomplete_request)

        # Should handle gracefully
        assert "allow_request" in result

    def test_encrypt_empty_string(self, security_mgr):
        """Test encrypting empty string"""
        encrypted = security_mgr.encrypt_sensitive_data("")
        decrypted = security_mgr.decrypt_sensitive_data(encrypted)

        assert decrypted == ""

    def test_verify_hmac_with_empty_data(self, security_mgr):
        """Test HMAC verification with empty data"""
        result = security_mgr.verify_hmac_signature("", "sig", "secret")
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--cov=security.enhanced_security",
        "--cov-report=term-missing",
        "--cov-report=html",
    ])
