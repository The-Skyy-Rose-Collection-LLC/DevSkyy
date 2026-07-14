---
name: memory-system
description: Use at the start and end of every task — read the canonical memory before acting and write the outcome after. Unifies OpenWolf files and claude-mem so knowledge persists across sessions instead of being re-derived.
origin: SkyyRose
---

# Memory System

Knowledge that is not written down does not survive the session. This project runs
**three** memory layers, and the recurring failure mode is not missing memory — it is
memory that was never written, or written and never read: a session re-derives a fact
already known, repeats a mistake already logged, or fixes a bug already fixed once.

> **Boot first:** `SOT.md` → `.wolf/anatomy.md` → `.wolf/cerebrum.md` →
> `.wolf/buglog.json` → `.wolf/claude-mem-digest.md`. Same order every session — do not
> act on a task before this pass completes.

## When to Use

- **Start of every task:** read canon before acting, before generating code, before
  claiming a fact about the codebase.
- **End of every task:** write the outcome before the session ends. If you learned
  something and didn't write it, the next session pays for the discovery again.
- Any bug fix, user correction, new convention, or architectural decision — mid-task,
  not batched to the end.

## Method

**Three layers, one discipline:**

1. **OpenWolf files** (`.wolf/`) — fast, structured, per-repo.
   - `.wolf/anatomy.md` — 2-3 line description + token estimate per file. Read BEFORE
     reading any file; if the description answers the question, don't open the file.
   - `.wolf/cerebrum.md` — Do-Not-Repeat list, Key Learnings, User Preferences, Decision
     Log. Read BEFORE generating code.
   - `.wolf/memory.md` — append one row per significant action:
     `| HH:MM | description | file(s) | outcome | ~tokens |`.
   - `.wolf/buglog.json` — read BEFORE fixing any bug (the fix may already be known);
     append AFTER with `error_message`, `root_cause`, `fix`, `tags`.
2. **claude-mem** — cross-session observation DB, searched via the `mem-search` skill /
   `get_observations([IDs])`, synced into `.wolf/claude-mem-digest.md` at SessionStart.
   The digest holds only the newest 25 observations — for anything older, search the DB
   directly with `mem-search` / `get_observations([IDs])` before re-deriving an answer it
   may already hold. Cross-reference direction: when an OpenWolf entry relates to a
   claude-mem observation, append `[cmem #NNN]` to the `.wolf/memory.md` row or the
   `cerebrum.md` entry.
3. **The canonical sources** registered in root `SOT.md` — catalog CSV, `sot-images.json`,
   brand canon, and this project's own OpenWolf memory. Never fork a second copy of a SOT.

**READ before acting:** SOT → anatomy → cerebrum → buglog → claude-mem-digest.
**WRITE after acting:** append the `.wolf/memory.md` row; update `cerebrum.md` on any
correction, convention, or preference; log `.wolf/buglog.json` on any fix; cross-ref
`[cmem #NNN]` where a claude-mem observation covers the same event.

Token discipline: prefer an anatomy description over a full file read; never re-read a
file already read this session.

## Loop until memory is current

Bounded — a memory pass is not a research spiral:

```
1. Act (make the change, fix the bug, answer the question).
2. Write the lesson — the correct file(s) from Method, not a mental note.
3. Confirm the write landed (see Verify, below).
4. Next action, or done.
```

## Verify from an authoritative source

A recalled memory is **not authoritative on its own** — cerebrum entries and claude-mem
observations rot as the codebase moves under them.

- If a memory names a file, flag, function, or path, **re-verify it against the live
  source** (Read/Grep) before relying on it or repeating it as fact. A stale cerebrum
  entry pointing at a moved file is worse than no entry.
- Cite obs IDs (`[cmem #NNN]`) or the specific `cerebrum.md` heading you relied on — not
  "memory says," a traceable pointer.
- **After writing**, re-read the file (`.wolf/memory.md`, `cerebrum.md`, `buglog.json`)
  to confirm the entry actually persisted — a write that silently failed is the same as
  never writing.

## Adversarial pass

[[adversarial-verification]] — assume the recalled memory is stale until ground truth
confirms it. Before trusting a cerebrum "Do-Not-Repeat" or a claude-mem observation as
settled, check whether the file/behavior it describes still matches the current source;
don't propagate a stale lesson forward into a new `cerebrum.md` entry.

## Guardrails · Handoff · Log

- **The bar to log is LOW.** A redundant cerebrum entry costs nothing; a missing one
  means the next session re-derives the discovery from scratch. When in doubt, write it.
- Cross-ref [[self-learning]] and [[continuous-learning]] — every pod's dispatch skill
  (see `CROSS-PLUGIN.md`) routes its lessons back through this memory system, not a
  plugin-local file.
- A task that ends without a `.wolf/memory.md` row is not done, even if the code is
  correct — the deliverable includes the memory write.
