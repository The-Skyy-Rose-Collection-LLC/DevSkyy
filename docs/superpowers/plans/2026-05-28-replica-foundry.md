# Replica Foundry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the multi-tenant SaaS imagery platform's engine-and-guarantee vertical slice — generate a verified 3D replica of a real garment (SkyyRose as tenant #1), provably never an invention.

**Architecture:** A new `skyyrose/elite_studio/platform/` layer adds multi-tenant primitives (logical `tenant_id` isolation), a free per-tenant `CapabilityMatrix` that probes every dependency before any spend, and a dossier-VALIDATE fidelity gate that composes existing scorers (`VisualRegressionTester` SSIM + `dino_embedder` DINOv2 + `clip_embedder` CLIP) against golden references plus a Blender-rendered view set. The existing `threed` TRELLIS venture is wrapped tenant-scoped. Nothing delivers without a `FidelityReport` + human approval.

**Tech Stack:** Python 3.11+, pytest, dataclasses (frozen), `trimesh` (mesh sanity), Blender headless (render), existing `skyyrose.core.{clip_embedder,dino_embedder,dossier_loader,catalog_loader,paths}`, existing `skyyrose.elite_studio.{budget,quality.visual_regression}`, `agents.trellis_agent.TrellisAgent`.

---

## Spec Deviation (one — read before starting)

**Same-engine (Modal/fal.ai) fallback wiring is deferred out of Phase 1.** Spec §12.8 placed it in Phase 1; this plan moves it to a post-Phase-1 flag-flip, gated on the Phase 0.2 consistency check (Task 2). Rationale: "transparent overflow" requires proof that hosted output matches local within the consistency bar — claiming it before that proof would violate the locked "no silent fallback" rule. Phase 1 ships local-TRELLIS-only; once the Phase 0.2 bar passes, enabling hosted overflow is a config change, not new architecture. **If you want hosted fallback wired inside Phase 1 anyway, add it as a task that routes 100% to local until the bar passes — flag this before execution.**

---

## Source of Truth & Reuse Map (read before Task 1)

Verified existing interfaces this plan integrates against — **do not reimplement these**:

| Need | Reuse | Signature (verified) |
|---|---|---|
| CSV row + dossier | `skyyrose.core.dossier_loader.get_product_with_dossier(sku)` | `-> dict` = `{**csv_row, "dossier": {...}, "_dossier": Dossier}`; raises `KeyError` (SKU absent) / `DossierMissingError` |
| Dossier shape | `Dossier` dataclass | fields: `sku,name,collection,slug,garment_type_lock,branding_block,negative_block,scene_pose,scene_setting,logo_reference,extra_logos` — **no palette/material field** |
| Catalog rows | `skyyrose.core.catalog_loader.read_catalog_rows()`, `CATALOG_CSV` | `-> Iterable[dict]` keyed by CSV columns incl `sku`, `dossier_slug` |
| Golden dir | `skyyrose.core.paths.GOLDEN_DIR` | `Path` → `skyyrose/elite_studio/assets/golden/{sku}/{angle}.jpg` (+ legacy `reference.jpg`=front) |
| SSIM vs golden | `skyyrose.elite_studio.quality.visual_regression.VisualRegressionTester` | `.compare_multi_angle({angle: path}, sku) -> MultiAngleResult`; `.coverage_for(sku) -> {angle: bool}`; **no-reference ⇒ `passed=True` (must override for our gate)** |
| Visual similarity | `skyyrose.core.dino_embedder` | `embed_image(path)->np.ndarray`, `cosine_similarity(a,b)->float` (mirror of clip_embedder API — confirm names in Task 8) |
| Text-image align | `skyyrose.core.clip_embedder` | `embed_image(path)->np.ndarray(512,)`, `embed_text(str)->np.ndarray`, `cosine_similarity(a,b)->float` |
| Cost ceiling | `skyyrose.elite_studio.budget` | `RunBudget(ceiling_usd=...)`, `.ensure_within_budget(cost_usd, stage)`, `.spend(cost_usd, stage)`, `.snapshot()`; `BudgetExceededError`; `DEFAULT_BUDGET_USD` |
| 3D engine | `agents.trellis_agent.TrellisAgent` | `.is_available()->bool`, `await .image_to_3d(image_path, product_name)->dict` (MeshyGenerationResult-shaped, `local_path` key); `TrellisAgentError`, `TrellisTimeoutError` |
| Venture base | `skyyrose.elite_studio.ventures._base` | `VentureManifest`, `AgentBinding`, `VentureState`, `PipelineResult` |

**Brand palette (canonical, from `CLAUDE.md`):** rose_gold `#B76E79`, dark `#0A0A0A`, silver `#C0C0C0`, crimson `#DC143C`, gold `#D4AF37`. Defined as a constant in Task 9 (not invented — documented brand tokens).

**Coverage granularity (Phase 1 decision):** coverage is **angle-level**, not face-level. A rendered view is *verified* if a golden reference exists for that angle (compared via SSIM/DINOv2); *inferred* if no reference exists (e.g. br-001 has front only → back/side are inferred). Inferred views are brand-palette-validated and always routed to human. Per-face ray-cast coverage is a noted future refinement, not Phase 1.

---

## File Structure

```
skyyrose/elite_studio/platform/
  __init__.py                       exports public API
  tenancy.py                        Tenant, FidelityThresholds, TenantRegistry        [Task 4]
  catalog_source.py                 CatalogSource protocol, SkyyRoseCatalogSource     [Task 5]
  capability.py                     CapabilityStatus, CapabilityMatrix                [Task 6]
  approval.py                       ApprovalRecord, ApprovalQueue                     [Task 12]
  service.py                        generate_3d() orchestrator                        [Task 13]
  fidelity/
    __init__.py
    render.py                       BlenderRenderer: GLB -> angle PNGs + coverage     [Task 7]
    metrics.py                      visible-face composite scorer                     [Task 8]
    validate.py                     hidden-face brand-palette + mesh sanity           [Task 9]
    report.py                       FidelityVerdict, FidelityReport, persistence      [Task 10]
    gate.py                         FidelityGate.evaluate() disposition               [Task 11]
scripts/
  phase0_pose_calibration.py        Phase 0.1 camera-pose calibration                 [Task 1]
  phase0_same_engine_consistency.py Phase 0.2 local vs hosted TRELLIS                 [Task 2]
  phase0_engine_ab.py               Phase 0.3 cross-engine A/B score table            [Task 3]
skyyrose/elite_studio/ventures/threed/
  service.py                        tenant-scoped wrapper over ThreeDPipeline         [Task 14]
tests/elite_studio/platform/
  test_tenancy.py test_catalog_source.py test_capability.py
  test_fidelity_render.py test_fidelity_metrics.py test_fidelity_validate.py
  test_fidelity_report.py test_fidelity_gate.py test_approval.py test_service.py
  test_threed_service.py
```

**Execution order:** Tasks build in dependency order. Phase 0 (Tasks 1-3) is harness/calibration and can run in parallel with early Phase 1 since it needs GPU+paid (STOP-AND-SHOW). Phase 1 core (Tasks 4-13) is strictly ordered. Task 14-15 wire the venture + fallback last.

---

## Phase 0 — Empirical Calibration (GPU + PAID, STOP-AND-SHOW gated)

> Phase 0 scripts gate every paid/GPU call behind explicit `y` confirmation and `RunBudget`. Their *pure logic* (scoring, table assembly, pose math) is unit-tested; the dispatch is not.

### Task 1: Camera-pose calibration (Phase 0.1 — runs before any score table)

**Files:**
- Create: `scripts/phase0_pose_calibration.py`
- Test: `tests/elite_studio/platform/test_pose_calibration.py`

Goal: produce a concrete Blender camera definition whose render of a mesh aligns to the SkyyRose techflat capture pose, validated by silhouette-IoU against the golden front. Output: a JSON `camera_profile` (location, rotation_euler, lens, ortho_scale) written to `skyyrose/elite_studio/platform/fidelity/camera_profiles/skyyrose.json`.

- [ ] **Step 1: Write the failing test (pure pose math — silhouette IoU)**

