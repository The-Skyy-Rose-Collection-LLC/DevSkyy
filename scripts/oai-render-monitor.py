#!/usr/bin/env python3
"""Entrypoint for the render-pipeline live monitor.

Adds the repo root (for the `config` package) and `scripts/` (for the
`oai_render` package) to sys.path, then delegates to oai_render.monitor.

Read-only: serves a localhost dashboard over the RunLog JSONL that every paid
`generate` run writes. Makes NO API calls and never touches the pipeline.

Usage:
  python scripts/oai-render-monitor.py                 # newest run, port 8946
  python scripts/oai-render-monitor.py --run <file>    # pin a specific run
  python scripts/oai-render-monitor.py --once          # aggregate JSON, exit
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent  # DevSkyy repo root
_SCRIPTS = _ROOT / "scripts"
for _p in (str(_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from oai_render.monitor import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
