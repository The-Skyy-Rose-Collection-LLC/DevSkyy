#!/bin/bash
# DevSkyy Clean Coding Compliance Setup Script
# Sets up automated code quality enforcement system

set -e

echo "🚀 Setting up DevSkyy Clean Coding Compliance System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ $(echo "$PYTHON_VERSION < 3.11" | bc -l) -eq 1 ]]; then
    print_error "Python 3.11+ is required, found $PYTHON_VERSION"
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# Install pre-commit
print_status "Installing pre-commit..."
pip3 install pre-commit

# Install pre-commit hooks
print_status "Installing pre-commit hooks..."
pre-commit install

# Install additional tools
print_status "Installing code quality tools..."
pip3 install black isort ruff mypy bandit[toml] detect-secrets

# Install testing tools
print_status "Installing testing tools..."
pip3 install pytest pytest-cov pytest-asyncio

# Install documentation tools
print_status "Installing documentation tools..."
pip3 install markdownlint-cli2

# Generate secrets baseline
print_status "Generating secrets baseline..."
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan --baseline .secrets.baseline
    print_success "Secrets baseline generated"
else
    print_warning "detect-secrets not available, skipping baseline generation"
fi

# Run initial pre-commit check
print_status "Running initial pre-commit check..."
if pre-commit run --all-files; then
    print_success "All pre-commit hooks passed!"
else
    print_warning "Some pre-commit hooks failed. This is normal for first run."
    print_status "Running auto-fixes..."

    # Run formatters
    black . || true
    isort . || true
    ruff --fix . || true

    print_status "Re-running pre-commit hooks..."
    pre-commit run --all-files || true
fi

# Create .env.example if it doesn't exist
if [ ! -f .env.example ]; then
    print_status "Creating .env.example..."
    cat > .env.example << EOF
# DevSkyy Environment Configuration
# Copy to .env and fill in your values

# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key-here

# DevSkyy Platform
DEVSKYY_API_KEY=your-devskyy-api-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost/devskyy

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# WordPress (optional)
WORDPRESS_URL=https://your-wordpress-site.com
WORDPRESS_USERNAME=your-username
WORDPRESS_PASSWORD=your-app-password

# Development
DEBUG=false
LOG_LEVEL=INFO
EOF
    print_success ".env.example created"
fi

# Update .gitignore
print_status "Updating .gitignore..."
cat >> .gitignore << 'EOF'

# Code quality reports
.coverage
htmlcov/
coverage.xml
.pytest_cache/
.mypy_cache/
.ruff_cache/
bandit-report.json
safety-report.json

# Environment files
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
EOF

print_success "Setup complete! 🎉"
echo
echo "📋 Next steps:"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Run 'pre-commit run --all-files' to check all files"
echo "3. Commit your changes - pre-commit hooks will run automatically"
echo "4. Push to trigger GitHub Actions CI/CD pipeline"
echo
echo "🔧 Available commands:"
echo "  pre-commit run --all-files    # Run all hooks manually"
echo "  pytest --cov                  # Run tests with coverage"
echo "  bandit -r .                   # Security scan"
echo "  ruff check .                  # Linting"
echo "  black .                       # Code formatting"
echo
echo "📚 Documentation:"
echo "  - CLEAN_CODING_AGENTS.md     # Full system documentation"
echo "  - DEVELOPER_QUICKREF.md      # Daily workflow commands"
echo "  - .pre-commit-config.yaml    # Hook configuration"
