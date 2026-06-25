# Catalog & Dossier Steward Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a SkyyRose-dedicated Catalog & Dossier Steward — an AI-free deterministic verification engine plus a swappable AI reasoning layer — that QA's catalog↔dossier data quality and scaffolds (never authors) dossiers.

**Architecture:** Hexagonal. An AI-free core (`engine.py`, `scaffold.py`, `models.py`, `config.py`) holds all value and runs with zero AI. AI sits behind a 3-method `LLMReasoner` port with two adapters (`DeterministicReasoner` = no LLM, `PydanticAIReasoner` = Pydantic AI). Thin interfaces (CLI, MCP, optional ADK agent) call one `StewardService`.

**Tech Stack:** Python 3.11+, Pydantic v2, Pydantic AI v1.30.1, pytest. Reuses `skyyrose.core.catalog_loader`, `skyyrose.core.dossier_loader`, `skyyrose.core.dossier_schema`.

**Spec:** `docs/superpowers/specs/2026-05-29-catalog-dossier-steward-design.md`
**Model routing:** `docs/model-routing.md`

---

## File Structure

All under one package, `skyyrose/steward/`. AI-free modules import NO LLM/framework code (enforced by a test in Task 13).

| File | Responsibility | AI-free? |
|------|---------------|----------|
| `skyyrose/steward/__init__.py` | Package marker + public exports | yes |
| `skyyrose/steward/models.py` | `Severity`, `Dimension`, `Finding`, `DimensionScore`, `RenderReadiness`, `StewardReport`, `DossierSkeleton` | yes |
| `skyyrose/steward/config.py` | `TaskClass` enum + `model_for()` (reads routing policy) | yes |
| `skyyrose/steward/engine.py` | `verify_catalog()` + six dimension checks | yes |
| `skyyrose/steward/scaffold.py` | `build_skeleton()`, `write_draft()` | yes |
| `skyyrose/steward/ports.py` | `LLMReasoner` Protocol + `ReasonerError` | yes |
| `skyyrose/steward/adapters/__init__.py` | adapter exports | — |
| `skyyrose/steward/adapters/deterministic_reasoner.py` | no-LLM `LLMReasoner` | yes |
| `skyyrose/steward/adapters/pydantic_ai_reasoner.py` | Pydantic AI `LLMReasoner` | no |
| `skyyrose/steward/service.py` | `StewardService` use-case API | no (composes) |
| `skyyrose/steward/interfaces/__init__.py` | — | — |
| `skyyrose/steward/interfaces/cli.py` | argparse CLI (`python -m skyyrose.steward`) | no |
| `skyyrose/steward/interfaces/mcp.py` | MCP tool exposure | no |
| `skyyrose/steward/__main__.py` | `python -m skyyrose.steward` entrypoint | no |
| `tests/steward/*` | one test module per unit | — |

**Known debt (do NOT fix in this plan, note only):** `skyyrose/core/catalog_loader.py:44-48` `get_product()` has a redundant loop; `__all__` lists `get_product` twice. The Steward must not depend on `get_product`; use `read_catalog_rows()` / `get_all_skus()`.

---

## Phase 1 — Core models (AI-free)

### Task 1: Severity + Dimension enums and Finding

**Files:**
- Create: `skyyrose/steward/__init__.py`
- Create: `skyyrose/steward/models.py`
- Test: `tests/steward/__init__.py`, `tests/steward/test_models.py`

- [ ] **Step 1: Create package markers**

`skyyrose/steward/__init__.py`:
```python
"""SkyyRose Catalog & Dossier Steward.

AI-free deterministic verification engine + swappable AI reasoning layer.
See docs/superpowers/specs/2026-05-29-catalog-dossier-steward-design.md.
"""
```

`tests/steward/__init__.py`:
```python
```

- [ ] **Step 2: Write the failing test**

`tests/steward/test_models.py`:
```python
from __future__ import annotations

from skyyrose.steward.models import Dimension, Finding, Severity


def test_severity_ordering_rank():
    assert Severity.CRITICAL.rank > Severity.HIGH.rank
    assert Severity.HIGH.rank > Severity.MEDIUM.rank
    assert Severity.MEDIUM.rank > Severity.LOW.rank
    assert Severity.LOW.rank > Severity.INFO.rank


def test_finding_is_frozen_and_blocking():
    f = Finding(
        dimension=Dimension.INTEGRITY,
        sku="br-001",
        severity=Severity.CRITICAL,
        message="dossier file missing",
        evidence_path="data/dossiers/x.md",
    )
    assert f.is_blocking is True
    assert f.evidence_path == "data/dossiers/x.md"


def test_finding_non_blocking_below_high():
    f = Finding(
        dimension=Dimension.COMPLETENESS,
        sku="br-001",
        severity=Severity.LOW,
        message="missing color_hex",
    )
    assert f.is_blocking is False
    assert f.evidence_path is None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/steward/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.models'`

- [ ] **Step 4: Write minimal implementation**

`skyyrose/steward/models.py`:
```python
"""Typed result models for the Steward. AI-free — no LLM/framework imports."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def rank(self) -> int:
        order = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return order[self]


class Dimension(StrEnum):
    VALIDITY = "validity"
    COMPLETENESS = "completeness"
    INTEGRITY = "integrity"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"
    ACCURACY = "accuracy"


@dataclass(frozen=True)
class Finding:
    dimension: Dimension
    sku: str
    severity: Severity
    message: str
    evidence_path: str | None = None

    @property
    def is_blocking(self) -> bool:
        """HIGH or CRITICAL block render-readiness."""
        return self.severity.rank >= Severity.HIGH.rank
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/steward/test_models.py -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add skyyrose/steward/__init__.py skyyrose/steward/models.py tests/steward/__init__.py tests/steward/test_models.py
git commit -m "feat(steward): Severity/Dimension enums + Finding model"
```

---

### Task 2: DimensionScore, RenderReadiness, StewardReport

**Files:**
- Modify: `skyyrose/steward/models.py`
- Test: `tests/steward/test_report.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_report.py`:
```python
from __future__ import annotations

from skyyrose.steward.models import (
    Dimension,
    DimensionScore,
    Finding,
    RenderReadiness,
    Severity,
    StewardReport,
)


def _finding(sku, sev, dim=Dimension.INTEGRITY, msg="x"):
    return Finding(dimension=dim, sku=sku, severity=sev, message=msg)


def test_dimension_score_pct():
    s = DimensionScore(dimension=Dimension.VALIDITY, passed=8, failed=2)
    assert s.total == 10
    assert s.score_pct == 80.0


def test_dimension_score_pct_zero_total():
    s = DimensionScore(dimension=Dimension.ACCURACY, passed=0, failed=0)
    assert s.score_pct == 100.0  # vacuously clean


def test_report_render_readiness_groups_blocking_by_sku():
    findings = [
        _finding("br-001", Severity.CRITICAL),
        _finding("br-001", Severity.LOW),
        _finding("lh-002", Severity.MEDIUM),
    ]
    report = StewardReport.from_findings(
        findings=findings,
        skus=["br-001", "lh-002", "sg-003"],
        scores=[],
    )
    by_sku = {r.sku: r for r in report.render_readiness}
    assert by_sku["br-001"].ready is False
    assert len(by_sku["br-001"].blocking_findings) == 1
    assert by_sku["lh-002"].ready is True   # MEDIUM is not blocking
    assert by_sku["sg-003"].ready is True   # no findings


def test_report_counts():
    findings = [_finding("br-001", Severity.CRITICAL), _finding("br-001", Severity.LOW)]
    report = StewardReport.from_findings(findings=findings, skus=["br-001"], scores=[])
    assert report.total_findings == 2
    assert report.blocking_count == 1
    assert report.ready_count == 0
    assert report.sku_count == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_report.py -v`
Expected: FAIL — `ImportError: cannot import name 'DimensionScore'`

- [ ] **Step 3: Write minimal implementation (append to `models.py`)**

Append to `skyyrose/steward/models.py`:
```python
@dataclass(frozen=True)
class DimensionScore:
    dimension: Dimension
    passed: int
    failed: int

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def score_pct(self) -> float:
        if self.total == 0:
            return 100.0
        return round(100.0 * self.passed / self.total, 1)


@dataclass(frozen=True)
class RenderReadiness:
    sku: str
    ready: bool
    blocking_findings: tuple[Finding, ...]


@dataclass(frozen=True)
class StewardReport:
    findings: tuple[Finding, ...]
    scores: tuple[DimensionScore, ...]
    render_readiness: tuple[RenderReadiness, ...]

    @classmethod
    def from_findings(
        cls,
        findings: list[Finding],
        skus: list[str],
        scores: list[DimensionScore],
    ) -> StewardReport:
        readiness: list[RenderReadiness] = []
        for sku in skus:
            blocking = tuple(f for f in findings if f.sku == sku and f.is_blocking)
            readiness.append(
                RenderReadiness(sku=sku, ready=not blocking, blocking_findings=blocking)
            )
        return cls(
            findings=tuple(findings),
            scores=tuple(scores),
            render_readiness=tuple(readiness),
        )

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def blocking_count(self) -> int:
        return sum(1 for f in self.findings if f.is_blocking)

    @property
    def sku_count(self) -> int:
        return len(self.render_readiness)

    @property
    def ready_count(self) -> int:
        return sum(1 for r in self.render_readiness if r.ready)

    def to_dict(self) -> dict:
        return {
            "findings": [
                {
                    "dimension": f.dimension.value,
                    "sku": f.sku,
                    "severity": f.severity.value,
                    "message": f.message,
                    "evidence_path": f.evidence_path,
                }
                for f in self.findings
            ],
            "scores": [
                {"dimension": s.dimension.value, "passed": s.passed,
                 "failed": s.failed, "score_pct": s.score_pct}
                for s in self.scores
            ],
            "render_readiness": [
                {"sku": r.sku, "ready": r.ready,
                 "blocking": [b.message for b in r.blocking_findings]}
                for r in self.render_readiness
            ],
            "summary": {
                "total_findings": self.total_findings,
                "blocking_count": self.blocking_count,
                "ready_count": self.ready_count,
                "sku_count": self.sku_count,
            },
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_report.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/models.py tests/steward/test_report.py
git commit -m "feat(steward): DimensionScore, RenderReadiness, StewardReport"
```

