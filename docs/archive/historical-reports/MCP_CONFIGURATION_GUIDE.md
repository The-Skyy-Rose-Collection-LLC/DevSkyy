# MCP Server Configuration Guide for DevSkyy

This guide configures all required MCP (Model Context Protocol) servers for DevSkyy enterprise deployment.

---

## 🔧 Git Configuration

### 1. Add Remote Repository

```bash
# If you have a GitHub repository
cd /Users/coreyfoster/.cursor/worktrees/DevSkyy-main_2/sLWW3
git remote add origin https://github.com/YOUR_USERNAME/DevSkyy.git

# Or if using SSH
git remote add origin git@github.com:YOUR_USERNAME/DevSkyy.git

# Verify
git remote -v
```

### 2. Push to Repository

```bash
# First time push
git push -u origin fix-commit-compliance-sLWW3

# Or merge to main first
git checkout main
git merge fix-commit-compliance-sLWW3
git push origin main
```

---

## 📦 Docker Hub MCP Configuration

### Docker Registry Setup

Based on your existing configuration:
- **Registry:** `docker.io`
- **Organization:** `skyyrosellc`
- **Image:** `skyyrosellc/devskyy`

### Configure Docker Hub Token

```bash
# Generate new Docker Hub token at https://hub.docker.com/settings/security
export DOCKER_HUB_TOKEN="your-new-token"

# Login to Docker Hub
echo "$DOCKER_HUB_TOKEN" | docker login -u skyyrosellc --password-stdin docker.io
```

### Update Environment Variables

```bash
# Add to .env file
cat >> .env << EOF

# Docker Hub Configuration
DOCKER_REGISTRY=docker.io
DOCKER_REGISTRY_USERNAME=skyyrosellc
DOCKER_REGISTRY_TOKEN=$DOCKER_HUB_TOKEN
EOF
```

---

## 🔑 GitHub Actions Secrets

Navigate to: `https://github.com/YOUR_USERNAME/DevSkyy/settings/secrets/actions`

Add these secrets:

```bash
DOCKER_REGISTRY=docker.io
DOCKER_REGISTRY_USERNAME=skyyrosellc
DOCKER_REGISTRY_TOKEN=<your-docker-token>

JWT_SECRET_KEY=<generate-with-openssl-rand-hex-32>
ENCRYPTION_MASTER_KEY=<generate-with-openssl-rand-hex-32>
DATABASE_URL=<your-database-url>

# API Keys (if needed)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# WordPress (optional)
WP_SSH_HOST=sftp.wp.com
WP_SSH_USER=skyyrose.wordpress.com
WP_SSH_PRIVATE_KEY=<your-ssh-private-key>
```

---

## 🚀 Kubernetes MCP Configuration

### Create Kubernetes Secrets

```bash
# Set your Kubernetes namespace
kubectl create namespace production

# Create secrets
kubectl create secret generic devskyy-secrets \
  --from-literal=JWT_SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=ENCRYPTION_MASTER_KEY="$(openssl rand -hex 32)" \
  --from-literal=DATABASE_URL="postgresql://user:pass@host:5432/db" \
  --from-literal=ANTHROPIC_API_KEY="sk-ant-..." \
  --namespace=production

# Create Docker registry secret
kubectl create secret docker-registry docker-hub-credentials \
  --docker-server=docker.io \
  --docker-username=skyyrosellc \
  --docker-password="<your-docker-token>" \
  --namespace=production
```

### Update Kubernetes Deployments

The deployment files in `kubernetes/production/` already reference these secrets:

```yaml
envFrom:
- secretRef:
    name: devskyy-secrets
imagePullSecrets:
- name: docker-hub-credentials
```

---

## ☁️ WordPress SFTP MCP Configuration

### SSH Key Setup

```bash
# Generate SSH key for WordPress SFTP
ssh-keygen -t ed25519 -C "devskyy@skyyrosellc.com" -f ~/.ssh/wordpress_devskyy

# Copy public key to WordPress host
ssh-copy-id -i ~/.ssh/wordpress_devskyy.pub skyyrose.wordpress.com
```

### Add to .env

```bash
cat >> .env << EOF

# WordPress SFTP Configuration
WP_SSH_HOST=sftp.wp.com
WP_SSH_USER=skyyrose.wordpress.com
WP_SSH_PRIVATE_KEY_PATH=$HOME/.ssh/wordpress_devskyy
WP_SSH_PORT=22
EOF
```

