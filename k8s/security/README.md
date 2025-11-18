# DevSkyy Kubernetes Security

Enterprise-grade security configurations for the DevSkyy platform following zero-trust principles.

## Security Components

### 1. Network Policies (`network-policies.yaml`)

Zero-trust network segmentation using Kubernetes NetworkPolicy resources.

**Key Features:**
- **API Pod Isolation**: Ingress restricted to NGINX Ingress Controller only (not 0.0.0.0/0)
- **Worker Pod Isolation**: No ingress traffic allowed to background workers
- **Database Isolation**: PostgreSQL/Redis only accessible from application pods
- **Default Deny**: All traffic denied by default unless explicitly allowed

**Apply Network Policies:**
```bash
kubectl apply -f network-policies.yaml
```

### 2. Falco Runtime Security

Falco monitors kernel syscalls for suspicious behavior and generates real-time alerts.

**Install Falco:**
```bash
# Add Falco Helm repository
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# Install Falco with custom rules
helm install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set falco.grpc.enabled=true \
  --set falco.grpcOutput.enabled=true

# Verify installation
kubectl get pods -n falco
```

**Monitor Falco Alerts:**
```bash
# View real-time alerts
kubectl logs -n falco -l app=falco -f | grep -i "priority=warning\|priority=critical"

# Export alerts to Slack/PagerDuty (optional)
# FIXED: This file now exists in the repository
kubectl apply -f falco-sidekick.yaml
```

**Configure Sidekick Secrets:**
```bash
# Create secrets for alert routing
kubectl create secret generic falco-sidekick-secrets \
  --from-literal=slack-webhook-url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL' \
  --from-literal=pagerduty-routing-key='YOUR_PAGERDUTY_KEY' \
  --namespace=falco
```

### 3. Pod Security Standards

Enforce pod security at the namespace level using Pod Security Admission.

**Apply Pod Security Labels:**
```bash
# Enforce restricted security standard
kubectl label namespace devskyy \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted
```

### 4. RBAC (Role-Based Access Control)

Minimal RBAC permissions following the principle of least privilege.

**Key Permissions:**
- Read-only access to ConfigMaps
- Read access to specific secrets only (not all secrets)
- No write access to cluster resources
- No access to other namespaces

**Review RBAC:**
```bash
kubectl get role,rolebinding -n devskyy
kubectl describe role devskyy-role -n devskyy
```

### 5. Secret Management

**Recommended Tools:**

**Option A: Sealed Secrets (Bitnami)**
```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Seal a secret
kubeseal --format=yaml < secret.yaml > sealed-secret.yaml
kubectl apply -f sealed-secret.yaml
```

**Option B: External Secrets Operator**
```bash
# Install external-secrets
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace

# Create SecretStore for AWS Secrets Manager
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secretsmanager
  namespace: devskyy
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
EOF
```

### 6. Image Security Scanning

Scan container images for vulnerabilities using Trivy.

**Scan Images:**
```bash
# Scan application image
trivy image --severity HIGH,CRITICAL devskyy:production

# Scan with exit code on vulnerabilities
trivy image --exit-code 1 --severity CRITICAL devskyy:production

# Generate report
trivy image --format json --output image-scan.json devskyy:production
```

### 7. OPA/Gatekeeper Policy Enforcement

Enforce custom policies using Open Policy Agent (OPA) Gatekeeper.

**Install Gatekeeper:**
```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/release-3.14/deploy/gatekeeper.yaml
```

**Example Policy: Require Read-Only Root Filesystem**
```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirereadonlyrootfilesystem
spec:
  crd:
    spec:
      names:
        kind: K8sRequireReadOnlyRootFilesystem
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequirereadonlyrootfilesystem

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not container.securityContext.readOnlyRootFilesystem
        msg := sprintf("Container %v must have readOnlyRootFilesystem=true", [container.name])
      }
```

### 8. Network Traffic Encryption

**TLS Between Services (mTLS):**

Install a service mesh like Istio or Linkerd for automatic mTLS between pods.

**Istio Installation:**
```bash
# Install Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH
istioctl install --set profile=default -y

# Enable automatic sidecar injection
kubectl label namespace devskyy istio-injection=enabled

# Verify mTLS
istioctl x describe pod <pod-name> -n devskyy
```

### 9. Audit Logging

Enable Kubernetes audit logging to track all API server requests.

**Audit Policy Example:**
```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: Metadata
  omitStages:
  - RequestReceived
  resources:
  - group: ""
    resources: ["secrets", "configmaps"]
  namespaces: ["devskyy"]
```

### 10. Vulnerability Scanning (Continuous)

**Snyk Monitor:**
```bash
# Install Snyk controller
helm repo add snyk-charts https://snyk.github.io/kubernetes-monitor
helm install snyk-monitor snyk-charts/snyk-monitor \
  --namespace snyk-monitor \
  --create-namespace \
  --set clusterName="devskyy-cluster" \
  --set policyOrgs={YOUR_SNYK_ORG_ID}
```

## Security Checklist

Before deploying to production, verify:

- [ ] Network policies applied and tested
- [ ] All secrets managed via sealed-secrets or external secrets operator
- [ ] Pod security standards enforced (restricted)
- [ ] RBAC configured with least privilege
- [ ] Container images scanned for vulnerabilities
- [ ] TLS certificates configured for ingress
- [ ] Falco runtime monitoring enabled
- [ ] Audit logging enabled
- [ ] Pod security contexts configured (runAsNonRoot, readOnlyRootFilesystem)
- [ ] Resource limits set on all containers
- [ ] PodDisruptionBudgets configured
- [ ] Backup and disaster recovery tested

## Incident Response

### Falco Alert Response

**Critical Alert Example:**
```
Priority: Critical
Rule: Shell spawned in container
Container: devskyy-api-xyz123
Command: /bin/bash
```

**Response Steps:**
1. Isolate the affected pod immediately
2. Capture forensic data (logs, memory dump)
3. Investigate the root cause
4. Patch the vulnerability
5. Update security policies

**Isolate Pod:**
```bash
# Apply isolation network policy
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-pod
  namespace: devskyy
spec:
  podSelector:
    matchLabels:
      pod: compromised-pod-label
  policyTypes:
  - Ingress
  - Egress
  ingress: []
  egress: []
EOF
```

### Security Audit

**Run Security Audit:**
```bash
# Audit RBAC permissions
kubectl auth can-i --list --namespace=devskyy

# Check for pods running as root
kubectl get pods -n devskyy -o json | \
  jq -r '.items[] | select(.spec.securityContext.runAsUser==0) | .metadata.name'

# Check for privileged pods
kubectl get pods -n devskyy -o json | \
  jq -r '.items[] | select(.spec.containers[].securityContext.privileged==true) | .metadata.name'

# Verify network policies
kubectl get networkpolicies -n devskyy
kubectl describe networkpolicy -n devskyy
```

## Compliance

### CIS Kubernetes Benchmark

Run kube-bench to check CIS compliance:

```bash
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs -f job/kube-bench
```

### NIST 800-190 Container Security

Key requirements implemented:
- ✅ Image vulnerability scanning
- ✅ Runtime security monitoring (Falco)
- ✅ Network segmentation (NetworkPolicy)
- ✅ Secrets management
- ✅ Least privilege access (RBAC)
- ✅ Audit logging

## References

- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/security-best-practices/)
- [NSA/CISA Kubernetes Hardening Guide](https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF)
- [OWASP Kubernetes Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html)
- [Falco Documentation](https://falco.org/docs/)
- [OPA Gatekeeper Documentation](https://open-policy-agent.github.io/gatekeeper/website/)
