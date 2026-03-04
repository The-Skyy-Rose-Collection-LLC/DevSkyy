"""Creative Core Agent — visual identity, design system, brand enforcement."""

try:
    from .agent import CreativeCoreAgent
except ImportError:
    CreativeCoreAgent = None  # type: ignore[assignment,misc]

__all__ = ["CreativeCoreAgent"]
