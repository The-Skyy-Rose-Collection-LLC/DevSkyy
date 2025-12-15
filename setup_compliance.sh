#!/bin/bash
# Setup Clean Coding Compliance Agents for DevSkyy
# Run this script after cloning the repository

set -e

echo "🚀 Setting up DevSkyy Clean Coding Compliance Agents"
echo "=================================================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required"
    echo "   Current version: $python_version"
    exit 1
fi
echo "   Python version: $python_version ✓"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
if [ -f "pyproject.toml" ]; then
    pip install -e ".[dev]" --quiet
    echo "   Dependencies installed ✓"
else
    echo "❌ Error: pyproject.toml not found"
    exit 1
fi
echo ""

# Install pre-commit
echo "🔧 Installing pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo "   Pre-commit hooks installed ✓"
else
    echo "   Installing pre-commit..."
    pip install pre-commit --quiet
    pre-commit install
    echo "   Pre-commit hooks installed ✓"
fi
echo ""

# Generate secrets baseline
echo "🔐 Generating secrets baseline..."
if command -v detect-secrets &> /dev/null; then
    if [ ! -f ".secrets.baseline" ]; then
        detect-secrets scan > .secrets.baseline
        echo "   Secrets baseline created ✓"
    else
        echo "   Secrets baseline already exists ✓"
    fi
else
    echo "   Installing detect-secrets..."
    pip install detect-secrets --quiet
    detect-secrets scan > .secrets.baseline
    echo "   Secrets baseline created ✓"
fi
echo ""

# Run pre-commit on all files (optional)
echo "🧹 Running pre-commit on all files (this may take a while)..."
read -p "Do you want to run pre-commit on all files now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pre-commit run --all-files || true
    echo "   Pre-commit checks completed ✓"
else
    echo "   Skipped. You can run 'pre-commit run --all-files' manually later."
fi
echo ""

# Create .env file if it doesn't exist
echo "🔑 Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "   Creating .env from .env.example..."
        cp .env.example .env
        echo "   .env created ✓"
        echo "   ⚠️  Please edit .env and add your API keys"
    else
        echo "   No .env.example found, skipping .env creation"
    fi
else
    echo "   .env already exists ✓"
fi
echo ""

# Summary
echo "=================================================="
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Make a commit to test pre-commit hooks"
echo "3. Push to GitHub to trigger CI/CD workflows"
echo ""
echo "Useful commands:"
echo "  • Run pre-commit manually:     pre-commit run --all-files"
echo "  • Update pre-commit hooks:     pre-commit autoupdate"
echo "  • Run tests:                   pytest tests/ -v"
echo "  • Check code coverage:         pytest tests/ --cov"
echo "  • Format code:                 black ."
echo "  • Lint code:                   ruff check ."
echo "  • Type check:                  mypy ."
echo ""
echo "For more information, see:"
echo "  • CLEAN_CODING_AGENTS.md - Complete compliance documentation"
echo "  • REPOSITORY_FILES.md - Full repository inventory"
echo ""
