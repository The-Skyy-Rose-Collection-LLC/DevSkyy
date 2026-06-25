---
name: universal-learner
description: Extracts reusable prompt elements from any input source — SkyyRose dossiers, gpt-image-2 prompts, brand docs, and design templates — into a structured element library aligned with the SkyyRose brand canon and gpt-image-2 output grammar. Supports SKU-aware dossier ingestion, brand-canon validation, human-review diff gating, and manifest export for design-master consumption.
---

# Universal Learner

**Version**: 2.0
**Architecture**: classify → domain → extract → tag → brand-validate → score → dedup → diff-gate → write → report
**Mode**: Semi-automatic (diff shown for human approval before any write)
**Schema contract**: `references/element-schema.md` (shared with design-master — do not drift)
**Seed corpus output**: `references/skyyrose-seed-elements.json` (produced by the seed ingestion procedure below)

---

## Supported Domains

Eight domains, all mapped to the schema `domain` field:

| domain | Sub-categories |
|--------|---------------|
| `fashion_editorial` | `garment_silhouette`, `fabric_texture`, `colorway_descriptor`, `construction_detail`, `model_direction`, `location_set`, `editorial_lighting` |
| `product` | product types, materials, photography techniques |
| `portrait` | lighting setups, pose, skin tone, expression |
| `interior` | room type, furniture, architectural detail |
| `art` | art style, medium, special effects |
| `design` | layout, typography, graphic effects |
| `video` | motion type, transition, temporal style |
| `common` | cross-domain photography/composition techniques |

`fashion_editorial` is the primary domain for all SkyyRose inputs. When a source touches multiple domains, emit elements in each domain with their own `domain` field.

---

## Invocation Modes

### Mode A — Single prompt or text snippet

```
/universal-learner learn: [paste full prompt text]
```

### Mode B — SKU dossier ingestion (primary SkyyRose mode)

```
/universal-learner dossier: br-004
```

Reads `wordpress-theme/skyyrose-flagship/data/dossiers/<slug>.md`, parses YAML frontmatter + zone-structured body, extracts and tags elements with SKU provenance.

### Mode C — Batch dossier sweep

```
/universal-learner batch-dossiers
```

Iterates all 33 SKU entries from the per-collection SOT JSONs at `data/collections/*.json` (products[].sku), ingests each dossier, runs full pipeline. Produces one combined diff for review before writing.

### Mode D — gpt-image-2 prompt extraction

```
/universal-learner gpt-image-2: [paste prompt text or point to scripts/oai_render/prompt.py]
```

Parses the `BASE_PROCEDURE` / `COLLECTION_SCENES` grammar, assigns `grammatical_position` to each parsed clause, and emits elements tagged with `source_type: "prompt"`.

### Mode E — Brand document ingestion

```
/universal-learner brand-doc: [file path]
```

Accepts `knowledge-base/seed/from-interview.md`, `docs/brand/collection-stories.md`, or any brand/design-spec markdown. Extracts editorial language, scene vocabulary, and canonical aesthetics as `source_type: "brand-doc"` elements.

### Mode F — Design system / template ingestion

```
/universal-learner design-system: [file path or pasted content]
```

Auto-detected when input contains structural keywords: `system`, `framework`, `workflow`, `template`, `module`. Stores both extracted elements and the full raw content (in `visual_reference`) as a design-template record.

### Mode G — Seed corpus procedure

```
/universal-learner seed
```

Runs batch-dossiers + brand-doc ingestion for `knowledge-base/seed/from-interview.md` and `docs/brand/collection-stories.md` as a single founding sweep. Output written to `references/skyyrose-seed-elements.json`. See "Seed Corpus Procedure" section below.

### Mode H — Manifest export

```
/universal-learner export [--collection <slug>] [--mode <ghost|on-model|flatlay>]
```

Queries the element library and emits a gpt-image-2 element manifest consumable by design-master. See "Manifest Export" section below.

---

## Pipeline — Step by Step

