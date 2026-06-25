#!/usr/bin/env python3
"""Trash WC products that exist on skyyrose.co but not in canonical CSV.

Reads canonical SKUs from wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv,
fetches live products via public Store API (no auth, no rate-limit on read),
DELETEs extras via authenticated WC v3 (requires WOOCOMMERCE_KEY/SECRET in env).

Default mode is dry-run. Pass --commit to actually trash.
Default delete is non-force (recoverable from WC trash). Pass --force for hard delete.
"""

from __future__ import annotations

import argparse
import base64
import csv
import os
import sys
import time
from pathlib import Path

import httpx

CATALOG = (
    Path(__file__).resolve().parent.parent
    / "wordpress-theme"
    / "skyyrose-flagship"
    / "data"
    / "skyyrose-catalog.csv"
)
SITE = "https://skyyrose.co"
STORE_API = f"{SITE}/wp-json/wc/store/v1/products"
WC_API = f"{SITE}/wp-json/wc/v3/products"


def load_csv_skus() -> set[str]:
    with CATALOG.open() as f:
        return {row["sku"].strip() for row in csv.DictReader(f) if row.get("sku")}


def fetch_live() -> list[dict]:
    out: list[dict] = []
    for page in range(1, 10):
        r = httpx.get(
            STORE_API,
            params={"per_page": 100, "page": page},
            headers={"User-Agent": "wc-trash-extras/1.0"},
            timeout=30,
            follow_redirects=True,
        )
        if r.status_code == 429:
            print(f"  page {page} 429 -> stopping pagination (have {len(out)})")
            break
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        out.extend(items)
        time.sleep(3)
    return out


def trash(pid: int, ck: str, cs: str, force: bool) -> tuple[int, str]:
    auth = base64.b64encode(f"{ck}:{cs}".encode()).decode()
    hdr = {"Authorization": f"Basic {auth}", "User-Agent": "wc-trash-extras/1.0"}
    for attempt in range(4):
        r = httpx.delete(
            f"{WC_API}/{pid}",
            params={"force": "true" if force else "false"},
            headers=hdr,
            timeout=30,
        )
        if r.status_code == 429:
            wait = int(r.headers.get("retry-after", 30))
            print(f"    429 -> sleep {wait}s (attempt {attempt + 1})")
            time.sleep(wait)
            continue
        break
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    return r.status_code, body.get("status") or body.get("message") or r.text[:120]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--commit", action="store_true", help="actually delete (default: dry-run)")
    ap.add_argument(
        "--force", action="store_true", help="hard delete (default: trash, recoverable)"
    )
    ap.add_argument("--only", nargs="*", help="restrict to specific SKUs")
    args = ap.parse_args()

    csv_skus = load_csv_skus()
    print(f"CSV SKUs: {len(csv_skus)}")

    live = fetch_live()
    live_by_sku = {p["sku"]: p for p in live if p.get("sku")}
    print(f"LIVE products: {len(live)} ({len(live_by_sku)} with SKU)")

    extras = sorted(set(live_by_sku) - csv_skus)
    if args.only:
        extras = [s for s in extras if s in set(args.only)]

    if not extras:
        print("No extras to trash.")
        return 0

    print(f"\nEXTRAS ({len(extras)}):")
    for sku in extras:
        p = live_by_sku[sku]
        print(f"  {sku:20s} #{p['id']:6d}  {p['name']}")

    if not args.commit:
        print("\n[DRY-RUN] pass --commit to delete")
        return 0

    ck = os.getenv("WOOCOMMERCE_KEY")
    cs = os.getenv("WOOCOMMERCE_SECRET")
    if not ck or not cs:
        print("ERROR: WOOCOMMERCE_KEY/WOOCOMMERCE_SECRET not in env", file=sys.stderr)
        return 2

    mode = "FORCE-DELETE" if args.force else "TRASH"
    print(f"\n[{mode}] proceeding on {len(extras)} products...")
    failures = 0
    for sku in extras:
        p = live_by_sku[sku]
        status, msg = trash(p["id"], ck, cs, args.force)
        ok = status in (200, 201)
        marker = "OK" if ok else "FAIL"
        print(f"  [{marker}] {sku} #{p['id']}  HTTP {status}  {msg}")
        if not ok:
            failures += 1
        time.sleep(8)

    print(f"\nDone. failures={failures}/{len(extras)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
