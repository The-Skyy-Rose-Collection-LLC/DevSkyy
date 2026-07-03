#!/usr/bin/env python3
"""wc_reconcile.py — read-only reconcile of the live WooCommerce store vs the catalog CSV.

Fetches every live product via GET /wp-json/wc/v3/products (BasicAuth, WOOCOMMERCE_KEY/
SECRET from .env.wordpress) and compares it against the canonical
wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv on:
  - SKU set (both directions — live-only and CSV-only)
  - price
  - name
  - publish status (CSV `published` vs WC `status`)
  - preorder status (CSV `is_preorder` vs WC post-meta `_is_preorder` — the key the theme's
    own preorder logic reads, per inc/woocommerce-preorder.php / inc/immersive-ajax.php)

Read-only: every request is a GET. Never creates, updates, or deletes anything. Caches
nothing across runs — every invocation hits the live API fresh.

Standalone:
    python scripts/wc_reconcile.py             # live reconcile, human-readable report
    python scripts/wc_reconcile.py --json       # machine-readable report

Importable (network-free):
    from scripts.wc_reconcile import diff_products, load_csv_rows
"""

from __future__ import annotations

import argparse
import base64
import csv
import html
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_CSV = REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "skyyrose-catalog.csv"
ENV_FILE = REPO_ROOT / ".env.wordpress"
SITE = "https://skyyrose.co"
WC_API = f"{SITE}/wp-json/wc/v3/products"
_MAX_PAGES = 20  # generous headroom — catalog is ~33 SKUs at per_page=100


class CredentialsMissing(RuntimeError):
    """WOOCOMMERCE_KEY/WOOCOMMERCE_SECRET are not available."""


@dataclass(frozen=True)
class ProductDrift:
    sku: str
    field: str
    csv_value: str
    live_value: str


@dataclass(frozen=True)
class ReconcileResult:
    csv_only: tuple[str, ...]  # SKUs in the CSV but not live
    live_only: tuple[str, ...]  # SKUs live but not in the CSV
    field_drift: tuple[ProductDrift, ...]
    csv_count: int
    live_count: int

    @property
    def clean(self) -> bool:
        return not (self.csv_only or self.live_only or self.field_drift)


# ---------------------------------------------------------------------------
# CSV side (network-free)
# ---------------------------------------------------------------------------


def load_csv_rows(csv_path: Path = CATALOG_CSV) -> dict[str, dict[str, str]]:
    """Load the canonical catalog CSV, keyed by SKU."""
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return {row["sku"].strip(): row for row in csv.DictReader(fh) if row.get("sku")}


# ---------------------------------------------------------------------------
# Live side (network) — every call is a GET, no writes
# ---------------------------------------------------------------------------


def _credentials() -> tuple[str, str]:
    load_dotenv(ENV_FILE)
    key = os.getenv("WOOCOMMERCE_KEY")
    secret = os.getenv("WOOCOMMERCE_SECRET")
    if not key or not secret:
        raise CredentialsMissing("WOOCOMMERCE_KEY/WOOCOMMERCE_SECRET not set")
    return key, secret


