"""Elite Studio run budget.

Hard ceiling on cumulative paid-API spend within a single pipeline run.
Stages call ``ensure_within_budget(cost_usd)`` before each paid dispatch;
the helper raises ``BudgetExceededError`` to halt the run cleanly.

The studio composes many engines (nano_banana, round-table tournament,
FASHN try-on, refine loops). Without a shared budget anchor, a runaway
refine loop or unhealthy tournament can quietly burn an order of
magnitude past the planned ceiling. This module is the anchor — every
new engine wired into the studio MUST update ``RunBudget`` before its
call.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import ClassVar

DEFAULT_BUDGET_USD = float(os.environ.get("ELITE_STUDIO_BUDGET_USD", "25.0"))


class BudgetExceededError(RuntimeError):
    """Raised when a stage would push cumulative cost past the ceiling.

    The caller is expected to halt the run (returning an error state)
    rather than retry the stage with a smaller payload — payload size
    is an upstream input, not a stage-local knob.
    """


@dataclass
class RunBudget:
    """Per-run cumulative cost tracker.

    Thread-safe. ``spend`` and ``check`` use a single re-entrant lock so
    concurrent stages cannot race past the ceiling.
    """

    ceiling_usd: float = DEFAULT_BUDGET_USD
    spent_usd: float = 0.0
    by_stage: dict[str, float] = field(default_factory=dict)
    _lock: ClassVar = threading.RLock()

    def remaining(self) -> float:
        with self._lock:
            return max(0.0, self.ceiling_usd - self.spent_usd)

    def ensure_within_budget(self, cost_usd: float, stage: str = "unknown") -> None:
        """Reject the next spend if it would breach the ceiling.

        Does NOT increment — the caller increments via ``spend`` after the
        paid call succeeds. This lets us refund partial failures without
        bookkeeping gymnastics.
        """
        if cost_usd < 0:
            raise ValueError(f"negative cost rejected: {cost_usd}")
        with self._lock:
            projected = self.spent_usd + cost_usd
            if projected > self.ceiling_usd:
                raise BudgetExceededError(
                    f"stage={stage!r} would push run to ${projected:.2f}, "
                    f"ceiling=${self.ceiling_usd:.2f} (spent so far=${self.spent_usd:.2f})"
                )

    def spend(self, cost_usd: float, stage: str = "unknown") -> None:
        """Record cost AFTER the paid call returned. Skip on zero."""
        if cost_usd <= 0:
            return
        with self._lock:
            self.spent_usd += cost_usd
            self.by_stage[stage] = self.by_stage.get(stage, 0.0) + cost_usd

    def snapshot(self) -> dict:
        """Frozen view for telemetry export."""
        with self._lock:
            return {
                "ceiling_usd": round(self.ceiling_usd, 4),
                "spent_usd": round(self.spent_usd, 4),
                "remaining_usd": round(self.remaining(), 4),
                "by_stage": {k: round(v, 4) for k, v in self.by_stage.items()},
            }


__all__ = ["RunBudget", "BudgetExceededError", "DEFAULT_BUDGET_USD"]
