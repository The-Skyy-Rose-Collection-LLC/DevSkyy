"""WooCommerce Webhooks API.

Handles incoming webhooks from WooCommerce for order updates, product changes, etc.
"""

from fastapi import APIRouter, Header, Request, status
from pydantic import BaseModel

router = APIRouter(tags=["woocommerce-webhooks"], prefix="/woocommerce/webhooks")


class WebhookPayload(BaseModel):
    """Generic webhook payload structure."""

    event: str
    data: dict


@router.post("/order", status_code=status.HTTP_200_OK, summary="Order webhook")
async def handle_order_webhook(
    request: Request,
    x_wc_webhook_signature: str | None = Header(None),
):
    """Handle WooCommerce order webhooks."""
    # TODO: Implement webhook signature verification
    # TODO: Process order updates
    return {"status": "received"}


@router.post("/product", status_code=status.HTTP_200_OK, summary="Product webhook")
async def handle_product_webhook(
    request: Request,
    x_wc_webhook_signature: str | None = Header(None),
):
    """Handle WooCommerce product webhooks."""
    # TODO: Implement webhook signature verification
    # TODO: Process product updates
    return {"status": "received"}
