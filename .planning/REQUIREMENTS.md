# Requirements: SkyyRose Imagery Pipeline & Product Photography

**Defined:** 2026-04-22 (v1.2) | **Prior milestone:** 2026-03-10 (v1.1)
**Core Value:** skyyrose.co works flawlessly on every device, passes WCAG AA accessibility, and shows the right products in the right collections — with professional ghost mannequin product photography for all 28 garment SKUs.

---

## v1.2 Requirements

Requirements for the CSV-driven ghost mannequin imagery pipeline. Phase numbering continues from v1.1 (last phase: 13).

### Infrastructure & Catalog

- [ ] **INFRA-01**: Shared CSV adapter module (`skyyrose.core.catalog_loader`) is the single data source for all 3 imagery pipelines (nano-banana, Elite Studio compositor, FLUX orchestrator)
- [ ] **INFRA-02**: SKU→bundle resolver keyed on `manifest.json` SKU field — resolves all name-mismatch cases without renaming any directory
- [ ] **INFRA-03**: 3 broken readers fixed: `renders/config.py` created, `elite_studio/fashion/context.py` stale CSV path corrected, `nano_banana.catalog` shim rebuilt
- [ ] **INFRA-04**: `garment_type_lock` column added to `skyyrose-catalog.csv` — enables garment-type prompt routing across all 3 pipelines
- [ ] **INFRA-05**: All techflat source files are single-view images (front / back / top / bottom as distinct files) before any pipeline run — compound sheets separated before intake
- [ ] **INFRA-06**: Missing techflat assets for br-007, sg-009, sg-012, br-012, sg-015 added to bundle directories before Phase 2 runs (user provides source assets)
- [ ] **INFRA-07**: Preflight audit script: scans all 30 SKUs, verifies bundle + techflat-front exists, writes `SKIPPED.json` — runs before any paid API call

### Ghost Mannequin Agent

- [ ] **GM-01**: Ghost mannequin LangGraph agent in Elite Studio (`skyyrose/elite_studio/agents/ghost_mannequin_agent.py`) — consistent with existing compositor architecture
- [ ] **GM-02**: 2-step generation pipeline per SKU: Gemini 2.5 Flash Image generate-on-white → BRIA RMBG 2.0 background removal → PIL white-background composite
- [ ] **GM-03**: Garment-type routing: jersey / hoodie / crewneck / tee / shorts / joggers / jacket / set each use distinct prompt templates driven by `garment_type_lock`
- [ ] **GM-04**: Dry-run mode: full cost preview without any API call; STOP AND SHOW manifest (exact SKU list, API, per-image cost, total cost) before any paid run
- [ ] **GM-05**: Output to `renders/ghost-mannequin/{sku}-ghost-front.webp`, 1200×1200px WebP — per-SKU failure logged to `renders/ghost-mannequin/failures.json`
- [ ] **GM-06**: Accessories (sg-007, lh-005) and unresolved SKUs silently skipped at runtime with reason logged — no error, no abort

### QA & Safety

- [ ] **QA-01**: Gemini response classifier node: validates 6 fields (finish_reason, responseModalities, file exists on disk, size > 10KB, path written, no safety block) — raises on all 4 silent HTTP-200 failure modes
- [ ] **QA-02**: Retry class separation in agent graph: retryable errors (429, transient 5xx) use exponential backoff; non-retryable (safety block, wrong modality, content filter) immediately flag SKU — hard spend cap enforced per run
- [ ] **QA-03**: Jersey OCR verification node: text and number zone check via Gemini Vision before any jersey SKU enters the review queue — gate applies to br-003, br-008, br-009, br-010, br-011, br-012
- [ ] **QA-04**: Background purity validator: corner-pixel RGB sample post-generation, hard reject if any corner pixel is more than 5 RGB units from (255, 255, 255)

### Review & Approval

- [ ] **REV-01**: `approved/` structural precondition: CSV update tool `exit(1)` if `renders/ghost-mannequin/approved/{sku}-ghost-front.webp` does not exist — structural enforcement that survives autonomous agent loops
- [ ] **REV-02**: `approve-ghost {sku}` CLI: moves file to `approved/`, updates CSV `front_model_image` field atomically, logs approval timestamp
- [ ] **REV-03**: `reject-ghost {sku} "{reason}"` CLI: logs rejection reason to `renders/ghost-mannequin/rejections.json`, keeps file in review directory for re-run
- [ ] **REV-04**: CSV atomic write: `os.replace()` temp-file pattern + row-count assertion before overwrite — prevents CSV corruption on interruption or agent loop abort

### WooCommerce Upload

- [ ] **UPLOAD-01**: After 100% approval of all in-scope front ghost mannequin images, batch upload approved images to WooCommerce Media Library and update each product's image field — triggered only on explicit user confirmation, never autonomously

