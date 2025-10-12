"""
Scripts Module
DevSkyy utility scripts and background agents

This module provides:
- Daily scanner agent for website monitoring
- Background agent management
- Build and deployment utilities
- System automation scripts
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .daily_scanner import DailyScannerAgent
    from .start_background_agents import BackgroundAgentManager

__all__ = [
    "DailyScannerAgent",
    "BackgroundAgentManager",
]

__version__ = "1.0.0"
