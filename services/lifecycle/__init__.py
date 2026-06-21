"""Customer-lifecycle services (deterministic, advisory-only).

Exposes the RFM + lifecycle-stage + churn-risk scorer that unifies the previously
fragmented churn/retention logic scattered across the SDK domain agents. Pure compute:
it suggests a Klaviyo segment/flow, it never sends.
"""

from __future__ import annotations

from services.lifecycle.retention import (
    LifecycleStage,
    RetentionAssessment,
    RetentionScorer,
    format_assessment,
)

__all__ = [
    "LifecycleStage",
    "RetentionAssessment",
    "RetentionScorer",
    "format_assessment",
]
