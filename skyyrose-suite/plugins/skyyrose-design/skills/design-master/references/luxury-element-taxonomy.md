# SkyyRose Luxury Fashion Element Taxonomy

Vocabulary reference for prompt composition. Elements are grouped by
`grammatical_position` (the slot they fill in the BASE_PROCEDURE order defined
in `scripts/oai_render/prompt.py`). Each entry is tagged with applicable
collections and presentation modes.

All elements in this taxonomy pass the brand-canon guard — none carry
`violation_flags`. The locked-out European-luxury-house register
(Bottega/Numéro/Hedi Slimane Celine/Rick Owens/Acne FW24/Givenchy-Tisci/032c/Off-White-early/Burberry-Imagined)
is deliberately absent. The Five affirmed style anchors (Kith, Oaklandish,
Culture Kings, Fear of God, Palm Angels) inform the vocabulary throughout.

---

## 1. Subject / Garment Silhouettes

These describe the garment form and sit in the `subject` position — usually
derived from the dossier garment-type lock, not selected from the library
independently, but listed here for freeform-request assembly.

| Term | Description | Collections | Modes |
|------|-------------|-------------|-------|
| heavyweight cotton fleece pullover hoodie | Relaxed-fit, kangaroo pocket, ribbed cuffs and hem, tonal drawstring | black-rose, love-hurts, signature | ghost, on-model |
| heavyweight crewneck sweatshirt | No hood, ribbed collar/cuffs/hem, clean chest zone | black-rose, signature | ghost, on-model |
| relaxed-fit jogger pant | Matching fleece bottom, ribbed ankle cuffs, elastic drawstring waist | black-rose, love-hurts, signature | ghost, on-model |
| satin bomber jacket | Glossy satin shell, ribbed collar/cuffs/hem, snap or zip closure | love-hurts, signature | ghost, on-model |
| sherpa jacket | Thick sherpa pile shell, snap closure, relaxed streetwear cut | black-rose, signature | ghost, on-model |
| nylon windbreaker | Technical nylon shell, zip placket, utility feel, lightweight | signature, black-rose | ghost, on-model |
| basketball shorts | Mid-thigh length, mesh or satin, elastic waist, brand side panel | black-rose, love-hurts | ghost, on-model |
| sport jersey | Cut-and-sew athletic silhouette, mesh panels, embroidered patch at chest | black-rose | ghost, on-model |
| colorblock hoodie set | Two-tone blocked hoodie and coordinating jogger, kids-scale proportions | kids-capsule | ghost, on-model |
| embroidered patch cap | Structured or unstructured cap with raised-embroidery brand patch | black-rose, signature | ghost, flatlay |

---

## 2. Material / Fabric Descriptors

Fill the `material` slot (MATERIAL line in BASE_PROCEDURE). These describe
surface texture and must match the spec — do not invent fabric for a SKU.

| Term | Surface feel | Use in prompt | Collections | Modes |
|------|-------------|---------------|-------------|-------|
| heavyweight cotton fleece | Soft, matte, dimensionally stable | "heavyweight cotton fleece must look soft, dense, and matte" | all | ghost, on-model, flatlay |
| glossy satin shell | Light-catching, smooth, liquid sheen | "satin shell must read glossy and clearly light-catching — not matte, not dull" | love-hurts, signature | ghost, on-model |
| sherpa pile | Thick visible pile, textured, warm-looking | "sherpa must show visible, lofty pile — not flat fleece" | black-rose, signature | ghost, on-model |
| smooth technical nylon | Clean surface, subtle sheen, structured | "nylon must look smooth and technical, not fabric-y" | signature, black-rose | ghost, on-model |
| mesh athletic fabric | Open-weave, dimensional, breathable-looking | "mesh panels must read as open-weave athletic mesh, not a solid panel" | black-rose, love-hurts | ghost, on-model |
| ribbed knit | Visible welt rib, elastic recovery texture | "ribbed cuffs and hem must show clear welt texture, not smooth jersey" | all | ghost, on-model |
| woven label | Fine woven-thread texture, tight weave, slightly raised | "interior woven label must read as woven fabric, not printed" | all | ghost |
| embroidery | Raised thread work, dimensional, slight sheen on thread top | "embroidered logo must read as raised thread work with dimensional texture" | all | ghost, on-model |
| heat-transfer vinyl | Smooth surface application, slight edge lift possible | "HTV graphic must look smooth and flat against the fabric, not printed-into" | signature, kids-capsule | ghost, on-model |
| sublimation print | All-over graphic fully integrated into fabric | "sublimated panel must look printed-into the fabric, no surface relief" | love-hurts, kids-capsule | ghost, on-model |

