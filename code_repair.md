# Code Repair Guide

## 🔧 Overview

DevSkyy includes a comprehensive automated code repair system with multiple agents designed to maintain code quality, fix issues, and ensure security compliance. This guide documents the available repair tools, workflows, and best practices.

**Last Updated:** November 2024  
**Version:** 5.0.0  
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Repair Agents Overview](#repair-agents-overview)
2. [Scanner Agents](#scanner-agents)
3. [Fixer Agents](#fixer-agents)
4. [Enhanced Auto-Fix System](#enhanced-auto-fix-system)
5. [Usage Examples](#usage-examples)
6. [Repair Workflows](#repair-workflows)
7. [Security Repairs](#security-repairs)
8. [Performance Optimization](#performance-optimization)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## Repair Agents Overview

DevSkyy provides three tiers of automated code repair:

### Available Agents

| Agent | Version | Purpose | Status |
|-------|---------|---------|--------|
| Scanner V1 | 1.0.0 | Basic code scanning | ✅ Active |
| Scanner V2 | 2.0.0 | Enterprise scanning with ML | ✅ Active |
| Fixer V1 | 1.0.0 | Basic automated fixes | ✅ Active |
| Fixer V2 | 2.0.0 | AI-powered repairs | ✅ Active |
| Enhanced AutoFix | 1.0.0 | Complete repair workflow | ✅ Active |
| Universal Self-Healing | 1.0.0 | Autonomous repair system | ✅ Active |

### Capabilities Matrix

| Capability | Scanner V1 | Scanner V2 | Fixer V1 | Fixer V2 | Enhanced AutoFix |
|------------|------------|------------|----------|----------|------------------|
| Syntax Error Detection | ✅ | ✅ | ✅ | ✅ | ✅ |
| Security Scanning | ⚠️ Basic | ✅ Advanced | ❌ | ✅ | ✅ |
| Performance Analysis | ❌ | ✅ | ❌ | ✅ | ✅ |
| Multi-Language | ✅ | ✅ | ✅ | ✅ | ✅ |
| AI-Powered Fixes | ❌ | ❌ | ❌ | ✅ | ✅ |
| Git Integration | ❌ | ❌ | ❌ | ⚠️ | ✅ |
| Backup/Rollback | ❌ | ❌ | ✅ | ✅ | ✅ |
| Self-Healing | ❌ | ✅ | ❌ | ✅ | ✅ |

---

## Scanner Agents

### Scanner V1 (`agent/modules/backend/scanner.py`)

**Purpose:** Basic code quality and error detection

#### Features
- Python, JavaScript, HTML, CSS, JSON syntax checking
- Code quality issues (line length, complexity)
- TODO/FIXME comment detection
- Basic security pattern matching
- File-level and project-level scanning

#### Usage

```python
from agent.modules.backend.scanner import scan_site

# Scan entire project
results = scan_site()

print(f"Files scanned: {results['files_scanned']}")
print(f"Errors found: {results['errors']}")
print(f"Warnings: {results['warnings']}")
```

#### Scan Output Structure

```json
{
  "files_scanned": 127,
  "errors": [
    {
      "file": "main.py",
      "line": 45,
      "type": "syntax_error",
      "message": "Missing colon after function definition",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "file": "utils.py",
      "line": 12,
      "type": "code_quality",
      "message": "Line too long (125 > 119 characters)",
      "severity": "warning"
    }
  ],
  "info": [
    {
      "file": "config.py",
      "line": 8,
      "type": "todo",
      "message": "TODO: Implement caching",
      "severity": "info"
    }
  ]
}
```

---

### Scanner V2 (`agent/modules/backend/scanner_v2.py`)

**Purpose:** Enterprise-grade scanning with ML and orchestration

#### Features
- All Scanner V1 features
- Multi-threaded scanning for performance
- Security vulnerability detection (OWASP Top 10)
- Dependency analysis
- Performance bottleneck identification
- Real-time health monitoring
- Integration with orchestrator
- ML-powered pattern detection

#### Advanced Security Patterns Detected

```python
security_patterns = {
    "hardcoded_secret": "password|secret|api_key in assignments",
    "sql_injection": "SQL queries with string concatenation",
    "xss_vulnerability": "innerHTML or dangerouslySetInnerHTML usage",
    "command_injection": "os.system or subprocess with user input",
    "path_traversal": "../ patterns in file operations",
    "insecure_crypto": "MD5, SHA1 usage for passwords"
}
```

#### Usage

```python
from agent.modules.backend.scanner_v2 import ScannerAgentV2

scanner = ScannerAgentV2()
await scanner.initialize()

# Comprehensive scan
results = await scanner.execute_core_function(
    scan_type="comprehensive",
    include_security=True,
    include_performance=True,
    deep_scan=True
)

# Security-focused scan
security_results = await scanner.execute_core_function(
    scan_type="security",
    include_dependencies=True
)

# Performance analysis
perf_results = await scanner.execute_core_function(
    scan_type="performance",
    profile_code=True
)
```

#### Output Structure

```json
{
  "scan_id": "scan_1699999999",
  "timestamp": "2024-11-11T09:00:00Z",
  "files_scanned": 245,
  "scan_duration": "2.3s",
  "errors": 3,
  "warnings": 15,
  "security_issues": 2,
  "performance_issues": 5,
  "issues": [
    {
      "file": "api/auth.py",
      "line": 89,
      "type": "security",
      "severity": "high",
      "issue": "Hardcoded API key detected",
      "recommendation": "Move to environment variable",
      "fix_available": true
    }
  ],
  "metrics": {
    "code_quality_score": 85,
    "security_score": 78,
    "performance_score": 92
  }
}
```

---

## Fixer Agents

### Fixer V1 (`agent/modules/backend/fixer.py`)

**Purpose:** Basic automated code repair

#### Features
- Syntax error correction
- Code formatting (autopep8 for Python)
- Import optimization
- Basic pattern-based fixes
- File backup before modification

#### Usage

```python
from agent.modules.backend.fixer import fix_issues

# Fix all issues from scan
scan_results = scan_site()
fix_results = fix_issues(scan_results)

print(f"Fixes applied: {fix_results['fixes_applied']}")
print(f"Files modified: {fix_results['files_modified']}")
```

#### Supported Fix Types

| Fix Type | Description | Language |
|----------|-------------|----------|
| `syntax_error` | Missing colons, brackets, quotes | Python, JS |
| `formatting` | Code style, indentation, spacing | Python, JS |
| `import_sort` | Organize imports alphabetically | Python |
| `unused_imports` | Remove unused imports | Python, JS |
| `line_length` | Break long lines | All |

---

### Fixer V2 (`agent/modules/backend/fixer_v2.py`)

**Purpose:** AI-powered enterprise code repair

#### Features
- All Fixer V1 features
- AI-powered fix generation (Claude/OpenAI)
- Security vulnerability patching
- Performance optimization fixes
- Multi-language support (Python, JS, TS, HTML, CSS)
- Safe backup and rollback
- Dry-run mode for previewing fixes

#### Usage

```python
from agent.modules.backend.fixer_v2 import FixerAgentV2

fixer = FixerAgentV2()
await fixer.initialize()

# Auto-fix with AI assistance
results = await fixer.execute_core_function(
    scan_results=scan_results,
    fix_type="auto",
    create_backup=True,
    dry_run=False
)

# Security-focused fixes only
security_fixes = await fixer.execute_core_function(
    scan_results=scan_results,
    fix_type="security",
    create_backup=True
)

# Preview fixes without applying
preview = await fixer.execute_core_function(
    scan_results=scan_results,
    dry_run=True
)
```

#### Advanced Fix Capabilities

```python
fix_capabilities = {
    # Python
    "python_print_to_logger": "Convert print() to logger.info()",
    "python_except_bare": "Add exception type to bare except",
    "python_type_hints": "Add missing type hints (AI)",
    "python_docstrings": "Generate missing docstrings (AI)",
    
    # JavaScript/TypeScript
    "js_var_to_const": "Replace var with const/let",
    "js_console_removal": "Comment out console.log",
    "js_arrow_functions": "Convert to arrow functions",
    "ts_any_types": "Replace 'any' with proper types (AI)",
    
    # Security
    "security_hardcoded_secrets": "Move to environment variables",
    "security_sql_injection": "Use parameterized queries",
    "security_xss": "Sanitize user input",
    
    # Performance
    "perf_n_plus_one": "Optimize database queries",
    "perf_caching": "Add caching where beneficial",
    "perf_async": "Convert to async/await"
}
```

#### Output Structure

```json
{
  "fix_id": "fix_1699999999",
  "timestamp": "2024-11-11T09:00:00Z",
  "fixes_applied": 12,
  "files_modified": 8,
  "backup_created": true,
  "backup_path": ".agent_backups/backup_1699999999",
  "fixes": [
    {
      "file": "api/auth.py",
      "line": 89,
      "type": "security",
      "before": "api_key = \"sk-1234567890\"",
      "after": "api_key = os.getenv(\"API_KEY\")",
      "description": "Moved hardcoded secret to environment variable",
      "ai_generated": true
    }
  ],
  "rollback_available": true
}
```

---

## Enhanced Auto-Fix System

### Enhanced AutoFix (`agent/modules/backend/enhanced_autofix.py`)

**Purpose:** Complete automated repair workflow with Git integration

#### Features
- Integrates Scanner + Fixer agents
- Automatic Git branch creation
- Multi-stage fixing pipeline
- Automated commit creation
- Rollback support
- Comprehensive reporting

#### Workflow Stages

1. **Initialization** - Create fix branch, backup state
2. **Scanning** - Comprehensive code analysis
3. **Basic Fixes** - Apply automated fixes
4. **Advanced Fixes** - AI-powered improvements
5. **Verification** - Re-scan to confirm fixes
6. **Commit** - Auto-commit with detailed message
7. **Report** - Generate fix summary

#### Usage

```python
from agent.modules.backend.enhanced_autofix import EnhancedAutoFix

autofix = EnhancedAutoFix()

# Run complete auto-fix workflow
results = autofix.run_enhanced_autofix(
    create_branch=True,
    branch_name="autofix/code-improvements",
    auto_commit=True,
    fix_types=["syntax", "security", "performance", "formatting"]
)

print(f"Branch: {results['fix_branch']}")
print(f"Total fixes: {results['total_fixes']}")
print(f"Commit: {results['commit_results']['commit_hash']}")
```

#### Fix Types

| Fix Type | Description | Examples |
|----------|-------------|----------|
| `syntax` | Syntax errors and basic issues | Missing colons, unmatched brackets |
| `security` | Security vulnerabilities | Hardcoded secrets, SQL injection |
| `performance` | Performance optimizations | N+1 queries, caching opportunities |
| `formatting` | Code style and formatting | Line length, indentation, imports |
| `quality` | Code quality improvements | Type hints, docstrings, naming |

#### Advanced Fix Example

```python
# Run with specific fix types
results = autofix.run_enhanced_autofix(
    create_branch=True,
    branch_name="autofix/security-improvements",
    auto_commit=True,
    fix_types=["security"]
)

# Results include:
{
  "session_id": "autofix_1699999999",
  "status": "completed",
  "branch_created": true,
  "original_branch": "main",
  "fix_branch": "autofix/security-improvements",
  "total_fixes": 8,
  "scan_results": {...},
  "fix_results": {...},
  "advanced_fixes": {...},
  "commit_results": {
    "commit_hash": "abc123def456",
    "message": "fix: automated security improvements\n\n- Removed 3 hardcoded secrets\n- Fixed 2 SQL injection vulnerabilities\n- Added input sanitization to 3 endpoints"
  }
}
```

---

## Usage Examples

### Example 1: Quick Code Scan

```python
from agent.modules.backend.scanner_v2 import ScannerAgentV2

async def quick_scan():
    scanner = ScannerAgentV2()
    await scanner.initialize()
    
    results = await scanner.execute_core_function(
        scan_type="quick",
        include_security=True
    )
    
    print(f"Files scanned: {results['files_scanned']}")
    print(f"Issues found: {len(results['issues'])}")
    
    for issue in results['issues']:
        if issue['severity'] == 'high':
            print(f"⚠️ {issue['file']}:{issue['line']} - {issue['issue']}")
```

### Example 2: Security-Focused Repair

```python
from agent.modules.backend.scanner_v2 import ScannerAgentV2
from agent.modules.backend.fixer_v2 import FixerAgentV2

async def security_repair():
    # Scan for security issues
    scanner = ScannerAgentV2()
    await scanner.initialize()
    
    scan_results = await scanner.execute_core_function(
        scan_type="security",
        include_dependencies=True
    )
    
    # Fix security issues
    fixer = FixerAgentV2()
    await fixer.initialize()
    
    fix_results = await fixer.execute_core_function(
        scan_results=scan_results,
        fix_type="security",
        create_backup=True
    )
    
    print(f"Security fixes applied: {fix_results['fixes_applied']}")
    print(f"Backup: {fix_results['backup_path']}")
```

### Example 3: Complete Project Repair

```python
from agent.modules.backend.enhanced_autofix import EnhancedAutoFix

def complete_repair():
    autofix = EnhancedAutoFix()
    
    results = autofix.run_enhanced_autofix(
        create_branch=True,
        branch_name="autofix/complete-repair",
        auto_commit=True,
        fix_types=["syntax", "security", "performance", "formatting", "quality"]
    )
    
    if results['status'] == 'completed':
        print(f"✅ Repair completed on branch: {results['fix_branch']}")
        print(f"📊 Total fixes: {results['total_fixes']}")
        print(f"💾 Commit: {results['commit_results']['commit_hash']}")
    else:
        print(f"❌ Repair failed: {results.get('error')}")
```

### Example 4: Dry Run (Preview Fixes)

```python
from agent.modules.backend.fixer_v2 import FixerAgentV2

async def preview_fixes():
    fixer = FixerAgentV2()
    await fixer.initialize()
    
    # Preview without applying
    preview = await fixer.execute_core_function(
        scan_results=scan_results,
        dry_run=True
    )
    
    print("Preview of fixes:")
    for fix in preview['fixes']:
        print(f"\n📝 {fix['file']}:{fix['line']}")
        print(f"Before: {fix['before']}")
        print(f"After:  {fix['after']}")
        print(f"Reason: {fix['description']}")
```

---

## Repair Workflows

### Workflow 1: Daily Code Maintenance

**Schedule:** Daily at 2 AM (automated)

```bash
# Via GitHub Actions or cron
python -m agent.modules.backend.enhanced_autofix \
  --create-branch \
  --branch-name "autofix/daily-$(date +%Y%m%d)" \
  --auto-commit \
  --fix-types "syntax,formatting,quality"
```

### Workflow 2: Pre-Deployment Security Check

**Trigger:** Before production deployment

```bash
# Run security scan and fix
python -m agent.modules.backend.scanner_v2 --scan-type security
python -m agent.modules.backend.fixer_v2 --fix-type security --create-backup
```

### Workflow 3: Performance Optimization

**Trigger:** Weekly or on-demand

```bash
# Scan for performance issues
python -m agent.modules.backend.scanner_v2 --scan-type performance --profile-code

# Apply performance fixes
python -m agent.modules.backend.fixer_v2 --fix-type performance --dry-run
# Review and approve
python -m agent.modules.backend.fixer_v2 --fix-type performance
```

### Workflow 4: Post-Merge Cleanup

**Trigger:** After merging PRs

```bash
# Run enhanced autofix on main branch
python -m agent.modules.backend.enhanced_autofix \
  --create-branch \
  --auto-commit \
  --fix-types "formatting,quality"
```

---

## Security Repairs

### Security Issue Categories

#### 1. Hardcoded Secrets

**Detection:**
```python
# Bad
api_key = "sk-1234567890"
password = "admin123"
```

**Automatic Fix:**
```python
# Good
import os
api_key = os.getenv("API_KEY")
password = os.getenv("DB_PASSWORD")
```

#### 2. SQL Injection

**Detection:**
```python
# Bad
query = f"SELECT * FROM users WHERE username='{username}'"
cursor.execute(query)
```

**Automatic Fix:**
```python
# Good
query = "SELECT * FROM users WHERE username=%s"
cursor.execute(query, (username,))
```

#### 3. XSS Vulnerabilities

**Detection:**
```javascript
// Bad
element.innerHTML = userInput;
```

**Automatic Fix:**
```javascript
// Good
element.textContent = userInput;
// Or use DOMPurify
element.innerHTML = DOMPurify.sanitize(userInput);
```

#### 4. Command Injection

**Detection:**
```python
# Bad
os.system(f"ls {user_path}")
```

**Automatic Fix:**
```python
# Good
import subprocess
subprocess.run(["ls", user_path], check=True)
```

### Security Repair Priority

| Priority | Issue Type | Auto-Fix | Review Required |
|----------|------------|----------|-----------------|
| 🔴 Critical | Hardcoded secrets | ✅ Yes | ✅ Yes |
| 🔴 Critical | SQL injection | ✅ Yes | ✅ Yes |
| 🟡 High | XSS vulnerabilities | ✅ Yes | ✅ Yes |
| 🟡 High | Command injection | ✅ Yes | ✅ Yes |
| 🟡 High | Insecure crypto | ⚠️ Partial | ✅ Yes |
| 🟢 Medium | Path traversal | ✅ Yes | ⚠️ Optional |
| 🟢 Medium | Weak validation | ⚠️ Partial | ⚠️ Optional |

---

## Performance Optimization

### Performance Issue Detection

#### 1. N+1 Query Problems

**Detection:**
```python
# Bad - N+1 queries
for user in users:
    orders = db.query(Order).filter(Order.user_id == user.id).all()
```

**Automatic Fix:**
```python
# Good - Single query with join
users_with_orders = db.query(User).options(joinedload(User.orders)).all()
```

#### 2. Missing Caching

**Detection:**
```python
# Bad - Repeated expensive computation
def get_product_recommendations(user_id):
    # Expensive ML computation
    return ml_model.predict(user_data)
```

**Automatic Fix:**
```python
# Good - With caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_product_recommendations(user_id):
    # Expensive ML computation
    return ml_model.predict(user_data)
```

#### 3. Synchronous I/O

**Detection:**
```python
# Bad - Blocking I/O
def fetch_data():
    response = requests.get(url)
    return response.json()
```

**Automatic Fix:**
```python
# Good - Async I/O
import aiohttp

async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

---

## Troubleshooting

### Common Issues

#### Issue: Fixer Not Finding Issues

**Symptoms:**
- Scanner finds issues but fixer shows 0 fixes applied

**Solution:**
```python
# Ensure scan results are passed correctly
scan_results = await scanner.execute_core_function()
fix_results = await fixer.execute_core_function(
    scan_results=scan_results  # Make sure this is passed
)
```

#### Issue: Backup Directory Not Found

**Symptoms:**
- `FileNotFoundError: .agent_backups`

**Solution:**
```bash
# Create backup directory
mkdir -p .agent_backups

# Or in code
from pathlib import Path
Path(".agent_backups").mkdir(exist_ok=True)
```

#### Issue: Git Branch Creation Failed

**Symptoms:**
- Enhanced autofix fails on branch creation

**Solution:**
```bash
# Check git status
git status

# Ensure working directory is clean
git stash

# Or disable branch creation
autofix.run_enhanced_autofix(create_branch=False)
```

#### Issue: AI-Powered Fixes Not Working

**Symptoms:**
- Fixer V2 falls back to basic fixes

**Solution:**
```bash
# Set API keys
export ANTHROPIC_API_KEY="your_key"
export OPENAI_API_KEY="your_key"

# Or in .env
echo "ANTHROPIC_API_KEY=your_key" >> .env
```

#### Issue: Permission Denied

**Symptoms:**
- `PermissionError` when writing fixes

**Solution:**
```bash
# Check file permissions
ls -la

# Fix permissions
chmod u+w path/to/file

# Or run with appropriate permissions
sudo python -m agent.modules.backend.fixer_v2
```

---

## Best Practices

### 1. Always Create Backups

```python
# ✅ Good - Creates backup before fixing
results = await fixer.execute_core_function(
    scan_results=scan_results,
    create_backup=True
)

# ❌ Bad - No backup
results = await fixer.execute_core_function(
    scan_results=scan_results,
    create_backup=False
)
```

### 2. Use Dry Run First

```python
# ✅ Good - Preview fixes first
preview = await fixer.execute_core_function(dry_run=True)
# Review preview
if looks_good:
    results = await fixer.execute_core_function(dry_run=False)

# ❌ Bad - Directly apply without review
results = await fixer.execute_core_function(dry_run=False)
```

### 3. Run in Feature Branches

```python
# ✅ Good - Use separate branch
results = autofix.run_enhanced_autofix(
    create_branch=True,
    branch_name="autofix/improvements"
)

# ❌ Bad - Fix directly on main
results = autofix.run_enhanced_autofix(create_branch=False)
```

### 4. Incremental Fixes

```python
# ✅ Good - Fix one type at a time
for fix_type in ["syntax", "security", "performance"]:
    results = await fixer.execute_core_function(fix_type=fix_type)
    # Review and test
    
# ❌ Bad - Fix everything at once without review
results = await fixer.execute_core_function(fix_type="all")
```

### 5. Monitor Fix Results

```python
# ✅ Good - Log and monitor
results = await fixer.execute_core_function()
logger.info(f"Fixes applied: {results['fixes_applied']}")
logger.info(f"Files modified: {results['files_modified']}")

# Send to monitoring
send_metric("code_fixes", results['fixes_applied'])
```

### 6. Regular Scans

```bash
# ✅ Good - Daily automated scans
# In .github/workflows/daily-scan.yml
schedule:
  - cron: '0 2 * * *'  # 2 AM daily

# ❌ Bad - Manual scans only
```

### 7. Review AI-Generated Fixes

```python
# ✅ Good - Review AI fixes
results = await fixer.execute_core_function()
for fix in results['fixes']:
    if fix['ai_generated']:
        print(f"Review: {fix['file']}:{fix['line']}")
        print(f"Change: {fix['before']} → {fix['after']}")

# ❌ Bad - Blindly trust AI fixes
```

### 8. Version Control Integration

```python
# ✅ Good - Use enhanced autofix with Git
autofix.run_enhanced_autofix(
    create_branch=True,
    auto_commit=True
)

# ❌ Bad - Manual file editing without version control
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/code-repair.yml
name: Automated Code Repair

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:      # Manual trigger

jobs:
  repair:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run code repair
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          python -m agent.modules.backend.enhanced_autofix \
            --create-branch \
            --branch-name "autofix/daily-$(date +%Y%m%d)" \
            --auto-commit
      
      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          title: 'Automated Code Repairs'
          body: 'Automated fixes from daily scan'
          branch: autofix/daily-$(date +%Y%m%d)
```

---

## Related Documentation

- [Code Review Guide](code_review.md) - Code review processes and standards
- [Security Policy](SECURITY.md) - Security guidelines and reporting
- [Contributing Guide](CONTRIBUTING.md) - Contribution guidelines and standards
- [Deployment Runbook](DEPLOYMENT_RUNBOOK.md) - Deployment procedures

---

## Support

For issues with code repair agents:

- **GitHub Issues:** [Report a bug](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues)
- **Email:** dev@skyyrose.co
- **Documentation:** [Official Docs](/docs)

---

**Last Updated:** November 2024  
**Version:** 5.0.0  
**Maintainer:** DevSkyy Platform Team

*© 2024 Skyy Rose LLC. All rights reserved.*
