"""Tests for the brand_centroid JSON sidecar machinery.

The sidecar exists so binary .npz centroids have a human-readable
provenance trail (see ADR-0002). These tests cover the round-trip
contract — sidecars must record encoder, model_id, sample_count,
threshold, dim/norm sanity checks, sample paths + hash, and an npz
SHA-256 — and the legacy-load case where an existing .npz lacks
sample_paths.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from skyyrose.elite_studio.quality.brand_centroid import (
    SIDECAR_SCHEMA_VERSION,
    BrandCentroid,
    save_centroid,
    save_centroid_with_sidecar,
    write_metadata_sidecar,
)


def _make_centroid(
    *,
    dim: int = 512,
    model_id: str = "openai/clip-vit-base-patch32",
    sample_paths: list[str] | None = None,
) -> BrandCentroid:
    rng = np.random.default_rng(42)
    raw = rng.standard_normal(dim).astype(np.float32)
    centroid = raw / np.linalg.norm(raw)
    return BrandCentroid(
        centroid=centroid.astype(np.float32),
        threshold=0.7631,
        sample_count=23,
        model_id=model_id,
        sample_paths=sample_paths or [],
    )


def test_sidecar_records_required_fields(tmp_path: Path) -> None:
    centroid = _make_centroid(sample_paths=["a/b/img1.png", "a/b/img2.webp", "a/b/img3.jpg"])
    npz_path = tmp_path / "brand_centroid.npz"
    save_centroid(centroid, npz_path)

    sidecar = write_metadata_sidecar(centroid, npz_path)
    payload = json.loads(sidecar.read_text())

    assert payload["schema_version"] == SIDECAR_SCHEMA_VERSION
    assert payload["encoder"] == "clip"
    assert payload["model_id"] == "openai/clip-vit-base-patch32"
    assert payload["sample_count"] == 23
    assert payload["threshold"] == pytest.approx(0.7631, abs=1e-4)
    assert payload["centroid_dim"] == 512
    assert payload["centroid_l2_norm"] == pytest.approx(1.0, abs=1e-4)
    assert payload["sample_paths"] == ["a/b/img1.png", "a/b/img2.webp", "a/b/img3.jpg"]
    assert payload["sample_paths_hash"] is not None
    assert len(payload["sample_paths_hash"]) == 16  # truncated sha256
    assert payload["npz_filename"] == "brand_centroid.npz"
    assert payload["npz_sha256"] is not None
    assert "generated_at" in payload


def test_sidecar_dino_encoder_inferred_from_model_id(tmp_path: Path) -> None:
    centroid = _make_centroid(dim=768, model_id="facebook/dinov2-base")
    npz_path = tmp_path / "brand_centroid_dino.npz"
    save_centroid(centroid, npz_path)
    sidecar = write_metadata_sidecar(centroid, npz_path)
    payload = json.loads(sidecar.read_text())

    assert payload["encoder"] == "dino"
    assert payload["centroid_dim"] == 768


def test_sidecar_explicit_encoder_overrides_inference(tmp_path: Path) -> None:
    """If the model_id is ambiguous, an explicit encoder argument wins."""
    centroid = _make_centroid(model_id="custom-encoder-xyz")
    npz_path = tmp_path / "brand_centroid.npz"
    save_centroid(centroid, npz_path)
    sidecar = write_metadata_sidecar(centroid, npz_path, encoder="dino")
    payload = json.loads(sidecar.read_text())

    assert payload["encoder"] == "dino"


def test_sidecar_handles_legacy_centroid_without_sample_paths(tmp_path: Path) -> None:
    """Centroids built before sample_paths existed should still get a sidecar."""
    centroid = _make_centroid(sample_paths=[])  # legacy: no sample paths
    npz_path = tmp_path / "brand_centroid.npz"
    save_centroid(centroid, npz_path)
    sidecar = write_metadata_sidecar(centroid, npz_path)
    payload = json.loads(sidecar.read_text())

    assert payload["sample_paths"] == []
    assert payload["sample_paths_hash"] is None  # explicit None, not a hash of empty


def test_sidecar_path_hash_is_deterministic(tmp_path: Path) -> None:
    """Same input paths -> same hash (provenance fingerprint)."""
    paths_a = ["x/img2.png", "x/img1.png", "x/img3.png"]
    paths_b = ["x/img1.png", "x/img2.png", "x/img3.png"]  # different order, same set
    c_a = _make_centroid(sample_paths=paths_a)
    c_b = _make_centroid(sample_paths=paths_b)

    npz_a = tmp_path / "a.npz"
    npz_b = tmp_path / "b.npz"
    save_centroid(c_a, npz_a)
    save_centroid(c_b, npz_b)

    payload_a = json.loads(write_metadata_sidecar(c_a, npz_a).read_text())
    payload_b = json.loads(write_metadata_sidecar(c_b, npz_b).read_text())

    assert payload_a["sample_paths_hash"] == payload_b["sample_paths_hash"]


def test_sidecar_path_hash_changes_when_filename_changes(tmp_path: Path) -> None:
    """Renaming/swapping a sample image must change the hash."""
    c_a = _make_centroid(sample_paths=["x/img1.png", "x/img2.png"])
    c_b = _make_centroid(sample_paths=["x/img1.png", "x/img2-RENAMED.png"])
    npz_a = tmp_path / "a.npz"
    npz_b = tmp_path / "b.npz"
    save_centroid(c_a, npz_a)
    save_centroid(c_b, npz_b)

    payload_a = json.loads(write_metadata_sidecar(c_a, npz_a).read_text())
    payload_b = json.loads(write_metadata_sidecar(c_b, npz_b).read_text())

    assert payload_a["sample_paths_hash"] != payload_b["sample_paths_hash"]


def test_save_centroid_with_sidecar_writes_both(tmp_path: Path) -> None:
    centroid = _make_centroid(sample_paths=["a.png", "b.png"])
    npz_path = tmp_path / "brand_centroid.npz"
    npz_out, sidecar_out = save_centroid_with_sidecar(centroid, npz_path)

    assert npz_out.exists()
    assert sidecar_out.exists()
    assert sidecar_out.name == "brand_centroid.metadata.json"

    payload = json.loads(sidecar_out.read_text())
    assert payload["sample_count"] == centroid.sample_count


def test_sidecar_overwrites_idempotently(tmp_path: Path) -> None:
    centroid = _make_centroid(sample_paths=["a.png"])
    npz_path = tmp_path / "brand_centroid.npz"
    save_centroid(centroid, npz_path)

    sidecar = write_metadata_sidecar(centroid, npz_path)
    first = sidecar.read_text()
    sidecar2 = write_metadata_sidecar(centroid, npz_path)
    second = sidecar2.read_text()

    assert sidecar == sidecar2
    # Payloads equal modulo generated_at timestamp; structurally identical.
    p1 = json.loads(first)
    p2 = json.loads(second)
    p1.pop("generated_at")
    p2.pop("generated_at")
    assert p1 == p2
