# DevSkyy Analytics Module Patterns

Patterns extracted from analytics module implementation session (2026-01-24).

## Pattern 1: DevSkyError Parameter Convention

**Context**: Custom exception handling in DevSkyy

**Problem**: `DevSkyError` uses `code` not `error_code` as the parameter name.

**Wrong**:
```python
raise DevSkyError(
    message="Failed to evaluate",
    error_code=DevSkyErrorCode.INTERNAL_ERROR,  # Wrong!
)
```

**Correct**:
```python
raise DevSkyError(
    message="Failed to evaluate",
    code=DevSkyErrorCode.INTERNAL_ERROR,  # Correct
)
```

---

## Pattern 2: Falsy Value Check for Numeric Fields

**Context**: When checking if a numeric value should be processed

**Problem**: `if numeric_value` treats `0` as falsy, skipping valid zero values.

**Wrong**:
```python
if numeric_value:  # Skips when value is 0
    process(numeric_value)
```

**Correct**:
```python
if numeric_value is not None:  # Handles 0 correctly
    process(numeric_value)
```

---

## Pattern 3: PostgreSQL Array Format for SQLAlchemy Raw Queries

**Context**: Inserting array values with raw SQL in SQLAlchemy

**Pattern**:
```python
# Convert Python list to PostgreSQL array literal
channels_array = (
    "{" + ",".join(request.notification_channels) + "}"
    if request.notification_channels
    else "{}"
)

# Use in parameterized query
await db.execute(
    text("INSERT INTO table (channels) VALUES (:channels)"),
    {"channels": channels_array}
)
```

---

## Pattern 4: Mock Side Effect for Stats Tracking

**Context**: Testing services that update internal statistics

**Problem**: Using `return_value` doesn't allow the mock to update stats.

**Wrong**:
```python
mock_send_slack.return_value = True
# Stats won't be updated
```

**Correct**:
```python
async def mock_send_slack(notification):
    notifier._stats["slack_sent"] += 1
    return True

mock_send_slack.side_effect = mock_send_slack
```

---

## Pattern 5: Role-Based Access for Analytics APIs

**Context**: FastAPI endpoint authorization

**Pattern**:
```python
from security import TokenPayload, require_roles

@router.get("/endpoint")
async def get_data(
    user: TokenPayload = Depends(require_roles(["admin", "analyst"])),
    db: AsyncSession = Depends(get_db),
) -> Response:
    # admin and analyst roles can access
    pass
```

---

## Pattern 6: Dynamic SQL Update Query Building

**Context**: Partial updates where only provided fields should be updated

**Pattern**:
```python
updates = []
params = {"id": item_id}

if request.name is not None:
    updates.append("name = :name")
    params["name"] = request.name

if request.enabled is not None:
    updates.append("is_enabled = :enabled")
    params["enabled"] = request.enabled

# Always update updated_by
updates.append("updated_by = :updated_by")
params["updated_by"] = user.sub

update_clause = ", ".join(updates)
query = text(f"UPDATE table SET {update_clause} WHERE id = :id RETURNING *")
await db.execute(query, params)
```

---

## Pattern 7: Alert Metadata Builder Helper

**Context**: Converting database rows to response models with nested structures

**Pattern**:
```python
def build_alert_metadata(
    triggered_at: datetime,
    metric_value: float | None,
    notifications_json: str | None,
    context_json: str | None,
    alert_config: Any | None = None,
) -> AlertMetadata:
    """Build metadata from database fields with safe parsing."""
    notifications = parse_json_field(notifications_json)
    context = parse_json_field(context_json)

    return AlertMetadata(
        trigger_time=triggered_at.isoformat() if triggered_at else "",
        metric_value=metric_value,
        condition_type=alert_config.condition_type if alert_config else None,
        notifications_sent=[...],
        context=context if isinstance(context, dict) else {},
    )
```

---

## Pattern 8: Bulk Operation with Partial Success

**Context**: Processing multiple items where some may fail

**Pattern**:
```python
results = []
succeeded = 0
failed = 0

for item_id in request.item_ids:
    try:
        # Process item
        await process(item_id)
        results.append(Result(id=item_id, success=True))
        succeeded += 1
    except Exception as e:
        results.append(Result(id=item_id, success=False, error=str(e)))
        failed += 1

await db.commit()

return BulkResponse(
    status="success" if failed == 0 else "partial",
    total_succeeded=succeeded,
    total_failed=failed,
    results=results,
)
```

---

## Tags

`devskyy` `analytics` `fastapi` `sqlalchemy` `postgresql` `testing` `error-handling`
