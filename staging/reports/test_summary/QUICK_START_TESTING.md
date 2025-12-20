# Quick Start - Staging Test Execution

**Estimated Time:** 3-4 hours
**Prerequisites:** Docker, PostgreSQL, Redis, AWS credentials, API keys

---

## 1. Environment Setup (10 minutes)

```bash
# Navigate to staging directory
cd /Users/coreyfoster/DevSkyy/staging

# Create environment file
cp .env.example .env.staging

# Edit .env.staging - CHANGE ALL DEFAULTS
# Required variables:
# - POSTGRES_PASSWORD
# - REDIS_PASSWORD
# - JWT_SECRET_KEY
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# - GOOGLE_API_KEY
# - AWS_ACCESS_KEY_ID
# - AWS_SECRET_ACCESS_KEY
vim .env.staging

# Create Docker Compose file (if not exists)
# File: docker-compose.staging.yml
# Must include: PostgreSQL, Redis, Prometheus, Grafana, AlertManager
```

---

## 2. Pre-Deployment Checks (5 minutes)

```bash
# Run pre-deployment checklist
./pre_deployment_checklist.sh

# Expected output:
# ✓ Git working directory clean
# ✓ Docker installed
# ✓ Ports available
# ✓ Disk space sufficient
# ✓ Environment file valid
```

---

## 3. Deploy to Staging (30 minutes)

```bash
# Execute deployment
./deploy_to_staging.sh

# What it does:
# 1. Creates backup
# 2. Builds Docker images
# 3. Starts services
# 4. Waits for health checks (up to 5 min)
# 5. Runs smoke tests
# 6. Auto-rollback on failure

# Expected output:
# ✓ Backup created
# ✓ Services started
# ✓ Health checks passed
# ✓ Smoke tests passed
# ✓ Deployment successful
```

---

## 4. Verify Deployment (10 minutes)

```bash
# Comprehensive health check
./healthcheck.sh --verbose

# Feature verification
./feature_verification.sh

# Full deployment verification
./verify-deployment.sh

# Expected: All checks pass
```

---

## 5. Run Security Tests (30 minutes)

```bash
# Navigate to project root
cd /Users/coreyfoster/DevSkyy

# Activate virtual environment
source .venv/bin/activate

# Run core security tests
pytest tests/test_security.py -v

# Run staging security features
pytest tests/test_staging_security_features.py -v

# Run staging integration tests
pytest tests/test_staging_integration.py -v

# Expected: All 79+ tests pass
```

---

## 6. Run Zero Trust Tests (15 minutes)

```bash
# Run zero trust tests
pytest tests/test_zero_trust.py -v

# Run staging zero trust tests
pytest tests/test_staging_zero_trust.py -v

# Expected: All mTLS tests pass
```

---

## 7. Verify Monitoring (15 minutes)

```bash
# Return to staging directory
cd /Users/coreyfoster/DevSkyy/staging

# Run complete monitoring test suite
./run_all_monitoring_tests.sh

# What it checks:
# - Prometheus healthy
# - Grafana accessible
# - AlertManager operational
# - All exporters connected
# - Security metrics available
# - Dashboards functional

# Expected: All monitoring services operational
```

---

## 8. Test Alert System (10 minutes)

```bash
# Trigger test alerts
./verify_alerts.sh

# What it does:
# 1. Simulates security event
# 2. Waits for Prometheus alert
# 3. Verifies Slack notification
# 4. Measures response time

# Expected: Alert fires and notification received
```

---

## 9. Run DAST Scan (60-90 minutes)

```bash
# Run dynamic application security testing
./run_dast_scan.sh

# What it does:
# 1. OWASP ZAP scan (active + passive)
# 2. Nuclei scan (template-based)
# 3. Vulnerability triage
# 4. Baseline comparison
# 5. Report generation

# Reports generated in: reports/dast/
# - zap_report_*.json (raw ZAP findings)
# - nuclei_report_*.json (raw Nuclei findings)
# - combined_vulnerability_report_*.json (unified)
# - vulnerability_summary_*.txt (human-readable)

# Expected: Zero critical/high blockers
```

---

## 10. Performance Baseline (30 minutes)

```bash
# Collect 30-minute performance baseline
./monitoring_performance_baseline.sh 30

# What it collects:
# - API request latency (p50, p95, p99)
# - Rate limiting performance
# - Memory/CPU usage
# - Error rates

# Report: monitoring_logs/performance_baseline_*.txt

# Expected latency:
# - p50: <100ms
# - p95: <300ms
# - p99: <500ms
```

---

## 11. Collect Logs (5 minutes)

```bash
# Collect all logs
./logs_collection.sh

# Logs compressed to: collected_logs/
# Includes:
# - Container logs
# - Application logs
# - Database logs
# - Monitoring logs

# Final health check (JSON format)
./healthcheck.sh --json > reports/test_summary/final_health_check.json
```

---

## 12. Review Results

### Check Test Logs

```bash
# View deployment log
cat logs/deployment.log

# View test results
cat logs/all_staging_tests.log

# View DAST summary
cat reports/dast/vulnerability_summary_*.txt | tail -50
```

### Check DAST Findings

```bash
# Count blockers
jq '.blockers | length' reports/dast/combined_vulnerability_report_*.json

# List critical issues
jq '.vulnerabilities[] | select(.severity == "critical")' reports/dast/combined_vulnerability_report_*.json

# View statistics
jq '.statistics' reports/dast/combined_vulnerability_report_*.json
```

