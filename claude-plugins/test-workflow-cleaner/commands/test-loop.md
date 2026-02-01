---
name: test-loop
description: Run tests with Ralph Loop until 100% pass. Analyzes failures, applies fixes, and iterates until perfection.
---

# Test Loop Command (Ralph Loop)

You have been asked to run tests with Ralph Loop until everything passes. **NEVER GIVE UP.**

## Ralph Loop Philosophy

**PERFECTION THROUGH PERSISTENCE.**

The loop continues until:
- ✅ ALL tests pass (success)
- 🛑 Unfixable error (report to user)
- ⚠️ Same failures for 5+ iterations (stuck - ask for help)

## Step 1: Detect Framework

```bash
# Identify testing framework
test -f pytest.ini || test -f conftest.py && echo "pytest"
test -f jest.config.js || grep -q '"jest"' package.json 2>/dev/null && echo "jest"
test -f vitest.config.ts && echo "vitest"
test -f go.mod && echo "go test"
test -f Cargo.toml && echo "cargo test"
```

## Step 2: Initial Test Run

Run all tests and capture output:

```bash
# Python (pytest)
pytest -v --tb=short 2>&1 | tee test_output.txt

# JavaScript (Jest)
npm test 2>&1 | tee test_output.txt

# JavaScript (Vitest)
npx vitest run 2>&1 | tee test_output.txt

# Go
go test -v ./... 2>&1 | tee test_output.txt

# Rust
cargo test 2>&1 | tee test_output.txt
```

## Step 3: Parse and Analyze Failures

For each failure, determine:

| Aspect | Question |
|--------|----------|
| Type | Import? Assertion? Type? Timeout? |
| Location | Which file, function, line? |
| Expected | What was expected? |
| Actual | What was received? |
| Root Cause | Why did it fail? |

## Step 4: Apply Fixes

Fix based on failure type:

**Import Errors:**
- Update import paths
- Install missing dependencies
- Fix module references

**Assertion Errors:**
- Update expected values if behavior changed
- Fix source code if behavior is wrong
- Update test if assertion is outdated

**Type Errors:**
- Fix type mismatches
- Update function signatures
- Add type conversions

**Timeout Errors:**
- Optimize slow code
- Increase timeout limits
- Add async handling

## Step 5: Re-run and Iterate

```
ITERATION 1: 47 passed, 3 failed
→ Fix 3 failures
→ Re-run

ITERATION 2: 49 passed, 1 failed
→ Fix 1 failure
→ Re-run

ITERATION 3: 50 passed, 0 failed
✅ SUCCESS - ALL TESTS PASSING
```

## Step 6: Use Context7 When Stuck

When stuck on framework-specific issues:

- pytest fixture errors → search "pytest fixtures"
- jest mock issues → search "jest mocking modules"
- async test failures → search "[framework] async testing"
- type errors → search "[language] type annotations"

## Step 7: Save Patterns to Memory (Serena)

After completion, save to memory:
- Common failure patterns encountered
- Successful fix strategies used
- Flaky test history

## Output Format

```
═══════════════════════════════════════════════════════════════
RALPH LOOP - TEST RUNNER
═══════════════════════════════════════════════════════════════

Framework: [detected framework]
Initial run: X passed, Y failed

───────────────────────────────────────────────────────────────
ITERATION 1
───────────────────────────────────────────────────────────────

Failure 1: [file]::[test_name]
  Type: [error type]
  Expected: [expected value]
  Actual: [actual value]
  Fix: [description of fix applied]

Running tests again...

───────────────────────────────────────────────────────────────
ITERATION N
───────────────────────────────────────────────────────────────

Result: X passed, 0 failed

═══════════════════════════════════════════════════════════════
✅ ALL TESTS PASSING
═══════════════════════════════════════════════════════════════

Total iterations: N
Tests fixed: X
Final result: Y/Y passing (100%)
```

## Important Rules

1. **NEVER give up** - Keep iterating until all pass
2. **ALWAYS analyze** before fixing
3. **DOCUMENT** every fix applied
4. **USE Context7** when stuck on framework-specific issues
5. **SAVE patterns** to Serena memory
6. **BACKUP** before making changes to test files

**PERSISTENCE IS THE PATH TO PERFECTION.**
