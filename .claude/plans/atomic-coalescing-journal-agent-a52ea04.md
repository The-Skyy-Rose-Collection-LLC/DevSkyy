# Enterprise Hooks & Skills System - Implementation Plan

## DevSkyy State-of-the-Art Machine Transformation

**Status**: Planning Phase
**Priority**: CRITICAL (addresses CRITICAL_WORKFLOW_DIRECTIVE)
**Created**: 2026-01-05
**Version**: 1.0.0

---

## Executive Summary

This plan transforms DevSkyy into an enterprise state-of-the-art machine by implementing:

1. **Workflow Skills** - Production-grade user-invocable operations
2. **Automation Hooks** - Auto-triggered quality gates and orchestration
3. **Hybrid MCP/RAG** - Enterprise integration layer
4. **Quality Enforcement** - Addresses CRITICAL_WORKFLOW_DIRECTIVE (ruff/linting)

**CRITICAL PATH**: Fix linting errors FIRST (ABSOLUTE RULE), then implement hooks/skills.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE INTERFACE                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────┐              ┌──────────────────────┐          │
│  │  User Commands  │              │   Automation Hooks   │          │
│  │  (Skills)       │              │   (Event-Driven)     │          │
│  ├─────────────────┤              ├──────────────────────┤          │
│  │ /deploy         │              │ PreToolUse ───────┐  │          │
│  │ /test-commit    │              │ PostToolUse ──────┼─►│          │
│  │ /code-review    │              │ Stop ─────────────┤  │          │
│  │ /fix-linting    │◄─────────┐   │ SessionStart ─────┤  │          │
│  │ /rag-ingest     │          │   │ UserPromptSubmit ─┘  │          │
│  │ /mcp-health     │          │   └──────────────────────┘          │
│  └─────────────────┘          │                                      │
│          │                     │                                      │
│          ▼                     ▼                                      │
│  ┌──────────────────────────────────────────────┐                   │
│  │         HOOK & SKILL ORCHESTRATOR             │                   │
│  │  (runtime/hook_executor.py)                   │                   │
│  ├──────────────────────────────────────────────┤                   │
│  │ • Hook Registration & Matching                │                   │
│  │ • Skill Invocation & Context Management       │                   │
│  │ • Audit Trail & Metrics                       │                   │
│  │ • Error Handling & Rollback                   │                   │
│  └───────────────────┬──────────────────────────┘                   │
│                      │                                                │
│                      ▼                                                │
│  ┌──────────────────────────────────────────────────────────┐       │
│  │              ENTERPRISE INTEGRATION LAYER                 │       │
│  ├──────────────────────────────────────────────────────────┤       │
│  │                                                            │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │       │
│  │  │ ToolRegistry │  │ RAG Pipeline │  │ MCP Servers  │   │       │
│  │  │ (99 tools)   │  │ (Semantic)   │  │ (4 servers)  │   │       │
│  │  ├──────────────┤  ├──────────────┤  ├──────────────┤   │       │
│  │  │ Categories   │  │ ChromaDB     │  │ devskyy_mcp  │   │       │
│  │  │ Severity     │  │ Embeddings   │  │ agent_bridge │   │       │
│  │  │ Validation   │  │ Rewriting    │  │ rag_server   │   │       │
│  │  │ PTC Support  │  │ Chunking     │  │ woocommerce  │   │       │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │       │
│  │                                                            │       │
│  └───────────────────┬────────────────────────────────┬─────┘       │
│                      │                                 │             │
│                      ▼                                 ▼             │
│  ┌──────────────────────────────────┐  ┌──────────────────────────┐│
│  │      SUPERAGENTS (6)             │  │   MONITORING & METRICS    ││
│  ├──────────────────────────────────┤  ├──────────────────────────┤│
│  │ Commerce, Creative, Marketing,   │  │ Prometheus Exporters      ││
│  │ Support, Operations, Analytics   │  │ Hook Execution Stats      ││
│  │                                  │  │ Tool Usage Analytics      ││
│  │ • 17 Prompt Techniques           │  │ RAG Quality Metrics       ││
│  │ • LLM Round Table                │  │ Error Rate Tracking       ││
│  │ • Self-Learning                  │  │ Audit Logs (GDPR)         ││
│  └──────────────────────────────────┘  └──────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

---

## Current State Analysis

### Existing Assets (What Works)

**Hooks Infrastructure** (`.claude/hooks/`):

- ✅ `hooks.json` - 6 hooks defined (PreToolUse, PostToolUse, Stop, SessionStart, UserPromptSubmit)
- ✅ `scripts/audit-log.sh` - GDPR-compliant audit logging (30-day retention)
- ✅ `scripts/load-context.sh` - Brand DNA & environment loading
- ✅ `scripts/validate-bash.sh` - Bash command security validation
- ✅ Prompt-based hooks for security validation, code quality, TDD enforcement

**Skills** (`.claude/skills/`):

- ✅ `/deploy` - Comprehensive 9-phase deployment pipeline
  - Pre-flight checks, security audit, code quality, testing, build, deploy, verify, smoke tests, reporting

**Tool Registry** (`runtime/tools.py`):

- ✅ Production-grade ToolSpec with Pydantic validation
- ✅ Multi-format export (OpenAI, Anthropic, MCP)
- ✅ Advanced Tool Use support (defer_loading, allowed_callers, input_examples)
- ✅ 10 categories, 5 severity levels
- ✅ Auto-PTC configuration for READ_ONLY tools
- ✅ Execution with timeout, retries, caching

**MCP Servers** (`mcp_servers/`):

- ✅ `devskyy_mcp.py` - 21 tools (main server)
- ✅ `agent_bridge_server.py` - 72 tools (comprehensive agent bridge)
- ✅ `rag_server.py` - 6 RAG tools (query, ingest, context, rewrite, list, stats)
- ✅ `woocommerce_mcp.py` - E-commerce operations

