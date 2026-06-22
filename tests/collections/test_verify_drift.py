import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "wordpress-theme/skyyrose-flagship/data"


def test_full_pipeline_then_verify_is_clean():
    # Runs the real pipeline against the real committed tree on purpose: this is
    # the gate that the checked-in SOT + tokens are self-consistent, so it must
    # NOT be redirected to a tmp copy.
    for script in ("gen-design-tokens.py", "build-collection-sot.py", "gen-collection-hub.py"):
        subprocess.run([sys.executable, str(DATA / script)], check=True)
    r = subprocess.run(
        [sys.executable, str(DATA / "verify-collection-sot.py")],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr


def test_stale_tokens_fail_and_verify_leaves_no_net_change(tmp_path):
    # Hermetic: route gen + verify (and verify's internal gen subprocess, which
    # inherits the env) at a private tmp copy of design-tokens.css via
    # SKYYROSE_TOKENS_CSS. The suite runs with asyncio_mode=auto alongside other
    # token-touching tests; operating on the shared real file made this test race
    # — a concurrent regen could wipe the injected junk before verify read it, so
    # verify saw clean tokens and returned 0. A private copy no other test knows
    # about removes that race by construction (and never mutates the real file).
    real_css = DATA.parent / "assets/css/design-tokens.css"
    tmp_css = tmp_path / "design-tokens.css"
    tmp_css.write_text(real_css.read_text())
    env = {**os.environ, "SKYYROSE_TOKENS_CSS": str(tmp_css)}

    # Start from a known-clean generated state in the tmp copy.
    subprocess.run([sys.executable, str(DATA / "gen-design-tokens.py")], check=True, env=env)
    original = tmp_css.read_text()
    end = "/* GENERATED:collection-tokens END */"
    # Inject a junk block INSIDE the generated region so a fresh generation diverges.
    stale = original.replace(end, '[data-collection="x"]{--z:1;}\n' + end, 1)
    assert stale != original
    tmp_css.write_text(stale)

    r = subprocess.run(
        [sys.executable, str(DATA / "verify-collection-sot.py")],
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 1, r.stdout + r.stderr
    assert "STALE" in r.stdout
    # Verify is net read-only on the token file: it must restore the bytes it
    # found, not leave its regen.
    assert tmp_css.read_text() == stale
