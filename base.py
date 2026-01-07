"""
DevSkyy Agent Base Classes
==========================

Base classes and dataclasses for the Super Agent architecture.

Components:
- SuperAgent: Abstract base class for all agents
- AgentConfig: Configuration dataclass
- AgentCapability: Capability enum
- LLMCategory: LLM routing category
- PlanStep: Workflow step definition
- RetrievalContext: RAG context holder
- ExecutionResult: Step execution result
- ValidationResult: Validation outcome

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from core.runtime.tool_registry import (
    ToolCallContext,
    ToolCategory,
    ToolRegistry,
    get_tool_registry,
)

# =============================================================================
# Enums
# =============================================================================


class AgentCapability(str, Enum):
    """
    Agent capabilities define what an agent can do.

    Used for:
    - Capability-based routing
    - Permission checking
    - Feature discovery
    """

    # Infrastructure
    CODE_SCANNING = "code_scanning"
    CODE_FIXING = "code_fixing"
    SELF_HEALING = "self_healing"
    MONITORING = "monitoring"
    DEPLOYMENT = "deployment"
    BACKUP_RESTORE = "backup_restore"

    # WordPress/Elementor
    WORDPRESS_MANAGEMENT = "wordpress_management"
    ELEMENTOR_BUILDER = "elementor_builder"
    THEME_GENERATION = "theme_generation"
    PLUGIN_MANAGEMENT = "plugin_management"

    # E-Commerce
    PRODUCT_MANAGEMENT = "product_management"
    ORDER_MANAGEMENT = "order_management"
    INVENTORY_MANAGEMENT = "inventory_management"
    PRICING_OPTIMIZATION = "pricing_optimization"
    CUSTOMER_MANAGEMENT = "customer_management"

    # Content
    CONTENT_GENERATION = "content_generation"
    SEO_OPTIMIZATION = "seo_optimization"
    SOCIAL_MEDIA = "social_media"
    EMAIL_MARKETING = "email_marketing"
    COPYWRITING = "copywriting"

    # Media
    IMAGE_GENERATION = "image_generation"
    IMAGE_EDITING = "image_editing"
    VIDEO_GENERATION = "video_generation"
    THREE_D_GENERATION = "3d_generation"
    VIRTUAL_TRYON = "virtual_tryon"

    # AI/ML
    NLP_PROCESSING = "nlp_processing"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TREND_PREDICTION = "trend_prediction"
    DEMAND_FORECASTING = "demand_forecasting"
    RECOMMENDATION = "recommendation"

    # Integration
    API_INTEGRATION = "api_integration"
    WEBHOOK_MANAGEMENT = "webhook_management"
    DATA_SYNC = "data_sync"


class LLMCategory(str, Enum):
    """
    LLM routing categories for 2-LLM agreement architecture.

    Categories:
    - CATEGORY_A: Reasoning/Planning (Claude, GPT-4)
    - CATEGORY_B: Execution/Coding (Sonnet, GPT-4-turbo)
    - CATEGORY_C: Fast/Simple (Haiku, GPT-3.5, Groq)
    """

    CATEGORY_A = "category_a"  # Reasoning-focused (Claude Opus, GPT-4)
    CATEGORY_B = "category_b"  # Execution-focused (Claude Sonnet, GPT-4-turbo)
    CATEGORY_C = "category_c"  # Speed-focused (Claude Haiku, GPT-3.5, Groq)


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    PLANNING = "planning"
    RETRIEVING = "retrieving"
    EXECUTING = "executing"
    VALIDATING = "validating"
    EMITTING = "emitting"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AgentConfig:
    """
    Configuration for a Super Agent.

    Defines the agent's identity, capabilities, and operational parameters.
    """

    # Identity
    name: str
    description: str
    version: str = "1.0.0"

    # Capabilities
    capabilities: set[AgentCapability] = field(default_factory=set)

    # LLM Routing
    llm_category: LLMCategory = LLMCategory.CATEGORY_B

    # Tool Configuration
    tool_category: ToolCategory = ToolCategory.SYSTEM

    # Operational Parameters
    default_timeout: float = 60.0
    max_concurrent_tools: int = 5
    max_retries: int = 3
    retry_delay: float = 1.0

    # Feature Flags
    enable_caching: bool = True
    enable_logging: bool = True
    enable_metrics: bool = True

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has a specific capability."""
        return capability in self.capabilities

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": [c.value for c in self.capabilities],
            "llm_category": self.llm_category.value,
            "tool_category": self.tool_category.value,
            "default_timeout": self.default_timeout,
            "max_concurrent_tools": self.max_concurrent_tools,
        }


# =============================================================================
# Workflow Dataclasses
# =============================================================================


