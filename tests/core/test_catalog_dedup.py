"""Tests for skyyrose.core.catalog_dedup."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from skyyrose.core import catalog_dedup


def _make_embeddings_json(tmp_path: Path) -> Path:
    """Build a synthetic embeddings JSON with one duplicate pair."""
    rng = np.random.default_rng(7)
    base = rng.standard_normal(512).astype(np.float32)
    base = base / np.linalg.norm(base)

    # br-001 and br-001-twin are 0.999 similar (duplicate).
    twin = base + rng.standard_normal(512).astype(np.float32) * 0.005
    twin = twin / np.linalg.norm(twin)

    other = rng.standard_normal(512).astype(np.float32)
    other = other / np.linalg.norm(other)

    payload = {
        "model": "test",
        "dim": 512,
        "products": {
            "br-001": {
                "name": "Original",
                "collection": "black-rose",
                "embedding": base.tolist(),
            },
            "br-001-twin": {
                "name": "Duplicate",
                "collection": "black-rose",
                "embedding": twin.tolist(),
            },
            "sg-001": {
                "name": "Different",
                "collection": "signature",
                "embedding": other.tolist(),
            },
        },
    }
    out = tmp_path / "embeddings.json"
    out.write_text(json.dumps(payload))
    return out


def test_find_duplicates_detects_near_duplicate(tmp_path: Path) -> None:
    path = _make_embeddings_json(tmp_path)
    dups = catalog_dedup.find_duplicates(path, threshold=0.98)
    pairs = {(d.sku_a, d.sku_b) for d in dups}
    assert ("br-001", "br-001-twin") in pairs or ("br-001-twin", "br-001") in pairs


def test_find_duplicates_skips_below_threshold(tmp_path: Path) -> None:
    path = _make_embeddings_json(tmp_path)
    dups = catalog_dedup.find_duplicates(path, threshold=0.98)
    pairs = {tuple(sorted([d.sku_a, d.sku_b])) for d in dups}
    assert tuple(sorted(["br-001", "sg-001"])) not in pairs


def test_find_duplicates_reports_score(tmp_path: Path) -> None:
    path = _make_embeddings_json(tmp_path)
    dups = catalog_dedup.find_duplicates(path, threshold=0.98)
    assert all(d.score >= 0.98 for d in dups)
    assert all(0.98 <= d.score <= 1.0 for d in dups)
