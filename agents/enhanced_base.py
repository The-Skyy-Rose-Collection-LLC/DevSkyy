"""
Enhanced Agent Base Classes
============================

Refactored agent base classes with improved:
- Error handling (standardized exception hierarchy)
- Type safety (comprehensive Pydantic models)
- Common patterns extraction
- Reduced code duplication

Provides backward-compatible enhancements to SuperAgent.
"""

from __future__ import annotations

import asyncio
import builtins
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field, field_validator

from agents.base_legacy import (
    AgentCapability,
    AgentConfig,
    ExecutionResult,
    PlanStep,
    RetrievalContext,
    SuperAgent,
    ValidationResult,
)
from agents.errors import (
    AgentError,
    ExecutionError,
    TimeoutError,
    ValidationError,
    wrap_exception,
)
from core.runtime.tool_registry import ToolCallContext, ToolRegistry

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Enhanced Configuration Models
# =============================================================================


class EnhancedAgentConfig(BaseModel):
    """Enhanced agent configuration with validation."""

    name: str = Field(..., min_length=1, max_length=100, description="Agent name")
    description: str = Field(..., min_length=10, description="Agent description")
    version: str = Field(default="1.0.0", description="Agent version")
    capabilities: set[AgentCapability] = Field(
        default_factory=set, description="Agent capabilities"
    )
    default_timeout: float = Field(
        default=30.0, ge=1.0, le=3600.0, description="Default timeout (1-3600s)"
    )
    max_retries: int = Field(default=3, ge=0, le=10, description="Max retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0, description="Retry delay (s)")
    enable_caching: bool = Field(default=True, description="Enable result caching")
    enable_telemetry: bool = Field(default=True, description="Enable telemetry/metrics")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate agent name format."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Agent name must be alphanumeric (with _ or -)")
        return v.lower()

    def to_base_config(self) -> AgentConfig:
        """Convert to base AgentConfig for backward compatibility."""
        return AgentConfig(
            name=self.name,
            description=self.description,
            version=self.version,
            capabilities=self.capabilities,
            default_timeout=self.default_timeout,
        )


# =============================================================================
# Enhanced Data Models
# =============================================================================


class EnhancedPlanStep(BaseModel):
    """Enhanced PlanStep with comprehensive validation."""

    # Identity
    step_id: str = Field(default_factory=lambda: __import__("uuid").uuid4().hex[:8])

    # Tool Reference
    tool_name: str = Field(..., min_length=1, description="Tool to execute")
    description: str = Field(..., min_length=1, description="Step description")

    # Inputs/Outputs
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)

    # Dependencies
    depends_on: list[str] = Field(default_factory=list, description="Step IDs this depends on")
    priority: int = Field(default=0, ge=0, description="Execution priority")

    # Status
    status: str = Field(default="pending", pattern="^(pending|running|completed|failed)$")
    error: str | None = None

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    timeout: float | None = Field(default=None, gt=0, description="Timeout in seconds")

    @property
    def is_ready(self) -> bool:
        """Check if step is ready to execute."""
        return self.status == "pending" and len(self.depends_on) == 0

    @property
    def duration_seconds(self) -> float | None:
        """Get execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_base_step(self) -> PlanStep:
        """Convert to base PlanStep for backward compatibility."""
        return PlanStep(
            step_id=self.step_id,
            tool_name=self.tool_name,
            description=self.description,
            inputs=self.inputs,
            outputs=self.outputs,
            depends_on=self.depends_on,
            priority=self.priority,
            status=self.status,
            error=self.error,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )


class EnhancedRetrievalContext(BaseModel):
    """Enhanced RetrievalContext with validation."""

    # Query
    query: str = Field(default="", description="Original query")

    # Retrieved Documents
    documents: list[dict[str, Any]] = Field(default_factory=list)
    relevance_scores: list[float] = Field(
        default_factory=list,
        description="Relevance scores (0-1)",
    )

    # Metadata
    retrieval_method: str = Field(default="semantic", description="Retrieval method")
    total_candidates: int = Field(default=0, ge=0, description="Total candidates searched")
    retrieval_time_ms: float = Field(default=0, ge=0, description="Retrieval time (ms)")

    # Source Information
    sources: list[str] = Field(default_factory=list, description="Source identifiers")

    @field_validator("relevance_scores")
    @classmethod
    def validate_scores(cls, v: list[float]) -> list[float]:
        """Validate relevance scores are between 0 and 1."""
        if any(score < 0 or score > 1 for score in v):
            raise ValueError("Relevance scores must be between 0 and 1")
        return v

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

    def to_base_context(self) -> RetrievalContext:
        """Convert to base RetrievalContext for backward compatibility."""
        return RetrievalContext(
            query=self.query,
            documents=self.documents,
            relevance_scores=self.relevance_scores,
            retrieval_method=self.retrieval_method,
            total_candidates=self.total_candidates,
            retrieval_time_ms=self.retrieval_time_ms,
            sources=self.sources,
        )


# =============================================================================
# Enhanced Result Models
# =============================================================================


class EnhancedExecutionResult(BaseModel):
    """Enhanced execution result with better error context."""

    tool_name: str
    step_id: str
    success: bool = True
    result: dict[str, Any] | None = None
    error: AgentError | None = None
    duration_seconds: float = 0.0
    started_at: datetime
    completed_at: datetime | None = None
    retries: int = 0
    cached: bool = False

    class Config:
        arbitrary_types_allowed = True

    def to_base_result(self) -> ExecutionResult:
        """Convert to base ExecutionResult for backward compatibility."""
        return ExecutionResult(
            tool_name=self.tool_name,
            step_id=self.step_id,
            success=self.success,
            result=self.result,
            error=str(self.error) if self.error else None,
            error_type=type(self.error).__name__ if self.error else None,
            duration_seconds=self.duration_seconds,
            started_at=self.started_at,
            completed_at=self.completed_at,
            retries=self.retries,
        )


class EnhancedValidationResult(BaseModel):
    """Enhanced validation result with structured warnings/errors."""

    is_valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning."""
        self.warnings.append(warning)

    def to_base_validation(self) -> ValidationResult:
        """Convert to base ValidationResult for backward compatibility."""
        result = ValidationResult(is_valid=self.is_valid)
        result.errors = self.errors.copy()
        result.warnings = self.warnings.copy()
        result.quality_score = self.quality_score
        result.confidence_score = self.confidence_score
        return result


