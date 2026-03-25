#!/usr/bin/env python3
"""Bright Data SERP API — Documentation Scraper

Finds and extracts official documentation pages for any technology/library
using Bright Data's SERP API. Verified official sources only, all languages.

Usage:
    # Single query, English
    python scripts/docs_scraper.py --queries "React"

    # Multiple queries, specific locale
    python scripts/docs_scraper.py --queries "FastAPI,Django,Vue.js" --lang ja --country jp

    # Search only (no page fetching)
    python scripts/docs_scraper.py --queries "Rust" --search-only

    # Multiple locales from file  (format: lang,country  e.g. "en,us")
    python scripts/docs_scraper.py --queries "Next.js" --langs-file locales.txt

    # Load queries from file (one per line)
    python scripts/docs_scraper.py --queries-file targets.txt --fetch-depth 8

Output structure:
    {output_dir}/{query-slug}/{lang}_{country}/
        ├── serp_results.json      Raw SERP response from Bright Data
        ├── index.json             Summary + all result URLs
        └── pages/
            ├── {slug}.json        Page metadata + content
            └── {slug}.md          Markdown content

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
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urlparse

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ─── API ──────────────────────────────────────────────────────────────────────

BRIGHTDATA_API_URL = "https://api.brightdata.com/request"

# Maximum content characters stored per page (keeps chunks reasonably sized)
MAX_PAGE_CONTENT_CHARS = 12_000

# ─── Official source detection ────────────────────────────────────────────────

UNOFFICIAL_DOMAINS: frozenset[str] = frozenset(
    {
        "medium.com",
        "dev.to",
        "hashnode.com",
        "stackoverflow.com",
        "stackexchange.com",
        "reddit.com",
        "quora.com",
        "freecodecamp.org",
        "codecademy.com",
        "udemy.com",
        "coursera.org",
        "pluralsight.com",
        "tutorialspoint.com",
        "geeksforgeeks.org",
        "w3schools.com",
        "baeldung.com",
        "javatpoint.com",
        "guru99.com",
        "simplilearn.com",
        "hackernoon.com",
        "towardsdatascience.com",
    }
)

OFFICIAL_PATH_SIGNALS: frozenset[str] = frozenset(
    {
        "/docs/",
        "/documentation/",
        "/api/",
        "/api-reference/",
        "/reference/",
        "/guide/",
        "/guides/",
        "/manual/",
        "/book/",
        "/learn/",
        "/tutorial/",
        "/getting-started/",
        "/overview/",
    }
)

OFFICIAL_SUBDOMAIN_SIGNALS: frozenset[str] = frozenset(
    {
        "docs",
        "developer",
        "developers",
        "learn",
        "guide",
        "reference",
        "api",
        "manual",
    }
)

# Domains that are documentation-hosting platforms — any project subdomain on
# these hosts is considered an official doc site (e.g. fastapi.tiangolo.com is
# the FastAPI author's domain, but readthedocs.io / github.io are generic).
DOCS_HOSTING_TLDS: frozenset[str] = frozenset(
    {
        "readthedocs.io",
        "readthedocs.org",
        "rtfd.io",
        "github.io",
        "gitbook.io",
        "netlify.app",  # many open-source projects host docs here
        "vercel.app",  # same
        "pages.dev",  # Cloudflare Pages
    }
)

# ─── Locale mappings ──────────────────────────────────────────────────────────

# ISO 639-1 → Google hl parameter
LANGUAGE_HL: dict[str, str] = {
    "en": "en",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "it": "it",
    "pt": "pt",
    "nl": "nl",
    "ru": "ru",
    "ja": "ja",
    "ko": "ko",
    "zh": "zh-CN",
    "zh-tw": "zh-TW",
    "ar": "ar",
    "hi": "hi",
    "tr": "tr",
    "pl": "pl",
    "sv": "sv",
    "da": "da",
    "fi": "fi",
    "nb": "no",
    "cs": "cs",
    "sk": "sk",
    "hu": "hu",
    "ro": "ro",
    "bg": "bg",
    "hr": "hr",
    "uk": "uk",
    "vi": "vi",
    "th": "th",
    "id": "id",
    "ms": "ms",
    "he": "he",
    "el": "el",
    "lt": "lt",
    "lv": "lv",
    "et": "et",
    "sl": "sl",
    "sr": "sr",
    "ca": "ca",
    "fa": "fa",
    "bn": "bn",
    "ta": "ta",
    "te": "te",
    "mr": "mr",
    "ur": "ur",
    "sw": "sw",
}

# ISO 3166-1 alpha-2 → Google gl parameter
COUNTRY_GL: dict[str, str] = {
    "us": "us",
    "gb": "gb",
    "ca": "ca",
    "au": "au",
    "in": "in",
    "de": "de",
    "fr": "fr",
    "jp": "jp",
    "kr": "kr",
    "cn": "cn",
    "tw": "tw",
    "br": "br",
    "mx": "mx",
    "es": "es",
    "it": "it",
    "nl": "nl",
    "ru": "ru",
    "pl": "pl",
    "se": "se",
    "no": "no",
    "dk": "dk",
    "fi": "fi",
    "ar": "ar",
    "za": "za",
    "ng": "ng",
    "sg": "sg",
    "my": "my",
    "id": "id",
    "th": "th",
    "vn": "vn",
    "ph": "ph",
    "eg": "eg",
    "il": "il",
    "tr": "tr",
    "sa": "sa",
    "ae": "ae",
    "pk": "pk",
    "bd": "bd",
    "nz": "nz",
    "ie": "ie",
    "ch": "ch",
    "at": "at",
    "be": "be",
    "pt": "pt",
    "cz": "cz",
    "hu": "hu",
    "ro": "ro",
    "ua": "ua",
}

# ─── Data models ──────────────────────────────────────────────────────────────


@dataclass
class SERPResult:
    position: int
    title: str
    url: str
    description: str
    is_official: bool = False


@dataclass
class DocPage:
    url: str
    title: str
    content: str  # markdown
    lang: str
    country: str
    query: str
    slug: str
    fetched_at: float = field(default_factory=time.time)
    char_count: int = 0

    def __post_init__(self) -> None:
        self.char_count = len(self.content)


@dataclass
class DocCollection:
    query: str
    lang: str
    country: str
    scraped_at: float
    serp_results: list[SERPResult] = field(default_factory=list)
    pages: list[DocPage] = field(default_factory=list)

    @property
    def official_results(self) -> list[SERPResult]:
        return [r for r in self.serp_results if r.is_official]


# ─── Bright Data client ────────────────────────────────────────────────────────


class BrightDataSERPClient:
    """Async client for the Bright Data SERP API REST endpoint."""

    _RETRY_STATUSES = {429, 502, 503, 504}
    _MAX_RETRIES = 3

    # Headers that mimic a browser for direct doc page fetches
    _DOC_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(
        self,
        api_key: str,
        zone: str,
        unlocker_zone: str | None = None,
        timeout: float = 90.0,
        max_concurrency: int = 5,
    ) -> None:
        self._zone = zone
        self._unlocker_zone = unlocker_zone
        self._sem = asyncio.Semaphore(max_concurrency)
        # Bright Data SERP API client — handles both SERP queries and Web Unlocker fetches
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        # Direct HTTP client for fetching doc pages (fallback when unlocker not configured)
        self._doc_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers=self._DOC_HEADERS,
            follow_redirects=True,
        )

    async def __aenter__(self) -> BrightDataSERPClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self._client.aclose()
        await self._doc_client.aclose()

    async def _post(self, payload: dict) -> dict | str:
        """POST to Bright Data with exponential-backoff retry."""
        async with self._sem:
            for attempt in range(self._MAX_RETRIES):
                try:
                    resp = await self._client.post(BRIGHTDATA_API_URL, json=payload)
                    resp.raise_for_status()
                    ct = resp.headers.get("content-type", "")
                    return resp.json() if "json" in ct else resp.text
                except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
                    wait = 2**attempt
                    logger.warning(
                        "Bright Data timeout (%s) — retry %d/%d in %ds",
                        type(exc).__name__,
                        attempt + 1,
                        self._MAX_RETRIES,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code in self._RETRY_STATUSES:
                        wait = 2**attempt
                        logger.warning(
                            "Bright Data %d — retry %d/%d in %ds",
                            exc.response.status_code,
                            attempt + 1,
                            self._MAX_RETRIES,
                            wait,
                        )
                        await asyncio.sleep(wait)
                        continue
                    logger.error(
                        "Bright Data error %d: %s",
                        exc.response.status_code,
                        exc.response.text[:200],
                    )
                    raise
            raise RuntimeError(f"Max retries ({self._MAX_RETRIES}) exceeded")

    async def search(
        self,
        query: str,
        lang: str = "en",
        country: str = "us",
        num: int = 10,
    ) -> dict:
        """Run a Google search query, return parsed SERP results."""
        hl = LANGUAGE_HL.get(lang, lang)
        gl = COUNTRY_GL.get(country, country)
        encoded_q = quote_plus(query)
        google_url = f"https://www.google.com/search?q={encoded_q}&hl={hl}&gl={gl}&brd_json=1"
        payload = {
            "zone": self._zone,
            "url": google_url,
            "format": "raw",
            "data_format": "parsed_light",
        }
        result = await self._post(payload)
        if isinstance(result, str):
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {"raw": result}
        return result

    async def fetch_page(self, url: str) -> str:
        """Fetch a documentation page and return cleaned text.

        Prefers Web Unlocker (handles JS-rendered sites) when configured.
        Falls back to a direct HTTP request with browser headers.
        """
        if self._unlocker_zone:
            return await self._fetch_page_unlocker(url)
        async with self._sem:
            resp = await self._doc_client.get(url)
            resp.raise_for_status()
            return _html_to_text(resp.text)

    async def _fetch_page_unlocker(self, url: str) -> str:
        """Fetch a page through Bright Data Web Unlocker (JS-rendering + geo-bypass)."""
        payload = {
            "zone": self._unlocker_zone,
            "url": url,
            "format": "raw",
        }
        result = await self._post(payload)
        if not isinstance(result, str):
            return ""
        text = _html_to_text(result)
        return text[:MAX_PAGE_CONTENT_CHARS] if len(text) > MAX_PAGE_CONTENT_CHARS else text


# ─── Official docs filter ──────────────────────────────────────────────────────


class OfficialDocsFilter:
    """Heuristically identifies verified official documentation URLs."""

    def __init__(self, extra_blocked: set[str] | None = None) -> None:
        self._blocked = UNOFFICIAL_DOMAINS | (extra_blocked or set())

    def is_blocked(self, url: str) -> bool:
        """Return True if the URL is from a known unofficial domain."""
        try:
            hostname = (urlparse(url).hostname or "").lower()
        except Exception:
            return True
        return any(blocked in hostname for blocked in self._blocked)

    def is_official(self, url: str, title: str = "", description: str = "") -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False

        hostname = (parsed.hostname or "").lower()
        path = parsed.path.lower()
        parts = hostname.split(".")
        subdomain = parts[0] if len(parts) > 2 else ""

        # Block known unofficial sources
        if self.is_blocked(url):
            return False

        # Official if hosted on a known documentation platform (readthedocs.io, github.io, etc.)
        if any(hostname.endswith(tld) for tld in DOCS_HOSTING_TLDS):
            return True

        # Official if subdomain matches known doc subdomains
        if subdomain in OFFICIAL_SUBDOMAIN_SIGNALS:
            return True

        # Official if path contains doc-like segments
        for signal in OFFICIAL_PATH_SIGNALS:
            if signal in path:
                return True

        # Official if title or description mentions documentation
        combined = (title + " " + description).lower()
        return any(
            kw in combined
            for kw in ("official documentation", "official docs", " documentation", "api reference")
        )


# ─── SERP parser ──────────────────────────────────────────────────────────────


def parse_serp_response(raw: dict, doc_filter: OfficialDocsFilter) -> list[SERPResult]:
    """Extract organic results + sitelinks from a Bright Data SERP response.

    Google surfaces sitelinks (extensions with type='site_link') for the top
    result — these are the most important sub-pages of the official docs
    (e.g. /reference/, /learn/, /tutorial/).  We emit them as additional
    SERPResults so they get fetched and ingested without a second SERP query.
    """
    organic: list[dict] = (
        raw.get("organic")
        or raw.get("results")
        or (raw.get("general") or {}).get("organic", [])
        or []
    )

    results: list[SERPResult] = []
    seen: set[str] = set()

    for i, item in enumerate(organic):
        link: str = item.get("link") or item.get("url") or ""
        title: str = item.get("title") or ""
        desc: str = item.get("description") or item.get("snippet") or ""
        if not link or link in seen:
            continue
        seen.add(link)

        top_position = i < 3 and not doc_filter.is_blocked(link)
        results.append(
            SERPResult(
                position=i + 1,
                title=title,
                url=link,
                description=desc,
                is_official=doc_filter.is_official(link, title, desc) or top_position,
            )
        )

        # Expand sitelinks from Google's structured extensions for top results.
        # These are pre-vetted deep links (Reference, Learn, Tutorial…) from the
        # same domain — treat them as official if the parent result is official.
        if top_position:
            for ext in item.get("extensions", []):
                if ext.get("type") != "site_link":
                    continue
                sl_link: str = ext.get("link", "")
                sl_text: str = ext.get("text", "")
                if not sl_link or sl_link in seen:
                    continue
                seen.add(sl_link)
                results.append(
                    SERPResult(
                        position=i + 1,  # same rank as parent
                        title=f"{title} — {sl_text}",
                        url=sl_link,
                        description=desc,
                        is_official=True,  # sitelinks of an official result are official
                    )
                )

    return results


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _html_to_text(html: str) -> str:
    """Strip HTML tags and return clean readable text, prioritising main content."""
    # Remove chrome elements (nav, header, footer, sidebar) before any tag stripping
    # so their link/label noise doesn't consume the content budget.
    for chrome_tag in ("nav", "header", "footer", "aside"):
        html = re.sub(
            rf"<{chrome_tag}[^>]*>.*?</{chrome_tag}>",
            "",
            html,
            flags=re.DOTALL | re.IGNORECASE,
        )
    # Remove script/style blocks entirely
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Heading tags → markdown-style prefix so content hierarchy is preserved
    html = re.sub(r"<h1[^>]*>", "\n# ", html, flags=re.IGNORECASE)
    html = re.sub(r"<h2[^>]*>", "\n## ", html, flags=re.IGNORECASE)
    html = re.sub(r"<h3[^>]*>", "\n### ", html, flags=re.IGNORECASE)
    html = re.sub(r"<h[4-6][^>]*>", "\n#### ", html, flags=re.IGNORECASE)
    # Only semantic block elements get newlines — <div> is stripped silently to avoid
    # Vitepress/Docusaurus sidebar noise (those apps wrap every item in <div>).
    html = re.sub(r"<(br|p|li|tr)[^>]*>", "\n", html, flags=re.IGNORECASE)
    # Strip remaining tags
    html = re.sub(r"<[^>]+>", "", html)
    # Decode common HTML entities
    for entity, char in (
        ("&amp;", "&"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&#39;", "'"),
        ("&nbsp;", " "),
    ):
        html = html.replace(entity, char)
    # Collapse horizontal whitespace per-line, then strip whitespace-only lines
    html = re.sub(r"[ \t]+", " ", html)
    lines = [ln.strip() for ln in html.splitlines()]
    # Remove consecutive blank lines — keep at most one separator
    result: list[str] = []
    blank_run = 0
    for ln in lines:
        if ln == "":
            blank_run += 1
            if blank_run == 1:
                result.append("")
        else:
            blank_run = 0
            result.append(ln)
    return "\n".join(result).strip()


def slugify(text: str) -> str:
    """Convert text to a filesystem-safe slug (max 80 chars)."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s-]+", "-", text).strip("-")[:80]


