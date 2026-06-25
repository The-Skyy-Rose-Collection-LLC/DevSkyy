# SkyyRose Plugin Suite — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the single `skyyrose-elite` plugin into a 5-plugin SkyyRose suite (market / design / core / qa + orchestrator) under one marketplace, built from cleaned skills, with cross-plugin routing, embedded dev-team workflow, and memory wired to existing substrates.

**Architecture:** Phase 1 cleans flagged skills *in place* (`~/.claude/skills`, `.claude/skills`) so the suite is built from correct sources. Phase 2 scaffolds `skyyrose-suite/` and copies cleaned skills + distributes agents + builds the orchestrator. Phase 3 registers, verifies, ships.

**Tech Stack:** Claude Code plugins (marketplace.json/plugin.json), Markdown skills/agents, local marketplace install, git.

**Hard rule (all phases):** every "missing file / unverified dep / broken ref" is **filesystem-checked before any fix** (`ls`/`test -f`/`grep`). Auditor missing-file false-positive rate was ~50% this run. Never fix from the audit alone.

**Spec:** `docs/superpowers/specs/2026-06-13-skyyrose-plugin-suite-design.md` · **Audits:** spec §4/§4b + `docs/skill-quality-audit-2026-06-13.md`

---

## File Structure

```
skyyrose-elite/  →  skyyrose-suite/                 (git mv; marketplace root)
  .claude-plugin/marketplace.json                   (rewrite: 5 plugins)
  CROSS-PLUGIN.md                                    (new: handoff doctrine)
  plugins/
    skyyrose/        .claude-plugin/plugin.json  commands/skyyrose.md  agents/skyyrose-orchestrator.md  workflows/
    skyyrose-market/ .claude-plugin/plugin.json  skills/*  agents/*
    skyyrose-design/ .claude-plugin/plugin.json  skills/*  agents/*
    skyyrose-core/   .claude-plugin/plugin.json  skills/*  agents/*
    skyyrose-qa/     .claude-plugin/plugin.json  skills/*  agents/*
```
Cleanup edits (Phase 1) touch source skills under `~/.claude/skills/<name>/` and `.claude/skills/<name>/` — NOT the suite (suite copies them after cleaning).

---

# PHASE 1 — Clean flagged skills (build suite from clean sources)

### Task 1.1: Fix WP REST canon bug — `wordpress-woocommerce-automation`

**Files:** Modify `.claude/skills/wordpress-woocommerce-automation/SKILL.md` (+ `~/.claude/skills/` copy if present)

- [ ] **Step 1: Confirm the defect**

Run: `grep -n "wp-json" .claude/skills/wordpress-woocommerce-automation/SKILL.md`
Expected: a line building `f"{site_url}/wp-json"` (the 401-on-WP.com bug).

- [ ] **Step 2: Replace the base-URL pattern**

Replace every `{site_url}/wp-json/wc/v3/...` construction with the WP.com-safe form:
```python
# WP.com Atomic blocks /wp-json/ — use the query-param REST route (project CLAUDE.md canon)
base = f"{site_url}/?rest_route=/wc/v3"
# endpoints append with & not /: f"{base}/products" → f"{site_url}/?rest_route=/wc/v3/products"
```
Add a one-line note: `# NOTE: skyyrose.co (WP.com Atomic) 401s on /wp-json/; ?rest_route= is mandatory.`

- [ ] **Step 3: Verify**

