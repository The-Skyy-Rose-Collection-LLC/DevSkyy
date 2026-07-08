"""The job-title evaluator agents. Thin: identity + adapter + core."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from evaluation.budget import EvalBudget
from evaluation.contracts import Verdict
from evaluation.core import EvaluationCore, JudgeFn
from evaluation.domains.copy import CopyAdapter
from evaluation.domains.imagery import ImageryAdapter

# Conservative ceiling for a caller that forgets budget=: at the default
# per-call estimate (evaluation.budget.DEFAULT_EST_JUDGE_COST_USD, $0.05) this
# affords ~20 judge calls -- comfortably clears the default cap=2 (3 calls)
# happy path while still hard-stopping a runaway revision loop.
_DEFAULT_GATE_BUDGET_USD = 1.00


class RenderFidelityEvaluator:
    """Imagery domain: does a generated product photo 100%-replicate the real garment?"""

    job_title = "Render Fidelity Evaluator"

    def __init__(self, judge_fn: JudgeFn, adapter: ImageryAdapter | None = None) -> None:
        self._core = EvaluationCore(judge_fn=judge_fn)
        self._adapter = adapter or ImageryAdapter()

    async def evaluate(self, subject: bytes, ref: Any) -> Verdict:
        return await self._core.score(self._adapter, subject, ref)

    def adapter(self) -> ImageryAdapter:
        return self._adapter


class CopyEvaluator:
    """Copy domain: does generated copy hold the SkyyRose brand line?"""

    job_title = "Brand Copy Evaluator"

    def __init__(self, judge_fn: JudgeFn, adapter: CopyAdapter | None = None) -> None:
        self._core = EvaluationCore(judge_fn=judge_fn)
        self._adapter = adapter or CopyAdapter()

    async def evaluate(self, subject: str, ref: Any) -> Verdict:
        """Single-shot score (deterministic gate -> judge -> verdict)."""
        return await self._core.score(self._adapter, subject, ref)

    async def gate(
        self,
        ref: Any,
        producer: Callable[[Any], Awaitable[Any]],
        cap: int = 2,
        *,
        budget: EvalBudget | None = None,
        unbounded: bool = False,
    ) -> Verdict:
        """Score-and-revise loop: re-call the producer up to `cap` times on failure.

        Defaults to a conservative ``EvalBudget`` so a caller that forgets
        ``budget=`` gets bounded spend instead of silently unlimited judge calls.
        Pass ``unbounded=True`` to opt out explicitly (matches
        ``EvaluationCore.gate()``'s back-compat ``budget=None`` default).
        """
        if budget is None and not unbounded:
            budget = EvalBudget(cap_usd=_DEFAULT_GATE_BUDGET_USD)
        return await self._core.gate(self._adapter, ref, producer, cap, budget=budget)

    def adapter(self) -> CopyAdapter:
        return self._adapter
