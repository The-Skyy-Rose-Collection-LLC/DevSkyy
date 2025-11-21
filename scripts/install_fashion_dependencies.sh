#!/bin/bash
# DevSkyy Fashion Orchestrator - Dependency Installation Script
# Version: 3.0.0-fashion
# Updated: 2025-11-21
#
# Installs all SDKs and dependencies for The Skyy Rose Collection Fashion Orchestrator
# Per Truth Protocol Rule #1 - All sources verified

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}║  DevSkyy Fashion Orchestrator - Dependency Installation       ║${NC}"
echo -e "${BLUE}║  The Skyy Rose Collection                                     ║${NC}"
echo -e "${BLUE}║                                                                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}→${NC} Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}✗ Python 3.11+ required. Found: $python_version${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python $python_version"

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}→${NC} Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
    echo -e "${GREEN}✓${NC} Virtual environment created"
fi

# Activate virtual environment
echo -e "${YELLOW}→${NC} Activating virtual environment..."
source "$PROJECT_DIR/venv/bin/activate"
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Upgrade pip, setuptools, wheel
echo -e "${YELLOW}→${NC} Upgrading pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel --quiet
echo -e "${GREEN}✓${NC} Build tools upgraded"

# Function to install package with retry
install_package() {
    local package=$1
    local max_retries=3
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        if pip install "$package" --quiet; then
            return 0
        fi
        retry_count=$((retry_count + 1))
        echo -e "${YELLOW}  Retry $retry_count/$max_retries...${NC}"
        sleep 2
    done

    return 1
}

# Install PyTorch first (with CUDA support if available)
echo ""
echo -e "${BLUE}▶ Step 1/7: Installing PyTorch${NC}"
echo -e "${YELLOW}→${NC} Detecting CUDA availability..."

if command -v nvidia-smi &> /dev/null; then
    cuda_version=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}' || echo "none")
    echo -e "${GREEN}✓${NC} CUDA detected: $cuda_version"
    echo -e "${YELLOW}→${NC} Installing PyTorch with CUDA 12.1 support..."
    pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
        --index-url https://download.pytorch.org/whl/cu121 --quiet || {
        echo -e "${RED}✗ PyTorch installation failed${NC}"
        exit 1
    }
else
    echo -e "${YELLOW}⚠${NC} CUDA not detected, installing CPU-only PyTorch..."
    pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --quiet || {
        echo -e "${RED}✗ PyTorch installation failed${NC}"
        exit 1
    }
fi
echo -e "${GREEN}✓${NC} PyTorch installed"

# Install AI Model SDKs
echo ""
echo -e "${BLUE}▶ Step 2/7: Installing AI Model SDKs${NC}"

packages=(
    "anthropic>=0.69.0"
    "openai>=2.7.2"
    "stability-sdk>=0.8.4"
    "replicate>=0.25.0"
)

for package in "${packages[@]}"; do
    package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
    echo -e "${YELLOW}→${NC} Installing $package_name..."
    if install_package "$package"; then
        echo -e "${GREEN}✓${NC} $package_name installed"
    else
        echo -e "${RED}✗${NC} Failed to install $package_name"
        exit 1
    fi
done

# Install Hugging Face libraries
echo ""
echo -e "${BLUE}▶ Step 3/7: Installing Hugging Face Libraries${NC}"

hf_packages=(
    "transformers>=4.57.1,<5.0.0"
    "diffusers>=0.27.0"
    "huggingface-hub>=0.23.0"
    "accelerate>=0.28.0"
    "peft>=0.10.0"
    "datasets>=2.18.0"
    "safetensors>=0.4.0"
)

for package in "${hf_packages[@]}"; do
    package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
    echo -e "${YELLOW}→${NC} Installing $package_name..."
    if install_package "$package"; then
        echo -e "${GREEN}✓${NC} $package_name installed"
    else
        echo -e "${RED}✗${NC} Failed to install $package_name"
        exit 1
    fi
done

# Install 3D processing libraries
echo ""
echo -e "${BLUE}▶ Step 4/7: Installing 3D Processing Libraries${NC}"

three_d_packages=(
    "trimesh>=4.4.0"
    "PyMCubes>=0.1.4"
    "open3d>=0.18.0"
    "pygltflib>=1.16.0"
    "PyWavefront>=1.3.3"
)

for package in "${three_d_packages[@]}"; do
    package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
    echo -e "${YELLOW}→${NC} Installing $package_name..."
    if install_package "$package"; then
        echo -e "${GREEN}✓${NC} $package_name installed"
    else
        echo -e "${YELLOW}⚠${NC} $package_name failed (optional, continuing...)"
    fi
done

# Install image processing libraries
echo ""
echo -e "${BLUE}▶ Step 5/7: Installing Image Processing Libraries${NC}"

image_packages=(
    "Pillow>=10.2.0"
    "opencv-python>=4.9.0"
    "scikit-image>=0.22.0"
    "albumentations>=1.4.0"
    "controlnet-aux>=0.0.7"
    "mediapipe>=0.10.0"
)

