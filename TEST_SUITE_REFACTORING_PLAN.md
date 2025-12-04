# Test Suite Refactoring Plan

## Executive Summary

**Current State:**
- **Coverage:** 8.64%
- **Tests Collected:** 4,064
- **Passing:** 372 tests
- **Failing:** 76 tests
- **Collection Errors:** 21 files

**Target State:**
- **Phase 1 Target:** 30% coverage, 0 collection errors
- **Phase 2 Target:** 50% coverage, <10 failing tests
- **Phase 3 Target:** 70% coverage, stable CI/CD
- **Phase 4 Target:** 90% coverage, production-ready

---

## Root Cause Analysis

### Category 1: Missing Dependencies (7 files)
| File | Missing Dependency | Fix |
|------|-------------------|-----|
| `tests/api/test_dashboard_comprehensive.py` | `psutil` | Add to test dependencies |
| `tests/test_video_generation.py` | `PIL` (Pillow) | Add to test dependencies |
| `tests/monitoring/test_system_monitor.py` | `psutil` | Add to test dependencies |
| `tests/infrastructure/test_elasticsearch_manager.py` | Module instantiation at import | Lazy initialization |
| `tests/infrastructure/test_redis_manager.py` | Redis connection at import | Lazy initialization |
| `tests/ml/test_model_validation.py` | ML dependencies | Add optional deps |
| `tests/security/test_security_fixes.py` | Unknown | Investigate |

### Category 2: Hardcoded Paths (4 files)
| File | Issue | Fix |
|------|-------|-----|
| `tests/e2e/test_fashion_automation_e2e.py` | `/home/user/DevSkyy/` hardcoded | Use relative paths |
| `tests/integration/test_content_workflow.py` | Same hardcoded path | Use relative paths |
| `tests/unit/agent/test_fashion_orchestrator.py` | Same hardcoded path | Use relative paths |
| `agent/fashion_orchestrator.py:767` | Global instantiation fails | Lazy initialization |

### Category 3: Module Structure Issues (3 files)
| File | Issue | Fix |
|------|-------|-----|
| `tests/unit/agent/test_orchestrator.py` | Duplicate module name | Rename file |
| `tests/integration/test_sqlite_setup.py` | `AsyncSessionLocal` missing | Update import |
| `tests/unit/test_database.py` | `DatabaseManager` missing | Update import |

### Category 4: API Contract Mismatches (6 files - fashion_ai_bounded_autonomy)
All tests in `tests/fashion_ai_bounded_autonomy/` fail due to import errors from the source modules.

### Category 5: Test Expectation Mismatches (76 failing tests)
- `security/jwt_auth.py`: `UserRole` is `str` not `Enum` - tests expect `.value`
- `security/encryption.py`: API changes in encryption functions
- `services/rag_service.py`: API changes in RAG service

---

## Strategic Refactoring Plan

### Phase 1: Foundation Fixes (Week 1)
**Goal:** 0 collection errors, all tests can be collected

#### Agent 1: Dependency Resolution Agent
**Responsibility:** Fix all missing dependency issues
**Success Criteria:** `pytest --collect-only` shows 0 errors

#### Agent 2: Path Normalization Agent  
**Responsibility:** Fix all hardcoded path issues
**Success Criteria:** Tests work regardless of working directory

#### Agent 3: Module Structure Agent
**Responsibility:** Fix duplicate names and import issues
**Success Criteria:** No import conflicts or missing symbols

---

### Phase 2: Mock Infrastructure (Week 2)
**Goal:** All external dependencies properly mocked

#### Agent 4: External API Mock Agent
**Responsibility:** Create mock fixtures for all external APIs
**Success Criteria:** Tests run without network calls

#### Agent 5: Database Mock Agent
**Responsibility:** Create proper database fixtures
**Success Criteria:** Tests use in-memory SQLite

---

### Phase 3: Test Alignment (Week 3)
**Goal:** Fix API contract mismatches

#### Agent 6: API Contract Alignment Agent
**Responsibility:** Update tests to match current implementations
**Success Criteria:** 0 failing tests due to API mismatches

---

### Phase 4: Coverage Boost (Week 4)
**Goal:** Achieve 50%+ coverage

#### Agent 7: High-Impact Coverage Agent
**Responsibility:** Add tests for uncovered critical modules
**Success Criteria:** 50% overall coverage

