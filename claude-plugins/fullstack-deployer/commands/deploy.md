---
name: deploy
description: Deploy the application to Vercel with full validation and autonomous error handling
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
  - Task
argument-hint: "[--prod|--preview] [--skip-tests]"
---

# Deploy Command

Deploy the application to Vercel with comprehensive validation, testing, and autonomous error handling.

## Execution Steps

1. **Pre-deployment validation**
   - Run TypeScript check: `npx tsc --noEmit`
   - Run ESLint: `npm run lint`
   - Run unit tests: `npm test` (unless --skip-tests)
   - Build project: `npm run build`

2. **Deploy to Vercel**
   - Check Vercel CLI installed
   - If `--prod` flag: Deploy to production with `vercel --prod`
   - If `--preview` or no flag: Deploy preview with `vercel`

3. **Post-deployment validation**
   - Verify deployment URL responds
   - Check health endpoint if available
   - Validate external service connections

## Arguments

- `--prod`: Deploy to production (default is preview)
- `--preview`: Deploy as preview (default behavior)
- `--skip-tests`: Skip running tests before deployment

## Error Handling

If any step fails:
1. Capture the error message
2. Use Context7 to fetch official documentation for the error
3. Apply the fix automatically
4. Retry the failed step
5. Continue until deployment succeeds

Use the error-resolver agent if errors persist.

## Example Usage

```
/deploy                  # Deploy preview
/deploy --prod           # Deploy to production
/deploy --skip-tests     # Deploy without running tests
/deploy --prod --skip-tests  # Production without tests
```

## Success Criteria

Deployment is complete when:
- All pre-deployment checks pass
- Vercel deployment succeeds
- Deployment URL is accessible
- Health check returns healthy (if endpoint exists)

Report the deployment URL when complete.
