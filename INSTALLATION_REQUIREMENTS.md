# SkyyRose Installation & Dependency Requirements

## Quick Install

```bash
# Core installation with all dependencies
pip install -e .

# Or development install (includes test tools)
pip install -e ".[dev]"

# Or full installation (all optional dependencies)
pip install -e ".[all]"
```

## Dependency Overview

### Core Dependencies
- **FastAPI** (0.109+): Web framework
- **Pydantic** (2.5+): Data validation **[CRITICAL: v2.x required]**
- **SQLAlchemy** (2.0+): ORM
- **httpx/aiohttp** (3.9+): Async HTTP clients
- **Redis** (5.0+): Caching and queues

### For 3D Asset Pipeline
- **Pillow** (PIL, 10.0+): Image processing for background removal, contrast enhancement
- **OpenCV** (4.8+): Advanced image optimization
- **numpy** (1.26+): Numerical operations for image processing

### For Deployment & Testing Scripts
- **Selenium** (4.15+): Core Web Vitals measurement via Lighthouse
- **Playwright** (1.40+): Browser automation for functionality testing
- **aiohttp** (3.9+): Async HTTP for API calls

### For 3D Generation Services (External)
- **orchestration/huggingface_3d_client.py**: Requires HUGGINGFACE_API_KEY (free tier available)
- **agents/tripo_agent.py**: Requires TRIPO_API_KEY (paid service, ~$0.50-1.00 per model)

### LLM Provider SDKs
- **OpenAI** (1.6+): GPT-4, GPT-4 Vision, DALL-E
- **Anthropic** (0.75+): Claude models
- **Google** (genai 1.50+): Gemini, Imagen, Veo
- **Cohere** (5.20+): Command models
- **Mistral** (1.9+): Mistral models
- **Groq** (0.37+): Fast inference models

### WordPress Integration
- **woocommerce** (3.0+): WooCommerce REST API client
- **mcp** (1.23.0+): Model Context Protocol server

## Installation Troubleshooting

### Issue: Pydantic Version Mismatch

**Error**: `PydanticDeprecatedSince20`, `PydanticUserError`

**Solution**: Ensure Pydantic v2.x is installed
```bash
pip install --upgrade pydantic>=2.5
pip list | grep pydantic
# Should show: pydantic 2.5+ (not 1.x)
```

### Issue: PIL/Pillow Not Found

**Error**: `ModuleNotFoundError: No module named 'PIL'`

**Solution**: Install Pillow
```bash
pip install Pillow>=10.0
# Test
python3 -c "from PIL import Image; print('✓ Pillow working')"
```

### Issue: OpenCV Not Found

**Error**: `ModuleNotFoundError: No module named 'cv2'`

**Solution**: Install OpenCV
```bash
pip install opencv-python>=4.8
# Test
python3 -c "import cv2; print(f'✓ OpenCV {cv2.__version__} working')"
```

### Issue: Selenium/Playwright Not Available

**Error**: `ModuleNotFoundError: No module named 'selenium'`

**Solution**: Install browser automation tools
```bash
# For Selenium (Chromium-based)
pip install selenium>=4.15

# For Playwright (alternative)
pip install playwright>=1.40
python3 -m playwright install chromium

# Test
python3 -c "from selenium import webdriver; print('✓ Selenium working')"
```

## Environment Setup

### 1. Create .env File

```bash
cp .env.example .env
```

### 2. Configure Required Variables

```bash
# WordPress (required)
WORDPRESS_URL=http://localhost:8882
WORDPRESS_USER=admin
WORDPRESS_PASSWORD=your-password

# 3D Generation APIs (required for full pipeline)
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx
TRIPO_API_KEY=tripo_xxxxxxxxxxxxx

# LLM Providers (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional but recommended
WOOCOMMERCE_KEY=ck_xxx
WOOCOMMERCE_SECRET=cs_xxx
KLAVIYO_API_KEY=your-key
```

### 3. Verify Installation

