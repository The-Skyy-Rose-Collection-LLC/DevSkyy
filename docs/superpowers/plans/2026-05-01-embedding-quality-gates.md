# Embedding-Powered Quality Gates Implementation Plan

> **REVISED 2026-05-02 — Task 4 (Wire Embedding Gate Into Compositor Stage 5.5) is DEFERRED.**
> Reason: `CompositorAgent` is currently a 68-line `pass_through` shell pending rebuild (commit `f25fd25d3`, "Phase B1 scorched earth — rebuild pending"). Task 4 cannot be executed against the codebase as-is — the line numbers and method names it references no longer exist. See ADR-0001 and the companion stub plan `2026-05-02-compositor-agent-rebuild.md`. The embedding gate library produced by Tasks 1-3 will be ready to drop into the rebuilt agent.
> All other tasks (1, 2, 3, 5, 6, 7, 8, 9) remain executable as written — they target files that exist (`orchestration/threed_round_table.py`, `scripts/nano_banana/cli.py`, `wordpress-theme/skyyrose-flagship/data/product-embeddings.json`).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. **SKIP TASK 4 — it is marked DEFERRED below.**

**Goal:** Add three CLIP-embedding-driven quality gates to existing AI pipelines: (1) Compositor pre-QA filter that rejects off-brand renders before paid Gemini QA, (2) Catalog deduplication that catches near-identical SKUs at intake, and (3) CLIP text-to-image alignment scorer wired into Nano Banana and the 3D round-table judging.

**Architecture:** All three features share a single `skyyrose.core.clip_embedder` module — a singleton CLIP loader that exposes `embed_image()`, `embed_text()`, and `cosine_similarity()`. Each feature is a thin layer on top: brand-centroid math for the compositor gate, near-neighbor scanning for catalog dedup, and prompt-image alignment for the scorer. CLIP weights are loaded lazily at first use and reused across all three. No model loads in the browser — these are server-side gates.

**Tech Stack:** Python 3.11+, `transformers` 4.x (CLIP), `torch` 2.x (with MPS on Apple Silicon), `numpy`, `pillow`, pytest. CLIP model: `openai/clip-vit-base-patch32` (matches the embeddings format already shipped in `wordpress-theme/skyyrose-flagship/data/product-embeddings.json`).

---

## File Structure

**New modules:**
- `skyyrose/core/clip_embedder.py` — singleton CLIP loader, `embed_image`, `embed_text`, `cosine_similarity` (~130 lines)
- `skyyrose/elite_studio/quality/brand_centroid.py` — compute + persist brand-style centroid from approved images (~90 lines)
- `skyyrose/elite_studio/quality/embedding_gate.py` — pre-QA filter that scores renders against centroid (~80 lines)
- `skyyrose/elite_studio/quality/clip_alignment.py` — text-to-image CLIP similarity scorer (~70 lines)
- `skyyrose/core/catalog_dedup.py` — near-duplicate detection across catalog (~110 lines)
- `scripts/check_catalog_duplicates.py` — CLI wrapper for catalog dedup (~50 lines)
- `scripts/build_brand_centroid.py` — CLI to (re)compute and save the brand centroid (~50 lines)
- `skyyrose/elite_studio/data/brand_centroid.npz` — generated artifact (centroid + threshold)

**Modifications:**
- `skyyrose/elite_studio/agents/compositor_agent.py` — insert pre-QA gate between stage 5 and stage 6
- `orchestration/threed_round_table.py` — add `clip_alignment_score` field to `ThreeDQualityScores` and use it in the weighted total
- `scripts/nano_banana/cli.py` — add post-render alignment scoring, log to nano-banana audit output

**New tests:**
- `tests/elite_studio/test_clip_embedder.py`
- `tests/elite_studio/test_brand_centroid.py`
- `tests/elite_studio/test_embedding_gate.py`
- `tests/elite_studio/test_clip_alignment.py`
- `tests/elite_studio/test_compositor_gate_integration.py`
- `tests/core/test_catalog_dedup.py`
- `tests/scripts/test_check_catalog_duplicates.py`

---

## Task 1: Shared CLIP Embedder Service

**Files:**
- Create: `skyyrose/core/clip_embedder.py`
- Test: `tests/elite_studio/test_clip_embedder.py`

The singleton pattern matters: CLIP-base is ~600MB. Loading it 3+ times across pipelines would tank startup. We load once, share across all three features.

- [ ] **Step 1: Write the failing test**

Create `tests/elite_studio/test_clip_embedder.py`:
```python
"""Tests for skyyrose.core.clip_embedder."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from skyyrose.core import clip_embedder


@pytest.fixture
def red_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (224, 224), color=(220, 20, 20))
    p = tmp_path / "red.png"
    img.save(p)
    return p


@pytest.fixture
def blue_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (224, 224), color=(20, 20, 220))
    p = tmp_path / "blue.png"
    img.save(p)
    return p


def test_embed_image_returns_normalized_vector(red_image: Path) -> None:
    vec = clip_embedder.embed_image(red_image)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (512,)
    assert pytest.approx(float(np.linalg.norm(vec)), abs=1e-4) == 1.0


def test_embed_text_returns_normalized_vector() -> None:
    vec = clip_embedder.embed_text("a black hoodie on a moody street")
    assert vec.shape == (512,)
    assert pytest.approx(float(np.linalg.norm(vec)), abs=1e-4) == 1.0


def test_cosine_similarity_self_is_one(red_image: Path) -> None:
    vec = clip_embedder.embed_image(red_image)
    assert pytest.approx(clip_embedder.cosine_similarity(vec, vec), abs=1e-5) == 1.0


def test_cosine_similarity_different_images_below_one(red_image: Path, blue_image: Path) -> None:
    a = clip_embedder.embed_image(red_image)
    b = clip_embedder.embed_image(blue_image)
    sim = clip_embedder.cosine_similarity(a, b)
    assert -1.0 <= sim < 1.0


def test_singleton_does_not_reload_model(red_image: Path) -> None:
    clip_embedder.get_clip()
    state = clip_embedder._STATE  # internal access for test only
    first_model_id = id(state.model)
    clip_embedder.embed_image(red_image)
    assert id(state.model) == first_model_id
```