for package in "${image_packages[@]}"; do
    package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
    echo -e "${YELLOW}→${NC} Installing $package_name..."
    if install_package "$package"; then
        echo -e "${GREEN}✓${NC} $package_name installed"
    else
        echo -e "${YELLOW}⚠${NC} $package_name failed (optional, continuing...)"
    fi
done

# Install remaining dependencies from requirements-fashion.txt
echo ""
echo -e "${BLUE}▶ Step 6/7: Installing Remaining Dependencies${NC}"
echo -e "${YELLOW}→${NC} Installing from requirements-fashion.txt..."

if [ -f "$PROJECT_DIR/requirements-fashion.txt" ]; then
    pip install -r "$PROJECT_DIR/requirements-fashion.txt" --quiet || {
        echo -e "${YELLOW}⚠${NC} Some packages from requirements-fashion.txt failed (continuing...)"
    }
    echo -e "${GREEN}✓${NC} Base requirements installed"
else
    echo -e "${RED}✗${NC} requirements-fashion.txt not found"
    exit 1
fi

# Install development dependencies
echo ""
echo -e "${BLUE}▶ Step 7/7: Installing Development Tools${NC}"

dev_packages=(
    "pytest>=8.0.0"
    "pytest-asyncio>=0.23.0"
    "pytest-cov>=4.1.0"
    "black>=24.10.0"
    "ruff>=0.8.0"
    "mypy>=1.14.0"
)

for package in "${dev_packages[@]}"; do
    package_name=$(echo "$package" | cut -d'>' -f1 | cut -d'=' -f1)
    echo -e "${YELLOW}→${NC} Installing $package_name..."
    if install_package "$package"; then
        echo -e "${GREEN}✓${NC} $package_name installed"
    else
        echo -e "${YELLOW}⚠${NC} $package_name failed (optional, continuing...)"
    fi
done

# Verify installations
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Verifying Installations${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

python3 << 'EOF'
import sys

def verify_import(module_name, package_name=None):
    """Verify a module can be imported"""
    try:
        __import__(module_name)
        print(f"  ✓ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"  ✗ {package_name or module_name}: {e}")
        return False

print("\n🤖 AI Model SDKs:")
verify_import("anthropic", "Anthropic (Claude)")
verify_import("openai", "OpenAI (GPT-4, Shap-E)")
verify_import("stability_sdk", "Stability AI (SDXL)")
verify_import("replicate", "Replicate (LoRA)")

print("\n🤗 Hugging Face:")
verify_import("transformers", "Transformers")
verify_import("diffusers", "Diffusers (IDM-VTON)")
verify_import("accelerate", "Accelerate")
verify_import("peft", "PEFT (LoRA)")

print("\n🎨 3D Processing:")
verify_import("trimesh", "Trimesh")
verify_import("open3d", "Open3D")
verify_import("pygltflib", "PyGLTF")

print("\n🖼️ Image Processing:")
verify_import("PIL", "Pillow")
verify_import("cv2", "OpenCV")
verify_import("skimage", "Scikit-image")

print("\n🔥 ML Frameworks:")
verify_import("torch", "PyTorch")
verify_import("torchvision", "TorchVision")

# Check PyTorch CUDA
try:
    import torch
    if torch.cuda.is_available():
        print(f"  ✓ CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print(f"  ⚠ CUDA not available (CPU-only mode)")
except Exception as e:
    print(f"  ✗ PyTorch CUDA check failed: {e}")

print("\n📦 Core Libraries:")
verify_import("fastapi", "FastAPI")
verify_import("pydantic", "Pydantic")
verify_import("sqlalchemy", "SQLAlchemy")

print("\n🔒 Security:")
verify_import("cryptography", "Cryptography")
verify_import("jwt", "PyJWT")
verify_import("argon2", "Argon2")

EOF

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Installation Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Activate venv: ${BLUE}source venv/bin/activate${NC}"
echo -e "  2. Set API keys in ${BLUE}.env${NC} file:"
echo -e "     - ANTHROPIC_API_KEY=your_key_here"
echo -e "     - OPENAI_API_KEY=your_key_here"
echo -e "     - STABILITY_API_KEY=your_key_here"
echo -e "     - REPLICATE_API_TOKEN=your_token_here"
echo -e "     - HUGGINGFACE_TOKEN=your_token_here"
echo -e "  3. Run tests: ${BLUE}pytest tests/${NC}"
echo -e "  4. Start orchestrator: ${BLUE}python agent/fashion_orchestrator.py${NC}"
echo ""
echo -e "${YELLOW}Optional:${NC}"
echo -e "  - For GPU acceleration: Ensure CUDA 12.1+ is installed"
echo -e "  - For PyTorch3D: Install from conda or build from source"
echo -e "  - For USDZ support: Install pxr-usd package"
echo ""
echo -e "${GREEN}Ready for The Skyy Rose Collection! 👗✨${NC}"
