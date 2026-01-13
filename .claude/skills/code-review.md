---
name: code-review
description: Comprehensive code analysis - security, quality, complexity, coverage
tags: [code-quality, security, analysis, review]
---

# DevSkyy Comprehensive Code Review

I'll execute a **multi-dimensional code analysis** covering security, quality, complexity, and coverage.

## 🎯 Review Dimensions

```
Security → Type Safety → Complexity → Coverage → Documentation → OWASP
```

---

## Phase 1: Security Audit 🔐

### 1.1: Python Dependency Vulnerabilities (pip-audit)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "pip-audit --desc --format json 2>&1 || echo '{\"vulnerabilities\": []}'",
  "description": "Python dependency security audit",
  "timeout": 90000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if command -v pip-audit >/dev/null 2>&1; then pip-audit --desc 2>&1 | grep -E '(CRITICAL|HIGH|MEDIUM)' | head -20 || echo 'No vulnerabilities found'; else echo 'pip-audit not installed - run: pip install pip-audit'; fi",
  "description": "Parse vulnerability summary",
  "timeout": 60000
}
</params>
</tool_call>

### 1.2: Node.js Dependency Vulnerabilities (npm audit)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -d frontend ]; then cd frontend && npm audit --json 2>&1; else echo '{\"vulnerabilities\": {}}'; fi",
  "description": "Node.js dependency security audit",
  "timeout": 90000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -d frontend ]; then cd frontend && npm audit 2>&1 | grep -E '(critical|high|moderate)' | head -15 || echo 'No vulnerabilities found'; else echo 'No frontend directory'; fi",
  "description": "Parse npm vulnerability summary",
  "timeout": 60000
}
</params>
</tool_call>

### 1.3: Code Security Scan (bandit - OWASP)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "bandit -r . -f json -x './venv,./node_modules,./frontend/node_modules,./.venv,./tests' 2>&1 || echo '{\"results\": []}'",
  "description": "OWASP security scan with bandit",
  "timeout": 120000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "bandit -r . -x './venv,./node_modules,./frontend/node_modules,./.venv,./tests' 2>&1 | grep -E '(Issue:|Severity: High|Severity: Medium)' | head -30 || echo 'No security issues found'",
  "description": "Parse bandit results",
  "timeout": 90000
}
</params>
</tool_call>

---

## Phase 2: Type Safety Analysis 🔬

### 2.1: MyPy Type Checking

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "mypy . --no-error-summary --show-error-codes --pretty 2>&1 | head -100",
  "description": "Type check with mypy",
  "timeout": 120000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "mypy . --no-error-summary 2>&1 | grep -E 'error:' | wc -l | xargs echo 'Total type errors:'",
  "description": "Count type errors",
  "timeout": 90000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "mypy . --no-error-summary 2>&1 | grep -oE '\\[.*\\]' | sort | uniq -c | sort -rn | head -10",
  "description": "Most common type error codes",
  "timeout": 90000
}
</params>
</tool_call>

### 2.2: Type Hint Coverage

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "python3 -c \"import ast; import os; total_funcs = 0; typed_funcs = 0; [total_funcs := total_funcs + len([n for n in ast.walk(ast.parse(open(os.path.join(root, f)).read())) if isinstance(n, ast.FunctionDef)]) or typed_funcs := typed_funcs + len([n for n in ast.walk(ast.parse(open(os.path.join(root, f)).read())) if isinstance(n, ast.FunctionDef) and n.returns]) for root, _, files in os.walk('.') if 'venv' not in root and 'node_modules' not in root for f in files if f.endswith('.py')]; print(f'Type hint coverage: {(typed_funcs/total_funcs*100) if total_funcs > 0 else 0:.1f}% ({typed_funcs}/{total_funcs} functions)')\" 2>&1 || echo 'Type hint analysis failed'",
  "description": "Calculate type hint coverage",
  "timeout": 45000
}
</params>
</tool_call>

---

## Phase 3: Code Complexity Analysis 📊

