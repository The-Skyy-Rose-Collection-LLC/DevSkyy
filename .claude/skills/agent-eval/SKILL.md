---
name: agent-eval
description: Head-to-head comparison of coding agents (Claude Code, Aider, Codex, etc.) on custom YAML-defined tasks with pass rate, cost, time, and consistency metrics. Use when choosing between coding agents for a codebase, benchmarking an agent after a model or tooling update, or producing data-backed agent-selection decisions for a team. Do NOT use for grading a single fix or claim (that is adversarial-verification) or for eval-driven development of Claude Code sessions and prompts themselves (that is eval-harness).
origin: ECC
tools: Read, Write, Edit, Bash, Grep, Glob
---

# Agent Eval Skill

A lightweight CLI tool for comparing coding agents head-to-head on reproducible tasks. Every "which coding agent is best?" comparison runs on vibes — this tool systematizes it.

## When to use

- Comparing coding agents (Claude Code, Aider, Codex, etc.) on your own codebase
- Measuring agent performance before adopting a new tool or model
- Running regression checks when an agent updates its model or tooling
- Producing data-backed agent selection decisions for a team

**When NOT to use:**

- Grading whether a single fix, claim, or result actually holds — that is the `adversarial-verification` skill.
- Eval-driven development of Claude Code sessions, prompts, or skills (pass@k on your own workflows rather than head-to-head agent comparison) — that is the sibling `eval-harness` skill at `.claude/skills/eval-harness/SKILL.md`.
- Product imagery or render QC — that is the QC-judge pipeline, not a coding-agent benchmark.

## Inputs

All of these must exist before starting. Any one absent → **stop and report the missing input** — never substitute a hand-rolled comparison loop and label it an agent-eval result.

