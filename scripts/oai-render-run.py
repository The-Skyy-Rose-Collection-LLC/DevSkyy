#!/usr/bin/env python3
"""Entrypoint for the OpenAI gpt-image-2 product render pipeline.

Adds the repo root (for the `config` package) and `scripts/` (for the
`oai_render` package) to sys.path, then delegates to oai_render.cli.

Usage:
  python scripts/oai-render-run.py dry-run --sku br-010
  python scripts/oai-render-run.py dry-run --all
  python scripts/oai-render-run.py generate --sku br-010 --yes
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent  # DevSkyy repo root
_SCRIPTS = _ROOT / "scripts"
for _p in (str(_ROOT), str(_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from oai_render.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
