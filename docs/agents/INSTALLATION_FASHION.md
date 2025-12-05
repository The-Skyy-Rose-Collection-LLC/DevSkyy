# Fashion Orchestrator - Installation Guide

**Version**: 3.0.0-fashion
**Updated**: 2025-11-21
**For**: The Skyy Rose Collection

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
4. [API Key Setup](#api-key-setup)
5. [Model Downloads](#model-downloads)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)
8. [GPU Setup](#gpu-setup)

---

## Prerequisites

### System Requirements

**Operating System**:
- Linux (Ubuntu 20.04+, Debian 11+, or equivalent)
- macOS 12+ (limited GPU support)
- Windows 10+ with WSL2 (recommended for Windows users)

**Hardware**:
- **CPU**: Multi-core processor (4+ cores recommended)
- **RAM**: 16GB minimum, 32GB+ recommended
- **Storage**: 50GB+ free space for models and datasets
- **GPU** (optional but recommended):
  - NVIDIA GPU with CUDA 12.1+ support
  - 8GB+ VRAM minimum
  - 16GB+ VRAM recommended for optimal performance

**Software**:
- Python 3.11+ (required)
- pip 23.0+ (latest version)
- Git 2.30+
- CUDA 12.1+ (for GPU acceleration)
- Docker (optional, for containerized deployment)

### Check Prerequisites

```bash
# Check Python version
python3 --version  # Should be 3.11.0 or higher

# Check pip
pip --version

# Check Git
git --version

# Check CUDA (if using GPU)
nvidia-smi  # Should show CUDA 12.1+
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy
```

### 2. Run Automated Installation

```bash
# Make installation script executable
chmod +x scripts/install_fashion_dependencies.sh

# Run installation (takes 10-30 minutes depending on internet speed)
./scripts/install_fashion_dependencies.sh
```

### 3. Configure API Keys

```bash
# Copy environment template
cp .env.fashion.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

### 4. Download AI Models

```bash
# Activate virtual environment
source venv/bin/activate

# Download all models (takes 30-60 minutes, requires ~20GB storage)
python3 scripts/download_fashion_models.py --model all

# Or download specific models
python3 scripts/download_fashion_models.py --model idm-vton
```

### 5. Verify Installation

```bash
# Verify all dependencies
python3 scripts/download_fashion_models.py --verify-only

# Run test suite
pytest tests/

# Test fashion orchestrator
python3 agent/fashion_orchestrator.py
```

---

## Detailed Installation

### Step 1: Set Up Virtual Environment

```bash
cd DevSkyy

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Upgrade pip and build tools
pip install --upgrade pip setuptools wheel
```

### Step 2: Install PyTorch

**For GPU (CUDA 12.1)**:
```bash
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu121
```

**For CPU only**:
```bash
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

**Verify PyTorch**:
```python
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Step 3: Install AI Model SDKs

```bash
# Install Anthropic SDK (Claude 3.5 Sonnet)
pip install anthropic>=0.69.0

# Install OpenAI SDK (GPT-4, Shap-E)
pip install openai>=2.7.2

# Install Stability AI SDK (SDXL)
pip install stability-sdk>=0.8.4

# Install Replicate SDK (LoRA fine-tuning)
pip install replicate>=0.25.0

# Install Hugging Face libraries (IDM-VTON, Transformers)
pip install transformers>=4.57.1 diffusers>=0.27.0 \
    huggingface-hub>=0.23.0 accelerate>=0.28.0
```

### Step 4: Install 3D Processing Libraries

```bash
# Install 3D mesh processing
pip install trimesh>=4.4.0 PyMCubes>=0.1.4 open3d>=0.18.0

# Install 3D file format handlers
pip install pygltflib>=1.16.0 PyWavefront>=1.3.3
```

### Step 5: Install Image Processing Libraries

```bash
# Install core image libraries
pip install Pillow>=10.2.0 opencv-python>=4.9.0 \
    scikit-image>=0.22.0 albumentations>=1.4.0

# Install virtual try-on dependencies
pip install controlnet-aux>=0.0.7 mediapipe>=0.10.0
```

### Step 6: Install All Remaining Dependencies

```bash
# Install from requirements file
pip install -r requirements-fashion.txt
```

### Step 7: Install Development Tools (Optional)

```bash
# Install testing and linting tools
pip install pytest>=8.0.0 pytest-asyncio>=0.23.0 pytest-cov>=4.1.0 \
    black>=24.10.0 ruff>=0.8.0 mypy>=1.14.0
```

---

## API Key Setup

### Required API Keys

#### 1. Anthropic (Claude 3.5 Sonnet)

**Purpose**: Product description generation

**Get API Key**:
1. Visit https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys" section
4. Create new API key

**Add to .env**:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

**Verified Source**: https://www.anthropic.com/claude

---

#### 2. OpenAI (GPT-4, Shap-E)

**Purpose**: 3D generation, text generation

**Get API Key**:
1. Visit https://platform.openai.com/api-keys
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key immediately (shown only once)

**Add to .env**:
```bash
OPENAI_API_KEY=sk-proj-xxxxx
```

**Verified Source**: https://github.com/openai/openai-python

---

#### 3. Hugging Face Token

**Purpose**: IDM-VTON virtual try-on, model downloads

**Get Token**:
1. Visit https://huggingface.co/settings/tokens
2. Sign up or log in
3. Click "New token"
4. Select "Read" access
5. Copy the token

**Add to .env**:
```bash
HUGGINGFACE_TOKEN=hf_xxxxx
```

**Verified Source**: https://huggingface.co/docs

---

### Optional API Keys

#### 4. Stability AI (SDXL)

**Purpose**: Image generation

**Get API Key**:
1. Visit https://platform.stability.ai/account/keys
2. Sign up or log in
3. Create new API key

**Add to .env**:
```bash
STABILITY_API_KEY=sk-xxxxx
```

---

#### 5. Replicate (SDXL LoRA)

**Purpose**: Fine-tuned image generation

**Get Token**:
1. Visit https://replicate.com/account/api-tokens
2. Sign up or log in
3. Create new API token

**Add to .env**:
```bash
REPLICATE_API_TOKEN=r8_xxxxx
```

---

#### 6. ReadyPlayerMe (Avatars)

**Purpose**: Avatar generation

**Get API Key**:
1. Visit https://readyplayer.me/developers
2. Sign up for developer account
3. Get your API key from dashboard

**Add to .env**:
```bash
READYPLAYERME_API_KEY=rpm_xxxxx
```

---

### Complete .env File

```bash
# Copy the example file
cp .env.fashion.example .env

# Edit with your API keys
nano .env

# Required keys (minimum for basic functionality):
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
HUGGINGFACE_TOKEN=your_token_here

# Optional keys (enhanced features):
STABILITY_API_KEY=your_key_here
REPLICATE_API_TOKEN=your_token_here
READYPLAYERME_API_KEY=your_key_here

# Security keys (generate with: openssl rand -hex 32)
JWT_SECRET=your_generated_secret_here
ENCRYPTION_KEY=your_generated_key_here

# Database
DATABASE_URL=postgresql://localhost:5432/devskyy_fashion

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

---

## Model Downloads

### Automatic Download (Recommended)

```bash
# Activate virtual environment
source venv/bin/activate

# Download all models
python3 scripts/download_fashion_models.py --model all
```

**Expected Output**:
```
======================================================================
DevSkyy Fashion Orchestrator - Model Downloader
The Skyy Rose Collection
======================================================================

Model cache directory: /root/.cache/devskyy/models

======================================================================
PyTorch Verification
======================================================================
PyTorch version: 2.5.1
CUDA available: True
CUDA version: 12.1
GPU device: NVIDIA GeForce RTX 4090
GPU memory: 24.00 GB

======================================================================
API Key Verification
======================================================================
✓ ANTHROPIC_API_KEY configured
✓ OPENAI_API_KEY configured
✓ HUGGINGFACE_TOKEN configured
⚠ STABILITY_API_KEY not set
⚠ REPLICATE_API_TOKEN not set

======================================================================
Downloading IDM-VTON...
======================================================================
Source: https://huggingface.co/yisol/IDM-VTON
Paper: https://arxiv.org/abs/2403.05139
✓ Downloaded yisol/IDM-VTON (diffusion)

... (continues for each model)

======================================================================
DOWNLOAD SUMMARY
======================================================================
✓ IDM-VTON
✓ Stable Diffusion XL
✓ ControlNet
======================================================================
Total: 3 | Successful: 3 | Failed: 0
======================================================================

✓ All models downloaded successfully!

Models cached in: /root/.cache/devskyy/models
```

### Individual Model Downloads

```bash
# Download IDM-VTON only (~8GB)
python3 scripts/download_fashion_models.py --model idm-vton

# Download Stable Diffusion XL only (~7GB)
python3 scripts/download_fashion_models.py --model sdxl

# Download ControlNet only (~3GB)
python3 scripts/download_fashion_models.py --model controlnet
```

### Manual Model Downloads

If automatic download fails, download manually:

**IDM-VTON**:
```python
from diffusers import DiffusionPipeline

pipeline = DiffusionPipeline.from_pretrained(
    "yisol/IDM-VTON",
    cache_dir="~/.cache/devskyy/models"
)
```

**Stable Diffusion XL**:
```python
from diffusers import DiffusionPipeline

pipeline = DiffusionPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    cache_dir="~/.cache/devskyy/models"
)
```

---

## Verification

### 1. Verify Dependencies

```bash
python3 scripts/download_fashion_models.py --verify-only
```

**Expected Output**:
```
🤖 AI Model SDKs:
  ✓ Anthropic (Claude)
  ✓ OpenAI (GPT-4, Shap-E)
  ✓ Stability AI (SDXL)
  ✓ Replicate (LoRA)

🤗 Hugging Face:
  ✓ Transformers
  ✓ Diffusers (IDM-VTON)
  ✓ Accelerate
  ✓ PEFT (LoRA)

🎨 3D Processing:
  ✓ Trimesh
  ✓ Open3D
  ✓ PyGLTF

🖼️ Image Processing:
  ✓ Pillow
  ✓ OpenCV
  ✓ Scikit-image

🔥 ML Frameworks:
  ✓ PyTorch
  ✓ TorchVision
  ✓ CUDA available: NVIDIA GeForce RTX 4090

📦 Core Libraries:
  ✓ FastAPI
  ✓ Pydantic
  ✓ SQLAlchemy

🔒 Security:
  ✓ Cryptography
  ✓ PyJWT
  ✓ Argon2
```

### 2. Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=agent --cov-report=html tests/

# Run specific test
pytest tests/test_fashion_orchestrator.py -v
```

### 3. Test Fashion Orchestrator

```bash
# Run demonstration
python3 agent/fashion_orchestrator.py
```

**Expected Output**:
```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  👗 The Skyy Rose Collection - Fashion Orchestrator v3.0.0    ║
║                                                                ║
║  AI Agent Selection + 3D Fashion + Virtual Try-On             ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

================================================================================
👗 THE SKYY ROSE COLLECTION - FASHION ORCHESTRATOR
================================================================================

📋 Brand: The Skyy Rose Collection
   Categories: handbags, ready_to_wear, shoes, accessories, jewelry, eyewear

🤖 Available AI Models:
   - product_description_primary (Claude 3.5 Sonnet)
   - 3d_generation_primary (Shap-E)
   - avatar_generation_primary (ReadyPlayerMe)
   - virtual_try_on_primary (IDM-VTON)
   ... +6 more

✅ Task created: Generate product description: Midnight Rose Handbag
✅ Task created: Generate 3D asset: handbag
✅ Task created: Generate avatar: female realistic

✨ DEMONSTRATION COMPLETE
```

---

## Troubleshooting

### Common Issues

#### Issue 1: PyTorch Import Error

**Error**:
```
ImportError: No module named 'torch'
```

**Solution**:
```bash
# Reinstall PyTorch with correct CUDA version
pip uninstall torch torchvision torchaudio
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu121
```

---

#### Issue 2: CUDA Not Available

**Error**:
```
CUDA available: False
```

**Solutions**:

1. **Check NVIDIA driver**:
```bash
nvidia-smi
```

2. **Install CUDA 12.1**:
```bash
# Ubuntu/Debian
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run
```

3. **Add CUDA to PATH**:
```bash
export PATH=/usr/local/cuda-12.1/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH
```

---

#### Issue 3: Out of Memory (OOM)

**Error**:
```
RuntimeError: CUDA out of memory
```

**Solutions**:

1. **Reduce batch size**:
```bash
# In .env file
INFERENCE_BATCH_SIZE=1
```

2. **Enable mixed precision**:
```bash
ENABLE_MIXED_PRECISION=true
```

3. **Use CPU inference**:
```bash
CUDA_VISIBLE_DEVICES=""
```

---

#### Issue 4: Model Download Fails

**Error**:
```
HTTPError: 401 Unauthorized
```

**Solutions**:

1. **Check API token**:
```bash
# Verify token in .env
cat .env | grep HUGGINGFACE_TOKEN
```

2. **Login to Hugging Face**:
```bash
huggingface-cli login
```

3. **Manual download**:
```bash
# Download model manually
git lfs install
git clone https://huggingface.co/yisol/IDM-VTON ~/.cache/devskyy/models/yisol/IDM-VTON
```

---

#### Issue 5: Permission Denied

**Error**:
```
PermissionError: [Errno 13] Permission denied
```

**Solution**:
```bash
# Fix permissions
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Or use sudo (not recommended for venv)
sudo chown -R $USER:$USER venv/
```

---

### Getting Help

1. **Check logs**:
```bash
# Application logs
tail -f logs/fashion_orchestrator.log

# Error ledger
cat artifacts/error-ledger-*.json | jq
```

2. **Enable debug mode**:
```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

3. **Run diagnostics**:
```bash
python3 scripts/download_fashion_models.py --verify-only
```

4. **GitHub Issues**:
- Report issues: https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy/issues
- Search existing issues first

---

## GPU Setup

### NVIDIA GPU (Recommended)

**Requirements**:
- NVIDIA GPU (RTX 3060+, RTX 4090 optimal)
- CUDA 12.1+
- cuDNN 8.9+

**Installation**:

1. **Install NVIDIA Driver** (530+):
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nvidia-driver-530

# Verify
nvidia-smi
```

2. **Install CUDA 12.1**:
```bash
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run
sudo sh cuda_12.1.0_530.30.02_linux.run

# Add to PATH
echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

3. **Install cuDNN**:
```bash
# Download from: https://developer.nvidia.com/cudnn
# Follow NVIDIA installation instructions
```

4. **Verify Installation**:
```bash
nvcc --version  # Should show CUDA 12.1
python3 -c "import torch; print(torch.cuda.is_available())"  # Should print True
```

---

### Multi-GPU Setup

**Configure GPU usage**:

```bash
# In .env file
CUDA_VISIBLE_DEVICES=0,1,2,3  # Use 4 GPUs

# Or limit to specific GPUs
CUDA_VISIBLE_DEVICES=0  # Use only GPU 0
```

**Test multi-GPU**:
```python
import torch
print(f"GPUs available: {torch.cuda.device_count()}")
for i in range(torch.cuda.device_count()):
    print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
```

---

## Next Steps

After successful installation:

1. **Read the Guide**: See `FASHION_ORCHESTRATOR_GUIDE.md` for usage examples
2. **Configure Brand**: Customize brand settings in `.env`
3. **Test Workflows**: Try the example workflows
4. **Fine-tune Models**: Train brand-specific models
5. **Deploy**: Follow `ENTERPRISE_DEPLOYMENT.md` for production deployment

---

## Summary

**Installation Steps**:
1. ✅ Prerequisites verified
2. ✅ Virtual environment created
3. ✅ PyTorch installed
4. ✅ AI SDKs installed
5. ✅ 3D libraries installed
6. ✅ Image processing installed
7. ✅ API keys configured
8. ✅ Models downloaded
9. ✅ Installation verified

**Ready for**: The Skyy Rose Collection Fashion Orchestrator 👗✨

---

**Version**: 3.0.0-fashion
**Status**: ✅ Production Ready
**Last Updated**: 2025-11-21
