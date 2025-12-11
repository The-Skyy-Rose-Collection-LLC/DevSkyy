"""
DevSkyy Enterprise Webhook System
==================================

Production-grade webhook implementation following:
- RFC 2104: HMAC Message Authentication
- Stripe Webhook Signing Best Practices
- GitHub Webhooks Security Model

Features:
- Webhook registration and management
- HMAC-SHA256 request signing
- Automatic retry with exponential backoff
- Event filtering and routing
- Dead letter queue for failed deliveries
- Rate limiting per endpoint

Dependencies (verified from PyPI December 2024):
- fastapi==0.104.1
- httpx==0.25.2
- pydantic==2.5.2
"""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl, validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class WebhookConfig:
    """Webhook system configuration"""

    # Signing
    signature_header: str = "X-DevSkyy-Signature"
    timestamp_header: str = "X-DevSkyy-Timestamp"
    signature_algorithm: str = "sha256"

    # Delivery
    timeout_seconds: float = 30.0
    max_retries: int = 5
    retry_base_delay: float = 1.0  # Exponential backoff base
    retry_max_delay: float = 300.0  # 5 minutes max

    # Security
    max_age_seconds: int = 300  # 5 minutes - reject older webhooks

    # Rate limiting
    max_deliveries_per_minute: int = 60

    # Dead letter
    dead_letter_enabled: bool = True
    dead_letter_retention_days: int = 7


class WebhookEventType(str, Enum):
    """Standard webhook event types"""

    # Order events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_COMPLETED = "order.completed"
    ORDER_CANCELLED = "order.cancelled"
    ORDER_REFUNDED = "order.refunded"

    # Product events
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    PRODUCT_LOW_STOCK = "product.low_stock"

    # Customer events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_DELETED = "customer.deleted"

    # Payment events
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"

    # Agent events
    AGENT_TASK_STARTED = "agent.task.started"
    AGENT_TASK_COMPLETED = "agent.task.completed"
    AGENT_TASK_FAILED = "agent.task.failed"

    # System events
    SYSTEM_HEALTH_WARNING = "system.health.warning"
    SYSTEM_ERROR = "system.error"

    # Catch-all
    ALL = "*"


class DeliveryStatus(str, Enum):
    """Webhook delivery status"""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTERED = "dead_lettered"


# =============================================================================
# Models
# =============================================================================


class WebhookEndpoint(BaseModel):
    """Webhook endpoint registration"""

    id: str = Field(default_factory=lambda: f"whep_{secrets.token_urlsafe(16)}")
    url: HttpUrl
    secret: str = Field(default_factory=lambda: f"whsec_{secrets.token_urlsafe(32)}")
    events: list[str] = [WebhookEventType.ALL.value]
    description: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = {}

    # Stats
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    last_delivery_at: datetime | None = None

    @validator("events")
    def validate_events(cls, v):
        valid_events = {e.value for e in WebhookEventType}
        for event in v:
            if event not in valid_events and not event.startswith("custom."):
                raise ValueError(f"Invalid event type: {event}")
        return v


class WebhookEvent(BaseModel):
    """Webhook event payload"""

    id: str = Field(default_factory=lambda: f"evt_{secrets.token_urlsafe(16)}")
    type: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    data: dict[str, Any]
    api_version: str = "v1"
    metadata: dict[str, Any] = {}


class WebhookDelivery(BaseModel):
    """Record of webhook delivery attempt"""

    id: str = Field(default_factory=lambda: f"whdel_{secrets.token_urlsafe(16)}")
    endpoint_id: str
    event_id: str
    event_type: str

    # Delivery info
    url: str
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempt: int = 1

    # Response
    response_status: int | None = None
    response_body: str | None = None
    response_time_ms: float | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    delivered_at: datetime | None = None
    next_retry_at: datetime | None = None

    # Error info
    error_message: str | None = None


class WebhookEndpointCreate(BaseModel):
    """Create webhook endpoint request"""

    url: HttpUrl
    events: list[str] = [WebhookEventType.ALL.value]
    description: str | None = None
    metadata: dict[str, Any] = {}


class WebhookEndpointResponse(BaseModel):
    """Webhook endpoint response (includes secret only on creation)"""

    id: str
    url: str
    events: list[str]
    description: str | None
    is_active: bool
    created_at: datetime
    secret: str | None = None  # Only included on creation


# =============================================================================
# HMAC Signing (RFC 2104)
# =============================================================================


