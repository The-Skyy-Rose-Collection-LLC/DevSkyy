# DevSkyy Staging Monitoring Verification Suite

Comprehensive monitoring verification and testing suite for DevSkyy's staging environment.

## Overview

This suite provides automated verification of all monitoring components including Prometheus, Grafana, AlertManager, security metrics, alert systems, and performance baselines.

## Components

### 1. Monitoring Verification (`monitoring_verification.sh`)

Verifies core monitoring infrastructure health:
- Prometheus health and readiness
- Grafana connectivity and status
- AlertManager availability
- Exporter connectivity (postgres, redis, node, cadvisor)
- Scrape target verification
- Alert rules validation
- Metrics collection verification

**Usage:**
```bash
./monitoring_verification.sh
```

**Duration:** ~2-3 minutes

**Output:**
- Text report: `monitoring_logs/monitoring_verification_report_[timestamp].txt`
- JSON report: `monitoring_logs/monitoring_verification_report_[timestamp].json`

### 2. Alert Verification (`verify_alerts.sh`)

Tests alert firing and notification delivery:
- Generates test security events (failed logins, rate limit violations, SQL injection)
- Monitors for alert activation in Prometheus
- Verifies AlertManager receives alerts
- Checks notification delivery (Slack)
- Measures alert response times

**Usage:**
```bash
./verify_alerts.sh
```

**Duration:** ~5-10 minutes (includes wait time for alerts to fire)

**Output:**
- Text report: `monitoring_logs/alert_verification_report_[timestamp].txt`
- JSON report: `monitoring_logs/alert_verification_report_[timestamp].json`
- Alert details: `monitoring_logs/alert_[alert_name]_details.json`
- Response times: `monitoring_logs/alert_[alert_name]_response_time.txt`

### 3. Security Metrics Verification (`verify_security_metrics.py`)

Queries and analyzes security metrics from Prometheus:
- Failed login attempts
- Rate limit violations
- Request signing failures
- Threat score
- Active sessions
- Blocked IPs
- SQL injection attempts
- Unauthorized access attempts

**Usage:**
```bash
python3 verify_security_metrics.py

# With custom parameters
PROMETHEUS_URL=http://localhost:9090 METRICS_DURATION_MINUTES=30 python3 verify_security_metrics.py
```

**Duration:** ~30 seconds

**Output:**
- Text report: `monitoring_logs/security_metrics_report_[timestamp].txt`
- JSON report: `monitoring_logs/security_metrics_report_[timestamp].json`

**Exit Codes:**
- 0: All metrics OK
- 1: Some metrics in WARNING state
- 2: Some metrics in CRITICAL state

### 4. Grafana Dashboard Verification (`verify_grafana_dashboards.py`)

Verifies Grafana dashboards are operational:
- Datasource connectivity testing
- Dashboard discovery
- Panel data verification
- Query validation
- Dashboard health assessment

**Usage:**
```bash
python3 verify_grafana_dashboards.py

# With custom credentials
GRAFANA_URL=http://localhost:3000 GRAFANA_USERNAME=admin GRAFANA_PASSWORD=admin python3 verify_grafana_dashboards.py
```

**Duration:** ~1-2 minutes

**Output:**
- Text report: `monitoring_logs/grafana_verification_report_[timestamp].txt`
- JSON report: `monitoring_logs/grafana_verification_report_[timestamp].json`

**Exit Codes:**
- 0: All dashboards operational
- 1: Some dashboards have warnings
- 2: Critical issues with dashboards or datasources

### 5. Performance Baseline Collection (`monitoring_performance_baseline.sh`)

Collects performance metrics over time to establish baseline:
- API request latency (P50, P95, P99)
- Rate limiting performance
- Memory usage
- CPU usage
- Error rates
- Statistical analysis (mean, min, max, std dev)

**Usage:**
```bash
# Default 30 minutes
./monitoring_performance_baseline.sh

# Custom duration (in minutes)
./monitoring_performance_baseline.sh 60
```

**Duration:** 30 minutes (default) or specified duration

**Output:**
- Text report: `monitoring_logs/performance_baseline_report_[timestamp].txt`
- JSON report: `monitoring_logs/performance_baseline_report_[timestamp].json`
- Raw data CSV: `monitoring_logs/metrics_data_[timestamp].csv`

### 6. Master Test Runner (`run_all_monitoring_tests.sh`)

Runs all verification tests in sequence (except performance baseline):
- Automatically runs all quick verification tests
- Generates master report with combined results
- Provides pass/fail summary
- Skips long-running performance baseline (run separately)

**Usage:**
```bash
./run_all_monitoring_tests.sh
```

**Duration:** ~10-15 minutes

**Output:**
- Master text report: `monitoring_logs/master_monitoring_report_[timestamp].txt`
- Master JSON report: `monitoring_logs/master_monitoring_report_[timestamp].json`
- Individual test reports in `monitoring_logs/`

## Quick Start

### Prerequisites

1. **Required Tools:**
   ```bash
   # Check if tools are installed
   command -v curl && echo "curl OK"
   command -v jq && echo "jq OK"
   command -v python3 && echo "python3 OK"
   command -v bc && echo "bc OK"
   ```

2. **Install Missing Tools (macOS):**
   ```bash
   brew install jq bc
   ```

3. **Python Dependencies:**
   ```bash
   pip3 install requests
   ```

4. **Make Scripts Executable:**
   ```bash
   chmod +x *.sh
   ```

### Running All Tests

