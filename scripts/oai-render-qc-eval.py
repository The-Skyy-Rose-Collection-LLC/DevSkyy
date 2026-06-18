#!/usr/bin/env python3
"""Entrypoint for the QC-judge ground-truth evaluation harness.

Adds the repo root (for the `config` package) and `scripts/` (for the
`oai_render` package) to sys.path, then delegates to oai_render.qc_eval.

Scores the configured QC judge against the Fable-audited ground-truth set so a
judge regression is caught for cents before any paid batch. Makes one judge API
call per labeled render; generates NO images.

Usage:
  python scripts/oai-render-qc-eval.py
  python scripts/oai-render-qc-eval.py --json
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent  # DevSkyy repo root
_SCRIPTS = _ROOT / "scripts"
for _p in (str(_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from oai_render.qc_eval import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
