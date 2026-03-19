"""
DevSkyy Enhanced Base Super Agent
==================================

Base class for all 6 SuperAgents with:
- 17 Prompt Engineering Techniques (auto-selection)
- ML Capabilities Module
- Self-Learning Module
- LLM Round Table Interface

Architecture:
    EnhancedSuperAgent
    ├── PromptEngineeringModule (17 techniques)
    ├── MLCapabilitiesModule
    ├── SelfLearningModule
    ├── LLMRoundTableInterface
    └── ToolRegistry

This package replaces the monolithic ``base_super_agent.py`` file.
All public names are re-exported here so that existing imports of the form
``from agents.base_super_agent import X`` continue to work unchanged.
"""

# --- agent ---
from .agent import LLM_ROUTER_AVAILABLE, EnhancedSuperAgent
from .learning_module import SelfLearningModule
from .ml_module import (
    MLCapabilitiesModule,
    ProphetModelWrapper,
    SklearnModelWrapper,
    TrendExtrapolationWrapper,
)

# --- modules ---
from .prompt_module import PromptEngineeringModule, TaskCategoryAnalyzer, get_task_analyzer
from .round_table_module import PRODUCTION_ROUND_TABLE_AVAILABLE, LLMRoundTableInterface

# --- types ---
from .types import (
    AGENT_PROVIDER_PREFERENCES,
    HIGH_STAKES_AGENT_TYPES,
    HIGH_STAKES_TASK_TYPES,
    ROUND_TABLE_QUALITY_THRESHOLD,
    ROUND_TABLE_SCORING_WEIGHTS,
    TASK_PROVIDER_PREFERENCES,
    LearningRecord,
    LLMProvider,
    MLPrediction,
    PromptTechniqueResult,
    RoundTableEntry,
    RoundTableResult,
    SuperAgentType,
    TaskCategory,
)

__all__ = [
    # Types
    "SuperAgentType",
    "TaskCategory",
    "LLMProvider",
    # Provider preferences (for routing)
    "AGENT_PROVIDER_PREFERENCES",
    "TASK_PROVIDER_PREFERENCES",
    # Data classes
    "PromptTechniqueResult",
    "MLPrediction",
    "LearningRecord",
    "RoundTableEntry",
    "RoundTableResult",
    # Modules
    "PromptEngineeringModule",
    "MLCapabilitiesModule",
    "SelfLearningModule",
    "LLMRoundTableInterface",
    # ML wrappers
    "SklearnModelWrapper",
    "ProphetModelWrapper",
    "TrendExtrapolationWrapper",
    # Task Analysis
    "TaskCategoryAnalyzer",
    "get_task_analyzer",
    # Base class
    "EnhancedSuperAgent",
    # Availability flags
    "LLM_ROUTER_AVAILABLE",
    "PRODUCTION_ROUND_TABLE_AVAILABLE",
    # Round Table configuration
    "ROUND_TABLE_QUALITY_THRESHOLD",
    "HIGH_STAKES_TASK_TYPES",
    "HIGH_STAKES_AGENT_TYPES",
    "ROUND_TABLE_SCORING_WEIGHTS",
]