---

### Task 3: DossierSkeleton model

**Files:**
- Modify: `skyyrose/steward/models.py`
- Test: `tests/steward/test_skeleton_model.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_skeleton_model.py`:
```python
from __future__ import annotations

from skyyrose.steward.models import DossierSkeleton


def test_skeleton_to_markdown_has_canonical_sections():
    sk = DossierSkeleton(
        sku="br-001",
        slug="black-rose-crewneck",
        name="BLACK Rose Crewneck",
        collection="black-rose",
        garment_type="crewneck",
    )
    md = sk.to_markdown()
    assert md.startswith("---\n")
    assert "sku: br-001" in md
    assert "slug: black-rose-crewneck" in md
    assert "**Garment type lock:** crewneck" in md
    assert "## Branding" in md
    assert "## Negative" in md
    assert "## Scene direction" in md
    # No prose: placeholders only, marked with TODO-AUTHOR
    assert "TODO-AUTHOR" in md


def test_skeleton_never_contains_generated_prose():
    sk = DossierSkeleton(
        sku="lh-002", slug="love-hurts-joggers", name="Love Hurts Joggers",
        collection="love-hurts", garment_type="joggers",
    )
    md = sk.to_markdown()
    # the skeleton must not invent a branding description
    assert "Embroidered" not in md
    assert "**Technique:** TODO-AUTHOR" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_skeleton_model.py -v`
Expected: FAIL — `ImportError: cannot import name 'DossierSkeleton'`

- [ ] **Step 3: Write minimal implementation (append to `models.py`)**

Append to `skyyrose/steward/models.py`:
```python
@dataclass(frozen=True)
class DossierSkeleton:
    """An EMPTY structured dossier skeleton. Placeholders only — never prose."""

    sku: str
    slug: str
    name: str
    collection: str
    garment_type: str
    logo_reference: str = ""
    extra_logos: tuple[str, ...] = field(default_factory=tuple)

    def to_markdown(self) -> str:
        extra = "\n".join(f"  - {p}" for p in self.extra_logos) or "  - TODO-AUTHOR"
        return (
            "---\n"
            f"sku: {self.sku}\n"
            f"slug: {self.slug}\n"
            f"name: {self.name}\n"
            f"collection: {self.collection}\n"
            f"logo_reference: {self.logo_reference or 'TODO-AUTHOR'}\n"
            "extra_logos:\n"
            f"{extra}\n"
            "---\n\n"
            f"# {self.name} — Design Dossier\n\n"
            f"**Garment type lock:** {self.garment_type}\n\n"
            "## Branding\n\n"
            "List each branding placement as a bullet. One bullet per region.\n\n"
            "- **TODO-AUTHOR-region** (TODO-AUTHOR-dimensions): TODO-AUTHOR-description. "
            "**Technique:** TODO-AUTHOR. **Color:** TODO-AUTHOR.\n\n"
            "## Negative\n\n"
            "What must NOT appear in renders. One item per bullet.\n\n"
            "- TODO-AUTHOR\n\n"
            "## Scene direction\n\n"
            "**Pose:** TODO-AUTHOR\n\n"
            "**Setting:** TODO-AUTHOR\n"
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_skeleton_model.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/models.py tests/steward/test_skeleton_model.py
git commit -m "feat(steward): DossierSkeleton (placeholder-only, never prose)"
```

---

## Phase 2 — Config (model routing, AI-free)

### Task 4: TaskClass + model_for()

**Files:**
- Create: `skyyrose/steward/config.py`
- Test: `tests/steward/test_config.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_config.py`:
```python
from __future__ import annotations

import pytest

from skyyrose.steward.config import TaskClass, model_for


def test_reasoning_routes_to_opus():
    assert model_for(TaskClass.REASONING) == "anthropic:claude-opus-4-8"


def test_quick_routes_to_haiku():
    assert model_for(TaskClass.QUICK) == "anthropic:claude-haiku-4-5"


def test_general_routes_to_sonnet():
    assert model_for(TaskClass.GENERAL) == "anthropic:claude-sonnet-4-6"


def test_override_via_env(monkeypatch):
    monkeypatch.setenv("STEWARD_MODEL_REASONING", "anthropic:claude-opus-4-9")
    assert model_for(TaskClass.REASONING) == "anthropic:claude-opus-4-9"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.config'`

- [ ] **Step 3: Write minimal implementation**

`skyyrose/steward/config.py`:
```python
"""Model-routing config for the Steward. AI-free (no LLM imports).

Policy source of truth: docs/model-routing.md. Resolution order:
  1. env override  STEWARD_MODEL_<TASKCLASS>
  2. built-in default below
"""

from __future__ import annotations

import os
from enum import StrEnum


class TaskClass(StrEnum):
    REASONING = "reasoning"   # architecture, prioritization, narration
    QUICK = "quick"           # classification, short phrasing, workers
    GENERAL = "general"       # default / coding / orchestration


# Pydantic AI model strings (provider:model). Keep in sync with docs/model-routing.md.
_DEFAULTS: dict[TaskClass, str] = {
    TaskClass.REASONING: "anthropic:claude-opus-4-8",
    TaskClass.QUICK: "anthropic:claude-haiku-4-5",
    TaskClass.GENERAL: "anthropic:claude-sonnet-4-6",
}


def model_for(task: TaskClass) -> str:
    """Resolve the model string for a task class (env override wins)."""
    env_key = f"STEWARD_MODEL_{task.name}"
    return os.environ.get(env_key) or _DEFAULTS[task]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_config.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/config.py tests/steward/test_config.py
git commit -m "feat(steward): config-driven model routing (Opus/Haiku/Sonnet)"
```

---

## Phase 3 — Verification engine (AI-free, the heart)

Each dimension is a pure function `(rows, ...) -> list[Finding]`. `verify_catalog()` composes them.

### Task 5: Engine skeleton + Validity dimension

**Files:**
- Create: `skyyrose/steward/engine.py`
- Test: `tests/steward/test_engine_validity.py`, `tests/steward/conftest.py`

- [ ] **Step 1: Write the fixture conftest**

`tests/steward/conftest.py`:
```python
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_catalog(tmp_path: Path):
    """Build a tiny catalog CSV + dossiers dir and return (csv_path, dossiers_dir)."""
    data = tmp_path / "data"
    dossiers = data / "dossiers"
    dossiers.mkdir(parents=True)
    csv_path = data / "skyyrose-catalog.csv"

    def write(rows: list[dict[str, str]], dossier_files: dict[str, str]):
        header = [
            "sku", "name", "collection", "dossier_slug", "garment_type_lock",
            "render_output_slug",
        ]
        lines = [",".join(header)]
        for r in rows:
            lines.append(",".join(r.get(h, "") for h in header))
        csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        for slug, body in dossier_files.items():
            (dossiers / f"{slug}.md").write_text(body, encoding="utf-8")
        return csv_path, dossiers

    return write


VALID_DOSSIER = """---
sku: br-001
slug: black-rose-crewneck
name: BLACK Rose Crewneck
collection: black-rose
---

# BLACK Rose Crewneck — Design Dossier

**Garment type lock:** crewneck

## Branding

- **front-chest** (~10in wide): Embossed wordmark. **Technique:** embossed. **Color:** tonal black (#0A0A0A).

## Negative

- no external brand logos

## Scene direction

**Pose:** standing, three-quarter.

**Setting:** concrete studio.
"""
```

- [ ] **Step 2: Write the failing test**

`tests/steward/test_engine_validity.py`:
```python
from __future__ import annotations

from skyyrose.steward.engine import check_validity
from skyyrose.steward.models import Dimension, Severity
from tests.steward.conftest import VALID_DOSSIER


def test_valid_dossier_yields_no_validity_findings(tmp_catalog):
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "BLACK Rose Crewneck",
               "collection": "black-rose", "dossier_slug": "black-rose-crewneck",
               "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    findings = check_validity(["br-001"], csv_path, dossiers)
    assert [f for f in findings if f.dimension is Dimension.VALIDITY] == []


def test_missing_garment_lock_is_critical_validity(tmp_catalog):
    bad = VALID_DOSSIER.replace("**Garment type lock:** crewneck", "")
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": bad},
    )
    findings = check_validity(["br-001"], csv_path, dossiers)
    sev = {f.severity for f in findings if f.dimension is Dimension.VALIDITY}
    assert Severity.CRITICAL in sev
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/steward/test_engine_validity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.engine'`

- [ ] **Step 4: Write minimal implementation**