```
Input
  │
  ▼
Step 0: Source Classification
  │   Determine input type: dossier | prompt | brand-doc | design-system | raw-text
  │   For dossiers: parse YAML frontmatter (sku, name, collection, logo_reference,
  │     reference_image) + zone-structured body sections
  │   For gpt-image-2 mode: detect BASE_PROCEDURE slot labels
  │   Output: { source_type, source_id, collection_hint, raw_sections }
  │
  ▼
Step 1: Domain Classification
  │   Assign primary domain and optional secondary domains.
  │   SkyyRose dossiers → primary: fashion_editorial
  │   Sub-category selection from the 7 fashion_editorial sub-cats:
  │     garment_silhouette, fabric_texture, colorway_descriptor,
  │     construction_detail, model_direction, location_set, editorial_lighting
  │   Output: { primary: "fashion_editorial", secondary: [], sub_categories: [] }
  │
  ▼
Step 2: Element Extraction
  │   Extract all reusable prompt fragments from the source.
  │   Per domain, extract into the schema shape:
  │     element_id, prompt_fragment, grammatical_position, domain
  │   For dossier mode, read zone sections:
  │     • Garment-type lock → subject + material elements
  │     • Branding zones (front-chest / back / sleeves / pocket / collar) →
  │       construction_detail + colorway_descriptor elements
  │     • Negative list → exclusion elements (grammatical_position: "exclusion",
  │       prompt_fragment prefixed with "DO NOT")
  │     • Scene direction → scene + background + lighting elements
  │   For gpt-image-2 mode, map parsed clauses to grammatical_position slots:
  │     subject | presentation | view | lighting | background |
  │     material | fidelity | scene | exclusion
  │   Output: List[partial element records]
  │
  ▼
Step 3: Auto-Tagging
  │   Assign collection_tags using keyword signals:
  │     silver | armor | concrete | thorn | Cinzel → black-rose
  │     crimson | bloodline | grief | beast | gothic → love-hurts
  │     gold | origin | bedrock | confident | script → signature
  │     rose-gold | heir | regal | legacy | velvet → kids-capsule
  │   Assign mode_tags from presentation context:
  │     ghost | on-model | flatlay | campaign | lifestyle
  │   Attach sku and collection provenance from YAML frontmatter when in dossier mode.
  │   Output: elements with collection_tags and mode_tags populated
  │
  ▼
Step 3.5: Brand-Canon Validation  ← GUARD — runs before scoring, blocks on violations
  │
  │   AFFIRM signals (raise brand_alignment):
  │     concrete, urban, Oakland, streetwear, luxury-athletic, sport-heritage,
  │     cinematic-desaturated, monogram-editorial, West-Coast, thorn-motif,
  │     armor, Bay Bridge, golden hour, blue hour, candlelit-gothic
  │
  │   BLOCK signals → populate violation_flags:
  │     european-luxury-lineage
  │       (triggers: Bottega, Numéro, Hedi Slimane, Celine minimalist, Rick Owens
  │        register, Acne FW24 palette, Givenchy-Tisci, 032c, Off-White-early,
  │        Burberry-Imagined)
  │     pastel-preppy
  │       (triggers: pastel palette outside kids-capsule, preppy, ivy-league,
  │        country-club, polo-casual)
  │     minimalist-corporate
  │       (triggers: corporate minimalism, Helvetica-white-space, SaaS aesthetic,
  │        stock-photo lighting)
  │     cartoon
  │       (triggers: cartoon, illustrated, cel-shaded, anime, kawaii)
  │     mannequin-seams
  │       (triggers: visible seams, headless mannequin artifact, seam line)
  │
  │   RULE: if violation_flags is non-empty → set brand_canon.validated = false
  │     The element is held in a FLAGGED state.
  │     It will appear in the diff gate with a REJECT marker unless the user
  │     provides an explicit override (e.g., "OVERRIDE: approve flagged").
  │     No flagged element is written to the library without override.
  │
  │   Output: elements with brand_canon { validated, violation_flags } set
  │
  ▼
Step 4: Scoring
  │   Compute four independent scores per element:
  │
  │   reusability_score (int 1–10)
  │     Cross-context generic reuse:
  │       9–10  Universal across all collections and modes
  │       7–8   Domain-wide (any SkyyRose fashion shoot)
  │       5–6   Collection-specific but transferable across SKUs
  │       3–4   SKU-specific, limited reuse
  │       1–2   One-off; extract only if forced by source type
  │
  │   collection_specificity (int 0–3)
  │     0  Collection-agnostic
  │     1  Leans toward one collection but not locked
  │     2  Strongly associated with one collection
  │     3  Inseparable from exactly one collection's canon
  │
  │   brand_alignment (int 0–3)
  │     0  Neutral; no The-Five signal
  │     1  Weak alignment (one signal: e.g. streetwear but not Oakland)
  │     2  Clear alignment (urban-West-Coast, luxury-athletic, sport-heritage)
  │     3  Deep alignment (concrete + Oakland + garment protagonist + The Five)
  │     Note: violation_flags forces brand_alignment = 0 regardless of other signals.
  │
  │   gpt_image2_compatibility (int 0–3)
  │     0  Fragment likely to confuse the model (abstract, contradictory)
  │     1  Usable but may require tuning
  │     2  Renders reliably in edit-mode grammar
  │     3  Known-good against gpt-image-2 — used in production prompts
  │
  │   Output: all four scores attached to each element
  │
  ▼
Step 5: Deduplication
  │   Before assigning a new element_id, search existing library for:
  │     • Exact prompt_fragment match → skip (already exists)
  │     • High semantic overlap (>80% token overlap, same grammatical_position) →
  │       flag as MODIFY candidate (propose merging prompt_fragment variants)
  │     • Deprecated element with same concept → propose superseded_by linkage
  │   Output: deduplicated list; new elements, modify candidates, skip list
  │
  ▼
Step 6: Human-Review Diff Gate  ← NO WRITES UNTIL APPROVED
  │
  │   Emit a structured diff. Format per element:
  │
  │   [ADD] element_id: <id>
  │     prompt_fragment : "<text>"
  │     grammatical_position: <slot>
  │     domain / sub_category: <value>
  │     collection_tags: [<tags>]
  │     scores: reusability=N  specificity=N  alignment=N  gpt2=N
  │     brand_canon: validated=<bool>  flags=[<list or empty>]
  │     source: <source_type> / <source_id>
  │     → [APPROVE] / [REJECT] / [MODIFY: <suggested change>]
  │
  │   [MODIFY] element_id: <existing-id>
  │     current: "<old fragment>"
  │     proposed: "<new fragment>"
  │     reason: <why merging or updating>
  │     → [APPROVE] / [REJECT]
  │
  │   [DEPRECATE] element_id: <id>
  │     reason: <dossier corrected / superseded / canon violation>
  │     superseded_by: <new-id or null>
  │     → [APPROVE] / [REJECT]
  │
  │   Flagged (violation_flags non-empty) elements always receive [REJECT] by default.
  │   User may override with explicit "OVERRIDE: approve <element_id>".
  │
  │   WAIT for user response before proceeding to Step 7.
  │
  ▼
Step 7: Library Write
  │   Apply only the [APPROVE]d items from the diff.
  │   For each ADD:
  │     • Assign element_id (kebab-case, prefix: be-/lh-/sig-/kc-/common-)
  │     • Set added_date = today (YYYY-MM-DD)
  │     • Set version = 1, deprecated = false, superseded_by = null
  │     • Write to skyyrose-seed-elements.json (or active library file)
  │   For each MODIFY:
  │     • Increment version
  │     • Update prompt_fragment, scores as approved
  │   For each DEPRECATE:
  │     • Set deprecated = true, superseded_by = <new-id>
  │   For design-system mode:
  │     • Also write a design-template record with full raw content in visual_reference
  │
  ▼
Step 8: Learning Report
    Emit the post-write summary:
      • Elements added / modified / deprecated / skipped
      • Domain breakdown
      • Brand-canon violations caught (with element count)
      • Average scores across the new batch
      • Provenance summary (source files / SKUs ingested)
```

