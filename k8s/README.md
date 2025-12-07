# DevSkyy Kubernetes Deployment

Production-ready Kubernetes manifests for the DevSkyy platform with multi-environment support using Kustomize.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Ingress (NGINX)                        │
│            TLS, Rate Limiting, Security Headers             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Service (ClusterIP/LoadBalancer)               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│         Deployment (3-20 replicas with HPA/VPA)             │
│  - Security Context (runAsNonRoot, seccompProfile)          │
│  - Health Checks (liveness, readiness, startup)             │
│  - Resource Limits (500m-2 CPU, 1-4Gi memory)               │
│  - Pod Anti-Affinity (high availability)                    │
└───┬──────────────────────────────────────────────┬──────────┘
    │                                              │
┌───▼──────────────────┐            ┌─────────────▼──────────┐
│  PostgreSQL          │            │      Redis             │
│  StatefulSet         │            │   StatefulSet          │
│  - 500Gi PVC         │            │   - 50Gi PVC           │
│  - Production Config │            │   - AOF Persistence    │
└──────────────────────┘            └────────────────────────┘
```

## Directory Structure

```
k8s/
├── base/                          # Base Kubernetes resources
│   ├── namespace.yaml             # Namespace with ResourceQuota
│   ├── secrets.yaml               # Secret templates (replace with sealed-secrets)
│   ├── configmap.yaml             # Application and Nginx configuration
│   ├── rbac.yaml                  # ServiceAccount, Role, NetworkPolicy
│   ├── pvc.yaml                   # Persistent Volume Claims
│   ├── deployment.yaml            # Main application deployment
│   ├── service.yaml               # ClusterIP, Headless, LoadBalancer services
│   ├── ingress.yaml               # NGINX Ingress with TLS
│   ├── hpa.yaml                   # Horizontal/Vertical Pod Autoscaler
│   ├── postgres.yaml              # PostgreSQL StatefulSet
│   ├── redis.yaml                 # Redis StatefulSet
│   └── kustomization.yaml         # Base Kustomize configuration
├── overlays/
│   ├── development/               # Development environment
│   │   └── kustomization.yaml     # 1 replica, lower resources, dev.devskyy.local
│   ├── staging/                   # Staging environment
│   │   └── kustomization.yaml     # 2 replicas, medium resources, staging.devskyy.com
│   └── production/                # Production environment
│       ├── kustomization.yaml     # 3 replicas, full resources, api.devskyy.com
│       └── pdb.yaml               # Pod Disruption Budgets
└── README.md                      # This file
```

## Prerequisites

1. **Kubernetes Cluster** (v1.24+)
   - kubectl configured with cluster access
   - Sufficient resources (see resource requirements below)

2. **Kustomize** (v5.0+)
   - Included in kubectl v1.14+
   - Or install standalone: `brew install kustomize`

3. **NGINX Ingress Controller**
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
   ```

4. **cert-manager** (for TLS certificates)
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

5. **Metrics Server** (for HPA)
   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   ```

6. **Storage Class** (fast-ssd)
   ```bash
   # Example for AWS EBS gp3
   kubectl apply -f - <<EOF
   apiVersion: storage.k8s.io/v1
   kind: StorageClass
   metadata:
     name: fast-ssd
   provisioner: ebs.csi.aws.com
   parameters:
     type: gp3
     iops: "3000"
     throughput: "125"
   volumeBindingMode: WaitForFirstConsumer
   allowVolumeExpansion: true
   EOF
   ```

## Resource Requirements

### Development Environment
- **CPU**: 4 cores (requests), 8 cores (limits)
- **Memory**: 8Gi (requests), 16Gi (limits)
- **Storage**: 35Gi (10Gi app + 20Gi postgres + 5Gi redis)
- **Replicas**: 1 application pod

### Staging Environment
- **CPU**: 10 cores (requests), 20 cores (limits)
- **Memory**: 20Gi (requests), 40Gi (limits)
- **Storage**: 170Gi (50Gi app + 100Gi postgres + 20Gi redis)
- **Replicas**: 2-10 application pods (HPA)

### Production Environment
- **CPU**: 20 cores (requests), 40 cores (limits)
- **Memory**: 40Gi (requests), 80Gi (limits)
- **Storage**: 650Gi (100Gi app + 500Gi postgres + 50Gi redis)
- **Replicas**: 3-20 application pods (HPA)

## Quick Start

### 1. Configure Secrets

**CRITICAL**: Replace all placeholder secrets before deployment!

```bash
# Option A: Using kubectl (not recommended for production)
kubectl create secret generic devskyy-secrets \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=JWT_SECRET_KEY='your-jwt-secret' \
  --from-literal=ENCRYPTION_MASTER_KEY='your-encryption-key' \
  --from-literal=DATABASE_URL='postgresql://user:pass@postgres:5432/devskyy' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --namespace=devskyy

