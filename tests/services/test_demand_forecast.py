"""Tests for services.forecasting.demand — deterministic velocity/sellout forecaster.

Contract: deterministic given ``as_of``, never-raises, advisory.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest
from services.forecasting.demand import (
    DemandForecast,
    DemandForecaster,
    SelloutRisk,
    Trend,
    format_forecast,
)

AS_OF = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)


def _daily(units_per_day, start_day, end_day):
    """Sale entries for each day in [start_day, end_day] before AS_OF."""
    out = []
    for d in range(start_day, end_day + 1):
        date = (AS_OF - timedelta(days=d)).date().isoformat()
        out.append({"date": date, "units": units_per_day})
    return out


def _product(sales, **fields):
    p = {"sku": "br-001", "sales": sales}
    p.update(fields)
    return p


# --------------------------------------------------------------------------- #
# Velocity + trend
# --------------------------------------------------------------------------- #


def test_steady_velocity_and_trend():
    sales = _daily(2, 1, 28)  # 2/day for 28 days
    f = DemandForecaster().forecast(_product(sales), as_of=AS_OF)
    assert isinstance(f, DemandForecast)
    assert f.daily_velocity == pytest.approx(2.0)
    assert f.trend is Trend.STEADY
    assert f.forecast_units_30d == 60


def test_accelerating_trend():
    sales = _daily(4, 1, 14) + _daily(2, 15, 28)  # recent hotter than prior
    f = DemandForecaster().forecast(_product(sales), as_of=AS_OF)
    assert f.trend is Trend.ACCELERATING
    assert f.daily_velocity == pytest.approx(4.0)


def test_declining_trend():
    sales = _daily(1, 1, 14) + _daily(3, 15, 28)
    f = DemandForecaster().forecast(_product(sales), as_of=AS_OF)
    assert f.trend is Trend.DECLINING


def test_no_sales_is_no_data():
    f = DemandForecaster().forecast(_product([]), as_of=AS_OF)
    assert f.trend is Trend.NO_DATA
    assert f.daily_velocity == 0.0
    assert f.sellout_risk is SelloutRisk.NONE
    assert f.recommended_action == "no_action"
    assert f.days_to_sellout is None


# --------------------------------------------------------------------------- #
# Sellout + reorder
# --------------------------------------------------------------------------- #


def test_days_to_sellout_computed():
    sales = _daily(2, 1, 28)  # velocity 2/day
    f = DemandForecaster().forecast(_product(sales, inventory=20), as_of=AS_OF)
    assert f.days_to_sellout == pytest.approx(10.0)


def test_sellout_critical_when_below_lead_time():
    sales = _daily(2, 1, 28)  # 2/day -> 20 units sells out in 10d < 14d lead time
    f = DemandForecaster(lead_time_days=14).forecast(_product(sales, inventory=20), as_of=AS_OF)
    assert f.sellout_risk is SelloutRisk.CRITICAL
    assert f.recommended_action == "reorder_now"


def test_sellout_low_when_plenty_of_stock():
    sales = _daily(1, 1, 28)  # 1/day, 1000 units -> 1000 days
    f = DemandForecaster().forecast(_product(sales, inventory=1000), as_of=AS_OF)
    assert f.sellout_risk is SelloutRisk.LOW
    assert f.recommended_action == "no_action"


def test_inventory_from_stock_quantity_field():
    sales = _daily(2, 1, 28)
    f = DemandForecaster(lead_time_days=14).forecast(
        _product(sales, stock_quantity=20), as_of=AS_OF
    )
    assert f.days_to_sellout == pytest.approx(10.0)


def test_units_from_quantity_and_date_created_aliases():
    sales = [
        {"date_created": (AS_OF - timedelta(days=d)).date().isoformat(), "quantity": 2}
        for d in range(1, 29)
    ]
    f = DemandForecaster().forecast(_product(sales), as_of=AS_OF)
    assert f.daily_velocity == pytest.approx(2.0)


# --------------------------------------------------------------------------- #
# Robustness
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"sales": None},
        {"sales": "nope"},
        {"sales": [None, "x", {"date": "garbage", "units": "x"}]},
        {"sales": [{"units": 5}]},  # no date
        {"sales": _daily(2, 1, 28), "inventory": "nope"},
        {"sales": _daily(2, 1, 28), "inventory": -5},
    ],
)
def test_never_raises_on_garbage(bad):
    f = DemandForecaster().forecast(bad, as_of=AS_OF)
    assert isinstance(f, DemandForecast)
    assert f.daily_velocity >= 0.0


def test_none_product_does_not_raise():
    f = DemandForecaster().forecast(None, as_of=AS_OF)  # type: ignore[arg-type]
    assert f.trend is Trend.NO_DATA


def test_zero_velocity_no_division_error():
    f = DemandForecaster().forecast(_product([], inventory=50), as_of=AS_OF)
    assert f.days_to_sellout is None
    assert f.sellout_risk is SelloutRisk.NONE


# --------------------------------------------------------------------------- #
# Determinism + immutability + serialization
# --------------------------------------------------------------------------- #


def test_deterministic():
    p = _product(_daily(2, 1, 28), inventory=20)
    assert DemandForecaster().forecast(p, as_of=AS_OF) == DemandForecaster().forecast(
        p, as_of=AS_OF
    )


def test_frozen():
    f = DemandForecaster().forecast(_product([]), as_of=AS_OF)
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.daily_velocity = 9.0  # type: ignore[misc]


def test_as_dict_json_safe():
    import json

    f = DemandForecaster(lead_time_days=14).forecast(
        _product(_daily(2, 1, 28), inventory=20), as_of=AS_OF
    )
    payload = f.as_dict()
    json.dumps(payload)
    assert payload["sku"] == "br-001"
    assert payload["trend"] == f.trend.name
    assert payload["sellout_risk"] == f.sellout_risk.name
    assert payload["recommended_action"] == f.recommended_action


def test_forecast_units_method_arbitrary_horizon():
    f = DemandForecaster().forecast(_product(_daily(2, 1, 28)), as_of=AS_OF)
    assert f.forecast_units(7) == 14
    assert f.forecast_units(0) == 0


# --------------------------------------------------------------------------- #
# Tunability + preorder
# --------------------------------------------------------------------------- #


def test_window_tunable():
    # 5/day only in the last 3 days, nothing before.
    sales = _daily(5, 1, 3)
    wide = DemandForecaster(window_days=28).forecast(_product(sales), as_of=AS_OF)
    narrow = DemandForecaster(window_days=3).forecast(_product(sales), as_of=AS_OF)
    assert narrow.daily_velocity > wide.daily_velocity


def test_preorder_flag_surfaced():
    f = DemandForecaster().forecast(
        _product(_daily(3, 1, 14), is_preorder=True, inventory=80), as_of=AS_OF
    )
    assert f.is_preorder is True


def test_format_renders_markdown():
    f = DemandForecaster(lead_time_days=14).forecast(
        _product(_daily(2, 1, 28), inventory=20), as_of=AS_OF
    )
    text = format_forecast(f)
    assert "Demand Forecast" in text
    assert "br-001" in text


# --------------------------------------------------------------------------- #
# Regression: adversarial-review fixes
# --------------------------------------------------------------------------- #


def test_preorder_suppresses_critical_sellout():
    """Pre-orders are made-to-order — fast sell-through is good, not a reorder emergency."""
    f = DemandForecaster(lead_time_days=14).forecast(
        _product(_daily(2, 1, 28), inventory=2, is_preorder=True), as_of=AS_OF
    )
    assert f.is_preorder is True
    assert f.sellout_risk is SelloutRisk.NONE
    assert f.recommended_action == "no_action"


def test_today_partial_day_excluded_from_velocity():
    # Only today (recency 0) has sales → excluded → velocity 0, NO_DATA.
    sales = [{"date": AS_OF.date().isoformat(), "units": 50}]
    f = DemandForecaster().forecast(_product(sales), as_of=AS_OF)
    assert f.daily_velocity == 0.0
    assert f.trend is Trend.NO_DATA


def test_forecast_units_30d_is_always_30_days():
    f = DemandForecaster(window_days=7).forecast(_product(_daily(2, 1, 28)), as_of=AS_OF)
    assert f.forecast_units_30d == f.forecast_units(30)
    assert f.forecast_units_30d == 60  # velocity 2/day * 30


def test_zero_inventory_active_velocity_is_critical():
    f = DemandForecaster(lead_time_days=14).forecast(
        _product(_daily(2, 1, 28), inventory=0), as_of=AS_OF
    )
    assert f.days_to_sellout == 0.0
    assert f.sellout_risk is SelloutRisk.CRITICAL


def test_parse_dt_accepts_datetime_objects():
    sales = [{"date": AS_OF - timedelta(days=d), "units": 2} for d in range(1, 15)]
    f = DemandForecaster().forecast(_product(sales), as_of=AS_OF)
    assert f.daily_velocity == pytest.approx(2.0)