Run: `grep -c "rest_route" .claude/skills/wordpress-woocommerce-automation/SKILL.md` → ≥1
Run: `grep -c "wp-json/wc" .claude/skills/wordpress-woocommerce-automation/SKILL.md` → 0

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/wordpress-woocommerce-automation/
git commit -m "fix(skill): wordpress-woocommerce-automation use ?rest_route= (WP.com canon)"
```

### Task 1.2: Fix imagery-engine canon bug — `ai-image-generation`

**Files:** Modify `~/.claude/skills/ai-image-generation/SKILL.md`

- [ ] **Step 1: Confirm defect** — Run: `grep -niE "gemini 3|flux\.2|nano-banana" ~/.claude/skills/ai-image-generation/SKILL.md` (expect matches).
- [ ] **Step 2: Replace primary engine** — Set the canonical product-image engine to **OpenAI Image 2 (gpt-image, high fidelity)** per project lock. Keep other engines only as explicitly-labeled non-product/experimental options. Add a **STOP-AND-SHOW cost gate** block: any paid generation prints `Action/SKU/Source/Cost` and waits for `y` (per CLAUDE.md). Reference `project_imagery_engine_oai2` canon.
- [ ] **Step 3: Verify** — Run: `grep -ciE "image 2|gpt-image" ~/.claude/skills/ai-image-generation/SKILL.md` → ≥1; `grep -ci "STOP-AND-SHOW" ...` → ≥1.
- [ ] **Step 4: Commit** — `git add` (note: `~/.claude` is outside repo — record change in the audit doc's changelog instead; see Task 1.16).

### Task 1.3: Fix imagery canon bug — `fal-ai-media`

**Files:** Modify `.claude/skills/fal-ai-media/SKILL.md`

- [ ] **Step 1: Confirm** — `grep -ni "nano-banana" .claude/skills/fal-ai-media/SKILL.md` (expect matches).
- [ ] **Step 2: Fix** — Replace the **image** section's nano-banana models with a pointer to `ai-image-generation` (OAI Image 2 is canonical for product imagery). Keep fal.ai **video/audio** capabilities (not in conflict). Add note: `# Product images → use ai-image-generation (OAI Image 2). fal.ai here = video/audio only.`
- [ ] **Step 3: Verify** — `grep -c "nano-banana" .claude/skills/fal-ai-media/SKILL.md` → 0 in the image section; video/audio retained.
- [ ] **Step 4: Commit** — `git add .claude/skills/fal-ai-media/ && git commit -m "fix(skill): fal-ai-media defer product images to OAI Image 2 (canon)"`

### Task 1.4: `redis-patterns` → async-first

**Files:** Modify `.claude/skills/redis-patterns/SKILL.md`
- [ ] **Step 1: Confirm** — `grep -c "redis.asyncio\|aioredis" .claude/skills/redis-patterns/SKILL.md` → 0 (confirmed stale).
- [ ] **Step 2: Fix** — Convert primary examples to `redis.asyncio` (`import redis.asyncio as redis`; `await r.get(...)`; async connection pool). Keep a short "sync (scripts only)" note.
- [ ] **Step 3: Verify** — `grep -c "redis.asyncio" .claude/skills/redis-patterns/SKILL.md` → ≥1.
- [ ] **Step 4: Commit** — `git add .claude/skills/redis-patterns/ && git commit -m "fix(skill): redis-patterns async-first (redis.asyncio)"`

### Task 1.5: `database-migrations` → add Alembic

**Files:** Modify `.claude/skills/database-migrations/SKILL.md`
- [ ] **Step 1: Confirm** — `grep -ci alembic .claude/skills/database-migrations/SKILL.md` → 0.
- [ ] **Step 2: Fix** — Add an **Alembic** section (the project ORM): `alembic init`, `env.py` wiring to SQLAlchemy metadata, `alembic revision --autogenerate -m`, `alembic upgrade head`, batch-alter for SQLite, and the project rule that every model change ships a migration in the same commit.
- [ ] **Step 3: Verify** — `grep -ci "alembic revision --autogenerate" .claude/skills/database-migrations/SKILL.md` → ≥1.
- [ ] **Step 4: Commit** — `git add .claude/skills/database-migrations/ && git commit -m "fix(skill): database-migrations add Alembic (project ORM)"`

### Task 1.6: `backend-patterns` → add Python/FastAPI

**Files:** Modify `.claude/skills/backend-patterns/SKILL.md`
- [ ] **Step 1: Confirm** — `grep -ci "fastapi\|def \|async def" .claude/skills/backend-patterns/SKILL.md` (expect ~0 Python; Node-only).
- [ ] **Step 2: Fix** — Add a FastAPI/Python service-layer section (router→service→repository, Pydantic boundary validation, dependency-injection via `Depends`), OR narrow the skill's `description:` to "Node/TS backend patterns" and let `fastapi-patterns` own Python. **Decision at build:** if `fastapi-patterns` already covers Python service layers well, rescope backend-patterns to Node; else extend. Filesystem-check `fastapi-patterns` content first.
- [ ] **Step 3: Verify** — either Python section present, or `description:` scoped to Node + no Python claims.
- [ ] **Step 4: Commit** — `git add .claude/skills/backend-patterns/ && git commit -m "fix(skill): backend-patterns scope/extend for Python-primary repo"`

