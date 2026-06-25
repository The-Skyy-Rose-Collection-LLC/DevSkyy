---
name: stalled-agent-recovery
description: Recover gracefully when an Agent tool dispatch stalls, times out, or returns mid-edit. Detect via duration > 300s + partial-edit signature, locate agent's last write target, complete inline. Use when an Agent invocation returns a non-completion message, when the agent's last sentence is mid-thought, or when you suspect token budget hit.
---

# stalled-agent-recovery

## Trigger

Auto-detect when an `Agent` tool returns and ANY of these is true:
- Duration > 300s
- Token usage > 50K
- Last message in the agent's reply ends mid-sentence ("Now add..." / "Next step..." / "Continuing with...")
- Agent reply contains `agentId: <id>` continuation instruction
- TaskOutput on the agentId returns "No task found" (agent died)

User may also say: "the agent stalled", "resume the agent's work", "did the agent finish?", "complete what the agent started".

## The Rule

**Stalled agent != reset. Diff git state to find the partial work, then complete inline.** Do NOT spawn a new agent for the same task — it will likely stall the same way.

**Why:** Agent tool stalls almost always happen because the agent's context filled before it finished. Spawning a fresh agent with the same brief reproduces the failure. The completed-fraction of work IS valuable — preserve it.

**How to apply:** Check git state → identify last edit → complete remaining work inline → run tests → report delta vs agent's original scope.

## Workflow

### Step 1 — Detect

After Agent tool returns, scan reply for:
- Final message ends with `:` or `...` or `Now <verb>` (incomplete sentence)
- Total duration > 5 min
- `agentId: <hex>` follow-up hint
- Token usage > 50K reported

If any match → treat as stall.

### Step 2 — Try resume first (cheap)

```
TaskOutput(task_id=<agentId>, block=false, timeout=5000)
```

If returns output → agent finished, was just verbose. Read result, done.

If returns `"No task found with ID: <agentId>"` → agent gone, recovery mode.

### Step 3 — Diff git state

```bash
git status --short
git diff --stat
git diff <suspected-file>
```

Identify which files the agent touched. Read the diff — what's complete, what's scaffolded but not wired.

Common stall signatures:
- Imports + constants + type annotations added → wiring incomplete
- Function signature changed → callers not yet updated
- One stage of a multi-stage fix done → other stages pending

### Step 4 — Map remaining work

From the agent's original brief (visible in your conversation history), enumerate what was DONE vs PENDING. Update task list to reflect actual state.

### Step 5 — Complete inline with token discipline

Do NOT re-read files the agent already read (visible in your conversation as their tool calls). Pick up at the exact wiring point. Use parallel tool calls to batch the remaining edits.

Token budget for recovery: typically 10-20% of what the agent burned. If you're approaching 50% of the agent's budget, stop and ask user — recovery has its own scope creep risk.

### Step 6 — Verify

Run the project's test suite (`pytest`, `npm test`, etc.) against the scope. Report:
- Agent completed: <X>
- You completed: <Y>
- Test delta: before X/Y → after X/Y

## Anti-Patterns

- Don't re-dispatch the SAME agent prompt — same stall, double cost
- Don't roll back the agent's partial work to "start clean" — you lose hours of agent time
- Don't try to use `SendMessage` if the tool is unavailable (deferred + not in your loaded set) — TaskOutput is the fallback
- Don't claim the agent's work as yours in the commit msg — co-attribution or note in body

## Example invocation

Senior Developer agent dispatched for H-01/H-02 budget gate. Returns at 706s/64K tokens, final sentence: "Good — formatter broke the comment into a multi-line expression. Now add `budget` param to `render()` and wire the two budget gates:"

You: `git diff flux_pipeline.py` shows +11 lines (param + import + constants + docstring) but no wiring at call sites. Find the 2 FAL call sites with `grep -n "fal_client\." flux_pipeline.py`. Wire `ensure_within_budget` + `spend` at each. 6 tool calls total. 479 tests pass / 0 fail.

## Related

- `budgeted-subagent-dispatch` (prevention)
- `audit-pass2-verifier` (for verifying recovered work)
- `verification-before-completion`
