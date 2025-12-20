# DAST Quick Reference Card

Quick reference for running DAST scans and interpreting results.

## Quick Start

```bash
# 1. Run scan
./staging/run_dast_scan.sh

# 2. Check for blockers (exits 1 if blockers found)
echo $?

# 3. View summary
cat staging/reports/dast/vulnerability_summary_*.txt | tail -50
```

## Common Commands

### Run Basic Scan
```bash
./staging/run_dast_scan.sh
```

### Scan Custom URL
```bash
STAGING_URL=https://my-staging.com ./staging/run_dast_scan.sh
```

### Run Scans in Parallel (faster)
```bash
RUN_PARALLEL=true ./staging/run_dast_scan.sh
```

### Parse Individual Reports
```bash
# ZAP only
python3 staging/parse_zap_results.py \
    staging/reports/dast/zap_report.json \
    staging/reports/dast/zap_parsed.json

# Nuclei only
python3 staging/parse_nuclei_results.py \
    staging/reports/dast/nuclei_report.json \
    staging/reports/dast/nuclei_parsed.json
```

### Triage and Combine
```bash
python3 staging/vulnerability_triage.py \
    staging/reports/dast/zap_parsed.json \
    staging/reports/dast/nuclei_parsed.json \
    staging/reports/dast/combined.json
```

### Compare with Baseline
```bash
python3 staging/compare_baseline.py \
    staging/reports/dast/combined.json \
    staging/reports/dast/vulnerability_baseline.json \
    staging/reports/dast/delta.json
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success, no blockers |
| 1 | Blockers found or scan failed |

## Output Files

| File | Description |
|------|-------------|
| `zap_report_*.json` | Raw ZAP findings (JSON) |
| `zap_report_*.html` | ZAP visual report |
| `nuclei_report_*.json` | Raw Nuclei findings (JSONL) |
| `zap_parsed_*.json` | Parsed ZAP findings |
| `nuclei_parsed_*.json` | Parsed Nuclei findings |
| `combined_vulnerability_report_*.json` | Unified findings from all sources |
| `vulnerability_summary_*.txt` | Human-readable summary |
| `vulnerability_delta_*.json` | Comparison with baseline |

## Severity Levels

| Level | Description | Action Required |
|-------|-------------|-----------------|
| **Critical** | Immediate exploitation possible | Fix immediately |
| **High** | High impact vulnerability | Fix within 24-48h |
| **Medium** | Moderate risk | Fix within 1 week |
| **Low** | Minor issue | Fix within 2 weeks |
| **Info** | Informational only | Track/backlog |

## Priority Levels

| Priority | Timeline | Examples |
|----------|----------|----------|
| **Blocker** | Before production | RCE, SQLi, auth bypass |
| **Urgent** | 24-48 hours | Critical XSS, CSRF |
| **High** | 1 week | Security misconfigs |
| **Medium** | 2 weeks | Info disclosure |
| **Low** | When possible | Best practice violations |
| **Backlog** | Track only | Informational findings |

## Reading Reports

### Check for Blockers
```bash
jq '.blockers | length' combined_report.json
# 0 = safe to deploy
# >0 = review blockers
```

### List Critical Issues
```bash
jq '.vulnerabilities[] | select(.severity == "critical") | {title, priority}' combined_report.json
```

### Count by Severity
```bash
jq '.statistics.by_severity' combined_report.json
```

### View Remediation Plan
```bash
jq '.remediation_plan.immediate_action' combined_report.json
```

### Compare with Baseline
```bash
jq '.statistics | {new_count, fixed_count, net_change}' delta_report.json
```

## Common Issues & Solutions

### ZAP Won't Start
```bash
# Check if port is in use
lsof -i :8090

# Use different port
ZAP_PORT=8091 ./staging/run_dast_scan.sh

# Kill existing ZAP
docker stop zap-daemon && docker rm zap-daemon
```

### Scan Takes Too Long
```bash
# Increase timeout
MAX_SCAN_DURATION=7200 ./staging/run_dast_scan.sh

