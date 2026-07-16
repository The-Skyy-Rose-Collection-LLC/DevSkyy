"""Smoke test: nano-banana generate --help advertises --score-alignment."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_help_lists_score_alignment_flag() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "nano-banana-run.py"), "generate", "--help"],
        capture_output=True,
        text=True,
        # no cwd= — it forces macOS subprocess onto the crash-prone fork()
        # path (bug-263); the script is invoked by absolute path.
        env={**os.environ, "PYTHONPATH": str(REPO)},
    )
    assert result.returncode == 0, result.stderr
    assert "--score-alignment" in result.stdout
