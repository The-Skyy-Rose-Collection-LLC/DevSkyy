# Dependency Conflicts Resolution Plan

## Critical Conflicts Detected

**Date:** 2025-11-23
**Status:** Requires Resolution
**Impact:** May cause test failures and runtime issues

---

## Conflict Analysis

### 🔴 **Critical Conflicts (Security Impact)**

#### 1. cryptography Version Conflict
```
pyopenssl 24.0.0 requires: cryptography<43,>=41.0.5
We have: cryptography 46.0.3 (upgraded for CVE fixes)
```

**Resolution:** Upgrade pyopenssl to support cryptography 46.x
```bash
pip install 'pyopenssl>=24.2.1' --upgrade
```

**Rationale:** We CANNOT downgrade cryptography due to 4 CVEs (Truth Protocol Rule #13)

---

#### 2. protobuf Version Conflict
```
tensorflow 2.16.2 requires: protobuf<5.0.0,>=3.20.3
tensorflow-macos 2.12.0 requires: protobuf<5.0.0,>=3.20.3
We have: protobuf 6.33.1
```

**Resolution:** Pin protobuf to compatible version
```bash
pip install 'protobuf>=4.25.5,<5.0.0' --downgrade
```

**Rationale:** TensorFlow doesn't support protobuf 6.x yet

---

### 🟡 **High Priority Conflicts**

#### 3. uvicorn Version Conflict
```
fastmcp 2.13.1 requires: uvicorn>=0.35
devskyy 5.2.0 requires: uvicorn[standard]>=0.34.0
We have: uvicorn 0.31.1
```

**Resolution:** Upgrade uvicorn
```bash
pip install 'uvicorn[standard]>=0.35.0' --upgrade
```

---

#### 4. rich, websockets (fastmcp dependencies)
```
fastmcp 2.13.1 requires: rich>=13.9.4, websockets>=15.0.1
We have: rich 13.7.1, websockets 13.1
```

**Resolution:** Upgrade both
```bash
pip install 'rich>=13.9.4' 'websockets>=15.0.1' --upgrade
```

---

#### 5. botocore Version Conflict
```
aiobotocore 2.7.0 requires: botocore<1.31.65,>=1.31.16
We have: botocore 1.36.26
```

**Resolution:** Upgrade aiobotocore
```bash
pip install 'aiobotocore>=2.15.0' --upgrade
```

---

### 🟢 **Medium Priority Conflicts**

#### 6. TensorFlow-macOS Version Conflicts
```
tensorflow-macos 2.12.0 requires: keras<2.13, numpy<1.24, tensorboard<2.13
We have: keras 3.12.0, numpy 1.26.4, tensorboard 2.16.2
```

**Resolution Options:**
- **Option A:** Upgrade tensorflow-macos to 2.16.x (recommended)
- **Option B:** Downgrade keras, numpy, tensorboard (not recommended)
- **Option C:** Remove tensorflow-macos if not needed

**Recommended:**
```bash
pip install 'tensorflow-macos>=2.16.0' --upgrade
```

---

#### 7. jedi, pylint (Spyder IDE dependencies)
```
spyder 5.4.3 requires: jedi<0.19.0, pylint<3.0
python-lsp-server 1.7.2 requires: jedi<0.19.0
We have: jedi 0.19.2, pylint 3.3.2
```

**Resolution:** Upgrade Spyder (non-critical for production)
```bash
pip install 'spyder>=5.5.0' --upgrade
```

---

### 🔵 **Low Priority (Dev Dependencies)**

#### 8. Missing Jupyter/Notebook dependencies
```
spyder-kernels 2.4.4 requires: ipykernel, jupyter-client
widgetsnbextension 3.5.2 requires: notebook
conda 24.3.0 requires: menuinst
```

**Resolution:** Install if needed for development
```bash
pip install ipykernel jupyter-client notebook nbconvert qtconsole
```

---

## Resolution Script

**File:** `scripts/resolve_dependencies.sh`

```bash
#!/bin/bash
set -e

echo "🔧 Resolving DevSkyy dependency conflicts..."

# Critical: Upgrade pyopenssl for cryptography 46.x
echo "1. Upgrading pyopenssl..."
pip install 'pyopenssl>=24.2.1' --upgrade

# Critical: Downgrade protobuf for TensorFlow compatibility
echo "2. Fixing protobuf version..."
pip install 'protobuf>=4.25.5,<5.0.0' --force-reinstall

# High: Upgrade uvicorn and fastmcp dependencies
echo "3. Upgrading uvicorn..."
pip install 'uvicorn[standard]>=0.35.0' --upgrade

echo "4. Upgrading rich and websockets..."
pip install 'rich>=13.9.4' 'websockets>=15.0.1' --upgrade

# High: Upgrade aiobotocore
echo "5. Upgrading aiobotocore..."
pip install 'aiobotocore>=2.15.0' --upgrade

# Medium: Upgrade TensorFlow-macOS (if on macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "6. Upgrading tensorflow-macos..."
    pip install 'tensorflow-macos>=2.16.0' --upgrade
fi

# Medium: Upgrade Spyder (dev only)
echo "7. Upgrading spyder..."
pip install 'spyder>=5.5.0' --upgrade || echo "Spyder upgrade skipped"

# Verify resolution
echo "✅ Running pip check..."
pip check || echo "Some conflicts may remain - review manually"

echo "🎉 Dependency resolution complete!"
```

---

## Updated Requirements Files

### requirements.txt (Production)
```
# Updated to resolve conflicts

# Web Framework
fastapi~=0.121.0
uvicorn[standard]>=0.35.0  # UPGRADED from 0.31.1
starlette>=0.40.0
pydantic>=2.9.0,<3.0.0

# Security (MAINTAIN UPGRADES - CVE fixes)
cryptography>=46.0.3,<47.0.0  # DO NOT DOWNGRADE
pyopenssl>=24.2.1  # UPGRADED to support cryptography 46.x
setuptools>=78.1.1

# Database
sqlalchemy~=2.0.36

# AI/ML
anthropic~=0.69.0
openai~=2.7.2
torch>=2.8.0,<2.9.0
transformers~=4.57.1
protobuf>=4.25.5,<5.0.0  # DOWNGRADED for TensorFlow

# Infrastructure
redis>=7.1.0
elasticsearch>=9.2.0

# MCP
fastmcp>=2.13.1
rich>=13.9.4  # UPGRADED
websockets>=15.0.1  # UPGRADED

# AWS
boto3>=1.36.0
aiobotocore>=2.15.0  # UPGRADED

# TensorFlow (macOS)
tensorflow-macos>=2.16.0; sys_platform == 'darwin'  # UPGRADED
```

---

## Execution Plan

### Phase 1: Immediate (30 minutes)
```bash
cd /home/user/DevSkyy
bash scripts/resolve_dependencies.sh
pip check
```

### Phase 2: Validation (1 hour)
```bash
# Run tests to verify no breakage
pytest tests/ -v --tb=short

# Verify security packages
pip show cryptography setuptools pyopenssl

# Check application startup
python -c "import main; print('✅ App imports successfully')"
```

### Phase 3: Update Lock Files (15 minutes)
```bash
pip freeze > requirements.lock.txt
pip list --format=freeze > requirements-frozen.txt
```

---

## Risk Assessment

| Change | Risk | Mitigation |
|--------|------|------------|
| Keep cryptography 46.0.3 | LOW | Upgrade pyopenssl to support it |
| Downgrade protobuf 6.x → 4.x | LOW | TensorFlow compatibility required |
| Upgrade uvicorn 0.31 → 0.35 | LOW | Minor version, well-tested |
| Upgrade tensorflow-macos | MEDIUM | Test ML functionality |
| Upgrade aiobotocore | LOW | AWS SDK compatibility |

**Overall Risk:** LOW ✅

---

## Success Criteria

✅ `pip check` returns 0 conflicts
✅ All tests pass
✅ Application starts without errors
✅ Security packages remain upgraded (cryptography, setuptools)
✅ No Truth Protocol violations

---

## Rollback Plan

If issues occur:
```bash
# Restore from backup
cp requirements.txt.backup requirements.txt
pip install -r requirements.txt --force-reinstall
```

---

**Status:** Ready to execute
**Approval Required:** Yes (affects production dependencies)
**Estimated Time:** 2 hours (resolution + testing)
