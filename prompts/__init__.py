#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEVSKYY PROMPT ENGINEERING SYSTEM                                           ║
║  Multi-Technique Ensemble Prompting with Self-Critique                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  6 SUPER AGENTS (Multi-Technique Ensemble):                                  ║
║    1. Commerce Agent   - Products, inventory, pricing, orders, WooCommerce   ║
║    2. Creative Agent   - 3D assets (Tripo), virtual try-on (FASHN), media    ║
║    3. Marketing Agent  - Content, SEO, social media, campaigns               ║
║    4. Support Agent    - Customer service, tickets, FAQ, chat                ║
║    5. Operations Agent - WordPress, Elementor, deployment, monitoring        ║
║    6. Analytics Agent  - Reports, forecasting, ML predictions                ║
║                                                                              ║
║  PROMPTING ARCHITECTURE:                                                     ║
║    PHASE 1: PLAN    - Generate 3 solutions using different techniques        ║
║    PHASE 2: ANALYZE - Self-critique each output against criteria             ║
║    PHASE 3: SELECT  - Choose best option and implement                       ║
║                                                                              ║
║  17 VERIFIED TECHNIQUES (10+ sources each):                                  ║
║    Core: CoT, Few-Shot, Zero-Shot, Role/Persona, System Prompt               ║
║    Advanced: ToT, ReAct, Self-Consistency, RAG, Prompt Chaining              ║
║    ML-Based: APE, OPRO, DSPy, PromptBreeder, Reflexion, Constitutional AI    ║
╚══════════════════════════════════════════════════════════════════════════════╝

USAGE:
    # Build ensemble prompt for any Super Agent
    from prompts import build_commerce_prompt

    prompt = build_commerce_prompt("Check inventory for BLACK ROSE collection")
    # Returns prompt with 3 technique paths + self-analysis + selection

    # Or use the generic builder
    from prompts import build_ensemble_prompt, TechniqueType

    prompt = build_ensemble_prompt(
        agent_type="commerce",
        agent_role="Senior E-Commerce Director",
        agent_domain="inventory and orders",
        tools=["woocommerce_api", "inventory_tracker"],
        task="Your task here",
        constraints=["Never oversell"],
        success_criteria=["99.5% accuracy"],
    )
