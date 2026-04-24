# Domain Pitfalls: Ghost Mannequin AI Imagery Pipeline

**Domain:** CSV-driven AI product photography pipeline for luxury streetwear ecommerce
**Researched:** 2026-04-22
**Milestone:** v1.2 — CSV-Driven Ghost Mannequin Generation
**Confidence:** HIGH (project-specific codebase analysis), MEDIUM (general AI generation pitfalls)

---

## Critical Pitfalls

Mistakes that caused complete teardowns, wasted API spend, or will corrupt canonical data.

---

### Pitfall 1: The Scorched-Earth Precedent — Wrong Source Data Drives Everything Downstream

**What goes wrong:** The previous imagery pipeline (deleted April 2026, commit f25fd25d3) generated correct-looking images of the WRONG products. SKU `br-011` (The Rose — Hockey jersey) rendered as a baseball jersey because prompts read branding from `data/product-specs.json` instead of the CSV's `branding_spec` column. The QA system scored the image 100 because it measured text clarity and color quality, not product identity.

**Root causes documented in the post-mortem:**
1. Prompts read branding from `data/product-specs.json` instead of the CSV's `branding_spec` column — every CSV edit was invisible to the pipeline.
2. Reference images cross-contaminated — the same jersey techflat served 5 SKUs regardless of sport type.
3. Prompt said "copy reference exactly" — gave the reference image primacy over the REQUIRED BRANDING text block whenever they disagreed.

**Consequences:** 16,950 lines of pipeline code deleted, all generated images discarded, full rebuild required.

**Prevention:**
- `skyyrose.core.catalog_loader` is the single import point for product data. No new config file, JSON spec, or prompt registry. The `branding_spec` column in the CSV is the source of branding instructions for every generation call.
- QA scoring must include a product-identity check: the generated image must match the expected garment type, not just score well on generic image quality metrics.
- Before any batch run, print a manifest showing `sku → source file → branding_spec` for every product. Any discrepancy between what the prompt will say and what the CSV says is a hard block.

**Detection:** Run the preflight manifest and read every `branding_spec` value aloud against the product name before confirming. If a hockey jersey SKU's branding_spec describes baseball — something is wrong in the CSV.

**Phase assignment:** Phase 1 (SKU→bundle resolver + CSV adapter). Must be confirmed before any generation call is made.

---

### Pitfall 2: Bundle Directory Names Do Not Match CSV Product Names — 17 of 30 Products Mismatch

**What goes wrong:** `data/product-bundles/` has 32 directories named by product title. The canonical CSV has 30 SKUs. String comparison between CSV product names and bundle directory names fails for 17 of 30 products.

**Confirmed mismatches (from live codebase analysis, 2026-04-22):**
- `br-005`: CSV `BLACK Rose Hoodie — Signature Edition` (em dash `—`) vs bundle `BLACK Rose Hoodie - Signature Edition` (hyphen `-`)
- `br-008`: CSV `BLACK is Beautiful Jersey Series: 1. SF Inspired (Football)` vs bundle `BLACK is Beautiful Jersey Series: 1. SF inspired` (case mismatch, no sport suffix)
- `br-009`: CSV `BLACK is Beautiful Jersey Series: 2. Last Oakland (Football)` vs bundle `BLACK is Beautiful Jersey Series: 2. LAST OAKLAND` (ALL CAPS, different format)
- `br-010`: CSV `BLACK is Beautiful Jersey Series: 3. The Bay (Basketball)` vs bundle `BLACK is Beautiful Jersey Series: 3. THE BAY` (ALL CAPS)
- `br-011`: CSV `BLACK is Beautiful Jersey Series: 4. The Rose (Hockey)` vs bundle `BLACK is Beautiful Jersey Series: 4. THE ROSE (SHARKS EDITION)` (different subtitle)
- `br-003`: CSV `BLACK is Beautiful Jersey Series: 0. Baseball Classic` — no matching bundle directory at all
- `sg-001`: CSV `The Bridge Series 'The Bay Bridge' Shorts` (curly quotes) vs bundle `The Bridge Series The Bay Bridge Shorts` (no quotes)
- `sg-002`: CSV `The Bridge Series 'Stay Golden' Shirt` vs bundle `The Bridge Series Stay Golden Shirt` (no quotes)
- `sg-003`/`sg-005`: Similar curly-quote vs no-quote mismatch
- `sg-015`: CSV `The Windbreaker Set` — no bundle directory exists
- `lh-004`: CSV `Love Hurts Bomber Jacket` vs bundle `Love Hurts Varsity Jacket` — different garment type name
- `kids-001`: CSV `Kids Colorblock Hoodie Set — Red/Black` vs bundle `Kids Red Set`
- `kids-002`: CSV `Kids Colorblock Hoodie Set — Purple/Black` vs bundle `Kids Purple Set`

