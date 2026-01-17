"""
Product Clustering and Gallery Generation

Analyzes visual similarity between product images to:
- Group related product views (front/back/detail/lifestyle)
- Detect duplicate uploads
- Build WooCommerce product galleries
"""

from .gallery_builder import GalleryBuilder
from .similarity_matcher import SimilarityMatcher

__all__ = ["SimilarityMatcher", "GalleryBuilder"]
