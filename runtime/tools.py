"""
DevSkyy Tool Runtime
====================

Production-grade tool registry and execution runtime for AI agents.

Components:
- ToolRegistry: Central registry for all tools
- ToolCallContext: Execution context with permissions, timeouts, tracing
- ToolSeverity: Risk classification for tools
- ToolCategory: Functional categorization

References:
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
- Anthropic Tool Use: https://docs.anthropic.com/en/docs/tool-use
- JSON Schema: https://json-schema.org/draft/2020-12/json-schema-core.html

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ToolCategory(str, Enum):
    """Tool functional categories."""

    CONTENT = "content"
    COMMERCE = "commerce"
    MEDIA = "media"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    INTEGRATION = "integration"
    SYSTEM = "system"
    AI = "ai"
    OPERATIONS = "operations"
    SECURITY = "security"


class ToolSeverity(str, Enum):
    """
    Tool risk/severity levels.

    Determines required permissions and confirmation requirements.
    """

    READ_ONLY = "read_only"  # No side effects, safe to execute
    LOW = "low"  # Minor side effects, easily reversible
    MEDIUM = "medium"  # Moderate side effects, may require cleanup
    HIGH = "high"  # Significant side effects, careful review needed
    DESTRUCTIVE = "destructive"  # Irreversible actions, requires confirmation


class ParameterType(str, Enum):
    """JSON Schema parameter types."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ExecutionStatus(str, Enum):
    """Tool execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


# =============================================================================
# Context Models
# =============================================================================


@dataclass(slots=True)
class ToolCallContext:
    """
    Execution context for tool calls.

    Provides tracing, permissions, timeouts, and metadata for tool execution.
    Memory-optimized with __slots__ for high-frequency instantiation.
    """

    # Identification
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    user_id: str | None = None
    agent_id: str | None = None

    # Permissions
    permissions: set[str] = field(default_factory=set)
    is_admin: bool = False

    # Execution control
    timeout_seconds: float = 30.0
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Tracing
    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_permission(self, permission: str) -> bool:
        """Check if context has required permission."""
        if self.is_admin:
            return True
        return permission in self.permissions

    def has_any_permission(self, permissions: set[str]) -> bool:
        """Check if context has any of the required permissions."""
        if self.is_admin:
            return True
        return bool(self.permissions & permissions)

    def start_execution(self) -> None:
        """Mark execution as started."""
        self.started_at = datetime.now(UTC)

    def complete_execution(self) -> None:
        """Mark execution as completed."""
        self.completed_at = datetime.now(UTC)

    @property
    def duration_seconds(self) -> float | None:
        """Get execution duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/serialization."""
        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "permissions": list(self.permissions),
            "is_admin": self.is_admin,
            "timeout_seconds": self.timeout_seconds,
            "trace_id": self.trace_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration_seconds": self.duration_seconds,
        }


# =============================================================================
# Tool Definition Models
# =============================================================================


class ToolParameter(BaseModel):
    """Tool parameter definition with JSON Schema support."""

    model_config = ConfigDict(extra="forbid")

    name: str
    type: ParameterType
    description: str
    required: bool = False
    default: Any = None
    enum: list[Any] | None = None
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    items: dict[str, Any] | None = None  # For array types
    properties: dict[str, Any] | None = None  # For object types

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {
            "type": self.type.value,
            "description": self.description,
        }

        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default
        if self.min_value is not None:
            schema["minimum"] = self.min_value
        if self.max_value is not None:
            schema["maximum"] = self.max_value
        if self.min_length is not None:
            schema["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
        if self.pattern:
            schema["pattern"] = self.pattern
        if self.items:
            schema["items"] = self.items
        if self.properties:
            schema["properties"] = self.properties

        return schema


class ToolSpec(BaseModel):
    """
    Complete tool specification.

    Defines a tool's interface, constraints, and metadata.

    Supports Anthropic Advanced Tool Use (beta) features:
    - defer_loading: Tool Search - load on-demand for 85% token reduction
    - allowed_callers: Programmatic Tool Calling (PTC) - batch operations via code
    - input_examples: Tool Use Examples - concrete examples for 90% accuracy
    """

    model_config = ConfigDict(extra="forbid")

    # Identity
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    version: str = "1.0.0"

    # Classification
    category: ToolCategory
    severity: ToolSeverity = ToolSeverity.LOW

    # Interface
    parameters: list[ToolParameter] = Field(default_factory=list)
    input_schema: dict[str, Any] | None = None  # Raw JSON schema override
    returns: dict[str, Any] | None = None

    # Constraints
    permissions: set[str] = Field(default_factory=set)
    requires_auth: bool = False
    rate_limit: int | None = None  # Requests per minute
    timeout_seconds: float = 30.0

    # Behavior
    idempotent: bool = False
    cacheable: bool = False
    cache_ttl_seconds: int = 300

    # Advanced Tool Use (Anthropic Beta)
    defer_loading: bool = False  # Tool Search: load on-demand vs upfront
    allowed_callers: list[str] = Field(
        default_factory=list
    )  # PTC: e.g. ["code_execution_20250825"]
    input_examples: list[dict[str, Any]] = Field(
        default_factory=list
    )  # Concrete parameter examples

    # Metadata
    tags: set[str] = Field(default_factory=set)
    examples: list[dict[str, Any]] = Field(default_factory=list)
    enabled: bool = True

    # Implementation
    handler_path: str | None = None

    def get_required_params(self) -> list[str]:
        """Get list of required parameter names."""
        return [p.name for p in self.parameters if p.required]

    def get_json_schema(self) -> dict[str, Any]:
        """Get JSON Schema for parameters."""
        if self.input_schema:
            return self.input_schema

        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def to_openai_function(self) -> dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_json_schema(),
        }

    def to_anthropic_tool(self, include_advanced: bool = True) -> dict[str, Any]:
        """
        Convert to Anthropic tool format.

        Args:
            include_advanced: Include Advanced Tool Use fields (defer_loading, allowed_callers, input_examples)
        """
        tool: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_json_schema(),
        }

        # Add Advanced Tool Use fields if present
        if include_advanced:
            if self.defer_loading:
                tool["defer_loading"] = True
            if self.allowed_callers:
                tool["allowed_callers"] = self.allowed_callers
            if self.input_examples:
                tool["input_examples"] = self.input_examples

        return tool

    def to_mcp_tool(self, include_advanced: bool = True) -> dict[str, Any]:
        """
        Convert to MCP tool format.

        Args:
            include_advanced: Include Advanced Tool Use annotations
        """
        tool: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.get_json_schema(),
        }

        # Add annotations with Advanced Tool Use fields
        if include_advanced:
            annotations: dict[str, Any] = {
                "readOnlyHint": self.severity == ToolSeverity.READ_ONLY,
                "destructiveHint": self.severity == ToolSeverity.DESTRUCTIVE,
                "idempotentHint": self.idempotent,
            }
            if self.defer_loading:
                annotations["defer_loading"] = True
            if self.allowed_callers:
                annotations["allowed_callers"] = self.allowed_callers
            if self.input_examples:
                annotations["input_examples"] = self.input_examples

            tool["annotations"] = annotations

        return tool


# =============================================================================
# Execution Result
# =============================================================================


class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""

    model_config = ConfigDict(extra="forbid")

    # Identification
    tool_name: str
    request_id: str

    # Status
    status: ExecutionStatus
    success: bool

    # Result
    result: Any | None = None
    error: str | None = None
    error_type: str | None = None

    # Timing
    started_at: datetime
    completed_at: datetime
    duration_seconds: float

    # Metadata
    retries: int = 0
    from_cache: bool = False


# =============================================================================
# Tool Registry
# =============================================================================


# Type for tool handlers
ToolHandler = Callable[..., Any | Awaitable[Any]]
T = TypeVar("T")


class ToolRegistry:
    """
    Central registry for all DevSkyy tools.

    Features:
    - Tool registration with specs
    - Handler binding
    - Validation
    - Multi-format export (OpenAI, Anthropic, MCP)
    - Execution with context

    Usage:
        registry = ToolRegistry()

        @registry.tool(
            name="create_product",
            description="Create a new product",
            category=ToolCategory.COMMERCE,
            severity=ToolSeverity.MEDIUM,
        )
        async def create_product(name: str, price: float) -> dict:
            ...

        # Execute
        result = await registry.execute("create_product", {"name": "Test", "price": 99.99}, context)
    """

    _instance: ToolRegistry | None = None

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._cache: dict[str, Any] = {}

    @classmethod
    def get_instance(cls) -> ToolRegistry:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def register(
        self,
        spec: ToolSpec,
        handler: ToolHandler | None = None,
    ) -> None:
        """Register a tool with its specification."""
        self._tools[spec.name] = spec
        if handler:
            self._handlers[spec.name] = handler
        logger.debug(f"Registered tool: {spec.name} (category={spec.category.value})")

    def register_handler(self, name: str, handler: ToolHandler) -> None:
        """Register a handler for an existing tool."""
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        self._handlers[name] = handler

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        self._tools.pop(name, None)
        self._handlers.pop(name, None)

    def tool(
        self,
        name: str,
        description: str,
        category: ToolCategory,
        severity: ToolSeverity = ToolSeverity.LOW,
        input_schema: dict[str, Any] | None = None,
        permissions: set[str] | None = None,
        idempotent: bool = False,
        cacheable: bool = False,
        cache_ttl_seconds: int = 300,
        timeout_seconds: float = 30.0,
        tags: set[str] | None = None,
        # Advanced Tool Use (Anthropic Beta)
        defer_loading: bool = False,
        allowed_callers: list[str] | None = None,
        input_examples: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> Callable[[ToolHandler], ToolHandler]:
        """
        Decorator to register a tool.

        Usage:
            @registry.tool(
                name="my_tool",
                description="Does something",
                category=ToolCategory.SYSTEM,
                # Advanced Tool Use (optional)
                defer_loading=True,  # Load on-demand
                allowed_callers=["code_execution_20250825"],  # Enable PTC
                input_examples=[{"arg1": "example"}],  # Improve accuracy
            )
            async def my_tool(arg1: str) -> dict:
                return {"result": arg1}
        """

        def decorator(func: ToolHandler) -> ToolHandler:
            spec = ToolSpec(
                name=name,
                description=description,
                category=category,
                severity=severity,
                input_schema=input_schema,
                permissions=permissions or set(),
                idempotent=idempotent,
                cacheable=cacheable,
                cache_ttl_seconds=cache_ttl_seconds,
                timeout_seconds=timeout_seconds,
                tags=tags or set(),
                defer_loading=defer_loading,
                allowed_callers=allowed_callers or [],
                input_examples=input_examples or [],
                **kwargs,
            )
            self.register(spec, func)
            return func

        return decorator

    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------

    def get(self, name: str) -> ToolSpec | None:
        """Get tool specification by name."""
        return self._tools.get(name)

    def get_tool(self, name: str) -> ToolSpec | None:
        """Get tool specification by name (alias for get())."""
        return self.get(name)

    def get_handler(self, name: str) -> ToolHandler | None:
        """Get tool handler by name."""
        return self._handlers.get(name)

    def list_all(self) -> list[ToolSpec]:
        """Get all registered tools."""
        return list(self._tools.values())

    def list_enabled(self) -> list[ToolSpec]:
        """Get enabled tools only."""
        return [t for t in self._tools.values() if t.enabled]

    def get_by_category(self, category: ToolCategory) -> list[ToolSpec]:
        """Get tools by category."""
        return [t for t in self._tools.values() if t.category == category]

    def get_by_severity(self, severity: ToolSeverity) -> list[ToolSpec]:
        """Get tools by severity level."""
        return [t for t in self._tools.values() if t.severity == severity]

    def search(self, query: str) -> list[ToolSpec]:
        """Search tools by name or description."""
        query_lower = query.lower()
        return [
            t
            for t in self._tools.values()
            if query_lower in t.name.lower() or query_lower in t.description.lower()
        ]

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def validate_call(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: ToolCallContext | None = None,
    ) -> tuple[bool, list[str]]:
        """
        Validate tool call parameters and permissions.

        Returns:
            (is_valid, list_of_errors)
        """
        tool = self.get(tool_name)

        if not tool:
            return False, [f"Unknown tool: {tool_name}"]

        if not tool.enabled:
            return False, [f"Tool is disabled: {tool_name}"]

        errors: list[str] = []

        # Check permissions
        if context and tool.permissions:
            missing = tool.permissions - context.permissions
            if missing and not context.is_admin:
                errors.append(f"Missing permissions: {missing}")

        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in params:
                errors.append(f"Missing required parameter: {param.name}")

        # Validate parameter types and constraints
        for name, value in params.items():
            param = next((p for p in tool.parameters if p.name == name), None)

            if not param:
                # Allow extra params if no strict schema
                continue

            # Type validation
            type_errors = self._validate_param_type(param, value)
            errors.extend(type_errors)

        return len(errors) == 0, errors

    def _validate_param_type(self, param: ToolParameter, value: Any) -> list[str]:
        """Validate parameter type and constraints."""
        errors: list[str] = []
        expected_type = param.type

        # Type checks
        type_map = {
            ParameterType.STRING: str,
            ParameterType.INTEGER: int,
            ParameterType.NUMBER: (int, float),
            ParameterType.BOOLEAN: bool,
            ParameterType.ARRAY: list,
            ParameterType.OBJECT: dict,
        }

        expected = type_map.get(expected_type)
        if expected and not isinstance(value, expected):
            errors.append(f"Parameter {param.name} must be {expected_type.value}")
            return errors  # Skip further validation if type is wrong

        # Enum validation
        if param.enum and value not in param.enum:
            errors.append(f"Parameter {param.name} must be one of: {param.enum}")

        # Range validation
        if isinstance(value, int | float):
            if param.min_value is not None and value < param.min_value:
                errors.append(f"Parameter {param.name} must be >= {param.min_value}")
            if param.max_value is not None and value > param.max_value:
                errors.append(f"Parameter {param.name} must be <= {param.max_value}")

        # Length validation
        if isinstance(value, str):
            if param.min_length is not None and len(value) < param.min_length:
                errors.append(f"Parameter {param.name} must be at least {param.min_length} chars")
            if param.max_length is not None and len(value) > param.max_length:
                errors.append(f"Parameter {param.name} must be at most {param.max_length} chars")

        return errors

    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------

    async def execute(
        self,
        tool_name: str,
        params: dict[str, Any],
        context: ToolCallContext | None = None,
    ) -> ToolExecutionResult:
        """
        Execute a tool with validation and error handling.

        Args:
            tool_name: Name of the tool to execute
            params: Tool parameters
            context: Execution context

        Returns:
            ToolExecutionResult with status and result/error
        """
        context = context or ToolCallContext()
        started_at = datetime.now(UTC)
        context.start_execution()

        # Validate
        is_valid, errors = self.validate_call(tool_name, params, context)
        if not is_valid:
            return ToolExecutionResult(
                tool_name=tool_name,
                request_id=context.request_id,
                status=ExecutionStatus.FAILED,
                success=False,
                error="; ".join(errors),
                error_type="ValidationError",
                started_at=started_at,
                completed_at=datetime.now(UTC),
                duration_seconds=0,
            )

        tool = self.get(tool_name)
        handler = self.get_handler(tool_name)

        if not handler:
            return ToolExecutionResult(
                tool_name=tool_name,
                request_id=context.request_id,
                status=ExecutionStatus.FAILED,
                success=False,
                error=f"No handler registered for tool: {tool_name}",
                error_type="ConfigurationError",
                started_at=started_at,
                completed_at=datetime.now(UTC),
                duration_seconds=0,
            )

        # Check cache
        if tool and tool.cacheable:
            cache_key = f"{tool_name}:{hash(frozenset(params.items()))}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                return ToolExecutionResult(
                    tool_name=tool_name,
                    request_id=context.request_id,
                    status=ExecutionStatus.SUCCESS,
                    success=True,
                    result=cached,
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                    duration_seconds=0,
                    from_cache=True,
                )

        # Execute with timeout
        timeout = tool.timeout_seconds if tool else context.timeout_seconds
        retries = 0
        last_error: Exception | None = None

        while retries <= context.max_retries:
            try:
                if inspect.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(
                        handler(**params),
                        timeout=timeout,
                    )
                else:
                    # Run sync handler in executor
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: handler(**params)),
                        timeout=timeout,
                    )

                completed_at = datetime.now(UTC)
                context.complete_execution()

                # Cache result
                if tool and tool.cacheable:
                    cache_key = f"{tool_name}:{hash(frozenset(params.items()))}"
                    self._cache[cache_key] = result

                return ToolExecutionResult(
                    tool_name=tool_name,
                    request_id=context.request_id,
                    status=ExecutionStatus.SUCCESS,
                    success=True,
                    result=result,
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=(completed_at - started_at).total_seconds(),
                    retries=retries,
                )

            except TimeoutError:
                last_error = TimeoutError(f"Tool execution timed out after {timeout}s")
                retries += 1
                if retries <= context.max_retries:
                    await asyncio.sleep(context.retry_delay_seconds)

            except Exception as e:
                last_error = e
                retries += 1
                if retries <= context.max_retries:
                    await asyncio.sleep(context.retry_delay_seconds)

        # All retries exhausted
        completed_at = datetime.now(UTC)
        context.complete_execution()

        error_type = type(last_error).__name__ if last_error else "UnknownError"
        status = (
            ExecutionStatus.TIMEOUT
            if isinstance(last_error, asyncio.TimeoutError)
            else ExecutionStatus.FAILED
        )

        return ToolExecutionResult(
            tool_name=tool_name,
            request_id=context.request_id,
            status=status,
            success=False,
            error=str(last_error),
            error_type=error_type,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=(completed_at - started_at).total_seconds(),
            retries=retries,
        )

    # -------------------------------------------------------------------------
    # Export Formats
    # -------------------------------------------------------------------------

    def to_openai_functions(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        """Export as OpenAI function calling format."""
        tools = self.list_enabled() if enabled_only else self.list_all()
        return [t.to_openai_function() for t in tools]

    def to_anthropic_tools(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        """Export as Anthropic tool format."""
        tools = self.list_enabled() if enabled_only else self.list_all()
        return [t.to_anthropic_tool() for t in tools]

    def to_mcp_tools(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        """Export as MCP tool format."""
        tools = self.list_enabled() if enabled_only else self.list_all()
        return [t.to_mcp_tool() for t in tools]

    def export_schema(self) -> dict[str, Any]:
        """Export complete registry schema."""
        return {
            "version": "1.0.0",
            "total_tools": len(self._tools),
            "categories": {cat.value: len(self.get_by_category(cat)) for cat in ToolCategory},
            "tools": [t.model_dump() for t in self.list_all()],
        }


# =============================================================================
# Singleton Factory
# =============================================================================


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return ToolRegistry.get_instance()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "ToolCategory",
    "ToolSeverity",
    "ParameterType",
    "ExecutionStatus",
    # Context
    "ToolCallContext",
    # Specs
    "ToolParameter",
    "ToolSpec",
    # Results
    "ToolExecutionResult",
    # Registry
    "ToolRegistry",
    "get_tool_registry",
]
