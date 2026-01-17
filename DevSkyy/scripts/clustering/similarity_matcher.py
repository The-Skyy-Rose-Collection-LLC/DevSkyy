"""
Visual Similarity Matcher

Clusters product images by visual similarity using cosine distance.

Features:
- Hierarchical clustering for grouping related images
- Duplicate detection (similarity > 0.95)
- Product variant matching (same design, different colors)
- Cross-reference generation for WooCommerce
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage


@dataclass
class SimilarityMatch:
    """Result of similarity matching between two images."""

    image1_idx: int
    image2_idx: int
    image1_path: Path
    image2_path: Path
    similarity_score: float
    match_type: str  # "duplicate", "variant", "related", "different"

    def __post_init__(self):
        """Classify match type based on similarity score."""
        if self.similarity_score >= 0.95:
            self.match_type = "duplicate"  # Exact same image (or very close)
        elif self.similarity_score >= 0.85:
            self.match_type = "variant"  # Same product, different angle/lighting
        elif self.similarity_score >= 0.70:
            self.match_type = "related"  # Related product (same collection/style)
        else:
            self.match_type = "different"  # Unrelated


@dataclass
class ProductCluster:
    """Group of visually similar product images."""

    cluster_id: int
    image_indices: list[int]
    image_paths: list[Path]
    mean_similarity: float
    representative_idx: int  # Index of "best" image to represent cluster

    def __len__(self) -> int:
        return len(self.image_indices)


class SimilarityMatcher:
    """Match and cluster images by visual similarity."""

    def __init__(
        self,
        duplicate_threshold: float = 0.95,
        variant_threshold: float = 0.85,
        cluster_threshold: float = 0.70,
    ):
        """
        Initialize similarity matcher.

        Args:
            duplicate_threshold: Similarity score for exact duplicates (0-1)
            variant_threshold: Similarity score for same product variants (0-1)
            cluster_threshold: Minimum similarity for clustering (0-1)
        """
        self.duplicate_threshold = duplicate_threshold
        self.variant_threshold = variant_threshold
        self.cluster_threshold = cluster_threshold

    def compute_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Compute pairwise cosine similarity matrix.

        Args:
            embeddings: Embedding matrix (shape: [num_images, embedding_dim])

        Returns:
            Similarity matrix (shape: [num_images, num_images])
            Values in range [0, 1] (higher = more similar)
        """
        # Normalize embeddings (for efficient cosine similarity via dot product)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Compute similarity matrix
        similarity_matrix = np.dot(embeddings_norm, embeddings_norm.T)

        return similarity_matrix

    def find_duplicates(
        self, image_paths: list[Path], embeddings: np.ndarray
    ) -> list[SimilarityMatch]:
        """
        Find duplicate images (similarity >= duplicate_threshold).

        Args:
            image_paths: List of image file paths
            embeddings: Embedding matrix

        Returns:
            List of duplicate matches
        """
        similarity_matrix = self.compute_similarity_matrix(embeddings)
        duplicates = []

        # Find pairs with similarity >= threshold
        num_images = len(image_paths)
        for i in range(num_images):
            for j in range(i + 1, num_images):
                similarity = similarity_matrix[i, j]

                if similarity >= self.duplicate_threshold:
                    match = SimilarityMatch(
                        image1_idx=i,
                        image2_idx=j,
                        image1_path=image_paths[i],
                        image2_path=image_paths[j],
                        similarity_score=float(similarity),
                        match_type="duplicate",
                    )
                    duplicates.append(match)

        return duplicates

    def find_variants(
        self, image_paths: list[Path], embeddings: np.ndarray
    ) -> list[SimilarityMatch]:
        """
        Find product variants (same product, different angles/lighting).

        Similarity range: [variant_threshold, duplicate_threshold)

        Args:
            image_paths: List of image file paths
            embeddings: Embedding matrix

        Returns:
            List of variant matches
        """
        similarity_matrix = self.compute_similarity_matrix(embeddings)
        variants = []

        num_images = len(image_paths)
        for i in range(num_images):
            for j in range(i + 1, num_images):
                similarity = similarity_matrix[i, j]

                if self.variant_threshold <= similarity < self.duplicate_threshold:
                    match = SimilarityMatch(
                        image1_idx=i,
                        image2_idx=j,
                        image1_path=image_paths[i],
                        image2_path=image_paths[j],
                        similarity_score=float(similarity),
                        match_type="variant",
                    )
                    variants.append(match)

        return variants

    def cluster_products(
        self, image_paths: list[Path], embeddings: np.ndarray
    ) -> list[ProductCluster]:
        """
        Cluster images by visual similarity using hierarchical clustering.

        Args:
            image_paths: List of image file paths
            embeddings: Embedding matrix

        Returns:
            List of product clusters
        """
        if len(image_paths) < 2:
            # Single image - create single cluster
            return [
                ProductCluster(
                    cluster_id=0,
                    image_indices=[0],
                    image_paths=[image_paths[0]],
                    mean_similarity=1.0,
                    representative_idx=0,
                )
            ]

        # Compute distance matrix (1 - similarity)
        similarity_matrix = self.compute_similarity_matrix(embeddings)
        # Clip to [0, 1] to handle floating point precision issues
        similarity_matrix = np.clip(similarity_matrix, 0.0, 1.0)
        distance_matrix = 1 - similarity_matrix

        # Convert to condensed distance matrix for scipy
        condensed_distances = []
        num_images = len(image_paths)
        for i in range(num_images):
            for j in range(i + 1, num_images):
                condensed_distances.append(distance_matrix[i, j])

        # Hierarchical clustering (average linkage)
        linkage_matrix = linkage(condensed_distances, method="average")

        # Form clusters
        cluster_labels = fcluster(
            linkage_matrix,
            t=1 - self.cluster_threshold,  # Distance threshold
            criterion="distance",
        )

        # Build cluster objects
        clusters: dict[int, ProductCluster] = {}
        for idx, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = ProductCluster(
                    cluster_id=label,
                    image_indices=[],
                    image_paths=[],
                    mean_similarity=0.0,
                    representative_idx=idx,
                )

            clusters[label].image_indices.append(idx)
            clusters[label].image_paths.append(image_paths[idx])

        # Compute mean similarity and select representative image
        for cluster in clusters.values():
            if len(cluster.image_indices) > 1:
                # Get similarities within cluster
                indices = cluster.image_indices
                cluster_similarities = [
                    similarity_matrix[i, j] for i in indices for j in indices if i < j
                ]
                cluster.mean_similarity = float(np.mean(cluster_similarities))

                # Representative = image with highest average similarity to cluster
                avg_similarities = []
                for i in indices:
                    avg_sim = np.mean([similarity_matrix[i, j] for j in indices if j != i])
                    avg_similarities.append(avg_sim)

                best_idx = indices[np.argmax(avg_similarities)]
                cluster.representative_idx = best_idx
            else:
                cluster.mean_similarity = 1.0

        return list(clusters.values())

    def get_top_matches(
        self,
        query_idx: int,
        image_paths: list[Path],
        embeddings: np.ndarray,
        top_k: int = 5,
    ) -> list[SimilarityMatch]:
        """
        Find top-k most similar images to a query image.

        Args:
            query_idx: Index of query image
            image_paths: List of all image paths
            embeddings: Embedding matrix
            top_k: Number of results to return

        Returns:
            List of top-k similarity matches (excluding query itself)
        """
        similarity_matrix = self.compute_similarity_matrix(embeddings)
        query_similarities = similarity_matrix[query_idx]

        # Sort by similarity (descending)
        sorted_indices = np.argsort(query_similarities)[::-1]

        # Exclude query itself
        sorted_indices = sorted_indices[sorted_indices != query_idx]

        # Get top-k matches
        matches = []
        for i in sorted_indices[:top_k]:
            match = SimilarityMatch(
                image1_idx=query_idx,
                image2_idx=int(i),
                image1_path=image_paths[query_idx],
                image2_path=image_paths[i],
                similarity_score=float(query_similarities[i]),
                match_type="",  # Will be auto-classified in __post_init__
            )
            matches.append(match)

        return matches
