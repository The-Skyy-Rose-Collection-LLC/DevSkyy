"""
Base agent class for Elite Web Builder specialists.

Every specialist agent has:
- A role name (used by ModelRouter for provider selection)
- A system prompt (injected with learning context)
- Access to ground truth validator and verification tools
- Ralph-loop resilience on all external calls

Agents don't make API calls directly — they produce structured outputs
(code, config, analysis) that pass through the verification loop.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """The 8 agent roles in the team."""

    DIRECTOR = "director"
    DESIGN_SYSTEM = "design_system"
    FRONTEND_DEV = "frontend_dev"
    BACKEND_DEV = "backend_dev"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    SEO_CONTENT = "seo_content"
    QA = "qa"


@dataclass(frozen=True)
class AgentCapability:
    """A specific capability an agent can perform."""

    name: str
    description: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentOutput:
    """Immutable output from an agent task."""

    agent: str
    story_id: str
    content: str
    files_changed: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentSpec:
    """Specification for a specialist agent."""

    role: AgentRole
    name: str
    system_prompt: str
    capabilities: list[AgentCapability] = field(default_factory=list)
    knowledge_files: list[str] = field(default_factory=list)

    def build_prompt(self, learning_context: str = "") -> str:
        """Build the full system prompt including learning rules."""
        parts = [self.system_prompt]
        if learning_context:
            parts.append(f"\n{learning_context}")
        return "\n\n".join(parts)