### Check Monitoring

```bash
# View monitoring status
cat monitoring_logs/monitoring_verification_*.log | tail -50

# View security metrics
cat monitoring_logs/security_metrics_*.json | jq '.metrics'

# View Grafana dashboards
cat monitoring_logs/grafana_dashboards_*.json | jq '.dashboards'
```

---

## 13. Production Deployment Decision

### If All Tests Pass ✅

```bash
# All tests passed, ready for production
echo "✅ ALL TESTS PASSED"
echo "✅ Ready for production deployment"

# Next steps:
# 1. Schedule production deployment window
# 2. Brief operations team
# 3. Execute production deployment
# 4. Monitor post-deployment
```

### If Any Tests Fail ❌

```bash
# Tests failed, investigate
echo "❌ TESTS FAILED"
echo "❌ Review logs and remediate"

# Steps:
# 1. Review failed test logs
# 2. Identify root cause
# 3. Fix issues
# 4. Re-run tests
# 5. Do not proceed to production until all tests pass
```

---

## Emergency Rollback

If deployment fails or issues are discovered:

```bash
# Automatic rollback (if deploy failed)
# → deploy_to_staging.sh handles this automatically

# Manual rollback
./rollback.sh

# What it does:
# 1. Lists available backups
# 2. Prompts for confirmation
# 3. Stops current containers
# 4. Restores previous state
# 5. Restarts services
# 6. Verifies health

# Expected time: 10-15 minutes
```

---

## Troubleshooting

### Docker Issues

```bash
# Check Docker daemon
docker info

# Check running containers
docker ps

# Check container logs
docker logs <container_name>

# Restart Docker
sudo systemctl restart docker
```

### Database Issues

```bash
# Check PostgreSQL
docker exec -it postgres psql -U postgres -c "SELECT version();"

# Check Redis
docker exec -it redis redis-cli ping
```

### Monitoring Issues

```bash
# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health

# Check AlertManager
curl http://localhost:9093/-/healthy
```

### Test Failures

```bash
# Re-run specific test
pytest tests/test_security.py::TestRateLimiter -v

# Run with verbose output
pytest tests/test_security.py -vv

# Run with debug logging
pytest tests/test_security.py -v --log-cli-level=DEBUG
```

---

## Quick Reference

### Test Execution Summary

| Phase | Time | Command | Expected Result |
|-------|------|---------|-----------------|
| Setup | 10min | Edit .env.staging | All vars configured |
| Pre-check | 5min | ./pre_deployment_checklist.sh | All checks pass |
| Deploy | 30min | ./deploy_to_staging.sh | Deployment successful |
| Verify | 10min | ./healthcheck.sh --verbose | All services healthy |
| Security Tests | 30min | pytest tests/test_security.py -v | All 79+ tests pass |
| Zero Trust | 15min | pytest tests/test_zero_trust.py -v | All mTLS tests pass |
| Monitoring | 15min | ./run_all_monitoring_tests.sh | All services operational |
| Alerts | 10min | ./verify_alerts.sh | Alert fires, notification received |
| DAST | 90min | ./run_dast_scan.sh | Zero critical blockers |
| Performance | 30min | ./monitoring_performance_baseline.sh 30 | Latency within SLA |
| Logs | 5min | ./logs_collection.sh | All logs collected |

**Total Time:** 3-4 hours

---

## Success Criteria

### All Must Pass

- [ ] Pre-deployment checks: All pass
- [ ] Deployment: Successful
- [ ] Health checks: All services healthy
- [ ] Security tests: All 79+ tests pass
- [ ] Zero Trust tests: All mTLS tests pass
- [ ] Monitoring: All services operational
- [ ] Alerts: Alert system functional
- [ ] DAST: Zero critical/high blockers
- [ ] Performance: Latency within SLA (p95 <500ms)
- [ ] Error rate: <1%

### If All Pass

✅ **PROCEED TO PRODUCTION**

### If Any Fail

❌ **DO NOT PROCEED TO PRODUCTION**

Investigate, remediate, and re-test.

---

## Reports Generated

After completion, you will have:

1. **STAGING_TEST_REPORT.md** (35KB)
   - Comprehensive test documentation
   - Task-by-task status
   - Production readiness assessment

2. **TEST_STATISTICS.json**
   - Machine-readable statistics
   - Test coverage metrics
   - Expected results

3. **STAGING_VERIFICATION_COMPLETE.txt**
   - Executive summary
   - Quick reference
   - Next steps

4. **DAST Reports** (reports/dast/)
   - Vulnerability findings
   - Baseline comparison
   - Remediation recommendations

5. **Monitoring Logs** (monitoring_logs/)
   - Service health status
   - Security metrics
   - Dashboard verification

6. **Test Logs** (logs/)
   - Deployment log
   - Test results
   - Health check results

---

## Support

- **Main Documentation:** `/Users/coreyfoster/DevSkyy/staging/README.md`
- **Deployment Runbook:** `/Users/coreyfoster/DevSkyy/staging/DEPLOYMENT_RUNBOOK.md`
- **DAST Guide:** `/Users/coreyfoster/DevSkyy/staging/DAST_SCANNING.md`
- **Monitoring Guide:** `/Users/coreyfoster/DevSkyy/staging/README_MONITORING.md`

---

**Report Generated:** 2025-12-20 02:42:00 UTC
**Version:** 1.0.0
**Location:** `/Users/coreyfoster/DevSkyy/staging/reports/test_summary/`
