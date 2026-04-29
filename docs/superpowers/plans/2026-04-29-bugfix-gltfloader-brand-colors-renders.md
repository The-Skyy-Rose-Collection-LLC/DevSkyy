# Post-Image-Taste Bugfix Sprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close three open items left after the image-taste-frontend session: fix the skyy-3d.js GLTFLoader initialization bug, silence the PHP brand-color constant redefinition warnings, and recover + run the Nano Banana render pipeline for 12 SKUs missing `front_model_image`.

**Architecture:**
- Task 1 is a one-line JS fix in the WordPress theme's Three.js character overlay script.
- Task 2 is a one-line fix in the Python brand-constants generator followed by a regenerate step.
- Task 3 recovers the full Nano Banana pipeline package from a git worktree, then runs a batch render for 12 SKUs. Task 3 requires an explicit STOP/confirmation before any paid API call.

**Tech Stack:** Vanilla JS (ES5 IIFE), PHP 8.2 / WordPress, Python 3.14 + google-genai SDK (`gemini-3-pro-image-preview`).

---

## File Map

| File | Task | Action |
|------|------|--------|
| `wordpress-theme/skyyrose-flagship/assets/js/skyy-3d.js` | 1 | Modify line 56 |
| `scripts/sync_brand_to_php.py` | 2 | Modify lines 94-96 |
| `wordpress-theme/skyyrose-flagship/inc/brand.generated.php` | 2 | Regenerate (do not hand-edit) |
| `scripts/nano-banana-run.py` | 3 | Recover from worktree |
| `scripts/nano_banana/*.py` (18 modules) | 3 | Recover from worktree |
| `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` | 3 | Write `front_model_image` paths for 12 SKUs |

---

## Task 1 — Fix `loadThree()` GLTFLoader early-exit

**Root cause:** `loadThree()` returns early when `window.THREE` is already set, but never attaches `window.THREE_GLTFLoader`. Three.js r147+ ESM builds do NOT attach `GLTFLoader` to the `THREE` namespace — it is a separate addon imported via `jsm/loaders/GLTFLoader.js`. When another script pre-loads `window.THREE`, `loadModel()` finds `window.THREE_GLTFLoader === undefined` and warns/exits without loading the Skyy character.

**Files:**
- Modify: `wordpress-theme/skyyrose-flagship/assets/js/skyy-3d.js:56`

- [ ] **Step 1.1 — Reproduce the bug in devtools**

  Open a page that loads Three.js via CDN (e.g., any immersive template or the front page with `template-immersive-*.php`). In the browser console:
  ```js
  // Simulate the bug: set window.THREE but NOT window.THREE_GLTFLoader
  window.THREE = window.THREE || { version: '0.170.0' };
  // The character canvas should warn: "Skyy 3D: GLTFLoader not available"
  ```
  Expected: `console.warn` fires from `skyy-3d.js:135`.

- [ ] **Step 1.2 — Apply the fix**

  In `wordpress-theme/skyyrose-flagship/assets/js/skyy-3d.js`, change **line 56** from:
  ```js
  	if ( window.THREE ) {
  ```
  to:
  ```js
  	if ( window.THREE && window.THREE_GLTFLoader ) {
  ```
  The surrounding context should look like:
  ```js
  	function loadThree( callback ) {
  		if ( window.THREE && window.THREE_GLTFLoader ) {
  			callback( window.THREE );
  			return;
  		}

  		var base = 'https://cdn.jsdelivr.net/npm/three@0.170.0';
  ```

- [ ] **Step 1.3 — Verify fix logic**

  After the fix, `loadThree()` only early-returns when BOTH `window.THREE` AND `window.THREE_GLTFLoader` are set. When Three.js is pre-loaded by an immersive template without GLTFLoader, `loadThree()` injects the module script, which imports both and attaches both. The `three-ready` event fires and `callback` is called with the complete THREE object.

  Manual browser test:
  ```js
  // In console on any page with skyy-3d.js loaded:
  // 1. Confirm no "GLTFLoader not available" warning in console
  // 2. Confirm the skyy-3d-canvas element becomes visible (display: block)
  ```

