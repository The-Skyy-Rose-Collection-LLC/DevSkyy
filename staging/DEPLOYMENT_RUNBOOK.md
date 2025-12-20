# Staging Deployment Runbook

**Version:** 1.0
**Last Updated:** 2025-12-19
**Owner:** DevOps Team

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Process](#deployment-process)
4. [Expected Timeline](#expected-timeline)
5. [Verification Checklist](#verification-checklist)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Rollback Procedures](#rollback-procedures)
8. [Post-Deployment Tasks](#post-deployment-tasks)
9. [Emergency Contacts](#emergency-contacts)

---

## Overview

### Purpose

This runbook provides step-by-step instructions for deploying the SkyyRose application to the staging environment. It ensures consistent, safe deployments with proper validation and rollback capabilities.

### Architecture

Staging environment consists of:
- **Frontend**: Next.js dashboard (port 3000)
- **Backend**: Python FastAPI (port 5000)
- **Database**: PostgreSQL (port 5432)
- **Cache**: Redis (port 6379)
- **Monitoring**: Prometheus (9090), Grafana (3100), Alertmanager (9093)

### Deployment Strategy

- **Method**: Docker Compose with rolling updates
- **Backup**: Automatic backup before each deployment
- **Health Checks**: Comprehensive health monitoring
- **Rollback**: Automated rollback on failure
- **Retention**: Last 5 deployment backups retained

---

## Pre-Deployment Checklist

### 1. Run Automated Checklist

```bash
cd staging
./pre_deployment_checklist.sh
```

The automated checklist verifies:

- [ ] Git working directory is clean
- [ ] On main branch (or explicitly confirmed otherwise)
- [ ] Main branch is up-to-date with origin/main
- [ ] Git remote is accessible
- [ ] All tests passing locally
- [ ] Docker installed and daemon running
- [ ] docker-compose installed
- [ ] Docker permissions configured
- [ ] docker-compose.staging.yml exists and is valid
- [ ] Network connectivity available
- [ ] Docker Hub accessible
- [ ] Required ports available (3000, 5000, 5432, 6379)
- [ ] Sufficient disk space (5GB+ free)
- [ ] Sufficient backup space (2GB+ free)
- [ ] Adequate memory available
- [ ] .env.staging file exists
- [ ] Required environment variables defined
- [ ] All deployment scripts exist and are executable

### 2. Manual Verification

Additional manual checks:

- [ ] **Stakeholder Notification**: Inform team of upcoming deployment
- [ ] **Deployment Window**: Confirm deployment time is appropriate
- [ ] **Change Log**: Review changes being deployed
- [ ] **Database Migrations**: Verify migrations are ready (if applicable)
- [ ] **Feature Flags**: Confirm feature flag states
- [ ] **Dependencies**: Check for dependency updates or conflicts

### 3. Communication

- [ ] Notify team in Slack/Teams channel
- [ ] Set deployment status in monitoring dashboard
- [ ] Confirm on-call engineer is available

---

## Deployment Process

### Step 1: Navigate to Staging Directory

```bash
cd /Users/coreyfoster/DevSkyy/staging
```

### Step 2: Run Pre-Deployment Checklist

```bash
./pre_deployment_checklist.sh
```

**Expected Output:**
- All critical checks should pass (green checkmarks)
- Warnings are acceptable if understood
- Failures must be resolved before proceeding

**Action if Failed:**
- Fix reported issues
- Re-run checklist
- Do not proceed until all critical checks pass

### Step 3: Execute Deployment

```bash
./deploy_to_staging.sh
```

The deployment script will execute these phases:

#### Phase 1: Pre-Deployment Checks (2-3 minutes)
- Docker daemon verification
- Disk space check
- docker-compose validation
- Git status verification
- Port availability check

**What to Watch For:**
- Green checkmarks for each check
- Any warnings should be reviewed but may not block deployment

#### Phase 2: Backup (1-2 minutes)
- Creates timestamped backup directory
- Backs up docker-compose files
- Backs up environment files
- Exports PostgreSQL database
- Saves Redis data
- Records container versions
- Saves current git commit

**What to Watch For:**
- Backup directory creation
- Database dump success
- No backup failures

#### Phase 3: Tagging (< 1 minute)
- Creates git tag for rollback: `staging-deploy-YYYYMMDD_HHMMSS`

**What to Watch For:**
- Tag creation confirmation
- Tag name saved for reference

#### Phase 4: Build (5-10 minutes)
- Builds Docker images with `--no-cache`
- Compiles frontend and backend code

**What to Watch For:**
- Build progress for each service
- No build errors
- Image size is reasonable

**Common Issues:**
- Build cache issues: Already handled with `--no-cache`
- Dependency installation failures: Check network connectivity
- Out of disk space: Free up space or cleanup old images

#### Phase 5: Stop Old Services (30-60 seconds)
- Gracefully stops containers (30 second timeout)
- Removes stopped containers

**What to Watch For:**
- Containers stopping cleanly
- No hung processes

#### Phase 6: Start New Services (1-2 minutes)
- Starts all services in detached mode
- Database starts first
- Application services follow

**What to Watch For:**
- All containers start successfully
- No immediate crashes
- Port bindings successful

#### Phase 7: Health Checks (2-5 minutes)
- Runs comprehensive health checks every 5 seconds
- Maximum 60 attempts (5 minutes)
- Checks:
  - Container status
  - Port availability
  - Database connectivity
  - Redis connectivity
  - API responsiveness

**What to Watch For:**
- Progress through health check attempts
- Services becoming healthy
- All checks eventually passing

**Action if Failed:**
- Review container logs
- Check for configuration errors
- Automatic rollback will be triggered

#### Phase 8: Smoke Tests (1-2 minutes)
- Frontend accessibility (port 3000)
- Backend API health endpoint (port 5000)
- PostgreSQL connectivity
- Redis connectivity
- Prometheus metrics (optional)
- Grafana dashboard (optional)

**What to Watch For:**
- All critical tests passing
- Optional services may fail without blocking

#### Phase 9: Reporting
- Generates deployment report
- Shows running containers
- Displays resource usage
- Saves log file

---

## Expected Timeline

### Normal Deployment

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Pre-Deployment Checks | 2-3 min | 2-3 min |
| Backup | 1-2 min | 3-5 min |
| Tagging | < 1 min | 4-6 min |
| Build | 5-10 min | 9-16 min |
| Stop Old Services | 30-60 sec | 10-17 min |
| Start New Services | 1-2 min | 11-19 min |
| Health Checks | 2-5 min | 13-24 min |
| Smoke Tests | 1-2 min | 14-26 min |
| Reporting | < 1 min | 15-27 min |

**Total Expected Time: 15-30 minutes**

### Deployment with Issues

- **Failed Health Checks**: Add 5-10 minutes for automatic rollback
- **Failed Build**: Immediate failure, no rollback needed
- **Manual Investigation**: Variable, typically 10-30 minutes

---

## Verification Checklist

### Immediate Verification (During Deployment)

- [ ] All containers start successfully
- [ ] No container restart loops
- [ ] All ports are bound correctly
- [ ] Health checks pass
- [ ] Smoke tests pass

### Post-Deployment Verification (After Deployment)

#### 1. Container Status

```bash
docker ps --filter "name=staging-"
```

**Expected Result:**
- All containers show "Up" status
- No containers in "Restarting" state
- Health status shows "healthy" (if configured)

#### 2. Application Accessibility

```bash
# Frontend
curl http://localhost:3000

# Backend
curl http://localhost:5000/health

# Expected: Both return 200 OK
```

#### 3. Database Connectivity

```bash
docker exec staging-postgres pg_isready -U postgres
# Expected: accepting connections
```

#### 4. Redis Connectivity

```bash
docker exec staging-redis redis-cli ping
# Expected: PONG
```

#### 5. Monitoring Stack

```bash
# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3100/api/health

# Expected: Both return OK
```

#### 6. Run Full Health Check

```bash
./healthcheck.sh --verbose
```

**Expected Result:**
- All critical checks pass
- Overall status: HEALTHY

#### 7. Check Logs for Errors

```bash
# Collect recent logs
./logs_collection.sh --lines 100

# Or check individual containers
docker logs staging-backend --tail 50
docker logs staging-frontend --tail 50
```

**What to Look For:**
- No ERROR level logs
- Expected startup messages
- Successful database connections

#### 8. Functional Testing

Manual functional tests:

- [ ] Open frontend in browser: http://localhost:3000
- [ ] Verify dashboard loads correctly
- [ ] Test API endpoint: http://localhost:5000/
- [ ] Check agent control interface
- [ ] Verify Round Table viewer works
- [ ] Test 3D collection demos (if applicable)

#### 9. Performance Check

```bash
# Check resource usage
docker stats --no-stream

# Expected: Reasonable CPU and memory usage
```

#### 10. Database Verification

```bash
docker exec staging-postgres psql -U postgres -c "SELECT version();"
docker exec staging-postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Verify migrations ran
docker exec staging-postgres psql -U postgres -c "\dt"
```

---

## Troubleshooting Guide

### Issue: Deployment Script Fails at Pre-Checks

**Symptoms:**
- Pre-deployment checks fail
- Script exits before backup

**Diagnosis:**
```bash
./pre_deployment_checklist.sh
```

**Solutions:**

1. **Docker not running:**
   ```bash
   # Start Docker Desktop (macOS)
   open -a Docker

   # Or start Docker daemon (Linux)
   sudo systemctl start docker
   ```

2. **Insufficient disk space:**
   ```bash
   # Clean up old Docker images
   docker system prune -a

   # Clean up old backups
   rm -rf staging/backups/202*
   ```

3. **Ports in use:**
   ```bash
   # Find process using port
   lsof -i :3000

   # Kill process (replace PID)
   kill -9 <PID>
   ```

4. **Git not up to date:**
   ```bash
   git pull origin main
   ```

### Issue: Build Fails

**Symptoms:**
- Docker build returns non-zero exit code
- Error messages during npm install or pip install

**Diagnosis:**
```bash
# Check docker-compose logs
docker-compose -f staging/docker-compose.staging.yml logs --tail 50
```

**Solutions:**

1. **Network issues:**
   ```bash
   # Test connectivity
   ping 8.8.8.8
   curl https://registry.npmjs.org

   # Retry build
   ./deploy_to_staging.sh
   ```

2. **Dependency conflicts:**
   ```bash
   # Clear build cache
   docker builder prune -a

   # Rebuild
   ./deploy_to_staging.sh
   ```

3. **Syntax errors in code:**
   ```bash
   # Check recent commits
   git log --oneline -5

   # Run local tests
   make test
   ```

### Issue: Containers Start But Health Checks Fail

**Symptoms:**
- Containers are running
- Health check script fails
- Services not responding

**Diagnosis:**
```bash
# Check container status
docker ps -a --filter "name=staging-"

# Check specific container logs
docker logs staging-backend --tail 100
docker logs staging-frontend --tail 100
docker logs staging-postgres --tail 100

# Check health status
./healthcheck.sh --verbose
```

**Solutions:**

1. **Database not ready:**
   ```bash
   # Check PostgreSQL logs
   docker logs staging-postgres

   # Verify database is accepting connections
   docker exec staging-postgres pg_isready -U postgres

   # If not ready, wait and retry
   sleep 30
   ./healthcheck.sh
   ```

2. **Application errors:**
   ```bash
   # Check application logs for errors
   docker logs staging-backend 2>&1 | grep -i error

   # Check environment variables
   docker exec staging-backend env | grep -E "DATABASE|REDIS"
   ```

3. **Port binding issues:**
   ```bash
   # Verify ports are listening
   lsof -i :3000
   lsof -i :5000
   lsof -i :5432
   lsof -i :6379
   ```

4. **Memory/CPU constraints:**
   ```bash
   # Check resource usage
   docker stats --no-stream

   # Increase Docker resources in Docker Desktop settings
   ```

### Issue: Smoke Tests Fail

**Symptoms:**
- Health checks pass
- Smoke tests fail
- Services not responding to HTTP requests

**Diagnosis:**
```bash
# Test endpoints manually
curl -v http://localhost:3000
curl -v http://localhost:5000/health

# Check container networking
docker network inspect staging_default
```

**Solutions:**

1. **Frontend not responding:**
   ```bash
   # Check Next.js build
   docker logs staging-frontend

   # Verify port mapping
   docker port staging-frontend

   # Restart container
   docker-compose -f staging/docker-compose.staging.yml restart frontend
   ```

2. **Backend not responding:**
   ```bash
   # Check FastAPI startup
   docker logs staging-backend

   # Test backend internally
   docker exec staging-backend curl http://localhost:5000/health

   # Restart container
   docker-compose -f staging/docker-compose.staging.yml restart backend
   ```

### Issue: Database Connection Errors

**Symptoms:**
- Application logs show database connection errors
- "could not connect to server" messages

**Diagnosis:**
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs staging-postgres

# Test connection
docker exec staging-postgres psql -U postgres -c "SELECT 1;"
```

**Solutions:**

1. **PostgreSQL not started:**
   ```bash
   docker-compose -f staging/docker-compose.staging.yml up -d postgres
   ```

2. **Connection string incorrect:**
   ```bash
   # Verify DATABASE_URL in .env.staging
   cat staging/.env.staging | grep DATABASE_URL

   # Should be: postgresql://postgres:password@postgres:5432/dbname
   ```

3. **Database initialization failed:**
   ```bash
   # Stop and remove database
   docker-compose -f staging/docker-compose.staging.yml stop postgres
   docker volume rm staging_postgres_data

   # Restart deployment
   ./deploy_to_staging.sh
   ```

### Issue: Redis Connection Errors

**Symptoms:**
- Application logs show Redis connection errors
- "Connection refused" messages

**Diagnosis:**
```bash
# Check Redis is running
docker ps | grep redis

# Test Redis
docker exec staging-redis redis-cli ping
```

**Solutions:**

1. **Redis not started:**
   ```bash
   docker-compose -f staging/docker-compose.staging.yml up -d redis
   ```

2. **Connection string incorrect:**
   ```bash
   # Verify REDIS_URL in .env.staging
   cat staging/.env.staging | grep REDIS_URL

   # Should be: redis://redis:6379/0
   ```

### Issue: Automatic Rollback Triggered

**Symptoms:**
- Deployment fails during health checks or smoke tests
- Automatic rollback is initiated
- Message: "Deployment failed, initiating automatic rollback..."

**What Happens:**
- Current deployment is stopped
- Previous backup is restored
- Services are restarted with previous version

**Actions:**

1. **Wait for rollback to complete:**
   - Monitor rollback process
   - Verify services return to healthy state

2. **Investigate failure:**
   ```bash
   # Check deployment logs
   cat staging/logs/deploy_*.log | tail -100

   # Check what was being deployed
   git log --oneline -5

   # Review recent changes
   git diff HEAD~1
   ```

3. **Fix issues and retry:**
   - Address root cause
   - Run pre-deployment checklist
   - Retry deployment

---

## Rollback Procedures

### When to Rollback

Rollback if:
- Deployment fails health checks
- Critical bugs discovered after deployment
- Severe performance degradation
- Data integrity issues
- Security vulnerabilities introduced

### Automatic Rollback

Automatic rollback occurs when:
- Health checks fail during deployment
- Smoke tests fail during deployment

**No action required** - the deployment script handles this automatically.

### Manual Rollback

#### Method 1: Using Rollback Script (Recommended)

```bash
cd staging
./rollback.sh
```

**The script will:**
1. Verify backup exists
2. Confirm rollback (unless --auto flag used)
3. Stop current deployment
4. Restore configuration files
5. Restore git version
6. Rebuild Docker images
7. Restore databases
8. Restart all services
9. Run health checks
10. Run smoke tests
11. Generate notification

**Timeline:** 10-15 minutes

#### Method 2: Rollback to Specific Backup

```bash
# List available backups
ls -lt staging/backups/

# Rollback to specific backup
./rollback.sh --backup staging/backups/20251219_143022
```

#### Method 3: Manual Rollback Steps

If rollback script fails:

1. **Stop current services:**
   ```bash
   cd staging
   docker-compose -f docker-compose.staging.yml stop
   docker-compose -f docker-compose.staging.yml rm -f
   ```

2. **Identify last successful deployment:**
   ```bash
   cat staging/.last_backup
   # Shows path to last backup
   ```

3. **Restore configuration:**
   ```bash
   BACKUP_DIR=$(cat staging/.last_backup)
   cp ${BACKUP_DIR}/docker-compose.staging.yml staging/
   cp ${BACKUP_DIR}/.env.staging staging/
   ```

4. **Restore git version:**
   ```bash
   BACKUP_COMMIT=$(cat ${BACKUP_DIR}/git_commit.txt)
   git checkout $BACKUP_COMMIT
   ```

5. **Rebuild and restart:**
   ```bash
   cd staging
   docker-compose -f docker-compose.staging.yml build
   docker-compose -f docker-compose.staging.yml up -d
   ```

6. **Verify:**
   ```bash
   ./healthcheck.sh --verbose
   ```

### Post-Rollback Actions

After successful rollback:

- [ ] Verify all services are healthy
- [ ] Confirm application functionality
- [ ] Notify team of rollback
- [ ] Create incident report
- [ ] Investigate root cause
- [ ] Plan fix and re-deployment

---

## Post-Deployment Tasks

### Immediate (0-30 minutes after deployment)

1. **Monitor Application:**
   - Open Grafana: http://localhost:3100
   - Check dashboards for anomalies
   - Monitor error rates
   - Watch resource usage

2. **Check Logs:**
   ```bash
   # Collect logs for analysis
   ./logs_collection.sh --lines 500

   # Monitor in real-time
   docker-compose -f staging/docker-compose.staging.yml logs -f
   ```

3. **Verify Functionality:**
   - Test critical user paths
   - Verify integrations working
   - Check 3D demos loading
   - Test agent interactions

4. **Update Status:**
   - Update deployment status in monitoring
   - Notify team of successful deployment
   - Close deployment ticket

### Short-term (1-24 hours after deployment)

1. **Monitor Metrics:**
   - Check Prometheus alerts
   - Review Grafana dashboards
   - Monitor error logs
   - Track performance metrics

2. **User Feedback:**
   - Monitor user reports
   - Check for unexpected behavior
   - Review error tracking (Sentry, etc.)

3. **Database Health:**
   ```bash
   # Check query performance
   docker exec staging-postgres psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

   # Check database size growth
   docker exec staging-postgres psql -U postgres -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database;"
   ```

4. **Cleanup:**
   ```bash
   # Remove old Docker images
   docker image prune -a --filter "until=24h"

   # Archive logs
   ./logs_collection.sh
   ```

### Long-term (1-7 days after deployment)

1. **Performance Analysis:**
   - Review Grafana historical data
   - Analyze resource trends
   - Identify optimization opportunities

2. **Backup Verification:**
   - Verify automated backups working
   - Test backup restoration (non-prod)

3. **Documentation:**
   - Update deployment notes
   - Document any issues encountered
   - Update runbook if needed

4. **Retrospective:**
   - Review deployment process
   - Identify improvements
   - Update procedures

---

## Emergency Contacts

### On-Call Rotation

| Role | Primary | Backup |
|------|---------|--------|
| DevOps Engineer | TBD | TBD |
| Backend Engineer | TBD | TBD |
| Frontend Engineer | TBD | TBD |
| Database Admin | TBD | TBD |

### Escalation Path

1. **Level 1**: On-call DevOps Engineer
2. **Level 2**: Engineering Lead
3. **Level 3**: CTO

### Communication Channels

- **Slack**: #deployments, #incidents
- **Email**: devops@skyyrose.com
- **Incident Management**: TBD

---

## Appendix

### A. Script Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `pre_deployment_checklist.sh` | Validates environment before deployment | `./pre_deployment_checklist.sh` |
| `deploy_to_staging.sh` | Executes full deployment | `./deploy_to_staging.sh` |
| `rollback.sh` | Rolls back to previous version | `./rollback.sh [--auto] [--backup <path>]` |
| `healthcheck.sh` | Checks service health | `./healthcheck.sh [-v] [-j]` |
| `logs_collection.sh` | Collects and archives logs | `./logs_collection.sh [-a] [-n <lines>]` |

### B. Directory Structure

```
staging/
├── backups/              # Deployment backups (auto-managed)
│   └── YYYYMMDD_HHMMSS/ # Timestamped backup directories
├── collected_logs/       # Collected log archives
├── logs/                 # Deployment and rollback logs
├── notifications/        # Rollback notifications
├── reports/              # Deployment and health reports
├── docker-compose.staging.yml
├── .env.staging
├── deploy_to_staging.sh
├── rollback.sh
├── healthcheck.sh
├── logs_collection.sh
├── pre_deployment_checklist.sh
└── DEPLOYMENT_RUNBOOK.md (this file)
```

### C. Environment Variables

Required in `.env.staging`:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/skyyrose_staging

# Redis
REDIS_URL=redis://redis:6379/0

# Application
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=info

# API Keys (staging-specific)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### D. Monitoring Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Frontend | http://localhost:3000 | HTML page |
| Backend Health | http://localhost:5000/health | `{"status":"healthy"}` |
| Backend API | http://localhost:5000/ | API documentation |
| PostgreSQL | `docker exec staging-postgres pg_isready` | "accepting connections" |
| Redis | `docker exec staging-redis redis-cli ping` | "PONG" |
| Prometheus | http://localhost:9090/-/healthy | "Prometheus is Healthy" |
| Grafana | http://localhost:3100/api/health | `{"database":"ok"}` |
| Alertmanager | http://localhost:9093/-/healthy | "Alertmanager is Healthy" |

### E. Common Docker Commands

```bash
# View running containers
docker ps --filter "name=staging-"

# View all containers (including stopped)
docker ps -a --filter "name=staging-"

# Check container logs
docker logs staging-backend --tail 100 --follow

# Execute command in container
docker exec -it staging-backend bash

# Restart specific service
docker-compose -f staging/docker-compose.staging.yml restart backend

# View resource usage
docker stats --filter "name=staging-"

# Remove all staging containers
docker-compose -f staging/docker-compose.staging.yml down

# Remove containers and volumes
docker-compose -f staging/docker-compose.staging.yml down -v
```

### F. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-19 | DevOps | Initial runbook creation |

---

## Quick Reference Card

### Standard Deployment

```bash
cd staging
./pre_deployment_checklist.sh  # Verify readiness
./deploy_to_staging.sh          # Deploy
./healthcheck.sh --verbose      # Verify
```

### Emergency Rollback

```bash
cd staging
./rollback.sh                   # Rollback to last version
./healthcheck.sh --verbose      # Verify
```

### Health Check

```bash
cd staging
./healthcheck.sh --verbose      # Detailed health check
./healthcheck.sh --json         # JSON output
```

### Log Collection

```bash
cd staging
./logs_collection.sh            # Collect last 1000 lines
./logs_collection.sh --all      # Collect all logs
./logs_collection.sh -n 5000    # Collect last 5000 lines
```

---

**Remember**: When in doubt, run the health check and check the logs. Always prioritize safety over speed.
