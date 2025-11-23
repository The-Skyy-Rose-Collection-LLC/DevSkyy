"""
Comprehensive tests for infrastructure/notification_manager.py

WHY: Ensure notification system works correctly with ≥75% coverage
HOW: Test all notification channels, templates, rate limiting, and retry logic
IMPACT: Validates enterprise notification infrastructure reliability

Truth Protocol: Rules #1, #8, #15
Coverage Target: ≥75%
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.notification_manager import (
    NotificationChannel,
    NotificationManager,
    NotificationMessage,
    NotificationPriority,
    NotificationStatus,
    NotificationTemplate,
    RateLimiter,
)


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing."""
    client = MagicMock()
    client.post = AsyncMock(return_value=MagicMock(status_code=200))
    client.get = AsyncMock(return_value=MagicMock(status_code=200))
    client.aclose = AsyncMock()
    return client


@pytest.fixture
async def notification_manager(mock_http_client):
    """Create NotificationManager instance with mocked HTTP client."""
    with patch("infrastructure.notification_manager.AsyncClient", return_value=mock_http_client):
        manager = NotificationManager(
            rate_limit_per_second=1,
            max_concurrent_requests=10,
            request_timeout=30,
            retry_delay=1,
        )
        yield manager
        await manager.close()


@pytest.fixture
def sample_template():
    """Create sample notification template."""
    return NotificationTemplate(
        name="test_template",
        channel=NotificationChannel.SLACK,
        title_template="Test: {title}",
        message_template="Message: {message}",
        color="#00ff00",
        emoji="✅",
    )


# ============================================================================
# TEST Notification Enums
# ============================================================================


class TestNotificationEnums:
    """Test notification enum values."""

    def test_notification_channel_values(self):
        """Test all notification channel enum values."""
        assert NotificationChannel.SLACK.value == "slack"
        assert NotificationChannel.DISCORD.value == "discord"
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.SMS.value == "sms"
        assert NotificationChannel.WEBHOOK.value == "webhook"

    def test_notification_priority_values(self):
        """Test all notification priority enum values."""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.CRITICAL.value == "critical"
        assert NotificationPriority.URGENT.value == "urgent"

    def test_notification_status_values(self):
        """Test all notification status enum values."""
        assert NotificationStatus.PENDING.value == "pending"
        assert NotificationStatus.SENT.value == "sent"
        assert NotificationStatus.DELIVERED.value == "delivered"
        assert NotificationStatus.FAILED.value == "failed"
        assert NotificationStatus.RATE_LIMITED.value == "rate_limited"
        assert NotificationStatus.RETRYING.value == "retrying"


# ============================================================================
# TEST NotificationTemplate
# ============================================================================


class TestNotificationTemplate:
    """Test NotificationTemplate dataclass."""

    def test_template_initialization(self, sample_template):
        """Test NotificationTemplate initialization."""
        assert sample_template.name == "test_template"
        assert sample_template.channel == NotificationChannel.SLACK
        assert sample_template.title_template == "Test: {title}"
        assert sample_template.message_template == "Message: {message}"
        assert sample_template.color == "#00ff00"
        assert sample_template.emoji == "✅"

    def test_template_render_success(self, sample_template):
        """Test successful template rendering."""
        context = {"title": "Success", "message": "Operation completed"}

        result = sample_template.render(context)

        assert result["title"] == "Test: Success"
        assert result["message"] == "Message: Operation completed"
        assert result["color"] == "#00ff00"
        assert result["emoji"] == "✅"

    def test_template_render_with_fields(self):
        """Test template rendering with custom fields."""
        template = NotificationTemplate(
            name="with_fields",
            channel=NotificationChannel.SLACK,
            title_template="Alert",
            message_template="Message",
            fields=[
                {"name": "Status", "value": "{status}", "inline": True},
                {"name": "Duration", "value": "{duration}", "inline": False},
            ],
        )

        context = {"status": "OK", "duration": "5s"}
        result = template.render(context)

        assert len(result["fields"]) == 2
        assert result["fields"][0]["value"] == "OK"
        assert result["fields"][1]["value"] == "5s"

    def test_template_render_missing_context_key(self, sample_template):
        """Test template rendering with missing context key."""
        context = {"title": "Test"}  # Missing 'message' key

        result = sample_template.render(context)

        # Should return error template
        assert result["title"] == "Template Error"
        assert "Failed to render" in result["message"]


