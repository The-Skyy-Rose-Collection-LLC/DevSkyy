# Programmatic Tool Calling (PTC) Implementation Plan

> Enterprise-Grade Implementation for DevSkyy Platform

**Status**: Planning
**Owner**: Principal Engineer
**Target**: Production-Ready Integration
**Beta**: `advanced-tool-use-2025-11-20`

---

## 🎯 Executive Summary

Implement Anthropic's Programmatic Tool Calling to enable:

- **85% token reduction** via batch tool operations in code
- **3-10x latency reduction** by eliminating model round-trips
- **Large-scale data processing** (files > 1M tokens) via programmatic filtering
- **Cost optimization** through intelligent tool result processing

---

## 🏗️ Architecture Overview

### Current State

```
User Request → Agent → LLM → Tool Call → Handler → Response → LLM → User
                      ↑_____________________↓
                      (N round trips for N tools)
```

### Target State with PTC

```
User Request → Agent → LLM + Code Execution → [
    code: results = await query_database(...)
    code: filtered = [r for r in results if r['revenue'] > 10000]
    code: summary = aggregate(filtered)
] → Response → User
                ↑___Single round trip___↓
```

---

## 📋 Implementation Phases

### Phase 1: Core Infrastructure ✅ (Partially Done)

**Files**:

- `runtime/tools.py` - ToolSpec already has `allowed_callers`!
- `llm/base.py` - Need `CallerInfo` and `ContainerLifecycle` models

**Tasks**:

1. ✅ `ToolSpec.allowed_callers` field exists
2. ✅ `ToolSpec.to_anthropic_tool()` supports PTC fields
3. ❌ Add `CallerInfo` model to track invocation context
4. ❌ Add `ContainerLifecycle` model for container management
5. ❌ Update `ToolCall` to include `caller` field
6. ❌ Update `CompletionResponse` to track container info

### Phase 2: Anthropic Client Enhancement

**File**: `llm/providers/anthropic.py`

**Changes**:

```python
class AnthropicClient(BaseLLMClient):
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.anthropic.com",
        enable_ptc: bool = True,  # NEW
        **kwargs: Any,
    ) -> None:
        self.enable_ptc = enable_ptc
        # ...

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        if self.enable_ptc:
            headers["anthropic-beta"] = "advanced-tool-use-2025-11-20"  # NEW
        return headers

    async def complete(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,  # Increased default
        tools: list[dict[str, Any]] | None = None,
        container_id: str | None = None,  # NEW - for reuse
        **kwargs: Any,
    ) -> CompletionResponse:
        # ...
        data: dict[str, Any] = {
            "model": model,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if container_id:
            data["container"] = container_id  # NEW - reuse container

        if tools:
            # Convert ToolSpec format to Anthropic format
            data["tools"] = tools  # Already in correct format from ToolSpec

        # Parse response for:
        # - container: {id, expires_at}
        # - tool_use blocks with caller field
        # - code_execution_tool_result blocks
```

### Phase 3: Code Execution Tool

**File**: `runtime/code_execution_tool.py` (NEW)

```python
"""
Code Execution Tool for Programmatic Tool Calling.

Sandboxed Python environment for executing tool orchestration code.
"""

from pydantic import BaseModel, Field
from runtime.tools import ToolSpec, ToolCategory, ToolSeverity

class CodeExecutionInput(BaseModel):
    code: str = Field(..., description="Python code to execute")

CODE_EXECUTION_TOOL = ToolSpec(
    name="code_execution",
    description="Execute Python code in a sandboxed container. Available functions: all tools with allowed_callers=['code_execution_20250825']",
    category=ToolCategory.SYSTEM,
    severity=ToolSeverity.HIGH,
    parameters=[
        ToolParameter(
            name="code",
            type=ParameterType.STRING,
            description="Python code to execute. Tools are available as async functions.",
            required=True,
        )
    ],
    # This tool is managed by Anthropic, not called directly
    allowed_callers=["direct"],  # Claude decides when to use code execution
    timeout_seconds=60.0,
)

async def handle_code_execution(input: CodeExecutionInput, context: ToolCallContext) -> str:
    """
    This is a placeholder handler. The actual code execution happens
    in Anthropic's managed container. When we get a tool_use block
    with caller.type == "code_execution_20250825", we know it was
    invoked from code and should return the result to the container.
    """
    # Anthropic handles the actual execution
    # We only need to handle tool_result responses
    raise NotImplementedError("Code execution is managed by Anthropic")
```

