"""Smoke test: FLUX synthesis pipeline — br-001 front view.

Runs Stage 1 → 1.5 → 2 → 3 → 5 for the Black Rose Crewneck and prints
the result to stdout. Seed is fixed for reproducibility.

Usage (from project root, with .venv active):
    python scripts/smoke_test_flux_br001.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

# Load .env and .env.hf before any fal/google imports.
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env.hf")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s — %(message)s",
    stream=sys.stdout,
)

SKU = "br-001"
VIEW = "front"
SEED = 42
TECHFLAT = Path(
    "skyyrose/assets/images/source-products/black-rose/br-001-techflat-crewneck-joggers-set.jpeg"
)
OUT_DIR = Path("renders/output")


async def main() -> int:
    from skyyrose.core.dossier_loader import DOSSIERS_DIR, get_product_with_dossier
    from skyyrose.elite_studio.synthesis.flux_pipeline import render
    from skyyrose.elite_studio.synthesis.state.telemetry import CostTracker

    print(f"\n{'=' * 60}")
    print(f"  Smoke test: {SKU} × {VIEW}")
    print(f"  Techflat : {TECHFLAT}")
    print(f"  Seed     : {SEED}")
    print(f"{'=' * 60}\n")

    product = get_product_with_dossier(SKU)
    dossier: dict = product["dossier"]
    dossier["_dossier_path"] = str(DOSSIERS_DIR / f"{dossier['slug']}.md")

    print(f"Dossier  : {dossier['name']}")
    print(f"Lock     : {dossier['garment_type_lock'][:80]}…")
    print()

    tracker = CostTracker()
    result = await render(
        sku=SKU,
        view=VIEW,
        dossier=dossier,
        techflat_path=TECHFLAT,
        out_dir=OUT_DIR,
        seed=SEED,
        cost_tracker=tracker,
    )

    print(f"\n{'=' * 60}")
    print(f"  Result   : {'PASS ✓' if result.ok else 'FAIL ✗'}")
    print(f"  Attempts : {result.attempts}")
    print(f"  Duration : {result.duration_ms:,} ms")
    print(f"  Cost     : ${tracker.total_usd:.4f}")
    if result.output_path:
        print(f"  Output   : {result.output_path}")
    if result.quarantine_path:
        print(f"  Quarantine: {result.quarantine_path}")
    if result.audit_result:
        print(f"  Audit ok : {result.audit_result.ok}")
        if result.audit_result.violations:
            for v in result.audit_result.violations:
                print(f"    ✗ {v.severity.upper()} — {v.element} @ {v.region}")
    if result.error:
        print(f"  Error    : {result.error}")
    print(f"{'=' * 60}\n")

    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