# =============================================================================
# Execution Decorators
# =============================================================================


def with_error_handling(
    retryable: bool = True,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for standardized error handling.

    Wraps exceptions in AgentError and provides retry logic.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except AgentError:
                    # Already wrapped, re-raise
                    raise
                except Exception as e:
                    last_error = e
                    wrapped = wrap_exception(e, retryable=retryable)

                    if not wrapped.retryable or attempt == max_retries - 1:
                        logger.error(f"{func.__name__} failed: {wrapped}")
                        raise wrapped

                    # Retry
                    wait_time = retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): "
                        f"{wrapped}. Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)

            # Should never reach here, but just in case
            if last_error:
                raise wrap_exception(last_error)
            raise ExecutionError("Unknown error in wrapped function")

        return wrapper  # type: ignore[return-value]

    return decorator


def with_timeout(seconds: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for enforcing timeouts.

    Raises TimeoutError if operation exceeds timeout.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except builtins.TimeoutError as e:
                raise TimeoutError(
                    f"{func.__name__} timed out after {seconds}s",
                    timeout_seconds=seconds,
                    original_error=e,
                )

        return wrapper  # type: ignore[return-value]

    return decorator


def with_telemetry(
    metric_name: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for telemetry/metrics collection.

    Logs execution time and success/failure.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            name = metric_name or func.__name__
            started_at = datetime.now(UTC)

            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now(UTC) - started_at).total_seconds()
                logger.info(f"{name} completed in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now(UTC) - started_at).total_seconds()
                logger.error(f"{name} failed after {duration:.2f}s: {e}")
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


# =============================================================================
# Enhanced Super Agent
# =============================================================================


class EnhancedSuperAgent(SuperAgent):
    """
    Enhanced SuperAgent with improved error handling and common patterns.

    Improvements over base SuperAgent:
    - Standardized error handling with AgentError hierarchy
    - Built-in retry logic with exponential backoff
    - Comprehensive validation with Pydantic models
    - Reduced boilerplate in subclasses
    - Better type safety
    - Telemetry/metrics support

    Backward compatible with existing SuperAgent interface.
    """

    def __init__(
        self,
        config: EnhancedAgentConfig | AgentConfig,
        registry: ToolRegistry,
    ):
        # Convert enhanced config to base config if needed
        if isinstance(config, EnhancedAgentConfig):
            self._enhanced_config = config
            base_config = config.to_base_config()
        else:
            base_config = config
            # Create enhanced config from base
            self._enhanced_config = EnhancedAgentConfig(
                name=config.name,
                description=config.description,
                version=config.version,
                capabilities=config.capabilities,
                default_timeout=config.default_timeout,
            )

        super().__init__(base_config, registry)

    # -------------------------------------------------------------------------
    # Enhanced Execution with Error Handling
    # -------------------------------------------------------------------------

    async def execute_step_with_retry(
        self,
        step: PlanStep,
        retrieval_context: RetrievalContext,
        context: ToolCallContext,
    ) -> EnhancedExecutionResult:
        """
        Execute a step with retry logic and error handling.

        Enhanced version of _execute_step with:
        - Automatic retry on transient failures
        - Exponential backoff
        - Structured error capture
        - Telemetry
        """
        started_at = datetime.now(UTC)
        retries = 0

        for attempt in range(self._enhanced_config.max_retries + 1):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    self.registry.execute(step.tool_name, step.inputs, context),
                    timeout=step.timeout or self._enhanced_config.default_timeout,
                )

                return EnhancedExecutionResult(
                    tool_name=step.tool_name,
                    step_id=step.step_id,
                    success=result.success,
                    result=result.result,
                    duration_seconds=result.duration_seconds,
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                    retries=retries,
                )

            except builtins.TimeoutError as e:
                error = TimeoutError(
                    f"Step {step.step_id} timed out",
                    timeout_seconds=step.timeout or self._enhanced_config.default_timeout,
                    original_error=e,
                )
                retries += 1

                if attempt < self._enhanced_config.max_retries:
                    wait_time = self._enhanced_config.retry_delay * (2**attempt)
                    logger.warning(
                        f"Step {step.step_id} timed out (attempt {attempt + 1}). "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                return EnhancedExecutionResult(
                    tool_name=step.tool_name,
                    step_id=step.step_id,
                    success=False,
                    error=error,
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                    retries=retries,
                )

            except Exception as e:
                error = wrap_exception(
                    e,
                    message=f"Step {step.step_id} failed: {e}",
                    retryable=True,
                )
                retries += 1

                if error.retryable and attempt < self._enhanced_config.max_retries:
                    wait_time = self._enhanced_config.retry_delay * (2**attempt)
                    logger.warning(
                        f"Step {step.step_id} failed (attempt {attempt + 1}): {error}. "
                        f"Retrying in {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                return EnhancedExecutionResult(
                    tool_name=step.tool_name,
                    step_id=step.step_id,
                    success=False,
                    error=error,
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                    retries=retries,
                )

        # Should never reach here
        return EnhancedExecutionResult(
            tool_name=step.tool_name,
            step_id=step.step_id,
            success=False,
            error=ExecutionError(f"Step {step.step_id} failed after all retries"),
            started_at=started_at,
            completed_at=datetime.now(UTC),
            retries=retries,
        )

    def validate_inputs(self, inputs: dict[str, Any]) -> EnhancedValidationResult:
        """
        Validate agent inputs.

        Override in subclass for custom validation logic.
        """
        validation = EnhancedValidationResult()

        # Basic validation
        if not inputs:
            validation.add_warning("Empty inputs provided")

        return validation

    def validate_outputs(self, outputs: dict[str, Any]) -> EnhancedValidationResult:
        """
        Validate agent outputs.

        Override in subclass for custom validation logic.
        """
        validation = EnhancedValidationResult()

        if not outputs:
            validation.add_error("No outputs generated")

        return validation

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _handle_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
    ) -> AgentError:
        """
        Handle and wrap errors consistently.

        Converts generic exceptions to AgentError with context.
        """
        if isinstance(error, AgentError):
            if context:
                error.context.update(context)
            return error

        return wrap_exception(error)

    def _create_error_result(
        self,
        tool_name: str,
        step_id: str,
        error: Exception,
        started_at: datetime,
    ) -> EnhancedExecutionResult:
        """Create error result from exception."""
        agent_error = self._handle_error(error)

        return EnhancedExecutionResult(
            tool_name=tool_name,
            step_id=step_id,
            success=False,
            error=agent_error,
            started_at=started_at,
            completed_at=datetime.now(UTC),
        )


# =============================================================================
# Tool Execution Mixin
# =============================================================================


class ToolExecutionMixin:
    """
    Mixin for common tool execution patterns.

    Provides helper methods for tool registration and execution.
    """

    registry: ToolRegistry  # Type hint for IDE

    async def execute_tool_with_retry(
        self,
        tool_name: str,
        inputs: dict[str, Any],
        context: ToolCallContext,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Execute tool with retry logic."""
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                result = await self.registry.execute(tool_name, inputs, context)
                if result.success:
                    return result.result or {}
                else:
                    raise ExecutionError(
                        result.error or "Tool execution failed",
                        tool_name=tool_name,
                    )
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.warning(
                        f"Tool {tool_name} failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)

        raise ExecutionError(
            f"Tool {tool_name} failed after {max_retries} attempts",
            tool_name=tool_name,
            original_error=last_error,
        )

    def validate_tool_inputs(
        self,
        tool_name: str,
        inputs: dict[str, Any],
        required_fields: list[str] | None = None,
    ) -> None:
        """Validate tool inputs."""
        if required_fields:
            missing = [field for field in required_fields if field not in inputs]
            if missing:
                raise ValidationError(
                    f"Missing required fields for {tool_name}: {', '.join(missing)}",
                    context={"tool_name": tool_name, "missing_fields": missing},
                )


__all__ = [
    # Configuration
    "EnhancedAgentConfig",
    # Data Models
    "EnhancedPlanStep",
    "EnhancedRetrievalContext",
    # Results
    "EnhancedExecutionResult",
    "EnhancedValidationResult",
    # Base Classes
    "EnhancedSuperAgent",
    "ToolExecutionMixin",
    # Decorators
    "with_error_handling",
    "with_timeout",
    "with_telemetry",
]