### Phase 4: Tool Configuration Strategy

**Decision Matrix** - Which tools get `allowed_callers`?

| Tool Category | Direct | Code Execution | Rationale |
|---------------|--------|----------------|-----------|
| Database queries | ❌ | ✅ | Batch queries, filter results |
| Product search | ❌ | ✅ | Loop through collections |
| 3D generation | ✅ | ❌ | Slow, one-off operations |
| WordPress updates | ✅ | ❌ | User needs to see each change |
| System monitoring | ❌ | ✅ | Aggregate metrics |
| ML predictions | ❌ | ✅ | Batch predictions |

**Configuration Pattern**:

```python
# Example: Product search tool (GOOD for PTC)
PRODUCT_SEARCH_TOOL = ToolSpec(
    name="search_products",
    description="""
    Search WooCommerce products. Returns JSON array of products.

    Output format:
    [
        {"id": 123, "name": "Product Name", "price": 99.99, "stock": 10},
        ...
    ]
    """,  # Detailed output description for code handling
    category=ToolCategory.COMMERCE,
    severity=ToolSeverity.READ_ONLY,
    allowed_callers=["code_execution_20250825"],  # ONLY callable from code
    # ...
)

# Example: 3D generation (NOT good for PTC)
GENERATE_3D_TOOL = ToolSpec(
    name="generate_3d_from_description",
    description="Generate 3D model from text description",
    category=ToolCategory.MEDIA,
    severity=ToolSeverity.MEDIUM,
    allowed_callers=["direct"],  # ONLY direct invocation
    timeout_seconds=120.0,  # Too slow for code execution
    # ...
)
```

### Phase 5: Container Lifecycle Management

**File**: `runtime/container_manager.py` (NEW)

```python
"""
Container lifecycle management for code execution.

Handles:
- Container ID tracking
- Expiration monitoring
- State persistence across requests
"""

from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Dict, Optional

@dataclass
class Container:
    id: str
    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= self.expires_at

    @property
    def time_remaining_seconds(self) -> float:
        delta = self.expires_at - datetime.now(UTC)
        return max(0, delta.total_seconds())

class ContainerManager:
    """Manage code execution containers."""

    def __init__(self):
        self._containers: Dict[str, Container] = {}

    def register(self, container_id: str, expires_at: datetime) -> Container:
        """Register a new container from API response."""
        container = Container(id=container_id, expires_at=expires_at)
        self._containers[container_id] = container
        return container

    def get(self, container_id: str) -> Optional[Container]:
        """Get container by ID."""
        container = self._containers.get(container_id)
        if container and container.is_expired:
            del self._containers[container_id]
            return None
        return container

    def cleanup_expired(self) -> int:
        """Remove expired containers. Returns count removed."""
        expired = [cid for cid, c in self._containers.items() if c.is_expired]
        for cid in expired:
            del self._containers[cid]
        return len(expired)
```

### Phase 6: Response Parsing Enhancement

**File**: `llm/base.py` - Update models

```python
from enum import Enum
from typing import Literal

class CallerType(str, Enum):
    """Type of tool caller."""
    DIRECT = "direct"
    CODE_EXECUTION = "code_execution_20250825"

@dataclass
class CallerInfo:
    """Information about who/what invoked a tool."""
    type: CallerType
    tool_id: str | None = None  # For code_execution, references the code_execution tool_use block

@dataclass
class ToolCall:
    """Tool call with caller context."""
    id: str
    type: str
    function: dict[str, Any]
    caller: CallerInfo | None = None  # NEW

    @property
    def name(self) -> str:
        return self.function.get("name", "")

    @property
    def arguments(self) -> dict[str, Any]:
        return self.function.get("arguments", {})

    @property
    def is_programmatic(self) -> bool:
        """Check if this was a programmatic call from code execution."""
        return self.caller is not None and self.caller.type == CallerType.CODE_EXECUTION

@dataclass
class ContainerInfo:
    """Code execution container information."""
    id: str
    expires_at: datetime

    @property
    def time_remaining_seconds(self) -> float:
        delta = self.expires_at - datetime.now(UTC)
        return max(0, delta.total_seconds())

@dataclass
class CompletionResponse:
    """LLM completion response with PTC support."""
    content: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    finish_reason: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    latency_ms: float = 0
    raw: dict[str, Any] = field(default_factory=dict)
    container: ContainerInfo | None = None  # NEW - container info from response
```

**Update AnthropicClient.complete()** to parse:

```python
# In AnthropicClient.complete()
result = response.json()

# Parse container info
container_info = None
if "container" in result:
    container_info = ContainerInfo(
        id=result["container"]["id"],
        expires_at=datetime.fromisoformat(result["container"]["expires_at"].replace("Z", "+00:00"))
    )

# Parse tool calls with caller info
for block in result.get("content", []):
    # ...
    elif block["type"] == "tool_use":
        caller_info = None
        if "caller" in block:
            caller_data = block["caller"]
            caller_info = CallerInfo(
                type=CallerType(caller_data["type"]),
                tool_id=caller_data.get("tool_id")
            )

        tool_calls.append(
            ToolCall(
                id=block["id"],
                type="function",
                function={
                    "name": block["name"],
                    "arguments": block["input"],
                },
                caller=caller_info  # NEW
            )
        )

return CompletionResponse(
    # ...
    container=container_info  # NEW
)
```

### Phase 7: Agent Integration

**File**: `agents/base_super_agent.py`

Add method to `EnhancedSuperAgent`:

```python
async def execute_with_ptc(
    self,
    prompt: str,
    tools: list[ToolSpec] | None = None,
    container_id: str | None = None,
) -> tuple[str, ContainerInfo | None]:
    """
    Execute task with programmatic tool calling support.

    Args:
        prompt: User task
        tools: Available tools (auto-filtered by allowed_callers)
        container_id: Existing container to reuse

    Returns:
        (response_text, container_info)
    """
    # Get tools that support PTC
    if tools is None:
        registry = get_tool_registry()
        tools = registry.list_enabled()

    # Separate tools by allowed_callers
    code_exec_tools = [
        t for t in tools
        if "code_execution_20250825" in t.allowed_callers
    ]
    direct_tools = [
        t for t in tools
        if "direct" in t.allowed_callers
    ]

    # Include code_execution tool if we have PTC tools
    final_tools = []
    if code_exec_tools:
        final_tools.append(CODE_EXECUTION_TOOL.to_anthropic_tool())
        final_tools.extend([t.to_anthropic_tool() for t in code_exec_tools])
    final_tools.extend([t.to_anthropic_tool() for t in direct_tools])

    # Execute with container reuse
    client = AnthropicClient(enable_ptc=True)

    messages = [Message.user(prompt)]
    response = await client.complete(
        messages=messages,
        tools=final_tools,
        container_id=container_id,
        max_tokens=4096,
    )

    # Handle tool calls (both direct and programmatic)
    while response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call.is_programmatic:
                logger.info(f"Programmatic call to {tool_call.name} from container")
            else:
                logger.info(f"Direct call to {tool_call.name}")

            # Execute tool
            result = await self._execute_tool(tool_call)

            # Add tool result to conversation
            messages.append(Message.tool(
                tool_call_id=tool_call.id,
                content=result
            ))

        # Continue conversation with container reuse
        response = await client.complete(
            messages=messages,
            tools=final_tools,
            container_id=response.container.id if response.container else None,
            max_tokens=4096,
        )

    return response.content, response.container
```

---

## 🧪 Testing Strategy

### Unit Tests

**File**: `tests/test_ptc.py`

```python
import pytest
from datetime import datetime, UTC, timedelta
from llm.base import CallerInfo, CallerType, ToolCall, ContainerInfo
from runtime.tools import ToolSpec, ToolCategory, ToolSeverity

def test_caller_info_direct():
    caller = CallerInfo(type=CallerType.DIRECT)
    assert caller.type == CallerType.DIRECT
    assert caller.tool_id is None

def test_caller_info_code_execution():
    caller = CallerInfo(
        type=CallerType.CODE_EXECUTION,
        tool_id="srvtoolu_abc123"
    )
    assert caller.type == CallerType.CODE_EXECUTION
    assert caller.tool_id == "srvtoolu_abc123"

def test_tool_call_is_programmatic():
    # Direct call
    direct_call = ToolCall(
        id="toolu_001",
        type="function",
        function={"name": "search", "arguments": {}},
        caller=CallerInfo(type=CallerType.DIRECT)
    )
    assert not direct_call.is_programmatic

    # Programmatic call
    prog_call = ToolCall(
        id="toolu_002",
        type="function",
        function={"name": "search", "arguments": {}},
        caller=CallerInfo(
            type=CallerType.CODE_EXECUTION,
            tool_id="srvtoolu_abc"
        )
    )
    assert prog_call.is_programmatic

def test_container_expiration():
    future = datetime.now(UTC) + timedelta(minutes=4)
    container = ContainerInfo(id="cont_123", expires_at=future)
    assert container.time_remaining_seconds > 200
    assert container.time_remaining_seconds < 250

@pytest.mark.asyncio
async def test_tool_spec_allowed_callers():
    spec = ToolSpec(
        name="query_db",
        description="Query database",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.READ_ONLY,
        allowed_callers=["code_execution_20250825"],
    )

    tool_def = spec.to_anthropic_tool()
    assert tool_def["allowed_callers"] == ["code_execution_20250825"]
```