```bash
python3 << 'EOF'
import sys

print("Verifying installation...\n")

checks = [
    ("FastAPI", lambda: __import__('fastapi')),
    ("Pydantic v2", lambda: __import__('pydantic') and __import__('pydantic').VERSION.startswith('2')),
    ("SQLAlchemy", lambda: __import__('sqlalchemy')),
    ("aiohttp", lambda: __import__('aiohttp')),
    ("Pillow", lambda: __import__('PIL')),
    ("OpenCV", lambda: __import__('cv2')),
    ("httpx", lambda: __import__('httpx')),
]

failed = []
for name, check in checks:
    try:
        check()
        print(f"✓ {name}")
    except Exception as e:
        print(f"✗ {name}: {e}")
        failed.append(name)

if failed:
    print(f"\n⚠️  Missing: {', '.join(failed)}")
    print(f"Run: pip install -e .[dev]")
    sys.exit(1)
else:
    print(f"\n✅ All core dependencies installed!")
    sys.exit(0)
EOF
```

## Next Steps

1. **Install dependencies**: `pip install -e .`
2. **Verify installation**: Run the verification script above
3. **Configure .env**: Set WORDPRESS_URL, API keys, etc.
4. **Test connection**: Run deployment with `--verbose` flag
5. **Deploy**: Execute `python3 scripts/deploy_skyyrose_site.py --all`

## Minimal vs Full Installation

### Minimal (Core Only)
```bash
pip install -e .
```
**Includes**: FastAPI, Pydantic, SQLAlchemy, basic HTTP clients
**Missing**: 3D generation, testing tools
**Size**: ~200MB

### Development (Recommended)
```bash
pip install -e ".[dev]"
```
**Includes**: Core + testing, linting, formatting tools
**Adds**: Selenium, Playwright, pytest, mypy, ruff
**Size**: ~500MB

### Full (Everything)
```bash
pip install -e ".[all]"
```
**Includes**: Core + dev + ML libraries + LangGraph
**Adds**: numpy, pandas, scikit-learn, langgraph
**Size**: ~800MB+

## System Requirements

### Operating Systems
- ✅ macOS (Intel & Apple Silicon)
- ✅ Linux (Ubuntu 20.04+, Debian 11+)
- ✅ Windows (WSL2 or native)

### Python Version
- Minimum: Python 3.11
- Recommended: Python 3.12 (better performance)

### RAM
- Minimum: 2GB
- Recommended: 4GB+
- For 3D generation: 4GB+ (image processing)

### Disk Space
- Installation: 500MB-1GB
- Runtime (assets): 500MB-2GB
- Generated models: 50-200MB per collection

### Network
- Stable internet required
- API calls to: WordPress, HuggingFace, Tripo3D, LLM providers

## Verification Commands

```bash
# Check Python version
python3 --version
# Expected: Python 3.11+ or 3.12+

# Check pip is available
pip --version

# Install with verbose output
pip install -e . -v 2>&1 | grep -i "successfully"

# Check Pydantic version specifically
python3 -c "from pydantic import VERSION; print(f'Pydantic {VERSION}')"

# List installed packages
pip list | grep -E "fastapi|pydantic|sqlalchemy|aiohttp|pillow|opencv"

# Run full diagnostic
python3 << 'EOF'
import sys
import platform

print(f"Platform: {platform.platform()}")
print(f"Python: {sys.version}")
print(f"Pip: {__import__('pip').__version__}")

from pydantic import VERSION
print(f"Pydantic: {VERSION}")

import fastapi
print(f"FastAPI: {fastapi.__version__}")
EOF
```

---

## Dependency Security

### Security Checks

```bash
# Check for vulnerabilities
pip-audit

# Security audit
bandit -r .

# Dependency check
pip list --outdated
```

### Keeping Dependencies Updated

```bash
# Update all
pip install --upgrade -e .

# Update specific
pip install --upgrade pydantic fastapi

# Pin to specific versions (production)
pip freeze > requirements-lock.txt
pip install -r requirements-lock.txt
```

---

**Version**: 1.0.0  
**Last Updated**: December 25, 2025