---

## SKU-Aware Dossier Ingestion

Dossier path: `wordpress-theme/skyyrose-flagship/data/dossiers/<slug>.md`

### YAML frontmatter fields consumed

```yaml
sku: br-004
name: "Black Rose Hoodie"
collection: black-rose
logo_reference: "assets/images/logos/black-rose-logo.png"
reference_image: "data/product-references/br-004-hoodie-real-front.jpeg"
```

All five fields are mapped into provenance:
- `source_type: "dossier"`
- `source_id: <sku>`
- `collection_tags` seeded from `collection` field (no guessing required)
- `reference_image` and `logo_reference` emitted into the manifest export as `reference_images`

### Zone-to-grammatical_position mapping

| Dossier zone | Extracted as grammatical_position |
|---|---|
| Garment-type lock | `subject` |
| Materials / fabric description | `material` |
| Branding zones (front-chest / back / sleeves / pocket / collar) | `construction_detail` sub-cat |
| Colorway / accent description | `colorway_descriptor` sub-cat |
| Scene direction | `scene` + `background` + `lighting` |
| Negative list items | `exclusion` (prefixed "DO NOT") |

### Collection SOT JSONs

`data/collections/*.json` → `products[]` with fields: `sku`, `name`, `dossier`, `references`

The 33-SKU SOT is the authoritative index for batch mode. Never substitute a memory-based list.

