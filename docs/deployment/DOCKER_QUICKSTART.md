# 🐳 Docker Quick Start Guide

## ✅ Ready to Deploy with Docker

Your DevSkyy Enterprise Platform is **fully configured** for production Docker deployment.

---

## 🚀 Quick Deploy (3 Steps)

### 1. Set Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and add your keys:

```bash
# Required
SECRET_KEY=your-super-secret-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# Database (PostgreSQL)
POSTGRES_DB=devskyy
POSTGRES_USER=devskyy
POSTGRES_PASSWORD=strong-password-here
DATABASE_URL=postgresql://devskyy:strong-password-here@postgres:5432/devskyy

# Optional
REDIS_URL=redis://redis:6379
LOG_LEVEL=INFO
GRAFANA_PASSWORD=admin
```

### 2. Build & Start

**Option A: Full Stack with Monitoring**
```bash
docker-compose -f docker-compose.production.yml up -d
```

**Option B: Basic Stack (API + Database + Redis)**
```bash
docker-compose up -d api postgres redis
```

**Option C: Development Mode**
```bash
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check containers are running
docker-compose ps

# Check health
curl http://localhost:8000/health

# View API docs
open http://localhost:8000/api/v1/docs
```

---

## 📋 What Gets Deployed

### Full Production Stack

When you run `docker-compose -f docker-compose.production.yml up -d`:

