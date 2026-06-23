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
