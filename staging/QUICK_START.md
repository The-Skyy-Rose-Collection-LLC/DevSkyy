# Quick Start Guide - Monitoring Verification Suite

## 5-Minute Setup

### Step 1: Prerequisites Check

```bash
# Navigate to staging directory
cd /Users/coreyfoster/DevSkyy/staging

# Check required tools
command -v curl >/dev/null 2>&1 || echo "❌ Install curl"
command -v jq >/dev/null 2>&1 || echo "❌ Install jq: brew install jq"
command -v python3 >/dev/null 2>&1 || echo "❌ Install python3"
command -v bc >/dev/null 2>&1 || echo "❌ Install bc: brew install bc"
```

### Step 2: Install Python Dependencies

```bash
pip3 install requests
```

### Step 3: Verify Monitoring Stack is Running

```bash
# Check Prometheus
curl -f http://localhost:9090/-/healthy && echo "✓ Prometheus is running"

# Check Grafana
curl -f http://localhost:3000/api/health && echo "✓ Grafana is running"

# Check AlertManager
curl -f http://localhost:9093/-/healthy && echo "✓ AlertManager is running"
```

If any service is not running:
```bash
# Start the monitoring stack with Docker
cd /Users/coreyfoster/DevSkyy/docker
docker-compose up -d prometheus grafana alertmanager
```

### Step 4: Run Quick Verification (2-3 minutes)

```bash
cd /Users/coreyfoster/DevSkyy/staging

# Run monitoring health check
./monitoring_verification.sh
```

**Expected Output:**
- ✓ Prometheus is healthy
- ✓ Grafana is healthy
- ✓ AlertManager is healthy
- ✓ All exporters connected
- ✓ All scrape targets responding

### Step 5: Run Security Metrics Check (30 seconds)

```bash
python3 verify_security_metrics.py
```

**Expected Output:**
- Security metrics collected
- Threat score calculated
- Report generated

### Step 6: Run Complete Test Suite (10-15 minutes)

```bash
./run_all_monitoring_tests.sh
```

This runs:
1. Monitoring health verification ✓
2. Security metrics verification ✓
3. Grafana dashboard verification ✓
4. Alert system verification ✓

**Note:** Performance baseline collection is skipped in quick mode (takes 30 minutes).

---

## Common Scenarios

### Scenario 1: Quick Health Check (Before Deployment)

```bash
./monitoring_verification.sh && \
python3 verify_security_metrics.py && \
echo "✓ All systems operational"
```

### Scenario 2: Alert System Testing

```bash
# This will generate test security events and verify alerts fire
./verify_alerts.sh

# Check that alerts fired correctly in the report
cat monitoring_logs/alert_verification_report_*.txt | tail -20
```

### Scenario 3: Dashboard Verification

```bash
# Verify all Grafana dashboards are showing data
python3 verify_grafana_dashboards.py

# Check the report
cat monitoring_logs/grafana_verification_report_*.txt | tail -30
```

### Scenario 4: Full Performance Baseline (Run Overnight)

```bash
# Start 30-minute baseline collection
nohup ./monitoring_performance_baseline.sh 30 > baseline.log 2>&1 &

# Check progress
tail -f baseline.log

# Or run a shorter 5-minute test
./monitoring_performance_baseline.sh 5
```

---

## Understanding the Output

### Exit Codes

```bash
# Run a test and check result
./monitoring_verification.sh
echo $?  # 0 = success, 1 = failure
```

### Report Locations

All reports are saved in `monitoring_logs/`:

```bash
# View latest monitoring report
ls -t monitoring_logs/monitoring_verification_report_*.txt | head -1 | xargs cat

# View latest JSON report
ls -t monitoring_logs/monitoring_verification_report_*.json | head -1 | xargs jq .

# View all reports
ls -la monitoring_logs/
```

### Quick Report Summary

```bash
# Get summary from master report
./run_all_monitoring_tests.sh 2>&1 | tail -30
```

---

## Troubleshooting

### Issue: "Cannot connect to Prometheus"

```bash
# Check if Prometheus is running
docker ps | grep prometheus

# If not running, start it
cd /Users/coreyfoster/DevSkyy/docker
docker-compose up -d prometheus

# Check logs
docker logs devskyy-prometheus
```

### Issue: "jq: command not found"

```bash
# Install jq on macOS
brew install jq

# Or on Linux
sudo apt-get install jq
```

### Issue: "Python module 'requests' not found"

```bash
pip3 install requests
```

### Issue: "Permission denied" when running scripts

```bash
chmod +x *.sh
chmod +x *.py
```

### Issue: No metrics data

```bash
# Check if Prometheus is scraping
curl 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | {job: .scrapePool, health: .health}'

# Check specific metric exists
curl 'http://localhost:9090/api/v1/query?query=up' | jq .
```

---

## Integration with CI/CD

### Add to Your Pipeline

```yaml
# Add to .github/workflows/monitoring-check.yml
- name: Verify Monitoring
  run: |
    cd staging
    ./run_all_monitoring_tests.sh
```

### Daily Automated Check

```bash
# Add to crontab for daily 6 AM check
0 6 * * * cd /Users/coreyfoster/DevSkyy/staging && ./run_all_monitoring_tests.sh
```

---

## Next Steps

1. ✅ Run quick verification to ensure everything works
2. 📊 Review the generated reports in `monitoring_logs/`
3. 🔔 Test alerts by running `./verify_alerts.sh`
4. 📈 Collect performance baseline with `./monitoring_performance_baseline.sh`
5. 📝 Create a formal report using `MONITORING_REPORT_TEMPLATE.md`
6. 🔄 Schedule regular automated runs
7. 🎯 Set up alerts for verification failures

---

## Cheat Sheet

```bash
# Quick health check (2 min)
./monitoring_verification.sh

# Security metrics (30 sec)
python3 verify_security_metrics.py

# Full test suite (10-15 min)
./run_all_monitoring_tests.sh

# Alert testing (5-10 min)
./verify_alerts.sh

# Dashboard check (1-2 min)
python3 verify_grafana_dashboards.py

# Performance baseline (30 min)
./monitoring_performance_baseline.sh

# View latest report
ls -t monitoring_logs/*.txt | head -1 | xargs less

# View JSON report
ls -t monitoring_logs/*.json | head -1 | xargs jq .

# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana
curl http://localhost:3000/api/health

# Check AlertManager
curl http://localhost:9093/-/healthy

# View active alerts
curl 'http://localhost:9090/api/v1/alerts' | jq '.data.alerts[] | {name: .labels.alertname, state: .state}'
```

---

## Getting Help

If you encounter issues:

1. Check the main `README.md` for detailed documentation
2. Review logs in `monitoring_logs/`
3. Check Prometheus/Grafana/AlertManager logs:
   ```bash
   docker logs devskyy-prometheus
   docker logs devskyy-grafana
   docker logs devskyy-alertmanager
   ```
4. Verify monitoring stack is running:
   ```bash
   docker-compose ps
   ```

---

**Ready to start? Run your first test:**

```bash
cd /Users/coreyfoster/DevSkyy/staging
./monitoring_verification.sh
```

Good luck! 🚀
