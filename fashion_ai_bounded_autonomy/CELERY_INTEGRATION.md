# Celery Integration for Bounded Autonomy System

This document describes the async task processing integration using Celery and Redis.

## Overview

The bounded autonomy system uses Celery for asynchronous task processing while maintaining all security and approval requirements. Tasks run in the background but still respect bounded autonomy principles:

- ✅ All high-risk operations still require human approval
- ✅ All tasks are logged and auditable
- ✅ Tasks can be monitored and controlled
- ✅ Failed tasks are retried automatically
- ✅ Periodic tasks run on schedule

## Architecture

```
┌─────────────────┐
│  Bounded        │
│  Autonomy       │──────► Submit Task
│  Modules        │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Celery App     │
│  (celery_app.py)│
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Redis Broker   │◄──────► Workers
│  localhost:6379 │         (Multiple Queues)
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Task Execution │
│  (tasks.py)     │
└─────────────────┘
```

## Prerequisites

### 1. Redis Server

Redis must be running:

```bash
# Check if Redis is running
redis-cli ping

# If not running, start it
redis-server --daemonize yes

# Verify
redis-cli ping
# Should return: PONG
```

### 2. Python Dependencies

All required packages are already installed:
- celery==5.5.3
- redis (via kombu)
- kombu==5.5.4

## Task Queues

The system uses multiple queues for different task priorities:

| Queue | Purpose | Concurrency | Priority |
|-------|---------|-------------|----------|
| `bounded_autonomy_high_priority` | Approval notifications, urgent tasks | 4 workers | Highest |
| `bounded_autonomy_default` | General tasks | 2 workers | Normal |
| `bounded_autonomy_reports` | Report generation | 2 workers | Low |
| `bounded_autonomy_monitoring` | Health checks, metrics | 2 workers | Normal |
| `bounded_autonomy_data_processing` | Data ingestion, validation | 2 workers | Normal |

## Available Tasks

### Approval & Notifications

**`send_approval_notification_task`**
- Sends notification to operator when approval is required
- Retries: 3 attempts with 60s backoff
- Queue: high_priority

```python
from fashion_ai_bounded_autonomy.tasks import send_approval_notification_task

# Submit task
result = send_approval_notification_task.delay(
    action_id="action_123",
    agent_name="designer_agent",
    risk_level="high"
)
```

**`cleanup_expired_approvals_task`**
- Removes expired approval requests
- Runs: Hourly (automatic)
- Queue: default

### Data Processing

**`process_data_ingestion_task`**
- Processes data ingestion asynchronously
- Retries: 3 attempts with 120s backoff
- Queue: data_processing

```python
from fashion_ai_bounded_autonomy.tasks import process_data_ingestion_task

result = process_data_ingestion_task.delay(
    file_path="/path/to/data.csv",
    source_type="csv"
)
```

**`validate_data_task`**
- Validates and preprocesses data
- Queue: data_processing

### Report Generation

**`generate_daily_reports_task`**
- Generates daily summary reports
- Runs: Daily at midnight (automatic)
- Queue: reports

**`generate_weekly_report_task`**
- Generates weekly summary reports
- Queue: reports

**`export_metrics_task`**
- Exports performance metrics to CSV/JSON
- Queue: reports

```python
from fashion_ai_bounded_autonomy.tasks import export_metrics_task

result = export_metrics_task.delay(format="csv")
```

### Monitoring & Health

**`monitor_agent_health_task`**
- Checks health of all registered agents
- Runs: Every 5 minutes (automatic)
- Queue: monitoring

**`check_system_status_task`**
- Gets comprehensive system status
- Queue: monitoring

**`performance_snapshot_task`**
- Captures performance metrics snapshot
- Runs: Every 15 minutes (automatic)
- Queue: monitoring

### Task Execution

**`execute_approved_task_async`**
- Executes approved tasks asynchronously
- Retries: 3 attempts with 180s backoff
- Queue: default

