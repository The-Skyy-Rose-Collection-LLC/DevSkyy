---
name: lint
description: Run code quality checks and auto-fix issues
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
argument-hint: "[--fix] [--strict]"
---

# Lint Command

Run code quality checks including TypeScript, ESLint, and Prettier.

## Actions

### Check Only (default)
```
/lint
```
Report all issues without fixing.

### Auto-Fix
```
/lint --fix
```
Automatically fix all fixable issues.

### Strict Mode
```
/lint --strict
```
Include warnings as errors, stricter checks.

## Execution Steps

### Standard Check
```bash
# TypeScript
npx tsc --noEmit

# ESLint
npm run lint

# Prettier
npx prettier --check .
```

### Auto-Fix Mode
```bash
# ESLint with fix
npm run lint -- --fix

# Prettier fix
npx prettier --write .

# Re-check TypeScript (can't auto-fix types)
npx tsc --noEmit
```

### Strict Mode
```bash
# TypeScript strict
npx tsc --noEmit --strict

# ESLint with warnings as errors
npm run lint -- --max-warnings 0

# Prettier check
npx prettier --check .
```

## Output Format

```
Code Quality Check
═══════════════════════════════════════

TypeScript:
├── Status: ✅ Pass
└── Errors: 0

ESLint:
├── Status: ⚠️ 2 warnings
├── Errors: 0
├── Warnings: 2
│   ├── src/utils.ts:15 - no-console
│   └── src/api.ts:42 - @typescript-eslint/no-unused-vars
└── Auto-fixable: 1

Prettier:
├── Status: ✅ Pass
└── Files checked: 47

Summary:
├── Total issues: 2
├── Auto-fixable: 1
└── Manual fixes needed: 1
```

## Example Usage

```
/lint              # Check all
/lint --fix        # Fix all fixable issues
/lint --strict     # Strict mode, warnings = errors
/lint --fix --strict  # Fix then check strict
```

## Common Issues Fixed

**Auto-fixable:**
- Import ordering
- Formatting issues
- Trailing commas
- Quote style
- Semicolons

**Manual fix required:**
- Type errors
- Unused variables (review before removing)
- Missing dependencies in hooks
- Logic errors

## Integration

This command is automatically run:
- Before deployment (`/deploy`)
- During validation (`/validate`)
- By code-quality-checker agent

Use `--fix` to resolve issues before deployment.
