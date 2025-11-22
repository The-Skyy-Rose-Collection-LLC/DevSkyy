#!/bin/bash
# DevSkyy Fashion Dependencies Installation Script
# Installs all necessary dependencies for fashion e-commerce and 3D modeling features
# Exit code 0 = success
# Exit code 1 = installation failures

# Strict mode with explicit error handling
set -eEuo pipefail

# Trap for cleanup on unexpected errors
trap 'echo "Error on line $LINENO. Installation aborted."; exit 1' ERR

echo "=================================================="
echo "DevSkyy Fashion Dependencies Installation"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

INSTALLATION_FAILED=0

# Check Python version
echo "Step 1: Checking Python version..."
echo "-----------------------------------"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}✗${NC} Python 3.11+ required, found $PYTHON_VERSION"
    exit 1
else
    echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION"
fi
echo ""

# Check pip availability
echo "Step 2: Checking pip availability..."
echo "-----------------------------------"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip3 is available"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    echo -e "${GREEN}✓${NC} pip is available"
    PIP_CMD="pip"
else
    echo -e "${RED}✗${NC} pip not found. Please install pip first."
    exit 1
fi
echo ""

# Upgrade pip, setuptools, and wheel
echo "Step 3: Upgrading pip, setuptools, and wheel..."
echo "-----------------------------------"
if $PIP_CMD install --upgrade pip setuptools>=78.1.1 wheel > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Successfully upgraded pip, setuptools, and wheel"
else
    echo -e "${RED}✗${NC} Failed to upgrade pip tools"
    INSTALLATION_FAILED=1
fi
echo ""

# Install core dependencies
echo "Step 4: Installing core dependencies from requirements.txt..."
echo "-----------------------------------"
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt (this may take a few minutes)..."
    if $PIP_CMD install -r requirements.txt --no-cache-dir; then
        echo -e "${GREEN}✓${NC} Core dependencies installed successfully"
    else
        echo -e "${RED}✗${NC} Failed to install core dependencies"
        INSTALLATION_FAILED=1
    fi
else
    echo -e "${YELLOW}⚠${NC} requirements.txt not found, skipping core dependencies"
fi
echo ""

# Install fashion-specific ML dependencies
echo "Step 5: Installing fashion-specific ML dependencies..."
echo "-----------------------------------"

FASHION_PACKAGES=(
    # Computer Vision for fashion image processing
    "opencv-python>=4.11.0,<5.0.0"
    "Pillow>=11.1.0,<12.0.0"

    # ML/AI for fashion trend analysis
    "scikit-learn~=1.5.2"
    "pandas~=2.3.3"
    "numpy>=2.2.0,<2.3.0"

    # NLP for fashion descriptions
    "nltk~=3.9.1"

    # Image generation for fashion design
    "diffusers~=0.35.2"
    "transformers~=4.57.1"

    # Color palette extraction
    "colorthief~=0.2.1"
    "webcolors~=24.12.1"

    # Data visualization for trends
    "matplotlib~=3.10.0"
    "seaborn~=0.13.2"

    # Price optimization
    "scipy~=1.16.3"
)

echo "Installing fashion-specific packages:"
for package in "${FASHION_PACKAGES[@]}"; do
    echo "  - $package"
    if $PIP_CMD install "$package" --no-cache-dir > /dev/null 2>&1; then
        echo -e "    ${GREEN}✓${NC} Installed"
    else
        echo -e "    ${YELLOW}⚠${NC} Already installed or skipped"
    fi
done
echo ""

# Install 3D modeling dependencies (optional)
echo "Step 6: Installing 3D modeling dependencies (optional)..."
echo "-----------------------------------"

MODELING_PACKAGES=(
    # 3D model processing
    "trimesh~=4.5.3"
    "pygltflib~=1.16.2"

    # Rendering and visualization
    "pyrender~=0.1.45"

    # Mesh processing
    "meshio~=5.3.5"
)

