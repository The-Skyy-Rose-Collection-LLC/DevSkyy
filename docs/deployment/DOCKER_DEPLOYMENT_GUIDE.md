# DevSkyy Docker Deployment Guide

**Version:** 5.2.0
**Status:** Production-Ready ✅
**Truth Protocol:** Compliant
**Last Updated:** 2025-11-20

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Development Setup](#development-setup)
6. [Staging Setup](#staging-setup)
7. [Production Setup](#production-setup)
8. [Configuration](#configuration)
9. [Monitoring & Observability](#monitoring--observability)
10. [Security](#security)
11. [Backup & Recovery](#backup--recovery)
12. [Troubleshooting](#troubleshooting)
13. [Performance Optimization](#performance-optimization)

---

## Overview

DevSkyy uses a **multi-stage Docker architecture** supporting three environments:

- **Development**: Hot reload, debugging tools, database UIs
- **Staging**: Production-like testing environment
- **Production**: Full monitoring, security hardening, auto-scaling

### Key Features

✅ Multi-stage Dockerfile (single source of truth)
✅ Environment-specific docker-compose configurations
✅ PostgreSQL 15 + Redis 7 + Nginx + Prometheus + Grafana
✅ Automated database backups
✅ SSL/TLS termination
✅ Health checks & auto-restart
✅ Resource limits & performance monitoring
✅ Truth Protocol compliant (15/15 rules)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Nginx (Reverse Proxy)                 │
│            SSL/TLS Termination, Rate Limiting           │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────────┐
   │   API   │  │   API   │  │   API    │
   │ Worker1 │  │ Worker2 │  │ Worker3  │
   └────┬────┘  └────┬────┘  └────┬─────┘
        │            │            │
        └────────────┼────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   ┌──────────┐  ┌─────────┐  ┌───────────┐
   │PostgreSQL│  │  Redis  │  │Prometheus │
   │    DB    │  │  Cache  │  │ Monitoring│
   └──────────┘  └─────────┘  └───────────┘
        │                           │
        ▼                           ▼
   ┌──────────┐              ┌───────────┐
   │  Backup  │              │  Grafana  │
   │ Service  │              │Dashboards │
   └──────────┘              └───────────┘
```

---

## Prerequisites

### Required

- **Docker:** 24.0.0+
- **Docker Compose:** 2.20.0+
- **Git:** For version control
- **Minimum Resources:**
  - CPU: 2 cores
  - RAM: 4GB
  - Disk: 20GB

### Recommended (Production)

- **CPU:** 4+ cores
- **RAM:** 8GB+
- **Disk:** 100GB+ SSD
- **OS:** Ubuntu 22.04 LTS / Debian 12
- **Domain:** Configured DNS pointing to server

### Verification

```bash
# Check Docker version
docker --version
# Docker version 24.0.0 or higher

# Check Docker Compose version
docker-compose --version
# Docker Compose version v2.20.0 or higher

# Check system resources
docker info | grep -E 'CPUs|Total Memory'
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy
```

### 2. Set Up Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit with your secrets
nano .env
```

**Required Variables:**

```env
# Application
SECRET_KEY=your-secret-key-change-me-in-production
ENVIRONMENT=development

# AI API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Database
POSTGRES_DB=devskyy
POSTGRES_USER=devskyy
POSTGRES_PASSWORD=secure-password-here

# Redis (Production only)
REDIS_PASSWORD=secure-redis-password

# Monitoring (Production only)
GRAFANA_PASSWORD=secure-grafana-password
```

### 3. Choose Your Environment

**Development:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**Staging:**
```bash
docker-compose -f docker-compose.staging.yml up -d
```

**Production:**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Verify Deployment

```bash
# Check running containers
docker-compose -f docker-compose.dev.yml ps

# Check API health
curl http://localhost:8000/health

# View logs
docker-compose -f docker-compose.dev.yml logs -f api
```

---

## Development Setup

### Features

✅ Hot code reload
✅ Debug port (5678)
✅ Database UI (Adminer)
✅ Redis UI (Redis Commander)
✅ Email testing (Mailhog)

### Start Development Environment

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Access shell
docker-compose -f docker-compose.dev.yml exec api bash
```

### Access Services

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Main application |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Adminer | http://localhost:8080 | Database UI |
| Redis Commander | http://localhost:8081 | Redis UI |
| Mailhog | http://localhost:8025 | Email testing |

### Run Tests

```bash
# Run all tests
docker-compose -f docker-compose.dev.yml exec api pytest

# Run with coverage
docker-compose -f docker-compose.dev.yml exec api pytest --cov=. --cov-report=html

# Run specific test file
docker-compose -f docker-compose.dev.yml exec api pytest tests/test_api.py
```

### Database Operations

```bash
# Access PostgreSQL shell
docker-compose -f docker-compose.dev.yml exec postgres psql -U devskyy -d devskyy

# Run migrations
docker-compose -f docker-compose.dev.yml exec api alembic upgrade head

# Create new migration
docker-compose -f docker-compose.dev.yml exec api alembic revision --autogenerate -m "description"
```

### Stop Development Environment

```bash
# Stop services (keep data)
docker-compose -f docker-compose.dev.yml down

# Stop and remove volumes (clean slate)
docker-compose -f docker-compose.dev.yml down -v
```

---

## Staging Setup

Staging mimics production but with:
- Reduced resources
- More verbose logging
- Exposed debugging ports
- Test data instead of production data

### Deploy Staging

```bash
# Build and start
docker-compose -f docker-compose.staging.yml up -d --build

# Check status
docker-compose -f docker-compose.staging.yml ps

# View logs
docker-compose -f docker-compose.staging.yml logs -f
```

### Access Services

| Service | URL | Description |
|---------|-----|-------------|
| API | http://localhost:8000 | Main application |
| Prometheus | http://localhost:9090 | Metrics |
| Grafana | http://localhost:3000 | Dashboards |

### Run Integration Tests

```bash
# Full integration test suite
docker-compose -f docker-compose.staging.yml exec api pytest tests/integration/

# Load testing
docker-compose -f docker-compose.staging.yml exec api \
  locust -f tests/performance/locustfile.py --host=http://localhost:8000
```

---

## Production Setup

### 1. Pre-Deployment Checklist

- [ ] Domain DNS configured
- [ ] SSL certificates obtained
- [ ] All secrets configured in `.env`
- [ ] Firewall rules configured
- [ ] Backup strategy documented
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented

### 2. Generate SSL Certificates

**Option A: Let's Encrypt (Recommended)**

```bash
# Install Certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone \
  -d your-domain.com \
  -d www.your-domain.com \
  --email your-email@example.com \
  --agree-tos

# Copy to Docker volume
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem \
  docker/nginx/ssl/fullchain.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem \
  docker/nginx/ssl/privkey.pem

# Set permissions
chmod 600 docker/nginx/ssl/privkey.pem
```

**Option B: Self-Signed (Development/Testing Only)**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/privkey.pem \
  -out docker/nginx/ssl/fullchain.pem \
  -subj "/C=US/ST=State/L=City/O=DevSkyy/CN=localhost"
```

### 3. Configure Production Environment

```bash
# Create production .env
cat > .env << EOF
# Production Configuration
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Secrets (CHANGE THESE!)
SECRET_KEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)
GRAFANA_PASSWORD=$(openssl rand -base64 32)

# API Keys
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here

# Database
POSTGRES_DB=devskyy
POSTGRES_USER=devskyy

# Domain
DOMAIN=your-domain.com
EOF

# Generate DATABASE_URL with the password (must be done separately for proper expansion)
POSTGRES_PASSWORD=$(grep POSTGRES_PASSWORD= .env.prod | cut -d= -f2)
echo "DATABASE_URL=postgresql://devskyy:${POSTGRES_PASSWORD}@postgres:5432/devskyy" >> .env.prod
```

### 4. Deploy to Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --build-arg VCS_REF=$(git rev-parse --short HEAD)

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f api

# Check health
curl https://your-domain.com/health
```

### 5. Post-Deployment Verification

```bash
# Check all services are healthy
docker-compose -f docker-compose.prod.yml ps

# Test API endpoint
curl -k https://your-domain.com/api/v1/monitoring/health

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# View Grafana dashboards
# https://your-domain.com/grafana
```

---

## Configuration

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | `development` | `development`, `staging`, or `production` |
| `DEBUG` | No | `false` | Enable debug mode |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `SECRET_KEY` | Yes | - | Application secret key (32+ chars) |
| `ANTHROPIC_API_KEY` | Yes | - | Anthropic Claude API key |
| `OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `POSTGRES_DB` | Yes | `devskyy` | Database name |
| `POSTGRES_USER` | Yes | `devskyy` | Database user |
| `POSTGRES_PASSWORD` | Yes | - | Database password |
| `REDIS_PASSWORD` | Prod | - | Redis password (production only) |
| `GRAFANA_PASSWORD` | Prod | `admin` | Grafana admin password |
| `DOMAIN` | Prod | - | Production domain name |

### Resource Limits

**Development:**
- API: 2 CPU, 4GB RAM
- PostgreSQL: 0.5 CPU, 1GB RAM
- Redis: 0.3 CPU, 256MB RAM

**Production:**
- API: 2 CPU, 4GB RAM (reserving 1 CPU, 2GB RAM)
- PostgreSQL: 1 CPU, 2GB RAM (reserving 0.5 CPU, 1GB RAM)
- Redis: 0.5 CPU, 1GB RAM
- Nginx: 0.5 CPU, 512MB RAM

---

## Monitoring & Observability

### Prometheus Metrics

Access: `http://localhost:9090` (staging) or `https://your-domain.com/prometheus` (production)

**Key Metrics (Truth Protocol Rule #12):**

```promql
# P95 Latency (target: < 200ms)
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Error Rate (target: < 0.5%)
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Request Rate
rate(http_requests_total[5m])

# Database Connections
pg_stat_database_numbackends

# Cache Hit Ratio (target: > 80%)
redis_keyspace_hits_total / (redis_keyspace_hits_total + redis_keyspace_misses_total) * 100
```

### Grafana Dashboards

Access: `http://localhost:3000` (staging) or `https://your-domain.com/grafana` (production)

**Default Login:**
- Username: `admin`
- Password: From `GRAFANA_PASSWORD` env variable

**Recommended Dashboards:**
1. Application Performance (P95, throughput, errors)
2. Database Metrics (connections, queries, cache hits)
3. System Resources (CPU, memory, disk, network)
4. Container Metrics (per-service resource usage)

### Logs

```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service
docker-compose -f docker-compose.prod.yml logs -f api

# View last 100 lines
docker-compose -f docker-compose.prod.yml logs --tail=100 api

# Follow logs with timestamps
docker-compose -f docker-compose.prod.yml logs -f -t api
```

### Health Checks

```bash
# API health
curl https://your-domain.com/health

# Detailed monitoring endpoint
curl https://your-domain.com/api/v1/monitoring/health

# Database health
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U devskyy -d devskyy -c "SELECT * FROM devskyy.check_database_health();"

# Redis health
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

---

## Security

### Truth Protocol Rule #13: Security Baseline

✅ **Encryption:** AES-256-GCM for data at rest
✅ **TLS:** TLS 1.2+ for all external connections
✅ **Authentication:** OAuth2 + JWT (HS256/RS256)
✅ **Password Hashing:** Argon2id + bcrypt
✅ **Non-root Containers:** All services run as non-root
✅ **Secrets Management:** Environment variables only
✅ **Rate Limiting:** 100 req/min per IP (API)

### Security Best Practices

1. **Never commit secrets to Git**
   ```bash
   # Check for leaked secrets
   docker-compose -f docker-compose.prod.yml exec api \
     detect-secrets scan --all-files
   ```

2. **Rotate secrets regularly**
   ```bash
   # Generate new SECRET_KEY
   openssl rand -base64 32
   ```

3. **Keep images updated**
   ```bash
   # Pull latest base images
   docker-compose -f docker-compose.prod.yml pull

   # Rebuild with security updates
   docker-compose -f docker-compose.prod.yml build --no-cache
   ```

4. **Scan for vulnerabilities**
   ```bash
   # Install Trivy
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     aquasec/trivy image devskyy:prod
   ```

5. **Review security scan reports**
   ```bash
   # Run Bandit security linter
   docker-compose -f docker-compose.prod.yml exec api \
     bandit -r . -f json -o /app/artifacts/bandit-report.json
   ```

---

## Backup & Recovery

### Automated Backups

Production deployment includes automatic PostgreSQL backups:

- **Schedule:** Daily at midnight UTC
- **Retention:** 7 days, 4 weeks, 6 months
- **Location:** `postgres-backups` volume

### Manual Backup

```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec backup backup

# List backups
docker-compose -f docker-compose.prod.yml exec postgres \
  ls -lh /backups/

# Export backup to host
docker cp devskyy-postgres-prod:/backups/latest.dump ./backup-$(date +%Y%m%d).dump
```

### Restore from Backup

```bash
# Stop API to prevent connections
docker-compose -f docker-compose.prod.yml stop api

# Restore database
docker-compose -f docker-compose.prod.yml exec postgres \
  pg_restore -U devskyy -d devskyy --clean --if-exists /backups/latest.dump

# Restart API
docker-compose -f docker-compose.prod.yml start api
```

### Disaster Recovery

```bash
# 1. Stop all services
docker-compose -f docker-compose.prod.yml down

# 2. Backup volumes
docker run --rm \
  -v devskyy-prod_postgres-prod-data:/source \
  -v $(pwd)/backups:/backup \
  alpine tar -czf /backup/postgres-data-$(date +%Y%m%d).tar.gz -C /source .

# 3. Restore volumes
docker run --rm \
  -v devskyy-prod_postgres-prod-data:/target \
  -v $(pwd)/backups:/backup \
  alpine tar -xzf /backup/postgres-data-20251120.tar.gz -C /target

# 4. Restart services
docker-compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
sudo lsof -i :8000

# Kill process or change port in docker-compose
```

#### 2. Container Fails to Start

**Solution:**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Check resource usage
docker stats

# Inspect container
docker inspect devskyy-api-prod
```

#### 3. Database Connection Failed

**Solution:**
```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U devskyy -d devskyy -c "SELECT 1;"
```

#### 4. High Memory Usage

**Solution:**
```bash
# Check memory usage
docker stats

# Reduce workers in .env
WORKERS=2

# Restart with new config
docker-compose -f docker-compose.prod.yml restart api
```

#### 5. Slow API Response

**Solution:**
```bash
# Check P95 latency in Prometheus
# Query: histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Check database slow queries
docker-compose -f docker-compose.prod.yml exec postgres \
  psql -U devskyy -d devskyy -c "SELECT * FROM devskyy.slow_queries;"

# Check Redis cache hit ratio
docker-compose -f docker-compose.prod.yml exec redis \
  redis-cli INFO stats | grep keyspace
```

### Debug Mode

```bash
# Enable debug logging
docker-compose -f docker-compose.dev.yml exec api \
  bash -c "export LOG_LEVEL=DEBUG && python -m uvicorn main:app --reload"

# Check environment variables
docker-compose -f docker-compose.dev.yml exec api env | sort
```

---

## Performance Optimization

### Truth Protocol Rule #12: P95 < 200ms SLO

**Optimization Strategies:**

1. **Increase Workers**
   ```yaml
   # docker-compose.prod.yml
   environment:
     - WORKERS=8  # Adjust based on CPU cores
   ```

2. **Enable Redis Caching**
   ```python
   # Implement caching in application code
   # Example: Cache expensive queries for 5 minutes
   ```

3. **Database Connection Pooling**
   ```python
   # SQLAlchemy configuration
   pool_size=20
   max_overflow=10
   pool_pre_ping=True
   ```

4. **Optimize Database Queries**
   ```bash
   # Check slow queries
   docker-compose -f docker-compose.prod.yml exec postgres \
     psql -U devskyy -d devskyy -c "SELECT * FROM devskyy.slow_queries;"

   # Add indexes for slow queries
   ```

5. **Enable Gzip Compression** (Already configured in Nginx)

6. **Use CDN for Static Assets**

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/performance/locustfile.py --host=https://your-domain.com

# Target metrics:
# - P95 latency < 200ms
# - Error rate < 0.5%
# - Throughput > 1000 req/s (adjust based on requirements)
```

---

## Updating Deployment

### Rolling Update (Zero Downtime)

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Update services one at a time
docker-compose -f docker-compose.prod.yml up -d --no-deps --build api

# Verify health
curl https://your-domain.com/health
```

### Database Migrations

```bash
# Create migration
docker-compose -f docker-compose.prod.yml exec api \
  alembic revision --autogenerate -m "Add new table"

# Review migration file
cat migrations/versions/xxx_add_new_table.py

# Apply migration
docker-compose -f docker-compose.prod.yml exec api \
  alembic upgrade head

# Rollback if needed
docker-compose -f docker-compose.prod.yml exec api \
  alembic downgrade -1
```

---

## Additional Resources

- **Truth Protocol:** See [CLAUDE.md](./CLAUDE.md)
- **API Documentation:** `https://your-domain.com/docs`
- **Enterprise Deployment:** See [ENTERPRISE_DEPLOYMENT.md](./ENTERPRISE_DEPLOYMENT.md)
- **Security Guidelines:** See [SECURITY.md](./SECURITY.md)
- **Contributing:** See [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review application logs
3. Open GitHub issue: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues

---

**DevSkyy v5.2.0 | Truth Protocol Compliant ✅ | Last Updated: 2025-11-20**
