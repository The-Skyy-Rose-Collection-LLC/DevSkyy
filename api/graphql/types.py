"""
GraphQL Type Definitions
=========================

Strawberry type definitions for the DevSkyy GraphQL schema.
"""

from __future__ import annotations

import json
from typing import List, Optional

import strawberry


@strawberry.type
class ProductType:
    """GraphQL Product type — maps to the database Product model"""

    id: str
    sku: str
    name: str
    description: Optional[str]
    price: float
    compare_price: Optional[float]
    collection: Optional[str]
    is_active: bool
    images: List[str]

    @staticmethod
    def from_db(product: object) -> "ProductType":
        """Convert database Product model to GraphQL ProductType"""
        images: List[str] = []
        if hasattr(product, "images_json") and product.images_json:  # type: ignore[union-attr]
            try:
                images = json.loads(product.images_json)  # type: ignore[union-attr]
            except (json.JSONDecodeError, TypeError):
                images = []

        return ProductType(
            id=product.id,  # type: ignore[union-attr]
            sku=product.sku,  # type: ignore[union-attr]
            name=product.name,  # type: ignore[union-attr]
            description=product.description,  # type: ignore[union-attr]
            price=product.price,  # type: ignore[union-attr]
            compare_price=getattr(product, "compare_price", None),
            collection=product.collection,  # type: ignore[union-attr]
            is_active=product.is_active,  # type: ignore[union-attr]
            images=images,
        )
