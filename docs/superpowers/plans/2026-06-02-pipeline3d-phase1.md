# Unified 3D Pipeline Orchestrator — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a provider-agnostic staged 3D pipeline (Tripo-only vertical slice) that runs `image-to-3D → texture → remesh → export-GLB` for one SKU, driven by a CLI, wired through `RunBudget` + a STOP-AND-SHOW cost gate + telemetry + stage-level idempotency.

**Architecture:** Hexagonal. A deterministic core (`models`, `executor`, `router`, `estimator`, `store`) orchestrates stages; provider work lives behind an `Adapter` port. Stages chain by provider-native `task_id` (same-provider) carried on a unified `Artifact` handle. Execution spine is synchronous-within-stage (the adapter polls its provider to completion via the `tripo3d` SDK's `wait_for_task`); no event-driven DAG advancement.

**Tech Stack:** Python 3.11+, `tripo3d` SDK 0.4.1 (already installed), pytest, existing `skyyrose/elite_studio/{budget,telemetry,forensics}.py`.

**Spec:** `docs/superpowers/specs/2026-06-02-pipeline3d-orchestrator-design.html`

**Verified facts (this session):**
- `RunBudget.ensure_within_budget(cost_usd, stage="...")` raises `BudgetExceededError` before spend; `RunBudget.spend(cost_usd, stage)` records after; `RunBudget(ceiling_usd=...)`.
- `telemetry.stage(*, run_id, stage_name, sku, scene_name="", collection="", input_hash=None)` context manager; `telemetry.new_run_id()`; `telemetry.hash_inputs(*parts)`.
- `tripo3d.TripoClient` async context manager. Methods (exact signatures verified):
  - `image_to_model(image: str, ..., texture=True, pbr=True, face_limit=None) -> str` (task_id)
  - `texture_model(original_model_task_id: str, texture=True, pbr=True, ...) -> str`
  - `smart_lowpoly(original_model_task_id: str, face_limit=None, quad=False, ...) -> str`  ← remesh-to-GLB
  - `convert_model(original_model_task_id, format: Literal['GLTF','USDZ','FBX','OBJ','STL','3MF'], ...)` ← **GLB not accepted** (native); deferred for USDZ/FBX only
  - `wait_for_task(task_id, polling_interval=2.0, timeout=None, verbose=False) -> Task`
  - `download_task_models(task: Task, output_dir: str) -> Dict[str, str]`
  - `get_task(task_id) -> Task`, `get_balance() -> Balance`
  - `Task` has `.status` (`tripo3d.TaskStatus`), `.output` (`tripo3d.TaskOutput` with `.model`, `.pbr_model`, `.base_model`).

**Conventions:** every new package dir gets `__init__.py` (project rule — no implicit namespace packages). Frozen dataclasses for data. `black`/`ruff`/`isort`, line length 100. Tests under `tests/elite_studio/pipeline3d/`. Commit after every green step.

---

## File structure

| File | Responsibility |
|------|----------------|
| `skyyrose/elite_studio/pipeline3d/__init__.py` | package marker + public exports |
| `skyyrose/elite_studio/pipeline3d/models.py` | `Stage`, `TaskStatus`, `Artifact`, `StageSpec`, `JobSpec`, `StageResult`, `PipelineResult`, `STAGE_ORDER`, `ordered_stages()` |
| `skyyrose/elite_studio/pipeline3d/adapters/__init__.py` | adapters package marker |
| `skyyrose/elite_studio/pipeline3d/adapters/base.py` | `Adapter` Protocol + `StageContext` |
| `skyyrose/elite_studio/pipeline3d/store.py` | `StageStore` — file-based stage-level idempotency |
| `skyyrose/elite_studio/pipeline3d/router.py` | `Router.pick()` + `candidates()` + fallback + `NoAdapterError` |
| `skyyrose/elite_studio/pipeline3d/estimator.py` | `estimate(job, router)` — whole-job cost |
| `skyyrose/elite_studio/pipeline3d/executor.py` | `run_job()` — ordered stages, skip-cached, budget gate, telemetry, chaining |
| `skyyrose/elite_studio/pipeline3d/adapters/local_export.py` | `LocalExportAdapter` — EXPORT stage (download/copy to canonical path) |
| `skyyrose/elite_studio/pipeline3d/adapters/tripo.py` | `TripoAdapter` — IMAGE_TO_3D / TEXTURE / REMESH via tripo3d SDK |
| `skyyrose/elite_studio/pipeline3d/preflight.py` | `resolve_source()` — SKU/image resolution + source-exists guard |
| `skyyrose/elite_studio/pipeline3d/__main__.py` | CLI: `gen3d` (argparse) → preflight → estimate → confirm → run_job |
| `tests/elite_studio/pipeline3d/*` | unit tests per module (mock adapters; zero paid calls) |

---

### Task 1: Package scaffold + core models

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/__init__.py`
- Create: `skyyrose/elite_studio/pipeline3d/models.py`
- Create: `tests/elite_studio/pipeline3d/__init__.py`
- Test: `tests/elite_studio/pipeline3d/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_models.py
from pathlib import Path

from skyyrose.elite_studio.pipeline3d.models import (
    Artifact,
    JobSpec,
    PipelineResult,
    Stage,
    StageResult,
    TaskStatus,
    STAGE_ORDER,
    ordered_stages,
)


def test_stage_values():
    assert Stage.IMAGE_TO_3D.value == "image_to_3d"
    assert Stage.EXPORT.value == "export"


def test_stage_order_is_canonical():
    assert STAGE_ORDER == (Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH, Stage.EXPORT)


def test_ordered_stages_sorts_and_filters():
    # requested out of order + missing TEXTURE -> canonical order, TEXTURE dropped
    got = ordered_stages((Stage.EXPORT, Stage.IMAGE_TO_3D, Stage.REMESH))
    assert got == (Stage.IMAGE_TO_3D, Stage.REMESH, Stage.EXPORT)


def test_artifact_is_frozen():
    a = Artifact(provider="tripo", task_id="t1", path=Path("x.glb"))
    assert a.fmt == "glb"
    try:
        a.provider = "meshy"  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised


def test_jobspec_defaults():
    j = JobSpec(sku="br-001", source_image=Path("src.png"), stages=(Stage.IMAGE_TO_3D,))
    assert j.formats == ("glb",)
    assert j.budget_ceiling_usd == 5.0
    assert j.output_dir == Path("renders/3d")


def test_pipeline_result_holds_results():
    art = Artifact(provider="tripo", path=Path("o.glb"))
    r = StageResult(stage=Stage.IMAGE_TO_3D, artifact=art, cost_usd=0.4, duration_ms=10)
    pr = PipelineResult(
        job_id="abc",
        sku="br-001",
        status=TaskStatus.SUCCEEDED,
        results=(r,),
        final_artifact=art,
        total_cost_usd=0.4,
    )
    assert pr.status is TaskStatus.SUCCEEDED
    assert pr.results[0].cost_usd == 0.4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'skyyrose.elite_studio.pipeline3d'`

- [ ] **Step 3: Write the package markers and models**

```python
# skyyrose/elite_studio/pipeline3d/__init__.py
"""Unified 3D pipeline orchestrator (Tripo/Meshy workflow clone). Phase 1: Tripo vertical slice."""

from .models import (
    Artifact,
    JobSpec,
    PipelineResult,
    Stage,
    StageResult,
    StageSpec,
    TaskStatus,
    STAGE_ORDER,
    ordered_stages,
)

__all__ = [
    "Artifact",
    "JobSpec",
    "PipelineResult",
    "Stage",
    "StageResult",
    "StageSpec",
    "TaskStatus",
    "STAGE_ORDER",
    "ordered_stages",
]
```

```python
# tests/elite_studio/pipeline3d/__init__.py
```

```python
# skyyrose/elite_studio/pipeline3d/models.py
"""Core data types for the 3D pipeline orchestrator.

All data is immutable (frozen dataclasses). The Artifact is the chaining
handle: it carries BOTH a provider-native task_id (cheap same-provider
chaining) AND a downloadable model_url / local path (cross-provider handoff).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class Stage(StrEnum):
    """Fashion-tuned pipeline stages (no rig/animate)."""

    IMAGE_TO_3D = "image_to_3d"
    TEXTURE = "texture"
    REMESH = "remesh"
    EXPORT = "export"


class TaskStatus(StrEnum):
    """Normalized cross-provider task status (Meshy UPPERCASE + Tripo lowercase -> one enum)."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


#: Canonical dependency order. Executor runs stages in this order, skipping
#: any not requested.
STAGE_ORDER: tuple[Stage, ...] = (
    Stage.IMAGE_TO_3D,
    Stage.TEXTURE,
    Stage.REMESH,
    Stage.EXPORT,
)


def ordered_stages(stages: tuple[Stage, ...]) -> tuple[Stage, ...]:
    """Return the requested stages in canonical dependency order."""
    requested = set(stages)
    return tuple(s for s in STAGE_ORDER if s in requested)


@dataclass(frozen=True)
class Artifact:
    """The chaining handle passed from stage to stage."""

    provider: str
    fmt: str = "glb"
    task_id: str | None = None
    model_url: str | None = None
    path: Path | None = None
    polycount: int | None = None
    bytes: int | None = None
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StageSpec:
    """A requested stage plus its per-stage parameters."""

    stage: Stage
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class JobSpec:
    """A complete pipeline job."""

    sku: str
    source_image: Path
    stages: tuple[Stage, ...]
    formats: tuple[str, ...] = ("glb",)
    provider_hint: str | None = None
    budget_ceiling_usd: float = 5.0
    output_dir: Path = Path("renders/3d")
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StageResult:
    """Outcome of one stage."""

    stage: Stage
    artifact: Artifact
    cost_usd: float
    duration_ms: int
    cached: bool = False


@dataclass(frozen=True)
class PipelineResult:
    """Outcome of a whole job."""

    job_id: str
    sku: str
    status: TaskStatus
    results: tuple[StageResult, ...]
    final_artifact: Artifact | None
    total_cost_usd: float
    manifest_path: Path | None = None
    error: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_models.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/__init__.py skyyrose/elite_studio/pipeline3d/models.py tests/elite_studio/pipeline3d/__init__.py tests/elite_studio/pipeline3d/test_models.py
git commit -m "feat(pipeline3d): core data models for 3D orchestrator"
```

---

### Task 2: Adapter port + StageContext

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/adapters/__init__.py`
- Create: `skyyrose/elite_studio/pipeline3d/adapters/base.py`
- Test: `tests/elite_studio/pipeline3d/test_base.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_base.py
from pathlib import Path

from skyyrose.elite_studio.pipeline3d.adapters.base import Adapter, StageContext
from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage


class _FakeAdapter:
    name = "fake"

    def supports(self, stage: Stage) -> bool:
        return stage in (Stage.IMAGE_TO_3D, Stage.TEXTURE)

    def available(self) -> bool:
        return True

    def estimate_cost(self, stage: Stage, params: dict) -> float:
        return 1.0

    async def run_stage(self, stage: Stage, ctx: StageContext) -> Artifact:
        return Artifact(provider=self.name, task_id="t", path=ctx.output_dir / "x.glb")


def test_fake_satisfies_protocol():
    assert isinstance(_FakeAdapter(), Adapter)


def test_stage_context_defaults():
    ctx = StageContext(sku="br-001", source_image=Path("s.png"), output_dir=Path("/tmp/out"))
    assert ctx.last_artifact is None
    assert ctx.params == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_base.py -v`
Expected: FAIL — `ModuleNotFoundError: ...adapters.base`

- [ ] **Step 3: Write the port + context**

```python
# skyyrose/elite_studio/pipeline3d/adapters/__init__.py
"""Provider adapters for the 3D pipeline. Each wraps one engine behind the Adapter port."""
```

```python
# skyyrose/elite_studio/pipeline3d/adapters/base.py
"""Adapter port and the per-job mutable StageContext.

An Adapter wraps one provider (Tripo, Meshy, TRELLIS, local). The executor
holds a StageContext and threads each stage's output into the next via
``ctx.last_artifact`` — that is the chaining seam.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from ..models import Artifact, Stage


@dataclass
class StageContext:
    """Mutable per-job context threaded through stages."""

    sku: str
    source_image: Path
    output_dir: Path
    last_artifact: Artifact | None = None
    params: dict = field(default_factory=dict)


@runtime_checkable
class Adapter(Protocol):
    """A provider behind one or more pipeline stages."""

    name: str

    def supports(self, stage: Stage) -> bool:
        """True if this adapter can run the given stage."""
        ...

    def available(self) -> bool:
        """True if this adapter is usable now (e.g. API key present)."""
        ...

    def estimate_cost(self, stage: Stage, params: dict) -> float:
        """Estimated USD cost for running the given stage."""
        ...

    async def run_stage(self, stage: Stage, ctx: StageContext) -> Artifact:
        """Execute the stage (blocking: submit -> poll -> download) and return the artifact."""
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_base.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/adapters/ tests/elite_studio/pipeline3d/test_base.py
git commit -m "feat(pipeline3d): Adapter port + StageContext"
```

---

### Task 3: StageStore (file-based stage-level idempotency)

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/store.py`
- Test: `tests/elite_studio/pipeline3d/test_store.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_store.py
from pathlib import Path

from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage, StageResult
from skyyrose.elite_studio.pipeline3d.store import StageStore


def _result(tmp_path: Path) -> StageResult:
    art = Artifact(provider="tripo", task_id="t1", path=tmp_path / "m.glb", meta={"k": "v"})
    return StageResult(stage=Stage.IMAGE_TO_3D, artifact=art, cost_usd=0.4, duration_ms=123)


def test_miss_then_hit_roundtrip(tmp_path):
    store = StageStore(tmp_path / "store")
    h = "abc123"
    assert store.has(h, Stage.IMAGE_TO_3D) is False
    store.put(h, _result(tmp_path))
    assert store.has(h, Stage.IMAGE_TO_3D) is True
    got = store.get(h, Stage.IMAGE_TO_3D)
    assert got is not None
    assert got.cached is True
    assert got.artifact.task_id == "t1"
    assert got.artifact.path == tmp_path / "m.glb"
    assert got.artifact.meta == {"k": "v"}
    assert got.cost_usd == 0.4


def test_different_input_hash_is_isolated(tmp_path):
    store = StageStore(tmp_path / "store")
    store.put("hashA", _result(tmp_path))
    assert store.has("hashB", Stage.IMAGE_TO_3D) is False


def test_get_missing_returns_none(tmp_path):
    store = StageStore(tmp_path / "store")
    assert store.get("nope", Stage.REMESH) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_store.py -v`
Expected: FAIL — `ModuleNotFoundError: ...store`

- [ ] **Step 3: Write the store**

```python
# skyyrose/elite_studio/pipeline3d/store.py
"""File-based stage-level idempotency.

A job that dies at remesh must NOT re-bill image-to-3D + texture on retry.
Each completed stage result is persisted keyed by an input hash; resumed jobs
skip stages already present. One JSON file per input hash, stages as keys.

Phase 3 swaps this for the Redis-backed IdempotencyCache used by the async API;
the interface (has/get/put) is identical so callers are unaffected.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import Artifact, Stage, StageResult


class StageStore:
    """Persist and retrieve StageResults keyed by (input_hash, stage)."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, input_hash: str) -> Path:
        return self._root / f"{input_hash}.json"

    def _load(self, input_hash: str) -> dict:
        p = self._path(input_hash)
        if not p.is_file():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def has(self, input_hash: str, stage: Stage) -> bool:
        return stage.value in self._load(input_hash)

    def get(self, input_hash: str, stage: Stage) -> StageResult | None:
        rec = self._load(input_hash).get(stage.value)
        if not rec:
            return None
        art = dict(rec["artifact"])
        art["path"] = Path(art["path"]) if art.get("path") else None
        return StageResult(
            stage=stage,
            artifact=Artifact(**art),
            cost_usd=rec["cost_usd"],
            duration_ms=rec["duration_ms"],
            cached=True,
        )

    def put(self, input_hash: str, result: StageResult) -> None:
        data = self._load(input_hash)
        art = asdict(result.artifact)
        art["path"] = str(art["path"]) if art["path"] is not None else None
        data[result.stage.value] = {
            "artifact": art,
            "cost_usd": result.cost_usd,
            "duration_ms": result.duration_ms,
        }
        self._path(input_hash).write_text(
            json.dumps(data, indent=2, sort_keys=True, default=str), encoding="utf-8"
        )


__all__ = ["StageStore"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_store.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/store.py tests/elite_studio/pipeline3d/test_store.py
git commit -m "feat(pipeline3d): file-based stage-level idempotency store"
```

---

### Task 4: Router (capability + priority + availability + fallback)

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/router.py`
- Test: `tests/elite_studio/pipeline3d/test_router.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_router.py
import pytest

from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage
from skyyrose.elite_studio.pipeline3d.router import NoAdapterError, Router


class _Stub:
    def __init__(self, name, stages, available=True):
        self.name = name
        self._stages = set(stages)
        self._available = available

    def supports(self, stage):
        return stage in self._stages

    def available(self):
        return self._available

    def estimate_cost(self, stage, params):
        return 0.0

    async def run_stage(self, stage, ctx):
        return Artifact(provider=self.name)


def test_pick_respects_priority():
    a = _Stub("tripo", [Stage.IMAGE_TO_3D])
    b = _Stub("meshy", [Stage.IMAGE_TO_3D])
    r = Router([b, a], priority=["tripo", "meshy"])
    assert r.pick(Stage.IMAGE_TO_3D).name == "tripo"


def test_pick_skips_unavailable():
    a = _Stub("tripo", [Stage.IMAGE_TO_3D], available=False)
    b = _Stub("meshy", [Stage.IMAGE_TO_3D])
    r = Router([a, b], priority=["tripo", "meshy"])
    assert r.pick(Stage.IMAGE_TO_3D).name == "meshy"


def test_pick_skips_incapable():
    a = _Stub("tripo", [Stage.TEXTURE])
    b = _Stub("local", [Stage.EXPORT])
    r = Router([a, b])
    assert r.pick(Stage.EXPORT).name == "local"


def test_exclude_enables_fallback():
    a = _Stub("tripo", [Stage.REMESH])
    b = _Stub("meshy", [Stage.REMESH])
    r = Router([a, b], priority=["tripo", "meshy"])
    assert r.pick(Stage.REMESH, exclude={"tripo"}).name == "meshy"


def test_no_adapter_raises():
    r = Router([_Stub("tripo", [Stage.IMAGE_TO_3D])])
    with pytest.raises(NoAdapterError):
        r.pick(Stage.EXPORT)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_router.py -v`
Expected: FAIL — `ModuleNotFoundError: ...router`

- [ ] **Step 3: Write the router**

```python
# skyyrose/elite_studio/pipeline3d/router.py
"""Provider router: choose an adapter per stage by capability, priority, availability.

On stage failure the executor can call ``pick(stage, exclude=...)`` to fall back
to the next capable adapter (artifact handoff). This is the single place that
knows which engine runs which stage.
"""

from __future__ import annotations

from .adapters.base import Adapter
from .models import Stage


class NoAdapterError(RuntimeError):
    """No available, capable adapter exists for the requested stage."""


class Router:
    """Selects adapters for stages by priority order."""

    def __init__(self, adapters: list[Adapter], priority: list[str] | None = None) -> None:
        self._adapters = list(adapters)
        self._priority = priority or [a.name for a in adapters]

    def _ordered(self) -> list[Adapter]:
        idx = {name: i for i, name in enumerate(self._priority)}
        return sorted(self._adapters, key=lambda a: idx.get(a.name, len(idx) + 1))

    def candidates(self, stage: Stage) -> list[Adapter]:
        """All available, capable adapters for a stage, in priority order."""
        return [a for a in self._ordered() if a.supports(stage) and a.available()]

    def pick(self, stage: Stage, *, exclude: set[str] | None = None) -> Adapter:
        """Highest-priority available adapter for a stage, skipping ``exclude``."""
        skip = exclude or set()
        for adapter in self.candidates(stage):
            if adapter.name not in skip:
                return adapter
        raise NoAdapterError(f"no available adapter for stage={stage.value!r}")


__all__ = ["Router", "NoAdapterError"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_router.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/router.py tests/elite_studio/pipeline3d/test_router.py
git commit -m "feat(pipeline3d): provider router with priority + fallback"
```

---

### Task 5: Estimator (whole-job cost, computed once)

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/estimator.py`
- Test: `tests/elite_studio/pipeline3d/test_estimator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_estimator.py
from pathlib import Path

from skyyrose.elite_studio.pipeline3d.estimator import estimate
from skyyrose.elite_studio.pipeline3d.models import Artifact, JobSpec, Stage
from skyyrose.elite_studio.pipeline3d.router import Router


class _Stub:
    def __init__(self, name, costs):
        self.name = name
        self._costs = costs  # dict[Stage, float]

    def supports(self, stage):
        return stage in self._costs

    def available(self):
        return True

    def estimate_cost(self, stage, params):
        return self._costs[stage]

    async def run_stage(self, stage, ctx):
        return Artifact(provider=self.name)


def test_estimate_sums_per_stage_from_top_priority():
    tripo = _Stub("tripo", {Stage.IMAGE_TO_3D: 0.40, Stage.TEXTURE: 0.20, Stage.REMESH: 0.15})
    local = _Stub("local", {Stage.EXPORT: 0.0})
    router = Router([tripo, local], priority=["tripo", "local"])
    job = JobSpec(
        sku="br-001",
        source_image=Path("s.png"),
        stages=(Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH, Stage.EXPORT),
    )
    out = estimate(job, router)
    assert out["by_stage"] == {
        "image_to_3d": 0.40,
        "texture": 0.20,
        "remesh": 0.15,
        "export": 0.0,
    }
    assert out["total_usd"] == 0.75


def test_estimate_zero_when_no_candidate():
    router = Router([_Stub("tripo", {Stage.IMAGE_TO_3D: 0.40})], priority=["tripo"])
    job = JobSpec(sku="x", source_image=Path("s.png"), stages=(Stage.EXPORT,))
    out = estimate(job, router)
    assert out["by_stage"] == {"export": 0.0}
    assert out["total_usd"] == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_estimator.py -v`
Expected: FAIL — `ModuleNotFoundError: ...estimator`

- [ ] **Step 3: Write the estimator**

```python
# skyyrose/elite_studio/pipeline3d/estimator.py
"""Whole-job cost estimate, computed ONCE before the job starts.

Sums the top-priority candidate's per-stage cost across the requested stages.
The CLI shows the single total via the STOP-AND-SHOW gate — not one prompt
per stage.
"""

from __future__ import annotations

from .models import JobSpec, ordered_stages
from .router import Router


def estimate(job: JobSpec, router: Router) -> dict:
    """Return ``{"by_stage": {stage: usd}, "total_usd": float}``."""
    by_stage: dict[str, float] = {}
    for stage in ordered_stages(job.stages):
        candidates = router.candidates(stage)
        cost = candidates[0].estimate_cost(stage, job.params) if candidates else 0.0
        by_stage[stage.value] = round(cost, 4)
    total = round(sum(by_stage.values()), 4)
    return {"by_stage": by_stage, "total_usd": total}


__all__ = ["estimate"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_estimator.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/estimator.py tests/elite_studio/pipeline3d/test_estimator.py
git commit -m "feat(pipeline3d): whole-job cost estimator"
```

---

### Task 6: Executor (the orchestration heart)

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/executor.py`
- Test: `tests/elite_studio/pipeline3d/test_executor.py`

The executor runs stages in canonical order; skips stages already in the store
(idempotent resume); gates each paid stage on `RunBudget`; wraps each stage in a
telemetry span; chains `ctx.last_artifact` from one stage to the next; and on a
stage exception returns a `FAILED` `PipelineResult` with partial results (so a
retry resumes from the failed stage).

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_executor.py
import pytest

from skyyrose.elite_studio.budget import BudgetExceededError, RunBudget
from skyyrose.elite_studio.pipeline3d.executor import run_job
from skyyrose.elite_studio.pipeline3d.models import (
    Artifact,
    JobSpec,
    Stage,
    StageResult,
    TaskStatus,
)
from skyyrose.elite_studio.pipeline3d.router import Router
from skyyrose.elite_studio.pipeline3d.store import StageStore


class _RecordingAdapter:
    """Records calls; produces a deterministic artifact carrying the prior task_id."""

    def __init__(self, name, stages, cost=0.5, fail_on=None):
        self.name = name
        self._stages = set(stages)
        self._cost = cost
        self._fail_on = fail_on
        self.calls = []

    def supports(self, stage):
        return stage in self._stages

    def available(self):
        return True

    def estimate_cost(self, stage, params):
        return self._cost

    async def run_stage(self, stage, ctx):
        self.calls.append((stage, ctx.last_artifact.task_id if ctx.last_artifact else None))
        if self._fail_on is not None and stage == self._fail_on:
            raise RuntimeError(f"boom at {stage.value}")
        return Artifact(provider=self.name, task_id=f"{stage.value}-id", path=ctx.output_dir / "m.glb")


def _job(tmp_path, stages):
    return JobSpec(
        sku="br-001",
        source_image=tmp_path / "src.png",
        stages=stages,
        output_dir=tmp_path / "out",
    )


@pytest.mark.asyncio
async def test_runs_stages_in_order_and_chains_task_id(tmp_path):
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH])
    router = Router([adapter], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=10.0)
    job = _job(tmp_path, (Stage.REMESH, Stage.IMAGE_TO_3D, Stage.TEXTURE))

    result = await run_job(job, router=router, store=store, budget=budget)

    assert result.status is TaskStatus.SUCCEEDED
    assert [s for s, _ in adapter.calls] == [Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH]
    # chaining: texture saw image_to_3d's task_id; remesh saw texture's
    assert adapter.calls[1][1] == "image_to_3d-id"
    assert adapter.calls[2][1] == "texture-id"
    assert result.total_cost_usd == 1.5


@pytest.mark.asyncio
async def test_budget_blocks_before_paid_call(tmp_path):
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D], cost=99.0)
    router = Router([adapter], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=1.0)
    job = _job(tmp_path, (Stage.IMAGE_TO_3D,))

    with pytest.raises(BudgetExceededError):
        await run_job(job, router=router, store=store, budget=budget)
    assert adapter.calls == []  # never dispatched


