"""The job-title evaluator agents. Thin: identity + adapter + core."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from evaluation.contracts import Verdict
from evaluation.core import EvaluationCore, JudgeFn
from evaluation.domains.copy import CopyAdapter
from evaluation.domains.imagery import ImageryAdapter


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
        self, ref: Any, producer: Callable[[Any], Awaitable[Any]], cap: int = 2
    ) -> Verdict:
        """Score-and-revise loop: re-call the producer up to `cap` times on failure."""
        return await self._core.gate(self._adapter, ref, producer, cap)

    def adapter(self) -> CopyAdapter:
        return self._adapter
