# Docker Environment

Containerized deployment configuration for the DevSkyy Enterprise Platform.

## 🐳 Overview

This directory contains Docker-specific configurations for deploying DevSkyy in containerized environments. The setup is optimized for production deployment with security, performance, and scalability in mind.

## 📁 Files

- **`requirements.txt`** - Docker-specific Python dependencies
- **`Dockerfile`** - Multi-stage Docker build configuration
- **`docker-compose.yml`** - Complete stack deployment
- **`.env.example`** - Environment variables template
- **`nginx.conf`** - Reverse proxy configuration
- **`prometheus.yml`** - Monitoring configuration

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp docker/.env.example docker/.env

# Edit with your configuration
nano docker/.env
```

### 2. Build and Deploy
```bash
# Build the application
docker-compose -f docker/docker-compose.yml build

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Check service status
docker-compose -f docker/docker-compose.yml ps
```

### 3. Verify Deployment
```bash
# Check application health
curl http://localhost/health

# View logs
docker-compose -f docker/docker-compose.yml logs -f devskyy-app
```

## 🏗️ Architecture

### Services
- **devskyy-app** - Main FastAPI application
- **postgres** - PostgreSQL database
- **redis** - Caching and session storage
- **nginx** - Reverse proxy and load balancer
- **prometheus** - Metrics collection
- **grafana** - Monitoring dashboard

### Network
- **devskyy-network** - Isolated bridge network
- **Internal communication** - Services communicate via service names
- **External access** - Only nginx exposes ports 80/443

### Volumes
- **postgres_data** - Database persistence
- **redis_data** - Cache persistence
- **app_logs** - Application logs
- **app_data** - Application data storage

## 🔒 Security Features

### Container Security
- **Non-root user** - Application runs as `devskyy` user
- **Minimal base image** - Python slim image reduces attack surface
- **Multi-stage build** - Separates build and runtime environments
- **Health checks** - Automatic container health monitoring

### Network Security
- **Isolated network** - Services communicate on private network
- **Reverse proxy** - Nginx handles external traffic
- **SSL termination** - HTTPS encryption at proxy level
- **Rate limiting** - Built-in request rate limiting

### Data Security
- **Encrypted storage** - Database encryption at rest
- **Secure secrets** - Environment-based secret management
- **Backup encryption** - Automated encrypted backups
- **Audit logging** - Comprehensive operation logging

## 📊 Monitoring

### Health Checks
```bash
# Application health
curl http://localhost/health

# Database health
docker exec devskyy-postgres pg_isready -U devskyy

# Redis health
docker exec devskyy-redis redis-cli ping
```

### Metrics
- **Prometheus** - Available at http://localhost:9090
- **Grafana** - Available at http://localhost:3000 (admin/admin)
- **Application metrics** - Custom business metrics
- **Infrastructure metrics** - System resource monitoring

### Logs
```bash
# View all logs
docker-compose -f docker/docker-compose.yml logs

# Follow specific service
docker-compose -f docker/docker-compose.yml logs -f devskyy-app

# View last 100 lines
docker-compose -f docker/docker-compose.yml logs --tail=100
```

## 🔧 Configuration

### Environment Variables
Key configuration options in `.env`:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://devskyy:password@postgres:5432/devskyy

# Redis
REDIS_URL=redis://redis:6379/0

# AI Services
OPENAI_API_KEY=sk-your-key
```

### Scaling
```bash
# Scale application instances
docker-compose -f docker/docker-compose.yml up -d --scale devskyy-app=3

# Scale with load balancer
docker-compose -f docker/docker-compose.yml up -d --scale devskyy-app=3 --scale nginx=1
```

## 🚀 Deployment

### Development
```bash
# Start with development overrides
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d
```

### Production
```bash
# Production deployment
docker-compose -f docker/docker-compose.yml up -d

# With SSL certificates
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

### Cloud Deployment
```bash
# Deploy to Docker Swarm
docker stack deploy -c docker/docker-compose.yml devskyy

# Deploy to Kubernetes
kubectl apply -f docker/k8s/
```

## 🔄 Maintenance

### Updates
```bash
# Pull latest images
docker-compose -f docker/docker-compose.yml pull

# Rebuild and restart
docker-compose -f docker/docker-compose.yml up -d --build
```

### Backups
```bash
# Database backup
docker exec devskyy-postgres pg_dump -U devskyy devskyy > backup.sql

# Volume backup
docker run --rm -v devskyy_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### Cleanup
```bash
# Stop all services
docker-compose -f docker/docker-compose.yml down

# Remove volumes (WARNING: Data loss)
docker-compose -f docker/docker-compose.yml down -v

# Clean up unused resources
docker system prune -a
```

## 🐛 Troubleshooting

### Common Issues
1. **Port conflicts** - Check if ports 80, 443, 5432, 6379 are available
2. **Permission errors** - Ensure Docker daemon is running and user has permissions
3. **Memory issues** - Increase Docker memory allocation
4. **Network issues** - Check firewall and network configuration

### Debug Commands
```bash
# Check container status
docker-compose -f docker/docker-compose.yml ps

# Inspect container
docker inspect devskyy-app

# Execute commands in container
docker exec -it devskyy-app bash

# Check network connectivity
docker exec devskyy-app ping postgres
```

---

For more information, see the main [deployment documentation](../docs/deployment/README.md).
