---
name: docker
description: Generate Dockerfile and docker-compose configuration
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
argument-hint: "[--compose] [--production]"
---

# Docker Command

Generate optimized Docker configuration for your project.

## Execution Steps

1. **Detect application type**
   - Check package.json for Node.js/frontend
   - Check requirements.txt for Python
   - Check go.mod for Go
   - Identify framework (Next.js, React, Vue, etc.)

2. **Generate Dockerfile**
   - Create multi-stage build
   - Optimize for small image size
   - Add non-root user
   - Include health check
   - Create .dockerignore

3. **Generate docker-compose** (if `--compose`)
   - Application service
   - Database service (if detected)
   - Redis service (if detected)
   - Volume mounts for development

4. **Production optimizations** (if `--production`)
   - Smaller base images
   - No dev dependencies
   - Production environment variables
   - Security hardening

## Arguments

- `--compose`: Also generate docker-compose.yml
- `--production`: Optimize for production deployment

## Example Usage

```
/docker                      # Generate Dockerfile only
/docker --compose            # Include docker-compose
/docker --production         # Production-optimized
/docker --compose --production  # Both
```

## Output Files

- `Dockerfile`
- `.dockerignore`
- `docker-compose.yml` (if --compose)
- `docker-compose.prod.yml` (if --production)

## Build Commands

After generation:
```bash
# Build image
docker build -t my-app .

# Run with compose
docker-compose up -d

# Production build
docker build -f Dockerfile -t my-app:prod .
```
