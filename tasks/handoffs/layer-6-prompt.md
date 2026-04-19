# Elite Studio Layer 6 — Virtual Try-On

## Context

You are working in the `elite/layer-6-virtual-tryon` branch (worktree at `../elite-layer-6`).

Layers 1-5 are merged. Your job is to integrate virtual try-on as an optional parallel graph branch.

**Pre-reads (do these first):**
- `api/virtual_tryon.py` — full FASHN API client (59KB) — DO NOT rewrite, wrap it
- `skyyrose/elite_studio/graph/builder.py` — topology to extend with parallel branch
- `skyyrose/elite_studio/graph/nodes.py` — node pattern to follow
- `skyyrose/elite_studio/graph/state.py` — state to extend
- `skyyrose/elite_studio/models.py` — frozen dataclasses to extend
- `api/v1/elite_studio.py` (Layer 5) — REST endpoint to extend with `enable_tryon`

---

## Goal

After quality passes, try-on runs in parallel with the compositor (if enabled). Both complete before finalize. The try-on result is stored in state and returned in `ProductionResult`.

Final topology:
```
vision → [enrichment?] → generator → [safety?] → quality
quality → [retry?] → generator
quality → [proceed] → compositor (if enabled) ──────────────┐
                   → tryon (if enabled) ────────────────────┤
                   → variants (if enabled, Layer 2) ────────┤
                                                             ↓
                                                          finalize
```

LangGraph supports fan-out/fan-in natively. Use `add_node` + multiple edges from quality to compositor + tryon, then both feed into finalize.

---

## New Agent: `skyyrose/elite_studio/agents/tryon_agent.py`

```python
class TryOnAgent:
    """Wraps the existing FASHN virtual try-on client."""

    def try_on(
        self,
        sku: str,
        garment_image_path: str,
        model_image_path: str,
        category: str = "upper_body",
    ) -> TryOnResult:
        """Run virtual try-on. Returns TryOnResult."""
```

Implementation:
- Import `FASHNClient` from `api/virtual_tryon.py` (DO NOT copy-paste — import it)
- Use `FASHNClient.run_tryon()` or equivalent method (read virtual_tryon.py to find the right method)
- Save output to `{OUTPUT_DIR}/{sku}/tryon/{sku}-tryon-{timestamp}.jpg`
- Wrap all exceptions: return `TryOnResult(success=False, error=str(e))` on failure

---

## New Model: add to `skyyrose/elite_studio/models.py`

```python
@dataclass(frozen=True)
class TryOnResult:
    success: bool
    output_path: str = ""
    garment_sku: str = ""
    model_image_path: str = ""
    provider: str = "fashn"
    latency_s: float = 0.0
    error: str = ""
```

Also update `ProductionResult`:
```python
# Add to ProductionResult:
tryon: TryOnResult | None = None
```

---

## State Fields to Add (`graph/state.py`)

```python
tryon_result: TryOnResult | None
```

---

## GraphConfig Fields to Add (`graph/builder.py`)

```python
enable_tryon: bool = False
tryon_category: str = "upper_body"   # "upper_body", "lower_body", "dresses"
```

---

## Graph Node: `graph/nodes.py`

```python
def tryon_node(state: EliteStudioState) -> dict:
    """Run virtual try-on in parallel with compositor."""
    start = time.monotonic()

    gen = state.get("generation_result")
    if not gen or not gen.success:
        # No generated image — skip silently
        timings = dict(state.get("stage_timings", {}))
        timings["tryon"] = 0.0
        return {"tryon_result": None, "stage_timings": timings}

    agent = TryOnAgent()
    # Garment image = source product image for this SKU
    garment_path = _find_garment_image(state["sku"])  # helper: search PRODUCT_IMAGES_DIR
    result = agent.try_on(
        sku=state["sku"],
        garment_image_path=garment_path or gen.output_path,
        model_image_path=gen.output_path,
    )
    elapsed = time.monotonic() - start
    timings = dict(state.get("stage_timings", {}))
    timings["tryon"] = round(elapsed, 2)
    return {"tryon_result": result, "stage_timings": timings}
```

---

## Updated Graph Topology (`graph/builder.py`)

When `enable_tryon=True`, add `tryon` as a node, route from `quality` to `tryon` alongside compositor:

```python
# Fan-out from quality: compositor + tryon run in parallel
# LangGraph handles this via multiple conditional edge destinations
graph.add_conditional_edges(
    _QUALITY,
    after_quality,
    {
        _GENERATOR: _GENERATOR,
        _COMPOSITOR: _COMPOSITOR,
        _TRYON: _TRYON,
        _FINALIZE: _FINALIZE,
    },
)
graph.add_edge(_TRYON, _FINALIZE)  # tryon always goes to finalize
```

Note: True parallel fan-out in LangGraph requires `Send` API or multiple conditional outputs. Read the LangGraph docs for the current approach — the simplest correct implementation is preferred over complex parallelism if LangGraph's version doesn't support it cleanly. Sequential tryon → finalize is acceptable.

---

## CLI Update (`cli.py`)

Add to `produce` command:
```bash
python -m skyyrose.elite_studio produce br-001 --graph --tryon
```

```python
p_produce.add_argument("--tryon", action="store_true", help="Run virtual try-on")
```

In `_run_graph()`: pass `enable_tryon=args.tryon` to `GraphConfig`.

---

## API Update (`api/v1/elite_studio.py`, Layer 5)

Add to `ProduceRequest`:
```python
enable_tryon: bool = False
tryon_category: str = "upper_body"
```

Pass to `GraphConfig` when building the graph for sync jobs, or to `EliteStudioJobData` for async jobs.

---

## Tests to Create

| File | Covers |
|------|--------|
| `tests/test_tryon_agent.py` | try_on() with mock FASHN client |
| `tests/test_graph_nodes_tryon.py` | tryon_node with missing gen, successful gen |
| `tests/test_graph_builder_tryon.py` | Graph with enable_tryon=True includes tryon node |

---

## Doc to Create

`docs/elite-studio/LAYER_6_VIRTUAL_TRYON.md`:
- What try-on does
- How to enable: `--tryon` CLI flag, `enable_tryon: true` API field
- FASHN API key setup (env var `FASHN_API_KEY`)
- Supported garment categories
- Output location

---

## Standards

- Try-on disabled by default — zero cost impact when unused
- FASHN client errors must not fail the main job — try-on is additive
- Garment image not found: log warning, use generated model image as garment (best-effort)
- Files: <800 lines, functions <50 lines
- `pytest skyyrose/elite_studio/tests/ -v` — all tests pass

---

## Verification

1. `pytest skyyrose/elite_studio/tests/ -v` — all Layer 1-6 tests pass
2. `python -m skyyrose.elite_studio produce br-001 --graph` — no try-on (disabled by default)
3. `python -m skyyrose.elite_studio produce br-001 --graph --tryon` — try-on runs, output path in result
4. `POST /api/v1/elite-studio/produce` with `enable_tryon: true` — job includes try-on
5. `ProductionResult.tryon` is populated when `enable_tryon=True` and FASHN API responds
