"""FidelityGate — dossier-VALIDATE disposition.

Disposition (pure):
  any visible view below threshold        -> REJECT
  any inferred angle OR any violation     -> HUMAN_QUEUE
  full coverage, all pass, no violation   -> PASS_PENDING_HUMAN

Even PASS_PENDING_HUMAN still requires a human approval downstream — the gate
never auto-delivers. Inferred faces never auto-pass: their presence alone
forces HUMAN_QUEUE, so regeneration can never launder a hallucinated panel.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from skyyrose.elite_studio.platform.fidelity.metrics import VisibleScore
from skyyrose.elite_studio.platform.fidelity.report import FidelityReport, FidelityVerdict

logger = logging.getLogger(__name__)


def dispose(
    *,
    visible: Sequence[VisibleScore],
    inferred_angles: tuple[str, ...],
    violations: tuple[str, ...],
    threshold: float,
) -> FidelityVerdict:
    """Decide the verdict from scored visible views + coverage + violations.

    `threshold` is the tenant's visible_composite_min; 0.0 = report-only
    (never rejects on score, but inferred/violation routing still applies).
    """
    if threshold > 0.0 and any(not vs.passes(threshold) for vs in visible):
        return FidelityVerdict.REJECT
    if inferred_angles or violations:
        return FidelityVerdict.HUMAN_QUEUE
    return FidelityVerdict.PASS_PENDING_HUMAN


def evaluate(
    tenant, sku: str, mesh_path: str, *, attempt: int = 1, renderer=None
) -> FidelityReport:
    """Full dossier-VALIDATE pipeline -> FidelityReport.

    GATED-INTEGRATION: touches Blender + CLIP/DINOv2 models, so it is exercised
    in gated integration (real GLB), never in CI. The pure `dispose` it calls is
    unit-tested. render views -> score visible (vs golden) -> mesh sanity ->
    dispose -> report.
    """
    from skyyrose.elite_studio.platform.catalog_source import SkyyRoseCatalogSource
    from skyyrose.elite_studio.platform.fidelity.metrics import score_view
    from skyyrose.elite_studio.platform.fidelity.render import BlenderRenderer
    from skyyrose.elite_studio.platform.fidelity.validate import (
        inspect_glb_geometry,
        mesh_sanity_ok,
    )

    source = SkyyRoseCatalogSource(reference_root=tenant.reference_root)
    references = source.references(sku)
    renderer = renderer or BlenderRenderer()
    views = renderer.render(mesh_path, references)

    visible = [
        score_view(views.angle_paths[a], references[a], sku=sku, angle=a)
        for a in views.verified_angles()
    ]
    composite_by_angle = {vs.angle: vs.composite for vs in visible}

    violations: list[str] = []
    ok, detail = mesh_sanity_ok(**inspect_glb_geometry(mesh_path))
    if not ok:
        violations.append(f"mesh: {detail}")
    # Inferred views already force HUMAN_QUEUE via dispose — a missing hidden-face
    # color sample can never grant auto-pass, so brand-palette sampling of
    # inferred views is an advisory enrichment, added in gated integration.

    verdict = dispose(
        visible=visible,
        inferred_angles=views.inferred_angles(),
        violations=tuple(violations),
        threshold=tenant.thresholds.visible_composite_min,
    )
    return FidelityReport(
        tenant_id=tenant.id,
        sku=sku,
        mesh_path=mesh_path,
        verdict=verdict,
        composite_by_angle=composite_by_angle,
        verified_angles=views.verified_angles(),
        inferred_angles=views.inferred_angles(),
        violations=tuple(violations),
        attempts=attempt,
    )
