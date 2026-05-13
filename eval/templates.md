---
name: Per-Template UX Score, Issue Count, Performance Budget
specified_by: [v2: §5 Phase 0, §8]
phase: 0
test_command: node scripts/measurement/run-template-eval.js --template=<slug>  # PHASE 0.5 DELIVERABLE — script does not exist yet; running it will exit 1 with a 'Phase 0.5 not started' message until the runner is built. See scripts/measurement/README.md.
pass_threshold: UX score ≥ 8/10, P0 issues = 0, P1 issues ≤ 2, mobile LCP < 2.5s
last_updated: 2026-05-03
last_updated_by: eval-harness (Phase 0)
---

# Per-Template Eval Rubric

For each template (whether refactored or net-new in Phase 4), this rubric scores it across four dimensions before the template is allowed to merge.

## Dimensions

| Dimension | Method | Target | Pass threshold |
|-----------|--------|--------|----------------|
| **UX score** | `critique` skill 3-persona walkthrough (WP §7.2) | ≥ 8/10 | All 3 personas walk away "earned" or "satisfied"; no persona "rolled their eyes" |
| **Audit P0/P1 count** | `audit` skill — accessibility, perf, theming, anti-patterns | P0 = 0, P1 ≤ 2 | Zero P0 (blocking) issues; at most 2 P1 (high) issues with documented mitigation timeline |
| **Performance — mobile LCP** | PageSpeed Insights mobile profile + real-device verification | < 2.5s | Per WP §4.5 |
| **Performance — CLS / INP / TTFB** | Same | CLS < 0.1, INP < 200ms, TTFB < 600ms | Per WP §4.5 |
| **Brand coherence** | `skyyrose-brand-dna` voice/visual rules (`eval/brand.md`) | 0 banned phrases, palette match | Per WP §2.4 voice + §1.3 banned elements |
| **Banned elements** | Manual + grep against template output | 0 instances | Per WP §1.3 banned-by-default list |
| **5-pass thinking pass** | Per-page `eval/design-thinking/<slug>.md` exists with all 5 passes written in prose | Present | Per WP §1.1 |
| **Critique loop** | Build → self-critique → verify → revise → second self-critique → ship documented in commit history | All steps present | Per WP §1.2 + §7.1 |
| **KB pattern entry** | `kb-distill.js` wrote a `knowledge-base/patterns/wordpress/<slug>.md` entry | Present with `loop_count_to_converge` set | Per WP §1.5 Layer 3 |

## Test command

```bash
node scripts/measurement/run-template-eval.js --template=<slug>
```

Exits 0 on PASS, 1 on FAIL with diagnostic output. Reads `eval/templates-rows/<slug>.md` for per-template scores written by the agent that built the template.

## Per-template row format

Each template the agent works on adds a row file at `eval/templates-rows/<slug>.md`:

```yaml
---
template: <slug>
ux_score: <number>/10
audit_p0: <number>
audit_p1: <number>
mobile_lcp_seconds: <decimal>
cls: <decimal>
inp_ms: <number>
ttfb_ms: <number>
brand_coherence_pass: <bool>
banned_elements_count: <number>
five_pass_thinking_doc: eval/design-thinking/<slug>.md
critique_loop_iterations: <integer>
kb_pattern_entry: knowledge-base/patterns/wordpress/<slug>.md
last_evaluated: <YYYY-MM-DD>
status: <PASS | FAIL>
---

<prose explaining any FAIL conditions and remediation plan>
```

## Templates this rubric applies to

All templates listed in V2 §6 per-page accountability table get a row, including:

- All `template-*.php` files (collection, immersive, landing, info, experiences, spatial, style-quiz, drop-day, drop-live, etc.)
- `front-page.php`, `single-product.php` (and the new `single-product-narrative.php` variant from Phase 5.3), `archive-product.php`
- `skyyrose-canvas.php` (the universal builder shell)
- WC overrides: `woocommerce/cart/cart.php`, `woocommerce/checkout/form-checkout.php`, `woocommerce/single-product.php`

## Phase entry checklist

Phase 4 (new templates) and Phase 5 (commerce surfaces) gate each template's merge on this rubric returning PASS. Phase 7 ship-check re-runs this against every template before deploy.
