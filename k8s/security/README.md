# DevSkyy Security Infrastructure

This directory contains enterprise-grade security configurations for DevSkyy's Kubernetes deployment.

## 📋 Contents

1. **Falco Runtime Security** - `falco-rules.yaml`
2. **Kubernetes NetworkPolicies** - `network-policies.yaml`
3. **Secret Scanning** - `.github/workflows/secret-scan.yml`
4. **Image Signing** - Cosign integration in deploy.yml
5. **SLSA Provenance** - Build attestations in deploy.yml

---

## 🛡️ Falco Runtime Security

### What is Falco?

Falco is a cloud-native runtime security tool that detects unexpected behavior, intrusions, and data theft in real-time.

### Deployment

```bash
# 1. Install Falco via Helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

# 2. Create Falco namespace
kubectl create namespace falco

# 3. Install Falco with custom rules
helm install falco falcosecurity/falco \
  --namespace falco \
  --set tty=true \
  --set falco.grpc.enabled=true \
  --set falco.grpcOutput.enabled=true

# 4. Apply DevSkyy custom rules
kubectl apply -f falco-rules.yaml

# 5. Verify Falco is running
kubectl get pods -n falco
kubectl logs -n falco -l app=falco -f
```

### Monitoring Falco Alerts

```bash
# Stream live alerts
kubectl logs -n falco -l app=falco -f | grep -i "priority=warning\|priority=critical"

# Export alerts to Slack/PagerDuty
kubectl apply -f falco-sidekick.yaml  # (optional - for alert routing)
```

### Falco Rules Included

| Rule | Priority | Description |
|------|----------|-------------|
| Shell Spawned in Container | WARNING | Detects shell execution |
| Unauthorized File Access | CRITICAL | Access to /etc/shadow, SSH keys |
| Package Manager Execution | WARNING | Immutable container violation |
| Crypto Mining Detection | CRITICAL | Cryptocurrency mining |
| Reverse Shell Detection | CRITICAL | Backdoor attempts |
| Container Escape Attempt | CRITICAL | Privilege escalation |
| Model File Access | CRITICAL | AI/ML model theft |
| Environment Variable Access | WARNING | API key theft attempts |

---

## 🔒 Kubernetes NetworkPolicies

### Zero-Trust Network Architecture

Our NetworkPolicies implement a **default-deny** posture with explicit allow rules.

### Deployment

```bash
# 1. Ensure your cluster supports NetworkPolicies
kubectl get networkpolicies --all-namespaces

# 2. Create DevSkyy namespace
kubectl create namespace devskyy

# 3. Apply NetworkPolicies
kubectl apply -f network-policies.yaml

# 4. Verify policies are applied
kubectl get networkpolicies -n devskyy
```

### Network Segmentation

```
┌─────────────────────────────────────────────┐
│          Internet/Cloud Run LB              │
└──────────────────┬──────────────────────────┘
                   │ (HTTPS :443, HTTP :8000)
                   ▼
         ┌─────────────────┐
         │  Ingress Nginx  │
         └────────┬────────┘
                  │ (:8000)
                  ▼
         ┌─────────────────┐
         │  DevSkyy API    │◄──────┐
         │  (app=api)      │       │
         └─┬──────┬────────┘       │
           │      │                 │
           │      │                 │ Deny All
    (:5432)│      │(:6379)          │ by Default
           │      │                 │
           ▼      ▼                 │
    ┌──────────┐  ┌──────────┐     │
    │PostgreSQL│  │  Redis   │     │
    └──────────┘  └──────────┘     │
                                    │
         ┌─────────────────┐        │
         │ DevSkyy Worker │◄───────┘
         │ (app=worker)   │
         └────────────────┘
            │
            │ (:443 HTTPS only)
            ▼
      External AI APIs
      (Anthropic, OpenAI)
```

### Key Policies

1. **default-deny-ingress**: Block all inbound traffic by default
2. **default-deny-egress**: Block all outbound traffic by default
3. **allow-api-ingress**: API receives traffic from ingress controller only
4. **allow-api-to-postgres**: API can connect to database
5. **allow-api-to-redis**: API can connect to cache
6. **allow-api-external-calls**: API can call external HTTPS APIs only
7. **allow-worker-limited**: Workers have minimal network access

### Validation

```bash
# Test connectivity from API pod
kubectl exec -n devskyy -it <api-pod-name> -- curl -v postgres:5432
kubectl exec -n devskyy -it <api-pod-name> -- curl -v redis:6379
kubectl exec -n devskyy -it <api-pod-name> -- curl -v https://api.anthropic.com

# Verify blocked connections
kubectl exec -n devskyy -it <api-pod-name> -- curl -v http://internal-service:8080
# (should fail - not explicitly allowed)
```

---

## 🔐 Secret Scanning

### GitHub Actions Integration

We use **4 secret scanning tools** for comprehensive coverage:

1. **GitGuardian** - Commercial-grade secret detection
2. **Gitleaks** - Open-source secret scanner
3. **TruffleHog** - High-entropy string detection
4. **detect-secrets** - Yelp's secret baseline scanner

### Setup

