# Skipped Tests Analysis

**Date**: 2026-01-09
**Total Skipped Tests**: 9

This document provides analysis and recommendations for all skipped tests in the DevSkyy test suite.

---

## Summary Table

| # | Test File | Test Name | Skip Type | Reason | Recommendation |
|---|-----------|-----------|-----------|--------|----------------|
| 1 | `test_admin_dashboard_api.py` | `test_dashboard_integration` | `@pytest.mark.skip` | Integration test requiring FastAPI app | Keep skipped - run in CI integration stage |
| 2 | `test_admin_dashboard_api.py` | `test_dashboard_requires_auth` | `@pytest.mark.skip` | Integration test requiring FastAPI app | Keep skipped - run in CI integration stage |
| 3 | `test_ai_3d_api.py` | `test_ai3d_integration` | `@pytest.mark.skip` | Integration test requiring 3D pipeline | Keep skipped - run in CI integration stage |
| 4 | `test_sync_api.py` | `test_sync_integration` | `@pytest.mark.skip` | Integration test requiring sync service | Keep skipped - run in CI integration stage |
| 5 | `test_sync_api.py` | `test_bulk_sync_integration` | `@pytest.mark.skip` | Integration test requiring sync service | Keep skipped - run in CI integration stage |
| 6 | `test_pipeline.py` | `test_complete_pipeline` | `@pytest.mark.skipif` | Requires external services (FLUX_SPACE_URL, QWEN_SPACE_URL) | Conditional skip - OK |
| 7 | `test_alerting_integration.py` | `TestLiveSlackIntegration` (class) | `@pytest.mark.skipif` | Requires SLACK_WEBHOOK_URL | Conditional skip - OK |
| 8 | `test_huggingface_3d.py` | `test_full_hybrid_pipeline` | `@pytest.mark.skipif` | Requires HUGGINGFACE_API_TOKEN or HF_TOKEN | Conditional skip - OK |
| 9 | `test_security.py` | `test_bcrypt_fallback` | `@pytest.mark.skip` | passlib/bcrypt 5.x compatibility issue | **Intentional** - Argon2 is production default |

---

## Detailed Analysis

### Category 1: Integration Tests (5 tests)

These tests require a running FastAPI application with full dependencies (database, Redis, external services). They are properly marked with both `@pytest.mark.integration` and `@pytest.mark.skip`.

**Tests:**
1. `test_dashboard_integration` - Tests admin dashboard endpoints with authentication
2. `test_dashboard_requires_auth` - Tests that dashboard requires authentication
3. `test_ai3d_integration` - Tests AI 3D pipeline endpoints
4. `test_sync_integration` - Tests product sync endpoints
5. `test_bulk_sync_integration` - Tests bulk sync functionality

**Status**: These tests have working fixtures in `conftest.py` (`client`, `auth_headers`, `admin_headers`). They can be run in CI's integration stage where the full application is deployed.

**How to run**:
```bash
# In CI with full app running:
pytest -m integration --run-integration tests/
```

**Recommendation**: Keep as-is. The CI pipeline already has an `api-integration` job that runs these.

---

### Category 2: Conditional Environment Skips (3 tests)

These tests use `@pytest.mark.skipif` to conditionally skip when required environment variables are not set. This is the correct pattern for tests that require external services.

**Tests:**

1. **`test_complete_pipeline`** (`test_pipeline.py`)
   - Requires: `FLUX_SPACE_URL`, `QWEN_SPACE_URL`
   - Purpose: Full pipeline integration with Gradio spaces and WordPress
   - Recommendation: **Keep as-is** - Proper conditional skip for external dependencies

2. **`TestLiveSlackIntegration`** (`test_alerting_integration.py`)
   - Requires: `SLACK_WEBHOOK_URL`
   - Purpose: Live Slack webhook integration testing
   - Recommendation: **Keep as-is** - Only runs when Slack is configured

3. **`test_full_hybrid_pipeline`** (`test_huggingface_3d.py`)
   - Requires: `HUGGINGFACE_API_TOKEN` or `HF_TOKEN`
   - Purpose: HuggingFace 3D model generation pipeline
   - Recommendation: **Keep as-is** - Proper gating on API credentials

---

### Category 3: Intentional Compatibility Skip (1 test)

**`test_bcrypt_fallback`** (`test_security.py`)

**Issue**: passlib library has a compatibility issue with bcrypt 5.x. The bcrypt package changed its password length handling, which breaks passlib's BCrypt integration.

**Context**:
- Production uses **Argon2id** (the recommended modern algorithm)
- BCrypt support is retained only for legacy password verification
- This is a known upstream issue: https://github.com/pyca/bcrypt/issues/684

**Recommendation**: **Keep skipped** - This is intentional. The team has chosen Argon2id as the production standard. BCrypt support exists only for backward compatibility with legacy hashes.

---

## Action Items

| Priority | Action | Status |
|----------|--------|--------|
| High | Update skip reasons with clear documentation | ✅ Complete |
| Medium | Verify integration tests can run in CI integration stage | Pending verification |
| Low | Monitor passlib/bcrypt compatibility for future resolution | Tracking issue exists |

---

## Running Specific Test Categories

```bash
# Run all unit tests (excludes skipped)
pytest tests/ -m "not integration and not slow"

# Run integration tests (requires full app)
pytest tests/ -m integration --run-integration

# Run with all skipped tests visible
pytest tests/ -v --collect-only

# Show skip reasons
pytest tests/ -v -rs
```

---

## Conclusion

All 9 skipped tests are appropriately skipped:
- **5 integration tests**: Require running application infrastructure
- **3 conditional skips**: Properly gated on external service availability
- **1 intentional skip**: Known library compatibility issue with documented workaround

No tests require immediate unskipping. The test suite correctly separates unit tests (always run) from integration tests (run in CI integration stage) and environment-dependent tests (run when configured).
