# api/graphql/resolvers/ — Resolver functions for GraphQL fields

Database query functions called from `schema.py` Query/Mutation fields. Split out from `schema.py` so caching, batching, and DB concerns stay isolated from the schema definition.

## Key files

- `product_resolver.py` — `get_products_from_db(collection, limit, offset)` decorated with `@cached(ttl=300, key_prefix="products_list")`. Filters `is_active == True`, optional `collection` filter, ordered `created_at DESC`. Returns `list[Product]`.
- `__init__.py` — package marker; resolvers are imported by `schema.py` directly, not re-exported.

## Conventions

- List resolvers cache via `core.caching.multi_tier_cache.cached` (L1 in-memory → L2 Redis). Default TTL 5 minutes. Cache key includes all filter args for granular invalidation.
- Single-entity lookups go through DataLoaders (`api/graphql/dataloaders/`), not direct resolvers — see `schema.py:product()`.
- Use SQLAlchemy 2.x style: `select(Model).where(...)`, `await session.execute(query)`, `result.scalars().all()`. No `Session.query()`.
- `noqa: E712` is allowed when comparing booleans against `True`/`False` in SQLAlchemy where clauses (`Product.is_active == True`) — the `is True` form does not generate the correct SQL.

## Don't

- Don't put resolver logic inside `schema.py` — the schema file owns type wiring, not data access.
- Don't bypass the cache decorator for read-heavy list endpoints. The 5-minute TTL is calibrated for the catalog's update cadence.
- Don't return Strawberry types from a resolver — return DB models, let the schema layer call `ProductType.from_db(...)`. Separation keeps types and DB models decoupled.

## Related

- Consumers: `api/graphql/schema.py`
- Cache layer: `core/caching/multi_tier_cache.py`
- DB layer: `database/db.py` (`Product`, `DatabaseManager`)
