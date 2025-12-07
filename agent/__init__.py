"""
DevSkyy Agent Package

This package contains all the specialized AI agents for comprehensive
website management, optimization, and monitoring.

Modules:
    orchestrator: Main agent orchestration and task execution
    unified_orchestrator: MCP-optimized unified orchestration (98% token reduction)
    fashion_orchestrator: Fashion-specific AI workflows
    registry: Agent registration and discovery
    loader: Agent configuration loading
    router: Intelligent task routing
    security_manager: Agent security and access control

Mixins:
    mixins.react_mixin: ReAct (Reasoning + Acting) capabilities
"""

import os
import sys

__version__ = "2.0.0"
__author__ = "DevSkyy Enhanced Platform"

# Add current directory to Python path to enable relative imports
sys.path.insert(0, os.path.dirname(__file__))

# Public API exports
__all__ = [
    "AgentOrchestrator",
    "AgentRegistry",
    "AgentRouter",
    "AgentConfigLoader",
]


def __getattr__(name: str):
    """
    Lazy import of agent modules for performance.

    Args:
        name: The attribute name to import.

    Returns:
        The requested module or class.

    Raises:
        AttributeError: If the attribute is not found.
    """
    if name == "AgentOrchestrator":
        from agent.orchestrator import AgentOrchestrator
        return AgentOrchestrator
    elif name == "AgentRegistry":
        from agent.registry import AgentRegistry
        return AgentRegistry
    elif name == "AgentRouter":
        from agent.router import AgentRouter
        return AgentRouter
    elif name == "AgentConfigLoader":
        from agent.loader import AgentConfigLoader
        return AgentConfigLoader
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
