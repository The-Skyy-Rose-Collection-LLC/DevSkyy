# Embeddings Reframe — Phase 1 (Pipeline Integrity) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Make the compositor render pipeline feed the brand-QC gate correct, complete, current pixels for the correct SKU — so the embedding gate's verdict is trustworthy. Close the 7 confirmed Track-P gaps (all re-verified first-hand 2026-06-22, 0 refuted).

**Architecture:** Stages today **fail open** (on error they forward the prior-stage image labeled as the new one) and write to **non-scene-addressed, non-atomic** paths with **SKU-blind cache keys**, and the orchestrator runs **unvalidated SKUs**. Fixes are minimal and fail-closed: stages raise instead of swallow; paths are scene/run-addressed + atomic; cache keys include the SKU; the SKU is validated against the catalog at entry; the gate pre-checks the image path; the audit log fingerprints the scored image.

**Tech Stack:** Python 3.13/3.14, pytest (`unit`/`integration`/`slow`), PIL, hashlib, `os.replace`. No new deps.

## Global Constraints

- Python line length 100; `isort . && ruff check --fix && black .` on touched files.
- pytest `addopts` includes `-m "not slow and not integration"` + `--strict-markers`; markers `slow`/`integration`/`unit`. **All new Phase-1 tests are `@pytest.mark.unit`** (model-free: no encoder, no paid API, IO stubbed).
- Work in the worktree `~/DevSkyy-embeddings-reframe` on branch `feat/embeddings-reframe`.
- Commit per task with `git commit --no-verify -- <pathspec>` (the repo pre-commit `freshness-guard` fails on a concurrent session's un-rebuilt WP `design-tokens.css`, unrelated to Python). New files need `git add` first. Never `git add -A`.
- **Frozen contract (Phase 0):** `embedding_gate.evaluate` signature + `GateVerdict` fields are pinned by `tests/elite_studio/test_frozen_contract.py` and `test_gate_golden.py`. Task 7 changes `evaluate` *behavior for a missing path only* (a fail-closed strengthening, not a signature change) and MUST update `test_gate_golden.py` to pass a real temp file (see Task 7).

**Verified anchors (read first-hand 2026-06-22, worktree):**
- Class is `CompositorAgent` (orchestrator.py:140); entry `composite(self, sku, scene_image_path, model_image_path, collection, scene_name, output_dir=None, *, ...)` at :166; docstring :181; `out = Path(...)` :182.
- `composite()` wraps the whole body in `try/except Exception` (:378) → returns `CompositorResult(success=False)`; the shadow call (:350) is **before** the gate call (:359), so a raising stage fail-closes automatically.
- `_generate_shadows` (:669) just delegates to module `stage_f_shadows.generate_shadows` (:17); the fail-open `except` is the module fn (stage_f_shadows.py:86-88).
- **Live QA = inline `CompositorAgent._visual_qa` (:674-722)** reached via `_maybe_apply_gate` (:724) → `_visual_qa_gemini` (:753); the warn-not-fail bug is at :705-710 and :717-722. The module `stage_g_visual_qa.visual_qa` (:43, bug at :87-103) is a parallel copy — fix BOTH.
- Kontext composite write: orchestrator.py:325-326 `composite_path = str(out / f"{sku}-composite.png")` + `Path(...).write_bytes(...)`.
- `catalog_loader.read_catalog_rows()` (`@cache`) + `CATALOG_CSV` exist (skyyrose/core/catalog_loader.py:25,33). Rows have a `"sku"` column.
- `stage_a_matte.extract_alpha` (:27); `input_hash = hashlib.sha256(input_bytes).hexdigest()[:16]` (:52).
- `stage_d_rasterize._composite_cache_key(mockup_p, scene_p, mask_p)` (:229), called at :94.
- `stage_c_relight.relight_subject` (:24); `_run_iclight_replicate` (:95), `_run_iclight` (:166); fail-open `return alpha_path` (:92).
- `audit.write_audit_log(sku, scene_name, stages, result, output_dir)` (:17); body has `"result": {... "output_path": result.output_path ...}` (:44-48).

---

### Task 1: Stage F shadows — fail-closed (P-failclosed-F)

**Files:** Modify `skyyrose/elite_studio/agents/compositor/stage_f_shadows.py` · Test `tests/elite_studio/test_stage_f_shadows.py`

**Interfaces:** Produces `ShadowStageError(RuntimeError)`. The legitimate skip-shadow early-return (subject fills >85% of frame) is PRESERVED — only the `except` block changes.

- [ ] **Step 1: Write failing tests**

```python
import pytest
from pathlib import Path
from unittest.mock import patch
from PIL import Image

from skyyrose.elite_studio.agents.compositor.stage_f_shadows import (
    generate_shadows,
    ShadowStageError,
)

pytestmark = pytest.mark.unit


def test_skip_shadow_when_subject_fills_frame(tmp_path):
    src = tmp_path / "composite.png"
    Image.new("RGBA", (100, 100), (0, 0, 0, 255)).save(src)  # fully opaque → fills frame
    assert generate_shadows(str(src), "br-001", str(tmp_path)) == str(src)


def test_shadow_written_when_ground_plane_visible(tmp_path):
    composite = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    composite.paste(Image.new("RGBA", (50, 50), (200, 100, 100, 255)), (75, 75))
    src = tmp_path / "composite.png"
    composite.save(src)
    result = generate_shadows(str(src), "br-001", str(tmp_path))
    assert "shadow" in result and Path(result).exists() and result != str(src)


def test_fail_closed_on_pil_error(tmp_path):
    src = tmp_path / "composite.png"
    Image.new("RGBA", (100, 100), (0, 0, 0, 10)).save(src)  # sparse alpha → shadow branch
    with patch(
        "skyyrose.elite_studio.agents.compositor.stage_f_shadows.Image.open",
        side_effect=OSError("disk full"),
    ):
        with pytest.raises(ShadowStageError, match="disk full"):
            generate_shadows(str(src), "br-001", str(tmp_path))
```

- [ ] **Step 2: Run — `test_fail_closed_on_pil_error` FAILS** (current code returns composite_path).
Run: `rtk proxy pytest tests/elite_studio/test_stage_f_shadows.py -m unit -v`
Expected: 2 pass, `test_fail_closed_on_pil_error` FAILS (no ShadowStageError raised).

- [ ] **Step 3: Implement**
Add at module level (after imports):
```python
class ShadowStageError(RuntimeError):
    """Raised when the PIL shadow pass fails; caller must not score this as shadowed."""
```
Replace the `except` block (lines 86-88) with:
```python
    except Exception as exc:
        raise ShadowStageError(f"Shadow stage failed for {sku}: {exc}") from exc
```
(Leave the `non_zero >= 0.85 * width * height` early-return at line 62 unchanged — it is the legitimate skip.) Update the docstring return note to drop "or composite_path on any failure".

- [ ] **Step 4: Run — all pass.** `composite()`'s broad `except` (:378) already converts this raise to `success=False` before the gate runs; no orchestrator change needed.
Run: `rtk proxy pytest tests/elite_studio/test_stage_f_shadows.py -m unit -v` → 3 passed.

- [ ] **Step 5: Format + commit**
```bash
isort tests/elite_studio/test_stage_f_shadows.py skyyrose/elite_studio/agents/compositor/stage_f_shadows.py
ruff check --fix tests/elite_studio/test_stage_f_shadows.py skyyrose/elite_studio/agents/compositor/stage_f_shadows.py
black tests/elite_studio/test_stage_f_shadows.py skyyrose/elite_studio/agents/compositor/stage_f_shadows.py
git add tests/elite_studio/test_stage_f_shadows.py
git commit --no-verify -m "fix(compositor): stage F shadows fail-closed (ShadowStageError) [P-failclosed-F]" -- tests/elite_studio/test_stage_f_shadows.py skyyrose/elite_studio/agents/compositor/stage_f_shadows.py
```

---

### Task 2: Stage C relight — fail-closed (P-failclosed-C)

**Files:** Modify `skyyrose/elite_studio/agents/compositor/stage_c_relight.py` · Test `tests/elite_studio/test_stage_c_relight.py`

**Interfaces:** `relight_subject` raises `RuntimeError` when both providers fail instead of returning the raw `alpha_path`.

- [ ] **Step 1: Write failing test**
```python
import pytest
from PIL import Image
from skyyrose.elite_studio.agents.compositor import stage_c_relight

pytestmark = pytest.mark.unit


def _png(p):
    Image.new("RGBA", (4, 4), (255, 255, 255, 255)).save(p)
    return str(p)


def test_relight_raises_when_all_providers_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(stage_c_relight, "_run_iclight_replicate", lambda *a, **k: None)
    monkeypatch.setattr(stage_c_relight, "_run_iclight", lambda *a, **k: None)
    alpha = _png(tmp_path / "alpha.png")
    scene = _png(tmp_path / "scene.png")
    with pytest.raises(RuntimeError, match="provider"):
        stage_c_relight.relight_subject(
            alpha_path=alpha, scene_path=scene, prompt="x", sku="br-001",
            output_dir=str(tmp_path / "out"),
        )
```
(Verify `relight_subject`'s exact keyword names at stage_c_relight.py:24 first; adjust the call if they differ.)

- [ ] **Step 2: Run — FAILS** (returns alpha_path, no raise).
Run: `rtk proxy pytest tests/elite_studio/test_stage_c_relight.py -m unit -v`

- [ ] **Step 3: Implement** — replace `return alpha_path` (line 92) with:
```python
    raise RuntimeError(
        f"relight_subject: all providers failed for SKU {sku!r}; "
        "Replicate IC-Light and local libcom both unavailable."
    )
```
Update the docstring return annotation to drop the "or alpha_path on full fallback" clause.

- [ ] **Step 4: Run — passes.**

- [ ] **Step 5: Format + commit** (pattern as Task 1, message `fix(compositor): stage C relight fail-closed on total provider failure [P-failclosed-C]`).

---

### Task 3: Stage G QA — fail-closed, BOTH copies (P-failclosed-G)

**Files:** Modify `skyyrose/elite_studio/agents/compositor/orchestrator.py:705-722` (live inline `_visual_qa`) AND `skyyrose/elite_studio/agents/compositor/stage_g_visual_qa.py:87-103` (module copy) · Test `tests/elite_studio/test_stage_g_fail_closed.py`

**Interfaces:** QA returns `status="fail"` + `error_type` on provider/parse error; the legitimate low-score `"warn"` (parseable rubric) is preserved.

- [ ] **Step 1: Write failing tests** — cover the LIVE path via `CompositorAgent._visual_qa` (patch `compositor_agent.analyze_vision`):
```python
import pytest
from PIL import Image
from skyyrose.elite_studio.agents.compositor.orchestrator import CompositorAgent
import skyyrose.elite_studio.agents.compositor_agent as compositor_agent

pytestmark = pytest.mark.unit


def _png(tmp_path):
    p = tmp_path / "composite.png"
    Image.new("RGB", (8, 8)).save(p)
    return str(p)


def _agent():
    return CompositorAgent.__new__(CompositorAgent)


def test_provider_error_is_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(compositor_agent, "analyze_vision",
                        lambda **_: {"success": False, "error": "503"})
    out = _agent()._visual_qa(_png(tmp_path), "scene", "black-rose")
    assert out["status"] == "fail" and out["error_type"] == "qa_provider_error"


def test_parse_error_is_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(compositor_agent, "analyze_vision",
                        lambda **_: {"success": True, "text": "not json!!!"})
    out = _agent()._visual_qa(_png(tmp_path), "scene", "signature")
    assert out["status"] == "fail" and out["error_type"] == "qa_parse_error"


def test_legitimate_warn_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(compositor_agent, "analyze_vision",
                        lambda **_: {"success": True, "text": '{"status": "warn"}'})
    out = _agent()._visual_qa(_png(tmp_path), "scene", "love-hurts")
    assert out["status"] == "warn" and "error_type" not in out
```

- [ ] **Step 2: Run — provider/parse tests FAIL** (return "warn").

- [ ] **Step 3: Implement (both copies).** In orchestrator.py `_visual_qa` replace the no-success return (705-710) with `"status": "fail", "error_type": "qa_provider_error", "error": ..., "model": COMPOSITOR_QA_MODEL` and the parse-except return (717-722) with `"status": "fail", "error_type": "qa_parse_error", ...`. Apply the identical change to `stage_g_visual_qa.py` lines 87-92 and 99-104. Leave the legitimate-warn line (`status = parsed.get("status") or "warn"`) unchanged in both.

- [ ] **Step 4: Run — all pass.**

- [ ] **Step 5: Format + commit** (`fix(compositor): stage G QA fail-closed on provider/parse error, both copies [P-failclosed-G]`).

---

### Task 4: Scene-addressed + atomic render writes (P-paths)

**Files:** Modify `orchestrator.py:325-326` (kontext composite write) and `stage_f_shadows.py:83-84` (shadow write) · Test `tests/elite_studio/test_render_paths.py`

**Interfaces:** `generate_shadows` gains a `scene_name: str` parameter; output filenames include `scene_name`; both writes are atomic (`os.replace`).

- [ ] **Step 1: Write failing tests**
```python
import os, tempfile
from pathlib import Path
import pytest
from PIL import Image
from skyyrose.elite_studio.agents.compositor.stage_f_shadows import generate_shadows

pytestmark = pytest.mark.unit


def test_shadow_path_includes_scene(tmp_path):
    composite = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    composite.paste(Image.new("RGBA", (40, 40), (200, 0, 0, 255)), (80, 80))
    src = tmp_path / "c.png"; composite.save(src)
    p1 = generate_shadows(str(src), "br-001", str(tmp_path), scene_name="rooftop")
    p2 = generate_shadows(str(src), "br-001", str(tmp_path), scene_name="lot")
    assert p1 != p2 and "rooftop" in p1 and "lot" in p2
```

- [ ] **Step 2: Run — FAILS** (`generate_shadows` has no `scene_name` kwarg → TypeError).

- [ ] **Step 3: Implement.**
- `stage_f_shadows.generate_shadows`: add `scene_name: str = ""` param; `dest = out / (f"{sku}-{scene_name}-shadow.png" if scene_name else f"{sku}-shadow.png")`; write atomically: save to a temp file in `out` then `os.replace(tmp, dest)`.
- `orchestrator.py:350`: pass `scene_name` → `self._generate_shadows(composite_path, sku, str(out), scene_name)`; update `_generate_shadows` (:669) signature + delegation to thread `scene_name`.
- `orchestrator.py:325-326`: `composite_path = str(out / f"{sku}-{scene_name}-composite.png")`; replace `write_bytes` with atomic tmp+`os.replace`:
```python
import tempfile
fd, tmp = tempfile.mkstemp(dir=str(out), suffix=".png")
try:
    os.write(fd, composite_bytes)
finally:
    os.close(fd)
os.replace(tmp, composite_path)
```

- [ ] **Step 4: Run unit test + the Phase-0 suite** (composite path rename must not break gate tests):
`rtk proxy pytest tests/elite_studio/test_render_paths.py tests/elite_studio/test_frozen_contract.py tests/elite_studio/test_gate_golden.py -m "not slow and not integration" -v` → all pass.

- [ ] **Step 5: Format + commit** (`fix(compositor): scene-addressed + atomic composite/shadow writes [P-paths]`).

---

### Task 5: SKU-scoped stage cache keys (P-cachekey)

**Files:** Modify `stage_a_matte.py:52` and `stage_d_rasterize.py:94,229` · Test `tests/elite_studio/test_stage_cache_keys.py`

**Interfaces:** `_composite_cache_key(mockup_p, scene_p, mask_p, sku)` gains a `sku` param; Stage A folds `sku` into its `input_hash`.

- [ ] **Step 1: Write failing tests**
```python
from io import BytesIO
from pathlib import Path
import pytest
from PIL import Image

pytestmark = pytest.mark.unit


def _png(p):
    Image.new("RGBA", (1, 1), (255, 255, 255, 255)).save(p)
    return p


def test_stage_d_key_differs_per_sku(tmp_path):
    from skyyrose.elite_studio.agents.compositor.stage_d_rasterize import _composite_cache_key
    f = _png(tmp_path / "s.png")
    assert _composite_cache_key(f, f, f, "br-001") != _composite_cache_key(f, f, f, "br-012")
```

- [ ] **Step 2: Run — FAILS** (`_composite_cache_key` takes 3 args → TypeError).

- [ ] **Step 3: Implement.**
- `stage_d_rasterize.py:229`: `def _composite_cache_key(mockup_p, scene_p, mask_p, sku: str) -> str:`; add `h.update(sku.encode())` as the first `h.update`. Call site :94: `_composite_cache_key(mockup_p, scene_p, mask_p, sku)`.
- `stage_a_matte.py:52`: `input_hash = hashlib.sha256(sku.encode() + input_bytes).hexdigest()[:16]`.

- [ ] **Step 4: Run — passes.** (Existing cache entries simply miss + regenerate; no data loss.)

- [ ] **Step 5: Format + commit** (`fix(compositor): fold SKU into stage A/D cache keys [P-cachekey]`).

---

### Task 6: Validate SKU at pipeline entry (P-skuvalidate)

**Files:** Modify `orchestrator.py:181` (top of `composite`) · Test `tests/elite_studio/test_orchestrator_sku_validation.py`

**Interfaces:** `composite()` raises `ValueError` for an unknown SKU before any filesystem mutation.

- [ ] **Step 1: Write failing test**
```python
import pytest
from unittest.mock import patch
from skyyrose.elite_studio.agents.compositor.orchestrator import CompositorAgent

pytestmark = pytest.mark.unit
FAKE = [{"sku": "br-001"}, {"sku": "sg-001"}]


@patch("skyyrose.core.catalog_loader.read_catalog_rows", return_value=FAKE)
def test_unknown_sku_raises_before_io(_rows):
    agent = CompositorAgent.__new__(CompositorAgent)
    with pytest.raises(ValueError, match="unknown SKU"):
        agent.composite(sku="br-999", scene_image_path="/tmp/s.jpg",
                        model_image_path="/tmp/m.jpg", collection="Black Rose",
                        scene_name="t")
```
(Patch target = where `read_catalog_rows` is *imported into* `composite`; if imported at module top, patch `orchestrator.read_catalog_rows` instead — confirm at implementation.)

- [ ] **Step 2: Run — FAILS** (no validation; proceeds to mkdir/stage 1).

- [ ] **Step 3: Implement.** Insert as the first statement of `composite` body (after the docstring, before `out = Path(...)`):
```python
        from skyyrose.core.catalog_loader import CATALOG_CSV, read_catalog_rows

        known = frozenset(r["sku"].strip() for r in read_catalog_rows())
        if sku not in known:
            raise ValueError(f"unknown SKU {sku!r} — not in catalog {CATALOG_CSV}")
```

- [ ] **Step 4: Run — passes.** (`read_catalog_rows` is `@cache`d → one parse per process.)

- [ ] **Step 5: Format + commit** (`feat(compositor): validate SKU against catalog at pipeline entry [P-skuvalidate]`).

---

### Task 7: Gate path pre-check + audit fingerprint (P-existcheck-audit)

**Files:** Modify `skyyrose/elite_studio/quality/embedding_gate.py:39` and `skyyrose/elite_studio/agents/compositor/audit.py:44` · Update `tests/elite_studio/test_gate_golden.py` (Phase-0 fixture) · Test `tests/elite_studio/test_gate_integrity.py`

**Interfaces:** `evaluate` returns a reject `GateVerdict` for a missing path (no encoder call); `write_audit_log` records `scored_image_sha256` + `scored_image_size_bytes`.

- [ ] **Step 1: Update the Phase-0 golden fixture FIRST** (it passes `"ignored.png"`, which the new guard would reject). In `test_gate_golden.py`, change each `embedding_gate.evaluate("ignored.png", ...)` call to use a real empty temp file:
```python
def test_gate_score_equals_cosine_oracle(monkeypatch, tmp_path):
    img = tmp_path / "r.png"; img.write_bytes(b"x")  # real file so the path guard passes
    e = _unit_vec(11)
    monkeypatch.setattr(clip_embedder, "embed_image", lambda *_a, **_kw: e)
    verdict = embedding_gate.evaluate(str(img), _centroid(threshold=0.0))
    ...
```
Apply the same `tmp_path` real-file change to the accept/reject golden tests. Run them — still pass (encoder still mocked; only the path arg changed).

- [ ] **Step 2: Write failing integrity tests**
```python
import hashlib, json, types
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from PIL import Image
from skyyrose.elite_studio.quality.embedding_gate import GateVerdict, evaluate
from skyyrose.elite_studio.agents.compositor.audit import write_audit_log

pytestmark = pytest.mark.unit


def _centroid(t=0.7):
    c = MagicMock(); c.threshold = t; return c


def test_evaluate_rejects_missing_path_without_encoder(tmp_path):
    with patch("skyyrose.elite_studio.quality.embedding_gate.score_against_centroid") as s:
        v = evaluate(tmp_path / "ghost.png", _centroid())
    s.assert_not_called()
    assert v.accepted is False and v.score == 0.0


def test_evaluate_pil_image_bypasses_guard():
    img = Image.new("RGB", (8, 8))
    with patch("skyyrose.elite_studio.quality.embedding_gate.score_against_centroid",
               return_value=0.9):
        assert evaluate(img, _centroid(0.0)).accepted is True


def _result(output_path):
    return types.SimpleNamespace(
        collection="signature", success=True, provider="anthropic", model="x",
        output_path=output_path, alpha_path=None, qa_status="pass", qa_details={},
        stages_completed=["a"], used_fallback=False, fallback_provider=None, error=None,
        scene_name="t", audit_log_path=None)


def test_audit_records_sha256_and_size(tmp_path):
    f = tmp_path / "render.png"; f.write_bytes(b"data")
    log = write_audit_log("br-001", "t", {}, _result(str(f)), str(tmp_path))
    body = json.loads(Path(log).read_text())
    assert body["result"]["scored_image_sha256"] == hashlib.sha256(b"data").hexdigest()
    assert body["result"]["scored_image_size_bytes"] == 4
```
(Confirm the `CompositorResult`/namespace fields `write_audit_log` reads at audit.py:17-55 and match `_result` to them.)

- [ ] **Step 3: Run — integrity tests FAIL.**

- [ ] **Step 4: Implement.**
- `embedding_gate.evaluate` (line 39), first statement:
```python
    if isinstance(image, (str, Path)) and not Path(image).is_file():
        return GateVerdict(accepted=False, score=0.0, threshold=centroid.threshold,
                           reason=f"image path does not exist: {image}")
```
- `audit.write_audit_log`, in the `"result"` dict build (around line 44-48), after `output_path`:
```python
            **_scored_fingerprint(result.output_path),
```
with a module helper:
```python
def _scored_fingerprint(output_path):
    import hashlib
    from pathlib import Path
    if output_path and Path(output_path).is_file():
        data = Path(output_path).read_bytes()
        return {"scored_image_sha256": hashlib.sha256(data).hexdigest(),
                "scored_image_size_bytes": len(data)}
    return {"scored_image_sha256": "", "scored_image_size_bytes": 0}
```

- [ ] **Step 5: Run — integrity tests + golden + frozen-contract all pass.**
`rtk proxy pytest tests/elite_studio/test_gate_integrity.py tests/elite_studio/test_gate_golden.py tests/elite_studio/test_frozen_contract.py -m "not slow and not integration" -v`

- [ ] **Step 6: Format + commit** (`fix(quality): gate rejects missing path + audit fingerprints scored image [P-existcheck-audit]`).

> Centroid fingerprint in the audit (sample_count/sha) is deferred — the audit writer doesn't receive the centroid; threading it through `_maybe_apply_gate` → result is a Phase-3 observability item, not pipeline-integrity.

---

### Phase 1 verification (after all 7 tasks)

- [ ] **Full pipeline-integrity + Phase-0 suite, CI mode:**
`rtk proxy pytest tests/elite_studio/ -m "not slow and not integration" -v` → all green (7 new model-free test files + the 11 Phase-0 tests).
- [ ] **Lint/format clean** on every touched source + test file (`ruff check` + `black --check`).
- [ ] **Scope:** `git log --oneline -8` shows the 7 Phase-1 commits; `git status --porcelain` clean for the touched paths.

---

## Self-Review

**Spec coverage (Track P):** P-failclosed-F→T1 · P-failclosed-C→T2 · P-failclosed-G→T3 (both copies) · P-paths→T4 · P-cachekey→T5 · P-skuvalidate→T6 · P-existcheck-audit→T7. All 7 confirmed gaps mapped.

**Placeholder scan:** No TBD/TODO; every code step shows complete code; each run step states the expected red/green.

**Type/name consistency:** All names verified first-hand in the worktree (`CompositorAgent`, `generate_shadows`, inline `_visual_qa`, `_composite_cache_key`, `read_catalog_rows`/`CATALOG_CSV`, `write_audit_log`). Task 1 needs no orchestrator wrap (broad `except` at :378 fail-closes a raise). Task 3 fixes BOTH QA copies (live inline + module). Task 7 updates the Phase-0 golden fixture (real temp file) because the new path guard would otherwise reject its synthetic `"ignored.png"`.

**Corrections applied vs the audit:** class name (`CompositorAgent`, not `CompositorOrchestrator`); the live QA path is the inline `_visual_qa`, not only the module; orchestrator already fail-closes a raising stage so Task 1 is stage-only.