@pytest.mark.asyncio
async def test_cached_stage_is_skipped(tmp_path):
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D, Stage.TEXTURE])
    router = Router([adapter], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=10.0)
    h = "fixedhash"
    # pre-seed IMAGE_TO_3D
    store.put(
        h,
        StageResult(
            stage=Stage.IMAGE_TO_3D,
            artifact=Artifact(provider="tripo", task_id="cached-id", path=tmp_path / "c.glb"),
            cost_usd=0.4,
            duration_ms=5,
        ),
    )
    job = _job(tmp_path, (Stage.IMAGE_TO_3D, Stage.TEXTURE))

    result = await run_job(job, router=router, store=store, budget=budget, input_hash=h)

    # image_to_3d skipped; only texture ran, and it chained the cached task_id
    assert [s for s, _ in adapter.calls] == [Stage.TEXTURE]
    assert adapter.calls[0][1] == "cached-id"
    assert result.results[0].cached is True
    assert budget.spent_usd == 0.5  # only texture charged


@pytest.mark.asyncio
async def test_stage_failure_returns_partial_failed_result(tmp_path):
    adapter = _RecordingAdapter("tripo", [Stage.IMAGE_TO_3D, Stage.TEXTURE], fail_on=Stage.TEXTURE)
    router = Router([adapter], priority=["tripo"])
    store = StageStore(tmp_path / "store")
    budget = RunBudget(ceiling_usd=10.0)
    job = _job(tmp_path, (Stage.IMAGE_TO_3D, Stage.TEXTURE))

    result = await run_job(job, router=router, store=store, budget=budget)

    assert result.status is TaskStatus.FAILED
    assert result.error is not None and "boom" in result.error
    assert len(result.results) == 1  # image_to_3d succeeded and is persisted
    # image_to_3d cost charged, texture not
    assert budget.spent_usd == 0.5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_executor.py -v`
Expected: FAIL — `ModuleNotFoundError: ...executor`

(If `pytest-asyncio` is not configured, add `asyncio_mode = auto` under `[tool.pytest.ini_options]` in `pyproject.toml`, or mark with `@pytest.mark.asyncio`. The repo already uses async tests — verify with `grep -r "asyncio_mode" pyproject.toml setup.cfg pytest.ini`.)

- [ ] **Step 3: Write the executor**

```python
# skyyrose/elite_studio/pipeline3d/executor.py
"""The orchestration heart: run a JobSpec stage-by-stage.

Spine: synchronous-within-stage. Each stage's adapter blocks until the provider
returns an artifact. Job-level concurrency lives at the worker layer, not here.

Guarantees:
  * stages run in canonical dependency order (ordered_stages)
  * a stage already in the store is skipped (idempotent resume)
  * RunBudget.ensure_within_budget() gates BEFORE each paid dispatch
  * each stage is wrapped in a telemetry span
  * ctx.last_artifact threads one stage's output into the next (chaining)
  * a stage exception -> FAILED PipelineResult with partial results persisted
"""

