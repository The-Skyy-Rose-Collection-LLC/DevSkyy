# Bounded Autonomy File References

This document lists all file and directory references used by the bounded autonomy system to ensure consistency across modules.

## Database Files

| File Path | Module | Purpose | Config Parameter |
|-----------|--------|---------|------------------|
| `fashion_ai_bounded_autonomy/review_queue.db` | approval_system.py:37 | Approval queue and history | `db_path` |
| `fashion_ai_bounded_autonomy/review_queue.db` | bounded_autonomy_wrapper.py:404 | Reference for queue path | N/A |
| `fashion_ai_bounded_autonomy/performance_metrics.db` | performance_tracker.py:30 | KPI metrics and proposals | `db_path` |

## JSON Files

| File Path | Module | Purpose | Config Parameter |
|-----------|--------|---------|------------------|
| `fashion_ai_bounded_autonomy/review_queue.json` | bounded_autonomy_wrapper.py:407 | Review queue JSON format | N/A |
| `fashion_ai_bounded_autonomy/proposals.json` | performance_tracker.py:35 | Performance improvement proposals | N/A |
| `fashion_ai_bounded_autonomy/notifications.json` | watchdog.py:234 | Operator notifications | N/A |

## Runtime Directories

| Directory Path | Module | Purpose | Config Parameter |
|----------------|--------|---------|------------------|
| `fashion_ai_bounded_autonomy/quarantine/` | data_pipeline.py:31 | Invalid data quarantine | `config_path` |
| `fashion_ai_bounded_autonomy/validated/` | data_pipeline.py:32 | Validated data storage | `config_path` |
| `fashion_ai_bounded_autonomy/output/` | data_pipeline.py:33 | General output files | `config_path` |
| `fashion_ai_bounded_autonomy/output/` | report_generator.py:28 | Generated reports | `output_path` |
| `fashion_ai_bounded_autonomy/output/summaries/` | report_generator.py:32 | Daily/weekly summaries | N/A |
| `fashion_ai_bounded_autonomy/output/metrics/` | report_generator.py:33 | Metrics exports | N/A |
| `fashion_ai_bounded_autonomy/output/validation/` | report_generator.py:34 | Validation reports | N/A |
| `fashion_ai_bounded_autonomy/output/recommendations/` | report_generator.py:35 | Recommendation reports | N/A |

## Log Directories

| Directory Path | Module | Purpose | Config Parameter |
|----------------|--------|---------|------------------|
| `logs/audit/` | bounded_autonomy_wrapper.py:106 | Audit logs (*.jsonl) | `audit_log_path` |
| `logs/incidents/` | watchdog.py:45 | Incident logs (*.jsonl) | N/A |
| `logs/data_pipeline/` | data_pipeline.py:289 | Data pipeline logs (*.jsonl) | N/A |

## Configuration Files (Source Control)

| File Path | Purpose | Should Commit |
|-----------|---------|---------------|
| `fashion_ai_bounded_autonomy/config/architecture.yaml` | System architecture definition | ✅ YES |
| `fashion_ai_bounded_autonomy/config/agents_config.json` | Agent roles and capabilities | ✅ YES |
| `fashion_ai_bounded_autonomy/config/dataflow.yaml` | Data pipeline configuration | ✅ YES |
| `fashion_ai_bounded_autonomy/config/monitor.yaml` | Monitoring configuration | ✅ YES |
| `fashion_ai_bounded_autonomy/config/security_policy.txt` | Security rules | ✅ YES |

## .gitignore Coverage

### Generic Patterns (Already Covered)
- `*.db` → Covers all database files
- `*.sqlite` → Covers SQLite files
- `*.sqlite3` → Covers SQLite3 files
- `logs/` → Covers all log directories
- `*.log` → Covers all log files
- `htmlcov/` → Covers test coverage HTML reports
- `.pytest_cache/` → Covers pytest cache

### Bounded Autonomy Specific Patterns
```
fashion_ai_bounded_autonomy/notifications.json
fashion_ai_bounded_autonomy/proposals.json
fashion_ai_bounded_autonomy/review_queue.json
fashion_ai_bounded_autonomy/quarantine/
fashion_ai_bounded_autonomy/validated/
fashion_ai_bounded_autonomy/output/
fashion_ai_bounded_autonomy/performance_metrics.db
fashion_ai_bounded_autonomy/review_queue.db
```

## Path Construction Guidelines

### ✅ CORRECT: Use Path objects with relative paths
```python
from pathlib import Path

# Database files
db_path = Path("fashion_ai_bounded_autonomy/review_queue.db")

# Directories
output_dir = Path("fashion_ai_bounded_autonomy/output/")
```

### ❌ INCORRECT: Mixing string and Path operations
```python
# Don't mix string concatenation with Path objects
path = "fashion_ai_bounded_autonomy/" + "review_queue.db"  # Bad
path = Path("fashion_ai_bounded_autonomy") / "review_queue.db"  # Good
```

### ✅ CORRECT: Create parent directories
```python
path = Path("fashion_ai_bounded_autonomy/review_queue.db")
path.parent.mkdir(parents=True, exist_ok=True)
```

## Validation Checklist

When adding new file references:

1. ✅ Add file path constant or default parameter
2. ✅ Use `Path` objects for path manipulation
3. ✅ Create parent directories with `mkdir(parents=True, exist_ok=True)`
4. ✅ Update this FILE_REFERENCES.md document
5. ✅ Add to .gitignore if it's a runtime file
6. ✅ Verify no hardcoded absolute paths
7. ✅ Test path construction on different OS (Windows/Linux/macOS)

## Architecture.yaml References (Not Currently Implemented)

These are documented in `config/architecture.yaml` but not used in current implementation:

- `fashion_ai_bounded.db` - General system database (line 121)
- `logs/agents/message_queue.db` - Message queue (line 101)

If implementing these, follow the guidelines above and update this document.

## Last Updated

- Date: 2025-10-30
- By: Claude Code Bounded Autonomy Test Optimization
- Commit: [pending]