"""

__version__ = "2.0.0"
__author__ = "DevSkyy Team"

# =============================================================================
# AGENTS MODULE - 6 Super Agents with Ensemble Prompting
# =============================================================================
from .agents import (
    AGENT_DOMAINS,
    AGENT_TECHNIQUE_MAPPINGS,
    DEFAULT_CRITERIA,
    TECHNIQUE_PROMPTS,
    AgentCategory,
    AgentDomain,
    AgentTechniqueMapping,
    EvaluationCriteria,
    TechniqueConfig,
    TechniqueType,
    build_agent_prompt,
    build_analytics_prompt,
    build_commerce_prompt,
    build_creative_prompt,
    build_ensemble_prompt,
    build_marketing_prompt,
    build_operations_prompt,
    build_support_prompt,
    create_custom_agent,
    get_agent_domain,
    list_available_agents,
)

# =============================================================================
# BASE MODULE - 17 Verified Techniques
# =============================================================================
from .base import (
    ChainOfThought,
    FewShot,
    FewShotExample,
    GeneratedKnowledge,
    NegativeConstraints,
    PromptBuilder,
    PromptChain,
    PromptTechnique,
    ReAct,
    ReActStep,
    RoleConstraint,
    SelfConsistency,
    SuccessCriteria,
    TechniqueRegistry,
    TreeOfThoughts,
    ZeroShotCoT,
)

# =============================================================================
# INJECTORS MODULE - Dynamic Task Injection
# =============================================================================
from .injectors import ChainBuilder, TaskContext, TaskInjector, TaskTemplates

# =============================================================================
# META MODULE - Repo Development Meta-Prompts
# =============================================================================
from .meta import (
    SUBAGENT_CONFIGS,
    ArchitectSubagent,
    RepoContext,
    SubagentConfig,
    build_architect_prompt,
    build_code_review_prompt,
    build_documentation_prompt,
    build_test_generation_prompt,
)

# =============================================================================
# OPTIMIZATION MODULE - ML-Based Self-Improvement
# =============================================================================
from .optimization import (
    FeedbackType,
    MutationOperator,
    OptimizationRun,
    OptimizationStrategy,
    PromptVariant,
    ReflexionMemory,
    SelfImprovingPromptAgent,
)


def get_agent_prompt(agent_type: str, task: str) -> str:
    """Quick access to build an ensemble prompt for any Super Agent."""
    builders = {
        "commerce": build_commerce_prompt,
        "creative": build_creative_prompt,
        "marketing": build_marketing_prompt,
        "support": build_support_prompt,
        "operations": build_operations_prompt,
        "analytics": build_analytics_prompt,
    }
    builder = builders.get(agent_type.lower())
    if not builder:
        raise ValueError(f"Unknown agent type: {agent_type}. Use one of: {list(builders.keys())}")
    return builder(task)


def list_super_agents() -> dict:
    """List all Super Agents with their technique mappings."""
    return {
        "commerce": {
            "role": "Senior E-Commerce Operations Director",
            "domain": "Products, inventory, pricing, orders, WooCommerce",
            "techniques": ["ReAct", "CoT", "Direct"],
        },
        "creative": {
            "role": "Creative Director, AI Visual Production",
            "domain": "3D assets (Tripo3D), virtual try-on (FASHN), media",
            "techniques": ["Tree of Thoughts", "Generated Knowledge", "CoT"],
        },
        "marketing": {
            "role": "Chief Marketing Officer AI",
            "domain": "Content, SEO, social media, campaigns",
            "techniques": ["Generated Knowledge", "CoT", "Tree of Thoughts"],
        },
        "support": {
            "role": "Customer Experience Director",
            "domain": "Customer service, tickets, FAQ, chat",
            "techniques": ["ReAct", "CoT", "Direct"],
        },
        "operations": {
            "role": "Platform Operations Engineer",
            "domain": "WordPress, Elementor, deployment, monitoring",
            "techniques": ["ReAct", "CoT", "Tree of Thoughts"],
        },
        "analytics": {
            "role": "Chief Data Officer AI",
            "domain": "Reports, forecasting, ML predictions",
            "techniques": ["CoT", "Generated Knowledge", "Tree of Thoughts"],
        },
    }


__all__ = [
    "__version__",
    "PromptTechnique", "RoleConstraint", "ChainOfThought", "ZeroShotCoT",
    "FewShotExample", "FewShot", "TreeOfThoughts", "ReActStep", "ReAct",
    "SelfConsistency", "NegativeConstraints", "SuccessCriteria",
    "GeneratedKnowledge", "PromptChain", "PromptBuilder", "TechniqueRegistry",
    "AgentCategory", "AgentDomain", "AGENT_DOMAINS", "build_agent_prompt",
    "get_agent_domain", "list_available_agents", "create_custom_agent",
    "TechniqueType", "TechniqueConfig", "EvaluationCriteria",
    "AgentTechniqueMapping", "TECHNIQUE_PROMPTS", "DEFAULT_CRITERIA",
    "AGENT_TECHNIQUE_MAPPINGS", "build_ensemble_prompt", "build_commerce_prompt",
    "build_creative_prompt", "build_marketing_prompt", "build_support_prompt",
    "build_operations_prompt", "build_analytics_prompt",
    "ArchitectSubagent", "SubagentConfig", "SUBAGENT_CONFIGS", "RepoContext",
    "build_architect_prompt", "build_code_review_prompt",
    "build_test_generation_prompt", "build_documentation_prompt",
    "TaskContext", "TaskInjector", "TaskTemplates", "ChainBuilder",
    "OptimizationStrategy", "FeedbackType", "PromptVariant", "OptimizationRun",
    "ReflexionMemory", "MutationOperator", "SelfImprovingPromptAgent",
    "get_agent_prompt", "list_super_agents",
]
