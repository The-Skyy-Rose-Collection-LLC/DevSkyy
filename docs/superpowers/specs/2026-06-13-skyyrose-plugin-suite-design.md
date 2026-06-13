# SkyyRose Plugin Suite — Design Spec

**Date:** 2026-06-13
**Status:** Approved architecture; pending spec review → implementation plan
**Supersedes:** single `skyyrose-elite` plugin (becomes the marketplace root)

---

## 1. Goal

Split the monolithic `skyyrose-elite` plugin into a **5-plugin suite** under one local marketplace: 4 themed capability plugins + 1 orchestrator. The suite is **self-contained** (ships its own orchestration engine), **cross-calling** (a meta router delegates across plugins), and **memory-backed** (wired to existing claude-mem / OpenWolf / buglog substrates). Every skill is complete end-to-end; every agent embeds `token-aware-behavior` + `efficient-production`.

---

## 2. Architecture

```
skyyrose-suite/                          (was skyyrose-elite/ — marketplace root)
  .claude-plugin/marketplace.json        lists 5 plugins
  CROSS-PLUGIN.md                        handoff doctrine (shared)
  plugins/
    skyyrose/          ORCHESTRATOR — /skyyrose router command + skyyrose-orchestrator agent
                       + EMBEDDED skyyrose-dev-team workflow (the execution engine)
    skyyrose-market/   SEO / marketing / brand / content / social
    skyyrose-design/   design / imagery / WordPress
    skyyrose-core/     backend / memory-loops / behavior / planning
    skyyrose-qa/       testing / verification / audit loops
```

One local marketplace, 5 installable plugins. Claude Code exposes every installed plugin's skills/agents globally (namespaced `<plugin>:<name>`), so cross-plugin invocation is native; the orchestrator + routing docs make it intentional.

### Execution loop

1. `/skyyrose <task>` → **skyyrose-orchestrator** agent classifies the task (which plugin(s)).
2. **Single-skill task** → invoke that plugin's skill/agent directly (fast path).
3. **Multi-step build** → hand to the **embedded `skyyrose-dev-team` workflow** (plan → FE/BE build → review-fix loop → WP-health sweep → synth).
4. Workflow pulls skills/agents from the relevant plugins along the handoff graph: **market → design → qa → core → qa**.
5. **Memory/heal** (core): reads+writes claude-mem (episodic), `.wolf/cerebrum.md` (durable learnings), `.wolf/buglog.json` (bug→fix). Self-heal = `drive-to-green` + `stalled-agent-recovery` consult `buglog.json` BEFORE fixing.

---

## 3. Plugin manifests

### 3.1 `skyyrose` (orchestrator)
- **Command:** `/skyyrose <task>` — entry point / router.
- **Agent:** `skyyrose-orchestrator` (NEW) — classifies task → routes to plugin(s) or the dev-team workflow.
- **Workflow:** `skyyrose-dev-team` (EMBEDDED — moved from `.claude/workflows/`), the multi-step execution engine.
- **Docs:** `CROSS-PLUGIN.md` handoff graph.

### 3.2 `skyyrose-market` (~46 skills · 6 agents)
- **Skills:** 9 SkyyRose core (`brand-dna, content-engine, email-flows, influencer-growth, launch-commander, paid-media, photography-brief, product-copy, seo-commerce`) · 27 `skyyrose-social-*` · general (`brand-voice, seo, social-publisher, email-ops, market-research, marketing-campaign, crosspost, article-writing, investor-materials, investor-outreach, to-prd, to-issues`).
- **Agents:** `skyyrose-content-engine, skyyrose-email-strategist, skyyrose-influencer-lead, skyyrose-launch-commander, skyyrose-paid-media-buyer, skyyrose-seo-commerce`.

### 3.3 `skyyrose-design` (~55 skills · 5 agents)
- **Skills:** all 26 design/taste · imagery (`ai-image-generation, fal-ai-media, luxury-mockup-pipeline`) · FE structure (`frontend-patterns, shadcn, interactive-web-development, immersive-architect, immersive-interactive-architect`) · `threejs-*` (10) · WordPress (`woocommerce, wordpress-woocommerce-automation, wp-performance, wp-rest-api, wp-block-themes, wp-block-development, wp-plugin-development, wordpress-router, woocommerce-backend-dev, woocommerce-code-review, woocommerce-webhooks`) · `optimize, prototype, accessibility/frontend-a11y`.
- **Agents:** `skyyrose-photography-director, frontend-developer, deploy-and-verify, theme-heal-doctor, wp-code-simplifier`.

### 3.4 `skyyrose-core` (~25 skills · 8 agents)
- **Skills:** backend (`fastapi-patterns, fastapi-async-patterns, fastapi-python, postgres-patterns, redis-patterns, docker-patterns, sqlalchemy-alembic-..., api-design, database-migrations, error-handling, backend-patterns, python-patterns`) · memory/learn/heal (`continuous-learning-v2, universal-learner, stalled-agent-recovery, learned`) · behavior (`token-aware-behavior, efficient-production, strategic-compact, context-budget, token-budget-advisor, full-output-enforcement`) · planning (`writing-plans, executing-plans, brainstorming, parallel-prototyping`).
- **Agents:** `architect, python-reviewer, database-reviewer, build-error-resolver, refactor-cleaner, doc-updater, loop-operator, planner`.

### 3.5 `skyyrose-qa` (~18 skills · 5 agents)
- **Skills:** loops (`drive-to-green, audit-resolution-loop, verification-loop, verification-before-completion`) · `tdd-workflow, tdd, test-driven-development, e2e-testing, eval-harness, agent-eval, ai-regression-testing` · `audit, audit-pass2-verifier, systematic-debugging, critique, diagnose` · `requesting-code-review, receiving-code-review`.
- **Agents:** `code-reviewer, security-reviewer, tdd-guide, e2e-runner, fixer`.

