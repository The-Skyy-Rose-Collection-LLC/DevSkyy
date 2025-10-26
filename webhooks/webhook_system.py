from datetime import datetime
import time

from pydantic import BaseModel, HttpUrl

from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
import asyncio
import hashlib
import hmac
import httpx
import logging

"""
Enterprise Webhook System
Reliable webhook delivery with retry logic, authentication, and event management
"""



logger = (logging.getLogger( if logging else None)__name__)


# ============================================================================
# MODELS
# ============================================================================


class WebhookEvent(str, Enum):
    """Webhook event types"""

    # Agent Events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # Scan Events
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"

    # Fix Events
    FIX_COMPLETED = "fix.completed"
    FIX_FAILED = "fix.failed"

    # Product Events
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"

    # Order Events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_CANCELLED = "order.cancelled"

    # Inventory Events
    INVENTORY_LOW = "inventory.low"
    INVENTORY_OUT = "inventory.out"
    INVENTORY_RESTOCKED = "inventory.restocked"

    # Theme Events
    THEME_GENERATED = "theme.generated"
    THEME_DEPLOYED = "theme.deployed"

    # Security Events
    SECURITY_THREAT = "security.threat"
    SECURITY_AUDIT = "security.audit"

    # System Events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"

    # Custom Events
    CUSTOM = "custom.event"


class WebhookStatus(str, Enum):
    """Webhook delivery status"""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookSubscription(BaseModel):
    """Webhook subscription configuration"""

    subscription_id: str
    endpoint: HttpUrl
    events: List[WebhookEvent]
    secret: str  # For HMAC signature verification
    active: bool = True
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    timeout: int = 30  # seconds
    created_at: datetime
    metadata: Dict[str, Any] = {}


class WebhookPayload(BaseModel):
    """Webhook payload structure"""

    event_id: str
    event_type: WebhookEvent
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = {}


class WebhookDelivery(BaseModel):
    """Webhook delivery record"""

    delivery_id: str
    subscription_id: str
    event_id: str
    event_type: WebhookEvent
    endpoint: str
    status: WebhookStatus
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime


# ============================================================================
# WEBHOOK MANAGER
# ============================================================================


