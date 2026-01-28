---
name: verification-loop
description: Comprehensive verification before PR or after major changes.
---

# Verification Loop

Run after features, before PRs, after refactoring.

## Verification Phases

```bash
# 1. Build
npm run build 2>&1 | tail -20

# 2. Types
npx tsc --noEmit 2>&1 | head -30

# 3. Lint
npm run lint 2>&1 | head -30

# 4. Tests
npm test -- --coverage 2>&1 | tail -50

# 5. Security
grep -rn "sk-\|api_key\|console.log" src/ | head -10

# 6. Diff review
git diff --stat
```

## Report Format

```
VERIFICATION REPORT
Build:     [PASS/FAIL]
Types:     [PASS/FAIL]
Tests:     [X/Y passed, Z% coverage]
Security:  [X issues]
Overall:   [READY/NOT READY] for PR
```

## Related Tools

- **Command**: `/verify` for full verification
- **Agent**: `build-error-resolver` for build failures
- **Agent**: `security-reviewer` for security issues
- **Agent**: `code-reviewer` for diff review
- **Skill**: `fix-linting` for lint errors
