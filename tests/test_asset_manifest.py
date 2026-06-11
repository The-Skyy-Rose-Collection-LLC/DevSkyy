"""Asset-manifest integrity gate.

Guards the content-hashed SKU→asset manifest (``assets/products/manifest.json``)
against the two drift classes it exists to prevent:

1. **Stale manifest** — a source file was renamed/replaced but the manifest was
   not regenerated. ``--check`` (regenerate-and-diff) catches it.
2. **Broken tree** — the committed manifest names a file that is now missing or
   whose content changed. ``verify()`` catches it.

These are the bug-119 (mislabeled-reference) and "rename breaks mid-paid-run"
preventions, asserted in CI.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from skyyrose.core.asset_manifest import AssetManifest

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "assets" / "products" / "manifest.json"


def _load_builder():
    """Import scripts/build_asset_manifest.py as a module (hyphen-free path)."""
    spec = importlib.util.spec_from_file_location(
        "build_asset_manifest", REPO_ROOT / "scripts" / "build_asset_manifest.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_manifest_exists_and_loads():
    assert MANIFEST.exists(), (
        "assets/products/manifest.json missing — run scripts/build_asset_manifest.py"
    )
    m = AssetManifest.load()
    assert m.skus, "manifest registered zero SKUs"


def test_committed_manifest_matches_regenerated_tree():
    """The committed manifest must equal a fresh regeneration (no silent drift)."""
    builder = _load_builder()
    fresh = builder.build()
    committed = AssetManifest.load()
    assert committed.to_payload()["skus"] == fresh.to_payload()["skus"], (
        "asset manifest is stale — a source file changed without regeneration. "
        "Run `python scripts/build_asset_manifest.py` and commit."
    )


def test_every_pinned_asset_exists_and_hash_matches():
    """verify() over the whole committed manifest must report zero drift."""
    drift = AssetManifest.load().verify()
    assert not drift, "asset drift: " + "; ".join(
        f"{d.sku}/{d.role}:{d.kind}:{d.path}" for d in drift
    )


def test_catalog_sha_is_pinned():
    m = AssetManifest.load()
    assert m.catalog_sha and m.catalog_sha.startswith("sha256:")


def test_verify_detects_a_missing_file(tmp_path):
    """A manifest that names an absent file must surface as drift."""
    from skyyrose.core.asset_manifest import AssetRecord, SkuAssets

    m = AssetManifest()
    m.skus["x-001"] = SkuAssets(
        sku="x-001",
        name="X",
        collection="test",
        garment_type="tee",
        assets=[
            AssetRecord(
                role="front",
                path="assets/products/_does_not_exist.png",
                sha256="sha256:dead",
            )
        ],
    )
    drift = m.verify(base=tmp_path)
    assert len(drift) == 1 and drift[0].kind == "missing"


def test_keeper_with_missing_asset_is_ignored(tmp_path, monkeypatch):
    """A keeper whose surviving asset is gone must NOT block the re-render."""
    import json

    from scripts.oai_render import config, pipeline

    kj = tmp_path / "render-keepers.json"
    kj.write_text(
        json.dumps(
            {
                "keepers": [
                    {
                        "sku": "sg-009",
                        "style": "on-model",
                        "view": "front",
                        "asset": "assets/products/_gone.webp",
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(config, "KEEPERS_JSON", kj)
    skips = pipeline._keeper_skips()
    assert ("sg-009", "on-model", "front") not in skips  # asset missing → not skipped