`skyyrose/steward/engine.py`:
```python
"""Deterministic catalog↔dossier verification engine. AI-free.

Six DAMA-DMBOK data-quality dimensions, each a pure function over real data.
No LLM touches a verdict — Path.exists() cannot hallucinate.
"""

from __future__ import annotations

import csv
from pathlib import Path

from skyyrose.core.dossier_loader import (
    DossierMissingError,
    load_dossier,
)
from skyyrose.core.dossier_schema import DossierSchema, coverage_for
from skyyrose.steward.models import (
    Dimension,
    DimensionScore,
    Finding,
    Severity,
    StewardReport,
)


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


def _rows_for(skus: list[str], csv_path: Path) -> list[dict[str, str]]:
    rows = {r["sku"]: r for r in _read_rows(csv_path)}
    return [rows[s] for s in skus if s in rows]


def check_validity(skus: list[str], csv_path: Path, dossiers_dir: Path) -> list[Finding]:
    """Schema-parses each dossier; non-empty garment_lock + negatives + valid hex."""
    findings: list[Finding] = []
    for row in _rows_for(skus, csv_path):
        sku = row["sku"]
        slug = (row.get("dossier_slug") or "").strip()
        if not slug:
            continue  # integrity dimension reports the missing slug
        try:
            raw = load_dossier(slug, dossiers_dir=dossiers_dir)
            DossierSchema.from_raw(raw)
        except DossierMissingError:
            continue  # integrity dimension owns missing-file
        except Exception as exc:  # schema failure
            findings.append(Finding(
                dimension=Dimension.VALIDITY, sku=sku, severity=Severity.CRITICAL,
                message=f"dossier failed schema validation: {exc}",
                evidence_path=str(dossiers_dir / f"{slug}.md"),
            ))
            continue
        if not raw.garment_type_lock.strip():
            findings.append(Finding(
                dimension=Dimension.VALIDITY, sku=sku, severity=Severity.CRITICAL,
                message="garment_type_lock empty in dossier",
                evidence_path=str(dossiers_dir / f"{slug}.md"),
            ))
    return findings
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/steward/test_engine_validity.py -v`
Expected: PASS (2 passed)

- [ ] **Step 6: Commit**

```bash
git add skyyrose/steward/engine.py tests/steward/test_engine_validity.py tests/steward/conftest.py
git commit -m "feat(steward): engine scaffold + Validity dimension"
```

---

### Task 6: Integrity dimension (referential)

**Files:**
- Modify: `skyyrose/steward/engine.py`
- Test: `tests/steward/test_engine_integrity.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_engine_integrity.py`:
```python
from __future__ import annotations

from skyyrose.steward.engine import check_integrity
from skyyrose.steward.models import Dimension, Severity
from tests.steward.conftest import VALID_DOSSIER


def test_missing_dossier_file_is_critical_integrity(tmp_catalog):
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "ghost-slug", "garment_type_lock": "crewneck"}],
        dossier_files={},  # no file for ghost-slug
    )
    findings = check_integrity(["br-001"], csv_path, dossiers)
    crit = [f for f in findings
            if f.dimension is Dimension.INTEGRITY and f.severity is Severity.CRITICAL]
    assert crit and "ghost-slug" in crit[0].message


def test_empty_dossier_slug_is_critical_integrity(tmp_catalog):
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "", "garment_type_lock": "crewneck"}],
        dossier_files={},
    )
    findings = check_integrity(["br-001"], csv_path, dossiers)
    assert any(f.dimension is Dimension.INTEGRITY and f.severity is Severity.CRITICAL
               for f in findings)


def test_resolvable_dossier_no_integrity_finding(tmp_catalog):
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    findings = check_integrity(["br-001"], csv_path, dossiers)
    assert [f for f in findings if f.dimension is Dimension.INTEGRITY] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_engine_integrity.py -v`
Expected: FAIL — `ImportError: cannot import name 'check_integrity'`

- [ ] **Step 3: Write minimal implementation (append to `engine.py`)**

```python
def check_integrity(skus: list[str], csv_path: Path, dossiers_dir: Path) -> list[Finding]:
    """Every catalog dossier_slug must resolve to an existing dossier file."""
    findings: list[Finding] = []
    for row in _rows_for(skus, csv_path):
        sku = row["sku"]
        slug = (row.get("dossier_slug") or "").strip()
        if not slug:
            findings.append(Finding(
                dimension=Dimension.INTEGRITY, sku=sku, severity=Severity.CRITICAL,
                message="no dossier_slug in catalog row",
                evidence_path=str(csv_path),
            ))
            continue
        path = dossiers_dir / f"{slug}.md"
        if not path.exists():
            findings.append(Finding(
                dimension=Dimension.INTEGRITY, sku=sku, severity=Severity.CRITICAL,
                message=f"dossier_slug {slug!r} has no file",
                evidence_path=str(path),
            ))
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_engine_integrity.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/engine.py tests/steward/test_engine_integrity.py
git commit -m "feat(steward): Integrity dimension (dossier_slug resolves)"
```

---

### Task 7: Uniqueness dimension

**Files:**
- Modify: `skyyrose/steward/engine.py`
- Test: `tests/steward/test_engine_uniqueness.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_engine_uniqueness.py`:
```python
from __future__ import annotations

from skyyrose.steward.engine import check_uniqueness
from skyyrose.steward.models import Dimension, Severity


def test_duplicate_sku_is_high(tmp_catalog):
    csv_path, dossiers = tmp_catalog(
        rows=[
            {"sku": "br-001", "name": "A", "collection": "black-rose",
             "dossier_slug": "a", "garment_type_lock": "crewneck"},
            {"sku": "br-001", "name": "B", "collection": "black-rose",
             "dossier_slug": "b", "garment_type_lock": "hoodie"},
        ],
        dossier_files={},
    )
    findings = check_uniqueness(csv_path)
    assert any(f.dimension is Dimension.UNIQUENESS and f.severity is Severity.HIGH
               and "br-001" in f.message for f in findings)


def test_duplicate_dossier_slug_is_high(tmp_catalog):
    csv_path, dossiers = tmp_catalog(
        rows=[
            {"sku": "br-001", "name": "A", "collection": "black-rose",
             "dossier_slug": "shared", "garment_type_lock": "crewneck"},
            {"sku": "br-002", "name": "B", "collection": "black-rose",
             "dossier_slug": "shared", "garment_type_lock": "hoodie"},
        ],
        dossier_files={},
    )
    findings = check_uniqueness(csv_path)
    assert any("shared" in f.message for f in findings
               if f.dimension is Dimension.UNIQUENESS)


def test_unique_catalog_no_findings(tmp_catalog):
    csv_path, dossiers = tmp_catalog(
        rows=[
            {"sku": "br-001", "name": "A", "collection": "black-rose",
             "dossier_slug": "a", "garment_type_lock": "crewneck"},
            {"sku": "br-002", "name": "B", "collection": "black-rose",
             "dossier_slug": "b", "garment_type_lock": "hoodie"},
        ],
        dossier_files={},
    )
    assert check_uniqueness(csv_path) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_engine_uniqueness.py -v`
Expected: FAIL — `ImportError: cannot import name 'check_uniqueness'`

- [ ] **Step 3: Write minimal implementation (append to `engine.py`)**

```python
from collections import Counter


def check_uniqueness(csv_path: Path) -> list[Finding]:
    """No duplicate SKU and no duplicate dossier_slug in the catalog."""
    rows = _read_rows(csv_path)
    findings: list[Finding] = []

    sku_counts = Counter(r["sku"] for r in rows)
    for sku, n in sku_counts.items():
        if n > 1:
            findings.append(Finding(
                dimension=Dimension.UNIQUENESS, sku=sku, severity=Severity.HIGH,
                message=f"SKU {sku!r} appears {n} times in catalog",
                evidence_path=str(csv_path),
            ))

    slug_owners: dict[str, list[str]] = {}
    for r in rows:
        slug = (r.get("dossier_slug") or "").strip()
        if slug:
            slug_owners.setdefault(slug, []).append(r["sku"])
    for slug, owners in slug_owners.items():
        if len(owners) > 1:
            findings.append(Finding(
                dimension=Dimension.UNIQUENESS, sku=owners[0], severity=Severity.HIGH,
                message=f"dossier_slug {slug!r} shared by SKUs {owners}",
                evidence_path=str(csv_path),
            ))
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_engine_uniqueness.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/engine.py tests/steward/test_engine_uniqueness.py
git commit -m "feat(steward): Uniqueness dimension (no dup SKU/slug)"
```

---

### Task 8: Consistency dimension

**Files:**
- Modify: `skyyrose/steward/engine.py`
- Test: `tests/steward/test_engine_consistency.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_engine_consistency.py`:
```python
from __future__ import annotations

from skyyrose.steward.engine import check_consistency
from skyyrose.steward.models import Dimension, Severity
from tests.steward.conftest import VALID_DOSSIER


def test_garment_lock_mismatch_is_high(tmp_catalog):
    # CSV says hoodie, dossier says crewneck
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "BLACK Rose Crewneck", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "hoodie"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    findings = check_consistency(["br-001"], csv_path, dossiers)
    assert any(f.dimension is Dimension.CONSISTENCY and f.severity is Severity.HIGH
               for f in findings)


def test_collection_mismatch_is_medium(tmp_catalog):
    # CSV collection love-hurts, dossier collection black-rose
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "BLACK Rose Crewneck", "collection": "love-hurts",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    findings = check_consistency(["br-001"], csv_path, dossiers)
    assert any(f.dimension is Dimension.CONSISTENCY and f.severity is Severity.MEDIUM
               for f in findings)


def test_consistent_no_findings(tmp_catalog):
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "BLACK Rose Crewneck", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    assert check_consistency(["br-001"], csv_path, dossiers) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_engine_consistency.py -v`
Expected: FAIL — `ImportError: cannot import name 'check_consistency'`

