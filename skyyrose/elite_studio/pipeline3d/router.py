"""Provider router: choose an adapter per stage by capability, priority, availability.

On stage failure the executor can call ``pick(stage, exclude=...)`` to fall back
to the next capable adapter (artifact handoff). This is the single place that
knows which engine runs which stage.
"""

from __future__ import annotations

from .adapters.base import Adapter
from .models import Stage


class NoAdapterError(RuntimeError):
    """No available, capable adapter exists for the requested stage."""


class Router:
    """Selects adapters for stages by priority order."""

    def __init__(self, adapters: list[Adapter], priority: list[str] | None = None) -> None:
        self._adapters = list(adapters)
        self._priority = priority or [a.name for a in adapters]

    def _ordered(self) -> list[Adapter]:
        idx = {name: i for i, name in enumerate(self._priority)}
        return sorted(self._adapters, key=lambda a: idx.get(a.name, len(idx) + 1))

    def supporting(self, stage: Stage) -> list[Adapter]:
        """All adapters that CAN run a stage, in priority order (ignores availability).

        Used for cost ESTIMATION — the dry-run should price the intended engine
        whether or not its API key is currently loaded.
        """
        return [a for a in self._ordered() if a.supports(stage)]

    def candidates(self, stage: Stage) -> list[Adapter]:
        """All available, capable adapters for a stage, in priority order.

        Used for actual DISPATCH — an adapter without its key is skipped here.
        """
        return [a for a in self._ordered() if a.supports(stage) and a.available()]

    def pick(self, stage: Stage, *, exclude: set[str] | None = None) -> Adapter:
        """Highest-priority available adapter for a stage, skipping ``exclude``."""
        skip = exclude or set()
        for adapter in self.candidates(stage):
            if adapter.name not in skip:
                return adapter
        raise NoAdapterError(f"no available adapter for stage={stage.value!r}")


__all__ = ["Router", "NoAdapterError"]
