# Multi-Agent Conflict Resolution

**Purpose**: Standard procedures for resolving task conflicts when multiple agents operate on shared resources.

---

## Overview

### Agent Ecosystem
```
┌─────────────────────────────────────────────────────────────┐
│                    DevSkyy Orchestrator                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Content  │  │ Catalog  │  │   3D     │  │ Customer │    │
│  │  Agent   │  │  Agent   │  │ Pipeline │  │ Service  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │             │             │             │           │
│       └─────────────┴──────┬──────┴─────────────┘           │
│                            │                                 │
│                    ┌───────▼───────┐                        │
│                    │ Shared State  │                        │
│                    │   Manager     │                        │
│                    └───────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Conflict Types
| Type | Description | Example |
|------|-------------|---------|
| Resource Lock | Multiple agents accessing same resource | Two agents editing same product |
| Data Race | Concurrent writes to same field | Simultaneous price updates |
| Sequence | Operations executed out of order | Image upload before product create |
| Priority | Multiple tasks competing for resources | Bulk import vs real-time order |

---

## Locking Mechanism

### Resource Lock Structure
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ResourceLock:
    resource_type: str  # "product", "page", "order", etc.
    resource_id: str    # SKU, page ID, order ID
    agent_id: str       # Agent holding lock
    acquired_at: datetime
    expires_at: datetime
    operation: str      # Description of operation

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
```

### Lock Acquisition
```python
async def acquire_lock(
    resource_type: str,
    resource_id: str,
    agent_id: str,
    operation: str,
    timeout_seconds: int = 300
) -> Optional[ResourceLock]:
    """
    Attempt to acquire a lock on a resource.

    Returns:
        ResourceLock if successful, None if resource is locked
    """

    existing_lock = await get_lock(resource_type, resource_id)

    if existing_lock and not existing_lock.is_expired:
        # Log conflict
        log_conflict(
            resource_type=resource_type,
            resource_id=resource_id,
            requesting_agent=agent_id,
            holding_agent=existing_lock.agent_id,
            operation=operation
        )
        return None

    # Create new lock
    lock = ResourceLock(
        resource_type=resource_type,
        resource_id=resource_id,
        agent_id=agent_id,
        acquired_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(seconds=timeout_seconds),
        operation=operation
    )

    await save_lock(lock)
    return lock
```

### Lock Release
```python
async def release_lock(
    resource_type: str,
    resource_id: str,
    agent_id: str
) -> bool:
    """
    Release a lock held by an agent.

    Returns:
        True if lock was released, False if agent didn't hold lock
    """

    existing_lock = await get_lock(resource_type, resource_id)

    if not existing_lock:
        return True  # No lock to release

    if existing_lock.agent_id != agent_id:
        log_warning(
            f"Agent {agent_id} tried to release lock held by {existing_lock.agent_id}"
        )
        return False

    await delete_lock(resource_type, resource_id)
    return True
```

---

## Priority System

### Agent Priority Levels
| Priority | Agent Type | Use Case |
|----------|------------|----------|
| P0 | Emergency | Security issues, data corruption |
| P1 | Customer-facing | Order processing, support tickets |
| P2 | Business-critical | Inventory sync, price updates |
| P3 | Background | 3D processing, analytics |
| P4 | Maintenance | Cleanup, optimization |

### Priority Resolution
```python
PRIORITY_MAP = {
    "security_agent": 0,
    "order_agent": 1,
    "customer_service_agent": 1,
    "inventory_agent": 2,
    "catalog_agent": 2,
    "content_agent": 3,
    "3d_pipeline_agent": 3,
    "analytics_agent": 4,
    "cleanup_agent": 4
}

async def resolve_conflict_by_priority(
    lock: ResourceLock,
    requesting_agent: str,
    operation: str
) -> str:
    """
    Resolve conflict based on agent priority.

    Returns:
        "granted" - Requesting agent gets lock
        "queued" - Requesting agent added to queue
        "denied" - Operation should not proceed
    """

    holding_priority = PRIORITY_MAP.get(lock.agent_id, 5)
    requesting_priority = PRIORITY_MAP.get(requesting_agent, 5)

    if requesting_priority < holding_priority:
        # Higher priority agent - force release
        await force_release_lock(lock)
        return "granted"
    elif requesting_priority == holding_priority:
        # Same priority - queue
        await add_to_queue(lock.resource_type, lock.resource_id, requesting_agent, operation)
        return "queued"
    else:
        # Lower priority - wait
        return "queued"
```

---

## Queue Management