**RAG System** (`orchestration/vector_store.py`):

- ✅ ChromaDB vector store with Pinecone fallback
- ✅ Embeddings (sentence-transformers, OpenAI)
- ✅ Query rewriting (5 strategies: zero_shot, few_shot, sub_queries, step_back, hyde)
- ✅ Document ingestion pipeline

**SuperAgents** (`agents/`, `agent_sdk/super_agents/`):

- ✅ 6 agents: Commerce, Creative, Marketing, Support, Operations, Analytics
- ✅ 17 prompt engineering techniques with auto-selection
- ✅ LLM Round Table (6 providers)
- ✅ ML capabilities, self-learning

### Critical Gaps (What's Missing)

**CRITICAL (BLOCKING)**:

1. ❌ **Ruff/Linting Errors** - 3+ errors in agent_sdk/ and agents/
   - `SIM105` in task_queue.py (try-except-pass → contextlib.suppress)
   - `E402` in worker.py (module import not at top)
   - `F401` in creative_agent.py (unused import)
   - **MUST FIX FIRST** (CRITICAL_WORKFLOW_DIRECTIVE)

**HIGH PRIORITY**:
2. ❌ **Auto-Trigger Hooks** - PostToolUse hooks exist but need implementation:

- Auto-format after Write/Edit (isort && ruff --fix && black)
- Auto-test after code changes
- Auto-RAG-ingest after doc writes
- Auto-security-scan after dependency changes

1. ❌ **Missing Skills** - User-requested workflows:
   - `/test-and-commit` - TDD workflow
   - `/code-review` - Security + quality analysis
   - `/fix-linting` - Auto-fix ruff errors
   - `/rag-ingest` - Batch document ingestion
   - `/mcp-health` - Server diagnostics

2. ❌ **Agent-Tool Integration** - Agents don't use ToolRegistry directly:
   - SuperAgents use `execute_with_learning()` wrapper
   - Need to refactor to `tool_registry.execute()`
   - Missing unified tool catalog

3. ❌ **RAG Integration** - Not fully connected:
   - SuperAgents use queue-based ingestion, not RAG pipeline
   - Knowledge base uses keyword matching, not semantic search
   - Missing embedding drift detection
   - No retrieval metrics

4. ❌ **Monitoring & Metrics**:
   - No hook execution metrics
   - No tool usage analytics
   - No RAG quality metrics
   - Missing circuit breakers

**MEDIUM PRIORITY**:
7. ❌ **Missing Dependencies** - Required for RAG:

- `chromadb>=0.5.0` (not in pyproject.toml)
- `sentence-transformers>=3.0.0` (not in pyproject.toml)
- Need to add to dependencies

1. ❌ **Test Coverage**:
   - No tests for hooks
   - No tests for skills
   - No RAG integration tests
   - No agent-tool integration tests

2. ❌ **Documentation**:
   - No hook/skill development guide
   - No tool catalog documentation
   - No RAG usage guide

---

## Implementation Strategy

### Phase 0: CRITICAL - Fix Linting Errors (IMMEDIATE)

**Priority**: BLOCKING
**Duration**: 30 minutes
**Status**: MUST COMPLETE BEFORE ANY OTHER WORK

**Objective**: Address CRITICAL_WORKFLOW_DIRECTIVE by fixing all ruff/linting errors.

**Actions**:

1. **Fix agent_sdk/task_queue.py (SIM105)**:

   ```python
   # BEFORE (Line 157-160):
   try:
       await asyncio.sleep(0.1)
   except asyncio.CancelledError:
       pass

   # AFTER:
   import contextlib
   # ...
   with contextlib.suppress(asyncio.CancelledError):
       await asyncio.sleep(0.1)
   ```

2. **Fix agent_sdk/worker.py (E402)**:
   - Move module-level import to top of file
   - Ensure all imports before code

3. **Fix agents/creative_agent.py (F401)**:
   - Remove unused import `ImageInput`
   - Update import statement to only include used symbols

4. **Validation**:

   ```bash
   ruff check . --output-format=json  # Should return []
   isort . --check-only
   black --check .
   mypy .
   ```

**Acceptance Criteria**:

- ✅ Zero ruff errors
- ✅ Zero isort violations
- ✅ Zero black formatting issues
- ✅ CI pipeline passes

---

### Phase 1: Auto-Trigger Hooks (PostToolUse Automation)

**Priority**: HIGH
**Duration**: 2-3 days
**Dependencies**: Phase 0 complete

**Objective**: Implement auto-triggered quality gates and orchestration.

#### 1.1 Auto-Format Hook (Post Write/Edit)

**File**: `.claude/hooks/scripts/auto-format.sh`

```bash
#!/bin/bash
# Auto-format Python files after Write/Edit operations
# Triggers: PostToolUse (Write|Edit) on .py files

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process Python files
if [[ "$file_path" == *.py ]]; then
  echo "🎨 Auto-formatting: $file_path"

  # Run formatters
  isort "$file_path" --quiet 2>&1 || true
  ruff check "$file_path" --fix --quiet 2>&1 || true
  black "$file_path" --quiet 2>&1 || true

  # Check for remaining errors
  errors=$(ruff check "$file_path" --output-format=json 2>&1)
  if [ "$errors" != "[]" ]; then
    echo "⚠️  Formatting applied, but linting errors remain"
  else
    echo "✅ File formatted successfully"
  fi
fi

cat <<EOF
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "Auto-formatted $file_path"
}
EOF
```

