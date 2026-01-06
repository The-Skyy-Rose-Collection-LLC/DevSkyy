---
name: fix-linting
description: Auto-detect and fix all ruff/linting errors to meet DevSkyy code standards
tags: [code-quality, linting, automation, tdd]
---

# DevSkyy Linting Auto-Fix

I'll automatically detect and fix all linting errors to meet DevSkyy's enterprise code standards.

## 🎯 Linting Standards

**DevSkyy Requirements:**

- ✅ Type annotations: `X | Y` instead of `Union[X, Y]` (UP007)
- ✅ No unused variables (F841)
- ✅ Modern isinstance checks (UP038)
- ✅ Simplified conditionals (SIM118)
- ✅ Proper import sorting (isort)
- ✅ Consistent formatting (black)

---

## Phase 1: Detect Current Issues 🔍

Running comprehensive linting analysis...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "ruff check . --output-format=json 2>&1 | jq -r 'if type == \"array\" then \"Found \\(length) linting issues\" else . end'",
  "description": "Detect ruff linting issues",
  "timeout": 60000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "isort --check-only --diff . 2>&1 | head -50",
  "description": "Check import sorting",
  "timeout": 45000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "black --check . 2>&1 | head -50",
  "description": "Check code formatting",
  "timeout": 45000
}
</params>
</tool_call>

---

## Phase 2: Apply Auto-Fixes ✨

Applying automated fixes...

### 2.1: Import Sorting (isort)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "isort . 2>&1",
  "description": "Sort imports with isort",
  "timeout": 60000
}
</params>
</tool_call>

### 2.2: Ruff Auto-Fix

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "ruff check --fix . 2>&1",
  "description": "Auto-fix ruff violations",
  "timeout": 90000
}
</params>
</tool_call>

### 2.3: Code Formatting (black)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "black . 2>&1",
  "description": "Format code with black",
  "timeout": 60000
}
</params>
</tool_call>

---

## Phase 3: Verify Zero Errors ✅

Verifying all issues resolved...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "ruff check . 2>&1 || echo 'RUFF_ERRORS_FOUND'",
  "description": "Verify ruff compliance",
  "timeout": 45000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "isort --check-only . 2>&1 || echo 'ISORT_ERRORS_FOUND'",
  "description": "Verify import sorting",
  "timeout": 30000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "black --check . 2>&1 || echo 'BLACK_ERRORS_FOUND'",
  "description": "Verify formatting",
  "timeout": 30000
}
</params>
</tool_call>

---

## Phase 4: Type Checking (Optional) 🔬

Running mypy type checker...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "mypy . --no-error-summary 2>&1 | head -100 || echo 'Type checking completed with warnings'",
  "description": "Type check codebase",
  "timeout": 90000
}
</params>
</tool_call>

---

## Phase 5: Summary Report 📊

Generating linting summary...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== LINTING SUMMARY ===' && echo '' && echo 'Ruff:' && (ruff check . 2>&1 | tail -5 || echo '✅ All checks passed') && echo '' && echo 'Isort:' && (isort --check-only . 2>&1 | tail -3 || echo '✅ All imports sorted') && echo '' && echo 'Black:' && (black --check . 2>&1 | tail -3 || echo '✅ All code formatted')",
  "description": "Generate summary report",
  "timeout": 30000
}
</params>
</tool_call>

---

## ✅ Success Criteria

**MUST PASS (Blocking):**

- [ ] `ruff check .` returns zero errors
- [ ] `isort --check-only .` passes
- [ ] `black --check .` passes

**SHOULD PASS (Warnings):**

- [ ] `mypy .` has no new errors
- [ ] All existing functionality preserved

---

## 🚨 Next Steps

If all checks pass:

1. Review changed files: `git status`
2. View diff: `git diff`
3. Commit changes: `git add . && git commit -m "fix(lint): resolve all ruff/linting violations"`

If errors remain:

1. Review error output above
2. Manually fix remaining issues
3. Re-run `/fix-linting`

---

## 📝 Common Fixes Applied

**Type Annotations:**

```python
# Before
from typing import Union
def func(x: Union[str, int]) -> None: ...

# After
def func(x: str | int) -> None: ...
```

**Unused Variables:**

```python
# Before
result = expensive_operation()  # F841: unused

# After
_ = expensive_operation()  # or remove if truly unused
```

**Modern isinstance:**

```python
# Before
if isinstance(x, (str, bytes)):

# After
if isinstance(x, str | bytes):
```

---

**Linting Workflow Version:** 1.0.0
**DevSkyy Compliance:** ABSOLUTE RULES enforced
**Per Directive:** CRITICAL_WORKFLOW_DIRECTIVE - must fix before proceeding