---

## gpt-image-2 Extraction Mode

When the source is a gpt-image-2 prompt or `scripts/oai_render/prompt.py`:

Parse by BASE_PROCEDURE slot labels:

| Prompt clause pattern | grammatical_position |
|---|---|
| `PRODUCT: <garment> (SKU <id>)` | `subject` |
| `ghost / on-model / flatlay` presentation block | `presentation` |
| `front view / back view` directive | `view` |
| lighting description (studio / golden hour / blue hour / candlelit) | `lighting` |
| background / location description | `background` |
| fabric / texture clause | `material` |
| `high-fidelity / photorealistic / 100 megapixel` | `fidelity` |
| `COLLECTION SCENE:` block | `scene` |
| `DO NOT ...` clause | `exclusion` |

Tag each element with `source_type: "prompt"` and `source_id: "scripts/oai_render/prompt.py:<label>"`.

---

## Collection Auto-Tagging Reference

| Keyword signals in source | → collection_tag | accent |
|---|---|---|
| silver, armor, concrete, thorn, Cinzel, Bay Bridge, blue hour, dark-on-dark | `black-rose` | #C0C0C0 |
| crimson, bloodline, grief, beast, gothic, château, candlelit, burgundy | `love-hurts` | #DC143C |
| gold, origin, bedrock, confident, West-Coast, golden hour, script-anchor | `signature` | #D4AF37 |
| rose-gold, heir, regal, legacy, velvet, throne, scaled-down | `kids-capsule` | #B76E79 |

Empty `collection_tags` = collection-agnostic element (valid and common for common/product/lighting elements).

---

## Brand-Canon Validation Reference

### Affirm — raises brand_alignment

- Concrete / urban texture
- Oakland / Bay Area geography
- Streetwear silhouette
- Luxury-athletic / sport-heritage construction
- Cinematic-desaturated color grade
- Monogram-editorial composition
- West-Coast street-luxury confidence
- Thorn / rose motif (all collections)
- The Five reference aesthetics: Kith / Oaklandish / Culture Kings / Fear of God / Palm Angels

### Block — populates violation_flags, prevents write without override

