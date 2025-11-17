# Google Gemini Setup Guide for DevSkyy

Complete guide to enable Google Gemini for vision/image analysis and UI/design generation.

## 🎯 What You'll Get

Once Gemini is working, you'll unlock:
- ✅ **Vision/Image Analysis**: Analyze fashion products, UI designs, brand images
- ✅ **UI Component Generation**: Generate React components with visual understanding
- ✅ **Design Review**: Automated UI/UX analysis and feedback
- ✅ **Multimodal Content**: Combine text and image analysis for product descriptions
- ✅ **Faster Execution**: Gemini is cheaper and faster than Claude for many tasks

---

## 🔍 The Problem

The current environment has a conflict between system packages and pip packages, specifically with the `cryptography` library that Google's SDK depends on.

**Error**: `ModuleNotFoundError: No module named '_cffi_backend'`

---

## ✅ Solution 1: Virtual Environment (RECOMMENDED)

**Time**: 5 minutes
**Difficulty**: Easy
**Best for**: Development and testing

### Quick Setup

```bash
cd /home/user/DevSkyy

# Run the automated setup script
./setup_clean_env.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install anthropic openai google-generativeai python-dotenv transformers torch
```

### Usage

```bash
# Activate environment
source venv/bin/activate

# Run DevSkyy scripts
python test_multi_model.py

# Run any DevSkyy agent
python main.py

# Deactivate when done
deactivate
```

### Pros & Cons

✅ **Pros:**
- Quick to set up
- Isolated from system packages
- Easy to delete and recreate
- No Docker required

❌ **Cons:**
- Must activate/deactivate manually
- Separate from system Python

---

## ✅ Solution 2: Docker (PRODUCTION-READY)

**Time**: 10 minutes
**Difficulty**: Medium
**Best for**: Production deployment and consistency

### Quick Setup

```bash
cd /home/user/DevSkyy

# Build the container
docker-compose -f docker-compose.multimodel.yml build

# Run DevSkyy
docker-compose -f docker-compose.multimodel.yml up -d

# View logs
docker-compose -f docker-compose.multimodel.yml logs -f

# Stop
docker-compose -f docker-compose.multimodel.yml down
```

### Testing Inside Docker

```bash
# Run test script in container
docker-compose -f docker-compose.multimodel.yml exec devskyy-multimodel python test_multi_model.py

# Interactive shell
docker-compose -f docker-compose.multimodel.yml exec devskyy-multimodel bash
```

### Pros & Cons

✅ **Pros:**
- Production-ready
- Completely isolated
- Reproducible across systems
- Easy deployment
- No conflicts ever

❌ **Cons:**
- Requires Docker installed
- Slightly larger footprint
- More complex for beginners

---

## ✅ Solution 3: Quick System Fix

**Time**: 2 minutes
**Difficulty**: Easy
**Best for**: Quick testing only

### Steps

```bash
# Install system cryptography package
sudo apt-get update
sudo apt-get install -y python3-cffi libffi-dev

# Reinstall google-generativeai
pip uninstall -y google-generativeai
pip install --no-cache-dir google-generativeai
```

### Pros & Cons

✅ **Pros:**
- Very quick
- Works immediately
- No environment switching

⚠️ **Cons:**
- May have side effects
- Not as clean
- Could break other packages

---

## 🧪 Testing Gemini After Setup

Run this test to verify Gemini is working:

```python
from dotenv import load_dotenv
import os
load_dotenv()

import google.generativeai as genai

# Configure
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Test text generation
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content("Say 'Gemini ready!' in 3 words")
print(f"✅ Gemini: {response.text}")

# Test vision (with an image)
# vision_model = genai.GenerativeModel('gemini-pro-vision')
# response = vision_model.generate_content(["What's in this image?", image])
```

---

## 🎯 Recommended Approach by Use Case

| Use Case | Recommended Solution | Why |
|----------|---------------------|-----|
| **Local Development** | Virtual Environment | Fast setup, easy switching |
| **Production Deployment** | Docker | Reliable, reproducible |
| **Quick Testing** | System Fix | Immediate results |
| **CI/CD Pipeline** | Docker | Consistent environment |
| **Multiple Projects** | Virtual Environment | Project isolation |