**Hook Registration** (add to `.claude/hooks/hooks.json`):

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",
      "hooks": [
        {
          "type": "command",
          "command": "bash .claude/hooks/scripts/auto-format.sh",
          "timeout": 30
        }
      ]
    }
  ]
}
```

#### 1.2 Auto-Test Hook (Post Code Changes)

**File**: `.claude/hooks/scripts/auto-test.sh`

```bash
#!/bin/bash
# Auto-run tests after code file changes
# Detects relevant test files and executes them

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process code files (.py, .ts, .tsx)
if [[ "$file_path" =~ \.(py|ts|tsx)$ ]]; then
  # Find relevant test file
  if [[ "$file_path" == *.py ]]; then
    # Python: Look for test_<filename>.py or <filename>_test.py
    dir=$(dirname "$file_path")
    filename=$(basename "$file_path" .py)
    test_file=$(find tests/ -name "test_${filename}.py" -o -name "${filename}_test.py" 2>/dev/null | head -1)

    if [ -n "$test_file" ]; then
      echo "🧪 Running tests: $test_file"
      pytest "$test_file" -v --tb=short 2>&1 | tail -20
    fi
  elif [[ "$file_path" =~ \.(ts|tsx)$ ]]; then
    # TypeScript: Run Jest/Vitest
    cd frontend && npm run test -- --passWithNoTests 2>&1 | tail -20
  fi
fi

cat <<EOF
{
  "continue": true,
  "suppressOutput": true
}
EOF
```

#### 1.3 Auto-RAG-Ingest Hook (Post Doc Write)

**File**: `.claude/hooks/scripts/auto-rag-ingest.sh`

```bash
#!/bin/bash
# Auto-ingest documentation into RAG system
# Triggers: PostToolUse (Write|Edit) on .md files

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only process documentation files
if [[ "$file_path" =~ \.(md|txt|rst)$ ]]; then
  echo "📚 Ingesting into RAG: $file_path"

  # Call RAG ingestion via Python
  python -c "
import sys
sys.path.insert(0, '.')
from orchestration.document_ingestion import DocumentIngestionPipeline
from orchestration.vector_store import VectorStoreConfig

config = VectorStoreConfig()
pipeline = DocumentIngestionPipeline(config)
pipeline.ingest_file('$file_path')
print('✅ Document ingested successfully')
" 2>&1 || echo "⚠️  RAG ingestion failed"
fi

cat <<EOF
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "Auto-ingested $file_path into RAG system"
}
EOF
```

#### 1.4 Auto-Security-Scan Hook (Post Dependency Changes)

**File**: `.claude/hooks/scripts/auto-security-scan.sh`

```bash
#!/bin/bash
# Auto-run security scan after dependency changes
# Triggers: PostToolUse (Write|Edit) on package.json, pyproject.toml, requirements.txt

set -euo pipefail

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Detect dependency files
if [[ "$file_path" =~ (package\.json|pyproject\.toml|requirements\.txt|Pipfile)$ ]]; then
  echo "🔒 Running security scan after dependency change: $file_path"

  # Python dependencies
  if [[ "$file_path" =~ \.(toml|txt)$ ]]; then
    pip-audit --desc --format json 2>&1 | jq -r '.vulnerabilities[] | "\(.name): \(.advisory)"' | head -10
  fi

  # Node dependencies
  if [[ "$file_path" == "package.json" ]]; then
    cd frontend && npm audit --json 2>&1 | jq -r '.vulnerabilities | to_entries[] | "\(.key): \(.value.severity)"' | head -10
  fi
fi

cat <<EOF
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "Security scan completed"
}
EOF
```

**Testing Strategy**:

1. Create test file → verify auto-format runs
2. Modify code → verify tests auto-execute
3. Write doc → verify RAG ingestion
4. Update requirements.txt → verify security scan

---

### Phase 2: Workflow Skills (User Commands)

**Priority**: HIGH
**Duration**: 3-4 days
**Dependencies**: Phase 0 complete

#### 2.1 `/test-and-commit` Skill

**File**: `.claude/skills/test-and-commit.md`

```markdown
---
name: test-and-commit
description: TDD workflow - write tests, run them, commit if passing
tags: [tdd, testing, git, workflow]
---

# Test-and-Commit Workflow

Execute TDD best practices: tests first, then commit.

## Phase 1: Test Discovery
- Find all test files in `tests/`
- Identify new/modified tests

## Phase 2: Test Execution
- Run pytest with coverage
- Display failures immediately
- Block commit if tests fail

## Phase 3: Commit
- Stage changes (git add)
- Generate commit message from test names
- Commit with TDD compliance message
- Run git status verification

## Workflow
```bash
pytest tests/ -v --cov=. --cov-report=term
if [ $? -eq 0 ]; then
  git add .
  git commit -m "feat: $(pytest --collect-only -q | head -3 | tail -1)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
  git status
else
  echo "❌ BLOCKED: Tests must pass before commit"
  exit 1
fi
```

```

#### 2.2 `/code-review` Skill

**File**: `.claude/skills/code-review.md`

```markdown
---
name: code-review
description: Comprehensive code analysis with security, quality, and architecture review
tags: [review, security, quality, analysis]
---

# Comprehensive Code Review

## Review Dimensions

### 1. Security Analysis
- Run bandit (OWASP)
- Check for hardcoded secrets
- SQL injection risks
- XSS vulnerabilities
- Command injection

### 2. Code Quality
- Cyclomatic complexity (>10 = warning)
- Code duplication
- Type hint coverage
- Docstring coverage

### 3. Architecture Review
- Design pattern compliance
- SOLID principles
- Dependency injection
- Separation of concerns

### 4. Performance Analysis
- Algorithm complexity
- Database query efficiency
- Caching opportunities
- Async/await usage

### 5. Test Coverage
- Line coverage (target: >80%)
- Branch coverage
- Missing edge cases

## Output Format
```json
{
  "security_score": 0-100,
  "quality_score": 0-100,
  "architecture_score": 0-100,
  "test_coverage": 0-100,
  "overall_grade": "A-F",
  "critical_issues": [],
  "recommendations": []
}
```