**Additional issue — missing `techflat-front.jpeg` in 12 bundle directories:** Even when the bundle directory resolves, 12 of 32 dirs have no `techflat-front.jpeg`: `BLACK Rose Hoodie`, `BLACK Rose Hoodie - Signature Edition`, `BLACK Rose Sherpa Jacket`, `BLACK Rose x Love Hurts Basketball Shorts`, `Original Label Tee (Orchid)`, `Original Label Tee (White)`, `The Bridge Series The Bay Bridge Shirt`, `The Fannie`, `The Sherpa Jacket`, and 3 others.

**Consequences:** A string-comparison resolver silently picks the wrong bundle directory. A missing-file error crashes the batch mid-run, leaving partial output with no record of which SKUs completed. The `lh-004` bundle-name mismatch (Bomber → Varsity) means the bundle content may not correspond to the product at all.

**Prevention:**
- Do not use name-based or fuzzy bundle directory lookup at runtime. Add a `bundle_dir` column to the canonical CSV mapping each SKU to its exact directory name. This resolves the mismatch at authoring time.
- Preflight gate must verify: (a) `bundle_dir` column is populated for every SKU in the run, (b) the directory exists on disk, (c) `techflat-front.jpeg` exists inside it. Missing items are a hard block.
- SKUs with no techflat-front.jpeg write to `renders/ghost-mannequin/SKIPPED.json` and are skipped gracefully — the batch continues.
- For `lh-004` specifically: manually verify that the `Love Hurts Varsity Jacket` directory contains assets that correspond to the Bomber Jacket SKU before wiring that SKU.

**Phase assignment:** Phase 1 (canonical mapping). The `bundle_dir` column must be added to the CSV and manually populated before any generation work begins.

---

### Pitfall 3: Jersey Text and Number Rendering Hallucination

**What goes wrong:** AI generates jersey images with plausible-looking numbers or lettering that is visually wrong — wrong digit, mirrored character, merged glyphs, or the alternating rose-fill pattern (front: left=rose, right=plain; back: reversed) is simplified or inverted. The image passes automated QC (white background, edge variance, collar depth) but has wrong number fills.

**Why it happens:** Generation models treat jersey text as a high-frequency texture pattern, not a character sequence. The alternating rose-fill pattern is non-standard with minimal training data precedent. Sleeve patches are tiny and low-resolution in the techflat source — the model guesses at details it cannot resolve. Gemini 2.5 Flash (not Pro) has weaker text fidelity. This is documented in the project (MEMORY.md: "Gemini text weakness: Struggles with text rendering on jersey backs").

**Consequences:** A jersey with the wrong number fill ships to the product page. For the "Black Is Beautiful" series (br-008 through br-012), the alternating number fill is a brand identifier — hallucination here is a brand-critical failure.

**Warning signs:** OCR on the number region returns a different digit from what the catalog specifies. Reviewer approves without checking the number because they focused on background and shape.

**Prevention:**
- The jersey-specific prompt additions in STACK.md (`CRITICAL: Preserve all jersey text, numbers, team patches, and embroidery exactly. Do not hallucinate or alter any text.`) are required, not optional.
- Post-generation: run Gemini Vision or Tesseract OCR on the cropped number region of every jersey render and compare against the catalog-expected number. Flag below 0.85 similarity for mandatory manual review — do not let it proceed to the approval queue automatically.
- Never auto-approve jersey renders. Jersey SKUs require a separate explicit sign-off in the review step.
- The review approval tool must display the source techflat alongside the generated output in side-by-side comparison. Reviewers cannot catch hallucinations without the reference visible.
- Front shots are significantly more reliable than back shots for text (documented in project memory). Keep v1.2 to front-only — do not attempt back jerseys.

**Phase assignment:** Phase 3 (prompt engineering + generation) and Phase 4 (post-generation QC). The OCR verification gate must be built before the first jersey SKU is run.

---

### Pitfall 4: Gemini Silent HTTP 200 Failure — No Image Returned

