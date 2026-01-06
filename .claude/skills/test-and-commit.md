---
name: test-and-commit
description: TDD workflow automation - test, format, commit with coverage tracking
tags: [tdd, testing, automation, workflow]
---

# DevSkyy TDD Workflow Automation

I'll execute a **Test-Driven Development workflow** with automatic formatting and smart commits.

## 🎯 TDD Workflow

```
Detect Changes → Find Tests → Run Tests → Format Code → Commit → Coverage Report
```

---

## Phase 1: Detect Modified Files 🔍

Identifying changed Python files...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "git diff --name-only HEAD 2>&1 | grep '\\.py$' || echo 'No Python files modified'",
  "description": "Detect modified Python files",
  "timeout": 10000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "git diff --cached --name-only 2>&1 | grep '\\.py$' || echo 'No staged Python files'",
  "description": "Detect staged Python files",
  "timeout": 10000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "git status --porcelain 2>&1 | grep '\\.py$' || echo 'No untracked Python files'",
  "description": "Detect untracked Python files",
  "timeout": 10000
}
</params>
</tool_call>

---

## Phase 2: Identify Test Files 🧪

Mapping code files to their test counterparts...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "for file in $(git diff --name-only HEAD | grep '\\.py$'); do module=$(echo \"$file\" | sed 's|/|.|g' | sed 's|\\.py$||'); test_file=\"tests/test_${module##*.}.py\"; if [ -f \"$test_file\" ]; then echo \"Found: $test_file for $file\"; else echo \"Missing: $test_file for $file\"; fi; done",
  "description": "Map modified files to test files",
  "timeout": 15000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "find tests -name 'test_*.py' -type f 2>&1 | wc -l | xargs echo 'Total test files:'",
  "description": "Count existing test files",
  "timeout": 10000
}
</params>
</tool_call>

---

## Phase 3: Run Test Suite 🚦

Executing pytest with coverage analysis...

### 3.1: Coverage Baseline (Before)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f .coverage ]; then coverage report --format=total 2>&1 || echo '0'; else echo 'No baseline coverage'; fi",
  "description": "Get current coverage baseline",
  "timeout": 15000
}
</params>
</tool_call>

### 3.2: Run Tests with Coverage

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "pytest tests/ -v --tb=short --maxfail=5 --cov=. --cov-report=term --cov-report=json --cov-report=html --junitxml=test-results.xml 2>&1",
  "description": "Run test suite with coverage",
  "timeout": 300000
}
</params>
</tool_call>

### 3.3: Coverage Analysis (After)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f coverage.json ]; then jq -r '.totals | \"Coverage: \\(.percent_covered | tonumber | floor)% (\\(.num_statements) statements, \\(.covered_lines) covered)\"' coverage.json 2>&1; else echo 'Coverage data not available'; fi",
  "description": "Parse coverage results",
  "timeout": 10000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f coverage.json ]; then jq -r '.files | to_entries[] | select(.value.summary.percent_covered < 70) | \"⚠️  Low coverage: \\(.key) (\\(.value.summary.percent_covered | floor)%)\"' coverage.json 2>&1 | head -10 || echo 'All files meet coverage threshold'; else echo 'Coverage data not available'; fi",
  "description": "Identify low-coverage files",
  "timeout": 10000
}
</params>
</tool_call>

---

## Phase 4: Format Code ✨

**Only if tests pass** - applying DevSkyy code standards...

### 4.1: Import Sorting (isort)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "isort . --diff 2>&1 | head -50",
  "description": "Preview import sorting changes",
  "timeout": 30000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "isort . 2>&1 | tail -5",
  "description": "Apply import sorting",
  "timeout": 45000
}
</params>
</tool_call>

### 4.2: Linting (ruff)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "ruff check --fix . 2>&1 | tail -10",
  "description": "Auto-fix ruff violations",
  "timeout": 60000
}
</params>
</tool_call>

### 4.3: Formatting (black)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "black . 2>&1 | tail -5",
  "description": "Format code with black",
  "timeout": 45000
}
</params>
</tool_call>

---

## Phase 5: Git Commit 📝

Creating commit with test results...

### 5.1: Stage Files

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "git add -A 2>&1",
  "description": "Stage all changes",
  "timeout": 15000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "git status --short 2>&1 | head -20",
  "description": "Show staged changes",
  "timeout": 10000
}
</params>
</tool_call>

### 5.2: Generate Commit Message

**User Input Required**: Provide commit message or accept auto-generated message

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== AUTO-GENERATED COMMIT MESSAGE ===' && echo '' && git diff --cached --stat 2>&1 | tail -3 && echo '' && if [ -f coverage.json ]; then coverage_pct=$(jq -r '.totals.percent_covered | floor' coverage.json); echo \"test: add tests with ${coverage_pct}% coverage\"; else echo \"test: update tests and code formatting\"; fi",
  "description": "Generate default commit message",
  "timeout": 10000
}
</params>
</tool_call>

