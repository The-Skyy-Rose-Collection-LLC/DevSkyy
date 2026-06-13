---
description: SkyyRose Suite front door — classify a task and route it to the right plugin(s), or run the dev-team workflow for multi-step work.
argument-hint: <task description>
---

# /skyyrose

Entry point for the SkyyRose Suite. Hand it any task in `$ARGUMENTS` and it routes to the correct plugin(s).

## What to do

1. **Read the task** in `$ARGUMENTS`.
2. **Invoke the orchestrator agent** (`skyyrose-orchestrator`) to classify the task and choose a route. Do not guess the route yourself — the agent owns the classification logic and the handoff graph (see `CROSS-PLUGIN.md`).
3. **Follow the agent's routing decision:**
   - **Single-domain, single-skill** → invoke that plugin's skill directly (e.g. `skyyrose-market:brand-voice`, `skyyrose-design:design-master`).
   - **Multi-step / cross-domain** (e.g. "launch the drop", "build and ship the landing page") → run the embedded dev-team workflow at `workflows/skyyrose-dev-team.js` (plan → batched build → review-fix loop → WP health sweep → synthesis).
4. **Honor the guardrails** the orchestrator surfaces: STOP-AND-SHOW before any paid render (gpt-image-2) or production write; product facts resolve through the catalog CSV + per-SKU dossiers only.

## Routing quick reference

| Task shape | Route |
|------------|-------|
| copy / email / social / SEO / launch plan | `skyyrose-market` |
| product image / page / theme / 3D build | `skyyrose-design` |
| API / backend / migration / plan a feature | `skyyrose-core` |
| test / review / audit / verify / make-it-pass | `skyyrose-qa` |
| multi-step spanning the above | dev-team workflow |

If the task is ambiguous, state your interpretation and the chosen route in one line, then proceed.
