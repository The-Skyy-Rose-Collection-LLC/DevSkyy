# Elite Studio Layer 4 — Quality System

## Context

You are working in the `elite/layer-4-quality-system` branch (worktree at `../elite-layer-4`).

Layers 1, 2, 3 are already merged. Your job is to build an advanced quality system: ML-based classifier, human-in-the-loop review, visual regression testing, and load testing.

**Pre-reads (do these first):**
- `skyyrose/elite_studio/agents/quality_agent.py` — existing Claude Sonnet QC to augment
- `skyyrose/elite_studio/graph/nodes.py` — `quality_node` to replace
- `skyyrose/elite_studio/graph/edges.py` — add `should_escalate_to_human` edge
- `services/approval_queue_manager.py` — existing human review queue to integrate
- `skyyrose/elite_studio/graph/builder.py` — topology to extend

---

## Goal

Dual-layer QC: ML classifier (fast, cheap) → Claude Sonnet (if confidence low) → Human review (if still ambiguous). Visual regression catches regressions. Load tester identifies bottlenecks.

---

## New Package: `skyyrose/elite_studio/quality/`

### `__init__.py`
Exports: `QualityClassifier`, `HumanReviewGate`, `VisualRegressionTester`, `PipelineLoadTester`

### `ml_classifier.py`
```python
class QualityClassifier:
    """CLIP-based fast quality predictor."""

    def predict(self, image_path: str) -> ClassifierResult:
        """Score image quality 0.0-1.0. Fast (no LLM needed)."""
```

`ClassifierResult` (frozen dataclass):
```python
@dataclass(frozen=True)
class ClassifierResult:
    success: bool
    score: float = 0.0          # 0.0 = definitely fail, 1.0 = definitely pass
    confidence: float = 0.0     # how confident the classifier is
    label: str = ""             # "pass", "fail", "uncertain"
    error: str = ""
```

Implementation:
- Use `transformers` library: `CLIPModel` + `CLIPProcessor` from `openai/clip-vit-base-patch32`
- Candidate labels: `["high quality fashion photo", "low quality blurry photo", "inappropriate content"]`
- If `transformers` not installed: fall back to mock that returns `ClassifierResult(success=True, score=0.5, confidence=0.3, label="uncertain")`
- Cache model with `@lru_cache` (load once per process)

### `human_review.py`
```python
class HumanReviewGate:
    """Pauses graph for human approval using the existing approval queue."""

    def submit_for_review(self, sku: str, image_path: str, job_id: str) -> str:
        """Submit image for review. Returns review_id."""

    def get_decision(self, review_id: str, timeout: float = 300.0) -> ReviewDecision:
        """Poll for human decision. Returns approve/reject/timeout."""
```

`ReviewDecision` (frozen dataclass):
```python
@dataclass(frozen=True)
class ReviewDecision:
    review_id: str
    decision: str  # "approve", "reject", "timeout"
    reviewer: str = ""
    notes: str = ""
```

Integration: Uses `services/approval_queue_manager.py`'s `submit_item()` and `get_result()`. If approval queue is unavailable, default to `approve` with a warning log.

### `visual_regression.py`
```python
class VisualRegressionTester:
    """SSIM comparison against golden reference images."""

    def compare(self, generated_path: str, sku: str) -> RegressionResult:
        """Compare against golden reference. Pass if SSIM >= 0.85."""

    def set_golden(self, sku: str, image_path: str) -> None:
        """Store an image as the new golden reference for a SKU."""
```

`RegressionResult` (frozen dataclass):
```python
@dataclass(frozen=True)
class RegressionResult:
    success: bool
    sku: str
    ssim_score: float = 0.0      # 0.0-1.0
    passed: bool = False          # True if ssim_score >= threshold
    threshold: float = 0.85
    has_reference: bool = False   # False = no golden to compare against
    report_path: str = ""         # HTML side-by-side report
    error: str = ""
```

