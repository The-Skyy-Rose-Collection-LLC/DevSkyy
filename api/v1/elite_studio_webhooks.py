"""
Elite Studio Webhook Manager

Registers external webhook URLs and fires signed HTTP notifications
for Elite Studio job lifecycle events.

Events: job.completed, job.failed, job.review_required

Security: HMAC-SHA256 signatures are sent in the X-SkyyRose-Signature header.
Storage:  Redis hash  elite_studio:webhooks:{webhook_id}
Delivery: Fire-and-forget via httpx.AsyncClient — failures are logged, never raised.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_EVENTS = frozenset(
    {
        # Legacy job events
        "job.completed",
        "job.failed",
        "job.review_required",
        # Operation lifecycle
        "operation.created",
        "operation.started",
        "operation.completed",
        "operation.failed",
        "operation.review_required",
        # Character events
        "character.created",
        "character.updated",
        # Asset events
        "asset.generated",
        "asset.approved",
        "asset.rejected",
        # Billing / subscription
        "subscription.created",
        "subscription.updated",
        "subscription.cancelled",
        "invoice.paid",
        "usage.threshold_reached",
        # Team events
        "team.member_invited",
        "team.member_removed",
    }
)
_KEY_PREFIX = "elite_studio:webhooks"
_DELIVERY_TIMEOUT = 10  # seconds


# ---------------------------------------------------------------------------
# Webhook Manager
# ---------------------------------------------------------------------------


class WebhookManager:
    """Manages registration and delivery of Elite Studio webhook events."""

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Any = None

    # ------------------------------------------------------------------
    # Redis (lazy, best-effort)
    # ------------------------------------------------------------------

    def _get_redis(self) -> Any | None:
        if self._redis is not None:
            try:
                self._redis.ping()
                return self._redis
            except Exception:
                self._redis = None

        try:
            import redis as redis_lib

            self._redis = redis_lib.from_url(self._redis_url, decode_responses=True, socket_timeout=2)
            self._redis.ping()
            return self._redis
        except Exception as exc:
            logger.warning("WebhookManager: Redis unavailable — %s", exc)
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, url: str, events: list[str], secret: str) -> str:
        """Register a webhook endpoint.

        Args:
            url: HTTPS endpoint that will receive POST payloads.
            events: List of event names this webhook subscribes to.
            secret: Shared secret used for HMAC-SHA256 signing.

        Returns:
            webhook_id: Unique identifier for this registration.

        Raises:
            ValueError: If any event name is invalid.
        """
        invalid = set(events) - VALID_EVENTS
        if invalid:
            raise ValueError(f"Unknown events: {invalid}. Valid: {VALID_EVENTS}")

        webhook_id = uuid.uuid4().hex
        r = self._get_redis()
        if r is None:
            logger.warning("WebhookManager.register: Redis unavailable, webhook not persisted")
            return webhook_id

        key = f"{_KEY_PREFIX}:{webhook_id}"
        payload = {
            "webhook_id": webhook_id,
            "url": url,
            "events": json.dumps(events),
            "secret": secret,
            "registered_at": datetime.now(UTC).isoformat(),
        }
        try:
            r.hset(key, mapping=payload)
        except Exception as exc:
            logger.warning("WebhookManager.register failed to persist: %s", exc)

        return webhook_id

    def fire(self, event: str, payload: dict) -> None:
        """Fire a webhook event to all matching registered endpoints.

        This is fire-and-forget: failures are logged but never raised.

        Args:
            event: Event name (e.g. "job.completed").
            payload: Dict to be JSON-serialised as the POST body.
        """
        if event not in VALID_EVENTS:
            logger.warning("WebhookManager.fire: unknown event %r — skipped", event)
            return

        registrations = self._get_registrations_for_event(event)
        if not registrations:
            return

        import asyncio

        try:
            loop = asyncio.get_running_loop()
            # Inside an async context — schedule without blocking.
            loop.create_task(_fire_all(registrations, event, payload))
        except RuntimeError:
            # No running loop — fire synchronously via a new one.
            asyncio.run(_fire_all(registrations, event, payload))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_registrations_for_event(self, event: str) -> list[dict]:
        """Return all webhook registrations that subscribe to `event`."""
        r = self._get_redis()
        if r is None:
            return []

        registrations = []
        try:
            keys = r.keys(f"{_KEY_PREFIX}:*")
            for key in keys:
                data = r.hgetall(key)
                if not data:
                    continue
                events = json.loads(data.get("events", "[]"))
                if event in events:
                    registrations.append(data)
        except Exception as exc:
            logger.warning("WebhookManager._get_registrations_for_event failed: %s", exc)

        return registrations


# ---------------------------------------------------------------------------
# Async delivery helpers
# ---------------------------------------------------------------------------


async def _fire_all(registrations: list[dict], event: str, payload: dict) -> None:
    """Fire webhook to all registered URLs for this event (best-effort)."""
    import asyncio

    tasks = [_deliver(reg, event, payload) for reg in registrations]
    await asyncio.gather(*tasks, return_exceptions=True)


async def _deliver(registration: dict, event: str, payload: dict) -> None:
    """POST signed payload to a single webhook URL. Never raises."""
    url = registration.get("url", "")
    secret = registration.get("secret", "")
    if not url:
        return

    body = {
        "event": event,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": payload,
    }
    json_body = json.dumps(body, separators=(",", ":"))
    signature = _sign(secret, json_body)

    try:
        async with httpx.AsyncClient(timeout=_DELIVERY_TIMEOUT) as client:
            response = await client.post(
                url,
                content=json_body,
                headers={
                    "Content-Type": "application/json",
                    "X-SkyyRose-Signature": signature,
                    "X-SkyyRose-Event": event,
                },
            )
            if response.status_code >= 400:
                logger.warning(
                    "Webhook delivery non-2xx: url=%s event=%s status=%d",
                    url,
                    event,
                    response.status_code,
                )
    except Exception as exc:
        logger.warning("Webhook delivery failed: url=%s event=%s error=%s", url, event, exc)


def _sign(secret: str, body: str) -> str:
    """Return HMAC-SHA256 hex digest of body using secret."""
    return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
