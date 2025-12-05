# DevSkyy Enterprise - Docker Cloud Deployment Guide

## Docker Cloud Registry
**Registry**: `cloud://skyyrosellc/devskyy_linux-amd64`
**Platform**: Linux AMD64
**Version**: 5.1.0 Enterprise

---

## 🚀 Quick Start

### 1. Build and Push to Docker Cloud

```bash
# Set environment variables
export DOCKER_REGISTRY="cloud://skyyrosellc"
export DOCKER_USERNAME="skyyrosellc"
export DOCKER_PASSWORD="your-password"
export VERSION="5.1.0"

# Build and push
chmod +x scripts/build-and-push.sh
./scripts/build-and-push.sh
```

### 2. Pull and Run

```bash
# Pull from Docker Cloud
docker pull cloud://skyyrosellc/devskyy_linux-amd64:5.1.0

# Run container
docker run -d \
  --name devskyy-production \
  -p 8000:8000 \
  -e JWT_SECRET_KEY="your-secret-key" \
  -e ENCRYPTION_MASTER_KEY="your-encryption-key" \
  -e ANTHROPIC_API_KEY="sk-ant-your-key" \
  cloud://skyyrosellc/devskyy_linux-amd64:5.1.0

# Check health
curl http://localhost:8000/api/v1/monitoring/health
```

---

## 📦 Available Images

| Tag | Description | Size | Use Case |
|-----|-------------|------|----------|
| `latest` | Latest stable | ~500MB | Production |
| `5.1.0` | Current version | ~500MB | Production |
| `5.1.0-amd64` | AMD64 specific | ~500MB | x86_64 servers |
| `main-abc123` | Git commit | ~500MB | Testing |
| `develop` | Development | ~500MB | Staging |

---

## 🔧 Build Configuration

### Dockerfile.production

**Multi-stage build** for optimized size:
- **Stage 1 (Builder)**: Compile dependencies
- **Stage 2 (Runtime)**: Production-ready image

**Optimizations**:
- Non-root user (devskyy:devskyy)
- Minimal base image (python:3.11-slim)
- No unnecessary packages
- Health checks built-in
- Security scanning passed

### Build Arguments

```dockerfile
ARG VERSION=5.1.0
ARG BUILD_DATE
ARG GIT_COMMIT
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

**File**: `.github/workflows/docker-cloud-deploy.yml`

**Triggers**:
- Push to `main` → Production deployment
- Push to `develop` → Staging deployment
- Pull request → Build and test only
- Manual dispatch → Custom environment

**Pipeline Stages**:

```
┌─────────┐     ┌──────────┐     ┌───────┐     ┌─────────┐
│  Test   │────▶│ Security │────▶│ Build │────▶│ Deploy  │
└─────────┘     └──────────┘     └───────┘     └─────────┘
    ↓                ↓                ↓              ↓
90% coverage   0 vulns        Docker Cloud    Kubernetes
```

**Jobs**:

1. **Test** (3 min)
   - Run pytest suite
   - Generate coverage report
   - Upload to Codecov

2. **Security** (2 min)
   - pip-audit scan
   - safety check
   - CodeQL analysis

3. **Build** (5 min)
   - Multi-platform build
   - Push to Docker Cloud
   - Tag with version + SHA

4. **Deploy Staging** (3 min)
   - Deploy to staging cluster
   - Run health checks
   - Smoke tests

5. **Deploy Production** (5 min)
   - Blue-green deployment
   - Zero-downtime switch
   - Verification tests

**Total Pipeline Time**: ~15 minutes

---

## ☸️ Kubernetes Deployment

### Production Setup

**File**: `kubernetes/production/deployment.yaml`

**Architecture**: Blue-Green Deployment

```
┌──────────────────────────────────────┐
│     Load Balancer (api.devskyy.com)  │
└────────────────┬─────────────────────┘
                 │
        ┌────────▼────────┐
        │  Ingress (nginx) │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │   Service        │
        │ (selector: blue) │◄───── Switch
        └─────────┬────────┘
                  │
    ┌─────────────┴──────────────┐
    │                            │
