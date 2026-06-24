"""
Live HTTP verification for the SkyyRose production site.

Mirrors the verify_live() gate in deploy-theme.sh:
  - HTTP 200 on each URL
  - Response body >= MIN_BODY_BYTES
  - No PHP error markers in response body

Does NOT touch the live site — read-only HTTP GETs only.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PUBLIC_URL = os.environ.get("PUBLIC_URL", "https://skyyrose.co")
MIN_BODY_BYTES = 50_000

_PHP_ERROR_MARKERS = (
    "Fatal error",
    "Parse error",
    "Call to undefined",
    "There has been a critical error",
    "Warning: include(",
    "Warning: require(",
)

_VERIFY_PATHS = [
    "/",
    "/?s=test",
    "/404-check-skyyrose-nonexistent",
    "/?add-to-cart=1&quantity=1",  # cart page (WC redirect)
    "/shop/",
]


# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class VerifyError(RuntimeError):
    """Base class for verification errors."""


class VerifyFailedError(VerifyError):
    """Raised when one or more URL checks fail."""


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UrlCheckResult:
    url: str
    status_code: int | None
    body_bytes: int
    php_error: str | None  # first matching marker, or None
    error: str | None  # network/request error, or None

    @property
    def ok(self) -> bool:
        return self.status_code in (200, 301, 302) and self.php_error is None and self.error is None

    @property
    def verdict(self) -> Literal["pass", "fail"]:
        return "pass" if self.ok else "fail"


@dataclass
class VerifyReport:
    base_url: str
    results: list[UrlCheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.ok for r in self.results)

    @property
    def summary(self) -> str:
        total = len(self.results)
        failed = sum(1 for r in self.results if not r.ok)
        return f"{total - failed}/{total} checks passed"


# ---------------------------------------------------------------------------
# Core check
# ---------------------------------------------------------------------------


def _check_url(url: str, timeout: int = 15) -> UrlCheckResult:
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "cli-anything-skyyrose-theme/verify"},
        )
        body = resp.text
        body_bytes = len(resp.content)

        # Only check body size on 200s (redirects won't have full content)
        if resp.status_code == 200 and body_bytes < MIN_BODY_BYTES:
            return UrlCheckResult(
                url=url,
                status_code=resp.status_code,
                body_bytes=body_bytes,
                php_error=None,
                error=f"Response too small: {body_bytes} bytes (min {MIN_BODY_BYTES})",
            )

        php_error = next((marker for marker in _PHP_ERROR_MARKERS if marker in body), None)

        return UrlCheckResult(
            url=url,
            status_code=resp.status_code,
            body_bytes=body_bytes,
            php_error=php_error,
            error=None,
        )
    except requests.RequestException as exc:
        return UrlCheckResult(
            url=url,
            status_code=None,
            body_bytes=0,
            php_error=None,
            error=str(exc),
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def verify_live(
    base_url: str | None = None,
    paths: list[str] | None = None,
    timeout: int = 15,
) -> VerifyReport:
    """
    Run HTTP checks against the live site.

    Args:
        base_url: Override PUBLIC_URL env var or default https://skyyrose.co
        paths: URL paths to check (defaults to _VERIFY_PATHS)
        timeout: Per-request timeout in seconds

    Returns:
        VerifyReport with per-URL results.

    Raises:
        VerifyFailedError: if any check fails (includes report in message)
    """
    base = (base_url or DEFAULT_PUBLIC_URL).rstrip("/")
    check_paths = paths or _VERIFY_PATHS
    report = VerifyReport(base_url=base)

    for path in check_paths:
        url = base + path
        result = _check_url(url, timeout=timeout)
        report.results.append(result)

    if not report.passed:
        failures = [r for r in report.results if not r.ok]
        msg = f"verify_live failed ({len(failures)} checks): " + "; ".join(
            f"{r.url} → {r.error or r.php_error or r.status_code}" for r in failures
        )
        raise VerifyFailedError(msg)

    return report
