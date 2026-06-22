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

## Routing

The `skyyrose-orchestrator` agent owns the authoritative task→plugin classification table and the handoff graph (see `CROSS-PLUGIN.md`) — this command does not restate it (single source of truth). Pass `$ARGUMENTS` to the orchestrator and follow its decision. If the task is ambiguous, state your interpretation and chosen route in one line, then proceed.
