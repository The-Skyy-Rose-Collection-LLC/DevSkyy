"""
DataLoaders for N+1 Query Prevention
======================================

Uses aiodataloader to batch database queries efficiently.
"""

from api.graphql.dataloaders.product_loader import ProductDataLoader

__all__ = ["ProductDataLoader"]
