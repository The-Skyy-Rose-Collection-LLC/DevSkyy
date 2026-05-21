# ai_3d/providers/ — 3D generation provider clients

Async httpx clients for the three 3D-generation vendors AI-3D currently routes through. Each client owns its own rate-limit semantics, env-var contract, and response shape. The provider-agnostic pipeline logic lives one level up in `ai_3d/`.

## Key files

- `tripo.py` — `TripoClient` for Tripo3D. `ImageGenerationRequest(BaseModel)` validates inputs (`texture_resolution` 512–4096, image-existence check). Reads `TRIPO3D_API_KEY`.
- `huggingface.py` — `HuggingFace3DClient` for the Hugging Face Inference API. Preferred model: TRELLIS; documented fallbacks: TripoSR → Shap-E → Point-E. Reads `HUGGINGFACE_API_KEY` or `HF_TOKEN`.
- `meshy.py` — `MeshyClient` for Meshy AI. `MeshyTaskStatus(StrEnum)` represents the async task lifecycle. Reads `MESHY_API_KEY`.
- `__init__.py` — Re-exports `TripoClient`, `HuggingFace3DClient`, `MeshyClient`.

## Conventions

- Every client uses async httpx with `asyncio.Semaphore(5)` + a 2-second inter-call delay + exponential backoff on 429. Don't change these numbers without a documented cost review — they are tuned against vendor rate limits.
- Each client reads exactly one env var (or accepts a fallback for Hugging Face). Hard-fail at construction time if the key is missing — silent fallback to anonymous calls leads to mystery 401s.
- Calls are routed through agent wrappers (`agents/tripo_agent.py`, `agents/meshy_agent.py`) which enforce the STOP-AND-SHOW protocol. Direct use from `api/` handlers is prohibited.
- Model IDs are owned by the client, not the caller. `HuggingFace3DClient` chooses TRELLIS first and falls through TripoSR → Shap-E → Point-E internally.

## Don't

- Don't call these clients directly from `api/` handlers. Route through the agent layer so cost gates, retries, and audit trails apply.
- Don't widen `asyncio.Semaphore(5)` past 5 without a cost review and explicit vendor sign-off. Concurrency translates directly into per-minute spend.
- Don't hardcode model IDs in the caller. The client owns the fallback chain.
- Don't add a new provider here without also updating `ai_3d/resilience.py` retry/fallback rules and `ai_3d/CLAUDE.md`.

## Related

- `agents/tripo_agent.py`, `agents/meshy_agent.py` — agent wrappers that own STOP-AND-SHOW and cost gating
- `skyyrose/elite_studio/agents/three_d_agent.py` — consumes `MeshyClient` directly via async-with
- `skyyrose/elite_studio/sku_resolver.py` — consumes `TripoClient` directly via lazy import
- `ai_3d/CLAUDE.md` — parent pipeline doc
- `ai_3d/resilience.py` — retry / fallback / timeout policy for provider calls
