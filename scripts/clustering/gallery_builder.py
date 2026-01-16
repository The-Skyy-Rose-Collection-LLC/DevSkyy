"""
WooCommerce Product Gallery Builder

Automatically builds product galleries by grouping related images:
- Main product image (front view)
- Additional angles (back, side, detail)
- Lifestyle/contextual shots
- Color variants

Integrates with WordPress webp_image_mapping.json
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .similarity_matcher import ProductCluster, SimilarityMatcher


@dataclass
class ProductGallery:
    """WooCommerce product gallery with images grouped by similarity."""

    product_slug: str
    main_image_id: int
    main_image_url: str
    gallery_image_ids: list[int]
    gallery_image_urls: list[str]
    cluster_similarity: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "product_slug": self.product_slug,
            "main_image": {
                "id": self.main_image_id,
                "url": self.main_image_url,
            },
            "gallery": [
                {"id": img_id, "url": img_url}
                for img_id, img_url in zip(
                    self.gallery_image_ids, self.gallery_image_urls, strict=False
                )
            ],
            "cluster_similarity": round(self.cluster_similarity, 3),
            "total_images": 1 + len(self.gallery_image_ids),
        }


class GalleryBuilder:
    """Build WooCommerce product galleries from visual similarity clusters."""

    def __init__(
        self,
        wordpress_mapping_file: Path,
        matcher: SimilarityMatcher | None = None,
    ):
        """
        Initialize gallery builder.

        Args:
            wordpress_mapping_file: Path to webp_image_mapping.json
            matcher: SimilarityMatcher instance (creates default if None)
        """
        self.wordpress_mapping_file = wordpress_mapping_file
        self.matcher = matcher or SimilarityMatcher()

        # Load WordPress image mapping
        with open(wordpress_mapping_file) as f:
            self.wordpress_mapping: dict[str, dict[str, Any]] = json.load(f)

    def build_galleries_from_clusters(
        self,
        clusters: list[ProductCluster],
        image_paths: list[Path],
    ) -> list[ProductGallery]:
        """
        Build product galleries from similarity clusters.

        Args:
            clusters: List of product clusters
            image_paths: All image paths (must match cluster indices)

        Returns:
            List of product galleries
        """
        galleries = []

        for cluster in clusters:
            # Skip single-image clusters
            if len(cluster) < 2:
                continue

            # Get product slug from representative image
            main_path = image_paths[cluster.representative_idx]
            product_slug = main_path.stem  # e.g., "LH_FANNIE_2_main"

            # Get WordPress IDs from mapping
            if product_slug not in self.wordpress_mapping:
                continue

            main_data = self.wordpress_mapping[product_slug]
            main_image_id = main_data.get("webp_id")
            main_image_url = main_data.get("webp_url")

            if not main_image_id or not main_image_url:
                continue

            # Get gallery images (all cluster members except main)
            gallery_ids = []
            gallery_urls = []

            for idx in cluster.image_indices:
                if idx == cluster.representative_idx:
                    continue  # Skip main image

                gallery_path = image_paths[idx]
                gallery_slug = gallery_path.stem

                if gallery_slug in self.wordpress_mapping:
                    gallery_data = self.wordpress_mapping[gallery_slug]
                    gallery_id = gallery_data.get("webp_id")
                    gallery_url = gallery_data.get("webp_url")

                    if gallery_id and gallery_url:
                        gallery_ids.append(gallery_id)
                        gallery_urls.append(gallery_url)

            # Create gallery
            gallery = ProductGallery(
                product_slug=product_slug,
                main_image_id=main_image_id,
                main_image_url=main_image_url,
                gallery_image_ids=gallery_ids,
                gallery_image_urls=gallery_urls,
                cluster_similarity=cluster.mean_similarity,
            )

            galleries.append(gallery)

        return galleries

    def save_galleries(self, galleries: list[ProductGallery], output_file: Path) -> None:
        """
        Save product galleries to JSON file.

        Args:
            galleries: List of product galleries
            output_file: Path to output JSON file
        """
        data = {
            "total_galleries": len(galleries),
            "galleries": [gallery.to_dict() for gallery in galleries],
        }

        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Saved {len(galleries)} product galleries to {output_file}")

    def generate_woocommerce_import(
        self, galleries: list[ProductGallery], output_file: Path
    ) -> None:
        """
        Generate WooCommerce CSV import file for product galleries.

        Args:
            galleries: List of product galleries
            output_file: Path to output CSV file

        Format:
            product_slug,main_image_id,gallery_image_ids
            LH_FANNIE_2_main,8622,"8623,8624,8625"
        """
        import csv

        with open(output_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["product_slug", "main_image_id", "gallery_image_ids"])

            for gallery in galleries:
                gallery_ids_str = ",".join(str(id) for id in gallery.gallery_image_ids)
                writer.writerow(
                    [
                        gallery.product_slug,
                        gallery.main_image_id,
                        gallery_ids_str,
                    ]
                )

        print(f"✓ Generated WooCommerce import CSV: {output_file}")

    def get_product_recommendations(
        self,
        product_slug: str,
        image_paths: list[Path],
        embeddings: np.ndarray,
        top_k: int = 5,
    ) -> list[str]:
        """
        Get similar product recommendations based on visual similarity.

        Args:
            product_slug: Product slug to find recommendations for
            image_paths: All product image paths
            embeddings: Embedding matrix
            top_k: Number of recommendations to return

        Returns:
            List of recommended product slugs (sorted by similarity)
        """
        # Find query product index
        query_idx = None
        for idx, path in enumerate(image_paths):
            if path.stem == product_slug:
                query_idx = idx
                break

        if query_idx is None:
            return []

        # Get top similar products
        matches = self.matcher.get_top_matches(query_idx, image_paths, embeddings, top_k=top_k)

        # Extract product slugs
        recommendations = [image_paths[match.image2_idx].stem for match in matches]

        return recommendations
