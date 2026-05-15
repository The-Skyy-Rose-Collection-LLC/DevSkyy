"""AOS HealthCheck — snapshot aggregator for kernel subsystem state."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol


class HealthStatus(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass(frozen=True)
class SubsystemHealth:
    name: str
    status: HealthStatus
    details: dict[str, Any]


@dataclass(frozen=True)
class HealthSnapshot:
    overall: HealthStatus
    subsystems: tuple[SubsystemHealth, ...]
    captured_at: float


class _KernelHealthSource(Protocol):
    """Structural protocol — any object with these attributes satisfies it."""

    _booted: bool

    @property
    def processes(self) -> Any: ...

    @property
    def budget(self) -> Any: ...

    @property
    def modules(self) -> Any: ...

    @property
    def bus(self) -> Any: ...

    _breakers: dict[str, Any]


class HealthCheck:
    """Reads live kernel subsystem state and produces a HealthSnapshot.

    Accepts any object that satisfies the _KernelHealthSource protocol,
    avoiding a direct Kernel import and the circular dependency it would create.

    Usage::

        checker = HealthCheck(kernel)
        snap = checker.check()
        print(snap.overall)  # HealthStatus.OK | DEGRADED | DOWN
    """

    def __init__(self, kernel: _KernelHealthSource) -> None:
        self._kernel = kernel

    def check(self) -> HealthSnapshot:
        """Produce a health snapshot from the current kernel state."""
        subsystems: list[SubsystemHealth] = []

        subsystems.append(self._check_boot())
        subsystems.append(self._check_budget())
        subsystems.append(self._check_processes())
        subsystems.append(self._check_modules())
        subsystems.append(self._check_circuit_breakers())

        statuses = [s.status for s in subsystems]
        if HealthStatus.DOWN in statuses:
            overall = HealthStatus.DOWN
        elif HealthStatus.DEGRADED in statuses:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.OK

        return HealthSnapshot(
            overall=overall,
            subsystems=tuple(subsystems),
            captured_at=time.time(),
        )

    # ---------------------------------------------------------------- private

    def _check_boot(self) -> SubsystemHealth:
        booted = getattr(self._kernel, "_booted", False)
        return SubsystemHealth(
            name="kernel",
            status=HealthStatus.OK if booted else HealthStatus.DOWN,
            details={"booted": booted},
        )

    def _check_budget(self) -> SubsystemHealth:
        budget = self._kernel.budget
        remaining = getattr(budget, "system_remaining_usd", None)
        limit = getattr(budget, "system_budget_usd", None)
        if remaining is None:
            return SubsystemHealth(
                name="budget", status=HealthStatus.DEGRADED, details={"error": "unreadable"}
            )
        pct = (remaining / limit * 100) if limit else 0.0
        status = HealthStatus.OK if pct > 20 else HealthStatus.DEGRADED
        return SubsystemHealth(
            name="budget",
            status=status,
            details={
                "remaining_usd": remaining,
                "limit_usd": limit,
                "remaining_pct": round(pct, 1),
            },
        )

    def _check_processes(self) -> SubsystemHealth:
        pm = self._kernel.processes
        count = len(getattr(pm, "_processes", {}))
        return SubsystemHealth(
            name="process_manager",
            status=HealthStatus.OK,
            details={"process_count": count},
        )

    def _check_modules(self) -> SubsystemHealth:
        registry = self._kernel.modules
        loaded = len(getattr(registry, "_manifests", {}))
        registered = len(getattr(registry, "_factories", {}))
        return SubsystemHealth(
            name="module_registry",
            status=HealthStatus.OK,
            details={"loaded_modules": loaded, "registered_types": registered},
        )

    def _check_circuit_breakers(self) -> SubsystemHealth:
        breakers = getattr(self._kernel, "_breakers", {})
        open_names = [
            name for name, cb in breakers.items() if str(getattr(cb, "state", "")) == "open"
        ]
        status = HealthStatus.DEGRADED if open_names else HealthStatus.OK
        return SubsystemHealth(
            name="circuit_breakers",
            status=status,
            details={"total": len(breakers), "open": open_names},
        )