- [ ] **Step 2: Run test to verify failure**

```bash
pytest tests/elite_studio/test_clip_embedder.py -v
```
Expected: `ModuleNotFoundError: No module named 'skyyrose.core.clip_embedder'`

- [ ] **Step 3: Write the implementation**

Create `skyyrose/core/clip_embedder.py`:
```python
"""Singleton CLIP loader shared by all server-side embedding features.

Loads `openai/clip-vit-base-patch32` once on first call, reuses across all
features (compositor gate, catalog dedup, prompt alignment scorer). The
embedding dimension and L2-normalization match the browser-side embeddings
already shipped in wordpress-theme/skyyrose-flagship/data/product-embeddings.json.

Exports:
    get_clip() -> _ClipState                          # internal handle
    embed_image(path_or_pil) -> np.ndarray             # 512-dim L2-normalized
    embed_text(text) -> np.ndarray                     # 512-dim L2-normalized
    cosine_similarity(a, b) -> float                   # dot product (already normalized)

@package SkyyRose
@since 1.1.0
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Union

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

logger = logging.getLogger(__name__)

MODEL_ID = "openai/clip-vit-base-patch32"
EMBED_DIM = 512


@dataclass
class _ClipState:
    model: CLIPModel
    processor: CLIPProcessor
    device: str


_STATE: _ClipState | None = None
_LOCK = Lock()


def _select_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def get_clip() -> _ClipState:
    """Lazy singleton CLIP loader. Thread-safe."""
    global _STATE
    if _STATE is not None:
        return _STATE
    with _LOCK:
        if _STATE is not None:
            return _STATE
        device = _select_device()
        logger.info("Loading CLIP %s on %s", MODEL_ID, device)
        model = CLIPModel.from_pretrained(MODEL_ID).to(device).eval()
        processor = CLIPProcessor.from_pretrained(MODEL_ID)
        _STATE = _ClipState(model=model, processor=processor, device=device)
    return _STATE


def _l2_normalize(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v)
    if norm < 1e-9:
        return v
    return v / norm


def embed_image(source: Union[str, Path, Image.Image]) -> np.ndarray:
    """Run CLIP vision encoder. Returns L2-normalized 512-d numpy array."""
    state = get_clip()
    if isinstance(source, (str, Path)):
        img = Image.open(source).convert("RGB")
    elif isinstance(source, Image.Image):
        img = source.convert("RGB")
    else:
        raise TypeError(f"embed_image expects path or PIL.Image, got {type(source).__name__}")
    inputs = state.processor(images=img, return_tensors="pt").to(state.device)
    with torch.no_grad():
        feats = state.model.get_image_features(**inputs)
    feats = feats.squeeze(0).cpu().numpy().astype(np.float32)
    return _l2_normalize(feats)


def embed_text(text: str) -> np.ndarray:
    """Run CLIP text encoder. Returns L2-normalized 512-d numpy array."""
    if not text or not text.strip():
        raise ValueError("embed_text requires non-empty text")
    state = get_clip()
    inputs = state.processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(state.device)
    with torch.no_grad():
        feats = state.model.get_text_features(**inputs)
    feats = feats.squeeze(0).cpu().numpy().astype(np.float32)
    return _l2_normalize(feats)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product. Both inputs MUST already be L2-normalized."""
    if a.shape != b.shape:
        raise ValueError(f"shape mismatch: {a.shape} vs {b.shape}")
    return float(np.dot(a, b))
```

- [ ] **Step 4: Run tests, verify they pass**

```bash
pytest tests/elite_studio/test_clip_embedder.py -v
```
Expected: 5/5 pass. First run is slow (~10-30s for model download + load); subsequent runs use the cached model.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/core/clip_embedder.py tests/elite_studio/test_clip_embedder.py
git commit -m "feat(core): add singleton CLIP embedder for quality gates"
```

---

## Task 2: Brand Centroid Builder

**Files:**
- Create: `skyyrose/elite_studio/quality/brand_centroid.py`
- Create: `scripts/build_brand_centroid.py`
- Test: `tests/elite_studio/test_brand_centroid.py`

The brand centroid is the mean of CLIP image embeddings of approved hero shots. New renders are graded by cosine similarity to this centroid. We persist as `.npz` so the compositor can load it cheaply.

- [ ] **Step 1: Write the failing test**

Create `tests/elite_studio/test_brand_centroid.py`:
```python
"""Tests for skyyrose.elite_studio.quality.brand_centroid."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from skyyrose.elite_studio.quality import brand_centroid


@pytest.fixture
def approved_dir(tmp_path: Path) -> Path:
    d = tmp_path / "approved"
    d.mkdir()
    for i, color in enumerate([(20, 20, 20), (40, 40, 40), (10, 10, 10)]):
        Image.new("RGB", (224, 224), color=color).save(d / f"shot_{i}.png")
    return d


def test_build_centroid_returns_normalized_vector(approved_dir: Path) -> None:
    result = brand_centroid.build_centroid(approved_dir)
    assert result.centroid.shape == (512,)
    assert pytest.approx(float(np.linalg.norm(result.centroid)), abs=1e-4) == 1.0
    assert result.sample_count == 3


def test_build_centroid_records_threshold(approved_dir: Path) -> None:
    result = brand_centroid.build_centroid(approved_dir, threshold_percentile=10)
    # Threshold is the 10th percentile of in-cluster similarities — bounded.
    assert 0.0 < result.threshold < 1.0


def test_save_and_load_centroid_roundtrip(approved_dir: Path, tmp_path: Path) -> None:
    built = brand_centroid.build_centroid(approved_dir)
    out = tmp_path / "centroid.npz"
    brand_centroid.save_centroid(built, out)
    assert out.exists()
    loaded = brand_centroid.load_centroid(out)
    assert np.allclose(loaded.centroid, built.centroid, atol=1e-6)
    assert loaded.threshold == pytest.approx(built.threshold, abs=1e-6)
    assert loaded.sample_count == built.sample_count


def test_build_centroid_empty_dir_raises(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(ValueError, match="no image"):
        brand_centroid.build_centroid(empty)
```

- [ ] **Step 2: Run test to verify failure**

```bash
pytest tests/elite_studio/test_brand_centroid.py -v
```
Expected: `ModuleNotFoundError: No module named 'skyyrose.elite_studio.quality.brand_centroid'`

- [ ] **Step 3: Write the implementation**

Create `skyyrose/elite_studio/quality/brand_centroid.py`:
```python
"""Brand-style centroid: mean CLIP embedding of approved hero shots.

