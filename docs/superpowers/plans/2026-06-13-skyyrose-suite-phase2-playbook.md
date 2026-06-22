# SkyyRose Suite — Phase 2/3 Execution Playbook (filesystem-verified)

## Context

Phase 1 cleaned + enhanced the skill/agent sources (committed + changelog-recorded). Phase 2 restructures the single live `skyyrose-elite` plugin into the 5-plugin `skyyrose-suite`, built by **copying the cleaned content** into a tracked tree. Phase 3 re-registers + ships. This playbook is filesystem-verified (104/104 skills+agents resolved, 0 missing) so execution doesn't stall on missing/mis-pathed sources.

**Why the copy makes everything committable:** `skyyrose-elite/` is git-tracked. `git mv` → `skyyrose-suite/` stays tracked. Copies *into* it are committable — even though 26 source skills are symlinks into gitignored `.agents/` and ~25 sources live in gitignored `.claude/` or out-of-repo `~/.claude`. The copy is the mechanism that lands all Phase-1 uncommittable work in git.

## Verified mechanics

- **Manifests:** `marketplace.json` = `{name, owner, metadata, plugins:[...]}` (currently 1 plugin, `source:"./"`). `plugin.json` = `{name, version, description, author, license, homepage, keywords}`.
- **Registry:** `~/.claude/plugins/known_marketplaces.json` — dict keyed by marketplace name; `skyyrose-elite → {source:{source:"directory",path:".../skyyrose-elite"}, installLocation, lastUpdated}`. `installed_plugins.json` — `{version, plugins:{ "<plugin>@<marketplace>": [{scope,installPath:<CACHE>,version,installedAt,gitCommitSha}] }}`. **installPath points at a CACHE copy** (`~/.claude/plugins/cache/...`), written by the plugin installer — NOT hand-editable.
- **Source buckets (copy with `cp -RL` to dereference symlinks):** 49 project-realdir (`DevSkyy/.claude/skills/`), 15 symlink→`DevSkyy/.agents/skills/`, 12 `~/.claude/skills/`, 13 home-symlink→`~/.agents/skills/`. 36 `skyyrose-elite/skills/` are market natives.
- **Agents:** 18 needed; `skyyrose-photography-director` is tracked in `skyyrose-elite/agents/`, the other 17 live in gitignored `DevSkyy/.claude/agents/`.

## Target structure

```
skyyrose-suite/                         (git mv from skyyrose-elite)
  .claude-plugin/marketplace.json       (rewrite: 5 plugins, source ./plugins/<n>)
  CROSS-PLUGIN.md                        (new: handoff graph + namespace table)
  plugins/
    skyyrose/         .claude-plugin/plugin.json  commands/skyyrose.md  agents/skyyrose-orchestrator.md  workflows/
    skyyrose-market/  .claude-plugin/plugin.json  skills/* (36 native + 13 general)  agents/* (6)
    skyyrose-design/  .claude-plugin/plugin.json  skills/* (36)  agents/* (5)
    skyyrose-core/    .claude-plugin/plugin.json  skills/* (22)  agents/* (8)
    skyyrose-qa/      .claude-plugin/plugin.json  skills/* (15)  agents/* (5)
```

## Phase 2 — tasks

### 2.1 Restructure + marketplace
- `git mv skyyrose-elite skyyrose-suite`; `mkdir -p skyyrose-suite/plugins`.
- Move the 36 native `skyyrose-*` skills + `commands/skyyrose-elite.md` aside for the market plugin (2.2).
- Rewrite `skyyrose-suite/.claude-plugin/marketplace.json`: `name:"skyyrose-suite"`, `plugins:[5 entries]` each `{name, description, source:"./plugins/<name>", category, author, homepage}`.
- Write `CROSS-PLUGIN.md`: handoff graph (market→design→qa→core→qa), namespace table (`skyyrose-market:*` etc.), when-to-call-which.
- **Verify:** `python3 -c "import json;assert len(json.load(open('skyyrose-suite/.claude-plugin/marketplace.json'))['plugins'])==5"`.
- Commit: `feat(suite): scaffold skyyrose-suite marketplace (5 plugins) + CROSS-PLUGIN.md`.

