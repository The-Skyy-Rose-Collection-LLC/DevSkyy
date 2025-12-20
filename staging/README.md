# Staging Test Suite - Phase 2 Features

Comprehensive testing suite for DevSkyy Phase 2 security features in staging environment.

## Overview

This test suite provides complete verification of all Phase 2 security and monitoring features:

- **Tiered Rate Limiting** - Multiple subscription tiers with different limits
- **Request Signing** - HMAC-based request authentication
- **Security Headers** - HTTP security headers (HSTS, CSP, etc.)
- **CORS Configuration** - Cross-Origin Resource Sharing policies
- **MFA (Multi-Factor Authentication)** - TOTP-based 2FA
- **Audit Logging** - Immutable audit trail
- **File Upload Security** - Validation and malware prevention
- **Secret Management** - AWS Secrets Manager / Vault integration
- **Prometheus Metrics** - Security event monitoring
- **Grafana Dashboards** - Visual monitoring
- **Alert Rules** - Automated alerting
- **Zero Trust mTLS** - Service-to-service encryption

## Test Files

### 1. Integration Tests (`tests/test_staging_integration.py`)

Complete end-to-end tests for all Phase 2 features with real HTTP requests.

**Test Classes:**
- `TestTieredRateLimitingStaging` - Rate limiting with different tiers
- `TestRequestSigningStaging` - Request signature validation
- `TestSecurityHeadersStaging` - HTTP security headers
- `TestCORSStaging` - CORS configuration
- `TestMFAStaging` - MFA flow
- `TestAuditLoggingStaging` - Audit log entries
- `TestFileUploadStaging` - File upload validation
- `TestSecretRetrievalStaging` - Secrets management

**Run:**
```bash
# All integration tests
pytest tests/test_staging_integration.py -v

# Specific test class
pytest tests/test_staging_integration.py::TestTieredRateLimitingStaging -v

# Specific test
pytest tests/test_staging_integration.py::TestSecurityHeadersStaging::test_hsts_header_present -v
```

### 2. Monitoring Tests (`tests/test_staging_monitoring.py`)

Tests for Prometheus, Grafana, and alerting infrastructure.

**Test Classes:**
- `TestPrometheusMetrics` - Metrics endpoint and data collection
- `TestAlertRulesFiring` - Alert rule configuration
- `TestGrafanaDashboard` - Dashboard loading
- `TestSlackIntegration` - Alert notifications
- `TestMetricsCollection` - Metric recording

**Run:**
```bash
# All monitoring tests
pytest tests/test_staging_monitoring.py -v

# Prometheus tests only
pytest tests/test_staging_monitoring.py::TestPrometheusMetrics -v
```

### 3. Security Feature Tests (`tests/test_staging_security_features.py`)

Comprehensive security testing including attack prevention.

**Test Classes:**
- `TestXSSPrevention` - XSS payload blocking
- `TestCSRFProtection` - CSRF token validation
- `TestSQLInjectionPrevention` - SQL injection blocking
- `TestRateLimitEnforcement` - Rate limit enforcement
- `TestRequestSigningValidation` - Invalid signature rejection
- `TestAuditTrail` - Complete audit trail

**Run:**
```bash
# All security tests
pytest tests/test_staging_security_features.py -v

# XSS prevention only
pytest tests/test_staging_security_features.py::TestXSSPrevention -v
```

### 4. Zero Trust mTLS Tests (`tests/test_staging_zero_trust.py`)

Tests for mutual TLS and Zero Trust architecture.

**Test Classes:**
- `TestmTLSConnections` - Service-to-service mTLS
- `TestCertificateRotation` - Certificate rotation
- `TestServiceIdentity` - Service identity validation
- `TestCertificateValidation` - Certificate validation
- `TestZeroTrustConfiguration` - Zero Trust policies

**Run:**
```bash
# All Zero Trust tests
pytest tests/test_staging_zero_trust.py -v

# mTLS tests only
pytest tests/test_staging_zero_trust.py::TestmTLSConnections -v
```

## Shell Scripts

### Smoke Tests (`staging/smoke_tests.sh`)

Quick health checks for basic functionality.

**Tests:**
- API health endpoint
- Metrics endpoint
- Authenticated endpoint access
- Rate limiting
- Security headers
- CORS headers
- Request signing
- File upload validation
- Monitoring stack availability

