---
name: design-qc
description: Use when the user asks to check, evaluate, or improve the design/UI of the DevSkyy app. Captures screenshots via openwolf designqc, then reviews them against modern UI standards.
---

When the user asks you to check, evaluate, or improve the design/UI of their app:

1. Run `openwolf designqc` via Bash to capture screenshots.
   - The command auto-detects a running dev server, or starts one from package.json if needed
   - Use `--url <url>` only if auto-detection fails
   - The command saves compressed JPEG screenshots to `.wolf/designqc-captures/`
   - Full pages are captured as sectioned viewport-height images (top, section2, ..., bottom)
2. Read the captured screenshot images from `.wolf/designqc-captures/` using the Read tool.
3. Evaluate the design against modern standards (Shadcn UI, Tailwind, clean React patterns):
   - Spacing and whitespace consistency
   - Typography hierarchy and readability
   - Color contrast and accessibility (WCAG)
   - Visual hierarchy and focal points
   - Component consistency
   - Whether the design looks "dull" or "white-coded" (generic, no personality)
4. Provide specific, actionable feedback with fix suggestions.
5. If the user approves, implement the fixes directly in their code.
6. After fixes, re-run `openwolf designqc` to capture new screenshots and verify improvement.

**Token awareness:** Each screenshot costs ~2500 tokens. The command compresses images (JPEG quality 70, max width 1200px) to minimize cost. For large apps, use `--routes / /specific-page` to limit captures.

## When QA'ing the SkyyRose WordPress theme specifically

Standard step 3 (Shadcn/Tailwind/generic-React) does NOT apply — this is a brand-locked luxury-streetwear storefront, not a dashboard. Replace step 3 with:

- Cross-check every animated/motion element against `docs/design/visual-pattern-shortlist.md` — is it one of the 176 screened patterns, or an unscreened improvisation? Flag anything that reads generic-SaaS (glassmorphism dashboards, gradient-blob-on-white heroes, Inter/Space-Grotesk-as-safe-default) — that shortlist exists specifically to keep this theme out of that territory.
- Grep any new CSS/JS for `Cormorant Garamond`, `Playfair Display`, `Bebas Neue`, `Yellowtail` — cut fonts, hard fail regardless of how the design looks.
- Confirm every motion/animation has a `prefers-reduced-motion: reduce` fallback — not optional here.
- Confirm hex values trace to real tokens (`#B76E79` / `#0A0A0A` / `#C0C0C0` / `#DC143C` / `#D4AF37`), not placeholder colors left over from a sourced pattern spec.
- "Dull or white-coded" becomes: does it read as Kith / Oaklandish / Culture Kings / Fear of God / Palm Angels, or does it drift toward European-luxury-serif or generic streetwear-template territory?
