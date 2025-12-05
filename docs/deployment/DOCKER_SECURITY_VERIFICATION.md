# Docker Security Verification Guide

This guide helps you verify that all Docker images have the correct security package versions installed to fix the 7 CRITICAL CVEs.

## Quick Start

```bash
# Run automated verification script
./scripts/verify_docker_security.sh
```

## Manual Verification

### 1. Build All Docker Images

```bash
# Main application image
docker build -f Dockerfile -t devskyy:latest .

# Production optimized image
docker build -f Dockerfile.production -t devskyy:production .

# MCP server image
docker build -f Dockerfile.mcp -t devskyy:mcp .

# Multi-model AI image
docker build -f Dockerfile.multimodel -t devskyy:multimodel .
```

### 2. Verify Security Packages

For each image, verify the installed package versions:

```bash
# Check devskyy:latest
docker run --rm devskyy:latest pip list | grep -E 'pip|cryptography|setuptools'

# Check devskyy:production
docker run --rm devskyy:production pip list | grep -E 'pip|cryptography|setuptools'

# Check devskyy:mcp
docker run --rm devskyy:mcp pip list | grep -E 'pip|cryptography|setuptools'

# Check devskyy:multimodel
docker run --rm devskyy:multimodel pip list | grep -E 'pip|cryptography|setuptools'
```

### 3. Expected Output

Each image should show:

```
cryptography    46.0.3      (or higher)
pip             25.3        (or higher)
setuptools      78.1.1      (or higher)
```

## Detailed Verification

### Check Specific CVE Fixes

```bash
# Verify cryptography version (fixes 4 CRITICAL CVEs)
docker run --rm devskyy:latest python -c "import cryptography; print(f'cryptography {cryptography.__version__}')"

# Verify pip version (fixes CVE-2025-8869)
docker run --rm devskyy:latest pip --version

# Verify setuptools version (fixes 2 CRITICAL CVEs)
docker run --rm devskyy:latest python -c "import setuptools; print(f'setuptools {setuptools.__version__}')"
```

### Run Security Scan Inside Container

```bash
# Install and run pip-audit inside container
docker run --rm devskyy:latest sh -c "pip install pip-audit && pip-audit --desc"
```

Expected: No CRITICAL or HIGH vulnerabilities

## CVE Resolution Status

After successful verification, the following CVEs should be resolved:

| CVE ID | Package | Severity | Status |
|--------|---------|----------|--------|
| CVE-2025-8869 | pip | CRITICAL | ✓ FIXED |
| CVE-2024-26130 | cryptography | CRITICAL | ✓ FIXED |
| CVE-2023-50782 | cryptography | CRITICAL | ✓ FIXED |
| CVE-2024-0727 | cryptography | CRITICAL | ✓ FIXED |
| GHSA-h4gh-qq45-vh27 | cryptography | CRITICAL | ✓ FIXED |
| CVE-2025-47273 | setuptools | CRITICAL | ✓ FIXED |
| CVE-2024-6345 | setuptools | CRITICAL | ✓ FIXED |

**Total CRITICAL CVEs Resolved:** 7

## Troubleshooting

### Build Fails

If the build fails, check:

1. **Docker daemon running:**
   ```bash
   docker ps
   ```

2. **Sufficient disk space:**
   ```bash
   df -h
   ```

3. **Build logs:**
   ```bash
   docker build -f Dockerfile -t devskyy:latest . 2>&1 | tee build.log
   ```

### Package Version Mismatch

If package versions don't match requirements:

1. **Clear Docker cache:**
   ```bash
   docker builder prune -a
   ```

2. **Rebuild without cache:**
   ```bash
   docker build --no-cache -f Dockerfile -t devskyy:latest .
   ```

3. **Verify requirements.txt:**
   ```bash
   grep -E 'pip|cryptography|setuptools' requirements.txt
   ```

### Verification Script Fails

If the automated script fails:

1. **Check Docker permissions:**
   ```bash
   docker run hello-world
   ```

2. **Review error logs:**
   ```bash
   tail /tmp/build_*.log
   ```

3. **Run manual verification steps above**

## Production Deployment

Once all images are verified:

### 1. Tag for Production

```bash
docker tag devskyy:production devskyy:v5.1.0-secure
docker tag devskyy:mcp devskyy-mcp:v5.1.0-secure
```

### 2. Push to Registry

```bash
# Docker Hub
docker push devskyy:production

# AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag devskyy:production <account>.dkr.ecr.us-east-1.amazonaws.com/devskyy:v5.1.0-secure
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/devskyy:v5.1.0-secure

# Google Container Registry
gcloud auth configure-docker
docker tag devskyy:production gcr.io/<project>/devskyy:v5.1.0-secure
docker push gcr.io/<project>/devskyy:v5.1.0-secure
```

### 3. Deploy to Kubernetes

```bash
# Update deployment to use new image
kubectl set image deployment/devskyy devskyy=devskyy:v5.1.0-secure

# Monitor rollout
kubectl rollout status deployment/devskyy

# Verify deployment
kubectl get pods -l app=devskyy
```

### 4. Post-Deployment Verification

```bash
# Check pod security
kubectl exec -it <pod-name> -- pip list | grep -E 'pip|cryptography|setuptools'

# Run security scan in production
kubectl exec -it <pod-name> -- pip-audit --desc

# Check application health
curl https://api.devskyy.com/api/v1/monitoring/health
```

## Compliance Verification

### Truth Protocol Compliance

Verify Truth Protocol Rule #13 (Security baseline):

```bash
docker run --rm devskyy:latest sh -c "
echo 'Security Baseline Verification:'
echo '-------------------------------'
echo -n 'AES-256-GCM: '
python -c 'from cryptography.hazmat.primitives.ciphers.aead import AESGCM; print(\"✓ Available\")'
echo -n 'Argon2id: '
python -c 'from passlib.hash import argon2; print(\"✓ Available\")'
echo -n 'OAuth2+JWT: '
python -c 'import jwt; print(\"✓ Available\")'
echo -n 'PBKDF2: '
python -c 'from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC; print(\"✓ Available\")'
"
```

### Generate Compliance Report

```bash
docker run --rm devskyy:latest sh -c "
pip list --format=json | python -c '
import json, sys
packages = json.load(sys.stdin)
critical = {\"pip\": \"25.3\", \"cryptography\": \"46.0.3\", \"setuptools\": \"78.1.1\"}
print(\"\\nSecurity Package Compliance:\")
print(\"============================\\n\")
for pkg in packages:
    if pkg[\"name\"] in critical:
        required = critical[pkg[\"name\"]]
        status = \"✓ PASS\" if pkg[\"version\"] >= required else \"✗ FAIL\"
        print(f\"{pkg[\"name\"]:<15} {pkg[\"version\"]:<10} (required: >={required})  {status}\")
'
" > docker_compliance_report.txt

cat docker_compliance_report.txt
```

## References

- **Security Scan Report:** `artifacts/SECURITY_SCAN_REPORT_20251118.md`
- **Error Ledger:** `artifacts/error-ledger-20251118_160258.json`
- **CVE Database:** `artifacts/pip-audit-report.json`
- **Dockerfile Changes:** Git commit `8092c53`

## Support

If you encounter issues:

1. Check documentation: `docs/`
2. Review security report: `artifacts/SECURITY_SCAN_REPORT_20251118.md`
3. Run verification script: `./scripts/verify_docker_security.sh`
4. Contact DevSkyy Security Team

---

**Last Updated:** 2025-11-18  
**Version:** 5.1.0  
**Status:** All CRITICAL CVEs Resolved ✓
