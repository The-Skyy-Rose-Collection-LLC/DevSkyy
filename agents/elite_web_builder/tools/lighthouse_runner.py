"""Lighthouse performance measurement tool for Elite Web Builder.

Wraps the Lighthouse CLI (via npx) and parses JSON output into
immutable dataclasses. Provides performance budget checking and
markdown report formatting.

Usage:
    result = run_lighthouse("https://example.com")
    budget = check_performance_budget(result)
    report = format_report(result)

Requires: Node.js + npx available on PATH.
"""

from __future__ import annotations

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BUDGET: dict[str, float] = {
    "performance": 80.0,
    "accessibility": 90.0,
    "best_practices": 80.0,
    "seo": 80.0,
}

VALID_DEVICES = frozenset({"mobile", "desktop"})

ALL_CATEGORIES = ("performance", "accessibility", "best-practices", "seo")

# Maps Lighthouse audit IDs to short metric names
METRIC_AUDIT_MAP: dict[str, str] = {
    "first-contentful-paint": "FCP",
    "largest-contentful-paint": "LCP",
    "total-blocking-time": "TBT",
    "cumulative-layout-shift": "CLS",
    "speed-index": "SI",
}

LIGHTHOUSE_TIMEOUT_SECONDS = 120


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class LighthouseError(Exception):
    """Raised when Lighthouse CLI fails or returns invalid output."""


# ---------------------------------------------------------------------------
# Data models (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LighthouseResult:
    """Immutable container for a Lighthouse audit result."""

    url: str
    performance_score: float
    accessibility_score: float
    best_practices_score: float
    seo_score: float
    metrics: dict[str, float]
    audits: list[dict[str, Any]]
    timestamp: str


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def _build_command(
    url: str,
    categories: list[str] | None,
    device: str,
) -> list[str]:
    """Build the npx lighthouse CLI command."""
    cmd = [
        "npx",
        "lighthouse",
        url,
        "--output=json",
        "--quiet",
        "--chrome-flags=--headless --no-sandbox",
    ]
    if device == "desktop":
        cmd.append("--preset=desktop")
    if categories:
        cmd.append(f"--only-categories={','.join(categories)}")
    return cmd


def _extract_score(
    categories: dict[str, Any],
    category_key: str,
) -> float:
    """Extract a category score (0-100) from the report, defaulting to 0."""
    category = categories.get(category_key, {})
    raw_score = category.get("score")
    if raw_score is None:
        return 0.0
    return round(raw_score * 100, 1)


def _extract_metrics(audits: dict[str, Any]) -> dict[str, float]:
    """Extract core web vitals metrics from audit data."""
    metrics: dict[str, float] = {}
    for audit_id, short_name in METRIC_AUDIT_MAP.items():
        audit = audits.get(audit_id, {})
        value = audit.get("numericValue")
        metrics[short_name] = float(value) if value is not None else 0.0
    return metrics


def _extract_failed_audits(
    audits: dict[str, Any],
) -> list[dict[str, Any]]:
    """Collect audits with score < 1 (failed or warning), excluding None scores."""
    failed: list[dict[str, Any]] = []
    for audit_id, audit_data in audits.items():
        score = audit_data.get("score")
        if score is None:
            continue
        if score < 1:
            failed.append({
                "id": audit_data.get("id", audit_id),
                "title": audit_data.get("title", audit_id),
                "score": score,
            })
    return failed


