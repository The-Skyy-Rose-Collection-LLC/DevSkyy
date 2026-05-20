"""Phase 17 — review CLI tests (REV-01..04).

Uses tmp_path fixture to build an isolated repo skeleton per test:

    {tmp}/wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv
    {tmp}/renders/ghost-mannequin/{sku}-ghost-front.webp
    {tmp}/renders/ghost-mannequin/approved/   (created by approve())
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from skyyrose.core.review import (
    APPROVALS_JSON,
    APPROVED_SUBDIR,
    FRONT_MODEL_COL,
    GHOST_FILENAME_FMT,
    REJECTIONS_JSON,
    ReviewError,
    approve,
    atomic_csv_write,
    reject,
)

CATALOG_REL = Path("wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv")
GHOST_REL = Path("renders/ghost-mannequin")

REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVE_CLI = REPO_ROOT / "scripts" / "approve_ghost.py"
REJECT_CLI = REPO_ROOT / "scripts" / "reject_ghost.py"


def _make_fake_repo(tmp_path: Path, skus: list[str]) -> Path:
    """Build a minimal repo skeleton with catalog + ghost dir + image files."""
    catalog_path = tmp_path / CATALOG_REL
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "sku",
        "name",
        "price",
        "collection",
        "front_model_image",
        "back_model_image",
        "published",
    ]
    rows = [
        {
            "sku": sku,
            "name": f"Test {sku}",
            "price": "100",
            "collection": "test",
            "front_model_image": f"assets/images/products/{sku}-front.webp",
            "back_model_image": f"assets/images/products/{sku}-back.webp",
            "published": "1",
        }
        for sku in skus
    ]
    with catalog_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    ghost_dir = tmp_path / GHOST_REL
    ghost_dir.mkdir(parents=True, exist_ok=True)
    for sku in skus:
        (ghost_dir / GHOST_FILENAME_FMT.format(sku=sku)).write_bytes(
            b"WEBP_PLACEHOLDER_" + sku.encode()
        )
    return tmp_path


def _read_rows(catalog_path: Path) -> list[dict]:
    with catalog_path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _row_for(rows: list[dict], sku: str) -> dict:
    matches = [r for r in rows if r["sku"] == sku]
    assert len(matches) == 1, f"expected exactly 1 row for {sku}, got {len(matches)}"
    return matches[0]


# ─────────────────────────── REV-01: approve happy path ───────────────────────────


class TestApprove:
    def test_moves_file_into_approved_dir(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001", "sg-001"])
        src = root / GHOST_REL / "br-001-ghost-front.webp"
        approved_dst = root / GHOST_REL / APPROVED_SUBDIR / "br-001-ghost-front.webp"
        assert src.exists() and not approved_dst.exists()

        approve("br-001", root=root)

        assert approved_dst.exists()
        assert not src.exists()
        assert approved_dst.read_bytes() == b"WEBP_PLACEHOLDER_br-001"

    def test_updates_front_model_image_column(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        approve("br-001", root=root)
        row = _row_for(_read_rows(root / CATALOG_REL), "br-001")
        assert row[FRONT_MODEL_COL] == ("renders/ghost-mannequin/approved/br-001-ghost-front.webp")

    def test_preserves_csv_row_count(self, tmp_path: Path) -> None:
        skus = ["br-001", "sg-001", "lh-001"]
        root = _make_fake_repo(tmp_path, skus)
        before = _read_rows(root / CATALOG_REL)
        approve("br-001", root=root)
        after = _read_rows(root / CATALOG_REL)
        assert len(before) == len(after) == 3

    def test_preserves_other_rows_untouched(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001", "sg-001"])
        approve("br-001", root=root)
        sg_row = _row_for(_read_rows(root / CATALOG_REL), "sg-001")
        assert sg_row[FRONT_MODEL_COL] == "assets/images/products/sg-001-front.webp"

    def test_writes_approval_timestamp_log(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        result = approve("br-001", root=root)
        approvals_path = root / GHOST_REL / APPROVALS_JSON
        assert approvals_path.exists()
        entries = json.loads(approvals_path.read_text())
        assert len(entries) == 1
        assert entries[0]["sku"] == "br-001"
        assert entries[0]["timestamp"] == result.timestamp

    def test_returns_approval_result_struct(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        result = approve("br-001", root=root)
        assert result.sku == "br-001"
        assert result.approved_path.name == "br-001-ghost-front.webp"
        assert result.csv_path.name == "skyyrose-catalog.csv"
        assert "T" in result.timestamp  # ISO-8601 marker


# ─────────────────────────── REV-02: structural gate ──────────────────────────────


class TestApproveStructuralGate:
    def test_missing_review_file_raises_no_csv_change(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        (root / GHOST_REL / "br-001-ghost-front.webp").unlink()
        catalog_before = (root / CATALOG_REL).read_bytes()

        with pytest.raises(ReviewError, match="no review file"):
            approve("br-001", root=root)

        assert (root / CATALOG_REL).read_bytes() == catalog_before

    def test_sku_not_in_catalog_rolls_back_file_move(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["sg-001"])
        # Add a stray review file for a SKU not in the catalog.
        stray = root / GHOST_REL / "xx-999-ghost-front.webp"
        stray.write_bytes(b"STRAY")
        catalog_before = (root / CATALOG_REL).read_bytes()

        with pytest.raises(ReviewError, match="not in catalog"):
            approve("xx-999", root=root)

        # File must remain in the review dir (rollback semantics).
        assert stray.exists()
        assert (root / CATALOG_REL).read_bytes() == catalog_before

    def test_already_approved_rejects_second_approval(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        approve("br-001", root=root)
        # Put another review file in place to simulate a re-render.
        src = root / GHOST_REL / "br-001-ghost-front.webp"
        src.write_bytes(b"RE_RENDER")
        with pytest.raises(ReviewError, match="already approved"):
            approve("br-001", root=root)

    def test_cli_exit_code_1_on_missing_file(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        (root / GHOST_REL / "br-001-ghost-front.webp").unlink()
        result = subprocess.run(
            [sys.executable, str(APPROVE_CLI), "br-001", "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 1
        assert "no review file" in result.stderr


# ─────────────────────────── REV-03: reject path ──────────────────────────────────


class TestReject:
    def test_writes_rejection_entry(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        result = reject("br-001", "wrong color", root=root)
        rejections_path = root / GHOST_REL / REJECTIONS_JSON
        entries = json.loads(rejections_path.read_text())
        assert len(entries) == 1
        assert entries[0]["sku"] == "br-001"
        assert entries[0]["reason"] == "wrong color"
        assert entries[0]["timestamp"] == result.timestamp

    def test_leaves_file_in_review_dir(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        src = root / GHOST_REL / "br-001-ghost-front.webp"
        reject("br-001", "bad alignment", root=root)
        assert src.exists()
        assert src.read_bytes() == b"WEBP_PLACEHOLDER_br-001"

    def test_makes_no_csv_change(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        before = (root / CATALOG_REL).read_bytes()
        reject("br-001", "blurry", root=root)
        assert (root / CATALOG_REL).read_bytes() == before

    def test_empty_reason_raises(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        with pytest.raises(ReviewError, match="reason is required"):
            reject("br-001", "   ", root=root)

    def test_appends_multiple_rejections(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        reject("br-001", "first try blurry", root=root)
        reject("br-001", "second try wrong angle", root=root)
        entries = json.loads((root / GHOST_REL / REJECTIONS_JSON).read_text())
        assert [e["reason"] for e in entries] == [
            "first try blurry",
            "second try wrong angle",
        ]

    def test_cli_exit_code_0_on_success(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        result = subprocess.run(
            [sys.executable, str(REJECT_CLI), "br-001", "bad lighting", "--root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0
        assert "rejected: br-001" in result.stdout


# ─────────────────────────── REV-04: atomic write safety ─────────────────────────


class TestAtomicWrite:
    def test_os_replace_keeps_original_on_keyboard_interrupt(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SIGINT after tmp file is written but before os.replace() leaves
        original CSV byte-identical. This is the REV-04 guarantee."""
        root = _make_fake_repo(tmp_path, ["br-001", "sg-001"])
        csv_path = root / CATALOG_REL
        original_bytes = csv_path.read_bytes()

        real_replace = os.replace

        def boom_replace(src, dst):  # type: ignore[no-untyped-def]
            if str(dst).endswith("skyyrose-catalog.csv"):
                raise KeyboardInterrupt("simulated SIGINT mid-write")
            return real_replace(src, dst)

        monkeypatch.setattr("skyyrose.core.review.os.replace", boom_replace)

        with pytest.raises(KeyboardInterrupt):
            approve("br-001", root=root)

        # Original CSV byte-identical (atomicity guarantee).
        assert csv_path.read_bytes() == original_bytes

        # tmp file cleaned up — no .tmp_review_* siblings left behind.
        leftovers = list(csv_path.parent.glob(".tmp_review_*"))
        assert leftovers == [], f"tmp leftovers: {leftovers}"

    def test_atomic_csv_write_round_trip(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "data.csv"
        fieldnames = ["sku", "name", "front_model_image"]
        rows = [
            {"sku": "a-1", "name": "A", "front_model_image": "old/a.webp"},
            {"sku": "b-2", "name": "B", "front_model_image": "old/b.webp"},
        ]
        atomic_csv_write(rows, fieldnames, csv_path)
        roundtrip = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        assert roundtrip == rows

    def test_atomic_csv_write_overwrites_existing(self, tmp_path: Path) -> None:
        csv_path = tmp_path / "data.csv"
        csv_path.write_text("garbage,that,must,be,replaced\n", encoding="utf-8")
        fieldnames = ["sku", "front_model_image"]
        rows = [{"sku": "z-9", "front_model_image": "new/z.webp"}]
        atomic_csv_write(rows, fieldnames, csv_path)
        roundtrip = list(csv.DictReader(csv_path.open(encoding="utf-8")))
        assert roundtrip == rows


# ─────────────────────────── SKU allowlist (path-traversal defense) ──────────────


class TestSkuValidation:
    """HIGH-1 fix — sku is interpolated into paths AND into the CSV's
    front_model_image column. Untrusted shapes must be rejected before any
    filesystem or catalog operation runs."""

    @pytest.mark.parametrize(
        "bad_sku",
        [
            "../../../etc/passwd",
            "/etc/passwd",
            "br-001/../../sg-001",
            "br-001;rm -rf",
            "BR-001",  # uppercase rejected
            "br_001",  # underscore rejected
            "br-1",  # too few digits
            "br-12345",  # too many digits
            "b-001",  # too few letters
            "brrr-001",  # too many letters
            "",  # empty
            " br-001",  # leading whitespace
            "br-001\n",  # trailing newline
        ],
    )
    def test_approve_rejects_invalid_sku_shape(self, tmp_path: Path, bad_sku: str) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        catalog_before = (root / CATALOG_REL).read_bytes()
        with pytest.raises(ReviewError):
            approve(bad_sku, root=root)
        # CSV untouched; no file move attempted.
        assert (root / CATALOG_REL).read_bytes() == catalog_before

    @pytest.mark.parametrize(
        "bad_sku",
        ["../../foo", "/abs/path", "BR-001", "", "br-001\x00"],
    )
    def test_reject_rejects_invalid_sku_shape(self, tmp_path: Path, bad_sku: str) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        with pytest.raises(ReviewError):
            reject(bad_sku, "reason", root=root)
        rejections_path = root / GHOST_REL / REJECTIONS_JSON
        assert not rejections_path.exists()

    @pytest.mark.parametrize(
        "good_sku",
        ["br-001", "sg-005", "lh-005", "br-015", "sg-014", "kids-001", "kids-002"],
    )
    def test_accepts_real_catalog_sku_shapes(self, tmp_path: Path, good_sku: str) -> None:
        root = _make_fake_repo(tmp_path, [good_sku])
        approve(good_sku, root=root)
        assert (root / GHOST_REL / APPROVED_SUBDIR / f"{good_sku}-ghost-front.webp").exists()


# ─────────────────────────── Audit log failure modes ─────────────────────────────


class TestAuditLogFailureModes:
    """MEDIUM-2/3 fixes — the commit (file move + CSV) is on disk before the
    log writes. Log failure must NOT propagate; corrupted log must surface a
    clear ReviewError, not an opaque JSONDecodeError."""

    def test_corrupted_approvals_json_raises_clean_review_error(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        approvals_path = root / GHOST_REL / APPROVALS_JSON
        approvals_path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(ReviewError, match="audit log corrupted"):
            approve("br-001", root=root)

    def test_audit_log_write_failure_does_not_propagate(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """If approvals.json can't be written, the commit is still real and
        approve() must return ApprovalResult instead of raising."""
        root = _make_fake_repo(tmp_path, ["br-001"])

        real_atomic_json = None
        from skyyrose.core import review as review_mod

        real_atomic_json = review_mod._atomic_json_write

        def explode(records, json_path):  # type: ignore[no-untyped-def]
            raise OSError("simulated disk full on audit log")

        monkeypatch.setattr(review_mod, "_atomic_json_write", explode)

        with caplog.at_level("WARNING"):
            result = approve("br-001", root=root)

        # Commit succeeded — file moved + CSV updated — despite log failure.
        assert result.sku == "br-001"
        assert (root / GHOST_REL / APPROVED_SUBDIR / "br-001-ghost-front.webp").exists()
        row = _row_for(_read_rows(root / CATALOG_REL), "br-001")
        assert row[FRONT_MODEL_COL].startswith("renders/ghost-mannequin/approved/")
        # Warning was logged.
        assert any("audit log write failed" in r.message for r in caplog.records)
        # Restore so test isolation holds.
        monkeypatch.setattr(review_mod, "_atomic_json_write", real_atomic_json)


# ─────────────────────────── Rollback safety ─────────────────────────────────────


class TestCatalogValidation:
    """Coverage for _read_catalog error branches and _load_json_list shape check."""

    def test_missing_catalog_file_raises(self, tmp_path: Path) -> None:
        from skyyrose.core.review import _read_catalog

        with pytest.raises(ReviewError, match="catalog not found"):
            _read_catalog(tmp_path / "does-not-exist.csv")

    def test_catalog_missing_required_column_raises(self, tmp_path: Path) -> None:
        from skyyrose.core.review import _read_catalog

        bad = tmp_path / "bad.csv"
        bad.write_text("sku,name\nbr-001,A\n", encoding="utf-8")
        with pytest.raises(ReviewError, match="missing required column"):
            _read_catalog(bad)

    def test_catalog_empty_file_no_header_raises(self, tmp_path: Path) -> None:
        from skyyrose.core.review import _read_catalog

        empty = tmp_path / "empty.csv"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(ReviewError, match="no header row"):
            _read_catalog(empty)

    def test_load_json_list_rejects_non_list_shape(self, tmp_path: Path) -> None:
        from skyyrose.core.review import _load_json_list

        path = tmp_path / "log.json"
        path.write_text('{"not": "a list"}', encoding="utf-8")
        with pytest.raises(ReviewError, match="not a JSON list"):
            _load_json_list(path)

    def test_reject_missing_review_file_raises(self, tmp_path: Path) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        (root / GHOST_REL / "br-001-ghost-front.webp").unlink()
        with pytest.raises(ReviewError, match="nothing to reject"):
            reject("br-001", "any reason", root=root)

    def test_resolve_root_default_returns_repo_root(self) -> None:
        from skyyrose.core.review import _resolve_root

        result = _resolve_root(None)
        # When root=None, function walks parents[2] from review.py's location.
        # That's REPO_ROOT (skyyrose/core/review.py → parents[0]=core, parents[1]=skyyrose, parents[2]=repo).
        assert (result / "skyyrose" / "core" / "review.py").is_file()


class TestRollbackSafety:
    """MEDIUM-1 fix — if CSV write fails AND the rollback move also fails,
    the original CSV-write error must reach the caller, not the rollback
    error. The user needs to know what actually broke."""

    def test_rollback_failure_does_not_mask_csv_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        root = _make_fake_repo(tmp_path, ["br-001"])
        from skyyrose.core import review as review_mod

        # Make the CSV write fail with a specific OSError.
        def explode_csv(rows, fieldnames, csv_path):  # type: ignore[no-untyped-def]
            raise PermissionError("simulated: cannot write catalog")

        # Make the rollback shutil.move ALSO fail.
        def explode_move(src, dst):  # type: ignore[no-untyped-def]
            raise OSError("simulated: cannot rollback either")

        monkeypatch.setattr(review_mod, "atomic_csv_write", explode_csv)
        # Patch shutil.move INSIDE _safe_rollback_move — the initial move
        # already succeeded by the time we get here.
        original_move = review_mod.shutil.move
        call_count = {"n": 0}

        def conditional_move(src, dst, *a, **kw):  # type: ignore[no-untyped-def]
            call_count["n"] += 1
            if call_count["n"] == 1:
                return original_move(src, dst, *a, **kw)
            raise OSError("simulated: cannot rollback either")

        monkeypatch.setattr(review_mod.shutil, "move", conditional_move)

        with (
            caplog.at_level("WARNING"),
            pytest.raises(PermissionError, match="cannot write catalog"),
        ):
            approve("br-001", root=root)

        # Rollback failure surfaced via log, not by replacing the primary error.
        assert any("rollback move failed" in r.message for r in caplog.records)
