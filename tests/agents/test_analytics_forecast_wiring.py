"""Wiring tests: analytics_agent forecast/segment now fall back to the deterministic cores
instead of returning the old ``{"error": "ML module not available"}`` dead end.

The agent is constructed via ``__new__`` to bypass heavy LLM/config init — these tests target
only the fallback branches, which depend solely on ``self.ml_module`` being None.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from agents.analytics_agent import AnalyticsAgent

NOW = datetime.now(UTC)


def _agent_without_ml() -> AnalyticsAgent:
    inst = AnalyticsAgent.__new__(AnalyticsAgent)
    inst.ml_module = None  # type: ignore[attr-defined]
    return inst


@pytest.mark.asyncio
async def test_forecast_sales_uses_deterministic_fallback():
    sales = [
        {"date": (NOW - timedelta(days=d)).date().isoformat(), "units": 2} for d in range(1, 15)
    ]
    product = {"sku": "br-001", "sales": sales, "inventory": 20}
    res = await _agent_without_ml().forecast_sales(product=product)

    assert res["method"] == "deterministic_velocity"
    assert res["sku"] == "br-001"
    assert res["daily_velocity"] > 0
    assert "sellout_risk" in res
    assert "error" not in res


@pytest.mark.asyncio
async def test_forecast_sales_no_data_is_graceful_not_error():
    res = await _agent_without_ml().forecast_sales()
    assert res["forecast"] is None
    assert "note" in res
    assert "error" not in res


@pytest.mark.asyncio
async def test_segment_customers_uses_deterministic_rfm():
    customers = [
        {
            "id": 1,
            "orders": [
                {"date_created": (NOW - timedelta(days=400)).date().isoformat(), "total": "120"}
            ],
        },
        {
            "id": 2,
            "orders": [
                {"date_created": (NOW - timedelta(days=5)).date().isoformat(), "total": "300"}
            ],
        },
    ]
    res = await _agent_without_ml().segment_customers(customers=customers)
    assert res["engine"] == "deterministic_rfm"
    assert len(res["segments"]) == 2
    assert sum(res["segment_counts"].values()) == 2
    assert "error" not in res


@pytest.mark.asyncio
async def test_segment_customers_no_data_is_graceful():
    res = await _agent_without_ml().segment_customers()
    assert res["segments"] == []
    assert "note" in res
    assert "error" not in res


@pytest.mark.asyncio
async def test_segment_customers_deterministic_with_as_of():
    customers = [
        {"id": 1, "orders": [{"date_created": "2026-03-01T00:00:00", "total": "120"}]},
    ]
    a = await _agent_without_ml().segment_customers(customers=customers, as_of=NOW)
    b = await _agent_without_ml().segment_customers(customers=customers, as_of=NOW)
    assert a == b


@pytest.mark.asyncio
async def test_segment_customers_rejects_non_rfm_method():
    customers = [{"id": 1, "orders": []}]
    res = await _agent_without_ml().segment_customers(method="behavioral", customers=customers)
    assert res["segments"] == []
    assert "note" in res
    assert "error" not in res


@pytest.mark.asyncio
async def test_forecast_sales_deterministic_with_as_of():
    sales = [
        {"date": (NOW - timedelta(days=d)).date().isoformat(), "units": 2} for d in range(1, 15)
    ]
    product = {"sku": "br-001", "sales": sales, "inventory": 20}
    a = await _agent_without_ml().forecast_sales(product=product, as_of=NOW)
    b = await _agent_without_ml().forecast_sales(product=product, as_of=NOW)
    assert a == b
