"""
DevSkyy Core Agent Hierarchy
=============================

8 Core Agents + 1 Orchestrator with universal self-healing.

Architecture:
    Orchestrator
    ├── CommerceCore     (4 sub-agents)
    ├── ContentCore      (3 sub-agents)
    ├── CreativeCore     (4 sub-agents)
    ├── MarketingCore    (3 sub-agents)
    ├── OperationsCore   (4 sub-agents)
    ├── AnalyticsCore    (3 sub-agents)
    ├── ImageryCore      (5 sub-agents)
    └── WebBuilderCore   (5 sub-agents)

Every agent inherits SelfHealingMixin for:
- diagnose() / heal() / health_check() / circuit_breaker()
- Escalation chain: sub-agent → core → orchestrator → human
- Learning journal for heal attempt history
"""

import logging as _logging

_logger = _logging.getLogger(__name__)

# Base classes
try:
    from .base import (
        CircuitBreakerState,
        CoreAgent,
        CoreAgentType,
        Diagnosis,
        FailureCategory,
        HealAttempt,
        HealCycleResult,
        HealResult,
        HealthStatus,
        SelfHealingMixin,
    )
except ImportError as _e:
    _logger.debug("Core base classes unavailable: %s", _e)

try:
    from .sub_agent import SubAgent
except ImportError as _e:
    _logger.debug("SubAgent unavailable: %s", _e)

try:
    from .orchestrator import Orchestrator
except ImportError as _e:
    _logger.debug("Orchestrator unavailable: %s", _e)

__all__ = [
    # Base
    "SelfHealingMixin",
    "CoreAgent",
    "CoreAgentType",
    "SubAgent",
    "Orchestrator",
    # Self-healing types
    "FailureCategory",
    "CircuitBreakerState",
    "Diagnosis",
    "HealAttempt",
    "HealResult",
    "HealCycleResult",
    "HealthStatus",
]
