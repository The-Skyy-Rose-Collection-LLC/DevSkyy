#!/usr/bin/env python3
"""Structural deploy verification for skyyrose.co.

Called by scripts/deploy-theme.sh::verify_live() AFTER the curl-based
HTTP / size / PHP-error checks pass. Uses Scrapling to fetch live pages
and assert that template-specific DOM markers exist - catches regressions
where WordPress returns HTTP 200 but a template fell back to a default
page or stripped a critical section.

Usage:
  python3 verify_live_structure.py                    # homepage only (default)
  python3 verify_live_structure.py --page black-rose  # one named page
  python3 verify_live_structure.py --all              # every registered page
  python3 verify_live_structure.py --list             # print registry, no fetch
  python3 verify_live_structure.py --url https://staging.skyyrose.co --all

Exit codes:
  0 - all assertions passed for every page checked
  2 - one or more assertions failed (real regression) OR usage error
  3 - environment problem (scrapling missing, total network failure)
      Bash deploy script logs as warning; does NOT trigger rollback.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "https://skyyrose.co"
DEFAULT_TIMEOUT = 25

# Cache-bust query param appended to every fetched URL unless --no-cache-bust.
# Bypasses Jetpack Boost page cache so we observe a fresh render.
CACHE_BUST_PARAM = "deploy_verify"

# Number of fetch attempts per page (initial + retries). Set to 1 to disable
# retries. Connection-level errors trigger backoff; HTTP errors do not retry
# (a 500 won't fix itself in 1.5s, but a TLS handshake hiccup might).
FETCH_RETRY_ATTEMPTS = 2
FETCH_RETRY_BACKOFF_SECONDS = 1.5

# Theme slug — extracted because it appears in both the CSS-link selector
# and the human-readable label, so any rename happens in one place.
THEME_SLUG = "skyyrose-flagship"

# Per-collection holo-card minimums derived from the canonical CSV at
# wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv.
# Floors are set ~20% below actual counts so adding/removing one SKU
# does not auto-fail the gate; the regression mode we are catching is
# "page rendered ZERO or ONE card", not "catalog drifted by 1".
COLLECTION_CARD_FLOORS = {
    "black-rose": 12,  # 15 actual
    "love-hurts": 3,  # 4 actual
    "signature": 10,  # 12 actual
    "kids-capsule": 2,  # 2 actual (cannot go lower without breaking)
}


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


class FetchError(Exception):
    """Transport-layer fetch failure (connection, TLS, timeout)."""


@dataclass(frozen=True)
class Assertion:
    selector: str
    min_count: int
    label: str
    # When set, count must satisfy min_count <= actual <= max_count.
    # Used by GLOBAL_ASSERTIONS to assert error markers stay at 0.
    max_count: int | None = None

    def bounds_str(self) -> str:
        if self.max_count is not None and self.max_count == self.min_count:
            return f"exactly={self.min_count}"
        if self.max_count is not None:
            return f"min={self.min_count}, max={self.max_count}"
        return f"min={self.min_count}"


@dataclass(frozen=True)
class Page:
    name: str
    path: str
    assertions: tuple[Assertion, ...]


@dataclass(frozen=True)
class CheckResult:
    assertion: Assertion
    actual: int

    @property
    def passed(self) -> bool:
        if self.actual < self.assertion.min_count:
            return False
        return self.assertion.max_count is None or self.actual <= self.assertion.max_count


@dataclass
class PageReport:
    page: Page
    url: str
    http_status: int
    fetched: bool
    fetch_error: str | None = None
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.fetched and self.http_status == 200 and all(r.passed for r in self.results)


# ---------------------------------------------------------------------------
# Reusable assertion builders
# ---------------------------------------------------------------------------


# Single instance reused across every page in the registry. Renaming the
# theme means changing THEME_SLUG above, not editing 8+ scattered strings.
THEME_CSS_ASSERTION = Assertion(
    f"link[href*='{THEME_SLUG}']",
    1,
    f"theme CSS enqueued ({THEME_SLUG} active)",
)


# Universal assertions applied to every page. Catch render regressions
# without per-page setup. data-skyyrose-error is a project-wide beacon
# emitted by template parts that hit a "should not happen" branch (e.g.,
# template-parts/collection/page.php when content config is missing).
GLOBAL_ASSERTIONS: tuple[Assertion, ...] = (
    Assertion(
        "[data-skyyrose-error]",
        0,
        "no skyyrose render-error markers (universal regression beacon)",
        max_count=0,
    ),
)


def _main_assertion(class_name: str, what_ran: str) -> Assertion:
    """Build a `<main class="X">` assertion with a consistent label format."""
    return Assertion(
        f"main#primary.{class_name}",
        1,
        f"<main class='{class_name}'> ({what_ran})",
    )


def collection_assertions(slug: str) -> tuple[Assertion, ...]:
    """Build assertion tuple for a collection page (BR/LH/SIG/Kids)."""
    floor = COLLECTION_CARD_FLOORS[slug]
    return (
        Assertion(
            f"div.col-page[data-collection='{slug}']",
            1,
            f"<div class='col-page' data-collection='{slug}'>",
        ),
        Assertion("section.col-hero", 1, "<section class='col-hero'> (collection hero)"),
        Assertion(
            "div.holo",
            floor,
            f">= {floor} <.holo> product cards (universal grid rendered)",
        ),
        Assertion(
            f"div.holo--{slug}",
            floor,
            f">= {floor} <.holo--{slug}> cards (collection-specific rendered)",
        ),
        THEME_CSS_ASSERTION,
    )


def immersive_assertions(name: str) -> tuple[Assertion, ...]:
    """Build assertion tuple for the 3 immersive 3D pages.

    `name` is the human-readable collection name (e.g., "Black Rose")
    used only in the label, not in any selector. All 3 immersive pages
    share the same template-emitted markup.
    """
    return (
        _main_assertion("immersive-page", f"immersive template ran for {name}"),
        THEME_CSS_ASSERTION,
    )


HOMEPAGE_ASSERTIONS: tuple[Assertion, ...] = (
    Assertion("body.home", 1, "<body class='home'> (WP routed to front page)"),
    _main_assertion("homepage-v2", "front-page.php template ran"),
    Assertion("nav#mainNav", 1, "<nav id='mainNav'> (header.php rendered)"),
    Assertion("section#hero", 1, "<section id='hero'> (hero section emitted)"),
    Assertion("div#loader", 1, "<div id='loader'> (front-page.php loader element)"),
    THEME_CSS_ASSERTION,
    Assertion("meta[name='generator']", 1, "<meta name='generator'> (WordPress emitted)"),
)


ABOUT_ASSERTIONS: tuple[Assertion, ...] = (
    _main_assertion("abt-page", "about template ran"),
    Assertion("section.abt-hero", 1, "<section class='abt-hero'> (about hero section)"),
    THEME_CSS_ASSERTION,
)


PREORDER_ASSERTIONS: tuple[Assertion, ...] = (
    _main_assertion("preorder-gateway", "preorder template ran"),
    Assertion("section#hero", 1, "<section id='hero'>"),
    Assertion("section#showcase", 1, "<section id='showcase'> (preorder showcase)"),
    THEME_CSS_ASSERTION,
)


# ---------------------------------------------------------------------------
# Page registry
# ---------------------------------------------------------------------------

PAGE_REGISTRY: dict[str, Page] = {
    "home": Page("Homepage", "/", HOMEPAGE_ASSERTIONS),
    "black-rose": Page(
        "Collection: Black Rose",
        "/collection-black-rose/",
        collection_assertions("black-rose"),
    ),
    "love-hurts": Page(
        "Collection: Love Hurts",
        "/collection-love-hurts/",
        collection_assertions("love-hurts"),
    ),
    "signature": Page(
        "Collection: Signature",
        "/collection-signature/",
        collection_assertions("signature"),
    ),
    "kids-capsule": Page(
        "Collection: Kids Capsule",
        "/collection-kids-capsule/",
        collection_assertions("kids-capsule"),
    ),
    "about": Page("About", "/about/", ABOUT_ASSERTIONS),
    "preorder": Page("Pre-Order Gateway", "/pre-order/", PREORDER_ASSERTIONS),
    "experience-black-rose": Page(
        "Immersive: Black Rose",
        "/experience-black-rose/",
        immersive_assertions("Black Rose"),
    ),
    "experience-love-hurts": Page(
        "Immersive: Love Hurts",
        "/experience-love-hurts/",
        immersive_assertions("Love Hurts"),
    ),
    "experience-signature": Page(
        "Immersive: Signature",
        "/experience-signature/",
        immersive_assertions("Signature"),
    ),
}


# ---------------------------------------------------------------------------
# Fetch + evaluate
# ---------------------------------------------------------------------------


def _import_fetcher():
    """Import-late so missing scrapling triggers exit 3, not crash on argparse."""
    try:
        from scrapling.fetchers import Fetcher  # noqa: PLC0415
    except ImportError as exc:
        print(f"[SKIP] Scrapling not available: {exc}", file=sys.stderr)
        print(
            "[SKIP] Install via: source .venv/bin/activate && pip install 'scrapling[all]'",
            file=sys.stderr,
        )
        sys.exit(3)
    return Fetcher


def _fetch_once(fetcher, url: str, timeout: int):
    """Single fetch attempt — wraps any exception into a FetchError."""
    try:
        return fetcher.get(url, timeout=timeout)
    except (OSError, TimeoutError) as exc:
        raise FetchError(f"{type(exc).__name__}: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 — last-resort wrapper for SDK errors
        raise FetchError(f"{type(exc).__name__}: {exc}") from exc


def fetch_page(fetcher, url: str, timeout: int) -> tuple[object | None, str | None]:
    """Fetch with one retry on transport errors. Returns (response, error_str)."""
    last_error: str | None = None
    for attempt in range(FETCH_RETRY_ATTEMPTS):
        try:
            return _fetch_once(fetcher, url, timeout), None
        except FetchError as exc:
            last_error = str(exc)
            is_last = attempt + 1 >= FETCH_RETRY_ATTEMPTS
            if not is_last:
                time.sleep(FETCH_RETRY_BACKOFF_SECONDS * (attempt + 1))
    return None, last_error


def evaluate_assertions(response, assertions: tuple[Assertion, ...]) -> list[CheckResult]:
    """Run every selector against `response` and produce CheckResult per assertion.

    A selector that raises is treated as `count=0` plus a stderr warning —
    the assertion fails (since min_count >= 1 in nearly all cases) but the
    rest of the page's checks still run, so the operator gets a complete
    picture in one pass.
    """
    results: list[CheckResult] = []
    for assertion in assertions:
        try:
            matches = response.css(assertion.selector)
            count = len(matches) if matches is not None else 0
        except (AttributeError, TypeError, ValueError, RuntimeError) as exc:
            print(
                f"  [WARN] Selector {assertion.selector!r} raised {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            count = 0
        results.append(CheckResult(assertion, count))
    return results


def _build_url(base_url: str, path: str, cache_bust: bool) -> str:
    url = urljoin(base_url, path)
    if cache_bust:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{CACHE_BUST_PARAM}={int(time.time())}"
    return url


def check_page(fetcher, page: Page, base_url: str, timeout: int, cache_bust: bool) -> PageReport:
    url = _build_url(base_url, page.path, cache_bust)

    response, err = fetch_page(fetcher, url, timeout)
    if response is None:
        return PageReport(page=page, url=url, http_status=0, fetched=False, fetch_error=err)

    # Defensive: a malformed response object without `status` shouldn't be
    # silently treated as HTTP 0 — it's a transport-layer mismatch worth
    # flagging as a fetch error so the operator knows the contract broke.
    if not hasattr(response, "status"):
        return PageReport(
            page=page,
            url=url,
            http_status=0,
            fetched=False,
            fetch_error="response object missing 'status' attribute",
        )

    status = response.status
    if status != 200:
        return PageReport(page=page, url=url, http_status=status, fetched=True)

    results = evaluate_assertions(response, GLOBAL_ASSERTIONS + page.assertions)
    return PageReport(page=page, url=url, http_status=status, fetched=True, results=results)


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _format_check_line(result: CheckResult) -> str:
    status = "PASS" if result.passed else "FAIL"
    a = result.assertion
    return (
        f"  [{status}] {a.label}  "
        f"(selector={a.selector!r}, found={result.actual}, {a.bounds_str()})"
    )


def print_page_report(report: PageReport) -> None:
    print(f"=== {report.page.name}  ({report.url}) ===")
    if not report.fetched:
        print(f"  [FAIL] Fetch error: {report.fetch_error}")
        return
    if report.http_status != 200:
        print(f"  [FAIL] HTTP {report.http_status} (expected 200)")
        return
    for r in report.results:
        print(_format_check_line(r))


def _summary_detail(report: PageReport) -> str:
    if not report.fetched:
        return "fetch error"
    if report.http_status != 200:
        return f"HTTP {report.http_status}"
    passed_n = sum(1 for r in report.results if r.passed)
    return f"{passed_n}/{len(report.results)} assertions"


def print_summary(reports: list[PageReport]) -> None:
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for r in reports:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.page.name:<30} {_summary_detail(r)}")
    failed = [r for r in reports if not r.passed]
    print(f"\nResult: {len(reports) - len(failed)}/{len(reports)} pages passed")
    if failed:
        print(f"Failed pages: {', '.join(r.page.name for r in failed)}")


def list_registry() -> None:
    print("Global assertions (run on every page):")
    for a in GLOBAL_ASSERTIONS:
        print(f"  - {a.label}  ({a.bounds_str()})")
    print()
    print(f"Registered pages ({len(PAGE_REGISTRY)}):\n")
    for key, page in PAGE_REGISTRY.items():
        print(f"  {key:<22} -> {page.path}")
        print(f"  {'':<22}    {page.name}")
        for a in page.assertions:
            print(f"  {'':<22}    - {a.label}  ({a.bounds_str()})")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _resolve_pages(args: argparse.Namespace) -> list[Page]:
    """Translate --all / --page args into the actual page list to verify.

    Raises SystemExit(2) with a useful message on unknown --page values
    so the operator sees the available registry without re-running --list.
    """
    if args.all:
        return list(PAGE_REGISTRY.values())
    if args.page not in PAGE_REGISTRY:
        known = ", ".join(sorted(PAGE_REGISTRY))
        print(
            f"Unknown page: {args.page!r}\nKnown pages: {known}\n"
            f"Run with --list for full assertion details.",
            file=sys.stderr,
        )
        sys.exit(2)
    return [PAGE_REGISTRY[args.page]]


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--url", default=DEFAULT_BASE_URL, help=f"Base URL (default: {DEFAULT_BASE_URL})"
    )
    parser.add_argument(
        "--page", default="home", help="Page name from registry (default: home). See --list."
    )
    parser.add_argument(
        "--all", action="store_true", help="Verify every registered page (overrides --page)"
    )
    parser.add_argument("--list", action="store_true", help="Print page registry and exit")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Fetch timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--no-cache-bust",
        action="store_true",
        help=f"Skip ?{CACHE_BUST_PARAM}=<ts> query string",
    )
    return parser


def main() -> int:
    args = _build_arg_parser().parse_args()

    if args.list:
        list_registry()
        return 0

    pages = _resolve_pages(args)
    fetcher = _import_fetcher()
    base_url = args.url.rstrip("/")

    reports: list[PageReport] = []
    for page in pages:
        report = check_page(
            fetcher, page, base_url, args.timeout, cache_bust=not args.no_cache_bust
        )
        print_page_report(report)
        reports.append(report)
        print()

    print_summary(reports)

    # Exit 3 if every page failed to fetch (env/network problem),
    # otherwise exit 2 on any structural failure, else 0.
    if not any(r.fetched for r in reports):
        return 3
    return 2 if any(not r.passed for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