### Task 1.7: `immersive-*` — dedup + Three.js bump + companion docs

**Files:** `.claude/skills/immersive-architect/`, `.claude/skills/immersive-interactive-architect/`
- [ ] **Step 1: Confirm dup** — Run: `diff .claude/skills/immersive-architect/SKILL.md .claude/skills/immersive-interactive-architect/SKILL.md`. If identical → keep `immersive-interactive-architect` (the suite-mapped name), drop `immersive-architect`.
- [ ] **Step 2: Bump Three.js** — In the kept skill, replace CDN pin `three@0.128`/`r128` with `three@0.169`+; remove r128-only workarounds; note CapsuleGeometry/WebGPU now available.
- [ ] **Step 3: Create the 4 referenced companion docs** — `references/three-js-patterns.md`, `references/gsap-scroll-patterns.md`, `references/ar-mediapipe.md`, `references/woocommerce-3d-embed.md`. Each: real content matching what SKILL.md promises (boilerplate/geometry/shaders; ScrollTrigger/SplitText/Lottie; MediaPipe body-tracking; `<model-viewer>` WC embed per project 3D plan).
- [ ] **Step 4: Verify** — `for f in three-js-patterns gsap-scroll-patterns ar-mediapipe woocommerce-3d-embed; do test -f .claude/skills/immersive-interactive-architect/references/$f.md && echo OK $f; done` → 4 OK. `grep -c "0.128\|r128" SKILL.md` → 0.
- [ ] **Step 5: Commit** — `git add .claude/skills/immersive-interactive-architect/ && git rm -r .claude/skills/immersive-architect 2>/dev/null; git commit -m "fix(skill): immersive — dedup, Three.js r169, author 4 reference docs"`

### Task 1.8: `interactive-web-development` — pin + RSC

**Files:** `~/.claude/skills/interactive-web-development/SKILL.md`
- [ ] **Step 1: Fix** — Pin `framer-motion@^11`; add a Next.js App Router / RSC section (`"use client"` boundaries for animation, server components for data). Record in changelog (Task 1.16, `~/.claude`).
- [ ] **Step 2: Verify** — `grep -c "framer-motion@\|App Router\|use client" ~/.claude/skills/interactive-web-development/SKILL.md` → ≥1.

### Task 1.9: Consolidate TDD trio → `test-driven-development`

**Files:** keep `~/.claude/skills/test-driven-development/`; fold from `tdd`, `tdd-workflow`
- [ ] **Step 1: Confirm** — read all three; confirm `test-driven-development` is most rigorous (audit says so).
- [ ] **Step 2: Fold** — port any unique "tracer-bullet" guidance from `tdd`/`tdd-workflow` into `test-driven-development`. Add a Python (pytest) example alongside the TS one.
- [ ] **Step 3: Mark** — the suite will embed only `test-driven-development` (Phase 2). Leave `tdd`/`tdd-workflow` as general skills (out of suite). No deletion of generals.
- [ ] **Step 4: Verify** — `grep -ci pytest ~/.claude/skills/test-driven-development/SKILL.md` → ≥1.

### Task 1.10: Consolidate behavior cluster

**Files:** `~/.claude/skills/{context-budget,efficient-production,token-aware-behavior}/SKILL.md`
- [ ] **Step 1: Decide canonical** — `token-aware-behavior` = the agent-embed canonical (per spec §5). `context-budget` absorbs compaction/handoff thresholds; `efficient-production` absorbs the banned-pattern list. `strategic-compact`, `token-budget-advisor`, `full-output-enforcement` stay general but the **suite embeds only `token-aware-behavior` + `efficient-production`** (Phase 2) — no overlap shipped.
- [ ] **Step 2: Verify** — confirm token-aware-behavior + efficient-production each fully self-contained (no "see strategic-compact" dangling). `grep -c "see strategic-compact\|see token-budget" ...` → 0.

### Task 1.11: `verification-loop` Python phase + `executing-plans` recovery + `accessibility`

