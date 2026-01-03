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
                    loop = asyncio.get_running_loop()
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


# =============================================================================
# Tool Definitions (from orchestration/tool_registry.py)
# =============================================================================


class ToolDefinition(BaseModel):
    """
    Complete tool definition.

    Supports Anthropic Advanced Tool Use (beta) features:
    - defer_loading: Tool Search - load on-demand for 85% token reduction
    - allowed_callers: Programmatic Tool Calling (PTC) - batch operations via code
    - input_examples: Tool Use Examples - concrete examples for 90% accuracy
    """

    name: str
    description: str
    category: ToolCategory
    parameters: list[ToolParameter] = []
    returns: dict[str, Any] | None = None
    examples: list[dict[str, Any]] = []
    requires_auth: bool = False
    rate_limit: int | None = None  # Requests per minute
    timeout: float = 30.0
    enabled: bool = True

    # Advanced Tool Use (Anthropic Beta)
    defer_loading: bool = False  # Tool Search: load on-demand vs upfront
    allowed_callers: list[str] = []  # PTC: e.g. ["code_execution_20250825"]
    input_examples: list[dict[str, Any]] = []  # Concrete parameter examples

    # Implementation reference
    handler: str | None = None  # Module path to handler function

    def get_required_params(self) -> list[str]:
        """Get list of required parameter names"""
        return [p.name for p in self.parameters if p.required]

    def to_openai_function(self) -> dict:
        """Convert to OpenAI function calling format"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def to_anthropic_tool(self, include_advanced: bool = True) -> dict:
        """
        Convert to Anthropic tool format.

        Args:
            include_advanced: Include Advanced Tool Use fields (defer_loading, allowed_callers, input_examples)
        """
        tool: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {p.name: p.to_json_schema() for p in self.parameters},
                "required": self.get_required_params(),
            },
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

    def to_mcp_tool(self, include_advanced: bool = True) -> dict:
        """
        Convert to MCP tool format.

        Args:
            include_advanced: Include Advanced Tool Use annotations
        """
        tool: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {p.name: p.to_json_schema() for p in self.parameters},
                "required": self.get_required_params(),
            },
        }

        # Add annotations with Advanced Tool Use fields
        if include_advanced:
            annotations: dict[str, Any] = {
                "readOnlyHint": not self.requires_auth,
                "idempotentHint": False,
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
# Built-in Tools (37 tools)
# =============================================================================

BUILTIN_TOOLS = [
    # -------------------------------------------------------------------------
    # Content Tools (7)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="generate_product_description",
        description="Generate compelling product description for SkyyRose products",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(
                name="product_name",
                type=ParameterType.STRING,
                description="Product name",
                required=True,
            ),
            ToolParameter(
                name="collection",
                type=ParameterType.STRING,
                description="Collection (BLACK_ROSE, LOVE_HURTS, SIGNATURE)",
                required=True,
                enum=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"],
            ),
            ToolParameter(
                name="features",
                type=ParameterType.ARRAY,
                description="Product features",
                items={"type": "string"},
            ),
            ToolParameter(
                name="tone",
                type=ParameterType.STRING,
                description="Writing tone",
                default="luxury",
                enum=["luxury", "casual", "technical"],
            ),
        ],
        examples=[
            {
                "product_name": "Heart aRose Bomber",
                "collection": "BLACK_ROSE",
                "features": ["Rose gold zipper", "Embroidered back"],
            }
        ],
    ),
    ToolDefinition(
        name="generate_social_post",
        description="Generate social media post content",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(
                name="platform",
                type=ParameterType.STRING,
                description="Social platform",
                required=True,
                enum=["instagram", "tiktok", "twitter", "facebook"],
            ),
            ToolParameter(
                name="content_type",
                type=ParameterType.STRING,
                description="Content type",
                required=True,
                enum=["product_launch", "promotion", "lifestyle", "behind_scenes"],
            ),
            ToolParameter(
                name="product_id",
                type=ParameterType.INTEGER,
                description="Optional product ID",
            ),
            ToolParameter(
                name="hashtags",
                type=ParameterType.BOOLEAN,
                description="Include hashtags",
                default=True,
            ),
        ],
    ),
    ToolDefinition(
        name="generate_email_content",
        description="Generate email marketing content",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(
                name="email_type",
                type=ParameterType.STRING,
                description="Email type",
                required=True,
                enum=[
                    "welcome",
                    "abandoned_cart",
                    "order_confirmation",
                    "promotion",
                    "newsletter",
                ],
            ),
            ToolParameter(
                name="customer_name",
                type=ParameterType.STRING,
                description="Customer name",
            ),
            ToolParameter(
                name="products",
                type=ParameterType.ARRAY,
                description="Product IDs",
                items={"type": "integer"},
            ),
            ToolParameter(
                name="discount_code",
                type=ParameterType.STRING,
                description="Discount code if applicable",
            ),
        ],
    ),
    ToolDefinition(
        name="summarize_content",
        description="Summarize text content",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(
                name="text",
                type=ParameterType.STRING,
                description="Text to summarize",
                required=True,
                min_length=50,
            ),
            ToolParameter(
                name="max_length",
                type=ParameterType.INTEGER,
                description="Maximum summary length",
                default=200,
                min_value=50,
                max_value=1000,
            ),
            ToolParameter(
                name="style",
                type=ParameterType.STRING,
                description="Summary style",
                default="concise",
                enum=["concise", "detailed", "bullet_points"],
            ),
        ],
    ),
    ToolDefinition(
        name="translate_content",
        description="Translate content to another language",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(
                name="text",
                type=ParameterType.STRING,
                description="Text to translate",
                required=True,
            ),
            ToolParameter(
                name="target_language",
                type=ParameterType.STRING,
                description="Target language code",
                required=True,
            ),
            ToolParameter(
                name="preserve_formatting",
                type=ParameterType.BOOLEAN,
                description="Preserve formatting",
                default=True,
            ),
        ],
    ),
    ToolDefinition(
        name="edit_text",
        description="Edit and improve text content",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(
                name="text",
                type=ParameterType.STRING,
                description="Text to edit",
                required=True,
            ),
            ToolParameter(
                name="instructions",
                type=ParameterType.STRING,
                description="Editing instructions",
                required=True,
            ),
            ToolParameter(
                name="preserve_tone",
                type=ParameterType.BOOLEAN,
                description="Preserve original tone",
                default=True,
            ),
        ],
    ),
    ToolDefinition(
        name="generate_seo_metadata",
        description="Generate SEO title and meta description",
        category=ToolCategory.CONTENT,
        parameters=[
            ToolParameter(
                name="page_content",
                type=ParameterType.STRING,
                description="Page content or summary",
                required=True,
            ),
            ToolParameter(
                name="keywords",
                type=ParameterType.ARRAY,
                description="Target keywords",
                items={"type": "string"},
            ),
            ToolParameter(
                name="brand",
                type=ParameterType.STRING,
                description="Brand name",
                default="SkyyRose",
            ),
        ],
    ),
    # -------------------------------------------------------------------------
    # Commerce Tools (8)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="create_product",
        description="Create WooCommerce product",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(
                name="name",
                type=ParameterType.STRING,
                description="Product name",
                required=True,
            ),
            ToolParameter(
                name="price",
                type=ParameterType.NUMBER,
                description="Product price",
                required=True,
                min_value=0,
            ),
            ToolParameter(
                name="description",
                type=ParameterType.STRING,
                description="Product description",
                required=True,
            ),
            ToolParameter(
                name="collection",
                type=ParameterType.STRING,
                description="Collection",
                enum=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"],
            ),
            ToolParameter(
                name="sizes",
                type=ParameterType.ARRAY,
                description="Available sizes",
                items={"type": "string"},
            ),
            ToolParameter(
                name="images",
                type=ParameterType.ARRAY,
                description="Image URLs",
                items={"type": "string"},
            ),
        ],
        requires_auth=True,
        # Advanced Tool Use
        defer_loading=True,
        allowed_callers=["code_execution_20250825"],  # Enable PTC for batch product creation
        input_examples=[
            {
                "name": "Heart aRose Bomber Jacket",
                "price": 299.99,
                "description": "Premium bomber with rose gold accents",
                "collection": "BLACK_ROSE",
                "sizes": ["S", "M", "L", "XL"],
            },
            {
                "name": "Love Hurts Hoodie",
                "price": 149.99,
                "description": "Oversized hoodie with signature thorns",
                "collection": "LOVE_HURTS",
            },
        ],
    ),
    ToolDefinition(
        name="update_product",
        description="Update existing product",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(
                name="product_id",
                type=ParameterType.INTEGER,
                description="Product ID",
                required=True,
            ),
            ToolParameter(
                name="updates",
                type=ParameterType.OBJECT,
                description="Fields to update",
                required=True,
            ),
        ],
        requires_auth=True,
        # Advanced Tool Use
        defer_loading=True,
        allowed_callers=["code_execution_20250825"],  # Enable PTC for batch updates
        input_examples=[
            {"product_id": 123, "updates": {"price": 199.99, "sale_price": 149.99}},
            {"product_id": 456, "updates": {"stock_quantity": 50, "status": "publish"}},
        ],
    ),
    ToolDefinition(
        name="get_product",
        description="Get product details",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="product_id", type=ParameterType.INTEGER, description="Product ID"),
            ToolParameter(name="sku", type=ParameterType.STRING, description="Product SKU"),
        ],
    ),
    ToolDefinition(
        name="search_products",
        description="Search products",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(name="query", type=ParameterType.STRING, description="Search query"),
            ToolParameter(
                name="category",
                type=ParameterType.STRING,
                description="Category filter",
            ),
            ToolParameter(name="min_price", type=ParameterType.NUMBER, description="Minimum price"),
            ToolParameter(name="max_price", type=ParameterType.NUMBER, description="Maximum price"),
            ToolParameter(
                name="in_stock",
                type=ParameterType.BOOLEAN,
                description="In stock only",
                default=True,
            ),
            ToolParameter(
                name="limit",
                type=ParameterType.INTEGER,
                description="Result limit",
                default=20,
                max_value=100,
            ),
        ],
    ),
    ToolDefinition(
        name="update_inventory",
        description="Update product inventory",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(
                name="product_id",
                type=ParameterType.INTEGER,
                description="Product ID",
                required=True,
            ),
            ToolParameter(
                name="quantity",
                type=ParameterType.INTEGER,
                description="New quantity",
                required=True,
            ),
            ToolParameter(
                name="variation_id",
                type=ParameterType.INTEGER,
                description="Variation ID for variable products",
            ),
        ],
        requires_auth=True,
        # Advanced Tool Use
        defer_loading=True,
        allowed_callers=["code_execution_20250825"],  # Enable PTC for batch inventory sync
        input_examples=[
            {"product_id": 123, "quantity": 100},
            {"product_id": 456, "quantity": 25, "variation_id": 789},
        ],
    ),
    ToolDefinition(
        name="create_discount",
        description="Create discount code",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(
                name="code",
                type=ParameterType.STRING,
                description="Discount code",
                required=True,
            ),
            ToolParameter(
                name="type",
                type=ParameterType.STRING,
                description="Discount type",
                required=True,
                enum=["percent", "fixed_cart", "fixed_product"],
            ),
            ToolParameter(
                name="amount",
                type=ParameterType.NUMBER,
                description="Discount amount",
                required=True,
            ),
            ToolParameter(
                name="expiry",
                type=ParameterType.STRING,
                description="Expiry date (ISO format)",
            ),
            ToolParameter(
                name="usage_limit",
                type=ParameterType.INTEGER,
                description="Usage limit",
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="get_orders",
        description="Get orders list",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(
                name="status",
                type=ParameterType.STRING,
                description="Order status",
                enum=["pending", "processing", "completed", "cancelled", "refunded"],
            ),
            ToolParameter(
                name="customer_id",
                type=ParameterType.INTEGER,
                description="Customer ID",
            ),
            ToolParameter(
                name="date_from",
                type=ParameterType.STRING,
                description="Start date (ISO format)",
            ),
            ToolParameter(
                name="date_to",
                type=ParameterType.STRING,
                description="End date (ISO format)",
            ),
            ToolParameter(
                name="limit",
                type=ParameterType.INTEGER,
                description="Result limit",
                default=20,
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="process_refund",
        description="Process order refund",
        category=ToolCategory.COMMERCE,
        parameters=[
            ToolParameter(
                name="order_id",
                type=ParameterType.INTEGER,
                description="Order ID",
                required=True,
            ),
            ToolParameter(name="amount", type=ParameterType.NUMBER, description="Refund amount"),
            ToolParameter(
                name="reason",
                type=ParameterType.STRING,
                description="Refund reason",
                required=True,
            ),
            ToolParameter(
                name="restock",
                type=ParameterType.BOOLEAN,
                description="Restock items",
                default=True,
            ),
        ],
        requires_auth=True,
    ),
    # -------------------------------------------------------------------------
    # Media Tools (6)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="upload_image",
        description="Upload image to media library",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(
                name="file_path",
                type=ParameterType.STRING,
                description="Local file path or URL",
                required=True,
            ),
            ToolParameter(name="title", type=ParameterType.STRING, description="Image title"),
            ToolParameter(name="alt_text", type=ParameterType.STRING, description="Alt text"),
            ToolParameter(
                name="product_id",
                type=ParameterType.INTEGER,
                description="Attach to product",
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="generate_3d_model",
        description="Generate 3D model from description",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(
                name="product_name",
                type=ParameterType.STRING,
                description="Product name",
                required=True,
            ),
            ToolParameter(
                name="garment_type",
                type=ParameterType.STRING,
                description="Garment type",
                required=True,
                enum=["hoodie", "bomber", "tee", "track_pants", "sweatshirt", "jacket"],
            ),
            ToolParameter(
                name="collection",
                type=ParameterType.STRING,
                description="Collection",
                enum=["BLACK_ROSE", "LOVE_HURTS", "SIGNATURE"],
            ),
            ToolParameter(
                name="details",
                type=ParameterType.STRING,
                description="Additional details",
            ),
            ToolParameter(
                name="output_format",
                type=ParameterType.STRING,
                description="Output format",
                default="glb",
                enum=["glb", "gltf", "fbx", "obj"],
            ),
        ],
        requires_auth=True,
        timeout=300.0,
        # Advanced Tool Use
        defer_loading=True,
        allowed_callers=["code_execution_20250825"],  # Enable PTC for batch 3D generation
        input_examples=[
            {
                "product_name": "Heart aRose Bomber",
                "garment_type": "bomber",
                "collection": "BLACK_ROSE",
                "details": "Rose gold zippers, embroidered thorns on back",
                "output_format": "glb",
            },
            {
                "product_name": "Love Hurts Oversized Hoodie",
                "garment_type": "hoodie",
                "collection": "LOVE_HURTS",
                "details": "Distressed look, oversized fit",
            },
        ],
    ),
    ToolDefinition(
        name="virtual_tryon",
        description="Generate virtual try-on image",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(
                name="model_image",
                type=ParameterType.STRING,
                description="Model/person image path",
                required=True,
            ),
            ToolParameter(
                name="garment_image",
                type=ParameterType.STRING,
                description="Garment image path",
                required=True,
            ),
            ToolParameter(
                name="category",
                type=ParameterType.STRING,
                description="Garment category",
                default="tops",
                enum=["tops", "bottoms", "outerwear", "full_body"],
            ),
        ],
        requires_auth=True,
        timeout=120.0,
        # Advanced Tool Use
        defer_loading=True,
        input_examples=[
            {
                "model_image": "/images/models/model_01.jpg",
                "garment_image": "/images/products/bomber_black_rose.png",
                "category": "outerwear",
            },
        ],
    ),
    ToolDefinition(
        name="remove_background",
        description="Remove image background",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(
                name="image_path",
                type=ParameterType.STRING,
                description="Image path",
                required=True,
            ),
            ToolParameter(
                name="output_format",
                type=ParameterType.STRING,
                description="Output format",
                default="png",
            ),
        ],
    ),
    ToolDefinition(
        name="resize_image",
        description="Resize image",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(
                name="image_path",
                type=ParameterType.STRING,
                description="Image path",
                required=True,
            ),
            ToolParameter(name="width", type=ParameterType.INTEGER, description="Target width"),
            ToolParameter(name="height", type=ParameterType.INTEGER, description="Target height"),
            ToolParameter(
                name="maintain_aspect",
                type=ParameterType.BOOLEAN,
                description="Maintain aspect ratio",
                default=True,
            ),
        ],
    ),
    ToolDefinition(
        name="optimize_image",
        description="Optimize image for web",
        category=ToolCategory.MEDIA,
        parameters=[
            ToolParameter(
                name="image_path",
                type=ParameterType.STRING,
                description="Image path",
                required=True,
            ),
            ToolParameter(
                name="quality",
                type=ParameterType.INTEGER,
                description="Quality (1-100)",
                default=85,
                min_value=1,
                max_value=100,
            ),
            ToolParameter(
                name="format",
                type=ParameterType.STRING,
                description="Output format",
                enum=["webp", "jpeg", "png"],
            ),
        ],
    ),
    # -------------------------------------------------------------------------
    # Communication Tools (5)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="send_email",
        description="Send email",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(
                name="to",
                type=ParameterType.STRING,
                description="Recipient email",
                required=True,
            ),
            ToolParameter(
                name="subject",
                type=ParameterType.STRING,
                description="Email subject",
                required=True,
            ),
            ToolParameter(
                name="body",
                type=ParameterType.STRING,
                description="Email body (HTML supported)",
                required=True,
            ),
            ToolParameter(
                name="template",
                type=ParameterType.STRING,
                description="Email template name",
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="send_sms",
        description="Send SMS message",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(
                name="to",
                type=ParameterType.STRING,
                description="Phone number",
                required=True,
            ),
            ToolParameter(
                name="message",
                type=ParameterType.STRING,
                description="SMS message",
                required=True,
                max_length=160,
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="create_notification",
        description="Create system notification",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(
                name="title",
                type=ParameterType.STRING,
                description="Notification title",
                required=True,
            ),
            ToolParameter(
                name="message",
                type=ParameterType.STRING,
                description="Notification message",
                required=True,
            ),
            ToolParameter(
                name="type",
                type=ParameterType.STRING,
                description="Notification type",
                default="info",
                enum=["info", "success", "warning", "error"],
            ),
            ToolParameter(name="user_id", type=ParameterType.INTEGER, description="Target user ID"),
        ],
    ),
    ToolDefinition(
        name="schedule_notification",
        description="Schedule future notification",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(
                name="title",
                type=ParameterType.STRING,
                description="Notification title",
                required=True,
            ),
            ToolParameter(
                name="message",
                type=ParameterType.STRING,
                description="Notification message",
                required=True,
            ),
            ToolParameter(
                name="send_at",
                type=ParameterType.STRING,
                description="Send time (ISO format)",
                required=True,
            ),
            ToolParameter(
                name="channel",
                type=ParameterType.STRING,
                description="Notification channel",
                enum=["email", "sms", "push", "webhook"],
            ),
        ],
    ),
    ToolDefinition(
        name="send_webhook",
        description="Send webhook notification",
        category=ToolCategory.COMMUNICATION,
        parameters=[
            ToolParameter(
                name="url",
                type=ParameterType.STRING,
                description="Webhook URL",
                required=True,
            ),
            ToolParameter(
                name="event_type",
                type=ParameterType.STRING,
                description="Event type",
                required=True,
            ),
            ToolParameter(
                name="payload",
                type=ParameterType.OBJECT,
                description="Event payload",
                required=True,
            ),
        ],
        requires_auth=True,
    ),
    # -------------------------------------------------------------------------
    # Analytics Tools (5)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="get_sales_analytics",
        description="Get sales analytics",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(
                name="period",
                type=ParameterType.STRING,
                description="Time period",
                default="30d",
                enum=["7d", "30d", "90d", "1y", "custom"],
            ),
            ToolParameter(
                name="start_date",
                type=ParameterType.STRING,
                description="Start date for custom period",
            ),
            ToolParameter(
                name="end_date",
                type=ParameterType.STRING,
                description="End date for custom period",
            ),
            ToolParameter(
                name="group_by",
                type=ParameterType.STRING,
                description="Group by",
                default="day",
                enum=["hour", "day", "week", "month"],
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="get_product_analytics",
        description="Get product performance analytics",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(name="product_id", type=ParameterType.INTEGER, description="Product ID"),
            ToolParameter(
                name="period",
                type=ParameterType.STRING,
                description="Time period",
                default="30d",
            ),
            ToolParameter(
                name="metrics",
                type=ParameterType.ARRAY,
                description="Metrics to include",
                items={"type": "string"},
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="get_customer_analytics",
        description="Get customer analytics",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(
                name="metric",
                type=ParameterType.STRING,
                description="Metric type",
                required=True,
                enum=["acquisition", "retention", "ltv", "segments"],
            ),
            ToolParameter(
                name="period",
                type=ParameterType.STRING,
                description="Time period",
                default="30d",
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="forecast_demand",
        description="Forecast product demand",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(
                name="product_ids",
                type=ParameterType.ARRAY,
                description="Product IDs",
                items={"type": "integer"},
            ),
            ToolParameter(
                name="horizon",
                type=ParameterType.INTEGER,
                description="Forecast horizon (days)",
                default=30,
                min_value=7,
                max_value=90,
            ),
        ],
        requires_auth=True,
        # Advanced Tool Use
        defer_loading=True,
        input_examples=[
            {"product_ids": [101, 102, 103], "horizon": 30},
            {"product_ids": [201], "horizon": 90},
        ],
    ),
    ToolDefinition(
        name="generate_report",
        description="Generate analytics report",
        category=ToolCategory.ANALYTICS,
        parameters=[
            ToolParameter(
                name="report_type",
                type=ParameterType.STRING,
                description="Report type",
                required=True,
                enum=["sales", "inventory", "customers", "marketing"],
            ),
            ToolParameter(
                name="period",
                type=ParameterType.STRING,
                description="Time period",
                required=True,
            ),
            ToolParameter(
                name="format",
                type=ParameterType.STRING,
                description="Output format",
                default="pdf",
                enum=["pdf", "excel", "json"],
            ),
        ],
        requires_auth=True,
    ),
    # -------------------------------------------------------------------------
    # Integration Tools (4)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="wordpress_api_call",
        description="Make WordPress REST API call",
        category=ToolCategory.INTEGRATION,
        parameters=[
            ToolParameter(
                name="endpoint",
                type=ParameterType.STRING,
                description="API endpoint",
                required=True,
            ),
            ToolParameter(
                name="method",
                type=ParameterType.STRING,
                description="HTTP method",
                default="GET",
                enum=["GET", "POST", "PUT", "DELETE"],
            ),
            ToolParameter(name="data", type=ParameterType.OBJECT, description="Request data"),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="deploy_elementor_template",
        description="Deploy Elementor template",
        category=ToolCategory.INTEGRATION,
        parameters=[
            ToolParameter(
                name="template_name",
                type=ParameterType.STRING,
                description="Template name",
                required=True,
            ),
            ToolParameter(name="page_id", type=ParameterType.INTEGER, description="Target page ID"),
            ToolParameter(
                name="create_page",
                type=ParameterType.BOOLEAN,
                description="Create new page if page_id not provided",
                default=True,
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="sync_inventory",
        description="Sync inventory with external system",
        category=ToolCategory.INTEGRATION,
        parameters=[
            ToolParameter(
                name="source",
                type=ParameterType.STRING,
                description="Data source",
                required=True,
                enum=["shopify", "square", "csv", "api"],
            ),
            ToolParameter(
                name="mode",
                type=ParameterType.STRING,
                description="Sync mode",
                default="update",
                enum=["update", "replace", "merge"],
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="export_data",
        description="Export data to external format",
        category=ToolCategory.INTEGRATION,
        parameters=[
            ToolParameter(
                name="data_type",
                type=ParameterType.STRING,
                description="Data type",
                required=True,
                enum=["products", "orders", "customers", "analytics"],
            ),
            ToolParameter(
                name="format",
                type=ParameterType.STRING,
                description="Export format",
                default="csv",
                enum=["csv", "json", "xml"],
            ),
            ToolParameter(name="filters", type=ParameterType.OBJECT, description="Data filters"),
        ],
        requires_auth=True,
    ),
    # -------------------------------------------------------------------------
    # System Tools (2)
    # -------------------------------------------------------------------------
    ToolDefinition(
        name="clear_cache",
        description="Clear system cache",
        category=ToolCategory.SYSTEM,
        parameters=[
            ToolParameter(
                name="cache_type",
                type=ParameterType.STRING,
                description="Cache type",
                default="all",
                enum=["all", "page", "object", "cdn"],
            ),
        ],
        requires_auth=True,
    ),
    ToolDefinition(
        name="health_check",
        description="Check system health",
        category=ToolCategory.SYSTEM,
        parameters=[
            ToolParameter(
                name="components",
                type=ParameterType.ARRAY,
                description="Components to check",
                items={"type": "string"},
            ),
        ],
    ),
]

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
    "ToolDefinition",
    # Results
    "ToolExecutionResult",
    # Registry
    "ToolRegistry",
    "get_tool_registry",
    # Built-in Tools
    "BUILTIN_TOOLS",
]
