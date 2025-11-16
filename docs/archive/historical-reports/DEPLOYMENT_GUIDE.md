# DevSkyy Deployment Guide

**Complete guide for deploying DevSkyy to production using Docker**

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Configuration](#configuration)
3. [Quick Start](#quick-start)
4. [Deployment Options](#deployment-options)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Python 3.11+ (for verification)

---

## Configuration

All credentials are configured in `.env` (already set up):

```bash
REGISTRY=docker.io
IMAGE_NAME=docker.io/skyyrosellc/devskyy
REGISTRY_USERNAME=skyyrosellc
DEPLOY_MODE=docker
```

---

## Quick Start

### 1. Complete Deployment

```bash
./scripts/deploy.sh
```

This runs the full pipeline:
- ✅ Deployment verification (100% required)
- 🔨 Docker build
- 🧪 Local testing
- 📤 Push to registry
- 🚀 Deploy

### 2. Individual Steps

```bash
# Build only
./scripts/docker-build.sh

# Test locally
./scripts/docker-run.sh

# Push to registry
./scripts/docker-push.sh
```

---

## Deployment Options

### Option 1: Automated (Recommended)

Push to GitHub main branch triggers automatic deployment:

```bash
git push origin main
```

GitHub Actions will:
- Run tests
- Build Docker image
- Security scan
- Push to registry

### Option 2: Manual Deployment

```bash
# Pull and run
docker pull docker.io/skyyrosellc/devskyy:latest
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  docker.io/skyyrosellc/devskyy:latest
```

---

## Monitoring

### Health Checks

```bash
# Container health
docker ps -f name=devskyy

# API health
curl http://localhost:8000/health

# Monitoring endpoint
curl http://localhost:8000/api/v1/monitoring/health
```

### Logs

```bash
# Follow logs
docker logs -f devskyy-prod

# Search errors
docker logs devskyy-prod 2>&1 | grep ERROR
```

---

## Troubleshooting

### Build Fails

```bash
# Clean cache
docker system prune -a

# Rebuild
./scripts/docker-build.sh
```

### Container Won't Start

```bash
# Check logs
docker logs devskyy-prod

# Verify env vars
docker run --env-file .env docker.io/skyyrosellc/devskyy:latest env
```

### Health Check Fails

```bash
# Test endpoint
curl -v http://localhost:8000/health

# Check health status
docker inspect --format='{{.State.Health.Status}}' devskyy-prod
```

---

## Quick Reference

### Commands

```bash
Deploy:  ./scripts/deploy.sh
Build:   ./scripts/docker-build.sh
Run:     ./scripts/docker-run.sh
Push:    ./scripts/docker-push.sh
```

### URLs

```
Docs:    http://localhost:8000/docs
Health:  http://localhost:8000/health
```

---

🤖 Generated with Claude Code
