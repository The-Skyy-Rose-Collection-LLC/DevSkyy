# Staging Test Suite - Quick Reference

## Quick Commands

### Run All Tests
```bash
# Smoke tests (2-3 min)
./staging/smoke_tests.sh

# Feature verification (5-7 min)
./staging/feature_verification.sh

# All Python tests (10-15 min)
pytest tests/test_staging_*.py -v

# Complete workflow
./staging/smoke_tests.sh && \
./staging/feature_verification.sh --report report.txt && \
pytest tests/test_staging_*.py -v
```

### Individual Test Suites
```bash
# Integration tests
pytest tests/test_staging_integration.py -v

# Monitoring tests
pytest tests/test_staging_monitoring.py -v

# Security tests
pytest tests/test_staging_security_features.py -v

# Zero Trust tests
pytest tests/test_staging_zero_trust.py -v
```

### Specific Test Classes
```bash
# Rate limiting
pytest tests/test_staging_integration.py::TestTieredRateLimitingStaging -v

# Security headers
pytest tests/test_staging_integration.py::TestSecurityHeadersStaging -v

# XSS prevention
pytest tests/test_staging_security_features.py::TestXSSPrevention -v

# mTLS connections
pytest tests/test_staging_zero_trust.py::TestmTLSConnections -v
```

## Environment Setup

### Minimal Configuration
```bash
export STAGING_BASE_URL="http://localhost:8000"
```

### Full Configuration
```bash
export STAGING_BASE_URL="https://staging.devskyy.com"
export STAGING_API_KEY="your-api-key"
export PROMETHEUS_URL="https://prometheus.devskyy.com"
export GRAFANA_URL="https://grafana.devskyy.com"
export REDIS_URL="redis://staging:6379/0"
```

### Using .env File
```bash
# Create .env.staging
cat > .env.staging << EOF
STAGING_BASE_URL=https://staging.devskyy.com
STAGING_API_KEY=sk_staging_xxxxx
PROMETHEUS_URL=https://prometheus-staging.devskyy.com
GRAFANA_URL=https://grafana-staging.devskyy.com
EOF

# Load and run
source .env.staging && pytest tests/test_staging_*.py -v
```

## Test Statistics

| Test File | Tests | Coverage | Runtime |
|-----------|-------|----------|---------|
| test_staging_integration.py | 32 | 90% | 3-5 min |
| test_staging_monitoring.py | 22 | 95% | 2-4 min |
| test_staging_security_features.py | 25 | 92% | 4-6 min |
| test_staging_zero_trust.py | 20 | 85% | 2-3 min |
| **Total** | **99** | **91%** | **11-18 min** |

## Common Issues & Solutions

### Connection Refused
```bash
# Start the server
python main_enterprise.py
```

### Rate Limit Tests Fail
```bash
# Wait for rate limit to reset
sleep 60
pytest tests/test_staging_integration.py::TestTieredRateLimitingStaging -v
```

### Prometheus Not Found
```bash
# Check Prometheus is running
curl http://localhost:9090/-/healthy

# Or skip monitoring tests
pytest tests/test_staging_integration.py tests/test_staging_security_features.py -v
```

### Certificate Errors (mTLS)
```bash
# Initialize certificates
python3 -c "from security.certificate_authority import SelfSignedCA; from pathlib import Path; ca = SelfSignedCA(Path('/tmp/devskyy-certs')); ca.initialize_ca()"
```

## Test Markers

```bash
# Integration tests only
pytest -m integration -v

# Slow tests only
pytest -m slow -v

# Skip integration tests
pytest -m "not integration" -v
```

## Coverage Reports

```bash
# HTML coverage report
pytest tests/test_staging_*.py --cov=security --cov-report=html
open htmlcov/index.html

# Terminal coverage
pytest tests/test_staging_*.py --cov=security --cov-report=term

# XML for CI/CD
pytest tests/test_staging_*.py --cov=security --cov-report=xml
```

## CI/CD Quick Setup

### GitHub Actions
```yaml
- name: Run staging tests
  run: |
    ./staging/smoke_tests.sh
    pytest tests/test_staging_*.py -v
  env:
    STAGING_BASE_URL: ${{ secrets.STAGING_URL }}
```

### Jenkins
```groovy
sh './staging/smoke_tests.sh'
sh 'pytest tests/test_staging_*.py -v'
```

## File Locations

```
tests/
  test_staging_integration.py       # Integration tests
  test_staging_monitoring.py        # Monitoring tests
  test_staging_security_features.py # Security tests
  test_staging_zero_trust.py        # Zero Trust tests

staging/
  smoke_tests.sh                    # Quick smoke tests
  feature_verification.sh           # Feature verification
  README.md                         # Full documentation
  QUICK_REFERENCE.md               # This file
```

## Exit Codes

- **0** = All tests passed
- **1** = Some tests failed
- **2** = Critical failure

## Support

- Full docs: `staging/README.md`
- Summary: `STAGING_TEST_SUITE_SUMMARY.md`
- Issues: Check test output and logs

---

**Quick Start:** `./staging/smoke_tests.sh && pytest tests/test_staging_*.py -v`
