# TRELLIS.2 Deployment Handoff

**Status:** READY TO START · **Created:** 2026-04-27 · **Owner:** unassigned · **Estimated effort:** 2–4 hours for Phase 1 (HF Space), 1–2 days for Phase 2 (Modal + DevSkyy agent)

---

## TL;DR

DevSkyy needs remote GPU inference for Microsoft TRELLIS.2 (4B-param image-to-3D model) because it requires Linux + NVIDIA 24GB+ VRAM and our dev machines are Apple Silicon. Two-phase deployment recommended: **Phase 1 — fork Microsoft's HF Space as a private skyyrose space (fast path, ~3 hours, ~$0.40/hr while running)**; **Phase 2 — port to Modal serverless GPU and wire into `agents/trellis_agent.py` mirroring `agents/meshy_agent.py` (cost optimization, integration with DevSkyy planner)**.

The repo is already cloned at `/Users/theceo/DevSkyy/TRELLIS.2/` (832MB, gitignored at `.gitignore:384`).

---

## 1. Context

**What it is:** Microsoft TRELLIS.2 — image-to-3D generation, 4B params, outputs PBR-textured meshes via the novel "O-Voxel" sparse representation (handles open surfaces, draped fabric, non-manifold geometry — ideal for streetwear product 3D).

**Why we want it:** SkyyRose product 3D is currently routed through `agents/meshy_agent.py` (paid API, credit-based) and `agents/tripo_agent.py`. TRELLIS.2 is a SOTA self-hosted alternative that produces PBR materials suitable for the WordPress theme's Three.js scenes (`wordpress-theme/skyyrose-flagship/assets/js/experiences/`). Self-hosting also removes per-generation API costs at high volume.

**Reference points (verified 2026-04-27 against live repo state — do not modify, mirror only):**

*Active 3D routing surface:*
- `skyyrose/elite_studio/creative/nodes.py:130` — `three_d_model_node` (LangGraph node, the live entry point). Routes via `SDKGarment3DAgent` when `state.params.use_sdk_agent` is set, falls back to `ThreeDGenerationPipeline`.
- `agents/claude_sdk/domain_agents/immersive.py:34` — `SDKGarment3DAgent` (primary current 3D agent for the LangGraph path)
- `ai_3d/generation_pipeline.py:163` — `ThreeDGenerationPipeline` (fallback chain). Provider selection via `ThreeDProvider` enum at line 47.
- `orchestration/threed_round_table.py:540-565` — tournament-pattern orchestrator that runs multiple providers in parallel, scores, picks best. Currently wires `TripoAssetAgent` via lazy-load at `_get_tripo_agent()` (line 552). **This is the actual "master orchestrator" equivalent — `pipelines/skyyrose_master_orchestrator.py` was deleted in commit `f25fd25d3` (Phase B1 scorched earth) and does NOT exist.**

*Agent shape to mirror:*
- `agents/tripo_agent.py:238` — `TripoAssetAgent(SuperAgent)`. Config dataclass `TripoConfig` at line 101. This is the active wire-in pattern.
- `agents/meshy_agent.py:MeshyAgent` — same `SuperAgent` shape but currently NOT wired into the round table; useful as a second reference for API client + polling patterns.

*HTTP client pattern for remote inference:*
- `orchestration/huggingface_3d_client.py:HuggingFace3DClient` — closest existing pattern for an async HTTP client to a remote 3D model. Provides `HF3DModel` enum, `HF3DResult` Pydantic, `HF3DFormat`, `HF3DQuality` — directly reusable for Modal client side.

*Deploy + auth:*
- `scripts/deploy_hf_spaces.sh` — existing HF Spaces deploy pattern (machine-portable since 2026-04-27 — derives `PROJECT_ROOT` from `${BASH_SOURCE[0]}`)
- HF auth user: `damBruh` (existing space at `damBruh/skyyrose-flux-upscaler`)

---

## 2. Hard Constraints (from `TRELLIS.2/README.md`)

| Constraint | Detail |
|---|---|
| OS | Linux only (verified A100/H100) |
| GPU | NVIDIA, **≥24GB VRAM** required |
| CUDA | Toolkit 12.4 recommended |
| PyTorch | 2.6.0 + CUDA 12.4 |
| Native deps | `flash-attn` (or `xformers` fallback for V100), nvdiffrast, custom CUDA kernels in `o-voxel/` (Eigen submodule) |
| Inference time (H100) | 512³ ≈ 3s · 1024³ ≈ 17s · 1536³ ≈ 60s |
| Model weights | `microsoft/TRELLIS.2-4B` on HF (not bundled in repo) |

