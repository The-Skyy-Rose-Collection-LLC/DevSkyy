---
name: skyyrose-core-dispatch
description: Handoff router + memory/self-heal wiring for skyyrose-core. Use when an engineering task needs verification or design work, and to read/write the suite's shared memory substrates.
---

# skyyrose-core — Dispatch / Handoff + Memory Wiring

`skyyrose-core` owns backend (FastAPI/Python), data, infra, planning, behavior discipline, and memory/self-healing. Hand off along the suite graph (`CROSS-PLUGIN.md`): **core → qa** for tests/review.

> **Boot first:** orient from the root canonical sources — `SOT.md` → `.wolf/anatomy.md` → `.wolf/cerebrum.md` → `CLAUDE.md` (full block in `CROSS-PLUGIN.md`) — before acting.

## When to hand off

| The task also needs… | Hand off to | Example |
|----------------------|-------------|---------|
| Tests, review, or verification | `skyyrose-qa` | New API → `skyyrose-qa:test-driven-development` + `:requesting-code-review`. |
| A UI/page/component/3D for the backend | `skyyrose-design` | New endpoint needs a dashboard → `skyyrose-design:frontend-patterns`. |
| Copy/marketing around a feature | `skyyrose-market` | Feature launch note → `skyyrose-market:content-engine`. |

## Memory wiring (suite-wide substrates)

The suite reads and writes three persistent memory stores. `skyyrose-core` owns the discipline for using them:

- **claude-mem** (`~/.claude-mem/claude-mem.db`, project-scoped) — cross-session observations. Search before re-exploring; record significant decisions/discoveries. Surfaced via the `mem-search` skill / `get_observations`.
- **`.wolf/cerebrum.md`** — project conventions, key learnings, do-not-repeat list, decision log. Read before generating code; append on any new convention/gotcha/correction.
- **`.wolf/buglog.json`** — known bugs + fixes. **Read before fixing any bug** (the fix may be known); **append after fixing** any error/failed test/failed build with `error_message`, `root_cause`, `fix`, `tags`.

## Self-healing

Any plugin detecting a regression calls **`skyyrose-qa:drive-to-green`** (bounded run → diagnose → fix → re-run loop). On stall, escalate via `skyyrose-qa`'s recovery (`stalled-agent-recovery`). Record the resolution in `.wolf/buglog.json` + claude-mem so the next session inherits it.

## Guardrails
- Behavior discipline (`token-aware-behavior` + `efficient-production`) is always-on (embedded on every agent).
- Production writes / deploys are STOP-AND-SHOW.
