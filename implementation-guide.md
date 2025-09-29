# Repository Secret Configuration Guide

## Required Secrets for GitHub Actions

Add these secrets to your repository:
- Go to: Settings → Secrets and variables → Actions

### 1. Debug Logging Secret
```
Name: ACTIONS_STEP_DEBUG
Value: true
```

### 2. Optional: Enhanced Permissions
If you need additional permissions:
```
Name: GITHUB_TOKEN_PERMISSIONS
Value: |
  {
    "contents": "read",
    "actions": "write",
    "checks": "write",
    "pull-requests": "write"
  }
```

## Workflow File Locations

Place the workflow files in:
```
.github/workflows/
├── test-and-lint-enhanced.yml
└── debug-minimal.yml
```

## Quick Implementation Steps

1. Copy the enhanced workflow to `.github/workflows/test-and-lint-enhanced.yml`
2. Add the ACTIONS_STEP_DEBUG secret
3. Commit and push changes
4. Monitor the Actions tab for detailed logs

## Troubleshooting Commands

If you have access to the repository locally:

```bash
# Check workflow syntax
yamllint .github/workflows/*.yml

# Test npm scripts locally
npm ci
npm run lint
npm test
npm run build

# Check for dependency issues
npm audit
npm outdated
```