---

## 📊 What Works Where

| Feature | Current Env | Virtual Env | Docker |
|---------|-------------|-------------|--------|
| Claude Sonnet 4.5 | ✅ | ✅ | ✅ |
| OpenAI GPT | ⚠️ (needs billing) | ⚠️ | ⚠️ |
| Google Gemini | ❌ | ✅ | ✅ |
| Hugging Face | ✅ | ✅ | ✅ |

---

## 🚀 After Setup - Multi-Model Capabilities

Once Gemini is enabled, you can use these powerful features:

### 1. Fashion Image Analysis

```python
import asyncio
from skills.google_gemini_integration import GeminiContentAgent, GeminiClient
from skills.brand_intelligence import BrandIntelligenceManager

async def analyze_fashion_product():
    brand_manager = BrandIntelligenceManager()
    gemini = GeminiClient()
    content_agent = GeminiContentAgent(brand_manager, gemini)

    # Analyze product image
    analysis = await content_agent.analyze_fashion_image(
        "products/dress.jpg",
        analysis_type="comprehensive"
    )
    return analysis

# Run the async function
asyncio.run(analyze_fashion_product())
```

### 2. UI Component Generation

```python
import asyncio
from skills.google_gemini_integration import GeminiFrontendAgent, GeminiClient
from skills.brand_intelligence import BrandIntelligenceManager

async def generate_product_card():
    brand_manager = BrandIntelligenceManager()
    gemini = GeminiClient()
    frontend = GeminiFrontendAgent(brand_manager, gemini)

    # Generate React component
    component = await frontend.generate_ui_component(
        component_type="ProductCard",
        requirements={"features": ["image", "price", "add_to_cart"]}
    )
    return component

# Run the async function
asyncio.run(generate_product_card())
```

### 3. Intelligent Duo Routing

```python
from skills.intelligent_duo_routing import IntelligentDuoRouter, TaskCapability

router = IntelligentDuoRouter()

# Automatically selects best duo (likely Gemini + Claude)
primary, secondary, reasoning = router.select_best_duo(
    task_description="Generate product card with image analysis",
    required_capabilities=[
        TaskCapability.IMAGE_ANALYSIS,
        TaskCapability.UI_DESIGN
    ],
    available_models=["claude-sonnet-4-5", "gemini-pro"]
)

# Result: Gemini (image analysis) → Claude (code generation)
```

---

## 💡 Quick Decision Tree

```
Do you need Gemini right now?
│
├─ No → Keep using Claude (you have 90% functionality)
│
└─ Yes → Which scenario?
    │
    ├─ Just testing → Quick System Fix
    │
    ├─ Development → Virtual Environment
    │
    └─ Production → Docker
```

---

## 🆘 Troubleshooting

### Still getting import errors?

```bash
# In virtual environment or Docker:
pip list | grep -E "(google|cryptography)"

# Should show:
# google-generativeai  x.x.x
# cryptography         x.x.x
```

### Docker build fails?

```bash
# Clear Docker cache and rebuild
docker-compose -f docker-compose.multimodel.yml down -v
docker system prune -f
docker-compose -f docker-compose.multimodel.yml build --no-cache
```

### Virtual environment not working?

```bash
# Delete and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install anthropic openai google-generativeai python-dotenv
```

---

## ✅ Success Checklist

After setup, you should be able to:

- [ ] Import `google.generativeai` without errors
- [ ] Generate text with Gemini
- [ ] Analyze images with Gemini Vision
- [ ] Use intelligent duo routing
- [ ] Run all DevSkyy skills with full multi-model support

---

## 🎯 Next Steps After Setup

1. **Test all models**: Run `python test_multi_model.py`
2. **Try fashion analysis**: Test image analysis with a product photo
3. **Generate UI components**: Create React components with brand styling
4. **Use intelligent routing**: Let the system pick the best model per task

---

**Need help?** The setup is documented and tested. Choose your approach and enjoy full multi-model AI orchestration! 🚀
