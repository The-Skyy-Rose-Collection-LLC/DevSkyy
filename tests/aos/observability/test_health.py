"""Tests for HealthCheck."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from aos.healing.circuit_breaker import CircuitBreaker, CircuitState
from aos.observability.health import HealthCheck, HealthSnapshot, HealthStatus


def _make_kernel(
    *,
    booted: bool = True,
    remaining_usd: float = 80.0,
    budget_usd: float = 100.0,
    process_count: int = 0,
    loaded_modules: int = 0,
    registered_types: int = 0,
    breakers: dict | None = None,
) -> SimpleNamespace:
    budget = SimpleNamespace(
        system_remaining_usd=remaining_usd,
        system_budget_usd=budget_usd,
    )
    processes = SimpleNamespace(_processes={f"p{i}": None for i in range(process_count)})
    modules = SimpleNamespace(
        _manifests={f"m{i}": None for i in range(loaded_modules)},
        _factories={f"f{i}": None for i in range(registered_types)},
    )
    return SimpleNamespace(
        _booted=booted,
        budget=budget,
        processes=processes,
        modules=modules,
        bus=SimpleNamespace(),
        _breakers=breakers if breakers is not None else {},
    )


class TestBootSubsystem:
    def test_ok_when_booted(self):
        k = _make_kernel(booted=True)
        snap = HealthCheck(k).check()
        boot = next(s for s in snap.subsystems if s.name == "kernel")
        assert boot.status == HealthStatus.OK
        assert boot.details["booted"] is True

    def test_down_when_not_booted(self):
        k = _make_kernel(booted=False)
        snap = HealthCheck(k).check()
        boot = next(s for s in snap.subsystems if s.name == "kernel")
        assert boot.status == HealthStatus.DOWN


class TestBudgetSubsystem:
    def test_ok_above_20_pct(self):
        k = _make_kernel(remaining_usd=80.0, budget_usd=100.0)
        snap = HealthCheck(k).check()
        budget = next(s for s in snap.subsystems if s.name == "budget")
        assert budget.status == HealthStatus.OK
        assert budget.details["remaining_pct"] == 80.0

    def test_degraded_at_or_below_20_pct(self):
        k = _make_kernel(remaining_usd=20.0, budget_usd=100.0)
        snap = HealthCheck(k).check()
        budget = next(s for s in snap.subsystems if s.name == "budget")
        assert budget.status == HealthStatus.DEGRADED

    def test_degraded_when_remaining_unreadable(self):
        k = _make_kernel()
        del k.budget.system_remaining_usd
        snap = HealthCheck(k).check()
        budget = next(s for s in snap.subsystems if s.name == "budget")
        assert budget.status == HealthStatus.DEGRADED
        assert budget.details["error"] == "unreadable"

    def test_details_include_remaining_and_limit(self):
        k = _make_kernel(remaining_usd=55.0, budget_usd=100.0)
        snap = HealthCheck(k).check()
        budget = next(s for s in snap.subsystems if s.name == "budget")
        assert budget.details["remaining_usd"] == 55.0
        assert budget.details["limit_usd"] == 100.0


class TestProcessSubsystem:
    def test_ok_with_no_processes(self):
        k = _make_kernel(process_count=0)
        snap = HealthCheck(k).check()
        pm = next(s for s in snap.subsystems if s.name == "process_manager")
        assert pm.status == HealthStatus.OK
        assert pm.details["process_count"] == 0

    def test_reports_process_count(self):
        k = _make_kernel(process_count=5)
        snap = HealthCheck(k).check()
        pm = next(s for s in snap.subsystems if s.name == "process_manager")
        assert pm.details["process_count"] == 5


class TestModuleSubsystem:
    def test_reports_loaded_and_registered(self):
        k = _make_kernel(loaded_modules=3, registered_types=2)
        snap = HealthCheck(k).check()
        reg = next(s for s in snap.subsystems if s.name == "module_registry")
        assert reg.details["loaded_modules"] == 3
        assert reg.details["registered_types"] == 2
        assert reg.status == HealthStatus.OK


class TestCircuitBreakersSubsystem:
    def test_ok_with_no_breakers(self):
        k = _make_kernel(breakers={})
        snap = HealthCheck(k).check()
        cb = next(s for s in snap.subsystems if s.name == "circuit_breakers")
        assert cb.status == HealthStatus.OK
        assert cb.details["total"] == 0

    def test_ok_when_all_breakers_closed(self):
        breaker = CircuitBreaker(failure_threshold=3)
        k = _make_kernel(breakers={"spawn": breaker})
        snap = HealthCheck(k).check()
        cb = next(s for s in snap.subsystems if s.name == "circuit_breakers")
        assert cb.status == HealthStatus.OK
        assert cb.details["open"] == []

    def test_degraded_when_breaker_open(self):
        breaker = MagicMock()
        breaker.state = CircuitState.OPEN
        k = _make_kernel(breakers={"spawn": breaker})
        snap = HealthCheck(k).check()
        cb = next(s for s in snap.subsystems if s.name == "circuit_breakers")
        assert cb.status == HealthStatus.DEGRADED
        assert "spawn" in cb.details["open"]

    def test_reports_correct_total(self):
        b1, b2 = MagicMock(), MagicMock()
        b1.state = CircuitState.CLOSED
        b2.state = CircuitState.OPEN
        k = _make_kernel(breakers={"a": b1, "b": b2})
        snap = HealthCheck(k).check()
        cb = next(s for s in snap.subsystems if s.name == "circuit_breakers")
        assert cb.details["total"] == 2
        assert cb.details["open"] == ["b"]


class TestOverallStatus:
    def test_overall_ok_when_all_subsystems_ok(self):
        k = _make_kernel()
        snap = HealthCheck(k).check()
        assert snap.overall == HealthStatus.OK

    def test_overall_down_when_kernel_not_booted(self):
        k = _make_kernel(booted=False)
        snap = HealthCheck(k).check()
        assert snap.overall == HealthStatus.DOWN

    def test_overall_degraded_when_budget_low(self):
        k = _make_kernel(remaining_usd=10.0, budget_usd=100.0)
        snap = HealthCheck(k).check()
        assert snap.overall == HealthStatus.DEGRADED

    def test_overall_down_beats_degraded(self):
        breaker = MagicMock()
        breaker.state = CircuitState.OPEN
        k = _make_kernel(
            booted=False, remaining_usd=10.0, budget_usd=100.0, breakers={"x": breaker}
        )
        snap = HealthCheck(k).check()
        assert snap.overall == HealthStatus.DOWN


class TestSnapshot:
    def test_snapshot_has_captured_at(self):
        k = _make_kernel()
        snap = HealthCheck(k).check()
        assert isinstance(snap, HealthSnapshot)
        assert snap.captured_at > 0

    def test_snapshot_has_five_subsystems(self):
        k = _make_kernel()
        snap = HealthCheck(k).check()
        assert len(snap.subsystems) == 5
