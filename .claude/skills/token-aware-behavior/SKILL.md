---
name: token-aware-behavior
description: >
  Always-on context window management for Claude chat sessions. Activates automatically
  on every conversation — no trigger phrase needed. Instructs Claude to proactively
  monitor conversation length, compress history at 75% depth, emit structured handoff
  documents at 88%, and hard-stop at 95%. Use this skill whenever a conversation is
  running long, involves multi-step engineering tasks, contains large code blocks or
  tool results, or the user mentions "context", "losing track", "starting fresh", or
  "pick up where we left off." Prevents the silent dropoff pattern where Claude stops
  finishing work mid-task.
---

# Token-Aware Behavior

Embed real-time context awareness into every response. This skill runs silently
alongside all other work — it never interrupts flow unless action is required.

---

## Budget States (Mirror the token_budget.py thresholds)

Claude operates internal context depth estimates based on conversation
trajectory. Classify each response into one of 5 states:

| State      | Depth Proxy              | Behavior                              |
|------------|--------------------------|---------------------------------------|
| `nominal`  | Short/medium conv        | Full responses, no change             |
| `warn`     | Long conv, heavy tools   | Tighten output, skip redundant prose  |
| `compress` | Very long, many files    | Summarize previous phases in-place    |
| `handoff`  | Near saturation          | Generate handoff doc, signal clearly  |
| `critical` | Cannot safely continue   | Emit summary only, stop new content   |

---

## Signals That Elevate Budget State

**Elevates to WARN:**
- 10+ conversation turns with substantive content
- 3+ large code blocks / tool result dumps in context
- Multiple file reads in the same session
- Repeated back-and-forth on the same component

**Elevates to COMPRESS:**
- 20+ turns
- Multiple multi-file implementations
- Several tool execution cycles with large outputs
- Prior work from "phases" no longer directly referenced

**Elevates to HANDOFF:**
- Session has covered 3+ distinct tasks
- Context clearly dominated by historical turns
- New request requires as much context as what's already accumulated

---

## Behavior Per State

### NOMINAL / WARN
- No change to output style
- Internally: keep responses tight, avoid restating prior work verbatim
- Prefer references ("as built above", "extending the compressor from earlier")
  over re-explaining completed components

### COMPRESS
Proactively emit a compact phase summary before continuing:

```
[PHASE SUMMARY — compressing context]
Completed: <list of deliverables with file names>
Key decisions: <1-3 bullet points>
Open: <what's in progress>
Continuing with: <next action>
```
Then proceed immediately. Do NOT wait for user confirmation.

### HANDOFF
When handoff threshold is reached mid-task:

1. **Finish the current atomic unit of work** (current function, current file, current test)
2. **Emit structured handoff:**

```
[SESSION HANDOFF]
Session: <id or description>
Completed this session:
  - <file 1> — <one-line description>
  - <file 2> — ...
In progress: <task name> — <exact stopping point>
Next action: <specific, unambiguous instruction>
Files modified: <list>
Key decisions: <critical choices made>

RESUME PROMPT (paste into new session):
---
<self-contained prompt that seeds new session with full context>
---
```

3. **Tell the user explicitly:**
   > "Context is near its limit. I've generated a handoff above. Start a new
   > conversation, paste the RESUME PROMPT, and I'll pick up exactly where
   > we stopped — no context lost."

### CRITICAL
Emit only:
```
[CRITICAL — context limit reached]
<2-3 sentence summary of session state>
Handoff: <resume prompt>
```
Then stop. Do not attempt to continue work.

---

## Anti-Patterns to Avoid

- ❌ Silently stopping mid-task without handoff
- ❌ Asking "can I proceed?" instead of just proceeding
- ❌ Re-explaining completed work at length (wastes tokens)
- ❌ Pasting full file contents back when referencing prior work
- ❌ Large prose preambles before code
- ❌ Restating the user's request in full before answering

---

## Token-Efficient Response Patterns

**Instead of:**
> "Great question! In order to implement X, we'll need to consider Y and Z.
> Let me walk you through the approach step by step..."

**Write:**
> "Implementing X — here's the approach:"

**Instead of re-showing an entire file to change 3 lines:**
Use `str_replace` with the exact diff. Reference "the compressor from earlier"
not paste it again.

**Instead of explaining what you're about to do:**
Just do it. The code speaks.

---

## Handoff Document Format (machine-readable)

When generating a handoff for Claude Code or agent pipelines, emit JSON:

```json
{
  "session": "<session_id>",
  "completed": ["file1.py — purpose", "file2.py — purpose"],
  "in_progress": {
    "task": "<task name>",
    "status": "<exact stopping point>",
    "next_action": "<specific next step>"
  },
  "key_decisions": ["decision 1", "decision 2"],
  "files_modified": ["path/to/file1.py"],
  "resume_prompt": "<full self-contained resume text>"
}
```

---

## Integration with token-aware Module

The `token-aware/` Python module (client.py, token_budget.py, compressor.py,
handoff.py) is the programmatic implementation of these same rules.

Claude Code uses that module for automated pipelines.
This skill applies the same logic to Claude chat sessions.

They share thresholds: 60% warn / 75% compress / 88% handoff / 95% critical.

---

## Quick Reference

Before every response, internally ask:
1. Is this conversation approaching saturation? → classify state
2. Am I about to paste something I already showed? → reference instead
3. Is this task multi-session in scope? → flag early, plan handoffs
4. If I stopped right now, could the user resume? → if no, generate handoff
