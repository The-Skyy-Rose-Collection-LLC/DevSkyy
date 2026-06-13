# core/events/ — Event Sourcing Infrastructure

**Immutable append-only event store + in-process pub/sub bus.** Foundation for CQRS reads and audit trails.

## Public Surface (`core/events/__init__.py`)

- `Event` — immutable event dataclass (`event_store.py`)
- `EventStore` — append-only log with `append`, `get_events`, `replay`, `apply_event`
- `EventBus` — `subscribe(event_type, handler)`, `publish(event)`, `get_dead_letters()`, `clear_dead_letters()`
- `event_bus` — **global singleton instance** (`event_bus.py`)

## Hard Rules

- **Events are immutable** — never mutate an `Event` after construction. Build a new one
- **In-process bus** — `EventBus` is a Python-process-local pub/sub. Cross-process events require Redis Streams or Kafka (not provided here)
- **Dead-letter queue is the safety net** — handlers that raise land in `event_bus.get_dead_letters()`. Drain in long-running services or memory grows
- New event types: define an `Event` subclass in the producing module. Register handlers via `event_bus.subscribe(EventClass, handler_fn)`
- Tests MUST call `event_bus.clear_dead_letters()` between cases (singleton state leaks)

## Patterns

```python
from core.events import Event, event_bus

class ProductCreated(Event):
    sku: str
    name: str

async def handle_product_created(event: ProductCreated) -> None:
    ...

event_bus.subscribe(ProductCreated, handle_product_created)
await event_bus.publish(ProductCreated(sku="br-001", name="..."))
```

## Existing Handlers

- `event_handlers.py:ProductEventHandler` — catalog change handler with `handle()` + `subscribe()` methods

## Consumers

- `api/v1/products` — emits `ProductCreated` / `ProductUpdated` on writes
- `core/cqrs` — command handlers publish events; query handlers replay from store


