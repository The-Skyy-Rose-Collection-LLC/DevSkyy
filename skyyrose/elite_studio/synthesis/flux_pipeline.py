"""FLUX synthesis pipeline — main orchestrator (Stage 1 → 2 → 3 → 5).

Coordinates the four active stages into a single `render()` call:

    Stage 1   FLUX Kontext Pro    base garment, no decoration
    Stage 1.5 AuditFilter         H4 gate — accept Stage 1 or collect violation regions
    Stage 2   Gemini Flash        mask derivation (violation regions only, Path B)
    Stage 3   FLUX Fill Pro       inpaint decoration inside mask only
    Stage 5   VisionAuditAgent    fidelity gate + H4 retry-with-feedback

Stage 4 (IC-Light relighting) is deferred to v2.

Returns a ``RenderResult`` that carries:
  - ``ok``: True when the render passed the audit gate
  - ``output_path``: final accepted PNG (or the best attempt on failure)
  - ``quarantine_path``: set when all attempts exhausted without passing
  - ``audit_result``: last VisionAuditResult for the caller to log
  - ``manifest``: H5 forensic dict, written to disk automatically

Architecture: ``docs/architecture/flux-synthesis.md``
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from llm.model_ids import GEMINI_VISION_MODEL

from ..agents.vision_audit_agent import VisionAuditAgent, VisionAuditResult
from ..budget import BudgetExceededError, RunBudget  # noqa: F401 (BudgetExceededError re-raised)
from .clients import FalClient
from .stages.audit_filter import AuditError, AuditFilter  # noqa: F401 (AuditError re-raised)
from .stages.base_render import render_base
from .stages.decoration_inpaint import inpaint_decoration
from .stages.mask_deriver import MaskDeriver
from .state.telemetry import CostTracker

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3

# Canonical per-call cost estimates sourced from synthesis/state/telemetry.py FAL_COSTS.
_FLUX_KONTEXT_EST_COST_USD: float = 0.04  # fal-ai/flux-pro/kontext
_FLUX_FILL_EST_COST_USD: float = (
    0.05  # fal-ai/flux-pro/v1/fill and fal-ai/flux-kontext-lora/inpaint
)
DEFAULT_OUT_DIR = Path("renders/output")
QUARANTINE_DIR = Path("renders/quarantine")


@dataclass
class RenderResult:
    """Outcome of a single `render()` call.

    Callers should check ``ok`` first; on failure ``quarantine_path`` points
    to the best (rejected) attempt and ``audit_result`` explains why.
    """

    sku: str
    view: str
    ok: bool
    output_path: Path | None = None
    quarantine_path: Path | None = None
    audit_result: VisionAuditResult | None = None
    manifest: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    duration_ms: int = 0
    error: str = ""


async def render(
    *,
    sku: str,
    view: str,
    dossier: dict,
    techflat_path: str | Path,
    out_dir: str | Path | None = None,
    lora_url: str | None = None,
    lora_trigger: str | None = None,
    lora_scale: float = 0.85,
    cost_tracker: CostTracker | None = None,
    budget: RunBudget | None = None,
    seed: int | None = None,
    fal_client: FalClient | None = None,
) -> RenderResult:
    """Run the full FLUX synthesis pipeline for one SKU × view.

    Args:
        sku: product SKU (e.g. "br-001").
        view: "front" or "back".
        dossier: parsed dossier dict with ``name``, ``garment_type_lock``,
            ``branding_block``, ``negative_block``.
        techflat_path: path to the techflat image that Kontext uses as
            silhouette / color conditioning.
        out_dir: directory for accepted outputs. Defaults to
            ``renders/output/{name-slug}/``.
        lora_url: optional LoRA weights URL. When set, Stage 3 routes through
            ``fal-ai/flux-kontext-lora/inpaint`` with the lora scale.
        lora_trigger: trigger word for the LoRA (e.g. ``"SKYR_EMBOSS"``).
        lora_scale: per-LoRA influence weight (0–1).
        cost_tracker: optional accumulator passed through all stages.
        budget: optional hard ceiling enforcer; raises BudgetExceededError
            before each paid FAL call if the ceiling would be exceeded.
            BudgetExceededError propagates to the caller — do not catch here.
        seed: optional fixed seed for reproducibility.
        fal_client: optional pre-built client (useful for testing).

    Returns:
        RenderResult — callers check ``.ok``.
    """
    started = time.perf_counter()
    techflat_path = Path(techflat_path)

    name_slug = _name_slug(dossier.get("name", sku))
    resolved_out_dir = Path(out_dir) if out_dir else DEFAULT_OUT_DIR / name_slug

    client = fal_client or FalClient()
    tracker = cost_tracker or CostTracker()

    stage_dir = resolved_out_dir / f"{sku}-{view}"
    stage_dir.mkdir(parents=True, exist_ok=True)

    audit_result: VisionAuditResult | None = None
    final_path: Path | None = None
    last_inpaint_path: Path | None = None
    attempts_made = 0

    prior_violations: list[dict] = []

    try:
        # ── Stage 1: FLUX Kontext Pro — clean base garment ─────────────────
        if budget is not None:
            budget.ensure_within_budget(_FLUX_KONTEXT_EST_COST_USD, stage="flux_stage1_kontext")
        logger.info("stage1 start: sku=%s view=%s", sku, view)
        base = await render_base(
            client=client,
            techflat_path=techflat_path,
            dossier=dossier,
            out_dir=stage_dir,
            sku=sku,
            view=view,
            cost_tracker=tracker,
            seed=seed,
        )
        if budget is not None:
            budget.spend(_FLUX_KONTEXT_EST_COST_USD, stage="flux_stage1_kontext")

        # ── Stage 1.5: AuditFilter — accept Stage 1 or collect violations ──
        logger.info("stage1.5 start: sku=%s view=%s", sku, view)
        stage1_audit = await asyncio.to_thread(AuditFilter().check, base.output_path, dossier, view)
        if stage1_audit.passed:
            logger.info(
                "stage1.5 PASS: sku=%s view=%s — Stage 1 accepted, 0 FLUX Fill calls",
                sku,
                view,
            )
            final_path = base.output_path
        else:
            # ── Stage 2: Gemini Flash — mask only violated regions ──────────
            logger.info("stage2 start: sku=%s view=%s", sku, view)
            deriver = MaskDeriver()
            mask_result = deriver.derive(
                image_path=base.output_path,
                dossier=dossier,
                view=view,
                out_dir=stage_dir,
                allowed_regions=stage1_audit.violation_regions,
            )
            logger.info(
                "stage2 mask: sku=%s view=%s method=%s coverage=%.3f",
                sku,
                view,
                mask_result.method,
                mask_result.coverage_frac,
            )

            # ── Stage 3 + 5: Inpaint → Audit with H4 retry loop ───────────
            auditor = VisionAuditAgent()
            for attempt in range(1, MAX_ATTEMPTS + 1):
                if budget is not None:
                    budget.ensure_within_budget(_FLUX_FILL_EST_COST_USD, stage="flux_stage3_fill")
                logger.info(
                    "stage3 attempt %d/%d: sku=%s view=%s", attempt, MAX_ATTEMPTS, sku, view
                )

                inpaint = await inpaint_decoration(
                    client=client,
                    base_image_path=base.output_path,
                    mask_path=mask_result.mask_path,
                    dossier=dossier,
                    out_dir=stage_dir,
                    sku=sku,
                    view=view,
                    attempt=attempt,
                    prior_violations=prior_violations,
                    lora_url=lora_url,
                    lora_trigger=lora_trigger,
                    lora_scale=lora_scale,
                    cost_tracker=tracker,
                    seed=seed,
                )
                if budget is not None:
                    budget.spend(_FLUX_FILL_EST_COST_USD, stage="flux_stage3_fill")
                last_inpaint_path = inpaint.output_path
                attempts_made = attempt

                # Stage 5: vision audit (sync; run in thread so we don't block event loop)
                audit_result = await asyncio.to_thread(
                    auditor.audit,
                    inpaint.output_path,
                    dossier,
                    view,
                )
                logger.info(
                    "stage5 audit: sku=%s view=%s attempt=%d ok=%s violations=%d",
                    sku,
                    view,
                    attempt,
                    audit_result.ok,
                    len(audit_result.violations),
                )

                if audit_result.ok:
                    final_path = inpaint.output_path
                    break

                # Build violation feedback list for the next attempt.
                blocking = [v for v in audit_result.violations if v.is_blocking]
                prior_violations = [
                    {"element": v.element, "region": v.region, "severity": v.severity}
                    for v in blocking
                ]

    except Exception as exc:
        logger.exception("flux_pipeline fatal error: sku=%s view=%s", sku, view)
        duration_ms = int((time.perf_counter() - started) * 1000)
        return RenderResult(
            sku=sku,
            view=view,
            ok=False,
            error=str(exc),
            attempts=1,
            duration_ms=duration_ms,
        )

    duration_ms = int((time.perf_counter() - started) * 1000)

    if final_path is None:
        # All attempts exhausted — quarantine the last attempt.
        quarantine_path = _quarantine(last_inpaint_path, sku, view)
        manifest = _build_manifest(
            sku=sku,
            view=view,
            dossier=dossier,
            techflat_path=techflat_path,
            output_path=quarantine_path,
            audit_result=audit_result,
            lora_url=lora_url,
            attempts=attempts_made,
            duration_ms=duration_ms,
            quarantined=True,
        )
        _write_manifest(quarantine_path, manifest)
        return RenderResult(
            sku=sku,
            view=view,
            ok=False,
            quarantine_path=quarantine_path,
            audit_result=audit_result,
            manifest=manifest,
            attempts=attempts_made,
            duration_ms=duration_ms,
        )

    manifest = _build_manifest(
        sku=sku,
        view=view,
        dossier=dossier,
        techflat_path=techflat_path,
        output_path=final_path,
        audit_result=audit_result,
        lora_url=lora_url,
        attempts=attempts_made,
        duration_ms=duration_ms,
        quarantined=False,
    )
    _write_manifest(final_path, manifest)
    logger.info(
        "flux_pipeline done: sku=%s view=%s attempts=%d duration_ms=%d cost=$%.4f",
        sku,
        view,
        attempts_made,
        duration_ms,
        tracker.total_usd,
    )
    return RenderResult(
        sku=sku,
        view=view,
        ok=True,
        output_path=final_path,
        audit_result=audit_result,
        manifest=manifest,
        attempts=attempts_made,
        duration_ms=duration_ms,
    )


# ── Helpers ──────────────────────────────────────────────────────────────────


def _name_slug(name: str) -> str:
    """Turn a product name into a filesystem slug."""
    return name.lower().replace(" ", "-").replace("'", "").replace("/", "-")


def _quarantine(path: Path | None, sku: str, view: str) -> Path:
    """Move a rejected render to the quarantine directory."""
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    q_dir = QUARANTINE_DIR / sku / ts
    q_dir.mkdir(parents=True, exist_ok=True)
    if path and path.is_file():
        dest = q_dir / path.name
        shutil.copy2(path, dest)
        return dest
    # No render file at all — return the quarantine dir as a sentinel.
    return q_dir / f"{sku}-{view}-quarantine.png"


def _build_manifest(
    *,
    sku: str,
    view: str,
    dossier: dict,
    techflat_path: Path,
    output_path: Path | None,
    audit_result: VisionAuditResult | None,
    lora_url: str | None,
    attempts: int,
    duration_ms: int,
    quarantined: bool,
) -> dict[str, Any]:
    """Build the H5 forensic manifest dict."""
    dossier_path = dossier.get("_dossier_path", "")
    dossier_sha = _sha256_file(dossier_path) if dossier_path else ""
    return {
        "product_name": dossier.get("name", sku),
        "sku": sku,
        "view": view,
        "dossier_path": dossier_path,
        "dossier_sha256": dossier_sha,
        "techflat_path": str(techflat_path),
        "lora_url": lora_url,
        "model_stage1": "fal-ai/flux-pro/kontext",
        "model_stage3": (
            "fal-ai/flux-kontext-lora/inpaint" if lora_url else "fal-ai/flux-pro/v1/fill"
        ),
        "model_audit": GEMINI_VISION_MODEL,
        "timestamp": datetime.now(UTC).isoformat(),
        "attempts": attempts,
        "duration_ms": duration_ms,
        "quarantined": quarantined,
        "output_path": str(output_path) if output_path else None,
        "audit": audit_result.to_dict() if audit_result else {},
    }


def _write_manifest(adjacent_path: Path | None, manifest: dict[str, Any]) -> None:
    """Write manifest.json next to the output or quarantine file."""
    if adjacent_path is None:
        return
    dest = adjacent_path.parent / "manifest.json"
    try:
        dest.write_text(json.dumps(manifest, indent=2, default=str))
    except Exception:
        logger.warning("could not write manifest to %s", dest)


def _sha256_file(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file():
        return ""
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
