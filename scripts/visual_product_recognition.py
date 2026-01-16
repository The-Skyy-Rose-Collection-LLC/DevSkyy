#!/usr/bin/env python3
"""
Visual Product Recognition for SkyyRose Catalog

Analyzes product images using CLIP embeddings to automatically:
- Group related product views (front/back/detail/lifestyle)
- Detect duplicate uploads
- Build WooCommerce product galleries
- Generate cross-sell recommendations

Usage:
    # Analyze WordPress catalog
    python scripts/visual_product_recognition.py

    # Analyze custom image directory
    python scripts/visual_product_recognition.py \
        --image-dir /path/to/images \
        --output-dir ./product_analysis

    # Use fine-tuned ResNet model (after training)
    python scripts/visual_product_recognition.py \
        --embedder resnet \
        --model-path data/models/resnet_skyyrose.pth

Features:
- Option 1 (Active): CLIP embeddings (zero-shot, fast)
- Option 2 (Pre-configured): ResNet fine-tuned (requires labeled dataset)

Output:
- product_galleries.json: WooCommerce gallery mappings
- woocommerce_import.csv: CSV for bulk product import
- similarity_report.json: Duplicate/variant detection
- embeddings.npy: Cached embeddings for future analysis
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from clustering import GalleryBuilder, SimilarityMatcher
from image_embeddings import EmbedderConfig, get_embedder

# Colors for output
GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


def collect_product_images(image_dir: Path) -> list[Path]:
    """
    Collect all product images from directory.

    Args:
        image_dir: Directory containing product images

    Returns:
        List of image file paths (WebP and JPG)
    """
    image_extensions = {".webp", ".jpg", ".jpeg", ".png"}
    images = []

    for ext in image_extensions:
        images.extend(image_dir.glob(f"**/*{ext}"))

    # Sort for consistent ordering
    images = sorted(images)

    return images


def generate_embeddings(
    image_paths: list[Path],
    embedder_config: EmbedderConfig,
    cache_file: Path | None = None,
) -> np.ndarray:
    """
    Generate embeddings for all product images.

    Args:
        image_paths: List of image file paths
        embedder_config: Embedder configuration
        cache_file: Path to cache embeddings (if None, no caching)

    Returns:
        Embedding matrix (shape: [num_images, embedding_dim])
    """
    # Check cache
    if cache_file and cache_file.exists():
        print(f"{BLUE}Loading cached embeddings from {cache_file}...{NC}")
        embeddings = np.load(cache_file)
        if len(embeddings) == len(image_paths):
            print(f"{GREEN}✓ Loaded {len(embeddings)} cached embeddings{NC}")
            return embeddings
        else:
            print(f"{YELLOW}⚠ Cache size mismatch, regenerating embeddings{NC}")

    # Generate embeddings
    print(f"\n{BLUE}Generating embeddings for {len(image_paths)} images...{NC}")
    embedder = get_embedder(embedder_config)

    embeddings = []
    for image_path in tqdm(image_paths, desc="Processing images"):
        try:
            embedding = embedder.encode_image(image_path)
            embeddings.append(embedding)
        except Exception as e:
            print(f"{RED}✗ Failed to process {image_path}: {e}{NC}")
            # Add zero embedding as placeholder
            embeddings.append(np.zeros(embedder.get_embedding_dim()))

    embeddings = np.array(embeddings)

    # Cache embeddings
    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        np.save(cache_file, embeddings)
        print(f"{GREEN}✓ Cached embeddings to {cache_file}{NC}")

    return embeddings


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Visual product recognition for SkyyRose catalog")
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=None,
        help="Directory containing product images (default: use WordPress mapping)",
    )
    parser.add_argument(
        "--wordpress-mapping",
        type=Path,
        default=Path("wordpress/webp_image_mapping.json"),
        help="WordPress image mapping file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("wordpress/product_analysis"),
        help="Output directory for analysis results",
    )
    parser.add_argument(
        "--embedder",
        choices=["clip", "resnet"],
        default="clip",
        help="Embedder type (clip=fast, resnet=fine-tuned)",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Path to fine-tuned ResNet model (for --embedder resnet)",
    )
    parser.add_argument(
        "--duplicate-threshold",
        type=float,
        default=0.95,
        help="Similarity threshold for duplicates (0-1)",
    )
    parser.add_argument(
        "--variant-threshold",
        type=float,
        default=0.85,
        help="Similarity threshold for variants (0-1)",
    )
    parser.add_argument(
        "--cluster-threshold",
        type=float,
        default=0.70,
        help="Similarity threshold for clustering (0-1)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Don't use cached embeddings",
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}Visual Product Recognition - SkyyRose Catalog{NC}")
    print(f"{BLUE}{'=' * 70}{NC}\n")

    # Collect images
    if args.image_dir:
        print(f"Image directory: {args.image_dir}")
        image_paths = collect_product_images(args.image_dir)
    else:
        print(f"WordPress mapping: {args.wordpress_mapping}")
        # TODO: Extract image paths from WordPress mapping
        # For now, use fallback directory
        fallback_dir = Path("/tmp/full_catalog_processing/webp_optimized/webp")
        if fallback_dir.exists():
            image_paths = collect_product_images(fallback_dir)
        else:
            print(f"{RED}Error: No image directory specified and fallback not found{NC}")
            sys.exit(1)

    print(f"Found {len(image_paths)} product images\n")

    if len(image_paths) == 0:
        print(f"{RED}Error: No images found{NC}")
        sys.exit(1)

    # Configure embedder
    embedder_config = EmbedderConfig(
        embedder_type=args.embedder,
        resnet_model_path=args.model_path,
        device=None,  # Auto-detect
    )

    print(f"Embedder: {args.embedder}")
    if args.embedder == "resnet" and args.model_path:
        print(f"Model path: {args.model_path}")
    print()

    # Generate embeddings
    cache_file = None if args.no_cache else args.output_dir / "embeddings.npy"
    embeddings = generate_embeddings(image_paths, embedder_config, cache_file)

    print(f"\n{GREEN}✓ Generated embeddings: {embeddings.shape}{NC}\n")

    # Initialize matcher
    matcher = SimilarityMatcher(
        duplicate_threshold=args.duplicate_threshold,
        variant_threshold=args.variant_threshold,
        cluster_threshold=args.cluster_threshold,
    )

    # Find duplicates
    print(f"{BLUE}Detecting duplicates...{NC}")
    duplicates = matcher.find_duplicates(image_paths, embeddings)
    print(f"{GREEN}✓ Found {len(duplicates)} duplicate pairs{NC}")

    # Find variants
    print(f"\n{BLUE}Detecting product variants...{NC}")
    variants = matcher.find_variants(image_paths, embeddings)
    print(f"{GREEN}✓ Found {len(variants)} variant pairs{NC}")

    # Cluster products
    print(f"\n{BLUE}Clustering products by visual similarity...{NC}")
    clusters = matcher.cluster_products(image_paths, embeddings)
    print(f"{GREEN}✓ Created {len(clusters)} product clusters{NC}")

    # Show cluster stats
    cluster_sizes = [len(c) for c in clusters]
    print(f"  - Single image: {sum(1 for s in cluster_sizes if s == 1)}")
    print(f"  - 2-5 images: {sum(1 for s in cluster_sizes if 2 <= s <= 5)}")
    print(f"  - 6+ images: {sum(1 for s in cluster_sizes if s >= 6)}")

    # Build galleries (if WordPress mapping available)
    if args.wordpress_mapping.exists():
        print(f"\n{BLUE}Building WooCommerce product galleries...{NC}")
        gallery_builder = GalleryBuilder(args.wordpress_mapping, matcher)
        galleries = gallery_builder.build_galleries_from_clusters(clusters, image_paths)
        print(f"{GREEN}✓ Built {len(galleries)} product galleries{NC}")

        # Save galleries
        gallery_file = args.output_dir / "product_galleries.json"
        gallery_builder.save_galleries(galleries, gallery_file)

        # Generate WooCommerce import CSV
        csv_file = args.output_dir / "woocommerce_import.csv"
        gallery_builder.generate_woocommerce_import(galleries, csv_file)

    # Save similarity report
    print(f"\n{BLUE}Generating similarity report...{NC}")
    report = {
        "summary": {
            "total_images": len(image_paths),
            "duplicate_pairs": len(duplicates),
            "variant_pairs": len(variants),
            "clusters": len(clusters),
        },
        "duplicates": [
            {
                "image1": str(dup.image1_path.name),
                "image2": str(dup.image2_path.name),
                "similarity": round(dup.similarity_score, 3),
            }
            for dup in duplicates
        ],
        "variants": [
            {
                "image1": str(var.image1_path.name),
                "image2": str(var.image2_path.name),
                "similarity": round(var.similarity_score, 3),
            }
            for var in variants
        ],
        "clusters": [
            {
                "cluster_id": c.cluster_id,
                "size": len(c),
                "images": [p.name for p in c.image_paths],
                "mean_similarity": round(c.mean_similarity, 3),
            }
            for c in clusters
            if len(c) > 1
        ],
    }

    report_file = args.output_dir / "similarity_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"{GREEN}✓ Saved similarity report: {report_file}{NC}")

    # Summary
    print(f"\n{BLUE}{'=' * 70}{NC}")
    print(f"{BLUE}Analysis Complete{NC}")
    print(f"{BLUE}{'=' * 70}{NC}")
    print(f"Output directory: {args.output_dir}")
    print("\nFiles generated:")
    print("  - embeddings.npy: Cached embeddings for future analysis")
    print("  - similarity_report.json: Duplicate/variant detection")
    if args.wordpress_mapping.exists():
        print("  - product_galleries.json: WooCommerce gallery mappings")
        print("  - woocommerce_import.csv: Bulk product import CSV")
    print(f"\n{GREEN}✓ Done!{NC}\n")


if __name__ == "__main__":
    main()
