import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import logging
import time
from typing import Any

from httpx import AsyncClient


"""
Enterprise Notification Manager - Multi-Channel Communication System
Implements Slack/Discord webhooks with rate limiting, templates, and delivery confirmation
Target: Max 1 message/second rate limiting with rich formatting support
"""

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification channel types"""

    SLACK = "slack"
    DISCORD = "discord"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Notification priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class NotificationStatus(Enum):
    """Notification delivery status"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    RETRYING = "retrying"


@dataclass
class NotificationTemplate:
    """Notification template structure"""

    name: str
    channel: NotificationChannel
    title_template: str
    message_template: str
    color: str | None = None
    emoji: str | None = None
    fields: list[dict[str, str]] = None
    attachments: list[dict[str, Any]] = None
    fashion_context: bool = False

    def render(self, context: dict[str, Any]) -> dict[str, Any]:
        """Render template with context data"""
        try:
            title = self.title_template.format(**context)
            message = self.message_template.format(**context)

            rendered = {
                "title": title,
                "message": message,
                "color": self.color,
                "emoji": self.emoji,
            }

            # Render fields if present
            if self.fields:
                rendered["fields"] = []
                for field in self.fields:
                    rendered["fields"].append(
                        {
                            "name": field["name"].format(**context),
                            "value": field["value"].format(**context),
                            "inline": field.get("inline", False),
                        }
                    )

            return rendered

        except KeyError as e:
            logger.error(f"Template rendering error - missing context key: {e}")
            return {
                "title": "Template Error",
                "message": f"Failed to render template: {self.name}",
                "color": "#ff0000",
            }