```bash
# 1. Add GitGuardian API key to GitHub Secrets
# Settings → Secrets → Actions → New secret
# Name: GITGUARDIAN_API_KEY
# Value: <your-api-key>

# 2. (Optional) Add Gitleaks license for advanced features
# Name: GITLEAKS_LICENSE
# Value: <your-license-key>

# 3. Workflow runs automatically on:
# - Every push to main/develop
# - Every pull request
# - Daily at 4 AM UTC
```

### Local Scanning

```bash
# Install detect-secrets
pip install detect-secrets==1.5.0

# Create baseline
detect-secrets scan --baseline .secrets.baseline

# Scan for new secrets
detect-secrets scan --baseline .secrets.baseline --fail-on-unaudited

# Install pre-commit hook
cat > .git/hooks/pre-commit <<'EOF'
#!/bin/bash
detect-secrets-hook --baseline .secrets.baseline $(git diff --cached --name-only)
EOF
chmod +x .git/hooks/pre-commit
```

---

## 🔏 Cosign Image Signing

### How It Works

Every Docker image is cryptographically signed using **Sigstore Cosign** with keyless OIDC signing:

1. Build Docker image in GitHub Actions
2. Sign image with Cosign using GitHub OIDC token
3. Push signed image to GHCR
4. Verify signature before deployment

### Verification

```bash
# Verify image signature
cosign verify ghcr.io/the-skyy-rose-collection-llc/devskyy/api:latest \
  --certificate-identity-regexp="https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy" \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com

# Output: Verification successful!
```

### Key Benefits

- ✅ **No key management** - Uses GitHub OIDC tokens
- ✅ **Immutable audit trail** - Signed in Rekor transparency log
- ✅ **Supply chain security** - Prevents image tampering
- ✅ **Compliance** - Meets SLSA Level 3 requirements

---

## 📜 SLSA Provenance

### What is SLSA?

SLSA (Supply-chain Levels for Software Artifacts) is a framework for ensuring the integrity of software artifacts.

### Our Implementation

We achieve **SLSA Level 3** compliance:

- ✅ **Build provenance** - Attestations for every image
- ✅ **Hermetic builds** - Isolated build environment
- ✅ **Non-falsifiable** - Signed with GitHub OIDC
- ✅ **Verifiable** - Stored in GitHub attestations

### Viewing Attestations

```bash
# View attestations for an image
gh attestation verify oci://ghcr.io/the-skyy-rose-collection-llc/devskyy/api:latest \
  --owner The-Skyy-Rose-Collection-LLC

# Download attestation
gh api \
  -H "Accept: application/vnd.github+json" \
  /repos/The-Skyy-Rose-Collection-LLC/DevSkyy/attestations
```

---

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] Apply NetworkPolicies
- [ ] Deploy Falco
- [ ] Configure secret scanning
- [ ] Verify Cosign signing works
- [ ] Test SLSA provenance generation

### Post-Deployment

- [ ] Monitor Falco alerts (first 24 hours)
- [ ] Verify NetworkPolicies block unauthorized traffic
- [ ] Check secret scanning results
- [ ] Audit image signatures
- [ ] Review SLSA attestations

---

## 📊 Security Metrics

Monitor these key metrics:

| Metric | Target | Tool |
|--------|--------|------|
| Falco Alerts | < 5/day | Falco logs |
| Blocked Network Connections | Log all | NetworkPolicy audit |
| Secrets Exposed | 0 | GitGuardian/Gitleaks |
| Unsigned Images | 0 | Cosign verification |
| SLSA Compliance | Level 3 | GitHub Attestations |

---

## 🆘 Incident Response

### Falco Alert Response

```bash
# 1. View recent critical alerts
kubectl logs -n falco -l app=falco --tail=100 | grep "CRITICAL"

# 2. Identify compromised pod
kubectl get pods -n devskyy -o wide

# 3. Isolate pod (apply NetworkPolicy)
kubectl label pod <pod-name> quarantine=true

# 4. Capture forensics
kubectl exec <pod-name> -- ps aux > forensics-ps.txt
kubectl exec <pod-name> -- netstat -tulpn > forensics-netstat.txt
kubectl logs <pod-name> > forensics-logs.txt

# 5. Delete compromised pod
kubectl delete pod <pod-name>

# 6. Investigate image
trivy image ghcr.io/...
cosign verify ...
```

### Secret Exposure Response

```bash
# 1. Rotate exposed secret immediately
# 2. Revoke API keys
# 3. Update GitHub Secrets
# 4. Redeploy application
kubectl rollout restart deployment/devskyy-api -n devskyy

# 5. Audit access logs for unauthorized usage
# 6. Add exposed pattern to .gitignore
# 7. Rewrite Git history if needed (use BFG Repo-Cleaner)
```

---

## 📚 Additional Resources

- [Falco Documentation](https://falco.org/docs/)
- [Kubernetes NetworkPolicies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Sigstore Cosign](https://docs.sigstore.dev/cosign/overview/)
- [SLSA Framework](https://slsa.dev/)
- [GitGuardian](https://www.gitguardian.com/docs)
- [OWASP Kubernetes Security](https://owasp.org/www-project-kubernetes-security/)

---

**Maintained by:** DevSkyy Security Team
**Last Updated:** 2025-11-17
**Security Contact:** security@devskyy.io
