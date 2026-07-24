"""
Tripo3D Multi-Account / Multi-Region Credential Resolution
============================================================

The user runs MULTIPLE Tripo3D accounts across two API regions: `.ai`
(global) and `.com` (China). A `tsk_*` API key is bound to exactly one
account+region combination and returns a 401 or a 0-balance response when
tried against the other region. Before any paid Tripo3D call, the correct
(key, region) pair — the one that actually holds usable credit — must be
discovered rather than assumed.

This module is the reusable extraction of the discovery logic that
originally lived only in `scripts/skyy_avatar_rig.py`. It probes every
candidate key against both regions and returns the combination with the
HIGHEST balance (not the first with a positive balance) — this avoids
resolving to a low-balance account when another configured account holds
enough credit to cover a caller's `--max-cost` gate.

NOTE on base_url: `tripo3d.TripoClient.__init__` accepts only `api_key`,
`IS_GLOBAL`, and an optional `v3_base_url` override — there is no generic
`base_url` kwarg. `IS_GLOBAL` alone is what selects the `.ai` vs `.com`
region internally (it flips `TripoClient.BASE_URL` and the default v3 host).
`TripoCredentials.base_url` below is kept as an informational/diagnostic
record only, matching the historical behavior of `scripts/skyy_avatar_rig.py`
— it is not, and should not be, passed to `TripoClient`.

API Documentation: https://docs.tripo3d.ai/
"""

from __future__ import annotations

import logging
import os
from typing import Any, NamedTuple

from agents.errors import ConfigurationError

logger = logging.getLogger(__name__)

DEFAULT_GLOBAL_BASE_URL = "https://api.tripo3d.ai/v2"
DEFAULT_CHINA_BASE_URL = "https://api.tripo3d.com/v2"


class TripoCredentials(NamedTuple):
    """A resolved (API key, region) pair confirmed to hold a usable credit balance."""

    api_key: str
    is_global: bool
    base_url: str
    balance: float


def mask_api_key(key: str) -> str:
    """Truncate an API key to its first 4 + last 4 characters for safe logging.

    Never log a full API key. Keys shorter than 9 characters are masked entirely
    since a partial reveal of a short key leaks most of its content.
    """
    if len(key) < 9:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def _collect_candidate_keys() -> list[str]:
    """Build the ordered, de-duplicated list of candidate Tripo API keys from env.

    Reads `TRIPO_API_KEYS` (comma-separated) first, then appends the
    single-key env vars `TRIPO_API_KEY` / `TRIPO3D_API_KEY` if not already
    present. Only `tsk_`-prefixed keys are kept — the Tripo3D SDK itself
    rejects any other prefix with a `ValueError`, so filtering here avoids
    wasted probe cycles on obviously malformed keys.
    """
    keys_csv = os.getenv("TRIPO_API_KEYS", "").strip()
    single_key = os.getenv("TRIPO_API_KEY", "").strip() or os.getenv("TRIPO3D_API_KEY", "").strip()

    candidates = [k.strip() for k in keys_csv.split(",") if k.strip()]
    if single_key and single_key not in candidates:
        candidates.append(single_key)

    deduped: list[str] = []
    seen: set[str] = set()
    for key in candidates:
        if key not in seen and key.startswith("tsk_"):
            seen.add(key)
            deduped.append(key)
    return deduped


async def _probe_key_on_region(key: str, is_global: bool) -> dict[str, Any]:
    """Try a single key against a single region. Return a diagnostic dict.

    NOTE: the raw API key is intentionally NOT stored in the returned dict —
    callers that need the key track it separately (e.g. alongside the loop
    variable that produced this probe). Keeping the key out of the dict
    prevents static analysis from tainting the numeric `balance` field via
    data-flow from the key.

    Raises:
        ConfigurationError: If the tripo3d SDK is not installed. This is
            raised (not caught) so the caller fails closed immediately
            rather than silently treating every probe as a 0-balance auth
            failure.
    """
    try:
        from tripo3d import TripoClient
    except ImportError as exc:
        raise ConfigurationError(
            "tripo3d SDK not installed. Run: pip install 'tripo3d>=0.4.1'",
            config_key="tripo3d",
        ) from exc

    region = "global (.ai)" if is_global else "china (.com)"
    masked = mask_api_key(key)
    try:
        async with TripoClient(api_key=key, IS_GLOBAL=is_global) as client:
            balance = await client.get_balance()
            available = float(getattr(balance, "balance", 0))
            frozen = float(getattr(balance, "frozen", 0))
            return {
                "key_display": masked,
                "region": region,
                "is_global": is_global,
                "auth_ok": True,
                "balance": available,
                "frozen": frozen,
                "error": None,
            }
    except Exception as exc:
        return {
            "key_display": masked,
            "region": region,
            "is_global": is_global,
            "auth_ok": False,
            "balance": 0.0,
            "frozen": 0.0,
            "error": str(exc),
        }


