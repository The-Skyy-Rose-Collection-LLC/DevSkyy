#!/usr/bin/env python3
"""build-site-guide.py — generate data/site-guide.json for the Skyy mascot guide brain.

Deterministic, data-driven navigation data for the Tier-1 (no-LLM) mascot guide
engine. Every URL is parsed out of the theme's own PHP source — never hand-typed
here — so the "no hardcoded nav" invariant holds: rename a page slug in
`inc/theme-activation-setup.php` or `inc/menu-setup.php` and regenerating this
file picks it up automatically.

Sources parsed:
  - inc/menu-setup.php               skyyrose_get_menu_definitions() — nav title/url pairs
  - inc/theme-activation-setup.php   skyyrose_get_required_pages() + the WooCommerce
                                      $wc_pages array — slug => title page registry
  - footer.php                       hardcoded legal/help <li><a href="home_url('/x/')">
                                      links (FAQ, shipping-returns, privacy-policy, ...)
  - data/skyyrose-catalog.csv        distinct `collection` values (collection => URL)

Fails loud (non-zero exit) if any source yields suspiciously little — a silent
empty/partial site-guide.json would quietly break the mascot's "where is X"
answers without anyone noticing.

Usage:
    python3 scripts/build-site-guide.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
THEME_DIR = REPO_ROOT / "wordpress-theme" / "skyyrose-flagship"

# Title always immediately precedes url as adjacent keys within a menu item
# (parent or child) in inc/menu-setup.php, so a single non-greedy DOTALL
# regex correctly pairs each title with its own url regardless of nesting.
_TITLE_URL_RE = re.compile(
    r"'title'\s*=>\s*__\(\s*'([^']*)'\s*,\s*'skyyrose'\s*\).*?'url'\s*=>\s*'([^']*)'",
    re.DOTALL,
)

# Matches both skyyrose_get_required_pages() entries and the WooCommerce
# $wc_pages array in inc/theme-activation-setup.php — both share the exact
# shape `'slug' => array( 'title' => __( 'Title', 'skyyrose' ), ...)`.
_PAGE_REGISTRY_RE = re.compile(
    r"'([a-z0-9-]+)'\s*=>\s*array\(\s*'title'\s*=>\s*__\(\s*'([^']*)'\s*,\s*'skyyrose'\s*\)",
)

# footer.php: <li><a href="<?php echo esc_url( home_url( '/faq/' ) ); ?>">
#   <?php esc_html_e( 'FAQ', 'skyyrose' ); ?></a></li>
_FOOTER_LINK_RE = re.compile(
    r"home_url\(\s*'([^']+)'\s*\)\s*\);\s*\?>\"><\?php\s*esc_html_e\(\s*'([^']*)'",
)


def slugify(value: str) -> str:
    """Mirror WordPress sanitize_title() closely enough for internal slugs."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def title_case_slug(slug: str) -> str:
    """'kids-capsule' -> 'Kids Capsule'."""
    return " ".join(word.capitalize() for word in slug.split("-") if word)


def extract_menu_items(php_source: str) -> list[dict[str, str]]:
    """Flat list of {title, url} pairs from skyyrose_get_menu_definitions().

    Anchor-only urls (e.g. '/contact/#faq') are excluded — they point at a
    section of an existing page, not a distinct destination.
    """
    items = []
    for title, url in _TITLE_URL_RE.findall(php_source):
        if title and url and "#" not in url:
            items.append({"title": title, "url": url})
    return items


def extract_page_registry(php_source: str) -> dict[str, str]:
    """slug -> title for every `'slug' => array('title' => __('...', 'skyyrose')` entry.

    Covers both skyyrose_get_required_pages() and the WooCommerce $wc_pages
    array in inc/theme-activation-setup.php — they share the same shape.
    """
    return dict(_PAGE_REGISTRY_RE.findall(php_source))


def extract_footer_legal_links(php_source: str) -> dict[str, str]:
    """slug -> title for footer.php's hardcoded home_url() <li> links."""
    out: dict[str, str] = {}
    for url, title in _FOOTER_LINK_RE.findall(php_source):
        if "#" in url:
            continue
        slug = url.strip("/")
        if slug and title:
            out[slug] = title
    return out


def extract_collections(csv_path: Path) -> list[str]:
    """Sorted distinct `collection` column values from the catalog CSV."""
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        collections = {
            row["collection"].strip() for row in reader if row.get("collection", "").strip()
        }
    return sorted(collections)