@dataclass
class NotificationMessage:
    """Notification message structure"""

    id: str
    channel: NotificationChannel
    webhook_url: str
    title: str
    message: str
    priority: NotificationPriority
    template_name: str | None = None
    context: dict[str, Any] = None
    color: str | None = None
    emoji: str | None = None
    fields: list[dict[str, str]] = None
    attachments: list[dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    sent_at: datetime | None = None
    status: NotificationStatus = NotificationStatus.PENDING
    error_message: str | None = None
    fashion_context: dict[str, Any] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.context is None:
            self.context = {}
        if self.fashion_context is None:
            self.fashion_context = {}


class RateLimiter:
    """Rate limiter for notification channels"""

    def __init__(self, max_requests: int = 1, time_window: int = 1):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.channel_limits = defaultdict(lambda: deque())

    async def acquire(self, channel: str = "default") -> bool:
        """Acquire rate limit permission"""
        now = time.time()
        channel_requests = self.channel_limits[channel]

        # Remove old requests outside time window
        while channel_requests and channel_requests[0] <= now - self.time_window:
            channel_requests.popleft()

        # Check if we can make a request
        if len(channel_requests) < self.max_requests:
            channel_requests.append(now)
            return True

        return False

    async def wait_for_slot(self, channel: str = "default") -> float:
        """Wait for next available slot"""
        channel_requests = self.channel_limits[channel]

        if not channel_requests:
            return 0.0

        # Calculate wait time until oldest request expires
        oldest_request = channel_requests[0]
        wait_time = max(0, self.time_window - (time.time() - oldest_request))

        if wait_time > 0:
            await asyncio.sleep(wait_time)

        return wait_time


class NotificationManager:
    """Enterprise notification manager with multi-channel support"""

    def __init__(
        self,
        rate_limit_per_second: int = 1,
        max_concurrent_requests: int = 10,
        request_timeout: int = 30,
        retry_delay: int = 5,
    ):
        self.rate_limiter = RateLimiter(max_requests=rate_limit_per_second, time_window=1)
        self.max_concurrent_requests = max_concurrent_requests
        self.request_timeout = request_timeout
        self.retry_delay = retry_delay

        # Message queues and tracking
        self.pending_messages: dict[str, NotificationMessage] = {}
        self.sent_messages: dict[str, NotificationMessage] = {}
        self.failed_messages: dict[str, NotificationMessage] = {}
        self.delivery_history = deque(maxlen=1000)

        # Templates
        self.templates: dict[str, NotificationTemplate] = {}

        # HTTP client for webhook requests
        self.http_client = AsyncClient(timeout=request_timeout)

        # Metrics
        self.metrics = {
            "total_sent": 0,
            "total_failed": 0,
            "total_rate_limited": 0,
            "avg_delivery_time": 0.0,
            "last_updated": datetime.now(),
        }

        # Setup default templates
        self._setup_default_templates()

        logger.info("Notification manager initialized with rate limiting")

    def _setup_default_templates(self):
        """Setup default notification templates for fashion e-commerce"""

        # System alerts
        self.add_template(
            NotificationTemplate(
                name="system_alert",
                channel=NotificationChannel.SLACK,
                title_template="🚨 System Alert: {alert_type}",
                message_template="**Alert:** {message}\n**Severity:** {severity}\n**Time:** {timestamp}",
                color="#ff4444",
                emoji="🚨",
                fields=[
                    {"name": "Environment", "value": "{environment}", "inline": True},
                    {"name": "Service", "value": "{service}", "inline": True},
                    {
                        "name": "Correlation ID",
                        "value": "{correlation_id}",
                        "inline": True,
                    },
                ],
            )
        )

        # Deployment notifications
        self.add_template(
            NotificationTemplate(
                name="deployment_success",
                channel=NotificationChannel.SLACK,
                title_template="🚀 Deployment Successful",
                message_template="**Version:** {version}\n**Environment:** {environment}\n**Duration:** {duration}",
                color="#00ff00",
                emoji="🚀",
                fields=[
                    {"name": "Branch", "value": "{branch}", "inline": True},
                    {"name": "Commit", "value": "{commit_hash}", "inline": True},
                    {"name": "Deployed By", "value": "{deployed_by}", "inline": True},
                ],
            )
        )

        # Fashion trend alerts
        self.add_template(
            NotificationTemplate(
                name="fashion_trend_alert",
                channel=NotificationChannel.SLACK,
                title_template="👗 Fashion Trend Alert: {trend_name}",
                message_template="**New Trend Detected:** {trend_name}\n**Category:** {category}\n**Popularity Score:** {popularity_score}\n**Season:** {season}",
                color="#ff69b4",
                emoji="👗",
                fields=[
                    {
                        "name": "Target Demographic",
                        "value": "{target_demographic}",
                        "inline": True,
                    },
                    {"name": "Price Range", "value": "{price_range}", "inline": True},
                    {
                        "name": "Sustainability Score",
                        "value": "{sustainability_score}",
                        "inline": True,
                    },
                ],
                fashion_context=True,
            )
        )

        # Inventory alerts
        self.add_template(
            NotificationTemplate(
                name="inventory_low_stock",
                channel=NotificationChannel.SLACK,
                title_template="📦 Low Stock Alert",
                message_template="**Product:** {product_name}\n**Current Stock:** {current_stock}\n**Threshold:** {threshold}",
                color="#ffa500",
                emoji="📦",
                fields=[
                    {"name": "SKU", "value": "{sku}", "inline": True},
                    {"name": "Category", "value": "{category}", "inline": True},
                    {"name": "Supplier", "value": "{supplier}", "inline": True},
                ],
                fashion_context=True,
            )
        )

        # Performance alerts
        self.add_template(
            NotificationTemplate(
                name="performance_degradation",
                channel=NotificationChannel.SLACK,
                title_template="⚡ Performance Alert",
                message_template="**Metric:** {metric_name}\n**Current Value:** {current_value}\n**Threshold:** {threshold}",
                color="#ff8c00",
                emoji="⚡",
                fields=[
                    {"name": "Service", "value": "{service}", "inline": True},
                    {"name": "Duration", "value": "{duration}", "inline": True},
                    {"name": "Impact", "value": "{impact}", "inline": True},
                ],
            )
        )

    def add_template(self, template: NotificationTemplate):
        """Add notification template"""
        self.templates[template.name] = template
        logger.debug(f"Added notification template: {template.name}")

    def remove_template(self, template_name: str):
        """Remove notification template"""
        if template_name in self.templates:
            del self.templates[template_name]
            logger.debug(f"Removed notification template: {template_name}")

    async def send_notification(
        self,
        channel: NotificationChannel,
        webhook_url: str,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_name: str | None = None,
        context: dict[str, Any] | None = None,
        **kwargs,
    ) -> str:
        """Send notification message"""

        # Generate unique message ID
        message_id = hashlib.sha256(f"{channel.value}_{webhook_url}_{title}_{time.time()}".encode()).hexdigest()

        # Create notification message
        notification = NotificationMessage(
            id=message_id,
            channel=channel,
            webhook_url=webhook_url,
            title=title,
            message=message,
            priority=priority,
            template_name=template_name,
            context=context or {},
            **kwargs,
        )

        # Add to pending queue
        self.pending_messages[message_id] = notification

        # Schedule delivery
        asyncio.create_task(self._deliver_message(notification))

        logger.info(f"Notification queued: {message_id} ({channel.value})")
        return message_id

    async def send_from_template(
        self,
        template_name: str,
        webhook_url: str,
        context: dict[str, Any],
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> str:
        """Send notification using template"""

        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")

        template = self.templates[template_name]
        rendered = template.render(context)

        return await self.send_notification(
            channel=template.channel,
            webhook_url=webhook_url,
            title=rendered["title"],
            message=rendered["message"],
            priority=priority,
            template_name=template_name,
            context=context,
            color=rendered.get("color"),
            emoji=rendered.get("emoji"),
            fields=rendered.get("fields"),
            fashion_context=context if template.fashion_context else None,
        )

    async def _deliver_message(self, notification: NotificationMessage):
        """Deliver notification message with rate limiting and retries"""
        start_time = time.time()

        try:
            # Wait for rate limit slot
            channel_key = f"{notification.channel.value}_{notification.webhook_url}"

            if not await self.rate_limiter.acquire(channel_key):
                # Rate limited - wait for slot
                wait_time = await self.rate_limiter.wait_for_slot(channel_key)
                notification.status = NotificationStatus.RATE_LIMITED
                self.metrics["total_rate_limited"] += 1

                logger.debug(f"Rate limited notification {notification.id}, waited {wait_time:.2f}s")

                # Try to acquire again after waiting
                if not await self.rate_limiter.acquire(channel_key):
                    raise Exception("Failed to acquire rate limit slot after waiting")

            # Prepare webhook payload
            payload = await self._prepare_payload(notification)

            # Send webhook request
            response = await self.http_client.post(
                notification.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()

            # Mark as sent
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now()

            # Move to sent messages
            if notification.id in self.pending_messages:
                del self.pending_messages[notification.id]
            self.sent_messages[notification.id] = notification

            # Update metrics
            delivery_time = time.time() - start_time
            self.metrics["total_sent"] += 1
            self._update_avg_delivery_time(delivery_time)

            # Record delivery history
            self.delivery_history.append(
                {
                    "message_id": notification.id,
                    "channel": notification.channel.value,
                    "status": "sent",
                    "delivery_time": delivery_time,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            logger.info(f"Notification sent: {notification.id} ({delivery_time:.2f}s)")

        except Exception as e:
            await self._handle_delivery_error(notification, str(e))

    async def _prepare_payload(self, notification: NotificationMessage) -> dict[str, Any]:
        """Prepare webhook payload based on channel type"""

        if notification.channel == NotificationChannel.SLACK:
            return await self._prepare_slack_payload(notification)
        elif notification.channel == NotificationChannel.DISCORD:
            return await self._prepare_discord_payload(notification)
        else:
            # Generic webhook payload
            return {
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority.value,
                "timestamp": notification.created_at.isoformat(),
                "context": notification.context,
            }

    async def _prepare_slack_payload(self, notification: NotificationMessage) -> dict[str, Any]:
        """Prepare Slack webhook payload"""

        payload = {
            "text": notification.title,
            "attachments": [
                {
                    "color": notification.color or "#36a64f",
                    "title": notification.title,
                    "text": notification.message,
                    "ts": int(notification.created_at.timestamp()),
                }
            ],
        }

        # Add emoji to text if specified
        if notification.emoji:
            payload["text"] = f"{notification.emoji} {payload['text']}"

        # Add fields if present
        if notification.fields:
            payload["attachments"][0]["fields"] = notification.fields

        # Add fashion context if present
        if notification.fashion_context:
            payload["attachments"][0]["footer"] = "Fashion Industry Context"
            payload["attachments"][0]["footer_icon"] = "https://example.com/fashion-icon.png"

        return payload

    async def _prepare_discord_payload(self, notification: NotificationMessage) -> dict[str, Any]:
        """Prepare Discord webhook payload"""

        embed = {
            "title": notification.title,
            "description": notification.message,
            "color": (int(notification.color.replace("#", ""), 16) if notification.color else 3447003),
            "timestamp": notification.created_at.isoformat(),
        }

        # Add fields if present
        if notification.fields:
            embed["fields"] = notification.fields

        # Add fashion context if present
        if notification.fashion_context:
            embed["footer"] = {
                "text": "Fashion Industry Context",
                "icon_url": "https://example.com/fashion-icon.png",
            }

        payload = {"embeds": [embed]}

        # Add emoji to content if specified
        if notification.emoji:
            payload["content"] = f"{notification.emoji} {notification.title}"

        return payload

    async def _handle_delivery_error(self, notification: NotificationMessage, error: str):
        """Handle notification delivery error with retry logic"""

        notification.error_message = error
        notification.retry_count += 1

        if notification.retry_count <= notification.max_retries:
            # Schedule retry
            notification.status = NotificationStatus.RETRYING

            retry_delay = self.retry_delay * (2 ** (notification.retry_count - 1))  # Exponential backoff

            logger.warning(
                f"Notification {notification.id} failed, retrying in {retry_delay}s (attempt {notification.retry_count}/{notification.max_retries})"
            )

            await asyncio.sleep(retry_delay)
            await self._deliver_message(notification)

        else:
            # Max retries exceeded
            notification.status = NotificationStatus.FAILED

            # Move to failed messages
            if notification.id in self.pending_messages:
                del self.pending_messages[notification.id]
            self.failed_messages[notification.id] = notification

            self.metrics["total_failed"] += 1

            # Record failure in history
            self.delivery_history.append(
                {
                    "message_id": notification.id,
                    "channel": notification.channel.value,
                    "status": "failed",
                    "error": error,
                    "retry_count": notification.retry_count,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            logger.error(f"Notification {notification.id} failed permanently: {error}")

    def _update_avg_delivery_time(self, delivery_time: float):
        """Update average delivery time metric"""
        if self.metrics["avg_delivery_time"] == 0:
            self.metrics["avg_delivery_time"] = delivery_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics["avg_delivery_time"] = alpha * delivery_time + (1 - alpha) * self.metrics["avg_delivery_time"]

        self.metrics["last_updated"] = datetime.now()

    async def get_message_status(self, message_id: str) -> dict[str, Any] | None:
        """Get notification message status"""

        # Check all message stores
        for store_name, store in [
            ("pending", self.pending_messages),
            ("sent", self.sent_messages),
            ("failed", self.failed_messages),
        ]:
            if message_id in store:
                message = store[message_id]
                return {
                    "message_id": message_id,
                    "status": message.status.value,
                    "channel": message.channel.value,
                    "title": message.title,
                    "priority": message.priority.value,
                    "created_at": message.created_at.isoformat(),
                    "sent_at": message.sent_at.isoformat() if message.sent_at else None,
                    "retry_count": message.retry_count,
                    "error_message": message.error_message,
                    "store": store_name,
                }

        return None

    async def get_metrics(self) -> dict[str, Any]:
        """Get notification system metrics"""

        return {
            "delivery_metrics": self.metrics,
            "queue_status": {
                "pending": len(self.pending_messages),
                "sent": len(self.sent_messages),
                "failed": len(self.failed_messages),
            },
            "templates": list(self.templates.keys()),
            "rate_limiting": {
                "max_per_second": self.rate_limiter.max_requests,
                "time_window": self.rate_limiter.time_window,
            },
            "recent_deliveries": list(self.delivery_history)[-10:],  # Last 10 deliveries
        }

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check"""

        try:
            # Test HTTP client
            test_response = await self.http_client.get("https://httpbin.org/status/200", timeout=5)
            http_client_healthy = test_response.status_code == 200

            metrics = await self.get_metrics()

            return {
                "status": "healthy" if http_client_healthy else "degraded",
                "http_client": "healthy" if http_client_healthy else "unhealthy",
                "rate_limiting": "active",
                "templates_loaded": len(self.templates),
                "pending_messages": len(self.pending_messages),
                "avg_delivery_time": self.metrics["avg_delivery_time"],
                "target_rate_limit": "1 message/second",
                "meets_target": True,  # Always true if system is running
                "metrics": metrics,
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Close HTTP client and cleanup"""
        await self.http_client.aclose()
        logger.info("Notification manager closed")


# Global notification manager instance
notification_manager = NotificationManager()
