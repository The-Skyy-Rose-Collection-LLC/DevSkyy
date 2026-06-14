import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"
CSS = ROOT / "wordpress-theme/skyyrose-flagship/assets/css/design-tokens.css"
GEN = DATA / "gen-design-tokens.py"


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