```python
# tests/elite_studio/platform/test_pose_calibration.py
import numpy as np
from scripts.phase0_pose_calibration import silhouette_iou


def test_silhouette_iou_identical_is_one():
    mask = np.zeros((64, 64), dtype=bool)
    mask[16:48, 16:48] = True
    assert silhouette_iou(mask, mask) == 1.0


def test_silhouette_iou_disjoint_is_zero():
    a = np.zeros((64, 64), dtype=bool); a[0:10, 0:10] = True
    b = np.zeros((64, 64), dtype=bool); b[40:50, 40:50] = True
    assert silhouette_iou(a, b) == 0.0


def test_silhouette_iou_half_overlap():
    a = np.zeros((10, 10), dtype=bool); a[:, 0:5] = True
    b = np.zeros((10, 10), dtype=bool); b[:, 2:7] = True
    # intersection cols 2-4 (3), union cols 0-6 (7) → 30/70
    assert round(silhouette_iou(a, b), 4) == round(30 / 70, 4)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_pose_calibration.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.phase0_pose_calibration'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/phase0_pose_calibration.py
"""Phase 0.1 — camera-pose calibration for the fidelity gate.

Establishes a Blender camera whose render of a generated mesh aligns to the
SkyyRose techflat capture pose, so visible-face render-compare is meaningful.
Validated by silhouette IoU against the golden front image. PAID/GPU dispatch
(running TRELLIS to get a calibration mesh) is STOP-AND-SHOW gated.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

PROFILE_PATH = (
    Path(__file__).resolve().parent.parent
    / "skyyrose/elite_studio/platform/fidelity/camera_profiles/skyyrose.json"
)

# Starting camera guess for flat front-facing techflats (orthographic front).
# Calibration refines ortho_scale to match the golden silhouette extent.
DEFAULT_CAMERA = {
    "type": "ORTHO",
    "location": [0.0, -2.5, 0.0],
    "rotation_euler": [1.5708, 0.0, 0.0],  # look down +Y
    "ortho_scale": 1.2,
    "lens": 50,
}


def silhouette_iou(a: np.ndarray, b: np.ndarray) -> float:
    """Intersection-over-union of two boolean silhouette masks."""
    a = a.astype(bool)
    b = b.astype(bool)
    union = np.logical_or(a, b).sum()
    if union == 0:
        return 1.0
    return float(np.logical_and(a, b).sum() / union)


def write_profile(profile: dict, path: Path = PROFILE_PATH) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    # Calibration mesh generation is GPU+paid → STOP-AND-SHOW. Until confirmed,
    # write the default profile and report it for human review.
    profile = dict(DEFAULT_CAMERA)
    out = write_profile(profile)
    print(f"camera profile written: {out}")
    print(json.dumps(profile, indent=2))
    print(
        "\nTo calibrate against a real mesh (GPU + paid TRELLIS run), re-run with "
        "--calibrate br-001 and confirm the STOP-AND-SHOW manifest."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_pose_calibration.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/phase0_pose_calibration.py tests/elite_studio/platform/test_pose_calibration.py
git commit -m "feat: phase0 camera-pose calibration (silhouette-IoU + default profile)"
```

---

### Task 2: Same-engine consistency check (Phase 0.2)

**Files:**
- Create: `scripts/phase0_same_engine_consistency.py`
- Test: `tests/elite_studio/platform/test_same_engine_consistency.py`

Goal: compare local-TRELLIS vs hosted-TRELLIS (Modal/fal.ai) output on the identical br-001 input. Pure logic = the consistency verdict from two scores; dispatch is STOP-AND-SHOW.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_same_engine_consistency.py
from scripts.phase0_same_engine_consistency import consistency_verdict


def test_high_similarity_allows_transparent_overflow():
    v = consistency_verdict(local_vs_hosted_score=0.97, bar=0.95)
    assert v["transparent_overflow_allowed"] is True


