"""Domain-agnostic evaluation orchestration.

score():  deterministic gate -> judge -> verdict (single shot). Used by the render
          pipeline seam (the pipeline owns re-render) and by the calibration harness.
gate():   score -> if fail, adapter.revise -> re-score, cap N, early-exit. Used by the
          content domain (the core owns the revise loop).

``attempts`` counts revisions only (excludes the initial producer+score); a verdict
that passes on the first score returns attempts=0.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import replace
from typing import Any

from evaluation.adapter import DomainAdapter
from evaluation.budget import DEFAULT_EST_JUDGE_COST_USD, CostCapExceeded, EvalBudget
from evaluation.contracts import Verdict

# wrap ClaudeJudge as: lambda req: judge.run(**req)
JudgeFn = Callable[[dict], tuple[dict, float]]  # request -> (judge_output, cost_usd)


class EvaluationCore:
    def __init__(self, judge_fn: JudgeFn) -> None:
        if asyncio.iscoroutinefunction(judge_fn):
            raise TypeError("judge_fn must be synchronous (returns (dict, float), not a coroutine)")
        self._judge = judge_fn

    async def score(self, adapter: DomainAdapter, subject: Any, ref: Any) -> Verdict:
        det = adapter.deterministic_checks(subject, ref)
        if det:
            return Verdict(
                domain=adapter.domain,
                passed=False,
                score=0.0,
                gate_results={},
                failure_tags=tuple(det),
                reason="deterministic pre-check failed",
                cost_usd=0.0,
            )
        request = adapter.build_judge_request(subject, ref)
        judge_output, cost = self._judge(request)
        verdict = adapter.parse_verdict(judge_output, det)
        return replace(verdict, cost_usd=cost)

    async def gate(
        self,
        adapter: DomainAdapter,
        ref: Any,
        producer: Callable[[Any], Awaitable[Any]],
        cap: int = 2,
        *,
        budget: EvalBudget | None = None,
        est_call_cost_usd: float = DEFAULT_EST_JUDGE_COST_USD,
    ) -> Verdict:
        """producer -> judge -> revise loop, capped at ``cap`` revisions.

        When ``budget`` is supplied, the per-call estimate is checked BEFORE every
        paid judge call (the initial score and each revision); if the next call
        would exceed the cap, ``CostCapExceeded`` is raised before producing or
        judging — so a batch never loops past its ceiling. Actual per-call cost is
        accumulated into ``budget`` and reported as the returned verdict's
        ``cost_usd`` (the loop total, not just the last call).
        """
        self._ensure_affordable(budget, est_call_cost_usd)
        subject = await producer(ref)
        verdict = await self.score(adapter, subject, ref)
        total_cost = verdict.cost_usd
        if budget is not None:
            budget.add(verdict.cost_usd)
        attempts = 0
        # Only revise when the judge is calibrated (hard_gate).  A soft_signal
        # verdict means kappa < KAPPA_FLOOR — we don't trust the judge enough to
        # spend money on a revise loop; return the scored verdict as-is.
        while verdict.mode == "hard_gate" and not verdict.passed and attempts < cap:
            self._ensure_affordable(budget, est_call_cost_usd)
            attempts += 1
            critique = {
                "failure_tags": verdict.failure_tags,
                "reason": verdict.reason,
                "detail": dict(verdict.detail),
            }
            subject = await adapter.revise(ref, critique)
            verdict = await self.score(adapter, subject, ref)
            total_cost += verdict.cost_usd
            if budget is not None:
                budget.add(verdict.cost_usd)
            if verdict.passed:
                break
        return replace(verdict, attempts=attempts, cost_usd=total_cost)

    @staticmethod
    def _ensure_affordable(budget: EvalBudget | None, est_call_cost_usd: float) -> None:
        """Raise ``CostCapExceeded`` before a paid judge call that would exceed the cap."""
        if budget is not None and not budget.can_afford(est_call_cost_usd):
            raise CostCapExceeded(
                f"Eval budget exhausted: spent ${budget.spent_usd:.4f} of "
                f"${budget.cap_usd:.4f}; next judge call (est ${est_call_cost_usd:.4f}) "
                f"would exceed the cap. No paid call made."
            )
