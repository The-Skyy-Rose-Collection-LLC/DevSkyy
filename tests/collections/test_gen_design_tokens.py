import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"
CSS = ROOT / "wordpress-theme/skyyrose-flagship/assets/css/design-tokens.css"
GEN = DATA / "gen-design-tokens.py"


def _load_gen():
    # Filename is hyphenated (not importable normally) — load it as a module so we
    # can monkeypatch its CSS path and call main() in-process.
    spec = importlib.util.spec_from_file_location("gen_design_tokens_mod", GEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _region():
    css = CSS.read_text()
    s = css.index("GENERATED:collection-tokens START")
    e = css.index("GENERATED:collection-tokens END")
    return css[s:e]


def test_generated_region_palette_and_fonts():
    subprocess.run([sys.executable, str(GEN)], check=True)
    region = _region()
    for slug in ("black-rose", "love-hurts", "signature", "kids-capsule"):
        assert f'[data-collection="{slug}"]' in region
    # Black Rose: silver accent, NO red anywhere in its block (canon purge)
    br = region[
        region.index('[data-collection="black-rose"]') : region.index(
            '[data-collection="love-hurts"]'
        )
    ]
    assert "#C0C0C0" in br
    assert "#DC143C" not in br
    # consumed tokens preserved
    assert "--skyyrose-accent-rgb:" in region
    assert "--skyyrose-secondary:" in region
    assert "--skyyrose-font-display:" in region
    # accent-rgb is numeric "r, g, b"
    assert "192, 192, 192" in br
    # two-role fonts + display aliases caps
    assert "--skyyrose-font-script:" in region and "Pinyon Script" in region
    assert "var(--skyyrose-font-caps)" in region
    # dropped: font-gothic
    assert "--skyyrose-font-gothic" not in region


def test_generation_idempotent():
    subprocess.run([sys.executable, str(GEN)], check=True)
    first = CSS.read_text()
    subprocess.run([sys.executable, str(GEN)], check=True)
    assert CSS.read_text() == first


def test_missing_markers_exits_1(tmp_path, monkeypatch, capsys):
    mod = _load_gen()
    bad = tmp_path / "design-tokens.css"
    bad.write_text(":root { --x: 1; }\n")  # no GENERATED markers at all
    monkeypatch.setattr(mod, "CSS", bad)
    assert mod.main() == 1
    assert "missing the GENERATED" in capsys.readouterr().err


def test_end_marker_before_start_exits_1(tmp_path, monkeypatch, capsys):
    mod = _load_gen()
    bad = tmp_path / "design-tokens.css"
    # The generator regenerates the global-fonts region first, so the fixture must
    # carry a well-formed global-fonts region for main() to reach the
    # collection-tokens ordering check this test exercises. The collection-tokens
    # markers are intentionally reversed (END before START).
    bad.write_text(
        "/* GENERATED:global-fonts START */\n/* GENERATED:global-fonts END */\n"
        "/* GENERATED:collection-tokens END */\n/* GENERATED:collection-tokens START */\n"
    )
    monkeypatch.setattr(mod, "CSS", bad)
    assert mod.main() == 1
    assert "collection-tokens END marker before START" in capsys.readouterr().err
