"""
Usage Metering
==============

Records and retrieves per-tenant, per-intent usage counters backed by Redis.
Falls back to an in-process dict when Redis is unavailable, so the platform
continues to operate without a Redis connection (with the trade-off that
counters are lost on restart).

Key schema:
    elite_studio:usage:{tenant_id}:{intent}:{YYYY-MM}

All keys for a billing period share the same TTL (62 days), so Redis
automatically evicts historical data without a manual cleanup job.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from billing.plans import intent_allowed, quota_remaining

logger = logging.getLogger(__name__)

_KEY_PREFIX = "elite_studio:usage"
_TTL_SECONDS = 62 * 24 * 3600  # 62-day TTL per period key


def _current_period() -> str:
    """Return the current billing period as ``YYYY-MM``."""
    return datetime.now(UTC).strftime("%Y-%m")


def _key(tenant_id: str, intent: str, period: str) -> str:
    return f"{_KEY_PREFIX}:{tenant_id}:{intent}:{period}"


class UsageMetering:
    """
    Records and checks creative-operation usage per tenant per billing period.

    Supports two backends:
    - Redis (preferred)  — durable, shared across workers
    - In-process dict    — automatic fallback when Redis is unavailable

    Args:
        redis_url: Optional Redis connection URL.  When omitted (or when the
                   connection fails) the in-process fallback is used silently.
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._redis: Any = None
        self._fallback: dict[str, int] = defaultdict(int)
        self._use_fallback = True

        if redis_url:
            self._redis = self._connect(redis_url)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def record(self, tenant_id: str, intent: str, count: int = 1) -> None:
        """
        Increment the usage counter for *tenant_id* / *intent* this month.

        Args:
            tenant_id: Tenant identifier.
            intent:    Creative intent (e.g. "product-render").
            count:     Number of units to add (default 1).
        """
        period = _current_period()
        k = _key(tenant_id, intent, period)

        if self._redis and not self._use_fallback:
            try:
                pipe = self._redis.pipeline()
                pipe.incrby(k, count)
                pipe.expire(k, _TTL_SECONDS)
                pipe.execute()
                return
            except Exception as exc:
                logger.warning("Redis record failed, using fallback: %s", exc)
                self._use_fallback = True

        self._fallback[k] += count

    def get_usage(self, tenant_id: str, intent: str, period: str = "") -> int:
        """
        Return the usage count for *tenant_id* / *intent* in *period*.

        Args:
            tenant_id: Tenant identifier.
            intent:    Creative intent.
            period:    Billing period string (YYYY-MM).  Defaults to current month.

        Returns:
            Integer count of units consumed.
        """
        period = period or _current_period()
        k = _key(tenant_id, intent, period)

        if self._redis and not self._use_fallback:
            try:
                value = self._redis.get(k)
                return int(value) if value is not None else 0
            except Exception as exc:
                logger.warning("Redis get_usage failed, using fallback: %s", exc)
                self._use_fallback = True

        return self._fallback.get(k, 0)

    def get_all_usage(self, tenant_id: str, period: str = "") -> dict[str, int]:
        """
        Return all intent usage counts for *tenant_id* in *period*.

        Args:
            tenant_id: Tenant identifier.
            period:    Billing period (YYYY-MM).  Defaults to current month.

        Returns:
            Dict mapping intent → count.
        """
        period = period or _current_period()
        pattern = f"{_KEY_PREFIX}:{tenant_id}:*:{period}"

        if self._redis and not self._use_fallback:
            try:
                keys = self._redis.keys(pattern)
                if not keys:
                    return {}
                values = self._redis.mget(keys)
                result: dict[str, int] = {}
                for raw_key, raw_val in zip(keys, values, strict=False):
                    # Extract intent from key: elite_studio:usage:{tid}:{intent}:{period}
                    parts = raw_key.decode() if isinstance(raw_key, bytes) else raw_key
                    segments = parts.split(":")
                    if len(segments) >= 5:
                        intent = ":".join(segments[3:-1])
                        result[intent] = int(raw_val) if raw_val is not None else 0
                return result
            except Exception as exc:
                logger.warning("Redis get_all_usage failed, using fallback: %s", exc)
                self._use_fallback = True

        # Fallback: scan in-process dict
        prefix = f"{_KEY_PREFIX}:{tenant_id}:"
        suffix = f":{period}"
        result: dict[str, int] = {}
        for k, v in self._fallback.items():
            if k.startswith(prefix) and k.endswith(suffix):
                # k = elite_studio:usage:{tenant_id}:{intent}:{period}
                inner = k[len(prefix) : -len(suffix)]
                result[inner] = v
        return result

    def check_quota(self, tenant_id: str, tier: str, intent: str) -> tuple[bool, int]:
        """
        Check whether *tenant_id* is within quota for *intent*.

        Args:
            tenant_id: Tenant identifier.
            tier:      Subscription tier string.
            intent:    Creative intent.

        Returns:
            Tuple (allowed: bool, remaining: int).
            ``remaining`` is -1 for unlimited, 0 when exhausted.
        """
        if not intent_allowed(tier, intent):
            return False, 0

        used = self.get_usage(tenant_id, intent)
        remaining = quota_remaining(tier, intent, used)

        if remaining == -1:
            return True, -1

        return remaining > 0, remaining

    def reset_period(self, tenant_id: str, period: str) -> None:
        """
        Clear all usage counters for *tenant_id* in *period*.

        Intended for testing and admin operations only.

        Args:
            tenant_id: Tenant identifier.
            period:    Billing period string (YYYY-MM).
        """
        pattern = f"{_KEY_PREFIX}:{tenant_id}:*:{period}"

        if self._redis and not self._use_fallback:
            try:
                keys = self._redis.keys(pattern)
                if keys:
                    self._redis.delete(*keys)
                return
            except Exception as exc:
                logger.warning("Redis reset_period failed, using fallback: %s", exc)
                self._use_fallback = True

        # Fallback
        prefix = f"{_KEY_PREFIX}:{tenant_id}:"
        suffix = f":{period}"
        to_delete = [k for k in self._fallback if k.startswith(prefix) and k.endswith(suffix)]
        for k in to_delete:
            del self._fallback[k]

    # -------------------------------------------------------------------------
    # Private
    # -------------------------------------------------------------------------

    def _connect(self, redis_url: str) -> Any:
        """Attempt to connect to Redis.  Returns client or None on failure."""
        try:
            import redis  # type: ignore[import]

            client = redis.from_url(redis_url, decode_responses=False, socket_connect_timeout=2)
            client.ping()
            self._use_fallback = False
            logger.info("UsageMetering connected to Redis: %s", redis_url.split("@")[-1])
            return client
        except Exception as exc:
            logger.warning("Redis unavailable (%s) — UsageMetering using in-process fallback.", exc)
            return None