1. **The `agent-eval` CLI on PATH.** Observed absent on this machine 2026-07-29 (`command -v agent-eval` → exit 1) `[repro]`. Install from the repository in [Links](#links) only after reviewing its source.
2. **A target git repository** with a pinned commit SHA, so every worktree starts from identical state.
3. **≥1 task YAML** (template below) containing **≥1 deterministic judge** (pytest, build command). A task whose only judge is an LLM is not a valid task definition.
4. **Every agent under test installed and authenticated** — its own CLI on PATH, API keys loaded from env, never hardcoded.

## Core Concepts

### YAML Task Definitions

Define tasks declaratively. Each task specifies what to do, which files to touch, and how to judge success:

```yaml
name: add-retry-logic
description: Add exponential backoff retry to the HTTP client
repo: ./my-project
files:
  - src/http_client.py
prompt: |
  Add retry logic with exponential backoff to all HTTP requests.
  Max 3 retries. Initial delay 1s, max delay 30s.
judge:
  - type: pytest
    command: pytest tests/test_http_client.py -v
  - type: grep
    pattern: "exponential_backoff|retry"
    files: src/http_client.py
commit: "abc1234"  # pin to specific commit for reproducibility
```

### Git Worktree Isolation

Each agent run gets its own git worktree — no Docker required. This provides reproducibility isolation so agents cannot interfere with each other or corrupt the base repo.

### Metrics Collected

| Metric | What It Measures |
|--------|-----------------|
| Pass rate | Did the agent produce code that passes the judge? |
| Cost | API spend per task (when available) |
| Time | Wall-clock seconds to completion |
| Consistency | Pass rate across repeated runs (e.g., 3/3 = 100%) |

## Workflow

### 1. Define Tasks

Create a `tasks/` directory with YAML files, one per task:

```bash
mkdir tasks
# Write task definitions (see template above)
```

### 2. Run Agents

Execute agents against your tasks:

```bash
agent-eval run --task tasks/add-retry-logic.yaml --agent claude-code --agent aider --runs 3
```

Each run:
1. Creates a fresh git worktree from the specified commit
2. Hands the prompt to the agent
3. Runs the judge criteria
4. Records pass/fail, cost, and time

### 3. Compare Results

Generate a comparison report:

```bash
agent-eval report --format table
```

```
Task: add-retry-logic (3 runs each)
┌──────────────┬───────────┬────────┬────────┬─────────────┐
│ Agent        │ Pass Rate │ Cost   │ Time   │ Consistency │
├──────────────┼───────────┼────────┼────────┼─────────────┤
│ claude-code  │ 3/3       │ $0.12  │ 45s    │ 100%        │
│ aider        │ 2/3       │ $0.08  │ 38s    │  67%        │
└──────────────┴───────────┴────────┴────────┴─────────────┘
```

## Judge Types

### Code-Based (deterministic)

```yaml
judge:
  - type: pytest
    command: pytest tests/ -v
  - type: command
    command: npm run build
```

### Pattern-Based

```yaml
judge:
  - type: grep
    pattern: "class.*Retry"
    files: src/**/*.py
```

### Model-Based (LLM-as-judge)

```yaml
judge:
  - type: llm
    prompt: |
      Does this implementation correctly handle exponential backoff?
      Check for: max retries, increasing delays, jitter.
```

## Verification

The report table is the tool's self-assessment, not evidence. After a comparison completes, run each of these — every one can return "no":

```bash
command -v agent-eval
git -C "$TARGET_REPO" worktree list
git -C "$TARGET_REPO" status --porcelain
pytest tests/test_http_client.py -v
```

1. `command -v agent-eval` — **PASS:** prints a path and exits 0. `[repro]` If it exits 1, no tool ran, so any "results" you are holding came from somewhere else — discard them (fail-open pattern, bug-230).
2. `git -C "$TARGET_REPO" worktree list` — **PASS:** one worktree per agent-run, each rooted at the pinned commit. `[repro]`
3. `git -C "$TARGET_REPO" status --porcelain` on the **base** repo — **PASS:** empty output; agents wrote only inside their own worktrees. `[repro]`
4. Re-run the winning row's deterministic judge yourself inside that agent's worktree, substituting the task's own judge command (for the template task: `pytest tests/test_http_client.py -v`) — **PASS:** your independently observed verdict matches the report row. `[test]` At least one re-derivation per report; a table you never spot-checked is `[inferred]`.

Judge falsifiability (rule 3 of `docs/skill-authoring-standard.md`): before trusting any task, run its judge in a fresh worktree at the pinned commit **before** any agent touches it. **PASS:** the judge is RED there — the task is genuinely unsolved at base. A judge already green on the unmodified repo can never fail, so every agent "solves" it.

## Worked example

A real invocation on this machine (2026-07-29), exercising the Inputs gate:

```bash
$ command -v agent-eval; echo "exit=$?"
exit=1
```

Observed output: `exit=1` — the CLI is not installed here `[repro]`. The correct response was to stop at Inputs and report the blocker, which is what this section records: no comparison was run and none is claimed. Once installed, a run against the template task is invoked as:

```bash
agent-eval run --task tasks/add-retry-logic.yaml --agent claude-code --agent aider --runs 3
agent-eval report --format table
```

Command shape is from the upstream README in [Links](#links) `[docs]` — re-verify flags against `agent-eval --help` after installing, before citing any of them.

## Failure modes

- **Fail-open preflight (bug-230, ×6 in this repo).** The tool is missing or the run crashed, and an empty/zero-row report gets read as "no differences between agents". An errored gate's output is an artifact — re-run and demand exit 0 before reading any table.
- **Vacuous judge.** A grep judge matches the prompt text an agent echoed into a comment, or the judge is already green at the pinned commit. Guard: prove RED-at-base before the eval (Verification, last step).
- **Single-run comparison.** Agents are non-deterministic; one run per agent makes the consistency column meaningless. Minimum 3 runs.
- **Unpinned commit.** The base repo drifts between runs, so results across days are not comparable. Pin `commit:` in every task YAML.
- **Worktree pollution (bug-231 pattern: shared-state contamination).** An agent writes outside its worktree, corrupting the base repo or a sibling run's results. Guard: Verification step 3; also never use a shared stash stack across eval worktrees.
- **Cost apples-to-oranges.** Some agent CLIs report no spend; comparing a measured cost against "n/a" is `[inferred]`, not measured. Annotate missing columns — never fill them in.
- **LLM-judge drift.** Model-based judges change verdicts across model versions. Keep at least one deterministic judge per task and treat LLM judgments as advisory.

## Best Practices

- **Start with 3-5 tasks** that represent your real workload, not toy examples
- **Run at least 3 trials** per agent to capture variance — agents are non-deterministic
- **Pin the commit** in your task YAML so results are reproducible across days/weeks
- **Include at least one deterministic judge** (tests, build) per task — LLM judges add noise
- **Track cost alongside pass rate** — a 95% agent at 10x the cost may not be the right choice
- **Version your task definitions** — they are test fixtures, treat them as code

## Links

- Repository: [github.com/joaquinhuigomez/agent-eval](https://github.com/joaquinhuigomez/agent-eval)
