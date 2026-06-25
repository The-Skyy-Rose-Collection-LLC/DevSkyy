"""Phase 18 — upload CLI tests (UPLOAD-01).

FakeWCClient implements the WCClient Protocol; no HTTP mocking needed.
Each test builds a tiny isolated repo skeleton via tmp_path + monkeypatch on
read_catalog_rows so the real catalog is never touched.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from skyyrose.elite_studio.upload import (
    APPROVED_PUBLIC_PREFIX,
    GHOST_FILENAME_FMT,
    PreviewRow,
    UploadEntry,
    UploadManifest,
    UploadResult,
    WCClient,
    build_manifest,
    format_manifest_table,
    format_results_table,
    preview_manifest,
    upload_batch,
)

CATALOG_REL = Path("wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv")
GHOST_REL = Path("renders/ghost-mannequin")
APPROVED_REL = GHOST_REL / "approved"

REPO_ROOT = Path(__file__).resolve().parents[1]
UPLOAD_CLI = REPO_ROOT / "scripts" / "upload_approved.py"


def _approved_path(tmp_path: Path, sku: str) -> Path:
    """Return tmp_path-rooted equivalent of renders/ghost-mannequin/approved/{sku}-ghost-front.webp.

    Required because _validate_source enforces structural containment:
    resolved path's parent must be `approved/`, grandparent `ghost-mannequin/`.
    """
    p = tmp_path / "renders" / "ghost-mannequin" / "approved" / f"{sku}-ghost-front.webp"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


# ─────────────────────────── fake WC client ──────────────────────────────────


class FakeWCClient:
    """In-memory WC client implementing WCClient Protocol. Tests script behaviour."""

    def __init__(
        self,
        *,
        sku_to_product: dict[str, int] | None = None,
        product_images: dict[int, list[dict[str, Any]]] | None = None,
        upload_failures: set[str] | None = None,
        update_failures: set[int] | None = None,
        lookup_failures: set[str] | None = None,
    ) -> None:
        self.sku_to_product = sku_to_product or {}
        self.product_images = product_images or {}
        self.upload_failures = upload_failures or set()
        self.update_failures = update_failures or set()
        self.lookup_failures = lookup_failures or set()
        self._next_media_id = 1000
        self.calls: list[tuple[str, Any]] = []

    async def find_product_id_by_sku(self, sku: str) -> int | None:
        self.calls.append(("find", sku))
        if sku in self.lookup_failures:
            raise RuntimeError(f"simulated lookup failure for {sku}")
        return self.sku_to_product.get(sku)

    async def get_product_images(self, product_id: int) -> list[dict[str, Any]]:
        self.calls.append(("get_images", product_id))
        return list(self.product_images.get(product_id, []))

    async def upload_media(self, file_path: Path, alt_text: str = "") -> dict[str, Any]:
        self.calls.append(("upload_media", str(file_path)))
        if file_path.name in self.upload_failures:
            raise RuntimeError(f"simulated media upload failure: {file_path.name}")
        media_id = self._next_media_id
        self._next_media_id += 1
        source_url = f"https://cdn.example.com/{file_path.name}"
        return {"id": media_id, "source_url": source_url, "alt_text": alt_text}

    async def set_product_image(
        self, product_id: int, media_id: int, source_url: str
    ) -> dict[str, Any]:
        self.calls.append(("set_image", product_id, media_id))
        if product_id in self.update_failures:
            raise RuntimeError(f"simulated update failure for product {product_id}")
        # Mutate state so subsequent get_product_images reflects the write.
        self.product_images[product_id] = [{"id": media_id, "src": source_url, "position": 0}]
        return {"id": product_id, "images": self.product_images[product_id]}


# ─────────────────────────── fixtures ─────────────────────────────────────────


def _make_fake_repo(
    tmp_path: Path,
    *,
    skus: list[str],
    approved_skus: list[str],
    published_overrides: dict[str, str] | None = None,
    skipped_json: dict[str, Any] | None = None,
) -> Path:
    """Build a minimal repo skeleton with catalog + approved/ + optional SKIPPED.json."""
    overrides = published_overrides or {}
    catalog_path = tmp_path / CATALOG_REL
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sku",
        "name",
        "price",
        "collection",
        "front_model_image",
        "published",
    ]
    rows = [
        {
            "sku": sku,
            "name": f"Test {sku}",
            "price": "100",
            "collection": "test",
            "front_model_image": f"assets/images/products/{sku}-front.webp",
            "published": overrides.get(sku, "1"),
        }
        for sku in skus
    ]
    with catalog_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    approved_dir = tmp_path / APPROVED_REL
    approved_dir.mkdir(parents=True, exist_ok=True)
    for sku in approved_skus:
        (approved_dir / GHOST_FILENAME_FMT.format(sku=sku)).write_bytes(b"WEBP_" + sku.encode())

    if skipped_json is not None:
        skipped_path = tmp_path / GHOST_REL / "SKIPPED.json"
        skipped_path.write_text(json.dumps(skipped_json), encoding="utf-8")
    return tmp_path


@pytest.fixture
def patch_catalog_loader(monkeypatch: pytest.MonkeyPatch):
    """Redirect read_catalog_rows() to a per-test CSV path."""

    def _patch(root: Path) -> None:
        from skyyrose.core import catalog_loader as cl
        from skyyrose.elite_studio import upload as up

        csv_path = root / CATALOG_REL

        def fake_read(path: Path | None = None) -> list[dict[str, str]]:
            with csv_path.open(encoding="utf-8", newline="") as f:
                return list(csv.DictReader(f))

        monkeypatch.setattr(cl, "read_catalog_rows", fake_read)
        monkeypatch.setattr(up, "read_catalog_rows", fake_read)

    return _patch


# ─────────────────────────── TestBuildManifest (UPLOAD-01 manifest gating) ───


class TestBuildManifest:
    def test_includes_only_skus_with_approved_files(
        self, tmp_path: Path, patch_catalog_loader: Any
    ) -> None:
        root = _make_fake_repo(
            tmp_path,
            skus=["br-001", "br-002", "br-003"],
            approved_skus=["br-001", "br-003"],
        )
        patch_catalog_loader(root)
        manifest = build_manifest(root=root)
        assert sorted(e.sku for e in manifest.entries) == ["br-001", "br-003"]
        assert any(s.sku == "br-002" and "no approved file" in s.reason for s in manifest.skipped)

    def test_excludes_sku_with_published_zero(
        self, tmp_path: Path, patch_catalog_loader: Any
    ) -> None:
        root = _make_fake_repo(
            tmp_path,
            skus=["br-001", "br-002"],
            approved_skus=["br-001", "br-002"],
            published_overrides={"br-002": "0"},
        )
        patch_catalog_loader(root)
        manifest = build_manifest(root=root)
        assert [e.sku for e in manifest.entries] == ["br-001"]
        assert any(s.sku == "br-002" and "published" in s.reason for s in manifest.skipped)

    def test_excludes_skus_in_skipped_json(self, tmp_path: Path, patch_catalog_loader: Any) -> None:
        root = _make_fake_repo(
            tmp_path,
            skus=["br-001", "sg-007"],
            approved_skus=["br-001", "sg-007"],
            skipped_json={
                "skipped": [{"sku": "sg-007", "name": "Beanie", "collection": "signature"}]
            },
        )
        patch_catalog_loader(root)
        manifest = build_manifest(root=root)
        assert [e.sku for e in manifest.entries] == ["br-001"]
        assert any(s.sku == "sg-007" and "SKIPPED.json" in s.reason for s in manifest.skipped)

    def test_empty_manifest_when_nothing_eligible(
        self, tmp_path: Path, patch_catalog_loader: Any
    ) -> None:
        root = _make_fake_repo(tmp_path, skus=["br-001", "br-002"], approved_skus=[])
        patch_catalog_loader(root)
        manifest = build_manifest(root=root)
        assert manifest.entries == []
        assert len(manifest.skipped) == 2

    def test_entries_sorted_by_sku(self, tmp_path: Path, patch_catalog_loader: Any) -> None:
        root = _make_fake_repo(
            tmp_path,
            skus=["sg-001", "br-001", "lh-002"],
            approved_skus=["sg-001", "br-001", "lh-002"],
        )
        patch_catalog_loader(root)
        manifest = build_manifest(root=root)
        assert [e.sku for e in manifest.entries] == ["br-001", "lh-002", "sg-001"]

    def test_passes_catalog_rows_override(self, tmp_path: Path) -> None:
        # When catalog_rows is provided directly, no CSV read happens.
        (tmp_path / APPROVED_REL).mkdir(parents=True)
        (tmp_path / APPROVED_REL / "br-001-ghost-front.webp").write_bytes(b"x")
        rows = [{"sku": "br-001", "published": "1"}]
        manifest = build_manifest(root=tmp_path, catalog_rows=rows)
        assert [e.sku for e in manifest.entries] == ["br-001"]


# ─────────────────────────── TestPreviewManifest (read-only) ─────────────────


class TestPreviewManifest:
    @pytest.mark.asyncio
    async def test_returns_ready_for_new_image(self, tmp_path: Path) -> None:
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=_approved_path(tmp_path, "br-001"))],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 50, "src": "https://cdn.example.com/old-image.jpg"}]},
        )
        rows = await preview_manifest(client, manifest)
        assert rows[0].status == "READY"
        assert rows[0].product_id == 100
        assert rows[0].current_image_url == "https://cdn.example.com/old-image.jpg"

    @pytest.mark.asyncio
    async def test_returns_already_synced_when_basename_matches(self, tmp_path: Path) -> None:
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=_approved_path(tmp_path, "br-001"))],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={
                100: [{"id": 99, "src": "https://cdn.example.com/br-001-ghost-front.webp"}]
            },
        )
        rows = await preview_manifest(client, manifest)
        assert rows[0].status == "ALREADY_SYNCED"

    @pytest.mark.asyncio
    async def test_returns_product_not_found_when_sku_missing_in_wc(self, tmp_path: Path) -> None:
        manifest = UploadManifest(
            entries=[UploadEntry(sku="xx-999", source_path=tmp_path / "xx-999-ghost-front.webp")],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(sku_to_product={})
        rows = await preview_manifest(client, manifest)
        assert rows[0].status == "PRODUCT_NOT_FOUND"
        assert rows[0].product_id is None

    @pytest.mark.asyncio
    async def test_lookup_failure_marks_product_not_found_not_raises(self, tmp_path: Path) -> None:
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=_approved_path(tmp_path, "br-001"))],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(lookup_failures={"br-001"})
        rows = await preview_manifest(client, manifest)
        assert rows[0].status == "PRODUCT_NOT_FOUND"


# ─────────────────────────── TestUploadBatch (writes) ────────────────────────


class TestUploadBatch:
    @pytest.mark.asyncio
    async def test_happy_path_uploaded_and_verified(self, tmp_path: Path) -> None:
        (_approved_path(tmp_path, "br-001")).write_bytes(b"image-bytes")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=_approved_path(tmp_path, "br-001"))],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 50, "src": "https://cdn.example.com/old.jpg"}]},
        )
        results = await upload_batch(client, manifest)
        assert len(results) == 1
        r = results[0]
        assert r.status == "UPLOADED"
        assert r.verified is True
        assert r.product_id == 100
        assert r.media_id is not None
        assert r.error is None

    @pytest.mark.asyncio
    async def test_dry_run_makes_zero_calls(self, tmp_path: Path) -> None:
        manifest = UploadManifest(
            entries=[
                UploadEntry(sku="br-001", source_path=tmp_path / "a"),
                UploadEntry(sku="br-002", source_path=tmp_path / "b"),
            ],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient()
        results = await upload_batch(client, manifest, dry_run=True)
        assert client.calls == []
        assert all(r.status == "DRY_RUN" for r in results)

    @pytest.mark.asyncio
    async def test_already_synced_skips_upload_call(self, tmp_path: Path) -> None:
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={
                100: [{"id": 99, "src": "https://cdn.example.com/br-001-ghost-front.webp"}]
            },
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "ALREADY_SYNCED"
        # No upload_media call was made.
        assert not any(c[0] == "upload_media" for c in client.calls)

    @pytest.mark.asyncio
    async def test_product_not_found_continues_batch(self, tmp_path: Path) -> None:
        for sku in ("br-001", "br-002"):
            _approved_path(tmp_path, sku).write_bytes(b"x")
        manifest = UploadManifest(
            entries=[
                UploadEntry(sku="br-001", source_path=_approved_path(tmp_path, "br-001")),
                UploadEntry(sku="br-002", source_path=_approved_path(tmp_path, "br-002")),
            ],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-002": 200},
            product_images={200: [{"id": 1, "src": "old.jpg"}]},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "PRODUCT_NOT_FOUND"
        assert results[1].status == "UPLOADED"

    @pytest.mark.asyncio
    async def test_media_upload_failure_marks_failed(self, tmp_path: Path) -> None:
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 1, "src": "old.jpg"}]},
            upload_failures={"br-001-ghost-front.webp"},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "FAILED"
        assert "media upload failed" in results[0].error

    @pytest.mark.asyncio
    async def test_product_update_failure_marks_failed(self, tmp_path: Path) -> None:
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 1, "src": "old.jpg"}]},
            update_failures={100},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "FAILED"
        assert "product update failed" in results[0].error

    @pytest.mark.asyncio
    async def test_verification_failure_when_post_image_mismatch(self, tmp_path: Path) -> None:
        """Verify path: set_product_image succeeds but get_product_images returns
        a different src than the one we just uploaded. Should mark VERIFICATION_FAILED."""
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )

        class FlakyClient(FakeWCClient):
            async def set_product_image(self, product_id, media_id, source_url):
                # Simulate: WC accepts update but the stored src is mangled.
                self.calls.append(("set_image", product_id, media_id))
                self.product_images[product_id] = [
                    {"id": media_id, "src": "https://cdn.example.com/WRONG.webp"}
                ]
                return {"id": product_id}

        client = FlakyClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 1, "src": "old.jpg"}]},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "VERIFICATION_FAILED"
        assert results[0].verified is False

    @pytest.mark.asyncio
    async def test_source_vanished_between_manifest_and_upload(self, tmp_path: Path) -> None:
        ghost = _approved_path(tmp_path, "br-001")
        # Note: file NOT created → simulates vanish race.
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=ghost)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 1, "src": "old.jpg"}]},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "FAILED"
        assert "source file vanished" in results[0].error


# ─────────────────────────── TestRendering ───────────────────────────────────


class TestRendering:
    def test_format_manifest_table_handles_empty(self) -> None:
        assert format_manifest_table([]) == "(empty manifest)"

    def test_format_results_table_handles_empty(self) -> None:
        assert format_results_table([]) == "(no results)"

    def test_format_manifest_table_renders_columns(self, tmp_path: Path) -> None:
        rows = [
            PreviewRow(
                sku="br-001",
                source_path=tmp_path / "x",
                product_id=100,
                current_image_url="https://cdn.example.com/old.jpg",
                status="READY",
            )
        ]
        out = format_manifest_table(rows)
        assert "br-001" in out and "100" in out and "READY" in out

    def test_format_results_table_truncates_long_errors(self) -> None:
        long_err = "X" * 200
        results = [
            UploadResult(
                sku="br-001",
                product_id=100,
                media_id=None,
                source_url=None,
                status="FAILED",
                verified=False,
                error=long_err,
            )
        ]
        out = format_results_table(results)
        # Error column is truncated to 60 chars; not the full 200.
        assert "X" * 60 in out
        assert "X" * 70 not in out


# ─────────────────────────── TestCLIStopAndShow ──────────────────────────────


class TestCLIStopAndShow:
    def test_empty_manifest_exits_1(self, tmp_path: Path) -> None:
        # Build a repo with NO approved files.
        _make_fake_repo(tmp_path, skus=["br-001"], approved_skus=[])
        env_root = str(tmp_path)
        result = subprocess.run(
            [sys.executable, str(UPLOAD_CLI), "--dry-run", "--root", env_root],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "manifest empty" in result.stderr

    def test_dry_run_makes_zero_wc_calls_exits_0(self, tmp_path: Path) -> None:
        _make_fake_repo(tmp_path, skus=["br-001"], approved_skus=["br-001"])
        result = subprocess.run(
            [sys.executable, str(UPLOAD_CLI), "--dry-run", "--root", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "STOP — Confirm before proceeding" in result.stderr
        assert "[--dry-run]" in result.stderr
        assert "br-001" in result.stderr

    def test_dry_run_lists_skipped_skus(self, tmp_path: Path) -> None:
        _make_fake_repo(
            tmp_path,
            skus=["br-001", "br-002"],
            approved_skus=["br-001"],  # br-002 has no approved file
        )
        result = subprocess.run(
            [sys.executable, str(UPLOAD_CLI), "--dry-run", "--root", str(tmp_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "SKIPPED" in result.stderr
        assert "br-002" in result.stderr


# ─────────────────────────── module-level smoke ──────────────────────────────


def test_wcclient_protocol_runtime_check_via_fake() -> None:
    """Sanity: FakeWCClient satisfies the WCClient Protocol shape (duck-typed)."""
    fake: WCClient = FakeWCClient()
    assert hasattr(fake, "find_product_id_by_sku")
    assert hasattr(fake, "get_product_images")
    assert hasattr(fake, "upload_media")
    assert hasattr(fake, "set_product_image")


def test_approved_public_prefix_matches_phase17_contract() -> None:
    """Cross-phase invariant: Phase 17 writes this prefix into CSV; Phase 18 reads from it."""
    assert APPROVED_PUBLIC_PREFIX == "renders/ghost-mannequin/approved"


# ─────────────────────────── TestEdgeCases (coverage push) ───────────────────


class TestEdgeCases:
    """Cover the defensive error branches in upload.py's pure layer."""

    def test_read_catalog_safe_returns_empty_on_filenotfound(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from skyyrose.elite_studio import upload as up

        def raise_fnf(path=None):
            raise FileNotFoundError("simulated missing catalog")

        monkeypatch.setattr(up, "read_catalog_rows", raise_fnf)
        # Empty repo + missing catalog → empty list, no raise
        from pathlib import Path as P

        result = up._read_catalog_safe(P("/nonexistent"))
        assert result == []

    def test_read_catalog_safe_returns_empty_on_generic_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from skyyrose.elite_studio import upload as up

        def raise_generic(path=None):
            raise RuntimeError("simulated parse error")

        monkeypatch.setattr(up, "read_catalog_rows", raise_generic)
        from pathlib import Path as P

        result = up._read_catalog_safe(P("/nonexistent"))
        assert result == []

    def test_load_skipped_set_handles_malformed_json(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import _load_skipped_set

        ghost_dir = tmp_path / "renders" / "ghost-mannequin"
        approved_dir = ghost_dir / "approved"
        approved_dir.mkdir(parents=True)
        (ghost_dir / "SKIPPED.json").write_text("{not json", encoding="utf-8")
        assert _load_skipped_set(approved_dir) == set()

    def test_load_skipped_set_handles_non_dict_root(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import _load_skipped_set

        ghost_dir = tmp_path / "renders" / "ghost-mannequin"
        approved_dir = ghost_dir / "approved"
        approved_dir.mkdir(parents=True)
        (ghost_dir / "SKIPPED.json").write_text("[1,2,3]", encoding="utf-8")
        assert _load_skipped_set(approved_dir) == set()

    def test_load_skipped_set_handles_skipped_not_list(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import _load_skipped_set

        ghost_dir = tmp_path / "renders" / "ghost-mannequin"
        approved_dir = ghost_dir / "approved"
        approved_dir.mkdir(parents=True)
        (ghost_dir / "SKIPPED.json").write_text('{"skipped": "not-a-list"}', encoding="utf-8")
        assert _load_skipped_set(approved_dir) == set()

    def test_resolve_root_default_returns_repo_root(self) -> None:
        from skyyrose.elite_studio.upload import _resolve_root

        result = _resolve_root(None)
        assert (result / "skyyrose" / "elite_studio" / "upload.py").is_file()

    def test_build_manifest_returns_empty_when_approved_dir_missing(
        self, tmp_path: Path, patch_catalog_loader: Any
    ) -> None:
        # Catalog exists but renders/ghost-mannequin/approved/ doesn't.
        catalog_path = tmp_path / CATALOG_REL
        catalog_path.parent.mkdir(parents=True)
        catalog_path.write_text("sku,published\nbr-001,1\n", encoding="utf-8")
        patch_catalog_loader(tmp_path)
        manifest = build_manifest(root=tmp_path)
        assert manifest.entries == []
        assert any("no approved/ directory" in s.reason for s in manifest.skipped)

    @pytest.mark.asyncio
    async def test_preview_handles_get_images_exception(self, tmp_path: Path) -> None:
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=tmp_path / "x")],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )

        class FlakyClient(FakeWCClient):
            async def get_product_images(self, product_id):
                raise RuntimeError("simulated image fetch failure")

        client = FlakyClient(sku_to_product={"br-001": 100})
        rows = await preview_manifest(client, manifest)
        # Lookup succeeded; image fetch failed → READY with no current_image_url
        assert rows[0].product_id == 100
        assert rows[0].current_image_url is None
        assert rows[0].status == "READY"

    @pytest.mark.asyncio
    async def test_upload_handles_get_images_exception_during_idempotency_check(
        self, tmp_path: Path
    ) -> None:
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )

        class FlakyClient(FakeWCClient):
            async def get_product_images(self, product_id):
                raise RuntimeError("simulated image fetch failure")

        client = FlakyClient(sku_to_product={"br-001": 100})
        results = await upload_batch(client, manifest)
        assert results[0].status == "FAILED"
        assert "image fetch failed" in results[0].error

    @pytest.mark.asyncio
    async def test_upload_handles_media_response_missing_id(self, tmp_path: Path) -> None:
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )

        class FlakyClient(FakeWCClient):
            async def upload_media(self, file_path, alt_text=""):
                # Return malformed response — missing id
                return {"source_url": "https://cdn.example.com/x.webp"}

        client = FlakyClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 1, "src": "old.jpg"}]},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "FAILED"
        assert "media response missing id" in results[0].error

    @pytest.mark.asyncio
    async def test_upload_handles_verification_get_exception(self, tmp_path: Path) -> None:
        """Post-write GET fails → VERIFICATION_FAILED, not FAILED."""
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )

        class FlakyClient(FakeWCClient):
            def __init__(self, **kw):
                super().__init__(**kw)
                self._get_call_count = 0

            async def get_product_images(self, product_id):
                self._get_call_count += 1
                # First call (idempotency check) succeeds; second (verify) fails.
                if self._get_call_count == 1:
                    return list(self.product_images.get(product_id, []))
                raise RuntimeError("simulated verify GET failure")

        client = FlakyClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 1, "src": "old.jpg"}]},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "VERIFICATION_FAILED"
        assert "verification GET failed" in results[0].error

    def test_append_upload_log_creates_new_file(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import append_upload_log

        results = [
            UploadResult(
                sku="br-001",
                product_id=100,
                media_id=500,
                source_url="https://cdn.example.com/br-001.webp",
                status="UPLOADED",
                verified=True,
                error=None,
            )
        ]
        log_path = append_upload_log(results, root=tmp_path)
        assert log_path.exists()
        data = json.loads(log_path.read_text())
        assert len(data) == 1
        assert data[0]["sku"] == "br-001"
        assert data[0]["status"] == "UPLOADED"

    def test_append_upload_log_appends_to_existing(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import append_upload_log

        # Seed an existing log.
        ghost_dir = tmp_path / "renders" / "ghost-mannequin"
        ghost_dir.mkdir(parents=True)
        log_path = ghost_dir / "upload_log.json"
        log_path.write_text(json.dumps([{"sku": "br-000", "status": "OLD"}]), encoding="utf-8")

        results = [
            UploadResult(
                sku="br-001",
                product_id=100,
                media_id=500,
                source_url=None,
                status="FAILED",
                verified=False,
                error="x",
            )
        ]
        append_upload_log(results, root=tmp_path)
        data = json.loads(log_path.read_text())
        assert len(data) == 2
        assert data[0]["sku"] == "br-000"
        assert data[1]["sku"] == "br-001"

    def test_append_upload_log_handles_corrupted_existing_log(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import append_upload_log

        ghost_dir = tmp_path / "renders" / "ghost-mannequin"
        ghost_dir.mkdir(parents=True)
        log_path = ghost_dir / "upload_log.json"
        log_path.write_text("{not json", encoding="utf-8")

        results = [
            UploadResult(
                sku="br-001",
                product_id=100,
                media_id=500,
                source_url=None,
                status="UPLOADED",
                verified=True,
                error=None,
            )
        ]
        append_upload_log(results, root=tmp_path)
        # Corrupt log was treated as empty; new write replaces it.
        data = json.loads(log_path.read_text())
        assert len(data) == 1

    def test_format_manifest_table_truncates_long_url(self, tmp_path: Path) -> None:
        rows = [
            PreviewRow(
                sku="br-001",
                source_path=tmp_path / "x",
                product_id=100,
                current_image_url="https://cdn.example.com/" + ("y" * 100),
                status="READY",
            )
        ]
        out = format_manifest_table(rows)
        assert "..." in out  # truncation marker present


# ─────────────────────────── TestSecurityHardening ───────────────────────────


class TestSecurityHardening:
    """Tests for the post-review HIGH/MEDIUM/LOW fixes."""

    # HIGH-2a — SKU regex validation in build_manifest
    @pytest.mark.parametrize(
        "bad_sku",
        ["../../../etc/passwd", "br_001", "BR-001", "br-1", "br-12345", "br-001\x00"],
    )
    def test_build_manifest_rejects_invalid_sku_format(
        self, tmp_path: Path, patch_catalog_loader: Any, bad_sku: str
    ) -> None:
        # Add a malformed row to the CSV.
        catalog_path = tmp_path / CATALOG_REL
        catalog_path.parent.mkdir(parents=True)
        catalog_path.write_text(
            f'sku,published\nbr-001,1\n"{bad_sku}",1\n',
            encoding="utf-8",
        )
        approved_dir = tmp_path / APPROVED_REL
        approved_dir.mkdir(parents=True)
        (approved_dir / "br-001-ghost-front.webp").write_bytes(b"x")
        patch_catalog_loader(tmp_path)
        manifest = build_manifest(root=tmp_path)
        assert [e.sku for e in manifest.entries] == ["br-001"]
        # Bad SKU appears in skipped with the "invalid SKU format" reason.
        assert any(s.sku == bad_sku and "invalid SKU format" in s.reason for s in manifest.skipped)

    # MEDIUM-1 — symlink rejection in _upload_one
    @pytest.mark.asyncio
    async def test_upload_rejects_symlink_source(self, tmp_path: Path) -> None:
        real_target = tmp_path / "real.webp"
        real_target.write_bytes(b"x")
        link = _approved_path(tmp_path, "br-001")
        link.symlink_to(real_target)
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=link)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 1, "src": "old.jpg"}]},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "FAILED"
        assert "symlink" in results[0].error.lower()

    # MEDIUM-2 — credential scrubbing
    def test_scrub_credentials_redacts_consumer_secret(self) -> None:
        from skyyrose.elite_studio.upload import _scrub_credentials

        body = "error: consumer_secret=cs_abc123def456 not authorized"
        scrubbed = _scrub_credentials(body)
        assert "cs_abc123def456" not in scrubbed
        assert "consumer_secret=***" in scrubbed

    def test_scrub_credentials_redacts_multiple_token_types(self) -> None:
        from skyyrose.elite_studio.upload import _scrub_credentials

        body = "Authorization: Bearer eyJhbGciOiJIUzI1 password=hunter2"
        scrubbed = _scrub_credentials(body)
        assert "eyJhbGciOiJIUzI1" not in scrubbed
        assert "hunter2" not in scrubbed

    def test_scrub_credentials_passthrough_for_safe_text(self) -> None:
        from skyyrose.elite_studio.upload import _scrub_credentials

        body = "Product 12345 not found in WC media library"
        assert _scrub_credentials(body) == body

    # MEDIUM-3 — site_url validation
    def test_validate_site_url_rejects_empty(self) -> None:
        from skyyrose.elite_studio.upload import UploadError, _validate_site_url

        with pytest.raises(UploadError, match="empty"):
            _validate_site_url("")

    def test_validate_site_url_rejects_http_scheme(self) -> None:
        from skyyrose.elite_studio.upload import UploadError, _validate_site_url

        with pytest.raises(UploadError, match="https"):
            _validate_site_url("http://skyyrose.co")

    def test_validate_site_url_rejects_unknown_host(self) -> None:
        from skyyrose.elite_studio.upload import UploadError, _validate_site_url

        with pytest.raises(UploadError, match="not in allowlist"):
            _validate_site_url("https://attacker.example.com")

    def test_validate_site_url_accepts_production_host(self) -> None:
        from skyyrose.elite_studio.upload import _validate_site_url

        _validate_site_url("https://skyyrose.co")  # no raise
        _validate_site_url("https://www.skyyrose.co")
        _validate_site_url("https://public-api.wordpress.com")

    def test_validate_site_url_honors_env_allowlist_extension(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from skyyrose.elite_studio.upload import _validate_site_url

        monkeypatch.setenv("SKYYROSE_SITE_URL_ALLOWLIST", "staging.skyyrose.co,dev.local")
        _validate_site_url("https://staging.skyyrose.co")
        _validate_site_url("https://dev.local")

    # LOW-2 — path-aware basename match (not substring) for idempotency
    @pytest.mark.asyncio
    async def test_already_synced_requires_basename_at_path_end_not_substring(
        self, tmp_path: Path
    ) -> None:
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={
                100: [
                    {
                        "id": 99,
                        "src": "https://attacker.example.com/br-001-ghost-front.webp-suffix",
                    }
                ]
            },
        )
        results = await upload_batch(client, manifest)
        # Trailing "-suffix" makes the URL path basename "br-001-ghost-front.webp-suffix",
        # which is NOT equal to expected → upload proceeds.
        assert results[0].status == "UPLOADED"

    # Idempotency must survive a cache-busting query string (?v=N)
    @pytest.mark.asyncio
    async def test_already_synced_ignores_cache_bust_query_string(self, tmp_path: Path) -> None:
        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=src)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={
                100: [
                    {
                        "id": 99,
                        "src": "https://cdn.example.com/br-001-ghost-front.webp?v=2&ts=1234",
                    }
                ]
            },
        )
        results = await upload_batch(client, manifest)
        # Query string stripped → URL path basename equals expected → no upload.
        assert results[0].status == "ALREADY_SYNCED"
        assert not any(c[0] == "upload_media" for c in client.calls)

    # Containment check fires when source resolves outside approved/
    @pytest.mark.asyncio
    async def test_upload_rejects_source_resolving_outside_approved_dir(
        self, tmp_path: Path
    ) -> None:
        approved = tmp_path / "renders" / "ghost-mannequin" / "approved"
        approved.mkdir(parents=True)
        # Real file is placed in approved/'s parent (ghost-mannequin/), NOT in
        # approved/. The crafted path uses ../ so the lexical .parent looks
        # like approved/ but resolve() escapes it.
        sneaky_target = tmp_path / "renders" / "ghost-mannequin" / "outside.webp"
        sneaky_target.write_bytes(b"x")
        attacker = approved / ".." / "outside.webp"

        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=attacker)],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={100: [{"id": 1, "src": "old.jpg"}]},
        )
        results = await upload_batch(client, manifest)
        assert results[0].status == "FAILED"
        assert "not inside renders/ghost-mannequin/approved/" in results[0].error

    # _validate_site_url hardening
    def test_validate_site_url_rejects_embedded_credentials(self) -> None:
        from skyyrose.elite_studio.upload import UploadError, _validate_site_url

        with pytest.raises(UploadError, match="credentials"):
            _validate_site_url("https://user:pass@skyyrose.co")

    def test_validate_site_url_rejects_explicit_port(self) -> None:
        from skyyrose.elite_studio.upload import UploadError, _validate_site_url

        with pytest.raises(UploadError, match="port"):
            _validate_site_url("https://skyyrose.co:8443")

    def test_validate_site_url_normalizes_host_case(self) -> None:
        from skyyrose.elite_studio.upload import _validate_site_url

        # Uppercase host accepted via case-normalized comparison.
        _validate_site_url("https://SkyyRose.CO")

    # preview_manifest must use the same path-aware match
    @pytest.mark.asyncio
    async def test_preview_ignores_cache_bust_query_string(self, tmp_path: Path) -> None:
        manifest = UploadManifest(
            entries=[UploadEntry(sku="br-001", source_path=_approved_path(tmp_path, "br-001"))],
            skipped=[],
            generated_at="2026-05-19T00:00:00+00:00",
        )
        client = FakeWCClient(
            sku_to_product={"br-001": 100},
            product_images={
                100: [
                    {
                        "id": 99,
                        "src": "https://cdn.example.com/br-001-ghost-front.webp?v=2",
                    }
                ]
            },
        )
        rows = await preview_manifest(client, manifest)
        assert rows[0].status == "ALREADY_SYNCED"

    # _validate_source helper (extracted from _upload_one)
    def test_validate_source_passes_real_file(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import _validate_source

        src = _approved_path(tmp_path, "br-001")
        src.write_bytes(b"x")
        entry = UploadEntry(sku="br-001", source_path=src)
        assert _validate_source(entry, product_id=100) is None

    def test_validate_source_rejects_missing(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import _validate_source

        entry = UploadEntry(sku="br-001", source_path=tmp_path / "gone.webp")
        result = _validate_source(entry, product_id=100)
        assert result is not None
        assert result.status == "FAILED"
        assert "vanished" in result.error

    def test_image_basename_matches_exact(self) -> None:
        from skyyrose.elite_studio.upload import _image_basename_matches

        assert _image_basename_matches(
            "https://cdn.example.com/br-001-ghost-front.webp", "br-001-ghost-front.webp"
        )
        assert not _image_basename_matches("", "br-001-ghost-front.webp")
        assert not _image_basename_matches(
            "https://cdn.example.com/other.webp", "br-001-ghost-front.webp"
        )

    # Adapter timing: _validate_site_url MUST run in __aenter__ before any
    # network call. Verified by constructing WooCommerceUploader with a
    # fake config that fails the allowlist; entering the context must raise.
    @pytest.mark.asyncio
    async def test_wc_uploader_validates_site_url_at_aenter_before_network(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from skyyrose.elite_studio.upload import UploadError, WooCommerceUploader

        # Build a sham WooCommerceConfig that bypasses env loading.
        class FakeConfig:
            site_url = "https://attacker.example.com"
            consumer_key = "ck_should_never_be_sent"
            consumer_secret = "cs_should_never_be_sent"

            @classmethod
            def from_env(cls):
                return cls()

        # Replace the import inside WooCommerceUploader.__init__ so we never
        # actually touch wordpress.products / aiohttp.
        import sys
        import types

        fake_wp_products = types.ModuleType("wordpress.products")
        fake_wp_products.WooCommerceConfig = FakeConfig

        class FakeProducts:
            def __init__(self, *a, **kw):
                raise AssertionError(
                    "WooCommerceProducts must not be constructed when validation fails"
                )

        fake_wp_products.WooCommerceProducts = FakeProducts
        monkeypatch.setitem(sys.modules, "wordpress.products", fake_wp_products)

        # Construct the uploader (deferred import + config.from_env both work).
        uploader = WooCommerceUploader()

        # __aenter__ must raise UploadError BEFORE any network or aiohttp import.
        with pytest.raises(UploadError, match="not in allowlist"):
            await uploader.__aenter__()

    # build_manifest classifier extraction — verify _classify_sku is pure
    def test_classify_sku_returns_upload_entry_for_eligible(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import _classify_sku

        approved_dir = tmp_path / "approved"
        approved_dir.mkdir()
        (approved_dir / "br-001-ghost-front.webp").write_bytes(b"x")
        row = {"sku": "br-001", "published": "1"}
        result = _classify_sku("br-001", row, approved_dir, set())
        assert isinstance(result, UploadEntry)
        assert result.sku == "br-001"

    def test_classify_sku_returns_skipped_for_unpublished(self, tmp_path: Path) -> None:
        from skyyrose.elite_studio.upload import SkippedEntry as SE
        from skyyrose.elite_studio.upload import _classify_sku

        approved_dir = tmp_path / "approved"
        approved_dir.mkdir()
        (approved_dir / "br-001-ghost-front.webp").write_bytes(b"x")
        row = {"sku": "br-001", "published": "0"}
        result = _classify_sku("br-001", row, approved_dir, set())
        assert isinstance(result, SE)
        assert "published" in result.reason

    # _resolve_product_id extraction
    @pytest.mark.asyncio
    async def test_resolve_product_id_returns_pid_on_success(self) -> None:
        from skyyrose.elite_studio.upload import _resolve_product_id

        client = FakeWCClient(sku_to_product={"br-001": 100})
        pid, fail = await _resolve_product_id(client, "br-001")
        assert pid == 100 and fail is None

    @pytest.mark.asyncio
    async def test_resolve_product_id_returns_not_found_on_missing(self) -> None:
        from skyyrose.elite_studio.upload import _resolve_product_id

        client = FakeWCClient(sku_to_product={})
        pid, fail = await _resolve_product_id(client, "xx-999")
        assert pid is None
        assert fail is not None
        assert fail.status == "PRODUCT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_resolve_product_id_returns_failed_on_exception(self) -> None:
        from skyyrose.elite_studio.upload import _resolve_product_id

        client = FakeWCClient(lookup_failures={"br-001"})
        pid, fail = await _resolve_product_id(client, "br-001")
        assert pid is None
        assert fail is not None
        assert fail.status == "FAILED"
        assert "sku lookup failed" in fail.error