---

## Detailed Agent Specifications

### Agent 1: Dependency Resolution Agent

**Domain:** Package dependencies and imports
**Priority:** CRITICAL (blocks all other work)

**Tasks:**
1. Add missing test dependencies to `pyproject.toml`
2. Create lazy initialization wrappers for modules that instantiate at import
3. Add graceful degradation for optional dependencies

**Files to modify:**
```
pyproject.toml                           # Add: psutil, Pillow to test deps
monitoring/system_monitor.py             # Lazy init for SystemMonitor
infrastructure/elasticsearch_manager.py  # Lazy init for ElasticsearchManager
agent/fashion_orchestrator.py            # Remove global instantiation line 767
```

**Verification:**
```bash
ENVIRONMENT=development python -m pytest --collect-only 2>&1 | grep "ERROR collecting"
# Expected: 0 errors
```

**Deliverables:**
- [ ] Updated `pyproject.toml` with all test dependencies
- [ ] PR with lazy initialization changes
- [ ] Documentation of optional vs required dependencies

---

### Agent 2: Path Normalization Agent

**Domain:** File paths and configuration loading
**Priority:** HIGH

**Tasks:**
1. Replace all hardcoded `/home/user/DevSkyy/` paths with dynamic resolution
2. Create path resolution utility in `core/paths.py`
3. Update all config file loading to use project root detection

**Files to modify:**
```
core/paths.py                            # NEW: Path resolution utilities
agent/fashion_orchestrator.py            # Lines 155-181: config loading
config/unified_config.py                 # Any hardcoded paths
tests/conftest.py                        # Add PROJECT_ROOT fixture
```

**Pattern to implement:**
```python
# core/paths.py
from pathlib import Path

def get_project_root() -> Path:
    """Get project root regardless of working directory."""
    return Path(__file__).parent.parent

def get_config_path(relative_path: str) -> Path:
    """Get absolute path to config file."""
    return get_project_root() / relative_path
```

**Verification:**
```bash
cd /tmp && ENVIRONMENT=development python -c "from agent.fashion_orchestrator import FashionOrchestrator"
# Expected: No FileNotFoundError
```

---

### Agent 3: Module Structure Agent

**Domain:** Python module organization and imports
**Priority:** HIGH

**Tasks:**
1. Rename duplicate test files to unique names
2. Fix missing symbol imports in test files
3. Update `__init__.py` exports where needed

**Files to modify:**
```
tests/unit/agent/test_orchestrator.py    # RENAME to test_unified_orchestrator.py
tests/unit/test_database.py              # Fix DatabaseManager import
tests/integration/test_sqlite_setup.py   # Fix AsyncSessionLocal import
database/__init__.py                     # Export required symbols
```

**Verification:**
```bash
python -m pytest tests/unit/ --collect-only 2>&1 | grep "import file mismatch"
# Expected: 0 matches
```

---

### Agent 4: External API Mock Agent

**Domain:** HTTP API mocking and fixtures
**Priority:** HIGH

**Tasks:**
1. Create `tests/fixtures/api_mocks.py` with reusable mock responses
2. Implement VCR-style recording for external APIs (optional)
3. Create mock fixtures for: OpenAI, Anthropic, WordPress, Tripo3D, FASHN

**Files to create/modify:**
```
tests/fixtures/__init__.py               # NEW
tests/fixtures/api_mocks.py              # NEW: Mock response definitions
tests/fixtures/openai_mocks.py           # NEW: OpenAI-specific mocks
tests/fixtures/wordpress_mocks.py        # NEW: WordPress API mocks
tests/conftest.py                        # Add mock fixtures
```

**Mock pattern:**
```python
# tests/fixtures/api_mocks.py
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client with standard responses."""
    client = MagicMock()
    client.chat.completions.create = MagicMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mocked response"))]
    ))
    return client

@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client with standard responses."""
    client = MagicMock()
    client.messages.create = MagicMock(return_value=MagicMock(
        content=[MagicMock(text="Mocked Claude response")]
    ))
    return client
```

**Verification:**
```bash
ENVIRONMENT=development python -m pytest tests/ -k "api" --tb=short 2>&1 | grep -c "PASSED"
# Expected: Significant increase in passing tests
```

---

### Agent 5: Database Mock Agent

