#!/usr/bin/env python3
"""
DevSkyy Self-Improving Prompt Agent - ML-Based Prompt Optimization
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class OptimizationStrategy(str, Enum):
    """Prompt optimization strategies."""
    APE = "automatic_prompt_engineer"
    OPRO = "optimization_by_prompting"
    DSPY = "dspy_compilation"
    EVOLUTIONARY = "evolutionary_mutation"
    REFLEXION = "reflexion_verbal_rl"
    HYBRID = "hybrid_optimization"


class FeedbackType(str, Enum):
    """Types of feedback for learning."""
    EXPLICIT_RATING = "explicit_rating"
    IMPLICIT_ACCEPT = "implicit_accept"
    IMPLICIT_REJECT = "implicit_reject"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    A_B_WINNER = "ab_winner"


@dataclass
class PromptVariant:
    """A single prompt variant being tested/optimized."""
    id: str
    prompt_text: str
    version: int = 1
    parent_id: Optional[str] = None
    mutation_type: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    total_rating_sum: float = 0.0
    rating_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_used_at: Optional[str] = None

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0

    @property
    def average_rating(self) -> float:
        return self.total_rating_sum / self.rating_count if self.rating_count > 0 else 0.0

    @property
    def confidence(self) -> float:
        n = self.success_count + self.failure_count
        return min(1.0, n / 100) if n > 0 else 0.0

    def record_feedback(self, feedback: FeedbackType, value: Optional[float] = None):
        self.last_used_at = datetime.utcnow().isoformat()
        if feedback in (FeedbackType.TASK_SUCCESS, FeedbackType.IMPLICIT_ACCEPT, FeedbackType.A_B_WINNER):
            self.success_count += 1
        elif feedback in (FeedbackType.TASK_FAILURE, FeedbackType.IMPLICIT_REJECT):
            self.failure_count += 1
        if feedback == FeedbackType.EXPLICIT_RATING and value is not None:
            self.total_rating_sum += value
            self.rating_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "prompt_text": self.prompt_text, "version": self.version,
            "parent_id": self.parent_id, "mutation_type": self.mutation_type,
            "success_count": self.success_count, "failure_count": self.failure_count,
            "success_rate": self.success_rate, "average_rating": self.average_rating,
            "confidence": self.confidence, "created_at": self.created_at, "last_used_at": self.last_used_at,
        }


@dataclass
class OptimizationRun:
    """Record of a single optimization run."""
    run_id: str
    strategy: OptimizationStrategy
    task_description: str
    initial_prompt: str
    best_prompt: str
    best_score: float
    iterations: int
    variants_tested: int
    started_at: str
    completed_at: str
    improvement_pct: float


@dataclass
class ReflexionMemory:
    """Episodic memory for Reflexion-style self-improvement."""
    task_type: str
    trajectory: List[Dict[str, str]] = field(default_factory=list)
    reflections: List[str] = field(default_factory=list)

    def add_step(self, action: str, observation: str, reward: float):
        self.trajectory.append({
            "action": action, "observation": observation, "reward": reward,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def add_reflection(self, reflection: str):
        self.reflections.append(reflection)

    def get_recent_context(self, n: int = 5) -> str:
        recent = self.trajectory[-n:] if self.trajectory else []
        parts = []
        for step in recent:
            parts.extend([f"Action: {step['action']}", f"Observation: {step['observation']}", f"Reward: {step['reward']}", "---"])
        return "\n".join(parts)

    def get_reflections_context(self) -> str:
        if not self.reflections:
            return "No prior reflections for this task type."
        return "\n".join([f"• {r}" for r in self.reflections[-10:]])


class MutationOperator:
    """Mutation operators for evolutionary prompt optimization."""

    @staticmethod
    def direct_mutation_prompt() -> str:
        return """
You are a prompt optimization expert. Your task is to improve the following prompt.

ORIGINAL PROMPT:
{original_prompt}

PERFORMANCE FEEDBACK:
{feedback}

Generate an improved version of this prompt that:
1. Maintains the original intent
2. Addresses the feedback issues
3. Is clearer and more specific
4. Includes better structure

