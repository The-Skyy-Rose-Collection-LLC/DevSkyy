---
name: 3D Pipeline Workflow
description: This skill should be used when the user asks to "generate 3D models", "create 3D assets", "convert images to 3D", "optimize 3D meshes", "integrate Tripo3D", or mentions 3D asset pipelines, GLB/OBJ formats, texture baking, or product 3D visualization.
version: 1.0.0
---

# 3D Pipeline Workflow Skill

Use this skill when working with 3D asset generation, optimization, and integration in DevSkyy.

## When to Use This Skill

Invoke this skill when the user:

- Wants to generate 3D models from text descriptions or images
- Needs to process, optimize, or convert 3D assets
- Asks about Tripo3D integration or 3D pipeline architecture
- Requests 3D product visualization for SkyyRose collections
- Mentions GLB, OBJ, FBX formats or texture baking
- Wants to integrate 3D assets into WordPress/Elementor or WooCommerce

## 3D Pipeline Architecture

### Core Components

1. **Tripo3D Agent** (`agents/tripo_agent.py`):
   - Text-to-3D generation
   - Image-to-3D conversion
   - Model refinement and optimization
   - Texture baking and PBR materials

2. **3D Asset Pipeline** (`agents/visual_generation.py:ThreeDAssetPipeline`):
   - Validation (polycount, texture resolution)
   - Format conversion (GLB → OBJ, etc.)
   - WordPress upload and attachment
   - WooCommerce product integration
   - Retry logic with exponential backoff

3. **MCP Tools**:
   - `devskyy_generate_3d_from_description`
   - `devskyy_generate_3d_from_image`

## Text-to-3D Generation

### Basic Usage

```python
from agents.tripo_agent import TripoAgent

agent = TripoAgent(tool_registry=get_registry())

# Generate from text
result = await agent.generate_from_text(
    prompt="luxury hoodie with embroidered rose logo",
    style="realistic",
    output_format="glb"
)

print(f"Model URL: {result.model_url}")
print(f"Polycount: {result.polycount}")
print(f"Texture Size: {result.texture_size}")
```

### Advanced Options

```python
result = await agent.generate_from_text(
    prompt="premium leather jacket with metal zippers",
    style="realistic",  # Options: realistic, cartoon, low_poly, stylized
    output_format="glb",  # Options: glb, obj, fbx
    texture_resolution=2048,  # 1024, 2048, 4096
    polycount_target=50000,  # Target polygon count
    pbr_materials=True,  # Generate PBR textures
    refine_iterations=3  # Number of refinement passes
)
```

## Image-to-3D Conversion

### From Product Photography

```python
# Convert product photo to 3D model
result = await agent.generate_from_image(
    image_path="/path/to/product.jpg",
    remove_background=True,  # Auto-remove background
    generate_backface=True,  # Create geometry for hidden sides
    output_format="glb"
)
```

### From Concept Art

```python
# Convert design sketch to 3D
result = await agent.generate_from_image(
    image_url="https://example.com/design-sketch.png",
    style_guide="SkyyRose brand aesthetic",
    enhance_details=True,
    output_format="obj"
)
```

## Full 3D Asset Pipeline

### Complete Workflow

```python
from agents.visual_generation import ThreeDAssetPipeline

pipeline = ThreeDAssetPipeline(
    tripo_api_key=TRIPO_API_KEY,
    wordpress_url=WORDPRESS_URL,
    woo_key=WOO_KEY,
    woo_secret=WOO_SECRET
)

# Generate with full pipeline
asset = await pipeline.generate(
    prompt="midnight black hoodie with rose gold embroidery",
    retries=3  # Retry on failure
)

# Result includes:
# - model_url: Direct GLB file URL
# - wordpress_media_id: Uploaded to WordPress
# - woocommerce_product_id: Attached to product
# - validation: Polycount, texture checks
# - metadata: Generation parameters
```

### Validation Checks

The pipeline automatically validates:

```python
# Polycount limits
MAX_POLYCOUNT = 100_000  # For web rendering
MIN_POLYCOUNT = 5_000    # Minimum detail

# Texture resolution
MAX_TEXTURE_SIZE = 4096  # Max resolution
MIN_TEXTURE_SIZE = 1024  # Min quality

# File size
MAX_FILE_SIZE_MB = 50    # For web delivery
```

## Integration with WordPress/WooCommerce

### Upload to WordPress Media Library

```python
# Upload 3D model as WordPress media
media_id = await pipeline.upload_to_wordpress(
    glb_path="/path/to/model.glb",
    title="Product 3D Model",
    alt_text="Interactive 3D view of product"
)
```

### Attach to WooCommerce Product

```python
# Link 3D model to product
await pipeline.attach_to_product(
    product_id=12345,
    media_id=media_id,
    meta_key="_product_3d_model"
)
```

### Elementor Integration

```python
# Generate Elementor-compatible 3D widget
widget_data = {
    "widgetType": "model-viewer",
    "settings": {
        "src": asset.model_url,
        "alt": "Interactive Product View",
        "auto-rotate": True,
        "camera-controls": True,
        "shadow-intensity": 1
    }
}
```

## SkyyRose Collection Presets

### BLACK_ROSE Collection

```python
BLACK_ROSE_PRESET = {
    "style": "dark romantic aesthetic",
    "materials": {
        "base_color": "#1A1A1A",
        "metallic": 0.3,
        "roughness": 0.7
    },
    "lighting": "moody, dramatic shadows",
    "accents": "matte black with subtle rose gold details"
}

result = await agent.generate_from_text(
    prompt=f"{garment_type} in BLACK_ROSE style",
    style_guide=BLACK_ROSE_PRESET
)
```

