"""WooCommerce Webhooks API.

Handles incoming webhooks from WooCommerce for order updates, product changes, etc.
All endpoints require a valid HMAC signature via the X-WC-Webhook-Signature header.
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.wordpress_integration import verify_webhook

logger = logging.getLogger(__name__)

router = APIRouter(tags=["woocommerce-webhooks"], prefix="/woocommerce/webhooks")


@router.post("/order", status_code=status.HTTP_200_OK, summary="Order webhook")
async def handle_order_webhook(
    body: bytes = Depends(verify_webhook),
):
    """Handle WooCommerce order webhooks.

    Signature is verified via the verify_webhook dependency.
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        logger.warning("Order webhook received malformed JSON payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from exc
    logger.info(
        "Order webhook received",
        extra={"order_id": payload.get("id"), "status": payload.get("status")},
    )
    return {"status": "received"}


@router.post("/product", status_code=status.HTTP_200_OK, summary="Product webhook")
async def handle_product_webhook(
    body: bytes = Depends(verify_webhook),
):
    """Handle WooCommerce product webhooks.

    Signature is verified via the verify_webhook dependency.
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        logger.warning("Product webhook received malformed JSON payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from exc
    logger.info(
        "Product webhook received",
        extra={"product_id": payload.get("id"), "name": payload.get("name")},
    )
    return {"status": "received"}
