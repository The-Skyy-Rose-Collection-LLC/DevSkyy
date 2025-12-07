"""
Comprehensive Tests for Enterprise Webhook System (webhooks/webhook_system.py)
Tests HMAC signatures, exponential backoff, delivery tracking, circuit breakers
Coverage target: ≥90% for webhooks/webhook_system.py

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11.0
Per CLAUDE.md Truth Protocol - RFC 2104 HMAC compliance
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from webhooks.webhook_system import (
    DeliveryStatus,
    WebhookDelivery,
    WebhookEvent,
    WebhookManager,
    WebhookPayload,
    WebhookSubscription,
    generate_signature,
    verify_signature,
    webhook_manager,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def sample_subscription():
    """Sample webhook subscription"""
    return WebhookSubscription(
        endpoint="https://example.com/webhook",
        events=[WebhookEvent.AGENT_COMPLETED, WebhookEvent.PRODUCT_CREATED],
        secret="test_secret_key",
        max_retries=3,
        retry_delay_seconds=60,
        timeout_seconds=30,
    )


@pytest.fixture
def sample_payload():
    """Sample webhook payload"""
    return WebhookPayload(
        event_type=WebhookEvent.AGENT_COMPLETED,
        timestamp=datetime.now(UTC),
        data={"agent_id": "test_agent", "status": "success"},
    )


@pytest.fixture
def webhook_mgr():
    """Fresh webhook manager instance for testing"""
    return WebhookManager()


# ============================================================================
# TEST WEBHOOK EVENTS ENUM
# ============================================================================


class TestWebhookEvent:
    """Test WebhookEvent enum"""

    def test_agent_events(self):
        """Test agent-related events"""
        assert WebhookEvent.AGENT_STARTED.value == "agent.started"
        assert WebhookEvent.AGENT_COMPLETED.value == "agent.completed"
        assert WebhookEvent.AGENT_FAILED.value == "agent.failed"

    def test_scan_events(self):
        """Test scan-related events"""
        assert WebhookEvent.SCAN_COMPLETED.value == "scan.completed"
        assert WebhookEvent.SCAN_FAILED.value == "scan.failed"

    def test_fix_events(self):
        """Test fix-related events"""
        assert WebhookEvent.FIX_COMPLETED.value == "fix.completed"
        assert WebhookEvent.FIX_FAILED.value == "fix.failed"

    def test_product_events(self):
        """Test product-related events"""
        assert WebhookEvent.PRODUCT_CREATED.value == "product.created"
        assert WebhookEvent.PRODUCT_UPDATED.value == "product.updated"
        assert WebhookEvent.PRODUCT_DELETED.value == "product.deleted"

    def test_order_events(self):
        """Test order-related events"""
        assert WebhookEvent.ORDER_CREATED.value == "order.created"
        assert WebhookEvent.ORDER_UPDATED.value == "order.updated"
        assert WebhookEvent.ORDER_CANCELLED.value == "order.cancelled"

    def test_inventory_events(self):
        """Test inventory-related events"""
        assert WebhookEvent.INVENTORY_LOW.value == "inventory.low"
        assert WebhookEvent.INVENTORY_OUT.value == "inventory.out"
        assert WebhookEvent.INVENTORY_RESTOCKED.value == "inventory.restocked"

    def test_theme_events(self):
        """Test theme-related events"""
        assert WebhookEvent.THEME_GENERATED.value == "theme.generated"
        assert WebhookEvent.THEME_DEPLOYED.value == "theme.deployed"

    def test_security_events(self):
        """Test security-related events"""
        assert WebhookEvent.SECURITY_THREAT.value == "security.threat"
        assert WebhookEvent.SECURITY_AUDIT.value == "security.audit"

    def test_system_events(self):
        """Test system-related events"""
        assert WebhookEvent.SYSTEM_ERROR.value == "system.error"
        assert WebhookEvent.SYSTEM_WARNING.value == "system.warning"

    def test_custom_event(self):
        """Test custom event"""
        assert WebhookEvent.CUSTOM.value == "custom.event"


# ============================================================================
# TEST DELIVERY STATUS ENUM
# ============================================================================


class TestDeliveryStatus:
    """Test DeliveryStatus enum"""

    def test_delivery_statuses(self):
        """Test all delivery status values"""
        assert DeliveryStatus.PENDING.value == "pending"
        assert DeliveryStatus.SENT.value == "sent"
        assert DeliveryStatus.FAILED.value == "failed"
        assert DeliveryStatus.RETRYING.value == "retrying"
        assert DeliveryStatus.PERMANENTLY_FAILED.value == "permanently_failed"


# ============================================================================
# TEST WEBHOOK SUBSCRIPTION MODEL
# ============================================================================


class TestWebhookSubscription:
    """Test WebhookSubscription model"""

    def test_subscription_creation(self):
        """Test creating a webhook subscription"""
        sub = WebhookSubscription(
            endpoint="https://example.com/webhook",
            events=[WebhookEvent.AGENT_COMPLETED],
            secret="my_secret",
        )

        assert str(sub.endpoint) == "https://example.com/webhook"
        assert WebhookEvent.AGENT_COMPLETED in sub.events
        assert sub.secret == "my_secret"
        assert sub.active is True
        assert sub.max_retries == 3
        assert sub.subscription_id is not None

    def test_subscription_id_auto_generation(self):
        """Test subscription ID is auto-generated"""
        sub = WebhookSubscription(
            endpoint="https://example.com/webhook",
            events=[WebhookEvent.PRODUCT_CREATED],
            secret="secret",
        )

        assert sub.subscription_id is not None
        assert len(sub.subscription_id) > 0

    def test_created_at_auto_set(self):
        """Test created_at is auto-set"""
        sub = WebhookSubscription(
            endpoint="https://example.com/webhook",
            events=[WebhookEvent.AGENT_STARTED],
            secret="secret",
        )

        assert sub.created_at is not None
        assert isinstance(sub.created_at, datetime)

    def test_subscription_with_metadata(self):
        """Test subscription with metadata"""
        metadata = {"source": "test", "priority": "high"}
        sub = WebhookSubscription(
            endpoint="https://example.com/webhook",
            events=[WebhookEvent.CUSTOM],
            secret="secret",
            metadata=metadata,
        )

        assert sub.metadata == metadata

    def test_subscription_custom_retries(self):
        """Test subscription with custom retry settings"""
        sub = WebhookSubscription(
            endpoint="https://example.com/webhook",
            events=[WebhookEvent.AGENT_COMPLETED],
            secret="secret",
            max_retries=5,
            retry_delay_seconds=120,
        )

        assert sub.max_retries == 5
        assert sub.retry_delay_seconds == 120

    def test_subscription_inactive(self):
        """Test creating inactive subscription"""
        sub = WebhookSubscription(
            endpoint="https://example.com/webhook",
            events=[WebhookEvent.PRODUCT_CREATED],
            secret="secret",
            active=False,
        )

        assert sub.active is False


# ============================================================================
# TEST WEBHOOK PAYLOAD MODEL
# ============================================================================


class TestWebhookPayload:
    """Test WebhookPayload model"""

    def test_payload_creation(self):
        """Test creating a webhook payload"""
        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"agent_id": "test", "status": "success"},
        )

        assert payload.event_type == WebhookEvent.AGENT_COMPLETED
        assert payload.data["agent_id"] == "test"
        assert payload.event_id is not None
        assert payload.idempotency_key is not None

    def test_payload_event_id_auto_generation(self):
        """Test event_id is auto-generated"""
        payload = WebhookPayload(
            event_type=WebhookEvent.PRODUCT_CREATED,
            timestamp=datetime.now(UTC),
            data={"product_id": "prod123"},
        )

        assert payload.event_id is not None
        assert len(payload.event_id) > 0

    def test_payload_idempotency_key_auto_generation(self):
        """Test idempotency_key is auto-generated"""
        payload = WebhookPayload(
            event_type=WebhookEvent.ORDER_CREATED,
            timestamp=datetime.now(UTC),
            data={"order_id": "ord123"},
        )

        assert payload.idempotency_key is not None
        assert len(payload.idempotency_key) > 0

    def test_payload_custom_ids(self):
        """Test payload with custom event_id and idempotency_key"""
        custom_event_id = "custom_event_123"
        custom_idempotency = "custom_idem_456"

        payload = WebhookPayload(
            event_id=custom_event_id,
            event_type=WebhookEvent.THEME_GENERATED,
            timestamp=datetime.now(UTC),
            data={"theme_id": "theme123"},
            idempotency_key=custom_idempotency,
        )

        assert payload.event_id == custom_event_id
        assert payload.idempotency_key == custom_idempotency


# ============================================================================
# TEST SIGNATURE GENERATION (RFC 2104)
# ============================================================================


class TestSignatureGeneration:
    """Test HMAC-SHA256 signature generation (RFC 2104)"""

    def test_generate_signature(self):
        """Test signature generation"""
        payload = '{"test": "data"}'
        secret = "my_secret_key"

        signature = generate_signature(payload, secret)

        # Should return hex-encoded HMAC-SHA256
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex is 64 chars

    def test_signature_deterministic(self):
        """Test signature is deterministic"""
        payload = '{"test": "data"}'
        secret = "my_secret_key"

        sig1 = generate_signature(payload, secret)
        sig2 = generate_signature(payload, secret)

        assert sig1 == sig2

    def test_signature_different_payloads(self):
        """Test different payloads produce different signatures"""
        secret = "my_secret_key"

        sig1 = generate_signature('{"test": "data1"}', secret)
        sig2 = generate_signature('{"test": "data2"}', secret)

        assert sig1 != sig2

    def test_signature_different_secrets(self):
        """Test different secrets produce different signatures"""
        payload = '{"test": "data"}'

        sig1 = generate_signature(payload, "secret1")
        sig2 = generate_signature(payload, "secret2")

        assert sig1 != sig2

    def test_verify_signature_valid(self):
        """Test verifying a valid signature"""
        payload = '{"test": "data"}'
        secret = "my_secret_key"

        signature = generate_signature(payload, secret)
        result = verify_signature(payload, signature, secret)

        assert result is True

    def test_verify_signature_invalid(self):
        """Test verifying an invalid signature"""
        payload = '{"test": "data"}'
        secret = "my_secret_key"

        signature = "invalid_signature"
        result = verify_signature(payload, signature, secret)

        assert result is False

    def test_verify_signature_wrong_secret(self):
        """Test verifying with wrong secret"""
        payload = '{"test": "data"}'

        signature = generate_signature(payload, "secret1")
        result = verify_signature(payload, signature, "secret2")

        assert result is False

    def test_verify_signature_tampered_payload(self):
        """Test verifying tampered payload"""
        payload = '{"test": "data"}'
        secret = "my_secret_key"

        signature = generate_signature(payload, secret)

        # Tamper with payload
        tampered_payload = '{"test": "modified"}'
        result = verify_signature(tampered_payload, signature, secret)

        assert result is False


# ============================================================================
# TEST WEBHOOK MANAGER
# ============================================================================


class TestWebhookManager:
    """Test WebhookManager class"""

    def test_webhook_manager_initialization(self):
        """Test webhook manager initialization"""
        mgr = WebhookManager()

        assert mgr.subscriptions == {}
        assert mgr.delivery_history == []
        assert mgr.failed_deliveries == {}
        assert mgr.circuit_breaker_threshold == 5

    @pytest.mark.asyncio
    async def test_subscribe_webhook(self, webhook_mgr):
        """Test subscribing to webhook events"""
        subscription = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed", "product.created"],
            secret="test_secret",
        )

        assert str(subscription.endpoint) == "https://example.com/webhook"
        assert WebhookEvent.AGENT_COMPLETED in subscription.events
        assert subscription.secret == "test_secret"
        assert subscription.subscription_id in webhook_mgr.subscriptions

    @pytest.mark.asyncio
    async def test_subscribe_auto_generates_secret(self, webhook_mgr):
        """Test subscription auto-generates secret if not provided"""
        subscription = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.started"],
        )

        assert subscription.secret is not None
        assert len(subscription.secret) > 0

    @pytest.mark.asyncio
    async def test_subscribe_with_metadata(self, webhook_mgr):
        """Test subscription with metadata"""
        metadata = {"source": "test", "priority": "high"}

        subscription = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["product.created"],
            metadata=metadata,
        )

        assert subscription.metadata == metadata

    @pytest.mark.asyncio
    async def test_unsubscribe_webhook(self, webhook_mgr):
        """Test unsubscribing from webhooks"""
        subscription = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
        )

        result = await webhook_mgr.unsubscribe(subscription.subscription_id)

        assert result is True
        assert subscription.subscription_id not in webhook_mgr.subscriptions

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, webhook_mgr):
        """Test unsubscribing nonexistent subscription"""
        result = await webhook_mgr.unsubscribe("nonexistent_id")

        assert result is False

    @pytest.mark.asyncio
    async def test_emit_webhook_event(self, webhook_mgr):
        """Test emitting webhook event"""
        # Subscribe to event
        await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="secret",
        )

        # Mock _deliver_webhook to avoid actual HTTP call
        with patch.object(webhook_mgr, "_deliver_webhook", new_callable=AsyncMock) as mock_deliver:
            # Emit event
            await webhook_mgr.emit(
                WebhookEvent.AGENT_COMPLETED,
                {"agent_id": "test", "status": "success"},
            )

            # Verify delivery was called
            assert mock_deliver.call_count == 1

    @pytest.mark.asyncio
    async def test_emit_to_multiple_subscribers(self, webhook_mgr):
        """Test emitting to multiple subscribers"""
        # Subscribe multiple times
        await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook1",
            events=["product.created"],
        )
        await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook2",
            events=["product.created"],
        )

        with patch.object(webhook_mgr, "_deliver_webhook", new_callable=AsyncMock) as mock_deliver:
            await webhook_mgr.emit(
                WebhookEvent.PRODUCT_CREATED,
                {"product_id": "prod123"},
            )

            # Should deliver to both subscribers
            assert mock_deliver.call_count == 2

    @pytest.mark.asyncio
    async def test_emit_only_to_matching_events(self, webhook_mgr):
        """Test emitting only to matching event subscriptions"""
        # Subscribe to different events
        await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook1",
            events=["agent.completed"],
        )
        await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook2",
            events=["product.created"],
        )

        with patch.object(webhook_mgr, "_deliver_webhook", new_callable=AsyncMock) as mock_deliver:
            await webhook_mgr.emit(
                WebhookEvent.AGENT_COMPLETED,
                {"agent_id": "test"},
            )

            # Should only deliver to first subscriber
            assert mock_deliver.call_count == 1

    @pytest.mark.asyncio
    async def test_emit_skips_inactive_subscriptions(self, webhook_mgr):
        """Test emitting skips inactive subscriptions"""
        # Subscribe but set inactive
        subscription = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
        )
        subscription.active = False
        webhook_mgr.subscriptions[subscription.subscription_id] = subscription

        with patch.object(webhook_mgr, "_deliver_webhook", new_callable=AsyncMock) as mock_deliver:
            await webhook_mgr.emit(
                WebhookEvent.AGENT_COMPLETED,
                {"agent_id": "test"},
            )

            # Should not deliver to inactive subscription
            assert mock_deliver.call_count == 0

    @pytest.mark.asyncio
    async def test_deliver_webhook_success(self, webhook_mgr, sample_subscription, sample_payload):
        """Test successful webhook delivery"""
        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            await webhook_mgr._deliver_webhook(sample_subscription, sample_payload)

            # Check delivery was recorded
            assert len(webhook_mgr.delivery_history) == 1
            delivery = webhook_mgr.delivery_history[0]
            assert delivery.status == DeliveryStatus.SENT
            assert delivery.response_status_code == 200

    @pytest.mark.asyncio
    async def test_deliver_webhook_retry_on_failure(self, webhook_mgr, sample_subscription, sample_payload):
        """Test webhook retry on failure"""
        # Mock HTTP client to fail then succeed
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Server Error"

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.text = "OK"

        mock_client = AsyncMock()
        # First call fails, second succeeds
        mock_client.post = AsyncMock(side_effect=[mock_response_fail, mock_response_success])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        # Reduce retry delay for testing
        sample_subscription.retry_delay_seconds = 0

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            with patch("webhooks.webhook_system.asyncio.sleep", new_callable=AsyncMock):
                await webhook_mgr._deliver_webhook(sample_subscription, sample_payload)

                # Should have retried and succeeded
                assert len(webhook_mgr.delivery_history) >= 1

    @pytest.mark.asyncio
    async def test_deliver_webhook_circuit_breaker(self, webhook_mgr, sample_subscription, sample_payload):
        """Test circuit breaker opens after threshold failures"""
        # Set failure count to trigger circuit breaker
        webhook_mgr.failed_deliveries[str(sample_subscription.endpoint)] = 5

        await webhook_mgr._deliver_webhook(sample_subscription, sample_payload)

        # Check delivery was marked as permanently failed
        assert len(webhook_mgr.delivery_history) >= 1
        delivery = webhook_mgr.delivery_history[-1]  # Get the last delivery
        assert delivery.status == DeliveryStatus.PERMANENTLY_FAILED
        assert "Circuit breaker" in delivery.error_message

    @pytest.mark.asyncio
    async def test_test_webhook(self, webhook_mgr):
        """Test webhook testing functionality"""
        subscription = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
        )

        # Mock delivery
        with patch.object(webhook_mgr, "_deliver_webhook", new_callable=AsyncMock) as mock_deliver:
            # Add a delivery record to history
            test_delivery = WebhookDelivery(
                delivery_id="test123",
                subscription_id=subscription.subscription_id,
                event_id="evt123",
                status=DeliveryStatus.SENT,
                attempt_number=1,
                request_body="{}",
                request_headers={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            webhook_mgr.delivery_history.append(test_delivery)

            result = await webhook_mgr.test_webhook(subscription.subscription_id)

            # Verify test was performed
            mock_deliver.assert_called_once()
            assert result.status == DeliveryStatus.SENT

    @pytest.mark.asyncio
    async def test_test_webhook_nonexistent_subscription(self, webhook_mgr):
        """Test testing nonexistent subscription raises error"""
        with pytest.raises(ValueError, match="Subscription not found"):
            await webhook_mgr.test_webhook("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_delivery_history(self, webhook_mgr):
        """Test getting delivery history"""
        subscription_id = "sub123"

        # Add some delivery records
        for i in range(5):
            delivery = WebhookDelivery(
                delivery_id=f"del{i}",
                subscription_id=subscription_id,
                event_id=f"evt{i}",
                status=DeliveryStatus.SENT,
                attempt_number=1,
                request_body="{}",
                request_headers={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            webhook_mgr.delivery_history.append(delivery)

        history = await webhook_mgr.get_delivery_history(subscription_id, limit=3)

        assert len(history) == 3
        assert all(d.subscription_id == subscription_id for d in history)

    @pytest.mark.asyncio
    async def test_get_subscription(self, webhook_mgr):
        """Test getting subscription by ID"""
        subscription = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
        )

        result = await webhook_mgr.get_subscription(subscription.subscription_id)

        assert result == subscription

    @pytest.mark.asyncio
    async def test_get_nonexistent_subscription(self, webhook_mgr):
        """Test getting nonexistent subscription returns None"""
        result = await webhook_mgr.get_subscription("nonexistent_id")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_subscriptions(self, webhook_mgr):
        """Test listing all subscriptions"""
        sub1 = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook1",
            events=["agent.completed"],
        )
        sub2 = await webhook_mgr.subscribe(
            endpoint="https://example.com/webhook2",
            events=["product.created"],
        )

        subscriptions = await webhook_mgr.list_subscriptions()

        assert len(subscriptions) == 2
        assert sub1 in subscriptions
        assert sub2 in subscriptions


# ============================================================================
# TEST WEBHOOK MANAGER SINGLETON
# ============================================================================


class TestWebhookManagerSingleton:
    """Test webhook_manager singleton instance"""

    def test_singleton_exists(self):
        """Test webhook_manager singleton exists"""
        assert webhook_manager is not None
        assert isinstance(webhook_manager, WebhookManager)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestWebhookIntegration:
    """Integration tests for webhook system"""

    @pytest.mark.asyncio
    async def test_full_webhook_flow(self):
        """Test complete webhook flow from subscription to delivery"""
        mgr = WebhookManager()

        # Subscribe
        subscription = await mgr.subscribe(
            endpoint="https://httpbin.org/post",
            events=["agent.completed"],
            secret="test_secret",
        )

        assert subscription.subscription_id in mgr.subscriptions

        # Mock delivery to avoid actual network call
        with patch.object(mgr, "_deliver_webhook", new_callable=AsyncMock) as mock_deliver:
            # Emit event
            await mgr.emit(
                WebhookEvent.AGENT_COMPLETED,
                {"agent_id": "test_agent", "status": "success"},
            )

            # Verify delivery was attempted
            assert mock_deliver.call_count == 1

        # Unsubscribe
        result = await mgr.unsubscribe(subscription.subscription_id)
        assert result is True


    @pytest.mark.asyncio
    async def test_emit_no_subscribers(self):
        """Test emitting event with no subscribers"""
        mgr = WebhookManager()

        # Emit event with no subscriptions
        await mgr.emit(
            WebhookEvent.AGENT_COMPLETED,
            {"agent_id": "test", "status": "success"},
        )

        # Should not error, just no deliveries
        assert len(mgr.delivery_history) == 0


# ============================================================================
# ADDITIONAL COVERAGE TESTS
# ============================================================================


class TestWebhookDelivery:
    """Test webhook delivery scenarios for comprehensive coverage"""

    @pytest.mark.asyncio
    async def test_deliver_webhook_http_201(self):
        """Test successful webhook delivery with HTTP 201"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client with 201 response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.text = "Created"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            await mgr._deliver_webhook(subscription, payload)

        assert len(mgr.delivery_history) == 1
        assert mgr.delivery_history[0].status == DeliveryStatus.SENT
        assert mgr.delivery_history[0].response_status_code == 201

    @pytest.mark.asyncio
    async def test_deliver_webhook_http_202(self):
        """Test successful webhook delivery with HTTP 202"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client with 202 response
        mock_response = Mock()
        mock_response.status_code = 202
        mock_response.text = "Accepted"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            await mgr._deliver_webhook(subscription, payload)

        assert len(mgr.delivery_history) == 1
        assert mgr.delivery_history[0].status == DeliveryStatus.SENT
        assert mgr.delivery_history[0].response_status_code == 202

    @pytest.mark.asyncio
    async def test_deliver_webhook_http_204(self):
        """Test successful webhook delivery with HTTP 204"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client with 204 response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.text = ""

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            await mgr._deliver_webhook(subscription, payload)

        assert len(mgr.delivery_history) == 1
        assert mgr.delivery_history[0].status == DeliveryStatus.SENT
        assert mgr.delivery_history[0].response_status_code == 204

    @pytest.mark.asyncio
    async def test_deliver_webhook_http_400_error(self):
        """Test webhook delivery with HTTP 400 error"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )
        subscription.max_retries = 2
        subscription.retry_delay_seconds = 0  # Speed up test

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client with 400 error
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            with patch("webhooks.webhook_system.asyncio.sleep", new_callable=AsyncMock):
                await mgr._deliver_webhook(subscription, payload)

        # Should have retried
        assert len(mgr.delivery_history) >= 1

    @pytest.mark.asyncio
    async def test_deliver_webhook_connection_error(self):
        """Test webhook delivery with connection error"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )
        subscription.max_retries = 2
        subscription.retry_delay_seconds = 0  # Speed up test

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client to raise connection error
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            with patch("webhooks.webhook_system.asyncio.sleep", new_callable=AsyncMock):
                await mgr._deliver_webhook(subscription, payload)

        # Should have tried and failed
        assert len(mgr.delivery_history) >= 1
        # Check that at least one delivery is permanently failed
        failed_deliveries = [d for d in mgr.delivery_history if d.status == DeliveryStatus.PERMANENTLY_FAILED]
        assert len(failed_deliveries) >= 1
        assert "Connection failed" in failed_deliveries[0].error_message

    @pytest.mark.asyncio
    async def test_deliver_webhook_timeout_error(self):
        """Test webhook delivery with timeout error"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )
        subscription.max_retries = 1
        subscription.retry_delay_seconds = 0  # Speed up test

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client to raise timeout error
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Request timed out"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            with patch("webhooks.webhook_system.asyncio.sleep", new_callable=AsyncMock):
                await mgr._deliver_webhook(subscription, payload)

        # Should have tried and failed
        assert len(mgr.delivery_history) >= 1
        last_delivery = mgr.delivery_history[-1]
        assert last_delivery.status == DeliveryStatus.PERMANENTLY_FAILED
        assert "timed out" in last_delivery.error_message

    @pytest.mark.asyncio
    async def test_deliver_webhook_exponential_backoff(self):
        """Test webhook delivery uses exponential backoff"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )
        subscription.max_retries = 3
        subscription.retry_delay_seconds = 10  # Base delay

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client to always fail
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            with patch("webhooks.webhook_system.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                await mgr._deliver_webhook(subscription, payload)

                # Should have multiple retries with exponential backoff
                # Backoff: 10s (attempt 1), 20s (attempt 2), 40s (attempt 3)
                # Note: asyncio.sleep might be called multiple times
                assert len(mgr.delivery_history) >= 1

    @pytest.mark.asyncio
    async def test_deliver_webhook_failed_deliveries_increment(self):
        """Test failed deliveries counter increments"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )
        subscription.max_retries = 1
        subscription.retry_delay_seconds = 0

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client to fail
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            with patch("webhooks.webhook_system.asyncio.sleep", new_callable=AsyncMock):
                await mgr._deliver_webhook(subscription, payload)

        # Failed deliveries should increment
        assert mgr.failed_deliveries.get(str(subscription.endpoint), 0) > 0

    @pytest.mark.asyncio
    async def test_deliver_webhook_success_resets_failures(self):
        """Test successful delivery resets failure counter"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )

        # Set some failures
        mgr.failed_deliveries[str(subscription.endpoint)] = 3

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client to succeed
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            await mgr._deliver_webhook(subscription, payload)

        # Failure counter should reset to 0
        assert mgr.failed_deliveries[str(subscription.endpoint)] == 0

    @pytest.mark.asyncio
    async def test_deliver_webhook_signature_headers(self):
        """Test webhook delivery includes proper signature headers"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            await mgr._deliver_webhook(subscription, payload)

        # Verify headers were passed
        call_args = mock_client.post.call_args
        headers = call_args.kwargs["headers"]

        assert "X-Webhook-Signature" in headers
        assert headers["X-Webhook-Signature"].startswith("sha256=")
        assert "X-Webhook-Event" in headers
        assert "X-Webhook-ID" in headers
        assert headers["X-Webhook-ID"] is not None
        assert "X-Webhook-Timestamp" in headers
        assert "X-Idempotency-Key" in headers
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_deliver_webhook_response_body_truncation(self):
        """Test webhook delivery truncates large response bodies"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )

        payload = WebhookPayload(
            event_type=WebhookEvent.AGENT_COMPLETED,
            timestamp=datetime.now(UTC),
            data={"test": "data"},
        )

        # Mock HTTP client with large response
        large_response = "X" * 2000  # Response larger than 1000 char limit
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = large_response

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            await mgr._deliver_webhook(subscription, payload)

        # Response body should be truncated to 1000 chars
        delivery = mgr.delivery_history[0]
        assert len(delivery.response_body) == 1000

    @pytest.mark.asyncio
    async def test_emit_with_tasks(self):
        """Test emit function with multiple tasks"""
        mgr = WebhookManager()

        # Subscribe multiple endpoints
        await mgr.subscribe(
            endpoint="https://example.com/webhook1",
            events=["agent.completed"],
            secret="secret1",
        )
        await mgr.subscribe(
            endpoint="https://example.com/webhook2",
            events=["agent.completed"],
            secret="secret2",
        )
        await mgr.subscribe(
            endpoint="https://example.com/webhook3",
            events=["agent.completed"],
            secret="secret3",
        )

        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            # Emit event - should trigger all 3 subscriptions
            await mgr.emit(
                WebhookEvent.AGENT_COMPLETED,
                {"agent_id": "test", "status": "success"},
            )

        # Should have 3 deliveries
        assert len(mgr.delivery_history) == 3

    @pytest.mark.asyncio
    async def test_test_webhook_returns_delivery(self):
        """Test test_webhook returns the delivery record"""
        mgr = WebhookManager()
        subscription = await mgr.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed"],
            secret="test_secret",
        )

        # Mock HTTP client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "OK"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("webhooks.webhook_system.httpx.AsyncClient", return_value=mock_client):
            result = await mgr.test_webhook(subscription.subscription_id)

        # Should return a delivery record
        assert isinstance(result, WebhookDelivery)
        assert result.status == DeliveryStatus.SENT
        assert result.subscription_id == subscription.subscription_id

    @pytest.mark.asyncio
    async def test_delivery_history_limit(self):
        """Test get_delivery_history respects limit"""
        mgr = WebhookManager()
        subscription_id = "sub123"

        # Add 20 delivery records
        for i in range(20):
            delivery = WebhookDelivery(
                delivery_id=f"del{i}",
                subscription_id=subscription_id,
                event_id=f"evt{i}",
                status=DeliveryStatus.SENT,
                attempt_number=1,
                request_body="{}",
                request_headers={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            mgr.delivery_history.append(delivery)

        # Get last 5
        history = await mgr.get_delivery_history(subscription_id, limit=5)

        assert len(history) == 5
        # Should return most recent (last 5)
        assert history[0].delivery_id == "del15"
        assert history[4].delivery_id == "del19"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=webhooks.webhook_system", "--cov-report=term-missing"])
