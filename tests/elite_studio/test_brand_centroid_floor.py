"""Model-free tests for brand_centroid MIN_APPROVED floor + manifest allowlist.

These tests monkeypatch ``_embed`` so no CLIP/DINOv2 model is loaded.
They run in the default (non-slow) suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from skyyrose.elite_studio.quality import brand_centroid
from skyyrose.elite_studio.quality.brand_centroid import MIN_APPROVED, build_centroid


def _make_images(directory: Path, n: int) -> list[Path]:
    """Write ``n`` minimal PNG stubs (zero-byte files with .png extension)."""
    paths = []
    for i in range(n):
        p = directory / f"img_{i:03d}.png"
        p.touch()
        paths.append(p)
    return paths


def _fixed_embed(encoder, path: Path) -> np.ndarray:
    """Return a deterministic nonzero unit vector keyed on the filename."""
    seed = int.from_bytes(path.name.encode(), "little") % (2**31)
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(512).astype(np.float32)
    return v / np.linalg.norm(v)


# ── MIN_APPROVED floor ────────────────────────────────────────────────────────


def test_floor_raises_when_below_min(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(brand_centroid, "_embed", _fixed_embed)
    d = tmp_path / "approved"
    d.mkdir()
    _make_images(d, MIN_APPROVED - 1)

    with pytest.raises(ValueError, match=str(MIN_APPROVED)):
        build_centroid(d)


def test_floor_passes_at_exactly_min(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(brand_centroid, "_embed", _fixed_embed)
    d = tmp_path / "approved"
    d.mkdir()
    _make_images(d, MIN_APPROVED)

    result = build_centroid(d)
    assert result.sample_count == MIN_APPROVED
    assert result.centroid.shape == (512,)
    assert pytest.approx(float(np.linalg.norm(result.centroid)), abs=1e-4) == 1.0


# ── manifest allowlist ────────────────────────────────────────────────────────


def test_manifest_list_format_selects_subset(tmp_path: Path, monkeypatch) -> None:
    """Manifest as a plain list selects only those files; centroid uses subset."""
    monkeypatch.setattr(brand_centroid, "_embed", _fixed_embed)
    d = tmp_path / "approved"
    d.mkdir()
    all_paths = _make_images(d, MIN_APPROVED + 4)  # 12 total
    subset_names = [p.name for p in all_paths[:MIN_APPROVED]]  # pick first 8

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(subset_names))

    result = build_centroid(d, manifest=manifest)
    assert result.sample_count == MIN_APPROVED
    assert set(Path(p).name for p in result.sample_paths) == set(subset_names)


def test_manifest_object_format_selects_subset(tmp_path: Path, monkeypatch) -> None:
    """Manifest as {"approved": [...]} is also accepted."""
    monkeypatch.setattr(brand_centroid, "_embed", _fixed_embed)
    d = tmp_path / "approved"
    d.mkdir()
    all_paths = _make_images(d, MIN_APPROVED + 2)
    subset_names = [p.name for p in all_paths[:MIN_APPROVED]]

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"approved": subset_names}))

    result = build_centroid(d, manifest=manifest)
    assert result.sample_count == MIN_APPROVED
    assert set(Path(p).name for p in result.sample_paths) == set(subset_names)


def test_manifest_missing_file_raises(tmp_path: Path, monkeypatch) -> None:
    """A manifest entry with no matching file in approved_dir is an error."""
    monkeypatch.setattr(brand_centroid, "_embed", _fixed_embed)
    d = tmp_path / "approved"
    d.mkdir()
    _make_images(d, MIN_APPROVED)

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(["does_not_exist.png"]))

    with pytest.raises(ValueError, match="does_not_exist.png"):
        build_centroid(d, manifest=manifest)


def test_manifest_subset_below_floor_raises(tmp_path: Path, monkeypatch) -> None:
    """Manifest that selects fewer than MIN_APPROVED files raises the floor error."""
    monkeypatch.setattr(brand_centroid, "_embed", _fixed_embed)
    d = tmp_path / "approved"
    d.mkdir()
    all_paths = _make_images(d, MIN_APPROVED + 2)
    # Select only 3 — below the floor.
    subset_names = [p.name for p in all_paths[:3]]

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(subset_names))

    with pytest.raises(ValueError, match=str(MIN_APPROVED)):
        build_centroid(d, manifest=manifest)


# ── back-compat: no manifest + >= MIN_APPROVED ────────────────────────────────


def test_no_manifest_uses_all_images(tmp_path: Path, monkeypatch) -> None:
    """Without a manifest, all images in approved_dir are used (back-compat)."""
    monkeypatch.setattr(brand_centroid, "_embed", _fixed_embed)
    d = tmp_path / "approved"
    d.mkdir()
    n = MIN_APPROVED + 3
    _make_images(d, n)

    result = build_centroid(d)
    assert result.sample_count == n
