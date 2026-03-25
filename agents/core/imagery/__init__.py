"""Imagery & 3D Core Agent — photos, VTON, 3D model generation."""

try:
    from .agent import ImageryCoreAgent
except ImportError:
    ImageryCoreAgent = None  # type: ignore[assignment,misc]

__all__ = ["ImageryCoreAgent"]