class WebhookSigner:
    """
    HMAC-SHA256 webhook signing

    Signature format: t=timestamp,v1=signature

    Reference: RFC 2104 - HMAC
    """

    def __init__(self, config: WebhookConfig = None):
        self.config = config or WebhookConfig()

    def sign(self, payload: str, secret: str, timestamp: int = None) -> str:
        """
        Sign webhook payload

        Args:
            payload: JSON string payload
            secret: Webhook secret
            timestamp: Unix timestamp (generated if not provided)

        Returns:
            Signature string: t=timestamp,v1=signature
        """
        timestamp = timestamp or int(time.time())

        # Create signed payload
        signed_payload = f"{timestamp}.{payload}"

        # Compute HMAC-SHA256
        signature = hmac.new(
            secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        return f"t={timestamp},v1={signature}"

    def verify(self, payload: str, signature: str, secret: str, max_age: int = None) -> bool:
        """
        Verify webhook signature

        Args:
            payload: Raw request body
            signature: Signature header value
            secret: Webhook secret
            max_age: Maximum age in seconds (uses config default)

        Returns:
            True if valid, False otherwise
        """
        max_age = max_age or self.config.max_age_seconds

        # Parse signature
        parts = {}
        for part in signature.split(","):
            if "=" in part:
                key, value = part.split("=", 1)
                parts[key] = value

        if "t" not in parts or "v1" not in parts:
            logger.warning("Invalid signature format")
            return False

        timestamp = int(parts["t"])
        expected_sig = parts["v1"]

        # Check timestamp age
        current_time = int(time.time())
        if abs(current_time - timestamp) > max_age:
            logger.warning(f"Webhook timestamp too old: {current_time - timestamp}s")
            return False

        # Compute expected signature
        signed_payload = f"{timestamp}.{payload}"
        computed_sig = hmac.new(
            secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(expected_sig, computed_sig)


# =============================================================================
# Webhook Manager
# =============================================================================


class WebhookManager:
    """
    Manage webhook endpoints and deliveries

    Handles:
    - Endpoint registration
    - Event publishing
    - Delivery with retries
    - Dead letter queue
    """

    def __init__(self, config: WebhookConfig = None):
        self.config = config or WebhookConfig()
        self.signer = WebhookSigner(config)

        # In-memory stores (use database in production)
        self._endpoints: dict[str, WebhookEndpoint] = {}
        self._deliveries: dict[str, WebhookDelivery] = {}
        self._dead_letters: list[WebhookDelivery] = []

        # Rate limiting
        self._delivery_counts: dict[str, list[float]] = defaultdict(list)

        # HTTP client
        self._client: httpx.AsyncClient | None = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.config.timeout_seconds)
        return self._client

    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()

    # -------------------------------------------------------------------------
    # Endpoint Management
    # -------------------------------------------------------------------------

    def register_endpoint(
        self,
        url: str,
        events: list[str] = None,
        description: str = None,
        metadata: dict = None,
    ) -> WebhookEndpoint:
        """Register a new webhook endpoint"""
        endpoint = WebhookEndpoint(
            url=url,
            events=events or [WebhookEventType.ALL.value],
            description=description,
            metadata=metadata or {},
        )

        self._endpoints[endpoint.id] = endpoint
        logger.info(f"Registered webhook endpoint: {endpoint.id} -> {url}")

        return endpoint

    def get_endpoint(self, endpoint_id: str) -> WebhookEndpoint | None:
        """Get endpoint by ID"""
        return self._endpoints.get(endpoint_id)

    def list_endpoints(self, active_only: bool = True) -> list[WebhookEndpoint]:
        """List all endpoints"""
        endpoints = list(self._endpoints.values())
        if active_only:
            endpoints = [e for e in endpoints if e.is_active]
        return endpoints

    def update_endpoint(
        self,
        endpoint_id: str,
        url: str = None,
        events: list[str] = None,
        is_active: bool = None,
        description: str = None,
    ) -> WebhookEndpoint | None:
        """Update endpoint settings"""
        endpoint = self._endpoints.get(endpoint_id)
        if not endpoint:
            return None

        if url:
            endpoint.url = url
        if events is not None:
            endpoint.events = events
        if is_active is not None:
            endpoint.is_active = is_active
        if description is not None:
            endpoint.description = description

        return endpoint

    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete endpoint"""
        if endpoint_id in self._endpoints:
            del self._endpoints[endpoint_id]
            logger.info(f"Deleted webhook endpoint: {endpoint_id}")
            return True
        return False

    def rotate_secret(self, endpoint_id: str) -> str | None:
        """Rotate endpoint secret"""
        endpoint = self._endpoints.get(endpoint_id)
        if endpoint:
            new_secret = f"whsec_{secrets.token_urlsafe(32)}"
            endpoint.secret = new_secret
            logger.info(f"Rotated secret for endpoint: {endpoint_id}")
            return new_secret
        return None

    # -------------------------------------------------------------------------
    # Event Publishing
    # -------------------------------------------------------------------------

    async def publish(
        self, event_type: str, data: dict[str, Any], metadata: dict[str, Any] = None
    ) -> list[str]:
        """
        Publish event to all matching webhooks

        Args:
            event_type: Event type (e.g., "order.created")
            data: Event data
            metadata: Optional metadata

        Returns:
            List of delivery IDs
        """
        event = WebhookEvent(type=event_type, data=data, metadata=metadata or {})

        # Find matching endpoints
        matching_endpoints = [
            ep
            for ep in self._endpoints.values()
            if ep.is_active and self._event_matches(event_type, ep.events)
        ]

        if not matching_endpoints:
            logger.debug(f"No webhooks registered for event: {event_type}")
            return []

        # Create deliveries
        delivery_ids = []
        for endpoint in matching_endpoints:
            delivery = await self._deliver(endpoint, event)
            delivery_ids.append(delivery.id)

        logger.info(f"Published event {event.id} ({event_type}) to {len(delivery_ids)} endpoints")
        return delivery_ids

    def _event_matches(self, event_type: str, subscribed_events: list[str]) -> bool:
        """Check if event matches subscription"""
        if WebhookEventType.ALL.value in subscribed_events:
            return True

        if event_type in subscribed_events:
            return True

        # Check wildcard patterns (e.g., "order.*" matches "order.created")
        event_prefix = event_type.rsplit(".", 1)[0]
        for subscribed in subscribed_events:
            if subscribed.endswith(".*") and subscribed[:-2] == event_prefix:
                return True

        return False

    # -------------------------------------------------------------------------
    # Delivery
    # -------------------------------------------------------------------------

    async def _deliver(
        self, endpoint: WebhookEndpoint, event: WebhookEvent, attempt: int = 1
    ) -> WebhookDelivery:
        """Deliver webhook to endpoint"""

        # Check rate limit
        if not self._check_rate_limit(endpoint.id):
            logger.warning(f"Rate limit exceeded for endpoint: {endpoint.id}")
            delivery = WebhookDelivery(
                endpoint_id=endpoint.id,
                event_id=event.id,
                event_type=event.type,
                url=str(endpoint.url),
                status=DeliveryStatus.FAILED,
                attempt=attempt,
                error_message="Rate limit exceeded",
            )
            self._deliveries[delivery.id] = delivery
            return delivery

        # Prepare payload
        payload = event.model_dump_json()
        timestamp = int(time.time())
        signature = self.signer.sign(payload, endpoint.secret, timestamp)

        headers = {
            "Content-Type": "application/json",
            self.config.signature_header: signature,
            self.config.timestamp_header: str(timestamp),
            "User-Agent": "DevSkyy-Webhook/1.0",
            "X-DevSkyy-Event-ID": event.id,
            "X-DevSkyy-Event-Type": event.type,
            "X-DevSkyy-Delivery-ID": f"whdel_{secrets.token_urlsafe(16)}",
        }

        delivery = WebhookDelivery(
            endpoint_id=endpoint.id,
            event_id=event.id,
            event_type=event.type,
            url=str(endpoint.url),
            attempt=attempt,
        )

        start_time = time.time()

        try:
            client = await self.get_client()
            response = await client.post(str(endpoint.url), content=payload, headers=headers)

            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000] if response.text else None
            delivery.response_time_ms = (time.time() - start_time) * 1000

            # Check for success (2xx status)
            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.DELIVERED
                delivery.delivered_at = datetime.now(UTC)
                endpoint.successful_deliveries += 1
                endpoint.last_delivery_at = delivery.delivered_at
                logger.info(f"Webhook delivered: {delivery.id} -> {response.status_code}")
            else:
                raise Exception(f"Non-2xx response: {response.status_code}")

        except Exception as e:
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = str(e)
            delivery.response_time_ms = (time.time() - start_time) * 1000
            endpoint.failed_deliveries += 1

            logger.warning(f"Webhook delivery failed: {delivery.id} - {e}")

            # Schedule retry
            if attempt < self.config.max_retries:
                delivery.status = DeliveryStatus.RETRYING
                delay = min(
                    self.config.retry_base_delay * (2 ** (attempt - 1)),
                    self.config.retry_max_delay,
                )
                delivery.next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)

                # Schedule async retry
                asyncio.create_task(self._retry_delivery(endpoint, event, attempt + 1, delay))
            else:
                # Move to dead letter
                delivery.status = DeliveryStatus.DEAD_LETTERED
                if self.config.dead_letter_enabled:
                    self._dead_letters.append(delivery)
                    logger.error(f"Webhook dead lettered after {attempt} attempts: {delivery.id}")

        self._deliveries[delivery.id] = delivery
        return delivery

    async def _retry_delivery(
        self, endpoint: WebhookEndpoint, event: WebhookEvent, attempt: int, delay: float
    ):
        """Retry webhook delivery after delay"""
        await asyncio.sleep(delay)
        await self._deliver(endpoint, event, attempt)

    def _check_rate_limit(self, endpoint_id: str) -> bool:
        """Check if endpoint is within rate limit"""
        now = time.time()
        window_start = now - 60  # 1 minute window

        # Clean old entries
        self._delivery_counts[endpoint_id] = [
            t for t in self._delivery_counts[endpoint_id] if t > window_start
        ]

        # Check limit
        if len(self._delivery_counts[endpoint_id]) >= self.config.max_deliveries_per_minute:
            return False

        # Record delivery
        self._delivery_counts[endpoint_id].append(now)
        return True

    # -------------------------------------------------------------------------
    # Delivery History
    # -------------------------------------------------------------------------

    def get_delivery(self, delivery_id: str) -> WebhookDelivery | None:
        """Get delivery by ID"""
        return self._deliveries.get(delivery_id)

    def list_deliveries(
        self,
        endpoint_id: str = None,
        event_type: str = None,
        status: DeliveryStatus = None,
        limit: int = 100,
    ) -> list[WebhookDelivery]:
        """List deliveries with filters"""
        deliveries = list(self._deliveries.values())

        if endpoint_id:
            deliveries = [d for d in deliveries if d.endpoint_id == endpoint_id]
        if event_type:
            deliveries = [d for d in deliveries if d.event_type == event_type]
        if status:
            deliveries = [d for d in deliveries if d.status == status]

        # Sort by created_at desc
        deliveries.sort(key=lambda d: d.created_at, reverse=True)

        return deliveries[:limit]

    def get_dead_letters(self, limit: int = 100) -> list[WebhookDelivery]:
        """Get dead lettered deliveries"""
        return self._dead_letters[:limit]

    async def retry_dead_letter(self, delivery_id: str) -> WebhookDelivery | None:
        """Manually retry a dead lettered delivery"""
        # Find in dead letters
        for i, delivery in enumerate(self._dead_letters):
            if delivery.id == delivery_id:
                endpoint = self._endpoints.get(delivery.endpoint_id)
                if not endpoint:
                    return None

                # Create event from delivery
                event = WebhookEvent(
                    id=delivery.event_id,
                    type=delivery.event_type,
                    data={},  # Would need to store original data
                )

                # Remove from dead letters
                self._dead_letters.pop(i)

                # Retry
                return await self._deliver(endpoint, event, 1)

        return None


# =============================================================================
# FastAPI Router
# =============================================================================

webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])

# Global manager instance
webhook_manager = WebhookManager()


@webhook_router.post("/endpoints", response_model=WebhookEndpointResponse)
async def create_webhook_endpoint(request: WebhookEndpointCreate):
    """
    Register a new webhook endpoint

    The secret is only returned on creation - store it securely!
    """
    endpoint = webhook_manager.register_endpoint(
        url=str(request.url),
        events=request.events,
        description=request.description,
        metadata=request.metadata,
    )

    return WebhookEndpointResponse(
        id=endpoint.id,
        url=str(endpoint.url),
        events=endpoint.events,
        description=endpoint.description,
        is_active=endpoint.is_active,
        created_at=endpoint.created_at,
        secret=endpoint.secret,  # Only on creation
    )


@webhook_router.get("/endpoints", response_model=list[WebhookEndpointResponse])
async def list_webhook_endpoints(active_only: bool = True):
    """List all webhook endpoints"""
    endpoints = webhook_manager.list_endpoints(active_only)

    return [
        WebhookEndpointResponse(
            id=ep.id,
            url=str(ep.url),
            events=ep.events,
            description=ep.description,
            is_active=ep.is_active,
            created_at=ep.created_at,
        )
        for ep in endpoints
    ]


@webhook_router.get("/endpoints/{endpoint_id}", response_model=WebhookEndpointResponse)
async def get_webhook_endpoint(endpoint_id: str):
    """Get webhook endpoint details"""
    endpoint = webhook_manager.get_endpoint(endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return WebhookEndpointResponse(
        id=endpoint.id,
        url=str(endpoint.url),
        events=endpoint.events,
        description=endpoint.description,
        is_active=endpoint.is_active,
        created_at=endpoint.created_at,
    )


@webhook_router.delete("/endpoints/{endpoint_id}")
async def delete_webhook_endpoint(endpoint_id: str):
    """Delete a webhook endpoint"""
    if not webhook_manager.delete_endpoint(endpoint_id):
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return {"message": "Endpoint deleted", "id": endpoint_id}


@webhook_router.post("/endpoints/{endpoint_id}/rotate-secret")
async def rotate_webhook_secret(endpoint_id: str):
    """Rotate the signing secret for an endpoint"""
    new_secret = webhook_manager.rotate_secret(endpoint_id)
    if not new_secret:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    return {"message": "Secret rotated", "secret": new_secret}


@webhook_router.get("/deliveries", response_model=list[WebhookDelivery])
async def list_webhook_deliveries(
    endpoint_id: str = None,
    event_type: str = None,
    status: DeliveryStatus = None,
    limit: int = 100,
):
    """List webhook deliveries with filters"""
    return webhook_manager.list_deliveries(endpoint_id, event_type, status, limit)


@webhook_router.get("/deliveries/dead-letters", response_model=list[WebhookDelivery])
async def list_dead_letters(limit: int = 100):
    """List dead lettered deliveries"""
    return webhook_manager.get_dead_letters(limit)


@webhook_router.post("/deliveries/{delivery_id}/retry")
async def retry_dead_letter(delivery_id: str):
    """Manually retry a dead lettered delivery"""
    delivery = await webhook_manager.retry_dead_letter(delivery_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found in dead letters")

    return {"message": "Retry initiated", "delivery": delivery}


@webhook_router.post("/test/{endpoint_id}")
async def test_webhook_endpoint(endpoint_id: str):
    """Send a test event to a webhook endpoint"""
    endpoint = webhook_manager.get_endpoint(endpoint_id)
    if not endpoint:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    delivery_ids = await webhook_manager.publish(
        event_type="test.ping",
        data={
            "message": "Test webhook from DevSkyy",
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )

    return {"message": "Test event sent", "delivery_ids": delivery_ids}


# =============================================================================
# Webhook Receiver Helper
# =============================================================================


class WebhookReceiver:
    """
    Helper class for receiving and validating webhooks

    Usage:
        receiver = WebhookReceiver(secret="whsec_...")

        @app.post("/webhook")
        async def handle_webhook(request: Request):
            payload = await request.body()
            signature = request.headers.get("X-DevSkyy-Signature")

            event = receiver.verify_and_parse(payload, signature)

            if event.type == "order.created":
                handle_order(event.data)
    """

    def __init__(self, secret: str, config: WebhookConfig = None):
        self.secret = secret
        self.config = config or WebhookConfig()
        self.signer = WebhookSigner(config)

    def verify_and_parse(self, payload: bytes, signature: str) -> WebhookEvent:
        """
        Verify signature and parse webhook event

        Raises:
            ValueError: If signature is invalid or payload is malformed
        """
        payload_str = payload.decode("utf-8")

        if not self.signer.verify(payload_str, signature, self.secret):
            raise ValueError("Invalid webhook signature")

        try:
            data = json.loads(payload_str)
            return WebhookEvent(**data)
        except Exception as e:
            raise ValueError(f"Invalid webhook payload: {e}")


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Config
    "WebhookConfig",
    "WebhookEventType",
    "DeliveryStatus",
    # Models
    "WebhookEndpoint",
    "WebhookEvent",
    "WebhookDelivery",
    "WebhookEndpointCreate",
    "WebhookEndpointResponse",
    # Classes
    "WebhookSigner",
    "WebhookManager",
    "WebhookReceiver",
    # Instances
    "webhook_manager",
    # Router
    "webhook_router",
]