- [ ] **Step 1: verification-loop** — Modify `~/.claude/skills/verification-loop/SKILL.md`: add a Python phase (`ruff check`, `bandit -r`, `pytest`) beside the JS phases. Verify: `grep -c "bandit\|ruff\|pytest" ...` ≥1.
- [ ] **Step 2: executing-plans** — Modify `~/.claude/skills/executing-plans/SKILL.md`: add a concrete blocker-handling procedure (retry limit = 5, same-error-twice = stop, escalate with context). Verify: `grep -ci "retry\|blocker\|escalat" ...` ≥1.
- [ ] **Step 3: accessibility** — Modify `.claude/skills/accessibility/SKILL.md`: drop dead `swiftui-patterns` ref; add ARIA-widget patterns (dialog/combobox/tooltip) + axe-core/Playwright a11y test snippet. Verify: `grep -c "swiftui-patterns" ...` → 0; `grep -ci "axe\|aria" ...` ≥1.
- [ ] **Step 4: Commit** — `git add .claude/skills/accessibility/ && git commit -m "fix(skill): accessibility add ARIA widgets + axe testing, drop dead ref"` (the `~/.claude` edits → changelog Task 1.16).

### Task 1.12: `woocommerce-code-review` dead ref + `crosspost`/`to-*` dedup + `fastapi-python`

- [ ] **Step 1: woocommerce-code-review** — Modify `.claude/skills/woocommerce-code-review/SKILL.md`: the `../woocommerce-copy-guidelines/sentence-case.md` skill is **missing** (verified). Inline the sentence-case rule directly (1 short section) rather than dangle. Verify: `grep -c "woocommerce-copy-guidelines" ...` → 0.
- [ ] **Step 2: crosspost** — Modify `.claude/skills/crosspost/SKILL.md`: remove dead `social-graph-ranker` ref; either document Postbridge `SC_API_KEY` setup or narrow scope; add cross-ref to `social-publisher` to avoid duplication. Verify: `grep -c "social-graph-ranker" ...` → 0.
- [ ] **Step 3: fastapi-python** — 61L generic, redundant with `fastapi-patterns`. Suite embeds `fastapi-patterns` + `fastapi-async-patterns` only; `fastapi-python` excluded (no deletion of general). Note in changelog.
- [ ] **Step 4: to-prd/to-issues** — make the issue-tracker config explicit (GitHub Issues default) since `setup-matt-pocock-skills` runtime config may be absent; note structural overlap (keep both — distinct outputs PRD vs issues). Verify: `grep -ci "github" ~/.claude/skills/to-issues/SKILL.md` ≥1.
- [ ] **Step 5: Commit** — `git add .claude/skills/woocommerce-code-review/ .claude/skills/crosspost/ && git commit -m "fix(skill): woocommerce-code-review inline rule; crosspost drop dead ref"`

### Task 1.13: SHALLOW — `frontend-design-direction`, `woocommerce`; per-skill call on Chinese-only

- [ ] **Step 1: frontend-design-direction** — Modify `.claude/skills/frontend-design-direction/SKILL.md`: it's thin. Fold its unique value into `frontend-design` (cross-ref) OR expand with production-triad + anti-fingerprint. Decision: if <40 useful lines, suite embeds `frontend-design` only and excludes this. Verify the decision recorded.
- [ ] **Step 2: woocommerce** — Modify `.claude/skills/woocommerce/SKILL.md`: add HPOS / `wc_get_order` data-store CRUD section + WP.com constraints; prune generic plugin-structure boilerplate. Verify: `grep -ci "HPOS\|wc_get_order" ...` ≥1.
- [ ] **Step 3: Chinese-only per-skill call** — Read `~/.claude/skills/design-master/SKILL.md` + `universal-learner/SKILL.md`. For EACH: if it has salvageable suite value → translate to English + refocus; else **exclude from suite** (leave as general). Record decision per skill in changelog.
- [ ] **Step 4: Commit** — `git add .claude/skills/woocommerce/ .claude/skills/frontend-design-direction/ && git commit -m "fix(skill): woocommerce HPOS/data-store; frontend-design-direction disposition"`

### Task 1.14: Author remaining companion docs

**Files:** `.claude/skills/layout/reference/spatial-design.md`, `.claude/skills/wordpress-woocommerce-automation/references/woo-schemas.md`
- [ ] **Step 1: Confirm missing** — `test -f .claude/skills/layout/reference/spatial-design.md || echo MISSING`; same for woo-schemas.md.
- [ ] **Step 2: Author** — `spatial-design.md`: the spatial/layout reference `layout`'s SKILL.md cites (grid systems, spacing scale, optical alignment). `woo-schemas.md`: WooCommerce REST product/order JSON schemas the automation skill references.
- [ ] **Step 3: Verify** — both `test -f` pass; each >40 lines real content.
- [ ] **Step 4: Commit** — `git add .claude/skills/layout/ .claude/skills/wordpress-woocommerce-automation/ && git commit -m "docs(skill): author missing companion refs (spatial-design, woo-schemas)"`