```bash
# Run complete test suite (except performance baseline)
./run_all_monitoring_tests.sh

# Or run tests individually:
./monitoring_verification.sh
python3 verify_security_metrics.py
python3 verify_grafana_dashboards.py
./verify_alerts.sh

# Run performance baseline separately (takes 30 minutes)
./monitoring_performance_baseline.sh
```

## Environment Variables

Configure these environment variables to customize behavior:

```bash
# Prometheus URL (default: http://localhost:9090)
export PROMETHEUS_URL="http://localhost:9090"

# Grafana URL (default: http://localhost:3000)
export GRAFANA_URL="http://localhost:3000"
export GRAFANA_USERNAME="admin"
export GRAFANA_PASSWORD="admin"

# AlertManager URL (default: http://localhost:9093)
export ALERTMANAGER_URL="http://localhost:9093"

# API URL for alert testing (default: http://localhost:8000)
export API_URL="http://localhost:8000"

# Slack webhook for notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Metrics duration for security metrics (default: 15 minutes)
export METRICS_DURATION_MINUTES="15"
```

## Output Files

All reports are saved to `monitoring_logs/` directory:

```
monitoring_logs/
├── monitoring_verification_report_[timestamp].txt
├── monitoring_verification_report_[timestamp].json
├── security_metrics_report_[timestamp].txt
├── security_metrics_report_[timestamp].json
├── grafana_verification_report_[timestamp].txt
├── grafana_verification_report_[timestamp].json
├── alert_verification_report_[timestamp].txt
├── alert_verification_report_[timestamp].json
├── performance_baseline_report_[timestamp].txt
├── performance_baseline_report_[timestamp].json
├── metrics_data_[timestamp].csv
├── master_monitoring_report_[timestamp].txt
└── master_monitoring_report_[timestamp].json
```

## Report Template

A comprehensive monitoring report template is provided in `MONITORING_REPORT_TEMPLATE.md`. Use this template to create formal monitoring verification reports.

## Exit Codes

All scripts use standard exit codes:

- **0:** Success - all checks passed
- **1:** Warning/Failure - some checks failed or warnings detected
- **2:** Critical - critical issues detected
- **130:** Interrupted by user (Ctrl+C)

## Troubleshooting

### Scripts Won't Execute

```bash
# Make executable
chmod +x *.sh
```

### Cannot Connect to Prometheus

```bash
# Check if Prometheus is running
curl http://localhost:9090/-/healthy

# Check docker containers
docker ps | grep prometheus

# Check logs
docker logs devskyy-prometheus
```

### Python Scripts Fail

```bash
# Install required packages
pip3 install requests

# Check Python version (3.7+ required)
python3 --version
```

### No Data in Metrics

```bash
# Verify Prometheus is scraping targets
curl 'http://localhost:9090/api/v1/targets' | jq .

# Check if metrics exist
curl 'http://localhost:9090/api/v1/query?query=up' | jq .
```

### Alerts Not Firing

```bash
# Check alert rules are loaded
curl 'http://localhost:9090/api/v1/rules' | jq .

# Check AlertManager status
curl http://localhost:9093/-/healthy
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Monitoring Verification

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  verify-monitoring:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y jq bc
          pip3 install requests

      - name: Run monitoring verification
        run: |
          cd staging
          chmod +x *.sh
          ./run_all_monitoring_tests.sh

      - name: Upload reports
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: monitoring-reports
          path: staging/monitoring_logs/
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any

    triggers {
        cron('H */6 * * *')  // Every 6 hours
    }

    stages {
        stage('Setup') {
            steps {
                sh 'cd staging && chmod +x *.sh'
            }
        }

        stage('Verify Monitoring') {
            steps {
                sh 'cd staging && ./run_all_monitoring_tests.sh'
            }
        }

        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'staging/monitoring_logs/**/*', allowEmptyArchive: false
            }
        }
    }

    post {
        failure {
            emailext (
                subject: "Monitoring Verification Failed",
                body: "See attached reports",
                attachmentsPattern: 'staging/monitoring_logs/*.txt'
            )
        }
    }
}
```

## Best Practices

1. **Regular Execution:** Run the full test suite at least once per day
2. **Before Deployment:** Always run verification before deploying to production
3. **After Changes:** Run after any monitoring configuration changes
4. **Performance Baseline:** Collect new baseline after major infrastructure changes
5. **Alert Testing:** Test alerts weekly to ensure notification channels work
6. **Report Review:** Review reports with team weekly
7. **Threshold Tuning:** Adjust alert thresholds based on baseline data

## Advanced Usage

### Custom Metric Queries

Modify `verify_security_metrics.py` to add custom metrics:

```python
def get_custom_metric(self, duration_minutes: int = 15) -> SecurityMetric:
    query = f"your_custom_metric[{duration_minutes}m]"
    result = self.client.query(query)
    # Process result...
```

### Custom Alert Tests

Modify `verify_alerts.sh` to test custom alerts:

```bash
generate_custom_test_event() {
    # Your custom event generation logic
    curl -X POST "$API_URL/your/endpoint" ...
}
```

### Extended Performance Baseline

Run longer baseline collection:

```bash
# 24 hour baseline (1440 minutes)
./monitoring_performance_baseline.sh 1440
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review individual test logs in `monitoring_logs/`
3. Check Prometheus/Grafana/AlertManager logs
4. Consult the DevSkyy monitoring documentation

## Version History

- **v1.0** (2024-12-19): Initial release
  - Monitoring verification
  - Security metrics verification
  - Grafana dashboard verification
  - Alert testing
  - Performance baseline collection
  - Master test runner
  - Comprehensive reporting

## License

Internal use only - DevSkyy Project
