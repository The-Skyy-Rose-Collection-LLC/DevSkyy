"""Deterministic demand / sellout forecaster (advisory only).

Closes agent gap #3 (Drop/Demand Forecasting). The previous ``analytics_agent.forecast_sales``
fell through to "not available", and ``algorithm_agent._predict_demand`` was a pure-LLM guess.
This is a real, explainable baseline:

- **Velocity**: units sold per day over a trailing window.
- **Trend**: recent window vs the prior window (ACCELERATING / STEADY / DECLINING).
- **Sellout**: days-to-sellout = inventory / velocity, mapped to a risk band against the
  production lead time — the key signal for SkyyRose's pre-order/limited-run model ("will this
  drop sell out before we can restock?").
- **Reorder**: a recommended action derived from the sellout band.

Design (mirrors ``services/risk/fraud.py`` / ``services/lifecycle/retention.py``):
deterministic given ``as_of``, never-raises, advisory-only, founder-tunable. An ML time-series
model (ARIMA/Prophet) is a future upgrade behind this same interface.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import IntEnum, StrEnum
from typing import Any

# --------------------------------------------------------------------------- #
# Public types
# --------------------------------------------------------------------------- #


class Trend(StrEnum):
    ACCELERATING = "accelerating"
    STEADY = "steady"
    DECLINING = "declining"
    NO_DATA = "no_data"


class SelloutRisk(IntEnum):
    NONE = 0  # no inventory data or nothing selling
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4  # sells out before the next restock can arrive


@dataclass(frozen=True)
class DemandForecast:
    """Forecast for one product. Immutable, JSON-serializable."""

    sku: str | None
    daily_velocity: float  # units/day over the trailing window
    trend: Trend
    forecast_units_30d: int
    days_to_sellout: float | None
    sellout_risk: SelloutRisk
    recommended_action: str
    is_preorder: bool

    def forecast_units(self, horizon_days: int) -> int:
        """Projected units sold over ``horizon_days`` at the current velocity."""
        return int(round(self.daily_velocity * max(0, horizon_days)))

    def as_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "daily_velocity": self.daily_velocity,
            "trend": self.trend.name,
            "forecast_units_30d": self.forecast_units_30d,
            "days_to_sellout": self.days_to_sellout,
            "sellout_risk": self.sellout_risk.name,
            "recommended_action": self.recommended_action,
            "is_preorder": self.is_preorder,
        }


_ACTION_BY_RISK: dict[SelloutRisk, str] = {
    SelloutRisk.NONE: "no_action",
    SelloutRisk.LOW: "no_action",
    SelloutRisk.MEDIUM: "monitor",
    SelloutRisk.HIGH: "reorder_soon",
    SelloutRisk.CRITICAL: "reorder_now",
}


# --------------------------------------------------------------------------- #
# Defensive helpers (never raise)
# --------------------------------------------------------------------------- #


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        try:
            result = float(value.strip())
        except (ValueError, AttributeError):
            return None
    else:
        return None
    return result if math.isfinite(result) else None


def _parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
    if not isinstance(value, str):
        return None
    raw = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def _units(entry: dict) -> float:
    val = _to_float(entry.get("units"))
    if val is None:
        val = _to_float(entry.get("quantity"))
    return val if val is not None and val >= 0 else 0.0


def _entry_date(entry: dict) -> datetime | None:
    return _parse_dt(entry.get("date")) or _parse_dt(entry.get("date_created"))


# --------------------------------------------------------------------------- #
# Forecaster
# --------------------------------------------------------------------------- #


class DemandForecaster:
    """Forecast demand and sellout risk from a product's sales history (read-only, advisory)."""

    def __init__(
        self,
        *,
        window_days: int = 14,
        baseline_days: int | None = None,  # prior window length for trend; defaults to window
        lead_time_days: int = 14,  # production/restock lead time
        sellout_horizon_days: int = 30,
        accel_ratio: float = 1.15,
        decline_ratio: float = 0.85,
    ) -> None:
        self.window_days = max(1, window_days)
        self.baseline_days = max(
            1, baseline_days if baseline_days is not None else self.window_days
        )
        self.lead_time_days = lead_time_days
        self.sellout_horizon_days = sellout_horizon_days
        self.accel_ratio = accel_ratio
        self.decline_ratio = decline_ratio

    def forecast(self, product: dict[str, Any], *, as_of: datetime | None = None) -> DemandForecast:
        """Return a :class:`DemandForecast` for ``product``. Never raises."""
        now = as_of or datetime.now(UTC)
        if not isinstance(product, dict):
            return self._empty(None, False)

        sku = product.get("sku")
        sku_str = str(sku) if sku is not None else None
        is_preorder = bool(product.get("is_preorder", False))

        try:
            recent_units, prior_units = self._windowed_units(product, now)
        except Exception:
            return self._empty(sku_str, is_preorder)

        velocity = recent_units / self.window_days
        prior_velocity = prior_units / self.baseline_days
        trend = self._trend(recent_units, prior_units, velocity, prior_velocity)

        inventory = self._inventory(product)
        days_to_sellout = (
            (inventory / velocity) if (inventory is not None and velocity > 0) else None
        )
        risk = self._sellout_risk(days_to_sellout)
        if is_preorder:
            # Pre-orders are made-to-order: strong demand is a GOOD signal, not a reorder
            # emergency. Suppress the sellout alarm so the advisory stays signal, not noise.
            risk = SelloutRisk.NONE

        return DemandForecast(
            sku=sku_str,
            daily_velocity=round(velocity, 4),
            trend=trend,
            forecast_units_30d=int(round(velocity * 30)),
            days_to_sellout=round(days_to_sellout, 2) if days_to_sellout is not None else None,
            sellout_risk=risk,
            recommended_action=_ACTION_BY_RISK[risk],
            is_preorder=is_preorder,
        )

    def _empty(self, sku: str | None, is_preorder: bool) -> DemandForecast:
        return DemandForecast(
            sku=sku,
            daily_velocity=0.0,
            trend=Trend.NO_DATA,
            forecast_units_30d=0,
            days_to_sellout=None,
            sellout_risk=SelloutRisk.NONE,
            recommended_action=_ACTION_BY_RISK[SelloutRisk.NONE],
            is_preorder=is_preorder,
        )

    # -- internals --------------------------------------------------------- #

    def _windowed_units(self, product: dict, now: datetime) -> tuple[float, float]:
        sales = product.get("sales")
        if not isinstance(sales, list):
            return 0.0, 0.0
        recent = prior = 0.0
        recent_edge = self.window_days
        prior_edge = self.window_days + self.baseline_days
        today = now.date()
        for entry in sales:
            if not isinstance(entry, dict):
                continue
            dt = _entry_date(entry)
            if dt is None:
                continue
            recency = (today - dt.date()).days
            if recency < 1:
                continue  # today is a partial day (and future rows) — exclude from the rate
            units = _units(entry)
            if recency <= recent_edge:
                recent += units
            elif recency <= prior_edge:
                prior += units
        return recent, prior

    def _trend(
        self, recent_units: float, prior_units: float, velocity: float, prior_velocity: float
    ) -> Trend:
        if recent_units == 0 and prior_units == 0:
            return Trend.NO_DATA
        if prior_velocity == 0:
            # Reachable only when recent_units > 0 (the both-zero case returned above),
            # so velocity > 0 here — new demand against an empty prior window.
            return Trend.ACCELERATING
        if velocity >= prior_velocity * self.accel_ratio:
            return Trend.ACCELERATING
        if velocity <= prior_velocity * self.decline_ratio:
            return Trend.DECLINING
        return Trend.STEADY

    @staticmethod
    def _inventory(product: dict) -> float | None:
        inv = _to_float(product.get("inventory"))
        if inv is None:
            inv = _to_float(product.get("stock_quantity"))
        return inv if inv is not None and inv >= 0 else None

    def _sellout_risk(self, days_to_sellout: float | None) -> SelloutRisk:
        if days_to_sellout is None:
            return SelloutRisk.NONE
        if days_to_sellout <= self.lead_time_days:
            return SelloutRisk.CRITICAL
        if days_to_sellout <= self.sellout_horizon_days:
            return SelloutRisk.HIGH
        if days_to_sellout <= 2 * self.sellout_horizon_days:
            return SelloutRisk.MEDIUM
        return SelloutRisk.LOW


# --------------------------------------------------------------------------- #
# Reporting
# --------------------------------------------------------------------------- #


def format_forecast(forecast: DemandForecast) -> str:
    """Render a :class:`DemandForecast` as a markdown summary."""
    sellout = "n/a" if forecast.days_to_sellout is None else f"{forecast.days_to_sellout:.1f}d"
    preorder = " (pre-order)" if forecast.is_preorder else ""
    return "\n".join(
        [
            f"## Demand Forecast — {forecast.sku or 'n/a'}{preorder}",
            f"Velocity: **{forecast.daily_velocity:.2f}/day** | Trend: **{forecast.trend.name}** | "
            f"30d projection: **{forecast.forecast_units_30d} units**",
            f"Days to sellout: **{sellout}** | Sellout risk: **{forecast.sellout_risk.name}** | "
            f"Action: **{forecast.recommended_action}**",
        ]
    )


__all__ = [
    "DemandForecast",
    "DemandForecaster",
    "SelloutRisk",
    "Trend",
    "format_forecast",
]