- [ ] **Step 3: Write minimal implementation (append to `engine.py`)**

```python
def _norm(s: str) -> str:
    return (s or "").strip().lower()


def check_consistency(skus: list[str], csv_path: Path, dossiers_dir: Path) -> list[Finding]:
    """CSV vs dossier must agree on garment_type_lock (HIGH) and collection (MEDIUM)."""
    findings: list[Finding] = []
    for row in _rows_for(skus, csv_path):
        sku = row["sku"]
        slug = (row.get("dossier_slug") or "").strip()
        if not slug:
            continue
        try:
            raw = load_dossier(slug, dossiers_dir=dossiers_dir)
        except DossierMissingError:
            continue
        path = str(dossiers_dir / f"{slug}.md")
        if _norm(row.get("garment_type_lock", "")) != _norm(raw.garment_type_lock):
            findings.append(Finding(
                dimension=Dimension.CONSISTENCY, sku=sku, severity=Severity.HIGH,
                message=(f"garment_type_lock mismatch: csv="
                         f"{row.get('garment_type_lock')!r} dossier={raw.garment_type_lock!r}"),
                evidence_path=path,
            ))
        if raw.collection and _norm(row.get("collection", "")) != _norm(raw.collection):
            findings.append(Finding(
                dimension=Dimension.CONSISTENCY, sku=sku, severity=Severity.MEDIUM,
                message=(f"collection mismatch: csv={row.get('collection')!r} "
                         f"dossier={raw.collection!r}"),
                evidence_path=path,
            ))
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_engine_consistency.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/engine.py tests/steward/test_engine_consistency.py
git commit -m "feat(steward): Consistency dimension (CSV↔dossier agreement)"
```

---

### Task 9: Completeness dimension (+ golden coverage)

**Files:**
- Modify: `skyyrose/steward/engine.py`
- Test: `tests/steward/test_engine_completeness.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_engine_completeness.py`:
```python
from __future__ import annotations

from skyyrose.steward.engine import check_completeness
from skyyrose.steward.models import Dimension, Severity
from tests.steward.conftest import VALID_DOSSIER


def test_missing_color_hex_is_low(tmp_catalog):
    no_hex = VALID_DOSSIER.replace(" (#0A0A0A)", "")
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": no_hex},
    )
    findings = check_completeness(["br-001"], csv_path, dossiers, golden_dir=dossiers)
    assert any(f.dimension is Dimension.COMPLETENESS and f.severity is Severity.LOW
               and "color_hex" in f.message for f in findings)


def test_empty_scene_pose_is_medium(tmp_catalog):
    no_pose = VALID_DOSSIER.replace("**Pose:** standing, three-quarter.", "**Pose:**")
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": no_pose},
    )
    findings = check_completeness(["br-001"], csv_path, dossiers, golden_dir=dossiers)
    assert any(f.dimension is Dimension.COMPLETENESS and "scene_pose" in f.message
               for f in findings)


def test_missing_golden_back_is_low(tmp_catalog, tmp_path):
    golden = tmp_path / "golden"
    (golden / "br-001").mkdir(parents=True)
    (golden / "br-001" / "front.jpg").write_bytes(b"x")  # front only, no back
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    findings = check_completeness(["br-001"], csv_path, dossiers, golden_dir=golden)
    assert any("golden back" in f.message for f in findings
               if f.dimension is Dimension.COMPLETENESS)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_engine_completeness.py -v`
Expected: FAIL — `ImportError: cannot import name 'check_completeness'`

- [ ] **Step 3: Write minimal implementation (append to `engine.py`)**

```python
def check_completeness(
    skus: list[str],
    csv_path: Path,
    dossiers_dir: Path,
    golden_dir: Path,
) -> list[Finding]:
    """coverage_for() color/scene gaps (LOW/MEDIUM) + golden front/back presence (LOW)."""
    findings: list[Finding] = []
    for row in _rows_for(skus, csv_path):
        sku = row["sku"]
        slug = (row.get("dossier_slug") or "").strip()
        if not slug:
            continue
        try:
            raw = load_dossier(slug, dossiers_dir=dossiers_dir)
            schema = DossierSchema.from_raw(raw)
        except DossierMissingError:
            continue
        except Exception:
            continue  # validity dimension owns schema failures
        path = str(dossiers_dir / f"{slug}.md")
        cov = coverage_for(schema)
        if cov.hex_coverage_pct < 100.0:
            findings.append(Finding(
                dimension=Dimension.COMPLETENESS, sku=sku, severity=Severity.LOW,
                message=f"color_hex coverage {cov.hex_coverage_pct}% (<100%)",
                evidence_path=path,
            ))
        if not schema.scene_pose:
            findings.append(Finding(
                dimension=Dimension.COMPLETENESS, sku=sku, severity=Severity.MEDIUM,
                message="scene_pose empty", evidence_path=path,
            ))
        if not schema.scene_setting:
            findings.append(Finding(
                dimension=Dimension.COMPLETENESS, sku=sku, severity=Severity.MEDIUM,
                message="scene_setting empty", evidence_path=path,
            ))
        # Golden reference presence (front required, back nice-to-have)
        front = golden_dir / sku / "front.jpg"
        back = golden_dir / sku / "back.jpg"
        if not front.exists():
            findings.append(Finding(
                dimension=Dimension.COMPLETENESS, sku=sku, severity=Severity.MEDIUM,
                message="golden front.jpg missing", evidence_path=str(front),
            ))
        if not back.exists():
            findings.append(Finding(
                dimension=Dimension.COMPLETENESS, sku=sku, severity=Severity.LOW,
                message="golden back.jpg missing", evidence_path=str(back),
            ))
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_engine_completeness.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/engine.py tests/steward/test_engine_completeness.py
git commit -m "feat(steward): Completeness dimension (coverage + golden refs)"
```

---

### Task 10: Accuracy dimension (flag-gated) + verify_catalog() composition

**Files:**
- Modify: `skyyrose/steward/engine.py`
- Test: `tests/steward/test_engine_verify.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_engine_verify.py`:
```python
from __future__ import annotations

from skyyrose.steward.engine import verify_catalog
from skyyrose.steward.models import Dimension, StewardReport
from tests.steward.conftest import VALID_DOSSIER


def test_verify_catalog_returns_report_with_scores(tmp_catalog, tmp_path):
    golden = tmp_path / "golden"
    (golden / "br-001").mkdir(parents=True)
    (golden / "br-001" / "front.jpg").write_bytes(b"x")
    (golden / "br-001" / "back.jpg").write_bytes(b"x")
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "BLACK Rose Crewneck", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    report = verify_catalog(
        skus=["br-001"], csv_path=csv_path, dossiers_dir=dossiers, golden_dir=golden,
    )
    assert isinstance(report, StewardReport)
    assert report.sku_count == 1
    assert report.ready_count == 1  # clean dossier → ready
    dims = {s.dimension for s in report.scores}
    assert Dimension.VALIDITY in dims and Dimension.INTEGRITY in dims


def test_accuracy_skipped_without_vision_flag(tmp_catalog, tmp_path):
    golden = tmp_path / "golden"
    (golden / "br-001").mkdir(parents=True)
    (golden / "br-001" / "front.jpg").write_bytes(b"x")
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    report = verify_catalog(skus=["br-001"], csv_path=csv_path, dossiers_dir=dossiers,
                            golden_dir=golden, with_vision=False)
    assert all(f.dimension is not Dimension.ACCURACY for f in report.findings)


def test_accuracy_with_vision_never_false_greens(tmp_catalog, tmp_path):
    """--with-vision while scoring is unimplemented must NOT score a 100% pass."""
    golden = tmp_path / "golden"
    (golden / "br-001").mkdir(parents=True)
    (golden / "br-001" / "front.jpg").write_bytes(b"x")
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    report = verify_catalog(skus=["br-001"], csv_path=csv_path, dossiers_dir=dossiers,
                            golden_dir=golden, with_vision=True)
    # ACCURACY must be EXCLUDED from scores (no false 100%) ...
    assert all(s.dimension is not Dimension.ACCURACY for s in report.scores)
    # ... and the report must say accuracy was NOT verified.
    assert any(f.dimension is Dimension.ACCURACY and "NOT verified" in f.message
               for f in report.findings)


def _write_status_catalog(tmp_path):
    """Build a CSV with one published (live) + one draft row, with status columns."""
    data = tmp_path / "data"
    (data / "dossiers").mkdir(parents=True)
    csv_path = data / "skyyrose-catalog.csv"
    header = "sku,name,collection,dossier_slug,garment_type_lock,published,is_preorder,badge"
    lines = [
        header,
        "br-001,A,black-rose,a,crewneck,1,0,",      # published == 1 -> live
        "br-009,B,black-rose,b,hoodie,0,0,draft",   # published == 0 -> draft
    ]
    csv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return csv_path


def test_select_skus_default_is_published_only(tmp_path):
    from skyyrose.steward.engine import select_skus

    csv_path = _write_status_catalog(tmp_path)
    # default -> only the published/live SKU
    assert select_skus(csv_path) == ["br-001"]
    # include_all -> both rows
    assert set(select_skus(csv_path, include_all=True)) == {"br-001", "br-009"}
    # explicit list wins over status filtering
    assert select_skus(csv_path, explicit=["br-009"]) == ["br-009"]
    # status filter selects draft only
    assert select_skus(csv_path, status="draft") == ["br-009"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_engine_verify.py -v`