```

#### 2.3 `/fix-linting` Skill

**File**: `.claude/skills/fix-linting.md`

```markdown
---
name: fix-linting
description: Auto-fix all ruff/linting issues across codebase
tags: [linting, formatting, quality, automation]
---

# Auto-Fix Linting Issues

CRITICAL: Addresses CRITICAL_WORKFLOW_DIRECTIVE

## Execution Steps

1. Run isort (import sorting)
2. Run ruff check --fix (auto-fixable issues)
3. Run black (code formatting)
4. Verify no remaining errors
5. Report statistics

## Command Pipeline
```bash
echo "🎨 Phase 1: Import Sorting"
isort . --diff | tee /tmp/isort.log

echo "🔧 Phase 2: Linting (Auto-Fix)"
ruff check . --fix --output-format=json | tee /tmp/ruff-fix.log

echo "⚫ Phase 3: Code Formatting"
black . --diff | tee /tmp/black.log

echo "✅ Phase 4: Verification"
ruff check . --output-format=json > /tmp/ruff-final.json

# Parse results
total_fixed=$(jq length /tmp/ruff-fix.log)
remaining=$(jq length /tmp/ruff-final.json)

echo "
📊 Linting Summary:
  Fixed: $total_fixed issues
  Remaining: $remaining issues
  Status: $([ $remaining -eq 0 ] && echo '✅ PASS' || echo '⚠️  MANUAL FIX NEEDED')
"
```

```

#### 2.4 `/rag-ingest` Skill

**File**: `.claude/skills/rag-ingest.md`

```markdown
---
name: rag-ingest
description: Batch document ingestion into RAG system with validation
tags: [rag, ingestion, knowledge-base, semantic-search]
---

# RAG Batch Ingestion

Ingest documentation into ChromaDB vector store for semantic search.

## Supported Formats
- Markdown (.md)
- Text (.txt)
- PDF (.pdf)
- Python (.py) - docstrings extracted
- ReStructuredText (.rst)

## Ingestion Pipeline

1. **File Discovery**: Scan directory recursively
2. **Chunking**: Split into 512-token chunks (overlap: 50)
3. **Embedding**: Generate embeddings (sentence-transformers)
4. **Indexing**: Store in ChromaDB with metadata
5. **Validation**: Verify retrieval accuracy

## Usage
```python
from orchestration.document_ingestion import DocumentIngestionPipeline
from orchestration.vector_store import VectorStoreConfig

config = VectorStoreConfig(
    collection_name="devskyy_docs",
    persist_directory="./data/vectordb"
)

pipeline = DocumentIngestionPipeline(config)

# Ingest directory
stats = pipeline.ingest_directory(
    "docs/",
    recursive=True,
    file_patterns=["*.md", "*.py"]
)

print(f"Ingested {stats['total_documents']} documents")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Embedding dimension: {stats['embedding_dim']}")
```

## Validation

- Test query: "How to use RAG system?"
- Expected: Retrieve this document in top-3 results

```

#### 2.5 `/mcp-health` Skill

**File**: `.claude/skills/mcp-health.md`

```markdown
---
name: mcp-health
description: MCP server health check and diagnostics
tags: [mcp, monitoring, diagnostics, health-check]
---

# MCP Server Health Check

Comprehensive diagnostics for all MCP servers.

## Checks

### 1. Server Availability
- devskyy_mcp (21 tools)
- agent_bridge_server (72 tools)
- rag_server (6 tools)
- woocommerce_mcp (e-commerce)

### 2. Tool Catalog Validation
- Count tools per server
- Verify tool schemas
- Check handler registration
- Validate Advanced Tool Use fields

### 3. Performance Metrics
- Average tool execution time
- Error rate (last 24h)
- Cache hit rate
- Timeout occurrences

### 4. Dependency Health
- Database connectivity (PostgreSQL)
- Redis availability
- ChromaDB status
- External API availability (OpenAI, Anthropic, etc.)

## Output
```json
{
  "servers": [
    {
      "name": "devskyy_mcp",
      "status": "healthy",
      "tool_count": 21,
      "avg_latency_ms": 150,
      "error_rate": 0.01
    }
  ],
  "overall_health": "healthy|degraded|unhealthy",
  "recommendations": []
}
```

```

**Testing Strategy**:
1. Invoke each skill manually
2. Verify outputs match specifications
3. Test error scenarios
4. Measure execution time

---

### Phase 3: Hybrid MCP/RAG Enterprise Integration

**Priority**: HIGH
**Duration**: 4-5 days
**Dependencies**: Phases 0-2 complete

#### 3.1 Unified Tool Catalog

**File**: `runtime/tool_catalog.py`

```python
"""
Unified Tool Catalog
====================

Aggregates tools from all sources:
- ToolRegistry (runtime/tools.py)
- MCP Servers (4 servers, 99 tools)
- RAG Tools (6 tools)
- SuperAgent Tools (17 prompt techniques)

Provides:
- Centralized tool discovery
- Cross-server search
- Capability mapping
- Auto-documentation
"""

from dataclasses import dataclass
from typing import Any

from runtime.tools import ToolRegistry, ToolSpec


@dataclass
class ToolCatalogEntry:
    """Enhanced tool entry with source tracking."""

    spec: ToolSpec
    source: str  # "registry" | "mcp:server_name" | "rag" | "agent:agent_name"
    handler_available: bool
    last_used: datetime | None
    usage_count: int
    avg_execution_time_ms: float
    error_rate: float


