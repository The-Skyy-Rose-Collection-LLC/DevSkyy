# SkyyRose 3D Generation Pipeline

**Complete guide to the multi-stage 3D model generation system**

---

## Pipeline Overview

The SkyyRose 3D generation pipeline consists of **4 stages** that process product images into production-ready 3D models:

```
Product Image
    ↓
[Stage 1] Image Optimization (PIL, OpenCV)
    ↓
[Stage 2] HuggingFace Shap-E (Quick Preview)
    ↓
[Stage 3] Tripo3D (Production GLB/USDZ)
    ↓
[Stage 4] WordPress Upload
    ↓
Production 3D Models (Hotspots, AR, Web)
```

---

## Stage 1: Image Optimization

**Purpose**: Prepare raw product images for 3D generation

**Tools**: PIL (Pillow), OpenCV

**Input**: Original product images (JPG, PNG, JPEG)
- Black Rose: 0.62 - 1.28 MB
- Love Hurts: 0.6 - 21.87 MB (varies significantly)
- Signature: 0.1 - 3.22 MB

**Processing Steps**:
1. **Normalize Resolution**: Resize to 1024×1024 (standard for 3D generation)
2. **Background Removal**: Remove white/transparent backgrounds for clean geometry
3. **Contrast Enhancement**: Boost contrast for better 3D reconstruction accuracy
4. **Format Validation**: Ensure PNG format for transparency support

**Output**: Optimized PNG images (1024×1024, transparent background)

**Code Reference**: `orchestration/asset_pipeline.py::ProductAssetPipeline.optimize_image()`

---

## Stage 2: HuggingFace Shap-E (Preview & Optimization Hints)

**Purpose**: Generate quick 3D preview and extract optimization hints