Expected: FAIL — `ImportError: cannot import name 'verify_catalog'`

- [ ] **Step 3: Write minimal implementation (append to `engine.py`)**

```python
# Default production paths (overridable for tests / CI).
from skyyrose.core.catalog_loader import CATALOG_CSV as _DEFAULT_CSV
from skyyrose.core.dossier_loader import DOSSIERS_DIR as _DEFAULT_DOSSIERS

_DEFAULT_GOLDEN = (
    Path(__file__).resolve().parents[1] / "elite_studio" / "assets" / "golden"
)


def check_accuracy(skus: list[str], golden_dir: Path) -> tuple[list[Finding], bool]:
    """Flag-gated golden-reference accuracy. Returns (findings, ran).

    CRITICAL anti-false-green rule: accuracy NEVER scores as a pass until real
    CLIP/DINOv2 golden scoring is implemented. Until then `ran` is always False so
    the dimension is EXCLUDED from scores — a tool that fakes a 100% accuracy pass
    is the exact failure this deterministic engine exists to prevent. Presence
    checks (front/back on disk) live in Completeness, not here.
    """
    # Real CLIP/DINOv2 scoring is a follow-up. Report "not verified", ran=False.
    return (
        [Finding(
            dimension=Dimension.ACCURACY, sku=(skus[0] if skus else ""),
            severity=Severity.INFO,
            message="golden-reference accuracy scoring not yet implemented — NOT verified",
        )],
        False,
    )


def _score(dim: Dimension, skus: list[str], findings: list[Finding]) -> DimensionScore:
    failed_skus = {f.sku for f in findings if f.dimension is dim}
    failed = sum(1 for s in skus if s in failed_skus)
    return DimensionScore(dimension=dim, passed=len(skus) - failed, failed=failed)


def select_skus(
    csv_path: Path,
    *,
    explicit: list[str] | None = None,
    collection: str | None = None,
    status: str | None = None,
    include_all: bool = False,
) -> list[str]:
    """Resolve the SKU work-set from the catalog with a precedence filter.

    Precedence (first match wins):
      1. explicit list — exact SKUs, no further filtering
      2. include_all   — every row in the CSV
      3. collection / status filters — AND-combined
      4. default       — published/live rows only (status_from_row == 'live')

    Default = published-only so the report isn't flooded with expected
    'golden missing' / incomplete-dossier noise for draft SKUs.
    """
    from skyyrose.core.catalog_loader import status_from_row

    rows = _read_rows(csv_path)
    if explicit:
        wanted = set(explicit)
        return [r["sku"] for r in rows if r["sku"] in wanted]
    if include_all:
        return [r["sku"] for r in rows]
    if collection or status:
        out = []
        for r in rows:
            if collection and _norm(r.get("collection", "")) != _norm(collection):
                continue
            if status and status_from_row(r) != status:
                continue
            out.append(r["sku"])
        return out
    return [r["sku"] for r in rows if status_from_row(r) == "live"]


def verify_catalog(
    skus: list[str] | None = None,
    csv_path: Path | None = None,
    dossiers_dir: Path | None = None,
    golden_dir: Path | None = None,
    with_vision: bool = False,
    collection: str | None = None,
    status: str | None = None,
    include_all: bool = False,
) -> StewardReport:
    """Run all deterministic dimensions and assemble a StewardReport.

    SKU scope resolves through select_skus(): explicit `skus` > include_all >
    collection/status filter > default (published/live only).
    """
    csv_path = csv_path or _DEFAULT_CSV
    dossiers_dir = dossiers_dir or _DEFAULT_DOSSIERS
    golden_dir = golden_dir or _DEFAULT_GOLDEN
    skus = select_skus(
        csv_path, explicit=skus, collection=collection, status=status,
        include_all=include_all,
    )

    findings: list[Finding] = []
    findings += check_validity(skus, csv_path, dossiers_dir)
    findings += check_integrity(skus, csv_path, dossiers_dir)
    findings += check_consistency(skus, csv_path, dossiers_dir)
    findings += check_completeness(skus, csv_path, dossiers_dir, golden_dir)
    findings += check_uniqueness(csv_path)

    ran_accuracy = False
    if with_vision:
        acc_findings, ran_accuracy = check_accuracy(skus, golden_dir)
        findings += acc_findings

    # ACCURACY is scored ONLY when it actually ran — never a false 100% pass.
    dims = [Dimension.VALIDITY, Dimension.INTEGRITY, Dimension.CONSISTENCY,
            Dimension.COMPLETENESS, Dimension.UNIQUENESS]
    if ran_accuracy:
        dims.append(Dimension.ACCURACY)
    scores = [_score(d, skus, findings) for d in dims]
    return StewardReport.from_findings(findings=findings, skus=skus, scores=scores)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_engine_verify.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/engine.py tests/steward/test_engine_verify.py
git commit -m "feat(steward): Accuracy (flag-gated, no false-green) + verify_catalog composition"
```

---

## Phase 4 — Scaffold (AI-free)

### Task 11: build_skeleton() + write_draft()

**Files:**
- Create: `skyyrose/steward/scaffold.py`
- Test: `tests/steward/test_scaffold.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_scaffold.py`:
```python
from __future__ import annotations

import pytest

from skyyrose.steward.models import DossierSkeleton
from skyyrose.steward.scaffold import build_skeleton, write_draft


def test_build_skeleton_from_catalog_row():
    row = {"sku": "br-001", "name": "BLACK Rose Crewneck", "collection": "black-rose",
           "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}
    sk = build_skeleton(row)
    assert isinstance(sk, DossierSkeleton)
    assert sk.sku == "br-001"
    assert sk.slug == "black-rose-crewneck"
    assert sk.garment_type == "crewneck"


def test_build_skeleton_missing_slug_raises():
    row = {"sku": "br-001", "name": "X", "collection": "black-rose",
           "dossier_slug": "", "garment_type_lock": "crewneck"}
    with pytest.raises(ValueError, match="dossier_slug"):
        build_skeleton(row)


def test_write_draft_goes_to_drafts_never_canonical(tmp_path):
    row = {"sku": "br-001", "name": "X", "collection": "black-rose",
           "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}
    sk = build_skeleton(row)
    dossiers = tmp_path / "dossiers"
    dossiers.mkdir()
    out = write_draft(sk, dossiers_dir=dossiers)
    assert out.parent.name == "_drafts"
    assert out.name == "black-rose-crewneck.draft.md"
    # canonical path must be untouched
    assert not (dossiers / "black-rose-crewneck.md").exists()
    assert "TODO-AUTHOR" in out.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_scaffold.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.scaffold'`

- [ ] **Step 3: Write minimal implementation**

`skyyrose/steward/scaffold.py`:
```python
"""Dossier scaffolding — builds EMPTY skeletons + writes drafts. AI-free.

NEVER writes to a canonical {slug}.md — only to dossiers/_drafts/{slug}.draft.md.
Machine text must never reach a canonical dossier (per dossier-authoring canon).
"""

from __future__ import annotations

from pathlib import Path

from skyyrose.core.dossier_loader import DOSSIERS_DIR
from skyyrose.steward.models import DossierSkeleton


def build_skeleton(row: dict[str, str]) -> DossierSkeleton:
    """Build a placeholder skeleton from a catalog row. No prose generated."""
    slug = (row.get("dossier_slug") or "").strip()
    if not slug:
        raise ValueError(f"cannot scaffold {row.get('sku')!r}: no dossier_slug")
    return DossierSkeleton(
        sku=row["sku"],
        slug=slug,
        name=row.get("name", ""),
        collection=row.get("collection", ""),
        garment_type=(row.get("garment_type_lock") or "TODO-AUTHOR").strip(),
    )


def write_draft(skeleton: DossierSkeleton, dossiers_dir: Path | None = None) -> Path:
    """Write the skeleton to dossiers/_drafts/{slug}.draft.md. Never the canonical file."""
    base = dossiers_dir or DOSSIERS_DIR
    drafts = base / "_drafts"
    drafts.mkdir(parents=True, exist_ok=True)
    out = drafts / f"{skeleton.slug}.draft.md"
    out.write_text(skeleton.to_markdown(), encoding="utf-8")
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_scaffold.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/scaffold.py tests/steward/test_scaffold.py
git commit -m "feat(steward): scaffold skeleton + draft writer (never canonical)"
```

---

## Phase 5 — Ports + adapters

### Task 12: LLMReasoner port + DeterministicReasoner

**Files:**
- Create: `skyyrose/steward/ports.py`
- Create: `skyyrose/steward/adapters/__init__.py`
- Create: `skyyrose/steward/adapters/deterministic_reasoner.py`
- Test: `tests/steward/test_deterministic_reasoner.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_deterministic_reasoner.py`:
```python
from __future__ import annotations

from skyyrose.steward.adapters.deterministic_reasoner import DeterministicReasoner
from skyyrose.steward.models import (
    Dimension, DossierSkeleton, Finding, Severity, StewardReport,
)


def _f(sev, msg):
    return Finding(dimension=Dimension.INTEGRITY, sku="br-001", severity=sev, message=msg)


def test_prioritize_sorts_by_severity_desc():
    r = DeterministicReasoner()
    out = r.prioritize([_f(Severity.LOW, "a"), _f(Severity.CRITICAL, "b"),
                        _f(Severity.MEDIUM, "c")])
    assert [f.severity for f in out] == [Severity.CRITICAL, Severity.MEDIUM, Severity.LOW]


def test_interrogate_emits_question_per_todo():
    r = DeterministicReasoner()
    sk = DossierSkeleton(sku="br-001", slug="s", name="N", collection="c",
                         garment_type="crewneck")
    qs = r.interrogate(sk, known={})
    assert any("Branding" in q for q in qs)
    assert any("Scene" in q or "Pose" in q for q in qs)


def test_narrate_is_deterministic_text():
    r = DeterministicReasoner()
    report = StewardReport.from_findings(findings=[_f(Severity.CRITICAL, "x")],
                                         skus=["br-001"], scores=[])
    text = r.narrate(report)
    assert "1 finding" in text or "findings" in text
    assert "br-001" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_deterministic_reasoner.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.ports'`