**Usage:**
```bash
# Run smoke tests
./staging/smoke_tests.sh

# Verbose output
./staging/smoke_tests.sh --verbose

# Custom URL
./staging/smoke_tests.sh --url https://staging.devskyy.com

# With API key
STAGING_URL=https://staging.devskyy.com API_KEY=your-key ./staging/smoke_tests.sh
```

**Example Output:**
```
========================================
DevSkyy Staging Smoke Tests
========================================
Testing against: http://localhost:8000

[TEST] Testing health endpoint...
[PASS] Health endpoint returns 200 OK
[TEST] Testing metrics endpoint...
[PASS] Metrics endpoint returns Prometheus format
...

========================================
Test Summary
========================================
Passed:  7
Failed:  0
Skipped: 2

Total tests: 9
All tests passed!
```

### Feature Verification (`staging/feature_verification.sh`)

Comprehensive feature verification with detailed reporting.

**Features Verified:**
- Tiered rate limiting (4 checks)
- Request signing (3 checks)
- Security headers (6 checks)
- CORS configuration (2 checks)
- Prometheus metrics (5 checks)
- Monitoring stack (2 checks)
- Audit logging (2 checks)
- File upload security (2 checks)

**Usage:**
```bash
# Run verification
./staging/feature_verification.sh

# Generate report
./staging/feature_verification.sh --report verification-report.txt

# Custom URLs
STAGING_URL=https://staging.devskyy.com \
PROMETHEUS_URL=https://prometheus.devskyy.com \
GRAFANA_URL=https://grafana.devskyy.com \
./staging/feature_verification.sh
```

**Example Output:**
```
========================================
DevSkyy Phase 2 Feature Verification
========================================
Testing against: http://localhost:8000

[FEATURE] Tiered Rate Limiting
  ⊢ Checking: Rate limiting headers present
  ✓ Rate limiting headers found
  ⊢ Checking: Rate limiting enforcement
  ✓ Rate limiting triggered after excessive requests
  ...

DevSkyy Phase 2 Feature Verification Report
============================================

Date: 2025-12-19 23:45:00
Environment: http://localhost:8000

Summary:
--------
Features Verified: 6
Features Partial:  2
Features Failed:   0

Feature Details:
----------------
Tiered Rate Limiting: [PASS] 4/4 checks passed
Request Signing: [PASS] 3/3 checks passed
Security Headers: [PASS] 6/6 headers present
...

Feature verification complete!
```

## Environment Configuration

### Required Environment Variables

```bash
# Staging environment
export STAGING_BASE_URL="https://staging.devskyy.com"
export STAGING_API_KEY="your-api-key-here"

# Monitoring stack
export PROMETHEUS_URL="https://prometheus.devskyy.com"
export GRAFANA_URL="https://grafana.devskyy.com"
export GRAFANA_API_KEY="your-grafana-key"

# Optional
export REDIS_URL="redis://localhost:6379/0"
export CERT_DIR="/path/to/certificates"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### Test Configuration File

Create `.env.staging` in project root:

```bash
# Staging Test Configuration
STAGING_BASE_URL=https://staging.devskyy.com
STAGING_API_KEY=sk_staging_xxxxx
PROMETHEUS_URL=https://prometheus-staging.devskyy.com
GRAFANA_URL=https://grafana-staging.devskyy.com
GRAFANA_API_KEY=your-grafana-api-key
REDIS_URL=redis://staging-redis:6379/0
CERT_DIR=/tmp/staging-certs
```

Load before running tests:
```bash
source .env.staging
pytest tests/test_staging_*.py -v
```

## Running Tests

### Complete Test Suite

Run all staging tests:
```bash
# All tests with coverage
pytest tests/test_staging_*.py -v --cov=security --cov-report=html

# All tests with detailed output
pytest tests/test_staging_*.py -vv

# All tests in parallel (faster)
pytest tests/test_staging_*.py -v -n auto
```

### Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Staging Tests

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  test-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run smoke tests
        run: ./staging/smoke_tests.sh
        env:
          STAGING_URL: ${{ secrets.STAGING_URL }}
          API_KEY: ${{ secrets.STAGING_API_KEY }}

      - name: Run integration tests
        run: pytest tests/test_staging_integration.py -v
        env:
          STAGING_BASE_URL: ${{ secrets.STAGING_URL }}
          STAGING_API_KEY: ${{ secrets.STAGING_API_KEY }}

      - name: Feature verification
        run: ./staging/feature_verification.sh --report report.txt
        env:
          STAGING_URL: ${{ secrets.STAGING_URL }}
          PROMETHEUS_URL: ${{ secrets.PROMETHEUS_URL }}
          GRAFANA_URL: ${{ secrets.GRAFANA_URL }}

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: verification-report
          path: report.txt
```