✅ **DevSkyy API** (http://localhost:8000)
- FastAPI application
- 4 workers (configurable)
- Auto-restart on failure
- Health checks every 30s

✅ **PostgreSQL 15** (localhost:5432)
- Production database
- Persistent data volume
- Automated backups

✅ **Redis 7** (localhost:6379)
- Caching layer
- Session storage
- Message queue

✅ **Nginx** (http://localhost:80, https://localhost:443)
- Reverse proxy
- SSL termination
- Load balancing
- Static file serving

✅ **Prometheus** (http://localhost:9090)
- Metrics collection
- 30-day retention
- Custom dashboards

✅ **Grafana** (http://localhost:3000)
- Monitoring dashboards
- Real-time metrics
- Alerting

---

## 🔧 Common Commands

### Container Management

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart a service
docker-compose restart api

# View logs
docker-compose logs -f api

# Execute command in container
docker-compose exec api python -m pytest
```

### Database Operations

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U devskyy -d devskyy

# Backup database
docker-compose exec postgres pg_dump -U devskyy devskyy > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T postgres psql -U devskyy devskyy

# Run migrations
docker-compose exec api alembic upgrade head
```

### Monitoring

```bash
# View container stats
docker stats

# Check health status
docker-compose ps

# View API logs
docker-compose logs -f --tail=100 api

# Check Redis
docker-compose exec redis redis-cli ping

# Check PostgreSQL
docker-compose exec postgres pg_isready -U devskyy
```

---

## 🏗️ Deployment Scenarios

### Scenario 1: Local Development

```bash
# Start with hot reload
docker-compose up -d

# Make changes to code
# Container automatically reloads

# Run tests
docker-compose exec api pytest
```

### Scenario 2: Production Server

```bash
# Use production compose file
docker-compose -f docker-compose.production.yml up -d

# Enable monitoring
docker-compose -f docker-compose.production.yml --profile with-monitoring up -d

# Enable Nginx reverse proxy
docker-compose -f docker-compose.production.yml --profile with-nginx up -d
```

### Scenario 3: Cloud Deployment (AWS, GCP, Azure)

```bash
# Build for cloud
docker build -f Dockerfile.production -t devskyy:5.2.0 .

# Tag for registry
docker tag devskyy:5.2.0 your-registry/devskyy:5.2.0

# Push to registry
docker push your-registry/devskyy:5.2.0

# Deploy on cloud platform
# (Use platform-specific deployment tools)
```

---

## 🌐 Accessing Services

After deployment, access these URLs:

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/api/v1/docs | - |
| **Grafana** | http://localhost:3000 | admin / (see .env) |
| **Prometheus** | http://localhost:9090 | - |
| **PostgreSQL** | localhost:5432 | devskyy / (see .env) |
| **Redis** | localhost:6379 | - |

---

## 🔒 Security Best Practices

### Pre-Deployment Checklist

- [ ] Change default passwords in `.env`
- [ ] Generate strong `SECRET_KEY` (32+ characters)
- [ ] Use strong database password
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure SSL certificates for Nginx
- [ ] Set up firewall rules
- [ ] Enable automatic security updates

### Generate Secure Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate DATABASE_PASSWORD
openssl rand -base64 32

# Generate JWT_SECRET
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📊 Resource Requirements

### Minimum Requirements

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 20 GB
- **Network**: 100 Mbps

### Recommended Production

- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk**: 50+ GB SSD
- **Network**: 1 Gbps

### Resource Limits (Configured)

```yaml
# API Container
CPU: 2 cores (limit), 1 core (reserved)
Memory: 4 GB (limit), 2 GB (reserved)

# PostgreSQL
CPU: 1 core (limit)
Memory: 1 GB (limit)

# Redis
CPU: 0.5 core (limit)
Memory: 512 MB (limit)
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check environment variables
docker-compose config

# Verify .env file
cat .env

# Remove and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec api python -c "from database import engine; print(engine.connect())"

# Verify DATABASE_URL format
# Should be: postgresql://user:password@postgres:5432/database
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R $USER:$USER ./logs ./data ./artifacts

# Create directories if missing
mkdir -p logs data artifacts

# Check Docker user
docker-compose exec api whoami  # Should show 'devskyy' not 'root'
```

### High Memory Usage

```bash
# Check memory usage
docker stats

# Reduce workers
# Edit docker-compose.yml: WORKERS=2

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart services
docker-compose restart
```

---

## 🔄 Updates & Maintenance

### Update to Latest Version

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build --no-cache

# Restart with zero downtime
docker-compose up -d --no-deps --build api
```

### Database Migrations

```bash
# Create migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api alembic upgrade head

# Rollback migration
docker-compose exec api alembic downgrade -1
```

### Backup Strategy

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U devskyy devskyy | gzip > "$BACKUP_DIR/database.sql.gz"

# Backup Redis
docker-compose exec redis redis-cli BGSAVE
docker cp devskyy-redis:/data/dump.rdb "$BACKUP_DIR/redis-dump.rdb"

# Backup files
tar -czf "$BACKUP_DIR/files.tar.gz" ./data ./uploads

echo "Backup completed: $BACKUP_DIR"
```

---

## 📈 Scaling

### Horizontal Scaling (Multiple Instances)

```bash
# Scale API containers
docker-compose up -d --scale api=3

# Add Nginx load balancer
docker-compose --profile with-nginx up -d
```

### Vertical Scaling (More Resources)

Edit `docker-compose.production.yml`:

```yaml
services:
  devskyy:
    deploy:
      resources:
        limits:
          cpus: '4.0'    # Increase from 2.0
          memory: 8G     # Increase from 4G
```

---

## 🆘 Support

### Documentation
- [Docker README](./DOCKER_README.md) - Detailed Docker documentation
- [Security Verification](./DOCKER_SECURITY_VERIFICATION.md) - Security audit
- [Cloud Deployment](./DOCKER_CLOUD_DEPLOYMENT.md) - Cloud platform guides

### Quick Help

```bash
# Check Docker version
docker --version
docker-compose --version

# View all running containers
docker ps -a

# Clean up unused resources
docker system prune -a

# View disk usage
docker system df
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Port already in use | Change port in docker-compose.yml |
| Out of disk space | Run `docker system prune -a` |
| Container crashes | Check logs: `docker-compose logs api` |
| Slow performance | Increase resources in compose file |
| Can't connect to DB | Verify DATABASE_URL in .env |

---

## ✅ Production Checklist

Before going live:

- [ ] All environment variables set
- [ ] Strong passwords configured
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backup strategy implemented
- [ ] Monitoring alerts set up
- [ ] Health checks passing
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated

---

**Status**: ✅ Production Ready
**Docker Version**: 20.10+
**Docker Compose Version**: 2.0+
**Last Updated**: 2025-11-19
**Version**: 5.2.0-enterprise

---

**Need help?** Check [GitHub Issues](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues) or [Discussions](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/discussions)
