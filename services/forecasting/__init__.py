"""Demand-forecasting services (deterministic, advisory-only).

Exposes a velocity/sellout forecaster that replaces the ``forecast_sales`` stub (which fell
through to "not available") with a real, explainable model: trailing-window velocity, trend
direction, days-to-sellout, and a reorder recommendation. No ML training required; an ML
time-series model is a later upgrade behind the same interface.
"""

from __future__ import annotations

from services.forecasting.demand import (
    DemandForecast,
    DemandForecaster,
    SelloutRisk,
    Trend,
    format_forecast,
)

__all__ = [
    "DemandForecast",
    "DemandForecaster",
    "SelloutRisk",
    "Trend",
    "format_forecast",
]
