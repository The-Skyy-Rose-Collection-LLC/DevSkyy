#!/bin/bash
set -e

echo "🚀 DevSkyy MCP Configuration Setup"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# 1. Check if we're in the right directory
if [ ! -f "main.py" ] && [ ! -d "agent" ]; then
    print_error "Not in DevSkyy directory. Please run from project root."
    exit 1
fi

print_status "Directory check passed"

# 2. Check Git configuration
echo ""
echo "📦 Git Configuration"
echo "-------------------"

# Check if .git exists
if [ ! -d ".git" ]; then
    print_error "Not a git repository"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Check remote
if git remote get-url origin &> /dev/null; then
    REMOTE_URL=$(git remote get-url origin)
    print_status "Remote configured: $REMOTE_URL"
else
    print_warning "No remote configured"
    read -p "Enter GitHub repository URL (or press Enter to skip): " REPO_URL
    if [ ! -z "$REPO_URL" ]; then
        git remote add origin "$REPO_URL"
        print_status "Remote configured: $REPO_URL"
    fi
fi

# 3. Generate secure keys
echo ""
echo "🔑 Security Configuration"
echo "-------------------"

# Check if .env exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating..."
    
    # Generate secrets
    JWT_SECRET_KEY=$(openssl rand -hex 32)
    ENCRYPTION_MASTER_KEY=$(openssl rand -hex 32)
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Create .env from .env.example if it exists
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Created .env from .env.example"
        
        # Replace placeholder values
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/REPLACE-WITH-SECURE-RANDOM-STRING-MIN-32-CHARS/$JWT_SECRET_KEY/g" .env
            sed -i '' "s/REPLACE-WITH-SECURE-RANDOM-STRING-32-BYTES/$ENCRYPTION_MASTER_KEY/g" .env
        else
            # Linux
            sed -i "s/REPLACE-WITH-SECURE-RANDOM-STRING-MIN-32-CHARS/$JWT_SECRET_KEY/g" .env
            sed -i "s/REPLACE-WITH-SECURE-RANDOM-STRING-32-BYTES/$ENCRYPTION_MASTER_KEY/g" .env
        fi
    else
        # Create basic .env
        cat > .env << EOF
# DevSkyy Enterprise Configuration
JWT_SECRET_KEY=$JWT_SECRET_KEY
ENCRYPTION_MASTER_KEY=$ENCRYPTION_MASTER_KEY
SECRET_KEY=$SECRET_KEY

# Database
DATABASE_URL=sqlite:///devskyy.db

# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=INFO

# Docker
DOCKER_REGISTRY=docker.io
DOCKER_REGISTRY_USERNAME=skyyrosellc

# Add your API keys below
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
EOF
        print_status "Created basic .env file"
    fi
else
    print_status ".env file already exists"
    print_warning "Please review and update secrets manually"
fi

# 4. Docker configuration
echo ""
echo "🐳 Docker Configuration"
echo "-------------------"

if command -v docker &> /dev/null; then
    print_status "Docker detected: $(docker --version)"
    
    # Check if logged in
    if docker info &> /dev/null; then
        print_status "Docker is running"
        
        # Try to get logged in user
        USERNAME=$(docker info 2>/dev/null | grep "Username:" | awk '{print $2}')
        if [ ! -z "$USERNAME" ]; then
            print_status "Logged in as: $USERNAME"
        else
            print_warning "Not logged in to Docker Hub"
            read -p "Do you want to login now? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker login
            fi
        fi
    else
        print_error "Docker daemon is not running"
    fi
else
    print_warning "Docker not found. Install from https://docs.docker.com/get-docker/"
fi

# 5. Kubernetes configuration (optional)
echo ""
echo "☸️  Kubernetes Configuration"
echo "-------------------"

if command -v kubectl &> /dev/null; then
    print_status "kubectl detected: $(kubectl version --client --short 2>/dev/null)"
    
    if kubectl cluster-info &> /dev/null 2>&1; then
        print_status "Kubernetes cluster connection active"
        
        # Check if namespace exists
        if kubectl get namespace production &> /dev/null 2>&1; then
            print_status "Production namespace exists"
        else
            print_warning "Production namespace not found"
            read -p "Create production namespace? (y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kubectl create namespace production
                print_status "Created production namespace"
            fi
        fi
    else
        print_warning "No Kubernetes cluster connection"
    fi
else
    print_warning "kubectl not found"
fi

# 6. Verify Python environment
echo ""
echo "🐍 Python Configuration"
echo "-------------------"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python: $PYTHON_VERSION"
    
    # Check for required packages
    if python3 -m pip list | grep -q "fastapi"; then
        print_status "FastAPI installed"
    else
        print_warning "FastAPI not installed. Install with: pip install -r requirements.txt"
    fi
else
    print_error "Python 3 not found"
fi

# 7. Summary and next steps
echo ""
echo "=================================="
echo "📋 Setup Summary"
echo "=================================="
echo ""
echo "✅ Configuration complete!"
echo ""
echo "📝 Next Steps:"
echo "   1. Review and update .env file"
echo ""
if [ -f ".env" ]; then
    print_warning "   🔒 IMPORTANT: .env contains secrets. Never commit it!"
fi
echo "   2. Push to GitHub:"
echo "      git add ."
echo "      git commit -m 'Your commit message'"
echo "      git push -u origin $CURRENT_BRANCH"
echo ""
echo "   3. Configure GitHub Actions secrets:"
echo "      https://github.com/YOUR_REPO/settings/secrets/actions"
echo ""
echo "   4. Deploy:"
echo "      ./scripts/deploy.sh"
echo ""
echo "📖 For detailed information, see:"
echo "   - MCP_CONFIGURATION_GUIDE.md"
echo "   - SECURITY_CONFIGURATION_GUIDE.md"
echo "   - ENTERPRISE_REFACTOR_REPORT.md"
echo ""
print_status "Setup complete!"
echo ""