---

## 3. Presentation Modifiers

Fill the `presentation` slot. These expand or constrain the PRESENTATION block
for editorial/campaign work beyond the three base modes.

| Term | Description | Collections | Modes |
|------|-------------|-------------|-------|
| ghost-mannequin invisible form | Standard ghost: no person, no hanger, 3D shape preserved | all | ghost |
| flatlay top-down seamless | Top-down, garment neatly arranged, no wrinkles, seamless surface | all | flatlay |
| full-body fashion model front-facing | Standard on-model, head-to-hem, single look | all | on-model |
| three-quarter front-left model pose | Slight rotation showing left side, front logo visible, dynamic without losing readability | black-rose, signature | on-model |
| model facing away rear-facing | For back-view on-model; rear camera, model back visible | black-rose, love-hurts | on-model |
| editorial stillness | Model static, composed, low-energy pose — armor-quiet, not performative | black-rose | on-model |
| confident swagger lean | Slight weight shift, one shoulder dropped — effortless West Coast energy | signature | on-model |
| regal upright stance | Erect posture, chin level, young-royalty composure | kids-capsule | on-model |
| intimate close pose | Closer crop, emotionally charged body language — grief register | love-hurts | on-model |

---

## 4. Lighting

Fill the `lighting` slot (LIGHTING line in BASE_PROCEDURE). The base procedure
uses a universal lighting instruction; these elements are for editorial overrides.

| Term | Description | Collections | Modes |
|------|-------------|-------------|-------|
| soft even studio key | Diffused frontal key, subtle directional fill, gentle natural shadow | all | ghost, flatlay |
| Rembrandt portrait light | 45-degree key, triangle on shadow-side cheek, deep shadow on far side | black-rose, love-hurts | on-model |
| blue-hour ambient | Cool blue environmental light from the open sky at dusk — no direct sun | black-rose | on-model |
| golden-hour side rim | Warm orange-gold sun from low on one side, long cast shadows | signature | on-model |
| candlelight warm ambient | Flickering warm orange fill, high contrast, deep background shadows | love-hurts | on-model |
| cinematic overhead throne light | Warm overhead chandelier key, rich velvet shadows below, royal feel | kids-capsule | on-model |
| split lighting dramatic | Hard split: one side lit, one side in full shadow — clean halves | black-rose | on-model |
| low-key editorial ambient | Underexposed ambient fill, garment lit by key only, dark negative space | black-rose, love-hurts | on-model |
| natural diffuse overcast | Soft flat outdoor daylight, no directional shadows, even across garment | signature | on-model |
| product-card studio flat | Maximum even light, minimum shadow depth — clinical clarity for e-com | all | ghost, flatlay |

---

## 5. Background / Scene

Fill the `background` slot. For ghost/flatlay always use the clean studio
description. For on-model use the COLLECTION_SCENES. These elements add
specificity for editorial requests beyond the base scenes.

| Term | Description | Collections | Modes |
|------|-------------|-------------|-------|
| clean studio light-grey seamless | Neutral light-grey studio, no props, no scene — product-card default | all | ghost, flatlay |
| Bay Bridge Oakland shore blue hour | Bay Bridge silhouetted, Oakland shore foreground, deep blue sky, rose garden | black-rose | on-model |
| black-rose garden foreground | Dark rose blooms in deep shadow, out-of-focus, atmospheric | black-rose | on-model |
| gothic château candlelit interior | Arched stone hallways, heavy drapes, iron chandeliers, warm pools of candle | love-hurts | on-model |
| Beast's POV gothic interior | Camera at beast-eye-level looking across a dark ornate room — narrative POV | love-hurts | on-model |
| Golden Gate bridge golden hour | Iconic orange span in warm late-afternoon haze, bay water below | signature | on-model |
| Bay Area skyline golden hour | City skyline across the bay, warm haze, confident urban backdrop | signature | on-model |
| throne room gold velvet regal | Ornate throne, velvet curtains, gold and burgundy, grand chandelier | kids-capsule | on-model |
| Oakland concrete wall texture | Raw poured-concrete wall, slight aggregate texture, neutral mid-tone | black-rose, signature | on-model, flatlay |
| brick wall urban texture | Worn red/grey brick, street-level grit, natural ambient light | black-rose, signature | on-model |
| dark studio negative space | Nearly black background, model lit from one side — minimal environment | black-rose, love-hurts | on-model |

