"""
API v1 Webhooks Router
Webhook subscription management, testing, delivery tracking
Path: api/v1/webhooks

Author: DevSkyy Enterprise Team
Date: October 26, 2025
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from webhook_system import webhook_manager, WebhookEvent, WebhookSubscription, WebhookDelivery, DeliveryStatus
from jwt_auth import get_current_user, get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# ============================================================================
# MODELS
# ============================================================================


class WebhookSubscribeRequest(BaseModel):
    """Webhook subscription request"""

    endpoint: HttpUrl
    events: List[str]
    secret: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WebhookSubscribeResponse(BaseModel):
    """Webhook subscription response"""

    subscription_id: str
    endpoint: str
    events: List[str]
    active: bool
    created_at: datetime
    secret: str  # Return secret so client can verify signatures


class WebhookDeliveryResponse(BaseModel):
    """Webhook delivery record response"""

    delivery_id: str
    subscription_id: str
    event_id: str
    status: str
    attempt_number: int
    response_status_code: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    next_retry_at: Optional[datetime]


class WebhookTestResponse(BaseModel):
    """Webhook test response"""

    status: str
    delivery_id: str
    response_status_code: Optional[int]
    error_message: Optional[str]


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/subscribe", response_model=WebhookSubscribeResponse)
async def subscribe_to_webhooks(request: WebhookSubscribeRequest, current_user: Dict = Depends(get_current_user)):
    """
    Subscribe to webhook events

    Creates a new webhook subscription for the specified events.
    The client will receive HTTP POST requests to the endpoint URL
    when subscribed events occur.

    Args:
        request: WebhookSubscribeRequest with endpoint and events
        current_user: Current authenticated user (from JWT)

    Returns:
        WebhookSubscribeResponse with subscription_id and secret

    Status Codes:
        201: Successfully subscribed
        400: Invalid endpoint or events
        401: Unauthorized
    """
    try:
        # Validate events
        valid_events = [e.value for e in WebhookEvent]
        for event in request.events:
            if event not in valid_events:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event type: {event}. Valid events: {valid_events}",
                )

        # Subscribe
        subscription = await webhook_manager.subscribe(
            endpoint=str(request.endpoint), events=request.events, secret=request.secret, metadata=request.metadata
        )

        logger.info(f"Webhook subscribed by user {current_user.get('sub')}: " f"{subscription.subscription_id}")

        return WebhookSubscribeResponse(
            subscription_id=subscription.subscription_id,
            endpoint=str(subscription.endpoint),
            events=subscription.events,
            active=subscription.active,
            created_at=subscription.created_at,
            secret=subscription.secret,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to subscribe to webhooks"
        )


@router.delete("/{subscription_id}")
async def unsubscribe_from_webhooks(subscription_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Unsubscribe from webhooks

    Args:
        subscription_id: Subscription ID to remove
        current_user: Current authenticated user (from JWT)

    Returns:
        Unsubscribe confirmation

    Status Codes:
        200: Successfully unsubscribed
        404: Subscription not found
    """
    success = await webhook_manager.unsubscribe(subscription_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscription not found: {subscription_id}")

    logger.info(f"Webhook unsubscribed by user {current_user.get('sub')}: " f"{subscription_id}")

    return {"status": "success", "message": f"Successfully unsubscribed from {subscription_id}"}


@router.get("/list", response_model=List[WebhookSubscribeResponse])
async def list_subscriptions(current_user: Dict = Depends(get_current_user)):
    """
    List all active webhook subscriptions

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        List of WebhookSubscribeResponse
    """
    subscriptions = await webhook_manager.list_subscriptions()

    return [
        WebhookSubscribeResponse(
            subscription_id=sub.subscription_id,
            endpoint=str(sub.endpoint),
            events=[e.value if hasattr(e, "value") else str(e) for e in sub.events],
            active=sub.active,
            created_at=sub.created_at,
            secret=sub.secret,
        )
        for sub in subscriptions
    ]


@router.post("/{subscription_id}/test", response_model=WebhookTestResponse)
async def test_webhook(subscription_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Test webhook delivery with sample payload

    Sends a test payload to the webhook endpoint to verify delivery.
    Useful for validating webhook configuration.

    Args:
        subscription_id: Subscription ID to test
        current_user: Current authenticated user (from JWT)

    Returns:
        WebhookTestResponse with delivery status

    Status Codes:
        200: Test sent (check status for delivery result)
        404: Subscription not found
    """
    try:
        delivery = await webhook_manager.test_webhook(subscription_id)

        logger.info(
            f"Webhook test by user {current_user.get('sub')}: " f"{subscription_id} -> status {delivery.status}"
        )

        return WebhookTestResponse(
            status=delivery.status,
            delivery_id=delivery.delivery_id,
            response_status_code=delivery.response_status_code,
            error_message=delivery.error_message,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook test error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to test webhook")


@router.get("/{subscription_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_delivery_history(subscription_id: str, limit: int = 10, current_user: Dict = Depends(get_current_user)):
    """
    Get delivery history for a subscription

    Returns recent webhook delivery attempts (sent, failed, retrying)

    Args:
        subscription_id: Subscription ID
        limit: Maximum number of records to return (default: 10, max: 100)
        current_user: Current authenticated user (from JWT)

    Returns:
        List of WebhookDeliveryResponse in reverse chronological order

    Status Codes:
        200: Success
        404: Subscription not found
    """
    # Validate limit
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1

    try:
        deliveries = await webhook_manager.get_delivery_history(subscription_id, limit)

        return [
            WebhookDeliveryResponse(
                delivery_id=d.delivery_id,
                subscription_id=d.subscription_id,
                event_id=d.event_id,
                status=d.status,
                attempt_number=d.attempt_number,
                response_status_code=d.response_status_code,
                error_message=d.error_message,
                created_at=d.created_at,
                updated_at=d.updated_at,
                next_retry_at=d.next_retry_at,
            )
            for d in deliveries
        ]

    except Exception as e:
        logger.error(f"Delivery history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve delivery history"
        )


@router.get("/{subscription_id}/info", response_model=WebhookSubscribeResponse)
async def get_subscription_info(subscription_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Get information about a specific subscription

    Args:
        subscription_id: Subscription ID
        current_user: Current authenticated user (from JWT)

    Returns:
        WebhookSubscribeResponse with subscription details

    Status Codes:
        200: Success
        404: Subscription not found
    """
    subscription = await webhook_manager.get_subscription(subscription_id)

    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Subscription not found: {subscription_id}")

    return WebhookSubscribeResponse(
        subscription_id=subscription.subscription_id,
        endpoint=str(subscription.endpoint),
        events=[e.value if hasattr(e, "value") else str(e) for e in subscription.events],
        active=subscription.active,
        created_at=subscription.created_at,
        secret=subscription.secret,
    )


@router.get("/events/list", response_model=Dict[str, List[str]])
async def list_webhook_events(current_user: Dict = Depends(get_current_user)):
    """
    List all available webhook event types

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        Dictionary mapping event categories to event types
    """
    events_by_category = {
        "agent": ["agent.started", "agent.completed", "agent.failed"],
        "scanning": ["scan.completed", "scan.failed"],
        "fixing": ["fix.completed", "fix.failed"],
        "products": ["product.created", "product.updated", "product.deleted"],
        "orders": ["order.created", "order.updated", "order.cancelled"],
        "inventory": ["inventory.low", "inventory.out", "inventory.restocked"],
        "themes": ["theme.generated", "theme.deployed"],
        "security": ["security.threat", "security.audit"],
        "system": ["system.error", "system.warning"],
        "custom": ["custom.event"],
    }

    return events_by_category
