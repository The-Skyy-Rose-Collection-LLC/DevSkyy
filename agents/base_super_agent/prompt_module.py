"""
Prompt Engineering Module
==========================

Provides access to all 17 prompt engineering techniques with
auto-selection based on task category and performance history.
"""

import hashlib
import logging
from typing import Any

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

from .types import PromptTechniqueResult, SuperAgentType, TaskCategory

logger = logging.getLogger(__name__)


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
        """Apply technique with tool calling optimization."""
        if not tools:
            return self.apply_technique(technique, prompt, **kwargs)

        # Apply base technique first
        base_result = self.apply_technique(technique, prompt, tools=tools, **kwargs)
        enhanced = base_result.enhanced_prompt

        # Add tool-specific enhancements based on technique
        tool_names = [t.get("name", "unknown") for t in tools]
        tool_list = ", ".join(tool_names)

        if technique == PromptTechnique.REACT:
            enhanced = f"""
Task: {prompt}

Available Tools: {tool_list}

IMPORTANT: Use the ReAct format with tool calling:
Thought: [Your reasoning about what to do]
Action: tool_name(arguments)
Observation: [Tool result will appear here]
... (repeat Thought/Action/Observation as needed)
Final Answer: [Your final response]

{enhanced}
""".strip()

        elif technique == PromptTechnique.CHAIN_OF_THOUGHT:
            enhanced = f"""
{enhanced}

Available Tools: {tool_list}

When solving this problem step-by-step, consider which tools would help at each step.
Call tools when you need information, data, or actions you cannot perform directly.
""".strip()

        elif technique == PromptTechnique.TREE_OF_THOUGHTS:
            enhanced = f"""
{enhanced}

Available Tools for exploration: {tool_list}

For each branch of reasoning, identify which tools would provide the most valuable information.
Prioritize tool calls that reduce uncertainty or provide critical data.
""".strip()

        elif technique == PromptTechnique.RAG:
            enhanced = f"""
{enhanced}

Additional Tools Available: {tool_list}

Use tools to supplement the retrieved context when:
- The context is insufficient
- You need real-time data
- You need to perform actions
""".strip()

        else:
            enhanced = f"""
{enhanced}

Available Tools: {tool_list}

You have access to these tools to help complete the task. Use them when appropriate.
""".strip()

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


__all__ = [
    "PromptEngineeringModule",
    "TaskCategoryAnalyzer",
    "get_task_analyzer",
]
