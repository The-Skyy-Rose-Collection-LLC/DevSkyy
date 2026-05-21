# core/cqrs/ — Command Query Responsibility Segregation

**Separate buses for writes and reads.** Commands (mutations) go through `CommandBus`, queries (reads) through `QueryBus`. Each handler is registered once per type.

## Public Surface (`core/cqrs/__init__.py`)

- `Command` — base class for write requests (`command_bus.py`)
- `CommandBus` — `register_handler(CmdType, handler)`, `execute(cmd)`
- `Query` — base class for read requests (`query_bus.py`)
- `QueryBus` — `register_handler(QueryType, handler)`, `execute(query)`

## Hard Rules

- **One handler per type** — re-registration silently overwrites. Tests / startup wire each handler once
- **Commands mutate, return ack or ID** — never return business state; that's a query
- **Queries are read-only** — never mutate state inside a query handler
- Commands publish events to `core.events.event_bus` after success. Queries do not
- Built-in: `create_product_handler` registered in `command_bus.py`

## Patterns

```python
from core.cqrs import Command, CommandBus

@dataclass(frozen=True)
class CreateProduct(Command):
    sku: str
    name: str

async def handle_create_product(cmd: CreateProduct) -> str:
    ...  # persist, publish event, return ID

bus = CommandBus()
bus.register_handler(CreateProduct, handle_create_product)
product_id = await bus.execute(CreateProduct(sku="br-001", name="..."))
```

## Consumers

- `api/v1/products` — POST/PUT/DELETE dispatch through `CommandBus`
- `api/v1/products` — GET dispatches through `QueryBus`
- `agents/core/commerce/*` — agent-issued mutations go through `CommandBus`