**Domain:** Database fixtures and test isolation
**Priority:** MEDIUM

**Tasks:**
1. Create in-memory SQLite fixtures for all database tests
2. Implement test database seeding utilities
3. Add proper transaction rollback between tests

**Files to modify:**
```
tests/conftest.py                        # Enhanced database fixtures
tests/fixtures/database.py               # NEW: Database test utilities
database/__init__.py                     # Ensure proper exports
```

**Verification:**
```bash
ENVIRONMENT=development python -m pytest tests/infrastructure/test_database.py -v
# Expected: All tests pass with in-memory database
```

---

### Agent 6: API Contract Alignment Agent

**Domain:** Test expectations vs implementation reality
**Priority:** MEDIUM

**Tasks:**
1. Audit `security/jwt_auth.py` - update `UserRole` to proper Enum OR update tests
2. Audit `security/encryption.py` - align test expectations with actual API
3. Audit `services/rag_service.py` - update tests for current implementation

**Files to modify:**
```
security/jwt_auth.py                     # Line 72: UserRole class definition
tests/security/test_jwt_auth.py          # Update test expectations
tests/security/test_encryption.py        # Align with implementation
tests/services/test_rag_service*.py      # Update for current API
```

**Decision Point:**
- Option A: Fix implementation to match tests (if tests reflect desired behavior)
- Option B: Fix tests to match implementation (if implementation is correct)

**Verification:**
```bash
ENVIRONMENT=development python -m pytest tests/security/ -v --tb=short 2>&1 | grep -c "PASSED"
# Target: 90%+ of security tests passing
```

---

### Agent 7: High-Impact Coverage Agent

**Domain:** Test coverage improvement
**Priority:** MEDIUM (after other agents complete)

**Tasks:**
1. Identify top 10 modules by lines of uncovered code
2. Write tests for critical paths in each module
3. Focus on error handling and edge cases

**Target modules (by impact):**
```
1. main.py                    (606 lines, 30% covered → target 70%)
2. agent/orchestrator.py      (424 lines, 16% covered → target 50%)
3. services/consensus_orchestrator.py (349 lines, 0% → target 40%)
4. agent/fashion_orchestrator.py (236 lines, 0% → target 40%)
5. security/jwt_auth.py       (321 lines, 40% → target 70%)
```

**Verification:**
```bash
ENVIRONMENT=development python -m pytest tests/ --cov=. --cov-report=term-missing 2>&1 | grep "TOTAL"
# Target: 50%+ coverage
```

---

## Implementation Schedule

| Week | Agent(s) | Deliverables | Coverage Target |
|------|----------|--------------|-----------------|
| 1 | 1, 2, 3 | 0 collection errors | 15% |
| 2 | 4, 5 | Mock infrastructure complete | 25% |
| 3 | 6 | API contracts aligned | 40% |
| 4 | 7 | Coverage boost complete | 50% |

---

## Success Metrics

### Phase 1 Complete When:
- [ ] `pytest --collect-only` shows 0 errors
- [ ] All tests can be collected regardless of working directory
- [ ] No duplicate module name conflicts

### Phase 2 Complete When:
- [ ] All tests run without network calls
- [ ] Database tests use in-memory SQLite
- [ ] External API failures don't break tests

### Phase 3 Complete When:
- [ ] <10 failing tests (from 76)
- [ ] All security tests pass
- [ ] All core module tests pass

### Phase 4 Complete When:
- [ ] 50%+ overall coverage
- [ ] CI/CD pipeline green
- [ ] Test suite runs in <5 minutes

---

## Appendix: Research-Based Best Practices

### From Industry Research (2024-2025):

1. **Lazy Initialization:** Never instantiate heavy objects at module import time
2. **Mock External Services:** Use `pytest-vcr` or `responses` for HTTP mocking
3. **Fixture Hierarchy:** Use `conftest.py` at each test directory level
4. **Coverage Strategy:** Target high-impact code first (error handlers, auth, core logic)
5. **Test Isolation:** Each test should be independent and idempotent
6. **Dependency Groups:** Use `pyproject.toml` optional dependencies for test-only packages

### Tools Recommended:
- `pytest-cov`: Coverage reporting
- `pytest-xdist`: Parallel test execution
- `responses`: HTTP request mocking
- `factory-boy`: Test data generation
- `pytest-asyncio`: Async test support

