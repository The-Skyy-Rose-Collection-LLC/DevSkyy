# Skyyrose V2 — Knowledge Base

This is the **forward-looking** pattern/lesson/decision catalog for the V2 build (Phase 0 onward). It is one of **five integrated knowledge layers** on this project. The others are pre-existing memory systems that this KB cross-references rather than duplicates.

---

## The integration map (read this first)

When a task needs prior context, this is the priority order to consult:

| # | Layer | What lives there | When to read it |
|---|-------|------------------|-----------------|
| 1 | **knowledge-base/** (this dir) | V2-build patterns, lessons, decisions, references — the catalog of what we've learned during this build | When the task is new and might match a Phase 0+ pattern |
| 2 | **.serena/memories/** (29 files) | Project facts, coding standards, architecture decisions, deployment status, MCP setup | When the task touches catalog/CSV/SKU integrity, coding standards, or architectural conventions |
| 3 | **.planning/** (105+ files, GSD artifacts) | PROJECT.md (charter), RETROSPECTIVE.md (cross-milestone lessons), codebase/CONVENTIONS.md, codebase/CONCERNS.md (tech debt), research/PITFALLS.md, phase-specific PATTERNS.md (e.g., 14-catalog-foundation/14-PATTERNS.md is 579 lines of reusable patterns) | When the task connects to imagery pipeline, multi-agent orchestration, or domain modeling decisions made during prior milestones |
| 4 | **.wolf/** (OpenWolf — cerebrum.md, memory.md, buglog.json, anatomy.md) | Session continuity, file index, bug log with root-cause/fix/tags, cross-session learnings via cerebrum.md key-learnings + do-not-repeat sections | When debugging, resuming work, or checking "have I seen this error before?" |
| 5 | **claude-mem** (1300+ project-scoped observations in `~/.claude-mem/claude-mem.db`) | Auto-extracted observations from session transcripts, typed (`change`/`discovery`/`bugfix`/`refactor`/`decision`), vector-indexed in chroma | When the answer might be in a prior conversation. Query via `mem-search` MCP skill or look at `.wolf/claude-mem-digest.md` (last 25 auto-synced at SessionStart). |

There's also a **6th layer** added in Phase 0:

| 6 | **graphify-out/graph.json** (Phase 0 deliverable J) | Knowledge graph of the entire corpus with EXTRACTED/INFERRED/AMBIGUOUS edge tagging and community detection | When grep + vector search miss connections that exist topologically. Query via `/graphify query "<keywords>"` or `graphify-mcp:query` MCP tool. |

---

## How the 6-step per-edit workflow uses these layers

```bash
# Step 0 — Pre-edit knowledge consult (Compound Learning Loop, Layer 1)
grep -r "<task-keywords>" knowledge-base/ .serena/memories/ .planning/ .wolf/cerebrum.md tasks/lessons.md docs/SKYYROSE_*.md docs/PLAN_INDEX.md
mem-search "<task-keywords>"           # claude-mem vector index
graphify query "<task-keywords>"        # graphify topology

# Load matches into context. Begin work informed, not from scratch.
# Cite findings in §1.1 thinking-pass 5 and §1.2 critique-loop question 6.
```

If grep returns hits in multiple layers, prioritize via the table above. Layer 1 (this KB) is forward-looking and most current; layers 2-5 are backward-looking (existing project history); layer 6 is topological (cross-document connections).

---

## Schema

### Pattern entry (`knowledge-base/patterns/<domain>/<slug>.md`)

```markdown
---
title: <short descriptive name>
domain: <wordpress | woocommerce | threejs | css | accessibility | seo | conversion | brand | infra | meta>
problem: <what problem this solves, in one sentence>
sources_consulted:
  - url: <verified canonical source from trusted-set.md>
    accessed: <YYYY-MM-DD>
    relevance: <high | medium | low>
chosen_implementation: |
  <inline code or file path reference>
why_this_over_alternatives: |
  <prose, 50-150 words, naming what was rejected and why>
when_to_use:
  - <case 1>
  - <case 2>
when_NOT_to_use:
  - <case 1>
  - <case 2>
loop_count_to_converge: <integer, 1 = first try>
related_patterns:
  - <link to other KB entries>
related_lessons:
  - <link to lessons that informed this>
cross_refs:
  - <[v2: §N.M] | [wp: §N.M] | [cmem #NNN] | [serena: <m>] | [planning: <p>/<f>] | [wolf: <f>:<l>] | [adr: NNNN]>
---

<body — extended prose, code samples, diagrams as needed>
```

### Lesson entry (`knowledge-base/lessons/<slug>.md`)

```markdown
---
title: <what was tried that didn't work>
domain: <same domains as patterns>
what_was_tried: <description>
why_it_failed: <prose, with evidence>
better_alternative: <link to the patterns/ entry that replaced it>
how_to_recognize_this_trap: <signal future tasks should look for>
loop_count_to_recover: <integer; how many cycles before the better alternative was found>
cross_refs:
  - <same conventions as patterns>
---

<body>
```

### Decision entry (`knowledge-base/decisions/<slug>.md` — ADR-style)

```markdown
---
adr_id: <NNNN>
title: <short descriptive name>
status: <accepted | superseded | deprecated>
date: <YYYY-MM-DD>
deciders: <names>
context: |
  <2-4 paragraphs of background>
decision: |
  <what was decided>
consequences:
  positive:
    - <consequence>
  negative:
    - <consequence>
  neutral:
    - <consequence>
alternatives_considered:
  - title: <alt name>
    rejected_because: <reason>
related_decisions:
  - <link to other ADRs>
cross_refs:
  - <same conventions as patterns>
---

<body>
```

### Reference entry (`knowledge-base/references/<topic>.md`)

Curated index of canonical sources for a given technical or business domain. The trusted-set is in `references/trusted-set.md`.

### Seed entry (`knowledge-base/seed/from-<source-system>.md`)

Curated extracts from existing memory systems, written during Phase 0 KB seeding. These are pointers + context, not duplications. They tell future loops "here's where to look in the existing system for X."

**Seed entries (read in this order when context is needed):**

1. **`from-interview.md`** — autobiographical canon from Corey. **Active reference set as of 2026-05-25 is The Five** (`docs/brand/visual-references.md`): Kith / Oaklandish / Culture Kings / Fear of God / Palm Angels, with Aimé Leon Dore as acceptable adjacency. The historical interview list (which included The Row / Jacquemus / Document-i-D / Coach / Drake Related) is preserved in-doc but those entries are retired; see the in-file canon-supersession note. Plus anti-references (no blue, no clichés, no dry reveals, no lackluster, no dated, no gendered framing), Oakland canon (Deep East, Hills, Stone City, The 100s, Brookfield, Sobrante Park, Coliseum, Real Oakland, The Shows, Sequoyah Highlands), engineering rules, reality check (imagery is #1 blocker)
2. **`from-serena.md`** — index of Serena memories that matter for which task type
3. **`from-gsd.md`** — index of GSD `.planning/` artifacts that matter
4. **`from-claude-mem.md`** — categorized index of high-leverage claude-mem `[cmem #NNN]` IDs by domain
5. **`from-openwolf.md`** — pointer to `.wolf/cerebrum.md` Key Learnings + Do-Not-Repeat sections

**`from-interview.md` is PRIMARY SOURCE** — when there's a conflict between it and any derived doc (eval/brand-story.md, banned-elements.md, etc.), the interview wins.

---

## Cross-reference conventions

Every KB entry uses these in the `cross_refs:` field:

| Convention | Resolves to |
|------------|-------------|
| `[v2: §N.M]` | `docs/SKYYROSE_V2_MASTER_PLAN.md` section N.M |
| `[wp: §N.M]` | `docs/SKYYROSE_WORDPRESS_PLAN.md` section N.M |
| `[cmem #NNN]` | claude-mem observation #NNN (look up via `~/.claude-mem/claude-mem.db` or `.wolf/claude-mem-digest.md`) |
| `[serena: <memory-name>]` | `.serena/memories/<memory-name>.md` |
| `[planning: <phase>/<file>]` | `.planning/phases/<phase>/<file>` |
| `[wolf: <file>:<line>]` | `.wolf/<file>:<line>` (OpenWolf entry — typically `cerebrum.md` or `memory.md`) |
| `[adr: NNNN]` | `docs/adr/NNNN-*.md` |
| `[kb: <category>/<slug>]` | `knowledge-base/<category>/<slug>.md` |

---

## When to write to which layer

This KB is for **V2-build knowledge**. If a learning is not specific to this build, write it where it belongs:

| Type of knowledge | Write to |
|-------------------|----------|
| Pattern or lesson from a Phase 0+ V2 task | `knowledge-base/patterns/` or `knowledge-base/lessons/` (this KB) |
| Project-wide coding convention or architecture fact | `.serena/memories/<topic>.md` (Serena) |
| Cross-session learning from a corrective conversation | `.wolf/cerebrum.md` (OpenWolf — Key Learnings or Do-Not-Repeat section) |
| Bug fix with root cause | `.wolf/buglog.json` (OpenWolf — append entry per OpenWolf protocol) |
| GSD phase artifact (PLAN.md, SUMMARY.md, etc.) | `.planning/phases/<N>-<name>/` (GSD) |
| ADR for an architectural decision affecting the whole project | `docs/adr/NNNN-<topic>.md` |
| One-line memory tracking actions | `.wolf/memory.md` (OpenWolf — append per protocol) |

If a learning falls in **multiple categories**, the principle is: write it where future loops will look first, then add cross-references from the others. Most often, that's this KB plus a one-line pointer in OpenWolf's cerebrum.

---

## INDEX.md regeneration

`knowledge-base/INDEX.md` is auto-generated by `scripts/kb-distill.js --reindex` after every KB write. Do not hand-edit it. To regenerate:

```bash
node scripts/kb-distill.js --reindex
```

The index lists every entry by category (patterns / lessons / decisions / references / seed), with title, domain tag, and one-line summary.

---

## Layer 6 meta-KPI tracking

`scripts/measurement/loop-stats.js` (Phase 0.5 deliverable) reads every KB entry's `loop_count_to_converge` field and writes monthly stats to `eval/loop-convergence.md`:

- Avg loop count per domain — should decrease month-over-month
- First-try pass rate — should increase month-over-month
- KB entry reuse count — >50% of new tasks should cite at least one prior entry by month 2
- Anti-patterns avoided pre-loop — should increase as KB matures
- New trusted-set additions — slow but steady; signals KB depth growing

If these numbers don't trend in the right direction, the KB system is broken — investigate before continuing the build. The point of compound learning is that loop N+1 is cheaper than loop N. If it isn't, something's wrong with how the KB is being written or consulted.
