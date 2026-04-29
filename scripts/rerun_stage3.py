"""Stage 3 re-run script — skips Stage 1 and uses existing base + mask assets.

Usage:
    python scripts/rerun_stage3.py

Targets the three SKUs whose Stage 3 renders were quarantined after the
prompt construction fixes (negative_block injection, sublimated cardinality,
retry-header tonal-claim removal).
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# Add project root to sys.path so skyyrose package resolves.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PIL import Image

from skyyrose.core.dossier_loader import get_product_with_dossier
from skyyrose.elite_studio.agents.vision_audit_agent import VisionAuditAgent
from skyyrose.elite_studio.synthesis.clients import FalClient
from skyyrose.elite_studio.synthesis.stages.audit_filter import AuditFilter
from skyyrose.elite_studio.synthesis.stages.decoration_inpaint import inpaint_decoration
from skyyrose.elite_studio.synthesis.state.telemetry import CostTracker

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
MAX_MASK_COVERAGE = 0.40
QUARANTINE_DIR = ROOT / "renders" / "quarantine"
OUTPUT_DIR = ROOT / "renders" / "output"

# (sku, view) pairs to re-run — all four views with existing Stage 1 assets.
TARGETS: list[tuple[str, str]] = [
    ("sg-006", "front"),
    ("sg-006", "back"),
    ("sg-014", "front"),
    ("sg-015", "front"),
]


def _stage_dir(sku: str, view: str, name: str) -> Path:
    name_slug = name.lower().replace(" ", "-").replace("&", "&")
    return OUTPUT_DIR / name_slug / f"{sku}-{view}"


def _base_path(stage_dir: Path, sku: str, view: str) -> Path:
    return stage_dir / f"{sku}-{view}-stage1-base.png"


def _mask_path(stage_dir: Path, sku: str, view: str) -> Path:
    return stage_dir / f"{sku}-{view}-stage1-base-mask.png"


def _quarantine(src: Path, sku: str, view: str) -> Path:
    ts = time.strftime("%Y%m%dT%H%M%S")
    dest_dir = QUARANTINE_DIR / sku / ts
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    src.rename(dest)
    return dest


def _write_quarantine_manifest(sku: str, data: dict) -> Path:
    """Write a manifest to the quarantine dir without moving any render file.

    Used when escalation happens before Stage 3 runs (e.g. over-masked Stage 1).
    Returns the manifest path.
    """
    ts = time.strftime("%Y%m%dT%H%M%S")
    dest_dir = QUARANTINE_DIR / sku / ts
    dest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = dest_dir / "manifest.json"
    manifest_path.write_text(json.dumps(data, indent=2))
    return manifest_path


def _mask_coverage_frac(mask_path: Path) -> float:
    """Return the fraction of white (>127) pixels in a grayscale mask."""
    img = Image.open(mask_path).convert("L")
    pixels = list(img.getdata())
    return sum(1 for p in pixels if p > 127) / len(pixels)


async def rerun_one(
    sku: str,
    view: str,
    client: FalClient,
    tracker: CostTracker,
) -> dict:
    product = get_product_with_dossier(sku)
    if not product or not product.get("dossier"):
        logger.error("no dossier for %s — skip", sku)
        return {"sku": sku, "view": view, "ok": False, "error": "no_dossier"}

    dossier = product["dossier"]
    name = dossier["name"]
    stage_dir = _stage_dir(sku, view, name)
    base = _base_path(stage_dir, sku, view)
    mask = _mask_path(stage_dir, sku, view)

    if not base.is_file():
        logger.error("Stage 1 base missing: %s", base)
        return {"sku": sku, "view": view, "ok": False, "error": f"missing_base:{base}"}
    if not mask.is_file():
        logger.error("Stage 1 mask missing: %s", mask)
        return {"sku": sku, "view": view, "ok": False, "error": f"missing_mask:{mask}"}

    logger.info("=== %s %s — %s ===", sku, view, name)

    # Gate 1: Audit Stage 1 base — if it already passes H4, accept it without
    # running Stage 3.  Stage 3 is destructive (especially on large masks) and
    # should only run when Stage 1 genuinely fails.
    logger.info("gate1: auditing Stage 1 base")
    stage1_audit = await asyncio.to_thread(AuditFilter().check, base, dossier, view)
    if stage1_audit.passed:
        logger.info("gate1 PASS — Stage 1 base accepted, skipping Stage 3")
        return {
            "sku": sku,
            "view": view,
            "ok": True,
            "output_path": str(base),
            "stage": "stage1_accepted",
            "attempts": 0,
        }
    logger.info(
        "gate1 FAIL — %d violation region(s) in Stage 1 base, proceeding to gate 2",
        len(stage1_audit.violation_regions),
    )
    for region in stage1_audit.violation_regions:
        logger.warning("  region: %s", region)

    # Gate 2: Check mask coverage.  If the mask covers more than MAX_MASK_COVERAGE
    # of the image, FLUX Fill Pro will near-fully regenerate the garment and lose
    # fine details (small embroidery, thin drawstrings).  Escalate to quarantine
    # instead of spending FLUX budget on a run that will likely fail the same way.
    cov = _mask_coverage_frac(mask)
    logger.info("gate2: mask coverage %.1f%% (ceiling %.0f%%)", cov * 100, MAX_MASK_COVERAGE * 100)
    if cov > MAX_MASK_COVERAGE:
        logger.warning(
            "gate2 BLOCK — mask %.1f%% exceeds %.0f%% ceiling; "
            "Stage 3 would destructively regenerate; escalating to quarantine",
            cov * 100,
            MAX_MASK_COVERAGE * 100,
        )
        manifest_path = _write_quarantine_manifest(
            sku,
            {
                "product_name": name,
                "sku": sku,
                "view": view,
                "dossier_path": f"data/dossiers/{dossier.get('slug', sku)}.md",
                "stage": "stage1_over_masked",
                "mask_coverage_frac": round(cov, 4),
                "stage1_violation_regions": stage1_audit.violation_regions,
                "note": (
                    "Stage 1 base failed H4 audit AND mask coverage exceeds ceiling. "
                    "Needs Stage 1 re-run with corrected prompt before Stage 3 can proceed."
                ),
            },
        )
        return {
            "sku": sku,
            "view": view,
            "ok": False,
            "error": "over_masked_stage1",
            "mask_coverage_frac": round(cov, 4),
            "quarantine_manifest": str(manifest_path),
            "stage1_violation_regions": stage1_audit.violation_regions,
        }

    prior_violations: list[dict] = []
    last_inpaint_path: Path | None = None
    audit_result = None
    accepted_path: Path | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        logger.info("attempt %d/%d", attempt, MAX_ATTEMPTS)

        inpaint = await inpaint_decoration(
            client=client,
            base_image_path=base,
            mask_path=mask,
            dossier=dossier,
            out_dir=stage_dir,
            sku=sku,
            view=view,
            attempt=attempt,
            prior_violations=prior_violations,
            cost_tracker=tracker,
        )
        last_inpaint_path = inpaint.output_path

        audit_result = await asyncio.to_thread(
            VisionAuditAgent().audit,
            inpaint.output_path,
            dossier,
            view,
        )

        logger.info(
            "audit: ok=%s violations=%d",
            audit_result.ok,
            len(audit_result.violations),
        )
        for v in audit_result.violations:
            logger.warning("  [%s] %s — %s", v.severity, v.element, v.region)

        if audit_result.ok:
            accepted_path = inpaint.output_path
            break

        blocking = [v for v in audit_result.violations if v.severity in ("medium", "high")]
        prior_violations = [
            {"element": v.element, "region": v.region, "severity": v.severity} for v in blocking
        ]

    if accepted_path:
        logger.info("PASS: %s %s → %s", sku, view, accepted_path)
        return {
            "sku": sku,
            "view": view,
            "ok": True,
            "output_path": str(accepted_path),
            "attempts": attempt,
        }

    quarantine_path = _quarantine(last_inpaint_path, sku, view)
    manifest = {
        "product_name": name,
        "sku": sku,
        "view": view,
        "dossier_path": f"data/dossiers/{dossier.get('slug', sku)}.md",
        "audit_result": {
            "ok": audit_result.ok if audit_result else False,
            "violations": [
                {"element": v.element, "region": v.region, "severity": v.severity}
                for v in (audit_result.violations if audit_result else [])
            ],
        },
        "attempts": MAX_ATTEMPTS,
        "quarantine_path": str(quarantine_path),
    }
    manifest_path = quarantine_path.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    logger.warning("QUARANTINE: %s %s → %s", sku, view, quarantine_path)
    return {
        "sku": sku,
        "view": view,
        "ok": False,
        "quarantine_path": str(quarantine_path),
        "attempts": MAX_ATTEMPTS,
    }


async def main() -> None:
    client = FalClient()
    tracker = CostTracker()
    results = []

    for sku, view in TARGETS:
        result = await rerun_one(sku, view, client, tracker)
        results.append(result)

    print("\n=== BATCH SUMMARY ===")
    passed = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]
    print(f"  Passed : {len(passed)}/{len(results)}")
    print(f"  Failed : {len(failed)}/{len(results)}")
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        note = r.get("output_path") or r.get("quarantine_path") or r.get("error", "")
        print(f"  [{status}] {r['sku']} {r['view']}  {note}")


if __name__ == "__main__":
    asyncio.run(main())
