# Docker Setup and Configuration Guide

Complete guide for Docker setup, configuration, and best practices for the DevSkyy platform.

## Table of Contents

- [Installation](#installation)
- [Docker Configuration](#docker-configuration)
- [Building Images](#building-images)
- [Running Containers](#running-containers)
- [Docker Compose](#docker-compose)
- [Security Hardening](#security-hardening)
- [Troubleshooting](#troubleshooting)

## Installation

### Linux (Ubuntu/Debian)

```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verify installation
sudo docker run hello-world
```

### macOS

```bash
# Install Docker Desktop via Homebrew
brew install --cask docker

# Or download from https://www.docker.com/products/docker-desktop

# Start Docker Desktop
open -a Docker

# Verify installation
docker run hello-world
```

### Windows

1. Download Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop)
2. Run installer and follow setup wizard
3. Restart computer when prompted
4. Open Docker Desktop
5. Verify installation:
   ```powershell
   docker run hello-world
   ```

## Docker Configuration

### Post-Installation Steps (Linux)

#### Add User to Docker Group

**SECURE METHOD (Recommended):**

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and log back in for changes to take effect
# Or use newgrp to activate group without logout
newgrp docker

# Verify you can run docker without sudo
docker run hello-world
```

**Verify Permissions:**

```bash
# Check docker socket permissions (should be 660)
ls -l /var/run/docker.sock
# Output should show: srw-rw---- 1 root docker ... /var/run/docker.sock

# Check your group membership
groups
# Should include 'docker' group
```

#### INSECURE METHOD (NOT RECOMMENDED)

**WARNING: The following method is insecure and should NEVER be used:**

```bash
# ❌ DANGEROUS: DO NOT USE THIS METHOD
# Setting socket to 666 makes it world-writable and gives any local user root-equivalent access
# sudo chmod 666 /var/run/docker.sock

# ✅ SECURE ALTERNATIVE: Add user to docker group instead (see above)
sudo usermod -aG docker $USER
```

**Security Risk Explanation:**
- Setting `/var/run/docker.sock` to mode `666` makes it world-writable
- Any local user can access the Docker daemon
- This grants **root-equivalent access** to the entire system
- Attackers can escape containers and compromise the host

**Proper Solution:**
1. Keep socket owned by `root:docker` with `660` permissions
2. Add trusted users to the `docker` group
3. Use rootless Docker for additional security (see below)

### Docker Daemon Configuration

Create or edit `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65536,
      "Soft": 65536
    }
  },
  "storage-driver": "overlay2",
  "userland-proxy": false,
  "live-restore": true,
  "default-address-pools": [
    {
      "base": "172.17.0.0/16",
      "size": 24
    }
  ]
}
```

Restart Docker daemon:

```bash
sudo systemctl restart docker
```

### Rootless Docker (Most Secure)

For maximum security, run Docker in rootless mode:

```bash
# Install rootless Docker
curl -fsSL https://get.docker.com/rootless | sh

# Set environment variables
export PATH=/home/$USER/bin:$PATH
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock

# Add to ~/.bashrc or ~/.zshrc
echo 'export PATH=/home/$USER/bin:$PATH' >> ~/.bashrc
echo 'export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock' >> ~/.bashrc

# Enable systemd service
systemctl --user enable docker
systemctl --user start docker

# Verify
docker run hello-world
```

## Building Images

### Build Production Image

```bash
# Build with production Dockerfile
docker build -t devskyy:production -f Dockerfile.production .

# Build with build arguments
docker build \
  --build-arg BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') \
  --build-arg VCS_REF=$(git rev-parse --short HEAD) \
  --build-arg VERSION=1.0.0 \
  -t devskyy:production \
  -f Dockerfile.production \
  .

# Build with BuildKit (faster, more features)
DOCKER_BUILDKIT=1 docker build -t devskyy:production -f Dockerfile.production .
```

### Multi-Platform Builds

```bash
# Set up buildx
docker buildx create --name multiplatform --use
docker buildx inspect --bootstrap

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t devskyy:production \
  -f Dockerfile.production \
  --push \
  .
```

### Build Arguments

Common build arguments for DevSkyy:

| Argument | Description | Default |
|----------|-------------|---------|
| `BUILD_DATE` | Build timestamp | Current time |
| `VCS_REF` | Git commit SHA | Current commit |
| `VERSION` | Application version | latest |
| `PYTHON_VERSION` | Python base image version | 3.11-slim |

## Running Containers

### Basic Run

```bash
# Run production container
docker run -d \
  --name devskyy \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@postgres:5432/devskyy" \
  -e REDIS_URL="redis://redis:6379/0" \
  -e SECRET_KEY="your-secret-key" \
  devskyy:production

# View logs
docker logs -f devskyy

# Stop container
docker stop devskyy

# Remove container
docker rm devskyy
```

### Resource Limits

```bash
# Run with resource limits
docker run -d \
  --name devskyy \
  --cpus="2" \
  --memory="4g" \
  --memory-swap="4g" \
  --restart=unless-stopped \
  -p 8000:8000 \
  devskyy:production
```

### Security Options

```bash
# Run with security hardening
docker run -d \
  --name devskyy \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=100m \
  -p 8000:8000 \
  devskyy:production
```

## Docker Compose

### Development Environment

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/devskyy
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=development
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/app
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: devskyy
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Start Services

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v

# Rebuild and restart
docker compose up -d --build
```

### Production Environment

```yaml
# docker-compose.production.yml
version: '3.8'

services:
  app:
    image: devskyy:production
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_MASTER_KEY=${ENCRYPTION_MASTER_KEY}
      - ENVIRONMENT=production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G
      restart_policy:
        condition: on-failure
        max_attempts: 3
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G

volumes:
  postgres_data:
  redis_data:
```

## Security Hardening

### Image Scanning

```bash
# Scan with Trivy
trivy image --severity HIGH,CRITICAL devskyy:production

# Scan with Docker Scan
docker scan devskyy:production

# Scan with Grype
grype devskyy:production
```

### Security Best Practices

1. **Use Official Base Images**
   ```dockerfile
   FROM python:3.11-slim  # Official, maintained image
   ```

2. **Run as Non-Root User**
   ```dockerfile
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

3. **Multi-Stage Builds**
   ```dockerfile
   FROM python:3.11-slim AS builder
   # Build dependencies

   FROM python:3.11-slim
   COPY --from=builder /app /app
   ```

4. **Minimize Layers**
   ```dockerfile
   RUN apt-get update && apt-get install -y \
       package1 \
       package2 \
       && rm -rf /var/lib/apt/lists/*
   ```

5. **Use .dockerignore**
   ```
   .git
   .env
   __pycache__
   *.pyc
   .venv
   node_modules
   ```

### Secret Management

**❌ DON'T:**
```bash
# Don't pass secrets via build args
docker build --build-arg SECRET_KEY=mysecret .

# Don't commit secrets to images
COPY .env /app/.env
```

**✅ DO:**
```bash
# Use environment variables at runtime
docker run -e SECRET_KEY=$SECRET_KEY devskyy:production

# Use Docker secrets (Swarm mode)
echo "mysecret" | docker secret create db_password -
docker service create --secret db_password devskyy:production

# Use secret management tools
docker run --env-file <(vault kv get -format=dotenv secret/devskyy) devskyy:production
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs devskyy

# Inspect container
docker inspect devskyy

# Check exit code
docker inspect devskyy --format='{{.State.ExitCode}}'

# Run interactively for debugging
docker run -it --rm --entrypoint /bin/bash devskyy:production
```

### Permission Issues

```bash
# Check socket permissions
ls -l /var/run/docker.sock

# Verify group membership
groups

# If needed, refresh group membership
newgrp docker

# NEVER use chmod 666 on docker.sock (security risk!)
# Instead, ensure proper group membership
```

### Build Failures

```bash
# Build with verbose output
docker build --progress=plain -t devskyy:production -f Dockerfile.production .

# Clear build cache
docker builder prune -a

# Build with no cache
docker build --no-cache -t devskyy:production -f Dockerfile.production .
```

### Network Issues

```bash
# List networks
docker network ls

# Inspect network
docker network inspect bridge

# Create custom network
docker network create devskyy-network

# Run container on custom network
docker run -d --network devskyy-network --name devskyy devskyy:production
```

### Clean Up

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune

# Remove everything
docker system prune -a --volumes
```

## Performance Optimization

### BuildKit

Enable BuildKit for faster builds:

```bash
export DOCKER_BUILDKIT=1
docker build -t devskyy:production -f Dockerfile.production .
```

### Layer Caching

Optimize Dockerfile for better caching:

```dockerfile
# Copy requirements first (changes less frequently)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code last (changes frequently)
COPY . .
```

### Build Cache

```bash
# Save build cache
docker buildx build \
  --cache-to type=local,dest=/tmp/buildcache \
  -t devskyy:production \
  .

# Load build cache
docker buildx build \
  --cache-from type=local,src=/tmp/buildcache \
  -t devskyy:production \
  .
```

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Rootless Docker](https://docs.docker.com/engine/security/rootless/)
