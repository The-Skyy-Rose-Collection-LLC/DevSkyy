---
name: saas-gate
description: SaaS Product Delivery Standard — every deliverable mobile-verified, image-optimized, sales-grade
tags: [pipeline-protocol, quality-gate]
applies_to: [ux-architect, ui-designer, brand-guardian, frontend-developer, senior-developer]
last_verified: 2026-05-25
---

# SaaS Gate

Every agent operates as if they were a standalone SaaS product. There is no draft stage. Every output must clear:

1. **Mobile-first verified** — tested at 320 / 375 / 414 / 768 / 1024 / 1440. Touch targets ≥ 44×44 px. No horizontal scroll. Type clamps.
2. **Images optimized before publish** — AVIF + WebP + fallback. Variant coverage. Source dims ≥ render dims (no upscale blur). Above-fold `fetchpriority="high"`.
3. **Sales-presentation grade** — reads like a product page. First 200 words close a sale on the recommendation.
4. **Accessibility verified** — WCAG 2.2 AA. `prefers-reduced-motion` honored. Focus-visible everywhere.
5. **Performance verified** — Lighthouse perf ≥ 95 mobile throttle.
6. **Self-contained reading** — new reader can pick up cold.
7. **Conversion-ready CTAs** — exact commit message + verification command + ship-it call.

**Why:** founder said "these agent need to work like their own saas product. meaning everything the design should be optimized and presented to sale. mobile and images optimized to display before presented" — 2026-05-25.

**How to apply:** if any gate fails, do NOT surface the deliverable. Re-work it. Sub-SaaS deliverables get rejected by the orchestrator.

**Skill source:** `SKILL.md` section "SaaS Product Delivery Standard"
