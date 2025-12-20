# DevSkyy Phase 2 - Staging Deployment Guide

**Version:** 2.0.0
**Last Updated:** 2025-12-19
**Environment:** Staging
**Deployment Type:** Docker Compose

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Steps](#deployment-steps)
5. [Post-Deployment Verification](#post-deployment-verification)
6. [Monitoring Setup](#monitoring-setup)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)
9. [Maintenance Tasks](#maintenance-tasks)

---

## Prerequisites

### System Requirements

- **Operating System:** Ubuntu 20.04+ or compatible Linux distribution
- **Docker:** Version 20.10+
- **Docker Compose:** Version 2.0+
- **RAM:** Minimum 8GB (16GB recommended)
- **Disk Space:** Minimum 50GB free
- **CPU:** 4 cores minimum (8 cores recommended)

### Access Requirements

- SSH access to staging server
- GitHub repository access
- Docker Hub credentials (if using private images)
- API keys for all external services
- Domain DNS configuration access

### Installation Commands

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

---

## Pre-Deployment Checklist

### Infrastructure Checklist

- [ ] Server provisioned and accessible via SSH
- [ ] Firewall rules configured (ports 80, 443, 8000, 3000, 9090, 9093)
- [ ] SSL certificates obtained (Let's Encrypt or commercial)
- [ ] DNS records configured for staging.devskyy.com
- [ ] Backup storage configured
- [ ] Log aggregation endpoint ready

### Security Checklist

- [ ] All secrets rotated from development environment
- [ ] API keys created with staging-specific rate limits
- [ ] Database credentials generated (strong passwords)
- [ ] JWT secrets generated (256-bit minimum)
- [ ] Encryption master key generated (base64-encoded 32 bytes)
- [ ] Firewall rules tested
- [ ] SSH key-based authentication configured
- [ ] Disable password authentication in SSH

### Configuration Checklist

- [ ] `.env.staging` file prepared with all required values
- [ ] All API keys validated and active
- [ ] Slack webhook URL tested
- [ ] Email alert configuration verified
- [ ] CORS origins configured correctly
- [ ] WordPress staging site accessible

---

## Environment Configuration

### Step 1: Clone Repository

```bash
# SSH to staging server
ssh user@staging.devskyy.com

# Create application directory
sudo mkdir -p /opt/devskyy
sudo chown $USER:$USER /opt/devskyy
cd /opt/devskyy

# Clone repository
git clone https://github.com/yourusername/DevSkyy.git .
git checkout main  # or specific release tag
```

### Step 2: Configure Environment Variables

```bash
# Copy staging environment template
cp .env.staging .env

# Edit environment file with secure values
nano .env
```

**CRITICAL VARIABLES TO CHANGE:**

```bash
# Generate strong passwords
POSTGRES_PASSWORD=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 64)
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 16)

# Generate encryption master key (32 bytes, base64 encoded)
ENCRYPTION_MASTER_KEY=$(openssl rand -base64 32)

# Update in .env file
sed -i "s/CHANGE_THIS_PASSWORD/$POSTGRES_PASSWORD/g" .env
sed -i "s/staging-jwt-key-CHANGE-IN-PRODUCTION-use-secrets-manager/$JWT_SECRET_KEY/g" .env
sed -i "s/CHANGE_THIS_BASE64_ENCODED_KEY_32_BYTES/$ENCRYPTION_MASTER_KEY/g" .env
```

### Step 3: Add API Keys

Edit `.env` and add your staging API keys:

```bash
# LLM Provider Keys
OPENAI_API_KEY=sk-staging-your-actual-key
ANTHROPIC_API_KEY=sk-ant-staging-your-actual-key
GOOGLE_API_KEY=staging-your-actual-key
MISTRAL_API_KEY=staging-your-actual-key
COHERE_API_KEY=staging-your-actual-key
GROQ_API_KEY=staging-your-actual-key

# Visual Generation
TRIPO3D_API_KEY=staging-your-actual-key
FASHN_API_KEY=staging-your-actual-key

# Vector Store
PINECONE_API_KEY=staging-your-actual-key

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/ACTUAL/WEBHOOK
```

### Step 4: Configure Monitoring

```bash
# Create monitoring configuration directories
mkdir -p config/prometheus
mkdir -p config/grafana/provisioning/datasources
mkdir -p config/grafana/provisioning/dashboards
mkdir -p config/grafana/dashboards
mkdir -p config/alertmanager
mkdir -p config/loki
mkdir -p config/promtail
```

Copy staging-specific configurations (see Configuration Files section below).

---

## Deployment Steps

### Step 1: Pre-Deployment Backup

If this is an update to existing staging environment:

```bash
# Run backup script
./staging/backup.sh

# Verify backup created
ls -lh /opt/devskyy/data/backups/
```

### Step 2: Build Docker Images

```bash
# Build all images
docker-compose -f docker-compose.staging.yml build

# Verify images built successfully
docker images | grep devskyy
```

### Step 3: Initialize Volumes

```bash
# Create required directories
mkdir -p logs data uploads config/staging/postgres-backup

# Set proper permissions
chmod 755 logs data uploads
chmod 700 config/staging/postgres-backup
```

### Step 4: Start Infrastructure Services

Start services in dependency order:

```bash
# Start database first
docker-compose -f docker-compose.staging.yml up -d postgres

# Wait for database to be healthy (30 seconds)
sleep 30

# Verify database health
docker-compose -f docker-compose.staging.yml ps postgres

# Start Redis
docker-compose -f docker-compose.staging.yml up -d redis

# Wait for Redis to be healthy
sleep 10

# Verify Redis health
docker-compose -f docker-compose.staging.yml ps redis
```

### Step 5: Initialize Database

```bash
# Run database migrations
docker-compose -f docker-compose.staging.yml exec postgres psql -U staging_user -d devskyy_staging -f /docker-entrypoint-initdb.d/init-db.sql

# Verify tables created
docker-compose -f docker-compose.staging.yml exec postgres psql -U staging_user -d devskyy_staging -c "\dt"
```

### Step 6: Start Application

```bash
# Start main application
docker-compose -f docker-compose.staging.yml up -d devskyy-app

# Watch logs for startup
docker-compose -f docker-compose.staging.yml logs -f devskyy-app

# Wait for healthcheck to pass (check for "healthy" status)
watch docker-compose -f docker-compose.staging.yml ps
```

### Step 7: Start Reverse Proxy

```bash
# Start Nginx
docker-compose -f docker-compose.staging.yml up -d nginx

# Verify Nginx configuration
docker-compose -f docker-compose.staging.yml exec nginx nginx -t

# Check Nginx logs
docker-compose -f docker-compose.staging.yml logs nginx
```

### Step 8: Start Monitoring Stack

```bash
# Start monitoring services
docker-compose -f docker-compose.staging.yml up -d prometheus grafana alertmanager loki promtail

# Start exporters
docker-compose -f docker-compose.staging.yml up -d postgres-exporter redis-exporter node-exporter

# Verify all services running
docker-compose -f docker-compose.staging.yml ps
```

### Step 9: Automated Deployment Script

Alternatively, use the automated deployment script:

```bash
# Make script executable
chmod +x staging/deploy.sh

# Run deployment
./staging/deploy.sh
```

---

## Post-Deployment Verification

### Step 1: Run Verification Script

```bash
# Make verification script executable
chmod +x staging/verify-deployment.sh

# Run verification
./staging/verify-deployment.sh
```

### Step 2: Manual Health Checks

```bash
# Check application health endpoint
curl -f http://localhost:8000/health

# Check Prometheus
curl -f http://localhost:9090/-/healthy

# Check Grafana
curl -f http://localhost:3000/api/health

# Check AlertManager
curl -f http://localhost:9093/-/healthy

# Check Loki
curl -f http://localhost:3100/ready
```

### Step 3: Verify Database Connectivity

```bash
# Connect to database
docker-compose -f docker-compose.staging.yml exec postgres psql -U staging_user -d devskyy_staging

# Run test query
SELECT version();
\q
```

### Step 4: Verify Redis Connectivity

```bash
# Connect to Redis
docker-compose -f docker-compose.staging.yml exec redis redis-cli

# Test commands
PING
SET test_key "test_value"
GET test_key
DEL test_key
EXIT
```

### Step 5: Test API Endpoints

```bash
# Test authentication endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

# Test agent endpoint
curl http://localhost:8000/api/v1/agents/status
```

### Step 6: Verify Monitoring Dashboards

1. **Prometheus:** http://staging.devskyy.com:9090
   - Check targets are UP: Status > Targets
   - Verify metrics collection: Graph > Execute sample query

2. **Grafana:** http://staging.devskyy.com:3000
   - Login with admin credentials
   - Verify datasources: Configuration > Data Sources
   - Check dashboards load correctly

3. **AlertManager:** http://staging.devskyy.com:9093
   - Verify alerts routing configuration
   - Send test alert

---

## Monitoring Setup

### Prometheus Configuration

Create `/opt/devskyy/config/prometheus/prometheus.staging.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: 'staging'
    cluster: 'devskyy'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/alerts/*.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'devskyy-app'
    static_configs:
      - targets: ['devskyy-app:8000']
    metrics_path: '/metrics'

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### AlertManager Configuration

Create `/opt/devskyy/config/alertmanager/alertmanager.staging.yml`:

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: '${SLACK_WEBHOOK_URL}'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'staging-alerts'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'staging-alerts'
    slack_configs:
      - channel: '#staging-alerts'
        title: 'Staging Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'critical-alerts'
    slack_configs:
      - channel: '#critical-alerts'
        title: 'CRITICAL: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true

  - name: 'warning-alerts'
    slack_configs:
      - channel: '#staging-alerts'
        title: 'WARNING: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
        send_resolved: true
```

### Grafana Datasource Configuration

Create `/opt/devskyy/config/grafana/provisioning/datasources/datasources.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
```

---

## Troubleshooting

### Common Issues

#### Issue: Container won't start

```bash
# Check logs
docker-compose -f docker-compose.staging.yml logs [service_name]

# Check resource usage
docker stats

# Check disk space
df -h
```

#### Issue: Database connection failed

```bash
# Verify database is running
docker-compose -f docker-compose.staging.yml ps postgres

# Check database logs
docker-compose -f docker-compose.staging.yml logs postgres

# Test connection manually
docker-compose -f docker-compose.staging.yml exec postgres psql -U staging_user -d devskyy_staging
```

#### Issue: Application health check failing

```bash
# Check application logs
docker-compose -f docker-compose.staging.yml logs devskyy-app

# Check for port conflicts
sudo netstat -tulpn | grep 8000

# Restart application
docker-compose -f docker-compose.staging.yml restart devskyy-app
```

#### Issue: Prometheus targets down

```bash
# Check Prometheus logs
docker-compose -f docker-compose.staging.yml logs prometheus

# Verify target services are running
docker-compose -f docker-compose.staging.yml ps

# Check network connectivity
docker-compose -f docker-compose.staging.yml exec prometheus wget -O- http://devskyy-app:8000/metrics
```

#### Issue: Out of disk space

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Remove old logs
find /opt/devskyy/logs -name "*.log" -mtime +30 -delete
```

---

## Rollback Procedures

### Quick Rollback

```bash
# Stop current deployment
docker-compose -f docker-compose.staging.yml down

# Restore from backup
./staging/restore.sh [backup_timestamp]

# Start services
docker-compose -f docker-compose.staging.yml up -d
```

### Rolling Back to Previous Git Version

```bash
# Check available tags
git tag -l

# Checkout previous version
git checkout [previous_tag]

# Rebuild images
docker-compose -f docker-compose.staging.yml build

# Restart services
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml up -d
```

### Database Rollback

```bash
# List available backups
ls -lh config/staging/postgres-backup/

# Stop application
docker-compose -f docker-compose.staging.yml stop devskyy-app

# Restore database
docker-compose -f docker-compose.staging.yml exec postgres psql -U staging_user -d devskyy_staging < config/staging/postgres-backup/[backup_file]

# Start application
docker-compose -f docker-compose.staging.yml start devskyy-app
```

---

## Maintenance Tasks

### Daily Tasks

```bash
# Check service health
docker-compose -f docker-compose.staging.yml ps

# Review logs for errors
docker-compose -f docker-compose.staging.yml logs --tail=100 | grep -i error

# Check disk usage
df -h
docker system df
```

### Weekly Tasks

```bash
# Review Grafana dashboards for anomalies
# Check AlertManager for recurring alerts
# Review security logs
# Update API rate limits if needed
```

### Monthly Tasks

```bash
# Rotate secrets (if policy requires)
# Review and archive old logs
# Update Docker images
docker-compose -f docker-compose.staging.yml pull
docker-compose -f docker-compose.staging.yml up -d

# Cleanup old backups
find /opt/devskyy/data/backups -name "*.sql" -mtime +30 -delete
```

### Backup Schedule

```bash
# Daily automated backups via cron
0 2 * * * /opt/devskyy/staging/backup.sh

# Verify cron job
crontab -l
```

---

## Security Best Practices

1. **Never commit `.env` files to version control**
2. **Rotate secrets every 90 days minimum**
3. **Use separate API keys for staging (with spending limits)**
4. **Enable MFA for all admin accounts**
5. **Regularly update Docker images for security patches**
6. **Monitor failed authentication attempts**
7. **Keep firewall rules minimal (principle of least privilege)**
8. **Regularly review access logs**
9. **Use HTTPS for all external communication**
10. **Enable audit logging for all sensitive operations**

---

## Support & Escalation

### Internal Team Contacts

- **DevOps Lead:** devops@devskyy.com
- **Security Team:** security@devskyy.com
- **On-Call Engineer:** oncall@devskyy.com

### Monitoring Alerts

- **Slack Channel:** #staging-alerts
- **Critical Alerts:** #critical-alerts
- **PagerDuty:** staging-oncall rotation

### Documentation

- **Architecture Docs:** `/docs/architecture/`
- **API Docs:** https://staging.devskyy.com/docs
- **Runbooks:** `/docs/runbooks/`

---

## Appendix

### Useful Commands

```bash
# View all running containers
docker-compose -f docker-compose.staging.yml ps

# Follow logs for all services
docker-compose -f docker-compose.staging.yml logs -f

# Restart specific service
docker-compose -f docker-compose.staging.yml restart [service_name]

# Execute command in container
docker-compose -f docker-compose.staging.yml exec [service_name] [command]

# View resource usage
docker stats

# Clean up everything (DANGEROUS)
docker-compose -f docker-compose.staging.yml down -v
```

### Environment Variable Reference

See `staging/environment-variables.yaml` for complete documentation of all environment variables.

---

**Document Version:** 1.0
**Last Reviewed:** 2025-12-19
**Next Review:** 2026-01-19
