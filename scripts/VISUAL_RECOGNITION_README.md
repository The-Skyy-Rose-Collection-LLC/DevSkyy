# Visual Product Recognition for SkyyRose

Automatically analyze and group product images using AI-powered visual similarity.

Embeddings come from the unified CLIP encoder in `skyyrose.core.embeddings`
(`openai/clip-vit-base-patch32`, 512-d, revision-pinned). Per-image vectors are
cached by content hash, so re-runs skip unchanged images and a changed image is
recomputed even at the same path.

> The previous `scripts/image_embeddings/` OOP package (and its never-trained
> ResNet embedder) was removed in the Phase 2 embeddings reframe. The embedder is
> now CLIP-only via the shared core package.

## Capabilities

- **Auto-Gallery Builder**: Group front/back/detail views into product galleries
- **Duplicate Detection**: Find identical/near-identical uploads
- **Variant Matching**: Detect same product in different colors/angles
- **Cross-Sell Recommendations**: Find visually similar products
- **WooCommerce Integration**: Generate gallery mappings + CSV import

## Quick Start

### Installation

```bash
# The skyyrose package + ML deps install with the repo:
make install
# (CLIP runs on transformers + torch, already in the project deps.)
```

### Run Analysis on WordPress Catalog

```bash
python scripts/visual_product_recognition.py

# Output: wordpress/product_analysis/
#   - product_galleries.json (WooCommerce mappings)
#   - woocommerce_import.csv (bulk import)
#   - similarity_report.json (duplicates/variants)
#   - embeddings.npy (stacked matrix artifact)
#   - emb_cache/ (per-image content-hash cache; reused across runs)
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
python scripts/visual_product_recognition.py
# Check similarity_report.json -> "duplicates" section (similarity >= 0.95)
```

### Get Product Recommendations

```python
from clustering import GalleryBuilder
import numpy as np

# Reuse the matrix artifact written by a prior run.
embeddings = np.load("wordpress/product_analysis/embeddings.npy")

gallery_builder = GalleryBuilder("wordpress/webp_image_mapping.json")
recommendations = gallery_builder.get_product_recommendations(
    product_slug="LH_FANNIE_2_main",
    image_paths=image_paths,
    embeddings=embeddings,
    top_k=5,
)
```

To embed ad-hoc images directly from the core encoder:

```python
from skyyrose.core.embeddings.clip import ClipEncoder

encoder = ClipEncoder()
matrix = encoder.embed_images([path_a, path_b, path_c])  # (N, 512), L2-normalized
```

## Configuration

### Similarity Thresholds

```bash
python scripts/visual_product_recognition.py \
    --duplicate-threshold 0.95 \  # exact duplicates
    --variant-threshold 0.85 \    # same product, different angle
    --cluster-threshold 0.70      # related products
```

### Caching

```bash
# Disable the on-disk content-hash cache (always recompute):
python scripts/visual_product_recognition.py --no-cache
```

## Output Files

### `product_galleries.json`

```json
{
  "total_galleries": 45,
  "galleries": [
    {
      "product_slug": "LH_FANNIE_2_main",
      "main_image": {"id": 8622, "url": "https://skyyrose.co/.../LH_FANNIE_2_main.webp"},
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
  "summary": {"total_images": 102, "duplicate_pairs": 3, "variant_pairs": 24, "clusters": 45},
  "duplicates": [
    {"image1": "BR_SHERPA_main.webp", "image2": "BR_SHERPA_main_v2.webp", "similarity": 0.978}
  ]
}
```

## Performance (CLIP)

- **Speed**: ~2s per image (CPU), ~0.5s (GPU); batched in one forward pass per chunk
- **Accuracy**: 85-90% for general visual similarity
- **Embedding dim**: 512
- **First run** downloads the pinned CLIP weights; subsequent images hit the content-hash cache

## Troubleshooting

### CLIP Model Download Fails

```bash
# Pre-download the pinned revision:
python -c "from skyyrose.core.embeddings.clip import ClipEncoder; ClipEncoder().embed_image"
```

### Out of Memory (CPU)

Lower the batch size in `generate_embeddings` (default 32) or run on GPU.

## Architecture

```
scripts/
├── visual_product_recognition.py    # Main CLI (CLIP via skyyrose.core.embeddings)
├── clustering/
│   ├── similarity_matcher.py        # Cosine similarity clustering
│   └── gallery_builder.py           # WooCommerce gallery generation
skyyrose/core/embeddings/            # Unified encoder package
├── clip.py                          # ClipEncoder (revision-pinned, 512-d)
├── base.py                          # shared device/normalize/bomb-guard/batch
└── cache.py                         # content-hash read-through cache
```

---

**Status**: CLIP active via `skyyrose.core.embeddings` (Phase 2 reframe).

**For**: SkyyRose LLC