def _parse_report(
    raw_json: str,
    url: str,
    timestamp: str,
) -> LighthouseResult:
    """Parse raw Lighthouse JSON output into a LighthouseResult."""
    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, TypeError) as exc:
        raise LighthouseError(
            f"Failed to parse Lighthouse JSON output: {exc}"
        ) from exc

    categories = data.get("categories")
    if categories is None:
        raise LighthouseError(
            "Missing 'categories' key in Lighthouse report"
        )

    audits_raw = data.get("audits", {})

    return LighthouseResult(
        url=url,
        performance_score=_extract_score(categories, "performance"),
        accessibility_score=_extract_score(categories, "accessibility"),
        best_practices_score=_extract_score(categories, "best-practices"),
        seo_score=_extract_score(categories, "seo"),
        metrics=_extract_metrics(audits_raw),
        audits=_extract_failed_audits(audits_raw),
        timestamp=timestamp,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_lighthouse(
    url: str,
    categories: list[str] | None = None,
    device: str = "mobile",
) -> LighthouseResult:
    """Run Lighthouse CLI and return parsed results.

    Args:
        url: The URL to audit (must be non-empty).
        categories: Optional list of categories to audit.
            Defaults to all (performance, accessibility, best-practices, seo).
        device: Either "mobile" (default) or "desktop".

    Returns:
        LighthouseResult with scores, metrics, and failed audits.

    Raises:
        ValueError: If url is empty or device is invalid.
        LighthouseError: If Lighthouse CLI fails or returns bad output.
    """
    if not url or not url.strip():
        raise ValueError("url must not be empty")
    if device not in VALID_DEVICES:
        raise ValueError(
            f"device must be one of {sorted(VALID_DEVICES)}, got '{device}'"
        )

    cmd = _build_command(url.strip(), categories, device)
    timestamp = _get_timestamp()

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=LIGHTHOUSE_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise LighthouseError(
            "Lighthouse is not installed. "
            "Install with: npm install -g lighthouse"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise LighthouseError(
            f"Lighthouse timed out after {LIGHTHOUSE_TIMEOUT_SECONDS}s"
        ) from exc

    if proc.returncode != 0:
        raise LighthouseError(
            f"Lighthouse exited with exit code {proc.returncode}: "
            f"{proc.stderr.strip()}"
        )

    return _parse_report(proc.stdout, url.strip(), timestamp)


def check_performance_budget(
    result: LighthouseResult,
    budget: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Check a LighthouseResult against a performance budget.

    Args:
        result: The LighthouseResult to evaluate.
        budget: Optional custom thresholds. Defaults to DEFAULT_BUDGET.
            Keys: performance, accessibility, best_practices, seo.
            Values: minimum passing score (0-100).

    Returns:
        New dict with per-category status and an overall pass/fail.
    """
    effective_budget = {**DEFAULT_BUDGET, **(budget or {})}

    score_map = {
        "performance": result.performance_score,
        "accessibility": result.accessibility_score,
        "best_practices": result.best_practices_score,
        "seo": result.seo_score,
    }

    checks: dict[str, Any] = {"url": result.url}
    all_passing = True

    for category, threshold in effective_budget.items():
        actual = score_map.get(category, 0.0)
        passing = actual >= threshold
        if not passing:
            all_passing = False
        checks[category] = {
            "status": "pass" if passing else "fail",
            "actual": actual,
            "threshold": threshold,
        }

    checks["overall"] = "pass" if all_passing else "fail"
    return checks


def format_report(result: LighthouseResult) -> str:
    """Format a LighthouseResult as a readable markdown string.

    Args:
        result: The LighthouseResult to format.

    Returns:
        Markdown-formatted report string.
    """
    lines = [
        f"# Lighthouse Report",
        f"",
        f"**URL:** {result.url}",
        f"**Timestamp:** {result.timestamp}",
        f"",
        f"## Scores",
        f"",
        f"| Category | Score |",
        f"|----------|-------|",
        f"| Performance | {result.performance_score} |",
        f"| Accessibility | {result.accessibility_score} |",
        f"| Best Practices | {result.best_practices_score} |",
        f"| SEO | {result.seo_score} |",
        f"",
        f"## Core Web Vitals",
        f"",
    ]

    for key, value in result.metrics.items():
        lines.append(f"- **{key}:** {value}")

    lines.append("")

    if result.audits:
        lines.append("## Failed / Warning Audits")
        lines.append("")
        for audit in result.audits:
            score_pct = round(audit["score"] * 100) if audit["score"] else 0
            lines.append(
                f"- [{audit['id']}] {audit['title']} "
                f"(score: {score_pct}%)"
            )
    else:
        lines.append("## Audits")
        lines.append("")
        lines.append("All audits passed.")

    lines.append("")
    return "\n".join(lines)
