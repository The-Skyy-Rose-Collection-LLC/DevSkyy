# 3D Pipeline Documentation

**Purpose**: Standard procedures for 3D model generation and virtual try-on using Tripo3D and FASHN APIs.

---

## Overview

### Pipeline Flow
```
Product Image → Tripo3D → 3D Model → FASHN → Virtual Try-On → Website
      ↓              ↓           ↓          ↓              ↓
   Capture      Generate    Optimize    Apply         Display
```

### Supported Services
| Service | Purpose | API Endpoint |
|---------|---------|--------------|
| Tripo3D | 3D model generation | api.tripo3d.ai |
| FASHN | Virtual try-on | api.fashn.ai |

---

## Tripo3D Integration

### Authentication
```python
import os
from tripo3d import TripoClient

client = TripoClient(
    api_key=os.environ["TRIPO3D_API_KEY"]
)
```

### Generate 3D Model from Image

```python
async def generate_3d_model(
    image_path: str,
    product_sku: str,
    category: str
) -> dict:
    """
    Generate 3D model from product image.

    Args:
        image_path: Path to product image (1000x1000 recommended)
        product_sku: Product SKU for naming
        category: Product category for optimization presets

    Returns:
        dict with model_url, preview_url, and metadata
    """

    # Category-specific settings
    presets = {
        "tops": {"detail_level": "high", "texture_quality": "premium"},
        "bottoms": {"detail_level": "high", "texture_quality": "premium"},
        "accessories": {"detail_level": "ultra", "texture_quality": "premium"},
        "footwear": {"detail_level": "ultra", "texture_quality": "premium"}
    }

    settings = presets.get(category, presets["tops"])

    result = await client.generate(
        image=image_path,
        output_format="glb",
        **settings
    )

    # Log the generation
    log_3d_operation(
        operation="model_generation",
        sku=product_sku,
        status="success",
        model_id=result["model_id"]
    )

    return result
```

### Model Quality Requirements
| Attribute | Minimum | Target |
|-----------|---------|--------|
| Polygon count | 50K | 100K |
| Texture resolution | 2K | 4K |
| File size | - | < 10MB |
| Format | GLB | GLB |

---

## FASHN Virtual Try-On

### Authentication
```python
import os
from fashn import FashnClient

fashn_client = FashnClient(
    api_key=os.environ["FASHN_API_KEY"]
)
```

### Apply Virtual Try-On

```python
async def apply_virtual_tryon(
    model_image: str,  # Person/mannequin image
    garment_image: str,  # Product image
    product_sku: str,
    options: dict = None
) -> dict:
    """
    Apply virtual try-on to product.

    Args:
        model_image: Path to model/person image
        garment_image: Path to garment image
        product_sku: Product SKU for tracking
        options: Additional processing options

    Returns:
        dict with result_url and metadata
    """

    default_options = {
        "fit_type": "realistic",
        "lighting_match": True,
        "shadow_generation": True,
        "output_resolution": "high"
    }

    if options:
        default_options.update(options)

    result = await fashn_client.try_on(
        person=model_image,
        garment=garment_image,
        **default_options
    )

    # Log the operation
    log_3d_operation(
        operation="virtual_tryon",
        sku=product_sku,
        status="success",
        result_id=result["result_id"]
    )

    return result
```

### Model Image Requirements
| Type | Dimensions | Format | Notes |
|------|------------|--------|-------|
| Full body | 1080x1920 | JPG/PNG | Neutral pose, good lighting |
| Upper body | 1080x1080 | JPG/PNG | Arms slightly away from body |
| Lower body | 1080x1440 | JPG/PNG | Straight-on view |

---

## Processing Pipeline

### Full Product Processing

```python
async def process_product_3d(
    product_sku: str,
    product_images: list[str],
    category: str
) -> dict:
    """
    Full 3D processing pipeline for a product.

    Steps:
    1. Generate 3D model from main product image
    2. Create virtual try-on variants
    3. Generate preview renders
    4. Upload to CDN
    5. Update product metadata
    """

    results = {
        "sku": product_sku,
        "model_3d": None,
        "tryon_images": [],
        "preview_renders": [],
        "status": "processing"
    }

    try:
        # Step 1: Generate 3D model
        model_result = await generate_3d_model(
            image_path=product_images[0],
            product_sku=product_sku,
            category=category
        )
        results["model_3d"] = model_result["model_url"]

        # Step 2: Virtual try-on with standard models
        for model_image in get_standard_models(category):
            tryon_result = await apply_virtual_tryon(
                model_image=model_image,
                garment_image=product_images[0],
                product_sku=product_sku
            )
            results["tryon_images"].append(tryon_result["result_url"])

        # Step 3: Generate preview renders
        renders = await generate_preview_renders(
            model_url=results["model_3d"],
            angles=[0, 45, 90, 180, 270]
        )
        results["preview_renders"] = renders

        # Step 4: Upload to CDN
        cdn_urls = await upload_to_cdn(results)
        results.update(cdn_urls)

        # Step 5: Update WooCommerce product
        await update_product_3d_assets(product_sku, results)

        results["status"] = "complete"

    except Exception as e:
        results["status"] = "failed"
        results["error"] = str(e)
        log_3d_operation(
            operation="pipeline_error",
            sku=product_sku,
            status="failed",
            error=str(e)
        )

    return results
```