### LOVE_HURTS Collection

```python
LOVE_HURTS_PRESET = {
    "style": "edgy romantic, emotional depth",
    "materials": {
        "base_color": "#8B0000",  # Deep red
        "metallic": 0.5,
        "roughness": 0.4
    },
    "details": "heart motifs, artistic expression",
    "texture": "distressed, lived-in feel"
}
```

### SIGNATURE Collection

```python
SIGNATURE_PRESET = {
    "style": "clean minimal aesthetic, timeless",
    "materials": {
        "base_color": "#F5F5F5",  # Off-white
        "metallic": 0.8,
        "roughness": 0.2
    },
    "accents": "rose gold hardware",
    "finish": "premium, refined"
}
```

## Optimization Techniques

### Reduce Polycount

```python
from agents.tripo_agent import optimize_mesh

optimized = await optimize_mesh(
    input_path="high_poly.glb",
    target_polycount=25000,
    preserve_uv=True,
    preserve_normals=True
)
```

### Compress Textures

```python
from PIL import Image

def compress_texture(input_path: str, output_path: str, quality: int = 85):
    img = Image.open(input_path)
    img = img.resize((2048, 2048), Image.Resampling.LANCZOS)
    img.save(output_path, "JPEG", quality=quality, optimize=True)
```

### Convert Formats

```python
# GLB to OBJ conversion
from pygltflib import GLTF2

gltf = GLTF2().load(glb_path)
gltf.save(obj_path)
```

## Batch Processing

### Generate Multiple Variations

```python
variations = ["front view", "back view", "side view", "detail shot"]

models = []
for variation in variations:
    result = await agent.generate_from_text(
        prompt=f"{base_prompt} - {variation}",
        output_format="glb"
    )
    models.append(result)
```

### Product Collection Pipeline

```python
async def generate_collection_3d(collection_name: str, products: list):
    """Generate 3D models for entire product collection."""
    results = []

    for product in products:
        asset = await pipeline.generate(
            prompt=f"{product['name']} in {collection_name} style",
            retries=3
        )

        # Upload to WordPress
        media_id = await pipeline.upload_to_wordpress(
            glb_path=asset.local_path,
            title=f"{product['name']} 3D Model"
        )

        # Attach to WooCommerce
        await pipeline.attach_to_product(
            product_id=product['id'],
            media_id=media_id
        )

        results.append({
            "product_id": product['id'],
            "model_url": asset.model_url,
            "media_id": media_id
        })

    return results
```

## Error Handling

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def generate_with_retry(prompt: str):
    return await agent.generate_from_text(prompt)
```

### Validation Failures

```python
try:
    asset = await pipeline.generate(prompt)
except ValidationError as e:
    if "polycount" in str(e):
        # Retry with lower target
        asset = await pipeline.generate(
            prompt,
            polycount_target=30000
        )
    elif "texture" in str(e):
        # Retry with lower resolution
        asset = await pipeline.generate(
            prompt,
            texture_resolution=1024
        )
```

## File Locations

- **Tripo3D Agent**: `agents/tripo_agent.py`
- **3D Pipeline**: `agents/visual_generation.py`
- **MCP Tools**: `devskyy_mcp.py` (lines 245-312)
- **3D Converter Space**: `hf-spaces/3d-converter/`
- **WordPress Upload**: `orchestration/wordpress_integration.py`

## Testing

```python
import pytest

@pytest.mark.asyncio
async def test_3d_generation():
    agent = TripoAgent(tool_registry=get_registry())

    result = await agent.generate_from_text(
        prompt="simple cube",
        output_format="glb"
    )

    assert result.model_url
    assert result.polycount < 10000  # Simple shape
    assert result.format == "glb"

@pytest.mark.asyncio
async def test_pipeline_integration():
    pipeline = ThreeDAssetPipeline(...)

    asset = await pipeline.generate(
        prompt="test product",
        retries=1
    )

    assert asset.wordpress_media_id
    assert asset.validation.passed
```

## Common Use Cases

### Use Case 1: New Product Launch

```python
# Generate all 3D assets for new product
product_id = 12345
angles = ["hero", "front", "back", "side", "detail"]

for angle in angles:
    asset = await pipeline.generate(
        prompt=f"SkyyRose hoodie - {angle} view",
        retries=3
    )
    await pipeline.attach_to_product(product_id, asset.media_id)
```

### Use Case 2: AR Experience

```python
# Generate optimized model for mobile AR
ar_asset = await agent.generate_from_text(
    prompt="product for AR viewing",
    polycount_target=25000,  # Mobile-optimized
    texture_resolution=1024,  # Smaller textures
    output_format="glb"  # AR.js compatible
)
```

### Use Case 3: Virtual Try-On

```python
# Generate garment for virtual try-on
garment_3d = await agent.generate_from_image(
    image_path="product_photo.jpg",
    generate_backface=True,  # Full 360° view
    pbr_materials=True,  # Realistic materials
    output_format="glb"
)
```

## Next Steps

1. **Review** Tripo3D API documentation
2. **Test** 3D generation with sample prompts
3. **Optimize** pipeline for production use
4. **Integrate** with WordPress/WooCommerce
5. **Validate** 3D assets meet quality standards
6. **Document** collection-specific presets
7. **Monitor** generation success rates

## References

See `references/` directory for:

- Tripo3D API complete reference
- 3D optimization techniques
- WordPress 3D plugin integration
- WooCommerce 3D viewer setup
- Collection style guides
- Performance benchmarks