**What goes wrong:** Gemini returns HTTP 200 with a valid JSON envelope but no `inlineData` image part. The pipeline logs "success," writes nothing to disk, and proceeds. Downstream code finds a missing file, crashes, or marks the CSV row as done with a blank path.

**Why it happens:** Four distinct causes produce identical surface behavior:
1. `responseModalities` not set to `["IMAGE"]` or `["TEXT", "IMAGE"]` — model defaults to text-only output
2. `NO_IMAGE` finish reason — model accepted the request but produced no usable output (ambiguous prompt, techflat had too little color contrast)
3. `IMAGE_SAFETY` finish reason — content policy triggered on output; `promptFeedback` looks clean but `candidates[].content` is absent
4. Transparent background request — Gemini cannot generate transparent PNG; silent degradation occurs

**Consequences:** Undetected failures mean the CSV update tool writes an empty path, the review queue shows a thumbnail error that reviewers skip as a loading glitch, and a broken image gets approved to production.

**Prevention:**
- Classify every response before treating it as a success. Check six structural fields: `promptFeedback` existence, `candidates` presence, `candidates[].finishReason`, `candidates[].content` presence, `inlineData` presence, whether only text parts exist.
- Emit distinct error codes: `SILENT_NO_IMAGE`, `SILENT_SAFETY`, `SILENT_NO_CANDIDATES`, `CONFIG_ERROR` — not a generic "failed."
- Never write a CSV path for a SKU unless `os.path.exists(output_path)` AND `os.path.getsize(output_path) > 10_000`.
- Abort batch and alert if `SILENT_NO_IMAGE` exceeds 10% of the run — signals a systemic prompt or configuration problem.

**Phase assignment:** Phase 3 (batch script foundation). Cannot be retrofitted after CSV rows are populated.

---

### Pitfall 5: `render_source_override` Column Is the Wrong Source for Ghost Mannequin Input

**What goes wrong:** The `render_source_override` column in the CSV contains filenames like `br-008-sf-inspired.jpg` that resolve to `wordpress-theme/skyyrose-flagship/assets/images/products/br-008-sf-inspired.jpg`. These are the deployed product images for the live site. Using them as ghost mannequin input generates ghosted versions of the existing product photos (which may already show a model or on-location styling), not of the techflats.

**Why it happens:** The `render_source_override` column was designed for the FASHN virtual try-on pipeline, which uses existing product photos as garment references. Ghost mannequin requires the `techflat-front.jpeg` from the bundle directory — a completely different source file.

**Consequences:** Ghost mannequin generation runs on wrong inputs. Outputs look like a ghosted existing product photo, not a clean studio techflat on white. All 30 outputs are wrong.

**Prevention:**
- The ghost mannequin script must never use `render_source_override` as its source. It uses the `bundle_dir` column (to be added in Phase 1) to resolve `data/product-bundles/{bundle_dir}/techflat-front.jpeg`.
- Document this column separation explicitly in `catalog_loader.py` docstring: "`render_source_override` is for try-on/FASHN pipelines. Ghost mannequin uses `bundle_dir` → techflat-front.jpeg exclusively."

**Phase assignment:** Phase 1 (canonical mapping design) and Phase 2 (input resolution logic). This distinction must be documented before the first line of the batch script is written.

---

### Pitfall 6: CSV Write Corruption During `front_model_image` Update

**What goes wrong:** The CSV update tool reads all rows, modifies `front_model_image` for an approved SKU, and rewrites the file. If the process is interrupted mid-write (crash, KeyboardInterrupt, disk full), the CSV is left empty or partially written. The CSV is the canonical source of truth for the WordPress theme (PHP), Python pipelines, and all three imagery pipelines simultaneously — corruption takes everything down at once.

**Why it happens:** Python's `csv.writer` opens in `'w'` mode, which truncates the file immediately before writing begins. Any failure during the write leaves an empty or truncated file. `os.rename()` is only atomic within the same filesystem — if `/tmp` is on a different mount, the temp-file-then-rename pattern is not actually atomic.

**Consequences:** WordPress theme stops loading products. All three AI pipelines error on startup. If no recent git commit exists, the loss is permanent.