The compositor pre-QA gate scores each new render's cosine similarity to
this centroid. A shot far from the centroid is off-brand and skipped before
the paid Gemini QA stage.

@package SkyyRose
@since 1.1.0
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from skyyrose.core import clip_embedder

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


@dataclass
class BrandCentroid:
    centroid: np.ndarray            # (512,) L2-normalized
    threshold: float                # cosine score below which renders fail the gate
    sample_count: int               # number of approved images that built it
    model_id: str                   # CLIP model used (for compatibility checking)


def _list_images(directory: Path) -> list[Path]:
    return sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTS)


def build_centroid(approved_dir: Path, threshold_percentile: float = 10.0) -> BrandCentroid:
    """Compute centroid + a robust threshold from approved hero shots.

    Threshold is the `threshold_percentile`-th percentile of in-cluster
    cosine similarities (each approved image vs centroid). Setting it to
    10 means we accept renders at least as similar to the centroid as 90%
    of our approved set already is.
    """
    paths = _list_images(approved_dir)
    if not paths:
        raise ValueError(f"no image files in {approved_dir}")

    embeddings = np.stack([clip_embedder.embed_image(p) for p in paths])
    raw_centroid = embeddings.mean(axis=0)
    norm = np.linalg.norm(raw_centroid)
    if norm < 1e-9:
        raise ValueError("degenerate centroid (zero magnitude)")
    centroid = (raw_centroid / norm).astype(np.float32)

    # In-cluster similarity distribution -> robust threshold.
    sims = embeddings @ centroid
    threshold = float(np.percentile(sims, threshold_percentile))

    return BrandCentroid(
        centroid=centroid,
        threshold=threshold,
        sample_count=len(paths),
        model_id=clip_embedder.MODEL_ID,
    )


def save_centroid(c: BrandCentroid, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        path,
        centroid=c.centroid,
        threshold=np.array(c.threshold, dtype=np.float32),
        sample_count=np.array(c.sample_count, dtype=np.int64),
        model_id=np.array(c.model_id),
    )


def load_centroid(path: Path) -> BrandCentroid:
    data = np.load(path, allow_pickle=False)
    return BrandCentroid(
        centroid=data["centroid"],
        threshold=float(data["threshold"]),
        sample_count=int(data["sample_count"]),
        model_id=str(data["model_id"]),
    )
```

- [ ] **Step 4: Run tests, verify pass**

```bash
pytest tests/elite_studio/test_brand_centroid.py -v
```
Expected: 4/4 pass.

- [ ] **Step 5: Create the CLI script**

Create `scripts/build_brand_centroid.py`:
```python
#!/usr/bin/env python3
"""Build the SkyyRose brand-style centroid from approved hero shots.

Usage:
    python3 scripts/build_brand_centroid.py \\
        --approved-dir wordpress-theme/skyyrose-flagship/assets/images/products \\
        --output skyyrose/elite_studio/data/brand_centroid.npz \\
        --threshold-percentile 10

Re-run whenever the approved-shot set changes.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skyyrose.elite_studio.quality.brand_centroid import build_centroid, save_centroid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approved-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold-percentile", type=float, default=10.0)
    args = parser.parse_args()

    if not args.approved_dir.is_dir():
        print(f"FATAL: approved-dir not found: {args.approved_dir}", file=sys.stderr)
        return 1

    print(f"Building centroid from {args.approved_dir}...")
    centroid = build_centroid(args.approved_dir, threshold_percentile=args.threshold_percentile)
    save_centroid(centroid, args.output)
    print(f"Wrote centroid ({centroid.sample_count} samples, threshold={centroid.threshold:.4f}) -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Commit**

```bash
git add skyyrose/elite_studio/quality/brand_centroid.py scripts/build_brand_centroid.py tests/elite_studio/test_brand_centroid.py
git commit -m "feat(quality): add brand-style centroid builder for pre-QA gating"
```

---

## Task 3: Compositor Embedding Gate (Logic)

**Files:**
- Create: `skyyrose/elite_studio/quality/embedding_gate.py`
- Test: `tests/elite_studio/test_embedding_gate.py`

The gate logic is intentionally separate from the compositor integration so it's unit-testable without the full pipeline.

- [ ] **Step 1: Write the failing test**

Create `tests/elite_studio/test_embedding_gate.py`:
```python
"""Tests for skyyrose.elite_studio.quality.embedding_gate."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from skyyrose.elite_studio.quality import embedding_gate
from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid


@pytest.fixture
def fake_centroid() -> BrandCentroid:
    rng = np.random.default_rng(42)
    raw = rng.standard_normal(512).astype(np.float32)
    centroid = raw / np.linalg.norm(raw)
    return BrandCentroid(centroid=centroid, threshold=0.65, sample_count=10, model_id="test")


@pytest.fixture
def render_image(tmp_path: Path) -> Path:
    Image.new("RGB", (224, 224), color=(30, 30, 30)).save(tmp_path / "render.png")
    return tmp_path / "render.png"


def test_score_returns_cosine_in_range(fake_centroid: BrandCentroid, render_image: Path) -> None:
    score = embedding_gate.score_against_centroid(render_image, fake_centroid)
    assert -1.0 <= score <= 1.0


def test_evaluate_accepts_when_above_threshold(fake_centroid: BrandCentroid, render_image: Path, monkeypatch) -> None:
    monkeypatch.setattr(embedding_gate, "score_against_centroid", lambda *_args, **_kw: 0.80)
    verdict = embedding_gate.evaluate(render_image, fake_centroid)
    assert verdict.accepted is True
    assert verdict.score == pytest.approx(0.80)
    assert verdict.threshold == pytest.approx(0.65)


def test_evaluate_rejects_below_threshold(fake_centroid: BrandCentroid, render_image: Path, monkeypatch) -> None:
    monkeypatch.setattr(embedding_gate, "score_against_centroid", lambda *_args, **_kw: 0.40)
    verdict = embedding_gate.evaluate(render_image, fake_centroid)
    assert verdict.accepted is False
    assert "below" in verdict.reason.lower()
