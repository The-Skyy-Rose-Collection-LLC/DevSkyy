"""Content Core Agent — pages, products, blogs, SEO copy."""

try:
    from .agent import ContentCoreAgent
except ImportError:
    ContentCoreAgent = None  # type: ignore[assignment,misc]

__all__ = ["ContentCoreAgent"]