### Task 1.15: Fill the 5 agent gaps

**Files:** `.claude/agents/{frontend-developer,fixer,loop-operator,wp-code-simplifier,deploy-and-verify}.md`
- [ ] **Step 1: frontend-developer** — add the missing `description:` frontmatter line (summarize the 255L body). Verify: `awk -F: '/^description:/{print;exit}' .claude/agents/frontend-developer.md` non-empty.
- [ ] **Step 2: Complete the 4 thin agents** — for `fixer`(17L), `loop-operator`(36L), `wp-code-simplifier`(30L), `deploy-and-verify`(37L): expand each to the standard agent shape (role, when-to-use, procedure, tools, output, examples). Verify each: `wc -l <file>` ≥ 60.
- [ ] **Step 3: Commit** — `git add .claude/agents/ && git commit -m "fix(agents): add frontend-developer desc + complete 4 thin agents"`

### Task 1.16: Cleanup changelog (track `~/.claude` edits)

**Files:** Create `docs/skill-cleanup-changelog-2026-06-13.md`
- [ ] **Step 1:** Record every `~/.claude/skills` edit (outside-repo, uncommittable) with skill, change, verify-command-output. (ai-image-generation, interactive-web-development, test-driven-development, behavior cluster, verification-loop, executing-plans, to-issues, fastapi-python disposition, Chinese-skill decisions.)
- [ ] **Step 2: Commit** — `git add docs/skill-cleanup-changelog-2026-06-13.md && git commit -m "docs: skill cleanup changelog (Phase 1)"`

---

# PHASE 2 — Scaffold the suite

### Task 2.1: Restructure to `skyyrose-suite` + marketplace

**Files:** `skyyrose-elite/` → `skyyrose-suite/`, `.claude-plugin/marketplace.json`, `CROSS-PLUGIN.md`
- [ ] **Step 1:** `git mv skyyrose-elite skyyrose-suite`; create `skyyrose-suite/plugins/`.
- [ ] **Step 2:** Rewrite `skyyrose-suite/.claude-plugin/marketplace.json` to list 5 plugins, each `"source": "./plugins/<name>"`.
- [ ] **Step 3:** Write `skyyrose-suite/CROSS-PLUGIN.md` — handoff graph (market→design→qa→core→qa), namespace table, when-to-call-which.
- [ ] **Step 4: Verify** — `python3 -c "import json;d=json.load(open('skyyrose-suite/.claude-plugin/marketplace.json'));assert len(d['plugins'])==5"` → no error.
- [ ] **Step 5: Commit** — `git add skyyrose-suite && git commit -m "feat(suite): scaffold skyyrose-suite marketplace (5 plugins) + CROSS-PLUGIN.md"`

### Task 2.2: `skyyrose-market` plugin (move current content)

**Files:** `skyyrose-suite/plugins/skyyrose-market/{.claude-plugin/plugin.json,skills/,agents/}`
- [ ] **Step 1:** Move current `skyyrose-suite/skills/*` (36) → `plugins/skyyrose-market/skills/`; move 6 market agents → `plugins/skyyrose-market/agents/` (photography-director goes to design in 2.3).
- [ ] **Step 2:** Copy cleaned general marketing skills (`brand-voice, content-engine, email-ops, seo, social-publisher, market-research, marketing-campaign, crosspost, article-writing, investor-materials, investor-outreach, to-prd, to-issues`) from source into `skills/`.
- [ ] **Step 3:** Write `plugin.json` (name `skyyrose-market`, description, keywords).
- [ ] **Step 4: Verify** — `ls plugins/skyyrose-market/skills | wc -l` ≈ 46; 6 agents.
- [ ] **Step 5: Commit** — `git commit -m "feat(suite): skyyrose-market plugin"`

### Task 2.3: `skyyrose-design` plugin

