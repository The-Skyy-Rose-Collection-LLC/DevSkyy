"""Normalized verdict shared across evaluation domains."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import IntEnum
from types import MappingProxyType
from typing import Literal

EvalDomain = Literal["imagery", "copy"]


class Severity(IntEnum):
    """Alert-routing surfaces: DASHBOARD (info), TICKET (actionable), PAGE (blocking)."""

    DASHBOARD = 1
    TICKET = 2
    PAGE = 3


@dataclass(frozen=True)
class Verdict:
    domain: EvalDomain
    passed: bool
    score: float  # 0..1 (imagery: gates_passed/total; copy: composite/5)
    gate_results: Mapping[str, object]  # imagery: {gate: bool}; copy: {dimension: int}
    failure_tags: tuple[str, ...] = ()
    reason: str = ""
    cost_usd: float = 0.0
    attempts: int = 0
    mode: Literal["hard_gate", "soft_signal"] = "soft_signal"
    detail: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # freeze the mappings (frozen= only protects field rebinding, not contents)
        object.__setattr__(self, "gate_results", MappingProxyType(dict(self.gate_results)))
        object.__setattr__(self, "detail", MappingProxyType(dict(self.detail)))
        # range invariants
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"score must be 0..1, got {self.score}")
        if self.cost_usd < 0.0:
            raise ValueError(f"cost_usd must be >= 0, got {self.cost_usd}")
        if self.attempts < 0:
            raise ValueError(f"attempts must be >= 0, got {self.attempts}")
