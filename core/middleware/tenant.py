"""
Tenant Middleware
================

Resolves the active tenant for every inbound HTTP request and attaches it
to ``request.state`` so downstream handlers can read it without touching
headers or tokens directly.

Resolution order:
1. ``X-Tenant-ID`` request header (explicit override, e.g. internal services)
2. ``tenant_id`` claim inside the JWT bearer token
3. Fall-through: empty string (single-tenant / unauthenticated mode)

This middleware NEVER raises an error.  A missing tenant is not an
authentication failure — it is simply an empty tenant context.
"""

from __future__ import annotations

import hmac
import logging
import os
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response

logger = logging.getLogger(__name__)

# Env-gated shared secret allowing trusted internal services (e.g. background
# workers, admin tooling) to override tenant context via X-Tenant-ID.
# When unset, the header is ignored — defaults-closed.
_INTERNAL_SERVICE_TOKEN_ENV = "TENANT_HEADER_TRUST_TOKEN"
_INTERNAL_SERVICE_HEADER = "X-Internal-Service-Token"


async def tenant_middleware(request: Request, call_next: Callable) -> Response:
    """
    ASGI middleware that resolves and attaches tenant context.

    After this middleware runs, downstream code can access:
    - ``request.state.tenant_id``   — str, may be empty
    - ``request.state.tenant_tier`` — str, defaults to "free"

    Args:
        request:   Incoming FastAPI/Starlette request.
        call_next: Next handler in the middleware chain.

    Returns:
        HTTP response from the downstream handler.
    """
    tenant_id, tenant_tier = _resolve_tenant(request)

    request.state.tenant_id = tenant_id
    request.state.tenant_tier = tenant_tier

    return await call_next(request)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_tenant(request: Request) -> tuple[str, str]:
    """
    Return (tenant_id, tier) extracted from the request.

    Tries header first, then JWT claim, then defaults.
    Never raises — returns ("", "free") on any failure.
    """
    # 1. Explicit header — only honored when the caller also presents a
    #    matching internal-service shared secret. Unauthenticated clients
    #    cannot spoof tenancy this way.
    header_tenant = request.headers.get("X-Tenant-ID", "").strip()
    if header_tenant and _internal_service_token_valid(request):
        tier = request.headers.get("X-Tenant-Tier", "free").strip() or "free"
        return header_tenant, tier

    # 2. Fall back to the verified JWT bearer token claim.
    try:
        payload = _extract_jwt_claims(request)
        tenant_id = str(payload.get("tenant_id", "")).strip()
        tier = str(payload.get("tier", "free")).strip() or "free"
        return tenant_id, tier
    except Exception:
        # Swallow all JWT parse errors — auth middleware handles real auth.
        pass

    return "", "free"


def _internal_service_token_valid(request: Request) -> bool:
    """Return True when the request carries a valid internal-service token."""
    expected = os.getenv(_INTERNAL_SERVICE_TOKEN_ENV, "")
    if not expected:
        # Defaults-closed: no secret configured, never trust the override.
        return False
    presented = request.headers.get(_INTERNAL_SERVICE_HEADER, "")
    return bool(presented) and hmac.compare_digest(presented, expected)


def _extract_jwt_claims(request: Request) -> dict[str, Any]:
    """
    Decode JWT claims WITHOUT verification (verification happens in auth middleware).

    We only read the payload to retrieve ``tenant_id`` and ``tier``.
    Token validation is the responsibility of ``security.jwt_oauth2_auth``.

    Returns:
        Decoded JWT payload dict, or empty dict if token is absent / malformed.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return {}

    token = auth_header[7:].strip()
    if not token:
        return {}

    secret = os.getenv("JWT_SECRET_KEY", "")
    if not secret:
        # No secret configured — refuse to trust any token. Never fall back
        # to unverified decoding; that was the previous security hole.
        return {}

    try:
        import jwt  # PyJWT

        claims: dict[str, Any] = jwt.decode(
            token,
            secret,
            algorithms=["HS256", "HS512"],
            options={"require": ["exp"]},
        )
        return claims
    except Exception:
        return {}
