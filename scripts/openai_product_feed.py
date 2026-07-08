#!/usr/bin/env python3
"""Generate the OpenAI ChatGPT product feed from live WooCommerce inventory.

Maps skyyrose.co's live WooCommerce catalog to the OpenAI Commerce "Stable"
file-upload product feed schema (docs/integrations/openai-product-feed-spec.md),
validates every mapped item against the spec's required fields, and writes a
csv.gz feed file (see scripts/openai_feed/writer.py for the format rationale).

Read-only against WooCommerce in both modes (GET requests only) — safe to run
without STOP-AND-SHOW confirmation.

Usage:
    python scripts/openai_product_feed.py                 # dry-run (default): fetch, validate, report
    python scripts/openai_product_feed.py --dry-run        # same, explicit
    python scripts/openai_product_feed.py --write           # also writes feeds/openai-product-feed.csv.gz
                                                              # and feeds/openai-feed-exclusions.json
    python scripts/openai_product_feed.py --write --out-dir /tmp/feeds
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.openai_feed.catalog import load_catalog  # noqa: E402
from scripts.openai_feed.constants import DEFAULT_CONSTANTS  # noqa: E402
from scripts.openai_feed.mapping import map_product_to_feed_items  # noqa: E402
from scripts.openai_feed.validation import partition_items  # noqa: E402
from scripts.openai_feed.wc_client import (  # noqa: E402
    WooCommerceCredentialsError,
    WooCommerceRequestError,
    fetch_catalog,
)
from scripts.openai_feed.writer import (  # noqa: E402
    EXCLUSIONS_FILENAME,
    FEED_FILENAME,
    write_csv_feed,
    write_exclusions,
)

DEFAULT_OUT_DIR = REPO_ROOT / "feeds"


def build_feed_items(
    products: list[dict[str, Any]], catalog: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Map every live, catalog-registered WC product to feed items.

    Filters to `status == "publish"` and SKUs present in the canonical
    catalog CSV — WC products outside the CSV (drafts, orphaned test
    products) are catalog drift, not feed candidates. See the compliance
    report's "Live-store vs catalog-CSV drift" section for what was found.
    """
    items: list[dict[str, Any]] = []
    for product in products:
        if product.get("status") != "publish":
            continue
        sku = product.get("sku")
        if not sku or sku not in catalog:
            continue
        catalog_row = catalog.get(sku)
        items.extend(map_product_to_feed_items(product, catalog_row, DEFAULT_CONSTANTS))
    return items


def run(*, write: bool, out_dir: Path) -> int:
    try:
        products = fetch_catalog()
    except WooCommerceCredentialsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except WooCommerceRequestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    catalog = load_catalog()
    feed_items = build_feed_items(products, catalog)
    valid_items, excluded_items = partition_items(feed_items)

    print(f"Fetched {len(products)} WooCommerce products.")
    print(f"Mapped {len(feed_items)} feed items from published, catalog-registered SKUs.")
    print(f"  Valid (feed-ready):  {len(valid_items)}")
    print(f"  Excluded (invalid):  {len(excluded_items)}")

    if excluded_items:
        print("\nExcluded items:", file=sys.stderr)
        for entry in excluded_items:
            print(f"  - {entry['item_id']} ({entry['title']}):", file=sys.stderr)
            for error in entry["errors"]:
                print(f"      {error}", file=sys.stderr)

    if not write:
        print("\nDry-run mode (default) — no files written. Pass --write to emit the feed.")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    feed_path = out_dir / FEED_FILENAME
    exclusions_path = out_dir / EXCLUSIONS_FILENAME
    write_csv_feed(valid_items, feed_path)
    write_exclusions(excluded_items, exclusions_path)
    print(f"\nWrote {len(valid_items)} items to {feed_path}")
    print(f"Wrote exclusions report to {exclusions_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch, validate, and report only. No files written. (Default.)",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="Write feeds/openai-product-feed.csv.gz and feeds/openai-feed-exclusions.json.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Output directory for --write mode (default: {DEFAULT_OUT_DIR}).",
    )
    args = parser.parse_args()

    write = bool(args.write)
    return run(write=write, out_dir=args.out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