| Flag key | Trigger terms |
|---|---|
| `european-luxury-lineage` | Bottega Veneta weave, Numéro editorial, Hedi Slimane Celine, Rick Owens architectural drape, Acne FW24 palette, Givenchy-Tisci, 032c, Off-White-early, Burberry-Imagined |
| `pastel-preppy` | pastel palette (outside kids-capsule hero accent), preppy, ivy-league, country-club, polo-casual |
| `minimalist-corporate` | corporate minimalism, Helvetica white-space layout, SaaS product-shot aesthetic, stock-photo lighting rig |
| `cartoon` | cartoon, illustrated, cel-shaded, anime, kawaii, comic-book |
| `mannequin-seams` | visible seam lines, headless-mannequin artifact |

---

## Provenance Fields (per schema)

Every element carries full provenance per `references/element-schema.md`:

```json
{
  "source_type": "dossier",
  "source_id": "br-004",
  "added_date": "2026-06-13",
  "version": 1,
  "deprecated": false,
  "superseded_by": null
}
```

`source_type` enum: `dossier` | `prompt` | `template` | `brand-doc` | `manual`

On edit: bump `version`. On retirement: set `deprecated: true`, set `superseded_by` to the replacing element_id or null.

---

## Seed Corpus Procedure

The founding corpus is built from these sources (run once, then maintained via incremental ingestion):

| Source | Mode | SKUs / docs |
|---|---|---|
| All 33 dossiers in `data/collections/*.json` | batch-dossiers | 33 SKUs |
| `knowledge-base/seed/from-interview.md` | brand-doc | founder voice, brand DNA |
| `docs/brand/collection-stories.md` | brand-doc | per-collection narrative canon |

**Procedure:**

1. Run `Mode G: /universal-learner seed`
2. Pipeline ingests all three source groups sequentially.
3. A single combined diff is emitted for human review.
4. After approval, elements are written to `references/skyyrose-seed-elements.json`.
5. This file is the seed corpus — `design-master` and `universal-learner` both reference it.
6. The file is NOT produced or overwritten by this skill directly during non-seed runs; incremental additions are staged for review first.

The seed JSON output path is `references/skyyrose-seed-elements.json`. The schema for every record in that file is defined in `references/element-schema.md`. Do not create or overwrite it without running the full seed procedure and completing the diff-gate approval.

---

## Manifest Export

The manifest export (`Mode H`) produces the gpt-image-2 element manifest that `design-master` consumes to assemble render prompts.

Format (array of element records per schema, filtered and sorted):

```json
[
  {
    "element_id": "be-bg-blue-hour-bay-bridge",
    "prompt_fragment": "the Bay Bridge silhouetted behind, shot from the Oakland shore at blue hour, framed by a moody black-rose garden",
    "grammatical_position": "background",
    "domain": "fashion_editorial",
    "collection_tags": ["black-rose"],
    "mode_tags": ["on-model", "campaign"],
    "reusability_score": 7,
    "collection_specificity": 3,
    "brand_alignment": 3,
    "gpt_image2_compatibility": 3,
    "brand_canon": { "validated": true, "violation_flags": [] },
    "source_type": "prompt",
    "source_id": "scripts/oai_render/prompt.py:COLLECTION_SCENES",
    "added_date": "2026-06-13",
    "version": 1,
    "deprecated": false,
    "superseded_by": null
  }
]
```

Export filters:
- `--collection <slug>`: restrict to elements with that collection_tag (or collection-agnostic elements)
- `--mode <ghost|on-model|flatlay>`: restrict to elements whose mode_tags include the target
- Deprecated elements are always excluded from export
- Flagged elements (brand_canon.validated = false) are always excluded from export

design-master reads this manifest and assembles `grammatical_position` slots into the `images.edit` call:
`client.images.edit(model="gpt-image-2", image=[...refs...], prompt=<assembled>, size="1024x1536", quality="high", background="auto", n=1)`

---

## Learning Report Format

