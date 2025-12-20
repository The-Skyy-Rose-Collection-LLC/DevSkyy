# Staging Deployment Automation - Complete Index

**Project:** SkyyRose Staging Deployment System
**Created:** 2025-12-19
**Status:** Production Ready
**Location:** `/Users/coreyfoster/DevSkyy/staging/`

---

## Quick Navigation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **[DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md)** | Complete deployment guide | Before every deployment |
| **[DEPLOYMENT_SCRIPTS_SUMMARY.md](DEPLOYMENT_SCRIPTS_SUMMARY.md)** | Script reference guide | Learning how scripts work |
| **[DELIVERY_COMPLETE.txt](DELIVERY_COMPLETE.txt)** | Delivery checklist | Verification of deliverables |
| **This Document** | Quick reference index | Finding the right resource |

---

## Scripts Quick Reference

### 1. Pre-Deployment Validation

```bash
./pre_deployment_checklist.sh
```

**Use when:**
- Before every deployment
- Verifying environment setup
- Troubleshooting deployment issues

**What it checks:**
- Git status and branch
- Docker installation and daemon
- Port availability
- Disk space
- Environment files
- Test execution

**Output:**
- Console (color-coded)
- Exit code 0 = ready, 1 = not ready

---

### 2. Deployment

```bash
./deploy_to_staging.sh
```

**Use when:**
- Deploying to staging
- After pre-deployment checklist passes

**Duration:** 15-30 minutes

**What it does:**
1. Pre-deployment checks
2. Backup current state
3. Tag deployment
4. Build Docker images
5. Stop old containers
6. Start new containers
7. Health monitoring
8. Smoke tests
9. Automatic rollback (if needed)

**Outputs:**
- `staging/backups/YYYYMMDD_HHMMSS/` - Backup
- `staging/logs/deploy_YYYYMMDD_HHMMSS.log` - Log
- `staging/reports/deployment_YYYYMMDD_HHMMSS.txt` - Report

---

### 3. Rollback

```bash
# Interactive rollback
./rollback.sh

# Automatic rollback (no confirmation)
./rollback.sh --auto

# Rollback to specific backup
./rollback.sh --backup staging/backups/20251219_143022
```

**Use when:**
- Deployment failed
- Critical bugs discovered
- Need to restore previous version

**Duration:** 10-15 minutes

**What it does:**
1. Verify backup exists
2. Stop current deployment
3. Restore configuration
4. Restore git version
5. Restore databases
6. Restart services
7. Health checks
8. Smoke tests

**Outputs:**
- `staging/logs/rollback_YYYYMMDD_HHMMSS.log` - Log
- `staging/notifications/rollback_YYYYMMDD_HHMMSS.txt` - Notification

---

### 4. Health Check

```bash
# Standard check
./healthcheck.sh

# Verbose output
./healthcheck.sh --verbose

# JSON output
./healthcheck.sh --json

# Both verbose and JSON
./healthcheck.sh -v -j
```

**Use when:**
- After deployment
- Regular monitoring
- Troubleshooting issues
- Automated monitoring

**Duration:** 10-30 seconds

**What it checks:**
- Docker daemon
- Container status
- Port availability
- Database connectivity
- Redis connectivity
- API responsiveness
- Monitoring stack
- Resource usage
- Disk space

**Outputs:**
- Console (color-coded)
- `staging/reports/health_YYYYMMDD_HHMMSS.json` - Report
- Exit code 0 = healthy, 1 = unhealthy

---

### 5. Log Collection

```bash
# Collect last 1000 lines
./logs_collection.sh

# Collect all logs
./logs_collection.sh --all

# Collect custom number of lines
./logs_collection.sh --lines 5000

# No compression
./logs_collection.sh --no-compress

# No cleanup of old archives
./logs_collection.sh --no-cleanup
```

**Use when:**
- After deployment
- Troubleshooting issues
- Regular log archival
- Before major changes

**Duration:** 30-60 seconds

**What it collects:**
- Container logs (all staging containers)
- docker-compose logs
- System information
- Application logs
- Database logs
- Redis logs
- Monitoring data

**Outputs:**
- `staging/collected_logs/logs_YYYYMMDD_HHMMSS.tar.gz` - Archive
- Keeps last 5 archives automatically

---

## Common Workflows

### Standard Deployment Workflow

```mermaid
graph TD
    A[Start] --> B[Pre-Deployment Checklist]
    B --> C{Checks Pass?}
    C -->|No| D[Fix Issues]
    D --> B
    C -->|Yes| E[Deploy to Staging]
    E --> F{Deployment Success?}
    F -->|No| G[Auto Rollback]
    G --> H[Investigate]
    F -->|Yes| I[Health Check]
    I --> J{All Healthy?}
    J -->|No| K[Manual Investigation]
    J -->|Yes| L[Deployment Complete]
    K --> M{Rollback Needed?}
    M -->|Yes| N[Manual Rollback]
    M -->|No| O[Fix and Monitor]
```