---

## 6. Fidelity / Quality Modifiers

Fill the `fidelity` slot or reinforce the FIDELITY/PHOTOREALISM lines.
Use in editorial prompts to emphasize specific quality requirements.

| Term | Description | Collections | Modes |
|------|-------------|-------------|-------|
| exact silhouette lock | Garment silhouette must match reference exactly — no reinterpretation | all | ghost, on-model |
| embroidery thread fidelity | Every thread color and stitch direction must match the reference photo | all | ghost, on-model |
| patch interior verbatim | All text, numerals, emblems inside the patch must be reproduced exactly | black-rose | ghost, on-model |
| logo placement lock | Logo position relative to pocket/seam must match reference exactly | all | ghost, on-model |
| fabric drape natural | Natural gravity-driven drape — no artificially stiff or posed fabric | all | ghost, on-model |
| seam visibility real | Real sewn seams visible at appropriate scale — not smooth-blended | all | ghost, on-model |
| colorway fidelity true | Reproduce colorway from reference — no hue shift, no oversaturation | all | ghost, on-model, flatlay |
| tech-flat to photorealistic | References are flat vector tech flats — output must be dimensional and photographic | all | ghost |
| no invented elements | Render ONLY what is in the reference and spec — nothing added or embellished | all | all |

---

## 7. Exclusion / Negatives

These map to the `exclusion` grammatical position. They are injected as
`DO NOT ...` sentences in the NEGATIVE_GUARDRAILS block. The base NEGATIVE_GUARDRAILS
already covers the core exclusions; these are additional per-SKU or per-mode
negatives for editorial use.

| Term | DO NOT sentence | Collections | Modes |
|------|----------------|-------------|-------|
| no extra garments | DO NOT add any garment, accessory, or clothing item not in the spec. | all | all |
| no text watermarks | DO NOT add text, watermarks, mockup labels, price tags, or size tags. | all | all |
| no collage panels | DO NOT produce a multi-panel image, split-screen, collage, or grid. | all | all |
| no brand bleed | DO NOT add any logo, graphic, or branding element not physically present on the garment. | all | all |
| no back panel in front view | DO NOT render the back of the garment when the VIEW directive specifies front. | all | ghost, on-model |
| no white ribbing on BR hoodie | DO NOT render white ribbed trim on the Black Rose Hoodie — cuffs and hem are tonal black. | black-rose | ghost, on-model |
| no rose on back | DO NOT place any rose, logo, or graphic on the back of this garment — back is clean. | black-rose | ghost, on-model |
| no pastel on kids | DO NOT use pastel, washed-out, or soft-tone color treatment — Kids Capsule is luxury, not babyish. | kids-capsule | ghost, on-model |
| no cartoon illustration | DO NOT render in an illustrated, cartoon, animated, or vector style. | all | all |
| no mannequin seams | DO NOT show hanger, mannequin form, or any internal support structure. | all | ghost |
| no stock-photo lighting | DO NOT use ring-flash beauty-dish or flat commercial lighting — use the lighting directive above. | all | on-model |
| no invented corrections | DO NOT invent or hallucinate embroidery, patches, logos, or graphics not present in the spec. | all | all |
| no duplicate garments | DO NOT show more than ONE instance of this garment in the frame. | all | all |
| no cropping | DO NOT crop any part of the garment, sleeve, hem, or graphic out of the frame. | all | all |

---

## Usage Notes

1. For standard pipeline renders, the BASE_PROCEDURE from `prompt.py` covers
   lighting, background, fidelity, and negative guardrails completely. Query
   this taxonomy when building freeform editorial requests or extending a
   base prompt with collection-specific atmosphere.

2. Match `collection_tags` and `mode_tags` before selecting any element. A
   black-rose scene element must not appear in a kids-capsule prompt.

3. Run every element through the canon guard: any element evoking the
   locked-out European-luxury lineage must be rejected, even if it arrives
   via freeform request.

4. Seed elements for machine-queryable storage are in
   `references/skyyrose-seed-elements.json` (element_id format). This
   taxonomy is the human-readable companion reference.