```
# Universal Learner — Learning Report

Date      : YYYY-MM-DD
Source(s) : <source_type> / <source_id>
Mode      : <A–H>

## Domain Breakdown

primary  : fashion_editorial
  sub-cats: garment_silhouette(N), fabric_texture(N), colorway_descriptor(N),
            construction_detail(N), model_direction(N), location_set(N), editorial_lighting(N)
secondary: product(N), common(N)

## Diff Results

  ADD      : N elements approved / N rejected / N modified
  MODIFY   : N elements updated
  DEPRECATE: N elements retired

## Brand-Canon Report

  Validated     : N elements
  Flagged       : N elements
    european-luxury-lineage : N
    pastel-preppy           : N
    minimalist-corporate    : N
    cartoon                 : N
    mannequin-seams         : N
  Overrides applied: N

## Score Summary (approved batch)

  reusability avg        : N.N / 10
  collection_specificity : N.N / 3
  brand_alignment        : N.N / 3
  gpt_image2_compat      : N.N / 3

## Provenance

  SKUs ingested : [list]
  Docs ingested : [list]

## Library State

  Total elements (post-write): N
  By collection tag:
    signature    : N
    black-rose   : N
    love-hurts   : N
    kids-capsule : N
    agnostic     : N
```

---

## Scoring Reference

### reusability_score (1–10)

| Score | Criterion |
|---|---|
| 9–10 | Universal — cross-collection, cross-mode, cross-domain |
| 7–8 | Domain-wide — any SkyyRose fashion shoot, any collection |
| 5–6 | Collection-transferable — fits multiple SKUs in one collection |
| 3–4 | SKU-specific — tied to one garment's details |
| 1–2 | One-off — extract only when source_type demands preservation |

### collection_specificity (0–3)

| Score | Criterion |
|---|---|
| 0 | Collection-agnostic |
| 1 | Leans toward one collection, not locked |
| 2 | Strongly associated with one collection's aesthetic |
| 3 | Inseparable from exactly one collection's locked canon |

### brand_alignment (0–3)

| Score | Criterion |
|---|---|
| 0 | Neutral; no The-Five signal. Always 0 when violation_flags non-empty. |
| 1 | Weak: one affirmation signal (e.g. streetwear but not Oakland-anchored) |
| 2 | Clear: urban-West-Coast or luxury-athletic or sport-heritage confirmed |
| 3 | Deep: concrete + Oakland + garment protagonist + The-Five reference |

### gpt_image2_compatibility (0–3)

| Score | Criterion |
|---|---|
| 0 | Fragment likely to confuse the model (abstract, contradictory, or over-specified) |
| 1 | Usable but may require prompt tuning before production use |
| 2 | Renders reliably in images.edit mode grammar |
| 3 | Known-good — used in production prompts in scripts/oai_render/prompt.py |

---

## Acceptance Criteria

- Correctly identifies and assigns `fashion_editorial` as primary domain for all SkyyRose inputs
- Parses YAML frontmatter (sku / name / collection / logo_reference / reference_image) from dossiers
- Tags elements with correct collection_tag from keyword signals AND from frontmatter
- Brand-canon validation catches all BLOCK-list terms; flagged elements never written without override
- All four scores (reusability / collection_specificity / brand_alignment / gpt_image2_compatibility) computed per element
- gpt-image-2 extraction mode assigns `grammatical_position` correctly from BASE_PROCEDURE slot labels
- All elements carry provenance fields (source_type / source_id / added_date / version / deprecated / superseded_by)
- Human-review diff gate emitted before every write; no element written without explicit [APPROVE]
- Seed corpus procedure documented; output path `references/skyyrose-seed-elements.json` referenced
- Manifest export produces schema-valid JSON consumable by design-master
- All element records conform to `references/element-schema.md`
- No deprecated elements appear in manifest export
- No flagged elements appear in manifest export

---

**Status**: Active
**Last updated**: 2026-06-13
**Schema contract**: `references/element-schema.md`
**Seed corpus**: `references/skyyrose-seed-elements.json`
**Consumers**: design-master (manifest reader), oai_render pipeline (prompt assembler)
