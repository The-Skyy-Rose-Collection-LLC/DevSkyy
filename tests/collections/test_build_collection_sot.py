import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"
ASSETS = ROOT / "wordpress-theme/skyyrose-flagship/assets"
BUILD = DATA / "build-collection-sot.py"


def _run_build(out_dir: Path, *extra: str) -> None:
    """Run the SOT builder, writing ALL output into `out_dir`.

    Every test gets its own pytest `tmp_path`, so the suite never mutates the tracked
    SOT files in the working tree and can't be raced by a concurrent build (the bug that
    produced the 'GENERATED' vs '2026-06-14' flake when a manual build ran alongside the
    background test suite).
    """
    subprocess.run(
        [sys.executable, str(BUILD), "--out-dir", str(out_dir), *extra],
        check=True,
    )


def _sot(out_dir: Path, slug: str) -> dict:
    return json.loads((out_dir / slug / "sot.json").read_text())


def _orphans(out_dir: Path) -> dict:
    return json.loads((out_dir / "_orphans.json").read_text())


def test_build_emits_per_folder_sot_and_orphans(tmp_path):
    _run_build(tmp_path)
    for slug in ["black-rose", "love-hurts", "signature", "kids-capsule"]:
        sot = _sot(tmp_path, slug)
        assert sot["collection"] == slug
        assert "products" in sot and "imagery" in sot and "lockup" in sot
        assert "story" in sot and "palette" in sot and "fonts" in sot
        assert "other_collection_files" not in sot  # retired
        for p in sot["products"]:
            for _col, im in p.get("images", {}).items():
                if im.get("resolved"):
                    assert (ASSETS / im["resolved"]).is_file()
    assert isinstance(_orphans(tmp_path)["orphans"], list)


def test_registered_expands_format_siblings(tmp_path):
    _run_build(tmp_path)
    orph = set(_orphans(tmp_path)["orphans"])
    # homepage-col-black-rose is a manifest atmospherics entry with avif+webp formats;
    # both siblings must be registered (not orphaned)
    assert not any(o.endswith("homepage-col-black-rose.avif") for o in orph)
    assert not any(o.endswith("homepage-col-black-rose.webp") for o in orph)


def test_registered_expands_responsive_dash_siblings(tmp_path):
    # Responsive width tokens ("480w.webp") are dash-suffixed on disk (base-480w.webp).
    # hero backdrops + lookbook responsives must ALL be registered, not orphaned.
    _run_build(tmp_path)
    orph = set(_orphans(tmp_path)["orphans"])
    for f in (
        "branding/hero/luxury-nighttime-1280w.webp",
        "branding/hero/forbidden-midnight-480w.webp",
        "images/lookbook/lb-black-rose-football-960w.avif",
    ):
        assert f not in orph, f"{f} should be registered (responsive sibling), not orphaned"


def test_updated_defaults_to_generated(tmp_path):
    _run_build(tmp_path)
    assert _sot(tmp_path, "black-rose")["updated"] == "GENERATED"


def test_updated_flag_sets_field(tmp_path):
    # --updated propagates the given value into every sot.json 'updated' field.
    _run_build(tmp_path, "--updated", "2026-06-14")
    assert _sot(tmp_path, "signature")["updated"] == "2026-06-14"


def test_updated_flag_without_value_exits_clean_not_indexerror(tmp_path):
    # argparse rejects a missing value with a usage error (exit != 0), NOT the old
    # IndexError traceback from manual sys.argv indexing.
    r = subprocess.run(
        [sys.executable, str(BUILD), "--out-dir", str(tmp_path), "--updated"],
        capture_output=True,
        text=True,
    )
    assert r.returncode != 0
    assert "IndexError" not in r.stderr
