"""Risk-scoring services (deterministic, advisory-only).

Currently exposes the fraud/chargeback risk scorer. Every module here is pure and
never-raises: it scores and recommends, it never mutates an order or calls a write API.
"""

from __future__ import annotations

from services.risk.fraud import (
    FraudAssessment,
    FraudScorer,
    RiskLevel,
    RiskSignal,
    format_assessment,
)

__all__ = [
    "FraudAssessment",
    "FraudScorer",
    "RiskLevel",
    "RiskSignal",
    "format_assessment",
]
