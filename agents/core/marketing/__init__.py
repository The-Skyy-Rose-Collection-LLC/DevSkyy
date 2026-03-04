"""Marketing Core Agent — campaigns, social, audience growth."""

try:
    from .agent import MarketingCoreAgent
except ImportError:
    MarketingCoreAgent = None  # type: ignore[assignment,misc]

__all__ = ["MarketingCoreAgent"]
