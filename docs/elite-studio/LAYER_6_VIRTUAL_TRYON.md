# Layer 6 — Virtual Try-On

Elite Studio Layer 6 adds optional virtual try-on to the image production
pipeline. It is **disabled by default** — zero cost and zero latency impact
when unused.

## What it does

After the quality-control step (and optional compositing), the try-on node
places the generated garment onto a fashion model using the FASHN API. The
output is saved alongside the standard renders as:

```
skyyrose/assets/images/products/<sku>/tryon/<sku>-tryon-<timestamp>.jpg
```

The result is reported in `ProductionResult.tryon` (a `TryOnResult` dataclass).
A failed try-on sets `tryon.success = False` and populates `tryon.error`, but
**never causes the main job to fail**.

## How to enable

### CLI

```bash
# Requires --graph to use the LangGraph engine
python -m skyyrose.elite_studio produce br-001 --graph --tryon
```

### Python API

```python
from skyyrose.elite_studio.graph import GraphConfig, run_single

config = GraphConfig(
    enable_tryon=True,
    tryon_category="upper_body",   # optional, default: upper_body
)
result = run_single(sku="br-001", view="front", config=config)

if result.tryon and result.tryon.success:
    print(result.tryon.output_path)
```

## FASHN API key setup

Set the environment variable before running:

```bash
export FASHN_API_KEY="your-key-here"
```

Or add it to the project `.env` file at the repo root:

```
FASHN_API_KEY=your-key-here
```

Get an API key at: https://fashn.ai/dashboard

Pricing: ~$0.075 per image (pay-as-you-go as of 2025).

## Supported garment categories

Pass via `tryon_category` in `GraphConfig` or the underlying `TryOnAgent`:

| Elite Studio value | FASHN value  | Use for                        |
|--------------------|--------------|--------------------------------|
| `upper_body`       | `tops`       | Shirts, hoodies, crewnecks     |
| `tops`             | `tops`       | Same as upper_body             |
| `lower_body`       | `bottoms`    | Joggers, shorts, sweatpants    |
| `bottoms`          | `bottoms`    | Same as lower_body             |
| `dresses`          | `dresses`    | Full dresses                   |
| `outerwear`        | `outerwear`  | Jackets, sherpa, varsity       |
| `full_body`        | `full_body`  | Full outfits, sets             |

## Output location

```
skyyrose/assets/images/products/
└── <sku>/
    └── tryon/
        └── <sku>-tryon-20260406_120000.jpg
```

## Architecture

```
GraphConfig(enable_tryon=True)
        │
   build_graph()
        │
   quality_node → [compositor_node →] tryon_node → finalize_node
                                            │
                                       TryOnAgent.try_on()
                                            │
                                  agents/fashn_agent.py
                                  FashnTryOnAgent._tool_virtual_tryon()
                                            │
                                       FASHN API
```

The `TryOnAgent` is a thin synchronous wrapper that:
1. Resolves the garment image from `OUTPUT_DIR/<sku>/`
2. Calls `FashnTryOnAgent._tool_virtual_tryon()` via `asyncio.run()`
3. Copies the FASHN output to the canonical Elite Studio path
4. Returns a frozen `TryOnResult` dataclass

## Error handling

All exceptions from the FASHN agent are caught inside `TryOnAgent.try_on()`.
Errors are logged at `WARNING` level and returned as:

```python
TryOnResult(success=False, error="<message>", latency_s=<elapsed>)
```

The main graph job always proceeds to `finalize_node` regardless.
