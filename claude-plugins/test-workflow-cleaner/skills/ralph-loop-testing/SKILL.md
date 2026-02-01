# Ralph Loop Testing

This skill provides knowledge for running tests with Ralph Loop - iterating continuously until all tests pass. It activates when users mention "ralph loop", "iterate tests", "fix until pass", "test loop", "keep running tests", or need to automatically fix failing tests.

---

## Ralph Loop Philosophy

**ITERATE UNTIL PERFECT.**

Ralph Loop is a perfectionist approach to testing:
1. Run all tests
2. If failures exist, analyze and fix
3. Repeat until 100% pass
4. Never ship failing tests

## Ralph Loop Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    RALPH LOOP TESTING                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐               │
│   │  RUN    │───▶│ ANALYZE │───▶│   FIX   │               │
│   │  TESTS  │    │ FAILURES│    │  CODE   │               │
│   └─────────┘    └─────────┘    └────┬────┘               │
│        ▲                             │                     │
│        │         ┌─────────┐         │                     │
│        └─────────│  LOOP   │◀────────┘                     │
│                  │  BACK   │                               │
│                  └─────────┘                               │
│                                                             │
│   Exit Condition: ALL TESTS PASS                           │
└─────────────────────────────────────────────────────────────┘
```

## Iteration Strategy

### Phase 1: Initial Run
```bash
# Python
pytest -v --tb=short 2>&1 | tee test_results.txt

# JavaScript
npm test 2>&1 | tee test_results.txt

# Go
go test -v ./... 2>&1 | tee test_results.txt
```

### Phase 2: Failure Analysis

Parse test output to categorize failures:

| Failure Type | Example | Fix Strategy |
|--------------|---------|--------------|
| Import Error | `ModuleNotFoundError` | Fix import path or install dependency |
| Assertion Error | `AssertionError: 1 != 2` | Fix logic or update expected value |
| Type Error | `TypeError: expected str` | Fix type mismatch |
| Attribute Error | `AttributeError: no 'foo'` | Add missing attribute or fix reference |
| Timeout | `TimeoutError` | Optimize or increase timeout |
| Mock Error | `MagicMock has no attribute` | Update mock configuration |

### Phase 3: Automated Fix

For each failure type, apply appropriate fix:

```python
def fix_failure(failure: dict) -> str:
    """Generate fix for a test failure."""

    if failure['type'] == 'import_error':
        # Check if module was renamed
        # Check if module was moved
        # Update import statement
        pass

    elif failure['type'] == 'assertion_error':
        # Analyze expected vs actual
        # If actual is correct, update assertion
        # If actual is wrong, fix source code
        pass

    elif failure['type'] == 'attribute_error':
        # Check if attribute was renamed
        # Check if class interface changed
        # Update test or add missing attribute
        pass
```

### Phase 4: Re-run and Validate

```bash
# Run only previously failed tests (pytest)
pytest --lf -v

# Run only changed test files
pytest tests/test_modified.py -v

# Full suite after fixes
pytest -v
```

## Context7 Integration

Use Context7 to fetch documentation when fixing failures:

```
When encountering:
- Framework-specific errors → Fetch framework docs
- Library errors → Fetch library docs
- Best practice questions → Search patterns

Example queries:
- "pytest fixture scope session"
- "jest mock module default export"
- "go test table driven"
```

## Memory Integration (Serena)

Track test patterns across sessions:

```markdown
# Test Memory

## Known Flaky Tests
- `test_api.py::test_timeout` - Occasional timeout on CI
- `test_integration.py::test_db` - Needs database cleanup

## Common Failure Patterns
- Import errors after refactoring `utils/` module
- Mock failures when `api.py` interface changes

## Successful Fix Patterns
- AssertionError in serialization → Check datetime format
- TypeError in API tests → Validate request body schema
```

## Ralph Loop Commands

### Start Loop
```bash
# Basic loop
ralph-loop pytest

# With max iterations
ralph-loop --max-iter 10 pytest

# With specific tests
ralph-loop pytest tests/test_api.py
```

### Loop Output Format
```
═══════════════════════════════════════════════════════════════
RALPH LOOP - ITERATION 1
═══════════════════════════════════════════════════════════════

Running: pytest -v
Result: 47 passed, 3 failed

FAILURES:
1. test_api.py::test_create_user - AssertionError
2. test_api.py::test_update_user - TypeError
3. test_utils.py::test_format_date - ValueError

Analyzing failures...
Applying fixes...

═══════════════════════════════════════════════════════════════
RALPH LOOP - ITERATION 2
═══════════════════════════════════════════════════════════════

Running: pytest --lf -v
Result: 2 passed, 1 failed

FAILURES:
1. test_utils.py::test_format_date - ValueError

Analyzing failures...
Applying fixes...

═══════════════════════════════════════════════════════════════
RALPH LOOP - ITERATION 3
═══════════════════════════════════════════════════════════════

Running: pytest -v
Result: 50 passed, 0 failed

✅ ALL TESTS PASSING

Total iterations: 3
Total time: 45.2s
Tests fixed: 3
```

## Fix Priority Order

1. **Syntax Errors** - Can't run other tests until fixed
2. **Import Errors** - Block entire test files
3. **Setup/Fixture Errors** - Block multiple tests
4. **Individual Test Failures** - Fix in order of complexity

## Common Fix Patterns

### Import Fixes
```python
# Before: Module moved
from old_path import func

# After: Updated import
from new_path import func
```

### Assertion Fixes
```python
# Before: Expected value outdated
assert result == "old_value"

# After: Updated to match new behavior
assert result == "new_value"
```

### Mock Fixes
```python
# Before: Mocking removed method
@patch('module.OldClass.old_method')

# After: Mock updated class/method
@patch('module.NewClass.new_method')
```

### Type Fixes
```python
# Before: Wrong type
result = get_data()  # Returns dict now, not list

# After: Handle new type
result = get_data()
assert isinstance(result, dict)
```

## Safety Guards

### Backup Before Fixes
```bash
# Create backup before modifications
cp test_file.py test_file.py.backup

# Restore if fix fails
mv test_file.py.backup test_file.py
```

### Validate Fixes
```python
def validate_fix(original: str, fixed: str) -> bool:
    """Ensure fix is valid before applying."""
    # Parse both versions
    try:
        ast.parse(original)
        ast.parse(fixed)
    except SyntaxError:
        return False

    # Ensure test count unchanged (unless intentional)
    original_tests = count_tests(original)
    fixed_tests = count_tests(fixed)

    return fixed_tests >= original_tests
```

### Track All Changes
```python
changes_log = []

def apply_fix(file: str, fix: dict):
    """Apply fix and log change."""
    original = read_file(file)
    fixed = apply_change(original, fix)
    write_file(file, fixed)

    changes_log.append({
        'file': file,
        'original': original,
        'fixed': fixed,
        'fix_type': fix['type'],
        'timestamp': datetime.now()
    })
```

## Exit Conditions

Ralph Loop exits when:
1. **All tests pass** (success)
2. **No progress made** for 3 iterations (stuck)
3. **Critical error** that can't be auto-fixed
4. **User interruption** (manual stop)

Never exit just because "it's taking too long" - perfectionism requires patience.
