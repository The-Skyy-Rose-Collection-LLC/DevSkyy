"""Catalog duplicate detector.

Scans the browser-side embeddings JSON (or any compatible payload) for SKUs
whose CLIP embedding cosine similarity exceeds a threshold. Used by
scripts/check_catalog_duplicates.py at intake to flag near-identical SKUs
before they ship.

Threshold guidance:
    >= 0.99   exact duplicates (e.g. jersey variants of the same garment)
    0.95-0.99 likely duplicates worth a human review
    < 0.95    legitimately distinct products

@package SkyyRose
@since 1.1.0
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class DuplicatePair:
    sku_a: str
    sku_b: str
    score: float
    name_a: str
    name_b: str
    collection_a: str
    collection_b: str


def _load_embeddings(path: Path) -> tuple[list[str], np.ndarray, dict[str, dict]]:
    payload = json.loads(Path(path).read_text())
    products = payload["products"]
    skus = sorted(products.keys())
    matrix = np.stack([np.asarray(products[s]["embedding"], dtype=np.float32) for s in skus])
    return skus, matrix, products


def find_duplicates(embeddings_path: Path, threshold: float = 0.98) -> list[DuplicatePair]:
    """Find every pair of SKUs whose cosine similarity >= threshold."""
    skus, matrix, products = _load_embeddings(embeddings_path)
    sims = matrix @ matrix.T  # (N, N), already L2-normalized
    pairs: list[DuplicatePair] = []
    n = len(skus)
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sims[i, j])
            if score >= threshold:
                pairs.append(
                    DuplicatePair(
                        sku_a=skus[i],
                        sku_b=skus[j],
                        score=score,
                        name_a=products[skus[i]].get("name", ""),
                        name_b=products[skus[j]].get("name", ""),
                        collection_a=products[skus[i]].get("collection", ""),
                        collection_b=products[skus[j]].get("collection", ""),
                    )
                )
    pairs.sort(key=lambda p: -p.score)
    return pairs
