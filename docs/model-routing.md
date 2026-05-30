# Model Routing Policy

**Living document.** Source of truth for which model to use for which class of work across
DevSkyy/SkyyRose AI systems. Update as models change; code that selects models reads this policy
(via config), so updating here propagates.

**Last updated:** 2026-05-29

---

## Principle

Match model capability to task demand. Reasoning gets the strongest model; high-frequency quick
actions get a lighter, cheaper, faster model; general work gets the best all-rounder. Model choice
is **config-driven, never hardcoded** (see `feedback_ai_portability_architecture`).

## Policy

| Task class | Model | Model ID | Rationale |
|-----------|-------|----------|-----------|
| **Deep reasoning** — architecture, complex analysis, prioritization, multi-step synthesis, narration of structured results | Opus 4.8 | `claude-opus-4-8` | Maximum reasoning depth |
| **Quick actions** — classification, short phrasing, field-level summaries, high-frequency worker calls | Haiku 4.5 | `claude-haiku-4-5` | ~3× cheaper, fast, ~90% of Sonnet capability |
| **General / medium** — main development, coding, orchestration, default when unsure | Sonnet 4.6 | `claude-sonnet-4-6` | Best general/coding model |

## Latest model IDs (keep current)

- Opus 4.8: `claude-opus-4-8`
- Sonnet 4.6: `claude-sonnet-4-6`
- Haiku 4.5: `claude-haiku-4-5`

When building AI applications, default to the latest and most capable Claude models. Prefer
config references to these IDs over literals scattered in code.

## How to apply

1. In code, resolve the model from a config keyed by **task class** (e.g.
   `skyyrose/steward/config.py`), not by a hardcoded string.
2. When a new model ships, update the IDs and the table here, then bump the config — code follows.
3. Known debt: `sdk/python/adk/pydantic_adk.py` still defaults to stale strings
   (`gpt-4o-mini`, `claude-sonnet-4-0`). Fix to config-driven latest when that file is next touched.

## First consumer

The Catalog & Dossier Steward
(`docs/superpowers/specs/2026-05-29-catalog-dossier-steward-design.md`): deep reasoning →
Opus 4.8, quick actions → Haiku 4.5.
