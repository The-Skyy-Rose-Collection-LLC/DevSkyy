"""The port that makes one core serve many domains."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from evaluation.contracts import Verdict


@runtime_checkable
class DomainAdapter(Protocol):
    domain: str

    def deterministic_checks(self, subject: Any, ref: Any) -> list[str]:
        """Free, un-hallucinatable hard-fail tags (empty = clean)."""
        ...

    def build_judge_request(self, subject: Any, ref: Any) -> dict:
        """Return {"messages": list[dict], "tool": dict}, consumed by ClaudeJudge.run(**request)."""
        ...

    def parse_verdict(self, judge_output: dict, det_failures: list[str]) -> Verdict: ...

    async def revise(self, ref: Any, critique: dict) -> Any:
        """Produce a revised subject (content: re-call agent; imagery: re-render)."""
        ...

    def load_ground_truth(self) -> list[dict]:
        """Labeled examples for calibration: [{"subject_id": str, "label_pass": bool, "comment": str}]."""
        ...
