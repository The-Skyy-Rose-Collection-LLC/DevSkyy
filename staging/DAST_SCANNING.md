# DAST and Vulnerability Scanning System

Comprehensive Dynamic Application Security Testing (DAST) and vulnerability scanning verification for the staging environment.

## Overview

This system integrates **OWASP ZAP** and **Nuclei** to perform thorough security testing on the staging environment before production deployment. It automatically:

- Runs multiple security scanners in parallel
- Parses and normalizes findings
- Identifies and removes duplicates
- Prioritizes vulnerabilities by severity and business impact
- Compares results against baseline to track progress
- Identifies production blockers
- Generates comprehensive reports

## Components

### 1. Main Scan Orchestrator (`run_dast_scan.sh`)

Main entry point that coordinates all scanning activities.

**Features:**
- Runs OWASP ZAP active and passive scans
- Runs Nuclei vulnerability scans
- Collects and categorizes findings
- Generates combined reports
- Identifies critical blockers

**Usage:**
```bash
# Basic scan
./staging/run_dast_scan.sh

# Scan with custom URL
STAGING_URL=https://staging.example.com ./staging/run_dast_scan.sh

# Run scans in parallel
RUN_PARALLEL=true ./staging/run_dast_scan.sh

# With custom timeout
MAX_SCAN_DURATION=7200 ./staging/run_dast_scan.sh
```