---

## v1.1 Requirements (Completed 2026-03-11)

### Accessibility

- [x] **A11Y-01**: All buttons have explicit `type="button"` attribute
- [x] **A11Y-02**: No duplicate element IDs in rendered HTML (stylesheet handles, nonce fields)
- [x] **A11Y-03**: Empty headings have content or `aria-hidden="true"`
- [x] **A11Y-04**: Empty links have descriptive `aria-label` attributes
- [x] **A11Y-05**: Focusable elements with `aria-hidden="true"` have `tabindex="-1"`
- [x] **A11Y-06**: All form inputs (radio, text) have associated labels or `aria-label`
- [x] **A11Y-07**: Skip navigation link is wired and functional
- [x] **A11Y-08**: Stylesheet and script handles are unique (no `skyyrose-accessibility` collision)
- [x] **A11Y-09**: Below-fold images have `loading="lazy"`, hero images have `loading="eager"`

### Color Contrast

- [x] **CNTR-01**: All text meets WCAG AA contrast ratio (4.5:1 normal text, 3:1 large text)
- [x] **CNTR-02**: Narrative subtext opacity increased to meet 4.5:1 against background
- [x] **CNTR-03**: Interactive-cards small text (10-12px) meets minimum contrast
- [x] **CNTR-04**: Love Hurts $0 pricing replaced with "Pre-Order" display

### Responsive & Typography

- [x] **RESP-01**: Font sizes scale appropriately across mobile/tablet/desktop breakpoints
- [x] **RESP-02**: No horizontal overflow or layout breaking on mobile devices (320px+)
- [x] **RESP-03**: Touch targets meet minimum 44x44px on mobile
- [x] **RESP-04**: Typography hierarchy is consistent across all page templates

### Luxury Cursor

- [x] **CURS-01**: Cursor renders above modals/popups (z-index management)
- [x] **CURS-02**: Cursor pauses or adapts when modal/popup is open
- [x] **CURS-03**: Cursor JS does not load on pages where it's CSS-hidden (immersive)

### Collection & Product Data

- [ ] **DATA-01**: Black Rose collection shows correct hero banner image
- [x] **DATA-02**: Pre-order products are not displayed in live collection catalog pages
- [x] **DATA-03**: Product-to-collection assignments match authoritative product list

---

## Future Requirements (v1.3+)

### Back Garment Generation

- **GM-BACK-01**: Ghost mannequin back shots for all SKUs with confirmed `techflat-back.jpeg`
- **GM-BACK-02**: Front + back composite into a single 2400×1200px hero image per product

### Accessories & Special Cases

- **FLAT-01**: Flat-lay pipeline for sg-007 (Signature Beanie)
- **FLAT-02**: Flat-lay pipeline for lh-005 (The Fannie)

### Ongoing Intake

- **INTAKE-01**: Ghost mannequin generation on new product intake (per-SKU, not batch)
- **INTAKE-02**: Automated WooCommerce upload on new product approval (no manual gate)

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-angle generation (side, 3/4) | Only front techflats confirmed; back deferred to v1.3 |
| Frontend review UI | CLI approval tool sufficient for 30-product catalog |
| Real-time API in web requests | Ghost mannequin takes 10–60s/image; batch-only pipeline |
| On-model / scene composites | Elite Studio compositor handles those; this pipeline is white-bg studio only |
| WCAG AAA compliance | Targeting AA level — AAA deferred |
| New feature development | This milestone is imagery pipeline only |

---

## Traceability

_Populated by roadmapper — maps each REQ-ID to the phase that satisfies it._

### v1.2

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 through INFRA-07 | — | Pending |
| GM-01 through GM-06 | — | Pending |
| QA-01 through QA-04 | — | Pending |
| REV-01 through REV-04 | — | Pending |
| UPLOAD-01 | — | Pending |

### v1.1

| Requirement | Phase | Status |
|-------------|-------|--------|
| A11Y-01 through A11Y-09 | Phase 10 | Complete |
| CNTR-01 through CNTR-04 | Phase 11 | Complete |
| RESP-01 through RESP-04 | Phase 12 | Complete |
| CURS-01 through CURS-03 | Phase 13 | Complete |
| DATA-01 | Phase 9 | Pending |
| DATA-02 through DATA-03 | Phase 9 | Complete |

**Coverage:**
- v1.2 requirements: 19 total (7 INFRA + 6 GM + 4 QA + 4 REV + 1 UPLOAD)
- Mapped to phases: 0 (pending roadmap)
- v1.1 requirements: 22 total, 21 complete, 1 pending (DATA-01)

---

*Requirements defined: 2026-04-22*
*Last updated: 2026-04-22 — v1.2 milestone scoping*
