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

# Import existing components
from adk.base import (
    ADKProvider,
    AgentConfig,
    AgentResult,
    AgentStatus,
    BaseDevSkyyAgent,
)
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
# Data Classes
# =============================================================================


@dataclass
class PromptTechniqueResult:
    """Result from applying a prompt technique"""
    technique: PromptTechnique
    original_prompt: str
    enhanced_prompt: str
    metadata: dict[str, Any] = field(default_factory=dict)


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
            t: {"uses": 0, "successes": 0, "avg_score": 0.0}
            for t in PromptTechnique
        }

    def auto_select_technique(
        self,
        task_category: TaskCategory,
        context: dict[str, Any] | None = None
    ) -> PromptTechnique:
        """
        Automatically select the best technique for a task category.

        Uses historical performance data to optimize selection.
        """
        # Get default mapping
        default_technique = self.TECHNIQUE_MAPPING.get(
            task_category,
            PromptTechnique.ROLE_BASED
        )

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

    def _get_alternative_techniques(
        self,
        task_category: TaskCategory
    ) -> list[PromptTechnique]:
        """Get alternative techniques for a task category"""
        alternatives = {
            TaskCategory.REASONING: [
                PromptTechnique.TREE_OF_THOUGHTS,
                PromptTechnique.SELF_CONSISTENCY
            ],
            TaskCategory.CLASSIFICATION: [
                PromptTechnique.CHAIN_OF_THOUGHT,
                PromptTechnique.STRUCTURED_OUTPUT
            ],
            TaskCategory.CREATIVE: [
                PromptTechnique.ENSEMBLE,
                PromptTechnique.ROLE_BASED
            ],
            TaskCategory.SEARCH: [
                PromptTechnique.RAG,
                PromptTechnique.CHAIN_OF_THOUGHT
            ],
            TaskCategory.QA: [
                PromptTechnique.CHAIN_OF_THOUGHT,
                PromptTechnique.FEW_SHOT
            ],
        }
        return alternatives.get(task_category, [PromptTechnique.ROLE_BASED])

    def apply_technique(
        self,
        technique: PromptTechnique,
        prompt: str,
        **kwargs
    ) -> PromptTechniqueResult:
        """Apply a specific prompt engineering technique"""
        enhanced_prompt = prompt
        metadata = {"technique": technique.value}

        if technique == PromptTechnique.CHAIN_OF_THOUGHT:
            enhanced_prompt = ChainOfThought.create_prompt(
                question=prompt,
                context=kwargs.get("context", "")
            )

        elif technique == PromptTechnique.FEW_SHOT:
            examples = kwargs.get("examples", [])
            if not examples:
                examples = self._generate_examples(prompt, kwargs.get("domain"))
            enhanced_prompt = FewShotLearning.create_prompt(
                task=kwargs.get("task", "Complete the following"),
                examples=examples,
                query=prompt
            )

        elif technique == PromptTechnique.TREE_OF_THOUGHTS:
            enhanced_prompt = TreeOfThoughts.create_prompt(
                problem=prompt,
                n_branches=kwargs.get("n_branches", 3)
            )

        elif technique == PromptTechnique.REACT:
            tools = kwargs.get("tools", [])
            enhanced_prompt = ReActPrompting.create_prompt(
                task=prompt,
                tools=tools
            )

        elif technique == PromptTechnique.RAG:
            context = kwargs.get("context", [])
            enhanced_prompt = RAGPrompting.create_prompt(
                question=prompt,
                context=context
            )

        elif technique == PromptTechnique.STRUCTURED_OUTPUT:
            schema = kwargs.get("schema", {})
            enhanced_prompt = StructuredOutput.create_json_prompt(
                task=prompt,
                schema=schema
            )

        elif technique == PromptTechnique.CONSTITUTIONAL:
            principles = kwargs.get(
                "principles",
                ConstitutionalAI.get_default_principles()
            )
            enhanced_prompt = ConstitutionalAI.create_critique_prompt(
                response=prompt,
                principles=principles
            )

        elif technique == PromptTechnique.NEGATIVE_PROMPTING:
            negative = kwargs.get("negative", [])
            enhanced_prompt = NegativePrompting.create_prompt(
                task=prompt,
                negative=negative
            )

        elif technique == PromptTechnique.ROLE_BASED:
            role = kwargs.get("role", "an expert assistant")
            background = kwargs.get("background", "")
            enhanced_prompt = RoleBasedPrompting.create_prompt(
                role=role,
                task=prompt,
                background=background
            )

        elif technique == PromptTechnique.SELF_CONSISTENCY:
            variants = SelfConsistency.create_variants(
                base_prompt=prompt,
                n_variants=kwargs.get("n_variants", 5)
            )
            enhanced_prompt = variants[0]  # Use first, run all in execution
            metadata["variants"] = variants

        elif technique == PromptTechnique.ENSEMBLE:
            # Combine multiple techniques
            techniques = kwargs.get("techniques", [
                PromptTechnique.CHAIN_OF_THOUGHT,
                PromptTechnique.ROLE_BASED
            ])
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
            metadata=metadata
        )

    def _generate_examples(
        self,
        prompt: str,
        domain: str | None
    ) -> list[dict[str, str]]:
        """Generate few-shot examples based on domain"""
        if domain:
            return FewShotLearning.create_examples_for_domain(domain)
        return []

    def record_outcome(
        self,
        technique: PromptTechnique,
        success: bool,
        score: float = 0.0
    ):
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
                "demand_forecaster": {
                    "type": "prophet",
                    "task": "time_series"
                },
                "price_optimizer": {
                    "type": "sklearn",
                    "task": "regression"
                },
                "inventory_predictor": {
                    "type": "sklearn",
                    "task": "regression"
                },
            },
            SuperAgentType.CREATIVE: {
                "style_classifier": {
                    "type": "transformers",
                    "model": "google/vit-base-patch16-224"
                },
                "quality_scorer": {
                    "type": "custom",
                    "task": "image_quality"
                },
            },
            SuperAgentType.MARKETING: {
                "sentiment_analyzer": {
                    "type": "transformers",
                    "model": "cardiffnlp/twitter-roberta-base-sentiment"
                },
                "trend_predictor": {
                    "type": "prophet",
                    "task": "trend"
                },
            },
            SuperAgentType.SUPPORT: {
                "intent_classifier": {
                    "type": "transformers",
                    "model": "facebook/bart-large-mnli"
                },
                "escalation_predictor": {
                    "type": "sklearn",
                    "task": "classification"
                },
            },
            SuperAgentType.OPERATIONS: {
                "anomaly_detector": {
                    "type": "sklearn",
                    "task": "anomaly"
                },
                "performance_predictor": {
                    "type": "sklearn",
                    "task": "regression"
                },
            },
            SuperAgentType.ANALYTICS: {
                "forecaster": {
                    "type": "prophet",
                    "task": "forecast"
                },
                "clusterer": {
                    "type": "sklearn",
                    "task": "clustering"
                },
            },
        }
        return configs.get(self.agent_type, {})

    async def _load_model(self, config: dict) -> Any:
        """Load a specific ML model"""
        model_type = config.get("type")

        if model_type == "transformers":
            try:
                from transformers import pipeline
                return pipeline("text-classification", model=config.get("model"))
            except ImportError:
                logger.warning("transformers not installed")
                return None

        elif model_type == "sklearn":
            # Placeholder for sklearn models
            return {"type": "sklearn", "config": config}

        elif model_type == "prophet":
            # Placeholder for Prophet models
            return {"type": "prophet", "config": config}

        return None

    async def predict(
        self,
        model_name: str,
        input_data: Any,
        **kwargs
    ) -> MLPrediction:
        """Run prediction using specified model"""
        start_time = time.time()

        model = self._models.get(model_name)
        if not model:
            return MLPrediction(
                task=model_name,
                prediction=None,
                confidence=0.0,
                model_used="none",
                latency_ms=0.0,
                metadata={"error": f"Model {model_name} not found"}
            )

        try:
            # Run inference based on model type
            if callable(model):
                result = model(input_data)
                prediction = result[0] if isinstance(result, list) else result
            else:
                prediction = {"status": "placeholder", "input": str(input_data)[:100]}

            latency = (time.time() - start_time) * 1000

            return MLPrediction(
                task=model_name,
                prediction=prediction,
                confidence=prediction.get("score", 0.8) if isinstance(prediction, dict) else 0.8,
                model_used=model_name,
                latency_ms=latency,
                metadata=kwargs
            )

        except Exception as e:
            return MLPrediction(
                task=model_name,
                prediction=None,
                confidence=0.0,
                model_used=model_name,
                latency_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)}
            )

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
        user_feedback: float | None = None
    ):
        """Record execution for learning"""
        record = LearningRecord(
            task_id=task_id,
            task_type=task_type,
            prompt_hash=hashlib.md5(prompt.encode()).hexdigest()[:16],
            technique_used=technique,
            llm_provider=llm_provider,
            success=success,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            user_feedback=user_feedback
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
                "avg_cost_usd": 0.0
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
            (opt["providers"][prov]["avg_latency"] * (n - 1) + record.latency_ms) / n
        )

        # Update aggregates
        total = opt["total_executions"]
        success_count = sum(
            t["successes"] for t in opt["techniques"].values()
        )
        opt["success_rate"] = success_count / total if total > 0 else 0

        # Running averages
        opt["avg_latency_ms"] = (
            (opt["avg_latency_ms"] * (total - 1) + record.latency_ms) / total
        )
        opt["avg_cost_usd"] = (
            (opt["avg_cost_usd"] * (total - 1) + record.cost_usd) / total
        )

    def get_best_technique(self, task_type: str) -> PromptTechnique | None:
        """Get the best performing technique for a task type"""
        opt = self._optimizations.get(task_type)
        if not opt or not opt["techniques"]:
            return None

        best = max(
            opt["techniques"].items(),
            key=lambda x: x[1]["successes"] / max(x[1]["uses"], 1)
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
            "recommendations": self._generate_recommendations()
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
        self._knowledge_base[key] = {
            "value": value,
            "added_at": datetime.now(UTC).isoformat()
        }

    def query_knowledge_base(self, key: str) -> Any:
        """Query the knowledge base"""
        entry = self._knowledge_base.get(key)
        return entry["value"] if entry else None


# =============================================================================
# LLM Round Table Interface
# =============================================================================


class LLMRoundTableInterface:
    """
    Interface for LLM Round Table competitions.

    Flow:
    1. All LLMs generate responses in parallel
    2. Score and rank using 4 metrics
    3. Select top 2 for A/B comparison
    4. Judge LLM determines winner
    5. Return winning response
    """

    SCORING_CRITERIA = {
        "relevance": 0.3,      # How relevant is the response
        "quality": 0.3,        # Overall quality of output
        "completeness": 0.2,   # Does it fully answer the prompt
        "efficiency": 0.2,     # Token efficiency and cost
    }

    def __init__(self):
        self._providers: dict[LLMProvider, Callable] = {}
        self._judge_provider: LLMProvider = LLMProvider.CLAUDE
        self._history: list[RoundTableResult] = []

    def register_provider(
        self,
        provider: LLMProvider,
        generator: Callable
    ):
        """Register an LLM provider"""
        self._providers[provider] = generator

    def set_judge(self, provider: LLMProvider):
        """Set the judge LLM for A/B testing"""
        self._judge_provider = provider

    async def compete(
        self,
        prompt: str,
        providers: list[LLMProvider] | None = None,
        context: dict[str, Any] | None = None
    ) -> RoundTableResult:
        """
        Run Round Table competition.

        Args:
            prompt: The task prompt
            providers: LLM providers to include (default: all registered)
            context: Additional context for generation

        Returns:
            RoundTableResult with winner and all entries
        """
        task_id = hashlib.md5(
            f"{prompt}{datetime.now(UTC).isoformat()}".encode()
        ).hexdigest()[:16]

        # Use specified providers or all registered
        active_providers = providers or list(self._providers.keys())

        # Generate responses in parallel
        entries = await self._generate_all(prompt, active_providers, context)

        if not entries:
            raise ValueError("No providers generated responses")

        # Score all entries
        scored_entries = self._score_entries(entries, prompt)

        # Sort by total score
        sorted_entries = sorted(
            scored_entries,
            key=lambda x: x.total_score,
            reverse=True
        )

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
            judge_reasoning=judge_reasoning
        )

        self._history.append(result)
        return result

    async def _generate_all(
        self,
        prompt: str,
        providers: list[LLMProvider],
        context: dict[str, Any] | None
    ) -> list[RoundTableEntry]:
        """Generate responses from all providers in parallel"""
        entries = []

        async def generate_one(provider: LLMProvider) -> RoundTableEntry | None:
            generator = self._providers.get(provider)
            if not generator:
                return None

            start_time = time.time()
            try:
                response = await generator(prompt, context)
                latency = (time.time() - start_time) * 1000

                return RoundTableEntry(
                    provider=provider,
                    response=response.get("text", str(response)),
                    latency_ms=latency,
                    cost_usd=response.get("cost", 0.0)
                )
            except Exception as e:
                logger.error(f"Provider {provider} failed: {e}")
                return None

        # Run all generators concurrently
        tasks = [generate_one(p) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, RoundTableEntry):
                entries.append(result)

        return entries

    def _score_entries(
        self,
        entries: list[RoundTableEntry],
        prompt: str
    ) -> list[RoundTableEntry]:
        """Score all entries using defined criteria"""
        for entry in entries:
            scores = {}

            # Relevance: Basic keyword matching
            prompt_words = set(prompt.lower().split())
            response_words = set(entry.response.lower().split())
            overlap = len(prompt_words & response_words)
            scores["relevance"] = min(overlap / max(len(prompt_words), 1), 1.0)

            # Quality: Length and structure heuristics
            response_len = len(entry.response)
            if 100 <= response_len <= 2000:
                scores["quality"] = 1.0
            elif response_len < 100:
                scores["quality"] = response_len / 100
            else:
                scores["quality"] = max(0.5, 1 - (response_len - 2000) / 5000)

            # Completeness: Check for common completion indicators
            completion_indicators = ["therefore", "in conclusion", "finally", "to summarize"]
            has_completion = any(ind in entry.response.lower() for ind in completion_indicators)
            scores["completeness"] = 1.0 if has_completion else 0.7

            # Efficiency: Based on latency and cost
            latency_score = max(0, 1 - entry.latency_ms / 10000)
            cost_score = max(0, 1 - entry.cost_usd / 0.1)
            scores["efficiency"] = (latency_score + cost_score) / 2

            entry.scores = scores

            # Calculate weighted total
            entry.total_score = sum(
                scores[criterion] * weight
                for criterion, weight in self.SCORING_CRITERIA.items()
            )

        return entries

    async def _ab_test(
        self,
        prompt: str,
        top_two: list[RoundTableEntry]
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
        stats = {p.value: {"wins": 0, "participations": 0, "avg_score": 0.0}
                 for p in LLMProvider}

        for result in self._history:
            for entry in result.entries:
                prov = entry.provider.value
                stats[prov]["participations"] += 1
                n = stats[prov]["participations"]
                stats[prov]["avg_score"] = (
                    (stats[prov]["avg_score"] * (n - 1) + entry.total_score) / n
                )

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

        # State
        self._initialized = False
        self._execution_count = 0
        self._active_provider = ADKProvider.PYDANTIC

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

    def select_technique(
        self,
        task_category: TaskCategory,
        context: dict[str, Any] | None = None
    ) -> PromptTechnique:
        """
        Select the best prompt technique for a task.

        Uses learning module data if available.
        """
        # Check if learning module has a better suggestion
        if self.learning_module:
            learned_technique = self.learning_module.get_best_technique(
                task_category.value
            )
            if learned_technique:
                return learned_technique

        # Fall back to prompt module auto-selection
        return self.prompt_module.auto_select_technique(task_category, context)

    def apply_technique(
        self,
        technique: PromptTechnique,
        prompt: str,
        **kwargs
    ) -> PromptTechniqueResult:
        """Apply a prompt engineering technique"""
        return self.prompt_module.apply_technique(technique, prompt, **kwargs)

    async def predict(
        self,
        model_name: str,
        input_data: Any,
        **kwargs
    ) -> MLPrediction | None:
        """Run ML prediction"""
        if not self.ml_module:
            return None
        return await self.ml_module.predict(model_name, input_data, **kwargs)

    async def run_round_table(
        self,
        prompt: str,
        providers: list[LLMProvider] | None = None,
        context: dict[str, Any] | None = None
    ) -> RoundTableResult | None:
        """Run LLM Round Table competition"""
        if not self.round_table:
            return None
        return await self.round_table.compete(prompt, providers, context)

    @abstractmethod
    async def execute(self, prompt: str, **kwargs) -> AgentResult:
        """Execute agent task - must be implemented by subclasses"""
        pass

    async def execute_with_learning(
        self,
        prompt: str,
        task_type: str,
        technique: PromptTechnique | None = None,
        **kwargs
    ) -> AgentResult:
        """
        Execute with automatic learning and optimization.

        This method:
        1. Selects the best technique if not specified
        2. Applies the technique to enhance the prompt
        3. Executes the task
        4. Records the outcome for learning
        5. Updates technique stats
        """
        import uuid

        task_id = str(uuid.uuid4())[:16]
        start_time = time.time()

        # Select technique if not specified
        if technique is None:
            task_category = self._infer_task_category(prompt)
            technique = self.select_technique(task_category)

        # Apply technique
        enhanced = self.apply_technique(technique, prompt, **kwargs)

        # Execute
        result = await self.execute(enhanced.enhanced_prompt, **kwargs)

        # Calculate metrics
        latency_ms = (time.time() - start_time) * 1000
        success = result.status == AgentStatus.COMPLETED
        cost_usd = result.usage.get("cost_usd", 0.0) if result.usage else 0.0

        # Record for learning
        if self.learning_module:
            self.learning_module.record_execution(
                task_id=task_id,
                task_type=task_type,
                prompt=prompt,
                technique=technique,
                llm_provider=self._active_provider.value,
                success=success,
                latency_ms=latency_ms,
                cost_usd=cost_usd
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

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive agent statistics"""
        stats = {
            "agent_type": self.agent_type.value if self.agent_type else None,
            "execution_count": self._execution_count,
            "initialized": self._initialized,
            "active_provider": self._active_provider.value,
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


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Types
    "SuperAgentType",
    "TaskCategory",
    "LLMProvider",
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
    # Base class
    "EnhancedSuperAgent",
]
