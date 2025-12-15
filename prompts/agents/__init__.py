"""DevSkyy Prompt Engineering - Agents Module"""

from .base_agent import (
    AGENT_DOMAINS,
    AgentCategory,
    AgentDomain,
    build_agent_prompt,
    create_custom_agent,
    get_agent_domain,
    list_available_agents,
)
from .ensemble_prompts import (
    AGENT_TECHNIQUE_MAPPINGS,
    DEFAULT_CRITERIA,
    TECHNIQUE_PROMPTS,
    AgentTechniqueMapping,
    EvaluationCriteria,
    TechniqueConfig,
    TechniqueType,
    build_analytics_prompt,
    build_commerce_prompt,
    build_creative_prompt,
    build_ensemble_prompt,
    build_marketing_prompt,
    build_operations_prompt,
    build_support_prompt,
)

__all__ = [
    "AgentCategory", "AgentDomain", "AGENT_DOMAINS", "build_agent_prompt",
    "get_agent_domain", "list_available_agents", "create_custom_agent",
    "TechniqueType", "TechniqueConfig", "EvaluationCriteria",
    "AgentTechniqueMapping", "TECHNIQUE_PROMPTS", "DEFAULT_CRITERIA",
    "AGENT_TECHNIQUE_MAPPINGS", "build_ensemble_prompt", "build_commerce_prompt",
    "build_creative_prompt", "build_marketing_prompt", "build_support_prompt",
    "build_operations_prompt", "build_analytics_prompt",
]
