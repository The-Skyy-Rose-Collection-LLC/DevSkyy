#!/usr/bin/env python3
"""
GLB publish manifest — lists SHIP-CLEARED SKUs (verdict=pass in the current
renders/3d/qc/fidelity_report.json) with their GLB path and file size.

OUTPUT ONLY. Makes zero WordPress/WooCommerce writes and zero paid API calls — a
separate, explicitly-confirmed deploy step consumes this file.

Usage:
    python scripts/glb_publish_manifest.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb_fidelity as gf  # noqa: E402


def build_publish_manifest(sku_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Shape verdict=pass SKU rows into a ship-cleared publish manifest."""
    entries: list[dict[str, Any]] = []
    for row in sku_rows:
        if row.get("verdict") != "pass":
            continue
        glb_path = Path(row["glb"])
        entries.append(
            {
                "sku": row["sku"],
                "glb_path": str(glb_path),
                "glb_bytes": glb_path.stat().st_size if glb_path.exists() else None,
                "color_delta_e": row.get("color_delta_e"),
                "master": row.get("master"),
            }
        )
    return {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "note": (
            "OUTPUT ONLY — ship-cleared SKUs under the current fidelity gate. "
            "No WordPress/WooCommerce writes, no paid API calls."
        ),
        "entries": entries,
        "summary": {"count": len(entries)},
    }


def main() -> None:
    report_path = gf.QC_DIR / "fidelity_report.json"
    if not report_path.exists():
        sys.exit(f"No fidelity_report.json at {report_path} — run scripts/glb_fidelity.py first")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    manifest = build_publish_manifest(report["skus"])

    gf.QC_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = gf.QC_DIR / "publish_manifest.json"
    tmp_path = manifest_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    os.replace(tmp_path, manifest_path)

    print(
        f"Publish manifest -> {manifest_path} ({manifest['summary']['count']} ship-cleared SKU(s))"
    )


if __name__ == "__main__":
    main()
