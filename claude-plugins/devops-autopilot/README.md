# DevOps Autopilot

An autonomous DevOps plugin for Claude Code that **proactively** handles CI/CD pipelines, containers, and infrastructure when frontend projects are detected.

## Key Feature: Proactive Activation

Unlike traditional tools that wait for commands, DevOps Autopilot **automatically activates** when it detects:
- Frontend frameworks (React, Next.js, Vue, Angular, Svelte)
- Deployment discussions ("deploy", "production", "release")
- DevOps needs (CI/CD, pipelines, containers)

## Features

- **Pipeline Generation**: GitHub Actions, GitLab CI, Jenkins
- **Container Management**: Docker, Kubernetes, AWS ECS
- **Infrastructure as Code**: Terraform for multi-cloud
- **Autonomous Operation**: Self-learning with Context7, auto-fix errors
- **Proactive Triggers**: Automatically offers DevOps setup

## Installation

```bash
# Load plugin with Claude Code
claude --plugin-dir /path/to/devops-autopilot
```

## Commands

| Command | Description |
|---------|-------------|
| `/pipeline` | Generate CI/CD pipeline (GitHub Actions, GitLab CI, Jenkins) |
| `/docker` | Generate Dockerfile and docker-compose |
| `/k8s` | Generate Kubernetes manifests or Helm charts |
| `/terraform` | Generate Terraform infrastructure code |
| `/deploy-infra` | Deploy infrastructure with autonomous error handling |
| `/devops-status` | Check status of pipelines, containers, infrastructure |

## Agents

The plugin includes 5 autonomous agents:

| Agent | Triggers | Purpose |
|-------|----------|---------|
| `devops-orchestrator` | Frontend/deployment mentions | Coordinates full DevOps setup |
| `pipeline-generator` | CI/CD needs | Generates pipeline configurations |
| `container-manager` | Docker/K8s mentions | Creates container configurations |
| `infra-provisioner` | Terraform/cloud mentions | Generates infrastructure code |
| `error-resolver` | DevOps errors | Diagnoses and fixes errors |

## Skills

Comprehensive knowledge base:

- **GitHub Actions** - Workflows, actions, secrets
- **GitLab CI** - Pipelines, jobs, variables
- **Jenkins** - Jenkinsfile, declarative pipelines
- **Docker & Kubernetes** - Dockerfile, manifests, Helm
- **Terraform** - AWS, GCP, Azure infrastructure
- **AWS ECS** - Fargate, ECR, task definitions

## Usage Examples

### Automatic Detection
When you mention a frontend framework, the plugin proactively offers DevOps setup:

```
You: I'm building a Next.js app

DevOps Autopilot: I detected a Next.js project. Would you like me to set up:
- GitHub Actions CI/CD pipeline
- Docker configuration
- Kubernetes manifests
- Terraform infrastructure
```

### Explicit Commands

```bash
# Generate GitHub Actions pipeline
/pipeline github --docker --deploy

# Create Docker configuration
/docker --compose --production

# Generate Kubernetes manifests
/k8s --ingress --hpa

# Create Terraform infrastructure
/terraform aws --ecs

# Check all DevOps status
/devops-status --all
```

## Autonomous Behavior

When errors occur:
1. Captures the exact error
2. Fetches documentation from Context7
3. Applies fixes automatically
4. Retries until successful
5. Reports what was fixed

## Platform Support

### CI/CD Platforms
- GitHub Actions
- GitLab CI
- Jenkins

### Container Platforms
- Docker
- Kubernetes
- AWS ECS/Fargate

### Cloud Providers
- AWS (primary)
- Google Cloud
- Microsoft Azure

### Infrastructure Tools
- Terraform (primary)
- Docker Compose
- Helm

## Prerequisites

Depending on what you're deploying:
- Docker installed for container builds
- Terraform installed for infrastructure
- AWS CLI configured for AWS deployments
- kubectl configured for Kubernetes

## Environment Variables

For AWS deployments:
```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
```

For container registries:
```bash
DOCKERHUB_USERNAME=your_username
DOCKERHUB_TOKEN=your_token
```

## License

MIT