async def _scan_all_candidates(keys: list[str]) -> tuple[str | None, dict[str, Any] | None]:
    """Probe every key x region combo, returning the highest-balance winner."""
    logger.info(
        "Multi-account / multi-region Tripo discovery: trying %d key(s) x 2 regions = %d probes",
        len(keys),
        len(keys) * 2,
    )

    best_key: str | None = None
    best_result: dict[str, Any] | None = None
    probed = 0
    for key in keys:
        for is_global in (True, False):
            probed += 1
            result = await _probe_key_on_region(key, is_global)
            logger.info(
                "  [%d/%d] key %s on %s: %s, balance=%.2f%s",
                probed,
                len(keys) * 2,
                result["key_display"],
                result["region"],
                "auth ok" if result["auth_ok"] else "auth failed",
                result["balance"],
                f", error: {result['error']}" if result["error"] else "",
            )
            if result["auth_ok"] and result["balance"] > 0:
                if best_result is None or result["balance"] > best_result["balance"]:
                    best_key = key
                    best_result = result

    return best_key, best_result


async def resolve_tripo_credentials(
    candidate_keys: list[str] | None = None,
) -> TripoCredentials:
    """Resolve the (key, region) combination with the highest usable balance.

    Tries every candidate key against both regions (`.ai` global, then
    `.com` China) and returns the credit-holding combo with the HIGHEST
    balance — not the first non-zero one — so a low-balance account never
    wins over another configured account that actually has enough credit
    for a caller's `--max-cost` gate.

    Args:
        candidate_keys: Explicit keys to try, in order. When `None`
            (default), candidates are built from `TRIPO_API_KEYS`
            (comma-separated) plus `TRIPO_API_KEY` / `TRIPO3D_API_KEY`,
            de-duplicated. Pass an empty list to force a "no key
            configured" failure regardless of environment state.

    Returns:
        `TripoCredentials` for the key+region combo with the highest
        `balance > 0` among all probed candidates.

    Raises:
        ConfigurationError: If the tripo3d SDK is not installed, no key is
            configured, or no candidate key+region combo has a positive
            balance. This function never returns an unusable or empty
            credential silently — every failure mode fails closed.
    """
    keys = _collect_candidate_keys() if candidate_keys is None else candidate_keys

    if not keys:
        raise ConfigurationError(
            "No Tripo API key configured. Set TRIPO_API_KEYS (comma-separated) "
            "or TRIPO_API_KEY / TRIPO3D_API_KEY.",
            config_key="TRIPO_API_KEY",
        )

    best_key, best_result = await _scan_all_candidates(keys)

    if best_key is not None and best_result is not None:
        base_url = (
            os.getenv("TRIPO_API_BASE_URL", DEFAULT_GLOBAL_BASE_URL)
            if best_result["is_global"]
            else DEFAULT_CHINA_BASE_URL
        )
        logger.info(
            "Resolved Tripo credentials: key %s on %s (balance=%.2f)",
            best_result["key_display"],
            best_result["region"],
            best_result["balance"],
        )
        return TripoCredentials(
            api_key=best_key,
            is_global=best_result["is_global"],
            base_url=base_url,
            balance=best_result["balance"],
        )

    raise ConfigurationError(
        f"No Tripo account with credits found across {len(keys)} key(s) x 2 regions. "
        "Add another tsk_* key from the account that holds your credits, or top up "
        "an existing account.",
        config_key="TRIPO_API_KEYS",
    )


__all__ = [
    "TripoCredentials",
    "mask_api_key",
    "resolve_tripo_credentials",
]