def test_below_bar_requires_human_signoff():
    v = consistency_verdict(local_vs_hosted_score=0.80, bar=0.95)
    assert v["transparent_overflow_allowed"] is False
    assert "human sign-off" in v["policy"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_same_engine_consistency.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/phase0_same_engine_consistency.py
"""Phase 0.2 — same-engine consistency: local TRELLIS vs hosted TRELLIS.

Closes the spec's unverified "identical fidelity profile" claim. If local-vs-
hosted similarity on the identical input clears the bar, hosted fallback is
allowed as transparent overflow; otherwise it keeps full human sign-off.
GPU + paid dispatch is STOP-AND-SHOW gated.
"""
from __future__ import annotations

import sys

CONSISTENCY_BAR = 0.95


def consistency_verdict(local_vs_hosted_score: float, bar: float = CONSISTENCY_BAR) -> dict:
    allowed = local_vs_hosted_score >= bar
    return {
        "score": round(local_vs_hosted_score, 4),
        "bar": bar,
        "transparent_overflow_allowed": allowed,
        "policy": (
            "hosted == local; transparent overflow permitted"
            if allowed
            else "hosted output diverges; hosted fallback requires human sign-off"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    print(
        "Same-engine consistency requires GPU + paid dispatch (local + hosted "
        "TRELLIS on br-001). Run under STOP-AND-SHOW; pass the two render paths "
        "to consistency_verdict() with a DINOv2 score from fidelity.metrics."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_same_engine_consistency.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/phase0_same_engine_consistency.py tests/elite_studio/platform/test_same_engine_consistency.py
git commit -m "feat: phase0 same-engine consistency verdict (transparent-overflow gate)"
```

---

### Task 3: Cross-engine A/B score table (Phase 0.3)

**Files:**
- Create: `scripts/phase0_engine_ab.py`
- Test: `tests/elite_studio/platform/test_engine_ab.py`

Goal: assemble a fidelity-score table across {TRELLIS, Tripo, Meshy} for br-001 + lh-004 → recommend the per-tenant threshold. Pure logic = table assembly + threshold recommendation; engine dispatch is STOP-AND-SHOW.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_engine_ab.py
from scripts.phase0_engine_ab import recommend_threshold, ABRow


def test_recommend_threshold_is_min_passing_minus_margin():
    rows = [
        ABRow(sku="br-001", engine="trellis", visible_score=0.91),
        ABRow(sku="lh-004", engine="trellis", visible_score=0.88),
        ABRow(sku="br-001", engine="meshy", visible_score=0.74),
    ]
    # threshold = lowest TRELLIS score (0.88) minus a 0.03 safety margin
    assert recommend_threshold(rows, engine="trellis", margin=0.03) == 0.85


def test_recommend_threshold_ignores_other_engines():
    rows = [ABRow(sku="br-001", engine="meshy", visible_score=0.50)]
    assert recommend_threshold(rows, engine="trellis", margin=0.03) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_engine_ab.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/phase0_engine_ab.py
"""Phase 0.3 — cross-engine fidelity A/B for threshold calibration.

Runs br-001 + lh-004 through {TRELLIS, Tripo, Meshy}, scores each mesh via the
fidelity gate in report-only mode against the golden references, and recommends
the per-tenant visible-face threshold from real garments. Engine dispatch is
STOP-AND-SHOW gated and accounted against RunBudget. Per-SKU costs (from
tasks/phase-e-manifest.md): Meshy $0.20, Tripo $0.25, TRELLIS-local $0.00.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ABRow:
    sku: str
    engine: str
    visible_score: float


def recommend_threshold(rows: list[ABRow], *, engine: str, margin: float = 0.03) -> float | None:
    """Lowest passing score for `engine` minus a safety margin, or None."""
    scores = [r.visible_score for r in rows if r.engine == engine]
    if not scores:
        return None
    return round(min(scores) - margin, 4)


def main(argv: list[str] | None = None) -> int:
    print(
        "Cross-engine A/B requires GPU + paid dispatch (TRELLIS/Tripo/Meshy on "
        "br-001 + lh-004). Run under STOP-AND-SHOW + RunBudget; feed each mesh "
        "to fidelity.gate in report-only mode, collect ABRow per (sku, engine), "
        "then call recommend_threshold(rows, engine='trellis')."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_engine_ab.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add scripts/phase0_engine_ab.py tests/elite_studio/platform/test_engine_ab.py
git commit -m "feat: phase0 cross-engine A/B score table + threshold recommendation"
```

---

## Phase 1 — Platform Vertical Slice

> **Pre-task (one-time):** the `threed` venture is built + tested (10/10 green) but uncommitted. Before Task 14 modifies it, commit the existing venture so the wrap is a clean diff: `git add skyyrose/elite_studio/ventures/threed/ skyyrose/elite_studio/ventures/__init__.py skyyrose/elite_studio/ventures/README.md && git commit -m "feat: TRELLIS-only threed venture (verify path + compute-gated generation)"`. Do NOT bundle the unrelated dirty-tree files (CLAUDE.md context blocks, golden binaries) — add the venture paths explicitly.

### Task 4: Tenancy primitives

**Files:**
- Create: `skyyrose/elite_studio/platform/__init__.py`, `skyyrose/elite_studio/platform/tenancy.py`
- Test: `tests/elite_studio/platform/test_tenancy.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_tenancy.py
import pytest
from skyyrose.elite_studio.platform.tenancy import (
    FidelityThresholds, Tenant, TenantRegistry, UnknownTenantError,
)


def test_default_thresholds_are_report_only():
    t = FidelityThresholds()
    assert t.visible_composite_min == 0.0  # report-only until Phase 0 calibrates


def test_registry_resolves_seeded_skyyrose():
    reg = TenantRegistry.default()
    tenant = reg.get("skyyrose")
    assert tenant.id == "skyyrose"
    assert "trellis" in tenant.enabled_engines


def test_registry_unknown_tenant_raises():
    reg = TenantRegistry.default()
    with pytest.raises(UnknownTenantError):
        reg.get("acme")


def test_tenant_output_root_is_namespaced(tmp_path):
    reg = TenantRegistry.default()
    tenant = reg.get("skyyrose")
    root = tenant.product_root(base=tmp_path, sku="br-001", version=2)
    assert root == tmp_path / "skyyrose" / "br-001" / "v2"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_tenancy.py -v`
Expected: FAIL — `ModuleNotFoundError: skyyrose.elite_studio.platform`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/__init__.py
"""Multi-tenant platform layer for Elite Studio (Replica Foundry).

Cross-venture primitives: tenancy, capability probing, fidelity gating,
approval. Each venture (threed first, 2D later) composes these through a
tenant-scoped service so every delivered asset is a verified replica.
"""
from __future__ import annotations
```

```python
# skyyrose/elite_studio/platform/tenancy.py
"""Tenant identity + per-tenant config. Phase 1 = logical isolation.

`tenant_id` namespaces every persisted artifact. SkyyRose is seeded as
tenant #1; adding tenant #2 = implement a CatalogSource + register a Tenant,
no core rewrite.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


class UnknownTenantError(KeyError):
    """Raised when a tenant_id is not registered."""


@dataclass(frozen=True)
class FidelityThresholds:
    """Per-tenant fidelity gate tuning. Default = report-only (0.0).

    Phase 0 calibration replaces `visible_composite_min` with a real number.
    Until then the gate scores everything and auto-rejects nothing.
    """

    visible_composite_min: float = 0.0


@dataclass(frozen=True)
class Tenant:
    """A brand served by the platform. SkyyRose = tenant #1."""

    id: str
    display_name: str
    catalog_source: str  # dotted import path to a CatalogSource impl
    reference_root: Path
    enabled_engines: frozenset[str]
    thresholds: FidelityThresholds = field(default_factory=FidelityThresholds)

    def product_root(self, base: Path, sku: str, version: int) -> Path:
        """Canonical delivered-asset path: <base>/<tenant>/<sku>/v<version>/."""
        return base / self.id / sku / f"v{version}"


@dataclass(frozen=True)
class TenantRegistry:
    """Resolves tenant_id -> Tenant. Phase 1 seeds SkyyRose only."""

    _tenants: dict[str, Tenant]

    @classmethod
    def default(cls) -> TenantRegistry:
        from skyyrose.core.paths import GOLDEN_DIR

        skyyrose = Tenant(
            id="skyyrose",
            display_name="SkyyRose",
            catalog_source="skyyrose.elite_studio.platform.catalog_source.SkyyRoseCatalogSource",
            reference_root=Path(GOLDEN_DIR),
            enabled_engines=frozenset({"trellis"}),
        )
        return cls(_tenants={skyyrose.id: skyyrose})

    def get(self, tenant_id: str) -> Tenant:
        try:
            return self._tenants[tenant_id]
        except KeyError as exc:
            raise UnknownTenantError(f"Unknown tenant: {tenant_id!r}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(self._tenants.keys())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_tenancy.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/__init__.py skyyrose/elite_studio/platform/tenancy.py tests/elite_studio/platform/test_tenancy.py
git commit -m "feat: tenancy primitives (Tenant, TenantRegistry, FidelityThresholds)"
```

---

### Task 5: CatalogSource protocol + SkyyRose impl

**Files:**
- Create: `skyyrose/elite_studio/platform/catalog_source.py`
- Test: `tests/elite_studio/platform/test_catalog_source.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_catalog_source.py
import pytest
from skyyrose.elite_studio.platform.catalog_source import (
    CatalogSource, ProductRecord, SkyyRoseCatalogSource,
)


def test_skyyrose_source_satisfies_protocol():
    assert isinstance(SkyyRoseCatalogSource(), CatalogSource)


def test_get_br001_returns_record_with_dossier():
    rec = SkyyRoseCatalogSource().get("br-001")
    assert isinstance(rec, ProductRecord)
    assert rec.sku == "br-001"
    assert rec.dossier  # non-empty dossier dict
    assert rec.garment_type_lock  # pulled from dossier


def test_get_missing_sku_raises_keyerror():
    with pytest.raises(KeyError):
        SkyyRoseCatalogSource().get("zz-999")


def test_references_returns_existing_views_only():
    src = SkyyRoseCatalogSource()
    refs = src.references("br-001")
    # br-001 has front only (no back.jpg) → exactly the views that exist on disk
    assert "front" in refs
    assert "back" not in refs  # br-001 has no back golden
    assert all(p.exists() for p in refs.values())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_catalog_source.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/catalog_source.py
"""Per-tenant catalog access. SkyyRose impl wraps the locked dossier loader.

The protocol generalizes ground-truth resolution so tenant #2 implements its
own source without touching the platform core. SkyyRose's source resolves the
LOCKED canonical sources only (CSV + dossier + golden); DossierMissingError
propagates (no silent fallback).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from skyyrose.core.paths import GOLDEN_DIR
from skyyrose.elite_studio.quality.visual_regression import CANONICAL_ANGLES


@dataclass(frozen=True)
class ProductRecord:
    """A resolved product: CSV row + parsed dossier + ground-truth refs."""

    sku: str
    name: str
    collection: str
    garment_type_lock: str
    dossier: dict  # full dossier.to_dict()
    row: dict = field(default_factory=dict, repr=False)


@runtime_checkable
class CatalogSource(Protocol):
    """Per-tenant ground-truth resolution."""

    def get(self, sku: str) -> ProductRecord: ...
    def references(self, sku: str) -> dict[str, Path]: ...


class SkyyRoseCatalogSource:
    """Tenant #1 source — reads catalog CSV + dossier + golden references."""

    def __init__(self, reference_root: Path | None = None) -> None:
        self._reference_root = Path(reference_root or GOLDEN_DIR)

    def get(self, sku: str) -> ProductRecord:
        from skyyrose.core.dossier_loader import get_product_with_dossier

        merged = get_product_with_dossier(sku)  # raises KeyError / DossierMissingError
        dossier = merged["dossier"]
        return ProductRecord(
            sku=sku,
            name=dossier.get("name", ""),
            collection=dossier.get("collection", ""),
            garment_type_lock=dossier.get("garment_type_lock", ""),
            dossier=dossier,
            row={k: v for k, v in merged.items() if k not in ("dossier", "_dossier")},
        )

    def references(self, sku: str) -> dict[str, Path]:
        """Return {angle: path} for every golden view that exists on disk.

        Honors the legacy reference.jpg=front convention. Missing views are
        omitted (not faked) — the gate marks omitted angles 'inferred'.
        """
        sku_dir = self._reference_root / sku
        out: dict[str, Path] = {}
        for angle in CANONICAL_ANGLES:
            candidate = sku_dir / f"{angle}.jpg"
            if candidate.is_file():
                out[angle] = candidate
            elif angle == "front" and (sku_dir / "reference.jpg").is_file():
                out[angle] = sku_dir / "reference.jpg"
        return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_catalog_source.py -v`
Expected: PASS (4 passed). If `br-001` dossier is absent in this checkout, the test environment is broken — fix the catalog, not the test.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/catalog_source.py tests/elite_studio/platform/test_catalog_source.py
git commit -m "feat: CatalogSource protocol + SkyyRoseCatalogSource (wraps dossier loader)"
```

---

### Task 6: CapabilityMatrix (verifiable endpoints)

**Files:**
- Create: `skyyrose/elite_studio/platform/capability.py`
- Test: `tests/elite_studio/platform/test_capability.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_capability.py
from pathlib import Path
from skyyrose.elite_studio.platform.capability import (
    CapabilityStatus, CapabilityMatrix,
)
from skyyrose.elite_studio.platform.tenancy import TenantRegistry


def test_capability_status_is_immutable():
    s = CapabilityStatus(name="engine", ok=True, detail="ready")
    assert s.ok and s.name == "engine"


def test_probe_returns_all_capabilities_without_spend():
    tenant = TenantRegistry.default().get("skyyrose")
    matrix = CapabilityMatrix(tenant).probe()
    names = {c.name for c in matrix.statuses}
    assert {"catalog", "reference_store", "fidelity_scorer", "engine_local"} <= names


def test_required_ok_false_when_a_required_cap_red():
    statuses = (
        CapabilityStatus(name="catalog", ok=False, detail="missing"),
        CapabilityStatus(name="engine_local", ok=True, detail="ready"),
    )
    matrix = CapabilityMatrix.__new__(CapabilityMatrix)
    object.__setattr__(matrix, "statuses", statuses)
    assert matrix.required_ok(required=("catalog",)) is False


def test_required_ok_true_when_all_required_green():
    statuses = (CapabilityStatus(name="catalog", ok=True, detail="ok"),)
    matrix = CapabilityMatrix.__new__(CapabilityMatrix)
    object.__setattr__(matrix, "statuses", statuses)
    assert matrix.required_ok(required=("catalog",)) is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_capability.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/capability.py
"""Per-tenant capability probing — FREE, no spend, queryable on demand.

Generalizes the threed verify_capability node: every dependency (catalog,
references, fidelity scorer, engines, approval store) gets a free probe.
Generation refuses to start if a required capability is red. You structurally
cannot spend on an unproven endpoint — the no-hallucination guarantee at the
infrastructure layer.
"""
from __future__ import annotations

import importlib
from dataclasses import dataclass

from skyyrose.elite_studio.platform.tenancy import Tenant


@dataclass(frozen=True)
class CapabilityStatus:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class CapabilityMatrix:
    """A frozen snapshot of one tenant's dependency readiness."""

    tenant: Tenant
    statuses: tuple[CapabilityStatus, ...] = ()

    def probe(self) -> "CapabilityMatrix":
        """Run all free probes and return a populated matrix (immutable copy)."""
        statuses = (
            self._probe_catalog(),
            self._probe_reference_store(),
            self._probe_fidelity_scorer(),
            self._probe_engine_local(),
        )
        return CapabilityMatrix(tenant=self.tenant, statuses=statuses)

    def required_ok(self, required: tuple[str, ...]) -> bool:
        by_name = {s.name: s for s in self.statuses}
        return all(by_name.get(name, CapabilityStatus(name, False, "absent")).ok for name in required)

    def _resolve_source(self):
        module_path, _, attr = self.tenant.catalog_source.rpartition(".")
        return getattr(importlib.import_module(module_path), attr)()

    def _probe_catalog(self) -> CapabilityStatus:
        try:
            self._resolve_source()
        except Exception as exc:  # noqa: BLE001 — probe must never raise
            return CapabilityStatus("catalog", False, f"source error: {exc}")
        return CapabilityStatus("catalog", True, "source importable")

    def _probe_reference_store(self) -> CapabilityStatus:
        root = self.tenant.reference_root
        ok = root.is_dir()
        return CapabilityStatus("reference_store", ok, str(root) if ok else f"missing: {root}")

    def _probe_fidelity_scorer(self) -> CapabilityStatus:
        try:
            importlib.import_module("skyyrose.core.dino_embedder")
            importlib.import_module("skyyrose.core.clip_embedder")
        except Exception as exc:  # noqa: BLE001
            return CapabilityStatus("fidelity_scorer", False, f"import error: {exc}")
        return CapabilityStatus("fidelity_scorer", True, "scorers importable")

    def _probe_engine_local(self) -> CapabilityStatus:
        if "trellis" not in self.tenant.enabled_engines:
            return CapabilityStatus("engine_local", False, "trellis not enabled")
        try:
            from agents.trellis_agent import TrellisAgent

            ready = TrellisAgent().is_available()
        except Exception as exc:  # noqa: BLE001
            return CapabilityStatus("engine_local", False, f"agent error: {exc}")
        return CapabilityStatus("engine_local", ready, "ready" if ready else "env not ready")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_capability.py -v`
Expected: PASS (4 passed). `engine_local` may be `ok=False` on a non-GPU box — the test asserts the capability is *present*, not green.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/capability.py tests/elite_studio/platform/test_capability.py
git commit -m "feat: CapabilityMatrix — free per-tenant dependency probe"
```

---

### Task 7: Blender renderer (GLB → angle views + coverage)

**Files:**
- Create: `skyyrose/elite_studio/platform/fidelity/__init__.py`, `skyyrose/elite_studio/platform/fidelity/render.py`
- Test: `tests/elite_studio/platform/test_fidelity_render.py`

> The Blender subprocess is the one heavy-compute piece. The renderer writes a temp Blender script (mirrors `agents.trellis_agent`'s temp-runner pattern), runs it headless, and returns angle→PNG paths. Tests mock the subprocess; the pure logic (which angles to render, coverage computation) is tested directly.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_fidelity_render.py
from pathlib import Path
from skyyrose.elite_studio.platform.fidelity.render import (
    RenderViews, coverage_from_references, RENDER_ANGLES,
)


def test_render_angles_include_front_back_sides():
    assert {"front", "back", "left", "right"} <= set(RENDER_ANGLES)


def test_coverage_marks_referenced_angles_verified():
    refs = {"front": Path("/x/front.jpg")}
    cov = coverage_from_references(refs, RENDER_ANGLES)
    assert cov["front"] is True   # has reference → verifiable
    assert cov["back"] is False   # no reference → inferred


def test_render_views_reports_inferred_angles():
    views = RenderViews(
        angle_paths={"front": Path("/r/front.png"), "back": Path("/r/back.png")},
        coverage={"front": True, "back": False},
    )
    assert views.inferred_angles() == ("back",)
    assert views.verified_angles() == ("front",)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_fidelity_render.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/fidelity/__init__.py
"""Fidelity gate: render → verify visible → validate hidden → dispose."""
from __future__ import annotations
```

```python
# skyyrose/elite_studio/platform/fidelity/render.py
"""Render a GLB to a canonical set of angle views via Blender headless.

Coverage is angle-level (Phase 1): an angle is 'verifiable' iff a golden
reference exists for it; otherwise it is 'inferred' and routed to validation +
human. The Blender subprocess writes PNGs; the camera profile comes from
phase0_pose_calibration. Mirrors the temp-runner-script subprocess pattern of
agents.trellis_agent.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

RENDER_ANGLES: tuple[str, ...] = ("front", "back", "left", "right", "detail-1")
_CAMERA_PROFILE = Path(__file__).parent / "camera_profiles" / "skyyrose.json"


def coverage_from_references(references: dict[str, Path], angles: tuple[str, ...]) -> dict[str, bool]:
    """angle -> True if a reference exists (verifiable), else False (inferred)."""
    return {angle: angle in references for angle in angles}


@dataclass(frozen=True)
class RenderViews:
    angle_paths: dict[str, Path]
    coverage: dict[str, bool]

    def verified_angles(self) -> tuple[str, ...]:
        return tuple(a for a, ok in self.coverage.items() if ok)

    def inferred_angles(self) -> tuple[str, ...]:
        return tuple(a for a, ok in self.coverage.items() if not ok)


class BlenderRenderError(RuntimeError):
    """Raised when Blender is unavailable or the render subprocess fails."""


class BlenderRenderer:
    """Headless Blender GLB → angle PNG renderer."""

    def __init__(self, blender_bin: str | None = None, output_dir: Path | str = "renders/fidelity"):
        self.blender_bin = blender_bin or os.environ.get("BLENDER_BIN") or shutil.which("blender")
        self.output_dir = Path(output_dir)

    def is_available(self) -> bool:
        return bool(self.blender_bin and Path(self.blender_bin).exists())

    def render(self, glb_path: str, references: dict[str, Path]) -> RenderViews:
        if not self.is_available():
            raise BlenderRenderError("blender binary not found (set BLENDER_BIN)")
        run_id = uuid.uuid4().hex[:10]
        out = (self.output_dir / run_id).resolve()
        out.mkdir(parents=True, exist_ok=True)
        script = self._build_script(glb_path=Path(glb_path).resolve(), out_dir=out)
        fd, tmp = tempfile.mkstemp(suffix=".py", prefix="fidelity_render_")
        with os.fdopen(fd, "w") as fh:
            fh.write(script)
        try:
            proc = subprocess.run(
                [self.blender_bin, "-b", "-P", tmp],
                check=False, capture_output=True, text=True, timeout=300,
            )
        finally:
            Path(tmp).unlink(missing_ok=True)
        angle_paths = {a: out / f"{a}.png" for a in RENDER_ANGLES if (out / f"{a}.png").is_file()}
        if proc.returncode != 0 or not angle_paths:
            raise BlenderRenderError(f"blender failed (rc={proc.returncode}): {proc.stderr[-1500:]}")
        return RenderViews(
            angle_paths=angle_paths,
            coverage=coverage_from_references(references, tuple(angle_paths.keys())),
        )

    @staticmethod
    def _build_script(glb_path: Path, out_dir: Path) -> str:
        profile = json.loads(_CAMERA_PROFILE.read_text()) if _CAMERA_PROFILE.is_file() else {}
        return f'''import bpy, math, json
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath={str(glb_path)!r})
prof = {json.dumps(profile)}
scene = bpy.context.scene
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = True
cam_data = bpy.data.cameras.new("fcam"); cam = bpy.data.objects.new("fcam", cam_data)
scene.collection.objects.link(cam); scene.camera = cam
if prof.get("type") == "ORTHO":
    cam_data.type = "ORTHO"; cam_data.ortho_scale = prof.get("ortho_scale", 1.2)
light_data = bpy.data.lights.new("key", type="SUN"); light = bpy.data.objects.new("key", light_data)
scene.collection.objects.link(light)
RADIUS = 2.5
ANGLES = {{"front": 0, "back": 180, "left": 90, "right": 270, "detail-1": 30}}
for name, deg in ANGLES.items():
    r = math.radians(deg)
    cam.location = (RADIUS*math.sin(r), -RADIUS*math.cos(r), 0.0)
    cam.rotation_euler = (math.radians(90), 0.0, r)
    scene.render.filepath = {str(out_dir)!r} + "/" + name + ".png"
    bpy.ops.render.render(write_still=True)
print("OK")
'''
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_fidelity_render.py -v`
Expected: PASS (3 passed). The pure logic is tested; the Blender subprocess is exercised only in gated integration.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/fidelity/__init__.py skyyrose/elite_studio/platform/fidelity/render.py tests/elite_studio/platform/test_fidelity_render.py
git commit -m "feat: Blender headless GLB->views renderer + angle-level coverage"
```

---

### Task 8: Visible-face composite metric

**Files:**
- Create: `skyyrose/elite_studio/platform/fidelity/metrics.py`
- Test: `tests/elite_studio/platform/test_fidelity_metrics.py`

> Composes existing scorers. Verified: `skyyrose/core/dino_embedder.py` exports `embed_image(source) -> np.ndarray` and `cosine_similarity(a, b) -> float` — exact mirror of `clip_embedder`. The imports in Step 3 are correct as written.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_fidelity_metrics.py
from skyyrose.elite_studio.platform.fidelity.metrics import composite_score, VisibleScore


def test_composite_is_weighted_mean_of_components():
    s = composite_score(dino=0.90, clip=0.80, ssim=0.70)
    # default weights dino .5 / clip .2 / ssim .3 → .45+.16+.21 = .82
    assert round(s, 4) == 0.82


def test_visible_score_passes_above_threshold():
    vs = VisibleScore(angle="front", dino=0.9, clip=0.85, ssim=0.88, composite=0.886)
    assert vs.passes(threshold=0.85) is True


def test_visible_score_fails_below_threshold():
    vs = VisibleScore(angle="front", dino=0.5, clip=0.5, ssim=0.5, composite=0.5)
    assert vs.passes(threshold=0.85) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_fidelity_metrics.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/fidelity/metrics.py
"""Visible-face fidelity metric: compose DINOv2 + CLIP + SSIM into a composite.

Reuses existing scorers — no new model deps:
  - DINOv2 (skyyrose.core.dino_embedder): strongest image-image similarity.
  - CLIP   (skyyrose.core.clip_embedder): secondary perceptual signal.
  - SSIM   (VisualRegressionTester): structural / embellishment placement.
A view scores only against a real golden reference; no reference ⇒ no score
(the view is 'inferred', handled by validate.py + human).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# Composite weights — DINOv2 dominates (best visual discriminator per its docstring).
W_DINO, W_CLIP, W_SSIM = 0.5, 0.2, 0.3


def composite_score(*, dino: float, clip: float, ssim: float) -> float:
    return round(W_DINO * dino + W_CLIP * clip + W_SSIM * ssim, 6)


@dataclass(frozen=True)
class VisibleScore:
    angle: str
    dino: float
    clip: float
    ssim: float
    composite: float

    def passes(self, threshold: float) -> bool:
        return self.composite >= threshold


def score_view(render_path: Path, reference_path: Path, *, sku: str, angle: str) -> VisibleScore:
    """Score one rendered view against its golden reference."""
    from skyyrose.core import clip_embedder, dino_embedder
    from skyyrose.elite_studio.quality.visual_regression import VisualRegressionTester

    dino = dino_embedder.cosine_similarity(
        dino_embedder.embed_image(render_path), dino_embedder.embed_image(reference_path)
    )
    clip = clip_embedder.cosine_similarity(
        clip_embedder.embed_image(render_path), clip_embedder.embed_image(reference_path)
    )
    ssim = VisualRegressionTester().compare(str(render_path), sku, angle=angle).ssim_score
    return VisibleScore(
        angle=angle, dino=float(dino), clip=float(clip), ssim=float(ssim),
        composite=composite_score(dino=float(dino), clip=float(clip), ssim=float(ssim)),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_fidelity_metrics.py -v`
Expected: PASS (3 passed). `score_view` (model inference) is exercised only in gated integration.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/fidelity/metrics.py tests/elite_studio/platform/test_fidelity_metrics.py
git commit -m "feat: visible-face composite metric (DINOv2 + CLIP + SSIM)"
```

---

### Task 9: Hidden-face validation (brand palette + mesh sanity)

**Files:**
- Create: `skyyrose/elite_studio/platform/fidelity/validate.py`
- Test: `tests/elite_studio/platform/test_fidelity_validate.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_fidelity_validate.py
from skyyrose.elite_studio.platform.fidelity.validate import (
    color_in_brand_palette, BRAND_PALETTE, mesh_sanity_ok,
)


def test_rose_gold_is_in_palette():
    assert color_in_brand_palette((183, 110, 121), tolerance=10) is True  # #B76E79


def test_off_brand_green_is_not_in_palette():
    assert color_in_brand_palette((0, 200, 0), tolerance=10) is False


def test_palette_contains_documented_brand_hexes():
    assert "#B76E79" in BRAND_PALETTE and "#D4AF37" in BRAND_PALETTE


def test_mesh_sanity_rejects_empty_mesh():
    ok, detail = mesh_sanity_ok(vertex_count=0, face_count=0, is_watertight=False)
    assert ok is False and "empty" in detail.lower()


def test_mesh_sanity_accepts_well_formed_mesh():
    ok, _ = mesh_sanity_ok(vertex_count=5000, face_count=9000, is_watertight=True)
    assert ok is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_fidelity_validate.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/fidelity/validate.py
"""Hidden-face validation: inferred views have no ground truth, so validate
them against the brand palette + garment-type plausibility + mesh sanity.

The dossier has no structured palette field (text blocks only), so the
documented canonical brand palette is the allowed-color set. Inferred views
always route to human regardless — this validation flags obvious violations
early, it does not grant auto-pass.
"""
from __future__ import annotations

# Canonical brand palette (CLAUDE.md brand tokens).
BRAND_PALETTE: dict[str, tuple[int, int, int]] = {
    "#B76E79": (183, 110, 121),  # rose gold
    "#0A0A0A": (10, 10, 10),     # dark
    "#C0C0C0": (192, 192, 192),  # silver
    "#DC143C": (220, 20, 60),    # crimson
    "#D4AF37": (212, 175, 55),   # gold
    "#FFFFFF": (255, 255, 255),  # white (garment base)
}


def color_in_brand_palette(rgb: tuple[int, int, int], *, tolerance: int = 24) -> bool:
    """True if rgb is within Chebyshev `tolerance` of any brand color."""
    return any(
        all(abs(c - b) <= tolerance for c, b in zip(rgb, brand))
        for brand in BRAND_PALETTE.values()
    )


def mesh_sanity_ok(*, vertex_count: int, face_count: int, is_watertight: bool) -> tuple[bool, str]:
    """Reject degenerate meshes. Returns (ok, detail)."""
    if vertex_count == 0 or face_count == 0:
        return False, "empty mesh (no geometry)"
    if face_count < 100:
        return False, f"degenerate mesh ({face_count} faces)"
    if not is_watertight:
        return True, "non-watertight (acceptable for open garment surfaces, flagged)"
    return True, "ok"


def inspect_glb_geometry(glb_path: str) -> dict:
    """Load a GLB with trimesh and return geometry stats for mesh_sanity_ok."""
    import trimesh  # type: ignore[import]

    scene = trimesh.load(glb_path, force="scene")
    geo = scene.dump(concatenate=True) if hasattr(scene, "dump") else scene
    return {
        "vertex_count": int(len(geo.vertices)),
        "face_count": int(len(geo.faces)),
        "is_watertight": bool(getattr(geo, "is_watertight", False)),
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_fidelity_validate.py -v`
Expected: PASS (5 passed). `inspect_glb_geometry` (trimesh load) is exercised in gated integration.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/fidelity/validate.py tests/elite_studio/platform/test_fidelity_validate.py
git commit -m "feat: hidden-face validation (brand palette + mesh sanity)"
```

---

### Task 10: FidelityReport model + persistence

**Files:**
- Create: `skyyrose/elite_studio/platform/fidelity/report.py`
- Test: `tests/elite_studio/platform/test_fidelity_report.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_fidelity_report.py
import json
from skyyrose.elite_studio.platform.fidelity.report import (
    FidelityReport, FidelityVerdict,
)


def test_verdict_enum_values():
    assert FidelityVerdict.PASS_PENDING_HUMAN.value == "pass_pending_human"
    assert FidelityVerdict.REJECT.value == "reject"
    assert FidelityVerdict.HUMAN_QUEUE.value == "human_queue"


def test_report_roundtrips_to_json(tmp_path):
    rep = FidelityReport(
        tenant_id="skyyrose", sku="br-001", mesh_path="/r/x.glb",
        verdict=FidelityVerdict.HUMAN_QUEUE, composite_by_angle={"front": 0.91},
        verified_angles=("front",), inferred_angles=("back",),
        violations=(), attempts=1,
    )
    path = rep.persist(base=tmp_path)
    assert path.exists()
    loaded = json.loads(path.read_text())
    assert loaded["verdict"] == "human_queue"
    assert loaded["sku"] == "br-001"
    assert loaded["inferred_angles"] == ["back"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_fidelity_report.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/fidelity/report.py
"""FidelityReport — the audit trail behind '100% replica'.

Persisted per asset, tenant-namespaced. Nothing delivers without one + a human
approval. Records every visible-face score, which angles were verified vs
inferred, hidden-face violations, and the regeneration attempt count.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path


class FidelityVerdict(StrEnum):
    PASS_PENDING_HUMAN = "pass_pending_human"  # visible passed, hidden in-range
    HUMAN_QUEUE = "human_queue"                # visible passed, hidden flagged
    REJECT = "reject"                          # visible failed


@dataclass(frozen=True)
class FidelityReport:
    tenant_id: str
    sku: str
    mesh_path: str
    verdict: FidelityVerdict
    composite_by_angle: dict[str, float]
    verified_angles: tuple[str, ...]
    inferred_angles: tuple[str, ...]
    violations: tuple[str, ...]
    attempts: int
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        d["verified_angles"] = list(self.verified_angles)
        d["inferred_angles"] = list(self.inferred_angles)
        d["violations"] = list(self.violations)
        return d

    def persist(self, base: Path, *, suffix: str = "") -> Path:
        """Write to <base>/<tenant>/<sku>/fidelity_report{suffix}.json.

        `suffix` (e.g. "_attempt2") preserves each regeneration attempt's
        report instead of clobbering — the audit trail keeps every try's
        scores, as the spec requires.
        """
        out_dir = base / self.tenant_id / self.sku
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"fidelity_report{suffix}.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_fidelity_report.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/fidelity/report.py tests/elite_studio/platform/test_fidelity_report.py
git commit -m "feat: FidelityReport model + tenant-namespaced persistence"
```

---

### Task 11: FidelityGate disposition

**Files:**
- Create: `skyyrose/elite_studio/platform/fidelity/gate.py`
- Test: `tests/elite_studio/platform/test_fidelity_gate.py`

> The gate's disposition logic is pure and fully testable without GPU. It takes already-computed `VisibleScore`s + coverage + violations and decides the verdict. The orchestration that *produces* those inputs (render + score + validate) lives in `evaluate()` and is exercised in gated integration; the disposition is unit-tested directly.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_fidelity_gate.py
from skyyrose.elite_studio.platform.fidelity.gate import dispose
from skyyrose.elite_studio.platform.fidelity.metrics import VisibleScore
from skyyrose.elite_studio.platform.fidelity.report import FidelityVerdict


def _vs(angle, composite):
    return VisibleScore(angle=angle, dino=composite, clip=composite, ssim=composite, composite=composite)


def test_visible_fail_is_reject():
    v = dispose(visible=[_vs("front", 0.50)], inferred_angles=("back",), violations=(), threshold=0.85)
    assert v is FidelityVerdict.REJECT


def test_visible_pass_with_violation_is_human_queue():
    v = dispose(visible=[_vs("front", 0.92)], inferred_angles=("back",), violations=("off-brand color on back",), threshold=0.85)
    assert v is FidelityVerdict.HUMAN_QUEUE


def test_visible_pass_inferred_present_is_human_queue():
    # ANY inferred angle forces human review even with no explicit violation
    v = dispose(visible=[_vs("front", 0.92)], inferred_angles=("back",), violations=(), threshold=0.85)
    assert v is FidelityVerdict.HUMAN_QUEUE


def test_full_coverage_clean_is_pass_pending_human():
    v = dispose(visible=[_vs("front", 0.92), _vs("back", 0.90)], inferred_angles=(), violations=(), threshold=0.85)
    assert v is FidelityVerdict.PASS_PENDING_HUMAN


def test_report_only_threshold_zero_never_rejects_on_score():
    v = dispose(visible=[_vs("front", 0.10)], inferred_angles=(), violations=(), threshold=0.0)
    assert v is FidelityVerdict.PASS_PENDING_HUMAN
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_fidelity_gate.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/fidelity/gate.py
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


def evaluate(tenant, sku: str, mesh_path: str, *, attempt: int = 1, renderer=None) -> FidelityReport:
    """Full dossier-VALIDATE pipeline → FidelityReport.

    GATED-INTEGRATION: touches Blender + CLIP/DINOv2 models, so it is exercised
    in gated integration (real GLB), never in CI. The pure `dispose` it calls is
    unit-tested above. render views → score visible (vs golden) → mesh sanity →
    dispose → report.
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
        tenant_id=tenant.id, sku=sku, mesh_path=mesh_path, verdict=verdict,
        composite_by_angle=composite_by_angle,
        verified_angles=views.verified_angles(), inferred_angles=views.inferred_angles(),
        violations=tuple(violations), attempts=attempt,
    )
```

> `dispose` is unit-tested (above). `evaluate` is the integration composition (Blender + models) — verified in gated integration on a real br-001 GLB, not in CI. It is the production `evaluate_fn` consumed by Task 14's `default_replica_runner`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_fidelity_gate.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/fidelity/gate.py tests/elite_studio/platform/test_fidelity_gate.py
git commit -m "feat: FidelityGate disposition (reject/human-queue/pass-pending)"
```

---

### Task 12: Approval queue

**Files:**
- Create: `skyyrose/elite_studio/platform/approval.py`
- Test: `tests/elite_studio/platform/test_approval.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_approval.py
from skyyrose.elite_studio.platform.approval import ApprovalQueue, ApprovalRecord


def test_enqueue_creates_pending_record(tmp_path):
    q = ApprovalQueue(store_dir=tmp_path)
    rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path="/r/fr.json")
    assert rec.status == "pending"
    assert q.get(rec.id).status == "pending"


def test_approve_transitions_to_approved(tmp_path):
    q = ApprovalQueue(store_dir=tmp_path)
    rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path="/r/fr.json")
    q.approve(rec.id, reviewer="corey")
    assert q.get(rec.id).status == "approved"


def test_reject_transitions_to_rejected(tmp_path):
    q = ApprovalQueue(store_dir=tmp_path)
    rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path="/r/fr.json")
    q.reject(rec.id, reviewer="corey", reason="back panel wrong")
    got = q.get(rec.id)
    assert got.status == "rejected" and got.reason == "back panel wrong"


def test_pending_lists_only_pending(tmp_path):
    q = ApprovalQueue(store_dir=tmp_path)
    a = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path="/r/a.json")
    q.enqueue(tenant_id="skyyrose", sku="lh-004", report_path="/r/b.json")
    q.approve(a.id, reviewer="corey")
    pending = q.pending(tenant_id="skyyrose")
    assert {r.sku for r in pending} == {"lh-004"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_approval.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/approval.py
"""Human approval queue — the mandatory gate before any delivery.

File-backed JSON store (Phase 1 logical isolation; a DB-backed queue is a
later phase). No asset is promoted to the canonical product tree until a
record here is 'approved'.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class ApprovalRecord:
    id: str
    tenant_id: str
    sku: str
    report_path: str
    status: str  # pending | approved | rejected
    reviewer: str = ""
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def with_status(self, status: str, *, reviewer: str = "", reason: str = "") -> "ApprovalRecord":
        return ApprovalRecord(
            id=self.id, tenant_id=self.tenant_id, sku=self.sku, report_path=self.report_path,
            status=status, reviewer=reviewer, reason=reason, created_at=self.created_at,
        )


class ApprovalQueue:
    def __init__(self, store_dir: Path | str = "renders/fidelity/approvals") -> None:
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, record_id: str) -> Path:
        return self.store_dir / f"{record_id}.json"

    def _write(self, rec: ApprovalRecord) -> None:
        self._path(rec.id).write_text(json.dumps(asdict(rec), indent=2), encoding="utf-8")

    def enqueue(self, *, tenant_id: str, sku: str, report_path: str) -> ApprovalRecord:
        rec = ApprovalRecord(
            id=uuid.uuid4().hex[:12], tenant_id=tenant_id, sku=sku,
            report_path=report_path, status="pending",
        )
        self._write(rec)
        return rec

    def get(self, record_id: str) -> ApprovalRecord:
        return ApprovalRecord(**json.loads(self._path(record_id).read_text()))

    def approve(self, record_id: str, *, reviewer: str) -> ApprovalRecord:
        rec = self.get(record_id).with_status("approved", reviewer=reviewer)
        self._write(rec)
        return rec

    def reject(self, record_id: str, *, reviewer: str, reason: str) -> ApprovalRecord:
        rec = self.get(record_id).with_status("rejected", reviewer=reviewer, reason=reason)
        self._write(rec)
        return rec

    def pending(self, *, tenant_id: str) -> tuple[ApprovalRecord, ...]:
        out = []
        for p in sorted(self.store_dir.glob("*.json")):
            rec = ApprovalRecord(**json.loads(p.read_text()))
            if rec.tenant_id == tenant_id and rec.status == "pending":
                out.append(rec)
        return tuple(out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_approval.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/approval.py tests/elite_studio/platform/test_approval.py
git commit -m "feat: file-backed human approval queue"
```

---

### Task 13: Service orchestrator

**Files:**
- Create: `skyyrose/elite_studio/platform/service.py`
- Modify: `skyyrose/elite_studio/platform/__init__.py` (export `generate_3d`, `GenerationResult`)
- Test: `tests/elite_studio/platform/test_service.py`

> `generate_3d` is the public entry: resolve tenant → probe capability (refuse on red, zero spend) → on green+`generate`, **delegate to the venture replica runner** (Task 14), which does generate → gate → approval. The runner is injected (`replica_runner`) so this task's orchestration is tested with a fake, no GPU; the real runner is resolved lazily by default (no import-time dependency on the venture). Returns a `GenerationResult` envelope (status + report_path + approval_id).

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_service.py
from dataclasses import dataclass
from skyyrose.elite_studio.platform.service import generate_3d, GenerationResult
from skyyrose.elite_studio.platform.capability import CapabilityMatrix, CapabilityStatus
from skyyrose.elite_studio.platform.tenancy import TenantRegistry


class _FakeMatrix(CapabilityMatrix):
    def probe(self):
        return self


def _green_matrix(tenant):
    statuses = tuple(
        CapabilityStatus(n, True, "ok")
        for n in ("catalog", "reference_store", "fidelity_scorer", "engine_local")
    )
    return _FakeMatrix(tenant=tenant, statuses=statuses)


@dataclass
class _FakeOutcome:
    status: str = "queued_for_human"
    report_path: str = "/r/skyyrose/br-001/fidelity_report_attempt1.json"
    approval_id: str = "ap123"


def test_refuses_when_required_capability_red():
    tenant = TenantRegistry.default().get("skyyrose")
    red = _FakeMatrix(tenant=tenant, statuses=(CapabilityStatus("engine_local", False, "no gpu"),))
    res = generate_3d("skyyrose", "br-001", source_image="/g/front.jpg", generate=True, matrix=red)
    assert res.status == "capability_unavailable"
    assert res.report_path == ""


def test_does_not_generate_when_gate_off():
    tenant = TenantRegistry.default().get("skyyrose")
    res = generate_3d("skyyrose", "br-001", generate=False, matrix=_green_matrix(tenant))
    assert res.status == "not_requested"


def test_unknown_tenant_is_error():
    res = generate_3d("acme", "br-001", generate=True)
    assert res.status == "unknown_tenant"


def test_missing_source_image_is_error():
    tenant = TenantRegistry.default().get("skyyrose")
    res = generate_3d("skyyrose", "br-001", generate=True, matrix=_green_matrix(tenant))
    assert res.status == "missing_source_image"


def test_delegates_to_replica_runner_on_green():
    tenant = TenantRegistry.default().get("skyyrose")
    captured = {}

    def fake_runner(*, tenant, sku, source_image):
        captured["sku"] = sku
        return _FakeOutcome()

    res = generate_3d(
        "skyyrose", "br-001", source_image="/g/front.jpg", generate=True,
        matrix=_green_matrix(tenant), replica_runner=fake_runner,
    )
    assert captured["sku"] == "br-001"
    assert res.status == "queued_for_human"
    assert res.approval_id == "ap123"
    assert res.report_path.endswith("fidelity_report_attempt1.json")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/service.py
"""Tenant-scoped 3D generation orchestrator (public entry point).

resolve tenant -> probe capability (refuse on red, zero spend) -> on
green+generate, delegate to the venture replica runner (generate -> fidelity
gate -> approval). No silent fallback: unknown tenant, red capability, and
missing source image all produce honest hard-states. The replica runner is
injectable for testing; the real one is resolved lazily so this module has no
import-time dependency on the venture wiring.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from skyyrose.elite_studio.platform.capability import CapabilityMatrix
from skyyrose.elite_studio.platform.tenancy import Tenant, TenantRegistry, UnknownTenantError

logger = logging.getLogger(__name__)

REQUIRED_CAPS = ("catalog", "reference_store", "fidelity_scorer", "engine_local")


class _Outcome(Protocol):
    status: str
    report_path: str
    approval_id: str


ReplicaRunner = Callable[..., _Outcome]


@dataclass(frozen=True)
class GenerationResult:
    tenant_id: str
    sku: str
    status: str
    report_path: str = ""
    approval_id: str = ""


def _default_replica_runner(*, tenant: Tenant, sku: str, source_image: str) -> _Outcome:
    """Lazily resolve the real venture replica runner (avoids import cycle)."""
    from skyyrose.elite_studio.ventures.threed.service import default_replica_runner

    return default_replica_runner(tenant=tenant, sku=sku, source_image=source_image)


def generate_3d(
    tenant_id: str,
    sku: str,
    *,
    source_image: str | None = None,
    generate: bool = False,
    registry: TenantRegistry | None = None,
    matrix: CapabilityMatrix | None = None,
    replica_runner: ReplicaRunner | None = None,
) -> GenerationResult:
    registry = registry or TenantRegistry.default()
    try:
        tenant = registry.get(tenant_id)
    except UnknownTenantError:
        return GenerationResult(tenant_id, sku, status="unknown_tenant")

    probed = (matrix or CapabilityMatrix(tenant)).probe()
    if not probed.required_ok(REQUIRED_CAPS):
        red = [s.name for s in probed.statuses if not s.ok]
        logger.info("generate_3d refused: red caps %s", red)
        return GenerationResult(tenant_id, sku, status="capability_unavailable")

    if not generate:
        return GenerationResult(tenant_id, sku, status="not_requested")

    if not source_image:
        return GenerationResult(tenant_id, sku, status="missing_source_image")

    runner = replica_runner or _default_replica_runner
    outcome = runner(tenant=tenant, sku=sku, source_image=source_image)
    return GenerationResult(
        tenant_id, sku, status=outcome.status,
        report_path=outcome.report_path, approval_id=outcome.approval_id,
    )
```

```python
# skyyrose/elite_studio/platform/__init__.py  (append)
from skyyrose.elite_studio.platform.service import GenerationResult, generate_3d  # noqa: E402

__all__ = ["GenerationResult", "generate_3d"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_service.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/service.py skyyrose/elite_studio/platform/__init__.py tests/elite_studio/platform/test_service.py
git commit -m "feat: tenant-scoped generate_3d orchestrator (refuse-on-red, gated)"
```

---

### Task 14: Wire the full generate→gate→approve path into the threed venture service

**Files:**
- Create: `skyyrose/elite_studio/ventures/threed/service.py`
- Test: `tests/elite_studio/platform/test_threed_service.py`

> This is where the engine, gate, and approval compose into the real heavy path. The engine call (`TrellisAgent.image_to_3d`) and the fidelity `evaluate` are injected as callables so the orchestration is tested with fakes; the production wiring uses the real ones. Local TRELLIS generation is free, so `run_replica` makes no `RunBudget` call — budget guarding applies only to Phase 0 paid dispatch and the future hosted-overflow path. Per spec §6, a `REJECT` verdict triggers bounded regeneration (`max_attempts`, default 2) with the attempt count recorded in the report; exhaustion escalates (status `rejected`). The fixed threshold across attempts + inferred-faces-always-human (Task 11) is what keeps retry from laundering a hallucinated panel.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_threed_service.py
from skyyrose.elite_studio.ventures.threed.service import (
    run_replica, ReplicaOutcome, default_replica_runner,
)
from skyyrose.elite_studio.platform.fidelity.report import FidelityReport, FidelityVerdict
from skyyrose.elite_studio.platform.tenancy import TenantRegistry


def _fake_generate(image_path, product_name):
    return {"local_path": "/tmp/mesh.glb", "status": "completed"}


def _fake_evaluate(tenant_id, sku, mesh_path):
    return FidelityReport(
        tenant_id=tenant_id, sku=sku, mesh_path=mesh_path,
        verdict=FidelityVerdict.HUMAN_QUEUE, composite_by_angle={"front": 0.91},
        verified_angles=("front",), inferred_angles=("back",), violations=(), attempts=1,
    )


def test_human_queue_verdict_enqueues_not_delivers(tmp_path):
    outcome = run_replica(
        tenant_id="skyyrose", sku="br-001", source_image="/g/front.jpg",
        generate_fn=_fake_generate, evaluate_fn=_fake_evaluate,
        report_base=tmp_path, approval_dir=tmp_path / "ap",
    )
    assert outcome.status == "queued_for_human"
    assert outcome.approval_id
    assert outcome.delivered_path == ""


def test_reject_verdict_does_not_enqueue(tmp_path):
    def _reject_eval(tenant_id, sku, mesh_path):
        return FidelityReport(
            tenant_id=tenant_id, sku=sku, mesh_path=mesh_path,
            verdict=FidelityVerdict.REJECT, composite_by_angle={"front": 0.4},
            verified_angles=("front",), inferred_angles=(), violations=(), attempts=1,
        )
    outcome = run_replica(
        tenant_id="skyyrose", sku="br-001", source_image="/g/front.jpg",
        generate_fn=_fake_generate, evaluate_fn=_reject_eval,
        report_base=tmp_path, approval_dir=tmp_path / "ap",
    )
    assert outcome.status == "rejected"
    assert outcome.approval_id == ""


def test_default_replica_runner_wires_engine_and_gate_into_run_replica(tmp_path):
    tenant = TenantRegistry.default().get("skyyrose")
    outcome = default_replica_runner(
        tenant=tenant, sku="br-001", source_image="/g/front.jpg",
        generate_fn=_fake_generate, evaluate_fn=_fake_evaluate,
        report_base=tmp_path, approval_dir=tmp_path / "ap",
    )
    assert outcome.status == "queued_for_human"
    assert outcome.approval_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_threed_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/ventures/threed/service.py
"""Tenant-scoped replica path: generate -> fidelity gate -> approval.

Composes the existing ThreeDPipeline engine with the platform fidelity gate +
approval queue. Verdict routing: REJECT -> stop (regen handled upstream);
HUMAN_QUEUE / PASS_PENDING_HUMAN -> enqueue for human sign-off. Delivery to the
canonical product tree happens ONLY after a human approves (separate step).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from skyyrose.elite_studio.platform.approval import ApprovalQueue
from skyyrose.elite_studio.platform.fidelity.report import FidelityReport, FidelityVerdict

logger = logging.getLogger(__name__)

GenerateFn = Callable[[str, str], dict]            # (image_path, product_name) -> result dict
EvaluateFn = Callable[[str, str, str], FidelityReport]  # (tenant, sku, mesh_path) -> report


@dataclass(frozen=True)
class ReplicaOutcome:
    tenant_id: str
    sku: str
    status: str  # generated | rejected | queued_for_human | engine_failed
    report_path: str = ""
    approval_id: str = ""
    delivered_path: str = ""  # populated only after human approval (separate step)


def run_replica(
    *,
    tenant_id: str,
    sku: str,
    source_image: str,
    generate_fn: GenerateFn,
    evaluate_fn: EvaluateFn,
    report_base: Path,
    approval_dir: Path,
    max_attempts: int = 2,
) -> ReplicaOutcome:
    last_report_path = ""
    for _attempt in range(1, max_attempts + 1):
        result = generate_fn(source_image, sku)
        mesh_path = str(result.get("local_path", ""))
        if not mesh_path or result.get("status") != "completed":
            return ReplicaOutcome(tenant_id, sku, status="engine_failed")

        report = evaluate_fn(tenant_id, sku, mesh_path)
        last_report_path = str(report.persist(base=report_base, suffix=f"_attempt{_attempt}"))

        if report.verdict is FidelityVerdict.REJECT:
            # Bounded regen: threshold is FIXED across attempts. Retry is honest
            # only because the front has ground truth; exhausting attempts
            # escalates (status 'rejected') — never auto-ships a best-of-failed.
            continue

        queue = ApprovalQueue(store_dir=approval_dir)
        rec = queue.enqueue(tenant_id=tenant_id, sku=sku, report_path=last_report_path)
        return ReplicaOutcome(
            tenant_id, sku, status="queued_for_human",
            report_path=last_report_path, approval_id=rec.id,
        )

    return ReplicaOutcome(tenant_id, sku, status="rejected", report_path=last_report_path)


def _trellis_generate_fn() -> GenerateFn:
    """Build a generate_fn backed by the local self-hosted TRELLIS engine."""
    import asyncio

    from agents.trellis_agent import TrellisAgent

    agent = TrellisAgent()

    def _gen(image_path: str, sku: str) -> dict:
        return asyncio.run(agent.image_to_3d(image_path=image_path, product_name=sku))

    return _gen


def _gate_evaluate_fn(tenant) -> EvaluateFn:
    """Build an evaluate_fn backed by the fidelity gate's full evaluate()."""
    from skyyrose.elite_studio.platform.fidelity import gate

    def _eval(tenant_id: str, sku: str, mesh_path: str) -> FidelityReport:
        return gate.evaluate(tenant, sku, mesh_path)

    return _eval


def default_replica_runner(
    *,
    tenant,
    sku: str,
    source_image: str,
    generate_fn: GenerateFn | None = None,
    evaluate_fn: EvaluateFn | None = None,
    report_base: Path | None = None,
    approval_dir: Path | None = None,
) -> ReplicaOutcome:
    """Production runner: real local-TRELLIS engine + fidelity gate via run_replica.

    Resolved lazily by `platform.service.generate_3d`. The seams (generate_fn,
    evaluate_fn, dirs) are injectable so the wiring is testable without GPU; the
    defaults use the real engine + gate (gated-integration).
    """
    from skyyrose.elite_studio.config import OUTPUT_DIR

    base = report_base or (Path(OUTPUT_DIR) / "fidelity")
    return run_replica(
        tenant_id=tenant.id,
        sku=sku,
        source_image=source_image,
        generate_fn=generate_fn or _trellis_generate_fn(),
        evaluate_fn=evaluate_fn or _gate_evaluate_fn(tenant),
        report_base=base,
        approval_dir=approval_dir or (base / "approvals"),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_threed_service.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/ventures/threed/service.py tests/elite_studio/platform/test_threed_service.py
git commit -m "feat: tenant-scoped threed replica service (generate->gate->approval)"
```

---

### Task 15: Post-approval delivery to canonical product tree

**Files:**
- Create: `skyyrose/elite_studio/platform/delivery.py`
- Test: `tests/elite_studio/platform/test_delivery.py`

> The ONLY path that writes the canonical product tree. Runs solely after a human flips an `ApprovalRecord` to `approved`; copies the approved mesh into `products/<tenant>/<sku>/v{n}/` (next version, never overwriting). Closes the spec §7 "on approve → promote" step.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/platform/test_delivery.py
import json
import pytest
from skyyrose.elite_studio.platform.delivery import deliver_approved, NotApprovedError
from skyyrose.elite_studio.platform.approval import ApprovalQueue


def _make_report(tmp_path, mesh):
    rp = tmp_path / "fidelity_report_attempt1.json"
    rp.write_text(json.dumps({"mesh_path": str(mesh)}))
    return rp


def test_delivers_approved_mesh_to_versioned_tree(tmp_path):
    mesh = tmp_path / "m.glb"; mesh.write_bytes(b"glb")
    q = ApprovalQueue(store_dir=tmp_path / "ap")
    rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path=str(_make_report(tmp_path, mesh)))
    q.approve(rec.id, reviewer="corey")
    products = tmp_path / "products"
    dest = deliver_approved(rec.id, queue=q, products_base=products)
    assert dest == products / "skyyrose" / "br-001" / "v1" / "m.glb"
    assert dest.exists()


def test_second_delivery_bumps_version(tmp_path):
    mesh = tmp_path / "m.glb"; mesh.write_bytes(b"glb")
    q = ApprovalQueue(store_dir=tmp_path / "ap")
    products = tmp_path / "products"
    dest = None
    for _ in range(2):
        rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path=str(_make_report(tmp_path, mesh)))
        q.approve(rec.id, reviewer="corey")
        dest = deliver_approved(rec.id, queue=q, products_base=products)
    assert dest == products / "skyyrose" / "br-001" / "v2" / "m.glb"


def test_refuses_unapproved_record(tmp_path):
    mesh = tmp_path / "m.glb"; mesh.write_bytes(b"glb")
    q = ApprovalQueue(store_dir=tmp_path / "ap")
    rec = q.enqueue(tenant_id="skyyrose", sku="br-001", report_path=str(_make_report(tmp_path, mesh)))
    with pytest.raises(NotApprovedError):
        deliver_approved(rec.id, queue=q, products_base=tmp_path / "products")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/platform/test_delivery.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# skyyrose/elite_studio/platform/delivery.py
"""Post-approval delivery: promote an approved mesh into the canonical tree.

Runs ONLY after a human approves (ApprovalRecord.status == 'approved'). Copies
the approved mesh to products/<tenant>/<sku>/v{n}/ (next version, never
overwriting). This is the only writer of the canonical product tree — no
unapproved asset can reach it.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from skyyrose.elite_studio.platform.approval import ApprovalQueue
from skyyrose.elite_studio.platform.tenancy import TenantRegistry


class NotApprovedError(RuntimeError):
    """Raised when delivery is attempted for a non-approved record."""


def _next_version(sku_dir: Path) -> int:
    if not sku_dir.is_dir():
        return 1
    versions = [int(p.name[1:]) for p in sku_dir.glob("v*") if p.name[1:].isdigit()]
    return (max(versions) + 1) if versions else 1


def deliver_approved(
    approval_id: str,
    *,
    queue: ApprovalQueue,
    products_base: Path,
    registry: TenantRegistry | None = None,
) -> Path:
    """Promote the approved record's mesh into products/<tenant>/<sku>/v{n}/."""
    registry = registry or TenantRegistry.default()
    record = queue.get(approval_id)
    if record.status != "approved":
        raise NotApprovedError(f"record {approval_id} is {record.status!r}, not approved")
    tenant = registry.get(record.tenant_id)
    report = json.loads(Path(record.report_path).read_text())
    mesh_src = Path(report["mesh_path"])
    version = _next_version(products_base / tenant.id / record.sku)
    dest_dir = tenant.product_root(base=products_base, sku=record.sku, version=version)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / mesh_src.name
    shutil.copy2(mesh_src, dest)
    return dest
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/platform/test_delivery.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/platform/delivery.py tests/elite_studio/platform/test_delivery.py
git commit -m "feat: post-approval delivery to canonical product tree (only writer)"
```

---

### Task 16: Full-suite green + lint + capability smoke

**Files:**
- Modify: none (verification task)

- [ ] **Step 1: Run the whole platform suite**

Run: `pytest tests/elite_studio/platform/ -v`
Expected: PASS — all tests from Tasks 1-15 green.

- [ ] **Step 2: Run the existing threed venture suite (no regression)**

Run: `pytest skyyrose/elite_studio/ventures/threed/tests/ -v`
Expected: PASS (10 passed) — the wrap did not break the venture.

- [ ] **Step 3: Lint + format the new platform layer**

Run: `ruff check skyyrose/elite_studio/platform/ scripts/phase0_*.py && black --check skyyrose/elite_studio/platform/ scripts/phase0_*.py && isort --check-only skyyrose/elite_studio/platform/`
Expected: "No issues found" / "All done" / no diff. Fix any reported issues, re-run.

- [ ] **Step 4: Capability smoke (free, no GPU)**

Run: `python -c "from skyyrose.elite_studio.platform.capability import CapabilityMatrix; from skyyrose.elite_studio.platform.tenancy import TenantRegistry; import json; t=TenantRegistry.default().get('skyyrose'); print(json.dumps([s.__dict__ for s in CapabilityMatrix(t).probe().statuses], indent=2))"`
Expected: JSON listing catalog/reference_store/fidelity_scorer/engine_local statuses. `engine_local` may be red (no GPU) — that's an honest proof, not a failure.

- [ ] **Step 5: Commit (if lint applied fixes)**

```bash
git add -A skyyrose/elite_studio/platform/ scripts/
git commit -m "chore: lint + format replica foundry platform layer"
```

---

## Out of Scope (later phases — not this plan)

- 2D modality (compositor/nano-banana) — Phase 2
- Public REST API + self-serve tenant onboarding — Phase 3
- Billing/admin UI + alt-engine (Meshy) gated path — Phase 4
- Per-face ray-cast coverage (Phase 1 uses angle-level coverage)
- Hosted-engine (Modal/fal.ai) production dispatch — wired behind the consistency-check gate from Phase 0.2 once that bar is met

---

## Verification Summary

After all tasks: `pytest tests/elite_studio/platform/ skyyrose/elite_studio/ventures/threed/tests/ -v` green, lint clean, and a free capability probe runs without GPU. The heavy paths (Blender render, model inference, paid generation) are exercised only in gated integration + Phase 0, never in CI.