**Files:** `skyyrose-suite/plugins/skyyrose-design/{...}`
- [ ] **Step 1:** Copy cleaned design skills (26), imagery (`ai-image-generation, fal-ai-media, luxury-mockup-pipeline`), FE (`frontend-patterns, shadcn, interactive-web-development, immersive-interactive-architect`), `threejs-*` (10), WP (`woocommerce, wordpress-woocommerce-automation, wp-performance, wp-rest-api, wp-block-themes, wp-block-development, wp-plugin-development, wordpress-router, woocommerce-backend-dev, woocommerce-code-review, woocommerce-webhooks`), `optimize, prototype, accessibility`. Skip Chinese-only excludes per 1.13.
- [ ] **Step 2:** Agents: `skyyrose-photography-director, frontend-developer, deploy-and-verify, theme-heal-doctor, wp-code-simplifier`.
- [ ] **Step 3:** `plugin.json`. **Verify** companion dirs copied (immersive references/, etc.): `ls plugins/skyyrose-design/skills/immersive-interactive-architect/references | wc -l` → 4.
- [ ] **Step 4: Commit** — `git commit -m "feat(suite): skyyrose-design plugin"`

### Task 2.4: `skyyrose-core` plugin

**Files:** `skyyrose-suite/plugins/skyyrose-core/{...}`
- [ ] **Step 1:** Copy backend (`fastapi-patterns, fastapi-async-patterns, postgres-patterns, redis-patterns, docker-patterns, api-design, database-migrations, error-handling, backend-patterns, python-patterns`), memory/heal (`continuous-learning-v2, universal-learner?, stalled-agent-recovery, learned`), behavior (`token-aware-behavior, efficient-production, strategic-compact, context-budget, token-budget-advisor, full-output-enforcement`), planning (`writing-plans, executing-plans, brainstorming, parallel-prototyping`).
- [ ] **Step 2:** Agents: `architect, python-reviewer, database-reviewer, build-error-resolver, refactor-cleaner, doc-updater, loop-operator, planner`.
- [ ] **Step 3:** `plugin.json`. **Verify** token-aware-behavior + efficient-production present (canonical for embeds).
- [ ] **Step 4: Commit** — `git commit -m "feat(suite): skyyrose-core plugin"`

### Task 2.5: `skyyrose-qa` plugin

**Files:** `skyyrose-suite/plugins/skyyrose-qa/{...}`
- [ ] **Step 1:** Copy `drive-to-green, audit-resolution-loop, verification-loop, verification-before-completion, test-driven-development, e2e-testing, eval-harness, agent-eval, ai-regression-testing, audit, audit-pass2-verifier, systematic-debugging→diagnose (keep diagnose), critique, requesting-code-review, receiving-code-review`.
- [ ] **Step 2:** Agents: `code-reviewer, security-reviewer, tdd-guide, e2e-runner, fixer`.
- [ ] **Step 3:** `plugin.json`. **Verify** ~16 skills, 5 agents.
- [ ] **Step 4: Commit** — `git commit -m "feat(suite): skyyrose-qa plugin"`

### Task 2.6: Orchestrator plugin + embedded dev-team workflow

**Files:** `skyyrose-suite/plugins/skyyrose/{commands/skyyrose.md, agents/skyyrose-orchestrator.md, workflows/skyyrose-dev-team.*, .claude-plugin/plugin.json}`
- [ ] **Step 1:** `skyyrose-orchestrator.md` agent — classify task → plugin(s); single-skill→direct, multi-step→dev-team workflow. Include the embed block (Task 2.7).
- [ ] **Step 2:** `commands/skyyrose.md` — `/skyyrose <task>` front door invoking the orchestrator agent.
- [ ] **Step 3:** Copy `.claude/workflows/skyyrose-dev-team*` → `plugins/skyyrose/workflows/` (embed). Verify the workflow script still resolves plugin skills by namespace.
- [ ] **Step 4: Verify** — `test -f plugins/skyyrose/commands/skyyrose.md && test -f plugins/skyyrose/workflows/skyyrose-dev-team-context.html`.
- [ ] **Step 5: Commit** — `git commit -m "feat(suite): orchestrator plugin + embedded dev-team workflow"`

### Task 2.7: Embed behavior block on all 25 agents

