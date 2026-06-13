# aos/ — Agent Operating System micro-kernel

AOS is the runtime substrate for all AI agent execution in DevSkyy. It provides spawn lifecycle, policy enforcement, inter-process messaging, audit, cognitive planning, memory, and self-healing — without modifying the underlying `EnhancedSuperAgent` classes.

## Key files

- `__init__.py` — re-exports the public surface: `Kernel`, `SpawnRequest`, `AgentProcess`, `AuditTrail`

## Subsystems

| Package | Role |
|---------|------|
| `kernel/` | Coordinator — boots and wires all subsystems |
| `adapters/` | Non-invasive wrapper around existing SuperAgents |
| `governance/` | Policy, approval, budget, audit trail |
| `ipc/` | Typed async pub/sub message bus |
| `cognition/` | Goal decomposition, planning, reflection |
| `healing/` | Circuit breaker + healing director |
| `memory/` | Namespaced TTL key/value store per agent PID |
| `modules/` | importlib-based dynamic module loader |
| `observability/` | Metrics, health, fine-tune buffer |
| `runtime/` | `AgentContainer` execution sandbox |
| `shell/` | Interactive REPL + command dispatch |

## Conventions

- All async. Every public lifecycle method is `async`. Sync wrappers are not provided.
- Pydantic models use `model_config = {"frozen": True}` for immutability — see `aos/cognition/types.py`.
- `StrEnum` for all categorical constants (`AuditEventType`, `MessageType`, `HealAction`, etc.).
- `Kernel` is the only entry point for spawning. Never instantiate `ProcessManager`, `MessageBus`, or `AuditTrail` directly in application code.

## Don't

- Don't import from subsystem internals past their `__init__.py` in application code — use `from aos import Kernel, SpawnRequest`.
- Don't call `EnhancedSuperAgent.execute()` directly from kernel code — always go through `SuperAgentAdapter`.
- Don't add synchronous I/O to any module that runs inside the kernel event loop.

## Related

- `agents/` — the `EnhancedSuperAgent` classes that AOS wraps
- `tests/aos/` — full test suite mirroring this package structure
- `main_enterprise.py` — boots the Kernel at startup
