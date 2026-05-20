"""AOS healing types — action enum, retry config, and healing decision."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HealAction(StrEnum):
    RETRY = "retry"
    ABORT = "abort"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class RetryConfig:
    max_retries: int
    base_delay_seconds: float
    exponential: bool = False


@dataclass(frozen=True)
class HealDecision:
    action: HealAction
    delay_seconds: float
    reason: str
