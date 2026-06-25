# SkyyRose Suite — Skill Content-Quality Audit

**Date:** 2026-06-13
**Method:** 7 parallel content auditors read every suite skill's SKILL.md against a production bar (shallow / stale / incomplete / contradictory / redundant), then the main thread **verified every existence/missing-file claim against the filesystem** (auditors over-report missing files ~50%).

---

## A. CONFIRMED — STALE / project-canon conflicts (fix before embedding)
These are correctness issues, not just freshness — several conflict with locked project canon.

| Skill | Issue | Fix |
|-------|-------|-----|
| `wordpress-woocommerce-automation` | builds `/wp-json/` base URL → **401 on WP.com Atomic**; project CLAUDE.md mandates `?rest_route=` | swap to `?rest_route=` form |
| `ai-image-generation` | references Gemini 3 Pro / FLUX.2 — **conflicts with project's locked OAI Image 2 engine**; no STOP-AND-SHOW cost gate | align to OAI Image 2; add cost gate |
| `fal-ai-media` | nano-banana image models — **conflicts with OAI Image 2 lock** (memory says "erase nano-banana") | replace image section with OAI Image 2; keep video/audio |
| `redis-patterns` | sync `redis.Redis`, not `redis.asyncio` — project is async-first (**confirmed: no async in file**) | swap to `redis.asyncio` + async examples |
| `database-migrations` | **no Alembic** (project's SQLAlchemy ORM) (**confirmed**) | add Alembic section (autogenerate, env.py, batch-alter) |
| `backend-patterns` | Node/Express/Next only — **no FastAPI/Python** in a Python-primary repo | extend with FastAPI/Python or rescope |
| `immersive-interactive-architect` | Three.js CDN pinned **r128** (current r169+); blocks CapsuleGeometry, WebGPU, new color mgmt | update CDN pins, drop r128 workarounds |
| `interactive-web-development` | framer-motion examples unpinned; no App Router/RSC patterns | pin version; add RSC section |

## B. CONFIRMED — REDUNDANT (consolidate, don't embed all)
| Cluster | Action |
|---------|--------|
| `immersive-architect` ≈ `immersive-interactive-architect` (auditor: byte-identical) | keep one (verify with diff), drop the other |
| TDD trio: `tdd`, `tdd-workflow`, `test-driven-development` | keep `test-driven-development` (most rigorous); merge tracer-bullet from others; drop 2 |
| Behavior cluster: `token-aware-behavior` / `strategic-compact` / `token-budget-advisor` / `full-output-enforcement` overlap `context-budget` + `efficient-production` | consolidate compaction/handoff into `context-budget`; banned-pattern list into `efficient-production`; keep token-aware as the canonical embed |
| `systematic-debugging` ≈ `diagnose` | consolidate into `diagnose` |
| `error-handling` retry logic dup'd in `backend-patterns` | dedupe (reference, don't copy) |
| `api-design`, `python-patterns` user-copy == project-copy | dedup (Tier-A) |
| `to-issues` ≈ `to-prd` (structural overlap) | keep both only if distinct outputs; else merge |
| `crosspost` ≈ `social-publisher` (multi-platform posting) | dedupe or scope crosspost to its unique value |

## C. CONFIRMED — SHALLOW (rewrite/expand or rescope)
| Skill | Issue | Fix |
|-------|-------|-----|
| `design-master` | Chinese-only; a graphic-prompt tool, not a frontend skill | translate + refocus, or move out of design plugin |
| `universal-learner` | Chinese-only; hardcoded to an 18-prompt dataset, not this project | localize + reproject, or drop |
| `frontend-design-direction` | thin salvaged PR; no production triad / anti-fingerprint | merge into `frontend-design` or expand |
| `woocommerce` | generic cookbook; no HPOS / `wc_get_order` data-store / WP.com constraints | add HPOS + data-store; prune boilerplate |

## D. NEEDS-VERIFY — RESOLVED against filesystem (2026-06-13)

