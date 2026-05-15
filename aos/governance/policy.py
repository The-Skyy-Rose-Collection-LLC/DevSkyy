"""PolicyEngine — declarative ALLOW/DENY/REQUIRE_APPROVAL rules for kernel actions.

Rules are evaluated against an ActionDescriptor (a flat dict of action attrs).
Precedence: explicit DENY > REQUIRE_APPROVAL > ALLOW. First matching rule wins
within each precedence tier; otherwise the default verdict applies.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PolicyVerdict(StrEnum):
    """Outcome of a policy evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


_PRECEDENCE: dict[PolicyVerdict, int] = {
    PolicyVerdict.DENY: 3,
    PolicyVerdict.REQUIRE_APPROVAL: 2,
    PolicyVerdict.ALLOW: 1,
}


class PolicyRule(BaseModel):
    """A single ALLOW/DENY/REQUIRE_APPROVAL rule with a flat-match condition."""

    model_config = {"frozen": True}

    name: str
    verdict: PolicyVerdict
    match: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""

    def matches(self, descriptor: Mapping[str, Any]) -> bool:
        """True when every key in self.match is present and equal in descriptor."""
        for key, expected in self.match.items():
            if descriptor.get(key) != expected:
                return False
        return True


class PolicyDecision(BaseModel):
    """The evaluated result for an action."""

    model_config = {"frozen": True}

    verdict: PolicyVerdict
    matched_rule: str | None = None
    reason: str = ""


class PolicyEngine:
    """In-memory rule evaluator.

    Rules can be added at runtime. evaluate() picks the highest-precedence
    matching rule. With no matching rule, the default_verdict applies.
    """

    def __init__(
        self,
        *,
        default_verdict: PolicyVerdict = PolicyVerdict.ALLOW,
    ) -> None:
        self._rules: list[PolicyRule] = []
        self._default = default_verdict

    @property
    def rules(self) -> tuple[PolicyRule, ...]:
        """Read-only snapshot of registered rules."""
        return tuple(self._rules)

    def add_rule(self, rule: PolicyRule) -> None:
        """Register a new rule. Order does not affect precedence."""
        self._rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        """Remove the first rule with the given name. Returns True if removed."""
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                return True
        return False

    def evaluate(self, descriptor: Mapping[str, Any]) -> PolicyDecision:
        """Evaluate the action descriptor against all rules.

        Returns the highest-precedence matching verdict. Defaults to ALLOW (or
        the configured default) when no rule matches.
        """
        best: PolicyRule | None = None
        for rule in self._rules:
            if not rule.matches(descriptor):
                continue
            if best is None or _PRECEDENCE[rule.verdict] > _PRECEDENCE[best.verdict]:
                best = rule

        if best is None:
            return PolicyDecision(verdict=self._default, reason="no matching rule")
        return PolicyDecision(
            verdict=best.verdict,
            matched_rule=best.name,
            reason=best.reason or f"matched rule {best.name}",
        )
