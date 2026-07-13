#!/usr/bin/env python3
"""Generate CLIP image embeddings for the canonical catalog SKUs.

Builds ``wordpress-theme/skyyrose-flagship/data/product-embeddings.json`` — the
input ``scripts/catalog_ml_audit.py`` loads. Each SKU's FRONT product image is
resolved via the canonical SOT imagery manifest (``data/sot-images.json`` —
NEVER the raw CSV image columns, per ``feedback_sot_imagery_everywhere.md``),
then encoded with the local CLIP vision model (``openai/clip-vit-base-patch32``,
512-d, L2-normalized).

Output schema (matches what ``catalog_ml_audit.py`` expects — dict keyed by
SKU, not a list):

    {
      "model": "openai/clip-vit-base-patch32",
      "dim": 512,
      "generated": "<ISO-8601 UTC timestamp>",
      "products": {
        "<sku>": {
          "name": "<catalog name>",
          "collection": "<catalog collection slug>",
          "embedding": [512 floats]
        },
        ...
      }
    }

Usage:
    /Users/theceo/DevSkyy/.venv/bin/python scripts/generate_product_embeddings.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.core import clip_embedder  # noqa: E402
from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.core.paths import THEME_ROOT  # noqa: E402

SOT_IMAGES_PATH = ROOT / "data" / "sot-images.json"
OUTPUT_PATH = ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "product-embeddings.json"


def _load_sot_images() -> dict[str, dict]:
    """Load the canonical SOT imagery contract (never the raw CSV image columns)."""
    payload = json.loads(SOT_IMAGES_PATH.read_text())
    return payload["images"]


def main() -> int:
    catalog_rows = read_catalog_rows()
    sot_images = _load_sot_images()

    products: dict[str, dict] = {}
    skipped: list[tuple[str, str]] = []

    for row in catalog_rows:
        sku = row["sku"]
        name = row["name"]
        collection = row["collection"]

        entry = sot_images.get(sku)
        if not entry or not entry.get("front"):
            skipped.append((sku, "no front image in sot-images.json"))
            continue

        front_rel = entry["front"]
        front_abs = THEME_ROOT / front_rel
        if not front_abs.exists():
            skipped.append((sku, f"resolved path does not exist: {front_abs}"))
            continue

        try:
            vec = clip_embedder.embed_image(front_abs)
        except Exception as exc:  # noqa: BLE001 — log and skip, never crash the batch
            skipped.append((sku, f"CLIP embed failed: {exc}"))
            continue

        products[sku] = {
            "name": name,
            "collection": collection,
            "embedding": vec.tolist(),
        }
        print(f"  embedded {sku} ({name}) <- {front_rel}")

    if not products:
        print("FATAL: zero SKUs embedded — nothing to write", file=sys.stderr)
        return 2

    payload = {
        "model": clip_embedder.MODEL_ID,
        "dim": clip_embedder.EMBED_DIM,
        "generated": datetime.now(UTC).isoformat(timespec="seconds"),
        "products": products,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")

    print()
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"  embedded: {len(products)}/{len(catalog_rows)} SKUs")
    if skipped:
        print(f"  skipped: {len(skipped)}")
        for sku, reason in skipped:
            print(f"    - {sku}: {reason}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
