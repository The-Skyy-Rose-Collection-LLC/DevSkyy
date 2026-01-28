# Verification Command

Run comprehensive verification on codebase.

## Order
1. **Build** - Run build, STOP if fails
2. **Types** - TypeScript check
3. **Lint** - Run linter
4. **Tests** - Run all tests + coverage
5. **Console.log** - Audit source files
6. **Git** - Show uncommitted changes

## Output
```
VERIFICATION: [PASS/FAIL]
Build:   [OK/FAIL]
Types:   [OK/X errors]
Lint:    [OK/X issues]
Tests:   [X/Y passed, Z% coverage]
Logs:    [OK/X console.logs]
Ready for PR: [YES/NO]
```

## Arguments
- `quick` - Build + types only
- `full` - All checks (default)
- `pre-commit` - Commit-relevant checks
- `pre-pr` - Full + security scan
