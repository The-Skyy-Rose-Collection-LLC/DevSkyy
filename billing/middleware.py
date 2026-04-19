"""
Billing Middleware
=================

ASGI middleware that enforces entitlement checks before creative operations
and appends quota usage headers to every response.

Only applies to routes that carry the ``X-Creative-Intent`` header or match
the ``/api/v1/elite-studio/`` path prefix.

On quota exhaustion, returns HTTP 402 Payment Required with an upgrade prompt
rather than letting the request through.

Usage in main_enterprise.py::

    from billing.middleware import billing_middleware
    app.middleware("http")(billing_middleware)
"""

from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from billing.entitlements import EntitlementChecker
from billing.metering import UsageMetering

logger = logging.getLogger(__name__)

# Routes that require creative quota enforcement. Matches every API version
# (v1, v2, …) so new versions do not silently bypass billing.
_CREATIVE_PATH_RE = re.compile(r"^/api/v\d+/(elite-studio|portal)/")

# Header name the caller uses to declare creative intent
_INTENT_HEADER = "X-Creative-Intent"

# Singleton metering + checker (initialised lazily)
_metering: UsageMetering | None = None
_checker: EntitlementChecker | None = None


def _get_checker() -> EntitlementChecker:
    """Return the shared EntitlementChecker, creating it on first call."""
    global _metering, _checker
    if _checker is None:
        import os

        redis_url = os.getenv("REDIS_URL")
        _metering = UsageMetering(redis_url=redis_url)
        _checker = EntitlementChecker(metering=_metering)
    return _checker


async def billing_middleware(request: Request, call_next: Callable) -> Response:
    """
    ASGI middleware that enforces billing entitlements.

    Flow:
    1. Skip non-creative endpoints.
    2. Read tenant context from ``request.state`` (set by tenant_middleware).
    3. Read intended creative operation from ``X-Creative-Intent`` header.
    4. If quota exceeded → return 402 immediately.
    5. Otherwise → forward request and append ``X-Quota-Remaining`` header.

    Args:
        request:   Incoming HTTP request.
        call_next: Next middleware / route handler.

    Returns:
        HTTP response.
    """
    # Only enforce on creative-operation endpoints
    if not _is_creative_endpoint(request):
        return await call_next(request)

    intent = request.headers.get(_INTENT_HEADER, "").strip()
    if not intent:
        # No intent declared — pass through; route handler validates further
        return await call_next(request)

    tenant_id: str = getattr(request.state, "tenant_id", "") or ""
    tier: str = getattr(request.state, "tenant_tier", "free") or "free"

    # Anonymous requests with no tenant operate as "free"
    if not tenant_id:
        tenant_id = "_anonymous"

    try:
        checker = _get_checker()
        # UsageMetering uses a sync Redis client; offload to a thread so we
        # do not block the event loop on every creative request.
        result = await asyncio.to_thread(
            checker.check, tenant_id=tenant_id, tier=tier, intent=intent
        )
    except Exception as exc:
        logger.error("billing_middleware entitlement check error: %s", exc)
        # Fail open — let the request through rather than block on infra error
        return await call_next(request)

    if not result.allowed:
        logger.info(
            "quota_exceeded tenant=%s tier=%s intent=%s reason=%s",
            tenant_id,
            tier,
            intent,
            result.reason,
        )
        return JSONResponse(
            status_code=402,
            content={
                "error": "quota_exceeded",
                "message": result.reason,
                "intent": intent,
                "tier": tier,
                "upgrade_to": result.upgrade_to,
                "upgrade_url": "/api/v1/portal/subscriptions",
            },
        )

    # Allowed — forward and tag response with remaining quota
    response: Response = await call_next(request)

    # Only meter successful usage. 4xx/5xx don't consume quota.
    if response.status_code < 400 and _metering is not None:
        try:
            await asyncio.to_thread(_metering.record, tenant_id, intent, 1)
        except Exception as exc:
            logger.error("billing_middleware record error: %s", exc)

    remaining = result.remaining
    if remaining != -1:
        remaining = max(0, remaining - 1)
    response.headers["X-Quota-Remaining"] = str(remaining) if remaining != -1 else "unlimited"
    response.headers["X-Quota-Intent"] = intent

    return response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_creative_endpoint(request: Request) -> bool:
    """Return True when the request path targets a creative operation."""
    return _CREATIVE_PATH_RE.match(request.url.path) is not None
