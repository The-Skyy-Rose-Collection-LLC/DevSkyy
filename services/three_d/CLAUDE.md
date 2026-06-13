# services/three_d/ — 3D Provider Abstraction (US-017)

**Protocol-based 3D provider layer with automatic failover.** Unifies Replicate, Tripo3D, HuggingFace, Gemini (image gen), TRELLIS under one `I3DProvider` interface.

## Public Surface (`services/three_d/__init__.py`)

| Group | Symbols | Source |
|-------|---------|--------|
| Interface | `I3DProvider`, `ThreeDRequest`, `ThreeDResponse`, `ProviderHealth`, `ProviderStatus`, `ThreeDCapability` | `provider_interface.py` |
| Errors | `ThreeDProviderError`, `ThreeDGenerationError`, `ThreeDTimeoutError` | `provider_interface.py` |
| Factory | `ThreeDProviderFactory`, `get_provider_factory()` | `provider_factory.py` |
| Optional | `GeminiImageProvider` (None if `google-genai` missing) | `gemini_provider.py` |

## Provider Implementations

| Provider | File | Notes |
|----------|------|-------|
| Replicate | `replicate_provider.py` | Used for InstantMesh / TripoSR via Replicate API |
| Tripo3D | `tripo_provider.py` | Direct Tripo3D API (`.ai` and `.com` are separate regions with separate keys — see brand memory) |
| HuggingFace | `huggingface_provider.py` | HF Spaces fallback for TRELLIS |
| Gemini | `gemini_provider.py` | Nano Banana Pro — **image gen, not 3D** (used for reference imagery in pipeline) |
| TRELLIS | `trellis/` subpackage | Microsoft Structured 3D Latents — clothing-specialized |

## Hard Rules

- **All 3D dispatch through `ThreeDProviderFactory`** — never instantiate provider clients directly. Factory handles failover, health checks, capability routing
- `get_provider_factory()` is a **process-level singleton** — tests must reset or mock at the protocol layer
- **`GeminiImageProvider` is optional** — guard against `None` (`__init__.py:34-38`). If `google-genai` not installed, Gemini is unavailable; factory must skip it in capability routing
- **STOP-AND-SHOW gate** — every paid 3D call (Replicate, Tripo, FASHN, Meshy) surfaces SKU + cost before dispatch per CLAUDE.md money/production protocol
- Tripo multi-account: `.ai` and `.com` are separate regions with separate API keys — never reuse one key across regions
- `ProviderHealth` checks run on factory init + periodic — unhealthy providers fall to the back of the failover chain
- `ThreeDCapability` is the routing key — request → capability match → first healthy provider with that capability

## Consumers

- `api/v1/clothing_3d/*` — async 3D job pipeline (idempotency-gated)
- `skyyrose/elite_studio/*` — round-table 3D generation
- `agents/core/creative/*` — 3D asset generation requests

## Subpackage

- `trellis/` — TRELLIS-specific pipeline (config, garment-aware prompts, pre/postprocess). Implements `I3DProvider` via `TrellisProvider`


