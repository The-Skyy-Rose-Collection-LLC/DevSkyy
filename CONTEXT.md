# DevSkyy

Imagery, dossier, and storefront pipeline for SkyyRose luxury streetwear. This glossary captures terms whose meaning is non-obvious or has historically been used ambiguously in this codebase.

## Language

### Compositor

**CompositorAgent**:
The canonical scene compositor. Owns six stages (alpha → prompt-eng → relight → composite → shadows → QA) as private methods, exposes a single `composite(sku, image_path, scene_name, collection)` entry point. Lives at `skyyrose/elite_studio/agents/compositor_agent.py`. Currently a 68-line `pass_through` shell pending rebuild — see ADR-0001 and `docs/superpowers/plans/2026-05-02-compositor-agent-rebuild.md`.
_Avoid_: "the compositor script", "the compositor function", "the compositor module"

**compositor_node**:
The LangGraph node that delegates to `CompositorAgent.composite()`. Lives at `skyyrose/elite_studio/graph/nodes.py:318`. Glue and telemetry, not stage logic.
_Avoid_: "the compositor pipeline" (overloaded — see Flagged ambiguities)

**Stage**:
One of the six private methods inside `CompositorAgent.composite()`: alpha (BRIA RMBG), prompt-eng (Claude Opus), relight (libcom), composite (FLUX Fill / Kontext fallback chain), shadows (GPSDiffusion fallback to PIL gaussian), QA (Gemini visual gate). Stages are deterministic transforms, not separate agents.
_Avoid_: "step", "phase" (the project uses "phase" for milestone tracking — `Phase 1`, `Phase 1.5`, `Phase B1` etc.)

**Embedding gate**:
A pre-QA filter inserted between Stage 5 (shadows) and Stage 6 (QA). Scores the rendered image's CLIP embedding against the brand centroid for the SKU's collection; if the cosine similarity is below the threshold, the render is marked `fail` without paying for Gemini QA. Conditional on the per-collection brand centroid file existing — falls through to Gemini if not present.

**Brand centroid**:
The mean CLIP image embedding of the approved hero shots for one collection, plus a percentile-based threshold derived from in-cluster similarity. There are four brand centroids — one per collection (Black Rose, Love Hurts, Signature, Kids Capsule) — because each collection has a deliberately distinct aesthetic. Built from the catalog CSV (`front_model_image` field grouped by `collection`), not by globbing a directory. Stored as `.npz` files keyed by collection slug.
_Avoid_: "the brand centroid" (singular implies global — there is no global centroid)

### Catalog

**SKU**:
A short identifier like `br-001`, `sg-007`, `kids-002`, `lh-003`. The collection prefix (`br-`, `sg-`, `lh-`, `kids-`) maps 1:1 to a collection. Source of truth: `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`.

**Dossier**:
Per-product design specification at `wordpress-theme/skyyrose-flagship/data/dossiers/{name-slug}.md`. Carries the rich per-region branding spec (technique, dimensions, color, NEGATIVE list) the 3D RAS pipeline reads. Filenames are name-keyed (e.g., `black-rose-crewneck.md`), not SKU-keyed.
_Avoid_: "spec" (overloaded with eval specs), "manifest" (retired terminology — see Flagged ambiguities)

## Relationships

- A **compositor_node** invokes exactly one **CompositorAgent**
- A **CompositorAgent.composite()** runs six **Stages** in fixed order
- An **Embedding gate** is conditional: present when the per-collection **Brand centroid** `.npz` exists, absent otherwise
- A **Brand centroid** belongs to exactly one collection; the **Embedding gate** loads the centroid keyed by the `collection` parameter passed to `composite()`
- A **SKU** has exactly one **Dossier** (hard-fails if missing — no silent fallback to `branding_spec`)

## Example dialogue

> **Engineer:** "The compositor pipeline is slow on Stage 4 — should I parallelize the FLUX calls?"
> **Pipeline owner:** "By 'compositor pipeline' you mean the six stages inside `CompositorAgent.composite()`, not the LangGraph (`vision → generator → quality → compositor → finalize`). Yes, parallelize the FLUX retries within Stage 4 — but the per-stage budget is owned by the agent, not the node."

## Flagged ambiguities

- "**Pipeline**" was used to mean (a) the LangGraph topology vision→generator→quality→compositor→finalize, AND (b) the compositor's internal six-stage flow. Resolved: outer = "the graph" / "the LangGraph pipeline"; inner = "the compositor stages". The procedural `scripts/run_compositor_pipeline.py` is neither — it's a transitional CLI, see ADR-0001.
- "**Compositor**" was used to mean both **CompositorAgent** AND `scripts/run_compositor_pipeline.py`. Resolved: the script is transitional; **CompositorAgent** is canonical. ADR-0001.
- "**Manifest**" / "**catalog YAML**" referred to the retired `assets/product-masters/{catalog.yaml,manifest.json}` files. Resolved: source of truth is the CSV at `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`. The retired files MUST NOT be resurrected.
- "**Override**" / "**ML-generated dossier**" referred to the retired `skyyrose/assets/data/prompts/overrides/{sku}.json` parallel store. Resolved: hallucination-prone, replaced by Corey-authored dossiers. CI rejects any code re-referencing the path.
