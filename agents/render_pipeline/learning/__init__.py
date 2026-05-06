"""Continuous-improvement subsystem for the RenderPipeline agent.

Three loops, each persisting structured signals to disk so the agent
gets measurably better with every run — across sessions, without
human intervention beyond catalog/dossier edits.

  Loop 1 — Engine Routing (auto-learned)
    Every QA tournament records which engine was used, what score
    it produced, and what fields drove the routing decision. Over
    time, build a per-SKU `engine_winrate` table. When the table
    has ≥3 successful runs at score ≥80 with one engine, propose
    that engine as the SKU's `engine_override`. Catalog edits stay
    human-approved (commit gate); the system surfaces the proposal,
    doesn't auto-apply.

  Loop 2 — Prompt Template A/B (already exists, formalized)
    PromptRegistry.record_score is the existing entry point. Wire
    it into the agent's QA tool so every tournament feeds back. The
    registry's avg_score tracking selects the winning template per
    category × view × model_hint. The new piece: weekly digest of
    template-performance deltas, surfaced as a markdown report.

  Loop 3 — Failure-Mode Catalog (knowledge accretion)
    When a SKU repeatedly fails (≥2 runs with score <50), capture
    the synthesis judge's `issues` and `suggested_fixes` into a
    per-SKU failure-mode log. After 5+ entries on a SKU, the log
    is structured enough to suggest dossier amendments — e.g., "the
    judge consistently says 'fabric reads as glossy satin instead
    of fleece' → dossier should add a sentence about matte finish
    explicitly".

All three loops write to `data/agent-learning/` (gitignored, but
durable on disk). Periodic `learning/digest.py` produces a markdown
report that goes into the Obsidian knowledge graph.

Storage shape:
  data/agent-learning/
    engine-winrate/
      {sku}.jsonl          # append-only: {ts, engine, score, vision_keywords}
    template-scores/
      {template_id}.jsonl  # append-only: {ts, sku, score}
    failure-modes/
      {sku}.jsonl          # append-only: {ts, score, issues, suggested_fixes}
    proposals.md           # human-readable digest of pending overrides
"""

from agents.render_pipeline.learning.proposals import propose_engine_overrides
from agents.render_pipeline.learning.recorder import (
    record_engine_outcome,
    record_failure_mode,
    record_template_score,
)

__all__ = [
    "record_engine_outcome",
    "record_template_score",
    "record_failure_mode",
    "propose_engine_overrides",
]