**Prevention:**
- Write pattern: write to a temp file in the SAME directory as the CSV (same filesystem), then `os.replace()`. Never open the canonical CSV in `'w'` mode directly.
- Before any write, assert the new row count matches the original row count. Row count mismatch aborts before the rename.
- After any write, read the file back and verify the targeted SKU's `front_model_image` field reflects the new value.
- The CSV is tracked in git. The approval tool prints the git diff it is about to cause and requires 'y' confirmation — same STOP AND SHOW pattern as the FASHN pipeline.
- Keep a timestamped backup alongside the CSV before any write: `skyyrose-catalog.csv.bak-{timestamp}`.

**Phase assignment:** Phase 5 (CSV update tool). Atomic write is required in the initial implementation, not a later hardening pass.

---

### Pitfall 7: Cost Runaway via Unbounded Retry Logic

**What goes wrong:** A batch script retries failed SKUs automatically without a hard cap. Gemini 429 rate limit errors (transient, need longer wait) trigger the same retry path as generation failures (permanent, move on). The script retries 30 SKUs × 5 times = 150 calls for 0 completed renders while the operator is not watching.

**Why it happens:** Gemini 2.5 Flash Image has effective throughput limits below 2 requests per minute before 429 throttling begins. It does not return `Retry-After` headers. Scripts that implement `retries=5` without distinguishing 429 from generation failure spiral into unbounded spend. The STOP AND SHOW cost manifest covered the planned run, not a 5× spiral.

**Consequences:** Unexpected API bill. A 150-call spiral on a 30-SKU batch costs 5× the estimated budget (~$7–$9 planned → ~$35–$45 actual).

**Prevention:**
- Separate retry classes in code:
  - `429 RESOURCE_EXHAUSTED`: exponential backoff + jitter (start 15s, cap at 120s), max 3 retries
  - `NO_IMAGE` / silent failure: do NOT retry automatically — flag for human review, continue to next SKU
  - `IMAGE_SAFETY`: do NOT retry — log SKU and prompt hash, continue
  - Network timeout: retry once after 10s delay, then fail permanently
- Hard spend cap: track spend as `calls × price_per_call` locally. Halt batch and write a report if cap exceeds 1.5× the cost manifest estimate.
- Hard per-SKU cap: `MAX_RETRIES_TOTAL_PER_SKU = 2` regardless of failure class.
- Log every API call (SKU, attempt number, response class, cost) to `renders/ghost-mannequin/run-log.jsonl`.

**Phase assignment:** Must be in the batch script before the first real run.

---

## Moderate Pitfalls

---

### Pitfall 8: BRIA RMBG Returns Transparent PNG — Not White Background — Gemini Gets Wrong Input

**What goes wrong:** BRIA RMBG 2.0 returns an image with alpha channel (transparent background). If the pipeline uses this output directly as the Gemini generation input, Gemini receives a checkerboard transparency artifact and the generation output inherits an unpredictable background color.

**Why it happens:** Removing the background is the whole point of BRIA RMBG — transparent output is correct. But the pipeline requires a separate explicit "composite onto white" step before Stage 2 (Gemini input) AND another composite after Stage 4 (final output). These are not the same operation and both are required.

**Prevention:**
- Stage 1 output → composite onto `#FFFFFF` → this is the Gemini input. Do not pass alpha-channel images to Gemini.
- Stage 4 post-generation → composite generated output onto `#FFFFFF` again (Gemini may produce near-white, not pure white background).
- Assert that the Stage 2 input image has no alpha channel before calling the API. Alpha present = code path error.

**Phase assignment:** Phase 3 (pipeline stage wiring).

---

### Pitfall 9: Background Is Not Pure White (#FFFFFF)

