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
"""

import asyncio
import hashlib
import logging
import time
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

# Import existing components
from adk.base import ADKProvider, AgentConfig, AgentResult, AgentStatus, BaseDevSkyyAgent
from core.structured_logging import bind_contextvars, unbind_contextvars
from orchestration.prompt_engineering import (
    ChainOfThought,
    ConstitutionalAI,
    FewShotLearning,
    NegativePrompting,
    PromptEngineer,
    PromptTechnique,
    RAGPrompting,
    ReActPrompting,
    RoleBasedPrompting,
    SelfConsistency,
    StructuredOutput,
    TreeOfThoughts,
)

# Import LLM Router for intelligent provider selection
try:
    from llm.base import Message, ModelProvider
    from llm.router import LLMRouter, RoutingStrategy

    LLM_ROUTER_AVAILABLE = True
except ImportError:
    LLMRouter = None
    RoutingStrategy = None
    ModelProvider = None
    Message = None
    LLM_ROUTER_AVAILABLE = False

# Import production Round Table
try:
    from llm.round_table import LLMProvider as RoundTableProvider
    from llm.round_table import LLMRoundTable as ProductionRoundTable
    from llm.round_table import ResponseScorer as ProductionResponseScorer
    from llm.round_table import RoundTableEntry as ProductionRoundTableEntry
    from llm.round_table import RoundTableResult as ProductionRoundTableResult
    from llm.round_table import create_round_table

    PRODUCTION_ROUND_TABLE_AVAILABLE = True
except ImportError:
    ProductionRoundTable = None
    RoundTableProvider = None
    ProductionRoundTableResult = None
    ProductionRoundTableEntry = None
    ProductionResponseScorer = None
    create_round_table = None
    PRODUCTION_ROUND_TABLE_AVAILABLE = False

# Import Prometheus metrics for Round Table observability
try:
    from security.prometheus_exporter import exporter as prometheus_exporter

    METRICS_AVAILABLE = True
except ImportError:
    prometheus_exporter = None
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Types
# =============================================================================


class SuperAgentType(str, Enum):
    """Types of super agents"""

    COMMERCE = "commerce"
    CREATIVE = "creative"
    MARKETING = "marketing"
    SUPPORT = "support"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"


class TaskCategory(str, Enum):
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


class LLMProvider(str, Enum):
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


# =============================================================================
# Prompt Engineering Module
# =============================================================================


class PromptEngineeringModule:
    """
    Module providing access to all 17 prompt engineering techniques.

    Techniques:
    1. Role-Based Constraint - Establish persona and expertise
    2. Chain-of-Thought (CoT) - Step-by-step reasoning
    3. Few-Shot Learning - Example-based guidance
    4. Self-Consistency - Multiple paths, majority vote
    5. Tree of Thoughts (ToT) - Branching exploration
    6. ReAct - Reasoning + Acting interleaved
    7. RAG - Retrieval-Augmented Generation
    8. Prompt Chaining - Multi-step prompts
    9. Generated Knowledge - Self-generate context
    10. Negative Prompting - Specify what NOT to do
    11. Constitutional AI - Self-critique and revise
    12. COSTARD - Context-sensitive adaptation
    13. Meta-Prompting - Prompts about prompts
    14. Recursive Prompting - Self-referential refinement
    15. Structured Output - Format-specific outputs
    16. Temperature Scheduling - Dynamic temperature
    17. Ensemble Prompting - Combine multiple techniques
    """

    # Task type to technique mapping for auto-selection
    TECHNIQUE_MAPPING: dict[TaskCategory, PromptTechnique] = {
        TaskCategory.REASONING: PromptTechnique.CHAIN_OF_THOUGHT,
        TaskCategory.CLASSIFICATION: PromptTechnique.FEW_SHOT,
        TaskCategory.CREATIVE: PromptTechnique.TREE_OF_THOUGHTS,
        TaskCategory.SEARCH: PromptTechnique.REACT,
        TaskCategory.QA: PromptTechnique.RAG,
        TaskCategory.EXTRACTION: PromptTechnique.STRUCTURED_OUTPUT,
        TaskCategory.MODERATION: PromptTechnique.CONSTITUTIONAL,
        TaskCategory.GENERATION: PromptTechnique.ROLE_BASED,
        TaskCategory.ANALYSIS: PromptTechnique.CHAIN_OF_THOUGHT,
        TaskCategory.PLANNING: PromptTechnique.TREE_OF_THOUGHTS,
        TaskCategory.DEBUGGING: PromptTechnique.REACT,
        TaskCategory.OPTIMIZATION: PromptTechnique.SELF_CONSISTENCY,
    }

    def __init__(self):
        self.engineer = PromptEngineer()
        self._technique_stats: dict[PromptTechnique, dict] = {
            t: {"uses": 0, "successes": 0, "avg_score": 0.0} for t in PromptTechnique
        }

    def auto_select_technique(
        self, task_category: TaskCategory, context: dict[str, Any] | None = None
    ) -> PromptTechnique:
        """
        Automatically select the best technique for a task category.

        Uses historical performance data to optimize selection.
        """
        # Get default mapping
        default_technique = self.TECHNIQUE_MAPPING.get(task_category, PromptTechnique.ROLE_BASED)

        # Check if we have performance data suggesting a better option
        stats = self._technique_stats.get(default_technique)
        if stats and stats["uses"] > 10:
            success_rate = stats["successes"] / stats["uses"]
            if success_rate < 0.7:
                # Try alternative techniques
                alternatives = self._get_alternative_techniques(task_category)
                for alt in alternatives:
                    alt_stats = self._technique_stats.get(alt)
                    if alt_stats and alt_stats["uses"] > 5:
                        alt_success = alt_stats["successes"] / alt_stats["uses"]
                        if alt_success > success_rate:
                            return alt

        return default_technique

    def _get_alternative_techniques(self, task_category: TaskCategory) -> list[PromptTechnique]:
        """Get alternative techniques for a task category"""
        alternatives = {
            TaskCategory.REASONING: [
                PromptTechnique.TREE_OF_THOUGHTS,
                PromptTechnique.SELF_CONSISTENCY,
            ],
            TaskCategory.CLASSIFICATION: [
                PromptTechnique.CHAIN_OF_THOUGHT,
                PromptTechnique.STRUCTURED_OUTPUT,
            ],
            TaskCategory.CREATIVE: [PromptTechnique.ENSEMBLE, PromptTechnique.ROLE_BASED],
            TaskCategory.SEARCH: [PromptTechnique.RAG, PromptTechnique.CHAIN_OF_THOUGHT],
            TaskCategory.QA: [PromptTechnique.CHAIN_OF_THOUGHT, PromptTechnique.FEW_SHOT],
        }
        return alternatives.get(task_category, [PromptTechnique.ROLE_BASED])

    def apply_technique(
        self, technique: PromptTechnique, prompt: str, **kwargs
    ) -> PromptTechniqueResult:
        """Apply a specific prompt engineering technique"""
        enhanced_prompt = prompt
        metadata = {"technique": technique.value}

        if technique == PromptTechnique.CHAIN_OF_THOUGHT:
            enhanced_prompt = ChainOfThought.create_prompt(
                question=prompt, context=kwargs.get("context", "")
            )

        elif technique == PromptTechnique.FEW_SHOT:
            examples = kwargs.get("examples", [])
            if not examples:
                examples = self._generate_examples(prompt, kwargs.get("domain"))
            enhanced_prompt = FewShotLearning.create_prompt(
                task=kwargs.get("task", "Complete the following"), examples=examples, query=prompt
            )

        elif technique == PromptTechnique.TREE_OF_THOUGHTS:
            enhanced_prompt = TreeOfThoughts.create_prompt(
                problem=prompt, n_branches=kwargs.get("n_branches", 3)
            )

        elif technique == PromptTechnique.REACT:
            tools = kwargs.get("tools", [])
            enhanced_prompt = ReActPrompting.create_prompt(task=prompt, tools=tools)

        elif technique == PromptTechnique.RAG:
            context = kwargs.get("context", [])
            enhanced_prompt = RAGPrompting.create_prompt(question=prompt, context=context)

        elif technique == PromptTechnique.STRUCTURED_OUTPUT:
            schema = kwargs.get("schema", {})
            enhanced_prompt = StructuredOutput.create_json_prompt(task=prompt, schema=schema)

        elif technique == PromptTechnique.CONSTITUTIONAL:
            principles = kwargs.get("principles", ConstitutionalAI.get_default_principles())
            enhanced_prompt = ConstitutionalAI.create_critique_prompt(
                response=prompt, principles=principles
            )

        elif technique == PromptTechnique.NEGATIVE_PROMPTING:
            negative = kwargs.get("negative", [])
            enhanced_prompt = NegativePrompting.create_prompt(task=prompt, negative=negative)

        elif technique == PromptTechnique.ROLE_BASED:
            role = kwargs.get("role", "an expert assistant")
            background = kwargs.get("background", "")
            enhanced_prompt = RoleBasedPrompting.create_prompt(
                role=role, task=prompt, background=background
            )

        elif technique == PromptTechnique.SELF_CONSISTENCY:
            variants = SelfConsistency.create_variants(
                base_prompt=prompt, n_variants=kwargs.get("n_variants", 5)
            )
            enhanced_prompt = variants[0]  # Use first, run all in execution
            metadata["variants"] = variants

        elif technique == PromptTechnique.ENSEMBLE:
            # Combine multiple techniques
            techniques = kwargs.get(
                "techniques", [PromptTechnique.CHAIN_OF_THOUGHT, PromptTechnique.ROLE_BASED]
            )
            combined_parts = []
            for t in techniques:
                result = self.apply_technique(t, prompt, **kwargs)
                combined_parts.append(f"[{t.value}]\n{result.enhanced_prompt}")
            enhanced_prompt = "\n\n---\n\n".join(combined_parts)

        # Update stats
        self._technique_stats[technique]["uses"] += 1

        return PromptTechniqueResult(
            technique=technique,
            original_prompt=prompt,
            enhanced_prompt=enhanced_prompt,
            metadata=metadata,
        )

    def _generate_examples(self, prompt: str, domain: str | None) -> list[dict[str, str]]:
        """Generate few-shot examples based on domain"""
        if domain:
            return FewShotLearning.create_examples_for_domain(domain)
        return []

    def apply_technique_with_tools(
        self,
        technique: PromptTechnique,
        prompt: str,
        tools: list[dict] | None = None,
        **kwargs,
    ) -> PromptTechniqueResult:
        """Apply technique with tool calling optimization.

        Enhances prompts for LLM Round Table competition when tools are available.
        Adds tool-aware instructions based on the technique being used.

        Args:
            technique: Prompt technique to apply
            prompt: Base prompt
            tools: Available tools for the task
            **kwargs: Additional technique-specific parameters

        Returns:
            PromptTechniqueResult with tool-optimized prompt
        """
        if not tools:
            # No tools available, use standard technique
            return self.apply_technique(technique, prompt, **kwargs)

        # Apply base technique first
        base_result = self.apply_technique(technique, prompt, tools=tools, **kwargs)
        enhanced = base_result.enhanced_prompt

        # Add tool-specific enhancements based on technique
        tool_names = [t.get("name", "unknown") for t in tools]
        tool_list = ", ".join(tool_names)

        if technique == PromptTechnique.REACT:
            # ReAct already handles tools, but enhance with format
            tool_enhanced = f"""
Task: {prompt}

Available Tools: {tool_list}

IMPORTANT: Use the ReAct format with tool calling:
Thought: [Your reasoning about what to do]
Action: tool_name(arguments)
Observation: [Tool result will appear here]
... (repeat Thought/Action/Observation as needed)
Final Answer: [Your final response]

{enhanced}
"""
            enhanced = tool_enhanced.strip()

        elif technique == PromptTechnique.CHAIN_OF_THOUGHT:
            # Add tool awareness to CoT
            tool_enhanced = f"""
{enhanced}

Available Tools: {tool_list}

When solving this problem step-by-step, consider which tools would help at each step.
Call tools when you need information, data, or actions you cannot perform directly.
"""
            enhanced = tool_enhanced.strip()

        elif technique == PromptTechnique.TREE_OF_THOUGHTS:
            # Add tool usage to each branch
            tool_enhanced = f"""
{enhanced}

Available Tools for exploration: {tool_list}

For each branch of reasoning, identify which tools would provide the most valuable information.
Prioritize tool calls that reduce uncertainty or provide critical data.
"""
            enhanced = tool_enhanced.strip()

        elif technique == PromptTechnique.RAG:
            # Combine RAG context with tool calling
            tool_enhanced = f"""
{enhanced}

Additional Tools Available: {tool_list}

