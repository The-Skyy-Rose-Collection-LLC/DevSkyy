# Domain Pitfalls: AI Ghost Mannequin Pipeline

**Domain:** AI-driven ghost mannequin product photography from techflats, luxury streetwear
**Researched:** 2026-04-22
**Project context:** 30 SKUs, Gemini 2.5 Flash Image primary, FLUX fallback, techflat source, CSV-driven catalog

---

## Critical Pitfalls

Mistakes that cause rerenders, catalog corruption, or wasted paid API spend.

---

### Pitfall 1: Gemini Silent HTTP 200 Failure — No Image Returned

**What goes wrong:** Gemini returns HTTP 200 with a valid JSON envelope but no `inlineData` image part. The pipeline logs "success," writes nothing to disk, and proceeds as if the image was generated. Downstream code finds a missing file, crashes, or worse — marks the CSV row as done with a blank path.

**Why it happens:** Four distinct causes produce this identical surface behavior:
1. `responseModalities` not set to `["IMAGE"]` or `["TEXT", "IMAGE"]` — model defaults to text-only output
2. `NO_IMAGE` finish reason — model accepted the request but produced no usable output (ambiguous prompt, techflat had too little color contrast for the model to infer garment shape)
3. `IMAGE_SAFETY` finish reason — content policy triggered on-output (not on prompt), so `promptFeedback` looks clean but `candidates[].content` is absent
4. Transparent background request — Gemini cannot generate transparent PNG; silent degradation to non-transparent output that breaks downstream alpha assumptions

**Consequences:** Undetected failures mean 0-byte output files or missing keys, the CSV update tool writes an empty path, the review queue shows a thumbnail error that reviewers skip as a "loading glitch," and a broken image gets approved to production.

**Warning signs:**
- Output directory has fewer files than the number of SKUs processed
- Any output file under 10 KB
- `finishReason` field in response is `NO_IMAGE` or `IMAGE_SAFETY` — check explicitly, do not assume absence of error = success