## Test Coverage

Expected coverage for Phase 2 features:

| Feature | Coverage | Tests |
|---------|----------|-------|
| Tiered Rate Limiting | 95% | 8 tests |
| Request Signing | 90% | 6 tests |
| Security Headers | 100% | 7 tests |
| CORS | 85% | 3 tests |
| MFA | 80% | 3 tests |
| Audit Logging | 90% | 6 tests |
| File Upload | 90% | 4 tests |
| Secrets Management | 95% | 4 tests |
| Prometheus Metrics | 100% | 8 tests |
| Zero Trust mTLS | 85% | 12 tests |

## Troubleshooting

### Common Issues

**1. Connection Refused**
```
Error: Connection refused to http://localhost:8000
```
**Solution:** Ensure staging server is running:
```bash
# Start staging server
python main_enterprise.py
```

**2. Rate Limiting Tests Failing**
```
AssertionError: Rate limiter should block excessive requests
```
**Solution:** May need to adjust test timing or increase request count:
```python
# In test file, increase range
for i in range(30):  # Instead of 15
```

**3. Prometheus Not Accessible**
```
[SKIP] Prometheus not accessible in staging environment
```
**Solution:** Ensure Prometheus is running or set correct URL:
```bash
export PROMETHEUS_URL=http://your-prometheus:9090
```

**4. Certificate Issues (mTLS tests)**
```
FileNotFoundError: Certificate or key not found
```
**Solution:** Initialize certificates first:
```bash
python -c "from security.certificate_authority import SelfSignedCA; from pathlib import Path; ca = SelfSignedCA(Path('/tmp/devskyy-certs')); ca.initialize_ca()"
```

### Debug Mode

Enable detailed logging:
```bash
# Set log level
export LOG_LEVEL=DEBUG

# Run tests with verbose output
pytest tests/test_staging_integration.py -vv -s

# Run scripts with verbose mode
./staging/smoke_tests.sh --verbose
```

## Best Practices

### 1. Run Smoke Tests First
Always run smoke tests before full test suite:
```bash
./staging/smoke_tests.sh && pytest tests/test_staging_*.py
```

### 2. Use Markers for Test Selection
Run only specific types of tests:
```bash
# Only integration tests
pytest -m integration -v

# Only slow tests
pytest -m slow -v
```

### 3. Clean Up Between Runs
```bash
# Clear test cache
pytest --cache-clear

# Remove temporary files
rm -rf /tmp/devskyy-certs/* /tmp/uploads/*
```

### 4. Verify All Features Before Deployment
```bash
# Complete verification workflow
./staging/smoke_tests.sh && \
./staging/feature_verification.sh --report pre-deploy-report.txt && \
pytest tests/test_staging_*.py -v --cov=security
```

## Metrics and Reporting

### Test Results Dashboard

Monitor test results in Grafana:
- Panel: Staging Test Pass Rate
- Metric: `test_pass_rate{environment="staging"}`
- Alert: `test_pass_rate < 0.95`

### Automated Reports

Generate comprehensive reports:
```bash
# HTML report
pytest tests/test_staging_*.py --html=report.html --self-contained-html

# JUnit XML (for CI)
pytest tests/test_staging_*.py --junitxml=junit.xml

# Feature verification report
./staging/feature_verification.sh --report verification-$(date +%Y%m%d).txt
```

## Next Steps

After successful staging tests:

1. Review all test results and reports
2. Fix any failing or partial features
3. Update documentation for any gaps
4. Schedule production deployment
5. Prepare rollback plan
6. Run production smoke tests post-deployment

## Additional Documentation

- **Monitoring Tests**: See `README_MONITORING.md` for detailed monitoring verification suite
- **Security Architecture**: See `/docs/security/` for security implementation details
- **API Documentation**: See `/docs/api/` for API endpoint documentation

## Support

For issues or questions:
- Review test output and logs
- Check environment configuration
- Verify all dependencies installed
- Ensure staging environment is properly configured
- Contact DevOps team for infrastructure issues

## Version History

- **v1.0.0** (2025-12-19) - Initial comprehensive test suite
  - 4 test files with 50+ tests
  - 2 shell scripts for automation
  - Complete documentation

---

**Ready for Staging Deployment** ✓
