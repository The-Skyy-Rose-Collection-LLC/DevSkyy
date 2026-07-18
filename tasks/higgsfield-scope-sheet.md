# Higgsfield — SkyyRose Scope Build Sheet

**Purpose:** what we can build with Higgsfield, mapped to SkyyRose fashion deliverables, with the pipeline + credit gating for each. Use this to scope a run before spending.

**Account (live, 2026-07-16):** `1000 credits` · plan `Plus`.
**Gate (absolute):** every generation is paid → **STOP-AND-SHOW** the exact tool + model + cost, wait for explicit `y`. Read-only tools (`balance`, `presets_show`, `models_explore`, `show_*`, `job_status`, `*_status`, `get_cost` preflights) are free.
**Cost truth:** confirmed per-unit costs are from this project's own runs; everything else → run the tool's cost preflight (`get_cost:true` / dry plan) before scoping a number. Don't trust a guessed credit figure.

---

## 1. Capability catalog (grouped, fashion-first)

### A. Image — stills, editorial, compositing
| Tool | What it does | Fashion use | Cost |
|------|--------------|-------------|------|
| `generate_image` (+ `models_explore` to pick model) | Text/ref → image. `gpt_image_2` = crisp editorial/architectural; `nano_banana_pro` = character-heavy. Accepts reference images + edit mode. | Scroll-world scene stills; campaign/lookbook mood frames; collection hero art; the SR-monogram statue edit. | `gpt_image_2` ≈ **7 cr** @2k/high, ~0.5 cr @1k/low |
| `outpaint_image` | Expand / uncrop an image. | Re-frame a 3:2 still to 16:9 or 9:16 without regenerating; extend a hero backdrop. | preflight |
| `remove_background` | Cutout / transparent PNG. | Float a product or emblem over a scene; social stickers. | preflight |
| `upscale_image` | Enhance / 2K–4K. | Print-res campaign art, billboards, lookbook. | preflight |

> **Lane note:** Higgsfield image = *worlds + mood + editorial*. SKU-exact product shots stay on **OAI gpt-image-2** (our fidelity-gated pipeline), never Higgsfield.

### B. Video — the core lever (image → cinematic motion)
| Tool | What it does | Fashion use | Cost |
|------|--------------|-------------|------|
| `generate_video` | Image→video. Model chosen via `models_explore`. | Scroll-world camera legs; PDP/collection hero loops; drop teasers. | ≈ **12 cr / leg** (seedance/kling, observed) — preflight per model |
| `motion_control` | Recast / puppeteer / motion transfer onto a subject. | Give the mascot a canned walk/gesture; transfer a runway motion onto a look. | preflight |
| `reframe` | Change a finished video's aspect ratio. | One 16:9 master → 9:16 social + 1:1 feed, no re-render. | preflight |
| `upscale_video` | Enhance / 2K–4K a clip. | Finish a hero loop to crisp 4K for the homepage. | preflight |
| `presets_show` | ~60 themed image→video motion presets (RED CARPET, PAPARAZZI, DRIFT, etc.). Applied via `preset_id`. | Social/character content, mascot skits — **not** the architectural fly-through. | (feeds `generate_video`) |

**Video model roster (live from `models_explore`, image-input):**

| Model | start / end image | Res · duration | Seam-lock? | Best for |
|-------|-------------------|----------------|-----------|----------|
| `cinematic_studio_video_v2` (Higgsfield) | ✓ / ✓ | std·pro · 3–12s · 16:9/9:16 | **yes** | Refined cinematic camera + genre control + `preset_id` — **strongest fit for the scroll-world legs** |
| `seedance_2_0` (Bytedance) | ✓ / ✓ | 480p–4k · 4–15s | **yes** | Reference/identity-consistent; multi-SKU; current scroll-world default |
| `kling3_0` (Kling) | ✓ / ✓ | std·pro·4k · 3–15s | **yes** | Multi-shot, motion-transfer; the sanctioned NSFW-filter fallback |
| `veo3` (Google) | ✓ / ✗ | 16:9/9:16 | no | Single-shot cinematic; can't hold a seam |
| `grok_video_v15` (xAI) | ✓ / ✗ | 480p/720p · 2–15s | no | Single start-frame; can't hold a seam |

> **Seamless chain rule (unchanged):** only start+end-image models can frame-lock a seam → **`cinematic_studio_video_v2`, `seedance_2_0`, `kling3_0`**. Pick ONE for the whole chain (mixing render-character pops the seam). One start-only model = one clip, no connectors.