# Run targeted scan
# Edit run_dast_scan.sh to limit scope
```

### Too Many False Positives
```bash
# Edit parse_zap_results.py
# Add patterns to FALSE_POSITIVE_PATTERNS

# Edit parse_nuclei_results.py
# Add patterns to FALSE_POSITIVE_PATTERNS
```

### Update Baseline
```bash
# After fixing vulnerabilities
cp staging/reports/dast/combined_report_latest.json \
   staging/reports/dast/vulnerability_baseline.json
```

## Integration Examples

### Makefile
```makefile
dast-scan:
	./staging/run_dast_scan.sh

dast-check:
	@python3 staging/vulnerability_triage.py \
		staging/reports/dast/zap_parsed_*.json \
		staging/reports/dast/nuclei_parsed_*.json \
		staging/reports/dast/triage.json
```

### Pre-Deploy Check
```bash
#!/bin/bash
echo "Running security scan before deploy..."
./staging/run_dast_scan.sh

if [ $? -eq 0 ]; then
    echo "✓ Security scan passed"
    make deploy-production
else
    echo "✗ Security scan failed - blockers found"
    exit 1
fi
```

### Cron Job (Weekly Scan)
```bash
# Add to crontab
0 2 * * 1 cd /path/to/repo && ./staging/run_dast_scan.sh
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STAGING_URL` | https://staging.skyyrose.com | Target URL |
| `ZAP_PORT` | 8090 | ZAP proxy port |
| `ZAP_API_KEY` | changeme | ZAP API key |
| `MAX_SCAN_DURATION` | 3600 | Max scan time (seconds) |
| `NUCLEI_TIMEOUT` | 30m | Nuclei timeout |
| `RUN_PARALLEL` | false | Run scanners in parallel |

## Interpreting Results

### No Blockers, Few Findings
✅ **Safe to deploy**
- Review and track findings
- Update baseline after fixes

### Blockers Found
❌ **Do not deploy**
- Review blocker details
- Fix critical issues
- Re-scan before deploying

### Many New Vulnerabilities
⚠️ **Investigate**
- Compare with baseline
- Check if new features introduced risks
- Evaluate false positives

### Regressions Detected
❌ **Do not deploy**
- Fixed vulnerabilities reappeared
- Code changes introduced new risks
- Review recent changes

## Testing

```bash
# Run test suite
python3 staging/test_dast_parsers.py

# Should see:
# ZAP parser: PASSED ✓
# Nuclei parser: PASSED ✓
# Vulnerability triage: PASSED ✓
# Baseline comparison: PASSED ✓
```

## Support Checklist

Before asking for help:
- [ ] Check prerequisites are installed
- [ ] Review error messages in output
- [ ] Check environment variables
- [ ] Verify target URL is accessible
- [ ] Review troubleshooting section
- [ ] Run test suite

## Key Files

- `run_dast_scan.sh` - Main orchestrator
- `parse_zap_results.py` - ZAP parser
- `parse_nuclei_results.py` - Nuclei parser
- `vulnerability_triage.py` - Triage and prioritization
- `compare_baseline.py` - Baseline comparison
- `DAST_SCANNING.md` - Full documentation

## Quick Metrics

```bash
# Total vulnerabilities
jq '.statistics.total_vulnerabilities' combined_report.json

# Blockers
jq '.statistics.blockers' combined_report.json

# New since baseline
jq '.statistics.new_count' delta_report.json

# Fixed since baseline
jq '.statistics.fixed_count' delta_report.json

# Net change
jq '.statistics.net_change' delta_report.json
```

## Report Generation

```bash
# Generate all reports
./staging/run_dast_scan.sh

# Generate custom report
python3 -c "
import json
with open('staging/reports/dast/combined_report_latest.json') as f:
    data = json.load(f)
    print(f\"Total: {data['statistics']['total_vulnerabilities']}\")
    print(f\"Blockers: {data['statistics']['blockers']}\")
"
```