## Starting Workers

### Quick Start

```bash
# Start all workers and beat scheduler
./fashion_ai_bounded_autonomy/start_celery_worker.sh
```

This starts:
- 5 worker processes (12 total worker threads)
- 1 beat scheduler for periodic tasks
- All logs in `logs/celery/`
- All PIDs in `logs/celery/pids/`

### Manual Start (for development)

```bash
# Start a single worker
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app worker \
    --loglevel=info \
    --concurrency=4

# Start beat scheduler
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app beat \
    --loglevel=info
```

## Stopping Workers

```bash
# Graceful shutdown of all workers
./fashion_ai_bounded_autonomy/stop_celery_worker.sh
```

## Monitoring

### Inspect Active Tasks

```bash
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app inspect active
```

### Inspect Worker Stats

```bash
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app inspect stats
```

### View Registered Tasks

```bash
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app inspect registered
```

### Monitor with Flower (optional)

```bash
# Install flower
pip install flower

# Start flower web UI
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app flower

# Access at http://localhost:5555
```

## Task Results

Tasks return AsyncResult objects that can be queried:

```python
from fashion_ai_bounded_autonomy.tasks import generate_daily_reports_task

# Submit task
result = generate_daily_reports_task.delay()

# Check status
print(result.state)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY

# Wait for result (blocking)
report = result.get(timeout=300)  # 5 minute timeout

# Check if ready (non-blocking)
if result.ready():
    if result.successful():
        print("Task succeeded:", result.result)
    else:
        print("Task failed:", result.traceback)
```

## Periodic Tasks (Celery Beat)

The following tasks run automatically:

| Task | Frequency | Purpose |
|------|-----------|---------|
| `generate_daily_reports_task` | Daily | Generate daily summaries |
| `cleanup_expired_approvals_task` | Hourly | Remove expired approvals |
| `monitor_agent_health_task` | Every 5 min | Check agent health |
| `performance_snapshot_task` | Every 15 min | Capture metrics |

## Error Handling

### Automatic Retries

Tasks with `max_retries` will retry automatically on failure:

```python
@celery_app.task(bind=True, max_retries=3)
def my_task(self):
    try:
        # Task logic
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60)
```

### Task Timeouts

- Soft timeout: 5 minutes (sends SIGTERM)
- Hard timeout: 10 minutes (sends SIGKILL)

Configure per-task:

```python
@celery_app.task(soft_time_limit=300, time_limit=600)
def my_long_task():
    pass
```

### Dead Letter Queue

Failed tasks after max retries are stored in Redis for investigation:

```bash
# Inspect failed tasks
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app inspect reserved
```

## Integration with Bounded Autonomy

### Approval Workflow

When a high-risk action requires approval:

1. Action submitted to `ApprovalSystem`
2. System stores in database
3. **Celery task** sends notification to operator
4. Operator reviews via CLI or API
5. On approval, **Celery task** executes action asynchronously

### Data Pipeline

When processing large datasets:

1. Data file uploaded
2. **Celery task** validates and preprocesses
3. Results stored in validated/ directory
4. **Celery task** generates validation report

### Monitoring

Every 5 minutes:

1. **Celery task** checks agent health
2. Unhealthy agents logged
3. **Celery task** sends notifications if needed
4. Auto-recovery attempted (bounded by max retries)

## Configuration

### Redis Configuration

Edit `fashion_ai_bounded_autonomy/celery_app.py`:

```python
celery_app.conf.update(
    broker='redis://localhost:6379/0',  # Redis DB 0 for broker
    backend='redis://localhost:6379/1',  # Redis DB 1 for results
)
```

### Task Time Limits

```python
celery_app.conf.update(
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,  # 10 minutes
)
```

### Worker Concurrency

```python
celery_app.conf.update(
    worker_prefetch_multiplier=4,  # Tasks per worker
    worker_max_tasks_per_child=1000,  # Restart after N tasks
)
```

