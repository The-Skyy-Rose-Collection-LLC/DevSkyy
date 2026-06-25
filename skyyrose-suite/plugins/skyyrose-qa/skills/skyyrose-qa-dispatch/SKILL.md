---
name: skyyrose-qa-dispatch
description: Handoff router for skyyrose-qa. Use when verification surfaces work owned by another SkyyRose plugin (fixes, backend changes), and to close the loop by logging lessons to memory.
---

# skyyrose-qa — Dispatch / Handoff

`skyyrose-qa` owns TDD, drive-to-green, verification loops, audits, evals, and code review. It is the gate every built artifact passes before shipping. Hand off along the suite graph (`CROSS-PLUGIN.md`): **qa → core** (log lessons / backend fixes), **qa → design** (UI/theme fixes).

> **Boot first:** orient from the root canonical sources — `SOT.md` → `.wolf/anatomy.md` → `.wolf/cerebrum.md` → `.wolf/buglog.json` (read before fixing) → `CLAUDE.md` (full block in `CROSS-PLUGIN.md`) — before acting.

## When to hand off

| Verification found… | Hand off to | Example |
|---------------------|-------------|---------|
| A backend/data/API defect | `skyyrose-core` | Failing API test → `skyyrose-core` fixes, then re-verify here. |
| A UI/theme/render defect | `skyyrose-design` | Broken page or off-canon render → `skyyrose-design` fixes, then re-verify. |
| A persistent regression | self → `drive-to-green` | Run the bounded auto-fix loop until green. |
| A lesson worth keeping | `skyyrose-core` memory | Log root cause + fix to `.wolf/buglog.json` + claude-mem (see `skyyrose-core-dispatch`). |

## Closing the loop
1. Verify the artifact (tests, lint, type-check, build, or audit per the task).
2. On failure → route the fix to the owning plugin → **re-verify** (never accept a fix on a subagent's word; re-run the precise check).
3. On success → record the outcome; if a bug was fixed, append to `.wolf/buglog.json` + claude-mem via `skyyrose-core`.

## Guardrails
- Independently re-verify every "done" before relaying status or committing.
- Never weaken a test to make it pass — fix the code.
