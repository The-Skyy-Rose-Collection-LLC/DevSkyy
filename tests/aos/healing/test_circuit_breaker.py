"""Tests for CircuitBreaker state machine."""

from __future__ import annotations

from aos.healing.circuit_breaker import CircuitBreaker, CircuitState


def _make_breaker(
    failure_threshold: int = 3,
    recovery_timeout_seconds: float = 30.0,
    start_time: float = 0.0,
) -> tuple[CircuitBreaker, list[float]]:
    clock: list[float] = [start_time]
    cb = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout_seconds=recovery_timeout_seconds,
        time_fn=lambda: clock[0],
    )
    return cb, clock


def test_initial_state_is_closed() -> None:
    cb, _ = _make_breaker()
    assert cb.state == CircuitState.CLOSED


def test_closed_allows_requests() -> None:
    cb, _ = _make_breaker()
    assert cb.allow_request() is True


def test_failures_below_threshold_stay_closed() -> None:
    cb, _ = _make_breaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    assert cb.allow_request() is True


def test_threshold_failures_open_circuit() -> None:
    cb, _ = _make_breaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN


def test_open_circuit_blocks_requests() -> None:
    cb, _ = _make_breaker(failure_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.allow_request() is False


def test_open_does_not_allow_before_timeout() -> None:
    cb, clock = _make_breaker(failure_threshold=2, recovery_timeout_seconds=30.0, start_time=0.0)
    cb.record_failure()
    cb.record_failure()
    clock[0] = 29.9
    assert cb.allow_request() is False
    assert cb.state == CircuitState.OPEN


def test_open_transitions_to_half_open_after_timeout() -> None:
    cb, clock = _make_breaker(failure_threshold=2, recovery_timeout_seconds=30.0, start_time=0.0)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    clock[0] = 31.0
    assert cb.allow_request() is True
    assert cb.state == CircuitState.HALF_OPEN


def test_half_open_allows_probe_request() -> None:
    cb, clock = _make_breaker(failure_threshold=2, recovery_timeout_seconds=30.0, start_time=0.0)
    cb.record_failure()
    cb.record_failure()
    clock[0] = 31.0
    assert cb.allow_request() is True


def test_half_open_success_closes_circuit() -> None:
    cb, clock = _make_breaker(failure_threshold=2, recovery_timeout_seconds=30.0, start_time=0.0)
    cb.record_failure()
    cb.record_failure()
    clock[0] = 31.0
    cb.allow_request()  # transitions to HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED


def test_half_open_failure_reopens_circuit() -> None:
    cb, clock = _make_breaker(failure_threshold=2, recovery_timeout_seconds=30.0, start_time=0.0)
    cb.record_failure()
    cb.record_failure()
    clock[0] = 31.0
    cb.allow_request()  # transitions to HALF_OPEN
    cb.record_failure()
    assert cb.state == CircuitState.OPEN


def test_success_resets_failure_count_so_threshold_applies_fresh() -> None:
    cb, _ = _make_breaker(failure_threshold=3)
    cb.record_failure()
    cb.record_failure()
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED


def test_single_failure_threshold() -> None:
    cb, _ = _make_breaker(failure_threshold=1)
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