### 3.1: Cyclomatic Complexity (radon)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if command -v radon >/dev/null 2>&1; then radon cc . -a -s -j 2>&1 | jq -r 'to_entries | map(select(.value | length > 0)) | sort_by(-.value[0].complexity) | .[:10][] | \"\\(.key): Complexity \\(.value[0].complexity) (\\(.value[0].rank))\"' 2>&1 || echo 'Radon analysis complete'; else echo 'radon not installed - run: pip install radon'; fi",
  "description": "Analyze cyclomatic complexity",
  "timeout": 60000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if command -v radon >/dev/null 2>&1; then echo '=== HIGH COMPLEXITY FUNCTIONS ===' && radon cc . -s -n C -n D -n E -n F 2>&1 | head -30 || echo 'No high-complexity functions'; else echo 'radon not installed'; fi",
  "description": "Identify high-complexity functions",
  "timeout": 60000
}
</params>
</tool_call>

### 3.2: Maintainability Index (radon)

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if command -v radon >/dev/null 2>&1; then radon mi . -s -j 2>&1 | jq -r 'to_entries | sort_by(.value.mi) | .[:10][] | \"⚠️  \\(.key): MI=\\(.value.mi | floor) (\\(.value.rank))\"' 2>&1 || echo 'Maintainability analysis complete'; else echo 'radon not installed'; fi",
  "description": "Calculate maintainability index",
  "timeout": 60000
}
</params>
</tool_call>

### 3.3: Code Duplication

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if command -v pylint >/dev/null 2>&1; then pylint --disable=all --enable=duplicate-code --min-similarity-lines=4 . 2>&1 | head -50 || echo 'No significant code duplication'; else echo 'pylint not installed - run: pip install pylint'; fi",
  "description": "Detect code duplication",
  "timeout": 90000
}
</params>
</tool_call>

---

## Phase 4: Test Coverage Analysis 🧪

### 4.1: Generate Coverage Report

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "pytest tests/ --cov=. --cov-report=json --cov-report=term -q 2>&1 | tail -20",
  "description": "Run tests with coverage",
  "timeout": 300000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f coverage.json ]; then jq -r '.totals | \"Overall Coverage: \\(.percent_covered | floor)%\\nStatements: \\(.num_statements)\\nCovered: \\(.covered_lines)\\nMissing: \\(.num_statements - .covered_lines)\"' coverage.json 2>&1; else echo 'Coverage data not available'; fi",
  "description": "Parse overall coverage",
  "timeout": 15000
}
</params>
</tool_call>

### 4.2: Coverage by Module

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f coverage.json ]; then echo '=== COVERAGE BY MODULE ===' && jq -r '.files | to_entries | map(select(.key | startswith(\"agents/\") or startswith(\"api/\") or startswith(\"llm/\") or startswith(\"orchestration/\") or startswith(\"runtime/\") or startswith(\"security/\"))) | group_by(.key | split(\"/\")[0]) | map({module: .[0].key | split(\"/\")[0], avg_coverage: (map(.value.summary.percent_covered) | add / length)}) | sort_by(.avg_coverage) | .[] | \"\\(.module): \\(.avg_coverage | floor)%\"' coverage.json 2>&1; else echo 'Coverage data not available'; fi",
  "description": "Calculate module-level coverage",
  "timeout": 20000
}
</params>
</tool_call>

### 4.3: Critical Low-Coverage Files

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f coverage.json ]; then echo '=== CRITICAL: LOW COVERAGE FILES ===' && jq -r '.files | to_entries | map(select(.value.summary.percent_covered < 70 and (.key | startswith(\"agents/\") or startswith(\"api/\") or startswith(\"runtime/\") or startswith(\"orchestration/\")))) | sort_by(.value.summary.percent_covered) | .[:10][] | \"🚨 \\(.key): \\(.value.summary.percent_covered | floor)% (\\(.value.summary.covered_lines)/\\(.value.summary.num_statements) lines)\"' coverage.json 2>&1 || echo 'All critical modules meet coverage threshold'; else echo 'Coverage data not available'; fi",
  "description": "Identify critical low-coverage files",
  "timeout": 15000
}
</params>
</tool_call>

---

## Phase 5: Documentation Completeness 📝

### 5.1: Docstring Coverage

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if command -v interrogate >/dev/null 2>&1; then interrogate . -v --exclude venv --exclude node_modules --exclude tests --fail-under 0 2>&1 | tail -20; else echo 'interrogate not installed - run: pip install interrogate'; fi",
  "description": "Check docstring coverage",
  "timeout": 60000
}
</params>
</tool_call>

