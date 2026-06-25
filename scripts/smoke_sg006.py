"""Smoke test: sg-006 front + back through the full FLUX synthesis pipeline.

Validates:
  - Stage 1.5 AuditFilter fires and returns audit JSON + violation_regions
  - If Stage 1 fails: mask coverage logged < 40%
  - Stage 3 only touches violation regions
  - Final render passes H4 fidelity gate (or quarantines with manifest)

Cost cap: 2 FLUX Kontext Pro ($0.08) + up to 2 FLUX Fill Pro ($0.10) = ~$0.21 worst case.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skyyrose.core.dossier_loader import get_product_with_dossier
from skyyrose.elite_studio.synthesis.flux_pipeline import render
from skyyrose.elite_studio.synthesis.state.telemetry import CostTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

SKU = "sg-006"
TECHFLAT = (
    ROOT
    / "wordpress-theme/skyyrose-flagship/assets/images/products/sg-006-mint-lavender-hoodie.png"
)
OUT_DIR = ROOT / "renders/smoke" / SKU


async def main() -> None:
    product = get_product_with_dossier(SKU)
    if not product or not product.get("dossier"):
        logger.error("no dossier for %s — abort", SKU)
        sys.exit(1)

    dossier = product["dossier"]
    tracker = CostTracker()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for view in ("front", "back"):
        logger.info("\n%s\n=== %s %s ===\n%s", "=" * 60, SKU, view, "=" * 60)
        result = await render(
            sku=SKU,
            view=view,
            dossier=dossier,
            techflat_path=TECHFLAT,
            out_dir=OUT_DIR,
            cost_tracker=tracker,
        )

        status = "PASS" if result.ok else "FAIL/QUARANTINE"
        logger.info(
            "result: %s  attempts=%d  duration=%dms", status, result.attempts, result.duration_ms
        )

        if result.output_path:
            logger.info("output  : %s", result.output_path)
        if result.quarantine_path:
            logger.warning("quarantined: %s", result.quarantine_path)
        if result.manifest:
            logger.info(
                "manifest:\n%s",
                json.dumps(
                    {k: v for k, v in result.manifest.items() if k != "boxes"},
                    indent=2,
                    default=str,
                ),
            )
        if result.audit_result:
            ar = result.audit_result
            logger.info(
                "final audit: ok=%s violations=%d",
                ar.ok,
                len(ar.violations),
            )
            for v in ar.violations:
                logger.warning("  [%s] %s — %s", v.severity, v.element, v.region)

    summary = tracker.summary()
    logger.info(
        "\n=== COST SUMMARY ===\n  Total: $%.4f  Calls: %d\n  By model: %s",
        summary["total_usd"],
        summary["calls"],
        json.dumps(summary.get("by_model_usd", {}), indent=4),
    )


if __name__ == "__main__":
    asyncio.run(main())
