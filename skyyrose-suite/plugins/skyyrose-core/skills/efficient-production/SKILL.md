---
name: efficient-production
description: >
  Always-on tool discipline and production output enforcement. Fires every session.
  Enforces: no file re-reads, batched parallel tool calls, anatomy.md check first,
  one targeted search, zero TODOs/mocks in delivered code, verify-before-claim
  anti-hallucination, HTML for structured agent docs. Complements token-aware-behavior
  (context window) and caveman (tone) — this one governs tool efficiency and output quality.
---

# Efficient Production Mode

Always active. No invocation needed. Runs silently alongside all other work.

## Tool Discipline (Every Tool Call)

**Before any tool call, ask: do I already have this?**

1. **No re-reads.** File read once this session = available for the rest of the session. Re-reading wastes tokens. Do not re-read.
2. **Batch parallel reads.** Need 3 files → dispatch all 3 in one parallel block. Not 3 sequential calls.
3. **Anatomy first.** If `.wolf/anatomy.md` exists in project, check its descriptions before reading full files. If the description answers the question, skip the full read.
4. **Targeted search.** Write the grep/search query that answers in one call. Three vague searches ≠ one good search. If searching, commit to it.
5. **Parallel agents.** Independent sub-tasks → single message with multiple Agent tool calls. Never sequential when work is independent.
6. **No confirmation fetches.** Don't fetch a URL to confirm something verifiable from context or logic.

## Production Gates (Before Marking Done)

Every deliverable passes all of these — no exceptions:

- Zero `TODO`, `FIXME`, `pass`, `raise NotImplementedError` in delivered code
- Zero mock or placeholder data in non-test code (test-boundary mocks only)
- Every factual claim about the codebase traces to a tool call from THIS session
- Tests green: `pytest tests/ -v` (Python) / `npm run type-check && npm run lint && npm run build` (frontend)
- Scope clean: `git diff --name-only` shows only paths for this task

## Verify Before Claim

Pattern: **Read source → Search codebase → Then state.**
Never: State plausibly → hope it matches reality.

If you haven't read it this session, you don't know it. Say "I don't know" and find out.

Do not invent function names, file paths, endpoint shapes, or module exports. Read first.

## HTML for Structured Docs

When writing agent briefings, system prompts, specs, or reference docs with 3+ navigable sections:
- Write `.html`, not `.md`
- Use `<section id="...">` for unambiguous anchors
- Use `<code>` for every file path, function name, and symbol
- Use `<table>` for role→file mappings and option comparisons
- Reserve `.md` for prose memory files (CLAUDE.md, cerebrum.md, memory.md, todo.md)

## Anti-Patterns

- Re-reading a file already in context
- Running 3 searches when 1 targeted query would work
- Summarizing what you're about to do instead of doing it
- Shipping code with `TODO` or `# placeholder` comments
- Stating a file path without having read it this session
- Creating a new client/utility when an existing one can be extended
