"""Validation scoring helpers shared across SuperAgents.

Computes ``(quality_score, confidence_score)`` for ``ValidationResult``
without fabricating numbers. The previous baseline of ``quality_score = 0.9``
on every clean run was a hardcoded placeholder — this module replaces it
with real measurements when available and a transparent low-confidence
baseline when not.
"""

from __future__ import annotations

from typing import Any

# Baseline quality when no real fidelity measurement is available.
# Deliberately below the typical 0.9 placeholder so that downstream
# consumers can distinguish "measured pass" from "no measurement".
_UNMEASURED_BASELINE = 0.6
_WARNING_PENALTY = 0.05
_MIN_BASELINE = 0.2

# Confidence: how much we trust the score we just produced.
_CONFIDENCE_MEASURED = 0.95
_CONFIDENCE_UNMEASURED = 0.5


def _normalize_fidelity(score: Any) -> float | None:
    """Coerce a fidelity reading into [0, 1]. Returns None on bad input."""
    try:
        value = float(score)
    except (TypeError, ValueError):
        return None
    # Tools may return either 0-1 or 0-100; normalize to 0-1.
    if value > 1.0:
        value = value / 100.0
    return max(0.0, min(1.0, value))


def compute_validation_scores(
    asset_validation: dict[str, Any] | None,
    warning_count: int,
) -> tuple[float, float]:
    """Compute (quality_score, confidence_score) for a clean validation run.

    Args:
        asset_validation: The dict returned by an agent's ``*_validate_asset``
            tool. May contain a ``fidelity_score`` key (0-1 or 0-100).
        warning_count: Number of validation warnings accumulated so far.

    Returns:
        Tuple of (quality_score, confidence_score), each in [0, 1].
    """
    measured: float | None = None
    if asset_validation is not None:
        measured = _normalize_fidelity(asset_validation.get("fidelity_score"))

    if measured is not None:
        # Real measurement — trust it, no warning-based degradation needed.
        return round(measured, 3), _CONFIDENCE_MEASURED

    # No measurement — degrade the baseline by warnings to surface signal.
    penalty = _WARNING_PENALTY * max(0, warning_count)
    baseline = max(_UNMEASURED_BASELINE - penalty, _MIN_BASELINE)
    return round(baseline, 3), _CONFIDENCE_UNMEASURED


__all__ = ["compute_validation_scores"]
