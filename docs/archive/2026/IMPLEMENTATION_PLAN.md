# DevSkyy Production Hardening - Implementation Plan

**Version:** 1.0.0
**Date:** December 18, 2025
**Status:** Stage 1 Complete - Ready for Execution

---

## Executive Summary

Based on RPVAE protocol stages 0-3 (Research, Verify, Authenticate), this document outlines the concrete implementation plan for production hardening.

---

## Verified Failures (Stage 2 Results)

### Critical Blockers

1. **Python 3.14 annotation resolution** - `security/jwt_oauth2_auth.py:935`
   - `NameError: name 'Request' is not defined`
   - Blocks all security tests

### Type Errors (85+)

- Legacy code: 40+ (acceptable - legacy folder)
- Production code: 20+ (must fix)
- Scripts: 25+ (should fix)

---

## Implementation Order (Mandatory)

### Phase 1: Unblock Tests (IMMEDIATE)

#### 1.1 Fix Python 3.14 Import Issue

**File:** `security/jwt_oauth2_auth.py`
**Line:** 25-45 (imports section)
**Change:** Add `Request` to module-level imports

```python
# Add to existing FastAPI imports at module level
from fastapi import Request
```

**Verification:** `pytest tests/ -v --collect-only` (should collect 129 tests)

---

### Phase 2: Security & Crypto Contract Fixes

#### 2.1 Fix AES-256-GCM Type Mismatches

**File:** `security/aes256_gcm_encryption.py`
**Lines:** 535, 559, 655
**Issue:** `dict[str, Any]` assigned to `str` variable
**Fix:** Correct variable types or add proper type narrowing

#### 2.2 Fix WordPress Client Null Safety

**File:** `wordpress/client.py`
**Line:** 103
**Issue:** `ClientSession | None` accessed without null check
**Fix:** Add explicit null guard

```python
if self.session is None:
    raise RuntimeError("Session not initialized. Call connect() first.")
```

#### 2.3 Fix CSP Middleware Return Types

**File:** `security/csp_middleware.py`
**Lines:** 126, 141
**Issue:** `Returning Any` instead of `Response`
**Fix:** Add explicit return type casting or type guards

---

### Phase 3: Packaging/Import Hygiene

#### 3.1 Fix Unused Imports

**File:** `agents/__init__.py`
**Lines:** 51, 60
**Issue:** Unused imports `CreativeVisualProvider`, `GenerationType`
**Fix:** Remove or add to `__all__`

#### 3.2 Sort Imports

**File:** `agents/__init__.py`
**Fix:** Run `isort agents/__init__.py`

---

### Phase 4: Type Annotation Fixes

#### 4.1 Production Code (Priority)

| File | Line | Fix |
|------|------|-----|
| `security/aes256_gcm_encryption.py` | 593 | Add `-> None` return type |
| `security/vulnerability_scanner.py` | 129, 176, 211 | Add generic type params `dict[str, Any]` |
| `security/csp_middleware.py` | 110, 164, 166, 197 | Add generic type params |

#### 4.2 Legacy Code (Defer)

- `legacy/sqlite_auth_system.py` - 20+ implicit Optional issues
- Plan: Add `# type: ignore` comments or fix as time permits

---

### Phase 5: Tool Runtime Layer (Based on Authenticated Research)

#### 5.1 Create Tool Runtime Contracts

**New File:** `runtime/contracts.py`

Following MCP 2025-11-25 specification + LangChain ToolRuntime pattern:

```python
from dataclasses import dataclass, field
from typing import TypedDict, Any
from enum import Enum
from pydantic import BaseModel

class ToolPermission(Enum):
    FILESYSTEM_READ = "filesystem:read"
    FILESYSTEM_WRITE = "filesystem:write"
    NETWORK_OUTBOUND = "network:outbound"
    DATABASE_READ = "database:read"
    DATABASE_WRITE = "database:write"
    WORDPRESS_API = "wordpress:api"
    LLM_INFERENCE = "llm:inference"
    VISUAL_GENERATION = "visual:generation"

@dataclass
class ToolSpec:
    """MCP-compatible tool specification."""
    name: str
    version: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema
    output_schema: dict[str, Any]  # JSON Schema
    permissions: list[ToolPermission] = field(default_factory=list)
    timeout_ms: int = 30000
    idempotent: bool = False
    retry_policy: dict[str, Any] | None = None

@dataclass
class ToolCallContext:
    """Context for tool execution (LangChain ToolRuntime pattern)."""
    correlation_id: str
    actor_id: str
    permissions: set[ToolPermission]
    timeout_ms: int
    idempotency_key: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)

class ToolCallResult(TypedDict):
    """MCP-compatible tool result."""
    content: list[dict[str, Any]]  # ContentBlock[]
    is_error: bool
    structured_content: dict[str, Any] | None
    execution_time_ms: int
```

#### 5.2 Enhance Existing ToolRegistry

**File:** `runtime/tools.py`
**Changes:**

- Add permission enforcement (deny-by-default)
- Add timeout handling
- Add idempotency key tracking
- Add structured error taxonomy

#### 5.3 Create Error Taxonomy

**New File:** `runtime/errors.py`

```python
from enum import Enum

class ToolErrorCode(str, Enum):
    # Input errors (4xx)
    INVALID_INPUT = "E4001"
    MISSING_PARAMETER = "E4002"
    PERMISSION_DENIED = "E4003"
    TOOL_NOT_FOUND = "E4004"

    # Execution errors (5xx)
    TIMEOUT = "E5001"
    RETRIES_EXHAUSTED = "E5002"
    INTERNAL_ERROR = "E5003"
    DEPENDENCY_FAILURE = "E5004"

    # External errors (6xx)
    NETWORK_ERROR = "E6001"
    API_ERROR = "E6002"
    RATE_LIMITED = "E6003"

class ToolError(Exception):
    """Typed exception for tool failures."""
    def __init__(self, code: ToolErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"{code.value}: {message}")
```

