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
