"""
WordPress integration package for SkyyRose.

Provides collection page management and WordPress client utilities.
"""

from .client import WordPressClient, WordPressError
from .collection_page_manager import CollectionDesignTemplates, CollectionType

__all__ = [
    "CollectionDesignTemplates",
    "CollectionType",
    "WordPressClient",
    "WordPressError",
]