@dataclass
class PlanStep:
    """
    A single step in an agent's execution plan.

    Steps form a DAG (Directed Acyclic Graph) with dependencies.
    """

    # Identity
    step_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # Tool Reference
    tool_name: str = ""
    description: str = ""

    # Inputs/Outputs
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)

    # Dependencies
    depends_on: list[str] = field(default_factory=list)
    priority: int = 0

    # Status
    status: str = "pending"
    error: str | None = None

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None

    @property
    def is_ready(self) -> bool:
        """Check if step is ready to execute (no pending dependencies)."""
        return self.status == "pending" and len(self.depends_on) == 0

    @property
    def duration_seconds(self) -> float | None:
        """Get execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class RetrievalContext:
    """
    Context from RAG (Retrieval-Augmented Generation) operations.

    Holds retrieved documents and their relevance scores.
    """

    # Query
    query: str = ""

    # Retrieved Documents
    documents: list[dict[str, Any]] = field(default_factory=list)
    relevance_scores: list[float] = field(default_factory=list)

    # Metadata
    retrieval_method: str = "semantic"
    total_candidates: int = 0
    retrieval_time_ms: float = 0

    # Source Information
    sources: list[str] = field(default_factory=list)

    def get_top_k(self, k: int = 5) -> list[dict[str, Any]]:
        """Get top-k documents by relevance."""
        if not self.documents:
            return []

        # Pair documents with scores and sort
        paired = list(zip(self.documents, self.relevance_scores, strict=False))
        paired.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in paired[:k]]

    def to_context_string(self, max_docs: int = 5) -> str:
        """Convert to a string suitable for LLM context."""
        top_docs = self.get_top_k(max_docs)
        if not top_docs:
            return ""

        parts = ["Retrieved Context:"]
        for i, doc in enumerate(top_docs, 1):
            content = doc.get("content", str(doc))
            parts.append(f"\n[{i}] {content[:500]}...")

        return "\n".join(parts)


@dataclass
class ExecutionResult:
    """
    Result of executing a single plan step.
    """

    # Identity
    tool_name: str
    step_id: str = ""

    # Outcome
    success: bool = False
    result: Any | None = None
    error: str | None = None
    error_type: str | None = None

    # Timing
    duration_seconds: float = 0.0
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Metadata
    retries: int = 0
    from_cache: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "step_id": self.step_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "retries": self.retries,
            "from_cache": self.from_cache,
        }


@dataclass
class ValidationResult:
    """
    Result of validating execution outputs.
    """

    # Outcome
    is_valid: bool = False

    # Issues
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Scores
    quality_score: float = 0.0
    confidence_score: float = 0.0

    # Metadata
    validated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    validator: str = ""

    def add_error(self, error: str) -> None:
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "quality_score": self.quality_score,
            "confidence_score": self.confidence_score,
            "validated_at": self.validated_at.isoformat(),
        }


# =============================================================================
# Super Agent Base Class
# =============================================================================


class SuperAgent(ABC):
    """
    Abstract base class for all DevSkyy Super Agents.

    Super Agents follow a structured workflow:
    1. Plan - Create execution plan
    2. Retrieve - Fetch relevant context (RAG)
    3. Execute - Run tools according to plan
    4. Validate - Check outputs
    5. Emit - Return structured results

    Subclasses must implement:
    - _plan(): Create execution plan
    - _retrieve(): Fetch relevant context
    - _execute_step(): Execute a single step
    - _validate(): Validate results
    - _emit(): Emit final output

    Usage:
        class MyAgent(SuperAgent):
            def __init__(self):
                config = AgentConfig(
                    name="my_agent",
                    description="Does something",
                    capabilities={AgentCapability.CONTENT_GENERATION},
                )
                super().__init__(config)

            async def _plan(self, request, context):
                return [PlanStep(...)]

            # ... implement other abstract methods

        agent = MyAgent()
        result = await agent.run({"action": "generate"})
    """

    def __init__(
        self,
        config: AgentConfig,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.config = config
        self.registry = registry or get_tool_registry()
        self._status = AgentStatus.IDLE
        self._tools: dict[str, Any] = {}

        # Initialize and register tools
        self._register_tools()

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name

    @property
    def status(self) -> AgentStatus:
        """Get current status."""
        return self._status

    # -------------------------------------------------------------------------
    # Abstract Methods (Must Implement)
    # -------------------------------------------------------------------------

    def _register_tools(self) -> None:  # noqa: B027
        """
        Register agent-specific tools with the registry.

        Override to register custom tools. This is intentionally not abstract
        as not all agents need custom tools.
        """
        pass

    @abstractmethod
    async def _plan(
        self,
        request: dict[str, Any],
        context: ToolCallContext,
    ) -> list[PlanStep]:
        """
        Create execution plan from request.

        Args:
            request: Input request parameters
            context: Execution context

        Returns:
            List of PlanStep objects forming the execution plan
        """
        pass

    @abstractmethod
    async def _retrieve(
        self,
        request: dict[str, Any],
        plan: list[PlanStep],
        context: ToolCallContext,
    ) -> RetrievalContext:
        """
        Retrieve relevant context for execution.

        Args:
            request: Input request parameters
            plan: Execution plan
            context: Execution context

        Returns:
            RetrievalContext with relevant documents
        """
        pass

    @abstractmethod
    async def _execute_step(
        self,
        step: PlanStep,
        retrieval_context: RetrievalContext,
        context: ToolCallContext,
    ) -> ExecutionResult:
        """
        Execute a single plan step.

        Args:
            step: Step to execute
            retrieval_context: Retrieved context
            context: Execution context

        Returns:
            ExecutionResult with outcome
        """
        pass

    @abstractmethod
    async def _validate(
        self,
        results: list[ExecutionResult],
        context: ToolCallContext,
    ) -> ValidationResult:
        """
        Validate execution results.

        Args:
            results: List of execution results
            context: Execution context

        Returns:
            ValidationResult with validation outcome
        """
        pass

    @abstractmethod
    async def _emit(
        self,
        results: list[ExecutionResult],
        validation: ValidationResult,
        context: ToolCallContext,
    ) -> dict[str, Any]:
        """
        Emit final structured output.

        Args:
            results: List of execution results
            validation: Validation result
            context: Execution context

        Returns:
            Final output dictionary
        """
        pass

    # -------------------------------------------------------------------------
    # Main Execution Flow
    # -------------------------------------------------------------------------

    async def run(
        self,
        request: dict[str, Any],
        context: ToolCallContext | None = None,
    ) -> dict[str, Any]:
        """
        Execute the agent workflow.

        Args:
            request: Input request parameters
            context: Optional execution context

        Returns:
            Final output from _emit()
        """
        context = context or ToolCallContext(agent_id=self.name)
        context.start_execution()

        try:
            # Phase 1: Planning
            self._status = AgentStatus.PLANNING
            plan = await self._plan(request, context)

            if not plan:
                return {
                    "status": "error",
                    "error": "Empty plan generated",
                    "agent": self.name,
                }

            # Phase 2: Retrieval
            self._status = AgentStatus.RETRIEVING
            retrieval_context = await self._retrieve(request, plan, context)

            # Phase 3: Execution
            self._status = AgentStatus.EXECUTING
            results = await self._execute_plan(plan, retrieval_context, context)

            # Phase 4: Validation
            self._status = AgentStatus.VALIDATING
            validation = await self._validate(results, context)

            # Phase 5: Emission
            self._status = AgentStatus.EMITTING
            output = await self._emit(results, validation, context)

            self._status = AgentStatus.COMPLETED
            context.complete_execution()

            return output

        except Exception as e:
            self._status = AgentStatus.FAILED
            context.complete_execution()

            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent": self.name,
                "request_id": context.request_id,
            }

    async def _execute_plan(
        self,
        plan: list[PlanStep],
        retrieval_context: RetrievalContext,
        context: ToolCallContext,
    ) -> list[ExecutionResult]:
        """
        Execute all steps in the plan respecting dependencies.

        Args:
            plan: Execution plan
            retrieval_context: Retrieved context
            context: Execution context

        Returns:
            List of execution results
        """
        results: list[ExecutionResult] = []
        completed_steps: set[str] = set()
        step_outputs: dict[str, Any] = {}

        # Sort by priority
        remaining = sorted(plan, key=lambda s: s.priority)

        while remaining:
            # Find ready steps
            ready = [s for s in remaining if all(dep in completed_steps for dep in s.depends_on)]

            if not ready:
                # Circular dependency or missing dependency
                break

            # Execute ready steps (could parallelize based on max_concurrent_tools)
            for step in ready:
                # Substitute outputs from previous steps
                resolved_inputs = self._resolve_inputs(step.inputs, step_outputs)
                step.inputs = resolved_inputs

                result = await self._execute_step(step, retrieval_context, context)
                results.append(result)

                # Track completion
                completed_steps.add(step.step_id)
                if result.success and result.result:
                    step_outputs[step.step_id] = result.result

                    # Also store by tool name for convenience
                    if isinstance(result.result, dict):
                        for key, value in result.result.items():
                            step_outputs[key] = value

                remaining.remove(step)

        return results

    def _resolve_inputs(
        self,
        inputs: dict[str, Any],
        step_outputs: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Resolve template references in inputs.

        Supports {key} syntax to reference previous step outputs.
        """
        resolved = {}

        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("{") and value.endswith("}"):
                ref_key = value[1:-1]
                resolved[key] = step_outputs.get(ref_key, value)
            else:
                resolved[key] = value

        return resolved

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_capabilities(self) -> set[AgentCapability]:
        """Get agent capabilities."""
        return self.config.capabilities

    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has capability."""
        return self.config.has_capability(capability)

    def to_dict(self) -> dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            "name": self.name,
            "status": self._status.value,
            "config": self.config.to_dict(),
            "tools": list(self._tools.keys()),
        }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "AgentCapability",
    "LLMCategory",
    "AgentStatus",
    # Config
    "AgentConfig",
    # Workflow Dataclasses
    "PlanStep",
    "RetrievalContext",
    "ExecutionResult",
    "ValidationResult",
    # Base Class
    "SuperAgent",
]
