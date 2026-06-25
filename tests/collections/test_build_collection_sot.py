import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"
ASSETS = ROOT / "wordpress-theme/skyyrose-flagship/assets"
BUILD = DATA / "build-collection-sot.py"


def test_build_emits_per_folder_sot_and_orphans():
    subprocess.run([sys.executable, str(BUILD)], check=True)
    for slug in ["black-rose", "love-hurts", "signature", "kids-capsule"]:
        sot = json.loads((DATA / "collections" / slug / "sot.json").read_text())
        assert sot["collection"] == slug
        assert "products" in sot and "imagery" in sot and "lockup" in sot
        assert "story" in sot and "palette" in sot and "fonts" in sot
        assert "other_collection_files" not in sot  # retired
        for p in sot["products"]:
            for _col, im in p.get("images", {}).items():
                if im.get("resolved"):
                    assert (ASSETS / im["resolved"]).is_file()
    orph = json.loads((DATA / "collections" / "_orphans.json").read_text())
    assert isinstance(orph["orphans"], list)


def test_registered_expands_format_siblings():
    orph = set(json.loads((DATA / "collections" / "_orphans.json").read_text())["orphans"])
    # homepage-col-black-rose is a manifest atmospherics entry with avif+webp formats;
    # both siblings must be registered (not orphaned)
    assert not any(o.endswith("homepage-col-black-rose.avif") for o in orph)
    assert not any(o.endswith("homepage-col-black-rose.webp") for o in orph)


def test_registered_expands_responsive_dash_siblings():
    # Responsive width tokens ("480w.webp") are dash-suffixed on disk (base-480w.webp).
    # hero backdrops + lookbook responsives must ALL be registered, not orphaned.
    orph = set(json.loads((DATA / "collections" / "_orphans.json").read_text())["orphans"])
    for f in (
        "branding/hero/luxury-nighttime-1280w.webp",
        "branding/hero/forbidden-midnight-480w.webp",
        "images/lookbook/lb-black-rose-football-960w.avif",
    ):
        assert f not in orph, f"{f} should be registered (responsive sibling), not orphaned"


def test_updated_defaults_to_generated():
    subprocess.run([sys.executable, str(BUILD)], check=True)
    sot = json.loads((DATA / "collections" / "black-rose" / "sot.json").read_text())
    assert sot["updated"] == "GENERATED"


def test_updated_flag_sets_field_then_restores():
    try:
        subprocess.run([sys.executable, str(BUILD), "--updated", "2026-06-14"], check=True)
        sot = json.loads((DATA / "collections" / "signature" / "sot.json").read_text())
        assert sot["updated"] == "2026-06-14"
    finally:
        subprocess.run([sys.executable, str(BUILD)], check=True)  # restore default state


def test_updated_flag_without_value_exits_clean_not_indexerror():
    # argparse rejects a missing value with a usage error (exit != 0), NOT the old
    # IndexError traceback from manual sys.argv indexing.
    r = subprocess.run([sys.executable, str(BUILD), "--updated"], capture_output=True, text=True)
    assert r.returncode != 0
    assert "IndexError" not in r.stderr