def fetch_live_products(*, timeout: float = 30.0) -> dict[str, dict[str, Any]]:
    """GET every live WC product, paginated, keyed by SKU. Read-only."""
    key, secret = _credentials()
    auth = base64.b64encode(f"{key}:{secret}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "User-Agent": "sot-doctor-wc-reconcile/1.0"}
    out: dict[str, dict[str, Any]] = {}
    for page in range(1, _MAX_PAGES + 1):
        resp = httpx.get(
            WC_API, params={"per_page": 100, "page": page}, headers=headers, timeout=timeout
        )
        # No special-case for 429: raise_for_status() surfaces it as an httpx.HTTPError,
        # which main()/sot_status.py already report as BROKEN. Silently breaking here
        # used to turn a rate-limit into an empty live-products dict — indistinguishable
        # from "the live store has zero products" — which diff_products() then reported
        # as every CSV SKU being live-only-missing. A transient failure must fail loudly,
        # not masquerade as catastrophic drift.
        resp.raise_for_status()
        items = resp.json()
        if not items:
            break
        for item in items:
            sku = (item.get("sku") or "").strip()
            if sku:
                out[sku] = item
        if len(items) < 100:
            break
    return out


# ---------------------------------------------------------------------------
# Pure diff — no network, fixture-testable
# ---------------------------------------------------------------------------


def _norm_price(value: str) -> str:
    """Normalize a price string for comparison ('120' == '120.00')."""
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return (value or "").strip()


def _csv_bool(value: str) -> bool:
    return (value or "").strip() in ("1", "true", "yes", "on")


def _live_meta(live: dict[str, Any], key: str) -> str:
    for entry in live.get("meta_data", []) or []:
        if entry.get("key") == key:
            return str(entry.get("value", ""))
    return ""


def diff_products(
    csv_rows: dict[str, dict[str, str]], live_products: dict[str, dict[str, Any]]
) -> ReconcileResult:
    """Pure diff — no network. Both inputs keyed by SKU."""
    csv_skus = set(csv_rows)
    live_skus = set(live_products)

    drift: list[ProductDrift] = []
    for sku in sorted(csv_skus & live_skus):
        csv_row, live = csv_rows[sku], live_products[sku]

        csv_price = _norm_price(csv_row.get("price", ""))
        live_price = _norm_price(live.get("price") or live.get("regular_price") or "")
        if csv_price and live_price and csv_price != live_price:
            drift.append(ProductDrift(sku, "price", csv_price, live_price))

        csv_name = csv_row.get("name", "").strip()
        live_name = (live.get("name") or "").strip()
        # WooCommerce stores/returns product titles HTML-entity-encoded (e.g. "&" as
        # "&amp;"); unescape both sides before comparing so that's never flagged as drift.
        if csv_name and live_name and html.unescape(csv_name) != html.unescape(live_name):
            drift.append(ProductDrift(sku, "name", csv_name, live_name))

        csv_published = _csv_bool(csv_row.get("published", ""))
        live_published = (live.get("status") or "").strip() == "publish"
        if csv_published != live_published:
            drift.append(
                ProductDrift(
                    sku,
                    "published",
                    "publish" if csv_published else "not-publish",
                    live.get("status") or "(none)",
                )
            )

        csv_preorder = _csv_bool(csv_row.get("is_preorder", ""))
        live_preorder = _live_meta(live, "_is_preorder") == "1"
        if csv_preorder != live_preorder:
            drift.append(ProductDrift(sku, "is_preorder", str(csv_preorder), str(live_preorder)))

    return ReconcileResult(
        csv_only=tuple(sorted(csv_skus - live_skus)),
        live_only=tuple(sorted(live_skus - csv_skus)),
        field_drift=tuple(drift),
        csv_count=len(csv_skus),
        live_count=len(live_skus),
    )


def reconcile() -> ReconcileResult:
    """Full live reconcile: load CSV, fetch live, diff. Raises CredentialsMissing
    if WOOCOMMERCE_KEY/SECRET are absent — callers treat that as LIVE-SKIPPED."""
    csv_rows = load_csv_rows()
    live_products = fetch_live_products()
    return diff_products(csv_rows, live_products)


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def _render_text(result: ReconcileResult) -> str:
    lines = [
        f"CSV SKUs: {result.csv_count}   LIVE SKUs: {result.live_count}",
    ]
    if result.clean:
        lines.append("No drift — live store matches the catalog CSV.")
        return "\n".join(lines)
    if result.csv_only:
        lines.append(f"\nCSV-only ({len(result.csv_only)}) — in CSV, missing live:")
        lines.extend(f"  {sku}" for sku in result.csv_only)
    if result.live_only:
        lines.append(f"\nLIVE-only ({len(result.live_only)}) — live, missing from CSV:")
        lines.extend(f"  {sku}" for sku in result.live_only)
    if result.field_drift:
        lines.append(f"\nField drift ({len(result.field_drift)}):")
        lines.extend(
            f"  {d.sku:12s} {d.field:12s} csv={d.csv_value!r} live={d.live_value!r}"
            for d in result.field_drift
        )
    return "\n".join(lines)


def _to_json(result: ReconcileResult) -> dict[str, Any]:
    return {
        "clean": result.clean,
        "csv_count": result.csv_count,
        "live_count": result.live_count,
        "csv_only": list(result.csv_only),
        "live_only": list(result.live_only),
        "field_drift": [
            {"sku": d.sku, "field": d.field, "csv_value": d.csv_value, "live_value": d.live_value}
            for d in result.field_drift
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_output", action="store_true")
    args = parser.parse_args(argv)

    try:
        result = reconcile()
    except CredentialsMissing as exc:
        if args.json_output:
            print(json.dumps({"skipped": True, "reason": str(exc)}))
        else:
            print(f"LIVE-SKIPPED: {exc}", file=sys.stderr)
        return 0
    except httpx.HTTPError as exc:
        if args.json_output:
            print(json.dumps({"error": True, "reason": str(exc)}))
        else:
            print(f"BROKEN: live fetch failed — {exc}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps(_to_json(result), indent=2))
    else:
        print(_render_text(result))
    return 0 if result.clean else 1


if __name__ == "__main__":
    sys.exit(main())