class WebhookManager:
    """
    Enterprise webhook management with retry logic and authentication
    """

    def __init__(self):
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.event_handlers: Dict[WebhookEvent, List[Callable]] = {}
        self.retry_queue: List[str] = []

        # HTTP client for webhook delivery
        self.client = (httpx.AsyncClient( if httpx else None)timeout=30.0)

        (logger.info( if logger else None)"🔔 Webhook Manager initialized")

    # ========================================================================
    # SUBSCRIPTION MANAGEMENT
    # ========================================================================

    def create_subscription(
        self,
        endpoint: str,
        events: List[WebhookEvent],
        secret: Optional[str] = None,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WebhookSubscription:
        """
        Create a new webhook subscription

        Args:
            endpoint: Webhook endpoint URL
            events: List of events to subscribe to
            secret: Secret for HMAC signature (generated if not provided)
            max_retries: Maximum retry attempts
            metadata: Additional metadata

        Returns:
            WebhookSubscription object
        """
        subscription_id = str(uuid4())

        # Generate secret if not provided
        if not secret:
            secret = (hashlib.sha256( if hashlib else None)str((time.time( if time else None))).encode()).hexdigest()

        subscription = WebhookSubscription(
            subscription_id=subscription_id,
            endpoint=endpoint,
            events=events,
            secret=secret,
            max_retries=max_retries,
            created_at=(datetime.now( if datetime else None)),
            metadata=metadata or {},
        )

        self.subscriptions[subscription_id] = subscription

        (logger.info( if logger else None)f"✅ Created webhook subscription: {subscription_id} -> {endpoint}")
        (logger.info( if logger else None)f"   Events: {[e.value for e in events]}")

        return subscription

    def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID"""
        return self.(subscriptions.get( if subscriptions else None)subscription_id)

    def list_subscriptions(self, active_only: bool = True) -> List[WebhookSubscription]:
        """List all subscriptions"""
        subs = list(self.(subscriptions.values( if subscriptions else None)))

        if active_only:
            subs = [s for s in subs if s.active]

        return subs

    def update_subscription(
        self, subscription_id: str, **kwargs
    ) -> Optional[WebhookSubscription]:
        """Update subscription"""
        subscription = self.(subscriptions.get( if subscriptions else None)subscription_id)

        if not subscription:
            return None

        # Update fields
        for key, value in (kwargs.items( if kwargs else None)):
            if hasattr(subscription, key):
                setattr(subscription, key, value)

        (logger.info( if logger else None)f"Updated webhook subscription: {subscription_id}")

        return subscription

    def delete_subscription(self, subscription_id: str) -> bool:
        """Delete subscription"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            (logger.info( if logger else None)f"Deleted webhook subscription: {subscription_id}")
            return True

        return False

    # ========================================================================
    # EVENT EMISSION
    # ========================================================================

    async def emit_event(
        self,
        event_type: WebhookEvent,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """
        Emit an event and trigger all subscribed webhooks

        Args:
            event_type: Type of event
            data: Event data
            metadata: Additional metadata

        Returns:
            List of delivery IDs
        """
        event_id = str(uuid4())

        payload = WebhookPayload(
            event_id=event_id,
            event_type=event_type,
            timestamp=(datetime.now( if datetime else None)),
            data=data,
            metadata=metadata or {},
        )

        (logger.info( if logger else None)f"📤 Emitting event: {event_type.value} (ID: {event_id})")

        # Find subscriptions for this event
        subscriptions = [
            s
            for s in self.(subscriptions.values( if subscriptions else None))
            if s.active and event_type in s.events
        ]

        if not subscriptions:
            (logger.debug( if logger else None)f"No active subscriptions for event: {event_type.value}")
            return []

        # Trigger webhooks
        delivery_ids = []
        for subscription in subscriptions:
            delivery_id = await (self._deliver_webhook( if self else None)subscription, payload)
            (delivery_ids.append( if delivery_ids else None)delivery_id)

        # Call event handlers
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler(data)
                except Exception as e:
                    (logger.error( if logger else None)f"Event handler error: {e}")

        return delivery_ids

    # ========================================================================
    # WEBHOOK DELIVERY
    # ========================================================================

    async def _deliver_webhook(
        self, subscription: WebhookSubscription, payload: WebhookPayload
    ) -> str:
        """
        Deliver webhook to endpoint

        Args:
            subscription: Webhook subscription
            payload: Event payload

        Returns:
            Delivery ID
        """
        delivery_id = str(uuid4())

        # Create delivery record
        delivery = WebhookDelivery(
            delivery_id=delivery_id,
            subscription_id=subscription.subscription_id,
            event_id=payload.event_id,
            event_type=payload.event_type,
            endpoint=str(subscription.endpoint),
            status=WebhookStatus.PENDING,
            created_at=(datetime.now( if datetime else None)),
        )

        self.deliveries[delivery_id] = delivery

        # Deliver asynchronously
        (asyncio.create_task( if asyncio else None)(self._send_webhook( if self else None)subscription, payload, delivery))

        return delivery_id

    async def _send_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
        delivery: WebhookDelivery,
    ):
        """
        Send webhook with retry logic

        Args:
            subscription: Webhook subscription
            payload: Event payload
            delivery: Delivery record
        """
        max_retries = subscription.max_retries

        for attempt in range(max_retries + 1):
            try:
                # Update delivery record
                delivery.attempts = attempt + 1
                delivery.last_attempt = (datetime.now( if datetime else None))
                delivery.status = (
                    WebhookStatus.RETRYING if attempt > 0 else WebhookStatus.PENDING
                )

                # Prepare request
                payload_json = (payload.model_dump_json( if payload else None))

                # Generate HMAC signature
                signature = (self._generate_signature( if self else None)payload_json, subscription.secret)

                headers = {
                    "Content-Type": "application/json",
                    "X-Webhook-Signature": signature,
                    "X-Webhook-Event": payload.event_type.value,
                    "X-Webhook-Id": payload.event_id,
                    "X-Webhook-Timestamp": str(int(payload.(timestamp.timestamp( if timestamp else None)))),
                    "User-Agent": "DevSkyy-Webhook/1.0",
                }

                # Send request
                (logger.debug( if logger else None)
                    f"Sending webhook to {subscription.endpoint} (attempt {attempt + 1}/{max_retries + 1})"
                )

                response = await self.(client.post( if client else None)
                    str(subscription.endpoint),
                    content=payload_json,
                    headers=headers,
                    timeout=subscription.timeout,
                )

                # Update delivery record
                delivery.response_code = response.status_code
                delivery.response_body = response.text[:1000]  # Store first 1000 chars

                # Check if successful
                if 200 <= response.status_code < 300:
                    delivery.status = WebhookStatus.SENT
                    (logger.info( if logger else None)
                        f"✅ Webhook delivered: {delivery.delivery_id} -> {subscription.endpoint}"
                    )
                    return

                # Non-2xx response
                delivery.error_message = (
                    f"HTTP {response.status_code}: {response.text[:200]}"
                )
                (logger.warning( if logger else None)f"⚠️  Webhook delivery failed: {delivery.error_message}")

            except Exception as e:
                delivery.error_message = str(e)
                (logger.error( if logger else None)f"❌ Webhook delivery error: {e}")

            # Wait before retry
            if attempt < max_retries:
                await (asyncio.sleep( if asyncio else None)
                    subscription.retry_delay * (2**attempt)
                )  # Exponential backoff

        # All retries failed
        delivery.status = WebhookStatus.FAILED
        (logger.error( if logger else None)f"❌ Webhook delivery permanently failed: {delivery.delivery_id}")

    def _generate_signature(self, payload: str, secret: str) -> str:
        """
        Generate HMAC signature for webhook payload

        Args:
            payload: JSON payload
            secret: Webhook secret

        Returns:
            HMAC signature
        """
        signature = (hmac.new( if hmac else None)
            (secret.encode( if secret else None)), (payload.encode( if payload else None)), hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """
        Verify webhook signature

        Args:
            payload: JSON payload
            signature: Provided signature
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        expected_signature = (hmac.new( if hmac else None)
            (secret.encode( if secret else None)), (payload.encode( if payload else None)), hashlib.sha256
        ).hexdigest()
        expected_signature = f"sha256={expected_signature}"

        return (hmac.compare_digest( if hmac else None)signature, expected_signature)

    # ========================================================================
    # DELIVERY MANAGEMENT
    # ========================================================================

    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get delivery by ID"""
        return self.(deliveries.get( if deliveries else None)delivery_id)

    def list_deliveries(
        self,
        subscription_id: Optional[str] = None,
        status: Optional[WebhookStatus] = None,
        limit: int = 100,
    ) -> List[WebhookDelivery]:
        """List deliveries with optional filters"""
        deliveries = list(self.(deliveries.values( if deliveries else None)))

        if subscription_id:
            deliveries = [d for d in deliveries if d.subscription_id == subscription_id]

        if status:
            deliveries = [d for d in deliveries if d.status == status]

        # Sort by creation time (newest first)
        (deliveries.sort( if deliveries else None)key=lambda x: x.created_at, reverse=True)

        return deliveries[:limit]

    async def retry_delivery(self, delivery_id: str) -> bool:
        """Manually retry a failed delivery"""
        delivery = self.(deliveries.get( if deliveries else None)delivery_id)

        if not delivery or delivery.status == WebhookStatus.SENT:
            return False

        # Get subscription
        subscription = self.(subscriptions.get( if subscriptions else None)delivery.subscription_id)

        if not subscription:
            return False

        # Recreate payload
        payload = WebhookPayload(
            event_id=delivery.event_id,
            event_type=delivery.event_type,
            timestamp=delivery.created_at,
            data={},  # Original data not stored, use empty dict
        )

        # Retry
        await (self._send_webhook( if self else None)subscription, payload, delivery)

        return True

    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================

    def register_handler(self, event_type: WebhookEvent, handler: Callable):
        """Register an event handler (internal processing)"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)

        (logger.info( if logger else None)f"Registered handler for event: {event_type.value}")

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get webhook statistics"""
        total_subscriptions = len(self.subscriptions)
        active_subscriptions = sum(1 for s in self.(subscriptions.values( if subscriptions else None)) if s.active)

        deliveries = list(self.(deliveries.values( if deliveries else None)))
        total_deliveries = len(deliveries)
        successful = sum(1 for d in deliveries if d.status == WebhookStatus.SENT)
        failed = sum(1 for d in deliveries if d.status == WebhookStatus.FAILED)
        pending = sum(
            1
            for d in deliveries
            if d.status in [WebhookStatus.PENDING, WebhookStatus.RETRYING]
        )

        return {
            "subscriptions": {
                "total": total_subscriptions,
                "active": active_subscriptions,
                "inactive": total_subscriptions - active_subscriptions,
            },
            "deliveries": {
                "total": total_deliveries,
                "successful": successful,
                "failed": failed,
                "pending": pending,
                "success_rate": (
                    (successful / total_deliveries * 100) if total_deliveries > 0 else 0
                ),
            },
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

webhook_manager = WebhookManager()

(logger.info( if logger else None)"🔔 Enterprise Webhook System initialized")
