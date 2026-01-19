---
name: k8s
description: Generate Kubernetes manifests for deployment
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - WebFetch
argument-hint: "[--helm] [--ingress] [--hpa]"
---

# Kubernetes Command

Generate Kubernetes manifests for deploying your application.

## Execution Steps

1. **Detect application requirements**
   - Check Dockerfile for port and health check
   - Identify resource requirements
   - Check for environment variables needed

2. **Generate base manifests**
   - Deployment with replicas
   - Service (ClusterIP)
   - ConfigMap for config
   - Secret template

3. **Add optional components**
   - Ingress (if `--ingress`)
   - HorizontalPodAutoscaler (if `--hpa`)
   - Helm chart (if `--helm`)

4. **Configure resources**
   - Resource requests and limits
   - Liveness and readiness probes
   - Environment variables

## Arguments

- `--helm`: Generate Helm chart instead of plain manifests
- `--ingress`: Include Ingress resource with TLS
- `--hpa`: Include HorizontalPodAutoscaler

## Example Usage

```
/k8s                         # Basic manifests
/k8s --ingress               # With Ingress
/k8s --hpa                   # With autoscaling
/k8s --helm                  # Full Helm chart
/k8s --ingress --hpa         # Production-ready
```

## Output Files

### Plain Manifests
```
k8s/
├── deployment.yaml
├── service.yaml
├── configmap.yaml
├── secret.yaml
├── ingress.yaml        # if --ingress
└── hpa.yaml            # if --hpa
```

### Helm Chart (if --helm)
```
helm/my-app/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ...
```

## Deploy Commands

After generation:
```bash
# Apply manifests
kubectl apply -f k8s/

# Install Helm chart
helm install my-app ./helm/my-app

# Check status
kubectl rollout status deployment/my-app
```