### 2.2–2.5 Per-plugin build (copy with dereference)
For each plugin: `mkdir -p plugins/<name>/{skills,agents,.claude-plugin}`; for each skill `cp -RL <resolved-source> plugins/<name>/skills/<skill>` (dereference symlinks, bring whole dir incl. `references/`); copy agents; write `plugin.json` (name/desc/version/author/keywords).
- **2.2 market:** 36 natives (`git mv` from old skills/) + 13 general (11 from `DevSkyy/.claude/skills/`, 2 — to-prd/to-issues — deref from `DevSkyy/.agents/skills/`). Agents: 6 elite (content-engine, email-strategist, influencer-lead, launch-commander, paid-media-buyer, seo-commerce). Verify ~49 skills, 6 agents.
- **2.3 design:** 36 skills per the resolution map (mixed buckets — incl. design-master + universal-learner WITH their `references/` dirs: element-schema.md, skyyrose-templates.json, luxury-element-taxonomy.md, skyyrose-seed-elements.json; immersive-interactive-architect WITH `references/` 4 docs). Agents: skyyrose-photography-director, frontend-developer, deploy-and-verify, theme-heal-doctor, wp-code-simplifier. **Verify** `ls plugins/skyyrose-design/skills/immersive-interactive-architect/references | wc -l` → 4; design-master references present (4 files).
- **2.4 core:** 22 skills. Agents: architect, python-reviewer, database-reviewer, build-error-resolver, refactor-cleaner, doc-updater, loop-operator, planner. **Verify** token-aware-behavior + efficient-production present (canonical embeds).
- **2.5 qa:** 15 skills. Agents: code-reviewer, security-reviewer, tdd-guide, e2e-runner, fixer.
- Commit each plugin separately.

### 2.6 Orchestrator plugin (`skyyrose`)
- `agents/skyyrose-orchestrator.md` — classify task → plugin(s); single-skill→direct, multi-step→dev-team workflow.
- `commands/skyyrose.md` — `/skyyrose <task>` front door.
- Copy `.claude/workflows/skyyrose-dev-team.js` + `skyyrose-dev-team-context.html` → `plugins/skyyrose/workflows/`. Verify the workflow still resolves skills by namespace.
- `plugin.json`. **Verify** `test -f plugins/skyyrose/commands/skyyrose.md && test -f plugins/skyyrose/workflows/skyyrose-dev-team-context.html`.

### 2.7 Behavior embed on 25 agents
- Append `## Operating Discipline (always-on)` (referencing `skyyrose-core:token-aware-behavior` + `skyyrose-core:efficient-production`) after frontmatter in every `plugins/*/agents/*.md`.
- **Verify:** `grep -rl "Operating Discipline" skyyrose-suite/plugins/*/agents | wc -l` → 25.

### 2.8 Dispatch routers + memory wiring
- Each themed plugin gets a `<name>-dispatch` skill (when-to-hand-off table from CROSS-PLUGIN.md).
- In `skyyrose-core` memory skills, document read/write to claude-mem / `.wolf/cerebrum.md` / `.wolf/buglog.json`; self-heal → `skyyrose-qa:drive-to-green`.
- **Verify:** 4 dispatch skills exist; `grep -rl "buglog.json" plugins/skyyrose-core/skills | wc -l` ≥1.

## Phase 3 — register, verify, ship

### 3.1 Re-register (FOUNDER ACTION at the cache step)
- Edit `~/.claude/plugins/known_marketplaces.json`: replace the `skyyrose-elite` key with `skyyrose-suite → {source:{source:"directory",path:".../skyyrose-suite"}, ...}`. (I can do this.)
- **The cache install (`installed_plugins.json` → 5 `<plugin>@skyyrose-suite` entries with cache copies) is performed by Claude Code's plugin system, not by editing JSON.** Founder runs the `/plugin` marketplace re-read / install (or restarts the session so the local marketplace is re-read). Remove the stale `skyyrose-elite@skyyrose-elite` install.

### 3.2 Verify load + routing
- 5 plugins load; skills discoverable namespaced (`skyyrose-market:*`, `skyyrose-design:*`, …).
- Smoke-test `/skyyrose <task>`: a single-skill route + a multi-step that hits the dev-team workflow.
- No broken refs: every `references/` path resolves; `php -l` on any moved WC companion content.

### 3.3 Land
- Update `.wolf/cerebrum.md` (suite architecture + Phase-1 lessons: tracked-vs-untracked committability, symlink-deref, ~50% auditor false-positive rate) + `tasks/todo.md`.
- `git status` clean (excl gitignored); **`git push origin HEAD:main` — STOP-AND-SHOW + explicit `y`.**

## Commit strategy
Everything in Phase 2 lands under `skyyrose-suite/` (tracked) → fully committable. Per-task commits (2.1 scaffold, 2.2–2.6 one per plugin, 2.7 embed, 2.8 routers). The push (3.3) is the only STOP-AND-SHOW.

## Risks + mitigations
1. **Symlink ship-broken** → `cp -RL` dereferences; verify no symlinks remain under `skyyrose-suite/` (`find skyyrose-suite -type l` → empty).
2. **Live plugin during transition** → the old `skyyrose-elite` install keeps working off its cache until 3.1; the repo rename doesn't break the installed cache copy. No downtime.
3. **Registration cache step not headless** → explicitly a founder action (3.1); I prep the marketplace + JSON, founder runs `/plugin`.
4. **`references/` dirs dropped** → copy whole skill dirs (`cp -RL <dir>`), verify companion-doc counts post-copy (design-master 4, immersive 4, universal-learner seed+schema).
5. **Behavior-embed namespace** → reference `skyyrose-core:token-aware-behavior` exactly; verify 25/25.
