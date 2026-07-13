---
name: verification-loop
description: "A comprehensive verification system for Claude Code sessions."
origin: ECC
---

# Verification Loop Skill

A comprehensive verification system for Claude Code sessions.

## When to Use

Invoke this skill:
- After completing a feature or significant code change
- Before creating a PR
- When you want to ensure quality gates pass
- After refactoring

## Verification Phases

### Phase 1: Build Verification
```bash
# Check if project builds
npm run build 2>&1 | tail -20
# OR
pnpm build 2>&1 | tail -20
```

If build fails, STOP and fix before continuing.

### Phase 2: Type Check
```bash
# TypeScript projects
npx tsc --noEmit 2>&1 | head -30

# Python projects
pyright . 2>&1 | head -30
```

Report all type errors. Fix critical ones before continuing.

### Phase 3: Lint Check
```bash
# JavaScript/TypeScript
npm run lint 2>&1 | head -30

# Python
ruff check . 2>&1 | head -30
```

### Phase 4: Test Suite
```bash
# JavaScript/TypeScript — run tests with coverage
npm run test -- --coverage 2>&1 | tail -50
# Target: 80% minimum coverage

# Python — run tests with short traceback, quiet summary
pytest --tb=short -q 2>&1 | tail -50
# Target: 85% minimum coverage (per project rules)
# For coverage report: pytest --cov --cov-report=term-missing -q
```

Report:
- Total tests: X
- Passed: X
- Failed: X
- Coverage: X%

### Phase 5: Security Scan
```bash
# JavaScript/TypeScript — check for secrets and debug leaks
grep -rn "sk-" --include="*.ts" --include="*.js" . 2>/dev/null | head -10
grep -rn "api_key" --include="*.ts" --include="*.js" . 2>/dev/null | head -10
grep -rn "console.log" --include="*.ts" --include="*.tsx" src/ 2>/dev/null | head -10

# Python — static security analysis (low severity and above)
bandit -r . -ll 2>&1 | head -40
# -ll = report LOW severity and above; add -x ./tests to exclude test dirs
# Install: pip install bandit
```

### Phase 6: Diff Review
```bash
# Show what changed
git diff --stat
git diff HEAD~1 --name-only
```

Review each changed file for:
- Unintended changes
- Missing error handling
- Potential edge cases

### WordPress Theme Gates

For changes touching `wordpress-theme/`, run these in addition to the phases above — they catch failure modes the generic JS/Python checks above miss (PHP syntax, coding standard, stale production assets, live-site drift).

```bash
# PHPCS — WordPress coding standard
cd wordpress-theme/skyyrose-flagship && vendor/bin/phpcs --standard=.phpcs.xml -s .

# php -l on every touched file (fast syntax check, run before phpcs)
git diff --name-only -- '*.php' | xargs -n1 php -l
```

**Rebuild `.min` after any CSS/JS edit.** The theme serves `.min` in production (`$use_min = ! SCRIPT_DEBUG` in `inc/enqueue.php`) — editing the source and stopping there ships no change live.

```bash
node scripts/build-css.js && node scripts/build-js.js
# Re-verify the .min OUTPUT, not just the source — diff or grep the built file for the change
```

**Cache-busted live curl** — never `WebFetch` a live page, it strips `<script>` tags (JSON-LD, OG tags) and WP.com Batcache can serve stale HTML:

```bash
curl -s "https://skyyrose.co/path/?cb=$(date +%s)" | grep -A2 "expected-marker"
```

**Playwright eyes-on** — after any change reaches skyyrose.co, navigate and screenshot both breakpoints, not just the curl check:

```bash
# mobile (375px) and desktop (1440px) viewports, check console for errors
```

## Output Format

After running all phases, produce a verification report:

```
VERIFICATION REPORT
==================

Build:     [PASS/FAIL]
Types:     [PASS/FAIL] (X errors)
Lint:      [PASS/FAIL] (X warnings)
Tests:     [PASS/FAIL] (X/Y passed, Z% coverage)
Security:  [PASS/FAIL] (X issues)
Diff:      [X files changed]

Overall:   [READY/NOT READY] for PR

Issues to Fix:
1. ...
2. ...
```

## Continuous Mode

For long sessions, run verification every 15 minutes or after major changes:

```markdown
Set a mental checkpoint:
- After completing each function
- After finishing a component
- Before moving to next task

Run: /verify
```

## Integration with Hooks

This skill complements PostToolUse hooks but provides deeper verification.
Hooks catch issues immediately; this skill provides comprehensive review.