---

## 🔐 Vercel Deployment (If Applicable)

### Install Vercel CLI

```bash
npm install -g vercel

# Login
vercel login
```

### Create Vercel Project

```bash
# In your project directory
vercel link

# Set up environment variables
vercel env add SECRET_KEY production
vercel env add DATABASE_URL production
# ... add all required variables
```

### GitHub Integration

1. Go to https://vercel.com/dashboard
2. Import Git Repository
3. Add build configuration
4. Set environment variables

---

## 📊 Monitoring & Observability

### Prometheus (Optional)

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

### Grafana (Optional)

```yaml
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## ✅ Verification Checklist

Run these commands to verify your MCP configuration:

```bash
#!/bin/bash
echo "🔍 Verifying MCP Configuration..."

# 1. Git remote
echo "1. Git Remote:"
git remote -v

# 2. Docker login
echo -e "\n2. Docker Login:"
docker info 2>&1 | grep -A 2 "Username" || echo "Not logged in"

# 3. Kubernetes secrets
echo -e "\n3. Kubernetes Secrets:"
kubectl get secrets -n production 2>/dev/null || echo "Kubernetes not configured"

# 4. WordPress SSH
echo -e "\n4. WordPress SSH:"
ssh -o ConnectTimeout=5 -o BatchMode=yes skyyrose.wordpress.com echo "OK" 2>/dev/null || echo "SSH not configured"

# 5. Environment variables
echo -e "\n5. Required Environment Variables:"
for var in JWT_SECRET_KEY ENCRYPTION_MASTER_KEY DATABASE_URL; do
    if [ -z "${!var}" ]; then
        echo "   ❌ $var: NOT SET"
    else
        echo "   ✅ $var: SET"
    fi
done

echo -e "\n✅ Verification complete"
```

---

## 🎯 Quick Start Commands

### Complete Setup Script

Save this as `setup_mcp.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 DevSkyy MCP Configuration Setup"

# 1. Set up Git remote (you'll need to provide your repo URL)
read -p "Enter your GitHub repository URL: " REPO_URL
if [ ! -z "$REPO_URL" ]; then
    git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
    echo "✅ Git remote configured"
fi

# 2. Generate secrets
echo "🔑 Generating secure keys..."
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export ENCRYPTION_MASTER_KEY=$(openssl rand -hex 32)

# 3. Create .env file
echo "📝 Creating .env file..."
cat > .env << EOF
# DevSkyy Configuration
JWT_SECRET_KEY=$JWT_SECRET_KEY
ENCRYPTION_MASTER_KEY=$ENCRYPTION_MASTER_KEY
DATABASE_URL=sqlite:///devskyy.db

# Docker Configuration
DOCKER_REGISTRY=docker.io
DOCKER_REGISTRY_USERNAME=skyyrosellc

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO
EOF

echo "✅ .env file created"

# 4. Set up Docker (if available)
if command -v docker &> /dev/null; then
    echo "🐳 Docker detected"
    read -p "Do you want to configure Docker Hub? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Please login to Docker Hub at https://hub.docker.com"
        echo "Then run: docker login"
    fi
fi

# 5. Display next steps
echo -e "\n✅ Setup complete!"
echo -e "\n📋 Next steps:"
echo "   1. Review .env file and update as needed"
echo "   2. Configure Docker Hub token"
echo "   3. Push to GitHub: git push -u origin main"
echo "   4. Set up GitHub Actions secrets"
echo -e "\n📖 See MCP_CONFIGURATION_GUIDE.md for details"
```

Make it executable and run:

```bash
chmod +x setup_mcp.sh
./setup_mcp.sh
```

---

## 📞 Support

For issues with MCP configuration:
1. Check logs: `tail -f logs/app.log`
2. Verify environment: `python -c "import os; print(os.environ.get('JWT_SECRET_KEY', 'NOT SET'))"`
3. Test connections: `./scripts/test-connections.sh`
4. Review documentation: See `DEPLOYMENT_GUIDE.md`

---

**Last Updated:** 2025-01-XX  
**Version:** 5.2 Enterprise  
**Status:** ✅ Ready for Production

