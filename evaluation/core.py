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
from dataclasses import replace
from typing import Any, Awaitable, Callable

from evaluation.adapter import DomainAdapter
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
    ) -> Verdict:
        subject = await producer(ref)
        verdict = await self.score(adapter, subject, ref)
        attempts = 0
        while not verdict.passed and attempts < cap:
            attempts += 1
            critique = {
                "failure_tags": verdict.failure_tags,
                "reason": verdict.reason,
                "detail": dict(verdict.detail),
            }
            subject = await adapter.revise(ref, critique)
            verdict = await self.score(adapter, subject, ref)
            if verdict.passed:
                break
        return replace(verdict, attempts=attempts)