Implementation:
- Use `scikit-image` (`skimage.metrics.structural_similarity`)
- Golden references stored at: `skyyrose/elite_studio/assets/golden/{sku}/reference.jpg`
- Generate HTML report: side-by-side images + SSIM score + pass/fail badge
- If no golden reference: return `RegressionResult(success=True, has_reference=False, passed=True)`

### `load_tester.py`
```python
class PipelineLoadTester:
    """Stress test the graph pipeline with concurrent mock runs."""

    def run(
        self,
        skus: list[str],
        concurrency: int = 4,
        iterations: int = 1,
    ) -> LoadTestReport:
        """Run pipeline with mock agents, measure throughput + latency."""
```

`LoadTestReport` (frozen dataclass):
```python
@dataclass(frozen=True)
class LoadTestReport:
    total_jobs: int
    successful: int
    failed: int
    throughput_per_min: float
    p50_latency_s: float
    p95_latency_s: float
    p99_latency_s: float
    bottleneck_stage: str          # stage with highest avg latency
    cost_per_sku_usd: float
    stage_latencies: dict[str, float]  # avg latency per stage
```

Implementation:
- Use `concurrent.futures.ThreadPoolExecutor`
- Mock all agents (return instant results)
- Measure wall-clock time per job and per stage
- Derive bottleneck from stage_timings in final state

---

## Graph Changes

### `graph/nodes.py` — update `quality_node`
```python
def quality_node(state: EliteStudioState) -> dict:
    # 1. Run ML classifier (fast)
    # 2. If confidence >= 0.8: use classifier decision
    # 3. If confidence < 0.8: run existing QualityAgent (Claude Sonnet)
    # 4. Return quality_result + classifier_result
```

Add new node:
```python
def human_review_node(state: EliteStudioState) -> dict:
    # Submit to HumanReviewGate
    # Pause and poll for decision
    # Return human_review_result
```

### `graph/edges.py` — add edge
```python
def after_quality_v2(state: EliteStudioState) -> str:
    # New: if QC confidence < threshold → "human_review"
    # Existing: if regenerate + retries left → "generator"
    # Existing: compositor or finalize
```

### `graph/builder.py` — extend GraphConfig + topology
```python
# New GraphConfig fields:
enable_human_review: bool = False
review_confidence_threshold: float = 0.6  # below this → escalate to human
enable_visual_regression: bool = False
```

Updated topology:
```
quality → [confidence < threshold AND enable_human_review] → human_review → [approve] → finalize/compositor
                                                                           → [reject] → generator (retry)
quality → [regenerate + retries left] → generator
quality → [proceed] → compositor or finalize
```

---

## New State Fields (`graph/state.py`)
```python
classifier_result: ClassifierResult | None
human_review_result: ReviewDecision | None
regression_result: RegressionResult | None
```

---

## Tests to Create

| File | Covers |
|------|--------|
| `tests/test_quality_classifier.py` | predict() with mock CLIP, fallback behavior |
| `tests/test_human_review.py` | submit + poll cycle (mock approval queue) |
| `tests/test_visual_regression.py` | compare with golden ref, no-ref path, report generation |
| `tests/test_load_tester.py` | run with mocked graph, verify report fields |
| `tests/test_graph_nodes_quality.py` | dual-QC logic: classifier pass, classifier uncertain → LLM |

---

## Standards

- `transformers` and `scikit-image` optional dependencies — graceful fallback if missing
- Human review timeout defaults to `approve` (never block production indefinitely)
- All new dataclasses: `@dataclass(frozen=True)`
- Files: <800 lines, functions <50 lines
- Run: `pytest skyyrose/elite_studio/tests/ -v` — all passing

---

## Verification

1. `pytest skyyrose/elite_studio/tests/ -v` — all tests pass
2. `QualityClassifier().predict("/path/to/image.jpg")` — returns ClassifierResult with score
3. `VisualRegressionTester().compare(path, "br-001")` — returns RegressionResult (no-ref path)
4. `PipelineLoadTester().run(["br-001","br-002"], concurrency=2)` — prints throughput report
5. Graph with `enable_human_review=True` pauses at review node when confidence low
