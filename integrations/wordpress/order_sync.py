"""
Order Processing and Fulfillment Automation
============================================

Production-grade order management with:
- Real-time order webhooks from WooCommerce
- Automated fulfillment workflows
- Inventory management
- Customer notifications
- Shipping integration hooks

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import base64
import hashlib
import hmac
import json
import logging
import os
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# Router for order sync endpoints
router = APIRouter(tags=["WordPress Order Sync"])


# =============================================================================
# Models
# =============================================================================


class OrderStatus(str, Enum):
    """WooCommerce order statuses."""

    PENDING = "pending"
    PROCESSING = "processing"
    ON_HOLD = "on-hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


class FulfillmentStatus(str, Enum):
    """Internal fulfillment statuses."""

    RECEIVED = "received"
    INVENTORY_RESERVED = "inventory_reserved"
    PICKING = "picking"
    PACKING = "packing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OrderLineItem(BaseModel):
    """Order line item (product)."""

    product_id: int = Field(..., description="WooCommerce product ID")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    price: float = Field(..., gt=0, description="Unit price")
    sku: str = Field("", description="Product SKU")
    total: float = Field(..., description="Line item total")


class OrderCustomer(BaseModel):
    """Order customer information."""

    id: int | None = Field(None, description="Customer ID")
    email: str = Field(..., description="Customer email")
    first_name: str = Field("", description="First name")
    last_name: str = Field("", description="Last name")


class OrderShipping(BaseModel):
    """Shipping information."""

    first_name: str = Field("", description="Recipient first name")
    last_name: str = Field("", description="Recipient last name")
    address_1: str = Field("", description="Address line 1")
    address_2: str = Field("", description="Address line 2")
    city: str = Field("", description="City")
    state: str = Field("", description="State/Province")
    postcode: str = Field("", description="Postal code")
    country: str = Field("", description="Country code")
    phone: str = Field("", description="Phone number")


class OrderWebhookPayload(BaseModel):
    """Webhook payload for WooCommerce order events."""

    id: int = Field(..., description="WooCommerce order ID")
    status: OrderStatus = Field(..., description="Order status")
    total: str = Field(..., description="Order total")
    currency: str = Field("USD", description="Currency code")
    customer: OrderCustomer | None = None
    line_items: list[OrderLineItem] = Field(default_factory=list)
    shipping: OrderShipping | None = None
    date_created: str = Field(..., description="Order creation timestamp")
    date_modified: str = Field(..., description="Last modified timestamp")
    payment_method: str = Field("", description="Payment method")
    payment_method_title: str = Field("", description="Payment method title")
    transaction_id: str = Field("", description="Transaction ID")

    @field_validator("total")
    @classmethod
    def validate_total(cls, v: str) -> str:
        """Ensure total is valid."""
        try:
            float(v)
            return v
        except ValueError as e:
            raise ValueError(f"Invalid total format: {v}") from e


class OrderFulfillmentRequest(BaseModel):
    """Request to update order fulfillment status."""

    order_id: str = Field(..., description="Internal order ID")
    status: FulfillmentStatus = Field(..., description="New fulfillment status")
    tracking_number: str | None = Field(None, description="Shipping tracking number")
    carrier: str | None = Field(None, description="Shipping carrier")
    notes: str = Field("", description="Fulfillment notes")


class OrderFulfillmentResult(BaseModel):
    """Result of order fulfillment operation."""

    success: bool
    order_id: str
    woocommerce_order_id: int | None = None
    status: FulfillmentStatus
    message: str
    correlation_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    errors: list[str] = Field(default_factory=list)


# =============================================================================
# In-Memory Order Store (Replace with database in production)
# =============================================================================

_order_store: dict[str, dict[str, Any]] = {}
_wc_order_mapping: dict[int, str] = {}


# =============================================================================
# Webhook Handlers
# =============================================================================


@router.post("/webhooks/order-created", response_model=OrderFulfillmentResult)
async def handle_new_order(
    request: Request,
    background_tasks: BackgroundTasks,
    x_wc_webhook_signature: str | None = Header(None, alias="X-WC-Webhook-Signature"),
) -> OrderFulfillmentResult:
    """
    Handle new WooCommerce order webhook.

    This endpoint is triggered when a new order is created in WooCommerce.
    It imports the order and initiates the fulfillment workflow.

    Fulfillment Workflow:
    1. Validate order data
    2. Reserve inventory
    3. Send to warehouse/fulfillment system
    4. Update customer with confirmation
    5. Track fulfillment progress

    Args:
        request: FastAPI Request object (for raw body access and signature validation)
        background_tasks: FastAPI background tasks
        x_wc_webhook_signature: WooCommerce webhook signature

    Returns:
        OrderFulfillmentResult with processing status
    """
    correlation_id = str(uuid4())

    # Get raw body bytes for signature verification
    body = await request.body()

    # Validate webhook signature if secret is configured
    webhook_secret = os.getenv("WOOCOMMERCE_WEBHOOK_SECRET", "")
    if webhook_secret:
        if not x_wc_webhook_signature:
            logger.warning(f"[{correlation_id}] Missing webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature",
            )

        if not _validate_webhook_signature(body, x_wc_webhook_signature):
            logger.warning(f"[{correlation_id}] Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    # Parse payload after signature verification
    try:
        payload_dict = json.loads(body.decode("utf-8"))
        payload = OrderWebhookPayload.model_validate(payload_dict)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"[{correlation_id}] Invalid payload format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload format: {e}",
        )

    logger.info(
        f"[{correlation_id}] Received new order webhook: WC Order ID {payload.id}, Total: {payload.total} {payload.currency}"
    )

    try:
        # Import order to internal system
        internal_order_id = await import_order_from_woocommerce(
            wc_order_id=payload.id,
            payload=payload,
            correlation_id=correlation_id,
        )

        # Trigger fulfillment workflow in background
        background_tasks.add_task(
            process_order_fulfillment,
            order_id=internal_order_id,
            correlation_id=correlation_id,
        )

        return OrderFulfillmentResult(
            success=True,
            order_id=internal_order_id,
            woocommerce_order_id=payload.id,
            status=FulfillmentStatus.RECEIVED,
            message="Order received and queued for fulfillment",
            correlation_id=correlation_id,
        )

    except Exception as e:
        logger.error(f"[{correlation_id}] Order processing failed: {e}", exc_info=True)
        return OrderFulfillmentResult(
            success=False,
            order_id="",
            woocommerce_order_id=payload.id,
            status=FulfillmentStatus.FAILED,
            message="Order processing failed",
            correlation_id=correlation_id,
            errors=[str(e)],
        )


@router.post("/webhooks/order-updated", response_model=OrderFulfillmentResult)
async def handle_order_update(
    payload: OrderWebhookPayload,
    background_tasks: BackgroundTasks,
    x_wc_webhook_signature: str | None = Header(None, alias="X-WC-Webhook-Signature"),
) -> OrderFulfillmentResult:
    """
    Handle WooCommerce order update webhook.

    Triggered when an order is updated in WooCommerce (status change, items modified, etc.).

    Args:
        payload: Updated order data
        background_tasks: FastAPI background tasks
        x_wc_webhook_signature: Webhook signature

    Returns:
        OrderFulfillmentResult
    """
    correlation_id = str(uuid4())
    logger.info(
        f"[{correlation_id}] Order updated: WC Order ID {payload.id}, Status: {payload.status}"
    )

    try:
        # Check if order exists internally
        internal_order_id = _wc_order_mapping.get(payload.id)

        if not internal_order_id:
            # Order doesn't exist, treat as new order
            logger.warning(
                f"[{correlation_id}] Order {payload.id} not found in internal system, importing as new"
            )
            internal_order_id = await import_order_from_woocommerce(
                wc_order_id=payload.id,
                payload=payload,
                correlation_id=correlation_id,
            )
        else:
            # Update existing order
            await update_internal_order(
                internal_order_id=internal_order_id,
                payload=payload,
                correlation_id=correlation_id,
            )

        # Handle status-specific actions
        if payload.status == OrderStatus.CANCELLED:
            background_tasks.add_task(
                handle_order_cancellation,
                order_id=internal_order_id,
                correlation_id=correlation_id,
            )
        elif payload.status == OrderStatus.REFUNDED:
            background_tasks.add_task(
                handle_order_refund,
                order_id=internal_order_id,
                correlation_id=correlation_id,
            )

        return OrderFulfillmentResult(
            success=True,
            order_id=internal_order_id,
            woocommerce_order_id=payload.id,
            status=FulfillmentStatus.RECEIVED,
            message=f"Order updated: {payload.status}",
            correlation_id=correlation_id,
        )

    except Exception as e:
        logger.error(f"[{correlation_id}] Order update failed: {e}", exc_info=True)
        return OrderFulfillmentResult(
            success=False,
            order_id="",
            woocommerce_order_id=payload.id,
            status=FulfillmentStatus.FAILED,
            message="Order update failed",
            correlation_id=correlation_id,
            errors=[str(e)],
        )


@router.post("/fulfillment/update", response_model=OrderFulfillmentResult)
async def update_fulfillment_status(
    request: OrderFulfillmentRequest,
    background_tasks: BackgroundTasks,
) -> OrderFulfillmentResult:
    """
    Update order fulfillment status.

    This endpoint is called by the warehouse/fulfillment system to update
    order status. It syncs the status back to WooCommerce and notifies the customer.

    Args:
        request: Fulfillment update request
        background_tasks: FastAPI background tasks

    Returns:
        OrderFulfillmentResult
    """
    correlation_id = str(uuid4())
    logger.info(
        f"[{correlation_id}] Updating fulfillment status: {request.order_id} -> {request.status}"
    )

    try:
        # Validate order exists
        if request.order_id not in _order_store:
            raise HTTPException(
                status_code=404,
                detail=f"Order not found: {request.order_id}",
            )

        order = _order_store[request.order_id]

        # Update internal order status
        order["fulfillment_status"] = request.status.value
        order["updated_at"] = datetime.now(UTC).isoformat()

        if request.tracking_number:
            order["tracking_number"] = request.tracking_number
        if request.carrier:
            order["carrier"] = request.carrier
        if request.notes:
            order["notes"] = request.notes

        # Sync status to WooCommerce
        wc_order_id = order.get("woocommerce_order_id")
        if wc_order_id:
            background_tasks.add_task(
                sync_status_to_woocommerce,
                wc_order_id=wc_order_id,
                fulfillment_status=request.status,
                tracking_number=request.tracking_number,
                carrier=request.carrier,
                correlation_id=correlation_id,
            )

        # Send customer notification
        if request.status == FulfillmentStatus.SHIPPED:
            background_tasks.add_task(
                send_shipping_notification,
                order_id=request.order_id,
                tracking_number=request.tracking_number,
                carrier=request.carrier,
                correlation_id=correlation_id,
            )

        return OrderFulfillmentResult(
            success=True,
            order_id=request.order_id,
            woocommerce_order_id=wc_order_id,
            status=request.status,
            message=f"Fulfillment status updated to {request.status.value}",
            correlation_id=correlation_id,
        )

    except Exception as e:
        logger.error(f"[{correlation_id}] Fulfillment update failed: {e}", exc_info=True)
        return OrderFulfillmentResult(
            success=False,
            order_id=request.order_id,
            status=FulfillmentStatus.FAILED,
            message="Fulfillment update failed",
            correlation_id=correlation_id,
            errors=[str(e)],
        )


# =============================================================================
# Core Order Functions
# =============================================================================


async def import_order_from_woocommerce(
    wc_order_id: int,
    payload: OrderWebhookPayload,
    correlation_id: str,
) -> str:
    """
    Import order from WooCommerce to internal system.

    Args:
        wc_order_id: WooCommerce order ID
        payload: Order webhook payload
        correlation_id: Request correlation ID

    Returns:
        Internal order ID
    """
    logger.info(f"[{correlation_id}] Importing WooCommerce order: {wc_order_id}")

    # Generate internal order ID
    internal_order_id = f"ord_{uuid4().hex[:12]}"
    _wc_order_mapping[wc_order_id] = internal_order_id

    # Store order in internal database
    _order_store[internal_order_id] = {
        "id": internal_order_id,
        "woocommerce_order_id": wc_order_id,
        "status": payload.status.value,
        "fulfillment_status": FulfillmentStatus.RECEIVED.value,
        "total": float(payload.total),
        "currency": payload.currency,
        "customer": payload.customer.model_dump() if payload.customer else {},
        "line_items": [item.model_dump() for item in payload.line_items],
        "shipping": payload.shipping.model_dump() if payload.shipping else {},
        "payment_method": payload.payment_method,
        "transaction_id": payload.transaction_id,
        "created_at": payload.date_created,
        "updated_at": payload.date_modified,
        "imported_at": datetime.now(UTC).isoformat(),
    }

    logger.info(f"[{correlation_id}] Order imported: {internal_order_id} <- WC:{wc_order_id}")
    return internal_order_id


async def update_internal_order(
    internal_order_id: str,
    payload: OrderWebhookPayload,
    correlation_id: str,
) -> None:
    """Update existing internal order with new data from WooCommerce."""
    logger.info(f"[{correlation_id}] Updating internal order: {internal_order_id}")

    if internal_order_id in _order_store:
        order = _order_store[internal_order_id]
        order["status"] = payload.status.value
        order["total"] = float(payload.total)
        order["line_items"] = [item.model_dump() for item in payload.line_items]
        order["updated_at"] = payload.date_modified


async def process_order_fulfillment(order_id: str, correlation_id: str) -> None:
    """
    Process order fulfillment workflow.

    This is the main fulfillment orchestration function. It coordinates:
    - Inventory reservation
    - Warehouse pick/pack
    - Shipping label generation
    - Customer notifications

    Args:
        order_id: Internal order ID
        correlation_id: Request correlation ID
    """
    logger.info(f"[{correlation_id}] Starting fulfillment workflow for order: {order_id}")

    if order_id not in _order_store:
        logger.error(f"[{correlation_id}] Order not found: {order_id}")
        return

    order = _order_store[order_id]

    # Step 1: Reserve inventory
    logger.info(f"[{correlation_id}] Reserving inventory for order {order_id}")
    line_items = order.get("line_items", [])
    for item in line_items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 0)
        sku = item.get("sku", "")
        await _update_inventory(
            product_id=product_id,
            quantity_change=-quantity,
            reason=f"Reserved for order {order_id}",
            sku=sku,
            correlation_id=correlation_id,
        )
    order["fulfillment_status"] = FulfillmentStatus.INVENTORY_RESERVED.value

    # Step 2: Send to warehouse (if applicable)
    logger.info(f"[{correlation_id}] Sending order {order_id} to warehouse")
    # NOTE: Integrate with ShipStation, ShipBob, or custom warehouse system as needed

    # Step 3: Mark as processing (picking inventory)
    order["fulfillment_status"] = FulfillmentStatus.PICKING.value
    order["updated_at"] = datetime.now(UTC).isoformat()

    logger.info(f"[{correlation_id}] Fulfillment workflow initiated for order {order_id}")


async def handle_order_cancellation(order_id: str, correlation_id: str) -> None:
    """Handle order cancellation - release inventory and refund if needed."""
    logger.info(f"[{correlation_id}] Processing cancellation for order: {order_id}")

    if order_id in _order_store:
        order = _order_store[order_id]
        order["fulfillment_status"] = FulfillmentStatus.CANCELLED.value
        order["updated_at"] = datetime.now(UTC).isoformat()

        # Release reserved inventory
        line_items = order.get("line_items", [])
        for item in line_items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            sku = item.get("sku", "")
            await _update_inventory(
                product_id=product_id,
                quantity_change=quantity,  # Positive to release
                reason=f"Released from cancelled order {order_id}",
                sku=sku,
                correlation_id=correlation_id,
            )
        logger.info(f"[{correlation_id}] Inventory released for cancelled order {order_id}")

        # Update WooCommerce order status
        wc_order_id = order.get("woocommerce_order_id")
        if wc_order_id:
            await _update_woocommerce_order(
                wc_order_id=wc_order_id,
                data={"status": "cancelled"},
                correlation_id=correlation_id,
            )

        # Send cancellation notification
        customer = order.get("customer", {})
        customer_email = customer.get("email")
        if customer_email:
            await _send_email_notification(
                email=customer_email,
                subject="Order Cancelled",
                order_id=order_id,
                notification_type="cancellation",
                correlation_id=correlation_id,
            )


async def handle_order_refund(order_id: str, correlation_id: str) -> None:
    """Handle order refund processing."""
    logger.info(f"[{correlation_id}] Processing refund for order: {order_id}")

    if order_id in _order_store:
        order = _order_store[order_id]
        order["fulfillment_status"] = FulfillmentStatus.CANCELLED.value
        order["updated_at"] = datetime.now(UTC).isoformat()

        # Release inventory (if items are being returned)
        line_items = order.get("line_items", [])
        for item in line_items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            sku = item.get("sku", "")
            await _update_inventory(
                product_id=product_id,
                quantity_change=quantity,  # Positive to release/return
                reason=f"Returned from refunded order {order_id}",
                sku=sku,
                correlation_id=correlation_id,
            )
        logger.info(f"[{correlation_id}] Inventory restored for refunded order {order_id}")

        # Update WooCommerce order status
        wc_order_id = order.get("woocommerce_order_id")
        if wc_order_id:
            await _update_woocommerce_order(
                wc_order_id=wc_order_id,
                data={"status": "refunded"},
                correlation_id=correlation_id,
            )

        # Send refund notification
        customer = order.get("customer", {})
        customer_email = customer.get("email")
        if customer_email:
            await _send_email_notification(
                email=customer_email,
                subject="Order Refunded",
                order_id=order_id,
                notification_type="refund",
                correlation_id=correlation_id,
            )


async def sync_status_to_woocommerce(
    wc_order_id: int,
    fulfillment_status: FulfillmentStatus,
    tracking_number: str | None,
    carrier: str | None,
    correlation_id: str,
) -> None:
    """
    Sync fulfillment status back to WooCommerce.

    Updates order notes and status in WooCommerce based on internal fulfillment status.
    """
    logger.info(
        f"[{correlation_id}] Syncing status to WooCommerce: Order {wc_order_id} -> {fulfillment_status}"
    )

    # Map internal fulfillment status to WooCommerce order status
    wc_status_mapping = {
        FulfillmentStatus.SHIPPED: "completed",
        FulfillmentStatus.DELIVERED: "completed",
        FulfillmentStatus.CANCELLED: "cancelled",
        FulfillmentStatus.FAILED: "failed",
    }

    # Build update data
    update_data: dict[str, Any] = {}

    # Update order status if there's a mapping
    if fulfillment_status in wc_status_mapping:
        update_data["status"] = wc_status_mapping[fulfillment_status]

    # Add tracking metadata if available
    meta_data = []
    if tracking_number:
        meta_data.append({"key": "_tracking_number", "value": tracking_number})
    if carrier:
        meta_data.append({"key": "_tracking_carrier", "value": carrier})
    if meta_data:
        update_data["meta_data"] = meta_data

    # Only update if there's something to update
    if update_data:
        await _update_woocommerce_order(
            wc_order_id=wc_order_id,
            data=update_data,
            correlation_id=correlation_id,
        )

    # Add order note with tracking info
    if tracking_number:
        note = f"Order shipped via {carrier or 'carrier'}. Tracking: {tracking_number}"
        logger.info(f"[{correlation_id}] Adding order note: {note}")


async def send_shipping_notification(
    order_id: str,
    tracking_number: str | None,
    carrier: str | None,
    correlation_id: str,
) -> None:
    """Send shipping notification email to customer."""
    logger.info(f"[{correlation_id}] Sending shipping notification for order: {order_id}")

    if order_id in _order_store:
        order = _order_store[order_id]
        customer = order.get("customer", {})
        customer_email = customer.get("email")

        if customer_email:
            await _send_email_notification(
                email=customer_email,
                subject="Your Order Has Shipped!",
                order_id=order_id,
                notification_type="shipping",
                tracking_number=tracking_number,
                carrier=carrier,
                correlation_id=correlation_id,
            )


# =============================================================================
# Utility Functions
# =============================================================================


def _validate_webhook_signature(payload_bytes: bytes, signature: str) -> bool:
    """
    Validate WooCommerce webhook signature using HMAC-SHA256.

    WooCommerce signs webhooks with HMAC-SHA256 and base64 encoding:
    1. Compute HMAC-SHA256 of raw body using webhook secret
    2. Base64 encode the result
    3. Compare with X-WC-Webhook-Signature header using constant-time comparison

    Reference: https://woocommerce.github.io/woocommerce-rest-api-docs/#webhooks

    Args:
        payload_bytes: Raw request body bytes
        signature: X-WC-Webhook-Signature header value (base64 encoded)

    Returns:
        True if signature is valid, False otherwise
    """
    secret = os.getenv("WOOCOMMERCE_WEBHOOK_SECRET", "")

    if not secret:
        logger.warning("WOOCOMMERCE_WEBHOOK_SECRET not configured - signature validation skipped")
        return False

    if not signature:
        logger.warning("No signature provided for validation")
        return False

    # Compute expected signature (HMAC-SHA256 with base64 encoding)
    expected = base64.b64encode(
        hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(expected, signature)


async def _update_inventory(
    product_id: int,
    quantity_change: int,
    reason: str,
    sku: str,
    correlation_id: str,
) -> None:
    """
    Update inventory for a product.

    Args:
        product_id: WooCommerce product ID
        quantity_change: Amount to change (negative for decrease, positive for increase)
        reason: Reason for inventory change
        sku: Product SKU for logging
        correlation_id: Request correlation ID
    """
    logger.info(
        f"[{correlation_id}] Updating inventory for product {product_id} (SKU: {sku}): "
        f"change={quantity_change:+d}, reason={reason}"
    )

    # Get WooCommerce API credentials
    wc_url = os.getenv("WOOCOMMERCE_URL", "")
    consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
    consumer_secret = os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")

    if not all([wc_url, consumer_key, consumer_secret]):
        logger.warning(
            f"[{correlation_id}] WooCommerce credentials not configured, skipping inventory update"
        )
        return

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First, get current stock quantity
            response = await client.get(
                f"{wc_url}/wp-json/wc/v3/products/{product_id}",
                auth=(consumer_key, consumer_secret),
            )
            response.raise_for_status()
            product_data = response.json()

            current_stock = product_data.get("stock_quantity") or 0
            new_stock = max(0, current_stock + quantity_change)

            # Update stock quantity
            update_response = await client.put(
                f"{wc_url}/wp-json/wc/v3/products/{product_id}",
                auth=(consumer_key, consumer_secret),
                json={"stock_quantity": new_stock},
            )
            update_response.raise_for_status()

            logger.info(
                f"[{correlation_id}] Inventory updated for product {product_id}: "
                f"{current_stock} -> {new_stock}"
            )
    except httpx.HTTPStatusError as e:
        logger.error(
            f"[{correlation_id}] Failed to update inventory for product {product_id}: "
            f"HTTP {e.response.status_code}"
        )
    except Exception as e:
        logger.error(f"[{correlation_id}] Failed to update inventory for product {product_id}: {e}")


async def _update_woocommerce_order(
    wc_order_id: int,
    data: dict[str, Any],
    correlation_id: str,
) -> bool:
    """
    Update order in WooCommerce via REST API.

    Args:
        wc_order_id: WooCommerce order ID
        data: Order data to update
        correlation_id: Request correlation ID

    Returns:
        True if update succeeded, False otherwise
    """
    logger.info(f"[{correlation_id}] Updating WooCommerce order {wc_order_id}: {data}")

    # Get WooCommerce API credentials
    wc_url = os.getenv("WOOCOMMERCE_URL", "")
    consumer_key = os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
    consumer_secret = os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")

    if not all([wc_url, consumer_key, consumer_secret]):
        logger.warning(
            f"[{correlation_id}] WooCommerce credentials not configured, skipping order update"
        )
        return False

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{wc_url}/wp-json/wc/v3/orders/{wc_order_id}",
                auth=(consumer_key, consumer_secret),
                json=data,
            )
            response.raise_for_status()

            logger.info(f"[{correlation_id}] WooCommerce order {wc_order_id} updated successfully")
            return True
    except httpx.HTTPStatusError as e:
        logger.error(
            f"[{correlation_id}] Failed to update WooCommerce order {wc_order_id}: "
            f"HTTP {e.response.status_code}"
        )
        return False
    except Exception as e:
        logger.error(f"[{correlation_id}] Failed to update WooCommerce order {wc_order_id}: {e}")
        return False


async def _send_email_notification(
    email: str,
    subject: str,
    order_id: str,
    notification_type: str,
    tracking_number: str | None = None,
    carrier: str | None = None,
    correlation_id: str = "",
) -> None:
    """
    Send email notification to customer.

    This is a logging placeholder for email notifications.
    In production, integrate with SendGrid, Mailgun, or AWS SES.

    Args:
        email: Customer email address
        subject: Email subject line
        order_id: Order ID for reference
        notification_type: Type of notification (shipping, cancellation, refund)
        tracking_number: Shipping tracking number (optional)
        carrier: Shipping carrier name (optional)
        correlation_id: Request correlation ID
    """
    # Structured logging for email notification
    # In production, replace with actual email sending via SendGrid/Mailgun/SES
    notification_data = {
        "notification_type": notification_type,
        "recipient_email": email,
        "subject": subject,
        "order_id": order_id,
        "tracking_number": tracking_number,
        "carrier": carrier,
        "correlation_id": correlation_id,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    logger.info(
        f"[{correlation_id}] Email notification queued: "
        f"type={notification_type}, to={email}, order={order_id}, "
        f"subject='{subject}', tracking={tracking_number}, carrier={carrier}"
    )

    # Log structured data for downstream processing/monitoring
    logger.info(f"[{correlation_id}] EMAIL_NOTIFICATION_DATA: {notification_data}")


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "router",
    "OrderWebhookPayload",
    "OrderFulfillmentRequest",
    "OrderFulfillmentResult",
    "OrderStatus",
    "FulfillmentStatus",
    "import_order_from_woocommerce",
    "process_order_fulfillment",
]