### Integration Tests

**File**: `tests/test_ptc_integration.py`

```python
@pytest.mark.asyncio
async def test_batch_product_search_with_ptc():
    """Test programmatic calling for batch operations."""
    client = AnthropicClient(enable_ptc=True)

    tools = [
        {
            "type": "code_execution_20250825",
            "name": "code_execution"
        },
        {
            "name": "search_products",
            "description": "Search products. Returns JSON array.",
            "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}},
            "allowed_callers": ["code_execution_20250825"]
        }
    ]

    response = await client.complete(
        messages=[Message.user(
            "Search for products in categories: jewelry, watches, accessories. "
            "Return total count per category."
        )],
        tools=tools,
        max_tokens=4096,
    )

    # Should trigger code execution with programmatic tool calls
    assert response.container is not None
    programmatic_calls = [tc for tc in response.tool_calls if tc.is_programmatic]
    assert len(programmatic_calls) > 0
```

---

## 📊 Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Token Usage (batch ops) | 10,000 | 1,500 | 85% reduction |
| Latency (5 tool calls) | 15s | 2s | 87% reduction |
| Cost (large dataset) | $0.50 | $0.10 | 80% reduction |
| Test Coverage | - | 95% | pytest --cov |

---

## 🚨 Risk Mitigation

### Container Expiration

- **Risk**: Tool takes >4.5min, container expires
- **Mitigation**:
  - Monitor `expires_at` field
  - Implement tool timeouts < 4min
  - Break long operations into chunks

### Tool Result Validation

- **Risk**: Code injection via tool results
- **Mitigation**:
  - Validate all tool results before returning
  - Sanitize user input
  - Use Pydantic models for structured outputs

### Backward Compatibility

- **Risk**: Breaking existing tool calls
- **Mitigation**:
  - `allowed_callers` defaults to `["direct"]` (current behavior)
  - `enable_ptc` flag on AnthropicClient (default True)
  - Gradual rollout per tool category

---

## 📝 Rollout Plan

### Week 1: Infrastructure

- [ ] Implement CallerInfo, ContainerInfo models
- [ ] Update ToolCall with caller field
- [ ] Add beta headers to AnthropicClient
- [ ] Write unit tests (95% coverage)

### Week 2: Tool Configuration

- [ ] Audit all 13 MCP tools
- [ ] Configure `allowed_callers` based on decision matrix
- [ ] Add detailed output descriptions
- [ ] Integration tests for each tool

### Week 3: Agent Integration

- [ ] Add `execute_with_ptc()` to EnhancedSuperAgent
- [ ] Update CommerceAgent with PTC examples
- [ ] Container lifecycle management
- [ ] End-to-end testing

### Week 4: Production Hardening

- [ ] Load testing (100 concurrent requests)
- [ ] Container expiration handling
- [ ] Monitoring & alerting
- [ ] Documentation & runbooks

---

## 📚 Documentation

### Files to Create

1. `docs/guides/PROGRAMMATIC_TOOL_CALLING.md` - User guide
2. `docs/architecture/PTC_ARCHITECTURE.md` - Technical deep-dive
3. `docs/runbooks/PTC_TROUBLESHOOTING.md` - Ops guide
4. `examples/ptc_batch_operations.py` - Code examples

### Files to Update

1. `README.md` - Add PTC feature highlight
2. `CLAUDE.md` - Add PTC patterns and best practices
3. `docs/MCP_ARCHITECTURE.md` - Document PTC integration

---

## ✅ Definition of Done

- [ ] All 9 TODO items completed
- [ ] Test coverage ≥ 95%
- [ ] Zero security vulnerabilities (bandit, pip-audit)
- [ ] All tools categorized with allowed_callers
- [ ] Documentation complete with examples
- [ ] Performance benchmarks meet targets
- [ ] Code review approved
- [ ] CI/CD pipeline green
- [ ] Deployed to staging and tested
- [ ] Runbook validated with on-call team

---

**Next Steps**: Get approval on architecture, then begin Phase 1 implementation.