## Logs

All logs are stored in `logs/celery/`:

```
logs/celery/
├── bounded_autonomy_default.log
├── bounded_autonomy_high_priority.log
├── bounded_autonomy_reports.log
├── bounded_autonomy_monitoring.log
├── bounded_autonomy_data_processing.log
└── celery_beat.log
```

View logs:

```bash
# Tail worker logs
tail -f logs/celery/bounded_autonomy_high_priority.log

# View beat scheduler log
tail -f logs/celery/celery_beat.log
```

## Troubleshooting

### Workers Not Starting

```bash
# Check Redis
redis-cli ping

# Check for port conflicts
lsof -i :6379

# Check logs
tail -100 logs/celery/bounded_autonomy_default.log
```

### Tasks Not Executing

```bash
# Check if workers are consuming from the queue
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app inspect active

# Check registered tasks
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app inspect registered

# Purge all pending tasks (CAUTION!)
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app purge
```

### High Memory Usage

```bash
# Reduce worker concurrency
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app worker --concurrency=2

# Enable worker auto-restart
celery_app.conf.worker_max_tasks_per_child = 100
```

## Security Considerations

1. **No External Network Access**: Tasks run in local-only mode by default
2. **Approval Required**: High-risk operations still require human approval
3. **Audit Logging**: All task executions are logged
4. **Redis Security**: Use password authentication in production
5. **Task Serialization**: Only JSON serialization (no pickle)

### Production Redis Setup

```bash
# Add password to redis.conf
requirepass YOUR_STRONG_PASSWORD

# Update celery_app.py
broker='redis://:YOUR_STRONG_PASSWORD@localhost:6379/0'
```

## Performance

### Throughput

- High priority queue: ~40 tasks/minute
- Default queue: ~20 tasks/minute
- Reports queue: ~10 tasks/minute

### Latency

- Task submission: <10ms
- Task pickup: <100ms (depends on worker prefetch)
- Task execution: varies by task

### Scaling

To handle more load:

```bash
# Add more workers
./fashion_ai_bounded_autonomy/start_celery_worker.sh

# Or increase concurrency
celery -A fashion_ai_bounded_autonomy.celery_app:celery_app worker --concurrency=8
```

## Best Practices

1. **Use Task IDs**: Always store task IDs for tracking
2. **Handle Failures**: Implement retry logic with exponential backoff
3. **Monitor Queues**: Watch queue lengths to prevent backlog
4. **Log Everything**: Use structured logging for debugging
5. **Test Tasks**: Write unit tests for task logic
6. **Graceful Shutdown**: Always use stop script, not kill -9

## Example Usage

### Submit a Task

```python
from fashion_ai_bounded_autonomy.tasks import submit_task_async

# Submit task by name
result = submit_task_async(
    'send_approval_notification',
    action_id='action_123',
    agent_name='designer_agent',
    risk_level='high'
)

# Get task ID
task_id = result.id
print(f"Task submitted: {task_id}")

# Check result later
from celery.result import AsyncResult
task_result = AsyncResult(task_id)
print(f"Status: {task_result.state}")
```

### Chain Tasks

```python
from celery import chain
from fashion_ai_bounded_autonomy.tasks import (
    process_data_ingestion_task,
    validate_data_task,
    generate_validation_report_task
)

# Create task chain
workflow = chain(
    process_data_ingestion_task.s("/path/to/data.csv", "csv"),
    validate_data_task.s(),
    generate_validation_report_task.s()
)

# Execute chain
result = workflow.apply_async()
```

## Support

For issues or questions:
1. Check logs in `logs/celery/`
2. Review task status with `celery inspect`
3. Consult bounded autonomy documentation
4. Verify Redis is running and accessible

---

**Last Updated**: 2025-11-04
**Celery Version**: 5.5.3
**Redis Version**: 7.0.15
