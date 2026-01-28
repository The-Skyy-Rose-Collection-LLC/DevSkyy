---
name: devops-status
description: Check status of CI/CD pipelines, containers, and infrastructure
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - WebFetch
argument-hint: "[--pipelines|--containers|--infra|--all]"
---

# DevOps Status Command

Check the status of all DevOps components: pipelines, containers, and infrastructure.

## Execution Steps

1. **Check CI/CD pipelines**
   - GitHub Actions: Recent workflow runs
   - GitLab CI: Recent pipeline status
   - Jenkins: Recent build status

2. **Check containers**
   - Local Docker containers
   - Kubernetes deployments (if configured)
   - ECS services (if configured)

3. **Check infrastructure**
   - Terraform state
   - Cloud resources status
   - Health endpoints

4. **Report status**
   - Overall health
   - Recent failures
   - Pending deployments

## Arguments

- `--pipelines`: Check CI/CD pipelines only
- `--containers`: Check containers only
- `--infra`: Check infrastructure only
- `--all`: Check everything (default)

## Example Usage

```
/devops-status               # Full status check
/devops-status --pipelines   # Pipelines only
/devops-status --containers  # Containers only
/devops-status --infra       # Infrastructure only
```

## Output Format

```
DevOps Status
═══════════════════════════════════════

CI/CD Pipelines:
├── GitHub Actions: ✅ Last run passed (2h ago)
├── Latest commit: abc123 - "Feature update"
└── Workflow: ci.yml

Containers:
├── Local Docker: 3 running
├── Kubernetes: ✅ 3/3 pods ready
└── ECS: ✅ 2 tasks running

Infrastructure:
├── Terraform: ✅ 15 resources
├── VPC: vpc-xxx (10.0.0.0/16)
├── ECS Cluster: my-cluster
└── RDS: ✅ Available

Health Checks:
├── Production: ✅ HTTP 200
├── Staging: ✅ HTTP 200
└── API: ✅ Healthy

Overall Status: ✅ All systems operational
```

## Automated Actions

If issues detected:
1. Diagnose the problem
2. Suggest remediation
3. Offer to fix automatically
