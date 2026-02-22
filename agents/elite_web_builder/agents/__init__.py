"""Specialist agents for Elite Web Builder.

Each agent is defined as an AgentSpec with role, system prompt, and capabilities.
Import individual specs or use ALL_SPECS for the complete team.
"""

from agents.accessibility import ACCESSIBILITY_SPEC
from agents.backend_dev import BACKEND_DEV_SPEC
from agents.base import AgentCapability, AgentOutput, AgentRole, AgentSpec
from agents.design_system import DESIGN_SYSTEM_SPEC
from agents.frontend_dev import FRONTEND_DEV_SPEC
from agents.performance import PERFORMANCE_SPEC
from agents.qa import QA_SPEC
from agents.provider_adapters import (
    LLMMessage,
    LLMResponse,
    get_adapter,
)
from agents.runtime import AgentRuntime
from agents.seo_content import SEO_CONTENT_SPEC

ALL_SPECS: tuple[AgentSpec, ...] = (
    DESIGN_SYSTEM_SPEC,
    FRONTEND_DEV_SPEC,
    BACKEND_DEV_SPEC,
    ACCESSIBILITY_SPEC,
    PERFORMANCE_SPEC,
    SEO_CONTENT_SPEC,
    QA_SPEC,
)

__all__ = [
    "AgentCapability",
    "AgentOutput",
    "AgentRole",
    "AgentSpec",
    "ACCESSIBILITY_SPEC",
    "BACKEND_DEV_SPEC",
    "DESIGN_SYSTEM_SPEC",
    "FRONTEND_DEV_SPEC",
    "PERFORMANCE_SPEC",
    "QA_SPEC",
    "SEO_CONTENT_SPEC",
    "ALL_SPECS",
    "AgentRuntime",
    "LLMMessage",
    "LLMResponse",
    "get_adapter",
]
