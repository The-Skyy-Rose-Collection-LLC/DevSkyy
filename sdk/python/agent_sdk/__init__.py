"""
DevSkyy Agent SDK Integration

Enterprise-grade multi-agent orchestration using Claude Agent SDK.
Integrates SuperAgents, LLM Round Table, and custom MCP tools.
"""

from __future__ import annotations

__version__ = "1.0.0"

# Lazy imports to avoid requiring claude_agent_sdk for all submodules
_lazy_imports = {
    "AgentOrchestrator": "agent_sdk.orchestrator",
    "RoundTableOrchestrator": "agent_sdk.round_table",
    "create_devskyy_tools": "agent_sdk.custom_tools",
}

__all__ = [
    "AgentOrchestrator",
    "RoundTableOrchestrator",
    "create_devskyy_tools",
]


def __getattr__(name: str):
    """Lazy import handler."""
    if name in _lazy_imports:
        import importlib

        module = importlib.import_module(_lazy_imports[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