def build_pages(
    menu_items: list[dict[str, str]],
    page_registry: dict[str, str],
    legal_links: dict[str, str],
    collections: list[str],
) -> dict[str, dict[str, Any]]:
    """Merge every source into slug -> {title, url, tips}.

    First writer wins per slug; sources are merged in priority order (page
    registry > footer legal links > catalog collections > nav menu) so the
    most authoritative title/url for a given slug is kept.
    """
    pages: dict[str, dict[str, Any]] = {}

    def add(slug: str, title: str, url: str) -> None:
        slug = slug.strip("-")
        if not slug or slug in pages:
            return
        pages[slug] = {"title": title, "url": url, "tips": []}

    for slug, title in page_registry.items():
        add(slug, title, "/" + slug + "/")

    for slug, title in legal_links.items():
        add(slug, title, "/" + slug + "/")

    for collection in collections:
        slug = "collection-" + slugify(collection)
        add(slug, title_case_slug(collection) + " Collection", "/" + slug + "/")

    for item in menu_items:
        slug = slugify(item["url"].strip("/")) or "home"
        add(slug, item["title"], item["url"])

    # The 'home' page is the static front page — WordPress serves it at the
    # site root, never at the literal '/home/' permalink its slug implies.
    if "home" in pages:
        pages["home"]["url"] = "/"

    return pages


def build_intents(pages: dict[str, dict[str, Any]], collections: list[str]) -> list[dict[str, Any]]:
    """Seed the scripted intent list. An intent is only emitted when its
    target page actually exists in `pages` — never point at a guessed URL.
    """
    intents: list[dict[str, Any]] = []

    def add_intent(intent_id: str, patterns: list[str], answer: str, page_slug: str) -> None:
        if page_slug not in pages:
            return
        intents.append(
            {
                "id": intent_id,
                "patterns": patterns,
                "answer": answer,
                "link": pages[page_slug]["url"],
            }
        )

    for collection in collections:
        slug = "collection-" + slugify(collection)
        label = pages.get(slug, {}).get("title", title_case_slug(collection))
        add_intent(
            "where-" + slugify(collection),
            [slugify(collection).replace("-", " "), collection.lower()],
            "Head to " + label + " →",
            slug,
        )

    add_intent(
        "where-shop",
        ["shop", "buy", "browse", "products", "store", "everything"],
        "Everything we've got, right here →",
        "shop",
    )
    add_intent(
        "where-preorder",
        ["pre-order", "preorder", "pre order", "reserve", "drop"],
        "Pre-ordering means we make each piece for you — no overstock, no waste →",
        "pre-order",
    )
    add_intent(
        "sizing",
        ["size", "sizing", "fit", "runs small", "runs big", "measurements"],
        "Fit notes live on every product page — general sizing lives in the FAQ →",
        "faq",
    )
    add_intent(
        "shipping",
        ["shipping", "returns", "exchange", "refund", "delivery", "ship"],
        "Shipping rates, delivery times, and our return policy →",
        "shipping-returns",
    )
    add_intent(
        "order-tracking",
        ["track", "order status", "where is my order", "my order", "tracking"],
        "Check your order status in your account →",
        "my-account",
    )

    return intents


def generate(theme_dir: Path = THEME_DIR) -> dict[str, Any]:
    """Parse every source and return the {pages, intents} site-guide dict.

    Raises SystemExit (not a soft error) if any source parses to
    suspiciously little — a regex that silently stops matching after an
    unrelated PHP reformat must fail the build, not ship an empty guide.
    """
    menu_source = (theme_dir / "inc" / "menu-setup.php").read_text(encoding="utf-8")
    activation_source = (theme_dir / "inc" / "theme-activation-setup.php").read_text(
        encoding="utf-8"
    )
    footer_source = (theme_dir / "footer.php").read_text(encoding="utf-8")
    catalog_path = theme_dir / "data" / "skyyrose-catalog.csv"

    menu_items = extract_menu_items(menu_source)
    page_registry = extract_page_registry(activation_source)
    legal_links = extract_footer_legal_links(footer_source)
    collections = extract_collections(catalog_path)

    if not collections:
        raise SystemExit("build-site-guide: 0 collections found in catalog CSV — aborting")
    if len(page_registry) < 4:
        raise SystemExit(
            f"build-site-guide: only {len(page_registry)} registered pages parsed "
            "from inc/theme-activation-setup.php — aborting (regex drift?)"
        )
    if not legal_links:
        raise SystemExit(
            "build-site-guide: 0 footer legal links parsed from footer.php — aborting "
            "(regex drift?)"
        )

    pages = build_pages(menu_items, page_registry, legal_links, collections)

    for required_slug in ("faq", "shipping-returns", "my-account", "pre-order", "shop"):
        if required_slug not in pages:
            raise SystemExit(
                f"build-site-guide: required page '{required_slug}' missing from parsed pages"
            )

    intents = build_intents(pages, collections)

    return {"pages": pages, "intents": intents}


def main() -> int:
    output_path = THEME_DIR / "data" / "site-guide.json"
    data = generate()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {output_path.relative_to(REPO_ROOT)} — "
        f"{len(data['pages'])} pages, {len(data['intents'])} intents"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
