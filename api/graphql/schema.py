"""
GraphQL Schema Definition
==========================

Strawberry GraphQL schema with DataLoader for N+1 prevention.
Mounts at /graphql with GraphiQL interactive playground enabled.

Usage:
    from api.graphql.schema import schema
    # or via graphql_router for FastAPI mounting
"""

from __future__ import annotations

from typing import List, Optional

import strawberry
from strawberry.types import Info

from api.graphql.dataloaders.product_loader import ProductDataLoader
from api.graphql.resolvers.product_resolver import get_products_from_db
from api.graphql.types import ProductType


@strawberry.type
class Query:
    """Root query type"""

    @strawberry.field(description="Fetch a single product by SKU")
    async def product(
        self,
        sku: str,
        info: Info,
    ) -> Optional[ProductType]:
        """
        Get single product by SKU using DataLoader for batching.
        Multiple concurrent calls are automatically batched into one DB query.
        """
        loader: ProductDataLoader = info.context.get("product_loader") or ProductDataLoader()
        db_product = await loader.load(sku)
        if db_product is None:
            return None
        return ProductType.from_db(db_product)

    @strawberry.field(description="List products with optional collection filter")
    async def products(
        self,
        collection: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ProductType]:
        """
        List products with optional collection filter and pagination.
        Results are ordered by newest first.
        """
        # Clamp limit to prevent abuse
        limit = max(1, min(limit, 100))
        db_products = await get_products_from_db(
            collection=collection,
            limit=limit,
            offset=offset,
        )
        return [ProductType.from_db(p) for p in db_products]


# Compile the schema
schema = strawberry.Schema(
    query=Query,
    config=strawberry.schema.config.StrawberryConfig(auto_camel_case=True),
)
