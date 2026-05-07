# Learning Loop

Continuous-improvement loop for the 9-step ADK render pipeline. Reads QA
tournament outcomes from `data/agent-learning/`, surfaces patterns, and
proposes catalog-level engine overrides + prompt-template adjustments.

## What the system records

Each live run of `qa_tournament_fn` writes JSONL lines to:

| Path | Recorded by | Used for |
|---|---|---|
| `data/agent-learning/engine-winrate/<sku>.jsonl` | `record_engine_outcome()` | Engine selection per SKU — which model wins QA most often |
| `data/agent-learning/template-scores/<template_id>.jsonl` | `record_template_score()` | Prompt template performance — which Layer-3 templates score best |
| `data/agent-learning/failure-modes/<sku>.jsonl` | `record_failure_mode()` | Common defects per SKU — recurring QA failure reasons |

All three paths are gitignored (run artifacts; reproducible from runs themselves).

## What the proposals layer produces

`agents/render_pipeline/learning/proposals.py`:

- `propose_engine_overrides(min_runs=3, min_score=80.0)` — returns proposed
  `engine_override` rows for `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
  when an engine consistently wins for a SKU.
- `digest_failure_modes(min_failures=5)` — clusters recurring failure reasons
  into actionable categories.
- `write_proposals_markdown()` — writes a human-readable summary file under
  `data/agent-learning/proposals.md` (gitignored; regenerated from raw JSONL).

## Manual usage

Run the report on demand from the worktree root:

```bash
make adk-learning-report
```

Output: proposals markdown path + terminal printout of engine overrides and
failure-mode digest. No API cost — pure local file analysis.

## Recommended `/loop` prompt

Once at least 7 days of QA tournament outcomes have accumulated, schedule
a daily summary that promotes consistent learnings into the catalog and
re-runs the worst-scoring SKU with refined prompts.

In a Claude Code session, invoke:

```
/loop every 24h:
  1. cd /Users/theceo/DevSkyy-render-pipeline
  2. Run `make adk-learning-report` and parse the proposals
  3. For each engine_override proposal with min_score >= 85 and runs >= 5:
     - Update wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv
       to set engine_override for that SKU
     - Commit with message "feat(catalog): promote engine_override <eng> for <sku>
       (learning-loop, <runs> runs, score=<score>)"
  4. For each failure-mode digest entry with count >= 10:
     - Open agents/render_pipeline/tools/build_prompt.py
     - Add a Layer-3 negative directive addressing that pattern
     - Commit with message "feat(prompt): negative directive for <pattern>
       (<count> occurrences in last 7 days)"
  5. Identify the lowest-scoring SKU in the last 24h
  6. STOP-AND-SHOW: present the worst-scoring SKU and its score, ask whether
     to re-run with the new catalog/prompt updates (paid call ~$0.30)
  7. If approved, run `make adk-eval-live` against that SKU and post the
     score diff. Note: `make adk-eval` is the safe-default that SKIPS the
     paid call; only `make adk-eval-live` (with EVAL_LIVE=1) actually fires.
```

## Thresholds — when to actually enable continuous mode

The loop above is **not** safe to enable on day 1. It mutates the canonical
catalog CSV and the prompt-engineering code on its own. Before flipping it on:

- [ ] At least 30 successful pipeline runs across 5+ SKUs to give the
      `min_runs` floor enough signal to avoid false promotions
- [ ] A backup branch of `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`
      so loop-driven changes can be reverted in one command
- [ ] Manual review of the first proposals output to confirm the recommendations
      match human judgment (run `make adk-learning-report` after ~10 runs and
      eyeball the output)
- [ ] STOP-AND-SHOW gate enforced on the paid re-run step (already in the
      prompt above — keep it)

## What this loop does NOT do

- It does not modify the dossier files (`wordpress-theme/skyyrose-flagship/data/dossiers/*.md`)
  — those are Corey-authored canonical specs per `feedback_dossier_authoring.md`
  in project memory. The pipeline must hard-fail on missing dossiers, not
  generate or "improve" them.
- It does not change ADK agent topology or tool order — those decisions
  live in `agents/render_pipeline/agent.py` and require human review.
- It does not deploy anything — proposals land as commits on a learning branch,
  not on `main` or production.

## Diagnostics

If `make adk-learning-report` reports `(no proposals — need more runs)`:

- Verify QA tournaments are actually recording: `find data/agent-learning -name '*.jsonl' | xargs wc -l`
- Verify recorder calls fire from `qa_tournament_fn`: search for `record_engine_outcome\|record_template_score\|record_failure_mode` in `agents/render_pipeline/tools/qa_tournament.py`
- Tournament writes outcome JSONL on completion — confirm each run produces ≥1 line per SKU file
