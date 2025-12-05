# Security Dependency Update Plan
## Based on CodeAnt AI Security Report - 2025-10-24

### Critical SCA Vulnerabilities to Address

---

## 🔴 CRITICAL PRIORITY (Fix Immediately)

### 1. **joblib** - CVE-2024-34997
- **Current**: 1.4.3
- **Issue**: Deserialization of Untrusted Data (CRITICAL)
- **Fix**: Upgrade to 1.4.4 or later when available
- **Mitigation**: Never deserialize joblib files from untrusted sources
- **Status**: ⚠️ No fix available yet, mitigation in place

### 2. **langchain** - CVE-2025-2828
- **Current**: 0.4.0
- **Issue**: Server-Side Request Forgery (SSRF) (CRITICAL)
- **Fix**: Upgrade to 0.4.1+ or apply SSRF protections
- **Mitigation**: Implement strict URL validation and whitelist
- **Status**: ⚠️ Pending patch

### 3. **pandas** - CVE-2020-13091
- **Current**: 2.3.0
- **Issue**: Deserialization of Untrusted Data (CRITICAL)
- **Fix**: Upgrade to latest 2.4.x
- **Action**: `pip install --upgrade pandas>=2.4.0`
- **Status**: ⏳ Ready to upgrade

### 4. **torch** - CVE-2025-32434
- **Current**: 2.3.0
- **Issue**: Deserialization of Untrusted Data (CRITICAL)
- **Fix**: Upgrade to 2.6.0+ (when available for macOS)
- **Mitigation**: Never use torch.load() with untrusted data; use weights_only=True
- **Status**: ⚠️ macOS compatibility issues with 2.6.0

---

## 🟠 HIGH PRIORITY

### 5. **aiomysql** - CVE-2025-62611
- **Current**: 0.2.1
- **Issue**: External Control of File Name or Path (CWE-73)
- **Fix**: Upgrade to 0.2.2+ when available
- **Mitigation**: Input validation on all file paths
- **Status**: ⚠️ No patch available

### 6. **mlflow** - Multiple CVEs (12 vulnerabilities)
- **Current**: 3.2.0
- **Issues**:
  - CVE-2024-1560: Path Traversal
  - CVE-2024-37052-37059: Deserialization of Untrusted Data (8 CVEs)
  - CVE-2024-37061: Code Injection
  - CVE-2025-0453: Resource Exhaustion
- **Fix**: Upgrade to 3.3.0+ or disable MLflow if not used
- **Action**: `pip install --upgrade mlflow>=3.3.0`
- **Status**: ⏳ Ready to upgrade

### 7. **transformers** - Multiple CVEs (13 vulnerabilities)
- **Current**: 4.48.0
- **Issues**:
  - CVE-2024-11392-11394: Deserialization of Untrusted Data
  - CVE-2024-12720, CVE-2025-2099, CVE-2025-5197, CVE-2025-6638, CVE-2025-6921: CWE-1333/Resource Exhaustion
- **Fix**: Upgrade to 4.49.0+ when available
- **Mitigation**: Only load models from trusted sources (HuggingFace official)
- **Status**: ⚠️ Pending patch

### 8. **PyJWT** - CVE-2025-45768
- **Current**: 2.11.0
- **Issue**: Missing Encryption of Sensitive Data (MEDIUM)
- **Fix**: Ensure proper key management and use algorithm allowlist
- **Mitigation**: Explicitly specify algorithms=['RS256', 'HS256']
- **Status**: ✅ Already mitigated in code

### 9. **python-json-logger** - CVE-2025-27607
- **Current**: 3.2.0
- **Issue**: Inclusion of Functionality from Untrusted Control Sphere (HIGH)
- **Fix**: Upgrade to 3.2.1+ or switch to structlog
- **Action**: `pip install --upgrade python-json-logger>=3.2.1` or migrate to structlog
- **Status**: ⏳ Ready to upgrade

---

## 🟡 MEDIUM/LOW PRIORITY

### 10. **torch** - Additional CVEs (Multiple)
- CVE-2025-2998, 2999, 3000, 3001, 3121, 3136: Memory Buffer Issues (MEDIUM)
- CVE-2025-46149: Reachable Assertion (MEDIUM)
- CVE-2025-46152: Out-of-bounds Write (MEDIUM)
- CVE-2025-55554: Integer Overflow (MEDIUM)
- CVE-2025-2149: Improper Initialization (LOW)
- CVE-2025-4287: Improper Resource Shutdown (LOW)