---

## Asset Management

### File Naming Convention
```
{sku}_{asset_type}_{variant}.{ext}

Asset types:
- 3d: 3D model file
- tryon: Virtual try-on image
- render: 3D render preview
- thumb: Thumbnail preview

Examples:
- SR-TOP-045_3d_main.glb
- SR-TOP-045_tryon_model1.jpg
- SR-TOP-045_render_front.jpg
- SR-TOP-045_thumb_360.gif
```

### Storage Structure
```
/assets/3d/
├── models/
│   └── {sku}/
│       ├── {sku}_3d_main.glb
│       └── {sku}_3d_lowpoly.glb
├── tryon/
│   └── {sku}/
│       ├── {sku}_tryon_model1.jpg
│       └── {sku}_tryon_model2.jpg
└── renders/
    └── {sku}/
        ├── {sku}_render_front.jpg
        ├── {sku}_render_side.jpg
        └── {sku}_render_back.jpg
```

---

## Quality Assurance

### Automated Checks
```python
def validate_3d_output(model_path: str, sku: str) -> dict:
    """Validate 3D model meets quality standards."""

    checks = {
        "file_exists": os.path.exists(model_path),
        "file_size_ok": os.path.getsize(model_path) < 10_000_000,
        "format_valid": model_path.endswith(".glb"),
        "polygon_count": None,
        "texture_resolution": None
    }

    # Additional mesh analysis
    mesh_stats = analyze_mesh(model_path)
    checks["polygon_count"] = mesh_stats["polygons"] >= 50000
    checks["texture_resolution"] = mesh_stats["texture_res"] >= 2048

    passed = all(v for v in checks.values() if v is not None)

    return {
        "sku": sku,
        "passed": passed,
        "checks": checks
    }
```

### Manual Review Triggers
Flag for human review when:
- Polygon count < 50K
- Texture artifacts detected
- Lighting inconsistencies in try-on
- Model proportions seem incorrect

---

## Error Handling

### Retry Strategy
```python
RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_factor": 2,
    "retry_on": [
        "RateLimitError",
        "TimeoutError",
        "ServiceUnavailable"
    ]
}
```

### Common Errors
| Error | Cause | Resolution |
|-------|-------|------------|
| ImageQualityError | Input image too low res | Request higher quality image |
| ProcessingTimeout | Complex model | Increase timeout, simplify geometry |
| TextureGenerationFailed | Insufficient detail | Provide additional reference images |
| RateLimitExceeded | Too many requests | Implement backoff, queue requests |

---

## API Rate Limits

### Tripo3D
| Tier | Requests/Hour | Concurrent |
|------|---------------|------------|
| Free | 10 | 1 |
| Pro | 100 | 5 |
| Enterprise | 1000 | 20 |

### FASHN
| Tier | Requests/Hour | Concurrent |
|------|---------------|------------|
| Starter | 50 | 2 |
| Business | 500 | 10 |
| Enterprise | 5000 | 50 |

---

## Logging Requirements

All 3D operations must be logged:

```python
def log_3d_operation(
    operation: str,
    sku: str,
    status: str,
    **kwargs
) -> None:
    """Log 3D pipeline operations."""

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "sku": sku,
        "status": status,
        "agent": "3d_pipeline_agent",
        **kwargs
    }

    # Write to log file
    with open("/logs/3d_pipeline.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
```

---

## Cost Tracking

### Per-Operation Costs (Estimated)
| Operation | Cost | Notes |
|-----------|------|-------|
| 3D Model Generation | $0.50-2.00 | Varies by complexity |
| Virtual Try-On | $0.10-0.25 | Per image |
| Preview Renders | $0.05 | Per angle |

Track costs per SKU for ROI analysis.

---

**Last Updated**: 2025-12-02
**Owner**: 3D/AR Team
**Review Cycle**: Monthly