**Steps:**

1. **Prepare**
   ```bash
   cd staging
   ./pre_deployment_checklist.sh
   ```

2. **Deploy**
   ```bash
   ./deploy_to_staging.sh
   ```

3. **Verify**
   ```bash
   ./healthcheck.sh --verbose
   ```

4. **Collect Logs** (optional)
   ```bash
   ./logs_collection.sh
   ```

---

### Emergency Rollback Workflow

```mermaid
graph TD
    A[Issue Detected] --> B[Assess Severity]
    B --> C{Critical?}
    C -->|Yes| D[Immediate Rollback]
    C -->|No| E[Monitor/Fix]
    D --> F[./rollback.sh]
    F --> G{Rollback Success?}
    G -->|Yes| H[Verify Health]
    G -->|No| I[Manual Intervention]
    H --> J[Create Incident Report]
    I --> J
    E --> K{Fixed?}
    K -->|No| D
    K -->|Yes| L[Continue Monitoring]
```

**Steps:**

1. **Initiate Rollback**
   ```bash
   cd staging
   ./rollback.sh
   ```

2. **Verify Restoration**
   ```bash
   ./healthcheck.sh --verbose
   ```

3. **Collect Logs for Analysis**
   ```bash
   ./logs_collection.sh --all
   ```

4. **Document Incident**
   - What went wrong
   - When it was detected
   - Rollback time
   - Root cause (if known)

---

### Regular Monitoring Workflow

```bash
# Daily health check (add to cron)
0 9 * * * /Users/coreyfoster/DevSkyy/staging/healthcheck.sh --json > /tmp/staging_health.json

# Weekly log collection (add to cron)
0 0 * * 0 /Users/coreyfoster/DevSkyy/staging/logs_collection.sh

# Alert on unhealthy status
*/5 * * * * /Users/coreyfoster/DevSkyy/staging/healthcheck.sh || echo "Staging unhealthy" | mail -s "ALERT: Staging Unhealthy" devops@skyyrose.com
```

---

## File Locations

### Scripts (Executable)

| File | Size | Purpose |
|------|------|---------|
| `deploy_to_staging.sh` | 15K | Main deployment script |
| `rollback.sh` | 14K | Rollback automation |
| `healthcheck.sh` | 16K | Health monitoring |
| `logs_collection.sh` | 16K | Log aggregation |
| `pre_deployment_checklist.sh` | 15K | Pre-deployment validation |

### Documentation

| File | Size | Purpose |
|------|------|---------|
| `DEPLOYMENT_RUNBOOK.md` | 23K | Complete deployment guide |
| `DEPLOYMENT_SCRIPTS_SUMMARY.md` | 17K | Script reference |
| `DELIVERY_COMPLETE.txt` | 8K | Delivery checklist |
| `DEPLOYMENT_AUTOMATION_INDEX.md` | This file | Quick reference |

### Data Directories

| Directory | Purpose | Retention |
|-----------|---------|-----------|
| `backups/` | Deployment backups | Last 5 deployments |
| `logs/` | Deployment/rollback logs | Manual cleanup |
| `collected_logs/` | Compressed log archives | Last 5 archives |
| `reports/` | Health/deployment reports | Manual cleanup |
| `notifications/` | Rollback notifications | Manual cleanup |

---

## Troubleshooting Quick Reference

### Issue: Deployment Fails

**Check:**
1. Run pre-deployment checklist
   ```bash
   ./pre_deployment_checklist.sh
   ```

2. Check recent logs
   ```bash
   ls -lt logs/deploy_*.log | head -1 | awk '{print $9}' | xargs tail -100
   ```

3. Check container status
   ```bash
   docker ps -a --filter "name=staging-"
   ```

**Solutions:**
- Fix reported issues
- Ensure Docker is running
- Check disk space
- Verify network connectivity

### Issue: Services Unhealthy

**Check:**
1. Run health check
   ```bash
   ./healthcheck.sh --verbose
   ```

2. Check container logs
   ```bash
   docker logs staging-backend --tail 100
   docker logs staging-frontend --tail 100
   ```

3. Check database
   ```bash
   docker exec staging-postgres pg_isready -U postgres
   ```

**Solutions:**
- Restart problematic service
- Check configuration files
- Verify environment variables
- Consider rollback if critical

### Issue: Rollback Needed

**Steps:**
1. Collect current logs first
   ```bash
   ./logs_collection.sh --all
   ```

2. Execute rollback
   ```bash
   ./rollback.sh
   ```

3. Verify restoration
   ```bash
   ./healthcheck.sh --verbose
   ```

---

## Best Practices

### Before Deployment

- [ ] Run pre-deployment checklist
- [ ] Review recent changes
- [ ] Notify team
- [ ] Ensure on-call available
- [ ] Check deployment window

