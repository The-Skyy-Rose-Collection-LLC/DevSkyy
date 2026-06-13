# api/graphql/ — Strawberry GraphQL surface

Alternative read API alongside REST. Mounts at `/graphql` (defined in `main_enterprise.py` via the Strawberry/FastAPI adapter). GraphiQL playground enabled in non-production.

## Key files

- `schema.py` — `Query` root + compiled `strawberry.Schema`. `product(sku)` + `products(collection, limit, offset)`. `auto_camel_case=True`. `DisableIntrospection` added when `ENVIRONMENT=production`.
- `types.py` — `ProductType` with `from_db(product)` factory. JSON-decodes `images_json` defensively (catches `JSONDecodeError`/`TypeError`).
- `dataloaders/product_loader.py` — `ProductDataLoader` (aiodataloader) — see `dataloaders/CLAUDE.md`.
- `resolvers/product_resolver.py` — `get_products_from_db()` decorated with `@cached(ttl=300)` — see `resolvers/CLAUDE.md`.

## Conventions

- The `info.context` dict carries the per-request `product_loader`. Resolvers fall back to constructing a fresh loader if context lacks it.
- `limit` is clamped to `[1, 100]` inside the resolver — never trust client-supplied limits.
- N+1 prevention is mandatory for any new list resolver: extend `dataloaders/` and call `loader.load_many()`, not raw queries in a loop.
- Schema is compiled at import time. Adding a new type means adding it to `types.py`, then exposing a resolver in `schema.py` — no runtime registration.

## Don't

- Don't run SQL directly in `schema.py`. Resolvers belong in `resolvers/`, batch loads in `dataloaders/`.
- Don't expose mutations from GraphQL without explicit auth review. Current surface is read-only by design; write paths go through REST where webhook + audit hooks live.
- Don't import `database.db.DatabaseManager` from `schema.py` — keep the schema layer free of DB concerns.

## Related

- DB layer: `database/db.py` (`Product` model, `DatabaseManager`)
- Cache layer: `core/caching/multi_tier_cache.py` (the `@cached` decorator)
- FastAPI mount: `api/graphql_server.py`
