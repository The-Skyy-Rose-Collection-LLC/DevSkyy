---
name: rollback
description: Rollback to a previous Vercel deployment with verification
allowed-tools:
  - Bash
  - Read
  - WebFetch
argument-hint: "[deployment-url]"
---

# Rollback Command

Rollback the production deployment to a previous version and verify the rollback was successful.

## Execution Steps

1. **List recent deployments**
   ```bash
   vercel ls --limit 5
   ```

2. **Perform rollback**
   - If deployment URL provided: Rollback to that specific deployment
   - If no URL provided: Rollback to previous production deployment
   ```bash
   vercel rollback [deployment-url]
   ```

3. **Verify rollback**
   - Check new production URL responds
   - Verify health endpoint
   - Test critical functionality

## Arguments

- `deployment-url` (optional): Specific deployment URL to rollback to
  - If omitted, rolls back to the previous production deployment

## Example Usage

```
/rollback                                    # Rollback to previous deployment
/rollback https://project-abc123.vercel.app  # Rollback to specific deployment
```

## Verification Checklist

After rollback, verify:
- Production URL responds (HTTP 200)
- Homepage loads correctly
- API health check passes
- WordPress connection works
- WooCommerce connection works

## Output

Report:
- Previous deployment URL
- New production deployment URL
- Verification status for each check
