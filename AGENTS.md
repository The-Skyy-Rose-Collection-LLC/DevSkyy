# Agent Orchestration — DevSkyy

## When to Use Agents

Use agents **proactively** — don't wait to be asked. The rules:

1. **Code just written/modified** → `code-reviewer` (always)
2. **Complex feature request** → `planner` first, then execute
3. **Bug report** → fix it autonomously, then `security-reviewer` if it touched auth/input
4. **Build fails** → `build-error-resolver`
5. **Dead code suspected** → `refactor-cleaner`
6. **Before deploy** → `deploy-and-verify`
7. **After deploy** → screenshot all pages with Chrome DevTools MCP

## Project Agents (`.claude/agents/`)

### Core Workflow

| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `planner` | opus | Before any 3+ step task | Creates step-by-step plan, identifies risks, waits for approval |
| `architect` | opus | Architectural decisions, new systems | Designs system structure, evaluates trade-offs |
| `code-reviewer` | sonnet | After EVERY code change | Reviews quality, security, maintainability — mandatory |
| `security-reviewer` | sonnet | Auth, user input, API endpoints, secrets | Flags OWASP Top 10, injection, XSS, leaked secrets |
| `tdd-guide` | opus | New features, bug fixes | Enforces RED→GREEN→IMPROVE, 85%+ coverage |

### Build & Deploy

| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `build-error-resolver` | sonnet | Build fails, type errors | Minimal diffs to get build green — no architectural edits |
| `deploy-and-verify` | sonnet | Before production deploy | Runs PHP lint → deploy → cache flush → screenshot all pages |
| `e2e-runner` | sonnet | Critical user flows | Playwright E2E tests, screenshots, traces |

### Cleanup & Docs

| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `refactor-cleaner` | sonnet | Dead code, duplicates, bloat | Runs analysis tools, safely removes unused code |
| `wp-code-simplifier` | haiku | After WordPress theme edits | Reviews WP code for dead refs, duplicates, XSS, bloat |
| `doc-updater` | haiku | After significant changes | Updates codemaps, READMEs, docs |

### Language-Specific

| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `python-reviewer` | sonnet | Any Python code change | PEP 8, type hints, security, performance |
| `database-reviewer` | sonnet | SQL, migrations, schemas | Query optimization, schema design, security |

### Operations

| Agent | Model | When | What It Does |
|-------|-------|------|-------------|
| `loop-operator` | sonnet | Long-running autonomous tasks | Monitors agent loops, intervenes when stalled |

---

## Parallel Agent Strategy

**ALWAYS run independent agents in parallel.** One message, multiple Agent tool calls.

```
GOOD: 3 agents in parallel
  Agent 1: security-reviewer on auth module
  Agent 2: code-reviewer on API changes
  Agent 3: python-reviewer on ML pipeline

BAD: Sequential when independent
  First agent 1... wait... then agent 2... wait... then agent 3
```

## Agent Selection by Workspace

| Workspace | Primary Agents | Review Agent |
|-----------|---------------|--------------|
| **Python API** (`/`) | planner, tdd-guide, build-error-resolver | python-reviewer |
| **Dashboard** (`frontend/`) | planner, e2e-runner | code-reviewer |
| **WordPress** (`wordpress-theme/`) | deploy-and-verify, wp-code-simplifier | code-reviewer |
| **Database** (`database/`) | planner | database-reviewer |

## WordPress Theme Deploy Pipeline

The standard deploy sequence for SkyyRose:

```
1. planner          → Plan the changes
2. (implement)      → Write the code
3. code-reviewer    → Review changes
4. wp-code-simplifier → WordPress-specific review
5. security-reviewer → If touched auth/input/WC
6. deploy-and-verify → PHP lint + deploy + screenshots
7. (verify)         → Chrome DevTools MCP screenshots
```

## Model Routing

| Complexity | Model | Agents |
|-----------|-------|--------|
| Deep reasoning, architecture | **Opus** | planner, architect, tdd-guide |
| Code work, reviews, builds | **Sonnet** | code-reviewer, security-reviewer, build-error-resolver, e2e-runner |
| Lightweight docs, quick checks | **Haiku** | doc-updater, wp-code-simplifier |