- [ ] **Step 1.4 — Commit**

  ```bash
  git add wordpress-theme/skyyrose-flagship/assets/js/skyy-3d.js
  git commit -m "fix(skyy-3d): guard loadThree early-exit on THREE && GLTFLoader both present"
  ```

---

## Task 2 — Silence PHP brand-color constant redefinition warnings

**Root cause:** `functions.php` includes `brand.generated.php` at position 50 and `brand-colors.php` at position 52. The generated file uses bare `define()` calls for the five primary colors (`SKYYROSE_COLOR_DARK`, `SKYYROSE_COLOR_ROSE_GOLD`, etc.). When `brand-colors.php` runs second and calls `define()` for the same constants, PHP/WP-CLI emits "Constant already defined" notices. The fix belongs in the generator, not in either PHP file directly.

**Files:**
- Modify: `scripts/sync_brand_to_php.py:94-96`
- Regenerate: `wordpress-theme/skyyrose-flagship/inc/brand.generated.php`

- [ ] **Step 2.1 — Confirm the warning reproduces**

  ```bash
  cd /Users/theceo/DevSkyy/wordpress-theme/skyyrose-flagship
  # Check for duplicate define in generated file
  grep "define.*SKYYROSE_COLOR_ROSE_GOLD" inc/brand.generated.php inc/brand-colors.php
  ```
  Expected: both files emit an unguarded `define( 'SKYYROSE_COLOR_ROSE_GOLD', ...)` line.

- [ ] **Step 2.2 — Fix the generator**

  In `scripts/sync_brand_to_php.py`, the color-constants block is at lines 94-96. Change it from:
  ```python
  	for key, const in mapping.items():
  		if key in primary:
  			out.append(f"define( '{const}', {_php_string(primary[key])} );")
  ```
  to:
  ```python
  	for key, const in mapping.items():
  		if key in primary:
  			out.append(
  				f"if ( ! defined( '{const}' ) ) define( '{const}', {_php_string(primary[key])} );"
  			)
  ```

- [ ] **Step 2.3 — Regenerate the PHP file**

  ```bash
  cd /Users/theceo/DevSkyy
  source .venv/bin/activate
  python scripts/sync_brand_to_php.py
  ```
  Expected output: `wordpress-theme/skyyrose-flagship/inc/brand.generated.php` updated. No errors.

- [ ] **Step 2.4 — Verify the regenerated file has guards**

  ```bash
  grep "SKYYROSE_COLOR_ROSE_GOLD" wordpress-theme/skyyrose-flagship/inc/brand.generated.php
  ```
  Expected:
  ```
  if ( ! defined( 'SKYYROSE_COLOR_ROSE_GOLD' ) ) define( 'SKYYROSE_COLOR_ROSE_GOLD', '#B76E79' );
  ```

- [ ] **Step 2.5 — Verify the `--check` flag passes**

  ```bash
  python scripts/sync_brand_to_php.py --check
  ```
  Expected: exits 0 with "OK: ... is in sync with brand.yaml"

- [ ] **Step 2.6 — PHP lint**

  ```bash
  cd wordpress-theme
  npm run lint:php 2>&1 | tail -5
  ```
  Expected: 0 errors, 0 warnings.

- [ ] **Step 2.7 — Commit both files together**

  ```bash
  git add scripts/sync_brand_to_php.py
  git add wordpress-theme/skyyrose-flagship/inc/brand.generated.php
  git commit -m "fix(brand): guard color constant defines in generator to prevent WP-CLI redefinition warnings"
  ```

---

## Task 3 — Recover Nano Banana pipeline and render 12 missing front_model_image SKUs

**⚠️ PAID API CALLS — READ THIS BEFORE RUNNING STEP 3.4**

This task uses `gemini-3-pro-image-preview` (Nano Banana Pro). Each image generation call is a paid Gemini API request. Step 3.4 contains the exact STOP/confirm protocol. Do not run any `generate` subcommands until after the user types "y" at the prompt.

**Root cause for missing pipeline:** The `scripts/nano_banana/` package in `main` contains only `catalog.py` + `__init__.py`. The full 20-module package (cli, pipeline, generate, router, etc.) and the entry-point `scripts/nano-banana-run.py` exist only in the git worktree at `.claude/worktrees/infallible-bell/`. They need to be recovered to main.

