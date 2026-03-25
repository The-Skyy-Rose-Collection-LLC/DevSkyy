"""
WordPress Integration Python Package
=====================================

Python-side representations of WordPress theme data, templates, and
collection design constants.  PHP is the source of truth for rendering;
this package exposes the same data so Python agents can reference it
without making live HTTP calls.
"""

from .collection_page_manager import CollectionDesignTemplates, CollectionType

__all__ = ["CollectionDesignTemplates", "CollectionType"]
