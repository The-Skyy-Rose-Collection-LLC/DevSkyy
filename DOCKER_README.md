# DevSkyy Enterprise Platform - Docker Image

[![Docker Pulls](https://img.shields.io/docker/pulls/skyyrosellc/devskyy)](https://hub.docker.com/r/skyyrosellc/devskyy)
[![Docker Image Size](https://img.shields.io/docker/image-size/skyyrosellc/devskyy/latest)](https://hub.docker.com/r/skyyrosellc/devskyy)
[![Docker Image Version](https://img.shields.io/docker/v/skyyrosellc/devskyy?sort=semver)](https://hub.docker.com/r/skyyrosellc/devskyy)

## 🚀 **Enterprise Fashion E-commerce Automation Platform**

DevSkyy is a comprehensive enterprise platform that combines AI-powered fashion intelligence, automated e-commerce management, and advanced agent orchestration to revolutionize fashion retail operations.

---

## 🏗️ **Quick Start**

### **Basic Usage**
```bash
# Pull and run the latest version
docker pull skyyrosellc/devskyy:latest
docker run -p 8000:8000 skyyrosellc/devskyy:latest
```

### **Production Deployment**
```bash
# Run with environment variables
docker run -d \
  --name devskyy-production \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=your-database-url \
  -e REDIS_URL=your-redis-url \
  --restart unless-stopped \
  skyyrosellc/devskyy:latest
```

### **Development Mode**
```bash
# Run development version with hot reload
docker run -d \
  --name devskyy-dev \
  -p 8000:8000 \
  -v $(pwd):/app \
  -e ENVIRONMENT=development \
  skyyrosellc/devskyy:development
```

---

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ENVIRONMENT` | Application environment | `production` | No |
| `PORT` | Server port | `8000` | No |
| `HOST` | Server host | `0.0.0.0` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |
| `SECRET_KEY` | Application secret key | - | Yes |
| `DATABASE_URL` | Database connection URL | - | Yes |
| `REDIS_URL` | Redis connection URL | - | No |
| `ANTHROPIC_API_KEY` | Anthropic AI API key | - | No |
| `OPENAI_API_KEY` | OpenAI API key | - | No |

### **Volume Mounts**

| Path | Description | Purpose |
|------|-------------|---------|
| `/app/logs` | Application logs | Persistent logging |
| `/app/uploads` | File uploads | User-generated content |
| `/app/tmp` | Temporary files | Cache and processing |

---

## 🏷️ **Available Tags**

| Tag | Description | Use Case |
|-----|-------------|----------|
| `latest` | Latest stable release | Production deployment |
| `development` | Development build with tools | Local development |
| `{version}` | Specific version (e.g., `5.2.0`) | Version pinning |
| `{branch}-{sha}` | Branch-specific builds | Testing specific commits |

---

## 🚀 **Features**

### **🤖 AI-Powered Agent System**
- **Multi-Agent Orchestration**: Coordinate multiple AI agents for complex tasks
- **Self-Healing Architecture**: Automatic recovery and optimization
- **Real-Time Monitoring**: Comprehensive health checks and metrics

### **👗 Fashion Intelligence**
- **Computer Vision**: Advanced image analysis and product recognition
- **Trend Analysis**: AI-powered fashion trend prediction
- **Style Recommendations**: Personalized fashion recommendations

### **🛒 E-commerce Automation**
- **Product Management**: Automated product creation and optimization
- **Inventory Tracking**: Real-time inventory management
- **Price Optimization**: Dynamic pricing strategies

### **🔒 Enterprise Security**
- **Multi-Layer Authentication**: JWT, OAuth, and API key support
- **Input Validation**: Comprehensive security scanning
- **Audit Logging**: Complete activity tracking

---

## 🐳 **Docker Compose Example**

```yaml
version: '3.8'

services:
  devskyy:
    image: skyyrosellc/devskyy:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/devskyy
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=devskyy
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

## 🔍 **Health Checks**

The container includes built-in health checks:

```bash
# Check container health
docker ps --filter "name=devskyy"

# Manual health check
curl http://localhost:8000/health

# Detailed health status
curl http://localhost:8000/health/detailed
```

---

## 📊 **Monitoring**

### **Metrics Endpoints**
- `/health` - Basic health check
- `/health/detailed` - Comprehensive health status
- `/metrics` - Prometheus metrics
- `/api/agents/status` - Agent system status

### **Logging**
```bash
# View container logs
docker logs devskyy-production

# Follow logs in real-time
docker logs -f devskyy-production

# View specific log level
docker logs devskyy-production 2>&1 | grep ERROR
```

---

## 🛠️ **Development**

### **Building Locally**
```bash
# Clone repository
git clone https://github.com/SkyyRoseLLC/DevSkyy.git
cd DevSkyy

# Build production image
docker build -t devskyy:local .

# Build development image
docker build --target development -t devskyy:dev .
```

### **Running Tests**
```bash
# Run tests in container
docker run --rm devskyy:dev python -m pytest tests/

# Run with coverage
docker run --rm devskyy:dev python -m pytest tests/ --cov=.
```

---

## 🔐 **Security**

### **Security Features**
- Non-root user execution
- Minimal base image (Python slim)
- Regular security updates
- Vulnerability scanning

### **Security Scanning**
```bash
# Scan image for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image skyyrosellc/devskyy:latest
```

---

## 📞 **Support**

- **Documentation**: [GitHub Repository](https://github.com/SkyyRoseLLC/DevSkyy)
- **Issues**: [GitHub Issues](https://github.com/SkyyRoseLLC/DevSkyy/issues)
- **Discussions**: [GitHub Discussions](https://github.com/SkyyRoseLLC/DevSkyy/discussions)

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](https://github.com/SkyyRoseLLC/DevSkyy/blob/main/LICENSE) file for details.

---

**Maintained by [Skyy Rose LLC](https://skyyrose.com) 🌹**