```

- [ ] **Step 2: Run test to verify failure**

```bash
pytest tests/elite_studio/test_embedding_gate.py -v
```
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the implementation**

Create `skyyrose/elite_studio/quality/embedding_gate.py`:
```python
"""Pre-QA embedding gate: cosine similarity vs brand centroid.

Sits between Compositor stage 5 (shadows) and stage 6 (Gemini visual QA).
If a render's CLIP embedding is too far from the brand centroid, we mark it
failed before paying for Gemini QA. Saves ~$0.025 per rejected render.

Typical brand centroid threshold sits around 0.65-0.75. Tune via
build_brand_centroid.py --threshold-percentile.

@package SkyyRose
@since 1.1.0
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from PIL import Image

from skyyrose.core import clip_embedder
from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid


@dataclass
class GateVerdict:
    accepted: bool
    score: float
    threshold: float
    reason: str


def score_against_centroid(image: Union[Path, str, Image.Image], centroid: BrandCentroid) -> float:
    """Cosine similarity between image embedding and brand centroid."""
    embedding = clip_embedder.embed_image(image)
    return clip_embedder.cosine_similarity(embedding, centroid.centroid)


def evaluate(image: Union[Path, str, Image.Image], centroid: BrandCentroid) -> GateVerdict:
    """Decide whether `image` is on-brand enough to proceed to paid QA."""
    score = score_against_centroid(image, centroid)
    if score >= centroid.threshold:
        return GateVerdict(
            accepted=True,
            score=score,
            threshold=centroid.threshold,
            reason=f"on-brand (score {score:.3f} >= threshold {centroid.threshold:.3f})",
        )
    return GateVerdict(
        accepted=False,
        score=score,
        threshold=centroid.threshold,
        reason=f"below brand threshold (score {score:.3f} < threshold {centroid.threshold:.3f})",
    )
```

- [ ] **Step 4: Run tests, verify pass**

```bash
pytest tests/elite_studio/test_embedding_gate.py -v
```
Expected: 3/3 pass.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/quality/embedding_gate.py tests/elite_studio/test_embedding_gate.py
git commit -m "feat(quality): add embedding-based pre-QA gate"
```

---

## Task 4: Wire Embedding Gate Into Compositor Stage 5.5  &nbsp; — &nbsp; ⏸ DEFERRED

> **DEFERRED 2026-05-02. Do not execute.** `skyyrose/elite_studio/agents/compositor_agent.py` is currently a 68-line `pass_through` shell — the line-number anchors below (`:367`, `_run_pipeline`, `_visual_qa`) refer to the pre-`f25fd25d3` agent that was gutted on 2026-04-21. The replacement work is tracked in `docs/superpowers/plans/2026-05-02-compositor-agent-rebuild.md`. Once the rebuild lands, this task will be re-drafted against the new agent API (likely as a one-line `_embedding_gate()` call between `_shadows()` and `_visual_qa()` inside the rebuilt `composite()`).
>
> The design content below is preserved for historical reference and to inform the rebuild plan's grilling.

**Files (when un-deferred):**
- Modify: `skyyrose/elite_studio/agents/compositor_agent.py:367` (insert gate before Stage 6)
- Test: `tests/elite_studio/test_compositor_gate_integration.py`

We insert the gate as "Stage 5.5" — after shadows, before Gemini QA. If the gate rejects, we set qa to {status: "fail", reason: ...} and skip Gemini.

- [ ] **Step 1: Read the existing stage transition**

```bash
sed -n '350,400p' skyyrose/elite_studio/agents/compositor_agent.py
```
Confirm Stage 5 ends at line 366 (`stages_done = 5`) and Stage 6 begins at line 367 (`# Stage 6: QA`).

- [ ] **Step 2: Write the failing integration test**

Create `tests/elite_studio/test_compositor_gate_integration.py`:
```python
"""Integration test: compositor invokes embedding gate before Gemini QA."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from skyyrose.elite_studio.quality.brand_centroid import BrandCentroid


@pytest.fixture
def fake_centroid_file(tmp_path: Path) -> Path:
    from skyyrose.elite_studio.quality.brand_centroid import save_centroid
    rng = np.random.default_rng(0)
    v = rng.standard_normal(512).astype(np.float32)
    v = v / np.linalg.norm(v)
    centroid = BrandCentroid(centroid=v, threshold=0.99, sample_count=5, model_id="test")  # threshold 0.99 forces rejection
    out = tmp_path / "brand_centroid.npz"
    save_centroid(centroid, out)
    return out


def test_compositor_skips_gemini_when_gate_rejects(fake_centroid_file: Path, tmp_path: Path) -> None:
    """When the gate rejects, compositor stages QA as 'fail' without calling Gemini."""
    from skyyrose.elite_studio.agents import compositor_agent
    img = Image.new("RGB", (224, 224), color=(50, 50, 50))
    img_path = tmp_path / "shadow.png"
    img.save(img_path)

    with patch.object(compositor_agent, "_visual_qa_gemini") as mock_gemini:
        verdict = compositor_agent._maybe_apply_gate(
            shadow_path=str(img_path),
            scene_name="oakland_night",
            collection="black-rose",
            centroid_path=fake_centroid_file,
        )
        assert verdict["status"] == "fail"
        assert "below brand threshold" in verdict["reason"].lower()
        mock_gemini.assert_not_called()


def test_compositor_calls_gemini_when_gate_accepts(fake_centroid_file: Path, tmp_path: Path) -> None:
    """When the gate accepts, compositor proceeds to Gemini QA."""
    from skyyrose.elite_studio.agents import compositor_agent
    from skyyrose.elite_studio.quality.brand_centroid import load_centroid, save_centroid

    centroid = load_centroid(fake_centroid_file)
    centroid.threshold = -1.0  # force acceptance
    save_centroid(centroid, fake_centroid_file)

    img = Image.new("RGB", (224, 224), color=(50, 50, 50))
    img_path = tmp_path / "shadow.png"
    img.save(img_path)

    with patch.object(compositor_agent, "_visual_qa_gemini", return_value={"status": "pass"}) as mock_gemini:
        verdict = compositor_agent._maybe_apply_gate(
            shadow_path=str(img_path),
            scene_name="oakland_night",
            collection="black-rose",
            centroid_path=fake_centroid_file,
        )
        assert verdict["status"] == "pass"
        mock_gemini.assert_called_once()
