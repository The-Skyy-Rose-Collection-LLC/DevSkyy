"""
Coding Doctor Sub-Agent
========================

Wraps agents/coding_doctor_agent.py into the new hierarchy.

Parent: Operations Core Agent
Capabilities: Lint auto-fix, type error resolution, code smell detection.
"""

from __future__ import annotations

from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent


class CodingDoctorSubAgent(SubAgent):
    """Code quality — lint fix, type check, code health analysis."""

    name = "coding_doctor"
    parent_type = CoreAgentType.OPERATIONS
    description = "Lint auto-fix, type error resolution, code smell detection"
    capabilities = [
        "lint_fix",
        "type_check",
        "code_review",
        "health_report",
    ]

    system_prompt = (
        "You are the Code Quality Doctor for the DevSkyy platform. "
        "You analyze Python and TypeScript code for lint issues, type errors, "
        "code smells, and anti-patterns. You follow ruff, mypy, and black standards "
        "for Python; ESLint + TypeScript strict for JS/TS. Return actionable fixes "
        "with file paths and line numbers."
    )

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        return await self._llm_execute(task)


__all__ = ["CodingDoctorSubAgent"]
