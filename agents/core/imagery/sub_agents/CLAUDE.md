# agents/core/imagery/sub_agents/ — Imagery sub-agents (5 modules)

Per-vendor sub-agents for the Imagery & 3D domain. Each handles one provider with vendor-specific failover, quota management, and quality gating. All inherit `SubAgent` from `agents/core/sub_agent.py`.

## Inventory

| File | Class | Vendor | Purpose |
|------|-------|--------|---------|
| `gemini_image.py` | `GeminiImageSubAgent` | Google Gemini (Nano Banana 2, Nano Banana Pro) | AI image generation — text-to-image, image edit, references |
| `fashn_vton.py` | `FashnVtonSubAgent` | FASHN AI | Virtual try-on with failover chain: FASHN → WeShopAI → IDM-VTON |
| `tripo_3d.py` | `Tripo3dSubAgent` | Tripo3D (.ai + .com regions) | Text-to-3D + image-to-3D model generation |
| `meshy_3d.py` | `Meshy3dSubAgent` | Meshy AI | 3D model generation; acts as Tripo failover and vice versa |
| `hf_spaces.py` | `HfSpacesSubAgent` | HuggingFace Spaces | Multi-Space orchestration + quota tracking across HF-backed providers |

## Provider-specific facts

### Gemini Image (`gemini_image.py`)
- **Models:** Nano Banana = `gemini-2.5-flash-image` (original), Nano Banana 2 = `gemini-3.1-flash-image-preview` (default), Nano Banana Pro = `gemini-3-pro-image-preview` (4K, deep reasoning)
- **Per `model_ids.py`:** `NANO_BANANA_2_MODEL` is the canonical default; `NANO_BANANA_PRO_MODEL` for 4K/hero renders
- **Strength:** image refs (multi-image fusion). **Weakness:** text rendering inside images (Gemini text-on-image is unreliable — verify with QC panel)

### FASHN VTON (`fashn_vton.py`)
- **API:** `https://api.fashn.ai/v1`
- **Endpoints (all paid, all gated by STOP AND SHOW):**
  - `/tryon` — garment-on-person try-on
  - `/product-to-model` — generate model wearing the product
  - `/edit` — edit existing VTON output
  - `/model-create` — generate a base model
  - `/image-to-video` — turn VTON image into video
- **Cost:** ~$0.075-$0.30 per sample, often 4 samples × 4 models = $1.20+ per dispatch
- **Failover chain:** FASHN 5xx/timeout → WeShopAI → IDM-VTON. Sub-agent owns the chain — callers don't manage failover.

### Tripo 3D (`tripo_3d.py`)
- **Two regions, separate keys:** `.ai` region + `.com` region — `TRIPO_API_KEY_AI` / `TRIPO_API_KEY_COM` env vars
- **Failover:** Tripo down → route to `meshy_3d` sub-agent (and vice versa)
- **Spike record:** see project memory `feedback_tripo_multi_account.md` for real-world cost benchmarks
- **STOP AND SHOW** wired into `scripts/tripo_spike_asset_extraction.py` — per-call cost surfaced before dispatch

### Meshy 3D (`meshy_3d.py`)
- **Model:** `meshy-5` (mirrored in `ai_3d/providers/meshy.py`)
- **Use case:** Tripo failover + cases where Meshy outperforms Tripo for specific garment categories
- **Quality gate:** integrated with `validation_scoring.py` — output below threshold → re-route to Tripo

### HF Spaces (`hf_spaces.py`)
- **Not a provider** — orchestrates multiple HF-backed providers (and tracks quota across them)
- **Manages:** rate-limit windows, account rotation, Space cold-start handling
- **Cross-provider coordination:** when 2+ sub-agents share an HF account, this is the single source of truth for "how much quota is left"

## SubAgent contract (from `agents/core/sub_agent.py`)

```python
class FashnVtonSubAgent(SubAgent):
    name = "fashn_vton"
    parent_type = CoreAgentType.IMAGERY
    capabilities = ["virtual_tryon", "product_to_model", "model_create"]
    description = "FASHN AI virtual try-on with WeShopAI / IDM-VTON failover"
    system_prompt = "..."  # optional default

    async def execute(self, task: str, **kwargs) -> dict[str, Any]:
        # 1. Confirm STOP AND SHOW gate (paid call)
        # 2. Call provider via async client
        # 3. On failure → self.diagnose() → self.heal() (3 attempts)
        # 4. Quality gate via validation_scoring
        # 5. Still failing → escalate_to_parent() (ImageryCoreAgent)
        return ...
```

## Conventions

- **All paid API dispatches surface STOP AND SHOW** before execution. Show `Action / SKU / Source file path / Cost / Confirm? [y/N]` — wait for explicit "y" or "yes".
- **Reference products by name** in user-facing logs (not bare SKU). SKU-first conflations caused the br-001 bug class.
- **Source file paths are absolute.** Sub-agents must verify file exists + size + mtime before paying for an API call against it.
- **Dossier required for 3D.** `Tripo3dSubAgent` and `Meshy3dSubAgent` MUST load the SKU dossier; CSV `branding_spec` is NOT an acceptable fallback. Hard-fail with clear error.
- **SKIPPED.json respected.** Pull from `renders/ghost-mannequin/SKIPPED.json` at startup — skip any SKU in the list.
- **Failover chain documented in class docstring.** When adding a new provider failover edge, update the docstring + `agent.py` heal cycle.

## Don't

- Don't dispatch paid calls without STOP AND SHOW. The cost in dollars is real and so is the WC live-site impact when bad images get uploaded.
- Don't share an account between sub-agents without going through `hf_spaces` quota tracker. Double-spend → account suspension.
- Don't add a new provider here without:
  1. Registering it in `agents/core/imagery/agent.py:_register_sub_agents()`
  2. Adding the failover edge in the heal cycle
  3. Documenting quota source (own vs. HF Spaces pool)
- Don't bypass the quality gate. If output is below threshold, fail over — don't accept and ship.
- Don't call `os.environ.get("TRIPO_API_KEY")` — use the region-specific keys (`TRIPO_API_KEY_AI` / `TRIPO_API_KEY_COM`) and route to the matching endpoint.

## Related

- Parent core: `agents/core/imagery/agent.py` (`ImageryCoreAgent`)
- SubAgent base: `agents/core/sub_agent.py`
- Quality scoring: `agents/core/validation_scoring.py`
- Older standalone agents (wrapped by these): `agents/fashn_agent.py`, `agents/tripo_agent.py`, `agents/meshy_agent.py`
- Model IDs: `llm/model_ids.py` (`NANO_BANANA_*`, `MESHY_AI_MODEL`)
- 3D Round Table for quality vote: `orchestration/threed_round_table.py`
- HF 3D client: `orchestration/huggingface_3d_client.py`
- Pipeline orchestrator: `orchestration/asset_pipeline.py`
- Canonical catalog: `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
- Per-SKU dossiers: `knowledge-base/products/<sku>/`
- Skip list: `renders/ghost-mannequin/SKIPPED.json`

## Recent learnings

- FASHN agent capability confirmed (cmem #3318, 2026-05-11): `AgentCapability.VIRTUAL_TRYON` exposed via `agents/fashn_agent.py` at `api.fashn.ai/v1`.
- 3D pipeline file structure confirmed (cmem #3346, 2026-05-11): five sub-agents map 1:1 to vendor APIs.
- Tripo multi-account / multi-region setup is documented in project memory (`feedback_tripo_multi_account.md`).
