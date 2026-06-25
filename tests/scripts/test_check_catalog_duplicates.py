"""Smoke test for scripts/check_catalog_duplicates.py CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "check_catalog_duplicates.py"


def _build_synthetic(tmp_path: Path, with_duplicate: bool) -> Path:
    rng = np.random.default_rng(11)
    a = rng.standard_normal(512).astype(np.float32)
    a /= np.linalg.norm(a)
    b = a + rng.standard_normal(512).astype(np.float32) * (0.005 if with_duplicate else 1.0)
    b /= np.linalg.norm(b)
    payload = {
        "model": "t",
        "dim": 512,
        "products": {
            "x-1": {"name": "X", "collection": "c", "embedding": a.tolist()},
            "x-2": {"name": "Y", "collection": "c", "embedding": b.tolist()},
        },
    }
    p = tmp_path / "embeddings.json"
    p.write_text(json.dumps(payload))
    return p


def test_cli_exits_zero_when_no_duplicates(tmp_path: Path) -> None:
    embeds = _build_synthetic(tmp_path, with_duplicate=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--embeddings", str(embeds), "--threshold", "0.98"],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert result.returncode == 0, result.stderr
    assert "no duplicates" in result.stdout.lower()


def test_cli_exits_one_when_duplicates_found(tmp_path: Path) -> None:
    embeds = _build_synthetic(tmp_path, with_duplicate=True)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--embeddings", str(embeds), "--threshold", "0.98"],
        capture_output=True,
        text=True,
        cwd=str(REPO),
    )
    assert result.returncode == 1, result.stderr
    assert "x-1" in result.stdout and "x-2" in result.stdout
