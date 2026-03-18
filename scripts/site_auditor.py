#!/usr/bin/env python3
"""SkyyRose Site Auditor

Crawls skyyrose.co via Bright Data Web Unlocker, detects bugs, and feeds a
structured audit report into the devskyy_docs RAG vector store so all agents
can query site health.

Checks:
  - HTTP 404 / error pages
  - Broken images (internal 404s)
  - Missing meta title / description / Open Graph tags
  - Broken internal links
  - Deleted SKU content (lh-001, lh-005 must not appear)
  - Product price / pre-order integrity
  - Thin / empty content pages

Usage:
    python scripts/site_auditor.py
    python scripts/site_auditor.py --site-url https://skyyrose.co --max-pages 60
    python scripts/site_auditor.py --no-ingest  # audit only, skip RAG

Author: DevSkyy Platform
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

BRIGHTDATA_API_URL = "https://api.brightdata.com/request"

# Seed paths — always audited regardless of crawl depth
SEED_PATHS = [
    "/",
    "/shop",
    "/about",
    "/blog",
    "/shop/collections/black-rose",
    "/shop/collections/love-hurts",
    "/shop/collections/signature",
    "/shop/collections/kids-capsule",
]

# Deleted SKUs — must NEVER appear in live content
DELETED_SKUS = {"lh-001", "lh-005"}

# Expected price range per collection (min, max in USD)
COLLECTION_PRICE_RANGES = {
    "black-rose": (35, 115),
    "love-hurts": (45, 265),
    "signature": (25, 195),
    "kids-capsule": (40, 40),
}

# URL patterns to skip (not content pages)
SKIP_PATTERNS = re.compile(
    r"\.(css|js|png|jpg|jpeg|webp|gif|svg|ico|woff2?|ttf|pdf|xml|txt)$"
    r"|/wp-json/|/wp-admin/|/feed/|/wp-content/|#",
    re.IGNORECASE,
)

# ─── Data models ──────────────────────────────────────────────────────────────


@dataclass
class PageIssue:
    issue_type: str
    severity: str  # critical | high | medium | low
    detail: str
    element: str = ""


@dataclass
class PageAudit:
    url: str
    status: int  # 200, 404, etc. (inferred)
    title: str
    description: str
    issues: list[PageIssue] = field(default_factory=list)
    checked_at: float = field(default_factory=time.time)

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def highest_severity(self) -> str:
        for sev in ("critical", "high", "medium", "low"):
            if any(i.severity == sev for i in self.issues):
                return sev
        return "ok"


@dataclass
class AuditReport:
    site_url: str
    audited_at: float
    pages: list[PageAudit] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return sum(p.issue_count for p in self.pages)

    def issues_by_severity(self, severity: str) -> list[tuple[str, PageIssue]]:
        return [
            (p.url, issue) for p in self.pages for issue in p.issues if issue.severity == severity
        ]


# ─── Web Unlocker fetcher (raw HTML) ──────────────────────────────────────────


class _PageFetcher:
    """Fetches pages via Bright Data Web Unlocker and returns raw HTML."""

    _MAX_RETRIES = 3

    def __init__(self, api_key: str, unlocker_zone: str, concurrency: int = 3) -> None:
        self._zone = unlocker_zone
        self._sem = asyncio.Semaphore(concurrency)
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(90.0),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        # Lightweight client for HEAD checks (images, links) — no Unlocker needed
        self._head_client = httpx.AsyncClient(
            timeout=httpx.Timeout(15.0),
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; DevSkyy-Auditor/1.0)"},
        )

    async def __aenter__(self) -> _PageFetcher:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self._client.aclose()
        await self._head_client.aclose()

    async def fetch(self, url: str) -> str:
        """Return raw HTML via Web Unlocker. Empty string on failure."""
        async with self._sem:
            for attempt in range(self._MAX_RETRIES):
                try:
                    resp = await self._client.post(
                        BRIGHTDATA_API_URL,
                        json={"zone": self._zone, "url": url, "format": "raw"},
                    )
                    resp.raise_for_status()
                    return resp.text
                except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.PoolTimeout):
                    if attempt < self._MAX_RETRIES - 1:
                        await asyncio.sleep(2**attempt)
                except httpx.HTTPStatusError as exc:
                    logger.warning("Unlocker %d for %s", exc.response.status_code, url)
                    return ""
            return ""

    async def head(self, url: str) -> int:
        """Return HTTP status code via direct HEAD request."""
        try:
            resp = await self._head_client.head(url)
            return resp.status_code
        except Exception:
            return 0


# ─── HTML analysis helpers ────────────────────────────────────────────────────


def _extract_meta(html: str, name: str) -> str:
    m = re.search(
        rf'<meta\s+name=["\']?{re.escape(name)}["\']?\s+content=["\']?([^"\'>\n]+)',
        html,
        re.IGNORECASE,
    ) or re.search(
        rf'<meta\s+content=["\']?([^"\'>\n]+)["\']?\s+name=["\']?{re.escape(name)}',
        html,
        re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def _extract_og(html: str, prop: str) -> str:
    m = re.search(
        rf'<meta\s+property=["\']?og:{re.escape(prop)}["\']?\s+content=["\']?([^"\'>\n]+)',
        html,
        re.IGNORECASE,
    )
    return m.group(1).strip() if m else ""


def _extract_title(html: str) -> str:
    m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    return m.group(1).strip() if m else ""


def _extract_img_srcs(html: str) -> list[str]:
    return re.findall(r'<img[^>]+src=["\']([^"\'>\s]+)', html, re.IGNORECASE)


def _extract_links(html: str, base_url: str, site_host: str) -> list[str]:
    hrefs = re.findall(r'<a[^>]+href=["\']([^"\'>\s#]+)', html, re.IGNORECASE)
    links = []
    for href in hrefs:
        if href.startswith("mailto:") or href.startswith("tel:"):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.hostname and site_host in parsed.hostname:
            clean = parsed._replace(query="", fragment="").geturl()
            if not SKIP_PATTERNS.search(clean):
                links.append(clean)
    return list(dict.fromkeys(links))  # deduplicate, preserve order


def _infer_status(html: str, url: str) -> int:
    """Infer HTTP status from HTML content (Unlocker always returns 200)."""
    title = _extract_title(html).lower()
    body_snippet = html[:4000].lower()
    if "404" in title or "page not found" in title or "not found" in title:
        return 404
    if "500" in title or "server error" in title or "internal server error" in body_snippet:
        return 500
    if not html.strip():
        return 0
    return 200


def _word_count(html: str) -> int:
    text = re.sub(r"<[^>]+>", " ", html)
    return len(text.split())


# ─── Issue checkers ───────────────────────────────────────────────────────────


def _check_meta_tags(html: str, url: str) -> list[PageIssue]:
    issues: list[PageIssue] = []
    title = _extract_title(html)

    if not title:
        issues.append(PageIssue("missing_title", "critical", "Page has no <title> tag", "<title>"))
    elif len(title) < 10:
        issues.append(
            PageIssue(
                "short_title", "high", f"Title too short ({len(title)} chars): '{title}'", "<title>"
            )
        )

    desc = _extract_meta(html, "description")
    if not desc:
        issues.append(
            PageIssue(
                "missing_meta_description",
                "high",
                "Meta description tag missing",
                '<meta name="description">',
            )
        )
    elif len(desc) < 50:
        issues.append(
            PageIssue(
                "short_meta_description",
                "medium",
                f"Meta description too short ({len(desc)} chars)",
                '<meta name="description">',
            )
        )

    return issues


def _check_og_tags(html: str, url: str) -> list[PageIssue]:
    issues: list[PageIssue] = []
    for prop in ("title", "description", "image"):
        if not _extract_og(html, prop):
            issues.append(
                PageIssue(
                    f"missing_og_{prop}",
                    "medium",
                    f"Open Graph og:{prop} tag missing",
                    f'<meta property="og:{prop}">',
                )
            )
    return issues


def _check_deleted_skus(html: str, url: str) -> list[PageIssue]:
    issues: list[PageIssue] = []
    content_lower = html.lower()
    for sku in DELETED_SKUS:
        # Match SKU as standalone word/handle, not as substring of other SKUs
        if re.search(rf"\b{re.escape(sku)}\b", content_lower):
            issues.append(
                PageIssue(
                    "deleted_sku_visible",
                    "critical",
                    f"Deleted SKU '{sku}' found in page content — must be purged",
                    sku,
                )
            )
    return issues


def _check_thin_content(html: str, url: str) -> list[PageIssue]:
    words = _word_count(html)
    # Product/collection pages should have meaningful content
    is_collection = "/collections/" in url or "/shop" in url or "/product/" in url
    threshold = 80 if is_collection else 50
    if 0 < words < threshold:
        return [
            PageIssue(
                "thin_content",
                "medium",
                f"Page has only {words} words — may be empty or broken",
                "main content",
            )
        ]
    return []


def _check_price_integrity(html: str, url: str) -> list[PageIssue]:
    """Check that prices on collection pages fall within expected ranges."""
    issues: list[PageIssue] = []
    for collection, (min_p, max_p) in COLLECTION_PRICE_RANGES.items():
        if collection not in url:
            continue
        # Extract price values like $45, $195.00
        prices_found = re.findall(r"\$(\d+(?:\.\d{2})?)", html)
        for raw in prices_found:
            price = float(raw)
            if price > 0 and not (
                min_p <= price <= max_p + 50
            ):  # +50 buffer for tax/shipping display
                issues.append(
                    PageIssue(
                        "unexpected_price",
                        "high",
                        f"Price ${price} outside expected range ${min_p}–${max_p} for {collection}",
                        f"${raw}",
                    )
                )
    return issues


# ─── Main auditor ─────────────────────────────────────────────────────────────


class SiteAuditor:
    def __init__(
        self,
        site_url: str,
        fetcher: _PageFetcher,
        max_pages: int = 50,
        page_delay: float = 1.5,
    ) -> None:
        self._site_url = site_url.rstrip("/")
        self._host = urlparse(site_url).hostname or ""
        self._fetcher = fetcher
        self._max_pages = max_pages
        self._page_delay = page_delay

    async def _audit_page(self, url: str) -> tuple[PageAudit, list[str]]:
        logger.info("  Auditing: %s", url)
        html = await self._fetcher.fetch(url)

        status = _infer_status(html, url)
        title = _extract_title(html)
        description = _extract_meta(html, "description")

        issues: list[PageIssue] = []

        if status == 404:
            issues.append(PageIssue("page_404", "critical", "Page returned 404 Not Found", url))
            return (
                PageAudit(
                    url=url, status=status, title=title, description=description, issues=issues
                ),
                [],
            )

        if status == 500:
            issues.append(
                PageIssue("server_error", "critical", "Page returned 500 Server Error", url)
            )
            return (
                PageAudit(
                    url=url, status=status, title=title, description=description, issues=issues
                ),
                [],
            )

        if not html:
            issues.append(
                PageIssue("empty_response", "critical", "Page returned empty response", url)
            )
            return PageAudit(url=url, status=200, title="", description="", issues=issues), []

        # Run all content checks
        issues.extend(_check_meta_tags(html, url))
        issues.extend(_check_og_tags(html, url))
        issues.extend(_check_deleted_skus(html, url))
        issues.extend(_check_thin_content(html, url))
        issues.extend(_check_price_integrity(html, url))

        # Check internal images via HEAD
        img_issues = await self._check_images(html, url)
        issues.extend(img_issues)

        # Discover internal links for crawl queue
        links = _extract_links(html, url, self._host)

        return (
            PageAudit(url=url, status=status, title=title, description=description, issues=issues),
            links,
        )

    async def _check_images(self, html: str, base_url: str) -> list[PageIssue]:
        issues: list[PageIssue] = []
        srcs = _extract_img_srcs(html)

        async def _check_one(src: str) -> PageIssue | None:
            absolute = urljoin(base_url, src)
            parsed = urlparse(absolute)
            # Only check internal images
            if self._host not in (parsed.hostname or ""):
                return None
            status = await self._fetcher.head(absolute)
            if status == 404:
                return PageIssue("broken_image", "high", f"Image 404: {src}", src)
            if status == 0:
                return PageIssue("unreachable_image", "medium", f"Image unreachable: {src}", src)
            return None

        results = await asyncio.gather(*[_check_one(s) for s in srcs[:20]])  # cap at 20 per page
        issues.extend(r for r in results if r is not None)
        return issues

    async def run(self) -> AuditReport:
        report = AuditReport(site_url=self._site_url, audited_at=time.time())
        seeds = [f"{self._site_url}{p}" for p in SEED_PATHS]
        queue: list[str] = list(dict.fromkeys(seeds))
        visited: set[str] = set()

        while queue and len(visited) < self._max_pages:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            audit, discovered = await self._audit_page(url)
            report.pages.append(audit)

            for link in discovered:
                if link not in visited and link not in queue:
                    queue.append(link)

            await asyncio.sleep(self._page_delay)

        return report


# ─── Report formatters ────────────────────────────────────────────────────────


def _page_to_markdown(audit: PageAudit) -> str:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(audit.checked_at))
    sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "ok": "✅"}
    icon = sev_icon.get(audit.highest_severity, "✅")

    lines = [
        f"# Site Audit: {audit.url}",
        "",
        f"**Checked:** {ts}  ",
        f"**HTTP Status:** {audit.status}  ",
        f"**Title:** {audit.title or '(none)'}  ",
        f"**Meta Description:** {audit.description[:120] or '(none)'}  ",
        f"**Overall:** {icon} {audit.highest_severity.upper()} — {audit.issue_count} issue(s)",
        "",
    ]

    if not audit.issues:
        lines.append("No issues detected.")
        return "\n".join(lines)

    lines.append(f"## Issues ({audit.issue_count})")
    for issue in sorted(
        audit.issues, key=lambda i: ["critical", "high", "medium", "low"].index(i.severity)
    ):
        icon = sev_icon.get(issue.severity, "•")
        lines += [
            "",
            f"### {icon} [{issue.severity.upper()}] {issue.issue_type}",
            f"- **Element:** `{issue.element}`" if issue.element else "",
            f"- **Detail:** {issue.detail}",
        ]

    return "\n".join(l for l in lines if l is not None)


def _summary_to_markdown(report: AuditReport) -> str:
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(report.audited_at))
    critical = report.issues_by_severity("critical")
    high = report.issues_by_severity("high")
    medium = report.issues_by_severity("medium")

    lines = [
        "# SkyyRose Site Audit — Summary",
        "",
        f"**Site:** {report.site_url}  ",
        f"**Audited:** {ts}  ",
        f"**Pages checked:** {len(report.pages)}  ",
        f"**Total issues:** {report.total_issues}  ",
        f"**Critical:** {len(critical)} | **High:** {len(high)} | **Medium:** {len(medium)}",
        "",
        "## Pages Audited",
        "",
    ]

    sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "ok": "✅"}
    for p in report.pages:
        icon = sev_icon.get(p.highest_severity, "✅")
        lines.append(f"- {icon} [{p.status}] {p.url} — {p.issue_count} issue(s)")

    if critical:
        lines += ["", "## 🔴 Critical Issues", ""]
        for url, issue in critical:
            lines.append(f"- **{url}** → `{issue.issue_type}`: {issue.detail}")

    if high:
        lines += ["", "## 🟠 High Issues", ""]
        for url, issue in high[:30]:  # cap display at 30
            lines.append(f"- **{url}** → `{issue.issue_type}`: {issue.detail}")

    if medium:
        lines += ["", "## 🟡 Medium Issues", ""]
        for url, issue in medium[:20]:
            lines.append(f"- **{url}** → `{issue.issue_type}`: {issue.detail}")

    return "\n".join(lines)


# ─── Output & ingestion ───────────────────────────────────────────────────────


def _save_report(report: AuditReport, output_dir: Path) -> None:
    pages_dir = output_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    # Summary
    (output_dir / "summary.md").write_text(_summary_to_markdown(report), encoding="utf-8")

    # JSON for programmatic use
    (output_dir / "report.json").write_text(
        json.dumps(
            {
                "site_url": report.site_url,
                "audited_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(report.audited_at)),
                "pages_checked": len(report.pages),
                "total_issues": report.total_issues,
                "pages": [asdict(p) for p in report.pages],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # Per-page markdown
    for audit in report.pages:
        slug = re.sub(r"[^\w-]", "-", urlparse(audit.url).path.strip("/") or "homepage")
        slug = re.sub(r"-{2,}", "-", slug)[:80]
        (pages_dir / f"{slug}.md").write_text(_page_to_markdown(audit), encoding="utf-8")

    logger.info("Report saved → %s", output_dir)


async def _ingest_report(output_dir: Path, collection: str = "devskyy_docs") -> None:
    from orchestration.document_ingestion import DocumentIngestionPipeline, IngestionConfig
    from orchestration.vector_store import VectorStoreConfig, create_vector_store

    vs_config = VectorStoreConfig(collection_name=collection)
    pipeline = DocumentIngestionPipeline(config=IngestionConfig(chunk_size=512, chunk_overlap=50))
    pipeline._vector_store = create_vector_store(vs_config)
    await pipeline.initialize()

    result = await pipeline.ingest_directory(output_dir, recursive=True)
    stats = await pipeline.get_stats()
    doc_count = stats.get("vector_store", {}).get("document_count", "?")

    logger.info(
        "Ingested %d chunks from %d audit files | collection now has %s docs",
        result.total_chunks,
        result.total_documents,
        doc_count,
    )
    if result.failed_files:
        logger.warning("Failed to ingest: %s", result.failed_files[:5])


# ─── CLI ──────────────────────────────────────────────────────────────────────


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit skyyrose.co for bugs and feed results into RAG"
    )
    parser.add_argument("--site-url", default="https://skyyrose.co", help="Site to audit")
    parser.add_argument(
        "--max-pages", type=int, default=50, help="Max pages to crawl (default: 50)"
    )
    parser.add_argument(
        "--concurrency", type=int, default=2, help="Parallel page fetches (default: 2)"
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("audit_reports"), help="Output directory"
    )
    parser.add_argument(
        "--collection", default="devskyy_docs", help="ChromaDB collection (default: devskyy_docs)"
    )
    parser.add_argument("--no-ingest", action="store_true", help="Skip RAG ingestion")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    api_key = os.getenv("BRIGHTDATA_API_KEY")
    unlocker_zone = os.getenv("BRIGHTDATA_UNLOCKER_ZONE", "web_unlocker1")
    if not api_key:
        raise SystemExit("BRIGHTDATA_API_KEY not set — check your .env")

    ts = time.strftime("%Y%m%d-%H%M%S")
    site_slug = re.sub(r"[^\w]", "-", urlparse(args.site_url).hostname or "site")
    output_dir = args.output_dir / f"{site_slug}-{ts}"

    sep = "─" * 56
    print(f"\n{sep}")
    print("  SkyyRose Site Auditor")
    print(f"  Target : {args.site_url}")
    print(f"  Max    : {args.max_pages} pages")
    print(f"  Output : {output_dir}")
    print(f"{sep}\n")

    t0 = time.time()

    async with _PageFetcher(api_key, unlocker_zone, concurrency=args.concurrency) as fetcher:
        auditor = SiteAuditor(
            site_url=args.site_url,
            fetcher=fetcher,
            max_pages=args.max_pages,
            page_delay=1.0,
        )
        report = await auditor.run()

    _save_report(report, output_dir)

    if not args.no_ingest:
        print("\n  Ingesting audit report into RAG...")
        await _ingest_report(output_dir, args.collection)

    elapsed = time.time() - t0
    critical = len(report.issues_by_severity("critical"))
    high = len(report.issues_by_severity("high"))

    print(f"\n{sep}")
    print("  Audit complete")
    print(f"  Pages checked : {len(report.pages)}")
    print(f"  Total issues  : {report.total_issues}")
    print(f"  Critical      : {critical}")
    print(f"  High          : {high}")
    print(f"  Time          : {elapsed:.1f}s")
    print(f"  Report        : {output_dir}/summary.md")
    if not args.no_ingest:
        print(f"  RAG           : {args.collection} collection updated")
    print(f"{sep}\n")

    return 1 if critical > 0 else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
