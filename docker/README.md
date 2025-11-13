# DevSkyy Docker Subproject

## Overview

This directory contains Docker-specific configurations and dependencies for the DevSkyy platform. The Docker setup is isolated to prevent dependency conflicts with other subprojects (ML, MCP, Vercel).

## Structure

```
docker/
├── requirements.txt          # Docker-specific Python dependencies
├── docker-entrypoint.sh     # Container entrypoint script
├── mcp_gateway.py           # MCP gateway service
└── README.md                # This file
```

## Dependencies

The `requirements.txt` file contains only essential dependencies for Docker container operations:

- **Core Framework**: FastAPI, Uvicorn, Pydantic
- **Database**: SQLAlchemy with async support (SQLite, PostgreSQL)
- **Security**: Authentication, encryption, JWT
- **Monitoring**: Prometheus, structured logging
- **Caching**: Redis support

**Excluded**: Heavy ML libraries (torch, tensorflow, transformers) - use dedicated ML container

## Dockerfiles

The repository provides multiple Dockerfile configurations:

### 1. `Dockerfile` (Root - Production)
- Multi-stage build for optimized production
- Uses `requirements.txt` from root (full dependencies)
- Best for: Complete platform deployment

### 2. `Dockerfile.mcp` 
- Specialized for MCP server deployment
- Uses `requirements_mcp.txt` and `requirements.txt`
- Best for: MCP gateway service

### 3. `Dockerfile.production`
- Lightweight production image
- Uses `requirements-production.txt` (excludes heavy ML)
- Best for: Cloud deployment without ML features

## Building Docker Images

### Development Build
```bash
docker build -t devskyy:dev -f Dockerfile .
```

### MCP Server Build
```bash
docker build -t devskyy-mcp:latest -f Dockerfile.mcp .
```

### Production Build
```bash
docker build -t devskyy:prod -f Dockerfile.production .
```

## Running Containers

### Development
```bash
docker run -p 8000:8000 \
  -e ENVIRONMENT=development \
  -v $(pwd):/app \
  devskyy:dev
```

### Production
```bash
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e WORKERS=4 \
  devskyy:prod
```

### MCP Server
```bash
docker run -p 8000:8000 -p 3000:3000 \
  -e DEVSKYY_ENV=production \
  devskyy-mcp:latest
```

## Docker Compose

For multi-container deployments, see:
- `docker-compose.yml` (development)
- `docker-compose.mcp.yml` (MCP server)
- `docker-compose.production.yml` (production)

## Environment Variables

Required environment variables:
- `ENVIRONMENT`: `development`, `production`, `staging`
- `PORT`: API server port (default: 8000)
- `WORKERS`: Number of worker processes
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string (optional)

## Health Checks

All Docker containers include health checks:
- HTTP endpoint: `/health`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3

## Security

Docker containers follow security best practices:
- ✅ Non-root user (`devskyy` or `appuser`)
- ✅ Minimal base images (`python:3.11-slim`)
- ✅ No secrets in images (use environment variables)
- ✅ Multi-stage builds to reduce attack surface
- ✅ Security updates applied to dependencies

## CI/CD Integration

Docker builds are automated via GitHub Actions:
- Workflow: `.github/workflows/docker.yml`
- Triggers: Push to main, pull requests
- Registries: Docker Hub, GitHub Container Registry

## Troubleshooting

### Build failures
```bash
# Clear Docker cache
docker builder prune -a

# Build with no cache
docker build --no-cache -t devskyy:dev .
```

### Runtime issues
```bash
# View container logs
docker logs <container-id>

# Interactive shell
docker exec -it <container-id> /bin/bash

# Health check
docker inspect --format='{{.State.Health.Status}}' <container-id>
```

## Best Practices

1. **Dependency Isolation**: Use `docker/requirements.txt` for Docker-specific deps
2. **Layer Caching**: Order COPY commands from least to most frequently changed
3. **Security Scanning**: Run `docker scan` before deployment
4. **Size Optimization**: Use multi-stage builds, minimize layers
5. **Environment Configs**: Never hardcode secrets, use environment variables

## Related Documentation

- [Main README](/README.md)
- [MCP Deployment](/DOCKER_MCP_DEPLOYMENT.md)
- [Production Deployment](/DOCKER_CLOUD_DEPLOYMENT.md)
- [Deployment Guide](/DEPLOYMENT_GUIDE.md)