---

## 4. Completeness standard (end-to-end)

Every suite skill must meet the prototype-skill bar: valid frontmatter (`name` + `description`), a complete body (purpose, when-to-use, procedure, examples/output spec), zero TODO/placeholder/stub sections. **Audit result (2026-06-13):** suite-bound skills pass; the thin/stub files in the inventory are almost entirely `gsd-*` (excluded). Any suite-bound skill found below the bar during implementation is completed before its plugin is finalized.

### Agent gaps to fill
| Agent | Gap | Fix |
|-------|-----|-----|
| `frontend-developer` | missing `description:` frontmatter (255L body intact) | add description |
| `fixer` | 17L — too thin | complete to standard |
| `loop-operator` | 36L — thin | complete to standard |
| `wp-code-simplifier` | 30L — thin | complete to standard |
| `deploy-and-verify` | 37L — thin | complete to standard |

---

## 5. Agent embed: `token-aware-behavior` + `efficient-production`

**Audit:** 0 of 24 agents currently embed either. **All** get a standard always-on block appended (after frontmatter, before the agent body):

```markdown
## Operating Discipline (always-on)

This agent operates under two always-on behaviors — they govern HOW it works, not what:

- **token-aware-behavior** — monitor context budget (thresholds 60/75/88/95%). Compress history at 75%, emit a structured handoff at 88%, hard-stop at 95%. Never silently drop work mid-task.
- **efficient-production** — no file re-reads (read once, reuse); batch parallel tool calls; check `.wolf/anatomy.md` before full reads; one targeted search over three vague ones; verify-before-claim (no unverified assertions); zero TODO/mock/placeholder in delivered output; HTML for structured multi-section docs.

Canonical sources: `skyyrose-core:token-aware-behavior`, `skyyrose-core:efficient-production`.
```

The block points at the core-plugin copies as the in-suite canonical (themselves snapshots of the global `~/.claude/skills` masters per §8), so suite behavior stays single-sourced inside the suite while the global copies remain the master.

---

## 6. Cross-plugin routing

- **Naming:** `skyyrose-market:`, `skyyrose-design:`, `skyyrose-core:`, `skyyrose-qa:` — predictable, greppable.
- **Front door:** `/skyyrose` command → orchestrator agent classifies and delegates.
- **Per-plugin router skill:** each themed plugin ships a `<name>-dispatch` skill with a "when to hand off" table (the handoff graph).
- **Shared doctrine:** `CROSS-PLUGIN.md` at marketplace root, referenced by every plugin README.
- **Handoff graph:** market → design → qa → core → qa. (market briefs → design builds → qa verifies → core fixes+remembers → qa re-verifies.)

---

## 7. Memory + self-healing wiring

- **No new store.** core-plugin skills read/write existing substrates:
  - claude-mem DB — episodic ("what happened").
  - `.wolf/cerebrum.md` — durable learnings / do-not-repeat (self-learning target).
  - `.wolf/buglog.json` — bug→fix ledger (self-healing memory).
- **Self-learning:** `continuous-learning-v2` + `universal-learner` write durable patterns to cerebrum; the orchestrator appends SkyyRose-specific wins after each run.
- **Self-healing:** `drive-to-green` (bounded auto-fix loop, lives in `skyyrose-qa`) + `stalled-agent-recovery` (lives in `skyyrose-core`) consult `buglog.json` before fixing; new fixes append to `buglog.json`. core cross-calls `skyyrose-qa:drive-to-green` for the test→fix→verify cycle.

---

## 8. Sourcing & build mechanics

- **Embedded skills are snapshots.** General `~/.claude/skills` / `.claude/skills` copies stay canonical; re-embed to sync (documented in suite README).
- **Build phases:**
  1. Scaffold `skyyrose-suite/` + 5 `plugins/<name>/` dirs + `marketplace.json` (5 plugins) + `CROSS-PLUGIN.md`.
  2. Redistribute current `skyyrose-elite` content (36 skills + 7 agents) → market (36 + 6) / design (photography-director).
  3. Copy general skills into the right plugin (`skills/<name>/`).
  4. Embed 17 repo agents across the 4 themed plugins.
  5. Fill the 5 agent gaps; append the embed block to all 25 agents (24 + orchestrator).
  6. Build orchestrator: `/skyyrose` command + `skyyrose-orchestrator` agent; embed `skyyrose-dev-team` workflow.
  7. Write per-plugin `<name>-dispatch` router skills + `CROSS-PLUGIN.md`.
  8. Update `installed_plugins.json` + `known_marketplaces.json`; reinstall 5 plugins (local marketplace).
  9. Verify: all 5 plugins load; skills discoverable namespaced; `/skyyrose` routes; no broken refs.
  10. Commit + push.

- **Out of scope (stay as general skills, NOT in suite):** `gsd-*` (67), per-language pattern/testing families, unrelated misc utilities.

---

## 9. Success criteria

- 5 plugins install + load from one marketplace; all skills discoverable namespaced.
- `/skyyrose <task>` classifies + delegates correctly (single-skill fast path + dev-team multi-step path).
- Every suite skill passes the completeness bar; the 5 agent gaps filled.
- All 25 agents carry the embed block referencing core canonical behaviors.
- Memory/heal reads+writes claude-mem / cerebrum / buglog (no new store).
- Cross-plugin handoffs documented + working.
- Working tree clean; landed on main.