def _build_doc_query(library: str) -> str:
    """Construct a Google query optimised for official documentation."""
    # Cap exclusions to keep the query short (Google truncates long queries)
    noise_sites = " ".join(f"-site:{d}" for d in sorted(UNOFFICIAL_DOMAINS)[:6])
    return f"{library} official documentation {noise_sites}"


# ─── Scraper ──────────────────────────────────────────────────────────────────


class DocsScraper:
    """Orchestrates SERP search + optional page fetching for documentation."""

    def __init__(
        self,
        client: BrightDataSERPClient,
        output_dir: Path,
        doc_filter: OfficialDocsFilter,
        fetch_depth: int = 5,
        search_only: bool = False,
        page_delay: float = 1.0,
    ) -> None:
        self._client = client
        self._output_dir = output_dir
        self._filter = doc_filter
        self._fetch_depth = fetch_depth
        self._search_only = search_only
        self._page_delay = page_delay

    def _collection_path(self, query: str, lang: str, country: str) -> Path:
        return self._output_dir / slugify(query) / f"{lang}_{country}"

    async def scrape_query(
        self, query: str, lang: str = "en", country: str = "us"
    ) -> DocCollection:
        collection = DocCollection(
            query=query,
            lang=lang,
            country=country,
            scraped_at=time.time(),
        )

        # 1 — SERP search
        search_q = _build_doc_query(query)
        logger.info("[%s/%s] Searching: %s", lang, country, search_q)
        raw_serp = await self._client.search(search_q, lang=lang, country=country)
        collection.serp_results = parse_serp_response(raw_serp, self._filter)

        logger.info(
            "[%s/%s] %d results (%d official)",
            lang,
            country,
            len(collection.serp_results),
            len(collection.official_results),
        )

        # 2 — Page fetching (official only, up to fetch_depth)
        if not self._search_only:
            targets = collection.official_results[: self._fetch_depth]
            for result in targets:
                await asyncio.sleep(self._page_delay)
                page = await self._fetch_page(result, query, lang, country)
                if page:
                    collection.pages.append(page)

        # 3 — Persist to disk
        self._save(collection, raw_serp)
        return collection

    async def _fetch_page(
        self, result: SERPResult, query: str, lang: str, country: str
    ) -> DocPage | None:
        # Prefer Web Unlocker full-page content; fall back to SERP description snippet.
        content: str = ""
        if self._client._unlocker_zone:
            try:
                logger.info("  Fetching (Web Unlocker): %s", result.url)
                content = await self._client.fetch_page(result.url)
            except Exception as exc:
                logger.warning(
                    "  Unlocker failed for %s: %s — falling back to SERP snippet", result.url, exc
                )

        if not content:
            if not result.description:
                return None
            logger.info("  Indexing (SERP snippet): %s", result.url)
            content = result.description

        return DocPage(
            url=result.url,
            title=result.title,
            content=f"## {result.title}\n\n{content}\n\nSource: {result.url}",
            lang=lang,
            country=country,
            query=query,
            slug=slugify(result.title or result.url),
        )

    def _save(self, collection: DocCollection, raw_serp: dict) -> None:
        out = self._collection_path(collection.query, collection.lang, collection.country)
        pages_dir = out / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)

        # Raw SERP response
        (out / "serp_results.json").write_text(
            json.dumps(raw_serp, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Human-readable index
        index = {
            "query": collection.query,
            "lang": collection.lang,
            "country": collection.country,
            "scraped_at_iso": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(collection.scraped_at)
            ),
            "total_results": len(collection.serp_results),
            "official_results": len(collection.official_results),
            "pages_fetched": len(collection.pages),
            "serp_summary": [
                {
                    "position": r.position,
                    "title": r.title,
                    "url": r.url,
                    "is_official": r.is_official,
                    "description": r.description[:160],
                }
                for r in collection.serp_results
            ],
        }
        (out / "index.json").write_text(
            json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Individual pages
        for page in collection.pages:
            base = pages_dir / page.slug
            (base.with_suffix(".json")).write_text(
                json.dumps(asdict(page), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            (base.with_suffix(".md")).write_text(
                f"# {page.title}\n\n> **Source:** {page.url}  \n> **Lang:** {page.lang} / **Country:** {page.country}\n\n{page.content}",
                encoding="utf-8",
            )

        logger.info("Saved → %s", out)

    async def run(
        self,
        queries: list[str],
        langs: list[str],
        countries: list[str],
    ) -> list[DocCollection]:
        """Scrape all queries for every (lang, country) pair."""
        tasks = [
            self.scrape_query(q, lang=lng, country=cty)
            for q in queries
            for lng, cty in zip(langs, countries, strict=False)
        ]
        return await asyncio.gather(*tasks)


# ─── CLI ──────────────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scrape official documentation via Bright Data SERP API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--queries", metavar="A,B,...", help="Comma-separated library/tech names")
    src.add_argument(
        "--queries-file", type=Path, metavar="FILE", help="File with one query per line"
    )

    locale = p.add_mutually_exclusive_group()
    locale.add_argument(
        "--langs-file", type=Path, metavar="FILE", help="File with 'lang,country' lines"
    )
    locale.add_argument(
        "--lang", default="en", metavar="CODE", help="ISO 639-1 language code (default: en)"
    )

    p.add_argument(
        "--country",
        default="us",
        metavar="CODE",
        help="ISO 3166-1 alpha-2 country code (default: us)",
    )
    p.add_argument(
        "--output", type=Path, default=Path("scraped_docs"), metavar="DIR", help="Output directory"
    )
    p.add_argument(
        "--fetch-depth",
        type=int,
        default=5,
        metavar="N",
        help="Official pages to fetch per query (default: 5)",
    )
    p.add_argument(
        "--search-only", action="store_true", help="Only collect SERP results, skip page fetching"
    )
    p.add_argument(
        "--concurrency",
        type=int,
        default=3,
        metavar="N",
        help="Max parallel Bright Data requests (default: 3)",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=1.0,
        metavar="SECS",
        help="Seconds between page fetches (default: 1.0)",
    )
    p.add_argument("--verbose", action="store_true", help="Enable DEBUG logging")
    return p.parse_args()


async def main() -> None:
    args = _parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
    )

    api_key = os.getenv("BRIGHTDATA_API_KEY")
    zone = os.getenv("BRIGHTDATA_ZONE", "serp_api1")
    if not api_key:
        raise SystemExit("BRIGHTDATA_API_KEY not found in environment — check your .env")

    # Resolve queries
    if args.queries_file:
        raw_lines = args.queries_file.read_text(encoding="utf-8").splitlines()
        queries = [q.strip() for q in raw_lines if q.strip() and not q.startswith("#")]
    else:
        queries = [q.strip() for q in args.queries.split(",") if q.strip()]

    # Resolve locale pairs
    if args.langs_file:
        pairs = [
            ln.strip().split(",")
            for ln in args.langs_file.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")
        ]
        langs = [p[0].strip() for p in pairs]
        countries = [p[1].strip() if len(p) > 1 else "us" for p in pairs]
    else:
        langs = [args.lang]
        countries = [args.country]

    if not queries:
        raise SystemExit("No queries provided")

    logger.info(
        "Scraping %d quer%s × %d locale%s  (search_only=%s, fetch_depth=%d)",
        len(queries),
        "y" if len(queries) == 1 else "ies",
        len(langs),
        "" if len(langs) == 1 else "s",
        args.search_only,
        args.fetch_depth,
    )

    async with BrightDataSERPClient(api_key, zone, max_concurrency=args.concurrency) as client:
        scraper = DocsScraper(
            client=client,
            output_dir=args.output,
            doc_filter=OfficialDocsFilter(),
            fetch_depth=args.fetch_depth,
            search_only=args.search_only,
            page_delay=args.delay,
        )
        collections: list[DocCollection] = await scraper.run(queries, langs, countries)

    # ── Summary ──────────────────────────────────────────────────────────────
    total_serp = sum(len(c.serp_results) for c in collections)
    total_official = sum(len(c.official_results) for c in collections)
    total_pages = sum(len(c.pages) for c in collections)
    total_chars = sum(p.char_count for c in collections for p in c.pages)

    sep = "─" * 52
    print(f"\n{sep}")
    print(f"  Queries scraped  : {len(queries)}")
    print(f"  Locales          : {len(langs)}")
    print(f"  SERP results     : {total_serp}")
    print(f"  Official URLs    : {total_official}")
    print(f"  Pages fetched    : {total_pages}")
    print(f"  Content size     : {total_chars:,} chars")
    print(f"  Output dir       : {args.output.resolve()}")
    print(f"{sep}\n")


if __name__ == "__main__":
    asyncio.run(main())