```

- [ ] **Step 3: Run test to verify failure**

```bash
pytest tests/elite_studio/test_compositor_gate_integration.py -v
```
Expected: `AttributeError: module 'skyyrose.elite_studio.agents.compositor_agent' has no attribute '_maybe_apply_gate'`.

- [ ] **Step 4: Add the gate hook to compositor_agent.py**

In `skyyrose/elite_studio/agents/compositor_agent.py`, near the top of the module (after existing imports, line ~50), add:

```python
from skyyrose.elite_studio.quality import embedding_gate
from skyyrose.elite_studio.quality.brand_centroid import load_centroid

_DEFAULT_CENTROID_PATH = Path(__file__).parents[1] / "data" / "brand_centroid.npz"
```

Then add this private helper near the bottom of the file (before the last class/closing):

```python
def _visual_qa_gemini(*args, **kwargs):  # type: ignore[override]
    """Hook isolated for unit testing — preserves the existing Gemini path."""
    from skyyrose.elite_studio.agents.compositor_agent import CompositorAgent  # local re-import
    instance = CompositorAgent.__new__(CompositorAgent)
    return CompositorAgent._visual_qa(instance, *args, **kwargs)


def _maybe_apply_gate(
    shadow_path: str,
    scene_name: str,
    collection: str,
    centroid_path: Path | None = None,
) -> dict:
    """Run pre-QA gate. Reject -> skip Gemini. Accept -> call Gemini."""
    centroid_path = Path(centroid_path) if centroid_path else _DEFAULT_CENTROID_PATH
    if not centroid_path.exists():
        # No centroid built yet — fall through to Gemini (current behavior).
        return _visual_qa_gemini(shadow_path, scene_name, collection)

    centroid = load_centroid(centroid_path)
    verdict = embedding_gate.evaluate(shadow_path, centroid)
    if not verdict.accepted:
        return {
            "status": "fail",
            "reason": verdict.reason,
            "embedding_score": verdict.score,
            "embedding_threshold": verdict.threshold,
            "skipped_gemini": True,
        }
    return _visual_qa_gemini(shadow_path, scene_name, collection)
```

- [ ] **Step 5: Replace the Stage 6 call site**

In the `_run_pipeline` method (around line 367), replace:
```python
            # ------------------------------ Stage 6: QA
            started = time.perf_counter()
            qa = self._visual_qa(shadow_path, scene_name, collection)
```
with:
```python
            # ---------------------- Stage 5.5/6: pre-QA gate + Gemini QA
            started = time.perf_counter()
            qa = _maybe_apply_gate(shadow_path, scene_name, collection)
```

- [ ] **Step 6: Run tests, verify pass**

```bash
pytest tests/elite_studio/test_compositor_gate_integration.py -v
```
Expected: 2/2 pass.

- [ ] **Step 7: Smoke-test that existing compositor tests still pass**

```bash
pytest skyyrose/elite_studio/tests/test_compositor_agent.py -v
```
Expected: existing tests still green (gate is opt-in via the centroid file existing).

- [ ] **Step 8: Commit**

```bash
git add skyyrose/elite_studio/agents/compositor_agent.py tests/elite_studio/test_compositor_gate_integration.py
git commit -m "feat(compositor): wire embedding gate as pre-QA filter (stage 5.5)"
```

---

## Task 5: Catalog Deduplication Core

**Files:**
- Create: `skyyrose/core/catalog_dedup.py`
- Test: `tests/core/test_catalog_dedup.py`

Catches near-duplicate SKUs at intake. Uses the same browser-side embeddings JSON we already generate. Threshold 0.98 because identical-product variants (different color jerseys) score 1.000 in our actual data.

- [ ] **Step 1: Write the failing test**

Create `tests/core/test_catalog_dedup.py`:
```python
"""Tests for skyyrose.core.catalog_dedup."""
from __future__ import annotations

from pathlib import Path

import json
import numpy as np
import pytest

from skyyrose.core import catalog_dedup


def _make_embeddings_json(tmp_path: Path) -> Path:
    """Build a synthetic embeddings JSON with one duplicate pair."""
    rng = np.random.default_rng(7)
    base = rng.standard_normal(512).astype(np.float32)
    base = base / np.linalg.norm(base)

    # br-001 and br-001-twin are 0.999 similar (duplicate).
    twin = base + rng.standard_normal(512).astype(np.float32) * 0.005
    twin = twin / np.linalg.norm(twin)

    other = rng.standard_normal(512).astype(np.float32)
    other = other / np.linalg.norm(other)

    payload = {
        "model": "test",
        "dim": 512,
        "products": {
            "br-001":      {"name": "Original", "collection": "black-rose", "embedding": base.tolist()},
            "br-001-twin": {"name": "Duplicate", "collection": "black-rose", "embedding": twin.tolist()},
            "sg-001":      {"name": "Different", "collection": "signature",  "embedding": other.tolist()},
        },
    }
    out = tmp_path / "embeddings.json"
    out.write_text(json.dumps(payload))
    return out


def test_find_duplicates_detects_near_duplicate(tmp_path: Path) -> None:
    path = _make_embeddings_json(tmp_path)
    dups = catalog_dedup.find_duplicates(path, threshold=0.98)
    pairs = {(d.sku_a, d.sku_b) for d in dups}
    assert ("br-001", "br-001-twin") in pairs or ("br-001-twin", "br-001") in pairs


def test_find_duplicates_skips_below_threshold(tmp_path: Path) -> None:
    path = _make_embeddings_json(tmp_path)
    dups = catalog_dedup.find_duplicates(path, threshold=0.98)
    pairs = {tuple(sorted([d.sku_a, d.sku_b])) for d in dups}
    assert tuple(sorted(["br-001", "sg-001"])) not in pairs


def test_find_duplicates_reports_score(tmp_path: Path) -> None:
    path = _make_embeddings_json(tmp_path)
    dups = catalog_dedup.find_duplicates(path, threshold=0.98)
    assert all(d.score >= 0.98 for d in dups)
    assert all(0.98 <= d.score <= 1.0 for d in dups)