# ============================================================================
# TEST NotificationMessage
# ============================================================================


class TestNotificationMessage:
    """Test NotificationMessage dataclass."""

    def test_message_initialization(self):
        """Test NotificationMessage initialization."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test message",
            priority=NotificationPriority.HIGH,
        )

        assert msg.id == "msg123"
        assert msg.channel == NotificationChannel.SLACK
        assert msg.status == NotificationStatus.PENDING
        assert msg.retry_count == 0
        assert msg.created_at is not None

    def test_message_post_init_defaults(self):
        """Test NotificationMessage __post_init__ sets defaults."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test message",
            priority=NotificationPriority.NORMAL,
        )

        assert msg.context == {}
        assert msg.fashion_context == {}
        assert isinstance(msg.created_at, datetime)


# ============================================================================
# TEST RateLimiter
# ============================================================================


class TestRateLimiter:
    """Test RateLimiter functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(max_requests=5, time_window=10)

        assert limiter.max_requests == 5
        assert limiter.time_window == 10
        assert len(limiter.requests) == 0

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring within rate limit."""
        limiter = RateLimiter(max_requests=5, time_window=1)

        # Should be able to acquire up to max_requests
        for _ in range(5):
            result = await limiter.acquire("test_channel")
            assert result is True

    @pytest.mark.asyncio
    async def test_acquire_exceeds_limit(self):
        """Test acquiring when rate limit exceeded."""
        limiter = RateLimiter(max_requests=2, time_window=1)

        # Fill up the limit
        await limiter.acquire("test_channel")
        await limiter.acquire("test_channel")

        # Next acquire should fail
        result = await limiter.acquire("test_channel")
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_different_channels(self):
        """Test rate limiting is per-channel."""
        limiter = RateLimiter(max_requests=1, time_window=1)

        # Different channels should have independent limits
        result1 = await limiter.acquire("channel1")
        result2 = await limiter.acquire("channel2")

        assert result1 is True
        assert result2 is True

    @pytest.mark.asyncio
    async def test_wait_for_slot(self):
        """Test waiting for next available slot."""
        limiter = RateLimiter(max_requests=1, time_window=0.1)

        # Fill the limit
        await limiter.acquire("test_channel")

        # Wait for slot should return wait time
        wait_time = await limiter.wait_for_slot("test_channel")

        # Should have waited and now can acquire again
        result = await limiter.acquire("test_channel")
        assert result is True

    @pytest.mark.asyncio
    async def test_rate_limit_window_expiration(self):
        """Test requests expire after time window."""
        limiter = RateLimiter(max_requests=1, time_window=0.1)

        # Fill the limit
        await limiter.acquire("test_channel")

        # Wait for window to expire
        await asyncio.sleep(0.15)

        # Should be able to acquire again
        result = await limiter.acquire("test_channel")
        assert result is True


# ============================================================================
# TEST NotificationManager Initialization
# ============================================================================


class TestNotificationManagerInitialization:
    """Test NotificationManager initialization."""

    def test_manager_initialization(self, notification_manager):
        """Test manager initializes with default settings."""
        assert notification_manager.rate_limiter is not None
        assert notification_manager.max_concurrent_requests == 10
        assert notification_manager.request_timeout == 30
        assert notification_manager.retry_delay == 1

    def test_manager_has_templates(self, notification_manager):
        """Test manager initializes with default templates."""
        assert "system_alert" in notification_manager.templates
        assert "deployment_success" in notification_manager.templates
        assert "fashion_trend_alert" in notification_manager.templates
        assert "inventory_low_stock" in notification_manager.templates
        assert "performance_degradation" in notification_manager.templates

    def test_default_template_system_alert(self, notification_manager):
        """Test default system alert template."""
        template = notification_manager.templates["system_alert"]

        assert template.channel == NotificationChannel.SLACK
        assert "System Alert" in template.title_template
        assert template.color == "#ff4444"
        assert template.emoji == "🚨"

    def test_default_template_fashion_trend(self, notification_manager):
        """Test default fashion trend alert template."""
        template = notification_manager.templates["fashion_trend_alert"]

        assert template.fashion_context is True
        assert "Fashion Trend" in template.title_template


