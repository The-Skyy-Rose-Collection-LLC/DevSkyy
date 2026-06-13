# SkyyRose Element Schema (shared contract)

The single contract that `universal-learner` (writer) and `design-master` (reader) both implement.
`universal-learner` extracts elements into this shape; `design-master` queries them to assemble `gpt-image-2` prompts. One schema, two consumers — no code duplication.

This schema is grounded in two real artifacts (do not drift from them):
- **Input:** SkyyRose product dossiers — markdown + YAML frontmatter (`sku`, `name`, `collection`, `logo_reference`, `reference_image`) + zone-structured prose body (garment-type lock, Branding by placement zone, Negative, Scene direction). Source: `wordpress-theme/skyyrose-flagship/data/dossiers/*.md`.
- **Output target:** the production `gpt-image-2` prompt grammar in `scripts/oai_render/prompt.py` (`images.edit` mode, size `1024x1536`, `quality:high`, negatives baked inline as `DO NOT` text — gpt-image-2 has **no** `negative_prompt` API field, **no** `seed`).

## Element record

```json
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
```

### Field definitions

| Field | Type | Values / rule |
|-------|------|---------------|
| `element_id` | string | kebab-case, unique. Prefix by collection where applicable (`be-`/`lh-`/`sig-`/`kc-`/`common-`). |
| `prompt_fragment` | string | The literal text injected into a prompt. Written in gpt-image-2 style (declarative, comma-light, concrete). |
| `grammatical_position` | enum | `subject` (the garment), `presentation` (ghost/on-model/flatlay block), `view` (front/back directive), `lighting`, `background`, `material`, `fidelity`, `scene` (collection environment), `exclusion` (a `DO NOT` negative). Mirrors the `prompt.py` BASE_PROCEDURE slots. |
| `domain` | enum | `fashion_editorial` (primary), `product`, `portrait`, `interior`, `art`, `design`, `video`, `common`. |
| `collection_tags` | string[] | subset of `signature`, `black-rose`, `love-hurts`, `kids-capsule`. Empty = collection-agnostic. |
| `mode_tags` | string[] | subset of `ghost`, `on-model`, `flatlay` (match `prompt.py` presentation modes), plus `campaign`, `lifestyle` (broader composition intents). |
| `reusability_score` | int 1–10 | generic cross-context reuse (existing universal-learner scale). |
| `collection_specificity` | int 0–3 | bonus: how tightly bound to one collection's locked aesthetic. A BR-only element scores 3 even if not universal. |
| `brand_alignment` | int 0–3 | alignment with The Five (Kith / Oaklandish / Culture Kings / Fear of God / Palm Angels). |
| `gpt_image2_compatibility` | int 0–3 | known to render well in gpt-image-2 edit-mode grammar. |
| `brand_canon.validated` | bool | passed the canon-validation step. |
| `brand_canon.violation_flags` | string[] | e.g. `european-luxury-lineage`, `pastel-preppy`, `minimalist-corporate`, `cartoon`. Non-empty blocks commit without override. |
| `reference_labels` | string[] | Human-readable labels matching `reference_images[]` entries, e.g. `"image 1 — front real photo"`. |
| `is_patch` | bool | `true` for jersey SKUs that require the SPORT PATCH FIDELITY block in the prompt; `false` otherwise. |
| `founder_corrections` | string[] | Per-SKU verbatim review corrections from the founder. Empty array when none. |
| `source_type` | enum | `dossier`, `prompt`, `template`, `brand-doc`, `manual`. |
| `source_id` | string | the SKU (`br-004`), file path, or template id the element came from. |
| `added_date` | string | `YYYY-MM-DD`. |
| `version` | int | bump on edit. |
| `deprecated` | bool | true when retired (e.g. dossier corrected). |
| `superseded_by` | string\|null | `element_id` that replaces it. |

## Collection canon (locked — validation reference)

| Collection | accent hex | aesthetic keywords | collection scene (on-model) |
|------------|-----------|--------------------|------------------------------|
| `signature` | `#D4AF37` gold | origin/bedrock, confident West-Coast street-luxury, gold-on-dark, script anchor | Golden Gate + Bay skyline, golden hour |
| `black-rose` | `#C0C0C0` silver | armor, Oakland concrete, dark-on-dark, thorn motif, Cinzel restraint | Bay Bridge from Oakland shore, blue hour, black-rose garden |
| `love-hurts` | `#DC143C` crimson | Beast & rose, grief-as-love, heart+thorns, crimson/purple/burgundy | candlelit gothic château, Beast's POV |
| `kids-capsule` | `#B76E79` rose-gold | legacy/heir, no pastels/cartoons, regal scaled-down | regal gold-and-velvet throne room |

## Brand-canon validation (the guard)

- **Affirm** (raise `brand_alignment`): concrete/urban/Oakland, streetwear, luxury-athletic, sport-heritage, cinematic-desaturated, monogram-editorial.
- **Block** (`violation_flags`): European-luxury-house lineage (Bottega/Numéro/Hedi Slimane Celine/Rick Owens-register/Acne FW24/Givenchy-Tisci/032c/Off-White-early/Burberry-Imagined), pastel/preppy, minimalist-corporate, cartoon, mannequin-seams, stock-photo lighting.

## gpt-image-2 output contract (what design-master emits per render)

```json
{
  "sku": "br-004",
  "collection": "black-rose",
  "mode": "ghost",                  // ghost | on-model | flatlay
  "view": "front",                  // front | back
  "presentation_block": "...",      // grammatical_position=presentation fragment
  "view_directive": "...",          // grammatical_position=view fragment
  "background": "...",              // studio grey (ghost/flatlay) OR collection scene (on-model)
  "product_line": "PRODUCT: BLACK Rose Hoodie (SKU br-004) — Black Rose collection.",
  "reference_images": ["data/product-references/br-004-hoodie-real-front.jpeg"],
  "reference_labels": ["image 1 — front real photo"],
  "dossier_spec_path": "wordpress-theme/skyyrose-flagship/data/dossiers/black-rose-hoodie.md",
  "is_patch": false,
  "founder_corrections": [],
  "negative_guardrails": "DO NOT add text, watermarks, mockup labels ...",
  "size": "1024x1536",
  "quality": "high",
  "background_api": "auto",
  "estimated_cost_usd": 0.06,
  "ready_to_render": false          // flips true only after STOP-AND-SHOW y
}
```

The render call is `client.images.edit(model="gpt-image-2", image=[...refs...], prompt=<assembled>, size="1024x1536", quality="high", background="auto", n=1)`. design-master never calls it directly without the STOP-AND-SHOW manifest + `y`.
