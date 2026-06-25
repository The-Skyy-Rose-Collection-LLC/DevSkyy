"""Cost budget + STOP-AND-SHOW ceiling for evaluation judge calls.

``EvaluationCore.gate()`` runs a producer→judge→revise loop (up to ``cap``
revisions) — used by the batch/calibration paths, not the single-shot live
``evaluate()`` path. Before promoting ``gate()`` to production it needs a spend
ceiling so a batch can never loop past a budget.

``EvalBudget`` mirrors ``scripts/oai_render/cost.py`` ``SpendTracker`` but is kept
local to ``evaluation/`` on purpose: the domain-agnostic QC package must not
depend on the ``scripts/oai_render`` render domain (same decoupling rationale as
``monitoring/fleet_observer.py``'s local ``AlertSeverity`` copy — a few lines is
cheaper than an inverted dependency).
"""

from __future__ import annotations

from dataclasses import dataclass

# Conservative per-judge-call estimate for the pre-call budget guard. A verdict is
# ~1.5k output tokens at Sonnet ($15/1M out) ≈ $0.03; rounded up for headroom. The
# guard uses this ESTIMATE to block a call BEFORE it fires; ``add()`` records the
# ACTUAL cost the judge returns afterward.
DEFAULT_EST_JUDGE_COST_USD = 0.05


class CostCapExceeded(RuntimeError):
    """Raised before a paid judge call when it would exceed the budget ceiling."""


@dataclass
class EvalBudget:
    """Runtime accumulator that hard-stops paid judge calls at a cap.

    Check ``can_afford(next_est)`` BEFORE each judge call; ``add(actual)`` after it
    fires. A single ``EvalBudget`` shared across a batch of ``gate()`` calls caps
    the whole batch (the spec's "a batch over max_cost_usd is blocked before any
    paid call").
    """

    cap_usd: float
    spent_usd: float = 0.0

    def can_afford(self, next_cost_usd: float) -> bool:
        return (self.spent_usd + next_cost_usd) <= self.cap_usd

    def add(self, cost_usd: float) -> None:
        self.spent_usd = round(self.spent_usd + cost_usd, 6)

    @property
    def remaining_usd(self) -> float:
        return max(0.0, round(self.cap_usd - self.spent_usd, 6))
