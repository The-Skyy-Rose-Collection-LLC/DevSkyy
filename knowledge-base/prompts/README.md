# DevSkyy Prompt Engineering Dataset

Canonical registry, version history, and eval cases for every prompt that ships in DevSkyy. Triggered automatically by `.claude/hooks/prompt-eng-nudge.sh` whenever Claude detects prompt-engineering work in progress.

## Why this exists

Prompts in DevSkyy live in three places today:

1. **`.txt` files** — e.g., `agents/claude_sdk/prompts/researcher.txt`
2. **Inline Python strings** — `system_prompt="..."` in `agents/*.py`
3. **AgentDefinition prompts** — `skyyrose/multi_agent/agents.py` (`AGENT_DEFINITIONS`)

Without a registry, prompts drift silently. A prompt edited to fix one regression breaks another agent's behavior. Versions are lost. Performance regressions are invisible. Brand-voice violations creep in.

This directory is the **single source of truth** for prompt metadata — version, provenance, performance scores, and eval cases. The actual prompt text stays in the source file (no duplication); the registry tracks **where** each lives and **what** it does.

## Directory layout

```
knowledge-base/prompts/
├── README.md          ← this file
├── INDEX.yaml         ← master registry (every prompt + metadata)
├── templates/         ← reusable prompt fragments (intros, output schemas,
│                       few-shot demonstrations) for composition
├── library/           ← versioned prompt artifacts when a prompt needs
│                       version history but doesn't have a code home
└── eval/              ← per-prompt eval datasets (JSONL of input/expected)
    └── <id>.jsonl
```

## INDEX.yaml schema

```yaml
prompts:
  - id: brand-writer                # kebab-case, unique
    name: "SkyyRose Brand Writer"
    type: agent-system-prompt       # agent-system-prompt | mcp-tool | pipeline | meta
    domain: brand-content
    location:                       # WHERE the prompt lives (source of truth)
      file: skyyrose/multi_agent/agents.py
      symbol: AGENT_DEFINITIONS["brand-writer"].prompt
    consumed_by:                    # WHO calls this prompt
      - skyyrose/multi_agent/orchestrator.py:run_single_agent
    model:                          # default model when invoked
      default: claude-sonnet-4-6
      fallbacks: [claude-haiku-4-5]
    version: "1.0.0"                # bump on any text change
    last_updated: 2026-05-13
    performance:
      evaluated: null               # YYYY-MM-DD or null
      pass_rate: null
      cost_per_call_usd_p50: null
    canon_dependencies:             # what the prompt assumes about the world
      - knowledge-base/seed/from-interview.md  # brand canon
      - wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv  # SKU truth
    tags: [brand, marketing, copy]
    eval: eval/brand-writer.jsonl   # path or null
    notes: |
      Multi-line free text. Why this prompt exists, what NOT to do, etc.
```

## Workflow when editing a prompt

When the prompt-engineering hook fires (it sees you opening a prompt file or editing inline `system_prompt=` strings), follow this loop:

1. **Locate the entry** in `INDEX.yaml` matching the file/symbol you're about to edit. If none exists, **create one** (the hook will remind you).
2. **Bump the version** (`X.Y.0` for material rewrites, `X.Y.Z` for minor tweaks).
3. **Update `last_updated`** to today's date.
4. **Make the edit**.
5. **If eval/<id>.jsonl exists**, run it (manually or via the eval harness). Update `performance` block.
6. **If a new canon dependency**, add to `canon_dependencies` array.
7. Commit the prompt edit AND the INDEX.yaml update **in the same commit** with message `prompt(<id>): <change>`.

## Workflow when ADDING a new prompt

1. Write the prompt in its natural home (source file or `library/<id>.txt`).
2. Add an entry to `INDEX.yaml` with version `0.1.0` and `evaluated: null`.
3. Write an initial eval at `eval/<id>.jsonl` (start with 3–5 representative inputs).
4. Tag with applicable `tags` so future searches find it.

## Hook integration

`.claude/hooks/prompt-eng-nudge.sh` detects prompt-engineering work via:

- UserPromptSubmit prompts containing: `prompt`, `system_prompt`, `agent definition`, `few-shot`, `instruction`, `system message`, `prompt template`.
- PreToolUse Edit/MultiEdit on files matching `**/prompts/**`, `*_prompt*.py`, or content containing `system_prompt=` / `SYSTEM_PROMPT =`.

When triggered, it injects an `additionalContext` directive pointing here.

## Eval format (eval/<id>.jsonl)

JSONL, one test case per line:

```jsonl
{"id": "case-001", "input": "Write a launch caption for br-001", "expected": {"contains_tagline": true, "voice_match": "luxury-streetwear", "max_emojis": 2}, "tags": ["caption", "instagram"]}
{"id": "case-002", "input": "Describe lh-002 for product page", "expected": {"contains_collection": "love-hurts", "voice_match": "luxury-streetwear", "length_words": [50, 120]}, "tags": ["product-description"]}
```

`expected` is intentionally schemaless — pick the assertions that matter for THIS prompt. The eval harness (TBD) reads JSONL, calls the prompt with each input, and scores assertions.

## Anti-patterns (do NOT do)

- **Don't duplicate prompt text** in INDEX.yaml. Always reference the source file.
- **Don't edit a prompt without bumping `version`**. Silent edits create un-debuggable behavior changes.
- **Don't ignore eval failures**. If the eval breaks after your edit, revert OR fix the eval to reflect the new intended behavior — but document why in the entry's `notes`.
- **Don't create one-off prompts that aren't registered**. If it's worth running, it's worth a registry entry.
