#!/usr/bin/env python3
"""Pre-compute the top-N visually-similar SKUs for the [skyyrose_visual_similar] widget.

Replaces in-browser cosine computation. The widget previously fetched
~200KB of raw embeddings and did a 33×512 dot product in JS on every
product page; now it fetches ~10KB of pre-ranked neighbor lists.

For each SKU we precompute:
  - global top-8 most similar SKUs (cross-collection)
  - same-collection top-8 most similar SKUs

Output schema:
  {
    "version": "1.0",
    "model": "openai/clip-vit-base-patch32",
    "products": {
      "br-001": {
        "name": "...",
        "collection": "black-rose",
        "global":          [{"sku": "br-002", "score": 0.91}, ...],
        "same_collection": [{"sku": "br-002", "score": 0.91}, ...]
      },
      ...
    }
  }

Usage:
  python3 scripts/build_product_similarities.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "wordpress-theme/skyyrose-flagship/data/product-embeddings.json"
DEFAULT_OUTPUT = ROOT / "wordpress-theme/skyyrose-flagship/data/product-similarities.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-n", type=int, default=8)
    args = parser.parse_args()

    if not args.input.exists():
        print(f"FATAL: embeddings not found: {args.input}", file=sys.stderr)
        return 2

    payload = json.loads(args.input.read_text())
    products = payload["products"]
    skus = sorted(products.keys())

    matrix = np.stack([np.asarray(products[s]["embedding"], dtype=np.float32) for s in skus])
    sims = matrix @ matrix.T  # already L2-normalized; cosine == dot
    np.fill_diagonal(sims, -2.0)

    out: dict[str, dict] = {}
    for i, sku in enumerate(skus):
        row_global = np.argsort(-sims[i])[: args.top_n]
        my_collection = products[sku].get("collection", "")

        # Same-collection: filter then rank.
        same_indices = [
            j
            for j in range(len(skus))
            if j != i and products[skus[j]].get("collection", "") == my_collection
        ]
        same_indices.sort(key=lambda j: -float(sims[i, j]))
        same_top = same_indices[: args.top_n]

        out[sku] = {
            "name": products[sku].get("name", ""),
            "collection": my_collection,
            "global": [{"sku": skus[j], "score": round(float(sims[i, j]), 4)} for j in row_global],
            "same_collection": [
                {"sku": skus[j], "score": round(float(sims[i, j]), 4)} for j in same_top
            ],
        }

    payload_out = {
        "version": "1.0",
        "model": payload.get("model", "openai/clip-vit-base-patch32"),
        "top_n": args.top_n,
        "n_products": len(skus),
        "products": out,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload_out, indent=2))

    in_kb = args.input.stat().st_size // 1024
    out_kb = args.output.stat().st_size // 1024
    print(
        f"Wrote {args.output.relative_to(ROOT)} "
        f"({len(skus)} SKUs, top-{args.top_n} each, {out_kb}KB vs embeddings {in_kb}KB)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