```

- [ ] **Step 2: Run test to verify failure**

```bash
pytest tests/core/test_catalog_dedup.py -v
```
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the implementation**

Create `skyyrose/core/catalog_dedup.py`:
```python
"""Catalog duplicate detector.

Scans the browser-side embeddings JSON (or any compatible payload) for SKUs
whose CLIP embedding cosine similarity exceeds a threshold. Used by
scripts/check_catalog_duplicates.py at intake to flag near-identical SKUs
before they ship.

Threshold guidance:
    >= 0.99   exact duplicates (e.g. jersey variants of the same garment)
    0.95-0.99 likely duplicates worth a human review
    < 0.95    legitimately distinct products

@package SkyyRose
@since 1.1.0
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class DuplicatePair:
    sku_a: str
    sku_b: str
    score: float
    name_a: str
    name_b: str
    collection_a: str
    collection_b: str

    def __post_init__(self) -> None:
        # Normalize order so (a, b) and (b, a) collide in sets.
        if self.sku_a > self.sku_b:
            object.__setattr__(self, "sku_a", self.sku_b)
            object.__setattr__(self, "sku_b", self.sku_a if self.sku_a == self.sku_b else self.sku_b)


def _load_embeddings(path: Path) -> tuple[list[str], np.ndarray, dict[str, dict]]:
    payload = json.loads(Path(path).read_text())
    products = payload["products"]
    skus = sorted(products.keys())
    matrix = np.stack([np.asarray(products[s]["embedding"], dtype=np.float32) for s in skus])
    return skus, matrix, products


def find_duplicates(embeddings_path: Path, threshold: float = 0.98) -> list[DuplicatePair]:
    """Find every pair of SKUs whose cosine similarity >= threshold."""
    skus, matrix, products = _load_embeddings(embeddings_path)
    sims = matrix @ matrix.T  # (N, N), already L2-normalized
    pairs: list[DuplicatePair] = []
    n = len(skus)
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sims[i, j])
            if score >= threshold:
                pairs.append(
                    DuplicatePair(
                        sku_a=skus[i],
                        sku_b=skus[j],
                        score=score,
                        name_a=products[skus[i]].get("name", ""),
                        name_b=products[skus[j]].get("name", ""),
                        collection_a=products[skus[i]].get("collection", ""),
                        collection_b=products[skus[j]].get("collection", ""),
                    )
                )
    pairs.sort(key=lambda p: -p.score)
    return pairs
```

- [ ] **Step 4: Run tests, verify pass**

```bash
pytest tests/core/test_catalog_dedup.py -v
```
Expected: 3/3 pass.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/core/catalog_dedup.py tests/core/test_catalog_dedup.py
git commit -m "feat(core): add catalog duplicate detector"
```

---

## Task 6: Catalog Dedup CLI

**Files:**
- Create: `scripts/check_catalog_duplicates.py`
- Test: `tests/scripts/test_check_catalog_duplicates.py`

CLI wrapper. Exit code 1 if duplicates found above the threshold — fits naturally as a pre-commit hook on catalog CSV changes.

- [ ] **Step 1: Write the failing test**

Create `tests/scripts/test_check_catalog_duplicates.py`:
```python
"""Smoke test for scripts/check_catalog_duplicates.py CLI."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "check_catalog_duplicates.py"


def _build_synthetic(tmp_path: Path, with_duplicate: bool) -> Path:
    rng = np.random.default_rng(11)
    a = rng.standard_normal(512).astype(np.float32); a /= np.linalg.norm(a)
    b = a + rng.standard_normal(512).astype(np.float32) * (0.005 if with_duplicate else 1.0)
    b /= np.linalg.norm(b)
    payload = {
        "model": "t", "dim": 512,
        "products": {
            "x-1": {"name": "X", "collection": "c", "embedding": a.tolist()},
            "x-2": {"name": "Y", "collection": "c", "embedding": b.tolist()},
        },
    }
    p = tmp_path / "embeddings.json"
    p.write_text(json.dumps(payload))
    return p


def test_cli_exits_zero_when_no_duplicates(tmp_path: Path) -> None:
    embeds = _build_synthetic(tmp_path, with_duplicate=False)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--embeddings", str(embeds), "--threshold", "0.98"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert result.returncode == 0
    assert "no duplicates" in result.stdout.lower()


def test_cli_exits_one_when_duplicates_found(tmp_path: Path) -> None:
    embeds = _build_synthetic(tmp_path, with_duplicate=True)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--embeddings", str(embeds), "--threshold", "0.98"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert result.returncode == 1
    assert "x-1" in result.stdout and "x-2" in result.stdout
