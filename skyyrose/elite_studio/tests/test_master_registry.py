"""Tests for skyyrose.elite_studio.master_registry (Wave 1 reference-first pipeline)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from skyyrose.elite_studio import master_registry as mr


@pytest.fixture
def masters_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    manifest = tmp_path / "manifest.json"
    monkeypatch.setenv("SKYYROSE_MASTER_MANIFEST_PATH", str(manifest))
    return tmp_path


def _write_image(path: Path, payload: bytes = b"\x89PNG\r\n\x1a\n\xff") -> Path:
    path.write_bytes(payload)
    return path


def test_sha256_of_file_is_deterministic(tmp_path: Path) -> None:
    p = _write_image(tmp_path / "x.bin", b"hello world")
    assert mr.sha256_of_file(p) == mr.sha256_of_file(p)
    assert mr.sha256_of_file(p).startswith("sha256:")


def test_sha256_detects_content_change(tmp_path: Path) -> None:
    p = _write_image(tmp_path / "x.bin", b"aaa")
    h1 = mr.sha256_of_file(p)
    p.write_bytes(b"bbb")
    assert mr.sha256_of_file(p) != h1


def test_manifest_load_nonexistent_returns_empty(masters_root: Path) -> None:
    m = mr.Manifest.load()
    assert m.masters == {}
    assert m.version == 1


def test_register_and_save_and_reload_roundtrip(masters_root: Path) -> None:
    _write_image(masters_root / "br-001.webp", b"product bytes")
    m = mr.Manifest.load()
    entry = m.register(
        sku="br-001",
        master_path="br-001.webp",
        master_source="photograph",
        collection="black-rose",
        color_spec={"primary": "#0A0A0A", "accents": ["#B76E79"]},
        text_spec=["SKYY ROSE"],
        photographed_at="2026-03-08T14:22:00Z",
        locked_at_version="v3.2.0",
    )
    assert entry.sku == "br-001"
    assert entry.master_hash.startswith("sha256:")
    saved = m.save()
    assert saved.exists()

    # Reload and compare.
    m2 = mr.Manifest.load()
    assert m2.list_skus() == ["br-001"]
    reloaded = m2.require("br-001")
    assert reloaded.master_hash == entry.master_hash
    assert reloaded.color_spec == {"primary": "#0A0A0A", "accents": ["#B76E79"]}
    assert reloaded.text_spec == ["SKYY ROSE"]


def test_register_missing_master_file_raises(masters_root: Path) -> None:
    m = mr.Manifest.load()
    with pytest.raises(FileNotFoundError):
        m.register(sku="br-001", master_path="does-not-exist.webp", master_source="photograph")


def test_register_duplicate_without_overwrite_raises(masters_root: Path) -> None:
    _write_image(masters_root / "br-001.webp")
    m = mr.Manifest.load()
    m.register(sku="br-001", master_path="br-001.webp", master_source="photograph")
    with pytest.raises(ValueError, match="already registered"):
        m.register(sku="br-001", master_path="br-001.webp", master_source="photograph")


def test_register_overwrite_replaces_entry(masters_root: Path) -> None:
    _write_image(masters_root / "br-001.webp", b"v1")
    m = mr.Manifest.load()
    m.register(sku="br-001", master_path="br-001.webp", master_source="photograph")
    old_hash = m.require("br-001").master_hash

    _write_image(masters_root / "br-001.webp", b"v2")
    m.register(sku="br-001", master_path="br-001.webp", master_source="photograph", overwrite=True)
    assert m.require("br-001").master_hash != old_hash


def test_register_with_alpha_computes_alpha_hash(masters_root: Path) -> None:
    _write_image(masters_root / "br-001.webp", b"rgba")
    _write_image(masters_root / "br-001-alpha.png", b"alpha bytes")
    m = mr.Manifest.load()
    entry = m.register(
        sku="br-001",
        master_path="br-001.webp",
        master_source="photograph",
        alpha_path="br-001-alpha.png",
    )
    assert entry.alpha_hash is not None
    assert entry.alpha_hash.startswith("sha256:")
    assert entry.alpha_hash != entry.master_hash


def test_verify_detects_tampering(masters_root: Path) -> None:
    p = _write_image(masters_root / "br-001.webp", b"original")
    m = mr.Manifest.load()
    m.register(sku="br-001", master_path="br-001.webp", master_source="photograph")
    m.save()

    assert m.verify("br-001", p) is True

    p.write_bytes(b"tampered")
    assert m.verify("br-001", p) is False


def test_verify_unknown_sku_returns_false(masters_root: Path, tmp_path: Path) -> None:
    other = _write_image(tmp_path / "other.bin", b"x")
    m = mr.Manifest.load()
    assert m.verify("nonexistent", other) is False


def test_require_missing_raises_keyerror(masters_root: Path) -> None:
    m = mr.Manifest.load()
    with pytest.raises(KeyError, match="nonexistent"):
        m.require("nonexistent")


def test_save_is_atomic_no_partial_file(masters_root: Path) -> None:
    _write_image(masters_root / "br-001.webp")
    m = mr.Manifest.load()
    m.register(sku="br-001", master_path="br-001.webp", master_source="photograph")
    m.save()

    # No leftover tmp files.
    tmps = list(masters_root.glob(".manifest-*.tmp"))
    assert tmps == []

    # Manifest is valid JSON.
    data = json.loads((masters_root / "manifest.json").read_text())
    assert "br-001" in data["masters"]
    assert data["version"] == 1


def test_master_source_literal_types(masters_root: Path) -> None:
    _write_image(masters_root / "br-001.webp")
    m = mr.Manifest.load()
    for src in ("photograph", "cad_render", "3d_model", "generative_locked"):
        m.register(sku=f"test-{src}", master_path="br-001.webp", master_source=src)
    assert len(m.list_skus()) == 4