### During Deployment

- [ ] Monitor deployment progress
- [ ] Watch for errors
- [ ] Don't interrupt the process
- [ ] Be ready to investigate issues

### After Deployment

- [ ] Run health check
- [ ] Verify functionality
- [ ] Monitor logs
- [ ] Collect logs for analysis
- [ ] Update team

### Regular Maintenance

- [ ] Weekly health checks
- [ ] Weekly log collection
- [ ] Monthly backup verification
- [ ] Monthly rollback testing
- [ ] Quarterly runbook review

---

## Integration Examples

### CI/CD Pipeline (GitHub Actions)

```yaml
name: Deploy to Staging
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Pre-deployment checks
        run: staging/pre_deployment_checklist.sh

      - name: Deploy
        run: staging/deploy_to_staging.sh

      - name: Verify
        run: staging/healthcheck.sh --verbose

      - name: Collect logs on failure
        if: failure()
        run: staging/logs_collection.sh
```

### Monitoring Script

```bash
#!/bin/bash
# staging-monitor.sh

# Run health check
if ! /Users/coreyfoster/DevSkyy/staging/healthcheck.sh --json > /tmp/health.json; then
    # Send alert
    curl -X POST https://alerts.example.com/staging-unhealthy \
        -H "Content-Type: application/json" \
        -d @/tmp/health.json

    # Collect logs
    /Users/coreyfoster/DevSkyy/staging/logs_collection.sh
fi
```

### Auto-Recovery Script

```bash
#!/bin/bash
# staging-auto-recover.sh

MAX_RETRIES=3
retry_count=0

while [ $retry_count -lt $MAX_RETRIES ]; do
    if /Users/coreyfoster/DevSkyy/staging/healthcheck.sh; then
        echo "Health check passed"
        exit 0
    fi

    retry_count=$((retry_count + 1))
    echo "Health check failed, attempt $retry_count of $MAX_RETRIES"

    if [ $retry_count -lt $MAX_RETRIES ]; then
        echo "Restarting services..."
        docker-compose -f staging/docker-compose.staging.yml restart
        sleep 30
    fi
done

echo "Auto-recovery failed after $MAX_RETRIES attempts"
echo "Initiating rollback..."
/Users/coreyfoster/DevSkyy/staging/rollback.sh --auto
```

---

## Command Cheat Sheet

### Quick Commands

```bash
# Check if ready to deploy
./pre_deployment_checklist.sh

# Deploy
./deploy_to_staging.sh

# Rollback
./rollback.sh

# Health check
./healthcheck.sh -v

# Collect logs
./logs_collection.sh

# View recent deployment logs
tail -f logs/deploy_*.log

# View recent health reports
ls -lt reports/health_*.json | head -5

# View backups
ls -lt backups/

# Check container status
docker ps --filter "name=staging-"

# Check specific container logs
docker logs staging-backend --tail 100 -f
```

---

## Getting Help

### 1. Check Documentation

- **DEPLOYMENT_RUNBOOK.md** - Complete procedures
- **DEPLOYMENT_SCRIPTS_SUMMARY.md** - Script details
- This document - Quick reference

### 2. Run Diagnostics

```bash
# Pre-deployment validation
./pre_deployment_checklist.sh

# Health check
./healthcheck.sh --verbose

# Collect logs
./logs_collection.sh
```

### 3. Review Logs

```bash
# Deployment logs
ls -lt logs/deploy_*.log
tail -100 logs/deploy_YYYYMMDD_HHMMSS.log

# Container logs
docker logs staging-backend --tail 100
docker logs staging-frontend --tail 100
```

### 4. Contact Support

- DevOps Team
- On-call Engineer
- Check **DEPLOYMENT_RUNBOOK.md** for contact information

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-19 | Initial delivery - all scripts and documentation |

---

## Quick Start (First Time)

1. **Verify delivery:**
   ```bash
   cd /Users/coreyfoster/DevSkyy/staging
   ls -l *.sh DEPLOYMENT_*.md
   ```

2. **Create environment files:**
   ```bash
   # Copy docker-compose if needed
   cp ../docker-compose.yml docker-compose.staging.yml

   # Create .env.staging
   cat > .env.staging <<EOF
   DATABASE_URL=postgresql://postgres:password@postgres:5432/skyyrose_staging
   REDIS_URL=redis://redis:6379/0
   ENVIRONMENT=staging
   EOF
   ```

3. **Run pre-deployment check:**
   ```bash
   ./pre_deployment_checklist.sh
   ```

4. **Deploy:**
   ```bash
   ./deploy_to_staging.sh
   ```

5. **Verify:**
   ```bash
   ./healthcheck.sh --verbose
   ```

---

**Last Updated:** 2025-12-19
**Status:** Production Ready
**Next Review:** 2026-01-19
