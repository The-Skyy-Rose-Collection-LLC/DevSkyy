"""BudgetController — per-process and system-wide spend tracking + guards."""

from __future__ import annotations

import asyncio
from enum import StrEnum

from pydantic import BaseModel


class BudgetVerdict(StrEnum):
    """Result of a budget check."""

    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"


class BudgetDecision(BaseModel):
    """Verdict on a proposed expense."""

    model_config = {"frozen": True}

    verdict: BudgetVerdict
    reason: str
    projected_spend_usd: float
    limit_usd: float


class BudgetController:
    """Tracks system-wide spend + arbitrates per-process expenses.

    Per-process budgets live in AgentProcess.budget_usd / spent_usd.
    This controller adds:
      - system_budget_usd: hard ceiling across all processes
      - warning_threshold: 0.0-1.0 of process budget that triggers WARN
    """

    def __init__(
        self,
        *,
        system_budget_usd: float = 100.0,
        warning_threshold: float = 0.8,
    ) -> None:
        if not 0.0 < warning_threshold <= 1.0:
            msg = "warning_threshold must be in (0.0, 1.0]"
            raise ValueError(msg)
        self.system_budget_usd = system_budget_usd
        self.warning_threshold = warning_threshold
        self._system_spent_usd = 0.0
        self._lock = asyncio.Lock()

    @property
    def system_spent_usd(self) -> float:
        """Cumulative system-wide spend so far."""
        return self._system_spent_usd

    @property
    def system_remaining_usd(self) -> float:
        """How much of the system budget is left."""
        return max(0.0, self.system_budget_usd - self._system_spent_usd)

    async def check(
        self,
        *,
        process_budget_usd: float,
        process_spent_usd: float,
        projected_cost_usd: float,
    ) -> BudgetDecision:
        """Decide whether a process may incur projected_cost.

        Returns DENY if either the process or system budget would be exceeded.
        Returns WARN if the process would cross its warning threshold.
        """
        new_process_total = process_spent_usd + projected_cost_usd
        new_system_total = self._system_spent_usd + projected_cost_usd

        if new_process_total > process_budget_usd:
            return BudgetDecision(
                verdict=BudgetVerdict.DENY,
                reason=(
                    f"Process budget exceeded: ${new_process_total:.4f} > ${process_budget_usd:.4f}"
                ),
                projected_spend_usd=new_process_total,
                limit_usd=process_budget_usd,
            )
        if new_system_total > self.system_budget_usd:
            return BudgetDecision(
                verdict=BudgetVerdict.DENY,
                reason=(
                    f"System budget exceeded: "
                    f"${new_system_total:.4f} > ${self.system_budget_usd:.4f}"
                ),
                projected_spend_usd=new_system_total,
                limit_usd=self.system_budget_usd,
            )
        if new_process_total > process_budget_usd * self.warning_threshold:
            return BudgetDecision(
                verdict=BudgetVerdict.WARN,
                reason=(f"Process at {new_process_total / process_budget_usd:.0%} of budget"),
                projected_spend_usd=new_process_total,
                limit_usd=process_budget_usd,
            )
        return BudgetDecision(
            verdict=BudgetVerdict.ALLOW,
            reason="within budget",
            projected_spend_usd=new_process_total,
            limit_usd=process_budget_usd,
        )

    async def record(self, amount_usd: float) -> None:
        """Commit a spend amount to the system total."""
        async with self._lock:
            self._system_spent_usd += amount_usd

    async def reset(self) -> None:
        """Reset the system-spent counter (e.g., for daily rollover)."""
        async with self._lock:
            self._system_spent_usd = 0.0
