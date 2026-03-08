"""Analytics Core Agent — data, trends, conversion intelligence."""

try:
    from .agent import AnalyticsCoreAgent
except ImportError:
    AnalyticsCoreAgent = None  # type: ignore[assignment,misc]

__all__ = ["AnalyticsCoreAgent"]