### 11. **Other Dependencies**
- **esbuild@0.14.47**: Development server security issue (MEDIUM)
- **loguru@0.7.3**: CVE-2022-0338 - Log file exposure (MEDIUM)
- **tar@4.4.18**: DoS vulnerability (MEDIUM)
- **semver@7.3.5**: ReDoS vulnerability (HIGH)
- **path-to-regexp@6.2.1**: Backtracking regex (HIGH)
- **debug@4.1.1**: ReDoS (LOW)
- **undici@5.26.5**: Integrity option issue (LOW)

---

## 📋 Action Plan

### Phase 1: Immediate Mitigations (Today)
1. ✅ Create log sanitization utility (security/log_sanitizer.py)
2. ⏳ Fix all log injection vulnerabilities (auggie running)
3. ⏳ Fix JWT signature verification
4. ⏳ Fix XSS and SQL injection issues
5. ✅ Document security best practices

### Phase 2: Dependency Updates (This Week)
1. Update pandas to 2.4.x
2. Update mlflow to 3.3.x
3. Update python-json-logger to 3.2.1+
4. Update PyJWT configuration (algorithm allowlist)
5. Test all critical functionality after updates

### Phase 3: Framework Updates (Next Sprint)
1. Monitor torch 2.6.0+ for macOS compatibility
2. Watch for transformers 4.49.0 release
3. Track langchain SSRF patch
4. Evaluate joblib alternatives for untrusted data

### Phase 4: Infrastructure Security (Ongoing)
1. Fix Kubernetes security contexts (allowPrivilegeEscalation)
2. Update GitHub Actions permissions
3. Implement container security best practices
4. Add security scanning to CI/CD pipeline

---

## 🛡️ Security Mitigations (Already In Place)

### Code-Level Protections
- ✅ Never use eval() on user input (using ast.literal_eval)
- ✅ JWT signature verification with JWKS
- ✅ Password hashing with bcrypt (12 rounds)
- ✅ Input validation on all endpoints
- ✅ HTTPS-only in production
- ✅ Rate limiting on authentication endpoints
- ✅ CSRF protection with state parameters

### Runtime Protections
- ⚠️ torch.load() - Add weights_only=True parameter
- ⚠️ joblib.load() - Only load from trusted internal sources
- ⚠️ Pandas read_pickle() - Avoid or validate source
- ✅ SQL - Use parameterized queries (ORM)
- ✅ Templates - Use auto-escaping (Jinja2/FastAPI)

---

## 📊 Risk Assessment

| Package | Severity | Exploitability | Impact | Priority |
|---------|----------|----------------|---------|----------|
| joblib | CRITICAL | High | RCE | P0 |
| langchain | CRITICAL | Medium | SSRF | P0 |
| pandas | CRITICAL | High | RCE | P0 |
| torch | CRITICAL | High | RCE | P0 |
| mlflow | HIGH | Medium | Multiple | P1 |
| transformers | HIGH | Low | DoS | P1 |
| python-json-logger | HIGH | Low | Info Leak | P2 |

---

## 🔄 Update Commands

### Safe Immediate Updates
```bash
# Upgrade safe packages first
pip install --upgrade pandas>=2.4.0
pip install --upgrade mlflow>=3.3.0
pip install --upgrade python-json-logger>=3.2.1

# Test after each update
pytest tests/ -v

# Update requirements.txt
pip freeze > requirements.txt
```

### Careful Updates (Test Thoroughly)
```bash
# These may have breaking changes
pip install --upgrade transformers>=4.49.0  # When available
pip install --upgrade torch>=2.6.0  # When macOS compatible
pip install --upgrade langchain>=0.4.1  # When SSRF patch released

# Run full test suite
pytest tests/ --cov=. --cov-report=html
```

---

## 📝 Testing Checklist

After each dependency update:

- [ ] Run unit tests: `pytest tests/`
- [ ] Run security tests: `bandit -r .`
- [ ] Check for new vulnerabilities: `safety check`
- [ ] Test authentication flows
- [ ] Test API endpoints
- [ ] Verify logging works correctly
- [ ] Check ML model loading/saving
- [ ] Validate webhook functionality
- [ ] Test GDPR endpoints

---

## 📞 Emergency Contacts

- **Security Team**: security@devskyy.com
- **DevOps Lead**: devops@devskyy.com
- **CTO**: cto@devskyy.com

---

**Last Updated**: 2025-10-24
**Next Review**: 2025-10-31
**Security Audit Status**: In Progress
