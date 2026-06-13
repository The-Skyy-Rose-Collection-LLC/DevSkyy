# Skill Cleanup Changelog — Phase 1 (2026-06-13)

Phase 1 of the SkyyRose Plugin Suite build (`docs/superpowers/plans/2026-06-13-skyyrose-plugin-suite.md`). Each flagged skill was cleaned **in place** so the suite (Phase 2) is built from correct sources. Every edit below was filesystem-verified before and after (plan HARD RULE — auditor false-positive rate ~50% this run).

## Committability reality (the core reconciliation)

`.gitignore` L72 ignores `.claude/`. A curated subset is already tracked (77 skill files + 14 agents); those modifications **commit**. Untracked `.claude` files and `~/.claude` globals are **uncommittable** (founder chose: clean in place + record here). The cleaned content still reaches git via the Phase-2 suite copy. `git check-ignore` reports a *tracked* file as "not-ignored" because Git ignore rules never apply to tracked paths — that is why some `.claude` skills commit and others don't.

- **`.agents/skills/` is also gitignored.** 31 of 111 `.claude/skills/` entries are symlinks into it (`woocommerce`, `woocommerce-code-review`, `to-issues`, `layout`, `full-output-enforcement`…). Editing through the symlink writes to the gitignored target → uncommittable.

## Disproven plan assumptions (verified, no action taken)

| Plan task | Claim | Verified reality |
|-----------|-------|------------------|
| 1.12 `fastapi-python` | exists; exclude from suite | **does not exist** in `.claude/skills/` → moot |
| 1.12 `crosspost` | has dead `social-graph-ranker` ref | **clean**; the dead ref is in `social-publisher` L110 (fixed there) |
| 1.10 `token-aware-behavior`/`efficient-production` | may dangle refs | both **self-contained**; real dangling ref was `token-budget-advisor` L38 (fixed) |
| 1.6 `backend-patterns` | decide extend vs rescope | Node/TS-only; `fastapi-patterns` already owns Python → **rescoped** to Node |

## Committed edits (tracked `.claude` files)

| Task | File | Change | Verify | Commit |
|------|------|--------|--------|--------|
| 1.1 | `wordpress-woocommerce-automation/SKILL.md` | `/wp-json/` → `?rest_route=` (WP.com 401) | rest_route×3, wp-json/wc=0 | `1871de7f3` |
| 1.3 | `fal-ai-media/SKILL.md` | strip nano-banana image models → defer to ai-image-generation; keep video/audio | nano-banana=0; seedance/kling/veo/csm/thinksound retained | `c9d548290` |
| 1.6 | `backend-patterns/SKILL.md` | rescope `description:` to Node/TS | fastapi-patterns ref=2; desc names Node | (this batch) |
| 1.7 | `immersive-interactive-architect/SKILL.md` | Three.js r128 → r169 (ESM importmap) | r128=0 | (this batch) |
| 1.7 | (dedup) | `rm -rf immersive-architect` (byte-identical untracked dup) | dir gone | (no git rm; untracked) |
| 1.11 | `verification-loop/SKILL.md` | add Python phase (ruff/bandit/pytest) | bandit/pytest=4 | (this batch) |
| 1.15 | `agents/{loop-operator,wp-code-simplifier,deploy-and-verify}.md` | expand to standard shape (≥60L) | 157/118/148L | (this batch) |

## Uncommittable edits (gitignored `.claude`/`.agents` or `~/.claude` globals) — recorded here, land in git via Phase-2 suite copy

