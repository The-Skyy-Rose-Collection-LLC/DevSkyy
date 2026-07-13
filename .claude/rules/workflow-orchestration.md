# Workflow Orchestration

> Operating doctrine for any non-trivial work in DevSkyy. Pairs with [development-workflow.md](./development-workflow.md) (the *what* — research, TDD, review) and [agents.md](./agents.md) (the *who* — which agents to invoke).

This file governs *how* a task moves from request → done: when to plan, when to delegate, how to verify, how to learn from corrections.

---

## 1. Plan Node Default

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).
- If something goes sideways, STOP and re-plan immediately — don't keep pushing.
- Use plan mode for verification steps, not just building.
- Write detailed specs upfront to reduce ambiguity.

> Single-step tasks skip the plan. Three+ steps without a written plan = drift risk.

## 2. Subagent Strategy

- Use subagents liberally to keep the main context window clean.
- Offload research, exploration, and parallel analysis to subagents.
- For complex problems, throw more compute at it via subagents.
- One task per subagent for focused execution.

> Subagent selection lives in [agents.md](./agents.md). Default to parallel dispatch when work is independent — see [common/agents.md](../../../.claude/rules/agents.md).

## 3. Self-Improvement Loop

- After ANY correction from the user: update `tasks/lessons.md` with the pattern.
- Write rules for yourself that prevent the same mistake.
- Ruthlessly iterate on these lessons until mistake rate drops.
- Review lessons at session start for the relevant project.

> This rule operationalizes the **Self-Correction** clause in `CLAUDE.md`: fix → name lesson → commit fix + lesson together. Cerebrum (`.wolf/cerebrum.md`) and `tasks/lessons.md` are both update targets — cerebrum for project-wide gotchas, `tasks/lessons.md` for behavioral patterns.

## 4. Verification Before Done

- Never mark a task complete without proving it works.
- Diff behavior between main and your changes when relevant.
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness.

> Pairs with the **Output Quality — Production Standard** clause in `CLAUDE.md`. No `TODO`, `FIXME`, `pass`, or `raise NotImplementedError` in delivered code.

## 5. Demand Elegance (Balanced)

- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution."
- Skip this for simple, obvious fixes — don't over-engineer.
- Challenge your own work before presenting it.

> Balance against the existing **Critical Rules**: don't add abstractions beyond what the task requires. Elegance ≠ premature abstraction. Three similar lines beats a generic helper used once.

## 6. Autonomous Bug Fixing

- When given a bug report: just fix it. Don't ask for hand-holding.
- Point at logs, errors, failing tests — then resolve them.
- Zero context switching required from the user.
- Go fix failing CI tests without being told how.

> Bound by the **STOP AND SHOW** protocol in `CLAUDE.md`: bug fixing is autonomous, but money / production / irreversible-data actions still require explicit confirmation.

---

## Task Management

1. **Plan First** — write plan to `tasks/todo.md` with checkable items.
2. **Verify Plan** — check in before starting implementation.
3. **Track Progress** — mark items complete as you go.
4. **Explain Changes** — high-level summary at each step.
5. **Document Results** — add review section to `tasks/todo.md`.
6. **Capture Lessons** — update `tasks/lessons.md` after corrections.

> `tasks/todo.md` is the active worklist. `tasks/lessons.md` is the behavioral memory. Both are checked into the repo so they survive session boundaries.

## Core Principles

- **Simplicity First** — make every change as simple as possible. Impact minimal code.
- **No Laziness** — find root causes. No temporary fixes. Senior developer standards.
- **Minimal Impact** — changes should only touch what's necessary. Avoid introducing bugs.

---

## Cross-References

- Communication tone, autonomous bug-fix scope, STOP-AND-SHOW gate → `/Users/theceo/DevSkyy/CLAUDE.md`
- Research → planning → TDD → review pipeline → [development-workflow.md](./development-workflow.md)
- Agent selection (planner, code-reviewer, tdd-guide, etc.) → [agents.md](./agents.md)
- Pre/post tool hook policy → [hooks.md](./hooks.md)
- OpenWolf cerebrum / anatomy / memory loop → [openwolf.md](./openwolf.md)
