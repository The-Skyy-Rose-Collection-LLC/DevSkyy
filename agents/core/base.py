"""
DevSkyy Core Agent Base Classes
================================

Universal self-healing + hierarchical agent architecture.

Promoted from elite_web_builder/core/self_healer.py to serve ALL agents.

Classes:
    SelfHealingMixin — Universal self-healing (every agent inherits this)
    CoreAgent — Base for the 8 domain core agents

Self-Healing Flow:
    1. Agent executes task
    2. Failure detected → diagnose(failure)
    3. heal(diagnosis) → retry with different params (3 attempts)
    4. Still failing → escalate_to_parent() or escalate_to_orchestrator()
    5. Max escalation → Dashboard alert (human decides via 3D portal)

Circuit Breaker:
    CLOSED → normal operation
    OPEN → 5 consecutive failures → stop attempting, alert
    HALF_OPEN → cooldown expired → try one request → close or re-open
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import abstractmethod
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from agents.errors import (
    AgentError,
    ErrorCategory,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class CoreAgentType(StrEnum):
    """All 8 core agent domains + orchestrator."""

    COMMERCE = "commerce"
    CONTENT = "content"
    CREATIVE = "creative"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"
    IMAGERY = "imagery"
    WEB_BUILDER = "web_builder"
    ORCHESTRATOR = "orchestrator"


class FailureCategory(StrEnum):
    """How a failure should be routed for healing."""

    CODE_BUG = "code_bug"
    CONFIG = "config"
    WRONG_APPROACH = "wrong_approach"
    EXTERNAL = "external"
    DATA_QUALITY = "data_quality"
    PROVIDER_DOWN = "provider_down"


class CircuitBreakerState(StrEnum):
    """Circuit breaker states per agent."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing — stop attempting
    HALF_OPEN = "half_open"  # Cooldown expired — testing one request


# =============================================================================
# Data Models
# =============================================================================


@dataclass(frozen=True)
class HealAttempt:
    """Record of a single heal attempt."""

    category: FailureCategory
    description: str
    action_taken: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass(frozen=True)
class Diagnosis:
    """Analysis of what failed and how to fix it."""

    failure_category: FailureCategory
    description: str
    suggested_actions: list[str]
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealResult:
    """Outcome of a single heal attempt."""

    success: bool
    message: str
    changes: list[str] = field(default_factory=list)


@dataclass
class HealCycleResult:
    """Outcome of the entire heal cycle (possibly multiple attempts)."""

    success: bool
    attempts: int
    escalation_needed: bool = False
    history: list[HealResult] = field(default_factory=list)


@dataclass
class HealthStatus:
    """Health check result for an agent."""

    agent_name: str
    agent_type: str
    healthy: bool
    circuit_breaker: str  # CircuitBreakerState value
    consecutive_failures: int
    last_success: str | None = None
    last_failure: str | None = None
    sub_agent_health: dict[str, bool] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Failure Categorization
# =============================================================================

# Keyword patterns → failure category
_CATEGORY_OVERRIDES: list[tuple[str, FailureCategory]] = [
    ("env var", FailureCategory.CONFIG),
    ("missing config", FailureCategory.CONFIG),
    ("file not found", FailureCategory.CONFIG),
    ("api key", FailureCategory.CONFIG),
    ("connection refused", FailureCategory.EXTERNAL),
    ("rate limit", FailureCategory.EXTERNAL),
    ("timeout", FailureCategory.EXTERNAL),
    ("429", FailureCategory.EXTERNAL),
    ("503", FailureCategory.PROVIDER_DOWN),
    ("service unavailable", FailureCategory.PROVIDER_DOWN),
    ("provider", FailureCategory.PROVIDER_DOWN),
    ("corrupt", FailureCategory.DATA_QUALITY),
    ("invalid data", FailureCategory.DATA_QUALITY),
    ("schema", FailureCategory.DATA_QUALITY),
    ("approach", FailureCategory.WRONG_APPROACH),
    ("redesign", FailureCategory.WRONG_APPROACH),
    ("architectural", FailureCategory.WRONG_APPROACH),
]