- [ ] **Step 3: Write minimal implementation**

`skyyrose/steward/ports.py`:
```python
"""Ports for the Steward. AI-free — defines the AI boundary, imports no LLM."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from skyyrose.steward.models import DossierSkeleton, Finding, StewardReport


class ReasonerError(RuntimeError):
    """Raised when an LLMReasoner adapter fails irrecoverably."""


@runtime_checkable
class LLMReasoner(Protocol):
    """The only AI surface. Adapters: Deterministic (no LLM) and PydanticAI.

    INVARIANT: `prioritize` is ORDER-ONLY — it reorders findings and MUST return
    exactly the same set (same length, same items). It must never filter, drop, or
    add findings; doing so silently corrupts StewardReport.blocking_count /
    render_readiness. StewardService asserts the count is preserved.
    """

    def prioritize(self, findings: list[Finding]) -> list[Finding]: ...

    def interrogate(self, skeleton: DossierSkeleton, known: dict) -> list[str]: ...

    def narrate(self, report: StewardReport) -> str: ...
```

`skyyrose/steward/adapters/__init__.py`:
```python
"""Steward reasoner adapters."""
```

`skyyrose/steward/adapters/deterministic_reasoner.py`:
```python
"""No-LLM LLMReasoner. Proves the system runs with zero AI. AI-free."""

from __future__ import annotations

from skyyrose.steward.models import DossierSkeleton, Finding, StewardReport


class DeterministicReasoner:
    """Implements the LLMReasoner port without any model."""

    def prioritize(self, findings: list[Finding]) -> list[Finding]:
        return sorted(findings, key=lambda f: f.severity.rank, reverse=True)

    def interrogate(self, skeleton: DossierSkeleton, known: dict) -> list[str]:
        questions: list[str] = []
        if "branding" not in known:
            questions.append(
                f"Branding: list each placement region for {skeleton.name} "
                f"({skeleton.garment_type}) — region, dimensions, technique, color."
            )
        if "negative" not in known:
            questions.append(f"Negative: what must NOT appear in {skeleton.name} renders?")
        if "scene" not in known:
            questions.append(f"Scene direction: pose + setting for {skeleton.name}?")
        return questions

    def narrate(self, report: StewardReport) -> str:
        lines = [
            f"{report.total_findings} findings across {report.sku_count} SKUs; "
            f"{report.blocking_count} blocking; {report.ready_count} render-ready.",
        ]
        for r in report.render_readiness:
            if not r.ready:
                msgs = "; ".join(b.message for b in r.blocking_findings)
                lines.append(f"- {r.sku}: BLOCKED — {msgs}")
        return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_deterministic_reasoner.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/ports.py skyyrose/steward/adapters/__init__.py skyyrose/steward/adapters/deterministic_reasoner.py tests/steward/test_deterministic_reasoner.py
git commit -m "feat(steward): LLMReasoner port + DeterministicReasoner (no-LLM)"
```

---

### Task 13: AI-free import-discipline guard test

**Files:**
- Test: `tests/steward/test_ai_free_core.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_ai_free_core.py`:
```python
"""Guard: core modules must never import an LLM/framework. Enforces hexagonal core."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

CORE_MODULES = [
    "skyyrose/steward/models.py",
    "skyyrose/steward/config.py",
    "skyyrose/steward/engine.py",
    "skyyrose/steward/scaffold.py",
    "skyyrose/steward/ports.py",
    "skyyrose/steward/adapters/deterministic_reasoner.py",
]
FORBIDDEN = {"pydantic_ai", "anthropic", "openai", "claude_agent_sdk", "litellm"}


def _imports(path: str) -> set[str]:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


@pytest.mark.parametrize("module", CORE_MODULES)
def test_core_module_is_ai_free(module):
    leaked = _imports(module) & FORBIDDEN
    assert not leaked, f"{module} imports forbidden AI modules: {leaked}"
```

- [ ] **Step 2: Run test to verify it passes (this guard should already hold)**

Run: `pytest tests/steward/test_ai_free_core.py -v`
Expected: PASS (6 passed) — if any FAIL, refactor the offending import out of the core module.

- [ ] **Step 3: Commit**

```bash
git add tests/steward/test_ai_free_core.py
git commit -m "test(steward): guard core modules stay AI-free"
```

---

### Task 14: PydanticAIReasoner adapter

**Files:**
- Create: `skyyrose/steward/adapters/pydantic_ai_reasoner.py`
- Test: `tests/steward/test_pydantic_ai_reasoner.py`

- [ ] **Step 1: Write the failing test (uses Pydantic AI TestModel — no API calls)**

`tests/steward/test_pydantic_ai_reasoner.py`:
```python
from __future__ import annotations

import pytest

pytest.importorskip("pydantic_ai")

from skyyrose.steward.adapters.pydantic_ai_reasoner import PydanticAIReasoner
from skyyrose.steward.models import Dimension, Finding, Severity, StewardReport


def _f(sev):
    return Finding(dimension=Dimension.INTEGRITY, sku="br-001", severity=sev, message="x")


def test_prioritize_is_deterministic_locally():
    """prioritize() is pure ranking — no model needed even in the PydanticAI adapter."""
    r = PydanticAIReasoner()
    out = r.prioritize([_f(Severity.LOW), _f(Severity.CRITICAL)])
    assert out[0].severity is Severity.CRITICAL


def test_narrate_with_test_model():
    from pydantic_ai.models.test import TestModel

    r = PydanticAIReasoner()
    report = StewardReport.from_findings(findings=[_f(Severity.HIGH)], skus=["br-001"],
                                         scores=[])
    with r.agent.override(model=TestModel()):
        text = r.narrate(report)
    assert isinstance(text, str) and text


def test_conforms_to_port():
    from skyyrose.steward.ports import LLMReasoner
    assert isinstance(PydanticAIReasoner(), LLMReasoner)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_pydantic_ai_reasoner.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.adapters.pydantic_ai_reasoner'`

- [ ] **Step 3: Write minimal implementation**

`skyyrose/steward/adapters/pydantic_ai_reasoner.py`:
```python
"""Pydantic AI adapter for the LLMReasoner port. The ONLY core-adjacent AI module.

Model is config-driven (skyyrose.steward.config). prioritize() stays deterministic
(pure ranking needs no model); interrogate()/narrate() use the model.
"""

from __future__ import annotations

from skyyrose.steward.config import TaskClass, model_for
from skyyrose.steward.models import DossierSkeleton, Finding, StewardReport
from skyyrose.steward.ports import ReasonerError


class PydanticAIReasoner:
    """LLMReasoner backed by Pydantic AI."""

    def __init__(self, model: str | None = None):
        try:
            from pydantic_ai import Agent
        except ImportError as exc:  # pragma: no cover
            raise ReasonerError("pydantic-ai not installed") from exc
        self.agent = Agent(
            model or model_for(TaskClass.REASONING),
            system_prompt=(
                "You are the SkyyRose Catalog & Dossier Steward's reasoning layer. "
                "You NEVER author dossier prose. You prioritize data-quality findings, "
                "phrase targeted authoring questions for the human author, and summarize "
                "verification reports. Be precise and reference SKUs by name and id."
            ),
        )

    def prioritize(self, findings: list[Finding]) -> list[Finding]:
        # Pure ranking — deterministic, no model call.
        return sorted(findings, key=lambda f: f.severity.rank, reverse=True)

    def interrogate(self, skeleton: DossierSkeleton, known: dict) -> list[str]:
        prompt = (
            f"Dossier skeleton for {skeleton.name} ({skeleton.sku}, "
            f"{skeleton.garment_type}, {skeleton.collection}). Known: {known}. "
            "List the missing-field questions the author must answer. "
            "One question per line. Do NOT write any dossier content yourself."
        )
        try:
            result = self.agent.run_sync(prompt)
        except Exception as exc:
            raise ReasonerError(f"interrogate failed: {exc}") from exc
        return [ln.strip("-• ").strip() for ln in str(result.output).splitlines()
                if ln.strip()]

    def narrate(self, report: StewardReport) -> str:
        prompt = (
            "Summarize this verification report for a founder in 3-5 lines, "
            f"lead with blockers: {report.to_dict()['summary']}, "
            f"blocking SKUs: "
            f"{[r.sku for r in report.render_readiness if not r.ready]}."
        )
        try:
            return str(self.agent.run_sync(prompt).output)
        except Exception as exc:
            raise ReasonerError(f"narrate failed: {exc}") from exc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_pydantic_ai_reasoner.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/adapters/pydantic_ai_reasoner.py tests/steward/test_pydantic_ai_reasoner.py
git commit -m "feat(steward): PydanticAIReasoner adapter (config-driven model)"
```

---

## Phase 6 — Service + interfaces + snapshot

### Task 15: StewardService