| Task | File (location) | Change | Verify |
|------|-----------------|--------|--------|
| 1.2 | `ai-image-generation/SKILL.md` (`~/.claude`→`~/.agents`) | add Engine-Canon (gpt-image-2 = product engine) + STOP-AND-SHOW cost gate; label other models non-product | STOP-AND-SHOW=2; gpt-image=10; oai2 cite=1 |
| 1.4 | `redis-patterns/SKILL.md` (`.claude` untracked) | convert primary examples to `redis.asyncio` async-first; sync demoted to note | redis.asyncio=8; bare `import redis`=0 |
| 1.5 | `database-migrations/SKILL.md` (`.claude` untracked) | add Alembic section (init, async env.py, autogenerate, upgrade, SQLite batch) | autogenerate=2; batch_alter_table=4 |
| 1.7 | `immersive-interactive-architect/references/*.md` (new, gitignored) | author 4 companion docs: three-js-patterns, gsap-scroll-patterns, ar-mediapipe, woocommerce-3d-embed | 4 files, 400/355/398/431L |
| 1.8 | `interactive-web-development/SKILL.md` (`.claude` untracked) | pin `framer-motion@^11`; add Next.js App Router/RSC + `use client` + Suspense section | framer/use-client/App-Router=12 |
| 1.10 | `token-budget-advisor/SKILL.md` (`.claude` untracked) | inline token heuristics at L38; drop `../context-budget/` file link | `../context-budget`=0 |
| 1.11 | `accessibility/SKILL.md` (`.claude` untracked) | drop dead `swiftui-patterns`; add dialog/combobox/tabs ARIA + axe/jest-axe + Playwright | swiftui=0; axe/aria=15 |
| 1.11 | `executing-plans/SKILL.md` (`~/.claude` global) | add 2-attempt-stop + escalation blocker rule | retry/twice/escalat=4 |
| 1.12 | `woocommerce-code-review/SKILL.md` (symlink→`.agents`) | inline sentence-case rule; drop dead `woocommerce-copy-guidelines` link | guidelines=0; sentence case=2 |
| 1.12 | `social-publisher/SKILL.md` (`.claude` untracked) | remove dead `social-graph-ranker` ref (L110) | social-graph-ranker=0 |
| 1.12 | `to-issues/SKILL.md` (symlink→`.agents`) | specify `gh issue create`; drop unregistered `/setup-matt-pocock-skills` | gh issue create=2; setup-matt=0 |
| 1.13 | `woocommerce/SKILL.md` (symlink→`.agents`) | add HPOS / `wc_get_orders` data-store CRUD; prune boilerplate | HPOS/wc_get_orders/custom_order_tables=9 |
| 1.13 | `frontend-design-direction/SKILL.md` (`.claude` untracked) | add `See Also` cross-ref to `frontend-design` (compose, don't fold) | frontend-design ref=3 |
| 1.14 | `wordpress-woocommerce-automation/references/woo-schemas.md` (new, gitignored) | author WC REST product/order/customer/webhook schemas | 320L |
| 1.14 | `layout/reference/spatial-design.md` (`.agents`) | author spatial/layout reference (grid, spacing scale, optical alignment, container queries) | 349L |

## Decision 2 — Chinese skills: FULL ENHANCEMENT (founder-approved, done)

Both rewritten English + made brand-native + wired to the real `gpt-image-2` grammar (`scripts/oai_render/prompt.py`). Uncommittable (`~/.claude`); land in git via Phase-2 suite copy. Shared contract: `references/element-schema.md` (authored canonical; copied verbatim into both skills).

| File (`~/.claude/skills/`) | Change | Verify |
|----------------------------|--------|--------|
| `design-master/SKILL.md` (497L) | full English rewrite → gpt-image-2 prompt composer aligned to `prompt.py` grammar (ghost/on-model/flatlay modes, COLLECTION_SCENES, view, structured output contract, STOP-AND-SHOW cost gate, The-Five anchors) | gpt-image-2/1024x1536=21; STOP-AND-SHOW=6; Chinese=0; locked-out lineage=0 |
| `design-master/references/skyyrose-templates.json` (135L) | 5 presets: pdp-ghost + 1 on-model campaign per collection (verbatim COLLECTION_SCENES + palette + The-Five anchor) | JSON parses; 5 templates |
| `design-master/references/luxury-element-taxonomy.md` (179L) | 42 luxury-fashion elements by grammatical_position, tagged collection+mode | — |
| `design-master/references/element-schema.md` (94L) | verbatim copy of shared contract | identical to canonical |
| `universal-learner/SKILL.md` (591L) | full English rewrite + all 10 enhancements: `fashion_editorial` domain, SKU-aware dossier ingestion, collection auto-tag, brand-canon validation (Step 3.5), 4-axis scoring, gpt-image-2 extraction mode, provenance fields, human-review diff gate, seed-corpus procedure, manifest export | Chinese=0; fashion_editorial/brand-canon/provenance=22; diff-gate/manifest=22 |
| `universal-learner/references/element-schema.md` (94L) | authored canonical shared contract (dossier input → gpt-image-2 output) | — |
| `universal-learner/references/skyyrose-seed-elements.json` | **97 real elements** extracted from 11 dossiers (all 4 collections) + `prompt.py` COLLECTION_SCENES + collection-stories + visual-references | 97 elements; 0 violations; 0 missing fields; 0 dup ids; spans 9 grammatical positions + 4 collections |

Wiring: two separate files, one shared schema; `universal-learner` writes the seed library, `design-master` reads it (by `collection_tags`+`mode_tags`); STOP-AND-SHOW gate lives in `design-master` (the render trigger). Both enter git via Phase-2 `skyyrose-design` plugin copy.

## Lessons (for `.wolf/cerebrum.md` at Phase-3 land)

1. **Three install views of one skill** — project `.claude/skills/` (symlink or realdir), in-repo gitignored `.agents/skills/`, out-of-repo `~/.claude/skills/`. Committability = is-the-target-tracked, NOT realdir-vs-symlink.
2. **`git check-ignore` says "not-ignored" for tracked files under a gitignored parent** — tracking overrides ignore. Use `git ls-files --error-unmatch` to test true committability, not check-ignore alone.
3. **Auditor false positives confirmed ~50%** — `fastapi-python` (absent), `crosspost` dead ref (wrong file), `layout`/`ai-image-generation` "missing" (exist via `.agents`/symlink). Every flag filesystem-verified before acting; ~4 would have been wasted edits.
