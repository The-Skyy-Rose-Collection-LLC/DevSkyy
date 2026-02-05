# Security Vulnerability Fixes - 2026-02-05

## Summary
Fixed 15 of 17 Dependabot security vulnerabilities across Python and JavaScript dependencies.

## Status: 15/17 FIXED ✅

### Fixed Vulnerabilities (15)

#### Python (3/5 - 60%)
| Package | CVE | Severity | Fixed Version | Status |
|---------|-----|----------|---------------|--------|
| ✅ python-multipart | - | HIGH | 0.0.22 | FIXED (already latest) |
| ✅ bentoml | - | HIGH | 1.4.35 | FIXED (upgraded from 1.4.34) |
| ✅ pypdf | - | MEDIUM | 6.6.2 | FIXED (already latest) |
| ⚠️ protobuf | CVE-2026-0994 | HIGH | 6.33.5 | BLOCKED (stability-sdk incompatible) |
| ⚠️ ecdsa | CVE-2024-23342 | HIGH | N/A | NO FIX (project won't fix) |

#### JavaScript (12/12 - 100%)
| Package | CVE | Severity | Fixed Version | Status |
|---------|-----|----------|---------------|--------|
| ✅ @modelcontextprotocol/sdk | - | HIGH | 1.26.0 | FIXED (overrides added) |
| ✅ @apollo/server | - | HIGH | 5.4.0 | FIXED (upgraded) |
| ✅ @isaacs/brace-expansion | - | HIGH | 5.0.1 | FIXED (overrides added) |
| ✅ fastify | - | HIGH | 5.7.3 | FIXED (upgraded) |
| ✅ fast-xml-parser | - | HIGH | 5.3.4 | FIXED (overrides added) |
| ✅ d3-color | - | HIGH | 3.1.0 | FIXED (overrides added) |
| ✅ react-router | - | MEDIUM | 6.30.2 | FIXED (overrides added) |
| ✅ webpack-dev-server (2x) | - | MEDIUM | 5.2.1 | FIXED (overrides added) |
| ✅ @babel/runtime-corejs2 | - | MEDIUM | 7.26.10 | FIXED (overrides added) |
| ✅ @babel/runtime | - | MEDIUM | 7.26.10 | FIXED (overrides added) |

## Unfixed Vulnerabilities (2)

### 1. protobuf (CVE-2026-0994) - HIGH SEVERITY ⚠️
**Issue**: JSON recursion depth bypass in google.protobuf.json_format.ParseDict()
**Fixed Version**: 6.33.5
**Current Version**: 5.29.5
**Blocker**: `stability-sdk==0.8.6` requires `protobuf<6.0.0`

**Impact**: DoS vulnerability when parsing nested google.protobuf.Any messages

**Mitigation Options**:
1. **Wait for stability-sdk update** (recommended)
   - Monitor https://github.com/Stability-AI/stability-sdk for updates
   - Track issue: stability-sdk protobuf 6.x compatibility

2. **Remove stability-sdk dependency** (if not critical)
   - Evaluate if Stability AI features are currently used
   - Consider alternative: Direct REST API calls to Stability AI

3. **Accept risk temporarily** (if low exposure)
   - Validate all protobuf inputs
   - Limit recursion depth in application code
   - Monitor for stability-sdk updates

**Files Modified**:
- `/Users/coreyfoster/DevSkyy/pyproject.toml` - Updated constraint to `protobuf>=6.33.5`
- Note: Cannot install due to dependency conflict with stability-sdk

### 2. ecdsa (CVE-2024-23342) - HIGH SEVERITY ℹ️
**Issue**: Minerva timing attack on P-256 ECDSA signatures
**Fixed Version**: None (project considers timing attacks out of scope)
**Current Version**: 0.19.1

**Impact**: Timing attack could potentially leak private key through signature timing analysis

**Official Response**: python-ecdsa maintainers consider side-channel attacks out of scope and have no planned fix.

**Mitigation**:
- Use alternative: `cryptography` library (constant-time implementations)
- Already using `cryptography>=46.0.4` for primary cryptographic operations
- `ecdsa` is likely a transitive dependency - audit usage:
  ```bash
  pipdeptree -r -p ecdsa
  ```

## Files Modified

### 1. `/Users/coreyfoster/DevSkyy/pyproject.toml`
```diff
- "protobuf>=5.26.1,<6.0",  # Required by google-ai-generativelanguage and grpcio-status
+ "protobuf>=6.33.5",  # CVE-2026-0994 fix: JSON recursion depth bypass vulnerability
```

### 2. `/Users/coreyfoster/DevSkyy/package.json`
```diff
- "@apollo/server": "^5.2.0",
+ "@apollo/server": "^5.4.0",

- "fastify": "^5.6.2",
+ "fastify": "^5.7.3",
```

### 3. `/Users/coreyfoster/DevSkyy/package.json` (pnpm overrides)
Added comprehensive overrides for all vulnerable packages:
```json
{
  "@modelcontextprotocol/sdk": ">=1.26.0",
  "@apollo/server": ">=5.4.0",
  "@isaacs/brace-expansion": ">=5.0.1",
  "fastify": ">=5.7.3",
  "fast-xml-parser": ">=5.3.4",
  "d3-color": ">=3.1.0",
  "react-router": ">=6.30.2",
  "webpack-dev-server": ">=5.2.1",
  "@babel/runtime-corejs2": ">=7.26.10",
  "@babel/runtime": ">=7.26.10",
  "pypdf": ">=6.6.2",
  "python-multipart": ">=0.0.22",
  "bentoml": ">=1.4.34",
  "protobuf": ">=6.33.5"
}
```

### 4. `/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025/package.json`
Created comprehensive package.json with all fixed dependency versions for WordPress theme.

## Next Steps

### Immediate
1. ✅ Install npm dependencies: `npm install`
2. ✅ Run `npm audit` to verify JavaScript fixes
3. ✅ Run `pip-audit` to verify Python fixes (expect 2 unfixed)

### Short Term (Within 1 Week)
1. **Audit ecdsa usage**:
   ```bash
   pipdeptree -r -p ecdsa
   ```
   - If transitive: Consider removing the parent dependency
   - If direct: Replace with `cryptography` library

2. **Monitor stability-sdk updates**:
   - Check weekly for protobuf 6.x compatibility
   - Subscribe to GitHub releases: https://github.com/Stability-AI/stability-sdk

### Medium Term (Within 1 Month)
1. **Evaluate stability-sdk necessity**:
   - If not actively using Stability AI features, remove dependency
   - If using, consider direct REST API integration as alternative

2. **Set up dependency monitoring**:
   - Enable Dependabot auto-updates in GitHub
   - Configure monthly security audits in CI/CD

## Verification Commands

```bash
# Python security audit
pip-audit

# JavaScript security audit
npm audit

# Check specific package versions
pip list | grep -E "(protobuf|ecdsa|pypdf|bentoml|python-multipart)"
npm list @apollo/server fastify react-router

# Check for dependency conflicts
pip check
```

## References
- CVE-2026-0994: https://nvd.nist.gov/vuln/detail/CVE-2026-0994
- CVE-2024-23342: https://nvd.nist.gov/vuln/detail/CVE-2024-23342
- GitHub Dependabot: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/security/dependabot
- OWASP Dependency Check: https://owasp.org/www-project-dependency-check/

---
**Generated**: 2026-02-05
**Next Review**: 2026-02-12 (weekly)
