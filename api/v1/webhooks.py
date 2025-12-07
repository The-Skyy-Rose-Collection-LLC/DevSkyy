import logging
import re

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl

from security.jwt_auth import TokenData, get_current_active_user, require_developer
from security.log_sanitizer import sanitize_for_log, sanitize_user_identifier
from webhooks.webhook_system import WebhookEvent, WebhookSubscription, webhook_manager


"""
Webhook API Endpoints
Manage webhook subscriptions and deliveries
"""

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# ============================================================================
# REQUEST MODELS
# ============================================================================


class CreateWebhookRequest(BaseModel):
    """Create webhook subscription request"""

    endpoint: HttpUrl
    events: list[WebhookEvent]
    secret: str | None = None
    max_retries: int = 3


class UpdateWebhookRequest(BaseModel):
    """Update webhook subscription request"""

    endpoint: HttpUrl | None = None
    events: list[WebhookEvent] | None = None
    active: bool | None = None
    max_retries: int | None = None


class TestWebhookRequest(BaseModel):
    """Test webhook request"""

    subscription_id: str


# ============================================================================
# WEBHOOK SUBSCRIPTION MANAGEMENT
# ============================================================================


@router.post(
    "/subscriptions",
    response_model=WebhookSubscription,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook_subscription(
    request: CreateWebhookRequest, current_user: TokenData = Depends(require_developer)
):
    """
    Create a new webhook subscription

    Subscribe to events and receive webhook notifications at your endpoint.
    """
    try:
        subscription = webhook_manager.create_subscription(
            endpoint=str(request.endpoint),
            events=request.events,
            secret=request.secret,
            max_retries=request.max_retries,
            metadata={"created_by": current_user.email},
        )

        logger.info(
            f"Webhook subscription created by {sanitize_user_identifier(current_user.email)}: {sanitize_for_log(subscription.subscription_id)}"
        )

        return subscription

    except Exception as e:
        logger.error(f"Failed to create webhook subscription: {sanitize_for_log(str(e))}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription",
        )


@router.get("/subscriptions", response_model=list[WebhookSubscription])
async def list_webhook_subscriptions(
    active_only: bool = True, current_user: TokenData = Depends(get_current_active_user)
):
    """
    List all webhook subscriptions

    Filter by active status.
    """
    subscriptions = webhook_manager.list_subscriptions(active_only=active_only)

    return subscriptions


@router.get("/subscriptions/{subscription_id}", response_model=WebhookSubscription)
async def get_webhook_subscription(subscription_id: str, current_user: TokenData = Depends(get_current_active_user)):
    """Get a specific webhook subscription"""
    subscription = webhook_manager.get_subscription(subscription_id)

    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    return subscription


@router.patch("/subscriptions/{subscription_id}", response_model=WebhookSubscription)
async def update_webhook_subscription(
    subscription_id: str,
    request: UpdateWebhookRequest,
    current_user: TokenData = Depends(require_developer),
):
    """
    Update a webhook subscription

    Update endpoint, events, or active status.
    """
    update_data = request.model_dump(exclude_unset=True)

    if "endpoint" in update_data:
        update_data["endpoint"] = str(update_data["endpoint"])

    subscription = webhook_manager.update_subscription(subscription_id, **update_data)

    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    logger.info(f"Webhook subscription updated: {sanitize_for_log(subscription_id)}")

    return subscription


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook_subscription(subscription_id: str, current_user: TokenData = Depends(require_developer)):
    """
    Delete a webhook subscription

    Permanently removes the subscription.
    """
    success = webhook_manager.delete_subscription(subscription_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

    logger.info(f"Webhook subscription deleted: {sanitize_for_log(subscription_id)}")


# ============================================================================
# WEBHOOK DELIVERIES
# ============================================================================


@router.get("/deliveries", response_model=list[dict])
async def list_webhook_deliveries(
    subscription_id: str | None = None,
    status_filter: str | None = None,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    List webhook deliveries

    View delivery history and status.
    """
    deliveries = webhook_manager.list_deliveries(subscription_id=subscription_id, status=status_filter, limit=limit)

    return [delivery.model_dump() for delivery in deliveries]


@router.get("/deliveries/{delivery_id}")
async def get_webhook_delivery(delivery_id: str, current_user: TokenData = Depends(get_current_active_user)):
    """Get a specific webhook delivery"""
    delivery = webhook_manager.get_delivery(delivery_id)

    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    return delivery.model_dump()


@router.post("/deliveries/{delivery_id}/retry")
async def retry_webhook_delivery(delivery_id: str, current_user: TokenData = Depends(require_developer)):
    """
    Retry a failed webhook delivery

    Manually retry a delivery that failed.
    """
    success = await webhook_manager.retry_delivery(delivery_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot retry this delivery")

    logger.info(f"Webhook delivery retried: {sanitize_for_log(delivery_id)}")

    return {"message": "Delivery queued for retry", "delivery_id": delivery_id}


# ============================================================================
# WEBHOOK TESTING
# ============================================================================


@router.post("/test")
async def test_webhook(request: TestWebhookRequest, current_user: TokenData = Depends(require_developer)):
    """
    Send a test webhook

    Sends a test event to verify webhook configuration.
    """
    try:
        # Emit test event
        delivery_ids = await webhook_manager.emit_event(
            event_type=WebhookEvent.CUSTOM,
            data={
                "message": "This is a test webhook",
                "test": True,
                "triggered_by": current_user.email,
            },
            metadata={"test": True},
        )

        return {"message": "Test webhook sent", "delivery_ids": delivery_ids}

    except Exception as e:
        logger.error(f"Failed to send test webhook: {sanitize_for_log(str(e))}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test webhook",
        )


# ============================================================================
# WEBHOOK STATISTICS
# ============================================================================


@router.get("/statistics")
async def get_webhook_statistics(
    current_user: TokenData = Depends(get_current_active_user),
):
    """
    Get webhook statistics

    View subscription and delivery statistics.
    """
    stats = webhook_manager.get_statistics()

    return stats


logger.info("✅ Webhook API endpoints registered")


def _sanitize_log_input(self, user_input):
    """Sanitize user input for safe logging."""
    if not isinstance(user_input, str):
        user_input = str(user_input)

    # Remove control characters and potential log injection
    sanitized = re.sub(r"[\r\n\t]", " ", user_input)
    sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", sanitized)

    # Limit length to prevent log flooding
    return sanitized[:500] + "..." if len(sanitized) > 500 else sanitized
