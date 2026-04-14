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

import logging
from collections.abc import Callable
from typing import Any

from fastapi import Request, Response

logger = logging.getLogger(__name__)


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
    # 1. Explicit header wins.
    header_tenant = request.headers.get("X-Tenant-ID", "").strip()
    if header_tenant:
        return header_tenant, "free"

    # 2. Fall back to JWT bearer token claim.
    try:
        payload = _extract_jwt_claims(request)
        tenant_id = str(payload.get("tenant_id", "")).strip()
        tier = str(payload.get("tier", "free")).strip() or "free"
        return tenant_id, tier
    except Exception:
        # Swallow all JWT parse errors — auth middleware handles real auth.
        pass

    return "", "free"


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

    try:
        import jwt  # PyJWT

        # decode_token without verification — we only want the payload structure.
        claims: dict[str, Any] = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
            algorithms=["HS256", "HS512", "RS256"],
        )
        return claims
    except Exception:
        return {}