from __future__ import annotations

import time
from pathlib import Path

from skyyrose.elite_studio import telemetry
from skyyrose.elite_studio.budget import BudgetExceededError, RunBudget

from .adapters.base import StageContext
from .models import JobSpec, PipelineResult, StageResult, TaskStatus, ordered_stages
from .router import Router
from .store import StageStore


async def run_job(
    job: JobSpec,
    *,
    router: Router,
    store: StageStore,
    budget: RunBudget,
    run_id: str | None = None,
    input_hash: str | None = None,
) -> PipelineResult:
    """Execute all requested stages and return a PipelineResult."""
    run_id = run_id or telemetry.new_run_id()
    input_hash = input_hash or telemetry.hash_inputs(str(job.source_image), job.sku)

    ctx = StageContext(
        sku=job.sku,
        source_image=job.source_image,
        output_dir=Path(job.output_dir),
        params=dict(job.params),
    )
    results: list[StageResult] = []

    for stage in ordered_stages(job.stages):
        # Idempotent resume: skip stages already completed for this input.
        if store.has(input_hash, stage):
            cached = store.get(input_hash, stage)
            if cached is not None:
                ctx.last_artifact = cached.artifact
                results.append(cached)
                continue

        adapter = router.pick(stage)
        cost = adapter.estimate_cost(stage, ctx.params)

        # Budget gate raises BEFORE the paid call. Let it propagate — a job that
        # cannot afford a stage should halt loudly, not silently truncate.
        budget.ensure_within_budget(cost, stage.value)

        started = time.monotonic()
        try:
            with telemetry.stage(
                run_id=run_id,
                stage_name=stage.value,
                sku=job.sku,
                input_hash=input_hash,
            ) as span:
                span.set(provider=adapter.name)
                artifact = await adapter.run_stage(stage, ctx)
        except BudgetExceededError:
            raise
        except Exception as exc:  # noqa: BLE001 - stage isolation is intentional
            return PipelineResult(
                job_id=run_id,
                sku=job.sku,
                status=TaskStatus.FAILED,
                results=tuple(results),
                final_artifact=results[-1].artifact if results else None,
                total_cost_usd=round(sum(r.cost_usd for r in results), 4),
                error=f"{stage.value}: {exc}",
            )

        duration_ms = int((time.monotonic() - started) * 1000)
        budget.spend(cost, stage.value)
        result = StageResult(stage=stage, artifact=artifact, cost_usd=cost, duration_ms=duration_ms)
        store.put(input_hash, result)
        results.append(result)
        ctx.last_artifact = artifact

    return PipelineResult(
        job_id=run_id,
        sku=job.sku,
        status=TaskStatus.SUCCEEDED,
        results=tuple(results),
        final_artifact=results[-1].artifact if results else None,
        total_cost_usd=round(sum(r.cost_usd for r in results), 4),
    )