IMPROVED PROMPT:
"""

    @staticmethod
    def eda_mutation_prompt() -> str:
        return """
Analyze these high-performing prompts and generate a new prompt that combines their best qualities:

HIGH-PERFORMING PROMPTS:
{top_prompts}

TASK DESCRIPTION:
{task_description}

Generate a new prompt that synthesizes the effective patterns from the examples above.

NEW PROMPT:
"""

    @staticmethod
    def crossover_prompt() -> str:
        return """
Combine the best elements of these two prompts:

PARENT PROMPT A (Success rate: {score_a}):
{prompt_a}

PARENT PROMPT B (Success rate: {score_b}):
{prompt_b}

TASK:
{task_description}

Generate a child prompt that inherits the most effective elements from both parents.

CHILD PROMPT:
"""


class SelfImprovingPromptAgent:
    """ML-based agent that continuously improves prompts through feedback."""

    def __init__(
        self,
        strategy: OptimizationStrategy = OptimizationStrategy.HYBRID,
        llm_client: Optional[Any] = None,
        storage_path: Optional[Path] = None,
        population_size: int = 10,
        elite_size: int = 3,
        max_iterations: int = 20,
    ):
        self.strategy = strategy
        self.llm_client = llm_client
        self.storage_path = storage_path
        self.population_size = population_size
        self.elite_size = elite_size
        self.max_iterations = max_iterations
        self._registry: Dict[str, List[PromptVariant]] = {}
        self._reflexion_memory: Dict[str, ReflexionMemory] = {}
        self._opro_history: Dict[str, List[Tuple[str, float]]] = {}
        self._run_history: List[OptimizationRun] = []

    def _generate_variant_id(self, prompt_text: str) -> str:
        hash_input = f"{prompt_text}_{datetime.utcnow().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]

    def register_prompt(self, task_name: str, initial_prompt: str) -> PromptVariant:
        """Register a new prompt for optimization."""
        variant = PromptVariant(
            id=self._generate_variant_id(initial_prompt),
            prompt_text=initial_prompt,
            version=1,
        )
        self._registry[task_name] = [variant]
        self._opro_history[task_name] = []
        return variant

    def get_prompt(self, task_name: str) -> Optional[str]:
        """Get the current best prompt for a task."""
        variants = self._registry.get(task_name, [])
        if not variants:
            return None
        best = max(variants, key=lambda v: (v.success_rate * v.confidence, v.average_rating))
        return best.prompt_text

    def get_best_variant(self, task_name: str) -> Optional[PromptVariant]:
        """Get the best performing variant for a task."""
        variants = self._registry.get(task_name, [])
        if not variants:
            return None
        return max(variants, key=lambda v: (v.success_rate * v.confidence, v.average_rating))

    def record_feedback(self, task_name: str, feedback: FeedbackType, value: Optional[float] = None, variant_id: Optional[str] = None):
        """Record feedback for the current or specified variant."""
        variants = self._registry.get(task_name, [])
        if not variants:
            return
        if variant_id:
            for v in variants:
                if v.id == variant_id:
                    v.record_feedback(feedback, value)
                    return
        else:
            best = self.get_best_variant(task_name)
            if best:
                best.record_feedback(feedback, value)

    def get_stats(self, task_name: str) -> Dict[str, Any]:
        """Get optimization statistics for a task."""
        variants = self._registry.get(task_name, [])
        if not variants:
            return {"error": f"No variants registered for {task_name}"}
        best = self.get_best_variant(task_name)
        return {
            "task_name": task_name,
            "total_variants": len(variants),
            "best_variant_id": best.id if best else None,
            "best_success_rate": best.success_rate if best else 0.0,
            "best_average_rating": best.average_rating if best else 0.0,
            "total_feedback_collected": sum(v.success_count + v.failure_count for v in variants),
        }


__all__ = [
    "OptimizationStrategy", "FeedbackType", "PromptVariant", "OptimizationRun",
    "ReflexionMemory", "MutationOperator", "SelfImprovingPromptAgent",
]
