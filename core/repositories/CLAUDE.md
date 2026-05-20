# core/repositories/ — Data access ports (repository interfaces)

Generic and domain-specific repository ABCs. Encapsulates persistence behind a stable interface so business code does not depend on SQL, HTTP, or file-store details. The `database/` layer implements; this directory only defines.

## Key files

- `interfaces.py` — `IRepository[T]` generic ABC with `get_by_id`, `create`, `update`, `delete`, plus list/query helpers. Domain specializations: `IUserRepository`, `IProductRepository`, `IOrderRepository` — each extends `IRepository[T]` with the queries that domain needs.
- `__init__.py` — Re-exports the four interfaces.

## Conventions

- Code that needs to read or write a domain entity depends on the matching `I*Repository` — never on a concrete class in `database/`.
- Method signatures take and return domain types (Pydantic models, dataclasses) — never SQLAlchemy ORM rows.
- New domain entity → add the specialized ABC here (e.g., `IInvoiceRepository`) before writing the SQL implementation under `database/`.
- Mock these in unit tests via in-memory fakes that satisfy the ABC. The mock-shaped fixtures live alongside test modules, not here.
- `IRepository[T]` is generic on the domain type — use `TypeVar("T")` already declared in the module; don't introduce parallel type vars.

## Don't

- Don't bake SQL, HTTP, or file-path details into the interface signatures. The point of the port is to hide those.
- Don't return ORM rows from any method declared here. Callers must receive domain types.
- Don't expand the standard CRUD surface beyond `get_by_id / create / update / delete / list / find` without checking whether a domain-specialized method belongs on the subclass instead.
- Don't import from `database/`. Dependency runs `database → core.repositories`, not the reverse.

## Related

- `core/CLAUDE.md` — parent foundation layer
- `database/` — SQL / ORM implementations of these ports
- `core/services/CLAUDE.md` — sibling service ports
- `core/errors/CLAUDE.md` — `DevSkyError` subclasses raised by implementations
