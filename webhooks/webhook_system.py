"""
Enterprise Webhook System
RFC 2104 HMAC-SHA256 signatures, exponential backoff, delivery tracking
Author: DevSkyy Enterprise Team
Date: October 26, 2025

Citation: RFC 2104 (HMAC: Keyed-Hashing for Message Authentication)
"""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

import httpx
from pydantic import BaseModel, HttpUrl, validator
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS
# ============================================================================

class WebhookEvent(str, Enum):
    """Webhook event types"""
    
    # Agent Events
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    
    # Code Scanning
    SCAN_COMPLETED = "scan.completed"
    SCAN_FAILED = "scan.failed"
    
    # Code Fixing
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

class DeliveryStatus(str, Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    PERMANENTLY_FAILED = "permanently_failed"

# ============================================================================
# MODELS
# ============================================================================

class WebhookSubscription(BaseModel):
    """Webhook subscription configuration"""
    
    subscription_id: str = None
    endpoint: HttpUrl
    events: List[WebhookEvent]
    secret: str  # HMAC secret for signature generation
    active: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 30
    created_at: datetime = None
    metadata: Dict[str, Any] = {}
    
    @validator("subscription_id", pre=True, always=True)
    def set_subscription_id(cls, v):
        return v or str(uuid4())
    
    @validator("created_at", pre=True, always=True)
    def set_created_at(cls, v):
        return v or datetime.now(timezone.utc)

class WebhookPayload(BaseModel):
    """Webhook payload structure (RFC 2104 for signature)"""
    
    event_id: str  # Unique event identifier
    event_type: WebhookEvent
    timestamp: datetime
    data: Dict[str, Any]
    idempotency_key: str = None  # Prevent duplicate processing
    
    @validator("event_id", pre=True, always=True)
    def set_event_id(cls, v):
        return v or str(uuid4())
    
    @validator("idempotency_key", pre=True, always=True)
    def set_idempotency_key(cls, v):
        return v or str(uuid4())

class WebhookDelivery(BaseModel):
    """Webhook delivery record (for tracking)"""
    
    delivery_id: str
    subscription_id: str
    event_id: str
    status: DeliveryStatus
    attempt_number: int
    request_body: str  # JSON payload
    request_headers: Dict[str, str]
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    next_retry_at: Optional[datetime] = None

# ============================================================================
# SIGNATURE GENERATION (RFC 2104)
# ============================================================================

def generate_signature(payload: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook payload (RFC 2104)
    
    Args:
        payload: JSON payload to sign
        secret: HMAC secret key
        
    Returns:
        Hex-encoded HMAC-SHA256 signature
        
    Citation: RFC 2104 Section 2 (HMAC Definition)
    """
    signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """
    Verify HMAC-SHA256 signature
    
    Args:
        payload: Original JSON payload
        signature: Signature to verify
        secret: HMAC secret key
        
    Returns:
        True if signature valid
    """
    expected_signature = generate_signature(payload, secret)
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected_signature, signature)

# ============================================================================
# WEBHOOK MANAGER
# ============================================================================

class WebhookManager:
    """
    Enterprise webhook management system
    
    Features:
    - HMAC-SHA256 signatures (RFC 2104)
    - Exponential backoff retry
    - Circuit breaker per destination
    - Delivery tracking
    - Idempotency
    """
    
    def __init__(self):
        """Initialize webhook manager"""
        self.subscriptions: Dict[str, WebhookSubscription] = {}
        self.delivery_history: List[WebhookDelivery] = []
        self.failed_deliveries: Dict[str, int] = {}  # Track failures per endpoint
        self.circuit_breaker_threshold = 5  # Fail open after 5 consecutive failures
        
        logger.info("Webhook manager initialized")
    
    async def subscribe(
        self,
        endpoint: str,
        events: List[str],
        secret: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> WebhookSubscription:
        """
        Subscribe to webhook events
        
        Args:
            endpoint: Webhook destination URL
            events: List of event types to subscribe to
            secret: Secret for HMAC signature (auto-generated if not provided)
            metadata: Optional metadata
            
        Returns:
            WebhookSubscription with subscription_id
        """
        if not secret:
            secret = secrets.token_urlsafe(32)
        
        subscription = WebhookSubscription(
            endpoint=endpoint,
            events=[WebhookEvent(e) for e in events],
            secret=secret,
            metadata=metadata or {}
        )
        
        self.subscriptions[subscription.subscription_id] = subscription
        
        logger.info(
            f"Webhook subscribed: {subscription.subscription_id} -> {endpoint} "
            f"({len(events)} events)"
        )
        
        return subscription
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from webhooks
        
        Args:
            subscription_id: Subscription to remove
            
        Returns:
            True if successfully removed
        """
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Webhook unsubscribed: {subscription_id}")
            return True
        return False
    
    async def emit(self, event_type: WebhookEvent, data: Dict[str, Any]):
        """
        Emit webhook event to all subscribed endpoints
        
        Args:
            event_type: Type of event to emit
            data: Event data
        """
        payload = WebhookPayload(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            data=data
        )
        
        # Find all subscriptions for this event type
        matching_subscriptions = [
            sub for sub in self.subscriptions.values()
            if event_type in sub.events and sub.active
        ]
        
        # Deliver to all matching subscriptions
        tasks = [
            self._deliver_webhook(sub, payload)
            for sub in matching_subscriptions
        ]
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.debug(f"Event '{event_type}' emitted to {len(matching_subscriptions)} subscribers")
    
    async def _deliver_webhook(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
        attempt: int = 1
    ):
        """
        Deliver webhook with retry logic (exponential backoff)
        
        Args:
            subscription: Target subscription
            payload: Webhook payload
            attempt: Attempt number (for exponential backoff)
        """
        payload_json = payload.json()
        signature = generate_signature(payload_json, subscription.secret)
        
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": payload.event_type,
            "X-Webhook-ID": payload.event_id,
            "X-Webhook-Signature": f"sha256={signature}",
            "X-Webhook-Timestamp": payload.timestamp.isoformat(),
            "X-Idempotency-Key": payload.idempotency_key
        }
        
        delivery = WebhookDelivery(
            delivery_id=str(uuid4()),
            subscription_id=subscription.subscription_id,
            event_id=payload.event_id,
            status=DeliveryStatus.PENDING,
            attempt_number=attempt,
            request_body=payload_json,
            request_headers=headers,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        try:
            # Check circuit breaker
            failure_count = self.failed_deliveries.get(str(subscription.endpoint), 0)
            if failure_count >= self.circuit_breaker_threshold:
                logger.warning(
                    f"Circuit breaker OPEN for {subscription.endpoint} "
                    f"({failure_count} failures)"
                )
                delivery.status = DeliveryStatus.PERMANENTLY_FAILED
                delivery.error_message = "Circuit breaker open - too many failures"
                self.delivery_history.append(delivery)
                return
            
            # Send webhook with timeout
            async with httpx.AsyncClient(timeout=subscription.timeout_seconds) as client:
                response = await client.post(
                    str(subscription.endpoint),
                    content=payload_json,
                    headers=headers
                )
                
                delivery.response_status_code = response.status_code
                delivery.response_body = response.text[:1000]  # Truncate for storage
                
                if response.status_code in [200, 201, 202, 204]:
                    delivery.status = DeliveryStatus.SENT
                    self.failed_deliveries[str(subscription.endpoint)] = 0
                    logger.info(
                        f"Webhook delivered: {payload.event_type} -> "
                        f"{subscription.endpoint} (attempt {attempt})"
                    )
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text[:100]}")
        
        except Exception as e:
            delivery.error_message = str(e)
            
            # Decide if we should retry
            if attempt < subscription.max_retries:
                delivery.status = DeliveryStatus.RETRYING
                
                # Exponential backoff: 60s, 120s, 240s, ...
                backoff_seconds = subscription.retry_delay_seconds * (2 ** (attempt - 1))
                next_retry = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
                delivery.next_retry_at = next_retry
                
                logger.warning(
                    f"Webhook delivery failed (attempt {attempt}/{subscription.max_retries}): "
                    f"{str(e)}. Retrying in {backoff_seconds}s..."
                )
                
                # Schedule retry
                asyncio.create_task(
                    asyncio.sleep(backoff_seconds)
                )
                await self._deliver_webhook(subscription, payload, attempt + 1)
            else:
                delivery.status = DeliveryStatus.PERMANENTLY_FAILED
                self.failed_deliveries[str(subscription.endpoint)] = \
                    self.failed_deliveries.get(str(subscription.endpoint), 0) + 1
                
                logger.error(
                    f"Webhook permanently failed after {attempt} attempts: "
                    f"{subscription.endpoint} - {str(e)}"
                )
        
        finally:
            delivery.updated_at = datetime.now(timezone.utc)
            self.delivery_history.append(delivery)
    
    async def test_webhook(self, subscription_id: str) -> WebhookDelivery:
        """
        Test webhook delivery with sample payload
        
        Args:
            subscription_id: Subscription to test
            
        Returns:
            WebhookDelivery record with test result
        """
        subscription = self.subscriptions.get(subscription_id)
        if not subscription:
            raise ValueError(f"Subscription not found: {subscription_id}")
        
        test_payload = WebhookPayload(
            event_type=WebhookEvent.CUSTOM,
            timestamp=datetime.now(timezone.utc),
            data={"test": True, "message": "Webhook test delivery"}
        )
        
        await self._deliver_webhook(subscription, test_payload)
        
        # Return last delivery record
        return self.delivery_history[-1]
    
    async def get_delivery_history(
        self,
        subscription_id: str,
        limit: int = 10
    ) -> List[WebhookDelivery]:
        """
        Get delivery history for a subscription
        
        Args:
            subscription_id: Subscription ID
            limit: Maximum number of records to return
            
        Returns:
            List of WebhookDelivery records
        """
        matching = [
            d for d in self.delivery_history
            if d.subscription_id == subscription_id
        ]
        return matching[-limit:]  # Return most recent
    
    async def get_subscription(self, subscription_id: str) -> Optional[WebhookSubscription]:
        """Get subscription by ID"""
        return self.subscriptions.get(subscription_id)
    
    async def list_subscriptions(self) -> List[WebhookSubscription]:
        """List all subscriptions"""
        return list(self.subscriptions.values())

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

webhook_manager = WebhookManager()

if __name__ == "__main__":
    # Demo usage
    async def demo():
        # Subscribe
        sub = await webhook_manager.subscribe(
            endpoint="https://example.com/webhook",
            events=["agent.completed", "product.created"],
            metadata={"source": "demo"}
        )
        print(f"Subscription created: {sub.subscription_id}")
        
        # Emit event
        await webhook_manager.emit(
            WebhookEvent.AGENT_COMPLETED,
            {"agent_id": "scanner", "status": "success"}
        )
    
    asyncio.run(demo())
