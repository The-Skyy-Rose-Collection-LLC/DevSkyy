"""
Feature Flag System
====================

LaunchDarkly-inspired feature toggle system with:

1. **Global kill switch**: disable a flag for everyone instantly
2. **Percentage rollouts**: gradually roll out to % of users
3. **User targeting**: specific users/groups always see a variant
4. **A/B testing**: measure impact before full rollout

All state is in-memory by default. Flags can be loaded from:
- A dict (testing, static config)
- JSON file (file-based deployment)
- Database (dynamic, real-time updates)

The consistent hashing algorithm ensures the same user always gets the
same flag value — sticky assignment is critical for A/B test validity.

Usage:
    manager = FlagManager()
    manager.create_flag("graphql_products", rollout_percentage=10)
    manager.create_flag("new_checkout", enabled_for_users=["admin@devskyy.com"])

    # In API handler
    if await manager.is_enabled("graphql_products", user_id="user-abc"):
        return await graphql_products_handler(request)

    # Disable immediately for all users (kill switch)
    manager.disable("graphql_products")

Architecture note:
    core/ is allowed to import stdlib + pydantic only.
    This module uses only stdlib — no external deps.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Flag Definition
# ---------------------------------------------------------------------------


@dataclass
class FeatureFlag:
    """
    Defines a single feature flag.

    Attributes:
        name: Unique identifier (snake_case preferred)
        enabled: Global kill switch — False means disabled for everyone
        rollout_percentage: 0–100, percentage of users who see this feature.
            100 = everyone, 0 = no one (unless in enabled_for_users)
        enabled_for_users: Specific user IDs that always see this feature
            regardless of rollout_percentage (useful for internal testing)
        disabled_for_users: Specific user IDs always excluded (overrides all)
        description: Human-readable description for the flags dashboard
        metadata: Arbitrary key-value pairs for custom logic
    """

    name: str
    enabled: bool = True
    rollout_percentage: int = 100
    enabled_for_users: list[str] = field(default_factory=list)
    disabled_for_users: list[str] = field(default_factory=list)
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.rollout_percentage <= 100:
            raise ValueError(
                f"rollout_percentage must be 0–100, got {self.rollout_percentage}"
            )


# ---------------------------------------------------------------------------
# Flag Manager
# ---------------------------------------------------------------------------


class FlagManager:
    """
    In-process feature flag manager.

    Thread-safety: reads are safe from any coroutine. Writes (create_flag,
    set_rollout, etc.) should only happen at startup or in admin endpoints
    that don't run concurrently with flag evaluation.
    """

    def __init__(self) -> None:
        self._flags: dict[str, FeatureFlag] = {}

    # ---------------------------------------------------------------------------
    # Flag CRUD
    # ---------------------------------------------------------------------------

    def create_flag(
        self,
        name: str,
        *,
        enabled: bool = True,
        rollout_percentage: int = 100,
        enabled_for_users: Optional[list[str]] = None,
        disabled_for_users: Optional[list[str]] = None,
        description: str = "",
        metadata: Optional[dict[str, Any]] = None,
    ) -> FeatureFlag:
        """
        Create or replace a feature flag.

        Overwriting an existing flag replaces it entirely — useful for
        resetting to a clean state during deployments.
        """
        flag = FeatureFlag(
            name=name,
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            enabled_for_users=list(enabled_for_users or []),
            disabled_for_users=list(disabled_for_users or []),
            description=description,
            metadata=dict(metadata or {}),
        )
        self._flags[name] = flag
        logger.debug(
            f"Flag {name!r} created: enabled={enabled}, "
            f"rollout={rollout_percentage}%"
        )
        return flag

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Return a flag by name, or None if not found."""
        return self._flags.get(name)

    def enable(self, name: str) -> None:
        """Turn on the global kill switch for a flag."""
        if flag := self._flags.get(name):
            flag.enabled = True
            logger.info(f"Flag {name!r} enabled globally")

    def disable(self, name: str) -> None:
        """Disable a flag for all users immediately (kill switch)."""
        if flag := self._flags.get(name):
            flag.enabled = False
            logger.info(f"Flag {name!r} disabled globally (kill switch)")

    def set_rollout(self, name: str, percentage: int) -> None:
        """
        Update rollout percentage without recreating the flag.

        Use for progressive rollouts:
            set_rollout("new_checkout", 5)    # Start at 5%
            # Monitor metrics...
            set_rollout("new_checkout", 25)   # Expand to 25%
            set_rollout("new_checkout", 100)  # Full rollout
        """
        if not 0 <= percentage <= 100:
            raise ValueError(f"Percentage must be 0–100, got {percentage}")
        if flag := self._flags.get(name):
            flag.rollout_percentage = percentage
            logger.info(f"Flag {name!r} rollout updated to {percentage}%")

    def list_flags(self) -> list[dict[str, Any]]:
        """Return all flags as a list of dicts (for admin API)."""
        return [
            {
                "name": f.name,
                "enabled": f.enabled,
                "rollout_percentage": f.rollout_percentage,
                "description": f.description,
            }
            for f in self._flags.values()
        ]

    # ---------------------------------------------------------------------------
    # Flag Evaluation
    # ---------------------------------------------------------------------------

    def is_enabled(self, flag_name: str, user_id: Optional[str] = None) -> bool:
        """
        Evaluate whether a flag is enabled for a given user.

        Evaluation order (first match wins):
        1. Flag not found → False (safe default)
        2. Global kill switch off → False
        3. User in disabled_for_users → False
        4. User in enabled_for_users → True
        5. rollout_percentage == 100 → True (no need to hash)
        6. rollout_percentage == 0 → False
        7. Consistent hash of (flag_name + user_id) mod 100 < rollout_percentage → True

        Args:
            flag_name: The flag to evaluate
            user_id: Optional user identifier for sticky assignment.
                     If None, only global flag state applies.
        """
        flag = self._flags.get(flag_name)

        # (1) Flag not registered
        if flag is None:
            logger.debug(f"Flag {flag_name!r} not found — returning False")
            return False

        # (2) Global kill switch
        if not flag.enabled:
            return False

        # (3) User explicitly disabled
        if user_id and user_id in flag.disabled_for_users:
            return False

        # (4) User explicitly enabled
        if user_id and user_id in flag.enabled_for_users:
            return True

        # (5–6) Rollout shortcuts
        if flag.rollout_percentage == 100:
            return True
        if flag.rollout_percentage == 0:
            return False

        # (7) Consistent hash-based rollout
        if user_id is None:
            # No user context — use the global rollout_percentage directly
            return False  # Conservative: require user_id for percentage rollouts

        bucket = self._hash_bucket(flag_name, user_id)
        return bucket < flag.rollout_percentage

    @staticmethod
    def _hash_bucket(flag_name: str, user_id: str) -> int:
        """
        Compute a consistent 0–99 bucket for (flag_name, user_id).

        Uses SHA-256 for uniform distribution. The same inputs always
        produce the same output — guaranteeing sticky flag assignment.

        SHA-256 is overkill for this purpose but is already available
        in stdlib without additional deps.
        """
        key = f"{flag_name}:{user_id}".encode()
        digest = hashlib.sha256(key).hexdigest()
        # Take first 8 hex chars = 32-bit integer, mod 100
        return int(digest[:8], 16) % 100

    # ---------------------------------------------------------------------------
    # Bulk Loading
    # ---------------------------------------------------------------------------

    def load_from_dict(self, config: dict[str, Any]) -> None:
        """
        Bulk-load flags from a config dict.

        Config format:
            {
                "graphql_products": {
                    "enabled": true,
                    "rollout_percentage": 25,
                    "description": "GraphQL-backed product catalog"
                },
                "new_checkout": {
                    "enabled": false
                }
            }
        """
        # Whitelist allowed keys — reject unknown fields to prevent injection
        # if config source is an external file or API endpoint.
        _ALLOWED_KEYS = {
            "enabled", "rollout_percentage", "enabled_for_users",
            "disabled_for_users", "description", "metadata",
        }
        for name, settings in config.items():
            if not isinstance(settings, dict):
                logger.warning(f"Flag {name!r}: settings must be a dict — skipping")
                continue
            filtered = {k: v for k, v in settings.items() if k in _ALLOWED_KEYS}
            unknown = set(settings) - _ALLOWED_KEYS
            if unknown:
                logger.warning(f"Flag {name!r}: ignoring unknown keys {unknown}")
            self.create_flag(name, **filtered)
        logger.info(f"Loaded {len(config)} flags from config dict")


# ---------------------------------------------------------------------------
# Singleton (optional — use dependency injection in production)
# ---------------------------------------------------------------------------

# Module-level singleton for simple use cases.
# In production, prefer injecting FlagManager via FastAPI's Depends().
flag_manager = FlagManager()
