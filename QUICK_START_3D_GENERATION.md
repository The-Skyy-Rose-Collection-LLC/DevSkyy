# SkyyRose 3D Model Generation - Quick Start Guide

## **⚠️ IMPORTANT: Get the Correct API Key First!**

Your current API key (`tcli_...`) is a **CLI token** and **won't work** with the SDK.

### Step 1: Get the SDK API Key

**Go to**: <https://www.tripo3d.ai/dashboard>

**Look for**:

- "API Keys" section
- "Authentication" section
- "SDK" or "API Integration"

**Generate/Copy**:

- An **SDK API Key** (should start with `tsk_`)
- NOT a CLI token (tcli_)

### Step 2: Set Environment Variable

```bash
# Copy your SDK API key (starting with tsk_)
export TRIPO_API_KEY="tsk_your_sdk_key_here_from_dashboard"

# Verify it's set
echo $TRIPO_API_KEY
```

### Step 3: Install Dependencies

```bash
# Install official Tripo3D SDK
python3 -m pip install tripo3d

# Verify installation
python3 -c "from tripo3d import TripoClient; print('✓ SDK installed')"
```

---

## **Running 3D Generation**

### Option A: Use Official SDK Script (Recommended)

```bash
python3 scripts/generate_3d_models_official_sdk.py
```

**What it does**:

- Searches for images in `assets/extracted/{COLLECTION}/`
- Generates 3D models for each image
- Saves to `assets/3d-models-generated/`
- Creates summary JSON with results

### Option B: Use Individual Examples

```bash
# Image to 3D
python3 tripo-python-sdk/examples/image_to_model.py assets/extracted/BLACK_ROSE/image1.jpg --output-dir ./output

# Text to 3D
python3 tripo-python-sdk/examples/text_to_model.py "A luxury designer hoodie, premium quality, sophisticated" --output-dir ./output
```

---

## **Troubleshooting**

### "API key must start with 'tsk_'"

**Problem**: You're using a `tcli_` token instead of `tsk_`

**Solution**:

1. Go to <https://www.tripo3d.ai/dashboard>
2. Generate an **SDK API Key** (not CLI token)
3. Copy the key starting with `tsk_`
4. Run: `export TRIPO_API_KEY="tsk_your_key"`

### "Certificate verify failed"

**Problem**: Python can't verify SSL certificates

**Solution**: The SDK automatically handles this, but if you still have issues:

- On macOS: Run `/Applications/Python\ 3.x/Install\ Certificates.command`
- On Linux: `sudo apt-get install ca-certificates`
- On Windows: Use Python installer's SSL certificate updater

### "Task failed with status: failed"

**Problem**: The API rejected the request

**Possible causes**:

- Account balance is 0 (check at dashboard)
- Image file is corrupted
- Image is too large (> 100MB)
- API rate limit hit

**Solution**:

- Check balance: `python3 -c "import asyncio; from tripo3d import TripoClient; asyncio.run(TripoClient().get_balance())"`
- Try with a different, smaller image
- Wait a few minutes and retry

---

## **API Key Types Explained**

| Type | Prefix | Use Case | SDK Support |
|------|--------|----------|-------------|
| **CLI Token** | `tcli_` | Command-line tools only | ❌ NOT supported |
| **SDK Token** | `tsk_` | Python SDK, integrations | ✅ **REQUIRED** |
| **Web Token** | `web_` | Web dashboard | ❌ NOT for SDK |

---

## **Code Examples**

### Simple Image to 3D

```python
import asyncio
from tripo3d import TripoClient
from tripo3d.models import TaskStatus

async def main():
    async with TripoClient() as client:
        # Generate from image
        task_id = await client.image_to_model(
            image="path/to/your/image.jpg"
        )
        print(f"Task created: {task_id}")

        # Wait for completion
        task = await client.wait_for_task(task_id, verbose=True)

        if task.status == TaskStatus.SUCCESS:
            print("✓ Success!")
            files = await client.download_task_models(task, "./output")
            for model_type, path in files.items():
                if path:
                    print(f"  {model_type}: {path}")
        else:
            print(f"✗ Failed: {task.status}")

asyncio.run(main())
```

### Batch Processing

```python
import asyncio
from pathlib import Path
from tripo3d import TripoClient
from tripo3d.models import TaskStatus

async def batch_generate(image_dir: str, output_dir: str):
    image_files = list(Path(image_dir).glob("*.jpg")) + \
                  list(Path(image_dir).glob("*.png"))

    async with TripoClient() as client:
        for image_path in image_files:
            task_id = await client.image_to_model(image=str(image_path))
            task = await client.wait_for_task(task_id, verbose=True)

            if task.status == TaskStatus.SUCCESS:
                await client.download_task_models(task, output_dir)
                print(f"✓ {image_path.name}")
            else:
                print(f"✗ {image_path.name}: {task.status}")

asyncio.run(batch_generate("assets/extracted", "assets/3d-models"))
```

---

## **Next Steps**

After 3D generation is working:

1. **Phase 3**: Deploy pages to WordPress
2. **Phase 4**: Create WooCommerce products
3. **Phase 5**: Test and verify

See `docs/DEVSKYY_MCP_COMPLETE_SETUP.md` for full deployment guide.

---

## **Resources**

- **Official SDK**: <https://github.com/VAST-AI-Research/tripo-python-sdk>
- **API Pricing**: $0.20-0.40 per model
- **Dashboard**: <https://www.tripo3d.ai/dashboard>
- **Support**: <https://www.tripo3d.ai/support>

---

**Last Updated**: 2025-12-25
**Status**: Ready for SDK API key configuration