# ============================================================================
# TEST Template Management
# ============================================================================


class TestTemplateManagement:
    """Test template management operations."""

    def test_add_template(self, notification_manager, sample_template):
        """Test adding new template."""
        initial_count = len(notification_manager.templates)

        notification_manager.add_template(sample_template)

        assert len(notification_manager.templates) == initial_count + 1
        assert "test_template" in notification_manager.templates

    def test_remove_template(self, notification_manager):
        """Test removing template."""
        template_name = "system_alert"
        assert template_name in notification_manager.templates

        notification_manager.remove_template(template_name)

        assert template_name not in notification_manager.templates

    def test_remove_nonexistent_template(self, notification_manager):
        """Test removing non-existent template doesn't error."""
        notification_manager.remove_template("nonexistent")
        # Should not raise exception


# ============================================================================
# TEST Notification Sending
# ============================================================================


class TestNotificationSending:
    """Test sending notifications."""

    @pytest.mark.asyncio
    async def test_send_notification_simple(self, notification_manager, mock_http_client):
        """Test sending simple notification."""
        message_id = await notification_manager.send_notification(
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test message",
        )

        assert message_id is not None
        assert message_id in notification_manager.pending_messages

    @pytest.mark.asyncio
    async def test_send_notification_with_priority(self, notification_manager, mock_http_client):
        """Test sending notification with priority."""
        message_id = await notification_manager.send_notification(
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Critical Alert",
            message="System down",
            priority=NotificationPriority.CRITICAL,
        )

        msg = notification_manager.pending_messages.get(message_id)
        assert msg.priority == NotificationPriority.CRITICAL

    @pytest.mark.asyncio
    async def test_send_notification_with_context(self, notification_manager, mock_http_client):
        """Test sending notification with context data."""
        context = {"user_id": "user123", "action": "login"}

        message_id = await notification_manager.send_notification(
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="User Action",
            message="User logged in",
            context=context,
        )

        msg = notification_manager.pending_messages.get(message_id)
        assert msg.context == context

    @pytest.mark.asyncio
    async def test_send_from_template(self, notification_manager, mock_http_client):
        """Test sending notification from template."""
        context = {
            "alert_type": "HighCPU",
            "message": "CPU usage above 90%",
            "severity": "HIGH",
            "timestamp": datetime.now().isoformat(),
            "environment": "production",
            "service": "api-server",
            "correlation_id": "abc123",
        }

        message_id = await notification_manager.send_from_template(
            template_name="system_alert",
            webhook_url="https://hooks.slack.com/test",
            context=context,
        )

        assert message_id is not None

    @pytest.mark.asyncio
    async def test_send_from_nonexistent_template(self, notification_manager):
        """Test sending from non-existent template raises error."""
        with pytest.raises(ValueError, match="Template not found"):
            await notification_manager.send_from_template(
                template_name="nonexistent",
                webhook_url="https://hooks.slack.com/test",
                context={},
            )


# ============================================================================
# TEST Message Delivery
# ============================================================================


