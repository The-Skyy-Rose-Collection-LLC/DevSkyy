"""
DevSkyy Webhook Integration Examples
====================================

Comprehensive examples showing how to:
1. Register webhook endpoints
2. Receive and verify webhooks
3. Handle security events
4. Integrate with external services

Author: DevSkyy Team
Version: 1.0.0
"""

from fastapi import FastAPI, HTTPException, Request

from api.webhooks import WebhookReceiver, webhook_manager
from security.security_webhooks import (
    SecurityEventSeverity,
    SecurityEventType,
    SecurityWebhookManager,
)

# =============================================================================
# Stub functions for example purposes
# =============================================================================


async def process_new_order(data: dict) -> None:
    """Process a new order event (stub implementation)."""
    print(f"Processing new order: {data.get('order_id', 'unknown')}")


async def process_completed_order(data: dict) -> None:
    """Process a completed order event (stub implementation)."""
    print(f"Processing completed order: {data.get('order_id', 'unknown')}")


async def process_cancelled_order(data: dict) -> None:
    """Process a cancelled order event (stub implementation)."""
    print(f"Processing cancelled order: {data.get('order_id', 'unknown')}")


async def send_critical_alert(data: dict) -> None:
    """Send a critical security alert (stub implementation)."""
    print(f"CRITICAL ALERT: {data}")


async def log_security_event(data: dict) -> None:
    """Log a security event (stub implementation)."""
    print(f"Security event logged: {data.get('type', 'unknown')}")


# =============================================================================
# Example 1: Register Webhook Endpoints
# =============================================================================


async def register_webhook_endpoints():
    """
    Register webhook endpoints for different event types
    """

    # Register endpoint for all order events
    order_endpoint = webhook_manager.register_endpoint(
        url="https://your-app.com/webhooks/orders",
        events=["order.*"],  # Wildcard for all order events
        description="Order processing webhook",
        metadata={"service": "order_processor", "version": "1.0"},
    )
    print(f"✅ Registered order webhook: {order_endpoint.id}")
    print(f"   Secret: {order_endpoint.secret}")
    print("   Store this secret securely!")

    # Register endpoint for security events
    security_endpoint = webhook_manager.register_endpoint(
        url="https://your-app.com/webhooks/security",
        events=[
            SecurityEventType.INTRUSION_DETECTED.value,
            SecurityEventType.BRUTE_FORCE_ATTEMPT.value,
            SecurityEventType.DATA_BREACH_DETECTED.value,
        ],
        description="Security monitoring webhook",
        metadata={"service": "security_monitor", "alert_channel": "slack"},
    )
    print(f"✅ Registered security webhook: {security_endpoint.id}")

    # Register endpoint for all events
    all_events_endpoint = webhook_manager.register_endpoint(
        url="https://your-app.com/webhooks/all",
        events=["*"],  # All events
        description="Audit log webhook",
        metadata={"service": "audit_logger"},
    )
    print(f"✅ Registered audit webhook: {all_events_endpoint.id}")

    return {
        "order": order_endpoint,
        "security": security_endpoint,
        "audit": all_events_endpoint,
    }


# =============================================================================
# Example 2: Receive and Verify Webhooks
# =============================================================================

app = FastAPI()

# Initialize webhook receiver with your secret
# (Get this from the registration response)
webhook_receiver = WebhookReceiver(secret="whsec_YOUR_SECRET_HERE")


@app.post("/webhooks/orders")
async def handle_order_webhook(request: Request):
    """
    Receive and process order webhooks

    This endpoint:
    1. Verifies the webhook signature
    2. Parses the event payload
    3. Processes the event based on type
    """
    # Get raw body and signature
    body = await request.body()
    signature = request.headers.get("X-DevSkyy-Signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature header")

    try:
        # Verify and parse the webhook
        event = webhook_receiver.verify_and_parse(body, signature)

        # Process based on event type
        if event.type == "order.created":
            await process_new_order(event.data)
        elif event.type == "order.completed":
            await process_completed_order(event.data)
        elif event.type == "order.cancelled":
            await process_cancelled_order(event.data)

        return {"status": "success", "event_id": event.id}

    except ValueError as e:
        # Invalid signature or malformed payload
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/webhooks/security")
async def handle_security_webhook(request: Request):
    """
    Receive and process security event webhooks

    Critical security events trigger immediate alerts
    """
    body = await request.body()
    signature = request.headers.get("X-DevSkyy-Signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature header")

    try:
        event = webhook_receiver.verify_and_parse(body, signature)

        # Extract security event details
        severity = event.data.get("severity")

        # Handle critical events immediately
        if severity == "critical":
            await send_critical_alert(event.data)

        # Log all security events
        await log_security_event(event.data)

        return {"status": "success", "event_id": event.id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Example 3: Send Security Events
# =============================================================================


async def send_security_events_example():
    """
    Examples of sending security events via webhooks
    """

    # Initialize security webhook manager with the main webhook manager
    sec_webhook_mgr = SecurityWebhookManager(webhook_manager=webhook_manager)

    # Example 1: Login failure
    await sec_webhook_mgr.send_security_event(
        event_type=SecurityEventType.AUTH_LOGIN_FAILED,
        severity=SecurityEventSeverity.MEDIUM,
        title="Failed Login Attempt",
        description="User attempted to login with incorrect password",
        user_id="user_12345",
        ip_address="192.168.1.100",
        endpoint="/api/v1/auth/login",
        data={
            "username": "john.doe@example.com",
            "attempt_count": 3,
            "last_success": "2025-12-15T10:30:00Z",
        },
        actions_taken=["Incremented failure counter"],
        recommended_actions=["Monitor for brute force attempts"],
    )

    # Example 2: Intrusion detected
    await sec_webhook_mgr.send_security_event(
        event_type=SecurityEventType.INTRUSION_DETECTED,
        severity=SecurityEventSeverity.CRITICAL,
        affected_resource="/api/v1/admin/users",
        actions_taken=["Blocked suspicious IP", "Alerted security team"],
        recommended_actions=["Review access logs", "Consider IP ban"],
    )
