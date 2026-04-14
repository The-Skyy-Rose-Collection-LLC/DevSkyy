"""
Re-export TrendAdvisor from the fashion trends module.

Provides a clean import path from design/ subpackage.
"""

from __future__ import annotations

from ..trends import TrendAdvisor, TrendSignal

__all__ = ["TrendAdvisor", "TrendSignal"]