```

- [ ] **Step 2: Run test to verify failure**

```bash
pytest tests/scripts/test_check_catalog_duplicates.py -v
```
Expected: `FileNotFoundError` or non-zero exit.

- [ ] **Step 3: Write the CLI**

Create `scripts/check_catalog_duplicates.py`:
```python
#!/usr/bin/env python3
"""Detect near-duplicate SKUs by CLIP embedding similarity.

Usage:
    python3 scripts/check_catalog_duplicates.py \\
        --embeddings wordpress-theme/skyyrose-flagship/data/product-embeddings.json \\
        --threshold 0.98

Exits 0 if no duplicates found, 1 if duplicates exist (suitable for CI/pre-commit).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skyyrose.core.catalog_dedup import find_duplicates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embeddings", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.98)
    args = parser.parse_args()

    if not args.embeddings.exists():
        print(f"FATAL: embeddings file not found: {args.embeddings}", file=sys.stderr)
        return 2

    duplicates = find_duplicates(args.embeddings, threshold=args.threshold)

    if not duplicates:
        print(f"OK — no duplicates above threshold {args.threshold}")
        return 0

    print(f"FOUND {len(duplicates)} duplicate pair(s) at threshold {args.threshold}:")
    for d in duplicates:
        print(f"  {d.score:.4f}  {d.sku_a:<14} [{d.collection_a:<12}] {d.name_a}")
        print(f"           {d.sku_b:<14} [{d.collection_b:<12}] {d.name_b}")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests, verify pass**

```bash
pytest tests/scripts/test_check_catalog_duplicates.py -v
```
Expected: 2/2 pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/check_catalog_duplicates.py tests/scripts/test_check_catalog_duplicates.py
git commit -m "feat(scripts): add catalog duplicate detector CLI"
```

---

## Task 7: CLIP Text-to-Image Alignment Scorer

**Files:**
- Create: `skyyrose/elite_studio/quality/clip_alignment.py`
- Test: `tests/elite_studio/test_clip_alignment.py`

The killer feature: objective prompt-fidelity scoring. CLIP's text and image encoders share an embedding space, so cosine similarity between `embed_text(prompt)` and `embed_image(render)` measures alignment.

- [ ] **Step 1: Write the failing test**

Create `tests/elite_studio/test_clip_alignment.py`:
```python
"""Tests for skyyrose.elite_studio.quality.clip_alignment."""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from skyyrose.elite_studio.quality import clip_alignment


@pytest.fixture
def red_circle_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (224, 224), color="white")
    draw = ImageDraw.Draw(img)
    draw.ellipse((40, 40, 184, 184), fill="red")
    p = tmp_path / "red_circle.png"
    img.save(p)
    return p


def test_score_alignment_returns_float_in_range(red_circle_image: Path) -> None:
    score = clip_alignment.score_alignment("a red circle on a white background", red_circle_image)
    assert -1.0 <= score <= 1.0


def test_aligned_prompt_scores_higher_than_misaligned(red_circle_image: Path) -> None:
    aligned = clip_alignment.score_alignment("a red circle on a white background", red_circle_image)
    misaligned = clip_alignment.score_alignment("a green triangle on a black background", red_circle_image)
    assert aligned > misaligned


def test_score_batch_returns_one_score_per_prompt(red_circle_image: Path) -> None:
    scores = clip_alignment.score_alignment_batch(
        ["a red circle", "a red shape", "a blue square"],
        red_circle_image,
    )
    assert len(scores) == 3
    assert scores[0] >= scores[2]  # red circle prompt closer to red circle than blue square
```

- [ ] **Step 2: Run test to verify failure**

```bash
pytest tests/elite_studio/test_clip_alignment.py -v
```
Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Write the implementation**

Create `skyyrose/elite_studio/quality/clip_alignment.py`:
```python
"""CLIP text-to-image alignment scoring.

Quantifies "did this render match the prompt?" objectively. CLIP's text and
image encoders share a 512-d embedding space; cosine similarity between
embed_text(prompt) and embed_image(render) is the alignment score.

Typical scores:
    > 0.30   strong alignment
    0.20-0.30 moderate alignment (typical for well-prompted Stable Diffusion / FLUX)
    < 0.20   weak alignment, prompt mostly ignored

Use as a post-render gate in nano-banana and as a tiebreaker in the 3D
round-table judging.

