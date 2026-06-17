"""Domain-tagged evaluation observability: per-evaluation JSONL + batch summary +
judge-vs-human agreement. Alert+recommend only (never auto-acts)."""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.contracts import Verdict


class Observer:
    def __init__(self, log_path: Path) -> None:
        self._log = Path(log_path)
        self._log.parent.mkdir(parents=True, exist_ok=True)
        self._rows: list[dict] = []

    def record(self, *, subject_id: str, verdict: Verdict, duration_ms: int) -> None:
        row = {
            "subject_id": subject_id,
            "domain": verdict.domain,
            "passed": verdict.passed,
            "score": verdict.score,
            "failure_tags": list(verdict.failure_tags),
            "reason": verdict.reason,
            "cost_usd": verdict.cost_usd,
            "attempts": verdict.attempts,
            "mode": verdict.mode,
            "duration_ms": duration_ms,
        }
        self._rows.append(row)
        with self._log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")

    def summary(self) -> dict:
        total = len(self._rows)
        passed = sum(1 for r in self._rows if r["passed"])
        cost = sum(r["cost_usd"] for r in self._rows)
        tags: dict[str, int] = {}
        for r in self._rows:
            for t in r["failure_tags"]:
                tags[t] = tags.get(t, 0) + 1
        return {
            "total": total,
            "passed": passed,
            "flagged": total - passed,
            "flag_rate": (total - passed) / total if total else 0.0,
            "cost_usd": cost,
            "failure_tags": tags,
        }


def judge_human_agreement(judge_pass: list[bool], human_pass: list[bool]) -> float:
    if len(judge_pass) != len(human_pass) or not judge_pass:
        raise ValueError("equal-length non-empty lists required")
    return sum(1 for a, b in zip(judge_pass, human_pass) if a == b) / len(judge_pass)
