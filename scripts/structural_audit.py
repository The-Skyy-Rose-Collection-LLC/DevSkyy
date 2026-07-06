#!/usr/bin/env python3
"""Structural audit for skyyrose.co — WS6 of the structural remediation spec.

Crawls AUDIT_BASE_URL (default https://skyyrose.co) and asserts the acceptance
criteria of WS1–WS5. Exits non-zero on any failure. Real HTTP only, no fixtures.

Usage:
    AUDIT_BASE_URL=https://staging.example python scripts/structural_audit.py
    python scripts/structural_audit.py --only shell,routes

Checks:
    shell    — one primary-nav landmark, one skip link, no legacy-shell markers
    routes   — every redirects.csv row is a single-hop 301; canonical pages 200
    dom      — nothing after </footer> except hidden dialogs / cookie banner
    data     — piece counts agree between homepage and collections index
    commerce — no GET add-to-cart hrefs, placeholders, countdowns; og:image static
    brand    — no blue-dominant hex (B>R and B>G) in theme CSS or inline styles;
               no gendered merch framing
    meta     — exactly one canonical per page, never pointing at a legacy route
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = os.environ.get("AUDIT_BASE_URL", "https://skyyrose.co").rstrip("/")
REPO_ROOT = Path(__file__).resolve().parent.parent
REDIRECTS_CSV = Path(os.environ.get("AUDIT_REDIRECTS_CSV", REPO_ROOT / "redirects.csv"))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) skyyrose-structural-audit/1.0"
TIMEOUT = 30

CANONICAL_PAGES = [
    "/",
    "/collections/",
    "/collections/black-rose/",
    "/collections/love-hurts/",
    "/collections/signature/",
    "/collections/kids-capsule/",
    "/pre-order/",
    "/about/",
    "/faq/",
    "/size-guide/",
    "/contact/",
]

# Pages whose rendered HTML is swept for shell/commerce/brand/meta assertions.
AUDIT_PAGES = CANONICAL_PAGES

LEGACY_MARKERS = [
    "Enter the Universe",
    "theskyyrosecollection",  # legacy instagram handle (lowercase; FB handle is TitleCase)
    "skyyrosellc",
    'href="/preorder/',
    f'href="{BASE_URL}/preorder/',
]

LEGACY_ROUTES = [
    "/collection-black-rose/",
    "/collection-love-hurts/",
    "/collection-signature/",
    "/collection-kids-capsule/",
    "/experience-black-rose/",
    "/experience-love-hurts/",
    "/experience-signature/",
    "/experience-kids-capsule/",
    "/experiences/",
    "/preorder/",
]

GENDERED_PATTERNS = [
    r"\bmenswear\b",
    r"\bwomenswear\b",
    r"\bfor her\b",
    r"\bfor him\b",
]

COOKIE_HINTS = ("cookie", "consent", "cmplz", "gdpr")


@dataclass
class Audit:
    failures: list[str] = field(default_factory=list)
    passes: list[str] = field(default_factory=list)
    session: requests.Session = field(default_factory=requests.Session)
    _cache: dict[str, requests.Response] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.session.headers["User-Agent"] = UA

    def ok(self, label: str) -> None:
        self.passes.append(label)
        print(f"  PASS  {label}")

    def fail(self, label: str, detail: str = "") -> None:
        msg = f"{label}" + (f" — {detail}" if detail else "")
        self.failures.append(msg)
        print(f"  FAIL  {msg}")

    def check(self, condition: bool, label: str, detail: str = "") -> None:
        if condition:
            self.ok(label)
        else:
            self.fail(label, detail)

    def get(self, path: str, *, allow_redirects: bool = True) -> requests.Response:
        key = f"{path}|{allow_redirects}"
        if key not in self._cache:
            url = path if path.startswith("http") else f"{BASE_URL}{path}"
            sep = "&" if "?" in url else "?"
            busted = f"{url}{sep}cb={int(time.time() * 1000)}"
            self._cache[key] = self.session.get(
                busted, allow_redirects=allow_redirects, timeout=TIMEOUT
            )
        return self._cache[key]

    def soup(self, path: str) -> BeautifulSoup:
        return BeautifulSoup(self.get(path).text, "html.parser")


def is_hidden_or_allowed_after_footer(el: Tag) -> bool:
    """True if a post-footer element is legitimately there: hidden dialog/portal
    markup, templates, scripts, or the cookie banner."""
    if el.name in ("script", "style", "template", "link", "noscript"):
        return True
    if el.name == "dialog" and not el.has_attr("open"):
        return True
    if el.has_attr("hidden") or el.get("aria-hidden") == "true":
        return True
    style = (el.get("style") or "").replace(" ", "").lower()
    if "display:none" in style or "visibility:hidden" in style:
        return True
    idcls = " ".join([el.get("id") or ""] + (el.get("class") or [])).lower()
    if any(h in idcls for h in COOKIE_HINTS):
        return True
    # Empty structural wrappers (e.g. portal mount points) are fine.
    return not el.get_text(strip=True) and not el.find(("img", "video", "iframe"))


def blue_dominant_hexes(css_text: str) -> list[str]:
    """Colors where the blue channel strictly dominates red AND green.

    RGB channel comparison, not a pattern list — matches the approach already
    proven in the repo's brand-law tooling.
    """
    found: list[str] = []
    for m in re.finditer(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", css_text):
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        if b > r and b > g:
            found.append("#" + h)
    for m in re.finditer(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", css_text):
        r, g, b = (int(x) for x in m.groups())
        if b > r and b > g:
            found.append(f"rgb({r},{g},{b})")
    return found


def check_shell(a: Audit) -> None:
    print("\n== shell ==")
    for path in AUDIT_PAGES:
        if path in ("/size-guide/",):  # content page; shell asserted like the rest
            pass
        soup = a.soup(path)
        html = a.get(path).text

        primary_navs = [
            n
            for n in soup.find_all("nav")
            if "primary" in (n.get("aria-label") or "").lower()
            or "primary" in " ".join(n.get("class") or []).lower()
        ]
        a.check(
            len(primary_navs) == 1,
            f"{path} exactly one primary nav landmark",
            f"found {len(primary_navs)}",
        )

        skip_links = [
            l
            for l in soup.find_all("a", href=True)
            if l["href"].startswith("#")
            and re.match(r"skip to ", l.get_text(strip=True), re.IGNORECASE)
        ]
        a.check(
            len(skip_links) == 1,
            f"{path} exactly one skip link",
            f"found {len(skip_links)}: {[l.get_text(strip=True) for l in skip_links]}",
        )

        for marker in LEGACY_MARKERS:
            a.check(marker not in html, f"{path} no legacy marker {marker!r}")

        headers = soup.find_all("header")
        footers = soup.find_all("footer")
        a.check(len(headers) == 1, f"{path} exactly one <header>", f"found {len(headers)}")
        a.check(len(footers) == 1, f"{path} exactly one <footer>", f"found {len(footers)}")


def check_routes(a: Audit) -> None:
    print("\n== routes ==")
    if not REDIRECTS_CSV.exists():
        a.fail("redirects.csv present", f"missing at {REDIRECTS_CSV}")
        return
    with open(REDIRECTS_CSV, newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in rows:
        src, expected_to = row["from"], row["to"]
        r = a.get(src, allow_redirects=False)
        loc = r.headers.get("location", "")
        loc_path = urlparse(loc).path or loc
        single_hop = r.status_code == 301 and loc_path.rstrip("/") == expected_to.rstrip("/")
        a.check(
            single_hop,
            f"{src} → {expected_to} single-hop 301",
            f"got {r.status_code} → {loc or '(none)'}",
        )
    for path in CANONICAL_PAGES:
        r = a.get(path)
        # 5000 bytes is a PHP-fatal / white-screen tripwire, not a content-richness
        # gate — lean utility pages (size-guide, contact) can be valid 200s well
        # under a hero-page byte count, so this must stay low enough to never
        # false-positive on legitimate lightweight pages.
        a.check(
            r.status_code == 200 and len(r.text) > 5000,
            f"{path} 200 with substantial body",
            f"status={r.status_code} bytes={len(r.text)}",
        )
    # No internal links to legacy routes anywhere.
    for path in AUDIT_PAGES:
        html = a.get(path).text
        offenders = [
            route for route in LEGACY_ROUTES if re.search(rf'href="[^"]*{re.escape(route)}"', html)
        ]
        a.check(not offenders, f"{path} zero internal legacy-route links", str(offenders))


def check_dom(a: Audit) -> None:
    print("\n== dom ==")
    for path in AUDIT_PAGES:
        soup = a.soup(path)
        footer = soup.find("footer")
        if footer is None:
            a.fail(f"{path} has a <footer>")
            continue
        offenders = []
        offender_tags: list[Tag] = []
        for sib in footer.find_all_next():
            if sib.find_parent("footer") is not None:
                continue
            if any(
                p is not None and is_hidden_or_allowed_after_footer(p)
                for p in [sib, *sib.parents]
                if isinstance(p, Tag)
            ):
                continue
            if isinstance(sib, Tag) and not is_hidden_or_allowed_after_footer(sib):
                # One violation, one report: descendants of an already-recorded
                # offender would only restate it and crowd the [:5] window.
                if any(p is o for p in sib.parents for o in offender_tags):
                    continue
                offender_tags.append(sib)
                text = sib.get_text(strip=True)[:60]
                if (
                    text
                    or sib.find(("img", "video", "iframe"))
                    or sib.name in ("img", "video", "iframe")
                ):
                    offenders.append(f"<{sib.name}> {text!r}")
        a.check(not offenders, f"{path} nothing visible after </footer>", "; ".join(offenders[:5]))


def piece_counts(soup: BeautifulSoup) -> dict[str, int]:
    """Read data-driven piece counts from markup contract:
    elements carrying data-collection + data-piece-count."""
    counts: dict[str, int] = {}
    for el in soup.select("[data-collection][data-piece-count]"):
        raw = str(el["data-piece-count"]).strip()
        # Malformed markup must fail the data check, not crash the run.
        if raw.isdigit():
            counts[str(el["data-collection"])] = int(raw)
    return counts


def check_data(a: Audit) -> None:
    print("\n== data ==")
    home_counts = piece_counts(a.soup("/"))
    index_counts = piece_counts(a.soup("/collections/"))
    a.check(
        bool(home_counts),
        "homepage exposes data-driven piece counts",
        "no [data-collection][data-piece-count] elements",
    )
    a.check(
        bool(index_counts),
        "collections index exposes data-driven piece counts",
        "no [data-collection][data-piece-count] elements",
    )
    expected = {"black-rose", "love-hurts", "signature", "kids-capsule"}
    a.check(
        set(index_counts) >= expected,
        "collections index lists all four collections",
        f"missing {expected - set(index_counts)}",
    )
    for coll in sorted(set(home_counts) & set(index_counts)):
        a.check(
            home_counts[coll] == index_counts[coll],
            f"{coll} count agrees home vs index",
            f"home={home_counts[coll]} index={index_counts[coll]}",
        )
    # No hardcoded 'NN Pieces' outside the data-driven elements on home.
    soup = a.soup("/")
    for el in soup.select("[data-collection][data-piece-count]"):
        el.decompose()
    stray = re.findall(r"\b\d+\s+[Pp]ieces\b", soup.get_text(" "))
    # Edition-size copy ('250 pieces. Once sold out…') is brand canon, not a count.
    stray = [s for s in stray if not s.startswith("250")]
    a.check(not stray, "no stray hardcoded piece counts on homepage", str(stray[:5]))


def check_commerce(a: Audit) -> None:
    print("\n== commerce ==")
    for path in AUDIT_PAGES:
        html = a.get(path).text
        a.check(
            not re.search(r'href="[^"]*add-to-cart=', html),
            f"{path} no GET add-to-cart hrefs",
        )
        a.check(
            not re.search(r'src="[^"]*placeholder[^"]*\.(jpg|png|webp|gif)', html),
            f"{path} no placeholder images",
        )
        a.check(
            not re.search(r"countdown|data-timer|\b\d{2}:\d{2}:\d{2}:\d{2}\b", html, re.IGNORECASE),
            f"{path} no countdown markup",
        )
    soup = a.soup("/")
    og = soup.find("meta", property="og:image")
    a.check(
        og is not None and re.search(r"\.(webp|jpg|jpeg|png)(\?|$)", og.get("content", "")),
        "og:image is a static image URL",
        (og or {}).get("content", "missing"),
    )
    if og is not None and og.get("content"):
        r = a.session.head(og["content"], timeout=TIMEOUT, allow_redirects=True)
        a.check(
            r.status_code == 200 and r.headers.get("content-type", "").startswith("image/"),
            "og:image returns 200 with image MIME",
            f"status={r.status_code} type={r.headers.get('content-type')}",
        )


def check_brand(a: Audit) -> None:
    print("\n== brand ==")
    theme_css_urls: set[str] = set()
    for path in AUDIT_PAGES:
        soup = a.soup(path)
        html = a.get(path).text
        for link in soup.find_all("link", rel="stylesheet", href=True):
            href = urljoin(BASE_URL, link["href"])
            if "/themes/skyyrose-flagship/" in href:
                theme_css_urls.add(href)
        # WP core emits global-styles / block-library preset blocks the theme
        # cannot author (theme.json already disables every disableable default:
        # palette, gradients, duotone). Brand law is asserted on theme-owned
        # CSS: skip the core-emitted style blocks, scan everything else.
        core_style_ids = (
            "global-styles-inline-css",
            "wp-block-library-inline-css",
            "classic-theme-styles-inline-css",
            "core-block-supports-inline-css",
            "admin-bar-inline-css",
        )
        # Plugin-owned inline styles (Jetpack likes/sharing/search etc.) are
        # not the theme's palette to police — brand law targets theme output.
        plugin_style_prefixes = ("jetpack", "sharedaddy", "sharing")
        inline_css = " ".join(
            s.get_text()
            for s in soup.find_all("style")
            if (s.get("id") or "") not in core_style_ids
            and not (s.get("id") or "").startswith(plugin_style_prefixes)
        )
        inline_attrs = " ".join(m.group(1) for m in re.finditer(r'style="([^"]*)"', html))
        blues = blue_dominant_hexes(inline_css + " " + inline_attrs)
        a.check(not blues, f"{path} no blue-dominant colors inline", str(sorted(set(blues))[:8]))
        text = BeautifulSoup(html, "html.parser").get_text(" ")
        gendered = [p for p in GENDERED_PATTERNS if re.search(p, text, re.IGNORECASE)]
        a.check(not gendered, f"{path} no gendered merch framing", str(gendered))
    for href in sorted(theme_css_urls):
        css = a.get(href).text
        blues = blue_dominant_hexes(css)
        name = urlparse(href).path.rsplit("/", 1)[-1]
        a.check(not blues, f"theme css {name} no blue-dominant colors", str(sorted(set(blues))[:8]))


def check_meta(a: Audit) -> None:
    print("\n== meta ==")
    for path in AUDIT_PAGES:
        soup = a.soup(path)
        canonicals = soup.find_all("link", rel="canonical")
        a.check(len(canonicals) == 1, f"{path} exactly one canonical", f"found {len(canonicals)}")
        if len(canonicals) == 1:
            target = urlparse(canonicals[0].get("href", "")).path or "/"
            a.check(
                all(not target.startswith(lr.rstrip("/")) or target == "/" for lr in LEGACY_ROUTES),
                f"{path} canonical not a legacy route",
                target,
            )


CHECKS = {
    "shell": check_shell,
    "routes": check_routes,
    "dom": check_dom,
    "data": check_data,
    "commerce": check_commerce,
    "brand": check_brand,
    "meta": check_meta,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="comma-separated subset of checks: " + ",".join(CHECKS))
    args = parser.parse_args()
    selected = list(CHECKS) if not args.only else [s.strip() for s in args.only.split(",")]
    unknown = [s for s in selected if s not in CHECKS]
    if unknown:
        print(f"unknown checks: {unknown}", file=sys.stderr)
        return 2

    print(f"structural audit → {BASE_URL}")
    audit = Audit()
    for name in selected:
        CHECKS[name](audit)

    print(f"\n{len(audit.passes)} passed, {len(audit.failures)} failed")
    if audit.failures:
        print("\nFailures:")
        for f in audit.failures:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