**Files:**
- Recover: `scripts/nano-banana-run.py` (from worktree)
- Recover: `scripts/nano_banana/` — 18 missing modules (from worktree)
- Update: `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` (write `front_model_image` column for 12 SKUs)

- [ ] **Step 3.1 — Confirm the 12 SKUs missing front_model_image**

  ```bash
  python3 -c "
  import csv
  missing = []
  with open('wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv') as f:
      for r in csv.DictReader(f):
          if not r.get('front_model_image','').strip():
              missing.append((r['sku'], r['name'], r['collection']))
  print(f'Missing front_model_image: {len(missing)}')
  for sku, name, col in missing:
      print(f'  {sku:<15} {col:<15} {name}')
  "
  ```
  Expected (12 SKUs):
  ```
  Missing front_model_image: 12
    br-012          black-rose      BLACK is Beautiful Jersey Series: 5. Last Oakland (Baseball)
    lh-004          love-hurts      Love Hurts Bomber Jacket
    lh-005          love-hurts      The Fannie
    sg-003          signature       The Bridge Series 'Stay Golden' Shorts
    sg-005          signature       The Bridge Series 'The Bay Bridge' Shirt
    sg-007          signature       The Signature Beanie
    sg-013          signature       Mint & Lavender Crewneck
    sg-014          signature       Mint & Lavender Sweatpants
    sg-015          signature       The Windbreaker Set
    br-003-oakland  black-rose      BLACK is Beautiful Jersey Series: 0. Baseball Classic (Oakland Edition)
    br-003-giants   black-rose      BLACK is Beautiful Jersey Series: 0. Baseball Classic (Giants Edition)
    br-003-white    black-rose      BLACK is Beautiful Jersey Series: 0. Baseball Classic (White Edition)
  ```
  If the count differs, stop and verify before continuing.

- [ ] **Step 3.2 — Recover missing nano_banana modules from worktree**

  ```bash
  WORKTREE=".claude/worktrees/infallible-bell"

  # Copy entry point
  cp "$WORKTREE/scripts/nano-banana-run.py" scripts/nano-banana-run.py

  # Copy all missing package modules (catalog.py is already correct in main — skip it)
  for f in "$WORKTREE/scripts/nano_banana/"*.py; do
      fname=$(basename "$f")
      if [ "$fname" != "catalog.py" ]; then
          cp "$f" "scripts/nano_banana/$fname"
      fi
  done

  echo "Recovered files:"
  ls scripts/nano_banana/*.py | wc -l
  ```
  Expected: `ls` shows 20+ `.py` files in `scripts/nano_banana/`.

- [ ] **Step 3.3 — Verify the pipeline imports cleanly**

  ```bash
  source .venv/bin/activate
  python -c "from nano_banana.cli import main; print('import ok')" 2>&1
  ```
  Expected: `import ok` with no errors. If errors, read the traceback and fix any missing dependency:
  ```bash
  pip install -r requirements-imagery.txt
  ```

- [ ] **Step 3.4 — STOP: Confirm render manifest before any API call**

  Before running a single generation, print the following and wait for "y":
  ```
  STOP — Confirm before proceeding:

  Action  : Nano Banana generate (gemini-3-pro-image-preview)
  SKUs    : br-012, lh-004, lh-005, sg-003, sg-005, sg-007,
            sg-013, sg-014, sg-015, br-003-oakland, br-003-giants, br-003-white
  View    : front (front_model_image only)
  Count   : 12 image generation calls
  Command : python scripts/nano-banana-run.py generate --step front --pro
  Cost    : Gemini per-image rate × 12 — confirm your API quota

  Proceed? [y/N]
  ```
  **Do not proceed until the user types "y".**

- [ ] **Step 3.5 — Run dry-run to validate pipeline connectivity**

  ```bash
  source .venv/bin/activate
  python scripts/nano-banana-run.py dry-run 2>&1 | head -30
  ```
  Expected: lists SKUs and steps it would run, exits 0, no API calls made.