**Files:**
- Create: `skyyrose/steward/service.py`
- Test: `tests/steward/test_service.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_service.py`:
```python
from __future__ import annotations

from skyyrose.steward.adapters.deterministic_reasoner import DeterministicReasoner
from skyyrose.steward.service import StewardService
from tests.steward.conftest import VALID_DOSSIER


def test_service_verify_runs_with_deterministic_reasoner(tmp_catalog, tmp_path):
    golden = tmp_path / "golden"
    (golden / "br-001").mkdir(parents=True)
    (golden / "br-001" / "front.jpg").write_bytes(b"x")
    (golden / "br-001" / "back.jpg").write_bytes(b"x")
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "BLACK Rose Crewneck", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    svc = StewardService(reasoner=DeterministicReasoner())
    report, narrative = svc.verify(
        skus=["br-001"], csv_path=csv_path, dossiers_dir=dossiers, golden_dir=golden,
    )
    assert report.ready_count == 1
    assert isinstance(narrative, str) and narrative


def test_service_scaffold_writes_draft(tmp_catalog, tmp_path):
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={},
    )
    svc = StewardService(reasoner=DeterministicReasoner())
    out, questions = svc.scaffold("br-001", csv_path=csv_path, dossiers_dir=dossiers)
    assert out.name.endswith(".draft.md")
    assert questions  # interrogation questions present
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.service'`

- [ ] **Step 3: Write minimal implementation**

`skyyrose/steward/service.py`:
```python
"""Steward use-case API. Composes the AI-free engine with an LLMReasoner adapter."""

from __future__ import annotations

from pathlib import Path

from skyyrose.steward import engine, scaffold
from skyyrose.steward.models import StewardReport
from skyyrose.steward.ports import LLMReasoner


class StewardService:
    def __init__(self, reasoner: LLMReasoner):
        self._reasoner = reasoner

    def verify(
        self,
        skus: list[str] | None = None,
        csv_path: Path | None = None,
        dossiers_dir: Path | None = None,
        golden_dir: Path | None = None,
        with_vision: bool = False,
        collection: str | None = None,
        status: str | None = None,
        include_all: bool = False,
    ) -> tuple[StewardReport, str]:
        report = engine.verify_catalog(
            skus=skus, csv_path=csv_path, dossiers_dir=dossiers_dir,
            golden_dir=golden_dir, with_vision=with_vision,
            collection=collection, status=status, include_all=include_all,
        )
        prioritized = self._reasoner.prioritize(list(report.findings))
        # prioritize is contractually order-only (see ports.LLMReasoner) — guard it
        # so a misbehaving adapter can't silently corrupt blocking_count/readiness.
        assert len(prioritized) == len(report.findings), (
            "reasoner.prioritize changed the finding count — it must be order-only"
        )
        report = StewardReport(
            findings=tuple(prioritized),
            scores=report.scores,
            render_readiness=report.render_readiness,
        )
        narrative = self._reasoner.narrate(report)
        return report, narrative

    def scaffold(
        self,
        sku: str,
        csv_path: Path | None = None,
        dossiers_dir: Path | None = None,
    ) -> tuple[Path, list[str]]:
        rows = {r["sku"]: r for r in engine._read_rows(csv_path or engine._DEFAULT_CSV)}
        if sku not in rows:
            raise KeyError(f"SKU {sku!r} not in catalog")
        skeleton = scaffold.build_skeleton(rows[sku])
        out = scaffold.write_draft(skeleton, dossiers_dir=dossiers_dir)
        questions = self._reasoner.interrogate(skeleton, known={})
        return out, questions
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_service.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/service.py tests/steward/test_service.py
git commit -m "feat(steward): StewardService (verify + scaffold use-cases)"
```

---

### Task 16: CLI interface

**Files:**
- Create: `skyyrose/steward/interfaces/__init__.py`
- Create: `skyyrose/steward/interfaces/cli.py`
- Create: `skyyrose/steward/__main__.py`
- Test: `tests/steward/test_cli.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_cli.py`:
```python
from __future__ import annotations

from skyyrose.steward.interfaces.cli import build_parser, run


def test_parser_verify_defaults():
    args = build_parser().parse_args(["verify"])
    assert args.command == "verify"
    assert args.with_vision is False


def test_run_verify_json(tmp_catalog, tmp_path, capsys):
    golden = tmp_path / "golden"
    (golden / "br-001").mkdir(parents=True)
    (golden / "br-001" / "front.jpg").write_bytes(b"x")
    (golden / "br-001" / "back.jpg").write_bytes(b"x")
    from tests.steward.conftest import VALID_DOSSIER
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "BLACK Rose Crewneck", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    code = run(["verify", "--json", "--csv", str(csv_path),
                "--dossiers", str(dossiers), "--golden", str(golden)])
    assert code == 0
    out = capsys.readouterr().out
    assert '"summary"' in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.interfaces.cli'`

- [ ] **Step 3: Write minimal implementation**

`skyyrose/steward/interfaces/__init__.py`:
```python
"""Steward interfaces (CLI, MCP) — thin shells over StewardService."""
```

`skyyrose/steward/interfaces/cli.py`:
```python
"""argparse CLI for the Steward. Thin shell over StewardService."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from skyyrose.steward.adapters.deterministic_reasoner import DeterministicReasoner
from skyyrose.steward.service import StewardService


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="skyyrose.steward")
    sub = p.add_subparsers(dest="command", required=True)

    v = sub.add_parser("verify", help="verify catalog↔dossier data quality")
    v.add_argument("--skus", nargs="*", default=None,
                   help="explicit SKU list (overrides scope filters)")
    v.add_argument("--all", action="store_true", default=False,
                   help="check every catalog row (default: published/live only)")
    v.add_argument("--collection", default=None, help="filter to one collection slug")
    v.add_argument("--status", default=None,
                   help="filter by derived status: draft|pre-order|live|retired")
    v.add_argument("--with-vision", action="store_true", default=False)
    v.add_argument("--json", action="store_true", default=False)
    v.add_argument("--csv", default=None)
    v.add_argument("--dossiers", default=None)
    v.add_argument("--golden", default=None)

    s = sub.add_parser("scaffold", help="write a dossier draft skeleton for a SKU")
    s.add_argument("--sku", required=True)
    s.add_argument("--csv", default=None)
    s.add_argument("--dossiers", default=None)
    return p


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    svc = StewardService(reasoner=DeterministicReasoner())

    def _p(x):
        return Path(x) if x else None

    if args.command == "verify":
        report, narrative = svc.verify(
            skus=args.skus, csv_path=_p(args.csv), dossiers_dir=_p(args.dossiers),
            golden_dir=_p(args.golden), with_vision=args.with_vision,
            collection=args.collection, status=args.status, include_all=args.all,
        )
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(narrative)
        return 0

    if args.command == "scaffold":
        out, questions = svc.scaffold(args.sku, csv_path=_p(args.csv),
                                      dossiers_dir=_p(args.dossiers))
        print(f"draft written: {out}")
        print("Author questions:")
        for q in questions:
            print(f"  - {q}")
        return 0

    return 1
```

`skyyrose/steward/__main__.py`:
```python
"""python -m skyyrose.steward entrypoint."""

from __future__ import annotations

import sys

from skyyrose.steward.interfaces.cli import run

if __name__ == "__main__":
    sys.exit(run())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_cli.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add skyyrose/steward/interfaces/__init__.py skyyrose/steward/interfaces/cli.py skyyrose/steward/__main__.py tests/steward/test_cli.py
git commit -m "feat(steward): CLI interface (verify + scaffold)"
```

---

### Task 17: Snapshot test against live catalog

**Files:**
- Test: `tests/steward/test_snapshot.py`

- [ ] **Step 1: Write the test**

`tests/steward/test_snapshot.py`:
```python
"""Runs the engine against the REAL catalog as a data-quality gate (like
test_dossier_completeness.py). Asserts shape + no NEW critical regressions.
"""

from __future__ import annotations

from skyyrose.steward.engine import verify_catalog
from skyyrose.steward.models import Dimension


def test_live_catalog_report_shape():
    # include_all so the count covers every catalog row, not just published.
    report = verify_catalog(include_all=True)  # default real paths, no vision
    assert report.sku_count >= 33  # 33+ active SKUs as of 2026-05-29
    dims = {s.dimension for s in report.scores}
    assert Dimension.ACCURACY not in dims  # vision off by default


def test_no_critical_integrity_regressions():
    """Every catalog SKU with a dossier_slug must have a resolvable dossier."""
    report = verify_catalog(include_all=True)  # check the whole catalog
    crit_integrity = [
        f for f in report.findings
        if f.dimension is Dimension.INTEGRITY and f.severity.value == "critical"
    ]
    # Allow SKUs with no dossier_slug yet, but flag if a slug points nowhere.
    dangling = [f for f in crit_integrity if "has no file" in f.message]
    assert not dangling, "dangling dossier_slug(s):\n" + "\n".join(
        f"{f.sku}: {f.message}" for f in dangling
    )
```

- [ ] **Step 2: Run test**

Run: `pytest tests/steward/test_snapshot.py -v`
Expected: PASS. If `test_no_critical_integrity_regressions` FAILS, a catalog `dossier_slug` points to a missing file — fix the catalog/dossier, not the test.

- [ ] **Step 3: Commit**

```bash
git add tests/steward/test_snapshot.py
git commit -m "test(steward): live-catalog snapshot data-quality gate"
```

---

### Task 18: MCP interface + public exports + full suite

**Files:**
- Create: `skyyrose/steward/interfaces/mcp.py`
- Modify: `skyyrose/steward/__init__.py`
- Test: `tests/steward/test_mcp.py`

