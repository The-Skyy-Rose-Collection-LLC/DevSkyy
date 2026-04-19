"""Pending / lock lifecycle tests for master_registry (Wave 1 catalog bootstrap)."""

from __future__ import annotations

from pathlib import Path

import pytest

from skyyrose.elite_studio import master_registry as mr


@pytest.fixture
def masters_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    manifest = tmp_path / "manifest.json"
    monkeypatch.setenv("SKYYROSE_MASTER_MANIFEST_PATH", str(manifest))
    return tmp_path


def _write(path: Path, payload: bytes = b"bytes") -> Path:
    path.write_bytes(payload)
    return path


def test_register_pending_requires_no_file(masters_root: Path) -> None:
    m = mr.Manifest.load()
    entry = m.register_pending(
        sku="br-001",
        collection="black-rose",
        color_spec={"primary": "#0A0A0A", "accents": ["#B76E79"]},
        text_spec=["SKYY ROSE"],
    )
    assert entry.status == "pending"
    assert entry.master_source == "pending"
    assert entry.master_hash is None
    assert entry.master_path == ""
    assert entry.is_locked is False


def test_register_pending_duplicate_raises_without_overwrite(masters_root: Path) -> None:
    m = mr.Manifest.load()
    m.register_pending(sku="br-001")
    with pytest.raises(ValueError, match="already registered"):
        m.register_pending(sku="br-001")


def test_register_pending_overwrite_refreshes_metadata(masters_root: Path) -> None:
    m = mr.Manifest.load()
    m.register_pending(sku="br-001", notes="first")
    m.register_pending(sku="br-001", notes="updated", overwrite=True)
    assert m.require("br-001").notes == "updated"


def test_lock_transitions_pending_to_locked(masters_root: Path) -> None:
    _write(masters_root / "br-001.webp", b"real image bytes")
    m = mr.Manifest.load()
    m.register_pending(
        sku="br-001",
        collection="black-rose",
        color_spec={"primary": "#0A0A0A"},
        text_spec=["SKYY ROSE"],
    )
    locked = m.lock(sku="br-001", master_path="br-001.webp", master_source="photograph")
    assert locked.status == "locked"
    assert locked.master_source == "photograph"
    assert locked.master_hash is not None
    assert locked.master_hash.startswith("sha256:")
    assert locked.is_locked is True
    # Collection and specs preserved from pending entry.
    assert locked.collection == "black-rose"
    assert locked.color_spec == {"primary": "#0A0A0A"}
    assert locked.text_spec == ["SKYY ROSE"]


def test_lock_with_alpha_hashes_both(masters_root: Path) -> None:
    _write(masters_root / "br-001.webp")
    _write(masters_root / "br-001-alpha.png", b"alpha")
    m = mr.Manifest.load()
    m.register_pending(sku="br-001")
    locked = m.lock(
        sku="br-001",
        master_path="br-001.webp",
        master_source="cad_render",
        alpha_path="br-001-alpha.png",
    )
    assert locked.alpha_hash is not None
    assert locked.alpha_hash.startswith("sha256:")
    assert locked.alpha_hash != locked.master_hash


def test_lock_requires_existing_pending_entry(masters_root: Path) -> None:
    _write(masters_root / "br-001.webp")
    m = mr.Manifest.load()
    with pytest.raises(KeyError, match="br-001"):
        m.lock(sku="br-001", master_path="br-001.webp", master_source="photograph")


def test_lock_rejects_pending_as_source(masters_root: Path) -> None:
    _write(masters_root / "br-001.webp")
    m = mr.Manifest.load()
    m.register_pending(sku="br-001")
    with pytest.raises(ValueError, match="concrete master_source"):
        m.lock(sku="br-001", master_path="br-001.webp", master_source="pending")  # type: ignore[arg-type]


def test_lock_missing_file_raises(masters_root: Path) -> None:
    m = mr.Manifest.load()
    m.register_pending(sku="br-001")
    with pytest.raises(FileNotFoundError):
        m.lock(sku="br-001", master_path="nope.webp", master_source="photograph")


def test_verify_returns_false_for_pending(masters_root: Path) -> None:
    img = _write(masters_root / "br-001.webp", b"any bytes")
    m = mr.Manifest.load()
    m.register_pending(sku="br-001")
    assert m.verify("br-001", img) is False


def test_verify_returns_true_after_lock(masters_root: Path) -> None:
    img = _write(masters_root / "br-001.webp", b"the bytes")
    m = mr.Manifest.load()
    m.register_pending(sku="br-001")
    m.lock(sku="br-001", master_path="br-001.webp", master_source="photograph")
    assert m.verify("br-001", img) is True


def test_pending_and_locked_entries_save_and_reload(masters_root: Path) -> None:
    _write(masters_root / "br-001.webp")
    m = mr.Manifest.load()
    m.register_pending(sku="br-001", collection="black-rose")
    m.register_pending(sku="lh-002", collection="love-hurts")
    m.lock(sku="br-001", master_path="br-001.webp", master_source="photograph")
    m.save()

    reloaded = mr.Manifest.load()
    assert reloaded.require("br-001").status == "locked"
    assert reloaded.require("lh-002").status == "pending"
    assert reloaded.require("br-001").is_locked is True
    assert reloaded.require("lh-002").is_locked is False
