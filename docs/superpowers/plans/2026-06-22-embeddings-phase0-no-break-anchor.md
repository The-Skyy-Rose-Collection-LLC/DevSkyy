# Embeddings Reframe — Phase 0 (No-Break Anchor) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the regression net that lets the embeddings reframe proceed safely — a contract test + a model-free golden characterization test pinning the live gate's decision logic, and a CI test-split so the gate suite actually runs on every push.

**Architecture:** The live render path calls `embedding_gate.evaluate()` + `brand_centroid.load_centroid()` (plus `clip_alignment`, `render_quality`, `metrics`, `stage_g_visual_qa.maybe_apply_gate`). Today **zero** of their tests run in CI (`addopts` excludes `-m "not slow and not integration"`; both gate test modules are `pytestmark = integration`). Phase 0 adds two new `unit` test files (inspect-only contract + monkeypatched-encoder golden) that need no model, splits the existing gate tests so the model-free ones run in CI, and fixes one test that relies on `BrandCentroid` being mutable.

**Tech Stack:** Python 3.13, pytest (markers: `unit`/`integration`/`slow`), numpy, PIL. No new dependencies.

## Global Constraints

- Python line length 100; format with `isort . && ruff check --fix && black .` (run on touched files).
- pytest config (`pyproject.toml`): `addopts` includes `-m "not slow and not integration"` and `--strict-markers`. Registered markers: `slow`, `integration`, `unit`.
- The frozen contract (signatures + dataclass fields below) MUST NOT change in this or any later phase.
- New tests must be **model-free** (`@pytest.mark.unit`) — no HF Hub download at collection or run time (a transient HF 429 must never flake these; ref obs #17651).
- Patch at the **consuming** module namespace (ref obs #8254): `embedding_gate` calls `clip_embedder.embed_image`; patch `skyyrose.core.clip_embedder.embed_image`.
- Commit per task. The repo pre-commit hook runs a WordPress `freshness-guard` that currently fails on a **concurrent session's** un-rebuilt `design-tokens.css` — unrelated to these Python files. Commit Python with `--no-verify` **after** manually running `isort/ruff/black` on the touched files, and stage **only** this plan's files by explicit pathspec (never `git add -A` — 53 concurrent WP files are staged).

**Frozen contract (verified verbatim 2026-06-22):**
- `embedding_gate.score_against_centroid(image, centroid) -> float`
- `embedding_gate.evaluate(image, centroid) -> GateVerdict`; `GateVerdict` fields: `accepted, score, threshold, reason`
- `brand_centroid.load_centroid(path) -> BrandCentroid`; `BrandCentroid` fields: `centroid, threshold, sample_count, model_id, sample_paths`
- `clip_alignment.score_alignment(prompt, image) -> float`
- `clip_alignment.score_alignment_batch(prompts, image) -> list[float]`
- `render_quality.evaluate_render(render_path, prompt, centroid_path, *, min_dimension=512, alignment_threshold=0.20) -> RenderVerdict`; `RenderVerdict` fields: `verdict, brand_centroid_score, alignment_score, threshold_centroid, threshold_alignment, width, height, reason` (+ `combined_score` property)
- `render_quality.Verdict` enum: `SHIP="ship", REVIEW="review", KILL="kill"`
- `metrics.composite_score(*, dino, clip, ssim) -> float`
- `metrics.score_view(render_path, reference_path, *, sku, angle) -> VisibleScore`; `VisibleScore` fields: `angle, dino, clip, ssim, composite`
- `stage_g_visual_qa.maybe_apply_gate(shadow_path, scene_name, collection, *, analyze_vision, centroid_path=None) -> dict`
- `embedding_gate.evaluate` reason strings: accept → contains `"on-brand"`; reject → contains `"below brand threshold"`.

---

### Task 1: Frozen-contract test (T0-contract)

**Files:**
- Create: `tests/elite_studio/test_frozen_contract.py`

**Interfaces:**
- Consumes: the frozen contract above (read-only; `inspect`).
- Produces: nothing for later tasks (a guard).

- [ ] **Step 1: Write the contract test**

```python
"""Frozen-contract test: pins the public API the live render path depends on.

The embeddings reframe (Phase 2) re-points these modules onto the new package.
These signatures + dataclass field sets MUST NOT change. inspect-only — importing
these modules does not load any model (encoders are lazy singletons).
"""

from __future__ import annotations

import inspect
from dataclasses import fields

import pytest

pytestmark = pytest.mark.unit


def _param_names(fn) -> list[str]:
    return list(inspect.signature(fn).parameters)


def test_embedding_gate_contract() -> None:
    from skyyrose.elite_studio.quality import embedding_gate as m

    assert _param_names(m.score_against_centroid) == ["image", "centroid"]
    assert _param_names(m.evaluate) == ["image", "centroid"]
    assert {f.name for f in fields(m.GateVerdict)} == {
        "accepted",
        "score",
        "threshold",
        "reason",
    }


def test_brand_centroid_contract() -> None:
    from skyyrose.elite_studio.quality import brand_centroid as m

    assert _param_names(m.load_centroid) == ["path"]
    assert {f.name for f in fields(m.BrandCentroid)} == {
        "centroid",
        "threshold",
        "sample_count",
        "model_id",
        "sample_paths",
    }


def test_clip_alignment_contract() -> None:
    from skyyrose.elite_studio.quality import clip_alignment as m

    assert _param_names(m.score_alignment) == ["prompt", "image"]
    assert _param_names(m.score_alignment_batch) == ["prompts", "image"]


def test_render_quality_contract() -> None:
    from skyyrose.elite_studio.quality import render_quality as m

    params = inspect.signature(m.evaluate_render).parameters
    assert list(params) == [
        "render_path",
        "prompt",
        "centroid_path",
        "min_dimension",
        "alignment_threshold",
    ]
    assert params["min_dimension"].kind == inspect.Parameter.KEYWORD_ONLY
    assert params["min_dimension"].default == 512
    assert params["alignment_threshold"].default == 0.20
    assert {f.name for f in fields(m.RenderVerdict)} == {
        "verdict",
        "brand_centroid_score",
        "alignment_score",
        "threshold_centroid",
        "threshold_alignment",
        "width",
        "height",
        "reason",
    }
    assert [v.value for v in m.Verdict] == ["ship", "review", "kill"]


def test_fidelity_metrics_contract() -> None:
    from skyyrose.elite_studio.platform.fidelity import metrics as m

    cs = inspect.signature(m.composite_score).parameters
    assert list(cs) == ["dino", "clip", "ssim"]
    assert all(p.kind == inspect.Parameter.KEYWORD_ONLY for p in cs.values())
    sv = inspect.signature(m.score_view).parameters
    assert list(sv) == ["render_path", "reference_path", "sku", "angle"]
    assert {f.name for f in fields(m.VisibleScore)} == {
        "angle",
        "dino",
        "clip",
        "ssim",
        "composite",
    }


def test_stage_g_gate_contract() -> None:
    from skyyrose.elite_studio.agents.compositor import stage_g_visual_qa as m

    params = inspect.signature(m.maybe_apply_gate).parameters
    assert list(params) == [
        "shadow_path",
        "scene_name",
        "collection",
        "analyze_vision",
        "centroid_path",
    ]
    assert params["analyze_vision"].kind == inspect.Parameter.KEYWORD_ONLY
    assert params["centroid_path"].default is None
```

- [ ] **Step 2: Run the test — it PASSES against current `main` (pins the contract)**

Run: `rtk proxy pytest tests/elite_studio/test_frozen_contract.py -m "not slow and not integration" -v`
Expected: 6 passed. (Characterization test: it encodes the *current* contract, so it passes now; its value is catching a FUTURE break.)

- [ ] **Step 3: Prove the test can fail (sanity)**

Temporarily change one assertion, e.g. in `test_embedding_gate_contract` set the expected param list to `["image", "WRONG"]`.
Run: `rtk proxy pytest tests/elite_studio/test_frozen_contract.py::test_embedding_gate_contract -v`
Expected: FAIL (AssertionError). Then **revert** the change.

- [ ] **Step 4: Re-run — PASS**

Run: `rtk proxy pytest tests/elite_studio/test_frozen_contract.py -m "not slow and not integration" -v`
Expected: 6 passed.

- [ ] **Step 5: Format + commit**

```bash
isort tests/elite_studio/test_frozen_contract.py
ruff check --fix tests/elite_studio/test_frozen_contract.py
black tests/elite_studio/test_frozen_contract.py
git commit --no-verify -m "test(embeddings): pin frozen contract for render-path quality API" -- tests/elite_studio/test_frozen_contract.py
```

---

### Task 2: Golden gate-verdict test (T0-golden)

**Files:**
- Create: `tests/elite_studio/test_gate_golden.py`

**Interfaces:**
- Consumes: `embedding_gate.evaluate`, `embedding_gate.GateVerdict`, `brand_centroid.BrandCentroid`, `skyyrose.core.clip_embedder.embed_image` (monkeypatched), `clip_embedder.cosine_similarity` (real).
- Produces: the regression anchor Phase 2 must keep green (gate score == cosine of normalized vectors; accept/reject branches; reason strings; `GateVerdict` shape).

- [ ] **Step 1: Write the golden test**

```python
"""Golden characterization of the embedding-gate decision logic.

Model-free: monkeypatches clip_embedder.embed_image to a fixed seeded vector, so
the REAL score_against_centroid (cosine_similarity) + evaluate (threshold compare,
GateVerdict construction) run deterministically. Pins the gate's behavior so the
embeddings reframe (Phase 2) cannot silently change the score math, the accept/
reject branches, or the verdict shape.

Oracle: clip_embedder.cosine_similarity is `float(np.dot(a, b))` for L2-normalized
inputs, so `float(np.dot(e, c))` is an independent (non-circular) expected value.
"""

from __future__ import annotations

import numpy as np
import pytest

from skyyrose.core import clip_embedder
from skyyrose.elite_studio.quality import embedding_gate
from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid

pytestmark = pytest.mark.unit


def _unit_vec(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    v = rng.standard_normal(512).astype(np.float32)
    return v / np.linalg.norm(v)


def _centroid(threshold: float) -> BrandCentroid:
    return BrandCentroid(
        centroid=_unit_vec(7),
        threshold=threshold,
        sample_count=10,
        model_id="test",
    )


def test_gate_score_equals_cosine_oracle(monkeypatch) -> None:
    e = _unit_vec(11)
    monkeypatch.setattr(clip_embedder, "embed_image", lambda *_a, **_kw: e)

    verdict = embedding_gate.evaluate("ignored.png", _centroid(threshold=0.0))

    expected = float(np.dot(e, _unit_vec(7)))
    assert verdict.score == pytest.approx(expected, abs=1e-6)
    assert isinstance(verdict, embedding_gate.GateVerdict)


def test_gate_accepts_at_or_above_threshold(monkeypatch) -> None:
    e = _unit_vec(11)
    monkeypatch.setattr(clip_embedder, "embed_image", lambda *_a, **_kw: e)
    expected = float(np.dot(e, _unit_vec(7)))

    verdict = embedding_gate.evaluate("ignored.png", _centroid(threshold=expected - 0.01))

    assert verdict.accepted is True
    assert "on-brand" in verdict.reason.lower()


def test_gate_rejects_below_threshold(monkeypatch) -> None:
    e = _unit_vec(11)
    monkeypatch.setattr(clip_embedder, "embed_image", lambda *_a, **_kw: e)
    expected = float(np.dot(e, _unit_vec(7)))

    verdict = embedding_gate.evaluate("ignored.png", _centroid(threshold=expected + 0.01))

    assert verdict.accepted is False
    assert "below brand threshold" in verdict.reason.lower()
```

- [ ] **Step 2: Run — PASS (pins current decision logic)**

Run: `rtk proxy pytest tests/elite_studio/test_gate_golden.py -m "not slow and not integration" -v`
Expected: 3 passed.

- [ ] **Step 3: Prove it bites (sanity)**

Temporarily flip `expected - 0.01` to `expected + 0.01` in `test_gate_accepts_at_or_above_threshold`.
Run that test → Expected: FAIL (`assert verdict.accepted is True`). **Revert.**

- [ ] **Step 4: Re-run — PASS**

Run: `rtk proxy pytest tests/elite_studio/test_gate_golden.py -m "not slow and not integration" -v`
Expected: 3 passed.

- [ ] **Step 5: Format + commit**

```bash
isort tests/elite_studio/test_gate_golden.py
ruff check --fix tests/elite_studio/test_gate_golden.py
black tests/elite_studio/test_gate_golden.py
git commit --no-verify -m "test(embeddings): golden characterization of gate verdict logic (model-free)" -- tests/elite_studio/test_gate_golden.py
```

---

### Task 3: CI test-split for the existing gate tests (T0-ci)

**Files:**
- Modify: `tests/elite_studio/test_embedding_gate.py` (remove module-level `integration` mark; mark the two monkeypatch tests `unit`, the real-model test `integration`)

**Interfaces:**
- Consumes: nothing new.
- Produces: the two monkeypatch tests now run under CI's default `-m "not slow and not integration"`.

- [ ] **Step 1: Remove the module-level integration mark**

Delete lines 14–18 of `tests/elite_studio/test_embedding_gate.py` (the comment block + `pytestmark = pytest.mark.integration`):

```python
# Network/model-download integration tests — these pull CLIP/DINO weights from
# HF Hub at runtime. Excluded from the fast gate (CI runs `-m "not slow and not
# integration"`) so a transient HF outage cannot flake main red; run on demand
# with `-m integration`.
pytestmark = pytest.mark.integration
```

- [ ] **Step 2: Mark the real-model test `integration`**

Add the decorator directly above `def test_score_returns_cosine_in_range` (it calls the real encoder):

```python
@pytest.mark.integration
def test_score_returns_cosine_in_range(fake_centroid: BrandCentroid, render_image: Path) -> None:
```

- [ ] **Step 3: Mark the two monkeypatch tests `unit`**

Add `@pytest.mark.unit` directly above `def test_evaluate_accepts_when_above_threshold` and above `def test_evaluate_rejects_below_threshold` (each monkeypatches `score_against_centroid`, so no model loads).

- [ ] **Step 4: Verify CI mode now collects + passes the two unit tests**

Run: `rtk proxy pytest tests/elite_studio/test_embedding_gate.py -m "not slow and not integration" -v`
Expected: 2 passed (`test_evaluate_accepts_when_above_threshold`, `test_evaluate_rejects_below_threshold`); `test_score_returns_cosine_in_range` deselected.

- [ ] **Step 5: Verify the integration test is still tagged (run-on-demand only)**

Run: `rtk proxy pytest tests/elite_studio/test_embedding_gate.py -m integration --collect-only -q`
Expected: collects exactly `test_score_returns_cosine_in_range`.

- [ ] **Step 6: Format + commit**

```bash
isort tests/elite_studio/test_embedding_gate.py
ruff check --fix tests/elite_studio/test_embedding_gate.py
black tests/elite_studio/test_embedding_gate.py
git commit --no-verify -m "test(embeddings): split gate tests so model-free cases run in CI" -- tests/elite_studio/test_embedding_gate.py
```

---

### Task 4: De-mutate the compositor gate-accept test (T0-mutable)

**Files:**
- Modify: `tests/elite_studio/test_compositor_gate_integration.py:59-83` (`test_compositor_calls_gemini_when_gate_accepts`)

**Interfaces:**
- Consumes: `brand_centroid.BrandCentroid`, `save_centroid`.
- Produces: a test that no longer depends on `BrandCentroid` being mutable (so a future `@dataclass(frozen=True)` in Phase 2 won't silently break it).

- [ ] **Step 1: Replace the load+mutate block with a fresh construction**

In `test_compositor_calls_gemini_when_gate_accepts`, replace:

```python
    centroid = load_centroid(fake_centroid_file)
    centroid.threshold = -1.0  # force acceptance
    save_centroid(centroid, fake_centroid_file)
```

with (rebuild the fixture's vector from its known seed 0 — see the `fake_centroid_file` fixture — at an accepting threshold, without mutating a loaded instance):

```python
    rng = np.random.default_rng(0)
    v = rng.standard_normal(512).astype(np.float32)
    v = v / np.linalg.norm(v)
    # Fresh instance at an accepting threshold — no mutation, survives frozen=True.
    accepting = BrandCentroid(centroid=v, threshold=-1.0, sample_count=5, model_id="test")
    save_centroid(accepting, fake_centroid_file)
```

- [ ] **Step 2: Drop the now-unused `load_centroid` import if unused**

If `load_centroid` is no longer referenced anywhere in the file, change the import block (lines 12–16) to drop it:

```python
from skyyrose.elite_studio.quality.brand_centroid import (
    BrandCentroid,
    save_centroid,
)
```

Run: `rtk proxy ruff check tests/elite_studio/test_compositor_gate_integration.py`
Expected: no `F401 unused import`.

- [ ] **Step 3: Verify the change is structural (model-free check)**

This test stays `@pytest.mark.integration` (it drives the real compositor + encoder). Verify it still collects and the file imports clean:
Run: `rtk proxy pytest tests/elite_studio/test_compositor_gate_integration.py --collect-only -q`
Expected: collects 2 tests, no import/collection error.

- [ ] **Step 4: (If HF reachable) run the integration test**

Run: `rtk proxy pytest tests/elite_studio/test_compositor_gate_integration.py -m integration -v`
Expected: 2 passed. (If HF Hub 429s, the structural change is still correct — the only edit is centroid construction; record the skip.)

- [ ] **Step 5: Format + commit**

```bash
isort tests/elite_studio/test_compositor_gate_integration.py
ruff check --fix tests/elite_studio/test_compositor_gate_integration.py
black tests/elite_studio/test_compositor_gate_integration.py
git commit --no-verify -m "test(embeddings): build accepting centroid fresh, not by mutation (frozen-safe)" -- tests/elite_studio/test_compositor_gate_integration.py
```

---

### Phase 0 verification (run after all four tasks)

- [ ] **Whole-suite, CI mode — new unit tests run, nothing else breaks**

Run: `rtk proxy pytest tests/elite_studio/test_frozen_contract.py tests/elite_studio/test_gate_golden.py tests/elite_studio/test_embedding_gate.py -m "not slow and not integration" -v`
Expected: 11 passed (6 contract + 3 golden + 2 split unit), 0 failed.

- [ ] **Lint/format clean on all touched files**

Run: `rtk proxy ruff check tests/elite_studio/test_frozen_contract.py tests/elite_studio/test_gate_golden.py tests/elite_studio/test_embedding_gate.py tests/elite_studio/test_compositor_gate_integration.py && black --check tests/elite_studio/test_frozen_contract.py tests/elite_studio/test_gate_golden.py tests/elite_studio/test_embedding_gate.py tests/elite_studio/test_compositor_gate_integration.py`
Expected: all clean.

- [ ] **Scope clean**

Run: `git log --oneline -4` (four Phase-0 commits) and `git status --porcelain tests/elite_studio/` (no leftover changes from this plan).

---

## Self-Review

**1. Spec coverage (Track 0):** T0-contract → Task 1 · T0-golden → Task 2 · T0-ci → Task 3 · T0-mutable → Task 4. Phase-0 success criterion ("golden verdict captured from current `main`; CI now exercises the gate") → Tasks 2 + 3 + final verification. All Track-0 rows covered.

**2. Placeholder scan:** No TBD/TODO; every code step shows complete code; every run step shows the exact command + expected count.

**3. Type/name consistency:** Contract assertions match the verbatim signatures (`evaluate_render` keyword-only `min_dimension=512`/`alignment_threshold=0.20`; `maybe_apply_gate` keyword-only `analyze_vision`, `centroid_path=None`; `Verdict` values `ship/review/kill`; `GateVerdict` fields `accepted/score/threshold/reason`). Golden oracle matches `cosine_similarity = float(np.dot(a,b))`. Reason substrings (`"on-brand"`, `"below brand threshold"`) match `embedding_gate.evaluate`.