class UnifiedToolCatalog:
    """Centralized tool catalog across all systems."""

    def __init__(self, tool_registry: ToolRegistry):
        self.registry = tool_registry
        self.catalog: dict[str, ToolCatalogEntry] = {}
        self._build_catalog()

    def _build_catalog(self) -> None:
        """Build catalog from all sources."""
        # 1. ToolRegistry tools
        for tool in self.registry.list_all():
            self.catalog[tool.name] = ToolCatalogEntry(
                spec=tool,
                source="registry",
                handler_available=self.registry.get_handler(tool.name) is not None,
                last_used=None,
                usage_count=0,
                avg_execution_time_ms=0,
                error_rate=0
            )

        # 2. MCP Server tools (discover dynamically)
        # 3. RAG tools
        # 4. SuperAgent capabilities

    def search(self, query: str) -> list[ToolCatalogEntry]:
        """Semantic search across all tools."""
        # Use RAG to find relevant tools by description
        pass

    def get_by_capability(self, capability: str) -> list[ToolCatalogEntry]:
        """Find tools by capability (e.g., "3d_generation", "commerce")."""
        pass

    def export_documentation(self) -> str:
        """Generate markdown documentation for all tools."""
        pass
```

#### 3.2 Agent-Tool Integration

**File**: `agents/base_super_agent.py` (refactor)

```python
# CURRENT (execute_with_learning wrapper):
async def execute_task(self, task: str) -> AgentResult:
    result = await self.execute_with_learning(task)
    return result

# NEW (direct ToolRegistry usage):
async def use_tool(
    self,
    tool_name: str,
    params: dict[str, Any],
    context: ToolCallContext | None = None
) -> ToolExecutionResult:
    """Execute tool via ToolRegistry with full observability."""
    context = context or ToolCallContext(
        agent_id=self.agent_id,
        correlation_id=str(uuid.uuid4())
    )

    # Validate permissions
    tool = self.tool_registry.get(tool_name)
    if tool and tool.permissions:
        # Check agent has required permissions
        pass

    # Execute with metrics
    result = await self.tool_registry.execute(tool_name, params, context)

    # Record for self-learning
    self._record_tool_usage(tool_name, result)

    return result
```

**Migration Path**:

1. Add `tool_registry` parameter to SuperAgent **init**
2. Refactor all `execute_with_learning()` calls to `use_tool()`
3. Update tests
4. Deprecate old wrapper

#### 3.3 RAG Quality Hooks

**File**: `orchestration/rag_quality.py`

```python
"""
RAG Quality Monitoring
======================

Hooks for RAG system quality assurance:
- Chunk quality validation
- Embedding drift detection
- Retrieval accuracy metrics
- Cache optimization
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RAGQualityMetrics:
    """RAG system quality metrics."""

    # Ingestion Quality
    avg_chunk_size: int
    chunk_overlap_ratio: float
    duplicate_chunk_rate: float

    # Embedding Quality
    embedding_dimension: int
    embedding_variance: float  # High variance = good diversity
    embedding_drift: float  # Drift from baseline

    # Retrieval Quality
    avg_retrieval_score: float
    precision_at_k: dict[int, float]  # {1: 0.8, 3: 0.9, 5: 0.95}
    recall_at_k: dict[int, float]

    # Performance
    avg_query_latency_ms: float
    cache_hit_rate: float
    vector_db_size_mb: float


class RAGQualityMonitor:
    """Monitor and enforce RAG quality standards."""

    def validate_chunk_quality(self, chunk: str) -> dict[str, Any]:
        """Validate chunk before ingestion."""
        return {
            "valid": True,
            "issues": [],
            "score": 0.95,
            "recommendations": []
        }

    def detect_embedding_drift(self) -> float:
        """Detect drift in embeddings over time."""
        # Compare current embeddings to baseline
        # Alert if drift > threshold
        pass

    def measure_retrieval_accuracy(self, test_queries: list[str]) -> RAGQualityMetrics:
        """Measure retrieval accuracy with test queries."""
        pass
```

#### 3.4 MCP Server Orchestration

**File**: `mcp_servers/orchestrator.py`

```python
"""
MCP Server Orchestrator
=======================

