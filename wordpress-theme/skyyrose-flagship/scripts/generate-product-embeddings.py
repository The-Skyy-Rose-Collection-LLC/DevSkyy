#!/usr/bin/env python3
"""
Generate CLIP embeddings for every published SKU image.

Reads:  data/skyyrose-catalog.csv (canonical product source of truth)
Writes: data/product-embeddings.json (consumed by visual-similarity.js)

Run from the theme root:
    python3 scripts/generate-product-embeddings.py

Re-run whenever:
- A new published SKU is added to the catalog
- An existing SKU's primary `image` field changes
- You want to refresh after a major image asset update

The output JSON is checked in (small — ~70 KB for 24 products) so the browser
fetches a static asset, not a generated artifact. No model runs in the browser.

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

# Resolve theme root regardless of where the script is invoked from.
SCRIPT_DIR = Path(__file__).resolve().parent
THEME_ROOT = SCRIPT_DIR.parent

CATALOG_CSV = THEME_ROOT / "data" / "skyyrose-catalog.csv"
OUTPUT_JSON = THEME_ROOT / "data" / "product-embeddings.json"

MODEL_ID = "openai/clip-vit-base-patch32"


def load_published_rows(csv_path: Path) -> list[dict]:
    """Read every row where published == "1". Drop everything else."""
    if not csv_path.exists():
        sys.exit(f"FATAL: catalog not found at {csv_path}")

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row.get("published") == "1"]

    if not rows:
        sys.exit("FATAL: catalog has no published rows")

    return rows


def resolve_image(theme_root: Path, image_field: str) -> Path | None:
    """Catalog image fields are relative to the theme root."""
    if not image_field:
        return None
    candidate = theme_root / image_field
    return candidate if candidate.exists() else None


def embed_image(model: CLIPModel, processor: CLIPProcessor, path: Path, device: str) -> list[float]:
    """Run image through CLIP vision encoder, L2-normalize, return as Python list."""
    with Image.open(path) as img:
        img = img.convert("RGB")
        inputs = processor(images=img, return_tensors="pt").to(device)

    with torch.no_grad():
        features = model.get_image_features(**inputs)

    # L2 normalize so cosine similarity reduces to a dot product in the browser.
    features = features / features.norm(p=2, dim=-1, keepdim=True)
    return features.squeeze(0).cpu().tolist()


def main() -> int:
    rows = load_published_rows(CATALOG_CSV)
    print(f"Loaded {len(rows)} published SKUs from catalog", flush=True)

    device = (
        "cuda"
        if torch.cuda.is_available()
        else "mps"
        if torch.backends.mps.is_available()
        else "cpu"
    )
    print(f"Loading {MODEL_ID} on {device}...", flush=True)

    t0 = time.time()
    model = CLIPModel.from_pretrained(MODEL_ID).to(device).eval()
    processor = CLIPProcessor.from_pretrained(MODEL_ID)
    print(f"Model loaded in {time.time() - t0:.1f}s", flush=True)

    products: dict[str, dict] = {}
    skipped: list[tuple[str, str]] = []

    for i, row in enumerate(rows, 1):
        sku = row["sku"]
        image_path = resolve_image(THEME_ROOT, row.get("image", ""))

        if image_path is None:
            skipped.append((sku, f"image not found: {row.get('image', '<empty>')}"))
            continue

        try:
            embedding = embed_image(model, processor, image_path, device)
        except Exception as exc:
            skipped.append((sku, f"embed failed: {exc}"))
            continue

        products[sku] = {
            "name": row.get("name", ""),
            "collection": row.get("collection", ""),
            "image": row.get("image", ""),
            "embedding": [round(v, 6) for v in embedding],
        }
        print(f"  [{i:>2}/{len(rows)}] {sku:<10} {row.get('name', '')[:40]}", flush=True)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": MODEL_ID,
        "dim": 512,
        "count": len(products),
        "products": products,
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"), ensure_ascii=False)

    size_kb = OUTPUT_JSON.stat().st_size / 1024
    print(
        f"\nWrote {len(products)} embeddings ({size_kb:.1f} KB) -> {OUTPUT_JSON.relative_to(THEME_ROOT)}"
    )

    if skipped:
        print(f"\nSkipped {len(skipped)}:")
        for sku, reason in skipped:
            print(f"  {sku}: {reason}")
        return 1 if len(skipped) == len(rows) else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
