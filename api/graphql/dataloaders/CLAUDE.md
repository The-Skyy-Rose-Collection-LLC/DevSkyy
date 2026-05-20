<claude-mem-context>

</claude-mem-context>

# api/graphql/dataloaders/ — N+1 prevention via aiodataloader

Batches concurrent GraphQL field resolutions into single DB queries. One loader per entity type. Lives here (not in `core/`) because DataLoaders are GraphQL-specific lifecycle objects.

## Key files

- `product_loader.py` — `ProductDataLoader(DataLoader)` — batches by SKU, `max_batch_size=100`, request-scoped `cache=True`. `_batch_load_fn(skus)` runs one `SELECT WHERE sku IN (...)` then maps results back into input order, returning `None` for misses.
- `__init__.py` — exports `ProductDataLoader`.

## Conventions

- One loader instance per request (typically attached to `info.context["product_loader"]` in the GraphQL ASGI adapter). Sharing loaders across requests breaks request-scoped caching and leaks stale state.
- Always return results in the same order as input keys. Missing entities are `None`, never omitted — DataLoader contract requires positional alignment.
- Use `select(...).where(col.in_(keys))` — never iterate keys and run one query each.
- New loaders subclass `DataLoader`, take a `DatabaseManager` (or whichever store), implement `_batch_load_fn(self, keys) -> list[T | None]`.

## Don't

- Don't add business logic to the loader. It's a batched fetch primitive; filtering/sorting belongs in resolvers.
- Don't enable `cache=False` unless you have a concrete reason — request-scoped caching is the whole point of the layer.
- Don't raise on missing keys. Return `None` and let the resolver decide whether absence is an error.

## Related

- Consumers: `api/graphql/schema.py`
- DB layer: `database/db.py`
- aiodataloader docs: https://github.com/syrusakbary/aiodataloader
