# Dependency Updates - Action Plan

**Generated:** 2025-11-15
**Priority:** CRITICAL updates must be applied TODAY

---

## Quick Start

```bash
# 1. Backup current requirements
cp requirements.txt requirements.txt.backup

# 2. Apply all updates from this plan
# (edit requirements.txt as specified below)

# 3. Test installation
pip install -r requirements.txt

# 4. Run tests
pytest tests/ --cov --cov-fail-under=90

# 5. Generate lock file
pip install pip-tools
pip-compile requirements.txt --output-file requirements.lock

# 6. Commit changes
git add requirements.txt requirements.lock
git commit -m "security: update dependencies (fix CVE-GHSA-7f5h-v6xp-fcq8, update PyJWT strategy)"
```

---

## CRITICAL Updates (Apply Immediately)

### 1. Fix Starlette DoS Vulnerability (CVE: GHSA-7f5h-v6xp-fcq8)

**File:** `/home/user/DevSkyy/requirements.txt`
**Line:** 12

```diff
-fastapi~=0.119.0  # Includes starlette dependency - do not pin separately
+fastapi~=0.121.2  # Fix Starlette DoS (GHSA-7f5h-v6xp-fcq8)
```

**Impact:** Fixes CRITICAL DoS vulnerability in Starlette's FileResponse
**Testing Required:** Yes (especially file upload/download endpoints)

---

### 2. Update CA Certificates

**File:** `/home/user/DevSkyy/requirements.txt`
**Line:** 48

```diff
-certifi>=2024.12.14,<2025.0.0  # Security update
+certifi>=2025.11.12,<2026.0.0  # Security update (latest CA certificates)
```

**Impact:** Ensures latest SSL/TLS certificate validation
**Testing Required:** Yes (all HTTPS connections)

---

### 3. Fix PyJWT Version Strategy (Truth Protocol Violation)

**File:** `/home/user/DevSkyy/requirements.txt`
**Line:** 50

```diff
-PyJWT~=2.10.1  # Updated for security
+PyJWT>=2.10.1,<3.0.0  # Security-critical JWT (RFC 7519) - allows patch updates
```

**Files to Update:**
- `/home/user/DevSkyy/requirements.txt` (line 50)
- `/home/user/DevSkyy/requirements-production.txt` (line 30)
- `/home/user/DevSkyy/requirements-luxury-automation.txt` (line 19)
- `/home/user/DevSkyy/requirements_mcp.txt` (line 19)
- `/home/user/DevSkyy/requirements.vercel.txt` (line 20)
- `/home/user/DevSkyy/requirements.minimal.txt` (line 31)

**Impact:** Allows automatic patch updates for JWT security fixes
**Testing Required:** Yes (all authentication endpoints)

---

## HIGH Priority Updates (Apply Within 24h)

### 4. Update Security-Critical Build Tools

**File:** `/home/user/DevSkyy/requirements.txt`
**Line:** 9

```diff
-setuptools>=78.1.1,<79.0.0  # Fix CVE-2025-47273 (path traversal → RCE), CVE-2024-6345 (RCE via package_index)
+setuptools>=80.9.0,<81.0.0  # Latest security fixes
```

**Impact:** Latest security patches for build system
**Testing Required:** Yes (build and packaging)

---

### 5. Update HTTP Security Library

**File:** `/home/user/DevSkyy/requirements.txt`
**Line:** 40

```diff
-requests>=2.32.4,<3.0.0  # Security fix GHSA-9hjg-9r4m-mvj7
+requests>=2.32.5,<3.0.0  # Latest security fixes
```

**Impact:** Latest HTTP security patches
**Testing Required:** Yes (all HTTP requests)

---

### 6. Update Core Framework (Pydantic)

**File:** `/home/user/DevSkyy/requirements.txt`
**Line:** 15

```diff
-pydantic[email]>=2.9.0,<3.0.0 # Updated: langchain 0.3+ supports pydantic v2 (fastapi 0.119 requires >=2.9)
+pydantic[email]>=2.12.4,<3.0.0 # Latest stable version with bug fixes
```

**Impact:** Bug fixes and improvements in data validation
**Testing Required:** Yes (data models and validation)
**Note:** Review changelog for any API changes

---

### 7. Update PyTorch

**File:** `/home/user/DevSkyy/requirements.txt`
**Lines:** 66-67

```diff
-torch~=2.9.0  # Updated from 2.2.2 - Latest stable version with security fixes
-torchvision~=0.20.0  # Compatible with torch 2.9.0
+torch~=2.9.1  # Latest security fixes and bug patches
+torchvision~=0.20.1  # Compatible with torch 2.9.1
```

**Impact:** Security fixes and bug patches for ML framework
**Testing Required:** Yes (all ML/AI features)

