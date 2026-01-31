# DevSkyy Test Coverage Matrix

**Version**: 1.3.0
**Last Updated**: 2026-01-30
**Status**: Production
**Target Coverage**: 85%+

This document provides a comprehensive view of test coverage across the DevSkyy platform.

---

## Table of Contents

1. [Coverage Summary](#coverage-summary)
2. [Module Coverage Table](#module-coverage-table)
3. [Feature to Test Mapping](#feature-to-test-mapping)
4. [Test Organization](#test-organization)
5. [Test Markers](#test-markers)
6. [Running Tests](#running-tests)
7. [Coverage Gaps](#coverage-gaps)

---

## Coverage Summary

| Metric | Value |
|--------|-------|
| Total Test Files | 110+ |
| Total Lines of Test Code | ~51,000 |
| Estimated Tests | 2,500+ |
| Target Coverage | 85% |
| Critical Path Coverage | 100% |

### Test Distribution

```
tests/
  Root Tests:           ~45 files    (Core functionality)
  tests/api/            ~12 files    (API integration)
  tests/services/       ~20 files    (Service layer)
  tests/integration/    ~2 files     (E2E integration)
  tests/llm/            ~4 files     (LLM providers)
  tests/orchestration/  ~3 files     (RAG, embeddings)
  tests/security/       ~2 files     (Security layer)
  tests/agents/         ~2 files     (Agent tests)
  tests/mcp_servers/    ~2 files     (MCP infrastructure)
  tests/sync/           ~2 files     (Sync workflows)
  tests/cli/            ~2 files     (CLI tools)
```

---

## Module Coverage Table

### Core Module (`/core/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `core/auth/types.py` | `test_agents.py` | 100% | Covered |
| `core/auth/models.py` | `test_security.py` | 95% | Covered |
| `core/auth/interfaces.py` | `test_security.py` | 90% | Covered |
| `core/auth/token_payload.py` | `test_security.py` | 100% | Covered |
| `core/auth/role_hierarchy.py` | `test_security.py` | 95% | Covered |
| `core/runtime/tools.py` | `test_tool_registry.py` | 95% | Covered |
| `core/runtime/input_validator.py` | `test_input_validator.py` | 90% | Covered |
| `core/redis_cache.py` | `test_utils_modules.py` | 85% | Covered |
| `core/structured_logging.py` | `test_utils_modules.py` | 80% | Covered |
| `core/token_tracker.py` | `test_utils_modules.py` | 85% | Covered |

### Security Module (`/security/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `security/jwt_oauth2_auth.py` | `test_security.py` | 95% | Covered |
| `security/aes256_gcm_encryption.py` | `test_security.py` | 100% | Covered |
| `security/input_validation.py` | `test_security.py` | 90% | Covered |
| `security/rate_limiting.py` | `test_security.py` | 85% | Covered |
| `security/audit_log.py` | `test_security.py` | 80% | Covered |
| `security/mfa.py` | `test_mfa.py` | 90% | Covered |
| `security/secrets_manager.py` | `test_security.py` | 85% | Covered |
| `security/vulnerability_scanner.py` | `tests/security/test_vulnerability_scanner.py` | 80% | Covered |
| `security/zero_trust_config.py` | `test_zero_trust.py` | 85% | Covered |
| `security/nonce_cache.py` | `tests/security/test_nonce_cache.py` | 90% | Covered |

### Agents Module (`/agents/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `agents/base_super_agent.py` | `test_agents.py` | 85% | Covered |
| `agents/tripo_agent.py` | `test_tripo_agent.py` | 90% | Covered |
| `agents/fashn_agent.py` | `test_virtual_tryon.py` | 85% | Covered |
| `agents/commerce_agent.py` | `test_agents.py` | 80% | Covered |
| `agents/creative_agent.py` | `test_agents.py` | 75% | Partial |
| `agents/marketing_agent.py` | `test_agents.py` | 70% | Partial |
| `agents/support_agent.py` | `test_agents.py` | 70% | Partial |
| `agents/analytics_agent.py` | `test_agents.py` | 75% | Partial |
| `agents/visual_generation/gemini_native.py` | `test_gemini_native.py` | 85% | Covered |
| `agents/visual_generation/prompt_optimizer.py` | `test_gemini_prompts.py` | 80% | Covered |
| `agents/visual_generation/reference_manager.py` | `test_reference_manager.py` | 90% | Covered |

### API Module (`/api/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `api/agents.py` | `tests/api/test_agents.py` | 85% | Covered |
| `api/gdpr.py` | `test_gdpr.py`, `test_gdpr_hardening.py` | 95% | Covered |
| `api/three_d.py` | `tests/api/test_3d_pipeline.py` | 85% | Covered |
| `api/virtual_tryon.py` | `test_virtual_tryon.py` | 80% | Covered |
| `api/webhooks.py` | `test_sync_api.py` | 85% | Covered |
| `api/websocket.py` | Integration tested | 70% | Partial |
| `api/admin_dashboard.py` | `test_admin_dashboard_api.py` | 90% | Covered |
| `api/v1/assets.py` | `tests/api/test_assets_api.py` | 85% | Covered |
| `api/v1/brand_assets.py` | `tests/api/test_brand_assets.py` | 90% | Covered |
| `api/v1/approval.py` | `tests/api/test_approval_queue.py` | 85% | Covered |
| `api/v1/commerce.py` | `test_catalog_sync.py` | 80% | Covered |
| `api/v1/hf_spaces.py` | `test_huggingface_3d.py` | 75% | Partial |

### LLM Module (`/llm/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `llm/router.py` | `test_llm.py` | 80% | Covered |
| `llm/round_table.py` | `test_round_table.py` | 90% | Covered |
| `llm/classification.py` | `tests/llm/test_classification.py` | 85% | Covered |
| `llm/verification.py` | `tests/llm/test_verification.py` | 95% | Covered |
| `llm/providers/anthropic.py` | `test_anthropic_ptc.py` | 85% | Covered |
| `llm/providers/openai.py` | `test_llm.py` | 80% | Covered |
| `llm/providers/google.py` | `test_gemini_provider.py` | 80% | Covered |
| `llm/providers/groq.py` | `tests/llm/test_classification.py` | 85% | Covered |
| `llm/providers/deepseek.py` | `tests/llm/providers/test_deepseek.py` | 100% | Covered |
| `llm/unified_llm_client.py` | `test_llm.py` | 85% | Covered |

### Orchestration Module (`/orchestration/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `orchestration/rag_context_manager.py` | `test_rag_integration.py` | 85% | Covered |
| `orchestration/vector_store.py` | `test_rag_integration.py` | 80% | Covered |
| `orchestration/embedding_engine.py` | `tests/orchestration/test_embedding_engine.py` | 85% | Covered |
| `orchestration/reranker.py` | `tests/orchestration/test_reranker.py` | 100% | Covered |
| `orchestration/query_rewriter.py` | `test_rag_integration.py` | 75% | Partial |
| `orchestration/brand_context.py` | `test_agents.py` | 80% | Covered |
| `orchestration/llm_clients.py` | `test_llm.py` | 85% | Covered |
| `orchestration/huggingface_3d_client.py` | `test_huggingface_3d.py` | 80% | Covered |
| `orchestration/enterprise_index.py` | `tests/orchestration/test_enterprise_index.py` | 80% | Covered |

### Services Module (`/services/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `services/ml/` | `tests/services/ml/` | 85% | Covered |
| `services/three_d/` | `tests/services/three_d/` | 90% | Covered |
| `services/storage/r2_client.py` | `tests/services/test_r2_client.py` | 85% | Covered |
| `services/analytics/` | `tests/services/analytics/` | 80% | Covered |
| `services/approval_queue_manager.py` | `tests/services/test_approval_queue_manager.py` | 90% | Covered |
| `services/notifications/email.py` | `tests/services/test_email_notifications.py` | 85% | Covered |

### AI 3D Module (`/ai_3d/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `ai_3d/generation_pipeline.py` | `test_3d_pipeline.py` | 90% | Covered |
| `ai_3d/model_generator.py` | `test_ai_3d_generator.py` | 85% | Covered |
| `ai_3d/quality_enhancer.py` | `test_3d_pipeline.py` | 80% | Covered |
| `ai_3d/resilience.py` | `test_3d_pipeline_hardening.py` | 90% | Covered |
| `ai_3d/virtual_photoshoot.py` | `test_virtual_photoshoot.py` | 85% | Covered |

### ADK Module (`/adk/`)

| Component | Test File | Coverage | Status |
|-----------|-----------|----------|--------|
| `adk/base.py` | `test_adk.py` | 90% | Covered |
| `adk/google_adk.py` | `test_adk.py` | 85% | Covered |
| `adk/pydantic_adk.py` | `test_adk.py` | 80% | Covered |
| `adk/crewai_adk.py` | `test_adk.py` | 75% | Partial |
| `adk/autogen_adk.py` | `test_adk.py` | 75% | Partial |

---

## Feature to Test Mapping

### Authentication & Authorization

| Feature | Test Files | Priority |
|---------|------------|----------|
| JWT Token Generation | `test_security.py` | Critical |
| Token Refresh Flow | `test_security.py` | Critical |
| Token Revocation | `test_security.py` | Critical |
| Role-Based Access Control | `test_security.py` | Critical |
| OAuth2 Flows | `test_security.py` | High |
| MFA (TOTP) | `test_mfa.py` | High |
| Rate Limiting | `test_security.py` | High |
| Account Lockout | `test_security.py` | Medium |

### Agent Operations

| Feature | Test Files | Priority |
|---------|------------|----------|
| Agent Execution | `test_agents.py` | Critical |
| Tool Registry | `test_tool_registry.py` | Critical |
| Prompt Techniques | `test_agents.py` | High |
| RAG Context Retrieval | `test_rag_integration.py` | High |
| LLM Routing | `test_llm.py` | High |
| Round Table Consensus | `test_round_table.py` | Medium |

### 3D Generation

| Feature | Test Files | Priority |
|---------|------------|----------|
| Tripo3D Integration | `test_tripo_agent.py`, `test_3d_pipeline.py` | Critical |
| Quality Gates | `test_3d_pipeline_hardening.py` | High |
| Mesh Optimization | `test_3d_pipeline.py` | High |
| glTF Export | `test_3d_pipeline.py` | Medium |
| Virtual Photoshoot | `test_virtual_photoshoot.py` | Medium |

### Virtual Try-On

| Feature | Test Files | Priority |
|---------|------------|----------|
| FASHN API Integration | `test_virtual_tryon.py` | Critical |
| Image Upload | `test_virtual_tryon.py` | High |
| Try-On Generation | `test_virtual_tryon.py` | High |
| Result Storage | `test_virtual_tryon.py` | Medium |

### WordPress/WooCommerce

| Feature | Test Files | Priority |
|---------|------------|----------|
| Product Sync | `test_catalog_sync.py`, `test_sync_api.py` | Critical |
| Media Upload | `test_sync_api.py` | High |
| Webhook Handling | `test_sync_api.py` | High |
| Elementor Templates | Integration tested | Medium |

### GDPR Compliance

| Feature | Test Files | Priority |
|---------|------------|----------|
| Data Export | `test_gdpr.py` | Critical |
| Data Deletion | `test_gdpr.py` | Critical |
| Consent Management | `test_gdpr.py` | Critical |
| PII Masking | `test_gdpr_hardening.py` | High |
| Audit Trail | `test_gdpr.py` | High |

### RAG Pipeline

| Feature | Test Files | Priority |
|---------|------------|----------|
| Document Ingestion | `test_rag_integration.py` | High |
| Vector Search | `test_rag_integration.py` | High |
| Query Rewriting | `test_rag_integration.py` | Medium |
| Reranking | `tests/orchestration/test_reranker.py` | High |
| Embedding Generation | `tests/orchestration/test_embedding_engine.py` | High |

---

## Test Organization

### Directory Structure

```
tests/
  __init__.py
  conftest.py                    # Shared fixtures

  # Root-level tests (unit + component)
  test_agents.py                 # Agent unit tests
  test_security.py               # Security unit tests
  test_llm.py                    # LLM unit tests
  test_rag_integration.py        # RAG tests
  test_3d_pipeline.py            # 3D pipeline tests
  test_virtual_tryon.py          # Try-on tests
  test_gdpr.py                   # GDPR tests
  ...

  # Organized by layer
  api/                           # API integration tests
    test_assets_api.py
    test_approval_queue.py
    test_brand_assets.py
    test_3d_pipeline.py
    analytics/
      test_alert_*.py
      test_business_analytics.py
      ...

  services/                      # Service layer tests
    test_approval_queue_manager.py
    test_email_notifications.py
    test_r2_client.py
    analytics/
    ml/
    three_d/

  integration/                   # End-to-end tests
    test_api_endpoints.py
    test_hybrid_integration.py

  llm/                           # LLM provider tests
    test_classification.py
    test_verification.py
    providers/
      test_deepseek.py
      test_gemini_*.py

  orchestration/                 # Orchestration tests
    test_embedding_engine.py
    test_enterprise_index.py
    test_reranker.py

  security/                      # Security tests
    test_nonce_cache.py
    test_vulnerability_scanner.py

  mcp_servers/                   # MCP tests
    test_mcp_infrastructure.py

  sync/                          # Sync workflow tests
    test_sync_*.py

  cli/                           # CLI tests
    test_cli_*.py
```

### Test Categories

| Category | Directory/Pattern | Description |
|----------|-------------------|-------------|
| Unit | `test_*.py` (root) | Isolated component tests |
| Integration | `tests/integration/` | Component interaction tests |
| API | `tests/api/` | REST endpoint tests |
| Service | `tests/services/` | Business logic tests |
| E2E | Manual / Playwright | Full workflow tests |
| Performance | `@pytest.mark.performance` | Latency/throughput benchmarks |

---

## Test Markers

### Available Markers

```python
@pytest.mark.unit           # Fast, isolated tests
@pytest.mark.integration    # Requires service interaction
@pytest.mark.performance    # Benchmarks (may be slow)
@pytest.mark.slow           # Tests > 10s (external APIs)
@pytest.mark.asyncio        # Async test function
@pytest.mark.skip           # Skip test
@pytest.mark.xfail          # Expected failure
```

### Marker Usage

```python
# Unit test
@pytest.mark.unit
@pytest.mark.asyncio
async def test_jwt_generation():
    ...

# Integration test
@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_pipeline_end_to_end():
    ...

# Performance test
@pytest.mark.performance
@pytest.mark.asyncio
async def test_embedding_throughput():
    ...

# Slow test (external API)
@pytest.mark.slow
@pytest.mark.asyncio
async def test_tripo_real_api():
    ...
```

---

## Running Tests

### Full Test Suite

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Parallel execution
pytest tests/ -n auto
```

### By Marker

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Performance benchmarks
pytest -m performance
```

### By Module

```bash
# Security tests
pytest tests/test_security.py tests/security/ -v

# LLM tests
pytest tests/test_llm.py tests/llm/ -v

# Agent tests
pytest tests/test_agents.py tests/agents/ -v

# API tests
pytest tests/api/ tests/integration/ -v
```

### Single Test

```bash
# Specific test function
pytest tests/test_security.py::test_jwt_token_generation -v

# Specific test class
pytest tests/test_agents.py::TestSuperAgent -v

# Pattern matching
pytest tests/ -k "jwt" -v
```

### Debug Mode

```bash
# Verbose with logging
pytest tests/test_security.py -v -s --log-cli-level=DEBUG

# Stop on first failure
pytest tests/ -x

# Run last failed
pytest tests/ --lf
```

---

## Coverage Gaps

### Known Gaps (Target: Fill by Q2 2026)

| Module | Gap | Priority | Action |
|--------|-----|----------|--------|
| `agents/creative_agent.py` | 75% coverage | Medium | Add prompt variation tests |
| `agents/marketing_agent.py` | 70% coverage | Medium | Add campaign workflow tests |
| `agents/support_agent.py` | 70% coverage | Medium | Add conversation flow tests |
| `api/websocket.py` | 70% coverage | Low | Add WS integration tests |
| `orchestration/query_rewriter.py` | 75% coverage | Medium | Add expansion edge cases |
| `adk/crewai_adk.py` | 75% coverage | Low | Add multi-agent tests |
| `adk/autogen_adk.py` | 75% coverage | Low | Add conversation tests |

### Critical Paths (100% Coverage Required)

| Path | Status | Tests |
|------|--------|-------|
| Authentication Flow | Covered | `test_security.py` |
| Token Validation | Covered | `test_security.py` |
| Input Sanitization | Covered | `test_security.py` |
| Encryption/Decryption | Covered | `test_security.py` |
| GDPR Data Export | Covered | `test_gdpr.py` |
| GDPR Data Deletion | Covered | `test_gdpr.py` |
| 3D Quality Gates | Covered | `test_3d_pipeline_hardening.py` |
| Cost Calculation | Covered | `tests/llm/providers/test_deepseek.py` |

---

## Maintenance

### Adding New Tests

1. Identify the appropriate directory based on test type
2. Use existing fixtures from `conftest.py`
3. Add appropriate `@pytest.mark` decorators
4. Mock external APIs to avoid costs
5. Update this matrix when adding significant coverage

### Coverage Reports

```bash
# Generate HTML report
pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# View report
open htmlcov/index.html
```

### CI/CD Integration

```yaml
# .github/workflows/tests.yml
- name: Run Tests with Coverage
  run: |
    pytest tests/ \
      --cov=. \
      --cov-report=xml \
      --cov-fail-under=80

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```

---

## See Also

- [SYSTEM_ARCHITECTURE.md](../architecture/SYSTEM_ARCHITECTURE.md) - System architecture
- [tests/TEST_STRATEGY.md](/Users/coreyfoster/DevSkyy/tests/TEST_STRATEGY.md) - Test strategy details
- [tests/conftest.py](/Users/coreyfoster/DevSkyy/tests/conftest.py) - Shared fixtures
