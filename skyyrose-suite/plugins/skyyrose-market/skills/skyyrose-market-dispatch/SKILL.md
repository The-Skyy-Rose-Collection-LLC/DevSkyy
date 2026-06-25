---
name: skyyrose-market-dispatch
description: Handoff router for skyyrose-market. Use when a marketing task needs work owned by another SkyyRose plugin (imagery, pages, backend, or verification) — tells you when and where to hand off.
---

# skyyrose-market — Dispatch / Handoff

`skyyrose-market` owns copy, brand voice, SEO, email, social, paid media, influencer, and launch planning. When a task crosses out of that scope, hand off along the suite graph (see `CROSS-PLUGIN.md`): **market → design → qa → core → qa**.

> **Boot first:** orient from the root canonical sources — `SOT.md` (product facts → catalog CSV + dossier; brand canon → `knowledge-base/seed/from-interview.md`) → `.wolf/anatomy.md` → `.wolf/cerebrum.md` → `CLAUDE.md` (full block in `CROSS-PLUGIN.md`) — before acting.

## When to hand off

| The task also needs… | Hand off to | Example |
|----------------------|-------------|---------|
| A product image, mockup, landing page, theme, or 3D | `skyyrose-design` | A drop email needs hero imagery → `skyyrose-design:design-master` (gated by STOP-AND-SHOW). |
| Backend, data, an API, or a feature plan | `skyyrose-core` | A campaign needs a new signup endpoint → `skyyrose-core:fastapi-patterns`. |
| Verification, audit, or review of a built artifact | `skyyrose-qa` | A landing page is built → `skyyrose-qa` verifies before launch. |
| Multi-step orchestration (full drop) | `skyyrose` orchestrator → dev-team workflow | "Launch the Love Hurts capsule." |

## Guardrails
- Product facts (SKUs, prices, collections) resolve through the catalog CSV + per-SKU dossiers only.
- Brand canon (collections, palettes, The Five) is locked.
- Any paid render or production write is gated by STOP-AND-SHOW (owned by `skyyrose-design`).