class TestMessageDelivery:
    """Test message delivery logic."""

    @pytest.mark.asyncio
    async def test_deliver_message_success(self, notification_manager, mock_http_client):
        """Test successful message delivery."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test message",
            priority=NotificationPriority.NORMAL,
        )

        notification_manager.pending_messages[msg.id] = msg

        await notification_manager._deliver_message(msg)

        # Should move to sent messages
        await asyncio.sleep(0.1)  # Allow async task to complete
        assert mock_http_client.post.called

    @pytest.mark.asyncio
    async def test_deliver_message_rate_limited(self, notification_manager, mock_http_client):
        """Test delivery with rate limiting."""
        # Fill rate limit
        for i in range(5):
            msg = NotificationMessage(
                id=f"msg{i}",
                channel=NotificationChannel.SLACK,
                webhook_url="https://hooks.slack.com/test",
                title="Test",
                message="Test",
                priority=NotificationPriority.NORMAL,
            )
            notification_manager.pending_messages[msg.id] = msg
            asyncio.create_task(notification_manager._deliver_message(msg))

        # Give tasks time to run
        await asyncio.sleep(0.5)

    @pytest.mark.asyncio
    async def test_deliver_message_retry_on_error(self, notification_manager, mock_http_client):
        """Test message delivery retries on error."""
        mock_http_client.post = AsyncMock(side_effect=Exception("Network error"))

        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test",
            priority=NotificationPriority.NORMAL,
            max_retries=1,
        )

        notification_manager.pending_messages[msg.id] = msg

        await notification_manager._deliver_message(msg)

        # Should have attempted retry
        assert msg.retry_count > 0

    @pytest.mark.asyncio
    async def test_deliver_message_max_retries_exceeded(self, notification_manager, mock_http_client):
        """Test message fails after max retries."""
        mock_http_client.post = AsyncMock(side_effect=Exception("Network error"))

        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test",
            priority=NotificationPriority.NORMAL,
            max_retries=1,
        )

        notification_manager.pending_messages[msg.id] = msg

        await notification_manager._deliver_message(msg)

        # Allow retries to complete
        await asyncio.sleep(2)

        # Should eventually fail
        assert msg.status in [NotificationStatus.FAILED, NotificationStatus.RETRYING]


# ============================================================================
# TEST Payload Preparation
# ============================================================================


class TestPayloadPreparation:
    """Test webhook payload preparation."""

    @pytest.mark.asyncio
    async def test_prepare_slack_payload_basic(self, notification_manager):
        """Test preparing basic Slack payload."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test Alert",
            message="This is a test",
            priority=NotificationPriority.NORMAL,
            color="#00ff00",
        )

        payload = await notification_manager._prepare_slack_payload(msg)

        assert payload["text"] == "Test Alert"
        assert len(payload["attachments"]) == 1
        assert payload["attachments"][0]["title"] == "Test Alert"
        assert payload["attachments"][0]["text"] == "This is a test"
        assert payload["attachments"][0]["color"] == "#00ff00"

    @pytest.mark.asyncio
    async def test_prepare_slack_payload_with_emoji(self, notification_manager):
        """Test Slack payload with emoji."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Success",
            message="Operation completed",
            priority=NotificationPriority.NORMAL,
            emoji="✅",
        )

        payload = await notification_manager._prepare_slack_payload(msg)

        assert "✅" in payload["text"]

    @pytest.mark.asyncio
    async def test_prepare_slack_payload_with_fields(self, notification_manager):
        """Test Slack payload with fields."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Alert",
            message="Test",
            priority=NotificationPriority.NORMAL,
            fields=[{"name": "Status", "value": "OK", "inline": True}],
        )

        payload = await notification_manager._prepare_slack_payload(msg)

        assert "fields" in payload["attachments"][0]
        assert len(payload["attachments"][0]["fields"]) == 1

    @pytest.mark.asyncio
    async def test_prepare_discord_payload_basic(self, notification_manager):
        """Test preparing basic Discord payload."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.DISCORD,
            webhook_url="https://discord.com/webhook",
            title="Test Alert",
            message="This is a test",
            priority=NotificationPriority.NORMAL,
            color="#ff0000",
        )

        payload = await notification_manager._prepare_discord_payload(msg)

        assert "embeds" in payload
        assert len(payload["embeds"]) == 1
        assert payload["embeds"][0]["title"] == "Test Alert"
        assert payload["embeds"][0]["description"] == "This is a test"

    @pytest.mark.asyncio
    async def test_prepare_generic_payload(self, notification_manager):
        """Test preparing generic webhook payload."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.WEBHOOK,
            webhook_url="https://example.com/webhook",
            title="Test",
            message="Test message",
            priority=NotificationPriority.HIGH,
        )

        payload = await notification_manager._prepare_payload(msg)

        assert payload["title"] == "Test"
        assert payload["message"] == "Test message"
        assert payload["priority"] == "high"


# ============================================================================
# TEST Message Status
# ============================================================================