**Implication:** No local macOS path exists. Cannot run `setup.sh` on dev machines. All inference must be remote.

---

## 3. Decision Matrix

| Option | Cost (light use ~50 gens/day) | Cost (heavy ~500 gens/day) | Cold start | Setup complexity | Fit with DevSkyy patterns |
|---|---|---|---|---|---|
| **HF Space (private, A10G Small)** | $288/mo always-on OR sleep-on-idle | $288/mo capped | ~30s wake | Low (fork existing Space) | High — `scripts/deploy_hf_spaces.sh` already exists, HF auth done |
| **Modal serverless (A10G)** | ~$15/mo (pay per second) | ~$150/mo | ~10–30s warm, 60s cold | Medium (image build, decorator-based Python) | Medium-high — clean Python API fits `agents/` pattern |
| **RunPod persistent (A10G)** | $0.39/hr × 24 × 30 = $281/mo | same | None (always on) | Medium (manual instance mgmt) | Low — no managed deploy story |
| **HF Inference Endpoints (A10G)** | $0.60/hr × usage | same | ~60s cold | Low | Medium |

**Choice: Phase 1 = HF Space (sleep-on-idle), Phase 2 = Modal.**

**Rationale:**
- Phase 1 prioritizes time-to-first-3D-asset over cost. HF Space sleep-on-idle gives ~$10–40/mo for spiky use, no infra surprises. The Microsoft team publishes the Space (`huggingface.co/spaces/microsoft/TRELLIS.2`) — duplicate it instead of building from scratch.
- Phase 2 migrates to Modal once the integration story is real, because Modal's pay-per-second pricing crushes HF for spiky workloads (e.g., new product drops happen in batches; idle time should cost $0).
- RunPod and HF Inference Endpoints are documented in §10 for completeness but not recommended.

---

## 4. Pre-flight Checklist

Before starting Phase 1, verify each of these:

- [ ] `hf auth whoami` returns `damBruh` — if not, run `hf auth login`
- [ ] HF account has billing attached (payment method on file at `huggingface.co/settings/billing`) — required to upgrade Space hardware to A10G
- [ ] Repo state: `cd /Users/theceo/DevSkyy && git status` clean enough; `TRELLIS.2/` is already gitignored
- [ ] Confirm `damBruh` has Pro account OR willing to enable Spaces hardware billing (~$0.40/hr A10G Small)
- [ ] (Phase 2 only) Modal account: `pip install modal && modal setup`
- [ ] (Phase 2 only) HF token in environment for model weight download in Modal: `HF_TOKEN` env var

---

## 5. Phase 1 — HF Space Fork (PRIMARY)

### 5.1 Duplicate the upstream Space

The fastest path is to duplicate Microsoft's published Space and lock it private:

```bash
# Visit: https://huggingface.co/spaces/microsoft/TRELLIS.2
# Click: "..." menu → "Duplicate this Space"
# Set:
#   - Owner: damBruh
#   - Space name: skyyrose-trellis2
#   - Visibility: Private
#   - Hardware: A10G Small (24GB)  [click "Pay-as-you-go" if first time]
#   - Sleep time: 15 minutes (auto-pause on idle)
```

After duplication, the new Space lives at `https://huggingface.co/spaces/damBruh/skyyrose-trellis2`.

### 5.2 Verify it works

1. Wait ~5–10 min for the Space to build (CUDA images are heavy)
2. Open the Space URL, upload a test product image (use any front-facing techflat from `wordpress-theme/skyyrose-flagship/assets/techflats/`)
3. Confirm a `.glb` download appears

### 5.3 Add to existing deploy script

Edit `scripts/deploy_hf_spaces.sh` to include the new Space in the hardcoded list (around line 31, the `SPACES_DIR` block). The script is already machine-portable as of 2026-04-27 — `PROJECT_ROOT` derives from `${BASH_SOURCE[0]}`, no further changes needed.

### 5.4 Phase 1 done

At this point you have a working private HF Space. Stop here if you only need manual generation. Continue to Phase 2 if you need programmatic integration with DevSkyy agents.

---

## 6. Phase 2 — Modal Serverless + DevSkyy Agent

### 6.1 Why migrate from HF Space

HF Spaces are great for demo UIs but awkward for programmatic agent integration. They expose a Gradio API but cold-start each idle session, have request rate limits per Space, and bill at fixed hourly rates regardless of utilization. Modal's per-second billing and clean Python decorator API fit DevSkyy's `agents/` architecture.

### 6.2 Modal app structure