**What goes wrong:** The generated ghost mannequin has a background that is off-white (#F5F5F5, #E8E8E8) or has subtle color bleeding from garment edges. On the WooCommerce product page against a white page background, the image shows a visible bounding box around the garment — immediate "cheap brand" signal.

**Why it happens:** Gemini generates photographic white (not #FFFFFF) when prompted with "white studio background." Dark garments (Black Rose collection: black, silver) cause color bleed at garment edges — anti-aliasing blends black fabric pixels with white background into a visible grey fringe.

**Prevention:**
- After generation, sample 10 corner pixels and compute RGB distance from #FFFFFF. If mean distance > 15, flag for review.
- Post-processing: re-apply the Stage 1 BRIA alpha matte to the Stage 2 Gemini output and composite programmatically onto a guaranteed `#FFFFFF` PIL canvas. This eliminates background drift entirely (already documented as a known trick in STACK.md).
- Verify output with: assert that all sampled corner pixels are ≥ RGB(250, 250, 250).

**Phase assignment:** Phase 3 (post-processing stage).

---

### Pitfall 10: Shared CSV Adapter Import Breaks for `scripts/nano_banana/` Callers

**What goes wrong:** `skyyrose.core.catalog_loader` works when called from `skyyrose/elite_studio/catalog.py` with the project root on `sys.path`. The nano-banana package lives at `scripts/nano_banana/` — a different root. Scripts in `scripts/` that do `from skyyrose.core.catalog_loader import ...` fail with `ModuleNotFoundError: No module named 'skyyrose'` unless the project root is explicitly on `sys.path`.

**Why it happens:** The `nano_banana` package uses `scripts/` as its root. The `skyyrose/` package uses the project root. These are not the same `sys.path` entry. This is confirmed by the current state of the codebase: nano_banana's source files were deleted in the scorched-earth rebuild, and its `__init__.py` does not exist, meaning any new scripts/ caller must set up sys.path correctly from scratch.

**Prevention:**
- The ghost mannequin batch script entry point sets `sys.path` explicitly: `sys.path.insert(0, str(Path(__file__).resolve().parents[N]))` where N is the correct level to the project root. Comment explains why.
- Better: `make install` installs the `skyyrose` package in editable mode. All scripts assume this has run. Add a startup check: `python -c "from skyyrose.core.catalog_loader import read_catalog_rows; assert len(read_catalog_rows()) >= 30"` in preflight.

**Phase assignment:** Phase 2 (CSV adapter wiring).

---

### Pitfall 11: Cost Gate Bypassed by `--skip-preflight` in Agent Context

**What goes wrong:** The existing `renders/preflight.py` has a `--skip-preflight` flag. If the ghost mannequin batch script inherits this pattern and an autonomous agent (Ralph, Claude Code) passes `--skip-preflight` to unblock itself during testing, paid API calls happen without user confirmation.

**Why it happens:** Autonomous agents optimize for task completion and add convenience flags to unblock themselves. The flag exists for a legitimate reason (CI environments without stdin) but gets used in interactive contexts.

**Prevention:**
- Any invocation of `--skip-preflight` (or equivalent) writes an audit log entry to `renders/ghost-mannequin/run-log.json` recording: timestamp, SKU list, API used, estimated cost, and that confirmation was bypassed.
- In TTY context (`sys.stdin.isatty()` returns True), `--skip-preflight` prints a visible warning rather than silently skipping: `WARNING: Confirmation bypassed — X API calls (~$Y.ZZ) will proceed immediately.`
- The STOP AND SHOW protocol in CLAUDE.md is non-negotiable. Any code path that reaches a fal.ai or Gemini generation call without printing the manifest and receiving 'y' is a protocol violation.

**Phase assignment:** Phase 2 (batch script architecture).

---

### Pitfall 12: Human Review Gate Bypass — CSV Updated Before Review

**What goes wrong:** The review gate is by convention, not enforced structurally. The CSV update tool is callable directly after a batch run. An autonomous agent runs it immediately after the batch script completes. Wrong images — collapsed shapes, wrong jersey numbers, grey backgrounds — are written into the CSV and eventually appear on skyyrose.co.

**Prevention:**
- The CSV update tool requires a review approval record. `renders/ghost-mannequin/approved/` directory holds only human-approved files. The CSV update script checks: if `renders/ghost-mannequin/approved/{sku}-ghost-front.webp` does not exist, exit with an error.
- The batch script never moves files to `approved/` automatically. Only a human action moves files there.
- Add a precondition in the update script: verify the approved file's mtime is after the render's mtime (prevents re-approving a stale render while a fresh bad one sits in staging).

**Phase assignment:** Approval gate must be built into the CSV update tool in Phase 5. No review-less path should exist in the codebase.

---

### Pitfall 13: Techflat-to-Ghost-Mannequin Shape Collapse on Complex Garments

**What goes wrong:** Techflats are 2D top-view flat illustrations with no depth cues, no shading, no perspective. The AI generates a "3D ghost mannequin" that looks like a flat cardboard cutout with added shadow, not a volumetrically inflated garment. Hoodies lose hood volume. Bomber/varsity jackets appear paper-thin. The image is technically "generated" but commercially unusable.

**Why it happens:** Generative models infer 3D structure from lighting cues, fabric folds, and perspective in source imagery. Techflats deliberately omit all of these. Garments with complex 3D structure (hoodies, sherpa jackets, bombers) fail worse than flat-cut garments (tees, shorts).

**Prevention:**
- Classify SKUs by 3D complexity before batch run: Group A (tees, shorts, joggers — moderate risk), Group B (hoodies, crewnecks, jackets — high shape collapse risk), Group C (jerseys — text risk dominates).
- Group B prompt addition: `garment with natural fabric drape and volume, collar opening shows depth, sleeves have dimension and subtle fold shadows`.
- Provide a style reference image in the Gemini API call (multimodal image+text): a royalty-free ghost mannequin photo of a similar garment category to anchor the 3D expectation.
- Budget 2–3 generation samples per Group B SKU vs 1–2 for Group A.

**Phase assignment:** SKU complexity classification in Phase 1. Group-specific prompt templates before Group B runs.

---

## Minor Pitfalls

---

### Pitfall 14: Output Overwrite on Re-run Corrupts Mid-Review

**What goes wrong:** Output path `renders/ghost-mannequin/{sku}-ghost-front.webp` is fixed. A re-run for a failed SKU overwrites any previous output. If a reviewer was mid-review, they are comparing a new generation against their memory of the old one.

**Prevention:** Write re-runs to versioned paths (`{sku}-ghost-front-v{N}.webp`) in a staging subdirectory. The approval tool promotes the approved file to the canonical path. The canonical path never carries a version suffix.

**Phase assignment:** Phase 3 (output path logic).

---

### Pitfall 15: `BLACK is Beautiful` Legacy Bundle Dirs Are Ambiguous at Runtime

**What goes wrong:** Four legacy-named bundle directories exist alongside the numbered series directories: `BLACK is Beautiful Jersey`, `BLACK is Beautiful Jersey (Giants)`, `BLACK is Beautiful Jersey (Oakland)`, `BLACK is Beautiful Jersey (White)`. None of these match any current CSV SKU names. A fuzzy resolver that normalizes to lowercase could incorrectly match `BLACK is Beautiful Jersey` against `BLACK is Beautiful Jersey Series: 1. SF inspired` — producing the wrong techflat for a numbered series SKU.

**Prevention:** `bundle_dir` column in CSV must use exact directory name (case-sensitive). No fuzzy matching at runtime. Legacy directories that don't map to any current CSV SKU are ignored by the pipeline (they are historical artifacts, not active SKUs).

**Phase assignment:** Phase 1 (manual CSV population).

---

### Pitfall 16: Accessories and Two-Piece Sets Cannot Use Ghost Mannequin Directly

**What goes wrong:** The Signature Beanie (sg-007) and The Fannie (lh-005) have no torso or shoulder to anchor the ghost mannequin framing. The Kids sets (kids-001, kids-002) are two-piece sets — the AI either generates only one piece or produces a physically merged top-and-bottom.

**Prevention:**
- Accessories: exclude from ghost mannequin batch entirely. Handle in a separate styled flat-lay generation pass in v1.3.
- Kids sets: generate top and bottom separately, then composite. Do not attempt two-piece ghost mannequin in a single call.
- Mark these SKUs in the batch script with `skip_reason: "accessory"` or `skip_reason: "multi-piece"` in SKIPPED.json at Phase 1.

**Phase assignment:** Phase 1 (SKU classification before batch design).

---

### Pitfall 17: Dark Garment Lighting Collapse

**What goes wrong:** Black Rose collection garments (black-dominant colorway) generate flat, detail-less results because the AI defaults to low-key dramatic lighting rather than even product studio lighting. Fabric texture becomes invisible.

**Prevention:** Explicitly specify high-key, even product studio lighting in every prompt: `even studio lighting from three-point setup, no dramatic shadows, fabric texture clearly visible across the entire garment`. Run one black garment SKU in the pilot before processing all Black Rose SKUs.

**Phase assignment:** Phase 3 (prompt template, pilot run).

---

### Pitfall 18: WebP Output Quality Not Set Explicitly

**What goes wrong:** `image.save("output.webp")` without explicit quality parameter uses PIL's default (quality=80). The difference vs quality=85 is subtle but visible in fine textures (mesh holes, rib knit patterns) on a large display.

**Prevention:** Always pass `quality=85, method=6` to PIL's `save()` for WebP output. Assert the output file is >50KB for a 1200x1200 image. Sub-threshold files indicate quality degradation.

**Phase assignment:** Phase 3 (output pipeline).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| SKU→bundle mapping | 17/30 products need manual verification (Pitfall 2) | Add `bundle_dir` column to CSV; no fuzzy matching |
| Bundle dir audit | 12 dirs have no techflat-front.jpeg | Pre-populate SKIPPED.json; do not crash on missing techflat |
| Source input resolution | render_source_override is the wrong column (Pitfall 5) | Ghost mannequin always uses bundle_dir/techflat-front.jpeg |
| CSV adapter wiring | Import fails for scripts/ callers (Pitfall 10) | Explicit sys.path + make install smoke test |
| Accessory/kids SKUs | Cannot ghost mannequin (Pitfall 16) | Classify and skip in Phase 1 |
| Generation batch | Gemini silent HTTP 200 failure (Pitfall 4) | Six-field response classifier before any write |
| Jersey batch | Text/number hallucination (Pitfall 3) | Jersey-specific prompts + OCR gate; front-only in v1.2 |
| Gemini prompts | Safety filter refusal on mesh/hollow terms | Use technical vocabulary; test single jersey SKU first |
| Cost control | Unbounded retry spiral (Pitfall 7) | Hard spend cap + retry class separation |
| Cost gate | --skip-preflight bypass (Pitfall 11) | TTY detection; mandatory audit log on bypass |
| Stage wiring | BRIA alpha matte used raw as Gemini input (Pitfall 8) | Explicit white composite before Stage 2 input |
| Post-generation | Background not pure white (Pitfall 9) | Corner-pixel assertion; re-composite via alpha matte |
| Re-runs | Output overwrites mid-review (Pitfall 14) | Versioned staging paths; approval tool manages promotion |
| Review gate | CSV updated before human review (Pitfall 12) | approved/ directory precondition enforced structurally |
| CSV update | Corruption on interrupted write (Pitfall 6) | Atomic temp+rename in same dir; row-count assertion |
| Source data integrity | Wrong source data drives wrong renders (Pitfall 1) | branding_spec from CSV only; product-identity QA check |

---

## Sources

- Commit `f25fd25d3` (`refactor(imagery): Phase B1 scorched earth`) — HIGH confidence, first-party post-mortem documenting root causes of prior pipeline failure
- `/Users/theceo/DevSkyy/renders/preflight.py` — HIGH confidence, live cost-gate implementation showing existing STOP AND SHOW pattern
- `/Users/theceo/DevSkyy/skyyrose/core/catalog_loader.py` — HIGH confidence, actual shared CSV adapter module
- `data/product-bundles/` directory scan vs `skyyrose-catalog.csv` cross-reference — HIGH confidence, run live during research (2026-04-22)
- Project memory (`MEMORY.md`): "Gemini text weakness: Struggles with text rendering on jersey backs" — HIGH confidence, session-documented
- [Gemini 2.5 Flash Image prompting guide](https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/) — MEDIUM confidence ("complex typography sometimes needs refinement")
- [Gemini image generation official docs](https://ai.google.dev/gemini-api/docs/image-generation) — HIGH confidence (`responseModalities` requirement, transparent background limitation confirmed)
- [Ghost mannequin reflective/mesh activewear fixes](https://imageworkindia.com/ghost-mannequin-reflective-mesh-activewear/) — MEDIUM confidence (practitioner guide)
- [Ghost mannequin neck joint hallucinations](https://imageworkindia.com/generative-fill-prompt-ghost-mannequin-neck-joint/) — MEDIUM confidence
- [Atomic file writing in Python 2026](https://docs.bswen.com/blog/2026-04-04-atomic-file-writing-python/) — HIGH confidence (os.rename() cross-filesystem caveat confirmed)
- [Gemini 429 rate limit behavior](https://discuss.ai.google.dev/t/gemini-2-5-flash-image-frequent-429-resource-exhausted-during-sequential-image-generation-seeking-clarity-on-rate-limits/118691) — MEDIUM confidence (developer-reported ~2 RPM effective throughput, no Retry-After header)
- [Gemini safety settings 2026](https://ai.google.dev/gemini-api/docs/safety-settings) — MEDIUM confidence (specific jersey/clothing filter behavior inferred from pattern)

*Research completed: 2026-04-22 | Milestone: v1.2 Ghost Mannequin Pipeline*
