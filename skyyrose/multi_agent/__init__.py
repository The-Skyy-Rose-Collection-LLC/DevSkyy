"""
SkyyRose Multi-Agent System — Claude Agent SDK

Autonomous multi-agent orchestrator for the SkyyRose luxury fashion platform.
Uses Claude Agent SDK to coordinate specialized subagents with custom tools.

Architecture:
    Orchestrator (Opus 4.6) — master brain, delegates to subagents
    ├── brand-writer     — brand-voice content generation
    ├── theme-auditor    — WordPress theme quality & accessibility audit
    ├── product-analyst  — product catalog analysis & optimization
    ├── deploy-manager   — deployment & sync operations
    └── qa-inspector     — end-to-end quality assurance

Each subagent has its own tools, system prompt, and permission scope.
The orchestrator decides what to delegate based on the user's request.
"""

from .orchestrator import run_orchestrator, run_single_agent
from .agents import AGENT_DEFINITIONS
from .tools import CUSTOM_TOOLS

__all__ = [
    "run_orchestrator",
    "run_single_agent",
    "AGENT_DEFINITIONS",
    "CUSTOM_TOOLS",
]