**Environment Variables:**
- `STAGING_URL` - Target URL (default: https://staging.skyyrose.com)
- `ZAP_PORT` - ZAP proxy port (default: 8090)
- `ZAP_API_KEY` - ZAP API key (default: changeme)
- `MAX_SCAN_DURATION` - Maximum scan time in seconds (default: 3600)
- `NUCLEI_TIMEOUT` - Nuclei scan timeout (default: 30m)
- `RUN_PARALLEL` - Run ZAP and Nuclei in parallel (default: false)

**Output:**
- `reports/dast/zap_report_*.json` - ZAP JSON report
- `reports/dast/zap_report_*.html` - ZAP HTML report
- `reports/dast/nuclei_report_*.json` - Nuclei JSON report
- `reports/dast/combined_vulnerability_report_*.json` - Combined findings
- `reports/dast/vulnerability_summary_*.txt` - Human-readable summary

### 2. ZAP Results Parser (`parse_zap_results.py`)

Parses OWASP ZAP JSON reports and converts to standardized format.

**Features:**
- Maps ZAP findings to OWASP Top 10 categories
- Extracts CWE IDs and references
- Identifies false positives based on patterns
- Generates human-readable reports
- Categorizes by severity and confidence

**Usage:**
```bash
python3 staging/parse_zap_results.py \
    reports/dast/zap_report.json \
    reports/dast/zap_parsed.json
```

**False Positive Detection:**
- API endpoints without X-Frame-Options
- Static assets without CSP headers
- Infrastructure cookies (Vercel, etc.)

**Output:**
- Parsed JSON with standardized structure
- Human-readable text report
- Statistics by severity, OWASP category, and confidence

### 3. Nuclei Results Parser (`parse_nuclei_results.py`)

Parses Nuclei vulnerability scan results.

**Features:**
- Extracts CVE IDs and maps to CVE database
- Calculates CVSS scores and severity
- Extracts CWE IDs
- Provides remediation guidance
- Identifies false positives

**Usage:**
```bash
python3 staging/parse_nuclei_results.py \
    reports/dast/nuclei_report.json \
    reports/dast/nuclei_parsed.json
```

**Vulnerability Types:**
- CVE-based vulnerabilities
- Misconfigurations
- Information disclosure
- Default credentials
- Injection vulnerabilities
- Authentication issues

**Output:**
- Parsed JSON with CVE/CWE mappings
- Human-readable text report
- Statistics by severity and vulnerability type

### 4. Vulnerability Triage (`vulnerability_triage.py`)

Combines findings from multiple sources, deduplicates, and prioritizes.

**Features:**
- Merges ZAP and Nuclei findings
- Removes duplicates using intelligent matching
- Prioritizes by severity and business impact
- Identifies production blockers
- Generates remediation plan

**Usage:**
```bash
python3 staging/vulnerability_triage.py \
    reports/dast/zap_parsed.json \
    reports/dast/nuclei_parsed.json \
    reports/dast/combined_report.json
```

**Priority Levels:**
- **Blocker**: Must fix before production (RCE, SQLi, auth bypass)
- **Urgent**: Fix within 24-48 hours (critical XSS, CSRF)
- **High**: Fix within 1 week (security misconfigurations)
- **Medium**: Fix within 2 weeks (information disclosure)
- **Low**: Fix when possible (best practice violations)
- **Backlog**: Track but not urgent (informational)

**Remediation Complexity:**
- **Low**: 1-2 hours (headers, configs)
- **Medium**: 4-8 hours (XSS, CSRF fixes)
- **High**: 1-3 days (injection, auth issues)

**Output:**
- Unified vulnerability list
- Production blockers list
- Remediation plan by priority
- Duplicate tracking

### 5. Baseline Comparison (`compare_baseline.py`)

Compares current scan results against a known baseline.

**Features:**
- Identifies new vulnerabilities
- Tracks fixed vulnerabilities
- Detects regressions
- Monitors severity changes
- Generates delta reports

**Usage:**
```bash
python3 staging/compare_baseline.py \
    reports/dast/combined_report.json \
    reports/dast/vulnerability_baseline.json \
    reports/dast/vulnerability_delta.json
```

**Change Types:**
- **New**: Previously unknown vulnerabilities
- **Fixed**: Vulnerabilities resolved since baseline
- **Regression**: Fixed vulnerabilities that reappeared
- **Severity Increased**: Vulnerabilities that worsened
- **Severity Decreased**: Vulnerabilities that improved
- **Unchanged**: No change since baseline

**Output:**
- Delta report with all changes
- Regression alerts
- Progress tracking
- Net change statistics

## Installation

### Prerequisites

1. **OWASP ZAP**
   ```bash
   # Using Docker (recommended)
   docker pull owasp/zap2docker-stable

   # Or download from https://www.zaproxy.org/download/
   ```

2. **Nuclei**
   ```bash
   # Using Go
   go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

   # Or using Homebrew (macOS)
   brew install nuclei
   ```

3. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **jq** (JSON processor)
   ```bash
   # macOS
   brew install jq

   # Linux
   apt-get install jq
   ```

### Setup

1. Make scan script executable:
   ```bash
   chmod +x staging/run_dast_scan.sh
   ```

2. Configure environment variables:
   ```bash
   export STAGING_URL="https://staging.skyyrose.com"
   export ZAP_API_KEY="your-secure-api-key"
   ```

3. Create initial baseline (first run):
   ```bash
   ./staging/run_dast_scan.sh
   # This creates vulnerability_baseline.json automatically
   ```

## Workflow

### Standard Scan Workflow

```bash
# 1. Run complete DAST scan
./staging/run_dast_scan.sh

# 2. Review summary report
cat staging/reports/dast/vulnerability_summary_*.txt

# 3. Check for blockers
if [ $? -eq 0 ]; then
    echo "No blockers - safe to deploy"
else
    echo "Blockers found - review before deploy"
fi

# 4. Review detailed reports
open staging/reports/dast/zap_report_*.html
cat staging/reports/dast/combined_vulnerability_report_*.json
```

### CI/CD Integration

```yaml
# Example GitHub Actions workflow
- name: Run DAST Scan
  run: |
    ./staging/run_dast_scan.sh
  env:
    STAGING_URL: ${{ secrets.STAGING_URL }}
    ZAP_API_KEY: ${{ secrets.ZAP_API_KEY }}

- name: Upload Reports
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: dast-reports
    path: staging/reports/dast/

- name: Check for Blockers
  run: |
    python3 staging/vulnerability_triage.py \
      staging/reports/dast/zap_parsed_*.json \
      staging/reports/dast/nuclei_parsed_*.json \
      staging/reports/dast/triage.json
    # Exits 1 if blockers found
```

### Makefile Integration

```makefile
# Add to existing Makefile
.PHONY: dast-scan
dast-scan:
	@echo "Running DAST scan..."
	./staging/run_dast_scan.sh

.PHONY: dast-check-blockers
dast-check-blockers:
	@echo "Checking for production blockers..."
	@python3 staging/vulnerability_triage.py \
		staging/reports/dast/zap_parsed_*.json \
		staging/reports/dast/nuclei_parsed_*.json \
		staging/reports/dast/triage.json

.PHONY: dast-compare-baseline
dast-compare-baseline:
	@echo "Comparing with baseline..."
	@python3 staging/compare_baseline.py \
		staging/reports/dast/combined_report_*.json \
		staging/reports/dast/vulnerability_baseline.json \
		staging/reports/dast/delta.json
```

## Report Structure

### Combined Vulnerability Report

```json
{
  "metadata": {
    "tool": "VulnerabilityTriage",
    "version": "1.0.0",
    "generated_at": "2025-12-19T10:30:00Z"
  },
  "statistics": {
    "total_vulnerabilities": 45,
    "unique_vulnerabilities": 38,
    "duplicates_removed": 7,
    "blockers": 2,
    "by_severity": {
      "critical": 2,
      "high": 8,
      "medium": 15,
      "low": 10,
      "info": 3
    },
    "by_priority": {
      "blocker": 2,
      "urgent": 5,
      "high": 10,
      "medium": 12,
      "low": 8,
      "backlog": 1
    }
  },
  "blockers": [
    {
      "id": "abc123",
      "title": "SQL Injection in Product Search",
      "severity": "critical",
      "priority": "blocker",
      "sources": ["zap", "nuclei"],
      "remediation": "Use parameterized queries..."
    }
  ],
  "remediation_plan": {
    "immediate_action": [...],
    "short_term": [...],
    "medium_term": [...],
    "long_term": [...]
  }
}
```

### Baseline Delta Report

```json
{
  "summary": "...",
  "statistics": {
    "baseline_total": 40,
    "current_total": 38,
    "new_count": 5,
    "fixed_count": 7,
    "regression_count": 1,
    "net_change": -2
  },
  "new_vulnerabilities": [...],
  "fixed_vulnerabilities": [...],
  "regressions": [...]
}
```

## Best Practices

### 1. Regular Scanning
- Run scans on every staging deployment
- Weekly baseline comparisons
- Monthly full security reviews

### 2. Baseline Management
- Update baseline after verified fixes
- Keep historical baselines for trend analysis
- Document exceptions and accepted risks

### 3. False Positive Management
- Review and update false positive patterns
- Document reasons for FP classification
- Regularly re-evaluate FP status

### 4. Remediation Workflow
1. Fix blockers immediately
2. Address urgent items within 24-48h
3. Create tickets for high/medium priorities
4. Track all findings in issue tracker

### 5. Report Review
- Security team reviews all reports
- Development team addresses findings
- Product team accepts risk on low-priority items
- Document all decisions

## Troubleshooting

### ZAP Issues

**Problem**: ZAP fails to start
```bash
# Check if port is already in use
lsof -i :8090

# Use different port
ZAP_PORT=8091 ./staging/run_dast_scan.sh
```

**Problem**: ZAP scan times out
```bash
# Increase timeout
MAX_SCAN_DURATION=7200 ./staging/run_dast_scan.sh
```

### Nuclei Issues

**Problem**: Templates not updated
```bash
# Manually update
nuclei -update-templates

# Use specific template directory
nuclei -u $URL -t ./custom-templates/
```

**Problem**: Too many false positives
```bash
# Edit parse_nuclei_results.py FALSE_POSITIVE_PATTERNS
# Add custom patterns to filter known FPs
```

### Report Issues

**Problem**: Parser fails
```bash
# Check JSON validity
jq . reports/dast/zap_report.json

# Run parser with debug
python3 -m pdb staging/parse_zap_results.py ...
```

## Security Considerations

1. **API Keys**: Never commit ZAP API keys to version control
2. **Scan Scope**: Limit scans to staging environment only
3. **Rate Limiting**: Be mindful of scan impact on staging
4. **Data Sensitivity**: Don't include production data in staging
5. **Access Control**: Restrict access to vulnerability reports

## Metrics and KPIs

Track these metrics over time:
- Total vulnerabilities (trend down)
- Critical/High findings (target: 0)
- Mean time to remediation
- Regression rate (target: < 5%)
- False positive rate (target: < 10%)
- Scan coverage (URLs/endpoints tested)

## Integration Points

### Slack Notifications
```bash
# Add to run_dast_scan.sh
curl -X POST $SLACK_WEBHOOK \
  -d "{\"text\": \"DAST scan complete. Blockers: $blockers\"}"
```

### JIRA Integration
```python
# Create tickets for high-priority findings
from jira import JIRA
jira = JIRA(server, basic_auth=(user, token))
for vuln in high_priority_vulns:
    jira.create_issue(project="SEC", summary=vuln.title, ...)
```

### Metrics Dashboard
```python
# Export to Prometheus
from prometheus_client import Gauge
vuln_gauge = Gauge('vulnerabilities_total', 'Total vulnerabilities')
vuln_gauge.set(total_vulns)
```

## References

- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [Nuclei Documentation](https://nuclei.projectdiscovery.io/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Database](https://cwe.mitre.org/)
- [CVE Database](https://cve.mitre.org/)

## Support

For issues or questions:
1. Check troubleshooting section
2. Review tool documentation
3. Contact security team
4. File issue in project tracker