# Option B: Using sealed-secrets (recommended)
# Install sealed-secrets controller first:
# kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Create sealed secret:
kubeseal --format=yaml < secrets.yaml > sealed-secrets.yaml
kubectl apply -f sealed-secrets.yaml
```

### 2. Deploy to Development

```bash
# Build and preview manifests
kubectl kustomize k8s/overlays/development

# Apply to cluster
kubectl apply -k k8s/overlays/development

# Verify deployment
kubectl get all -n devskyy-dev
kubectl logs -f deployment/devskyy-dev -n devskyy-dev
```

### 3. Deploy to Staging

```bash
# Build and preview manifests
kubectl kustomize k8s/overlays/staging

# Apply to cluster
kubectl apply -k k8s/overlays/staging

# Verify deployment
kubectl get all -n devskyy-staging
kubectl logs -f deployment/devskyy-staging -n devskyy-staging
```

### 4. Deploy to Production

```bash
# Build and preview manifests
kubectl kustomize k8s/overlays/production

# IMPORTANT: Review all resources before applying to production!
kubectl diff -k k8s/overlays/production

# Apply to cluster
kubectl apply -k k8s/overlays/production

# Verify deployment
kubectl get all -n devskyy
kubectl logs -f deployment/devskyy -n devskyy

# Check HPA status
kubectl get hpa -n devskyy

# Check pod disruption budgets
kubectl get pdb -n devskyy
```

## Configuration Customization

### Image Tags

Update image tags in overlay kustomization.yaml:

```yaml
images:
- name: devskyy
  newName: your-registry/devskyy
  newTag: v1.2.3
```

### Ingress Hostnames

Update ingress hostname in overlay kustomization.yaml:

```yaml
patches:
- target:
    kind: Ingress
    name: devskyy-ingress
  patch: |-
    - op: replace
      path: /spec/rules/0/host
      value: your-domain.com
```

### Resource Limits

Adjust resource limits in overlay kustomization.yaml:

```yaml
patches:
- target:
    kind: Deployment
    name: devskyy
  patch: |-
    - op: replace
      path: /spec/template/spec/containers/0/resources/limits/cpu
      value: "4"
```

### HPA Scaling

Adjust HPA settings in overlay kustomization.yaml:

```yaml
patches:
- target:
    kind: HorizontalPodAutoscaler
    name: devskyy-hpa
  patch: |-
    - op: replace
      path: /spec/maxReplicas
      value: 50
```

## Security Hardening

### 1. Network Policies

Network policies are configured in `base/rbac.yaml`:
- Allow ingress from NGINX Ingress Controller (port 8000)
- Allow ingress from Prometheus (port 9091)
- Allow egress to PostgreSQL (port 5432)
- Allow egress to Redis (port 6379)
- Allow egress to DNS (port 53)
- Allow egress to HTTPS (port 443)

### 2. RBAC

Minimal RBAC permissions:
- Read access to ConfigMaps
- Read access to specific secrets only
- Read access to pods and services

### 3. Pod Security Context

All pods run with:
- `runAsNonRoot: true`
- `runAsUser: 1000` (non-root)
- `seccompProfile: RuntimeDefault`
- `allowPrivilegeEscalation: false`
- `readOnlyRootFilesystem: true` (where applicable)
- Dropped all capabilities

### 4. TLS/SSL

TLS certificates managed by cert-manager:
```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

## Monitoring and Observability

### Prometheus Metrics

Application exposes metrics on port 9091:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9091"
  prometheus.io/path: "/metrics"
```

### Health Checks

**Liveness Probe**: Checks if application is running
- Endpoint: `/health/live`
- Initial delay: 30s
- Period: 10s

**Readiness Probe**: Checks if application is ready to serve traffic
- Endpoint: `/health/ready`
- Initial delay: 10s
- Period: 5s

**Startup Probe**: Allows slow application startup
- Endpoint: `/health/startup`
- Failure threshold: 30
- Period: 10s (up to 5 minutes)

### Logs

View application logs:
```bash
# Real-time logs
kubectl logs -f deployment/devskyy -n devskyy

# Logs from all pods
kubectl logs -l app=devskyy -n devskyy --all-containers=true

# Previous pod logs (if crashed)
kubectl logs deployment/devskyy -n devskyy --previous
```

## Database Management

### PostgreSQL

**Access PostgreSQL**:
```bash
# Port-forward to local machine
kubectl port-forward statefulset/postgres 5432:5432 -n devskyy

