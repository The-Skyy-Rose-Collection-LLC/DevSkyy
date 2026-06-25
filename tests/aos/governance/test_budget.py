"""Tests for BudgetController."""

from __future__ import annotations

import pytest

from aos.governance.budget import BudgetController, BudgetVerdict


@pytest.fixture
def bc() -> BudgetController:
    return BudgetController(system_budget_usd=10.0, warning_threshold=0.8)


class TestCheck:
    @pytest.mark.asyncio
    async def test_allow_within_budget(self, bc: BudgetController):
        d = await bc.check(process_budget_usd=5.0, process_spent_usd=1.0, projected_cost_usd=0.5)
        assert d.verdict == BudgetVerdict.ALLOW

    @pytest.mark.asyncio
    async def test_warn_crossing_threshold(self, bc: BudgetController):
        d = await bc.check(process_budget_usd=5.0, process_spent_usd=3.5, projected_cost_usd=1.0)
        assert d.verdict == BudgetVerdict.WARN

    @pytest.mark.asyncio
    async def test_deny_over_process_budget(self, bc: BudgetController):
        d = await bc.check(process_budget_usd=5.0, process_spent_usd=4.5, projected_cost_usd=1.0)
        assert d.verdict == BudgetVerdict.DENY
        assert "Process budget" in d.reason

    @pytest.mark.asyncio
    async def test_deny_over_system_budget(self, bc: BudgetController):
        await bc.record(9.5)
        d = await bc.check(process_budget_usd=100.0, process_spent_usd=0.0, projected_cost_usd=1.0)
        assert d.verdict == BudgetVerdict.DENY
        assert "System budget" in d.reason


class TestRecord:
    @pytest.mark.asyncio
    async def test_record_accumulates(self, bc: BudgetController):
        await bc.record(1.5)
        await bc.record(2.0)
        assert bc.system_spent_usd == 3.5
        assert bc.system_remaining_usd == 6.5

    @pytest.mark.asyncio
    async def test_reset(self, bc: BudgetController):
        await bc.record(5.0)
        await bc.reset()
        assert bc.system_spent_usd == 0.0


class TestConfig:
    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError, match="warning_threshold"):
            BudgetController(warning_threshold=1.5)
        with pytest.raises(ValueError, match="warning_threshold"):
            BudgetController(warning_threshold=0.0)
