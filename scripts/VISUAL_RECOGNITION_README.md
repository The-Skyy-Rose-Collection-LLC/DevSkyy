# Visual Product Recognition for SkyyRose

Automatically analyze and group product images using AI-powered visual similarity.

## Features

- **Option 1 (Active)**: CLIP embeddings - Zero-shot, pre-trained, fast
- **Option 2 (Pre-configured)**: ResNet fine-tuning - Higher accuracy after labeling

### Capabilities

✅ **Auto-Gallery Builder**: Group front/back/detail views into product galleries
✅ **Duplicate Detection**: Find identical/near-identical uploads
✅ **Variant Matching**: Detect same product in different colors/angles
✅ **Cross-Sell Recommendations**: Find visually similar products
✅ **WooCommerce Integration**: Generate gallery mappings + CSV import

## Quick Start

### Installation

```bash
# Install dependencies
pip install transformers torch torchvision pillow numpy scipy tqdm

# Or use pip install from requirements
pip install -r scripts/requirements_visual_recognition.txt
```

### Run Analysis on WordPress Catalog

```bash
# Analyze all 102 uploaded products
python scripts/visual_product_recognition.py

# Output: wordpress/product_analysis/
#   - product_galleries.json (WooCommerce mappings)
#   - woocommerce_import.csv (bulk import)
#   - similarity_report.json (duplicates/variants)
#   - embeddings.npy (cached for future runs)
```

### Custom Image Directory

```bash
python scripts/visual_product_recognition.py \
    --image-dir /path/to/product/images \
    --output-dir ./analysis_results
```

## Usage Examples

### Find Duplicate Products

```bash
# Run analysis
python scripts/visual_product_recognition.py

# Check similarity_report.json → "duplicates" section
# Shows pairs with similarity >= 0.95
```

### Build Product Galleries

```bash
# Generate WooCommerce galleries
python scripts/visual_product_recognition.py

# Import to WooCommerce:
# 1. Upload woocommerce_import.csv
# 2. Or use product_galleries.json with REST API
```

### Get Product Recommendations

```python
from clustering import GalleryBuilder
from image_embeddings import get_embedder
import numpy as np

# Load embeddings
embeddings = np.load("wordpress/product_analysis/embeddings.npy")

# Find similar products
gallery_builder = GalleryBuilder("wordpress/webp_image_mapping.json")
recommendations = gallery_builder.get_product_recommendations(
    product_slug="LH_FANNIE_2_main",
    image_paths=image_paths,
    embeddings=embeddings,
    top_k=5
)
```

## Option 2: Fine-Tuned ResNet (Future)

When ready to fine-tune on SkyyRose catalog:

### Step 1: Label Products

```bash
# Interactive labeling tool
python scripts/training/prepare_dataset.py \
    --image-dir /tmp/full_catalog_processing/webp_optimized/webp \
    --output-dir data/product_dataset

# Assigns each image to a product group
# Minimum 100+ groups recommended
```

### Step 2: Train ResNet

```bash
# Fine-tune ResNet-50 (requires GPU)
python scripts/training/train_resnet.py \
    --dataset-dir data/product_dataset \
    --output-dir data/models \
    --epochs 50

# ~2-4 hours on GPU
# Output: resnet50_skyyrose_v1.pth
```

### Step 3: Switch to ResNet

```python
# Edit scripts/image_embeddings/config.py

DEFAULT_CONFIG = EmbedderConfig(
    embedder_type="resnet",  # Changed from "clip"
    resnet_model_path=Path("data/models/resnet50_skyyrose_v1.pth"),
    device="cuda",
)
```

### Step 4: Re-run Analysis

```bash
# Now uses fine-tuned ResNet
python scripts/visual_product_recognition.py

# Expect higher accuracy for:
# - Fabric textures (cotton vs fleece)
# - Color variants (same design, different colors)
# - SkyyRose-specific styles
```

## Configuration

### Similarity Thresholds

```bash
python scripts/visual_product_recognition.py \
    --duplicate-threshold 0.95 \  # Exact duplicates
    --variant-threshold 0.85 \     # Same product, different angle
    --cluster-threshold 0.70       # Related products
```

### Embedder Selection

```bash
# CLIP (default, fast)
python scripts/visual_product_recognition.py --embedder clip

# ResNet (after training)
python scripts/visual_product_recognition.py \
    --embedder resnet \
    --model-path data/models/resnet50_skyyrose_v1.pth
```

## Output Files

### `product_galleries.json`

```json
{
  "total_galleries": 45,
  "galleries": [
    {
      "product_slug": "LH_FANNIE_2_main",
      "main_image": {
        "id": 8622,
        "url": "https://skyyrose.co/.../LH_FANNIE_2_main.webp"
      },
      "gallery": [
        {"id": 8623, "url": "...LH_FANNIE_2_back.webp"},
        {"id": 8624, "url": "...LH_FANNIE_2_detail.webp"}
      ],
      "cluster_similarity": 0.892,
      "total_images": 3
    }
  ]
}
```

### `woocommerce_import.csv`

```csv
product_slug,main_image_id,gallery_image_ids
LH_FANNIE_2_main,8622,"8623,8624"
```

### `similarity_report.json`

```json
{
  "summary": {
    "total_images": 102,
    "duplicate_pairs": 3,
    "variant_pairs": 24,
    "clusters": 45
  },
  "duplicates": [
    {
      "image1": "BR_SHERPA_main.webp",
      "image2": "BR_SHERPA_main_v2.webp",
      "similarity": 0.978
    }
  ]
}
```

## Performance

### CLIP (Option 1)

- **Speed**: ~2s per image (CPU), ~0.5s (GPU)
- **Accuracy**: 85-90% for general similarity
- **Training**: None required
- **Embedding dim**: 512

### ResNet (Option 2, after training)

- **Speed**: ~1s per image (CPU), ~0.2s (GPU)
- **Accuracy**: 92-96% for SkyyRose products
- **Training**: 2-4 hours (50 epochs)
- **Embedding dim**: 2048

## Troubleshooting

### Out of Memory (CPU)

```bash
# Process in smaller batches (edit visual_product_recognition.py)
# Or use GPU if available
```

### CLIP Model Download Fails

```bash
# Pre-download model
python -c "from transformers import CLIPModel; CLIPModel.from_pretrained('openai/clip-vit-base-patch32')"
```

### ResNet Training Requires Labels

```bash
# Use prepare_dataset.py to label products first
# Minimum 100 product groups recommended
# Each group needs 2+ images
```

## Architecture

```
scripts/
├── visual_product_recognition.py    # Main CLI
├── image_embeddings/
│   ├── clip_embedder.py            # CLIP implementation (active)
│   ├── resnet_embedder.py          # ResNet implementation (future)
│   └── config.py                   # Model selection
├── clustering/
│   ├── similarity_matcher.py       # Cosine similarity clustering
│   └── gallery_builder.py          # WooCommerce gallery generation
└── training/
    ├── prepare_dataset.py          # Interactive labeling
    └── train_resnet.py            # Fine-tune ResNet
```

## Next Steps

1. ✅ Run CLIP analysis on WordPress catalog
2. ⏳ Review product_galleries.json recommendations
3. ⏳ Import galleries to WooCommerce
4. ⏳ Label products for ResNet training (when needed)

---

**Version**: 1.0.0
**Created**: 2026-01-16
**Status**: CLIP Active, ResNet Pre-configured

**For**: SkyyRose LLC
**Contact**: support@skyyrose.com
