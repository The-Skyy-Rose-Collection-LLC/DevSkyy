import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"


def test_full_pipeline_then_verify_is_clean():
    for script in ("gen-design-tokens.py", "build-collection-sot.py", "gen-collection-hub.py"):
        subprocess.run([sys.executable, str(DATA / script)], check=True)
    r = subprocess.run(
        [sys.executable, str(DATA / "verify-collection-sot.py")],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_stale_tokens_fail_and_verify_leaves_no_net_change():
    # Start from a known-clean generated state.
    for script in ("gen-design-tokens.py", "build-collection-sot.py"):
        subprocess.run([sys.executable, str(DATA / script)], check=True)
    css = DATA.parent / "assets/css/design-tokens.css"
    original = css.read_text()
    end = "/* GENERATED:collection-tokens END */"
    # Inject a junk block INSIDE the generated region so a fresh generation diverges.
    stale = original.replace(end, '[data-collection="x"]{--z:1;}\n' + end, 1)
    assert stale != original
    css.write_text(stale)
    try:
        r = subprocess.run(
            [sys.executable, str(DATA / "verify-collection-sot.py")],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 1, r.stdout + r.stderr
        assert "STALE" in r.stdout
        # Verify is net read-only: it must restore the bytes it found, not leave its regen.
        assert css.read_text() == stale
    finally:
        css.write_text(original)
        subprocess.run([sys.executable, str(DATA / "gen-design-tokens.py")], check=True)