- [ ] **Step 1: Write the failing test**

`tests/steward/test_mcp.py`:
```python
from __future__ import annotations

from skyyrose.steward.interfaces.mcp import steward_verify, steward_scaffold


def test_mcp_verify_returns_dict(tmp_catalog, tmp_path):
    golden = tmp_path / "golden"
    (golden / "br-001").mkdir(parents=True)
    (golden / "br-001" / "front.jpg").write_bytes(b"x")
    (golden / "br-001" / "back.jpg").write_bytes(b"x")
    from tests.steward.conftest import VALID_DOSSIER
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "BLACK Rose Crewneck", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={"black-rose-crewneck": VALID_DOSSIER},
    )
    out = steward_verify(csv=str(csv_path), dossiers=str(dossiers), golden=str(golden))
    assert out["summary"]["sku_count"] == 1


def test_mcp_scaffold_returns_draft_path(tmp_catalog, tmp_path):
    csv_path, dossiers = tmp_catalog(
        rows=[{"sku": "br-001", "name": "X", "collection": "black-rose",
               "dossier_slug": "black-rose-crewneck", "garment_type_lock": "crewneck"}],
        dossier_files={},
    )
    out = steward_scaffold(sku="br-001", csv=str(csv_path), dossiers=str(dossiers))
    assert out["draft_path"].endswith(".draft.md")
    assert out["questions"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/steward/test_mcp.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.steward.interfaces.mcp'`

- [ ] **Step 3: Write minimal implementation**

`skyyrose/steward/interfaces/mcp.py`:
```python
"""MCP-style tool functions for the Steward. Thin shell over StewardService.

Plain functions returning JSON-serializable dicts so they can be registered by
any MCP server wrapper (DevSkyy devskyy_mcp.py) or called directly. AI-optional:
uses the DeterministicReasoner so the tools run with zero AI.
"""

from __future__ import annotations

from pathlib import Path

from skyyrose.steward.adapters.deterministic_reasoner import DeterministicReasoner
from skyyrose.steward.service import StewardService


def _svc() -> StewardService:
    return StewardService(reasoner=DeterministicReasoner())


def steward_verify(
    skus: list[str] | None = None,
    with_vision: bool = False,
    csv: str | None = None,
    dossiers: str | None = None,
    golden: str | None = None,
) -> dict:
    """Verify catalog↔dossier data quality; returns the report as a dict."""
    report, narrative = _svc().verify(
        skus=skus,
        csv_path=Path(csv) if csv else None,
        dossiers_dir=Path(dossiers) if dossiers else None,
        golden_dir=Path(golden) if golden else None,
        with_vision=with_vision,
    )
    data = report.to_dict()
    data["narrative"] = narrative
    return data


def steward_scaffold(
    sku: str,
    csv: str | None = None,
    dossiers: str | None = None,
) -> dict:
    """Write a dossier draft skeleton for a SKU; returns draft path + author questions."""
    out, questions = _svc().scaffold(
        sku,
        csv_path=Path(csv) if csv else None,
        dossiers_dir=Path(dossiers) if dossiers else None,
    )
    return {"draft_path": str(out), "questions": questions}
```

Append to `skyyrose/steward/__init__.py`:
```python
from skyyrose.steward.engine import verify_catalog
from skyyrose.steward.models import (
    Dimension,
    Finding,
    Severity,
    StewardReport,
)
from skyyrose.steward.service import StewardService

__all__ = [
    "verify_catalog",
    "StewardService",
    "StewardReport",
    "Finding",
    "Severity",
    "Dimension",
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/steward/test_mcp.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the FULL steward suite + lint**

Run: `pytest tests/steward/ -v`
Expected: PASS (all). Then:
Run: `isort skyyrose/steward tests/steward && ruff check --fix skyyrose/steward tests/steward && black skyyrose/steward tests/steward`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add skyyrose/steward/interfaces/mcp.py skyyrose/steward/__init__.py tests/steward/test_mcp.py
git commit -m "feat(steward): MCP tool interface + public exports"
```

---

### Task 19: Wire CLI into pyproject + docs

**Files:**
- Modify: `pyproject.toml` (`[project.scripts]` if present, else skip)
- Create: `skyyrose/steward/README.md`

- [ ] **Step 1: Add console script (only if `[project.scripts]` exists in pyproject.toml)**

Check first: `grep -n "\[project.scripts\]" pyproject.toml`
If present, add under it:
```toml
steward = "skyyrose.steward.interfaces.cli:run"
```
If absent, skip — `python -m skyyrose.steward` already works via `__main__.py`.

- [ ] **Step 2: Write the README**

`skyyrose/steward/README.md`:
```markdown
# Catalog & Dossier Steward

AI-free verification engine + swappable AI reasoning for SkyyRose catalog/dossier QA.

## Usage

```bash
# Verify the whole catalog (human summary)
python -m skyyrose.steward verify

# Machine-readable report
python -m skyyrose.steward verify --json

# Specific SKUs + golden-reference accuracy (needs vision deps)
python -m skyyrose.steward verify --skus br-001 lh-002 --with-vision

# Scaffold a dossier draft (placeholders only — you author the content)
python -m skyyrose.steward scaffold --sku br-001
```

Drafts land in `wordpress-theme/skyyrose-flagship/data/dossiers/_drafts/{slug}.draft.md`.
The canonical `{slug}.md` is NEVER machine-written.

## Architecture
See `docs/superpowers/specs/2026-05-29-catalog-dossier-steward-design.md`.
Core (`engine/scaffold/models/config`) is AI-free (guarded by `tests/steward/test_ai_free_core.py`).
AI sits behind `ports.LLMReasoner`; swap adapters to change/remove AI.
```

- [ ] **Step 3: Run full suite once more**

Run: `pytest tests/steward/ -v && pytest tests/test_dossier_completeness.py -v`
Expected: PASS (steward suite + existing dossier gate both green).

- [ ] **Step 4: Commit**

```bash
git add skyyrose/steward/README.md pyproject.toml
git commit -m "docs(steward): usage README + console script wiring"
```

---

## Self-Review (completed by plan author)

**Spec coverage:**
- §3 hexagonal (core/ports/adapters/interfaces) → Tasks 1-18 ✓
- §4 six dimensions → Tasks 5-10 ✓ (Accuracy flag-gated in 10)
- §5 scaffold+interrogate, drafts never canonical → Tasks 3, 11, 12 ✓
- §6 LLMReasoner port + 2 adapters → Tasks 12, 14 ✓
- §7 record-don't-crash, degrade to deterministic → engine returns Findings (Tasks 5-10); service accepts any reasoner (Task 15) ✓
- §8 config-driven model routing → Task 4 ✓
- §9 testing (per-dimension, TestModel, deterministic, snapshot) → Tasks 5-18 ✓
- §10 supersession → deferred to Phase 2 spec (non-goal here) ✓
- §11 file layout (plain B) → File Structure table ✓
- AI-free guarantee enforced by test → Task 13 ✓

**Placeholder scan:** none — every code step has complete code. `TODO-AUTHOR` strings are intentional dossier-skeleton placeholders (asserted by tests), not plan placeholders.

**Type consistency:** `Finding`, `StewardReport.from_findings(findings, skus, scores)`, `DimensionScore(dimension, passed, failed)`, `verify_catalog(skus, csv_path, dossiers_dir, golden_dir, with_vision)`, `LLMReasoner.{prioritize, interrogate, narrate}` — names consistent across Tasks 1-18. `engine._read_rows` / `engine._DEFAULT_CSV` reused by Task 15 (defined Task 5/10). ✓

**Known deviation:** `StewardService.scaffold` reaches into `engine._read_rows` (private). Acceptable — same package; alternative is a public `engine.read_rows` (rename in Task 5 if a reviewer prefers).

## Review fixes applied (advisor pass, 2026-05-29)

- **Accuracy false-green killed (Task 10):** `check_accuracy` returns `(findings, ran)`; until real CLIP/DINOv2 scoring exists `ran=False`, so ACCURACY is **excluded from scores** and emits a "NOT verified" finding. New test `test_accuracy_with_vision_never_false_greens` locks this. A faked 100% accuracy pass is the exact anti-hallucination failure the engine exists to prevent.
- **`prioritize` order-only invariant (Tasks 12, 15):** documented on the `LLMReasoner` port; `StewardService.verify` asserts `len(prioritized) == len(findings)` so a misbehaving adapter can't silently corrupt `blocking_count`/readiness.
- **SKU scope filter (Task 10) — RESOLVED:** Corey chose "build a filter." `select_skus()` resolves the work-set with precedence `explicit skus > include_all > collection/status filter > default published/live only`. Default published-only avoids flooding the report with golden-missing noise for draft SKUs. Exposed on the CLI as `--skus / --all / --collection / --status`, threaded through `StewardService.verify` and `engine.verify_catalog`. Snapshot test (Task 17) passes `include_all=True` to cover the whole catalog. Tested by `test_select_skus_default_is_published_only`.
- **Supersession is Phase 2, not now:** `PRODUCT_ANALYST` + `QA_INSPECTOR` keep running unchanged this slice; the engine is built first, they get rewired onto it in the separate Phase 2 spec.
- **Engine duplication note (Task 5):** validity/consistency/completeness each load+parse the dossier (cached read, re-parsed). A `_load_safe(sku,row,dir)->(Dossier|None, schema|None, findings)` helper is a fair refactor if a reviewer prefers DRY over the explicit per-dimension form; left explicit here for TDD clarity. engine.py stays well under 800 lines (~6 functions).