Create `ai_3d/trellis2_modal.py` (note: `pipelines/` was emptied in the Phase B1 scorched-earth refactor — `f25fd25d3` — and is no longer the right home for new modules; `ai_3d/` is the active 3D pipeline directory next to `ai_3d/generation_pipeline.py`):

```python
# ai_3d/trellis2_modal.py — sketch only
import modal

image = (
    modal.Image.from_registry("nvidia/cuda:12.4.0-devel-ubuntu22.04")
    .pip_install("torch==2.6.0", index_url="https://download.pytorch.org/whl/cu124")
    .pip_install("flash-attn==2.6.3", "nvdiffrast", "trimesh", "huggingface_hub")
    .run_commands(
        "git clone -b main https://github.com/microsoft/TRELLIS.2.git --recursive /opt/trellis2",
        "cd /opt/trellis2 && bash setup.sh --o-voxel --flash-attn --nvdiffrast",
    )
    .env({"PYTHONPATH": "/opt/trellis2"})
)

app = modal.App("skyyrose-trellis2")

@app.cls(image=image, gpu="A10G", timeout=600, scaledown_window=300)
class Trellis2:
    @modal.enter()
    def load_model(self):
        from trellis2.pipelines import Trellis2Pipeline
        self.pipeline = Trellis2Pipeline.from_pretrained("microsoft/TRELLIS.2-4B")
        self.pipeline.cuda()

    @modal.method()
    def generate(self, image_bytes: bytes, resolution: int = 1024) -> bytes:
        from PIL import Image
        from io import BytesIO
        img = Image.open(BytesIO(image_bytes))
        outputs = self.pipeline.run(img, resolution=resolution)
        glb_bytes = outputs.export_glb()
        return glb_bytes
```

Deploy: `modal deploy ai_3d/trellis2_modal.py`

Endpoint: `https://damBruh--skyyrose-trellis2-trellis2-generate.modal.run` (Modal autogenerates).

### 6.3 DevSkyy agent — `agents/trellis_modal_agent.py`

**Mirror `agents/tripo_agent.py` shape (the verified active 3D agent), not Meshy** — `TripoAssetAgent` is the only `SuperAgent`-shaped 3D agent currently wired into `orchestration/threed_round_table.py`. Match its surface so the round-table integration in §6.4 is a one-line addition.

Key adaptations:

- `TrellisConfig` dataclass (mirror `TripoConfig` at `agents/tripo_agent.py:101`) with `modal_endpoint: str`, `resolution: int = 1024`, `seed: int | None`, `texture_resolution: int = 2048`, `timeout_seconds: int = 180`
- `class TrellisModalAgent(SuperAgent)` (mirror `TripoAssetAgent` at `agents/tripo_agent.py:238`) — async API client to the Modal endpoint, no polling needed (Modal's HTTPS endpoints are synchronous when warm)
- For the HTTP client side, mirror the async pattern in `orchestration/huggingface_3d_client.py:HuggingFace3DClient` — same `httpx.AsyncClient` + Pydantic result shape
- Reuse `agents/core/validation_scoring.py:compute_validation_scores` (already used by `meshy_agent.py:48` and `tripo_agent.py`)
- Register tool spec with `ToolRegistry` matching Tripo's registration (`ToolCategory.THREED`, `ToolSeverity.PAID`)

```python
# agents/trellis_modal_agent.py — interface only, mirrors TripoAssetAgent shape
from agents.core.base import SuperAgent, AgentCapability, AgentConfig

@dataclass
class TrellisConfig:
    modal_endpoint: str
    resolution: int = 1024
    texture_resolution: int = 2048
    seed: int | None = None
    timeout_seconds: int = 180

class TrellisModalAgent(SuperAgent):
    """Image-to-3D via self-hosted Microsoft TRELLIS.2 on Modal serverless GPU."""

    async def generate_from_image(
        self, image_path: Path, resolution: int = 1024
    ) -> TrellisGenerationResult: ...

def get_trellis_modal_agent(config: TrellisConfig | None = None) -> TrellisModalAgent: ...
```

### 6.4 Wire into the round-table tournament

The orchestrator surface that matters is **`orchestration/threed_round_table.py`** (the deleted `pipelines/skyyrose_master_orchestrator.py` was replaced by this tournament-pattern module). Two integration points:

**A. Add TRELLIS as a tournament participant (primary)**

Mirror the Tripo lazy-load block at `orchestration/threed_round_table.py:540-565`:

1. Add `enable_trellis2: bool = True` to the round-table constructor alongside `enable_tripo3d`
2. Add `TRELLIS2 = "trellis2"` to the `ThreeDProvider` enum at `ai_3d/generation_pipeline.py:47`. **Do not modify the existing `TRELLIS = "trellis"` slot at line 50** — that is wired to TRELLIS v1 (`microsoft/TRELLIS-image-large`) via `ai_3d/providers/huggingface.py:53` and is part of the default fallback chain at line 86 (`[TRELLIS, MESHY, TRIPO]`) with a registered `trellis_client` at line 202. v1 and v2 are two distinct pipelines: v1 uses HF Inference API serverless (already live), v2 uses self-hosted Modal serverless GPU (this handoff). They coexist as separate enum values and separate providers — never collapse them
3. Add `_get_trellis_agent()` mirroring `_get_tripo_agent()` (line 552) — lazy-loads `TrellisModalAgent`, sets `enable_trellis2 = False` on import failure, logs degraded state
4. Wire into `compete_text_to_3d()` and the image-to-3D variant so all three providers race in parallel; tournament scoring already handles winner selection

**B. Optional fast path through the LangGraph node**

For latency-sensitive flows (e.g., live preview during product upload), add a routing branch in `skyyrose/elite_studio/creative/nodes.py:130 three_d_model_node`:

- Insert TRELLIS.2 between the existing `SDKGarment3DAgent` branch (line 164: `from agents.claude_sdk.domain_agents.immersive import SDKGarment3DAgent`) and the `ThreeDGenerationPipeline` fallback (line 216)
- Trigger condition: `state.params.use_trellis2` flag (mirroring the existing `state.params.use_sdk_agent` pattern at line 133)
- Fall through to existing chain on failure

**Routing heuristic** (worth encoding once both paths work): prefer TRELLIS.2 for products with open/draped surfaces (jackets, hoodies, hooded sweatshirts) where O-Voxel handles topology better than iso-surface methods. Encode this at the `compete_image_to_3d()` caller, not inside the round table.

### 6.5 Tests

Mirror `tests/agents/test_meshy_agent.py` if it exists. At minimum:
- Unit: mocked Modal endpoint, validates request/response shape
- Integration (gated by `RUN_INTEGRATION=1`): single real generation against Modal, asserts GLB file is produced

---

## 7. Cost Projections (USD)

Assumptions: 100 product 3D generations per month (conservative for SkyyRose drop cadence), 17s avg per generation, A10G GPU.

| Phase | Path | Variable cost | Fixed monthly | Total/mo |
|---|---|---|---|---|
| 1 | HF Space, sleep-on-idle, manual triggers | ~30 wake-cycles × 5min × $0.40/hr = $1 | $0 (sleep-on-idle billed only when active) | **~$10** |
| 1 | HF Space, always-on | $0 | $0.40 × 730 = $292 | **~$292** |
| 2 | Modal, A10G, pay-per-second | 100 × 17s × $1.10/hr ÷ 3600 = $0.52 | $0 | **~$1** |
| 2 | Modal, A100 (faster) | 100 × 7s × $4.40/hr ÷ 3600 = $0.86 | $0 | **~$1** |

Modal wins decisively on cost for SkyyRose's expected volume. Migration ROI: pays for itself within first month.

---

## 8. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| `setup.sh` build fails in Modal image | Phase 2 blocked | Modal's image cache helps iteration; fall back to `xformers` instead of `flash-attn` if compile fails on Modal's CUDA |
| `microsoft/TRELLIS.2-4B` model weights gated on HF | First inference fails | Pass `HF_TOKEN` to Modal as a `modal.Secret`; pre-download in `@modal.enter()` |
| O-Voxel CUDA kernels mismatch GPU compute capability | Runtime error | Pin Modal GPU type to A10G or A100; document in agent config |
| HF Space billing surprises | Unexpected charge | Set spending limit at huggingface.co/settings/billing → "Spending limits" before duplication |
| TRELLIS.2 license incompatibility with commercial use | Can't ship | Verify `LICENSE` file in TRELLIS.2 repo allows commercial — confirmed MIT per HF badge, but recheck before production |
| Output GLB schema doesn't match WordPress Three.js loader | Frontend can't render | Validate GLB in `services/ml/visual_feature_extractor.py` style validator before saving |

---

## 9. Acceptance Criteria

**Phase 1 done when:**
- [ ] `https://huggingface.co/spaces/damBruh/skyyrose-trellis2` is private, on A10G, sleep-on-idle
- [ ] One end-to-end test: upload a SkyyRose product image, download a `.glb`
- [ ] Spending limit configured on damBruh account
- [ ] Space documented in DevSkyy `.planning/handoffs/trellis2-deployment.md` change log below

**Phase 2 done when:**
- [ ] `modal deploy ai_3d/trellis2_modal.py` succeeds, endpoint reachable
- [ ] `agents/trellis_modal_agent.py` mirrors `agents/tripo_agent.py:238 TripoAssetAgent` shape, registered in `ToolRegistry`
- [ ] `pytest tests/agents/test_trellis_modal_agent.py` passes (unit tests, mocked Modal)
- [ ] `ThreeDProvider.TRELLIS2` enum value added at `ai_3d/generation_pipeline.py:47`
- [ ] `_get_trellis_agent()` lazy-load block present in `orchestration/threed_round_table.py` mirroring lines 540-565
- [ ] Integration test (gated by `RUN_INTEGRATION=1`): one real round-table tournament generation includes TRELLIS.2 and produces valid GLB
- [ ] (Optional) Fast-path branch in `skyyrose/elite_studio/creative/nodes.py:130 three_d_model_node` triggered by `state.params.use_trellis2`

---

## 10. Alternatives (not recommended, documented for completeness)

**RunPod persistent A10G** — $281/mo always-on, manual SSH ops. Use only if you need >50% GPU utilization and can't tolerate Modal cold starts.

**HF Inference Endpoints** — Similar to Spaces but more enterprise-y. $0.60/hr A10G plus per-request markup. Skip — Spaces is cheaper for the same hardware.

**Self-hosted dedicated server** — Doesn't fit a small team. Operational burden too high for this volume.

**Replicate / fal.ai** — Worth checking if either has a hosted TRELLIS.2 endpoint by the time this is executed; would skip both phases entirely. Check `replicate.com/explore` and `fal.ai/models` for `TRELLIS` or `microsoft/TRELLIS.2` listings before starting Phase 1.

---

## 10.5 Complementary Providers — Parallel Deploy Tracks (added 2026-04-27)

A deep-research investigation surfaced three providers that **complement TRELLIS.2 rather than replace it**. They solve problems TRELLIS.2 was not designed for. None block Phase 1 or Phase 2 of this handoff — they are independent deploy tracks worth tracking as separate handoffs.

The four-tier strategy that emerged:

| Tier | Use case | Provider | License | Status |
|---|---|---|---|---|
| 1. Workhorse | Catalog product 3D (PBR, single-call, all-purpose) | **TRELLIS.2** | MIT | This handoff |
| 2. Hero geometry | Campaign drops where geometry detail trumps texture turnaround | **Hi3DGen** + texture pass | MIT (Bytedance) | Future handoff |
| 3. Animatable garments | **Immersive worlds avatar wearing actual products** with proper drape | **AniGen** (VAST-AI) | MIT | **Highest leverage — ship next** |
| 4. Design iteration | Internal — text-driven garment editing ("longer sleeves") before commit | **ChatGarment** | Apache-2.0 | R&D track |
| 5. Cloth physics post-process | Optional — proper drape under avatar motion in immersive worlds | **HOOD** (Dolorousrtur) | MIT | Post-AniGen, only if drape problems visible |

### 10.5.1 Hi3DGen / Stable3DGen — verified deploy-ready

- **Repo:** [github.com/Stable-X/Stable3DGen](https://github.com/Stable-X/Stable3DGen)
- **License:** MIT (Bytedance Inc 2025) — deliberately commercial-clean. The maintainers explicitly **removed non-commercial NVIDIA dependencies** (`kaolin`, `nvdiffrast`, `flexicube`) from the original TRELLIS so the adapted version can ship commercially.
- **HF Space:** `Stable-X/Hi3DGen` — Gradio SDK, RUNNING on `zero-a10g`, 699 likes, fork-ready
- **HF model weights:** `Stable-X/trellis-normal-v0-1` (109K downloads), `Stable-X/yoso-normal-v1-8-1` (57K downloads)
- **Approach:** image → normal map → 3D geometry ("normal bridging")
- **vs TRELLIS:** User studies (amateur + professional 3D artists) prefer Hi3DGen over 5 SOTA models including TRELLIS for detail and fidelity
- **Caveat:** Geometry-only, NOT PBR. Production use requires a separate texture pass (e.g., `VAST-AI/MV-Adapter-Img2Texture`)
- **Repo health:** 86 forks, 35 open issues, last push 2025-07-02 (9mo stale but real)
- **Deploy complexity:** Comparable to TRELLIS.2 — `spconv-cu`, `xformers`, `triton`, PyTorch 2.4. Single `app.py` Gradio entry, weights auto-downloaded via `huggingface_hub.snapshot_download` to local `weights/`. Modal-friendly with same image build pattern as TRELLIS.2.

### 10.5.2 AniGen (VAST-AI) — verified deploy-ready, ship-next priority

- **Repo:** [github.com/VAST-AI-Research/AniGen](https://github.com/VAST-AI-Research/AniGen) — **SIGGRAPH 2026 peer-reviewed**, 344 stars
- **HF model:** [VAST-AI/AniGen](https://huggingface.co/VAST-AI/AniGen) — published 2026-04-13 (~2 weeks ago)
- **HF Space:** `VAST-AI/AniGen` — Gradio, RUNNING on `zero-a10g`, public, sleep_time 172800 (~2 days), fork-ready
- **License:** MIT (HF tag confirms; GitHub metadata shows NOASSERTION but the LICENSE file in code is MIT)
- **Base model:** Built on `microsoft/TRELLIS-image-large` (familiar architecture — knowledge transfer from TRELLIS deploy)
- **Capability:** Single image → fully rigged, animatable 3D asset (mesh + articulated skeleton + skinning weights). TRELLIS.2 produces static meshes only.
- **Repo health:** Last push 2026-04-14 (one day after HF model release — very active)
- **Hardware:** **18GB+ VRAM** (lower than TRELLIS.2's 24GB). NVIDIA A800 / RTX3090 verified. CUDA 11.8 or 12.2.
- **Inference does NOT need CUBVH** (training does, via `setup.sh`)
- **Pretrained checkpoints:** ~23GB total on HF (`ss_flow` + `slat_flow` variants)
- **Why ship next:** Closes the longest-standing capability gap in `wordpress-theme/skyyrose-flagship/assets/js/experiences/` — namely, putting actual SkyyRose products on the moving Skyy avatar with proper drape physics. The immersive worlds architecture has been waiting for this exact piece since `assets/models/skyy.glb` was rigged with `idle`/`walk` clips.

### 10.5.3 ChatGarment — R&D track, not production

- **Repo:** [github.com/biansy000/ChatGarment](https://github.com/biansy000/ChatGarment) — 133 stars, Apache-2.0
- **Last push:** 2025-08-07
- **Capability:** LLM-driven garment estimation/generation/editing — including **text-based editing** ("make sleeves longer")
- **Stack:** Wraps [GarmentCodeRC](https://github.com/biansy000/GarmentCodeRC) (sewing patterns) + [ContourCraft-CG](https://github.com/biansy000/ContourCraft-CG) (cloth simulation)
- **Use case:** Internal Corey-facing tool to iterate on garment params before committing to full TRELLIS.2 / AniGen render runs. Not a customer-facing render path.

### 10.5.4 HOOD — optional Tier 5 cloth simulation post-process

- **Repo:** [github.com/Dolorousrtur/HOOD](https://github.com/Dolorousrtur/HOOD) — MIT, 200 stars, last push 2025-05-20
- **Paper:** "HOOD: Hierarchical Graphs for Generalized Modelling of Clothing Dynamics" (CVPR 2023), arXiv 2212.07242
- **What it does:** Graph-neural-network cloth simulator. Takes a static rigged garment mesh + body pose sequence → outputs physically-plausible drape per frame
- **What it does NOT do:** Image-to-3D. Pure simulation, not generation. Requires an existing 3D garment mesh as input (i.e., output of AniGen)
- **Strategic role:** Optional Tier 5 layered on top of Tier 3 (AniGen). AniGen produces a rigged static garment; HOOD adds proper drape under motion when the SkyyRose avatar walks through Bay Bridge / Beauty-and-Beast / Golden Gate scenes
- **Architectural consistency with Tier 4:** ChatGarment depends on `ContourCraft-CG` for cloth simulation. ContourCraft and HOOD are sibling works from overlapping authors. The simulation backend stays in one family across Tier 4 and Tier 5.
- **When to defer:** HOOD is latency-expensive (graph network per frame, can't run live in browser) and requires pre-baking physics tracks into the GLB. Skip until AniGen is shipping rigged garments and visible drape problems emerge in the immersive worlds. **Premature without that signal.**

### 10.5.5 Confirmed dead-ends from this round

- `microsoft/GarmentCrafter` (arxiv 2503.08678) — empty stub repo, no license, no checkpoints, 11mo dormant
- Spatio-Temporal Garment Reconstruction (arxiv 2602.24043, Feb 2026) — paper-only, no code released
- Tencent Hunyuan3D 3.0 — does **not exist**. `tencent/Hunyuan3D-2.1` (June 2025) is the latest, with PBR Texture Synthesis and "first production-ready 3D asset generation" billing. Tencent Community License — commercial OK with conditions.
- Dress-1-to-3 (arxiv 2502.03449) — project page only, no public code repo
- **Awesome-3D-Garments curated list deep dive (2026-04-27)** — confirmed the academic-licensing pattern: every garment-specific image-to-3D model in the list has either no LICENSE file (default "all rights reserved") or GPL-3.0 (copyleft, incompatible with proprietary code). Specific disqualifications:
  - **GarVerseLOD** ([zhongjinluo/GarVerseLOD](https://github.com/zhongjinluo/GarVerseLOD), ACM TOG 2024, 66 stars, 6000-model artist-made dataset) — NO LICENSE
  - **DrapeNet** ([liren2515/DrapeNet](https://github.com/liren2515/DrapeNet), 126 stars) — GPL-3.0 (copyleft blocker)
  - **DressCode** ([ihe-kaii/DressCode](https://github.com/ihe-kaii/DressCode), 280 stars, text→sewing pattern) — NO LICENSE
  - **ISP** ([liren2515/ISP](https://github.com/liren2515/ISP), 49 stars, multi-layered draping) — NO LICENSE
  - **Design2Cloth** ([jiali-zheng/Design2Cloth](https://github.com/jiali-zheng/Design2Cloth)) — NO LICENSE

### 10.5.6 Strategic implication of the licensing pattern

There is no garment-specific MIT-licensed image-to-3D model in the open-source ecosystem as of 2026-04-27. The four-tier strategy in §10.5 is not a compromise — it is the only legally viable architecture for SkyyRose. General-purpose models (TRELLIS.2, Hi3DGen, AniGen) with permissive licenses are the only commercially shippable path. Garment-specific academic work either is not licensed for commercial use or requires open-sourcing the consuming code.

### 10.5.7 Sources

- [Stable3DGen (Hi3DGen) GitHub](https://github.com/Stable-X/Stable3DGen)
- [Hi3DGen Space (HF)](https://huggingface.co/spaces/Stable-X/Hi3DGen)
- [Hi3DGen project page](https://stable-x.github.io/Hi3DGen/)
- [Hi3DGen arXiv 2503.22236](https://arxiv.org/abs/2503.22236)
- [VAST-AI/AniGen GitHub](https://github.com/VAST-AI-Research/AniGen)
- [VAST-AI/AniGen HF model](https://huggingface.co/VAST-AI/AniGen)
- [AniGen Space (HF)](https://huggingface.co/spaces/VAST-AI/AniGen)
- [ChatGarment GitHub](https://github.com/biansy000/ChatGarment)
- [Awesome-3D-Garments curated list](https://github.com/Shanthika/Awesome-3D-Garments)
- [Cool-GenAI-Fashion-Papers](https://github.com/wendashi/Cool-GenAI-Fashion-Papers)

---

## 11. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-04-27 | initial | Handoff drafted; repo cloned to `/Users/theceo/DevSkyy/TRELLIS.2/` and gitignored |
| 2026-04-27 | follow-up | Fixed `scripts/deploy_hf_spaces.sh` hardcoded `/Users/coreyfoster/DevSkyy` path → script-relative `${BASH_SOURCE[0]}` resolution; updated §1 and §5.3 references |
| 2026-04-27 | architecture-correction | Original §1 cited `pipelines/skyyrose_master_orchestrator.py` and `pipelines/skyyrose_luxury_pipeline.py` — both were deleted in commit `f25fd25d3` ("Phase B1 scorched earth — rebuild pending"). Verified live integration surface against repo: real entry point is `skyyrose/elite_studio/creative/nodes.py:130 three_d_model_node` (LangGraph) with `SDKGarment3DAgent` primary + `ThreeDGenerationPipeline` fallback. Real tournament orchestrator is `orchestration/threed_round_table.py:540-565`. Rewrote §1 (verified reference points), §6.2 (target dir `ai_3d/` not `pipelines/`), §6.3 (mirror `TripoAssetAgent` not `MeshyAgent` since Tripo is the only `SuperAgent`-shaped 3D agent currently in the round table), §6.4 (round-table tournament integration + optional LangGraph fast path, no master orchestrator), §9 acceptance criteria. |
| 2026-04-27 | live-verification | Verified all §1 line anchors against repo (nodes.py:130, immersive.py:34, generation_pipeline.py:47/163, threed_round_table.py:540-565, tripo_agent.py:101/238) — all exact. Caught two doc-bugs: §6.2 inline code-block comment said `pipelines/` (corrected to `ai_3d/`), §6.4 step 2 didn't disambiguate v1 vs v2 enum slots (now states v1 and v2 are two distinct pipelines that must coexist — existing `TRELLIS` slot routes to `microsoft/TRELLIS-image-large` via HF Inference API and stays untouched, new `TRELLIS2` slot routes to `microsoft/TRELLIS.2-4B` via Modal). |
| 2026-04-27 | deep-research-expansion | Investigated alternative image-to-3D models for fashion-specific use. Disqualified GarmentCrafter (empty stub repo, no license, 11mo dormant), Spatio-Temporal Garment Reconstruction Feb 2026 (paper-only), Dress-1-to-3 (project page only), and confirmed Hunyuan3D 3.0 does not exist (`tencent/Hunyuan3D-2.1` is the latest). Surfaced three complementary providers each verified deploy-ready: Hi3DGen (Bytedance, MIT, normal-bridging geometry, beats TRELLIS in user studies), AniGen (VAST-AI, MIT, SIGGRAPH 2026, animatable garments — pushed 2026-04-14, 18GB VRAM, lower than TRELLIS.2's 24GB), and ChatGarment (Apache-2.0, LLM-driven garment editing). Added §10.5 documenting a four-tier provider strategy: TRELLIS.2 as workhorse, Hi3DGen+texture-pass for hero geometry, AniGen for immersive-worlds avatar drape, ChatGarment for design iteration. None block this handoff; AniGen is the highest-leverage next ship because it closes the long-standing immersive-worlds capability gap (`wordpress-theme/skyyrose-flagship/assets/js/experiences/` + `assets/models/skyy.glb`). |
| 2026-04-27 | awesome-3d-garments-audit | Deep-read the Awesome-3D-Garments curated list (Shanthika/Awesome-3D-Garments, 506 lines). Verified code-release + license status for every plausible candidate. Zero new viable image-to-3D backends found — every garment-specific repo has either no LICENSE file (GarVerseLOD/ACM-TOG 2024 with 6000-model dataset, DressCode 280-stars, ISP, Design2Cloth) or GPL-3.0 copyleft (DrapeNet). One legitimate find: HOOD (Dolorousrtur/HOOD, MIT, CVPR 2023, 200 stars) — graph-NN cloth simulator, NOT image-to-3D. Added as optional Tier 5 in §10.5 four-tier table for post-AniGen drape physics on the immersive-worlds avatar. Architecturally consistent with Tier 4 ChatGarment (which depends on ContourCraft-CG, sibling work). Added §10.5.4 (HOOD), expanded §10.5.5 (dead-ends with academic-licensing pattern), added §10.5.6 (strategic implication: no garment-specific MIT image-to-3D model exists in open-source ecosystem — the four-tier strategy is the only legally viable architecture, not a compromise). Renumbered §10.5.5 Sources → §10.5.7. |
| 2026-04-27 | anigen-phase1-complete | Tier 3 (AniGen) Phase 1 verified end-to-end on `damBruh/SkyyRose-AniGen` (Private, Gradio, sleep-on-idle 15min). **Critical hardware calibration:** AniGen documented 18GB+ VRAM; reality is L4 24GB ($0.80/hr) **OOMs at FlexiCubes mesh extraction** despite model fitting earlier in the pipeline. **L40S 48GB ($1.80/hr) works cleanly** — full pipeline ~70s compute (Stage 1 generate_preview 52s + Stage 2 extract_glb 18s). Update §10.5.2: real-world VRAM requirement is **32GB+ at peak**, use L40S as the production tier. Verified GLB output at `.planning/handoffs/anigen-phase1-verify.glb` (1.87MB): 12,733 vertices / 18,742 faces, **1 skin with 10 joints**, JOINTS_0+WEIGHTS_0+inverseBindMatrices all present, generator=pygltflib@v1.16.3. Static T-pose rig — ready to be retargeted to or driven by external clips (e.g., the SkyyRose avatar's idle/walk Mixamo clips on `assets/models/skyy.glb`). **Strategic finding from this round:** HF Spaces auto-publish a Gradio API (discoverable via `agents.md` + `/gradio_api/info` + `/config`) — for AniGen this means **no Modal serverless deploy is needed for Phase 2**. The agent integration in §6.3 simplifies to `gradio_client.predict(fn_index=7)` for preview and `predict(fn_index=10)` for extract_glb against the existing HF Space. Modal still required for TRELLIS.2 (which has no comparable hosted endpoint) but optional for the AniGen track. Phase 1 acceptance criteria: ✅ Space private+L40S+sleep-on-idle, ✅ end-to-end test (br-001-crewneck.png → rigged GLB), spending limit configured pre-flight. Total Phase 1 verification spend: ~$0.20. |
