"""Smoke test: FLUX synthesis pipeline for br-001 (BLACK Rose Crewneck) front view.

Runs Stage 1 → 2 → 3+5 end-to-end and reports the outcome.
Output lands in renders/output/black-rose-crewneck/br-001-front/.
"""

import asyncio
import sys
from pathlib import Path

# Load env before any SDK import picks up os.environ
from dotenv import load_dotenv

for _f in [".env", ".env.hf", ".env.secrets"]:
    if Path(_f).exists():
        load_dotenv(_f, override=False)

from skyyrose.core.dossier_loader import DOSSIERS_DIR, get_product_with_dossier
from skyyrose.elite_studio.synthesis.flux_pipeline import render

TECHFLAT = Path("wordpress-theme/skyyrose-flagship/assets/images/products/br-001-crewneck.png")


async def main() -> None:
    product = get_product_with_dossier("br-001")
    dossier = product["dossier"]

    # Inject forensic manifest path
    slug = dossier.get("slug", "")
    dossier["_dossier_path"] = str(DOSSIERS_DIR / f"{slug}.md") if slug else ""

    print(f"SKU          : br-001 — {dossier['name']}")
    print(f"Techflat     : {TECHFLAT} ({TECHFLAT.stat().st_size // 1024}KB)")
    print(f"Dossier      : {dossier['_dossier_path']}")
    print(f"Garment lock : {dossier.get('garment_type_lock', '')[:80]}...")
    print()
    print("Starting FLUX pipeline...")
    print()

    result = await render(
        sku="br-001",
        view="front",
        dossier=dossier,
        techflat_path=TECHFLAT,
    )

    print()
    print("━" * 60)
    print(f"ok             : {result.ok}")
    print(f"attempts       : {result.attempts}")
    print(f"duration_ms    : {result.duration_ms}")
    print(f"output_path    : {result.output_path}")
    print(f"quarantine_path: {result.quarantine_path}")
    if result.error:
        print(f"error          : {result.error}")
    if result.audit_result:
        a = result.audit_result
        print(f"audit.ok       : {a.ok}")
        if a.violations:
            print("audit.violations:")
            for v in a.violations:
                print(f"  [{v.severity}] {v.element} @ {v.region}")
    print("━" * 60)

    if result.manifest:
        print("\nManifest written next to output file.")

    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