### Operation Queue
```python
from collections import deque
from typing import NamedTuple

class QueuedOperation(NamedTuple):
    agent_id: str
    operation: str
    priority: int
    queued_at: datetime

# Per-resource queues
resource_queues: dict[str, deque[QueuedOperation]] = {}

async def process_queue(resource_type: str, resource_id: str) -> None:
    """Process queued operations after lock release."""

    key = f"{resource_type}:{resource_id}"
    queue = resource_queues.get(key, deque())

    if not queue:
        return

    # Sort by priority, then by queue time
    sorted_ops = sorted(queue, key=lambda x: (x.priority, x.queued_at))

    for op in sorted_ops:
        # Attempt to execute queued operation
        lock = await acquire_lock(
            resource_type=resource_type,
            resource_id=resource_id,
            agent_id=op.agent_id,
            operation=op.operation
        )

        if lock:
            await notify_agent(op.agent_id, "lock_acquired", resource_id)
            break
```

---

## Conflict Scenarios

### Scenario 1: Simultaneous Product Updates
```
Agent A: Updating product price
Agent B: Updating product description

Resolution:
1. First agent to acquire lock proceeds
2. Second agent queued
3. After first completes, second receives lock
4. Both operations complete successfully
```

### Scenario 2: Bulk Import vs Real-Time Order
```
Agent A: Bulk importing 100 products (P3)
Agent B: Processing customer order (P1)

Resolution:
1. Order agent has higher priority
2. Bulk import pauses current batch
3. Order processing completes
4. Bulk import resumes
```

### Scenario 3: 3D Pipeline Timeout
```
Agent A: 3D model generation (taking > 5 minutes)
Agent B: Content update to same product

Resolution:
1. Check if 3D lock is expired
2. If expired, grant to content agent
3. 3D agent receives "lock_expired" notification
4. 3D agent must re-acquire lock to continue
```

---

## Deadlock Prevention

### Detection
```python
async def detect_deadlock(agents: list[str]) -> bool:
    """
    Detect circular wait conditions.

    Returns True if deadlock detected.
    """

    # Build wait-for graph
    wait_for: dict[str, set[str]] = {}

    for agent in agents:
        waiting_on = await get_agent_waiting_on(agent)
        if waiting_on:
            wait_for[agent] = waiting_on

    # Detect cycle using DFS
    visited = set()
    rec_stack = set()

    def has_cycle(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in wait_for.get(node, set()):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    for agent in agents:
        if agent not in visited:
            if has_cycle(agent):
                return True

    return False
```

### Resolution
```python
async def resolve_deadlock(involved_agents: list[str]) -> None:
    """
    Resolve deadlock by releasing lowest priority lock.
    """

    # Find lowest priority agent
    lowest = min(involved_agents, key=lambda a: PRIORITY_MAP.get(a, 5))

    # Release its locks
    locks = await get_locks_held_by(lowest)

    for lock in locks:
        await force_release_lock(lock)
        log_deadlock_resolution(
            agent=lowest,
            resource=f"{lock.resource_type}:{lock.resource_id}"
        )

    # Notify agent
    await notify_agent(lowest, "deadlock_resolved", "retry_operation")
```

---

## Merge Strategies

### For Product Data
```python
def merge_product_updates(
    base: dict,
    update_a: dict,
    update_b: dict
) -> dict:
    """
    Merge concurrent product updates.

    Strategy: Last-write-wins per field, with conflict log.
    """

    result = base.copy()
    conflicts = []

    all_keys = set(update_a.keys()) | set(update_b.keys())

    for key in all_keys:
        val_a = update_a.get(key)
        val_b = update_b.get(key)

        if val_a is not None and val_b is not None:
            if val_a != val_b:
                # Conflict - log and use latest
                conflicts.append({
                    "field": key,
                    "value_a": val_a,
                    "value_b": val_b,
                    "chosen": val_b  # Last write wins
                })
                result[key] = val_b
            else:
                result[key] = val_a
        elif val_a is not None:
            result[key] = val_a
        elif val_b is not None:
            result[key] = val_b

    if conflicts:
        log_merge_conflicts(conflicts)

    return result
```

---

## Logging Requirements

All conflicts must be logged:

```json
{
    "timestamp": "2025-12-02T10:30:00Z",
    "conflict_type": "resource_lock",
    "resource_type": "product",
    "resource_id": "SR-TOP-045",
    "holding_agent": "catalog_agent",
    "requesting_agent": "content_agent",
    "resolution": "queued",
    "queue_position": 1,
    "estimated_wait_seconds": 30
}
```

Log location: `/logs/conflict_resolution.log`

---

## Escalation Triggers

Escalate to human when:
- Deadlock persists > 5 minutes
- Same conflict occurs > 3 times in 1 hour
- P0/P1 agent blocked by P3/P4 agent
- Data integrity at risk

See `escalation_protocol.md` for escalation procedures.

---

**Last Updated**: 2025-12-02
**Owner**: Platform Team
**Review Cycle**: Monthly