Coordinates all MCP servers:
- Health monitoring
- Circuit breakers
- Load balancing
- Failover
"""

from enum import Enum


class ServerStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MCPServerOrchestrator:
    """Orchestrate multiple MCP servers."""

    def __init__(self):
        self.servers = {
            "devskyy_mcp": {"port": 8001, "tools": 21},
            "agent_bridge": {"port": 8002, "tools": 72},
            "rag_server": {"port": 8003, "tools": 6},
            "woocommerce": {"port": 8004, "tools": 10}
        }
        self.circuit_breakers = {}

    async def health_check(self, server_name: str) -> ServerStatus:
        """Check server health."""
        # HTTP health endpoint check
        # Tool availability check
        # Response time check
        pass

    async def route_tool_call(self, tool_name: str, params: dict) -> Any:
        """Route tool call to appropriate server with failover."""
        # 1. Find server hosting tool
        # 2. Check circuit breaker
        # 3. Execute with timeout
        # 4. Failover if needed
        pass
```

---

### Phase 4: Testing & Quality Assurance

**Priority**: CRITICAL
**Duration**: 2-3 days
**Dependencies**: Phases 0-3 complete

#### 4.1 Hook Integration Tests

**File**: `tests/integration/test_hooks.py`

```python
"""Integration tests for hooks system."""

import pytest


@pytest.mark.asyncio
async def test_auto_format_hook_triggers_on_write(tmp_path):
    """Verify auto-format hook runs after Write operation."""
    test_file = tmp_path / "test.py"

    # Write unformatted code
    test_file.write_text("import os;import sys\ndef foo( ):\n  pass")

    # Simulate PostToolUse hook
    # ... (hook execution logic)

    # Verify formatting applied
    formatted = test_file.read_text()
    assert "import os" in formatted
    assert "import sys" in formatted
    assert "def foo():" in formatted


@pytest.mark.asyncio
async def test_auto_test_hook_runs_relevant_tests():
    """Verify auto-test hook executes correct test file."""
    # Modify agents/creative_agent.py
    # Expect tests/test_creative_agent.py to run
    pass


@pytest.mark.asyncio
async def test_rag_ingest_hook_indexes_document():
    """Verify RAG ingestion hook adds document to vector store."""
    # Write new .md file
    # Verify it's indexed in ChromaDB
    # Verify retrievable via semantic search
    pass
```

#### 4.2 Skill Integration Tests

**File**: `tests/integration/test_skills.py`

```python
"""Integration tests for skills."""

import pytest


@pytest.mark.asyncio
async def test_deploy_skill_full_pipeline():
    """Test /deploy skill end-to-end."""
    # Run deploy skill
    # Verify all 9 phases execute
    # Check for deployment artifacts
    pass


@pytest.mark.asyncio
async def test_fix_linting_skill_resolves_errors():
    """Test /fix-linting skill."""
    # Introduce linting errors
    # Run skill
    # Verify errors fixed
    # Verify ruff check returns []
    pass


@pytest.mark.asyncio
async def test_rag_ingest_skill_batch_processes():
    """Test /rag-ingest skill."""
    # Create test docs
    # Run skill
    # Verify all docs indexed
    # Verify retrieval quality
    pass
```

#### 4.3 Tool Registry Tests

**File**: `tests/unit/test_tool_registry.py`

```python
"""Unit tests for ToolRegistry."""

import pytest
from runtime.tools import ToolRegistry, ToolSpec, ToolCategory, ToolSeverity


def test_tool_registration():
    """Test tool registration and retrieval."""
    registry = ToolRegistry()

    spec = ToolSpec(
        name="test_tool",
        description="Test tool",
        category=ToolCategory.SYSTEM,
        severity=ToolSeverity.READ_ONLY
    )

    registry.register(spec)
    assert registry.get("test_tool") == spec
    assert spec.allowed_callers == ["code_execution_20250825"]  # Auto-PTC


@pytest.mark.asyncio
async def test_tool_execution_with_validation():
    """Test tool execution with parameter validation."""
    # Register tool with schema
    # Execute with valid params → success
    # Execute with invalid params → ValidationError
    pass
```

#### 4.4 RAG Pipeline Tests

**File**: `tests/integration/test_rag_pipeline.py`

```python
"""RAG pipeline integration tests."""

import pytest


@pytest.mark.asyncio
async def test_document_ingestion_pipeline():
    """Test full document ingestion pipeline."""
    # Ingest test document
    # Verify chunking
    # Verify embeddings generated
    # Verify stored in ChromaDB
    pass


@pytest.mark.asyncio
async def test_semantic_search_accuracy():
    """Test retrieval accuracy."""
    # Ingest known documents
    # Query with test questions
    # Verify relevant docs retrieved
    # Measure precision@k, recall@k
    pass


@pytest.mark.asyncio
async def test_query_rewriting():
    """Test query rewriting strategies."""
    # Test all 5 strategies
    # Verify improved retrieval
    pass
```

**Coverage Target**: >80% for all new code

---

### Phase 5: Documentation & Deployment

**Priority**: MEDIUM
**Duration**: 1-2 days
**Dependencies**: Phases 0-4 complete

#### 5.1 Documentation

**Files to Create**:

1. `docs/HOOKS_AND_SKILLS_GUIDE.md` - Developer guide
2. `docs/TOOL_CATALOG.md` - Auto-generated tool documentation
3. `docs/RAG_USAGE_GUIDE.md` - RAG system usage
4. `docs/MONITORING.md` - Metrics and observability
5. `.claude/hooks/README.md` - Hook development guide
6. `.claude/skills/README.md` - Skill development guide

**Tool Catalog Auto-Generation**:

```python
# runtime/generate_tool_catalog.py
from runtime.tool_catalog import UnifiedToolCatalog

catalog = UnifiedToolCatalog(tool_registry)
markdown = catalog.export_documentation()

with open("docs/TOOL_CATALOG.md", "w") as f:
    f.write(markdown)
```

#### 5.2 Deployment Checklist

- [ ] All tests passing
- [ ] Zero linting errors
- [ ] Documentation complete
- [ ] Metrics dashboards configured
- [ ] Audit logs enabled
- [ ] Circuit breakers tested
- [ ] Rollback plan verified
- [ ] Performance benchmarks met

---

## Critical Files for Implementation

### Phase 0 (Linting Fixes)

1. `/Users/coreyfoster/DevSkyy/agent_sdk/task_queue.py` - Fix SIM105 (contextlib.suppress)
2. `/Users/coreyfoster/DevSkyy/agent_sdk/worker.py` - Fix E402 (import order)
3. `/Users/coreyfoster/DevSkyy/agents/creative_agent.py` - Fix F401 (unused import)

### Phase 1 (Hooks)

1. `/Users/coreyfoster/DevSkyy/.claude/hooks/scripts/auto-format.sh` - Auto-format hook
2. `/Users/coreyfoster/DevSkyy/.claude/hooks/scripts/auto-test.sh` - Auto-test hook
3. `/Users/coreyfoster/DevSkyy/.claude/hooks/scripts/auto-rag-ingest.sh` - RAG ingestion hook
4. `/Users/coreyfoster/DevSkyy/.claude/hooks/scripts/auto-security-scan.sh` - Security scan hook
5. `/Users/coreyfoster/DevSkyy/.claude/hooks/hooks.json` - Hook registration (modify)

### Phase 2 (Skills)

1. `/Users/coreyfoster/DevSkyy/.claude/skills/test-and-commit.md` - TDD workflow skill
2. `/Users/coreyfoster/DevSkyy/.claude/skills/code-review.md` - Code review skill
3. `/Users/coreyfoster/DevSkyy/.claude/skills/fix-linting.md` - Linting fix skill
4. `/Users/coreyfoster/DevSkyy/.claude/skills/rag-ingest.md` - RAG ingestion skill
5. `/Users/coreyfoster/DevSkyy/.claude/skills/mcp-health.md` - MCP health check skill

### Phase 3 (Integration)

1. `/Users/coreyfoster/DevSkyy/runtime/tool_catalog.py` - Unified tool catalog (create)
2. `/Users/coreyfoster/DevSkyy/runtime/hook_executor.py` - Hook execution engine (create)
3. `/Users/coreyfoster/DevSkyy/orchestration/rag_quality.py` - RAG quality monitoring (create)
4. `/Users/coreyfoster/DevSkyy/mcp_servers/orchestrator.py` - MCP orchestration (create)
5. `/Users/coreyfoster/DevSkyy/agents/base_super_agent.py` - Agent-tool integration (modify)

### Phase 4 (Testing)

1. `/Users/coreyfoster/DevSkyy/tests/integration/test_hooks.py` - Hook integration tests (create)
2. `/Users/coreyfoster/DevSkyy/tests/integration/test_skills.py` - Skill integration tests (create)
3. `/Users/coreyfoster/DevSkyy/tests/unit/test_tool_registry.py` - Tool registry tests (create)
4. `/Users/coreyfoster/DevSkyy/tests/integration/test_rag_pipeline.py` - RAG pipeline tests (create)

### Phase 5 (Documentation)

1. `/Users/coreyfoster/DevSkyy/docs/HOOKS_AND_SKILLS_GUIDE.md` - Developer guide (create)
2. `/Users/coreyfoster/DevSkyy/docs/TOOL_CATALOG.md` - Tool catalog (auto-gen)
3. `/Users/coreyfoster/DevSkyy/docs/RAG_USAGE_GUIDE.md` - RAG guide (create)

---

## Dependency Installation Plan

### Missing Packages (Add to pyproject.toml)

```toml
[project]
dependencies = [
    # ... existing dependencies ...

    # RAG System (CRITICAL)
    "chromadb>=0.5.0",
    "sentence-transformers>=3.0.0",

    # Code Quality (for hooks)
    "isort>=5.13.0",
    "ruff>=0.1.14",
    "black>=24.0.0",
    "mypy>=1.8.0",

    # Security Scanning
    "bandit>=1.7.5",
    "pip-audit>=2.7.0",

    # Testing
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
]
```

**Installation Command**:

```bash
pip install -e ".[dev,test]"
```

---

## Auto-Trigger Mechanisms

### How Hooks Auto-Activate

**PostToolUse Hooks** (from `.claude/hooks/hooks.json`):

1. **Matcher Pattern**: Uses regex to match tool names
   - Example: `"matcher": "Write|Edit"` matches Write or Edit tools
   - Example: `"matcher": "*"` matches all tools

2. **Hook Execution Flow**:

   ```
   User invokes tool (Write, Edit, Bash, etc.)
         ↓
   Claude Code checks hooks.json for matching PostToolUse hooks
         ↓
   Executes matched hooks in sequence
         ↓
   Hooks receive tool input/output as JSON via stdin
         ↓
   Hooks return decision (continue/block) + systemMessage
         ↓
   Claude Code injects systemMessage into context
   ```

3. **Hook Types**:
   - **command**: Execute bash script (e.g., `.claude/hooks/scripts/auto-format.sh`)
   - **prompt**: Send to LLM for analysis (e.g., security validation)

**Auto-Trigger Examples**:

```json
{
  "PostToolUse": [
    {
      "matcher": "Write|Edit",  // Trigger on file edits
      "hooks": [
        {
          "type": "command",
          "command": "bash .claude/hooks/scripts/auto-format.sh",
          "timeout": 30
        }
      ]
    },
    {
      "matcher": "mcp__.*__create_product",  // Trigger on product creation
      "hooks": [
        {
          "type": "prompt",
          "prompt": "Validate product data: $TOOL_INPUT",
          "timeout": 20
        }
      ]
    }
  ]
}
```

**Manual Trigger (Skills)**: Invoked explicitly via `/skill-name` command in chat.

---

## Integration Points

### 1. ToolRegistry ↔ SuperAgents

```python
# Before (agent_sdk/super_agents/commerce_agent.py):
result = await self.execute_with_learning(task)

# After:
result = await self.use_tool(
    "devskyy_manage_products",
    {"action": "create", "product_data": {...}},
    context=ToolCallContext(agent_id="commerce_001")
)
```

### 2. RAG System ↔ SuperAgents

```python
# Before (keyword-based):
knowledge = self.knowledge_base.search(query)

# After (semantic):
from orchestration.vector_store import VectorStoreManager

knowledge = await self.vector_store.semantic_search(
    query=task,
    top_k=5,
    filter_metadata={"agent_type": "commerce"}
)
```

### 3. MCP Servers ↔ ToolRegistry

```python
# Register MCP tools in ToolRegistry
from mcp_servers.server_manager import MCPServerManager

mcp_manager = MCPServerManager()
for server in mcp_manager.list_servers():
    for tool in server.list_tools():
        registry.register(
            spec=tool.to_tool_spec(),
            handler=mcp_manager.create_handler(server.name, tool.name)
        )
```

### 4. Hooks ↔ Metrics

```python
# In hook scripts:
echo "{\"hook\": \"auto-format\", \"duration_ms\": $duration}" >> .claude/hooks/logs/metrics.jsonl

# In Prometheus exporter:
hook_execution_duration = Histogram(
    'devskyy_hook_execution_seconds',
    'Hook execution duration',
    ['hook_name', 'status']
)
```

---

## Success Criteria

### Phase 0 (Linting)

- ✅ Zero ruff errors
- ✅ Zero isort violations
- ✅ Zero black formatting issues
- ✅ CI pipeline passes

### Phase 1 (Hooks)

- ✅ Auto-format runs on every Write/Edit
- ✅ Auto-test executes on code changes
- ✅ RAG auto-ingests documentation
- ✅ Security scan triggers on dependency changes
- ✅ All hooks complete in <30s

### Phase 2 (Skills)

- ✅ All 5 skills implemented
- ✅ `/fix-linting` resolves ruff errors
- ✅ `/test-and-commit` enforces TDD
- ✅ `/code-review` generates comprehensive reports
- ✅ `/rag-ingest` processes 100+ docs/minute
- ✅ `/mcp-health` detects server failures

### Phase 3 (Integration)

- ✅ Unified tool catalog with 99+ tools
- ✅ SuperAgents use ToolRegistry directly
- ✅ RAG retrieval accuracy >80% precision@5
- ✅ MCP orchestrator handles failover
- ✅ Circuit breakers prevent cascading failures

### Phase 4 (Testing)

- ✅ >80% test coverage
- ✅ All integration tests pass
- ✅ Performance benchmarks met (hooks <30s, RAG <500ms)
- ✅ Zero test failures

### Phase 5 (Documentation)

- ✅ Complete developer guides
- ✅ Auto-generated tool catalog
- ✅ Monitoring dashboards configured
- ✅ Runbook for common issues

---

## Risk Mitigation

### High-Risk Areas

1. **RAG Dependency Installation**:
   - Risk: ChromaDB may have C++ build requirements
   - Mitigation: Use pre-built wheels, fallback to simpler embedding model

2. **Auto-Hook Infinite Loops**:
   - Risk: Auto-format hook triggers Write → triggers hook again
   - Mitigation: Track hook execution depth, max depth = 2

3. **Tool Registry Migration**:
   - Risk: Breaking existing agent workflows
   - Mitigation: Gradual migration, maintain backward compatibility

4. **Performance Degradation**:
   - Risk: Hooks add latency to every operation
   - Mitigation: Async execution, timeout limits, conditional triggering

### Rollback Plan

If critical issues arise:

1. **Disable Hooks**: Set `"enabled": false` in hooks.json
2. **Revert ToolRegistry Changes**: Use git to restore agents/base_super_agent.py
3. **Fallback RAG**: Use keyword search instead of semantic
4. **Circuit Breaker**: Disable failing MCP servers

---

## Next Steps

### Immediate Actions (This Sprint)

1. **Fix Linting Errors** (Phase 0) - BLOCKING
   - File: agent_sdk/task_queue.py, worker.py, agents/creative_agent.py
   - Duration: 30 minutes
   - Owner: Implementation agent

2. **Implement Auto-Format Hook** (Phase 1)
   - File: .claude/hooks/scripts/auto-format.sh
   - Duration: 2 hours
   - Test: Write unformatted .py file, verify auto-format

3. **Create `/fix-linting` Skill** (Phase 2)
   - File: .claude/skills/fix-linting.md
   - Duration: 1 hour
   - Test: Introduce linting errors, run skill, verify fixed

### Future Sprints

- **Sprint 2**: Complete Phase 1 (all hooks), Phase 2 (all skills)
- **Sprint 3**: Phase 3 (integration layer)
- **Sprint 4**: Phase 4 (testing), Phase 5 (documentation)

---

## Appendix: File Structure Summary

```
DevSkyy/
├── .claude/
│   ├── hooks/
│   │   ├── hooks.json                      # Hook registration (modify)
│   │   ├── scripts/
│   │   │   ├── auto-format.sh              # NEW: Auto-format hook
│   │   │   ├── auto-test.sh                # NEW: Auto-test hook
│   │   │   ├── auto-rag-ingest.sh          # NEW: RAG ingestion hook
│   │   │   ├── auto-security-scan.sh       # NEW: Security scan hook
│   │   │   ├── audit-log.sh                # EXISTING
│   │   │   ├── load-context.sh             # EXISTING
│   │   │   └── validate-bash.sh            # EXISTING
│   │   └── README.md                       # NEW: Hook development guide
│   └── skills/
│       ├── deploy.md                       # EXISTING
│       ├── test-and-commit.md              # NEW
│       ├── code-review.md                  # NEW
│       ├── fix-linting.md                  # NEW
│       ├── rag-ingest.md                   # NEW
│       ├── mcp-health.md                   # NEW
│       └── README.md                       # NEW: Skill development guide
├── runtime/
│   ├── tools.py                            # EXISTING: ToolRegistry
│   ├── tool_catalog.py                     # NEW: Unified catalog
│   └── hook_executor.py                    # NEW: Hook execution engine
├── orchestration/
│   ├── vector_store.py                     # EXISTING
│   ├── document_ingestion.py               # EXISTING
│   ├── query_rewriter.py                   # EXISTING
│   └── rag_quality.py                      # NEW: RAG quality monitoring
├── mcp_servers/
│   ├── devskyy_mcp.py                      # EXISTING
│   ├── agent_bridge_server.py              # EXISTING
│   ├── rag_server.py                       # EXISTING
│   ├── woocommerce_mcp.py                  # EXISTING
│   └── orchestrator.py                     # NEW: MCP orchestration
├── agents/
│   └── base_super_agent.py                 # MODIFY: Add use_tool()
├── tests/
│   ├── integration/
│   │   ├── test_hooks.py                   # NEW
│   │   ├── test_skills.py                  # NEW
│   │   └── test_rag_pipeline.py            # NEW
│   └── unit/
│       └── test_tool_registry.py           # NEW
├── docs/
│   ├── HOOKS_AND_SKILLS_GUIDE.md           # NEW
│   ├── TOOL_CATALOG.md                     # NEW (auto-generated)
│   ├── RAG_USAGE_GUIDE.md                  # NEW
│   └── MONITORING.md                       # NEW
└── pyproject.toml                          # MODIFY: Add dependencies
```

---

**End of Plan**