**Prevention:**
- Classify every response before treating it as a success. Check six structural fields: `promptFeedback` existence, `candidates` presence, `candidates[].finishReason`, `candidates[].content` presence, `inlineData` presence, whether only text parts exist.
- Emit distinct error codes: `SILENT_NO_IMAGE`, `SILENT_SAFETY`, `SILENT_NO_CANDIDATES`, `CONFIG_ERROR` — not a generic "failed."
- Abort batch and alert if `SILENT_NO_IMAGE` exceeds 10% of the run — this signals a systemic prompt or configuration problem, not per-SKU variance.
- Never write a CSV path for a SKU unless `os.path.exists(output_path)` AND `os.path.getsize(output_path) > 10_000` (rejects near-empty files from partial writes).
- For transparent backgrounds: generate on pure white (#FFFFFF) then run `rembg` as a post-processing step — do not request alpha channel from Gemini.

**Phase:** Batch script foundation, Phase 1. Cannot be retrofitted after CSV rows are already populated.

**Cost impact if ignored:** Every bad render that passes undetected requires a full re-run of that SKU (≥$0.10/image × samples). With 30 SKUs × multi-sample runs, undetected silents can burn $30–$90 before discovery.

---

### Pitfall 2: Jersey Text and Number Rendering Hallucination

**What goes wrong:** AI generates plausible-looking jersey numbers/lettering that is visually wrong — wrong digit, mirrored character, merged glyphs, or stylistically correct but semantically garbage (e.g., "88" renders as "83", "BLACK IS BEAUTIFUL" drifts mid-word). The garment passes visual review because the reviewer is checking shape and background, not character-by-character accuracy.

**Why it happens:** Image generation models treat text as a high-frequency texture pattern, not a character sequence. Jersey numbers are particularly vulnerable because:
- Multi-digit numbers on dark fabric have low surrounding contrast for the model to anchor on
- The alternating rose-fill pattern (left number rose fill, right plain; reversed on back) is a non-standard layout with no training data precedent
- Sleeve patches are tiny and low-resolution in the techflat source — the model guesses at detail it cannot resolve
- Gemini 2.5 Flash (not Pro) has weaker text fidelity than Gemini Pro Image; this pipeline's primary model is the weaker text renderer

**Consequences:** A jersey with a wrong number or corrupted text ships to the product page. Customers notice. Brand trust for a luxury label is disproportionately damaged by this class of error. Correction requires a full re-render.

**Warning signs:**
- OCR confidence on number region below 0.85
- OCR return does not exactly match the catalog SKU's expected number
- Reviewer approves without checking the number — most likely to happen under time pressure

**Prevention:**
- Build a mandatory post-generation text verification step: use Gemini Vision (or Tesseract for digits) to OCR the number region of every jersey render and compare against the expected number from the catalog CSV.
- Use quotation marks around the literal string in prompts: `jersey number "23" in bold block font` — models treat quoted strings as literals more reliably than unquoted ones.
- Keep text segments short in a single prompt: numbers 0–99 succeed far more reliably than multi-word strings. For "BLACK IS BEAUTIFUL" back text, use a two-pass approach: generate garment without back text first, then inpaint text in a second call.
- Flag any jersey SKU in the review queue with the expected number shown alongside the render as an annotation. Reviewers must check the number explicitly, not just approve on aesthetics.
- Never auto-approve jersey renders — require explicit sign-off separate from the general review gate.

**Phase:** OCR verification must be built before the first jersey render runs. Do not run jersey SKUs until the check is implemented.

**Cost impact if ignored:** Wrong number discovered after CSV update → re-render (one API call per sample) + re-review time + risk of production deployment. Estimated: $0.30–$1.50 per jersey SKU requiring correction × up to 20 jersey SKUs in catalog.

---

### Pitfall 3: Techflat-to-Ghost-Mannequin Shape Collapse

**What goes wrong:** Techflats are 2D top-view flat illustrations — no depth cues, no shading, no perspective. The AI generates a "3D ghost mannequin" that looks like a flat cardboard cutout with added shadow, not a volumetrically inflated garment. Hoodies lose their hood volume. Bomber jackets appear paper-thin at the shoulders. Joggers render as flat rectangles. The image is technically "generated" but commercially unusable.

**Why it happens:** Generative image models infer 3D structure from lighting cues, fabric folds, and perspective in source imagery. Techflats deliberately omit all of these — they are technical documents, not reference photos. Garment categories with complex 3D structure (hoodies, bombers, sherpa jackets) fail worse than flat-cut garments (tees, shorts). This is the fundamental mismatch of the techflat-to-ghost-mannequin workflow.

**Consequences:** Flat-looking ghost mannequin images convey no fit information to the buyer, which is the entire point of ghost mannequin photography. Images require manual retouching or full re-render with revised strategy.

**Warning signs:**
- Rendered garment shoulder width is less than 80% of the source techflat shoulder span — the model collapsed proportions
- Hood area is flat or absent on hoodie renders
- Collar opening shows no depth (no visible interior)

**Prevention:**
- Classify SKUs by 3D complexity before batch run:
  - Group A: tees, shorts, joggers — moderate risk, run first to validate pipeline
  - Group B: hoodies, crewnecks, jackets — high shape collapse risk
  - Group C: jerseys — medium shape risk, text risk dominates
- For Group B garments: include explicit 3D volume instruction: `garment with natural fabric drape and volume, collar opening shows depth, sleeves have dimension and subtle fold shadows`.
- Provide a style reference image in the API call (Gemini supports multimodal image+text input): use a royalty-free ghost mannequin photo of a similar garment category to anchor the 3D expectation.
- Budget 2–3 generation samples per Group B SKU versus 1–2 for Group A. First sample is exploratory; second/third converge.

**Phase:** SKU complexity classification in Phase 1. Group-specific prompt templates in Phase 2 before Group B runs.

**Cost impact if ignored:** Group B SKUs failing at first attempt → 2× API spend on that subset. For 10 complex SKUs × 3 samples × $0.10 = $3 expected vs $6+ actual.

---

### Pitfall 4: Cost Runaway via Unbounded Retry Logic

**What goes wrong:** A batch script retries failed SKUs automatically without a hard cap. Gemini 429 rate limit errors (which are transient) trigger the same retry path as generation failures (which are permanent). The script retries 30 SKUs × 5 times each = 150 API calls for 0 completed renders while the operator is asleep.

**Why it happens:** Gemini 2.5 Flash Image has undocumented but empirically observed rate limits: effective throughput drops below 2 requests per minute before 429 throttling begins; failures start on the 3rd–4th sequential request; exponential backoff does not reliably recover because Gemini does not return `Retry-After` headers. Scripts that implement `retries=5` without distinguishing 429 (transient, wait longer) from generation failure (permanent, move on) spiral into unbounded spend.

**Consequences:** Unexpected API bill. A 150-call spiral on a 30-SKU batch can cost 5× the estimated budget. The STOP AND SHOW cost manifest is violated because the manifest covered the estimated run, not the actual spiral.

**Warning signs:**
- Run log shows the same SKU appearing more than 2 times
- Script has been running for >2× the estimated runtime
- Total calls counter exceeds 1.5× the planned call count

**Prevention:**
- Separate retry classes explicitly in code:
  - `429 RESOURCE_EXHAUSTED`: exponential backoff + jitter (start 15s, cap at 120s), max 3 retries
  - `NO_IMAGE` / `SILENT_FAILURE`: do NOT retry automatically — flag for human review, continue to next SKU
  - `IMAGE_SAFETY`: do NOT retry — log the SKU and prompt, continue
  - Network timeout: retry once with 10s delay, then fail permanently
- Hard spend cap: track spend as `calls × price_per_call` in a local counter. Halt the batch and write a report if the cap exceeds 1.5× the cost manifest estimate.
- Hard per-SKU cap: `MAX_RETRIES_TOTAL_PER_SKU = 2` regardless of failure class.
- CLI confirmation gate: require `--confirm` flag when batch size exceeds 10 SKUs. Print cost manifest and wait for stdin `y` before any API call is made.
- Log every API call (SKU, attempt number, response class, cost) to `renders/ghost-mannequin/run-log.jsonl` so post-run audit is always possible.

**Phase:** Must be in the batch script foundation before the first real run.

**Cost impact if ignored:** Worst case: 30 SKUs × 5 retries × 3 samples = 450 calls at $0.10–$0.15/call = $45–$67 on a run that should have cost $9–$13.

---

### Pitfall 5: Human Review Gate Bypass

**What goes wrong:** The review gate exists: outputs go to `renders/ghost-mannequin/` for human review before CSV update. But the CSV update tool is callable directly. An operator (or autonomous agent) runs the update tool immediately after the batch script completes, skipping review. Wrong images — wrong colors, collapsed shapes, wrong jersey numbers, white bleed on dark garments — are written into the CSV as canonical product images and eventually appear on skyyrose.co.

**Why it happens:** Review gates only work if they are structurally enforced, not by convention. If the update tool accepts `--sku` and `--path` with no precondition check, it is trivially bypassed. Autonomous agents (Ralph loop) are especially likely to skip gates because they optimize for task completion.

**Consequences:** Wrong image in CSV → wrong image on WooCommerce product page → customer-visible defect on a luxury brand site. Correction requires: identify wrong image, re-render, re-review, re-update CSV, potentially cache-bust WooCommerce product images.

**Warning signs:**
- CSV `front_model_image` column is updated on the same calendar day the batch script ran (same-day update is a flag — check that an `approved/` file exists)
- No `approved/` directory entry exists for a SKU that has a CSV path populated

**Prevention:**
- The CSV update tool must require a review approval record. Implement a `renders/ghost-mannequin/approved/` directory. Only files moved there by a human action are eligible for CSV update.
- The CSV update script checks: if `renders/ghost-mannequin/approved/{sku}-ghost-front.webp` does not exist, exit with an error — do not update the CSV.
- The batch script must never move files to `approved/` automatically. Only a human action (or an explicit approval command with a confirmation prompt) moves files there.
- Add a precondition in the update script: verify the approved file's mtime is after the render's mtime (prevents re-approving a stale render while a fresh bad one sits in the staging output directory).

**Phase:** Approval gate must be built into the CSV update tool in Phase 1. No review-less path should exist in the codebase.

**Cost impact if ignored:** Wrong image in production → brand damage (unquantifiable for luxury). Operational: re-render + re-review + redeploy + WooCommerce cache bust = $5–$20 direct cost plus significant time.

---

## Moderate Pitfalls

---

### Pitfall 6: Background Contamination — Not Pure White

**What goes wrong:** The generated ghost mannequin has a background that is off-white (#F5F5F5, #E8E8E8) rather than pure white (#FFFFFF), or has a subtle gradient, or has soft color bleeding from the garment at the edges. On the WooCommerce product page against a white page background, the image shows a visible bounding box around the garment.

**Why it happens:**
- FLUX has a documented training-data issue producing blurry/soft output on pure white backgrounds — the model was trained on photography, not studio white setups
- Gemini generates photographic white (not #FFFFFF) when prompted with "white studio background"
- Dark garments (Black Rose collection: black, silver) cause color bleed at garment edges during AI compositing — anti-aliasing blends black fabric pixels with white background into a visible grey fringe

**Warning signs:**
- Mean RGB value of corner pixels is below (250, 250, 250)
- Dark garment renders show a grey halo at the garment edge

**Prevention:**
- After generation, sample 10 corner pixels and compute distance from #FFFFFF. If mean distance > 15 RGB units, flag for review.
- Post-processing step: threshold-clip the background. Any pixel brighter than (245, 245, 245) in the "background zone" (edge 5% of image, non-garment mask) gets remapped to #FFFFFF.
- For dark garments specifically: use rembg to remove background after generation, then composite programmatically onto a pure #FFFFFF canvas. This eliminates the fringing problem entirely.

**Phase:** Post-processing pipeline, Phase 2.

**Cost impact if ignored:** Visible image box on product pages requires re-render or manual Photoshop. Affects multiple Black Rose SKUs simultaneously.

---

### Pitfall 7: CSV Path Drift — Filename Convention Mismatch

**What goes wrong:** Phase 1 batch script writes `renders/ghost-mannequin/{sku}-ghost-front.webp`. A Phase 2 retry or versioned re-run introduces `renders/ghost-mannequin/{sku}/{sku}-ghost-front-v2.webp`. Now the CSV `front_model_image` column has mixed path formats. The catalog loader (`skyyrose_get_product()` in PHP, `read_catalog_rows()` in Python) treats these paths as relative — the mismatch silently produces 404s on product pages.

**Warning signs:**
- CSV has rows with flat paths and rows with subdirectory paths
- Product images 404 on the live site for specific SKUs after a re-run

**Prevention:**
- Lock the path convention in a single constant imported by both the batch script and the update tool: `GHOST_MANNEQUIN_PATH_TEMPLATE = "renders/ghost-mannequin/{sku}-ghost-front.webp"`. Neither tool hardcodes a path.
- Add a CSV schema validator that runs before any CSV write: every `front_model_image` value must either be empty or match `^renders/ghost-mannequin/[a-z0-9-]+-ghost-front\.webp$`. Reject the write if it does not match.
- For versioning/retries: use a separate staging directory, move to the canonical path on approval. Canonical paths never carry version suffixes.

**Phase:** Constant definition and regex validator in Phase 1.

**Cost impact if ignored:** Silent 404s on product images discovered on customer-facing product page review, not in development. Full CSV audit and possible re-upload required.

---

### Pitfall 8: Overwriting a Good Image with a Bad Re-render

**What goes wrong:** SKU `br-003` passed review and was approved. The batch script runs again (different SKU set, or retry run) and accidentally includes `br-003`, or has no skip-if-exists logic. The new render is worse. The approved file in `approved/` is overwritten. The CSV update runs. The bad image replaces the good one.

**Warning signs:**
- Batch log shows a SKU being generated that already has an `approved/` entry
- `approved/` directory mtime on a file is newer than the original approval action timestamp

**Prevention:**
- Batch script checks for existing output: if `renders/ghost-mannequin/approved/{sku}-ghost-front.webp` exists, skip that SKU and log "SKIPPED — already approved." Override only with explicit `--force-rerender {sku}` flag.
- CSV update tool: if `front_model_image` is already populated for a SKU, require `--overwrite` flag. Do not silently overwrite.

**Phase:** Skip-if-exists logic in Phase 1 batch script.

**Cost impact if ignored:** One paid re-render that produces a worse image, plus review time, plus regression risk.

---

## Minor Pitfalls

---

### Pitfall 9: Garment Category Prompt Bleed

**What goes wrong:** A single generic "jersey" prompt template is used across all jersey types. Baseball jerseys get football collar structures. Hockey jerseys lose their distinctive hem cut. Basketball jerseys get button plackets.

**Prevention:** Build a prompt template per garment category (7 types across the catalog). Each template specifies the distinguishing structural features of that garment type. No single template covers more than one garment category.

**Phase:** Prompt template library, Phase 1.

---

### Pitfall 10: Dark Garment Lighting Collapse

**What goes wrong:** Black Rose collection garments (black-dominant colorway, silver accents) generate flat, detail-less results because the AI applies low-key dramatic lighting rather than the even product studio lighting required for e-commerce.

**Prevention:** Explicitly specify high-key, even product studio lighting: `even studio lighting from three-point setup, no dramatic shadows, fabric texture clearly visible across the entire garment`. Test one black garment SKU first in the pilot run before processing all Black Rose SKUs.

**Phase:** Prompt testing, Phase 1 pilot.

---

### Pitfall 11: Kids Set Garment Decomposition

**What goes wrong:** Kids set SKUs (kids-001, kids-002) are two-piece sets. The AI generates them as a single merged garment, generates only one piece, or produces a physically impossible merged top-and-bottom.

**Prevention:** Generate top and bottom separately, then composite. Do not attempt a two-piece ghost mannequin in a single generation call.

**Phase:** Kids SKU handling, Phase 2.

---

### Pitfall 12: Accessories Cannot Ghost Mannequin

**What goes wrong:** The beanie and fanny pack SKUs have no torso or shoulder to anchor the ghost mannequin framing. The model either invents a body to hang them on (defeating ghost mannequin), generates a floating accessory with incorrect scale, or produces an unusable result.

**Prevention:** Accessories require a different photography treatment — flat lay on white surface or 3/4 angle product shot, not ghost mannequin. Exclude these SKUs from the ghost mannequin batch entirely and handle them in a separate styled flat lay generation pass.

**Phase:** SKU classification in Phase 1 — 2 SKUs are explicitly out of scope for the ghost mannequin pipeline.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Batch script foundation | Silent HTTP 200 failure (Pitfall 1) | Six-field response classifier before any write |
| Batch script foundation | Unbounded retry / cost runaway (Pitfall 4) | Hard spend cap + retry class separation |
| CSV update tool | Review gate bypass (Pitfall 5) | `approved/` directory precondition enforced structurally |
| CSV update tool | Overwrite good with bad re-render (Pitfall 8) | Skip-if-approved + `--overwrite` flag required |
| Jersey SKUs | Text and number hallucination (Pitfall 2) | OCR verification gate before review queue entry |
| Hoodie/jacket SKUs | 3D shape collapse (Pitfall 3) | Complexity classification + 3D volume prompts + reference image |
| Black Rose SKUs | Dark garment lighting collapse (Pitfall 10) | High-key studio lighting in prompt; pilot one SKU first |
| Kids set SKUs | Garment decomposition (Pitfall 11) | Separate generation per piece |
| Beanie / fanny pack | Accessories fail ghost mannequin (Pitfall 12) | Exclude from batch; use flat lay pipeline |
| Post-processing | Background not pure white (Pitfall 6) | Corner-pixel check + programmatic white fill via rembg |
| Path management | CSV path drift (Pitfall 7) | Single path constant + regex validator on every CSV write |
| Pilot run | Unknown failure mode discovery | Run 3–5 Group A tee SKUs before full 30-SKU batch |

---

## Sources

- [Gemini 2.5 Flash Image 429 rate limit — developer forum](https://discuss.ai.google.dev/t/gemini-2-5-flash-image-frequent-429-resource-exhausted-during-sequential-image-generation-seeking-clarity-on-rate-limits/118691) — empirical: ~2 RPM effective throughput, 35% failure rate under backoff, no Retry-After header (MEDIUM confidence, developer-reported)
- [Gemini silent failure / IMAGE_SAFETY classification guide](https://www.aifreeapi.com/en/posts/gemini-image-silent-failure-image-safety-fix) — six-field response classifier pattern (MEDIUM confidence)
- [Gemini image generation official docs](https://ai.google.dev/gemini-api/docs/image-generation) — responseModalities requirement, transparent background limitation confirmed (HIGH confidence)
- [Ghost mannequin fabric texture mismatch](https://imageworkindia.com/fix-ai-ghost-mannequin-fabric-texture-mismatch/) — AI prioritizes structure over high-frequency textile detail (MEDIUM confidence)
- [Ghost mannequin neck joint hallucinations](https://imageworkindia.com/generative-fill-prompt-ghost-mannequin-neck-joint/) — random brand tags, anatomical anomalies, pixel context requirements (MEDIUM confidence)
- [FLUX white background blur issue](https://github.com/black-forest-labs/flux/issues/107) — documented community issue: white and yellow backgrounds produce blurry output (MEDIUM confidence)
- [Gemini transparent background limitation](https://news.ycombinator.com/item?id=46343260) — confirmed: no alpha channel output, rembg workaround documented (HIGH confidence, multiple corroborating sources)
- [Garment3DGen — watertight geometry and interior holes problem](https://arxiv.org/html/2403.18816v1) — generated garments require post-processing to add arm/neck/waist holes (HIGH confidence, academic)
- [AI product image batch — skipping review consequences](https://nextbuild.co/blog/ai-product-photos-inconsistent-ecommerce) — floating shadows, melted textures, color mismatch from unchecked auto-edits (MEDIUM confidence)
- [Gemini 429 rate limit resolution guide](https://blog.laozhang.ai/en/posts/gemini-image-429-rate-limit) — four rate limit dimensions, exponential backoff recommendations, Batch API alternative (MEDIUM confidence)
- Project memory: Gemini text weakness on jersey backs documented in MEMORY.md (`docs/NANO_BANANA.md` reference, skyyroseco@gmail.com project)