echo "Installing 3D modeling packages (optional):"
for package in "${MODELING_PACKAGES[@]}"; do
    echo "  - $package"
    if $PIP_CMD install "$package" --no-cache-dir > /dev/null 2>&1; then
        echo -e "    ${GREEN}✓${NC} Installed"
    else
        echo -e "    ${YELLOW}⚠${NC} Installation skipped (may require system dependencies)"
    fi
done
echo ""

# Install development dependencies (optional)
echo "Step 7: Installing development dependencies (optional)..."
echo "-----------------------------------"
if [ -f "requirements-dev.txt" ]; then
    read -p "Install development dependencies? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if $PIP_CMD install -r requirements-dev.txt --no-cache-dir; then
            echo -e "${GREEN}✓${NC} Development dependencies installed"
        else
            echo -e "${YELLOW}⚠${NC} Some development dependencies may have failed"
        fi
    else
        echo "Skipping development dependencies"
    fi
else
    echo -e "${YELLOW}⚠${NC} requirements-dev.txt not found, skipping"
fi
echo ""

# Verify installations
echo "Step 8: Verifying key package installations..."
echo "-----------------------------------"

# Map package names to their import names
# Format: "package_name:import_name"
KEY_PACKAGES=(
    "fastapi:fastapi"
    "anthropic:anthropic"
    "openai:openai"
    "transformers:transformers"
    "torch:torch"
    "numpy:numpy"
    "pandas:pandas"
    "scikit-learn:sklearn"
    "opencv-python:cv2"
    "Pillow:PIL"
)

for entry in "${KEY_PACKAGES[@]}"; do
    package="${entry%%:*}"
    import_name="${entry##*:}"

    if python3 -c "import ${import_name}" 2> /dev/null; then
        echo -e "${GREEN}✓${NC} $package - verified"
    else
        echo -e "${YELLOW}⚠${NC} $package - not found or import error"
    fi
done
echo ""

# Download NLTK data (required for fashion text processing)
echo "Step 9: Downloading NLTK data..."
echo "-----------------------------------"
if python3 -c "import nltk" 2> /dev/null; then
    echo "Downloading required NLTK datasets..."
    python3 -c "
import nltk
import ssl

# Handle SSL certificate issues
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required datasets
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('wordnet', quiet=True)
print('NLTK data downloaded successfully')
" 2>&1 | grep -E "downloaded|already"
    echo -e "${GREEN}✓${NC} NLTK data ready"
else
    echo -e "${YELLOW}⚠${NC} NLTK not installed, skipping data download"
fi
echo ""

# Create necessary directories
echo "Step 10: Creating required directories..."
echo "-----------------------------------"

DIRECTORIES=(
    "storage/3d_models"
    "storage/fashion_images"
    "storage/fashion_cache"
    "storage/ml_models"
    "artifacts"
    "logs"
)

for dir in "${DIRECTORIES[@]}"; do
    if mkdir -p "$dir" 2> /dev/null; then
        echo -e "${GREEN}✓${NC} Created/verified: $dir"
    else
        echo -e "${YELLOW}⚠${NC} Could not create: $dir"
    fi
done
echo ""

# Summary
echo "=================================================="
echo "Installation Summary"
echo "=================================================="
echo ""

if [ $INSTALLATION_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Fashion dependencies installed successfully!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Configure your .env file with API keys"
    echo "  2. Run 'python main.py' to start the application"
    echo "  3. Check the documentation in README.md"
    echo ""
    echo "For 3D modeling features, you may need to install system libraries:"
    echo "  Ubuntu/Debian: sudo apt-get install libgl1-mesa-glx libglib2.0-0"
    echo "  macOS: brew install mesa glib"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Installation completed with errors${NC}"
    echo ""
    echo "Some critical dependencies failed to install."
    echo "Please review the error messages above and retry."
    echo "You may need to install system dependencies first."
    echo ""
    exit 1
fi