┌───▼────┐                  ┌────▼────┐
│  Blue  │                  │  Green  │
│  (3)   │                  │   (3)   │
└────────┘                  └─────────┘
```

**Components**:
- **Namespace**: production
- **Blue Deployment**: 3 replicas (active)
- **Green Deployment**: 3 replicas (standby)
- **Service**: LoadBalancer with selector
- **HPA**: Auto-scale 3-10 pods based on CPU/memory
- **Ingress**: HTTPS with Let's Encrypt
- **PVC**: 10GB persistent storage

### Deployment Commands

```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/production/

# Check deployment status
kubectl get pods -n production
kubectl get deployments -n production
kubectl get services -n production

# View logs
kubectl logs -f deployment/devskyy-blue -n production

# Switch from blue to green (zero-downtime)
kubectl patch service devskyy-service \
  -n production \
  -p '{"spec":{"selector":{"version":"green"}}}'

# Rollback if needed
kubectl rollout undo deployment/devskyy-blue -n production
```

---

## 🔐 Secrets Management

### Create Docker Cloud Credentials

```bash
# For Kubernetes
kubectl create secret docker-registry docker-cloud-credentials \
  --docker-server=cloud://skyyrosellc \
  --docker-username=skyyrosellc \
  --docker-password=$DOCKER_PASSWORD \
  --namespace=production

# For GitHub Actions
gh secret set DOCKER_USERNAME --body "skyyrosellc"
gh secret set DOCKER_PASSWORD --body "$DOCKER_PASSWORD"
```

### Create Application Secrets

```bash
# Generate secure keys
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create Kubernetes secret
kubectl create secret generic devskyy-secrets \
  --from-literal=JWT_SECRET_KEY=$JWT_SECRET \
  --from-literal=ENCRYPTION_MASTER_KEY=$ENCRYPTION_KEY \
  --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  --namespace=production
```

---

## 📊 Monitoring & Health Checks

### Built-in Health Check

**Endpoint**: `/api/v1/monitoring/health`

**Docker Healthcheck**:
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/monitoring/health || exit 1
```

**Kubernetes Probes**:
```yaml
livenessProbe:
  httpGet:
    path: /api/v1/monitoring/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /api/v1/monitoring/health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

### Monitoring Stack

```bash
# Deploy Prometheus + Grafana
kubectl apply -f kubernetes/monitoring/

# Access Grafana dashboard
kubectl port-forward svc/grafana 3000:80 -n monitoring
# Open http://localhost:3000

# View metrics endpoint
curl http://localhost:8000/metrics
```

---

## 🔄 Deployment Strategies

### 1. Rolling Update (Default)
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### 2. Blue-Green Deployment
```bash
# Deploy to green
kubectl set image deployment/devskyy-green \
  devskyy=cloud://skyyrosellc/devskyy_linux-amd64:5.1.1

# Wait and verify
kubectl rollout status deployment/devskyy-green -n production
curl https://green.devskyy.com/api/v1/monitoring/health

# Switch traffic
kubectl patch service devskyy-service \
  -n production \
  -p '{"spec":{"selector":{"version":"green"}}}'
```

### 3. Canary Deployment
```yaml
# Deploy canary (10% traffic)
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: devskyy-canary
spec:
  hosts:
    - api.devskyy.com
  http:
    - match:
        - headers:
            canary:
              exact: "true"
      route:
        - destination:
            host: devskyy-green
          weight: 10
        - destination:
            host: devskyy-blue
          weight: 90
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Image Pull Error
```bash
# Error: Failed to pull image
# Solution: Check Docker Cloud credentials

kubectl get pods -n production
kubectl describe pod <pod-name> -n production

# Recreate secret
kubectl delete secret docker-cloud-credentials -n production
kubectl create secret docker-registry docker-cloud-credentials \
  --docker-server=cloud://skyyrosellc \
  --docker-username=skyyrosellc \
  --docker-password=$DOCKER_PASSWORD \
  --namespace=production
```

