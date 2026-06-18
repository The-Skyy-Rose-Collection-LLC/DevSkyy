"""The job-title evaluator agents. Thin: identity + adapter + core."""

from __future__ import annotations

from typing import Any

from evaluation.core import EvaluationCore, JudgeFn
from evaluation.domains.imagery import ImageryAdapter


class RenderFidelityEvaluator:
    """Imagery domain: does a generated product photo 100%-replicate the real garment?"""

    job_title = "Render Fidelity Evaluator"

    def __init__(self, judge_fn: JudgeFn, adapter: ImageryAdapter | None = None) -> None:
        self._core = EvaluationCore(judge_fn=judge_fn)
        self._adapter = adapter or ImageryAdapter()

    async def evaluate(self, subject: bytes, ref: Any) -> Any:
        return await self._core.score(self._adapter, subject, ref)

    def adapter(self) -> ImageryAdapter:
        return self._adapter
