import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"
GEN = DATA / "gen-collection-hub.py"


def test_hub_renders_all_sections_and_escapes():
    subprocess.run([sys.executable, str(GEN)], check=True)
    html = (DATA / "collections/black-rose/index.html").read_text()
    assert "<!DOCTYPE html>" in html
    assert "Black Rose" in html
    assert "#C0C0C0" in html  # palette swatch
    assert "Yellowtail" in html  # font specimen
    assert "black-rose-lockup" in html  # lockup reference
    assert "../../assets/" in html  # image refs into canonical tree
    # no unescaped script injection from data
    assert "<script>alert" not in html
