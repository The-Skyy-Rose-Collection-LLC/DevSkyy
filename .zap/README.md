# DAST Configuration for DevSkyy Platform

This directory contains Dynamic Application Security Testing (DAST) configurations for the DevSkyy platform.

## Overview

DevSkyy implements comprehensive DAST scanning using two complementary tools:

1. **OWASP ZAP** - Industry-standard web application security scanner
2. **Nuclei** - Fast, template-based vulnerability scanner

## Files

### `rules.tsv`

ZAP scanning rules configuration that defines how to handle different security findings:

- **HIGH severity** (FAIL): SQL Injection, XSS, Path Traversal, RCE, XXE, SSRF, etc.
- **MEDIUM severity** (WARN): CSRF, Insecure cookies, Missing security headers, etc.
- **LOW severity** (INFO): Information disclosure, version leaks, etc.

### `context.xml`

ZAP context file that defines:

- Target scope (<http://localhost:8000>)
- Technology stack (Python, FastAPI, PostgreSQL, etc.)
- Authentication settings (if needed)
- URL parsing rules

## CI/CD Integration

The DAST scans run automatically in GitHub Actions CI/CD pipeline:

### Workflow Jobs

1. **dast-zap** - OWASP ZAP full scan
   - Runs after lint jobs
   - Requires PostgreSQL and Redis services
   - Starts application on port 8000
   - Performs comprehensive security scan
   - Uploads HTML, JSON, and Markdown reports
   - Continues on error to not block deployments

2. **dast-nuclei** - Nuclei vulnerability scan
   - Runs in parallel with ZAP
   - Uses latest vulnerability templates
   - Scans for CVEs, exposures, misconfigurations
   - Uploads SARIF results to GitHub Security
   - Generates JSON and Markdown reports

## Local Testing

### Prerequisites

```bash
# Install OWASP ZAP
docker pull zaproxy/zap-stable

# Install Nuclei
GO111MODULE=on go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
# OR
wget https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_linux_amd64.zip
unzip nuclei_linux_amd64.zip && sudo mv nuclei /usr/local/bin/
```

### Run ZAP Scan Locally

```bash
# Start the application with Docker Compose
docker-compose up -d

# Wait for application to be ready
until curl -f http://localhost:8000/health; do sleep 2; done

# Run ZAP scan
docker run --network=host -v $(pwd):/zap/wrk/:rw \
  -t zaproxy/zap-stable zap-full-scan.py \
  -t http://localhost:8000 \
  -r zap-report.html \
  -J zap-report.json \
  -w zap-report.md \
  -c .zap/rules.tsv \
  -n .zap/context.xml

# View reports
open zap-report.html  # Or your browser of choice
```

### Run Nuclei Scan Locally

```bash
# Update templates
nuclei -update-templates

# Run scan
nuclei -u http://localhost:8000 \
  -severity critical,high,medium \
  -tags cve,exposure,misconfig,vulnerability \
  -stats \
  -json -o nuclei-report.json \
  -markdown-export nuclei-report.md \
  -sarif-export nuclei-report.sarif

# View reports
cat nuclei-report.md
```

## Scan Coverage

### OWASP ZAP Tests

- **Injection Attacks**: SQL, LDAP, Command, XXE
- **XSS**: Reflected, Stored, DOM-based
- **Path Traversal & File Inclusion**
- **Authentication & Session Management**
- **Access Control Issues**
- **CSRF & Security Headers**
- **Information Disclosure**
- **Server-Side Request Forgery (SSRF)**
- **Insecure Deserialization**
- **Known Vulnerabilities**

### Nuclei Tests

- **CVE Detection**: Latest known vulnerabilities
- **Exposure Detection**: Sensitive file/endpoint exposure
- **Misconfigurations**: Security misconfigurations
- **Default Credentials**: Common default passwords
- **Vulnerable Components**: Outdated libraries with known issues

## Customization

### Adding Custom ZAP Rules

Edit `rules.tsv` to modify scanning behavior:

```tsv
# Format: <rule_id> <threshold> <action>
# Example: Ignore specific rule
10011 DEFAULT IGNORE

# Example: Increase severity
40018 HIGH FAIL
```

### Excluding Endpoints from Scanning

Add to `.zap/context.xml`:

```xml
<excregexes>http://localhost:8000/admin/.*</excregexes>
<excregexes>http://localhost:8000/internal/.*</excregexes>
```

### Adding Authentication

Update `context.xml` with authentication details if your endpoints require auth:

```xml
<authentication>
    <type>1</type> <!-- Form-based -->
    <strategy>EACH_RESP</strategy>
    <loginurl>http://localhost:8000/api/auth/login</loginurl>
    <loginbody>username={%username%}&amp;password={%password%}</loginbody>
</authentication>
```

## Reports and Artifacts

All scan reports are uploaded as GitHub Actions artifacts and retained for 30 days:

- **ZAP Reports**: `zap-scan-reports`
  - `report_html.html` - Human-readable HTML report
  - `report_json.json` - Machine-readable JSON
  - `report_md.md` - Markdown summary

- **Nuclei Reports**: `nuclei-scan-reports`
  - `nuclei-report.json` - Detailed JSON results
  - `nuclei-report.md` - Markdown summary
  - `nuclei-report.sarif` - SARIF format (uploaded to GitHub Security)

## Security Thresholds

Current policy:

- **CRITICAL/HIGH** findings: Scan continues, reports uploaded
- **MEDIUM** findings: Warnings logged
- **LOW** findings: Informational only

To make scans fail on high severity findings, modify `.github/workflows/ci.yml`:

```yaml
- name: Run OWASP ZAP Full Scan
  uses: zaproxy/action-full-scan@v0.7.0
  with:
    fail_action: true  # Change to true to fail on high severity
```

## Troubleshooting

### Application Fails to Start

Check the uvicorn logs in the workflow:

```yaml
- name: Stop application server
  if: always()
  run: |
    cat uvicorn.log  # Logs are printed on failure
```

### False Positives

Add rules to `rules.tsv` to ignore specific findings:

```tsv
40018 DEFAULT IGNORE # Ignore SQL injection false positive
```

### Scan Takes Too Long

Reduce scan intensity by modifying ZAP options in workflow:

```yaml
cmd_options: '-a -j -l INFO -d'  # Remove -a for faster passive-only scan
```

## Best Practices

1. **Run scans regularly**: On every PR and before deployments
2. **Review all findings**: Don't just ignore warnings
3. **Update templates**: Keep Nuclei templates up-to-date
4. **Monitor trends**: Track vulnerability counts over time
5. **Fix high-severity issues**: Before merging to main
6. **Document exceptions**: If ignoring a finding, document why
7. **Use SARIF uploads**: Integrate with GitHub Security tab

## References

- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)
- [ZAP Scanning Rules](https://www.zaproxy.org/docs/alerts/)
- [Nuclei Templates](https://github.com/projectdiscovery/nuclei-templates)
- [GitHub Security Features](https://docs.github.com/en/code-security)
- [SARIF Format](https://sarifweb.azurewebsites.net/)

## Support

For issues or questions:

- DevSkyy Security Team
- GitHub Issues: Create an issue with the `security` label
- Documentation: See `security/` directory for additional security docs
