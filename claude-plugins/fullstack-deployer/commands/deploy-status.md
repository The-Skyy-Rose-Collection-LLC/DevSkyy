---
name: deploy-status
description: Check deployment status and health of all services
allowed-tools:
  - Bash
  - Read
  - WebFetch
argument-hint: "[--verbose]"
---

# Deployment Status Command

Check the current deployment status and health of all connected services.

## Execution Steps

1. **Vercel Deployment Status**
   ```bash
   vercel ls --limit 3
   vercel inspect --scope=production
   ```

2. **Health Check**
   ```bash
   curl -s "https://your-site.com/api/health"
   ```

3. **Service Connectivity**
   - WordPress API status
   - WooCommerce API status
   - Any other configured services

4. **Performance Check** (if --verbose)
   - Response times
   - Error rates
   - Resource usage

## Arguments

- `--verbose`: Include detailed performance metrics and response times

## Output Format

```
Deployment Status
═══════════════════════════════════════

Vercel:
├── Production URL: https://example.com
├── Last deployed: 2024-01-15 10:30 AM
├── Deployment ID: dpl_xxxxx
└── Status: ✅ Healthy

Services:
├── WordPress: ✅ Connected
│   └── Posts: 45 | Pages: 12 | Products: 156
├── WooCommerce: ✅ Connected
│   └── Products: 156 | Categories: 8
└── Health Endpoint: ✅ Healthy

Performance (verbose):
├── Homepage: 234ms
├── API Health: 45ms
├── WordPress API: 189ms
└── WooCommerce API: 267ms
```

## Example Usage

```
/deploy-status           # Basic status check
/deploy-status --verbose # Include performance metrics
```

## Health Indicators

- ✅ **Healthy**: Service responding normally
- ⚠️ **Degraded**: Service slow or intermittent
- ❌ **Down**: Service not responding

## Automated Actions

If services are unhealthy:
1. Diagnose the issue
2. Suggest remediation steps
3. Offer to run relevant fixes
