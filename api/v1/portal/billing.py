"""
Portal — Billing
================

Invoice retrieval and Stripe billing portal session creation.

Endpoints:
    GET  /billing/invoices       — list last 10 invoices
    POST /billing/portal-session — create Stripe billing portal session
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from billing.stripe_client import StripeClient
from core.auth.token_payload import TokenPayload
from security.jwt_oauth2_auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])


# ---------------------------------------------------------------------------
# Shared singleton
# ---------------------------------------------------------------------------


def _stripe() -> StripeClient:
    return StripeClient()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class InvoiceItem(BaseModel):
    """Simplified invoice record."""

    id: str
    number: str | None = None
    status: str | None = None
    amount_paid: int = 0  # in cents
    currency: str = "usd"
    created: int = 0  # Unix timestamp
    invoice_pdf: str | None = None
    hosted_invoice_url: str | None = None


class InvoiceListResponse(BaseModel):
    """List of invoices."""

    invoices: list[InvoiceItem]
    count: int
    timestamp: str


class PortalSessionRequest(BaseModel):
    """Request to create a billing portal session."""

    return_url: str = Field(
        ...,
        description="URL to redirect to after the portal session ends.",
    )
    customer_id: str | None = Field(
        default=None,
        description="Stripe customer ID. Resolved from tenant state if omitted.",
    )


class PortalSessionResponse(BaseModel):
    """Stripe billing portal session URL."""

    portal_url: str
    message: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/invoices",
    response_model=InvoiceListResponse,
    summary="List last 10 invoices",
)
async def list_invoices(
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
    limit: int = 10,
) -> InvoiceListResponse:
    """
    Return the last *limit* invoices for the current tenant's Stripe customer.
    """
    limit = max(1, min(limit, 100))
    customer_id = _resolve_customer_id(request, user)

    if not customer_id:
        return InvoiceListResponse(
            invoices=[],
            count=0,
            timestamp=datetime.now(UTC).isoformat(),
        )

    stripe = _stripe()
    raw_invoices = stripe.list_invoices(customer_id=customer_id, limit=limit)

    items: list[InvoiceItem] = []
    for inv in raw_invoices:
        try:
            items.append(
                InvoiceItem(
                    id=inv.get("id", ""),
                    number=inv.get("number"),
                    status=inv.get("status"),
                    amount_paid=int(inv.get("amount_paid", 0)),
                    currency=inv.get("currency", "usd"),
                    created=int(inv.get("created", 0)),
                    invoice_pdf=inv.get("invoice_pdf"),
                    hosted_invoice_url=inv.get("hosted_invoice_url"),
                )
            )
        except Exception as exc:
            logger.warning("Failed to parse invoice: %s", exc)

    return InvoiceListResponse(
        invoices=items,
        count=len(items),
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.post(
    "/portal-session",
    response_model=PortalSessionResponse,
    summary="Create Stripe billing portal session",
)
async def create_portal_session(
    body: PortalSessionRequest,
    request: Request,
    user: Annotated[TokenPayload, Depends(get_current_user)],
) -> PortalSessionResponse:
    """
    Create a Stripe Billing Portal session and return the redirect URL.

    The frontend should redirect the user to ``portal_url`` to manage
    payment methods, download invoices, and change plans.
    """
    customer_id = body.customer_id or _resolve_customer_id(request, user)

    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No Stripe customer found for this tenant. "
                "Subscribe to a plan first to access billing management."
            ),
        )

    stripe = _stripe()
    portal_url = stripe.create_portal_session(
        customer_id=customer_id,
        return_url=body.return_url,
    )

    if not portal_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to create billing portal session. Please try again later.",
        )

    return PortalSessionResponse(
        portal_url=portal_url,
        message="Billing portal session created. Redirect the user to portal_url.",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_customer_id(request: Request, user: TokenPayload) -> str | None:
    """Extract the Stripe customer ID from request state or user metadata."""
    # In a full implementation, load from the tenants DB row.
    # For now, read from request state (populated by tenant_middleware + DB lookup).
    customer_id = getattr(request.state, "stripe_customer_id", None)
    return customer_id or None
