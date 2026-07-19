"""Load the canonical product catalog CSV (SOT — see repo-root SOT.md).

Used to look up canonical facts WooCommerce doesn't reliably carry itself,
e.g. `is_preorder`, which drives the availability mapping in mapping.py.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG_PATH = (
    REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "skyyrose-catalog.csv"
)


def load_catalog(path: Path = DEFAULT_CATALOG_PATH) -> dict[str, dict[str, Any]]:
    """Return {sku: row_dict} for every row in the catalog CSV."""
    if not path.exists():
        raise FileNotFoundError(f"Canonical catalog CSV not found at {path} (see SOT.md)")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return {row["sku"]: row for row in reader if row.get("sku")}
