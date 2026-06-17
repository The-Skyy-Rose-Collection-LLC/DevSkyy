"""Normalized verdict shared across evaluation domains."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal


class Severity(IntEnum):
    DASHBOARD = 1
    TICKET = 2
    PAGE = 3


@dataclass(frozen=True)
class Verdict:
    domain: str  # "imagery" | "copy"
    passed: bool
    score: float  # 0..1 (imagery: gates_passed/total; copy: composite/5)
    gate_results: dict  # imagery: {gate: bool}; copy: {dimension: int}
    failure_tags: tuple[str, ...] = ()
    reason: str = ""
    cost_usd: float = 0.0
    attempts: int = 0
    mode: Literal["hard_gate", "soft_signal"] = "soft_signal"
    detail: dict = field(default_factory=dict)