#### 2. Health Check Failing
```bash
# Check pod logs
kubectl logs -f deployment/devskyy-blue -n production

# Check environment variables
kubectl exec -it deployment/devskyy-blue -n production -- env | grep -E 'JWT|ANTHROPIC'

# Test health endpoint directly
kubectl port-forward deployment/devskyy-blue 8000:8000 -n production
curl http://localhost:8000/api/v1/monitoring/health
```

#### 3. Database Connection Error
```bash
# Check database service
kubectl get svc postgres-service -n production

# Test connection
kubectl exec -it deployment/devskyy-blue -n production -- \
  python -c "import asyncpg; print('DB connection OK')"
```

---

## 📈 Performance Optimization

### Resource Allocation

**Requests** (guaranteed):
- CPU: 1 core (1000m)
- Memory: 2GB

**Limits** (maximum):
- CPU: 2 cores (2000m)
- Memory: 4GB

### Auto-scaling Configuration

```yaml
minReplicas: 3
maxReplicas: 10
targetCPUUtilization: 70%
targetMemoryUtilization: 80%
```

**Scaling Triggers**:
- CPU > 70% → Scale up
- CPU < 30% → Scale down
- Memory > 80% → Scale up

### Load Testing

```bash
# Install k6
brew install k6

# Run load test
k6 run load-tests/api-test.js \
  --vus 100 \
  --duration 5m \
  --out cloud

# Expected results:
# - Avg response time: < 100ms
# - 99th percentile: < 500ms
# - Success rate: > 99.9%
```

---

## 📚 Quick Reference Commands

### Build & Push
```bash
# Local build
docker build -f Dockerfile.production -t devskyy:local .

# Push to Docker Cloud
./scripts/build-and-push.sh

# Manual push
docker tag devskyy:local cloud://skyyrosellc/devskyy_linux-amd64:5.1.0
docker push cloud://skyyrosellc/devskyy_linux-amd64:5.1.0
```

### Kubernetes Operations
```bash
# Deploy
kubectl apply -f kubernetes/production/

# Status
kubectl get all -n production

# Logs
kubectl logs -f -l app=devskyy -n production

# Scale
kubectl scale deployment/devskyy-blue --replicas=5 -n production

# Update image
kubectl set image deployment/devskyy-blue \
  devskyy=cloud://skyyrosellc/devskyy_linux-amd64:5.1.1 \
  -n production

# Rollback
kubectl rollout undo deployment/devskyy-blue -n production
```

### Debugging
```bash
# Get shell access
kubectl exec -it deployment/devskyy-blue -n production -- /bin/bash

# Check configuration
kubectl get configmap devskyy-config -n production -o yaml

# View events
kubectl get events -n production --sort-by='.lastTimestamp'

# Network debug
kubectl run -it --rm debug --image=nicolaka/netshoot -n production
```

---

## 🎯 Production Checklist

Before deploying to production:

- [ ] Set all secrets in Kubernetes
- [ ] Configure Docker Cloud credentials
- [ ] Update DNS records for api.devskyy.com
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Configure monitoring and alerts
- [ ] Set up log aggregation
- [ ] Run load tests
- [ ] Test blue-green switching
- [ ] Verify health checks
- [ ] Test rollback procedure
- [ ] Document runbook
- [ ] Set up on-call rotation

---

## 🔗 Related Documentation

- **Main README**: `README.md`
- **Production Deployment**: `PRODUCTION_DEPLOYMENT.md`
- **A+ Upgrade Plan**: `A_PLUS_UPGRADE_PLAN.md`
- **Claude Code Guide**: `CLAUDE.md`
- **Enterprise Guide**: `ENTERPRISE_UPGRADE_COMPLETE.md`

---

## 📞 Support

**Docker Cloud Issues**: enterprise@devskyy.com
**Kubernetes Support**: devops@devskyy.com
**Emergency**: on-call@devskyy.com

---

**Status**: ✅ Production-ready Docker Cloud deployment
**Registry**: cloud://skyyrosellc/devskyy_linux-amd64
**Version**: 5.1.0 Enterprise
**Last Updated**: October 15, 2025
