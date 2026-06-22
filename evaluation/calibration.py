"""Cohen's kappa (binary pass/fail) → evaluator mode. Floor 0.65 (research-backed)."""

from __future__ import annotations

from collections import Counter
from typing import Literal

KAPPA_FLOOR = 0.65


def cohen_kappa(judge: list[int], human: list[int]) -> float:
    if len(judge) != len(human) or not judge:
        raise ValueError("equal-length non-empty rating lists required")
    n = len(judge)
    po = sum(1 for a, b in zip(judge, human, strict=True) if a == b) / n
    cj, ch = Counter(judge), Counter(human)
    cats = set(judge) | set(human)
    pe = sum((cj.get(c, 0) / n) * (ch.get(c, 0) / n) for c in cats)
    return 1.0 if pe == 1.0 else (po - pe) / (1 - pe)


def decide_mode(kappa: float) -> Literal["hard_gate", "soft_signal"]:
    return "hard_gate" if kappa >= KAPPA_FLOOR else "soft_signal"