**Model**: [HuggingFace Shap-E](https://huggingface.co/openai/shap-e)
- **Speed**: Fast (2-5 seconds per image)
- **Output Format**: OBJ/MTL (wavefront object)
- **Quality**: Low-poly preview (10K-50K polygons)
- **Use Case**: Validation and optimization metadata extraction

**Input**: Optimized 1024×1024 PNG from Stage 1

**Processing**:
1. Call HuggingFace Shap-E API with optimized image
2. Generate low-poly 3D preview model
3. Extract metadata:
   - Suggested polycount range for production
   - Optimal texture size recommendations
   - Geometry quality indicators
4. Cache results for faster subsequent processing

**Output Format - OBJ/MTL**:
```
Output:
  - model.obj (geometry + material references)
  - model.mtl (material definitions)
  - texture.png (base texture)
  
Specifications:
  - Polycount: 10K-50K
  - Texture Size: 1024×1024
  - File Size: 1-5 MB
```

**API Integration**: `orchestration/huggingface_3d_client.py`

```python
async def generate_preview(image_path: str, collection: str) -> PreviewResult:
    """Generate quick 3D preview via HuggingFace Shap-E."""
    # Calls HF API with image
    # Returns OBJ/MTL + optimization hints
```

**When to Use Stage 2**:
- ✅ Validation that image contains recognizable 3D-able content
- ✅ Quick preview for review before expensive production generation
- ✅ Extract optimization hints for Tripo3D parameters
- ✅ Generate fallback preview if Tripo3D fails

---

## Stage 3: Tripo3D (Production GLB/USDZ)

**Purpose**: Generate production-quality 3D models optimized for web and AR

**Service**: [Tripo3D API](https://www.tripo3d.ai/)
- **Speed**: Slow (30-120 seconds per image)
- **Output Formats**: GLB (web), USDZ (iOS AR)
- **Quality**: Production-grade (50K-200K polygons)
- **Optimization**: Material/texture enhancements

**Why We Use Both HuggingFace + Tripo3D**:

| Aspect | HuggingFace | Tripo3D |
|--------|-------------|---------|
| **Speed** | 2-5s | 30-120s |
| **Quality** | Preview (10-50K) | Production (50-200K) |
| **Output** | OBJ/MTL | GLB + USDZ |
| **Cost** | Low | Medium |
| **Use** | Validation | Final product |

**Input**: Original product image (from Stage 1 or raw)

**Processing**:
1. Call Tripo3D API with source image
2. Request GLB format (web-optimized, 50-200K polygons)
3. Request USDZ format (AR-optimized for iOS)
4. Apply material/texture enhancements
5. Validate output model integrity (file size, geometry)
6. Store with version metadata

**Output Specifications**:

**GLB (Web Format)**:
- Polycount: 50K-200K
- File Size: 10-50 MB
- Textures: Embedded
- Use Case: Website 3D viewer, hotspots
- Browsers: All modern browsers (WebGL)
- Performance: Optimized for fast loading

**USDZ (iOS AR Format)**:
- Polycount: 50K-200K  
- File Size: 10-50 MB
- Textures: Embedded
- Use Case: Apple AR Quick Look
- Devices: iPhone 12+ (iOS 14+)
- Performance: Hardware-accelerated AR rendering

**API Integration**: `agents/tripo_agent.py`

```python
class TripoAgent(EnhancedSuperAgent):
    async def generate_3d_models(
        self,
        image_path: str,
        collection: str,
        quality: str = "production"
    ) -> ModelGenerationResult:
        """Generate GLB + USDZ via Tripo3D API."""
        # Validates image
        # Calls Tripo3D API
        # Returns GLB + USDZ with metadata
```

**Configuration Options**:
```python
TRIPO_GENERATION_CONFIG = {
    "quality": "production",      # preview | draft | production
    "polycount_target": 150000,   # Target polygon count
    "enable_pbr": True,           # PBR material support
    "enable_rigging": False,      # Skeletal rigging (if applicable)
    "texture_resolution": 2048,   # 1024 | 2048 | 4096
}
```

---

## Stage 4: WordPress Upload & Integration

**Purpose**: Upload 3D models to WordPress media library and link to products

**Tools**: WordPress REST API, WooCommerce REST API

**Input**: GLB and USDZ files from Stage 3

**Processing**:
1. Upload GLB to WordPress media library
2. Upload USDZ to WordPress media library
3. Set custom meta fields:
   - `_skyyrose_glb_url`: URL to GLB file
   - `_skyyrose_usdz_url`: URL to USDZ file
   - `_skyyrose_ar_enabled`: Boolean flag for AR support
   - `_skyyrose_generation_date`: Timestamp
   - `_skyyrose_model_quality`: Quality level (preview/production)
4. Link to WooCommerce product via product ID
5. Enable AR Quick Look for iOS devices
6. Test cross-browser compatibility

**API Integration**: `wordpress/media_3d_sync.py`

```python
class Media3DSync:
    async def upload_model_files(
        self,
        product_id: int,
        glb_path: str,
        usdz_path: str,
        collection: str
    ) -> ModelUploadResult:
        """Upload GLB/USDZ and set WooCommerce meta."""
        # Uploads both formats
        # Sets custom meta fields
        # Links to product
```

**Custom Meta Fields** (WooCommerce Product):
```
_skyyrose_glb_url: "https://example.com/wp-content/uploads/2024/12/product.glb"
_skyyrose_usdz_url: "https://example.com/wp-content/uploads/2024/12/product.usdz"
_skyyrose_ar_enabled: "yes"
_skyyrose_generation_date: "2024-12-20T14:30:00Z"
_skyyrose_model_quality: "production"
_skyyrose_generation_model: "tripo3d"
_skyyrose_collection: "signature"
```

---

## Complete Pipeline Execution

### Orchestration Flow

**File**: `orchestration/asset_pipeline.py::ProductAssetPipeline`

```python
async def process_collection(collection: str) -> CollectionGenerationResult:
    """Process all products in a collection through all 4 stages."""
    
    # Stage 1: Extract and optimize images
    optimized_images = await self.optimize_images(collection)
    
    # Stage 2: Generate HuggingFace previews (parallel, 3 products)
    previews = await asyncio.gather(*[
        self.generate_preview(img) for img in optimized_images
    ])
    
    # Stage 3: Generate Tripo3D production models (parallel, 2 models at a time)
    models = await self.generate_production_models(
        collection,
        concurrency=2,  # Rate limit to avoid API throttling
        retries=3,      # Retry failed generations
    )
    
    # Stage 4: Upload to WordPress (sequential to avoid conflicts)
    uploads = await self.upload_all_models(
        collection,
        models,
        woocommerce_product_ids=product_mapping[collection]
    )
    
    return CollectionGenerationResult(
        collection=collection,
        total_products=len(optimized_images),
        successful=sum(1 for u in uploads if u.success),
        previews=previews,
        production_models=models,
        uploads=uploads
    )
```

---

## Deployment Configuration

### Environment Variables

```bash
# HuggingFace (Stage 2)
HUGGINGFACE_API_KEY=hf_xxxxxxxxxxxxx         # API key from huggingface.co
HUGGINGFACE_API_TIMEOUT=30                   # Timeout in seconds

# Tripo3D (Stage 3)
TRIPO_API_KEY=tripo_xxxxxxxxxxxxx             # API key from tripo3d.ai
TRIPO_API_TIMEOUT=120                        # Timeout for generation

# WordPress (Stage 4)
WORDPRESS_URL=http://localhost:8882
WORDPRESS_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
WOOCOMMERCE_KEY=ck_xxxxxxxxxxxxx
WOOCOMMERCE_SECRET=cs_xxxxxxxxxxxxx
```

### Running the Pipeline

**Full Collection Generation**:
```bash
python3 scripts/deploy_skyyrose_site.py \
    --phase 1 \
    --assets-zip "/path/to/updev 4.zip" \
    --collection "signature" \
    --verbose
```

**Generate Specific Product**:
```bash
python3 scripts/deploy_skyyrose_site.py \
    --phase 1 \
    --assets-zip "/path/to/updev 4.zip" \
    --product-id "266AD7B0-88A6-4489-AA58-AB72A575BD33" \
    --verbose
```

**Regenerate with Different Parameters**:
```bash
python3 scripts/deploy_skyyrose_site.py \
    --phase 3 \
    --collection "black-rose" \
    --quality "production" \
    --texture-resolution 4096 \
    --retry 5 \
    --verbose
```

---

## Collection-Specific Parameters

### Black Rose (Silver Luxury)
- **Colors**: Primary #000000, Accent #C0C0C0
- **Image Size Range**: 0.62 - 1.28 MB
- **Texture Style**: Metallic silver with dark reflections
- **Polycount Target**: 150K-200K
- **Recommended Quality**: production

### Love Hurts (Rose Gold Emotion)
- **Colors**: Primary #2D1B1F, Accent #B76E79
- **Image Size Range**: 0.6 - 21.87 MB (large variation!)
- **Texture Style**: Soft rose gold with emotional depth
- **Polycount Target**: 100K-150K
- **Recommended Quality**: production
- **Note**: Large image for IMG_0114 (21.87MB) may require memory optimization

### Signature (Gold Premium)
- **Colors**: Primary #0D0D0D, Accent #D4AF37
- **Image Size Range**: 0.1 - 3.22 MB
- **Texture Style**: Rich gold accents with luxury finish
- **Polycount Target**: 150K-200K
- **Recommended Quality**: production

---

## Error Handling & Retries

All stages include robust error handling:

```python
# Stage 2 Retry (HuggingFace)
async def generate_preview_with_retry(image: str) -> PreviewResult:
    for attempt in range(3):
        try:
            result = await hf_client.generate_preview(image)
            return result
        except TimeoutError:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Preview generation failed: {e}")
            return None  # Fallback to Stage 3 without preview

# Stage 3 Retry (Tripo3D)
async def generate_model_with_retry(image: str) -> ModelResult:
    for attempt in range(3):
        try:
            result = await tripo.generate(image)
            if result.validate():  # Validate geometry
                return result
        except APIError:
            await asyncio.sleep(5 * (attempt + 1))  # Longer backoff for paid API
        except Exception as e:
            logger.error(f"Model generation failed: {e}")
            raise  # Fail fast for permanent errors
```

---

## Performance Metrics

**Typical Generation Times** (per product):

| Stage | Tool | Time | Cost |
|-------|------|------|------|
| 1 | PIL/OpenCV | 1-2s | Free |
| 2 | HuggingFace | 2-5s | Free (API quota) |
| 3 | Tripo3D | 30-120s | ~$0.50-1.00 per model |
| 4 | WordPress | 3-5s | Free |
| **Total** | — | **36-132s** | **~$0.50-1.00** |

**Collection Generation** (5 products):

```
Total Time: 3-12 minutes (depending on Tripo3D queue)
Total Cost: $2.50-5.00 per collection
Total Output: 5 GLB + 5 USDZ files
```

---

## Verification Checklist

Post-generation verification:

- [ ] All GLB files load in Three.js viewer
- [ ] All USDZ files open in AR Quick Look (iOS)
- [ ] Models have correct collection colors
- [ ] Polycount within target range (50K-200K)
- [ ] File sizes reasonable (10-50MB per format)
- [ ] Textures properly embedded
- [ ] WooCommerce meta fields set correctly
- [ ] WordPress media library files accessible
- [ ] Cross-browser testing completed

---

## Troubleshooting

### Issue: HuggingFace Rate Limiting
**Solution**: Implement backoff with jitter
```python
async def with_rate_limit(api_call, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await api_call()
        except RateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
```

### Issue: Tripo3D Generation Timeout
**Solution**: Increase timeout or use larger image
```bash
python3 scripts/deploy_skyyrose_site.py \
    --tripo-timeout 180 \  # Increase to 3 minutes
    --verbose
```

### Issue: WordPress Upload Failed
**Solution**: Verify media library permissions
```bash
# Check WordPress media library
curl -X GET "http://localhost:8882/wp-json/wp/v2/media" \
  -H "Authorization: Bearer YOUR_APP_PASSWORD"
```

### Issue: Models Not AR-Compatible
**Solution**: Ensure USDZ is valid and properly formatted
```python
# Validate USDZ format
import zipfile
with zipfile.ZipFile('model.usdz') as z:
    # Check for usda file
    assert 'model.usda' in z.namelist()
```

---

## References

- **HuggingFace Shap-E**: https://huggingface.co/openai/shap-e
- **Tripo3D API**: https://www.tripo3d.ai/dashboard
- **GLB Format**: https://github.com/KhronosGroup/glTF/tree/main/specification/2.0
- **USDZ Format**: https://www.apple.com/augmented-reality/usdz/
- **Three.js GLTFLoader**: https://threejs.org/docs/index.html#examples/en/loaders/GLTFLoader
- **AR Quick Look**: https://developer.apple.com/arkit/quick-look/

---

**Version**: 1.0.0  
**Last Updated**: December 25, 2025