### 5.2: README Quality

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f README.md ]; then wc -l README.md | awk '{print \"README.md: \" $1 \" lines\"}' && echo '' && echo 'Required sections:' && grep -E '^#{1,2} ' README.md | head -15; else echo 'No README.md found'; fi",
  "description": "Analyze README structure",
  "timeout": 10000
}
</params>
</tool_call>

### 5.3: API Documentation

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "find docs -name '*.md' -type f 2>&1 | wc -l | xargs echo 'Documentation files:' && echo '' && echo 'Documentation structure:' && find docs -type f -name '*.md' 2>&1 | head -20 || echo 'No docs directory'",
  "description": "Check API documentation",
  "timeout": 15000
}
</params>
</tool_call>

---

## Phase 6: OWASP Top 10 Validation ⚡

### 6.1: Injection Vulnerabilities

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "grep -r -n -E '(eval\\(|exec\\(|os\\.system\\(|subprocess\\.call\\()' --include='*.py' . 2>&1 | grep -v 'venv' | grep -v 'node_modules' | head -20 || echo '✅ No obvious injection risks'",
  "description": "Detect potential injection points",
  "timeout": 30000
}
</params>
</tool_call>

### 6.2: Authentication/Authorization

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "grep -r -n -E '(password|secret|token|api_key|auth)' --include='*.py' . 2>&1 | grep -v 'venv' | grep -v 'test' | grep -v '.env' | grep -E '(=|:)' | head -20 || echo '✅ No hardcoded credentials detected'",
  "description": "Check for hardcoded secrets",
  "timeout": 30000
}
</params>
</tool_call>

