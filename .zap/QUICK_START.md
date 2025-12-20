# DAST Quick Start Guide

## TL;DR

DevSkyy now has automated security scanning with OWASP ZAP and Nuclei in CI/CD.

## What Just Happened?

Two new jobs in `.github/workflows/ci.yml`:

- `dast-zap` - OWASP ZAP comprehensive web app security scan
- `dast-nuclei` - Fast vulnerability scanner with latest CVE database

## Run Locally (One Command)

```bash
./.zap/test-dast-local.sh
```

This will:

1. Start PostgreSQL and Redis
2. Launch DevSkyy on port 8000
3. Run ZAP scan
4. Run Nuclei scan
5. Generate reports
6. Clean up everything

## View Results in CI/CD

1. Push to `main` or `develop`
2. Go to GitHub Actions tab
3. Click on your workflow run
4. Scroll to "DAST" jobs
5. Download artifacts when complete:
   - `zap-scan-reports` (HTML, JSON, MD)
   - `nuclei-scan-reports` (JSON, MD, SARIF)

## Quick Commands

### Just ZAP

```bash
docker-compose up -d postgres redis
uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 &

docker run --network=host -v $(pwd):/zap/wrk/:rw \
  -t zaproxy/zap-stable zap-full-scan.py \
  -t http://localhost:8000 -r zap-report.html

open zap-report.html
```

### Just Nuclei

```bash
nuclei -u http://localhost:8000 -severity critical,high,medium
```

## Configuration Files

- **rules.tsv** - What to scan for and how to respond
- **context.xml** - ZAP configuration (scope, tech stack)
- **README.md** - Full documentation
- **test-dast-local.sh** - Automated local testing

## What Gets Scanned?

- SQL Injection (PostgreSQL, MySQL, SQLite)
- Cross-Site Scripting (XSS - all types)
- Authentication & Session issues
- Security headers
- Path Traversal
- CSRF
- XXE, SSRF, RCE
- 1000+ CVEs (Nuclei)
- Misconfigurations
- Information disclosure

## Severity Levels

- **HIGH** → Scan continues, report uploaded
- **MEDIUM** → Warning logged
- **LOW** → Info only

## Customize Scanning

Edit `.zap/rules.tsv`:

```tsv
# Ignore specific finding
40018 DEFAULT IGNORE

# Make something fail CI
40012 HIGH FAIL
```

## Need Help?

1. Check logs in GitHub Actions
2. Read `.zap/README.md` for detailed docs
3. Run `.zap/test-dast-local.sh` to debug locally

## Files Overview

```
.zap/
├── rules.tsv              # Scanning rules
├── context.xml            # ZAP context
├── README.md              # Full documentation
├── QUICK_START.md         # This file
└── test-dast-local.sh     # Local test script
```

## That's It

Your app now has automated security testing on every push. Reports are in GitHub Actions artifacts.

---

For detailed information, see `.zap/README.md`
