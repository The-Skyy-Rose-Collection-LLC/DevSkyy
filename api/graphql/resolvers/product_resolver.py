"""
Product GraphQL Resolvers
==========================

Resolver functions for product queries using DataLoader for efficient batching.
List queries use @cached (5 min TTL) to avoid repeated DB calls for the same filters.
"""

from sqlalchemy import select

from core.caching.multi_tier_cache import cached
from database.db import DatabaseManager, Product


@cached(ttl=300, key_prefix="products_list")
async def get_products_from_db(
    collection: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Product]:
    """
    Fetch products from database with optional collection filter.

    Cached for 5 minutes (L1 in-memory → L2 Redis).
    Cache key includes all filter parameters for granular invalidation.
    Used by the products() list resolver.
    """
    db = DatabaseManager()
    async with db.session() as session:
        query = select(Product).where(Product.is_active == True)  # noqa: E712
        if collection:
            query = query.where(Product.collection == collection)
        query = query.limit(limit).offset(offset).order_by(Product.created_at.desc())
        result = await session.execute(query)
        return list(result.scalars().all())
