"""
Super Agent Types, Constants, and Data Classes
================================================

Enums, provider preferences, Round Table configuration, and
data classes used throughout the super agent modules.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from orchestration.prompt_engineering import PromptTechnique

# =============================================================================
# Enums
# =============================================================================


class SuperAgentType(StrEnum):
    """Types of super agents"""

    COMMERCE = "commerce"
    CREATIVE = "creative"
    MARKETING = "marketing"
    SUPPORT = "support"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"


class TaskCategory(StrEnum):
    """Task categories for technique auto-selection"""

    REASONING = "reasoning"
    CLASSIFICATION = "classification"
    CREATIVE = "creative"
    SEARCH = "search"
    QA = "qa"
    EXTRACTION = "extraction"
    MODERATION = "moderation"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    DEBUGGING = "debugging"
    OPTIMIZATION = "optimization"


class LLMProvider(StrEnum):
    """LLM providers for Round Table"""

    CLAUDE = "claude"
    GPT4 = "gpt4"
    GEMINI = "gemini"
    LLAMA = "llama"
    MISTRAL = "mistral"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


# =============================================================================
# Provider Preferences per Agent Type
# =============================================================================

# Maps SuperAgentType to preferred ModelProvider order
# Based on provider strengths for each domain
AGENT_PROVIDER_PREFERENCES: dict[str, list[str]] = {
    "commerce": ["anthropic", "openai", "google"],  # Anthropic for accuracy in transactions
    "creative": ["openai", "anthropic", "google"],  # OpenAI for creativity + DALL-E
    "marketing": ["google", "anthropic", "openai"],  # Google for trend awareness
    "support": ["anthropic", "openai", "google"],  # Anthropic for empathy, tone
    "operations": ["openai", "anthropic", "groq"],  # OpenAI for code execution
    "analytics": ["anthropic", "openai", "google"],  # Anthropic for reasoning
}

# Task-specific provider overrides
TASK_PROVIDER_PREFERENCES: dict[str, list[str]] = {
    "reasoning": ["anthropic", "openai"],
    "creative": ["openai", "anthropic"],
    "code": ["openai", "anthropic", "groq"],
    "analysis": ["anthropic", "google"],
    "search": ["google", "openai"],
    "classification": ["openai", "anthropic"],
}


# =============================================================================
# Round Table Configuration
# =============================================================================

# Quality threshold to trigger Round Table (0-1)
ROUND_TABLE_QUALITY_THRESHOLD = 0.8

# High-stakes task types that ALWAYS use Round Table
HIGH_STAKES_TASK_TYPES: set[str] = {
    "commerce_transaction",  # Financial transactions
    "payment_processing",  # Payment handling
    "security_audit",  # Security-related tasks
    "data_deletion",  # Destructive operations
    "user_authentication",  # Auth-related tasks
    "inventory_update",  # Stock changes
    "pricing_change",  # Price modifications
    "order_fulfillment",  # Order processing
    "refund_processing",  # Refund handling
    "customer_pii",  # Handling PII data
}

# Agent types that default to Round Table for important decisions
HIGH_STAKES_AGENT_TYPES: set[str] = {
    "commerce",  # All commerce agents use Round Table for transactions
    "operations",  # Operations for deployment decisions
}

# Round Table scoring weights
ROUND_TABLE_SCORING_WEIGHTS = {
    "relevance": 0.30,  # How relevant is the response to the prompt
    "quality": 0.30,  # Overall quality and coherence
    "completeness": 0.20,  # Does it fully address the request
    "efficiency": 0.20,  # Response efficiency (not too verbose/terse)
}


# =============================================================================
# Data Classes
# =============================================================================


@dataclass(slots=True)
class PromptTechniqueResult:
    """Result from applying a prompt technique. Memory-optimized with __slots__."""

    technique: PromptTechnique
    original_prompt: str
    enhanced_prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    task_category: TaskCategory | None = None
    selection_reason: str = ""


@dataclass
class MLPrediction:
    """Result from ML inference"""

    task: str
    prediction: Any
    confidence: float
    model_used: str
    latency_ms: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LearningRecord:
    """Record for self-learning module"""

    task_id: str
    task_type: str
    prompt_hash: str
    technique_used: PromptTechnique
    llm_provider: str
    success: bool
    latency_ms: float
    cost_usd: float
    user_feedback: float | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RoundTableEntry:
    """Entry for LLM Round Table competition"""

    provider: LLMProvider
    response: str
    latency_ms: float
    cost_usd: float
    scores: dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0


@dataclass
class RoundTableResult:
    """Result from LLM Round Table"""

    task_id: str
    prompt: str
    entries: list[RoundTableEntry]
    top_two: list[RoundTableEntry]
    winner: RoundTableEntry
    judge_reasoning: str
    ab_test_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


__all__ = [
    "SuperAgentType",
    "TaskCategory",
    "LLMProvider",
    "AGENT_PROVIDER_PREFERENCES",
    "TASK_PROVIDER_PREFERENCES",
    "ROUND_TABLE_QUALITY_THRESHOLD",
    "HIGH_STAKES_TASK_TYPES",
    "HIGH_STAKES_AGENT_TYPES",
    "ROUND_TABLE_SCORING_WEIGHTS",
    "PromptTechniqueResult",
    "MLPrediction",
    "LearningRecord",
    "RoundTableEntry",
    "RoundTableResult",
]
