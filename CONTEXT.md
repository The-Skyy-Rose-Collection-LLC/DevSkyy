# DevSkyy

Imagery, dossier, and storefront pipeline for SkyyRose luxury streetwear. This glossary captures terms whose meaning is non-obvious or has historically been used ambiguously in this codebase.

## Language

### Compositor

**CompositorAgent**:
The canonical scene compositor. Owns six stages (alpha → prompt-eng → relight → composite → shadows → QA) as private methods, exposes a single `composite(sku, image_path, scene_name, collection)` entry point. Lives at `skyyrose/elite_studio/agents/compositor_agent.py`. Currently a 68-line `pass_through` shell pending rebuild — see ADR-0001.
_Avoid_: "the compositor script", "the compositor function", "the compositor module"

**compositor_node**:
The LangGraph node that delegates to `CompositorAgent.composite()`. Lives at `skyyrose/elite_studio/graph/nodes.py:318`. Glue and telemetry, not stage logic.
_Avoid_: "the compositor pipeline" (overloaded — see Flagged ambiguities)

**Stage**:
One of the six private methods inside `CompositorAgent.composite()`: alpha (BRIA RMBG), prompt-eng (Claude Opus), relight (libcom), composite (FLUX Fill / Kontext fallback chain), shadows (GPSDiffusion fallback to PIL gaussian), QA (Gemini visual gate). Stages are deterministic transforms, not separate agents.
_Avoid_: "step", "phase" (the project uses "phase" for milestone tracking — `Phase 1`, `Phase 1.5`, `Phase B1` etc.)

### Quality systems

**Embedding gate**:
A pre-QA filter that scores a render's image embedding against a brand centroid. If cosine similarity is below threshold, the render is marked `fail` without paying for paid downstream QA. Lives at `skyyrose/elite_studio/quality/embedding_gate.py`. Conditional on a brand centroid file existing.

**Brand centroid**:
The mean image embedding of a set of approved hero shots, plus a percentile-based threshold derived from in-cluster similarity. **Currently global** (one centroid pooling all collections, 23 samples). Two encoders ship as parallel artifacts: CLIP (`brand_centroid.npz`, threshold 0.7631) and DINOv2 (`brand_centroid_dino.npz`, threshold 0.3905) — they have empirically complementary failure modes and the data argues for ensemble use rather than picking one (see `tasks/centroid-gate-measurement-analysis.md`, 2026-05-03). Per-collection split was considered and **measured against curated good/bad fixtures**; the data did not support the per-collection refactor and ADR-0002 is now flagged as measured-but-inconclusive on its original question. Stored as `.npz` (binary) with a `.metadata.json` sidecar (provenance).
_Avoid_: assuming the centroid is per-collection — it isn't.

**Ensemble gate** (proposed, not yet implemented):
A pre-QA filter that requires BOTH CLIP and DINOv2 centroids to accept a render. Empirically eliminates CLIP's 83% false-pass rate on raw product photography (DINOv2 catches all such cases) at the cost of stricter golden-fixture acceptance. Pending its own grilling pass — see `tasks/centroid-gate-measurement-analysis.md`.

**Visual regression gate**:
SSIM-based pixel-level comparison against approved goldens, with per-angle thresholds (detail shots stricter than full-body). Independent of the embedding gate — they catch different failure modes (semantic drift vs pixel drift). Lives at `skyyrose/elite_studio/quality/visual_regression.py`.

**Dual-agent QA gate**:
A consensus QA judge with `_PASS_THRESHOLD = 80`. Lives at `skyyrose/elite_studio/agents/quality_agent.py`. Distinct from both gates above — the dual-agent name is about the consensus mechanism (two judges agreeing), not about the gating layer.

### Catalog

**SKU**:
A short identifier like `br-001`, `sg-007`, `kids-002`, `lh-003`. The collection prefix (`br-`, `sg-`, `lh-`, `kids-`) maps 1:1 to a collection. Source of truth: `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`.

**Dossier**:
Per-product design specification at `wordpress-theme/skyyrose-flagship/data/dossiers/{name-slug}.md`. Carries the rich per-region branding spec (technique, dimensions, color, NEGATIVE list) the 3D RAS pipeline reads. Filenames are name-keyed, not SKU-keyed.
_Avoid_: "spec" (overloaded with eval specs), "manifest" (retired terminology — see Flagged ambiguities)

## Relationships

- A **compositor_node** invokes exactly one **CompositorAgent**
- A **CompositorAgent.composite()** runs six **Stages** in fixed order
- An **Embedding gate** is conditional: present when a **Brand centroid** `.npz` exists, absent otherwise
- The **Embedding gate**, **Visual regression gate**, and **Dual-agent QA gate** are independent — a render can pass one and fail another; they catch different failure modes
- A **SKU** has exactly one **Dossier** (hard-fails if missing — no silent fallback to `branding_spec`)

## Example dialogue

> **Engineer:** "The compositor pipeline rejected this render. Was it the embedding gate or the SSIM check?"
> **Pipeline owner:** "Both run independently. By 'the compositor pipeline' you mean the six **Stages** inside `CompositorAgent.composite()`, but the gates that flag failures live in `quality/`. Check `embedding_gate.py` for cosine-similarity rejections and `visual_regression.py` for SSIM-per-angle. The dual-agent **Quality Agent** is downstream of both."

## Flagged ambiguities

- "**Pipeline**" was used to mean (a) the LangGraph topology vision→generator→quality→compositor→finalize, AND (b) the compositor's internal six-stage flow. Resolved: outer = "the graph"; inner = "the compositor stages". The procedural `scripts/run_compositor_pipeline.py` is neither — it's a transitional CLI, see ADR-0001.
- "**Compositor**" was used to mean both **CompositorAgent** AND `scripts/run_compositor_pipeline.py`. Resolved: the script is transitional; **CompositorAgent** is canonical. ADR-0001.
- "**The brand centroid**" (singular, with definite article) was sometimes used as if there were one canonical centroid; sometimes implied per-collection centroids existed. Resolved: as-shipped is **one global centroid per encoder** (CLIP + DINOv2 = 2 files). Per-collection is deferred pending measurement data — ADR-0002.
- "**Manifest**" / "**catalog YAML**" referred to the retired `assets/product-masters/{catalog.yaml,manifest.json}` files. Resolved: source of truth is the CSV at `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`. The retired files MUST NOT be resurrected.
- "**Quality gate**" / "**QA gate**" — there are three independent ones (embedding, visual regression, dual-agent QA). Always disambiguate which one.
