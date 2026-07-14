---
name: self-learning
description: Use after any correction, mistake, discovery, or fix — capture the lesson durably into cerebrum + buglog so the same discovery is never repeated. Closes the improvement loop that makes the team better across sessions.
origin: SkyyRose
---

# Self-Learning

A lesson that lives only in the transcript dies with the session. The next agent —
or the next you, three hours from now — re-derives the same discovery, re-trips the
same gotcha, re-asks the founder the same question. This is the OpenWolf **Cerebrum
Learning protocol**, and it is MANDATORY every session, not a nice-to-have: every
correction, non-obvious convention, gotcha, and technical decision gets written down
where the next session will actually see it. The bar to log is **LOW** — a slightly
redundant entry costs nothing; a missing one costs the whole rediscovery.

> **Boot first:** read `.wolf/cerebrum.md` and `.wolf/buglog.json` before re-deriving
> anything — the fix or preference may already be recorded.

## When to Use

- After any user correction ("no, do it this way instead") or rejected suggestion.
- After any mistake, bug, failed test, failed build, or user-reported problem.
- After any discovery: a non-obvious project convention, a framework pattern, an API
  that surprised you, a dependency quirk, how modules connect.
- After a fix — the fix is only half the job; the lesson is the other half.
- Any file edited more than twice in one session — that pattern itself is a signal
  something was misunderstood and belongs in Do-Not-Repeat.

## Method

1. **Classify the lesson** — which store, which section:
   - **`.wolf/cerebrum.md` → User Preferences** — style, naming, workflow, a rejected
     suggestion.
   - **`.wolf/cerebrum.md` → Key Learnings** — a convention, framework pattern, API
     surprise, dependency quirk, how modules connect.
   - **`.wolf/cerebrum.md` → Do-Not-Repeat (WITH DATE)** — a mistake made or a gotcha
     that would trip up a fresh session.
   - **`.wolf/cerebrum.md` → Decision Log** — a significant technical choice + the
     "why", especially when the founder explains a trade-off.
   - **`.wolf/buglog.json`** — any error / failed test / failed build / user-reported
     problem, with `error_message`, `file`, `root_cause`, `fix`, `tags`.
   - **`tasks/lessons.md`** — behavioral corrections (how Claude should act), separate
     from engineering facts.
2. **Write it.** For a new buglog entry, allocate the ID via
   `python scripts/wolf_bug_id.py` — never guess or reuse an ID from memory (manual
   guessing has already caused cross-session ID collisions). If the same defect
   recurs, bump `occurrences` + `last_seen` on the existing entry instead of
   duplicating it.
3. **Sync recurring bugs.** Any buglog entry reaching `occurrences >= 2` must run
   `python scripts/wolf_recurring_sync.py` — it regenerates the 1-line recurring-issues
   digest between the `wolf:recurring` markers in `CLAUDE.md` so every future session
   loads it automatically without re-reading the full buglog.
4. **Commit fix + lesson together.** Per `CLAUDE.md`'s After-a-Mistake protocol: fix
   it → name the lesson in one sentence (what was wrong + why) → write the rule that
   prevents recurrence → commit the fix and the lesson in the same change.

## Loop until the lesson is durable

Bounded — same discipline as [[drive-to-green]], never more than a few turns per
lesson, stop if the same write fails twice (that's a tooling problem, not a retry
problem):

```
1. Extract the lesson from what just happened (correction, error, discovery).
2. Write it to the classified store (cerebrum section, buglog, or lessons.md).
3. Re-read the entry to confirm it landed — see Verify below.
4. Apply it: the next action in THIS session already reflects the new rule.
```

## Verify from an authoritative source

A learning is real only when it is **written and re-readable** — never assume the
write succeeded because the Edit/Write tool didn't error:

- **Re-read after writing.** Open `.wolf/cerebrum.md` or `.wolf/buglog.json` again and
  confirm the new entry is present, in the right section, with the right shape. An
  intention stated in a reply is not a lesson.
- **A Do-Not-Repeat rule must be concrete and checkable**, not a vague intention —
  "don't guess buglog IDs; run `scripts/wolf_bug_id.py`" is checkable, "be more
  careful with IDs" is not.
- **Use `scripts/wolf_bug_id.py` for every new bug ID** — never guess. This exact
  gotcha (manual ID guessing → collisions) is itself a Do-Not-Repeat entry; don't
  re-earn it.
- **Cite the entry** — quote the actual cerebrum line or buglog JSON you wrote, not a
  paraphrase of what you meant to write.

## Adversarial pass

- [[adversarial-verification]] — did the lesson actually get **written**, or only
  intended? Default to "not durable yet" until the re-read in the Verify step
  independently confirms the entry exists. A session that says "I've noted this" but
  never touched `.wolf/cerebrum.md` or `.wolf/buglog.json` produced nothing.

## Guardrails · Handoff · Log

- The bar is **LOW**. When in doubt, log it — a false-positive entry costs nothing; a
  missed lesson repeats the mistake, possibly at production cost.
- This skill is the substrate every pod's self-heal loop writes back to: per
  `CROSS-PLUGIN.md`'s handoff graph, `any plugin → skyyrose-qa:drive-to-green →
  skyyrose-core (memory log)` — `skyyrose-core` owns cerebrum/buglog discipline, and
  `self-learning` is where that write happens.
- Cross-ref [[memory-system]] (the read/write substrate this skill writes into),
  [[self-healing]] (the loop that triggers most of these writes), and
  [[continuous-learning]] (extracting reusable patterns beyond single-session fixes).