- [ ] **Step 3.6 — Generate front_model_image for each missing SKU**

  Run one SKU at a time to verify output format before batching:
  ```bash
  source .venv/bin/activate
  python scripts/nano-banana-run.py generate --sku br-012 --step front --pro
  ```
  Expected: creates `assets/images/products/renders/br-012-front-model.webp` (or per-SKU slug path — check the output directory in the log). Verify the file exists and is a valid image:
  ```bash
  file assets/images/products/renders/br-012-front-model.webp
  # Expected: RIFF ... WEBP
  ```

  Once the first SKU succeeds, run the remainder:
  ```bash
  for sku in lh-004 lh-005 sg-003 sg-005 sg-007 sg-013 sg-014 sg-015 br-003-oakland br-003-giants br-003-white; do
      python scripts/nano-banana-run.py generate --sku "$sku" --step front --pro
      echo "Done: $sku"
  done
  ```

- [ ] **Step 3.7 — Verify all 12 output files exist**

  ```bash
  python3 -c "
  import csv, os
  from pathlib import Path
  root = Path('wordpress-theme/skyyrose-flagship')
  skus = ['br-012','lh-004','lh-005','sg-003','sg-005','sg-007',
          'sg-013','sg-014','sg-015','br-003-oakland','br-003-giants','br-003-white']
  # Check renders directory for expected files
  render_dir = Path('assets/images/products/renders')
  for sku in skus:
      candidates = list(render_dir.glob(f'{sku}*front*')) if render_dir.exists() else []
      status = 'OK' if candidates else 'MISSING'
      print(f'{status:<8} {sku}', candidates[0] if candidates else '')
  "
  ```

- [ ] **Step 3.8 — Update catalog CSV with front_model_image paths**

  For each SKU that generated successfully, update the `front_model_image` column in
  `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`.

  The path must be theme-relative (matching the existing format in the CSV, e.g. `assets/images/products/...`).

  ```bash
  # Verify the current path format for a SKU that already has front_model_image
  python3 -c "
  import csv
  with open('wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv') as f:
      for r in csv.DictReader(f):
          if r.get('front_model_image','').strip():
              print(r['sku'], '→', r['front_model_image'])
              break
  "
  ```

  Edit the CSV directly (use the Edit tool, not sed) — add the `front_model_image` path for each of the 12 SKUs.

- [ ] **Step 3.9 — Verify catalog integrity**

  ```bash
  python3 -m pytest tests/test_catalog_csv_integrity.py -v 2>&1 | tail -20
  ```
  Expected: all tests PASS. If `EXPECTED_SKU_COUNT` fails, verify the row count is still 33 (no new rows were added).

- [ ] **Step 3.10 — Commit**

  ```bash
  git add scripts/nano-banana-run.py scripts/nano_banana/
  git add wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv
  git commit -m "feat(renders): recover nano_banana pipeline; add front_model_image for 12 SKUs"
  ```

- [ ] **Step 3.11 — Deploy WordPress theme**

  ```bash
  cd wordpress-theme
  npm run verify       # must pass before deploy
  npm run deploy
  ```
  The post-deploy verify gate will curl `https://skyyrose.co/?deploy_verify=<ts>` and assert HTTP 200 + no PHP error markers.

---

## Self-Review

**Spec coverage:** All three user-reported items have tasks.

**Placeholder scan:** No TBDs, no "implement later". Step 3.8 asks the executor to use the Edit tool for CSV — this is the correct approach since CSV edits are SKU-specific and depend on the actual output filenames from Step 3.6.

**Type consistency:** No shared types across tasks — each task is self-contained.

**Load-order note (Task 2):** `functions.php` line 50 = `brand.generated.php`, line 52 = `brand-colors.php`. After the fix, `brand.generated.php` emits `if ( ! defined(...) ) define(...)` for colors. Since it loads first, it sets them. `brand-colors.php` then also calls plain `define()` for the same 5 colors — which will still warn. If warnings persist after Task 2, the follow-up fix is to add `defined()` guards in `brand-colors.php` too. The plan addresses the generator (auto-generated file); the manually-authored file is a separate, lower-priority cleanup.