### D1. CONFIRMED real (fix in cleanup pass)
| Skill | Confirmed issue | Fix |
|-------|-----------------|-----|
| `wordpress-router` | depends on **missing** `wp-project-triage` skill; no fallback | add manual triage fallback or inline detection |
| `crosspost` | Postbridge setup undocumented (0 install mentions) + dead `social-graph-ranker` ref + overlaps `social-publisher` | document setup or drop Postbridge; remove dead ref; dedupe vs social-publisher |
| `agent-eval` | external binary, **0 install docs** | document install or mark aspirational |
| `eval-harness` | `/eval` commands not wired to real skills | wire or mark aspirational |
| `accessibility` | dead `swiftui-patterns` ref + content gaps (ARIA widgets, axe/NVDA testing) | drop dead ref; add ARIA-widget + axe/Playwright a11y sections |
| `verification-loop` | security scan is JS-only | add ruff/bandit Python phase |
| `executing-plans` | no error-recovery / escalation procedure | add blocker-handling + retry limit |
| `woocommerce-code-review` | dead `../woocommerce-copy-guidelines/sentence-case.md` (skill missing) | create guideline or inline the rule |
| `fastapi-python` | 61L generic; redundant with `fastapi-patterns` (327L) + `fastapi-async-patterns` (791L) | drop or merge into fastapi-patterns |
| `to-prd` / `to-issues` | `setup-matt-pocock-skills` EXISTS (satisfiable) but runtime issue-tracker config dep remains; structural overlap | make issue-tracker config explicit; dedupe overlap |

### D2. DISPROVEN by filesystem check (NO action)
- `ui-ux-pro-max` — `scripts/search.py` **exists**; SKILL.md **ASCII-only** (no "Vietnamese"). Complete.
- `woocommerce-backend-dev` — all 8 companion `.md` (code-entities, hooks, dependency-injection, …) **exist** in-dir. Not dangling.
- `extract-design` (designlang install documented, 8 mentions), `critique` (npx documented), `social-publisher` (socialclaw documented) — deps OK. social-publisher's only dead ref is `social-graph-ranker` (cosmetic).
- Sibling refs `liquid-glass-design`, `impeccable`, `setup-matt-pocock-skills` all **exist**.

## E. DISPROVEN — auditor claims verified FALSE (do NOT act)
- `frontend-slides` "missing STYLE_PRESETS.md" → **exists** (both copies)
- `prototype` "missing LOGIC.md/UI.md, incomplete" → **both companions exist**
- `fastapi-async-patterns` / `fastapi-python` "don't exist" → **both exist** (`async` is 791L, solid)

## F. Verified SOLID (no action) — majority
All 10 `threejs-*`, `frontend-patterns`, `shadcn`, `optimize`, `frontend-design`, `frontend-a11y`, design/taste set (`design-system`, `liquid-glass-design`, `minimalist-ui`, `industrial-brutalist-ui`, `motion-ui`, `high-end-visual-design`, `image-taste-frontend`, `gpt-taste`, `stitch-design-taste`, `bolder`, `colorize`, `delight`, `polish`, `impeccable`, `layout`, `redesign-existing-projects`, `aidesigner-frontend`, `ui-demo`), `fastapi-patterns`, `postgres-patterns`, `docker-patterns`, `continuous-learning-v2`, `stalled-agent-recovery`, `efficient-production`, `context-budget`, `writing-plans`, `brainstorming`, `parallel-prototyping`, `drive-to-green`, `audit-resolution-loop`, `verification-before-completion`, `e2e-testing`, `audit`, `audit-pass2-verifier`, `diagnose`, `receiving-code-review`, `luxury-mockup-pipeline`, and the marketing set (`brand-voice`, `content-engine`, `email-ops`, `seo`, `market-research`, `marketing-campaign`, `article-writing`, `investor-materials`, `investor-outreach`).

---

## Impact on the suite build
The gap-fill scope is bigger than structural-only: ~8 STALE fixes (3 are project-canon **correctness** bugs), ~6 redundancy consolidations, ~4 shallow rewrites, ~15 needs-verify, plus the structural companion-doc gaps (§4 of the design spec). **Every needs-verify item gets a filesystem/dep check before any fix** — the audit is the starting point, not the truth (auditor missing-file false-positive rate ~50% this run).
