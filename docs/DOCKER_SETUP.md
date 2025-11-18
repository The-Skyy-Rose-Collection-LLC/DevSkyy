# Docker Setup Guide for DevSkyy

This guide provides Docker installation and configuration instructions for local development environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation by Platform](#installation-by-platform)
- [Post-Installation Setup](#post-installation-setup)
- [Verification](#verification)
- [DevSkyy Docker Usage](#devskyy-docker-usage)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **RAM**: Minimum 4GB, recommended 8GB+
- **Disk Space**: 20GB free space
- **CPU**: 64-bit processor with virtualization support

### Enable Virtualization
- **Windows**: Enable Hyper-V or WSL2
- **macOS**: Virtualization enabled by default
- **Linux**: Check kernel support: `grep -E 'vmx|svm' /proc/cpuinfo`

---

## Installation by Platform

### Ubuntu/Debian Linux

```bash
# Update package index
sudo apt-get update

# Install required packages
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Add Docker's official GPG key
sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
sudo docker --version
sudo docker run hello-world
```

### macOS

#### Option 1: Docker Desktop (Recommended)

```bash
# Download Docker.dmg from https://www.docker.com/products/docker-desktop

# Install via GUI or command line:
sudo hdiutil attach Docker.dmg
sudo /Volumes/Docker/Docker.app/Contents/MacOS/install
sudo hdiutil detach /Volumes/Docker

# Start Docker Desktop from Applications
```

#### Option 2: Homebrew

```bash
# Install Docker Desktop via Homebrew
brew install --cask docker

# Start Docker Desktop
open -a Docker

# Verify installation
docker --version
docker run hello-world
```

### Windows

#### Windows 10/11 Pro, Enterprise, or Education

```powershell
# Download Docker Desktop from https://www.docker.com/products/docker-desktop

# Install Docker Desktop (GUI installer)
# Or via Chocolatey:
choco install docker-desktop

# Enable WSL2 backend (recommended)
wsl --install
wsl --set-default-version 2

# Start Docker Desktop from Start Menu

# Verify in PowerShell
docker --version
docker run hello-world
```

#### Windows 10/11 Home

```powershell
# Install WSL2 first
wsl --install
wsl --set-default-version 2

# Download and install Docker Desktop with WSL2 backend
# From: https://www.docker.com/products/docker-desktop

# Verify
docker --version
```

### Fedora/RHEL/CentOS

```bash
# Install Docker Engine
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Verify
sudo docker --version
```

---

## Post-Installation Setup

### Add User to Docker Group (Linux/macOS)

```bash
# Add current user to docker group
sudo usermod -aG docker $USER

# Apply group changes (logout/login or use newgrp)
newgrp docker

# Verify non-root access
docker run hello-world
```

### Configure Docker Resources

**Docker Desktop** (macOS/Windows):
1. Open Docker Desktop
2. Go to **Settings → Resources**
3. Adjust:
   - **CPUs**: 4+ cores (for DevSkyy)
   - **Memory**: 8GB+ (recommended)
   - **Swap**: 2GB
   - **Disk**: 60GB+

**Linux** (systemd service):
```bash
# Edit daemon configuration
sudo nano /etc/docker/daemon.json
```

```json
{
  "default-address-pools": [
    {
      "base": "172.17.0.0/12",
      "size": 24
    }
  ],
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
```

```bash
# Restart Docker
sudo systemctl restart docker
```

---

## Verification

### Check Installation

```bash
# Docker version
docker --version
docker compose version

# Docker info
docker info

# Run test container
docker run hello-world

# Check Docker Compose
docker compose version
```

### Expected Output

```
Docker version 28.2.2, build 28.2.2
Docker Compose version v2.XX.X

Client: Docker Engine - Community
 Version:           28.2.2
 API version:       1.XX
 Go version:        go1.XX.X
 Git commit:        XXXXXXX
 Built:             Mon Nov XX XX:XX:XX 2025
 OS/Arch:           linux/amd64
 Context:           default
```

---

## DevSkyy Docker Usage

### Build DevSkyy Image

```bash
# Navigate to DevSkyy repository
cd ~/DevSkyy

# Build Docker image
docker build -t devskyy:latest .

# Or with BuildKit (faster)
DOCKER_BUILDKIT=1 docker build -t devskyy:latest .

# Verify image
docker images | grep devskyy
```

### Run DevSkyy Container

```bash
# Run in detached mode with environment variables
docker run -d \
  --name devskyy-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@localhost:5432/devskyy" \
  -e SECRET_KEY="your-secret-key-here" \
  -e ENVIRONMENT="development" \
  devskyy:latest

# View logs
docker logs -f devskyy-api

# Check container status
docker ps

# Stop container
docker stop devskyy-api

# Remove container
docker rm devskyy-api
```

### Docker Compose (Recommended)

Create `docker-compose.yml` in project root:

```yaml
version: '3.8'

services:
  api:
    build: .
    image: devskyy:latest
    container_name: devskyy-api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://devskyy:devskyy@postgres:5432/devskyy
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=development
    depends_on:
      - postgres
      - redis
    volumes:
      - ./:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:15-alpine
    container_name: devskyy-postgres
    environment:
      - POSTGRES_USER=devskyy
      - POSTGRES_PASSWORD=devskyy
      - POSTGRES_DB=devskyy
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: devskyy-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build
```

---

## Troubleshooting

### Common Issues

#### 1. "Cannot connect to Docker daemon"

**Linux:**
```bash
# Check if Docker is running
sudo systemctl status docker

# Start Docker
sudo systemctl start docker

# Check socket permissions
sudo chmod 666 /var/run/docker.sock
```

**macOS/Windows:**
- Ensure Docker Desktop is running
- Restart Docker Desktop

#### 2. "Permission denied" errors

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again, or:
newgrp docker
```

#### 3. Port already in use

```bash
# Find process using port 8000
sudo lsof -i :8000
# or
sudo netstat -tulpn | grep :8000

# Kill process or use different port
docker run -p 8001:8000 devskyy:latest
```

#### 4. Out of disk space

```bash
# Clean up Docker resources
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove stopped containers
docker container prune
```

#### 5. Build failures

```bash
# Clear build cache
docker builder prune -a

# Build without cache
docker build --no-cache -t devskyy:latest .

# Check Dockerfile syntax
docker build --check .
```

#### 6. Container exits immediately

```bash
# Check logs
docker logs devskyy-api

# Run interactively
docker run -it devskyy:latest /bin/bash

# Check container health
docker inspect devskyy-api
```

### Performance Issues

#### Linux: Enable BuildKit

```bash
# Add to ~/.bashrc or ~/.zshrc
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

#### macOS/Windows: Increase Resources

1. Docker Desktop → Settings → Resources
2. Increase CPU/Memory allocation
3. Enable VirtioFS (macOS) for faster file sharing

---

## Docker Best Practices for DevSkyy

### Security

```bash
# 1. Don't run as root
USER appuser

# 2. Use specific image tags
FROM python:3.11.9-slim

# 3. Scan images for vulnerabilities
docker scout cves devskyy:latest
# or
trivy image devskyy:latest
```

### Performance

```dockerfile
# Use multi-stage builds
FROM python:3.11.9-slim AS builder
# Build dependencies
FROM python:3.11.9-slim AS runtime
# Copy only what's needed
```

### Cleanup

```bash
# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove everything (use with caution)
docker system prune -a --volumes
```

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [DevSkyy Workflows](.github/workflows/README.md)
- [Truth Protocol](CLAUDE.md)

---

**Last Updated:** 2025-11-17

**Maintained by:** DevSkyy Team
