"""
Factory for creating a fully-wired Orchestrator with all 8 core agents.

Usage:
    from agents.core.factory import create_orchestrator

    orchestrator = create_orchestrator()
    result = await orchestrator.route("Update product prices")
"""

from __future__ import annotations

import importlib
import logging

logger = logging.getLogger(__name__)

_CORE_AGENT_REGISTRY: list[tuple[str, str]] = [
    ("agents.core.commerce.agent", "CommerceCoreAgent"),
    ("agents.core.content.agent", "ContentCoreAgent"),
    ("agents.core.creative.agent", "CreativeCoreAgent"),
    ("agents.core.marketing.agent", "MarketingCoreAgent"),
    ("agents.core.operations.agent", "OperationsCoreAgent"),
    ("agents.core.analytics.agent", "AnalyticsCoreAgent"),
    ("agents.core.imagery.agent", "ImageryCoreAgent"),
    ("agents.core.web_builder.agent", "WebBuilderCoreAgent"),
]


def create_orchestrator(
    *,
    correlation_id: str | None = None,
    budget_limit_usd: float | None = None,
) -> Orchestrator:
    """Create fully-wired Orchestrator with all 8 core agents.

    Uses dynamic imports with graceful degradation — if a core agent
    fails to import, logs a warning and continues with the others.

    Args:
        correlation_id: Optional correlation ID for tracing.
        budget_limit_usd: Optional budget cap for autonomous operations.

    Returns:
        Orchestrator with all successfully-imported core agents registered.
    """
    from agents.core.orchestrator import Orchestrator

    orchestrator = Orchestrator(correlation_id=correlation_id)

    if budget_limit_usd is not None:
        orchestrator.set_budget_limit(budget_limit_usd)

    registered = 0
    for module_path, class_name in _CORE_AGENT_REGISTRY:
        try:
            module = importlib.import_module(module_path)
            agent_cls = getattr(module, class_name)
            agent = agent_cls(correlation_id=correlation_id)
            orchestrator.register_core_agent(agent)
            registered += 1
        except Exception as e:
            logger.warning(
                "Failed to import core agent %s.%s: %s",
                module_path,
                class_name,
                e,
            )

    logger.info(
        "[factory] Orchestrator created with %d/%d core agents",
        registered,
        len(_CORE_AGENT_REGISTRY),
    )
    return orchestrator