### 5.3: Create Commit

**Note**: This step will prompt for commit message confirmation

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f coverage.json ]; then coverage_pct=$(jq -r '.totals.percent_covered | floor' coverage.json); commit_msg=\"test: update tests with ${coverage_pct}% coverage\n\n🧪 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>\"; else commit_msg=\"test: update tests and formatting\n\n🧪 Generated with [Claude Code](https://claude.com/claude-code)\n\nCo-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>\"; fi && git commit -m \"$(echo -e \"$commit_msg\")\" 2>&1",
  "description": "Create git commit",
  "timeout": 15000
}
</params>
</tool_call>

---

## Phase 6: Test Results Summary 📊

Generating comprehensive test report...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== TDD WORKFLOW SUMMARY ===' && echo '' && echo '📁 Files Changed:' && git diff HEAD~1 --stat 2>&1 | tail -5 && echo '' && echo '🧪 Test Results:' && if [ -f test-results.xml ]; then python3 -c \"import xml.etree.ElementTree as ET; tree = ET.parse('test-results.xml'); root = tree.getroot(); tests = root.get('tests', '0'); failures = root.get('failures', '0'); errors = root.get('errors', '0'); skipped = root.get('skipped', '0'); print(f'Total: {tests} | Passed: {int(tests) - int(failures) - int(errors) - int(skipped)} | Failed: {failures} | Errors: {errors} | Skipped: {skipped}')\" 2>&1; else echo 'Test results not available'; fi && echo '' && echo '📈 Coverage:' && if [ -f coverage.json ]; then jq -r '.totals | \"\\(.percent_covered | floor)% coverage (\\(.covered_lines)/\\(.num_statements) statements)\"' coverage.json 2>&1; else echo 'Coverage data not available'; fi",
  "description": "Generate summary report",
  "timeout": 20000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f coverage.json ]; then echo '=== TOP 5 FILES BY COVERAGE ===' && jq -r '.files | to_entries | sort_by(.value.summary.percent_covered) | reverse | .[:5][] | \"✅ \\(.key): \\(.value.summary.percent_covered | floor)%\"' coverage.json 2>&1; fi",
  "description": "Show top covered files",
  "timeout": 10000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f coverage.json ]; then echo '=== FILES NEEDING ATTENTION ===' && jq -r '.files | to_entries | sort_by(.value.summary.percent_covered) | .[:5][] | \"⚠️  \\(.key): \\(.value.summary.percent_covered | floor)%\"' coverage.json 2>&1; fi",
  "description": "Show files needing coverage improvement",
  "timeout": 10000
}
</params>
</tool_call>

---

## ✅ Success Criteria

**MUST PASS (Blocking):**

- [ ] All tests pass (0 failures, 0 errors)
- [ ] Coverage > 70% overall
- [ ] Code formatted (isort, ruff, black)
- [ ] Commit created successfully

**SHOULD PASS (Warnings):**

- [ ] Coverage delta positive (improved from baseline)
- [ ] No new low-coverage files introduced
- [ ] All modified files have corresponding tests

---

## 🚨 Error Handling

**If tests fail:**

1. Review failure output above
2. Fix failing tests
3. Re-run `/test-and-commit`
4. **DO NOT COMMIT** until tests pass

**If coverage drops:**

1. Identify files with low coverage
2. Add missing test cases
3. Re-run `/test-and-commit`

**If formatting fails:**

1. Review linting errors
2. Fix manually or run `/fix-linting`
3. Re-run `/test-and-commit`

---

## 📋 Manual Override

If you need to commit without running tests:

```bash
# Stage specific files only
git add path/to/file.py

# Commit with custom message
git commit -m "feat(module): description"

# Skip pre-commit hooks
git commit --no-verify
```

**Warning**: Manual commits bypass TDD workflow and may introduce regressions.

---

## 📝 Commit Message Conventions

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `test`: Add or update tests
- `refactor`: Code restructuring (no behavior change)
- `docs`: Documentation only
- `chore`: Maintenance tasks

**Examples**:
- `test(agents): add SuperAgent integration tests with 85% coverage`
- `feat(api): implement GDPR data export endpoint`
- `fix(mcp): resolve ToolRegistry serialization error`

---

## 🔄 Next Steps

After successful commit:

1. Review coverage report: `open htmlcov/index.html`
2. Check test results: `cat test-results.xml`
3. Push to remote: `git push origin <branch>`
4. Create pull request (if ready)

---

**TDD Workflow Version:** 1.0.0
**DevSkyy Compliance:** Test-first development enforced
**Per Directive:** CRITICAL_WORKFLOW_DIRECTIVE - tests must pass before commit