# Connect using psql
psql postgresql://postgres:password@localhost:5432/devskyy

# Execute migrations
kubectl exec -it postgres-0 -n devskyy -- psql -U postgres -c "SELECT version();"
```

**Backup PostgreSQL**:
```bash
# Create backup
kubectl exec postgres-0 -n devskyy -- pg_dump -U postgres devskyy > backup.sql

# Restore backup
kubectl exec -i postgres-0 -n devskyy -- psql -U postgres devskyy < backup.sql
```

### Redis

**Access Redis**:
```bash
# Port-forward to local machine
kubectl port-forward statefulset/redis 6379:6379 -n devskyy

# Connect using redis-cli
redis-cli -h localhost -p 6379

# Check Redis info
kubectl exec -it redis-0 -n devskyy -- redis-cli INFO
```

## Scaling

### Manual Scaling

```bash
# Scale deployment
kubectl scale deployment/devskyy --replicas=5 -n devskyy

# Verify scaling
kubectl get pods -l app=devskyy -n devskyy
```

### Horizontal Pod Autoscaler (HPA)

HPA automatically scales based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)
- Custom metrics (http_requests_per_second: 1000)

**Check HPA status**:
```bash
kubectl get hpa -n devskyy
kubectl describe hpa devskyy-hpa -n devskyy
```

### Vertical Pod Autoscaler (VPA)

VPA automatically adjusts resource requests/limits:
- Min: 500m CPU, 1Gi memory
- Max: 4 CPU, 8Gi memory

**Check VPA status**:
```bash
kubectl get vpa -n devskyy
kubectl describe vpa devskyy-vpa -n devskyy
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl get pods -n devskyy
kubectl describe pod <pod-name> -n devskyy

# Check events
kubectl get events -n devskyy --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n devskyy
```

### Database Connection Issues

```bash
# Check PostgreSQL status
kubectl get statefulset postgres -n devskyy
kubectl logs postgres-0 -n devskyy

# Test connectivity
kubectl exec -it devskyy-<pod-id> -n devskyy -- \
  curl -v telnet://postgres:5432
```

### Ingress Not Working

```bash
# Check ingress status
kubectl get ingress -n devskyy
kubectl describe ingress devskyy-ingress -n devskyy

# Check NGINX Ingress Controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller

# Verify TLS certificate
kubectl get certificate -n devskyy
kubectl describe certificate devskyy-tls -n devskyy
```

### High Memory/CPU Usage

```bash
# Check resource usage
kubectl top pods -n devskyy
kubectl top nodes

# Check HPA metrics
kubectl get hpa -n devskyy
kubectl describe hpa devskyy-hpa -n devskyy

# Check VPA recommendations
kubectl describe vpa devskyy-vpa -n devskyy
```

## Maintenance

### Rolling Updates

```bash
# Update image tag
kubectl set image deployment/devskyy devskyy=devskyy:v2.0.0 -n devskyy

# Monitor rollout
kubectl rollout status deployment/devskyy -n devskyy

# Check rollout history
kubectl rollout history deployment/devskyy -n devskyy
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/devskyy -n devskyy

# Rollback to specific revision
kubectl rollout undo deployment/devskyy --to-revision=2 -n devskyy
```

### Cleanup

```bash
# Delete development environment
kubectl delete -k k8s/overlays/development

# Delete staging environment
kubectl delete -k k8s/overlays/staging

# Delete production environment (CAREFUL!)
kubectl delete -k k8s/overlays/production
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Kubernetes

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        kubeconfig: ${{ secrets.KUBE_CONFIG }}

    - name: Deploy to production
      run: |
        kubectl apply -k k8s/overlays/production
        kubectl rollout status deployment/devskyy -n devskyy
```

## Best Practices

1. **Secrets Management**
   - Never commit secrets to git
   - Use sealed-secrets or external secrets operator
   - Rotate secrets regularly

2. **Resource Limits**
   - Always set resource requests and limits
   - Monitor actual usage and adjust accordingly
   - Use VPA for automatic tuning

3. **High Availability**
   - Run at least 3 replicas in production
   - Use pod anti-affinity for node distribution
   - Configure PodDisruptionBudgets

4. **Monitoring**
   - Enable Prometheus scraping
   - Set up alerts for high CPU/memory usage
   - Monitor application logs

5. **Security**
   - Keep images up to date
   - Run security scans (Trivy, Snyk)
   - Follow least privilege principle
   - Enable network policies

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Documentation](https://kustomize.io/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets)

## Support

For issues or questions:
- GitHub Issues: [DevSkyy Issues](https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues)
- Documentation: [DevSkyy Docs](https://docs.devskyy.com)
