"""
GraphQL Server Router
======================

Mounts Strawberry GraphQL at /graphql with:
  - GraphiQL interactive playground (dev only)
  - DataLoader context injection (per-request N+1 prevention)
  - Correlation ID propagation

Include in main_enterprise.py:
    from api.graphql_server import graphql_router
    app.include_router(graphql_router, prefix="/graphql", tags=["GraphQL"])
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import Request
from strawberry.fastapi import GraphQLRouter

from api.graphql.dataloaders.product_loader import ProductDataLoader
from api.graphql.schema import schema

# Enable GraphiQL playground and introspection in development, disable in production
_is_production = os.getenv("ENVIRONMENT", "development") == "production"
_graphiql_enabled = not _is_production


async def _get_context(request: Request) -> dict[str, Any]:
    """
    Build per-request GraphQL context.

    Injects:
    - product_loader: Fresh DataLoader per request (request-scoped caching)
    - correlation_id: For distributed tracing
    - request: Original FastAPI request
    """
    return {
        "request": request,
        "product_loader": ProductDataLoader(),
        "correlation_id": request.headers.get("X-Correlation-ID", ""),
    }


# Mount Strawberry GraphQL as a FastAPI sub-router
graphql_router = GraphQLRouter(
    schema,
    graphql_ide="graphiql" if _graphiql_enabled else None,
    allow_queries_via_get=not _is_production,
    context_getter=_get_context,
)