---

### 8. Update AI API Clients

**File:** `/home/user/DevSkyy/requirements.txt`
**Lines:** 62, 61

```diff
-openai~=2.7.2  # Latest version - Updated 2025-11-10
+openai~=2.8.0  # Latest API features and fixes
```

```diff
-anthropic~=0.69.0  # Latest version
+anthropic~=0.73.0  # Latest Claude API features
```

**Impact:** Latest API features and improvements
**Testing Required:** Yes (AI integrations)

---

### 9. Fix Dependency Conflict (torch vs openai-whisper)

**File:** `/home/user/DevSkyy/requirements.txt`
**Line:** 146

```diff
-openai-whisper==20240930  # Latest whisper (date-based version, must use exact pin)
+openai-whisper==20250625  # Latest version (fixes torch 2.9.x compatibility)
```

**Impact:** Resolves pip installation conflict with torch~=2.9.1
**Testing Required:** Yes (voice/audio processing features)

---

## Additional Required Actions

### 10. Generate Lock Files

```bash
# Install pip-tools
pip install pip-tools

# Generate lock file for main requirements
pip-compile requirements.txt --output-file requirements.lock

# Generate lock file for production
pip-compile requirements-production.txt --output-file requirements-production.lock

# Commit lock files
git add requirements.lock requirements-production.lock
git commit -m "build: add dependency lock files for reproducible deployments"
```

**Impact:** Ensures reproducible deployments (Truth Protocol compliance)
**Priority:** HIGH

---

### 11. Sync requirements-production.txt

**File:** `/home/user/DevSkyy/requirements-production.txt`

Update these lines to match main requirements.txt:

```diff
Line 10:
-uvicorn[standard]==0.34.0
+uvicorn[standard]==0.38.0

Line 42:
-openai==2.3.0
+openai==2.8.0
```

---

### 12. Update CHANGELOG.md

Add entry to `/home/user/DevSkyy/CHANGELOG.md`:

```markdown
## [Version] - 2025-11-15

### Security
- **CRITICAL:** Fixed Starlette DoS vulnerability (GHSA-7f5h-v6xp-fcq8) by updating fastapi to 0.121.2
- Updated certifi to 2025.11.12 for latest CA certificates
- Updated setuptools to 80.9.0 for latest security fixes
- Updated requests to 2.32.5 for HTTP security patches

### Dependencies
- Updated PyJWT version strategy from ~=2.10.1 to >=2.10.1,<3.0.0 (Truth Protocol compliance)
- Updated pydantic to 2.12.4 for bug fixes and improvements
- Updated torch to 2.9.1 and torchvision to 0.20.1 for security fixes
- Updated openai to 2.8.0 for latest API features
- Updated anthropic to 0.73.0 for latest Claude API
- Updated openai-whisper to 20250625 (fixes torch dependency conflict)

### Build
- Added requirements.lock and requirements-production.lock for reproducible deployments
- Synchronized version constraints across all requirements files
```

---

## Verification Steps

### Step 1: Test Installation

```bash
# Create clean virtual environment
python3.11 -m venv /tmp/test-venv
source /tmp/test-venv/bin/activate

# Install updated requirements
pip install -r requirements.txt

# Verify no conflicts
pip check

# Check for vulnerabilities
pip-audit --desc --requirement requirements.txt
```

**Expected Result:** Clean installation, no conflicts, no HIGH/CRITICAL CVEs

---

### Step 2: Run Test Suite

```bash
# Run all tests with coverage
pytest tests/ --cov --cov-report=term --cov-report=html --cov-fail-under=90

# Run security tests specifically
pytest tests/ -m security

# Check test coverage
coverage report --show-missing
```

**Expected Result:** All tests pass, coverage ≥90%

---

### Step 3: Run Security Scans

```bash
# Vulnerability audit
pip-audit --desc

# Safety check
safety check --json

# Bandit security scan
bandit -r . -f json -o artifacts/security-report.json

# Trivy container scan (if using Docker)
trivy image devskyy:latest --severity HIGH,CRITICAL
```

**Expected Result:** No HIGH/CRITICAL vulnerabilities

---

### Step 4: Verify API Functionality

```bash
# Start development server
uvicorn main:app --reload --port 8000

# Test critical endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/...

# Run integration tests
pytest tests/integration/
```

**Expected Result:** All endpoints respond correctly

---

## Rollback Plan

If issues are encountered:

```bash
# Restore backup
cp requirements.txt.backup requirements.txt

# Reinstall previous versions
pip install -r requirements.txt

# Verify rollback
pip check
pytest tests/
```

---

## Complete Update Script

Save as `scripts/apply-dependency-updates.sh`:

```bash
#!/bin/bash
set -e

echo "DevSkyy Dependency Update Script"
echo "================================="
echo ""

# Backup
echo "1. Creating backup..."
cp requirements.txt requirements.txt.backup.$(date +%Y%m%d)
cp requirements-production.txt requirements-production.txt.backup.$(date +%Y%m%d)

# Apply updates to requirements.txt
echo "2. Applying updates to requirements.txt..."
sed -i 's/fastapi~=0.119.0/fastapi~=0.121.2/' requirements.txt
sed -i 's/certifi>=2024.12.14,<2025.0.0/certifi>=2025.11.12,<2026.0.0/' requirements.txt
sed -i 's/PyJWT~=2.10.1/PyJWT>=2.10.1,<3.0.0/' requirements.txt
sed -i 's/setuptools>=78.1.1,<79.0.0/setuptools>=80.9.0,<81.0.0/' requirements.txt
sed -i 's/requests>=2.32.4,<3.0.0/requests>=2.32.5,<3.0.0/' requirements.txt
sed -i 's/pydantic\[email\]>=2.9.0,<3.0.0/pydantic[email]>=2.12.4,<3.0.0/' requirements.txt
sed -i 's/torch~=2.9.0/torch~=2.9.1/' requirements.txt
sed -i 's/torchvision~=0.20.0/torchvision~=0.20.1/' requirements.txt
sed -i 's/openai~=2.7.2/openai~=2.8.0/' requirements.txt
sed -i 's/anthropic~=0.69.0/anthropic~=0.73.0/' requirements.txt
sed -i 's/openai-whisper==20240930/openai-whisper==20250625/' requirements.txt

# Apply updates to requirements-production.txt
echo "3. Applying updates to requirements-production.txt..."
sed -i 's/uvicorn\[standard\]==0.34.0/uvicorn[standard]==0.38.0/' requirements-production.txt
sed -i 's/openai==2.3.0/openai==2.8.0/' requirements-production.txt
sed -i 's/PyJWT==2.10.1/PyJWT>=2.10.1,<3.0.0/' requirements-production.txt

# Apply PyJWT updates to other files
echo "4. Applying PyJWT updates to other requirement files..."
for file in requirements-luxury-automation.txt requirements_mcp.txt requirements.vercel.txt requirements.minimal.txt; do
    sed -i 's/PyJWT==2.10.1/PyJWT>=2.10.1,<3.0.0/' "$file"
done

# Test installation
echo "5. Testing installation..."
python3.11 -m venv /tmp/devskyy-test-venv
source /tmp/devskyy-test-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip check

# Generate lock files
echo "6. Generating lock files..."
pip install pip-tools
pip-compile requirements.txt --output-file requirements.lock
pip-compile requirements-production.txt --output-file requirements-production.lock

# Cleanup
deactivate
rm -rf /tmp/devskyy-test-venv

echo ""
echo "✓ Updates applied successfully!"
echo ""
echo "Next steps:"
echo "1. Run: pytest tests/ --cov --cov-fail-under=90"
echo "2. Run: pip-audit --desc"
echo "3. Review and commit changes"
echo ""
```

Usage:
```bash
chmod +x scripts/apply-dependency-updates.sh
./scripts/apply-dependency-updates.sh
```

---

## Timeline

| Action | Priority | Due Date | Estimated Time |
|--------|----------|----------|----------------|
| Apply CRITICAL updates (1-3) | CRITICAL | 2025-11-15 EOD | 1 hour |
| Apply HIGH updates (4-9) | HIGH | 2025-11-16 EOD | 2 hours |
| Generate lock files (10) | HIGH | 2025-11-16 EOD | 30 minutes |
| Sync production files (11) | HIGH | 2025-11-16 EOD | 15 minutes |
| Update CHANGELOG (12) | HIGH | 2025-11-16 EOD | 15 minutes |
| Run full test suite | HIGH | 2025-11-16 EOD | 1 hour |
| **Total Estimated Time** | | | **5 hours** |

---

## Success Criteria

- ✓ No HIGH/CRITICAL CVEs detected by pip-audit
- ✓ All tests pass with coverage ≥90%
- ✓ No dependency conflicts (pip check passes)
- ✓ Lock files generated and committed
- ✓ CHANGELOG.md updated
- ✓ Truth Protocol compliance: 100%
- ✓ All production deployments use updated dependencies

---

## Support

For questions or issues:
1. Review full audit report: `/home/user/DevSkyy/artifacts/dependency-audit-report-2025-11-15.md`
2. Check error ledger: `/home/user/DevSkyy/artifacts/error-ledger-dependency-audit-2025-11-15.json`
3. Contact DevOps team

---

**Generated by:** Claude Code Dependency Management Agent
**Report Date:** 2025-11-15