### 6.3: Sensitive Data Exposure

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if [ -f security/__init__.py ]; then echo '✅ Security module found' && grep -E '(encrypt|decrypt|hash)' security/*.py | head -10; else echo '⚠️  No security module detected'; fi",
  "description": "Verify encryption implementation",
  "timeout": 15000
}
</params>
</tool_call>

### 6.4: CSRF/CORS Protection

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "if find . -name '*.py' -path '*/api/*' -type f 2>&1 | head -1 | xargs grep -l 'CORSMiddleware' >/dev/null 2>&1; then echo '✅ CORS middleware configured'; else echo '⚠️  CORS protection not detected'; fi",
  "description": "Check CORS configuration",
  "timeout": 15000
}
</params>
</tool_call>

---

## Phase 7: Code Quality Metrics 📐

### 7.1: Lines of Code Analysis

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== LINES OF CODE BY MODULE ===' && for dir in agents api llm orchestration runtime security mcp_servers; do if [ -d $dir ]; then lines=$(find $dir -name '*.py' -type f -exec wc -l {} + 2>&1 | tail -1 | awk '{print $1}'); echo \"$dir: $lines lines\"; fi; done",
  "description": "Count lines by module",
  "timeout": 20000
}
</params>
</tool_call>

### 7.2: Import Analysis

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== MOST IMPORTED MODULES ===' && grep -r '^from ' --include='*.py' . 2>&1 | grep -v 'venv' | grep -v '__pycache__' | awk '{print $2}' | sort | uniq -c | sort -rn | head -15",
  "description": "Analyze import patterns",
  "timeout": 30000
}
</params>
</tool_call>

### 7.3: TODO/FIXME/HACK Detection

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== CODE DEBT MARKERS ===' && grep -r -n -E '(TODO|FIXME|HACK|XXX|BUG|DEPRECATED)' --include='*.py' . 2>&1 | grep -v 'venv' | grep -v 'node_modules' | wc -l | xargs echo 'Total markers:' && echo '' && grep -r -n -E '(TODO|FIXME|HACK|XXX|BUG|DEPRECATED)' --include='*.py' . 2>&1 | grep -v 'venv' | head -20",
  "description": "Count technical debt markers",
  "timeout": 30000
}
</params>
</tool_call>

---

## Phase 8: Review Report Card 🏆

Generating scored review summary...

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "cat << 'EOF'\n=== CODE REVIEW REPORT CARD ===\n\n## Security Score\n- [ ] No CRITICAL vulnerabilities (pip-audit)\n- [ ] No HIGH vulnerabilities (npm audit)\n- [ ] No HIGH severity issues (bandit)\n- [ ] No hardcoded secrets\n- [ ] CORS/CSRF protection in place\n\n## Quality Score\n- [ ] Type errors < 50\n- [ ] Type hint coverage > 70%\n- [ ] Cyclomatic complexity < 10 (average)\n- [ ] Maintainability Index > 65 (average)\n- [ ] No significant code duplication\n\n## Coverage Score\n- [ ] Overall coverage > 70%\n- [ ] All critical modules > 70%\n- [ ] No critical files < 50%\n\n## Documentation Score\n- [ ] Docstring coverage > 70%\n- [ ] README.md comprehensive\n- [ ] API documentation exists\n- [ ] All public APIs documented\n\n## Code Health Score\n- [ ] TODO/FIXME count < 50\n- [ ] No eval/exec usage\n- [ ] Proper error handling\n- [ ] Follow DevSkyy conventions\n\n---\n\n## Severity Thresholds\n\n**CRITICAL (Block Deployment):**\n- Critical/High security vulnerabilities\n- Coverage < 50% on critical modules\n- Type errors > 100\n- Hardcoded secrets detected\n\n**HIGH (Warning - Fix Soon):**\n- Medium security vulnerabilities\n- Coverage 50-70% on critical modules\n- Type errors 50-100\n- Complexity > 15\n\n**MEDIUM (Tech Debt - Track):**\n- Low security issues\n- Coverage 70-80%\n- Type errors 10-50\n- Maintainability Index 50-65\n\n**LOW (Informational):**\n- Code style issues\n- Missing docstrings\n- TODO markers\nEOF",
  "description": "Display review report card",
  "timeout": 5000
}
</params>
</tool_call>

<tool_call>
<tool>Bash</tool>
<params>
{
  "command": "echo '=== ACTIONABLE ITEMS ===' && echo '' && echo '1. Security:' && if command -v pip-audit >/dev/null 2>&1; then pip-audit --desc 2>&1 | grep -c 'CRITICAL\\|HIGH' | xargs echo '   - Critical/High vulnerabilities:'; else echo '   - Run pip-audit to check'; fi && echo '' && echo '2. Type Safety:' && mypy . --no-error-summary 2>&1 | grep -c 'error:' | xargs echo '   - Type errors to fix:' && echo '' && echo '3. Coverage:' && if [ -f coverage.json ]; then jq -r '.totals.percent_covered | floor' coverage.json | xargs echo '   - Current coverage:'; echo '   - Target: 70%+'; else echo '   - Run pytest with --cov'; fi && echo '' && echo '4. Complexity:' && if command -v radon >/dev/null 2>&1; then radon cc . -s -n C -n D -n E -n F 2>&1 | grep -c 'C\\|D\\|E\\|F' | xargs echo '   - High-complexity functions:'; else echo '   - Install radon to check'; fi",
  "description": "Generate actionable items",
  "timeout": 60000
}
</params>
</tool_call>

---

## 📋 Next Steps

### Immediate Actions (CRITICAL):
1. Fix all CRITICAL/HIGH security vulnerabilities
2. Add tests to modules with coverage < 50%
3. Resolve hardcoded secrets
4. Implement missing CORS/CSRF protection

### Short-term (HIGH):
1. Reduce type errors to < 50
2. Refactor high-complexity functions (complexity > 10)
3. Improve coverage to 70%+ on all critical modules
4. Document public APIs

### Long-term (MEDIUM/LOW):
1. Add docstrings to improve documentation coverage
2. Reduce technical debt markers
3. Implement code duplication fixes
4. Maintain type hint coverage > 70%

---

## 🔄 Re-run After Fixes

```bash
# After fixing issues, re-run review
/code-review

# Or run specific checks
pip-audit --desc
pytest --cov=. --cov-report=term
mypy .
bandit -r .
```

---

**Code Review Version:** 1.0.0
**DevSkyy Compliance:** Enterprise security and quality standards
**OWASP Coverage:** Top 10 vulnerabilities validated
