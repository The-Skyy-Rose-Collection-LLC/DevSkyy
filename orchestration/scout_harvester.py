"""Scout Harvester — input layer for the COMPETITOR_SCOUT agent.

Pulls competitor ad creatives from three sources:

- **Meta Ad Library** (official API)
- **Google Ads Transparency Center** (public export)
- **Internal teardowns** (JSON files authored by the team)

Default mode is fixture-driven: loads `tests/fixtures/competitor_ads/*.json`
so the scout agent can be developed and tested with zero external calls.
Live scraping is gated behind `SCOUT_LIVE_SCRAPE=1` and raises
NotImplementedError until the official-API harvester PR ships.

The downstream COMPETITOR_SCOUT spec scores these payloads against the
8-dimension teardown rubric (knowledge/competitor_intel.md §2) and
synthesizes ad blueprints for SOCIAL_MEDIA + IMAGERY handoff.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Env var name for the live-scrape gate. Centralized so callers and tests
# reference one string and a rename propagates cleanly.
SCOUT_LIVE_MODE_ENV = "SCOUT_LIVE_SCRAPE"


class HarvestSource(StrEnum):
    """Supported scout harvest sources."""

    META_AD_LIBRARY = "meta_ad_library"
    GOOGLE_ADS_TRANSPARENCY = "google_ads_transparency"
    INTERNAL_TEARDOWN = "internal_teardown"


@dataclass(frozen=True)
class HarvestResult:
    """One harvested batch from a single source."""

    source: HarvestSource
    brand: str
    payload: dict[str, Any]
    path: Path | None = None
    is_fixture: bool = True
    errors: tuple[str, ...] = field(default_factory=tuple)


def _fixtures_dir() -> Path:
    """Default fixture directory — the repo's test-fixture tree."""
    here = Path(__file__).resolve()
    return here.parents[1] / "tests" / "fixtures" / "competitor_ads"


def _load_fixture(path: Path) -> HarvestResult:
    """Load one JSON fixture file into a HarvestResult."""
    data = json.loads(path.read_text(encoding="utf-8"))
    source_raw = data.get("source", "")
    try:
        source = HarvestSource(source_raw)
    except ValueError as exc:
        raise ValueError(f"Unknown source {source_raw!r} in {path}") from exc
    brand = data.get("brand") or data.get("page_name") or data.get("advertiser_name") or path.stem
    return HarvestResult(
        source=source,
        brand=str(brand),
        payload=data,
        path=path,
        is_fixture=True,
    )


def load_fixtures(directory: Path | None = None) -> list[HarvestResult]:
    """Public entry — delegates to the cached implementation so repeat calls
    don't re-stat + re-parse the fixture directory. Cache invalidation is a
    non-issue: fixtures are immutable at runtime. Tests that need a fresh
    directory pass an explicit path, which bypasses the cache.
    """
    if directory is not None:
        return _load_fixtures_uncached(directory)
    return _load_fixtures_cached()


def _load_fixtures_uncached(directory: Path) -> list[HarvestResult]:
    if not directory.is_dir():
        raise FileNotFoundError(f"Fixture dir missing: {directory}")
    results: list[HarvestResult] = []
    for path in sorted(directory.glob("*.json")):
        try:
            results.append(_load_fixture(path))
        except (ValueError, json.JSONDecodeError) as exc:
            logger.warning("Skipping invalid fixture %s: %s", path, exc)
    return results


@lru_cache(maxsize=1)
def _load_fixtures_cached() -> list[HarvestResult]:
    return _load_fixtures_uncached(_fixtures_dir())


def is_live_mode() -> bool:
    """True when SCOUT_LIVE_SCRAPE=1; otherwise fixtures mode."""
    return os.environ.get(SCOUT_LIVE_MODE_ENV) == "1"


def harvest(
    source: HarvestSource,
    brand: str,
    **kwargs: Any,
) -> HarvestResult:
    """Dispatch a harvest request. Live mode is deferred; default is fixtures.

    Args:
        source: which harvest backend to use
        brand: competitor brand identifier (e.g. Meta page_id, Google advertiser_id)
        **kwargs: RESERVED for live harvesters (date ranges, region, creative type).
                  Passing kwargs in fixture mode is an API error — fixtures are
                  static and cannot filter by date/region.

    Raises:
        ValueError: kwargs passed in fixture mode (misleading intent)
        NotImplementedError: when SCOUT_LIVE_SCRAPE=1 — live harvesters ship later
    """
    if is_live_mode():
        raise NotImplementedError(
            f"Live scraping deferred. {SCOUT_LIVE_MODE_ENV}=1 requires the "
            f"{source.value} harvester to be wired in a follow-up PR. "
            f"Unset the env var to use fixtures, or pass source={source.value} "
            f"directly to load_fixtures() for offline development."
        )
    if kwargs:
        raise ValueError(
            f"harvest() does not accept kwargs in fixture mode "
            f"(got: {sorted(kwargs)}). Those params are reserved for live "
            f"harvesters; fixtures are static snapshots."
        )

    # Fixture mode — find the matching fixture by source type.
    fixtures = load_fixtures()
    matches = [r for r in fixtures if r.source == source]
    if not matches:
        raise FileNotFoundError(
            f"No fixture for source={source.value}. "
            f"Available: {sorted({r.source.value for r in fixtures})}"
        )
    # Prefer a brand-name match when possible; otherwise return the first.
    for result in matches:
        if brand.lower() in result.brand.lower():
            return result
    logger.info("No brand-match for %r; returning first %s fixture", brand, source.value)
    return matches[0]


__all__ = [
    "HarvestResult",
    "HarvestSource",
    "harvest",
    "is_live_mode",
    "load_fixtures",
]
