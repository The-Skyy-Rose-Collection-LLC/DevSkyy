---
description: Run the FASHN/GarmentFidelityAgent preflight gate. Manifests every SKU source image, resolution method, and estimated cost BEFORE any API call executes. Invoke before any render generation. Argument is an optional SKU or collection filter.
argument-hint: [sku-or-collection]
allowed-tools: Bash, Read, Glob, Grep
---

You are running the renders preflight gate.

## What to do

1. Run the preflight module with any user-supplied filter:

   ```bash
   uv run python -m renders.preflight $ARGUMENTS
   ```

   If no argument is provided, run preflight across all SKUs in the active manifest.

2. Read the resulting manifest. Look for:
   - SKUs missing source images
   - Source images with resolution method `fallback` or `unknown` (not `manifest` or `verified`)
   - Estimated cost outliers (a single SKU costing >5x the median)
   - Color-space or aspect-ratio anomalies flagged by the gate

3. Summarize findings in this exact format:

   ```
   ## Preflight Result: <PASS | BLOCK>

   - Total SKUs checked: N
   - Manifest-resolved: N
   - Fallback-resolved: N (LIST any names)
   - Missing sources: N (LIST sku ids — these BLOCK the run)
   - Estimated total cost: $X.XX
   - Cost outliers: [list]

   ## Recommendation
   <one sentence: PROCEED, FIX-AND-RETRY, or HOLD>
   ```

4. If the gate returns BLOCK status, do NOT proceed to generation. List the exact files/SKUs that need attention. Do not auto-fix without user confirmation — preflight is an Ask gate per CLAUDE.md.

5. If the gate returns PASS, surface the manifest path so the user can review before authorizing the actual `python -m renders.fashn` call (which is gated separately in settings.json `ask`).

## What NOT to do

- Do NOT call `python -m renders.fashn` or `python -m renders.generate` from this command. Those are separately gated.
- Do NOT add `--no-preflight` or any flag that bypasses the gate. That flag is denied at the settings layer.
- Do NOT silently retry on failure. Surface the failure and stop.