__all__ = ["run_job"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_executor.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/executor.py tests/elite_studio/pipeline3d/test_executor.py
git commit -m "feat(pipeline3d): staged executor with budget gate, idempotent resume, chaining"
```

---

### Task 7: LocalExportAdapter (EXPORT stage)

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/adapters/local_export.py`
- Test: `tests/elite_studio/pipeline3d/test_local_export.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_local_export.py
import pytest

from skyyrose.elite_studio.pipeline3d.adapters.base import StageContext
from skyyrose.elite_studio.pipeline3d.adapters.local_export import LocalExportAdapter
from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage


def test_supports_only_export():
    a = LocalExportAdapter()
    assert a.supports(Stage.EXPORT) is True
    assert a.supports(Stage.IMAGE_TO_3D) is False
    assert a.available() is True
    assert a.estimate_cost(Stage.EXPORT, {}) == 0.0


@pytest.mark.asyncio
async def test_export_copies_prior_artifact_to_canonical_path(tmp_path):
    src = tmp_path / "intermediate.glb"
    src.write_bytes(b"glTF-bytes")
    out = tmp_path / "out"
    ctx = StageContext(sku="br-001", source_image=tmp_path / "s.png", output_dir=out)
    ctx.last_artifact = Artifact(provider="tripo", task_id="t9", path=src, fmt="glb")

    a = LocalExportAdapter()
    art = await a.run_stage(Stage.EXPORT, ctx)

    dest = out / "br-001.glb"
    assert dest.is_file()
    assert dest.read_bytes() == b"glTF-bytes"
    assert art.path == dest
    assert art.provider == "local"
    assert art.task_id == "t9"  # carries provenance forward


@pytest.mark.asyncio
async def test_export_without_prior_path_raises(tmp_path):
    ctx = StageContext(sku="x", source_image=tmp_path / "s.png", output_dir=tmp_path / "o")
    a = LocalExportAdapter()
    with pytest.raises(ValueError):
        await a.run_stage(Stage.EXPORT, ctx)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_local_export.py -v`
Expected: FAIL — `ModuleNotFoundError: ...adapters.local_export`

- [ ] **Step 3: Write the adapter**

```python
# skyyrose/elite_studio/pipeline3d/adapters/local_export.py
"""EXPORT stage: materialize the final artifact to the canonical output path.

GLB export is provider-agnostic — it is just a copy of the last stage's local
file to ``<output_dir>/<sku>.<fmt>``. This keeps the router uniform (every stage
has an adapter) without a paid call. Non-GLB export (USDZ/FBX) is a later phase
and goes through a provider convert stage, not here.
"""

from __future__ import annotations

import shutil

from ..models import Artifact, Stage
from .base import StageContext


class LocalExportAdapter:
    """Copies the prior artifact to the canonical output location. Cost 0."""

    name = "local"

    def supports(self, stage: Stage) -> bool:
        return stage == Stage.EXPORT

    def available(self) -> bool:
        return True

    def estimate_cost(self, stage: Stage, params: dict) -> float:
        return 0.0

    async def run_stage(self, stage: Stage, ctx: StageContext) -> Artifact:
        prior = ctx.last_artifact
        if prior is None or prior.path is None:
            raise ValueError("export stage requires a prior artifact with a local path")
        ctx.output_dir.mkdir(parents=True, exist_ok=True)
        dest = ctx.output_dir / f"{ctx.sku}.{prior.fmt}"
        shutil.copyfile(prior.path, dest)
        return Artifact(
            provider="local",
            fmt=prior.fmt,
            task_id=prior.task_id,
            model_url=prior.model_url,
            path=dest,
            polycount=prior.polycount,
            bytes=dest.stat().st_size,
            meta={**prior.meta, "exported_from": str(prior.path)},
        )


__all__ = ["LocalExportAdapter"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_local_export.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/adapters/local_export.py tests/elite_studio/pipeline3d/test_local_export.py
git commit -m "feat(pipeline3d): local export adapter (GLB materialization)"
```

---

### Task 8: TripoAdapter (image-to-3D / texture / remesh via tripo3d SDK)

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/adapters/tripo.py`
- Test: `tests/elite_studio/pipeline3d/test_tripo_adapter.py`

The adapter wraps the `tripo3d` SDK. `run_stage` opens an `async with TripoClient(...)`,
submits the correct task per stage, `wait_for_task`s to completion, downloads the GLB
to a local path, and returns an `Artifact` carrying the provider `task_id` (for
same-provider chaining) and the local `path`. Tests mock `TripoClient` so **no paid
calls** happen.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_tripo_adapter.py
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from skyyrose.elite_studio.pipeline3d.adapters.base import StageContext
from skyyrose.elite_studio.pipeline3d.adapters.tripo import TripoAdapter
from skyyrose.elite_studio.pipeline3d.models import Artifact, Stage


def test_capabilities_and_availability():
    a = TripoAdapter(api_key="tsk_test")
    assert a.name == "tripo"
    assert a.supports(Stage.IMAGE_TO_3D) is True
    assert a.supports(Stage.TEXTURE) is True
    assert a.supports(Stage.REMESH) is True
    assert a.supports(Stage.EXPORT) is False
    assert a.available() is True
    assert TripoAdapter(api_key="").available() is False


def test_estimate_cost_per_stage():
    a = TripoAdapter(api_key="tsk_test")
    assert a.estimate_cost(Stage.IMAGE_TO_3D, {}) > 0
    assert a.estimate_cost(Stage.EXPORT, {}) == 0.0


def _mock_client(tmp_path):
    """Build a mock TripoClient usable as an async context manager."""
    client = MagicMock()
    client.image_to_model = AsyncMock(return_value="img-task-1")
    client.texture_model = AsyncMock(return_value="tex-task-1")
    client.smart_lowpoly = AsyncMock(return_value="remesh-task-1")
    task = MagicMock()
    task.status = "success"
    task.output = MagicMock(model="https://tripo/model.glb")
    client.wait_for_task = AsyncMock(return_value=task)
    downloaded = tmp_path / "dl.glb"
    downloaded.write_bytes(b"glb")
    client.download_task_models = AsyncMock(return_value={"model": str(downloaded)})
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm, client, downloaded


@pytest.mark.asyncio
async def test_image_to_3d_submits_and_downloads(tmp_path):
    cm, client, downloaded = _mock_client(tmp_path)
    ctx = StageContext(
        sku="br-001",
        source_image=tmp_path / "src.png",
        output_dir=tmp_path / "out",
    )
    a = TripoAdapter(api_key="tsk_test", output_dir=tmp_path / "out")
    with patch("skyyrose.elite_studio.pipeline3d.adapters.tripo.TripoClient", return_value=cm):
        art = await a.run_stage(Stage.IMAGE_TO_3D, ctx)
    client.image_to_model.assert_awaited_once()
    assert art.provider == "tripo"
    assert art.task_id == "img-task-1"
    assert art.model_url == "https://tripo/model.glb"
    assert art.path == downloaded


@pytest.mark.asyncio
async def test_texture_chains_prior_task_id(tmp_path):
    cm, client, _ = _mock_client(tmp_path)
    ctx = StageContext(sku="br-001", source_image=tmp_path / "s.png", output_dir=tmp_path / "out")
    ctx.last_artifact = Artifact(provider="tripo", task_id="img-task-1", path=tmp_path / "m.glb")
    a = TripoAdapter(api_key="tsk_test", output_dir=tmp_path / "out")
    with patch("skyyrose.elite_studio.pipeline3d.adapters.tripo.TripoClient", return_value=cm):
        art = await a.run_stage(Stage.TEXTURE, ctx)
    client.texture_model.assert_awaited_once_with(
        original_model_task_id="img-task-1", texture=True, pbr=True
    )
    assert art.task_id == "tex-task-1"


@pytest.mark.asyncio
async def test_remesh_uses_smart_lowpoly_with_face_limit(tmp_path):
    cm, client, _ = _mock_client(tmp_path)
    ctx = StageContext(
        sku="br-001",
        source_image=tmp_path / "s.png",
        output_dir=tmp_path / "out",
        params={"target_polycount": 12000},
    )
    ctx.last_artifact = Artifact(provider="tripo", task_id="tex-task-1", path=tmp_path / "m.glb")
    a = TripoAdapter(api_key="tsk_test", output_dir=tmp_path / "out")
    with patch("skyyrose.elite_studio.pipeline3d.adapters.tripo.TripoClient", return_value=cm):
        art = await a.run_stage(Stage.REMESH, ctx)
    client.smart_lowpoly.assert_awaited_once_with(
        original_model_task_id="tex-task-1", face_limit=12000, quad=False
    )
    assert art.task_id == "remesh-task-1"


@pytest.mark.asyncio
async def test_texture_without_prior_task_id_raises(tmp_path):
    ctx = StageContext(sku="x", source_image=tmp_path / "s.png", output_dir=tmp_path / "out")
    a = TripoAdapter(api_key="tsk_test", output_dir=tmp_path / "out")
    with pytest.raises(ValueError):
        await a.run_stage(Stage.TEXTURE, ctx)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_tripo_adapter.py -v`
Expected: FAIL — `ModuleNotFoundError: ...adapters.tripo`

- [ ] **Step 3: Write the adapter**

```python
# skyyrose/elite_studio/pipeline3d/adapters/tripo.py
"""Tripo adapter — image-to-3D, texture, remesh via the tripo3d SDK 0.4.1.

Stage -> SDK call mapping (all return a task_id, then wait_for_task + download):
  IMAGE_TO_3D -> client.image_to_model(image=<src>, texture=False, pbr=False)  (base mesh)
  TEXTURE     -> client.texture_model(original_model_task_id=<prior>, texture=True, pbr=True)
  REMESH      -> client.smart_lowpoly(original_model_task_id=<prior>, face_limit=N, quad=False)

Note: convert_model does NOT accept 'GLB' (GLB is the native output); it is for
USDZ/FBX/etc. and is deferred to a later phase. GLB remesh uses smart_lowpoly.

Same-provider chaining uses the prior stage's Tripo task_id (carried on
ctx.last_artifact.task_id). The artifact is also downloaded to a local path each
stage so a stale 24h artifact URL never breaks a resume.
"""

from __future__ import annotations

import os
from pathlib import Path

from tripo3d import TripoClient

from ..models import Artifact, Stage
from .base import StageContext

# Rough USD estimates (provider credits -> USD). These are ESTIMATES sourced from
# provider docs; tune via env overrides. See spec §10 (Risks).
_DEFAULT_COST = {
    Stage.IMAGE_TO_3D: float(os.getenv("PIPELINE3D_TRIPO_IMAGE_USD", "0.40")),
    Stage.TEXTURE: float(os.getenv("PIPELINE3D_TRIPO_TEXTURE_USD", "0.20")),
    Stage.REMESH: float(os.getenv("PIPELINE3D_TRIPO_REMESH_USD", "0.15")),
}
_SUPPORTED = (Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH)


class TripoAdapter:
    """Wraps the tripo3d SDK behind the Adapter port."""

    name = "tripo"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        output_dir: str | Path = Path("renders/3d/_tripo"),
        timeout: float = 300.0,
        default_polycount: int = 30000,
    ) -> None:
        self._api_key = (
            api_key
            if api_key is not None
            else (os.getenv("TRIPO_API_KEY") or os.getenv("TRIPO3D_API_KEY") or "")
        )
        self._output_dir = Path(output_dir)
        self._timeout = timeout
        self._default_polycount = default_polycount

    def supports(self, stage: Stage) -> bool:
        return stage in _SUPPORTED

    def available(self) -> bool:
        return bool(self._api_key)

    def estimate_cost(self, stage: Stage, params: dict) -> float:
        return _DEFAULT_COST.get(stage, 0.0)

    async def run_stage(self, stage: Stage, ctx: StageContext) -> Artifact:
        if stage not in _SUPPORTED:
            raise ValueError(f"tripo adapter does not support stage={stage.value!r}")
        if stage in (Stage.TEXTURE, Stage.REMESH):
            prior = ctx.last_artifact
            if prior is None or prior.task_id is None:
                raise ValueError(f"{stage.value} requires a prior Tripo task_id to chain")

        self._output_dir.mkdir(parents=True, exist_ok=True)

        async with TripoClient(api_key=self._api_key) as client:
            if stage == Stage.IMAGE_TO_3D:
                task_id = await client.image_to_model(
                    image=str(ctx.source_image), texture=False, pbr=False
                )
            elif stage == Stage.TEXTURE:
                task_id = await client.texture_model(
                    original_model_task_id=ctx.last_artifact.task_id, texture=True, pbr=True
                )
            else:  # Stage.REMESH
                face_limit = int(ctx.params.get("target_polycount", self._default_polycount))
                task_id = await client.smart_lowpoly(
                    original_model_task_id=ctx.last_artifact.task_id,
                    face_limit=face_limit,
                    quad=False,
                )

            task = await client.wait_for_task(task_id, timeout=self._timeout)
            downloaded = await client.download_task_models(task, str(self._output_dir))
            model_path = downloaded.get("model") or next(iter(downloaded.values()), None)
            output = getattr(task, "output", None)
            model_url = getattr(output, "model", None) if output is not None else None

        path = Path(model_path) if model_path else None
        return Artifact(
            provider="tripo",
            fmt="glb",
            task_id=task_id,
            model_url=model_url,
            path=path,
            bytes=path.stat().st_size if path and path.is_file() else None,
            meta={"tripo_status": str(getattr(task, "status", "")), "stage": stage.value},
        )


__all__ = ["TripoAdapter"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_tripo_adapter.py -v`
Expected: PASS (6 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/adapters/tripo.py tests/elite_studio/pipeline3d/test_tripo_adapter.py
git commit -m "feat(pipeline3d): Tripo adapter (image-to-3d/texture/remesh via SDK)"
```

---

### Task 9: Preflight (source resolution + guard)

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/preflight.py`
- Test: `tests/elite_studio/pipeline3d/test_preflight.py`

`resolve_source` accepts an explicit image path (highest priority) or resolves a
SKU to its canonical flatlay source under `assets/product-source/<sku>__*/flatlay/`
(prefers a file whose name starts with `front`). Raises `PreflightError` if no
source exists — a paid job must never dispatch with a missing/ambiguous source.

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_preflight.py
import pytest

from skyyrose.elite_studio.pipeline3d.preflight import PreflightError, resolve_source


def test_explicit_image_path_wins(tmp_path):
    img = tmp_path / "explicit.png"
    img.write_bytes(b"x")
    got = resolve_source(sku="br-001", image=img, source_root=tmp_path / "assets")
    assert got == img


def test_explicit_missing_path_raises(tmp_path):
    with pytest.raises(PreflightError):
        resolve_source(sku="br-001", image=tmp_path / "nope.png", source_root=tmp_path)


def test_sku_resolves_front_flatlay(tmp_path):
    folder = tmp_path / "br-001__black-rose-crewneck" / "flatlay"
    folder.mkdir(parents=True)
    (folder / "back.png").write_bytes(b"b")
    front = folder / "front.png"
    front.write_bytes(b"f")
    got = resolve_source(sku="br-001", image=None, source_root=tmp_path)
    assert got == front


def test_sku_without_front_takes_first_sorted(tmp_path):
    folder = tmp_path / "sg-001__sig-tee" / "flatlay"
    folder.mkdir(parents=True)
    (folder / "b.png").write_bytes(b"b")
    (folder / "a.png").write_bytes(b"a")
    got = resolve_source(sku="sg-001", image=None, source_root=tmp_path)
    assert got.name == "a.png"


def test_unknown_sku_raises(tmp_path):
    with pytest.raises(PreflightError):
        resolve_source(sku="zz-999", image=None, source_root=tmp_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_preflight.py -v`
Expected: FAIL — `ModuleNotFoundError: ...preflight`

- [ ] **Step 3: Write preflight**

```python
# skyyrose/elite_studio/pipeline3d/preflight.py
"""Resolve a job's source image and guard against missing/ambiguous sources.

A paid 3D job must never dispatch without a confirmed canonical source. Priority:
  1. An explicit image path (must exist).
  2. SKU -> canonical flatlay: assets/product-source/<sku>__*/flatlay/
     preferring a file whose name starts with 'front', else first sorted image.
"""

from __future__ import annotations

from pathlib import Path

_DEFAULT_SOURCE_ROOT = Path("assets/product-source")
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


class PreflightError(RuntimeError):
    """The source image could not be resolved — do not dispatch."""


def resolve_source(
    *,
    sku: str,
    image: str | Path | None = None,
    source_root: str | Path | None = None,
) -> Path:
    """Return the resolved source image path or raise PreflightError."""
    if image is not None:
        p = Path(image)
        if not p.is_file():
            raise PreflightError(f"explicit image not found: {p}")
        return p

    root = Path(source_root) if source_root is not None else _DEFAULT_SOURCE_ROOT
    matches = sorted(root.glob(f"{sku}__*"))
    if not matches:
        raise PreflightError(f"no canonical source folder for sku={sku!r} under {root}")

    for folder in matches:
        flatlay = folder / "flatlay"
        if not flatlay.is_dir():
            continue
        images = sorted(p for p in flatlay.iterdir() if p.suffix.lower() in _IMAGE_EXTS)
        if not images:
            continue
        for img in images:
            if img.name.lower().startswith("front"):
                return img
        return images[0]

    raise PreflightError(f"no flatlay image found for sku={sku!r} under {root}")


__all__ = ["resolve_source", "PreflightError"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_preflight.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/preflight.py tests/elite_studio/pipeline3d/test_preflight.py
git commit -m "feat(pipeline3d): preflight source resolution + guard"
```

---

### Task 10: CLI (`gen3d` — wires preflight → estimate → STOP-AND-SHOW → run_job)

**Files:**
- Create: `skyyrose/elite_studio/pipeline3d/cli.py`
- Create: `skyyrose/elite_studio/pipeline3d/__main__.py`
- Test: `tests/elite_studio/pipeline3d/test_cli.py`

The CLI builds the router (Tripo + LocalExport), resolves the source, computes the
ONE whole-job estimate, prints a STOP-AND-SHOW banner (gated by `--go` /
`SKYYROSE_AUTO_CONFIRM` / TTY), then runs the job. Default is dry-run (estimate +
manifest only, no dispatch).

- [ ] **Step 1: Write the failing test**

```python
# tests/elite_studio/pipeline3d/test_cli.py
from pathlib import Path

import pytest

from skyyrose.elite_studio.pipeline3d import cli
from skyyrose.elite_studio.pipeline3d.models import Stage


def test_parse_stages_default_and_explicit():
    assert cli.parse_stages("image-to-3d,texture,remesh,export") == (
        Stage.IMAGE_TO_3D,
        Stage.TEXTURE,
        Stage.REMESH,
        Stage.EXPORT,
    )
    assert cli.parse_stages("image-to-3d,export") == (Stage.IMAGE_TO_3D, Stage.EXPORT)


def test_parse_stages_rejects_unknown():
    with pytest.raises(SystemExit):
        cli.parse_stages("image-to-3d,fly-to-moon")


def test_build_router_has_tripo_and_local():
    router = cli.build_router(api_key="tsk_test", output_dir=Path("/tmp/x"))
    names = {a.name for a in router._adapters}
    assert {"tripo", "local"} <= names


@pytest.mark.asyncio
async def test_dry_run_estimates_without_dispatch(tmp_path, capsys):
    img = tmp_path / "src.png"
    img.write_bytes(b"x")
    rc = await cli.run(
        [
            "--sku",
            "br-001",
            "--image",
            str(img),
            "--stages",
            "image-to-3d,texture,remesh,export",
            "--output-dir",
            str(tmp_path / "out"),
            "--api-key",
            "tsk_test",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "DRY RUN" in out
    assert "total" in out.lower()
    # nothing written to output dir on a dry run
    assert not (tmp_path / "out" / "br-001.glb").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/elite_studio/pipeline3d/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError: ...cli`

- [ ] **Step 3: Write the CLI**

```python
# skyyrose/elite_studio/pipeline3d/cli.py
"""CLI for the 3D pipeline orchestrator (Phase 1 driver).

Usage:
    python -m skyyrose.elite_studio.pipeline3d gen3d \
        --sku br-001 --stages image-to-3d,texture,remesh,export --format glb [--go]

Default is dry-run: resolve source + compute the ONE whole-job estimate + print
the STOP-AND-SHOW banner, but do NOT dispatch. Pass --go to dispatch paid stages
(still gated by the confirmation banner unless SKYYROSE_AUTO_CONFIRM=1 or no TTY).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from skyyrose.elite_studio.budget import RunBudget

from .adapters.local_export import LocalExportAdapter
from .adapters.tripo import TripoAdapter
from .estimator import estimate
from .executor import run_job
from .models import JobSpec, Stage
from .preflight import PreflightError, resolve_source
from .router import Router
from .store import StageStore

_STAGE_ALIASES = {
    "image-to-3d": Stage.IMAGE_TO_3D,
    "image_to_3d": Stage.IMAGE_TO_3D,
    "texture": Stage.TEXTURE,
    "remesh": Stage.REMESH,
    "export": Stage.EXPORT,
}
_DEFAULT_PRIORITY = ["tripo", "local"]


def parse_stages(value: str) -> tuple[Stage, ...]:
    """Parse a comma-separated stage list into ordered Stage values."""
    out: list[Stage] = []
    for raw in value.split(","):
        token = raw.strip().lower()
        if not token:
            continue
        if token not in _STAGE_ALIASES:
            raise SystemExit(f"unknown stage: {token!r} (valid: {', '.join(_STAGE_ALIASES)})")
        out.append(_STAGE_ALIASES[token])
    if not out:
        raise SystemExit("no stages requested")
    return tuple(out)


def build_router(*, api_key: str | None, output_dir: Path) -> Router:
    """Build the Phase 1 router: Tripo + local export."""
    adapters = [
        TripoAdapter(api_key=api_key, output_dir=output_dir / "_tripo"),
        LocalExportAdapter(),
    ]
    return Router(adapters, priority=_DEFAULT_PRIORITY)


def _confirm(*, sku: str, source: Path, est: dict, interactive: bool) -> bool:
    """STOP-AND-SHOW gate. Returns True iff allowed to dispatch."""
    banner = (
        "\nSTOP — Confirm before proceeding:\n\n"
        f"  Action : 3D pipeline (paid)\n"
        f"  SKU    : {sku}\n"
        f"  Source : {source}\n"
        f"  Stages : {', '.join(f'{k}=${v:.2f}' for k, v in est['by_stage'].items())}\n"
        f"  Total  : ~${est['total_usd']:.2f}\n\n"
        "Proceed? [y/N] "
    )
    if not interactive:
        return True
    if os.getenv("SKYYROSE_AUTO_CONFIRM") == "1" or not sys.stdin.isatty():
        return True
    sys.stdout.write(banner)
    sys.stdout.flush()
    try:
        return input().strip().lower() in {"y", "yes"}
    except EOFError:
        return False


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gen3d", description="Unified 3D pipeline (Phase 1: Tripo).")
    p.add_argument("--sku", required=True)
    p.add_argument("--image", default=None, help="Explicit source image path (overrides SKU lookup)")
    p.add_argument("--stages", default="image-to-3d,texture,remesh,export")
    p.add_argument("--format", default="glb", choices=["glb"])
    p.add_argument("--output-dir", default="renders/3d")
    p.add_argument("--source-root", default=None, help="Override canonical source root")
    p.add_argument("--budget", type=float, default=5.0, help="Per-job USD ceiling")
    p.add_argument("--api-key", default=None, help="Tripo API key (else env TRIPO_API_KEY)")
    p.add_argument("--go", action="store_true", help="Dispatch paid stages (default: dry-run)")
    return p


async def run(argv: list[str]) -> int:
    """Programmatic entry point. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    stages = parse_stages(args.stages)
    output_dir = Path(args.output_dir)

    try:
        source = resolve_source(sku=args.sku, image=args.image, source_root=args.source_root)
    except PreflightError as exc:
        sys.stderr.write(f"preflight failed: {exc}\n")
        return 2

    router = build_router(api_key=args.api_key, output_dir=output_dir)
    job = JobSpec(
        sku=args.sku,
        source_image=source,
        stages=stages,
        formats=(args.format,),
        budget_ceiling_usd=args.budget,
        output_dir=output_dir,
    )
    est = estimate(job, router)

    if not args.go:
        sys.stdout.write(
            f"\nDRY RUN — no dispatch.\n  SKU: {args.sku}\n  Source: {source}\n"
            f"  Stages: {', '.join(f'{k}=${v:.2f}' for k, v in est['by_stage'].items())}\n"
            f"  Estimated total: ~${est['total_usd']:.2f}\n"
            f"  (pass --go to dispatch)\n"
        )
        return 0

    if not _confirm(sku=args.sku, source=source, est=est, interactive=True):
        sys.stdout.write("aborted by user\n")
        return 1

    budget = RunBudget(ceiling_usd=args.budget)
    store = StageStore(output_dir / "_store")
    result = await run_job(job, router=router, store=store, budget=budget)
    sys.stdout.write(
        f"\nstatus: {result.status.value}\n"
        f"final: {result.final_artifact.path if result.final_artifact else None}\n"
        f"spent: ${result.total_cost_usd:.2f}\n"
    )
    if result.error:
        sys.stderr.write(f"error: {result.error}\n")
    return 0 if result.status.value == "succeeded" else 1


def main() -> int:
    return asyncio.run(run(sys.argv[1:]))


__all__ = ["run", "main", "parse_stages", "build_router"]
```

```python
# skyyrose/elite_studio/pipeline3d/__main__.py
"""Module entry point: ``python -m skyyrose.elite_studio.pipeline3d ...``."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/elite_studio/pipeline3d/test_cli.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Format + commit**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
isort skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && ruff check --fix skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d && black skyyrose/elite_studio/pipeline3d tests/elite_studio/pipeline3d
git add skyyrose/elite_studio/pipeline3d/cli.py skyyrose/elite_studio/pipeline3d/__main__.py tests/elite_studio/pipeline3d/test_cli.py
git commit -m "feat(pipeline3d): gen3d CLI (preflight + estimate + STOP-AND-SHOW + run)"
```

---

### Task 11: Full-package verification + dry-run smoke + docs

**Files:**
- Modify: `skyyrose/elite_studio/CLAUDE.md` (add pipeline3d learnings)
- Create: `skyyrose/elite_studio/pipeline3d/README.md`
- Test: full suite + coverage

- [ ] **Step 1: Run the full package test suite with coverage**

Run:
```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
pytest tests/elite_studio/pipeline3d/ -v --cov=skyyrose/elite_studio/pipeline3d --cov-report=term-missing
```
Expected: all tests PASS; coverage ≥ 85% on the new package. If any module is < 85%, add the missing-branch test before proceeding.

- [ ] **Step 2: Lint + type sanity on the new package**

Run:
```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
ruff check skyyrose/elite_studio/pipeline3d && black --check skyyrose/elite_studio/pipeline3d && isort --check-only skyyrose/elite_studio/pipeline3d
```
Expected: clean (no diffs, no lint errors).

- [ ] **Step 3: Real dry-run smoke (no paid call)**

Run:
```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
python -m skyyrose.elite_studio.pipeline3d --sku br-001 --image docs/superpowers/specs/2026-06-02-pipeline3d-orchestrator-design.html --stages image-to-3d,texture,remesh,export
```
Expected: prints `DRY RUN — no dispatch` with a per-stage breakdown and `Estimated total: ~$0.75`, exit 0. (Any readable file works as the `--image` here — the dry run never reads its bytes; it only proves wiring + estimate. No GLB is written.)

- [ ] **Step 4: Write the package README**

```markdown
# pipeline3d — Unified 3D Pipeline Orchestrator (Phase 1)

Provider-agnostic staged 3D pipeline cloning the Tripo3D/Meshy workflow shape:
`image-to-3D → texture → remesh → export-GLB`. Phase 1 ships the Tripo vertical
slice driven by a CLI.

## Quick start

```bash
# Dry run (estimate only, no dispatch):
python -m skyyrose.elite_studio.pipeline3d --sku br-001 \
    --stages image-to-3d,texture,remesh,export

# Paid dispatch (STOP-AND-SHOW gate; needs TRIPO_API_KEY):
python -m skyyrose.elite_studio.pipeline3d --sku br-001 \
    --stages image-to-3d,texture,remesh,export --go
```

## Architecture

| Module | Role |
|--------|------|
| `models` | immutable data types; `Artifact` is the chaining handle (task_id + path) |
| `router` | picks an adapter per stage by capability/priority/availability + fallback |
| `executor` | runs stages in order; budget gate; telemetry; idempotent resume; chaining |
| `estimator` | one whole-job cost estimate, shown before dispatch |
| `store` | file-based stage-level idempotency (resume skips completed stages) |
| `adapters/tripo` | image-to-3D / texture / remesh via the tripo3d SDK |
| `adapters/local_export` | EXPORT stage — copies final GLB to `<output>/<sku>.glb` |
| `preflight` | resolves the canonical source image + guards against missing source |

Execution spine: **synchronous-within-stage** (the adapter polls to completion).
Cross-provider chaining: same provider → pass `task_id`; different provider →
hand off the downloadable `model_url`/path.

## Roadmap

- **Phase 2:** Meshy + TRELLIS adapters, router fallback across providers, batch.
- **Phase 3:** REST API + Redis async worker, inbound webhook + HMAC, outbound events.

See `docs/superpowers/specs/2026-06-02-pipeline3d-orchestrator-design.html`.
```

- [ ] **Step 5: Add learnings to the elite_studio CLAUDE.md**

Append this block to `skyyrose/elite_studio/CLAUDE.md` (before the trailing `<claude-mem-context>` block if present, else at end):

```markdown
## pipeline3d — Unified 3D Pipeline Orchestrator

- `skyyrose/elite_studio/pipeline3d/` is the provider-agnostic staged 3D pipeline (Tripo/Meshy workflow clone). Stages: image-to-3D → texture → remesh → export-GLB.
- **Execution spine is synchronous-within-stage** — the adapter blocks via `tripo3d` SDK `wait_for_task`. No event-driven DAG advancement. Job concurrency is a worker-layer concern (Phase 3).
- **Chaining rule:** `Artifact` carries both a provider `task_id` (same-provider chaining) and a local `path`/`model_url` (cross-provider handoff). `router.pick(stage, exclude=...)` enables fallback.
- **Remesh-to-GLB uses `smart_lowpoly`, NOT `convert_model`** — the tripo3d SDK's `convert_model` format Literal excludes GLB (GLB is native output). `convert_model` is reserved for deferred USDZ/FBX export.
- **Cost gate:** whole-job estimate computed once (`estimator.estimate`), shown via STOP-AND-SHOW before dispatch. Reuses `RunBudget.ensure_within_budget`/`spend`. Paid dispatch requires `--go`; never auto-dispatches.
- **Idempotency:** `StageStore` (file-based) persists each stage result keyed by `(input_hash, stage)`; a resumed job skips completed stages so a crash at remesh does not re-bill image-to-3D + texture.
- Entry: `python -m skyyrose.elite_studio.pipeline3d --sku <sku> --stages ... [--go]`. Dry-run by default.
```

- [ ] **Step 6: Commit docs + final verification**

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/pipeline3d-orchestrator
git add skyyrose/elite_studio/pipeline3d/README.md skyyrose/elite_studio/CLAUDE.md
git commit -m "docs(pipeline3d): README + elite_studio learnings for Phase 1"
pytest tests/elite_studio/pipeline3d/ -q
```
Expected: full suite green.

---

## Self-review checklist (run before execution)

- **Spec coverage:** §2 layout → Tasks 1–10; §3 spine + chaining → Task 6 + Task 8; §4 router → Task 4; §5 reuse (budget/telemetry) → Task 6; §6 CLI surface → Task 10; §7 money/idempotency → Task 5 (store) + Task 6 (budget gate) + Task 10 (estimate+confirm); §9 testing → every task TDD + Task 11. REST/webhook (§6 Phase 3) intentionally NOT in this plan.
- **Type consistency:** `Stage`, `Artifact`, `StageContext`, `StageResult`, `JobSpec`, `PipelineResult`, `Router`, `StageStore`, `run_job`, `estimate`, `resolve_source`, `TripoAdapter`, `LocalExportAdapter` — names identical across all tasks. `run_stage(stage, ctx)` signature stable. `Artifact` field set fixed in Task 1, consumed unchanged in 3/6/7/8.
- **Idempotency key:** `telemetry.hash_inputs(str(source_image), sku)` in executor matches `StageStore` `has/get/put(input_hash, ...)` interface.
- **No placeholders:** every code step is complete and runnable.
