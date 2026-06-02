"""Tests for scripts/stage_review.py — the render -> review-queue bridge.

Mirrors tests/test_review.py: each test builds an isolated repo skeleton under
tmp_path and passes root= so nothing touches the real tree. The script is loaded
via importlib because scripts/ is not an importable package.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
# scripts/ is not a package; put it on the path so the CLI module imports by name
# (keeps coverage --cov=stage_review straightforward).
_SCRIPTS_DIR = str(REPO_ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import stage_review as sr  # noqa: E402

ReviewError = sr.ReviewError


# --------------------------------------------------------------------------- fixtures


def _png(path: Path, *, color=(10, 20, 30), size=(8, 8)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, "PNG")


def _repo(tmp_path: Path) -> Path:
    (tmp_path / "assets" / "product-source").mkdir(parents=True)
    (tmp_path / "renders" / "ghost-mannequin").mkdir(parents=True)
    return tmp_path


def _add_sku(tmp_path: Path, sku: str, slug: str, renders=("seedream-probe.png",)) -> Path:
    render_dir = tmp_path / "assets" / "product-source" / f"{sku}__{slug}" / "renders"
    for name in renders:
        _png(render_dir / name)
    return render_dir


def _skipped_json(tmp_path: Path, skus: list[str]) -> None:
    import json

    path = tmp_path / "renders" / "ghost-mannequin" / "SKIPPED.json"
    path.write_text(
        json.dumps({"skipped": [{"sku": s, "name": s, "collection": "x"} for s in skus]}),
        encoding="utf-8",
    )


def _review_file(tmp_path: Path, sku: str) -> Path:
    return tmp_path / "renders" / "ghost-mannequin" / f"{sku}-ghost-front.webp"


def _approved_file(tmp_path: Path, sku: str) -> Path:
    return tmp_path / "renders" / "ghost-mannequin" / "approved" / f"{sku}-ghost-front.webp"


# ------------------------------------------------------------------------ stage_one


@pytest.mark.unit
def test_stage_one_converts_png_to_webp(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")

    result = sr.stage_one("br-001", root=repo)

    assert result.status == "staged"
    dst = _review_file(repo, "br-001")
    assert dst.is_file()
    with Image.open(dst) as im:
        assert im.format == "WEBP"


@pytest.mark.unit
def test_stage_one_is_idempotent_without_force(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")
    sr.stage_one("br-001", root=repo)

    second = sr.stage_one("br-001", root=repo)
    assert second.status == "exists"


@pytest.mark.unit
def test_force_overwrites_existing_review_file(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")
    sr.stage_one("br-001", root=repo)

    forced = sr.stage_one("br-001", root=repo, force=True)
    assert forced.status == "staged"


@pytest.mark.unit
def test_already_approved_short_circuits(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")
    approved = _approved_file(repo, "br-001")
    approved.parent.mkdir(parents=True, exist_ok=True)
    approved.write_bytes(b"already")

    result = sr.stage_one("br-001", root=repo)
    assert result.status == "already-approved"
    assert not _review_file(repo, "br-001").exists()


@pytest.mark.unit
def test_skip_list_honored(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "lh-005", "the-fannie")
    _skipped_json(repo, ["lh-005"])

    result = sr.stage_one("lh-005", root=repo)
    assert result.status == "skipped"
    assert not _review_file(repo, "lh-005").exists()


@pytest.mark.unit
def test_multi_variant_picks_highest_version(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(
        repo,
        "lh-004",
        "love-hurts-bomber-jacket",
        renders=(
            "seedream-probe.png",
            "seedream-probe-v2-hollow.png",
            "seedream-probe-v3-styleref.png",
            "seedream-probe-v4-clean.png",
        ),
    )

    result = sr.stage_one("lh-004", root=repo)
    assert result.status == "staged"
    assert result.src.name == "seedream-probe-v4-clean.png"


@pytest.mark.unit
def test_render_override_selects_named_file(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(
        repo,
        "lh-004",
        "love-hurts-bomber-jacket",
        renders=("seedream-probe.png", "seedream-probe-v4-clean.png"),
    )

    result = sr.stage_one("lh-004", root=repo, render="seedream-probe.png")
    assert result.src.name == "seedream-probe.png"


@pytest.mark.unit
def test_override_missing_file_is_error(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")

    result = sr.stage_one("br-001", root=repo, render="does-not-exist.png")
    assert result.status == "error"


@pytest.mark.unit
def test_invalid_sku_raises(tmp_path):
    repo = _repo(tmp_path)
    with pytest.raises(ReviewError):
        sr.stage_one("../etc/passwd", root=repo)


@pytest.mark.unit
def test_no_source_folder_is_error_not_raise(tmp_path):
    repo = _repo(tmp_path)
    result = sr.stage_one("br-099", root=repo)
    assert result.status == "error"
    assert "no product-source folder" in result.detail


@pytest.mark.unit
def test_dry_run_writes_nothing(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")

    result = sr.stage_one("br-001", root=repo, dry_run=True)
    assert result.status == "would-stage"
    assert not _review_file(repo, "br-001").exists()


# ---------------------------------------------------------------------- discovery


@pytest.mark.unit
def test_discover_skus_ignores_non_sku_folders(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")
    _add_sku(repo, "kids-001", "kids-colorblock-hoodie")
    # a non-SKU directory that must be ignored
    (repo / "assets" / "product-source" / "_style-reference").mkdir(parents=True)

    skus = sr.discover_skus(repo)
    assert skus == ["br-001", "kids-001"]


@pytest.mark.unit
def test_ambiguous_folder_is_error(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "slug-one")
    _add_sku(repo, "br-001", "slug-two")

    result = sr.stage_one("br-001", root=repo)
    assert result.status == "error"
    assert "ambiguous" in result.detail


# ------------------------------------------------------------------------ stage_all


@pytest.mark.unit
def test_stage_all_stages_ready_and_skips_others(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")
    _add_sku(repo, "br-002", "black-rose-joggers")
    _add_sku(repo, "lh-005", "the-fannie")
    _skipped_json(repo, ["lh-005"])
    # br-002 already approved -> should short-circuit
    appr = _approved_file(repo, "br-002")
    appr.parent.mkdir(parents=True, exist_ok=True)
    appr.write_bytes(b"x")

    results = {r.sku: r.status for r in sr.stage_all(root=repo)}
    assert results["br-001"] == "staged"
    assert results["br-002"] == "already-approved"
    assert results["lh-005"] == "skipped"


# ------------------------------------------------------------------------------ CLI


@pytest.mark.unit
def test_cli_single_sku_live(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")

    code = sr.main(["br-001", "--root", str(repo)])
    assert code == 0
    assert _review_file(repo, "br-001").is_file()


@pytest.mark.unit
def test_cli_all_dry_run(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "black-rose-crewneck")

    code = sr.main(["--all", "--dry-run", "--root", str(repo)])
    assert code == 0
    assert not _review_file(repo, "br-001").exists()


@pytest.mark.unit
def test_cli_rejects_sku_and_all_together(tmp_path):
    with pytest.raises(SystemExit) as exc:
        sr.main(["br-001", "--all"])
    assert exc.value.code == 2


@pytest.mark.unit
def test_cli_requires_sku_or_all(tmp_path):
    with pytest.raises(SystemExit) as exc:
        sr.main([])
    assert exc.value.code == 2


@pytest.mark.unit
def test_cli_failure_exit_code(tmp_path):
    repo = _repo(tmp_path)
    # SKU valid but no source folder -> failure -> exit 1
    code = sr.main(["br-099", "--root", str(repo)])
    assert code == 1


@pytest.mark.unit
def test_load_skipped_tolerates_malformed_json(tmp_path):
    repo = _repo(tmp_path)
    (repo / "renders" / "ghost-mannequin" / "SKIPPED.json").write_text(
        "{not json", encoding="utf-8"
    )
    assert sr.load_skipped(repo) == set()


@pytest.mark.unit
def test_stage_result_ok_property():
    assert sr.StageResult("br-001", "staged", None, None, "").ok is True
    assert sr.StageResult("br-001", "error", None, None, "").ok is False


@pytest.mark.unit
def test_cli_all_no_folders_reports_nothing(tmp_path, capsys):
    repo = _repo(tmp_path)
    code = sr.main(["--all", "--root", str(repo)])
    assert code == 0
    assert "no SKUs to stage" in capsys.readouterr().out


@pytest.mark.unit
def test_cli_all_reports_per_sku_failure(tmp_path):
    repo = _repo(tmp_path)
    # ambiguous: two folders for one SKU -> genuine error -> exit 1
    _add_sku(repo, "br-001", "slug-a")
    _add_sku(repo, "br-001", "slug-b")
    code = sr.main(["--all", "--root", str(repo)])
    assert code == 1


@pytest.mark.unit
def test_render_override_rejected_with_all(tmp_path):
    with pytest.raises(SystemExit) as exc:
        sr.main(["--all", "--render", "x.png"])
    assert exc.value.code == 2


@pytest.mark.unit
def test_no_render_is_soft_skip_not_error(tmp_path):
    repo = _repo(tmp_path)
    # folder present but renders/ empty -> precondition not met, not a failure
    (repo / "assets" / "product-source" / "br-001__slug" / "renders").mkdir(parents=True)
    result = sr.stage_one("br-001", root=repo)
    assert result.status == "no-render"
    assert not _review_file(repo, "br-001").exists()


@pytest.mark.unit
def test_cli_all_with_unrendered_exits_zero(tmp_path):
    repo = _repo(tmp_path)
    _add_sku(repo, "br-001", "ready")
    (repo / "assets" / "product-source" / "br-002__pending" / "renders").mkdir(parents=True)
    code = sr.main(["--all", "--root", str(repo)])
    assert code == 0  # one staged, one not-yet-rendered — batch still succeeds
    assert _review_file(repo, "br-001").is_file()
