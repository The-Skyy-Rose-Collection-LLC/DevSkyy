"""
Product DataLoader - N+1 Query Prevention
==========================================

Batches multiple product requests into a single database query using DataLoader pattern.

Example:
    # Without DataLoader (N+1 problem):
    for sku in skus:
        product = await db.get_product(sku)  # N database queries!

    # With DataLoader (batched):
    loader = ProductDataLoader()
    products = await loader.load_many(skus)  # 1 database query!
"""

from typing import Any, List, Optional

from aiodataloader import DataLoader
from sqlalchemy import select

from database.db import DatabaseManager, Product


class ProductDataLoader(DataLoader):
    """
    DataLoader for batching product lookups by SKU

    Features:
    - Batches multiple requests into single DB query
    - Caches results within a single request
    - Handles missing products gracefully (returns None)
    - Thread-safe and async-friendly
    """

    def __init__(self) -> None:
        super().__init__(
            batch_load_fn=self._batch_load_fn,
            cache=True,  # Enable request-scoped caching
            max_batch_size=100,  # Batch up to 100 products at once
        )
        self.db_manager = DatabaseManager()

    async def _batch_load_fn(self, skus: List[str]) -> List[Optional[Product]]:
        """
        Batch load products by SKU list

        This function is called once for multiple load() requests, preventing N+1 queries.

        Args:
            skus: List of product SKUs to load

        Returns:
            List of Product objects (or None if not found), in same order as skus
        """
        if not skus:
            return []

        # Single database query for all SKUs
        async with self.db_manager.session() as session:
            result = await session.execute(select(Product).where(Product.sku.in_(skus)))
            products = result.scalars().all()

        # Create SKU -> Product mapping
        product_map = {product.sku: product for product in products}

        # Return products in same order as input SKUs
        # Missing products are returned as None
        return [product_map.get(sku) for sku in skus]


# Convenience function for getting database session (used in tests)
async def get_db_session() -> Any:
    """Get database session (for testing)"""
    db_manager = DatabaseManager()
    return db_manager.session()
