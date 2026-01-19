---
name: analyze-tests
description: Scan the codebase to identify outdated, orphaned, and irrelevant tests. Generates a comprehensive analysis report.
---

# Analyze Tests Command

You have been asked to analyze the test suite. Follow this workflow:

## Step 1: Detect Testing Framework

First, identify what testing framework(s) this project uses:

```bash
# Check for common testing configs
ls -la pytest.ini conftest.py jest.config.* vitest.config.* go.mod Cargo.toml 2>/dev/null
```

## Step 2: Find All Test Files

Discover all test files based on the framework:

**Python (pytest):**
- Pattern: `test_*.py` or `*_test.py`
- Skip: `__pycache__`, `.venv`, `node_modules`

**JavaScript/TypeScript (jest/vitest):**
- Pattern: `*.test.js`, `*.spec.js`, `*.test.ts`, `*.spec.ts`
- Skip: `node_modules`, `dist`, `build`

**Go:**
- Pattern: `*_test.go`

**Rust:**
- Pattern: `*_test.rs` or inline `#[cfg(test)]`

## Step 3: Analyze Each Test File

For each test file, check:

1. **Import Health** - Do all imports resolve?
2. **Source Mapping** - Does the source file still exist?
3. **Skip Status** - Any skipped tests and for how long?
4. **Quality** - Are there empty tests or tests without assertions?
5. **Last Modified** - When was it last updated?

## Step 4: Generate Analysis Report

Produce a structured report:

```markdown
# Test Analysis Report

## Summary
- Test files scanned: X
- Total tests found: Y
- Issues detected: Z

## Critical Issues (Immediate Action Required)
| File | Issue | Details |
|------|-------|---------|
| ... | ... | ... |

## Warnings (Review Recommended)
| File | Issue | Details |
|------|-------|---------|
| ... | ... | ... |

## Candidates for Removal
| File | Reason | Last Modified |
|------|--------|---------------|
| ... | ... | ... |

## Test Coverage Gaps
| Source File | Missing Tests |
|-------------|---------------|
| ... | ... |
```

## Step 5: Save to Memory (Serena)

If Serena MCP is available, save the analysis results for future reference.

## Important Notes

- Use Context7 to look up framework-specific testing patterns if needed
- DO NOT delete or modify any tests - this is analysis only
- Flag tests for review, let the user or test-cleaner handle removal
- Include git history context when available