**Files:** every `skyyrose-suite/plugins/*/agents/*.md`
- [ ] **Step 1:** Append the standard block (spec §5) after frontmatter in each agent: the `## Operating Discipline (always-on)` section referencing `skyyrose-core:token-aware-behavior` + `skyyrose-core:efficient-production`.
- [ ] **Step 2: Verify** — `for f in skyyrose-suite/plugins/*/agents/*.md; do grep -q "Operating Discipline" "$f" || echo "MISSING $f"; done` → no output. Count: `grep -rl "Operating Discipline" skyyrose-suite/plugins/*/agents | wc -l` → 25.
- [ ] **Step 3: Commit** — `git commit -m "feat(suite): embed token-aware + efficient-production on all 25 agents"`

### Task 2.8: Per-plugin dispatch routers + memory wiring

**Files:** `plugins/<name>/skills/<name>-dispatch/SKILL.md` (×4), memory note in core skills
- [ ] **Step 1:** Each themed plugin gets a `<name>-dispatch` skill with the "when to hand off" table (handoff graph from CROSS-PLUGIN.md).
- [ ] **Step 2:** In `skyyrose-core` memory skills, document read/write to claude-mem / `.wolf/cerebrum.md` / `.wolf/buglog.json`; self-heal cross-calls `skyyrose-qa:drive-to-green`.
- [ ] **Step 3: Verify** — 4 dispatch skills exist; `grep -rl "buglog.json" plugins/skyyrose-core/skills | wc -l` ≥1.
- [ ] **Step 4: Commit** — `git commit -m "feat(suite): per-plugin dispatch routers + memory wiring"`

---

# PHASE 3 — Register, verify, ship

### Task 3.1: Register + reinstall

**Files:** `~/.claude/plugins/installed_plugins.json`, `~/.claude/plugins/known_marketplaces.json`
- [ ] **Step 1:** Update the local marketplace entry to point at `skyyrose-suite` root; register the 5 plugins (replace the single `skyyrose-elite@skyyrose-elite` entry).
- [ ] **Step 2:** Reinstall (local marketplace re-read). Verify no `skyyrose-elite` dangling reference remains.
- [ ] **Step 3: Verify** — `python3 -c "import json;d=json.load(open('$HOME/.claude/plugins/installed_plugins.json'));print([k for k in d['plugins'] if 'skyyrose' in k])"` → 5 plugin keys.

### Task 3.2: Verify load + routing

- [ ] **Step 1:** Confirm all 5 plugins load + skills discoverable namespaced (the session skill list shows `skyyrose-market:*`, `skyyrose-design:*`, etc.).
- [ ] **Step 2:** Smoke-test `/skyyrose <sample task>` classifies + routes (single-skill + a multi-step that hits the dev-team workflow).
- [ ] **Step 3:** No broken refs: `for f in $(grep -rl "references/" skyyrose-suite/plugins/*/skills); do ...verify each ref exists...; done`.
- [ ] **Step 4:** php -l / structural checks on any moved WP companion content.

### Task 3.3: Land it

- [ ] **Step 1:** Update `.wolf/cerebrum.md` (suite architecture + the skill-cleanup lessons + auditor-false-positive lesson) + `tasks/todo.md`.
- [ ] **Step 2:** Final `git status` clean (excl gitignored); `git push origin HEAD:main` (STOP-AND-SHOW ack).
- [ ] **Step 3:** Verify origin/main updated; suite live.

---

## Self-Review

- **Spec coverage:** §2 arch → Tasks 2.1-2.8 ✓; §3 manifests → 2.2-2.6 ✓; §4 structural gaps → 1.14-1.15 ✓; §4b quality → 1.1-1.13 ✓; §5 embed → 2.7 ✓; §6 routing → 2.1/2.8 ✓; §7 memory → 2.8 ✓; §8 build mechanics → Phase 3 ✓. All covered.
- **Placeholder scan:** Cleanup tasks specify exact grep/verify gates + concrete change content; large content additions (Alembic, ARIA) specify required subsections + verify greps (acceptable for skill-markdown — verify gate proves completion). Chinese-skill + backend-patterns + frontend-design-direction are explicit decide-at-build with recorded-decision gates, not silent TBDs.
- **Consistency:** `token-aware-behavior` + `efficient-production` named identically in spec §5, Task 1.10, 2.4, 2.7. `skyyrose-suite` path consistent. Handoff graph (market→design→qa→core→qa) identical in CROSS-PLUGIN.md/2.1/2.8.
- **Filesystem-check rule** restated per phase — honors the ~50% false-positive lesson.