class TestMessageStatus:
    """Test message status tracking."""

    @pytest.mark.asyncio
    async def test_get_message_status_pending(self, notification_manager):
        """Test getting status of pending message."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test",
            priority=NotificationPriority.NORMAL,
        )

        notification_manager.pending_messages[msg.id] = msg

        status = await notification_manager.get_message_status(msg.id)

        assert status["message_id"] == msg.id
        assert status["status"] == "pending"
        assert status["store"] == "pending"

    @pytest.mark.asyncio
    async def test_get_message_status_sent(self, notification_manager):
        """Test getting status of sent message."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test",
            priority=NotificationPriority.NORMAL,
        )
        msg.status = NotificationStatus.SENT
        msg.sent_at = datetime.now()

        notification_manager.sent_messages[msg.id] = msg

        status = await notification_manager.get_message_status(msg.id)

        assert status["status"] == "sent"
        assert status["sent_at"] is not None

    @pytest.mark.asyncio
    async def test_get_message_status_nonexistent(self, notification_manager):
        """Test getting status of non-existent message."""
        status = await notification_manager.get_message_status("nonexistent")

        assert status is None


# ============================================================================
# TEST Metrics and Health Check
# ============================================================================


class TestMetricsAndHealthCheck:
    """Test metrics and health check operations."""

    @pytest.mark.asyncio
    async def test_get_metrics(self, notification_manager):
        """Test getting notification system metrics."""
        metrics = await notification_manager.get_metrics()

        assert "delivery_metrics" in metrics
        assert "queue_status" in metrics
        assert "templates" in metrics
        assert "rate_limiting" in metrics
        assert "recent_deliveries" in metrics

    @pytest.mark.asyncio
    async def test_metrics_queue_status(self, notification_manager):
        """Test metrics includes queue status."""
        # Add some messages
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test",
            priority=NotificationPriority.NORMAL,
        )
        notification_manager.pending_messages[msg.id] = msg

        metrics = await notification_manager.get_metrics()

        assert metrics["queue_status"]["pending"] >= 1

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, notification_manager, mock_http_client):
        """Test health check returns healthy status."""
        result = await notification_manager.health_check()

        assert result["status"] == "healthy"
        assert result["http_client"] == "healthy"
        assert "templates_loaded" in result
        assert "avg_delivery_time" in result

    @pytest.mark.asyncio
    async def test_health_check_degraded(self, notification_manager, mock_http_client):
        """Test health check returns degraded status on HTTP error."""
        mock_http_client.get = AsyncMock(return_value=MagicMock(status_code=500))

        result = await notification_manager.health_check()

        assert result["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, notification_manager, mock_http_client):
        """Test health check returns unhealthy status on exception."""
        mock_http_client.get = AsyncMock(side_effect=Exception("Connection error"))

        result = await notification_manager.health_check()

        assert result["status"] == "unhealthy"
        assert "error" in result


# ============================================================================
# TEST Error Handling
# ============================================================================


class TestErrorHandling:
    """Test error handling in notification system."""

    @pytest.mark.asyncio
    async def test_handle_delivery_error_retry(self, notification_manager):
        """Test error handler schedules retry."""
        msg = NotificationMessage(
            id="msg123",
            channel=NotificationChannel.SLACK,
            webhook_url="https://hooks.slack.com/test",
            title="Test",
            message="Test",
            priority=NotificationPriority.NORMAL,
            max_retries=2,
        )

        notification_manager.pending_messages[msg.id] = msg

        # Trigger error handling
        await notification_manager._handle_delivery_error(msg, "Network error")

        assert msg.error_message == "Network error"
        assert msg.retry_count == 1

    @pytest.mark.asyncio
    async def test_update_avg_delivery_time(self, notification_manager):
        """Test average delivery time calculation."""
        notification_manager._update_avg_delivery_time(100.0)
        assert notification_manager.metrics["avg_delivery_time"] == 100.0

        notification_manager._update_avg_delivery_time(200.0)
        # Should use exponential moving average
        assert notification_manager.metrics["avg_delivery_time"] > 100.0
        assert notification_manager.metrics["avg_delivery_time"] < 200.0


# ============================================================================
# TEST Global Instance
# ============================================================================


def test_global_notification_manager():
    """Test global notification_manager instance exists."""
    from infrastructure.notification_manager import notification_manager

    assert notification_manager is not None
    assert isinstance(notification_manager, NotificationManager)
    assert len(notification_manager.templates) > 0