### C. 3D
| Tool | What it does | Fashion use | Cost |
|------|--------------|-------------|------|
| `generate_3d` | Image → GLB mesh. | Quick 3D prop/emblem for a scene; NOT the SKU-exact garment pipeline (that's Meshy/Tripo). | preflight |

### D. Audio & Voice
| Tool | What it does | Fashion use | Cost |
|------|--------------|-------------|------|
| `generate_audio` | Music / SFX / ambience. | Score a drop teaser; ambience under a hero loop. | preflight |
| `create_voice` / `create_voice_from_confirmed_audio` / `list_voices` / `voice_change` | Build + apply a brand voice. | A consistent SkyyRose narrator/mascot voice. | preflight |
| `dubbing` | Re-voice a video in another language. | Localize a campaign film. | preflight |

### E. Made-to-brief video workflows (templated)
| Tool | What it does | Fashion use |
|------|--------------|-------------|
| `explainer_video` (+ `get_explainer_presets` / `resolve_explainer_preset`) | Narrated explainer/story video. | "How the collection is made" / brand-story film. |
| `get_workflow_instructions` → `get_workflow_bundle_file` | Catalog of multi-step video briefs (ad/commercial, UGC/talking-head, podcast, story). | Drop commercial; UGC-style creator ad; founder talking-head. |
| `shorts_studio_*` | Short-form vertical builder (presets + sessions). | TikTok/Reels drop content at volume. |
| `personal_clipper_*` | Cut a long video into short clips. | Turn a lookbook film into 8 social cuts. |

### F. Analysis & optimization
| Tool | What it does | Fashion use |
|------|--------------|-------------|
| `virality_predictor` | Predict engagement / hook / retention risk of a video. | Score a drop teaser before boosting spend. |
| `video_analysis_*` | Analyze a video (create/jobs/status). | QA a cut for pacing / attention before publish. |

### G. Marketing studio & characters
| Tool | Fashion use |
|------|-------------|
| `show_marketing_studio` / `..._generations` | Brand-kit ingestion (name/palette/tone from skyyrose.co) + campaign gen history. |
| `show_characters` / `show_reference_elements` | Character/identity consistency — lock the mascot across clips. |

### H. Infra / ops (free reads unless noted)
`balance` · `show_plans_and_credits` · `transactions` · `models_explore` · `presets_show` · `media_upload`/`media_confirm`/`media_import_url`/`media_upload_widget` · `show_medias` · `show_generations` · `reveal_generation` · `job_status`/`job_display` · `list_workspaces`/`select_workspace` · `sync_agents`.

### Off-lane for SkyyRose (do NOT scope here)
- `create_website`/`deploy_website`/`publish_website`/`website_*`, game creation — SkyyRose ships on **WordPress (skyyrose.co) + Vercel (devskyy.app)**; never route site/app builds through Higgsfield.
- SKU-exact product renders → **OAI gpt-image-2**. Virtual try-on → **FASHN**. Garment 3D → **Meshy/Tripo**. Product LoRA → our **SDXL**.

---

## 2. Fashion deliverables → pipeline → est. cost → gate

| Deliverable | Higgsfield pipeline | Est. credits | Gate |
|-------------|---------------------|--------------|------|
| **Scroll-world fly-through (in progress)** | 5 stills `generate_image gpt_image_2` (done) → 5 legs `generate_video` (cinematic_studio_v2 / seedance_2_0) + re-rolls | finale re-roll ~7 + 5 legs ~60 + re-rolls ~24 ≈ **~90** | STOP-AND-SHOW per batch |
| **PDP / collection hero video loop** | 1 still → 1 short seamless loop (`generate_video`, then `reframe` to sizes) | ~12–20 / surface | ✋ |
| **Drop-launch teaser film** | stills → legs (+ `presets_show` motion) → `generate_audio` score → `reframe` to 9:16/1:1 | ~40–80 | ✋ |
| **Campaign / lookbook editorial stills** | `generate_image` (mood, not SKU) → `upscale_image` for print | ~7–15 / image | ✋ |
| **Mascot voiced intro** | mascot still → `motion_control` / `generate_video` → `create_voice` + `dubbing` | preflight | ✋ |
| **Social verticals at volume** | `shorts_studio_*` / `personal_clipper_*` from a master → `virality_predictor` to rank | preflight | ✋ |

---

## 3. Recommended scope for the current 1000 credits

1. **Finish scroll-world** (~90 cr): re-roll the finale still (7), render 5 camera legs on `cinematic_studio_video_v2` **or** `seedance_2_0` (one model, seam-locked), budget re-rolls. → drops straight into the shipped scaffold (posters already wired; clips replace them with zero rewiring).
2. **1 PDP hero loop** as a proof (~15 cr) — validate the loop treatment on one collection page before scaling to all four.
3. **Hold** the rest (~880 cr) for a drop teaser + campaign stills once the fly-through is live.

Every step above still fires only on explicit `y` with the exact model + cost shown first.

---

_Generated 2026-07-16 from live `balance` + `models_explore` + `presets_show`. Re-verify credit costs with each tool's preflight before a run — per-unit prices move._