def categorize_failure(error: Exception | str) -> FailureCategory:
    """Categorize a failure for routing to the right fix strategy."""
    msg = str(error).lower()

    for keyword, category in _CATEGORY_OVERRIDES:
        if keyword in msg:
            return category

    # Map AgentError categories
    if isinstance(error, AgentError):
        mapping = {
            ErrorCategory.CONFIGURATION: FailureCategory.CONFIG,
            ErrorCategory.AUTHENTICATION: FailureCategory.CONFIG,
            ErrorCategory.NETWORK: FailureCategory.EXTERNAL,
            ErrorCategory.TIMEOUT: FailureCategory.EXTERNAL,
            ErrorCategory.RESOURCE: FailureCategory.EXTERNAL,
            ErrorCategory.DATA: FailureCategory.DATA_QUALITY,
            ErrorCategory.VALIDATION: FailureCategory.DATA_QUALITY,
        }
        return mapping.get(error.category, FailureCategory.CODE_BUG)

    return FailureCategory.CODE_BUG


# =============================================================================
# SelfHealingMixin — Universal, every agent inherits this
# =============================================================================


class SelfHealingMixin:
    """
    Universal self-healing capability for all DevSkyy agents.

    Provides:
    - diagnose(error) → Diagnosis with categorized failure + suggested actions
    - heal(diagnosis) → HealCycleResult with retry logic
    - health_check() → HealthStatus snapshot
    - circuit_breaker logic → auto-disable on repeated failures

    Escalation chain:
        Sub-agent fails → self-heal (3 attempts)
        ↓ can't fix
        Core agent tries (different sub-agent or approach)
        ↓ can't fix
        Orchestrator (Round Table consensus, provider swap)
        ↓ can't fix
        Dashboard alert (human decides via 3D portal)
    """

    # Configurable per agent
    _max_heal_attempts: int = 3
    _circuit_breaker_threshold: int = 5
    _circuit_breaker_cooldown_seconds: float = 60.0

    def __init_healing__(self) -> None:
        """Initialize healing state. Call from __init__ of concrete agents."""
        self._consecutive_failures: int = 0
        self._circuit_state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self._circuit_opened_at: float | None = None
        self._last_success_time: str | None = None
        self._last_failure_time: str | None = None
        # LRU-bounded learning journal (max 100 entries per agent)
        self._heal_journal: OrderedDict[str, HealAttempt] = OrderedDict()
        self._heal_journal_max: int = 100

    # -------------------------------------------------------------------------
    # Diagnosis
    # -------------------------------------------------------------------------

    def diagnose(self, error: Exception | str) -> Diagnosis:
        """
        Analyze a failure and produce a diagnosis.

        Categorizes the failure, suggests actions based on category,
        and checks the learning journal for past fixes.
        """
        category = categorize_failure(error)
        description = str(error)

        actions = self._suggested_actions_for(category)

        # Check learning journal for past successful fixes
        past_fixes = [
            entry
            for entry in self._heal_journal.values()
            if entry.category == category and entry.action_taken
        ]
        if past_fixes:
            actions.insert(0, f"Previously worked: {past_fixes[-1].action_taken}")

        return Diagnosis(
            failure_category=category,
            description=description,
            suggested_actions=actions,
            context={"agent": getattr(self, "name", "unknown")},
        )

    def _suggested_actions_for(self, category: FailureCategory) -> list[str]:
        """Generate suggested actions based on failure category."""
        actions: dict[FailureCategory, list[str]] = {
            FailureCategory.CODE_BUG: [
                "Fix code errors in affected output",
                "Run linter/formatter on generated code",
                "Review and fix logic errors",
            ],
            FailureCategory.CONFIG: [
                "Check environment variables and config files",
                "Verify API keys are set and valid",
                "Check file paths and permissions",
            ],
            FailureCategory.WRONG_APPROACH: [
                "Replan with a different strategy",
                "Try alternative implementation approach",
                "Escalate for Round Table consensus",
            ],
            FailureCategory.EXTERNAL: [
                "Retry with exponential backoff",
                "Switch to fallback provider",
                "Check service status page",
            ],
            FailureCategory.DATA_QUALITY: [
                "Validate input data format",
                "Clean/sanitize input data",
                "Check data source integrity",
            ],
            FailureCategory.PROVIDER_DOWN: [
                "Switch to alternative provider",
                "Queue task for later retry",
                "Check provider status page",
            ],
        }
        return list(actions.get(category, ["Investigate and fix manually"]))

    # -------------------------------------------------------------------------
    # Healing
    # -------------------------------------------------------------------------

    async def heal(
        self,
        diagnosis: Diagnosis,
        fixer: Any = None,
    ) -> HealCycleResult:
        """
        Run the heal cycle: attempt fix → verify → retry.

        If no fixer is provided, uses the default self._apply_fix method
        which subclasses can override for domain-specific healing.

        Args:
            diagnosis: What needs fixing.
            fixer: Optional async callable(diagnosis) -> HealResult.

        Returns:
            HealCycleResult with success status and attempt history.
        """
        if fixer is None:
            fixer = self._apply_fix

        history: list[HealResult] = []

        for attempt in range(1, self._max_heal_attempts + 1):
            logger.info(
                "[%s] Heal attempt %d/%d for %s: %s",
                getattr(self, "name", "agent"),
                attempt,
                self._max_heal_attempts,
                diagnosis.failure_category.value,
                diagnosis.description[:100],
            )

            try:
                fix_result = await fixer(diagnosis)
            except Exception as exc:
                fix_result = HealResult(
                    success=False,
                    message=f"Fixer raised: {exc}",
                )

            history.append(fix_result)

            # Record in learning journal
            journal_key = f"{time.time():.6f}"
            self._heal_journal[journal_key] = HealAttempt(
                category=diagnosis.failure_category,
                description=diagnosis.description[:200],
                action_taken=fix_result.message if fix_result.success else "",
            )
            # Enforce LRU bound
            while len(self._heal_journal) > self._heal_journal_max:
                self._heal_journal.popitem(last=False)

            if fix_result.success:
                self._record_success()
                logger.info(
                    "[%s] Heal succeeded on attempt %d",
                    getattr(self, "name", "agent"),
                    attempt,
                )
                return HealCycleResult(
                    success=True,
                    attempts=attempt,
                    history=history,
                )

            logger.warning(
                "[%s] Heal attempt %d failed: %s",
                getattr(self, "name", "agent"),
                attempt,
                fix_result.message,
            )

        # Exhausted all attempts
        self._record_failure()
        logger.error(
            "[%s] Heal cycle exhausted %d attempts — escalation needed",
            getattr(self, "name", "agent"),
            self._max_heal_attempts,
        )
        return HealCycleResult(
            success=False,
            attempts=self._max_heal_attempts,
            escalation_needed=True,
            history=history,
        )

    async def _apply_fix(self, diagnosis: Diagnosis) -> HealResult:
        """
        Default fix strategy. Subclasses override for domain-specific healing.

        Base implementation provides simple retry for EXTERNAL/PROVIDER_DOWN,
        and returns failure for other categories (requires subclass override).
        """
        category = diagnosis.failure_category

        if category in (FailureCategory.EXTERNAL, FailureCategory.PROVIDER_DOWN):
            # Wait and retry — external issues often resolve
            await asyncio.sleep(2.0)
            return HealResult(
                success=False,
                message="Waited for external service — needs re-execution",
            )

        return HealResult(
            success=False,
            message=f"No auto-fix for {category.value} — needs manual intervention or subclass override",
        )

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------

    def health_check(self) -> HealthStatus:
        """
        Return current health snapshot.

        Includes circuit breaker state, failure counts, and sub-agent health.
        """
        # Collect sub-agent health if this is a core agent
        sub_health: dict[str, bool] = {}
        for attr_name in dir(self):
            attr = getattr(self, attr_name, None)
            if isinstance(attr, SelfHealingMixin) and attr is not self:
                sub_name = getattr(attr, "name", attr_name)
                sub_status = attr.health_check()
                sub_health[sub_name] = sub_status.healthy

        return HealthStatus(
            agent_name=getattr(self, "name", self.__class__.__name__),
            agent_type=getattr(self, "core_type", CoreAgentType.ORCHESTRATOR).value
            if hasattr(self, "core_type")
            else "unknown",
            healthy=self._circuit_state == CircuitBreakerState.CLOSED,
            circuit_breaker=self._circuit_state.value,
            consecutive_failures=self._consecutive_failures,
            last_success=self._last_success_time,
            last_failure=self._last_failure_time,
            sub_agent_health=sub_health,
        )

    # -------------------------------------------------------------------------
    # Circuit Breaker
    # -------------------------------------------------------------------------

    def circuit_breaker_allows(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self._circuit_state == CircuitBreakerState.CLOSED:
            return True

        if self._circuit_state == CircuitBreakerState.OPEN:
            # Check cooldown
            if self._circuit_opened_at is not None:
                elapsed = time.time() - self._circuit_opened_at
                if elapsed >= self._circuit_breaker_cooldown_seconds:
                    self._circuit_state = CircuitBreakerState.HALF_OPEN
                    logger.info(
                        "[%s] Circuit breaker → HALF_OPEN (cooldown expired)",
                        getattr(self, "name", "agent"),
                    )
                    return True
            return False

        # HALF_OPEN — allow one test request
        return True

    def _record_success(self) -> None:
        """Record a successful execution."""
        self._consecutive_failures = 0
        self._last_success_time = datetime.now(UTC).isoformat()

        if self._circuit_state == CircuitBreakerState.HALF_OPEN:
            self._circuit_state = CircuitBreakerState.CLOSED
            logger.info(
                "[%s] Circuit breaker → CLOSED (success in half-open)",
                getattr(self, "name", "agent"),
            )

    def _record_failure(self) -> None:
        """Record a failed execution."""
        self._consecutive_failures += 1
        self._last_failure_time = datetime.now(UTC).isoformat()

        if self._consecutive_failures >= self._circuit_breaker_threshold:
            self._circuit_state = CircuitBreakerState.OPEN
            self._circuit_opened_at = time.time()
            logger.error(
                "[%s] Circuit breaker → OPEN (%d consecutive failures)",
                getattr(self, "name", "agent"),
                self._consecutive_failures,
            )

        if self._circuit_state == CircuitBreakerState.HALF_OPEN:
            self._circuit_state = CircuitBreakerState.OPEN
            self._circuit_opened_at = time.time()
            logger.warning(
                "[%s] Circuit breaker → OPEN (failed in half-open)",
                getattr(self, "name", "agent"),
            )


# =============================================================================
# CoreAgent — Base for the 8 domain core agents
# =============================================================================


class CoreAgent(SelfHealingMixin):
    """
    Base class for the 8 domain core agents.

    Each core agent:
    - Owns a domain (commerce, content, etc.)
    - Manages sub-agents that handle specific tasks
    - Self-heals and escalates failures to the orchestrator
    - Reports health via the 3D portal

    Subclasses must implement:
    - execute(task, **kwargs) → dict[str, Any]
    - get_sub_agents() → list of sub-agent instances

    Convention:
    - Core agents wrap existing EnhancedSuperAgent subclasses
    - They add self-healing + sub-agent delegation on top
    - Original agent classes remain importable for backward compat
    """

    core_type: CoreAgentType = CoreAgentType.ORCHESTRATOR  # Override in subclass
    name: str = "unnamed_core_agent"
    description: str = ""

    def __init__(
        self,
        *,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.correlation_id = correlation_id
        self.__init_healing__()
        self._sub_agents: dict[str, Any] = {}

    def register_sub_agent(self, name: str, sub_agent: Any) -> None:
        """Register a sub-agent under this core agent."""
        self._sub_agents[name] = sub_agent
        logger.debug("[%s] Registered sub-agent: %s", self.name, name)

    def get_sub_agents(self) -> dict[str, Any]:
        """Return all registered sub-agents."""
        return dict(self._sub_agents)

    async def delegate(
        self,
        sub_agent_name: str,
        task: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Delegate a task to a sub-agent with self-healing.

        If the sub-agent fails and can't self-heal, the core agent
        tries alternative sub-agents before escalating.
        """
        sub_agent = self._sub_agents.get(sub_agent_name)
        if sub_agent is None:
            raise AgentError(
                f"Sub-agent '{sub_agent_name}' not registered on {self.name}",
                category=ErrorCategory.CONFIGURATION,
            )

        # Check circuit breaker on sub-agent if it has one
        if isinstance(sub_agent, SelfHealingMixin):
            if not sub_agent.circuit_breaker_allows():
                logger.warning(
                    "[%s] Sub-agent '%s' circuit breaker is OPEN — trying alternatives",
                    self.name,
                    sub_agent_name,
                )
                return await self._try_alternative_sub_agents(
                    exclude=sub_agent_name, task=task, **kwargs
                )

        try:
            if hasattr(sub_agent, "execute"):
                result = await sub_agent.execute(task, **kwargs)
            elif callable(sub_agent):
                result = await sub_agent(task, **kwargs)
            else:
                raise AgentError(
                    f"Sub-agent '{sub_agent_name}' has no execute method",
                    category=ErrorCategory.CONFIGURATION,
                )

            if isinstance(sub_agent, SelfHealingMixin):
                sub_agent._record_success()

            return result if isinstance(result, dict) else {"result": result}

        except Exception as exc:
            logger.error(
                "[%s] Sub-agent '%s' failed: %s",
                self.name,
                sub_agent_name,
                exc,
            )

            # Try self-healing on the sub-agent
            if isinstance(sub_agent, SelfHealingMixin):
                diagnosis = sub_agent.diagnose(exc)
                heal_result = await sub_agent.heal(diagnosis)
                if heal_result.success:
                    # Retry after healing
                    return await self.delegate(sub_agent_name, task, **kwargs)

                sub_agent._record_failure()

            # Try alternative sub-agents
            return await self._try_alternative_sub_agents(
                exclude=sub_agent_name, task=task, original_error=exc, **kwargs
            )

    async def _try_alternative_sub_agents(
        self,
        exclude: str,
        task: str,
        original_error: Exception | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Try other sub-agents when the primary one fails."""
        for alt_name, alt_agent in self._sub_agents.items():
            if alt_name == exclude:
                continue

            # Skip agents with open circuit breakers
            if isinstance(alt_agent, SelfHealingMixin):
                if not alt_agent.circuit_breaker_allows():
                    continue

            try:
                logger.info(
                    "[%s] Trying alternative sub-agent: %s",
                    self.name,
                    alt_name,
                )
                if hasattr(alt_agent, "execute"):
                    result = await alt_agent.execute(task, **kwargs)
                    return result if isinstance(result, dict) else {"result": result}
            except Exception:
                continue

        # All sub-agents failed — escalate
        self._record_failure()
        raise AgentError(
            f"[{self.name}] All sub-agents failed for task. Escalation needed.",
            category=ErrorCategory.EXECUTION,
            context={"task": task[:200], "original_error": str(original_error)[:200]},
        )

    @abstractmethod
    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Execute a domain task. Implement in each core agent."""
        ...

    async def execute_safe(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """
        Execute with circuit breaker + self-healing wrapper.

        This is the primary entry point for external callers.
        """
        if not self.circuit_breaker_allows():
            return {
                "success": False,
                "error": f"Circuit breaker OPEN for {self.name}",
                "escalation_needed": True,
            }

        try:
            result = await self.execute(task, **kwargs)
            self._record_success()
            return result

        except Exception as exc:
            diagnosis = self.diagnose(exc)
            heal_result = await self.heal(diagnosis)

            if heal_result.success:
                # Retry after healing
                try:
                    result = await self.execute(task, **kwargs)
                    self._record_success()
                    return result
                except Exception as retry_exc:
                    self._record_failure()
                    return {
                        "success": False,
                        "error": str(retry_exc),
                        "heal_attempted": True,
                        "escalation_needed": True,
                    }

            self._record_failure()
            return {
                "success": False,
                "error": str(exc),
                "heal_attempted": True,
                "heal_history": [
                    {"success": h.success, "message": h.message} for h in heal_result.history
                ],
                "escalation_needed": heal_result.escalation_needed,
            }

    def to_portal_node(self) -> dict[str, Any]:
        """
        Serialize to a 3D portal node for the dashboard.

        Returns data compatible with React Three Fiber rendering.
        """
        health = self.health_check()
        return {
            "id": self.name,
            "type": self.core_type.value,
            "label": self.name.replace("_", " ").title(),
            "description": self.description,
            "healthy": health.healthy,
            "circuit_breaker": health.circuit_breaker,
            "consecutive_failures": health.consecutive_failures,
            "sub_agents": [
                {
                    "id": name,
                    "healthy": health.sub_agent_health.get(name, True),
                }
                for name in self._sub_agents
            ],
        }


__all__ = [
    "CoreAgentType",
    "FailureCategory",
    "CircuitBreakerState",
    "HealAttempt",
    "Diagnosis",
    "HealResult",
    "HealCycleResult",
    "HealthStatus",
    "categorize_failure",
    "SelfHealingMixin",
    "CoreAgent",
]