@package SkyyRose
@since 1.1.0
"""
from __future__ import annotations

from pathlib import Path
from typing import Union

from PIL import Image

from skyyrose.core import clip_embedder


def score_alignment(prompt: str, image: Union[Path, str, Image.Image]) -> float:
    """Cosine similarity between prompt and image embeddings."""
    text_vec = clip_embedder.embed_text(prompt)
    image_vec = clip_embedder.embed_image(image)
    return clip_embedder.cosine_similarity(text_vec, image_vec)


def score_alignment_batch(prompts: list[str], image: Union[Path, str, Image.Image]) -> list[float]:
    """Score multiple prompts against the same image. Embeds image once."""
    image_vec = clip_embedder.embed_image(image)
    return [
        clip_embedder.cosine_similarity(clip_embedder.embed_text(p), image_vec)
        for p in prompts
    ]
```

- [ ] **Step 4: Run tests, verify pass**

```bash
pytest tests/elite_studio/test_clip_alignment.py -v
```
Expected: 3/3 pass.

- [ ] **Step 5: Commit**

```bash
git add skyyrose/elite_studio/quality/clip_alignment.py tests/elite_studio/test_clip_alignment.py
git commit -m "feat(quality): add CLIP text-to-image alignment scorer"
```

---

## Task 8: Wire Alignment Scoring Into Nano Banana

**Files:**
- Modify: `scripts/nano_banana/cli.py` (add `--score-alignment` flag and post-render scoring)
- Test: extend the existing nano-banana test if one exists; otherwise add minimal smoke test

- [ ] **Step 1: Inspect the nano-banana cmd_generate function**

```bash
sed -n '60,120p' scripts/nano_banana/cli.py
```
Identify where `cmd_generate` writes outputs and where to insert the alignment scoring call.

- [ ] **Step 2: Add the alignment scoring helper**

In `scripts/nano_banana/cli.py`, after the imports, add:
```python
def _score_render_alignment(prompt: str, render_path: str) -> dict:
    """Score a generated render against its prompt. Returns logging dict."""
    from skyyrose.elite_studio.quality.clip_alignment import score_alignment
    score = score_alignment(prompt, render_path)
    return {
        "render_path": render_path,
        "prompt": prompt[:120],
        "alignment_score": round(score, 4),
        "verdict": "strong" if score >= 0.30 else "moderate" if score >= 0.20 else "weak",
    }
```

- [ ] **Step 3: Add the flag to the CLI parser**

Find the `cmd_generate` argparser setup and add:
```python
parser.add_argument(
    "--score-alignment",
    action="store_true",
    help="Score each render's CLIP alignment vs prompt and write to audit log",
)
```

- [ ] **Step 4: Call scoring after each render is written**

In `cmd_generate`, after each render path is produced, add:
```python
if args.score_alignment:
    alignment = _score_render_alignment(prompt_text, render_path)
    print(f"  alignment: {alignment['alignment_score']:.3f} ({alignment['verdict']})")
    audit_entries.append(alignment)
```

(Adapt variable names — `prompt_text`, `render_path`, `audit_entries` — to whatever the existing function uses; replace if names differ.)

- [ ] **Step 5: Write a smoke test**

Create `tests/scripts/test_nano_banana_alignment.py`:
```python
"""Smoke test: nano-banana --score-alignment writes scores to stdout."""
from __future__ import annotations

import subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_help_lists_score_alignment_flag() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "nano-banana-run.py"), "generate", "--help"],
        capture_output=True, text=True, cwd=str(REPO),
    )
    assert "--score-alignment" in result.stdout
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/scripts/test_nano_banana_alignment.py -v
```
Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add scripts/nano_banana/cli.py tests/scripts/test_nano_banana_alignment.py
git commit -m "feat(nano-banana): add --score-alignment for post-render CLIP scoring"
```

---

## Task 9: Wire Alignment Into 3D Round-Table Judging  &nbsp; — &nbsp; ✅ ALREADY IMPLEMENTED

> **OBSOLETE 2026-05-02. Do not execute.** `orchestration/threed_round_table.py:293` already defines `ThreeDQualityScores` with `clip_alignment_score: float = 0.0` at weight 0.20, with the original six metrics proportionally rebalanced to 0.80. The docstring documents the math. The plan's specified field names (`mesh_topology_score`, `texture_quality_score`, `file_format_score`, `uv_quality_score`) do not match the actual field names (`geometry_quality`, `texture_quality`, `polycount_efficiency`, `file_format_score`, `generation_speed`, `web_readiness`) — so the test as written would crash on import.
>
> **Replacement work (when needed):** verify the existing implementation actually receives a non-zero `clip_alignment_score` from upstream judge code. Search for `ThreeDQualityScores(` constructor calls and confirm at least one judge populates the field; if every judge passes the default 0.0, the field exists but is dead weight. That verification belongs in a separate "round-table alignment-score liveness" task, not in this plan.
>
> The design content below is preserved for historical reference.

**Files:**
- Modify: `orchestration/threed_round_table.py` (add `clip_alignment_score` field, integrate into total)
- Test: extend the existing 3D round-table test

- [ ] **Step 1: Read the existing scoring class**

```bash
sed -n '290,330p' orchestration/threed_round_table.py
```
Locate `ThreeDQualityScores`. Confirm the existing weighted total at line ~306-315.

- [ ] **Step 2: Write the failing test**

Create `tests/orchestration/test_threed_round_table_alignment.py`:
```python
"""Tests for 3D round-table CLIP alignment scoring."""
from __future__ import annotations

import pytest

from orchestration.threed_round_table import ThreeDQualityScores


def test_clip_alignment_score_field_exists() -> None:
    s = ThreeDQualityScores(clip_alignment_score=0.35)
    assert s.clip_alignment_score == pytest.approx(0.35)


def test_clip_alignment_contributes_to_total() -> None:
    high = ThreeDQualityScores(clip_alignment_score=0.40, file_format_score=80, mesh_topology_score=80, texture_quality_score=80)
    low = ThreeDQualityScores(clip_alignment_score=0.05, file_format_score=80, mesh_topology_score=80, texture_quality_score=80)
    assert high.total > low.total
```

- [ ] **Step 3: Run test to verify failure**

```bash
pytest tests/orchestration/test_threed_round_table_alignment.py -v
```
Expected: `TypeError: ThreeDQualityScores got an unexpected keyword argument 'clip_alignment_score'` or similar.

- [ ] **Step 4: Add the field**

In `orchestration/threed_round_table.py`, find the `ThreeDQualityScores` dataclass and add:
```python
clip_alignment_score: float = 0.0  # 0..1, prompt-image CLIP cosine similarity
```

Then update the `total` property to include it. Replace the existing weighted formula with:
```python
@property
def total(self) -> float:
    """Weighted total score (0-100)."""
    base_score = (
        self.mesh_topology_score * 0.35
        + self.texture_quality_score * 0.25
        + self.file_format_score * 0.10
        + self.clip_alignment_score * 100.0 * 0.20  # scale 0..1 to 0..100, weight 0.20
        + self.uv_quality_score * 0.10
    )
    return min(base_score + self.enhancement_bonus, 100.0)
```

(Adjust other weights if they no longer sum to 1.0 — the original sum minus 0.20 should cover the rebalance.)

- [ ] **Step 5: Run tests, verify pass**

```bash
pytest tests/orchestration/test_threed_round_table_alignment.py -v
```
Expected: 2/2 pass.

- [ ] **Step 6: Smoke-test existing round-table tests**

```bash
pytest orchestration/ tests/ -k threed_round_table -v
```
Expected: existing tests pass (0.0 alignment default = no behavior change for existing fixtures).

- [ ] **Step 7: Commit**

```bash
git add orchestration/threed_round_table.py tests/orchestration/test_threed_round_table_alignment.py
git commit -m "feat(round-table): add CLIP alignment score to 3D quality judging"
```

---

## Final verification

- [ ] **Step 1: Run the full new-code test suite**

```bash
pytest tests/elite_studio/ tests/core/test_catalog_dedup.py tests/scripts/test_check_catalog_duplicates.py tests/scripts/test_nano_banana_alignment.py tests/orchestration/test_threed_round_table_alignment.py -v
```
Expected: all green.

- [ ] **Step 2: Run linter and formatter**

```bash
ruff check skyyrose/core/clip_embedder.py skyyrose/elite_studio/quality/ skyyrose/core/catalog_dedup.py scripts/ tests/elite_studio/ tests/core/test_catalog_dedup.py tests/scripts/ --fix
black skyyrose/core/clip_embedder.py skyyrose/elite_studio/quality/ skyyrose/core/catalog_dedup.py scripts/check_catalog_duplicates.py scripts/build_brand_centroid.py
```

- [ ] **Step 3: Build the actual brand centroid (optional dry-run)**

```bash
python3 scripts/build_brand_centroid.py \
  --approved-dir wordpress-theme/skyyrose-flagship/assets/images/products \
  --output skyyrose/elite_studio/data/brand_centroid.npz \
  --threshold-percentile 10
```

- [ ] **Step 4: Run actual catalog dedup against shipped embeddings**

```bash
python3 scripts/check_catalog_duplicates.py \
  --embeddings wordpress-theme/skyyrose-flagship/data/product-embeddings.json \
  --threshold 0.98
```

This will surface the `br-003` jersey-variant cluster (expected — those are real near-duplicates).

- [ ] **Step 5: Final commit**

```bash
git add skyyrose/elite_studio/data/brand_centroid.npz
git commit -m "feat(quality): build brand centroid from approved hero shots"
```
