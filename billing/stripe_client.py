"""
Stripe Client
=============

Thin wrapper around the Stripe Python SDK.  All methods degrade gracefully
when ``STRIPE_SECRET_KEY`` is not configured — they log a warning and return
``None`` / ``False`` / empty collections rather than raising.

This means the platform can boot and operate without Stripe credentials
in development or test environments.

Usage::

    from billing.stripe_client import StripeClient

    client = StripeClient()
    customer_id = client.create_customer("t-001", "user@example.com", "Acme Co")
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class StripeClient:
    """
    Stripe API wrapper with graceful degradation.

    Initialisation reads ``STRIPE_SECRET_KEY`` from the environment.
    When the key is absent the client operates in stub mode: every method
    logs a warning and returns a safe default.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("STRIPE_SECRET_KEY", "")
        self._stripe: Any = None

        if self._api_key:
            try:
                import stripe  # type: ignore[import]

                stripe.api_key = self._api_key
                self._stripe = stripe
                logger.info("StripeClient initialized (live key present)")
            except ImportError:
                logger.warning("stripe package not installed — StripeClient in stub mode")
        else:
            logger.warning(
                "STRIPE_SECRET_KEY not set — StripeClient operating in stub mode. "
                "All methods will return None/False/empty."
            )

    # -------------------------------------------------------------------------
    # Customer
    # -------------------------------------------------------------------------

    def create_customer(self, tenant_id: str, email: str, name: str) -> str | None:
        """
        Create a Stripe Customer for a tenant.

        Args:
            tenant_id: Internal tenant identifier (stored as metadata).
            email:     Billing contact email.
            name:      Customer/company display name.

        Returns:
            Stripe customer ID string, or None on failure / stub mode.
        """
        if not self._stripe:
            logger.warning("create_customer: Stripe not configured")
            return None
        try:
            customer = self._stripe.Customer.create(
                email=email,
                name=name,
                metadata={"tenant_id": tenant_id},
            )
            return customer.id
        except Exception as exc:
            logger.error("create_customer failed: %s", exc)
            return None

    # -------------------------------------------------------------------------
    # Subscriptions
    # -------------------------------------------------------------------------

    def create_subscription(self, customer_id: str, price_id: str) -> dict | None:
        """
        Create a Stripe Subscription.

        Args:
            customer_id: Stripe customer ID.
            price_id:    Stripe price ID to subscribe to.

        Returns:
            Stripe subscription dict, or None on failure / stub mode.
        """
        if not self._stripe:
            logger.warning("create_subscription: Stripe not configured")
            return None
        try:
            subscription = self._stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )
            return dict(subscription)
        except Exception as exc:
            logger.error("create_subscription failed: %s", exc)
            return None

    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancel a Stripe Subscription immediately.

        Args:
            subscription_id: Stripe subscription ID.

        Returns:
            True on success, False on failure / stub mode.
        """
        if not self._stripe:
            logger.warning("cancel_subscription: Stripe not configured")
            return False
        try:
            self._stripe.Subscription.cancel(subscription_id)
            return True
        except Exception as exc:
            logger.error("cancel_subscription failed: %s", exc)
            return False

    def get_subscription(self, subscription_id: str) -> dict | None:
        """
        Retrieve a Stripe Subscription by ID.

        Args:
            subscription_id: Stripe subscription ID.

        Returns:
            Subscription dict, or None on failure / stub mode.
        """
        if not self._stripe:
            return None
        try:
            subscription = self._stripe.Subscription.retrieve(subscription_id)
            return dict(subscription)
        except Exception as exc:
            logger.error("get_subscription failed: %s", exc)
            return None

    # -------------------------------------------------------------------------
    # Invoices
    # -------------------------------------------------------------------------

    def list_invoices(self, customer_id: str, limit: int = 10) -> list[dict]:
        """
        List recent invoices for a customer.

        Args:
            customer_id: Stripe customer ID.
            limit:       Maximum number of invoices to return (max 100).

        Returns:
            List of invoice dicts, or empty list on failure / stub mode.
        """
        if not self._stripe:
            return []
        try:
            invoices = self._stripe.Invoice.list(customer=customer_id, limit=min(limit, 100))
            return [dict(inv) for inv in invoices.data]
        except Exception as exc:
            logger.error("list_invoices failed: %s", exc)
            return []

    # -------------------------------------------------------------------------
    # Customer Portal
    # -------------------------------------------------------------------------

    def create_portal_session(self, customer_id: str, return_url: str) -> str | None:
        """
        Create a Stripe Billing Portal session.

        Args:
            customer_id: Stripe customer ID.
            return_url:  URL to redirect to after the portal session.

        Returns:
            Portal session URL, or None on failure / stub mode.
        """
        if not self._stripe:
            logger.warning("create_portal_session: Stripe not configured")
            return None
        try:
            session = self._stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session.url
        except Exception as exc:
            logger.error("create_portal_session failed: %s", exc)
            return None

    # -------------------------------------------------------------------------
    # Price helpers
    # -------------------------------------------------------------------------

    def get_price_id(self, tier: str) -> str | None:
        """
        Look up the Stripe price ID for a tier using ``STRIPE_PRICE_IDS``.

        Reads the environment variable ``STRIPE_PRICE_IDS`` as a
        comma-separated list of ``tier:price_id`` pairs.

        Example env value::

            STRIPE_PRICE_IDS=starter:price_abc123,pro:price_def456

        Args:
            tier: Subscription tier name.

        Returns:
            Stripe price ID, or None if not configured.
        """
        raw = os.getenv("STRIPE_PRICE_IDS", "")
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            parts = item.split(":", 1)
            if len(parts) == 2 and parts[0].strip() == tier:
                return parts[1].strip()
        return None
