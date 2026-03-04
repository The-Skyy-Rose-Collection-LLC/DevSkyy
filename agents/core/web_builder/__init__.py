"""Web Builder Core Agent — theme generation, deployment, platform adapters."""

try:
    from .agent import WebBuilderCoreAgent
except ImportError:
    WebBuilderCoreAgent = None  # type: ignore[assignment,misc]

__all__ = ["WebBuilderCoreAgent"]
