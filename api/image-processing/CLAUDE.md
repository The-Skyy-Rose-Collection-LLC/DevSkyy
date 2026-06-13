# api/image-processing/ — Isolated TypeScript image enhancer (legacy spike)

Single file `luxury-enhance.ts` — a Node/TS class `LuxuryImageProcessor` that composes `sharp` + `@fal-ai/serverless-client` + `replicate` for product image cleanup (bg removal, upscale, luxury filter, format conversion).

## Key files

- `luxury-enhance.ts` — `LuxuryImageProcessor.enhanceProductImage(buffer, options)` returning `EnhancedImage` (buffer + metadata + timing).

## Status

This is the only TypeScript file in the otherwise Python `api/` tree and the only file in this subdir. It is NOT mounted into the FastAPI app and has no Python wrapper. Treat as a legacy spike, not active production code. The Python equivalents that actually ship live in `agents/core/imagery/` and `skyyrose/elite_studio/`.

## Conventions

- If reviving: port to Python and route through an agent. Direct TS in the API tree breaks the language-uniformity invariant of `api/`.
- Provider API keys read from `REPLICATE_API_TOKEN` and `FAL_KEY` env vars. Both are also used by the Python imagery path (`agents/core/imagery/`) — don't duplicate secrets.

## Don't

- Don't add new TypeScript files here. The dashboard's TS lives in `frontend/`; the API is Python-only.
- Don't call `fal` or `replicate` from this file in any new code — those are paid APIs and any new dispatch path must route through `agents/core/imagery/` so the STOP-AND-SHOW gate and cost telemetry apply.
- Don't import this module from Python. There is no functional bridge; pretending one exists wastes a debugging cycle.

## Related

- Python imagery hub: `agents/core/imagery/`
- Elite Studio (canonical imagery pipeline): `skyyrose/elite_studio/`
- Dashboard TS code: `frontend/`