---

### Phase 6: Agent Refactoring

#### 6.1 Update Base SuperAgent

**File:** `agents/base_super_agent.py`
**Changes:**

- Import and use `ToolCallContext` for all tool calls
- Add permission validation before tool execution
- Add structured logging with correlation IDs

#### 6.2 Update Individual Agents

**Files:**

- `agents/commerce_agent.py`
- `agents/creative_agent.py`
- `agents/marketing_agent.py`
- `agents/support_agent.py`
- `agents/operations_agent.py`
- `agents/analytics_agent.py`

**Pattern for each:**

```python
async def execute_tool(self, tool_name: str, args: dict, context: ToolCallContext) -> ToolCallResult:
    # Validate permissions
    self.runtime.validate_permissions(tool_name, context.permissions)

    # Execute with timeout
    result = await self.runtime.call_tool(tool_name, args, context)

    # Log with correlation ID
    logger.info(f"Tool executed", extra={
        "correlation_id": context.correlation_id,
        "tool": tool_name,
        "execution_time_ms": result["execution_time_ms"]
    })

    return result
```

---

### Phase 7: MCP Server Enhancement

#### 7.1 Update MCP Server

**File:** `mcp/openai_server.py`
**Changes:**

- Expose tools from `ToolRegistry`
- Implement deterministic tool discovery
- Add validation and observability

```python
from runtime.tools import ToolRegistry
from runtime.contracts import ToolSpec, ToolCallResult

class MCPServer:
    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry

    async def list_tools(self) -> list[ToolSpec]:
        """Deterministic tool discovery."""
        return sorted(self.registry.list_tools(), key=lambda t: t.name)

    async def call_tool(self, name: str, arguments: dict, context: dict) -> ToolCallResult:
        """Validated tool execution."""
        tool_context = ToolCallContext(**context)
        return await self.registry.execute(name, arguments, tool_context)
```

---

### Phase 8: Three.js Collection Experiences

#### 8.1 Create Experience Specification

**New File:** `src/types/Collection3DSpec.ts`

```typescript
export interface Collection3DExperienceSpec {
  spec_version: string;  // semver
  variant: 'SHOWROOM' | 'RUNWAY' | 'MATERIALS';
  collection_id: string;
  scene: SceneSpec;
  camera: CameraSpec;
  interactions: HotspotSpec[];
  ui_overlay: UIOverlaySpec;
  performance_budget: PerformanceBudget;
  analytics_events: string[];
}

export interface PerformanceBudget {
  max_triangles: number;
  max_texture_memory_mb: number;
  max_draw_calls: number;
  max_bundle_size_kb: number;
}
```

#### 8.2 Enhance Existing Experiences

**Files:**

- `src/collections/ShowroomExperience.ts`
- `src/collections/RunwayExperience.ts`
- `src/collections/BlackRoseExperience.ts` (adapt to Materials variant)

**Required Additions:**

- WebGL context loss handlers
- DRACO/KTX2 loader configuration
- prefers-reduced-motion support
- Keyboard navigation for hotspots
- 2D fallback mode with structured logging

#### 8.3 Add Playwright E2E Tests

**New File:** `tests/e2e/collections.spec.ts`

```typescript
test.describe('Collection 3D Experiences', () => {
  test('Showroom loads without console errors', async ({ page }) => {
    await page.goto('/collections/showroom');
    const errors = [];
    page.on('console', msg => { if (msg.type() === 'error') errors.push(msg); });
    await page.waitForSelector('[data-testid="3d-canvas"]');
    expect(errors).toHaveLength(0);
  });

  test('Hotspot is keyboard accessible', async ({ page }) => {
    await page.goto('/collections/showroom');
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.getAttribute('data-hotspot'));
    expect(focused).toBeTruthy();
  });

  test('Fallback mode triggers on WebGL failure', async ({ page }) => {
    // Force WebGL context loss
    await page.evaluate(() => {
      const canvas = document.querySelector('canvas');
      canvas?.getContext('webgl')?.getExtension('WEBGL_lose_context')?.loseContext();
    });
    await expect(page.locator('[data-testid="fallback-2d"]')).toBeVisible();
  });
});
```

---

### Phase 9: CI/CD Alignment

#### 9.1 Update GitHub Actions

**File:** `.github/workflows/ci.yml`
**Changes:**

- Add version pinning check
- Add Python 3.14 compatibility test
- Add Three.js bundle size check

#### 9.2 Add Version Pinning

**New Files:**

- `.nvmrc` (Node version)
- `.python-version` (Python version)

```bash
# .nvmrc
22.12.0

# .python-version
3.11.11
```

---

## Verification Commands

After each phase, run:

```bash
# Phase 1
pytest tests/ -v --collect-only

# Phase 2-4
pytest tests/ -v --tb=short
mypy --ignore-missing-imports .

# Phase 5-7
pytest tests/ -v
python -c "from runtime.contracts import ToolSpec, ToolCallContext; print('OK')"

# Phase 8
npm run test:collections
npm run build

# Phase 9
make ci
```

---

## Success Criteria

1. All 129 Python tests pass
2. All TypeScript tests pass
3. mypy reports 0 errors in production code (legacy excluded)
4. ruff reports 0 errors
5. Three.js bundle < 500KB
6. All 3 collection templates render without console errors
7. CI pipeline passes in < 10 minutes

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-18 | Claude | Initial plan based on RPVAE stages 0-3 |