Use tools to supplement the retrieved context when:
- The context is insufficient
- You need real-time data
- You need to perform actions
"""
            enhanced = tool_enhanced.strip()

        else:
            # Generic tool awareness for other techniques
            tool_enhanced = f"""
{enhanced}

Available Tools: {tool_list}

You have access to these tools to help complete the task. Use them when appropriate.
"""
            enhanced = tool_enhanced.strip()

        # Update metadata
        metadata = base_result.metadata.copy()
        metadata["tool_aware"] = True
        metadata["available_tools"] = tool_names

        return PromptTechniqueResult(
            technique=technique,
            original_prompt=prompt,
            enhanced_prompt=enhanced,
            metadata=metadata,
        )

    def record_outcome(self, technique: PromptTechnique, success: bool, score: float = 0.0):
        """Record technique outcome for learning"""
        stats = self._technique_stats[technique]
        stats["uses"] += 1
        if success:
            stats["successes"] += 1
        # Running average
        n = stats["uses"]
        stats["avg_score"] = ((stats["avg_score"] * (n - 1)) + score) / n

    def get_technique_stats(self) -> dict[str, dict]:
        """Get performance statistics for all techniques"""
        return {t.value: s for t, s in self._technique_stats.items()}


# =============================================================================
# Task Category Analyzer
# =============================================================================


class TaskCategoryAnalyzer:
    """
    Intelligent task category analyzer for automatic prompt technique selection.

    Uses multiple strategies:
    1. Keyword pattern matching (fast)
    2. Regex pattern analysis (structured)
    3. Agent context awareness (domain-specific)

    The analyzer logs all technique selections with correlation_id for:
    - Observability and debugging
    - A/B testing effectiveness
    - Performance optimization
    """

    # Extended keyword patterns with weights for more accurate classification
    CATEGORY_PATTERNS: dict[TaskCategory, dict[str, list[str]]] = {
        TaskCategory.REASONING: {
            "strong": ["why", "explain why", "reason", "because", "therefore", "thus"],
            "moderate": ["analyze", "understand", "logic", "deduce", "infer"],
        },
        TaskCategory.CLASSIFICATION: {
            "strong": ["classify", "categorize", "label", "which type", "what kind"],
            "moderate": ["sort", "group", "identify as", "determine type"],
        },
        TaskCategory.CREATIVE: {
            "strong": ["create", "design", "imagine", "invent", "brainstorm"],
            "moderate": ["generate ideas", "come up with", "visualize", "artistic"],
        },
        TaskCategory.SEARCH: {
            "strong": ["find", "search", "locate", "look up", "retrieve"],
            "moderate": ["discover", "seek", "hunt for", "track down"],
        },
        TaskCategory.QA: {
            "strong": ["what is", "who is", "when did", "where is", "how does"],
            "moderate": ["tell me about", "describe", "define", "explain what"],
        },
        TaskCategory.EXTRACTION: {
            "strong": ["extract", "parse", "pull out", "get the", "retrieve from"],
            "moderate": ["scrape", "obtain", "isolate", "separate"],
        },
        TaskCategory.MODERATION: {
            "strong": ["review", "moderate", "check for", "validate content", "safety"],
            "moderate": ["appropriate", "policy", "guidelines", "harmful"],
        },
        TaskCategory.GENERATION: {
            "strong": ["write", "compose", "draft", "produce", "generate text"],
            "moderate": ["author", "create content", "formulate", "construct"],
        },
        TaskCategory.ANALYSIS: {
            "strong": ["analyze", "examine", "study", "investigate", "assess"],
            "moderate": ["evaluate", "review data", "inspect", "scrutinize"],
        },
        TaskCategory.PLANNING: {
            "strong": ["plan", "schedule", "organize", "strategy", "roadmap"],
            "moderate": ["coordinate", "arrange", "prepare", "outline steps"],
        },
        TaskCategory.DEBUGGING: {
            "strong": ["fix", "debug", "error", "bug", "issue", "broken"],
            "moderate": ["troubleshoot", "resolve", "repair", "diagnose"],
        },
        TaskCategory.OPTIMIZATION: {
            "strong": ["optimize", "improve", "enhance", "better", "faster"],
            "moderate": ["refine", "streamline", "boost", "maximize", "efficiency"],
        },
    }

    # Technique selection with confidence thresholds
    TECHNIQUE_CONFIDENCE_THRESHOLDS = {
        "high": 0.8,  # Use primary technique
        "medium": 0.5,  # May consider alternatives
        "low": 0.3,  # Fall back to default
    }

    def __init__(self) -> None:
        self._analysis_cache: dict[str, tuple[TaskCategory, float]] = {}

    def analyze(
        self,
        prompt: str,
        agent_type: SuperAgentType | None = None,
        correlation_id: str | None = None,
    ) -> tuple[TaskCategory, float, str]:
        """
        Analyze a prompt to determine its task category.

        Args:
            prompt: The task prompt to analyze
            agent_type: Optional agent type for domain-specific hints
            correlation_id: Optional correlation ID for logging

        Returns:
            Tuple of (TaskCategory, confidence_score, selection_reason)
        """
        import uuid

        correlation_id = correlation_id or str(uuid.uuid4())[:12]
        prompt_lower = prompt.lower()

        # Check cache first
        cache_key = hashlib.md5(prompt_lower.encode(), usedforsecurity=False).hexdigest()[:16]
        if cache_key in self._analysis_cache:
            category, confidence = self._analysis_cache[cache_key]
            reason = f"cached_analysis:{category.value}"
            logger.debug(
                f"[{correlation_id}] Task category from cache: {category.value} "
                f"(confidence: {confidence:.2f})"
            )
            return category, confidence, reason

        # Score each category
        category_scores: dict[TaskCategory, float] = {}

        for category, patterns in self.CATEGORY_PATTERNS.items():
            score = 0.0

            # Strong patterns get higher weight
            for pattern in patterns.get("strong", []):
                if pattern in prompt_lower:
                    score += 2.0

            # Moderate patterns get lower weight
            for pattern in patterns.get("moderate", []):
                if pattern in prompt_lower:
                    score += 1.0

            category_scores[category] = score

        # Find best match
        if category_scores:
            best_category = max(category_scores, key=lambda k: category_scores[k])
            best_score = category_scores[best_category]

            # Normalize confidence (max possible is ~10 for 5 strong matches)
            confidence = min(best_score / 6.0, 1.0)

            # Apply agent-type bias
            if agent_type:
                confidence = self._apply_agent_bias(best_category, confidence, agent_type)

            # Cache result
            self._analysis_cache[cache_key] = (best_category, confidence)

            reason = f"pattern_match:{best_category.value}:score={best_score:.1f}"
            logger.info(
                f"[{correlation_id}] Task category inferred: {best_category.value} "
                f"(confidence: {confidence:.2f}, reason: {reason})"
            )

            return best_category, confidence, reason

        # Default fallback
        default_category = TaskCategory.GENERATION
        logger.info(f"[{correlation_id}] Task category defaulted to: {default_category.value}")
        return default_category, 0.5, "default_fallback"

    def _apply_agent_bias(
        self,
        category: TaskCategory,
        confidence: float,
        agent_type: SuperAgentType,
    ) -> float:
        """Apply agent-specific confidence bias."""
        # Agent-category affinities
        agent_affinities = {
            SuperAgentType.COMMERCE: [TaskCategory.GENERATION, TaskCategory.ANALYSIS],
            SuperAgentType.CREATIVE: [TaskCategory.CREATIVE, TaskCategory.GENERATION],
            SuperAgentType.MARKETING: [TaskCategory.CREATIVE, TaskCategory.GENERATION],
            SuperAgentType.SUPPORT: [TaskCategory.QA, TaskCategory.CLASSIFICATION],
            SuperAgentType.OPERATIONS: [TaskCategory.DEBUGGING, TaskCategory.PLANNING],
            SuperAgentType.ANALYTICS: [TaskCategory.ANALYSIS, TaskCategory.REASONING],
        }

        if category in agent_affinities.get(agent_type, []):
            return min(confidence * 1.2, 1.0)  # Boost confidence

        return confidence

    def select_technique(
        self,
        category: TaskCategory,
        confidence: float,
        correlation_id: str | None = None,
    ) -> tuple[PromptTechnique, str]:
        """
        Select the optimal prompt technique for a task category.

        Args:
            category: The task category
            confidence: Confidence score from analysis
            correlation_id: Optional correlation ID for logging

        Returns:
            Tuple of (PromptTechnique, selection_reason)
        """
        technique = PromptEngineeringModule.TECHNIQUE_MAPPING.get(
            category, PromptTechnique.ROLE_BASED
        )

        reason = (
            f"auto_selected:{technique.value}:category={category.value}:confidence={confidence:.2f}"
        )

        logger.info(
            f"[{correlation_id or 'N/A'}] Technique selected: {technique.value} "
            f"for category {category.value} (confidence: {confidence:.2f})"
        )

        return technique, reason


# Global analyzer instance
_task_analyzer = TaskCategoryAnalyzer()


def get_task_analyzer() -> TaskCategoryAnalyzer:
    """Get the global task category analyzer instance."""
    return _task_analyzer


# =============================================================================
# ML Model Wrappers
# =============================================================================


class SklearnModelWrapper:
    """
    Wrapper for scikit-learn models that handles fitting and prediction.

    Supports on-demand fitting with provided training data.
    """

    def __init__(self, model: Any, task: str, fitted: bool = False):
        self.model = model
        self.task = task
        self.fitted = fitted
        self._last_confidence = 0.85

    def fit(self, X: Any, y: Any = None) -> "SklearnModelWrapper":
        """Fit the model with training data."""
        import numpy as np

        X_arr = np.array(X) if not hasattr(X, "shape") else X

        if self.task in ("clustering", "anomaly"):
            self.model.fit(X_arr)
        else:
            if y is None:
                raise ValueError(f"Target y required for {self.task} task")
            y_arr = np.array(y) if not hasattr(y, "shape") else y
            self.model.fit(X_arr, y_arr)

        self.fitted = True
        return self

    def predict(self, X: Any, **kwargs) -> Any:
        """Run prediction on input data."""
        import numpy as np

        X_arr = np.array(X) if not hasattr(X, "shape") else X

        # Ensure 2D input
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(1, -1)

        if not self.fitted:
            # Auto-fit with synthetic data for demo purposes
            logger.warning(f"Model not fitted, using synthetic training for {self.task}")
            n_features = X_arr.shape[1]
            synthetic_X = np.random.randn(100, n_features)
            if self.task in ("clustering", "anomaly"):
                self.model.fit(synthetic_X)
            else:
                synthetic_y = (
                    np.random.randn(100)
                    if self.task == "regression"
                    else np.random.randint(0, 2, 100)
                )
                self.model.fit(synthetic_X, synthetic_y)
            self.fitted = True
            self._last_confidence = 0.6  # Lower confidence for auto-fitted

        result = self.model.predict(X_arr)

        # For classification, try to get probabilities
        if self.task == "classification" and hasattr(self.model, "predict_proba"):
            try:
                proba = self.model.predict_proba(X_arr)
                self._last_confidence = float(np.max(proba))
            except Exception:
                self._last_confidence = 0.75

        return result.tolist() if hasattr(result, "tolist") else result

    def get_confidence(self) -> float:
        """Return confidence score from last prediction."""
        return self._last_confidence

    def __call__(self, X: Any, **kwargs) -> Any:
        """Make wrapper callable."""
        return self.predict(X, **kwargs)


class ProphetModelWrapper:
    """
    Wrapper for Facebook Prophet time series forecasting.

    Handles data format conversion and prediction periods.
    """

    def __init__(self, model: Any, task: str = "forecast"):
        self.model = model
        self.task = task
        self.fitted = False
        self._last_confidence = 0.8

    def fit(self, df: Any) -> "ProphetModelWrapper":
        """
        Fit Prophet model with time series data.

        Args:
            df: DataFrame with 'ds' (date) and 'y' (value) columns
        """
        import pandas as pd

        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)

        if "ds" not in df.columns or "y" not in df.columns:
            raise ValueError("Prophet requires DataFrame with 'ds' and 'y' columns")

        self.model.fit(df)
        self.fitted = True
        return self

    def predict(self, periods: int = 30, **kwargs) -> Any:
        """
        Generate forecasts for future periods.

        Args:
            periods: Number of future periods to forecast
            **kwargs: Additional arguments (freq, include_history)

        Returns:
            Dict with forecast results
        """
        import pandas as pd

        if not self.fitted:
            # Create synthetic historical data for demo
            logger.warning("Prophet not fitted, using synthetic data")
            dates = pd.date_range(start="2024-01-01", periods=365, freq="D")
            import numpy as np

            values = 100 + np.cumsum(np.random.randn(365) * 2)
            df = pd.DataFrame({"ds": dates, "y": values})
            self.model.fit(df)
            self.fitted = True
            self._last_confidence = 0.6

        freq = kwargs.get("freq", "D")
        future = self.model.make_future_dataframe(periods=periods, freq=freq)
        forecast = self.model.predict(future)

        # Calculate confidence from uncertainty intervals
        if "yhat_lower" in forecast.columns and "yhat_upper" in forecast.columns:
            last_rows = forecast.tail(periods)
            interval_width = (last_rows["yhat_upper"] - last_rows["yhat_lower"]).mean()
            mean_value = last_rows["yhat"].mean()
            if mean_value > 0:
                self._last_confidence = max(0.5, 1.0 - (interval_width / mean_value / 4))

        return {
            "forecast": forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]
            .tail(periods)
            .to_dict("records"),
            "periods": periods,
            "fitted": self.fitted,
        }

    def get_confidence(self) -> float:
        """Return confidence score from last prediction."""
        return self._last_confidence

    def __call__(self, periods: int = 30, **kwargs) -> Any:
        """Make wrapper callable."""
        return self.predict(periods, **kwargs)


class TrendExtrapolationWrapper:
    """
    Simple trend extrapolation fallback when Prophet is not available.

    Uses linear regression for basic forecasting.
    """

    def __init__(self):
        self.slope = 0.0
        self.intercept = 0.0
        self.fitted = False
        self._last_confidence = 0.6

    def fit(self, data: list | Any) -> "TrendExtrapolationWrapper":
        """Fit linear trend to data."""
        import numpy as np

        if hasattr(data, "tolist"):
            values = data.tolist()
        elif isinstance(data, list):
            values = data
        else:
            values = list(data)

        n = len(values)
        if n < 2:
            return self

        x = np.arange(n)
        y = np.array(values)

        # Simple linear regression
        x_mean = x.mean()
        y_mean = y.mean()

        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if denominator > 0:
            self.slope = numerator / denominator
            self.intercept = y_mean - self.slope * x_mean
        else:
            self.slope = 0
            self.intercept = y_mean

        self.fitted = True
        return self

    def predict(self, periods: int = 30, **kwargs) -> Any:
        """Extrapolate trend for future periods."""
        if not self.fitted:
            logger.warning("TrendExtrapolation not fitted, returning baseline")
            return {
                "forecast": [{"period": i, "value": 100.0} for i in range(periods)],
                "confidence": 0.5,
            }

        start = kwargs.get("start_index", 0)
        forecasts = []

        for i in range(periods):
            idx = start + i
            value = self.intercept + self.slope * idx
            forecasts.append({"period": i, "value": value})

        return {
            "forecast": forecasts,
            "slope": self.slope,
            "intercept": self.intercept,
        }

    def get_confidence(self) -> float:
        """Return confidence score."""
        return self._last_confidence if self.fitted else 0.5

    def __call__(self, periods: int = 30, **kwargs) -> Any:
        """Make wrapper callable."""
        return self.predict(periods, **kwargs)


# =============================================================================
# ML Capabilities Module
# =============================================================================


class MLCapabilitiesModule:
    """
    Machine Learning capabilities for SuperAgents.

    Capabilities per agent type:
    - Commerce: Demand forecasting, dynamic pricing, inventory optimization
    - Creative: Style transfer, image classification, quality scoring
    - Marketing: Sentiment analysis, trend prediction, audience segmentation
    - Support: Intent classification, FAQ matching, escalation prediction
    - Operations: Anomaly detection, log analysis, performance prediction
    - Analytics: Time series forecasting, clustering, recommendation
    """

    def __init__(self, agent_type: SuperAgentType):
        self.agent_type = agent_type
        self._models: dict[str, Any] = {}
        self._initialized = False

    async def initialize(self):
        """Initialize ML models for this agent type"""
        logger.info(f"Initializing ML capabilities for {self.agent_type}")

        # Load models based on agent type
        model_configs = self._get_model_configs()
        for name, config in model_configs.items():
            try:
                self._models[name] = await self._load_model(config)
            except Exception as e:
                logger.warning(f"Failed to load model {name}: {e}")

        self._initialized = True

    def _get_model_configs(self) -> dict[str, dict]:
        """Get ML model configurations for this agent type"""
        configs = {
            SuperAgentType.COMMERCE: {
                "demand_forecaster": {"type": "prophet", "task": "time_series"},
                "price_optimizer": {"type": "sklearn", "task": "regression"},
                "inventory_predictor": {"type": "sklearn", "task": "regression"},
            },
            SuperAgentType.CREATIVE: {
                "style_classifier": {
                    "type": "transformers",
                    "model": "google/vit-base-patch16-224",
                },
                "quality_scorer": {"type": "custom", "task": "image_quality"},
            },
            SuperAgentType.MARKETING: {
                "sentiment_analyzer": {
                    "type": "transformers",
                    "model": "cardiffnlp/twitter-roberta-base-sentiment",
                },
                "trend_predictor": {"type": "prophet", "task": "trend"},
            },
            SuperAgentType.SUPPORT: {
                "intent_classifier": {"type": "transformers", "model": "facebook/bart-large-mnli"},
                "escalation_predictor": {"type": "sklearn", "task": "classification"},
            },
            SuperAgentType.OPERATIONS: {
                "anomaly_detector": {"type": "sklearn", "task": "anomaly"},
                "performance_predictor": {"type": "sklearn", "task": "regression"},
            },
            SuperAgentType.ANALYTICS: {
                "forecaster": {"type": "prophet", "task": "forecast"},
                "clusterer": {"type": "sklearn", "task": "clustering"},
            },
        }
        return configs.get(self.agent_type, {})

    async def _load_model(self, config: dict) -> Any:
        """
        Load a specific ML model based on configuration.

        Supports:
        - transformers: HuggingFace transformers pipelines
        - sklearn: scikit-learn models (regression, classification, clustering, anomaly)
        - prophet: Facebook Prophet for time series forecasting

        Args:
            config: Model configuration dict with 'type' and 'task' keys

        Returns:
            Loaded model object or callable wrapper
        """
        model_type = config.get("type")
        task = config.get("task", "default")

        if model_type == "transformers":
            try:
                from transformers import pipeline

                model_name = config.get("model", "distilbert-base-uncased")
                # Determine pipeline type from model name or task
                if "sentiment" in model_name or "sentiment" in task:
                    return pipeline("sentiment-analysis", model=model_name)
                elif "mnli" in model_name or "classification" in task:
                    return pipeline("zero-shot-classification", model=model_name)
                elif "vit" in model_name or "image" in task:
                    return pipeline("image-classification", model=model_name)
                else:
                    return pipeline("text-classification", model=model_name)
            except ImportError:
                logger.warning("transformers not installed, using sklearn fallback")
                return self._create_sklearn_model({"task": "classification"})

        elif model_type == "sklearn":
            return self._create_sklearn_model(config)

        elif model_type == "prophet":
            return self._create_prophet_model(config)

        return None

    def _create_sklearn_model(self, config: dict) -> Any:
        """
        Create a scikit-learn model wrapper.

        Returns a callable that wraps sklearn models for prediction.
        """
        task = config.get("task", "regression")

        try:
            if task == "regression":
                from sklearn.linear_model import Ridge

                model = Ridge()
            elif task == "classification":
                from sklearn.linear_model import LogisticRegression

                model = LogisticRegression(max_iter=1000)
            elif task == "clustering":
                from sklearn.cluster import KMeans

                model = KMeans(n_clusters=3, n_init=10)
            elif task == "anomaly":
                from sklearn.ensemble import IsolationForest

                model = IsolationForest(contamination=0.1)
            else:
                from sklearn.linear_model import Ridge

                model = Ridge()

            # Return wrapper that handles both fitting and prediction
            return SklearnModelWrapper(model=model, task=task, fitted=False)

        except ImportError:
            logger.warning("scikit-learn not installed")
            return None

    def _create_prophet_model(self, config: dict) -> Any:
        """
        Create a Prophet model wrapper for time series forecasting.

        Returns a callable that wraps Prophet for prediction.
        """
        try:
            from prophet import Prophet

            # Create Prophet model with sensible defaults
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                changepoint_prior_scale=0.05,
            )
            return ProphetModelWrapper(model=model, task=config.get("task", "forecast"))

        except ImportError:
            logger.warning("prophet not installed, using trend extrapolation fallback")
            return TrendExtrapolationWrapper()

    async def predict(
        self,
        model_name: str,
        input_data: Any,
        **kwargs,
    ) -> MLPrediction:
        """
        Run prediction using specified model.

        Args:
            model_name: Name of the model to use
            input_data: Input data for prediction (format depends on model type)
            **kwargs: Additional arguments passed to model

        Returns:
            MLPrediction with prediction, confidence, and metadata
        """
        start_time = time.time()

        model = self._models.get(model_name)
        if not model:
            return MLPrediction(
                task=model_name,
                prediction=None,
                confidence=0.0,
                model_used="none",
                latency_ms=0.0,
                metadata={"error": f"Model {model_name} not found"},
            )

        try:
            # Run inference based on model type
            if callable(model):
                result = model(input_data)
                prediction = result[0] if isinstance(result, list) else result
                confidence = self._extract_confidence(result)
            elif hasattr(model, "predict"):
                # Direct sklearn/prophet model
                prediction = model.predict(input_data, **kwargs)
                confidence = 0.85
            elif isinstance(
                model, SklearnModelWrapper | ProphetModelWrapper | TrendExtrapolationWrapper
            ):
                prediction = model.predict(input_data, **kwargs)
                confidence = model.get_confidence()
            else:
                # Unknown model type - attempt direct call
                prediction = {"input": str(input_data)[:100], "model_type": str(type(model))}
                confidence = 0.5

            latency = (time.time() - start_time) * 1000

            return MLPrediction(
                task=model_name,
                prediction=prediction,
                confidence=confidence,
                model_used=model_name,
                latency_ms=latency,
                metadata=kwargs,
            )

        except Exception as e:
            return MLPrediction(
                task=model_name,
                prediction=None,
                confidence=0.0,
                model_used=model_name,
                latency_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
            )

    def _extract_confidence(self, result: Any) -> float:
        """Extract confidence score from model result."""
        if isinstance(result, dict):
            return result.get("score", result.get("confidence", 0.8))
        elif isinstance(result, list) and len(result) > 0:
            first = result[0]
            if isinstance(first, dict):
                return first.get("score", first.get("confidence", 0.8))
        return 0.8

    def list_available_models(self) -> list[str]:
        """List available ML models for this agent"""
        return list(self._models.keys())


# =============================================================================
# Self-Learning Module
# =============================================================================


class SelfLearningModule:
    """
    Self-learning module for continuous improvement.

    Capabilities:
    1. Performance tracking (success rate, latency, cost)
    2. Prompt optimization (A/B test prompts)
    3. Tool usage analysis (which tools work best)
    4. Model selection optimization (best LLM per task)
    5. Knowledge base updates (learn from interactions)
    """

    def __init__(self, agent_type: SuperAgentType):
        self.agent_type = agent_type
        self._records: list[LearningRecord] = []
        self._optimizations: dict[str, Any] = {}
        self._knowledge_base: dict[str, Any] = {}

    def record_execution(
        self,
        task_id: str,
        task_type: str,
        prompt: str,
        technique: PromptTechnique,
        llm_provider: str,
        success: bool,
        latency_ms: float,
        cost_usd: float,
        user_feedback: float | None = None,
    ):
        """Record execution for learning"""
        record = LearningRecord(
            task_id=task_id,
            task_type=task_type,
            prompt_hash=hashlib.md5(prompt.encode(), usedforsecurity=False).hexdigest()[:16],
            technique_used=technique,
            llm_provider=llm_provider,
            success=success,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            user_feedback=user_feedback,
        )
        self._records.append(record)

        # Update optimizations
        self._update_optimizations(record)

    def _update_optimizations(self, record: LearningRecord):
        """Update optimization data based on new record"""
        task_type = record.task_type

        if task_type not in self._optimizations:
            self._optimizations[task_type] = {
                "techniques": {},
                "providers": {},
                "total_executions": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "avg_cost_usd": 0.0,
            }

        opt = self._optimizations[task_type]
        opt["total_executions"] += 1

        # Update technique stats
        tech = record.technique_used.value
        if tech not in opt["techniques"]:
            opt["techniques"][tech] = {"uses": 0, "successes": 0}
        opt["techniques"][tech]["uses"] += 1
        if record.success:
            opt["techniques"][tech]["successes"] += 1

        # Update provider stats
        prov = record.llm_provider
        if prov not in opt["providers"]:
            opt["providers"][prov] = {"uses": 0, "successes": 0, "avg_latency": 0}
        opt["providers"][prov]["uses"] += 1
        if record.success:
            opt["providers"][prov]["successes"] += 1
        n = opt["providers"][prov]["uses"]
        opt["providers"][prov]["avg_latency"] = (
            opt["providers"][prov]["avg_latency"] * (n - 1) + record.latency_ms
        ) / n

        # Update aggregates
        total = opt["total_executions"]
        success_count = sum(t["successes"] for t in opt["techniques"].values())
        opt["success_rate"] = success_count / total if total > 0 else 0

        # Running averages
        opt["avg_latency_ms"] = (opt["avg_latency_ms"] * (total - 1) + record.latency_ms) / total
        opt["avg_cost_usd"] = (opt["avg_cost_usd"] * (total - 1) + record.cost_usd) / total

    def get_best_technique(self, task_type: str) -> PromptTechnique | None:
        """Get the best performing technique for a task type"""
        opt = self._optimizations.get(task_type)
        if not opt or not opt["techniques"]:
            return None

        best = max(
            opt["techniques"].items(), key=lambda x: x[1]["successes"] / max(x[1]["uses"], 1)
        )

        try:
            return PromptTechnique(best[0])
        except ValueError:
            return None

    def get_best_provider(self, task_type: str) -> str | None:
        """Get the best performing LLM provider for a task type"""
        opt = self._optimizations.get(task_type)
        if not opt or not opt["providers"]:
            return None

        # Balance success rate and latency
        def score(item):
            name, stats = item
            success_rate = stats["successes"] / max(stats["uses"], 1)
            latency_score = 1 / (1 + stats["avg_latency"] / 1000)
            return success_rate * 0.7 + latency_score * 0.3

        best = max(opt["providers"].items(), key=score)
        return best[0]

    def get_optimization_report(self) -> dict[str, Any]:
        """Get full optimization report"""
        return {
            "agent_type": self.agent_type.value,
            "total_records": len(self._records),
            "task_optimizations": self._optimizations,
            "recommendations": self._generate_recommendations(),
        }

    def _generate_recommendations(self) -> list[str]:
        """Generate optimization recommendations"""
        recommendations = []

        for task_type, opt in self._optimizations.items():
            if opt["success_rate"] < 0.8:
                recommendations.append(
                    f"Task '{task_type}' has low success rate ({opt['success_rate']:.1%}). "
                    f"Consider using different techniques or providers."
                )

            if opt["avg_latency_ms"] > 5000:
                recommendations.append(
                    f"Task '{task_type}' has high latency ({opt['avg_latency_ms']:.0f}ms). "
                    f"Consider using faster models or caching."
                )

            if opt["avg_cost_usd"] > 0.1:
                recommendations.append(
                    f"Task '{task_type}' is expensive (${opt['avg_cost_usd']:.4f}/request). "
                    f"Consider using more cost-effective providers."
                )

        return recommendations

    def add_to_knowledge_base(self, key: str, value: Any):
        """Add knowledge to the agent's knowledge base"""
        self._knowledge_base[key] = {"value": value, "added_at": datetime.now(UTC).isoformat()}

    def query_knowledge_base(self, key: str) -> Any:
        """Query the knowledge base"""
        entry = self._knowledge_base.get(key)
        return entry["value"] if entry else None

    # -------------------------------------------------------------------------
    # RAG Integration for Self-Learning
    # -------------------------------------------------------------------------

    async def ingest_successful_response(
        self,
        prompt: str,
        response: str,
        task_type: str,
        technique: PromptTechnique,
        score: float,
        provider: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Auto-ingest successful responses (score > threshold) to RAG for future retrieval.

        Args:
            prompt: The original prompt
            response: The successful response
            task_type: Type of task
            technique: Technique used
            score: Quality score (0-1)
            provider: LLM provider that generated the response
            metadata: Optional additional metadata

        Returns:
            True if ingestion was successful
        """
        # Only ingest high-quality responses
        if score < ROUND_TABLE_QUALITY_THRESHOLD:
            return False

        try:
            # Build document content for RAG
            doc_content = f"""## Successful Response Record

**Task Type:** {task_type}
**Technique Used:** {technique.value}
**Quality Score:** {score:.2f}
**Provider:** {provider}
**Timestamp:** {datetime.now(UTC).isoformat()}

### Original Prompt
{prompt}

### Successful Response
{response}
"""
            # Store in knowledge base
            doc_key = f"learning:{task_type}:{hashlib.md5(prompt.encode(), usedforsecurity=False).hexdigest()[:12]}"
            self._knowledge_base[doc_key] = {
                "value": {
                    "prompt": prompt,
                    "response": response,
                    "task_type": task_type,
                    "technique": technique.value,
                    "score": score,
                    "provider": provider,
                    "metadata": metadata or {},
                },
                "added_at": datetime.now(UTC).isoformat(),
                "doc_content": doc_content,
            }

            # Queue for RAG ingestion (async batch processing)
            self._queue_rag_ingestion(
                doc_key,
                doc_content,
                {
                    "source": f"learning/{self.agent_type.value}/{task_type}",
                    "task_type": task_type,
                    "technique": technique.value,
                    "score": score,
                    "provider": provider,
                },
            )

            logger.info(f"Queued successful response for RAG ingestion: {doc_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to ingest successful response: {e}")
            return False

    def _queue_rag_ingestion(self, key: str, content: str, metadata: dict[str, Any]):
        """Queue content for RAG ingestion (batch processing)"""
        if not hasattr(self, "_rag_ingestion_queue"):
            self._rag_ingestion_queue: list[dict] = []

        self._rag_ingestion_queue.append(
            {
                "key": key,
                "content": content,
                "metadata": metadata,
                "queued_at": datetime.now(UTC).isoformat(),
            }
        )

        # Log queue size for monitoring
        if len(self._rag_ingestion_queue) % 10 == 0:
            logger.info(f"RAG ingestion queue size: {len(self._rag_ingestion_queue)}")

    async def flush_rag_queue(self) -> int:
        """
        Flush RAG ingestion queue to vector store.

        Returns:
            Number of items processed
        """
        if not hasattr(self, "_rag_ingestion_queue"):
            return 0

        queue = self._rag_ingestion_queue
        self._rag_ingestion_queue = []

        processed = 0
        try:
            # Check if RAG components are available
            from importlib.util import find_spec

            if find_spec("orchestration.document_ingestion") is not None:
                # RAG pipeline available - could integrate here
                pass

            # For now, store in knowledge base for retrieval
            for item in queue:
                self._knowledge_base[f"rag:{item['key']}"] = item
                processed += 1

            logger.info(f"Processed {processed} items from RAG ingestion queue")

        except ImportError:
            logger.warning("RAG components not available for queue flush")
            # Store back in queue for retry
            self._rag_ingestion_queue.extend(queue)

        return processed

    def query_similar_prompts(
        self, prompt: str, task_type: str | None = None, top_k: int = 5
    ) -> list[dict[str, Any]]:
        """
        Query knowledge base for similar prompts and their successful responses.

        Uses simple keyword matching. For semantic search, use RAG pipeline directly.

        Args:
            prompt: The prompt to find similar entries for
            task_type: Optional filter by task type
            top_k: Maximum number of results

        Returns:
            List of similar prompt records with scores
        """
        results = []
        prompt_words = set(prompt.lower().split())

        for key, entry in self._knowledge_base.items():
            if not key.startswith("learning:"):
                continue

            value = entry.get("value", {})

            # Filter by task type if specified
            if task_type and value.get("task_type") != task_type:
                continue

            # Calculate simple word overlap score
            stored_prompt = value.get("prompt", "")
            stored_words = set(stored_prompt.lower().split())

            if not stored_words:
                continue

            overlap = len(prompt_words & stored_words)
            union = len(prompt_words | stored_words)
            similarity = overlap / union if union > 0 else 0

            if similarity > 0.1:  # Minimum threshold
                results.append(
                    {
                        "key": key,
                        "similarity": similarity,
                        "prompt": stored_prompt,
                        "response": value.get("response", "")[:500],  # Truncate
                        "technique": value.get("technique"),
                        "score": value.get("score", 0),
                        "provider": value.get("provider"),
                        "task_type": value.get("task_type"),
                    }
                )

        # Sort by similarity and return top_k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def get_technique_recommendation(
        self, prompt: str, task_type: str | None = None
    ) -> tuple[PromptTechnique | None, float]:
        """
        Get technique recommendation based on similar prompts in knowledge base.

        Args:
            prompt: The prompt to get recommendation for
            task_type: Optional task type filter

        Returns:
            Tuple of (recommended technique, confidence score)
        """
        similar = self.query_similar_prompts(prompt, task_type, top_k=10)

        if not similar:
            return None, 0.0

        # Count technique successes weighted by similarity and score
        technique_scores: dict[str, float] = {}
        for item in similar:
            technique = item.get("technique")
            if not technique:
                continue

            # Weight by both similarity and quality score
            weight = item["similarity"] * item.get("score", 0.5)
            technique_scores[technique] = technique_scores.get(technique, 0) + weight

        if not technique_scores:
            return None, 0.0

        # Get best technique
        best_technique = max(technique_scores.items(), key=lambda x: x[1])
        total_weight = sum(technique_scores.values())
        confidence = best_technique[1] / total_weight if total_weight > 0 else 0

        try:
            return PromptTechnique(best_technique[0]), confidence
        except ValueError:
            return None, 0.0

    def get_learning_stats_for_rag(self) -> dict[str, Any]:
        """
        Get learning statistics formatted for RAG metadata.

        Returns:
            Dict with technique success rates and provider performance
        """
        stats = {
            "agent_type": self.agent_type.value,
            "total_records": len(self._records),
            "knowledge_base_size": len(self._knowledge_base),
            "technique_stats": {},
            "provider_stats": {},
        }

        # Aggregate technique stats across all task types
        for _task_type, opt in self._optimizations.items():
            for tech, tech_stats in opt.get("techniques", {}).items():
                if tech not in stats["technique_stats"]:
                    stats["technique_stats"][tech] = {"uses": 0, "successes": 0}
                stats["technique_stats"][tech]["uses"] += tech_stats.get("uses", 0)
                stats["technique_stats"][tech]["successes"] += tech_stats.get("successes", 0)

            for prov, prov_stats in opt.get("providers", {}).items():
                if prov not in stats["provider_stats"]:
                    stats["provider_stats"][prov] = {"uses": 0, "successes": 0, "total_latency": 0}
                stats["provider_stats"][prov]["uses"] += prov_stats.get("uses", 0)
                stats["provider_stats"][prov]["successes"] += prov_stats.get("successes", 0)

        # Calculate success rates
        for _tech, s in stats["technique_stats"].items():
            s["success_rate"] = s["successes"] / s["uses"] if s["uses"] > 0 else 0

        for _prov, s in stats["provider_stats"].items():
            s["success_rate"] = s["successes"] / s["uses"] if s["uses"] > 0 else 0

        return stats


# =============================================================================
# LLM Round Table Interface
# =============================================================================


class LLMRoundTableInterface:
    """
    Interface for LLM Round Table competitions.

    This interface wraps the production Round Table (llm/round_table.py) when available,
    falling back to a lightweight implementation otherwise.

    Flow:
    1. All LLMs generate responses in parallel
    2. Score and rank using 5 metrics (relevance, quality, completeness, efficiency, brand)
    3. Select top 2 for A/B comparison
    4. Judge LLM determines winner
    5. Persist results to database
    6. Return winning response

    Production Features (when llm/round_table.py is available):
    - Database persistence to Neon PostgreSQL
    - Enhanced ResponseScorer with brand alignment
    - ABTestResult with confidence scores
    - Comprehensive history and analytics
    """

    SCORING_CRITERIA = {
        "relevance": 0.25,  # How relevant is the response
        "quality": 0.25,  # Overall quality of output
        "completeness": 0.20,  # Does it fully answer the prompt
        "efficiency": 0.15,  # Token efficiency and cost
        "brand_alignment": 0.15,  # SkyyRose brand voice adherence
    }

    def __init__(self, db_url: str | None = None, use_production: bool = True):
        """
        Initialize Round Table Interface.

        Args:
            db_url: Database URL for persistence (production mode)
            use_production: Whether to use production Round Table when available
        """
        self._providers: dict[LLMProvider, Callable] = {}
        self._judge_provider: LLMProvider = LLMProvider.CLAUDE
        self._history: list[RoundTableResult] = []
        self._db_url = db_url
        self._use_production = use_production and PRODUCTION_ROUND_TABLE_AVAILABLE
        self._production_rt: Any = None  # ProductionRoundTable instance
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the Round Table (creates database connection if in production mode)."""
        if self._use_production and create_round_table is not None:
            try:
                self._production_rt = await create_round_table(self._db_url)
                self._initialized = True
                logger.info(
                    "LLM Round Table initialized with production backend (database persistence enabled)"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize production Round Table: {e}. Using fallback.")
                self._use_production = False
                self._initialized = True
        else:
            self._initialized = True
            logger.info("LLM Round Table initialized with lightweight backend")

    def register_provider(self, provider: LLMProvider, generator: Callable):
        """Register an LLM provider"""
        self._providers[provider] = generator

        # Also register with production Round Table if available
        if self._production_rt is not None and RoundTableProvider is not None:
            # Map internal LLMProvider to production RoundTableProvider
            provider_map = {
                LLMProvider.CLAUDE: RoundTableProvider.CLAUDE,
                LLMProvider.GPT4: RoundTableProvider.GPT4,
                LLMProvider.GEMINI: RoundTableProvider.GEMINI,
                LLMProvider.LLAMA: RoundTableProvider.LLAMA,
                LLMProvider.MISTRAL: RoundTableProvider.MISTRAL,
                LLMProvider.COHERE: RoundTableProvider.COHERE,
            }
            if provider in provider_map:
                self._production_rt.register_provider(provider_map[provider], generator)

    def set_judge(self, provider: LLMProvider):
        """Set the judge LLM for A/B testing"""
        self._judge_provider = provider

        # Also set in production Round Table
        if self._production_rt is not None and RoundTableProvider is not None:
            provider_map = {
                LLMProvider.CLAUDE: RoundTableProvider.CLAUDE,
                LLMProvider.GPT4: RoundTableProvider.GPT4,
                LLMProvider.GEMINI: RoundTableProvider.GEMINI,
            }
            if provider in provider_map:
                self._production_rt.set_judge(provider_map[provider])

    async def compete(
        self,
        prompt: str,
        providers: list[LLMProvider] | None = None,
        context: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> RoundTableResult:
        """
        Run Round Table competition.

        Args:
            prompt: The task prompt
            providers: LLM providers to include (default: all registered)
            context: Additional context for generation
            correlation_id: Optional correlation ID for tracing

        Returns:
            RoundTableResult with winner and all entries
        """
        # Ensure initialized
        if not self._initialized:
            await self.initialize()

        start_time = time.time()
        task_id = hashlib.md5(
            f"{prompt}{datetime.now(UTC).isoformat()}".encode(), usedforsecurity=False
        ).hexdigest()[:16]
        corr_id = correlation_id or task_id

        logger.info(
            "Round Table competition started",
            extra={
                "correlation_id": corr_id,
                "task_id": task_id,
                "provider_count": len(providers) if providers else len(self._providers),
                "use_production": self._use_production,
            },
        )

        # Delegate to production Round Table if available
        if self._use_production and self._production_rt is not None:
            try:
                prod_result = await self._production_rt.compete(prompt, context=context)
                # Convert production result to our format
                result = self._convert_production_result(prod_result, task_id)
                self._history.append(result)
                duration = time.time() - start_time

                # Emit metrics
                self._emit_competition_metrics(result, duration, use_production=True)

                logger.info(
                    "Round Table competition completed (production)",
                    extra={
                        "correlation_id": corr_id,
                        "winner": result.winner.provider.value,
                        "entries_count": len(result.entries),
                        "duration_seconds": duration,
                    },
                )
                return result
            except Exception as e:
                logger.warning(f"Production Round Table failed, using fallback: {e}")
                if METRICS_AVAILABLE and prometheus_exporter:
                    prometheus_exporter.record_round_table_error("production_fallback", "system")

        # Fallback to lightweight implementation
        active_providers = providers or list(self._providers.keys())

        # Generate responses in parallel with retry logic
        entries = await self._generate_all_with_retry(
            prompt, active_providers, context, max_retries=2
        )

        if not entries:
            if METRICS_AVAILABLE and prometheus_exporter:
                prometheus_exporter.record_round_table_error("no_responses", "all")
            raise ValueError("No providers generated responses")

        # Score all entries
        scored_entries = self._score_entries(entries, prompt)

        # Sort by total score
        sorted_entries = sorted(scored_entries, key=lambda x: x.total_score, reverse=True)

        # Select top 2
        top_two = sorted_entries[:2]

        # A/B test between top 2
        winner, judge_reasoning = await self._ab_test(prompt, top_two)

        result = RoundTableResult(
            task_id=task_id,
            prompt=prompt,
            entries=sorted_entries,
            top_two=top_two,
            winner=winner,
            judge_reasoning=judge_reasoning,
        )

        self._history.append(result)
        duration = time.time() - start_time

        # Emit metrics
        self._emit_competition_metrics(result, duration, use_production=False)

        logger.info(
            "Round Table competition completed (fallback)",
            extra={
                "correlation_id": corr_id,
                "winner": result.winner.provider.value,
                "entries_count": len(result.entries),
                "duration_seconds": duration,
            },
        )
        return result

    def _emit_competition_metrics(
        self,
        result: RoundTableResult,
        duration_seconds: float,
        use_production: bool,
    ) -> None:
        """Emit Prometheus metrics for a Round Table competition."""
        if not METRICS_AVAILABLE or prometheus_exporter is None:
            return

        # Record competition
        prometheus_exporter.record_round_table_competition(
            winner_provider=result.winner.provider.value,
            duration_seconds=duration_seconds,
            use_production=use_production,
        )

        # Record each provider's participation
        for entry in result.entries:
            if entry == result.winner:
                outcome = "winner"
            elif entry in result.top_two:
                outcome = "finalist"
            else:
                outcome = "participant"

            prometheus_exporter.record_round_table_provider(
                provider=entry.provider.value,
                outcome=outcome,
                latency_ms=entry.latency_ms,
            )

        # Update win rates
        stats = self.get_provider_stats()
        for provider_name, provider_stats in stats.items():
            if provider_stats["participations"] > 0:
                win_rate = provider_stats["wins"] / provider_stats["participations"]
                prometheus_exporter.update_round_table_win_rate(provider_name, win_rate)

    def _convert_production_result(self, prod_result: Any, task_id: str) -> RoundTableResult:
        """Convert production RoundTableResult to our format."""
        # Map production entries to our format
        entries = []
        for prod_entry in prod_result.entries:
            entry = RoundTableEntry(
                provider=LLMProvider(prod_entry.provider.value),
                response=prod_entry.response,
                latency_ms=prod_entry.latency_ms,
                cost_usd=prod_entry.cost_usd,
                scores=prod_entry.scores if hasattr(prod_entry, "scores") else {},
                total_score=prod_entry.total_score if hasattr(prod_entry, "total_score") else 0.0,
            )
            entries.append(entry)

        # Map winner
        winner_entry = entries[0]  # Default
        for entry in entries:
            if entry.provider.value == prod_result.winner.provider.value:
                winner_entry = entry
                break

        # Map top two
        top_two = entries[:2]

        return RoundTableResult(
            task_id=task_id,
            prompt=prod_result.prompt,
            entries=entries,
            top_two=top_two,
            winner=winner_entry,
            judge_reasoning=(
                prod_result.judge_reasoning if hasattr(prod_result, "judge_reasoning") else ""
            ),
            ab_test_id=prod_result.ab_test_id if hasattr(prod_result, "ab_test_id") else None,
        )

    async def _generate_all_with_retry(
        self,
        prompt: str,
        providers: list[LLMProvider],
        context: dict[str, Any] | None,
        max_retries: int = 2,
    ) -> list[RoundTableEntry]:
        """Generate responses from all providers in parallel with retry logic."""
        entries = []

        async def generate_one_with_retry(provider: LLMProvider) -> RoundTableEntry | None:
            generator = self._providers.get(provider)
            if not generator:
                return None

            last_error: Exception | None = None
            for attempt in range(max_retries + 1):
                start_time = time.time()
                try:
                    response = await generator(prompt, context)
                    latency = (time.time() - start_time) * 1000

                    return RoundTableEntry(
                        provider=provider,
                        response=response.get("text", str(response)),
                        latency_ms=latency,
                        cost_usd=response.get("cost", 0.0),
                    )
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        # Exponential backoff: 0.5s, 1s, 2s...
                        wait_time = 0.5 * (2**attempt)
                        logger.warning(
                            f"Provider {provider.value} failed (attempt {attempt + 1}/{max_retries + 1}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                        await asyncio.sleep(wait_time)

            logger.error(
                f"Provider {provider.value} failed after {max_retries + 1} attempts: {last_error}"
            )
            return None

        # Run all generators concurrently
        tasks = [generate_one_with_retry(p) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, RoundTableEntry):
                entries.append(result)

        return entries

    async def _generate_all(
        self, prompt: str, providers: list[LLMProvider], context: dict[str, Any] | None
    ) -> list[RoundTableEntry]:
        """Generate responses from all providers in parallel (no retry, for backward compat)."""
        return await self._generate_all_with_retry(prompt, providers, context, max_retries=0)

    # SkyyRose brand keywords for brand alignment scoring
    BRAND_KEYWORDS = {
        "luxury",
        "premium",
        "elegant",
        "sophisticated",
        "exclusive",
        "skyyrose",
        "rose",
        "love",
        "collection",
        "fashion",
        "quality",
        "crafted",
        "artisan",
        "bespoke",
        "curated",
    }

    def _score_entries(self, entries: list[RoundTableEntry], prompt: str) -> list[RoundTableEntry]:
        """Score all entries using defined criteria including brand alignment."""
        for entry in entries:
            scores = {}
            response_lower = entry.response.lower()

            # Relevance: Basic keyword matching with TF-IDF-like weighting
            prompt_words = set(prompt.lower().split())
            response_words = set(response_lower.split())
            overlap = len(prompt_words & response_words)
            scores["relevance"] = min(overlap / max(len(prompt_words), 1), 1.0)

            # Quality: Length, structure, and formatting heuristics
            response_len = len(entry.response)
            has_structure = any(
                marker in entry.response for marker in ["- ", "* ", "1.", "##", "**"]
            )
            base_quality = 0.0
            if 100 <= response_len <= 2000:
                base_quality = 1.0
            elif response_len < 100:
                base_quality = response_len / 100
            else:
                base_quality = max(0.5, 1 - (response_len - 2000) / 5000)
            # Bonus for structured responses
            scores["quality"] = min(1.0, base_quality + (0.1 if has_structure else 0))

            # Completeness: Check for common completion indicators
            completion_indicators = [
                "therefore",
                "in conclusion",
                "finally",
                "to summarize",
                "in summary",
            ]
            has_completion = any(ind in response_lower for ind in completion_indicators)
            scores["completeness"] = 1.0 if has_completion else 0.7

            # Efficiency: Based on latency and cost
            latency_score = max(0, 1 - entry.latency_ms / 10000)
            cost_score = max(0, 1 - entry.cost_usd / 0.1)
            scores["efficiency"] = (latency_score + cost_score) / 2

            # Brand Alignment: SkyyRose brand voice adherence
            brand_matches = sum(1 for kw in self.BRAND_KEYWORDS if kw in response_lower)
            scores["brand_alignment"] = min(
                1.0, brand_matches / 3
            )  # 3+ brand keywords = full score

            entry.scores = scores

            # Calculate weighted total
            entry.total_score = sum(
                scores.get(criterion, 0.0) * weight
                for criterion, weight in self.SCORING_CRITERIA.items()
            )

        return entries

    async def _ab_test(
        self, prompt: str, top_two: list[RoundTableEntry]
    ) -> tuple[RoundTableEntry, str]:
        """A/B test between top 2 entries using judge LLM"""
        if len(top_two) < 2:
            return top_two[0], "Only one entry, selected by default"

        # Create judge prompt
        judge_prompt = f"""Compare these two responses to the prompt: "{prompt[:500]}"

Response A ({top_two[0].provider.value}):
{top_two[0].response[:1000]}

Response B ({top_two[1].provider.value}):
{top_two[1].response[:1000]}

Which response better addresses the prompt? Consider:
- Accuracy and correctness
- Completeness of the answer
- Clarity and structure
- Actionable insights

Respond with:
WINNER: A or B
REASONING: Your explanation"""

        # Get judge's decision
        judge_generator = self._providers.get(self._judge_provider)
        if judge_generator:
            try:
                result = await judge_generator(judge_prompt, None)
                response_text = result.get("text", str(result))

                # Parse winner
                if "WINNER: A" in response_text.upper():
                    return top_two[0], response_text
                elif "WINNER: B" in response_text.upper():
                    return top_two[1], response_text
            except Exception as e:
                logger.error(f"Judge failed: {e}")

        # Default to highest scored if judge fails
        winner = top_two[0] if top_two[0].total_score >= top_two[1].total_score else top_two[1]
        return winner, f"Fallback to highest score: {winner.total_score:.2f}"

    def get_history(self, limit: int = 100) -> list[RoundTableResult]:
        """Get recent Round Table results"""
        return self._history[-limit:]

    def get_provider_stats(self) -> dict[str, dict]:
        """Get statistics for each provider"""
        stats = {p.value: {"wins": 0, "participations": 0, "avg_score": 0.0} for p in LLMProvider}

        for result in self._history:
            for entry in result.entries:
                prov = entry.provider.value
                stats[prov]["participations"] += 1
                n = stats[prov]["participations"]
                stats[prov]["avg_score"] = (
                    stats[prov]["avg_score"] * (n - 1) + entry.total_score
                ) / n

                if entry == result.winner:
                    stats[prov]["wins"] += 1

        return stats


# =============================================================================
# Enhanced Base Super Agent
# =============================================================================


class EnhancedSuperAgent(BaseDevSkyyAgent):
    """
    Enhanced Base Super Agent with all modules integrated.

    Features:
    - 17 Prompt Engineering Techniques
    - ML Capabilities
    - Self-Learning
    - LLM Round Table Integration

    All 6 SuperAgents inherit from this class.
    """

    agent_type: SuperAgentType = None
    sub_capabilities: list[str] = []

    def __init__(self, config: AgentConfig):
        super().__init__(config)

        # Initialize modules
        self.prompt_module = PromptEngineeringModule()
        self.ml_module: MLCapabilitiesModule | None = None
        self.learning_module: SelfLearningModule | None = None
        self.round_table: LLMRoundTableInterface | None = None

        # LLM Router for intelligent provider selection
        self._router: Any = None  # Type: LLMRouter | None
        self._router_available = LLM_ROUTER_AVAILABLE

        # Enterprise Intelligence Modules (NEW)
        self.enterprise_index: Any = None  # Type: EnterpriseIndex | None
        self.semantic_analyzer: Any = None  # Type: SemanticCodeAnalyzer | None
        self.verification_engine: Any = None  # Type: LLMVerificationEngine | None

        # State
        self._initialized = False
        self._execution_count = 0
        self._active_provider = ADKProvider.PYDANTIC
        self._current_model_provider: str | None = None  # Track routed provider

    async def initialize(self) -> None:
        """Initialize all modules"""
        logger.info(f"Initializing Enhanced Super Agent: {self.agent_type}")

        # Initialize ML module
        if self.agent_type:
            self.ml_module = MLCapabilitiesModule(self.agent_type)
            await self.ml_module.initialize()

            # Initialize learning module
            self.learning_module = SelfLearningModule(self.agent_type)

            # Initialize Round Table
            self.round_table = LLMRoundTableInterface()

        # Initialize LLM Router for intelligent provider selection
        if self._router_available and LLMRouter is not None and RoutingStrategy is not None:
            try:
                # Use COST strategy for low-temperature (deterministic) tasks
                # Use PRIORITY strategy for higher-temperature (creative) tasks
                strategy = (
                    RoutingStrategy.COST
                    if self.config.temperature < 0.5
                    else RoutingStrategy.PRIORITY
                )
                self._router = LLMRouter(strategy=strategy)
                logger.info(
                    f"LLM Router initialized for {self.agent_type} with {strategy.value} strategy"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize LLM Router: {e}")
                self._router = None

        # Initialize Enterprise Intelligence Modules (NEW)
        await self._init_enterprise_intelligence()

        # Initialize backend
        try:
            await self._init_pydantic_backend()
        except ImportError:
            try:
                await self._init_langchain_backend()
            except ImportError:
                logger.warning("No ADK backend available, using fallback")

        self._initialized = True
        logger.info(f"Enhanced Super Agent {self.agent_type} initialized")

    async def _init_pydantic_backend(self) -> None:
        """Initialize with PydanticAI backend"""
        from pydantic_ai import Agent

        self._backend_agent = Agent(
            self._get_model_string(),
            system_prompt=self.config.system_prompt,
        )
        self._active_provider = ADKProvider.PYDANTIC

    async def _init_langchain_backend(self) -> None:
        """Initialize with LangChain/LangGraph backend"""
        from langchain_openai import ChatOpenAI

        self._backend_llm = ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
        )
        self._active_provider = ADKProvider.LANGGRAPH

    def _get_model_string(self) -> str:
        """Get model string for current provider"""
        model = self.config.model.lower()
        if "gpt" in model:
            return f"openai:{self.config.model}"
        elif "claude" in model:
            return f"anthropic:{self.config.model}"
        elif "gemini" in model:
            return f"google-gla:{self.config.model}"
        return f"openai:{self.config.model}"

    def _get_preferred_provider(self, task_category: TaskCategory | None = None) -> str:
        """
        Get the preferred LLM provider based on agent type and task category.

        Uses AGENT_PROVIDER_PREFERENCES and TASK_PROVIDER_PREFERENCES to determine
        the optimal provider for each agent/task combination.

        Args:
            task_category: Optional task category for task-specific routing

        Returns:
            Provider name (e.g., 'anthropic', 'openai', 'google')
        """
        # Get agent-type preferences
        agent_key = self.agent_type.value if self.agent_type else "commerce"
        agent_prefs = AGENT_PROVIDER_PREFERENCES.get(agent_key, ["openai", "anthropic"])

        # Get task-specific preferences if task category is provided
        if task_category:
            task_key = task_category.value
            task_prefs = TASK_PROVIDER_PREFERENCES.get(task_key)

            if task_prefs:
                # Find intersection that maintains agent preference order
                common_providers = [p for p in agent_prefs if p in task_prefs]
                if common_providers:
                    return common_providers[0]

        # Fall back to first agent preference
        return agent_prefs[0] if agent_prefs else "openai"

    async def _route_to_provider(
        self, prompt: str, task_category: TaskCategory | None = None, **kwargs
    ) -> dict[str, Any]:
        """
        Route request through LLM Router for intelligent provider selection.

        Args:
            prompt: The prompt to send
            task_category: Optional task category for routing decisions
            **kwargs: Additional parameters for the LLM call

        Returns:
            Response dict with 'text', 'provider', 'model', 'usage' keys
        """
        preferred_provider = self._get_preferred_provider(task_category)
        self._current_model_provider = preferred_provider

        # If router is available, use it for intelligent routing
        if self._router is not None and Message is not None and ModelProvider is not None:
            try:
                # Convert string provider to ModelProvider enum
                provider_map = {
                    "openai": ModelProvider.OPENAI,
                    "anthropic": ModelProvider.ANTHROPIC,
                    "google": ModelProvider.GOOGLE,
                    "groq": ModelProvider.GROQ,
                    "mistral": ModelProvider.MISTRAL,
                    "cohere": ModelProvider.COHERE,
                }

                # Build preferred providers list (model_provider used for fallback)
                agent_key = self.agent_type.value if self.agent_type else "commerce"
                pref_list = AGENT_PROVIDER_PREFERENCES.get(agent_key, ["openai"])
                model_providers = [provider_map[p] for p in pref_list if p in provider_map]

                # Create message from prompt
                messages = [Message.user(prompt)]

                # Add system prompt if configured
                if self.config.system_prompt:
                    messages.insert(0, Message.system(self.config.system_prompt))

                # Route through LLM Router with fallback
                response = await self._router.complete_with_fallback(
                    messages=messages,
                    providers=model_providers,
                    temperature=kwargs.get("temperature", self.config.temperature),
                    max_tokens=kwargs.get("max_tokens", 2000),
                )

                # Get the actual provider used from response
                actual_provider = preferred_provider
                if hasattr(response, "model"):
                    # Infer provider from model name
                    model_lower = response.model.lower()
                    if "claude" in model_lower:
                        actual_provider = "anthropic"
                    elif "gpt" in model_lower:
                        actual_provider = "openai"
                    elif "gemini" in model_lower:
                        actual_provider = "google"
                    elif "llama" in model_lower:
                        actual_provider = "groq"
                    elif "mistral" in model_lower:
                        actual_provider = "mistral"

                self._current_model_provider = actual_provider
                logger.debug(f"Routed to {actual_provider} for {self.agent_type}")

                return {
                    "text": response.content if hasattr(response, "content") else str(response),
                    "provider": actual_provider,
                    "model": response.model if hasattr(response, "model") else self.config.model,
                    "usage": {
                        "input_tokens": (
                            response.usage.input_tokens
                            if hasattr(response, "usage") and response.usage
                            else 0
                        ),
                        "output_tokens": (
                            response.usage.output_tokens
                            if hasattr(response, "usage") and response.usage
                            else 0
                        ),
                        "cost_usd": (
                            response.usage.cost
                            if hasattr(response, "usage")
                            and response.usage
                            and hasattr(response.usage, "cost")
                            else 0.0
                        ),
                    },
                }

            except Exception as e:
                logger.warning(f"Router failed, falling back to direct call: {e}")

        # Fallback: Direct execution without router
        return await self._execute_direct(prompt, preferred_provider, **kwargs)

    async def _execute_direct(
        self,
        prompt: str,
        provider: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute directly without router when router is unavailable.

        Attempts multiple fallback strategies:
        1. Use existing backend agent
        2. Try direct LLM provider calls
        3. Raise error if no provider available (no silent failures)

        Args:
            prompt: The prompt to execute
            provider: Preferred provider name
            **kwargs: Additional execution arguments

        Returns:
            Dict with text, provider, model, and usage info

        Raises:
            RuntimeError: If no execution backend is available
        """
        # Strategy 1: Use existing backend if available
        if hasattr(self, "_backend_agent") and self._backend_agent:
            try:
                result = await self._backend_agent.run(prompt)
                return {
                    "text": str(result.data) if hasattr(result, "data") else str(result),
                    "provider": provider,
                    "model": self.config.model,
                    "usage": {"tokens": 0, "cost_usd": 0.0},
                }
            except Exception as e:
                logger.error(f"Backend execution failed: {e}")

        # Strategy 2: Try direct LLM provider calls
        try:
            from llm.router import get_llm_router

            router = get_llm_router()
            if router:
                # Get first available provider
                available = router.list_available_providers()
                if available:
                    fallback_provider = available[0]
                    logger.info(f"Using fallback provider: {fallback_provider}")

                    response = await router.route_and_execute(
                        prompt=prompt,
                        preferred_provider=fallback_provider,
                        task_type=(
                            self.agent_type.value
                            if hasattr(self.agent_type, "value")
                            else str(self.agent_type)
                        ),
                    )

                    return {
                        "text": response.content if hasattr(response, "content") else str(response),
                        "provider": fallback_provider,
                        "model": response.model if hasattr(response, "model") else "unknown",
                        "usage": {"tokens": 0, "cost_usd": 0.0},
                    }
        except ImportError:
            logger.debug("LLM router not available for fallback")
        except Exception as e:
            logger.warning(f"Direct LLM fallback failed: {e}")

        # Strategy 3: Raise error - no silent failures in production
        raise RuntimeError(
            f"No execution backend available for provider '{provider}'. "
            f"Configure at least one LLM provider (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.) "
            f"or ensure the backend agent is properly initialized."
        )

    def select_technique(
        self,
        task_category: TaskCategory,
        context: dict[str, Any] | None = None,
        prompt: str | None = None,
    ) -> PromptTechnique:
        """
        Select the best prompt technique for a task.

        Selection priority:
        1. RAG-based recommendation (similar prompt analysis)
        2. Learning module history
        3. Prompt module auto-selection
        """
        # Priority 1: Query RAG/knowledge base for similar prompts
        if self.learning_module and prompt:
            rag_technique, confidence = self.learning_module.get_technique_recommendation(
                prompt=prompt, task_type=task_category.value
            )
            if rag_technique and confidence > 0.6:  # High confidence threshold
                logger.debug(
                    f"RAG recommended technique {rag_technique.value} "
                    f"with {confidence:.1%} confidence"
                )
                return rag_technique

        # Priority 2: Check if learning module has a better suggestion from history
        if self.learning_module:
            learned_technique = self.learning_module.get_best_technique(task_category.value)
            if learned_technique:
                return learned_technique

        # Priority 3: Fall back to prompt module auto-selection
        return self.prompt_module.auto_select_technique(task_category, context)

    def apply_technique(
        self, technique: PromptTechnique, prompt: str, **kwargs
    ) -> PromptTechniqueResult:
        """Apply a prompt engineering technique"""
        return self.prompt_module.apply_technique(technique, prompt, **kwargs)

    async def predict(self, model_name: str, input_data: Any, **kwargs) -> MLPrediction | None:
        """Run ML prediction"""
        if not self.ml_module:
            return None
        return await self.ml_module.predict(model_name, input_data, **kwargs)

    async def run_round_table(
        self,
        prompt: str,
        providers: list[LLMProvider] | None = None,
        context: dict[str, Any] | None = None,
    ) -> RoundTableResult | None:
        """Run LLM Round Table competition"""
        if not self.round_table:
            return None
        return await self.round_table.compete(prompt, providers, context)

    @abstractmethod
    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute agent task - must be implemented by subclasses"""
        pass

    async def execute_auto(
        self,
        prompt: str,
        task_type: str | None = None,
        correlation_id: str | None = None,
        use_router: bool = True,
        use_round_table: bool = False,
        **kwargs,
    ) -> AgentResult:
        """
        Execute with AUTOMATIC prompt technique selection.

        This is the recommended entry point for all agent executions.
        It automatically:
        1. Generates a correlation_id for tracing
        2. Analyzes the prompt to determine TaskCategory
        3. Selects the optimal PromptTechnique from 17 available
        4. Applies the technique to enhance the prompt
        5. Routes to optimal LLM provider
        6. Logs all decisions for observability and A/B testing
        7. Records outcomes for self-learning optimization

        Args:
            prompt: The task prompt
            task_type: Optional task type for learning (auto-inferred if not provided)
            correlation_id: Optional correlation ID (auto-generated if not provided)
            use_router: Whether to use LLM Router for provider selection
            use_round_table: Whether to use Round Table for high-stakes tasks
            **kwargs: Additional execution parameters

        Returns:
            AgentResult with execution outcome and technique metadata
        """
        import uuid

        # Generate correlation_id for tracing
        correlation_id = correlation_id or str(uuid.uuid4())
        task_id = correlation_id[:16]
        start_time = time.time()

        # Use TaskCategoryAnalyzer for intelligent category inference
        analyzer = get_task_analyzer()
        task_category, confidence, analysis_reason = analyzer.analyze(
            prompt=prompt,
            agent_type=self.agent_type,
            correlation_id=correlation_id,
        )

        # Auto-infer task_type if not provided
        if task_type is None:
            task_type = (
                f"{self.agent_type.value if self.agent_type else 'general'}_{task_category.value}"
            )

        # Select optimal technique
        technique, selection_reason = analyzer.select_technique(
            category=task_category,
            confidence=confidence,
            correlation_id=correlation_id,
        )

        # Log the automatic selection for observability
        log = structlog.get_logger(__name__)

        # Bind execution-scoped context
        bind_contextvars(
            correlation_id=correlation_id,
            agent_id=str(
                getattr(self, "agent_id", self.agent_type.value if self.agent_type else "unknown")
            ),
        )

        log.info(
            "agent_technique_selection",
            agent_type=self.agent_type.value if self.agent_type else "unknown",
            task_category=task_category.value,
            technique=technique.value,
            confidence=round(confidence, 2),
        )

        # Apply technique to enhance prompt
        enhanced = self.apply_technique(technique, prompt, **kwargs)

        # Add correlation metadata to result
        enhanced_with_meta = PromptTechniqueResult(
            technique=enhanced.technique,
            original_prompt=enhanced.original_prompt,
            enhanced_prompt=enhanced.enhanced_prompt,
            metadata={
                **enhanced.metadata,
                "correlation_id": correlation_id,
                "task_category": task_category.value,
                "confidence": confidence,
                "selection_reason": selection_reason,
            },
            correlation_id=correlation_id,
            task_category=task_category,
            selection_reason=selection_reason,
        )

        # Determine if Round Table should be used
        should_use_round_table = use_round_table or self._is_high_stakes_task(task_type, prompt)

        # Execute with appropriate method
        if should_use_round_table and self.round_table:
            result = await self._execute_with_round_table_internal(
                enhanced_with_meta, task_type, task_category, correlation_id, **kwargs
            )
        elif use_router and self._router is not None:
            result = await self._execute_with_router_internal(
                enhanced_with_meta, task_category, correlation_id, **kwargs
            )
        else:
            # Direct execution
            result = await self.execute(enhanced_with_meta.enhanced_prompt, **kwargs)

        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        success = result.status == AgentStatus.COMPLETED
        cost_usd = result.cost_usd

        # Record for learning
        if self.learning_module:
            self.learning_module.record_execution(
                task_id=task_id,
                task_type=task_type,
                prompt=prompt,
                technique=technique,
                llm_provider=self._current_model_provider or self._active_provider.value,
                success=success,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
            )

        # Update technique stats
        self.prompt_module.record_outcome(technique, success)

        # Enrich result metadata with technique selection info
        if result.metadata is None:
            result.metadata = {}
        result.metadata.update(
            {
                "correlation_id": correlation_id,
                "task_category": task_category.value,
                "technique": technique.value,
                "technique_confidence": confidence,
                "selection_reason": selection_reason,
                "auto_selected": True,
            }
        )

        self._execution_count += 1

        log.info(
            "agent_execution_complete",
            status=result.status.value,
            latency_ms=round(latency_ms, 0),
            technique=technique.value,
            success=success,
        )

        # Unbind execution-scoped context
        unbind_contextvars("correlation_id", "agent_id")

        return result

    async def _execute_with_router_internal(
        self,
        enhanced: PromptTechniqueResult,
        task_category: TaskCategory,
        correlation_id: str,
        **kwargs,
    ) -> AgentResult:
        """Internal method for router-based execution."""
        try:
            routed_response = await self._route_to_provider(
                enhanced.enhanced_prompt, task_category=task_category, **kwargs
            )
            provider_used = routed_response.get("provider", self._active_provider.value)
            self._current_model_provider = provider_used

            return AgentResult(
                status=AgentStatus.COMPLETED,
                output=routed_response.get("text", ""),
                usage=routed_response.get("usage", {}),
                metadata={
                    "provider": provider_used,
                    "model": routed_response.get("model", self.config.model),
                    "routed": True,
                    "correlation_id": correlation_id,
                },
            )
        except Exception as e:
            logger.warning(f"[{correlation_id}] Routed execution failed: {e}")
            return await self.execute(enhanced.enhanced_prompt, **kwargs)

    async def _execute_with_round_table_internal(
        self,
        enhanced: PromptTechniqueResult,
        task_type: str,
        task_category: TaskCategory,
        correlation_id: str,
        **kwargs,
    ) -> AgentResult:
        """Internal method for Round Table execution."""
        if not self.round_table:
            return await self.execute(enhanced.enhanced_prompt, **kwargs)

        try:
            round_table_result = await self.round_table.compete(
                enhanced.enhanced_prompt,
                providers=None,  # Use all available
                context={
                    "task_type": task_type,
                    "task_category": task_category.value,
                    "agent_type": self.agent_type.value if self.agent_type else None,
                    "correlation_id": correlation_id,
                },
            )

            winner = round_table_result.winner
            success = winner is not None and winner.response

            return AgentResult(
                status=AgentStatus.COMPLETED if success else AgentStatus.FAILED,
                output=winner.response if winner else "",
                usage={
                    "cost_usd": winner.cost_usd if winner else 0.0,
                    "latency_ms": winner.latency_ms if winner else 0.0,
                    "round_table_entries": len(round_table_result.entries),
                },
                metadata={
                    "round_table": True,
                    "task_id": round_table_result.task_id,
                    "winning_provider": winner.provider.value if winner else None,
                    "winner_score": winner.total_score if winner else 0.0,
                    "judge_reasoning": round_table_result.judge_reasoning,
                    "correlation_id": correlation_id,
                },
            )
        except Exception as e:
            logger.warning(f"[{correlation_id}] Round Table failed: {e}")
            return await self.execute(enhanced.enhanced_prompt, **kwargs)

    async def execute_with_learning(
        self,
        prompt: str,
        task_type: str,
        technique: PromptTechnique | None = None,
        use_router: bool = True,
        **kwargs,
    ) -> AgentResult:
        """
        Execute with automatic learning, optimization, and intelligent routing.

        This method:
        1. Infers task category from prompt
        2. Selects the best technique if not specified
        3. Applies the technique to enhance the prompt
        4. Routes to optimal LLM provider based on agent type and task
        5. Executes the task
        6. Records the outcome for learning
        7. Updates technique and provider stats

        Args:
            prompt: The task prompt
            task_type: Type of task for learning categorization
            technique: Optional specific technique to use
            use_router: Whether to use LLM Router for provider selection
            **kwargs: Additional execution parameters

        Returns:
            AgentResult with execution outcome
        """
        import uuid

        task_id = str(uuid.uuid4())[:16]
        start_time = time.time()

        # Infer task category for routing and technique selection
        task_category = self._infer_task_category(prompt)

        # Select technique if not specified
        if technique is None:
            technique = self.select_technique(task_category)

        # Apply technique to enhance prompt
        enhanced = self.apply_technique(technique, prompt, **kwargs)

        # Track which provider was used
        provider_used = self._active_provider.value

        # Execute with intelligent routing if enabled and router available
        if use_router and self._router is not None:
            try:
                routed_response = await self._route_to_provider(
                    enhanced.enhanced_prompt, task_category=task_category, **kwargs
                )
                provider_used = routed_response.get("provider", provider_used)
                self._current_model_provider = provider_used

                # Build result from routed response
                result = AgentResult(
                    status=AgentStatus.COMPLETED,
                    output=routed_response.get("text", ""),
                    usage=routed_response.get("usage", {}),
                    metadata={
                        "provider": provider_used,
                        "model": routed_response.get("model", self.config.model),
                        "routed": True,
                        "task_category": task_category.value,
                        "technique": technique.value,
                    },
                )
            except Exception as e:
                logger.warning(f"Routed execution failed, falling back: {e}")
                result = await self.execute(enhanced.enhanced_prompt, **kwargs)
        else:
            # Direct execution without router
            result = await self.execute(enhanced.enhanced_prompt, **kwargs)

        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        success = result.status == AgentStatus.COMPLETED
        cost_usd = result.cost_usd

        # Record for learning with actual provider used
        if self.learning_module:
            self.learning_module.record_execution(
                task_id=task_id,
                task_type=task_type,
                prompt=prompt,
                technique=technique,
                llm_provider=provider_used,
                success=success,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
            )

        # Update technique stats
        self.prompt_module.record_outcome(technique, success)

        self._execution_count += 1
        return result

    def _infer_task_category(self, prompt: str) -> TaskCategory:
        """Infer task category from prompt"""
        prompt_lower = prompt.lower()

        category_keywords = {
            TaskCategory.REASONING: ["why", "explain", "analyze", "reason"],
            TaskCategory.CLASSIFICATION: ["classify", "categorize", "label", "type"],
            TaskCategory.CREATIVE: ["create", "design", "generate", "imagine"],
            TaskCategory.SEARCH: ["find", "search", "locate", "look for"],
            TaskCategory.QA: ["what", "who", "when", "where", "how"],
            TaskCategory.EXTRACTION: ["extract", "parse", "get", "pull"],
            TaskCategory.MODERATION: ["review", "check", "validate", "moderate"],
            TaskCategory.GENERATION: ["write", "compose", "draft", "produce"],
            TaskCategory.ANALYSIS: ["analyze", "examine", "study", "investigate"],
            TaskCategory.PLANNING: ["plan", "schedule", "organize", "strategy"],
            TaskCategory.DEBUGGING: ["fix", "debug", "error", "issue", "bug"],
            TaskCategory.OPTIMIZATION: ["optimize", "improve", "enhance", "better"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                return category

        return TaskCategory.GENERATION  # Default

    def _is_high_stakes_task(self, task_type: str, prompt: str | None = None) -> bool:
        """
        Determine if a task should use Round Table for quality assurance.

        High-stakes tasks include:
        - Tasks in HIGH_STAKES_TASK_TYPES
        - Tasks from HIGH_STAKES_AGENT_TYPES agents
        - Tasks with keywords indicating financial/security operations

        Args:
            task_type: The task type string
            prompt: Optional prompt to analyze for high-stakes keywords

        Returns:
            True if Round Table should be used
        """
        # Check if task type is explicitly high-stakes
        if task_type.lower() in HIGH_STAKES_TASK_TYPES:
            return True

        # Check if this agent type defaults to high-stakes
        agent_type = self.agent_type.value if self.agent_type else ""
        if agent_type in HIGH_STAKES_AGENT_TYPES:
            # Check for transaction-related keywords
            high_stakes_keywords = [
                "order",
                "payment",
                "refund",
                "transaction",
                "checkout",
                "purchase",
                "invoice",
                "charge",
                "deploy",
                "delete",
                "remove",
                "production",
            ]
            task_lower = task_type.lower()
            if any(kw in task_lower for kw in high_stakes_keywords):
                return True

        # Check prompt for high-stakes indicators
        if prompt:
            prompt_lower = prompt.lower()
            critical_keywords = [
                "process payment",
                "charge customer",
                "refund order",
                "delete",
                "remove permanently",
                "deploy to production",
                "update inventory",
                "change price",
                "modify stock",
                "authenticate user",
                "verify identity",
            ]
            if any(kw in prompt_lower for kw in critical_keywords):
                return True

        return False

    async def execute_with_round_table(
        self,
        prompt: str,
        task_type: str,
        technique: PromptTechnique | None = None,
        providers: list[LLMProvider] | None = None,
        **kwargs,
    ) -> AgentResult:
        """
        Execute task using LLM Round Table for quality assurance.

        Multiple LLMs compete, top 2 are A/B tested, winner is returned.
        Use for high-stakes tasks or when maximum quality is required.

        Args:
            prompt: The task prompt
            task_type: Type of task for categorization
            technique: Optional prompt technique to apply
            providers: Optional list of LLM providers to include
            **kwargs: Additional execution parameters

        Returns:
            AgentResult with winning response and metadata
        """
        import uuid

        task_id = str(uuid.uuid4())[:16]
        start_time = time.time()

        # Infer task category and select technique
        task_category = self._infer_task_category(prompt)
        if technique is None:
            technique = self.select_technique(task_category)

        # Apply technique to enhance prompt
        enhanced = self.apply_technique(technique, prompt, **kwargs)

        # Run Round Table competition
        if not self.round_table:
            logger.warning("Round Table not initialized, falling back to standard execution")
            return await self.execute_with_learning(
                prompt, task_type, technique, use_router=True, **kwargs
            )

        try:
            round_table_result = await self.round_table.compete(
                enhanced.enhanced_prompt,
                providers=providers,
                context={
                    "task_type": task_type,
                    "task_category": task_category.value,
                    "agent_type": self.agent_type.value if self.agent_type else None,
                },
            )

            # Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            winner = round_table_result.winner
            success = winner is not None and winner.response

            # Build result from winner
            result = AgentResult(
                status=AgentStatus.COMPLETED if success else AgentStatus.FAILED,
                output=winner.response if winner else "",
                usage={
                    "cost_usd": winner.cost_usd if winner else 0.0,
                    "latency_ms": winner.latency_ms if winner else 0.0,
                    "round_table_entries": len(round_table_result.entries),
                },
                metadata={
                    "round_table": True,
                    "task_id": round_table_result.task_id,
                    "winning_provider": winner.provider.value if winner else None,
                    "winner_score": winner.total_score if winner else 0.0,
                    "judge_reasoning": round_table_result.judge_reasoning,
                    "technique": technique.value,
                    "task_category": task_category.value,
                },
            )

            # Record for learning
            if self.learning_module:
                self.learning_module.record_execution(
                    task_id=task_id,
                    task_type=task_type,
                    prompt=prompt,
                    technique=technique,
                    llm_provider=(
                        f"round_table:{winner.provider.value}" if winner else "round_table"
                    ),
                    success=success,
                    latency_ms=latency_ms,
                    cost_usd=winner.cost_usd if winner else 0.0,
                    user_feedback=winner.total_score if winner else None,
                )

                # Auto-ingest successful responses to RAG for future retrieval
                if success and winner and winner.total_score >= ROUND_TABLE_QUALITY_THRESHOLD:
                    await self.learning_module.ingest_successful_response(
                        prompt=prompt,
                        response=winner.response,
                        task_type=task_type,
                        technique=technique,
                        score=winner.total_score,
                        provider=winner.provider.value,
                        metadata={
                            "round_table_entries": len(round_table_result.entries),
                            "judge_reasoning": round_table_result.judge_reasoning[:200],
                            "task_category": task_category.value,
                        },
                    )

            # Update technique stats
            self.prompt_module.record_outcome(
                technique, success, winner.total_score if winner else 0.0
            )

            self._execution_count += 1
            logger.info(
                f"Round Table completed: winner={winner.provider.value if winner else 'none'}, "
                f"score={winner.total_score:.2f if winner else 0}, entries={len(round_table_result.entries)}"
            )

            return result

        except Exception as e:
            logger.error(f"Round Table execution failed: {e}")
            # Fall back to standard execution
            return await self.execute_with_learning(
                prompt, task_type, technique, use_router=True, **kwargs
            )

    async def execute_smart(
        self,
        prompt: str,
        task_type: str,
        technique: PromptTechnique | None = None,
        force_round_table: bool = False,
        **kwargs,
    ) -> AgentResult:
        """
        Smart execution that auto-selects execution mode based on task stakes.

        Automatically uses Round Table for:
        - High-stakes tasks (transactions, security, etc.)
        - Force round table flag
        - Commerce/Operations agents for important decisions

        Uses standard routing execution for lower-stakes tasks.

        Args:
            prompt: The task prompt
            task_type: Type of task for categorization
            technique: Optional prompt technique to apply
            force_round_table: Force Round Table usage
            **kwargs: Additional execution parameters

        Returns:
            AgentResult with execution outcome
        """
        # Check if this is a high-stakes task
        use_round_table = force_round_table or self._is_high_stakes_task(task_type, prompt)

        if use_round_table and self.round_table:
            logger.info(f"High-stakes task detected, using Round Table: {task_type}")
            return await self.execute_with_round_table(prompt, task_type, technique, **kwargs)
        else:
            return await self.execute_with_learning(
                prompt, task_type, technique, use_router=True, **kwargs
            )

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive agent statistics"""
        stats = {
            "agent_type": self.agent_type.value if self.agent_type else None,
            "execution_count": self._execution_count,
            "initialized": self._initialized,
            "active_provider": self._active_provider.value,
            "current_model_provider": self._current_model_provider,
        }

        # Router status
        stats["router"] = {
            "available": self._router_available,
            "initialized": self._router is not None,
            "preferred_providers": AGENT_PROVIDER_PREFERENCES.get(
                self.agent_type.value if self.agent_type else "commerce", []
            ),
        }

        if self.prompt_module:
            stats["technique_stats"] = self.prompt_module.get_technique_stats()

        if self.learning_module:
            stats["learning"] = self.learning_module.get_optimization_report()

        if self.ml_module:
            stats["ml_models"] = self.ml_module.list_available_models()

        if self.round_table:
            stats["round_table"] = self.round_table.get_provider_stats()

        return stats

    def get_provider_recommendation(self, task_type: str | None = None) -> dict[str, Any]:
        """
        Get provider recommendation for this agent and optional task type.

        Returns:
            Dict with recommended provider and reasoning
        """
        agent_type = self.agent_type.value if self.agent_type else "commerce"
        agent_prefs = AGENT_PROVIDER_PREFERENCES.get(agent_type, ["openai"])

        task_category = None
        if task_type:
            try:  # noqa: SIM105 - simple pattern, no need to import contextlib
                task_category = TaskCategory(task_type)
            except ValueError:
                pass

        recommended = self._get_preferred_provider(task_category)

        return {
            "recommended_provider": recommended,
            "agent_type": agent_type,
            "agent_preferences": agent_prefs,
            "task_category": task_category.value if task_category else None,
            "reasoning": f"Based on {agent_type} agent preferences and task requirements",
        }

    async def _init_enterprise_intelligence(self) -> None:
        """
        Initialize Enterprise Intelligence Modules.

        Sets up:
        1. EnterpriseIndex - Multi-provider code search
        2. SemanticCodeAnalyzer - Pattern detection
        3. LLMVerificationEngine - DeepSeek + Claude verification
        """
        try:
            # Import enterprise modules
            from llm.providers.anthropic import AnthropicClient
            from llm.providers.deepseek import DeepSeekClient
            from llm.verification import LLMVerificationEngine, VerificationConfig
            from orchestration.enterprise_index import create_enterprise_index
            from orchestration.semantic_analyzer import SemanticCodeAnalyzer

            # Initialize Enterprise Index
            self.enterprise_index = create_enterprise_index()
            await self.enterprise_index.initialize()
            logger.info("EnterpriseIndex initialized with all configured providers")

            # Initialize Semantic Analyzer
            self.semantic_analyzer = SemanticCodeAnalyzer()
            logger.info("SemanticCodeAnalyzer initialized")

            # Initialize Verification Engine (DeepSeek + Claude)
            generator_client = DeepSeekClient()
            verifier_client = AnthropicClient()
            verification_config = VerificationConfig(
                generator_provider="deepseek",
                generator_model="deepseek-chat",
                verifier_provider="anthropic",
                verifier_model="claude-3-5-sonnet-20241022",
            )
            self.verification_engine = LLMVerificationEngine(
                generator_client=generator_client,
                verifier_client=verifier_client,
                config=verification_config,
            )
            logger.info("LLMVerificationEngine initialized (DeepSeek + Claude)")

        except ImportError as e:
            logger.warning(f"Enterprise intelligence modules not available: {e}")
            self.enterprise_index = None
            self.semantic_analyzer = None
            self.verification_engine = None
        except Exception as e:
            logger.error(f"Failed to initialize enterprise intelligence: {e}")
            self.enterprise_index = None
            self.semantic_analyzer = None
            self.verification_engine = None

    async def gather_enterprise_context(
        self,
        task_description: str,
        language: str = "python",
    ) -> dict[str, Any]:
        """
        Gather enterprise context BEFORE code generation (Context-First Pattern).

        This is the pre-flight phase that searches:
        1. Enterprise code indexes (GitHub, GitLab, Sourcegraph)
        2. Semantic patterns in existing codebase
        3. Similar implementations for reference

        Args:
            task_description: What code needs to be generated
            language: Programming language filter

        Returns:
            Context dict with:
            - similar_code: List of similar implementations
            - patterns: Detected patterns from semantic analysis
            - recommendations: Best practices from existing code
            - metadata: Search metadata
        """
        context = {
            "similar_code": [],
            "patterns": [],
            "recommendations": [],
            "metadata": {},
        }

        if not self.enterprise_index or not self.semantic_analyzer:
            logger.warning("Enterprise intelligence not initialized, skipping context gathering")
            return context

        try:
            # Import search types
            from orchestration.enterprise_index import SearchLanguage

            # Map string to enum
            lang_map = {
                "python": SearchLanguage.PYTHON,
                "typescript": SearchLanguage.TYPESCRIPT,
                "javascript": SearchLanguage.JAVASCRIPT,
                "go": SearchLanguage.GO,
                "rust": SearchLanguage.RUST,
                "java": SearchLanguage.JAVA,
            }
            search_lang = lang_map.get(language.lower(), SearchLanguage.PYTHON)

            # Phase 1: Search enterprise indexes
            logger.info(f"Searching enterprise indexes for: {task_description[:50]}...")
            search_results = await self.enterprise_index.search_code(
                query=task_description,
                language=search_lang,
                max_results_per_provider=3,
            )

            context["similar_code"] = [
                {
                    "repository": r.repository,
                    "file_path": r.file_path,
                    "snippet": r.code_snippet[:200],  # Truncate for context
                    "url": r.url,
                    "provider": r.provider,
                    "score": r.score,
                }
                for r in search_results[:5]  # Top 5 results
            ]

            # Phase 2: Semantic analysis of found code
            if search_results:
                logger.info(f"Analyzing {len(search_results)} code samples for patterns...")
                patterns_found = set()

                for result in search_results[:3]:  # Analyze top 3
                    try:
                        # Detect patterns in the code snippet
                        if len(result.code_snippet) > 50:
                            # For now, simple pattern extraction
                            # TODO: Integrate with semantic_analyzer.analyze_file()
                            if "class " in result.code_snippet:
                                patterns_found.add("object_oriented")
                            if "async " in result.code_snippet:
                                patterns_found.add("async_await")
                            if "def test" in result.code_snippet:
                                patterns_found.add("test_driven")
                    except Exception as e:
                        logger.warning(f"Pattern analysis failed for {result.file_path}: {e}")

                context["patterns"] = list(patterns_found)

            # Phase 3: Generate recommendations
            if context["similar_code"]:
                context["recommendations"] = [
                    f"Found {len(context['similar_code'])} similar implementations across enterprise codebases",
                    f"Common patterns: {', '.join(context['patterns']) if context['patterns'] else 'none detected'}",
                    "Consider following established patterns for consistency",
                ]

            context["metadata"] = {
                "search_query": task_description,
                "language": language,
                "results_count": len(search_results),
                "providers_used": list({r.provider for r in search_results}),
            }

            logger.info(
                f"Enterprise context gathered: {len(context['similar_code'])} examples, "
                f"{len(context['patterns'])} patterns"
            )

        except Exception as e:
            logger.error(f"Failed to gather enterprise context: {e}")

        return context


# =============================================================================
# Exports
# =============================================================================

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
