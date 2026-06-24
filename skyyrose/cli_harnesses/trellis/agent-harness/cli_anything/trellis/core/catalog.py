"""Generation catalog — JSON-lines history file for completed jobs.

Each completed (done or failed) GenerationRecord is appended as a single
JSON line to ~/.cli_anything/trellis/catalog.jsonl.

The catalog is append-only; records are never modified after writing.
Reading the catalog loads all lines and returns GenerationRecord objects.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Iterator, List, Optional

from cli_anything.trellis.core.generation import GenerationRecord

# ── Constants ─────────────────────────────────────────────────────────────────

CATALOG_DIR = Path.home() / ".cli_anything" / "trellis"
CATALOG_FILE = CATALOG_DIR / "catalog.jsonl"


# ── Catalog I/O ───────────────────────────────────────────────────────────────


def append_record(record: GenerationRecord, catalog_path: Optional[Path] = None) -> None:
    """Append *record* as a JSON line to the catalog file.

    Thread-safe via fcntl.flock (POSIX). Falls back silently on Windows.

    Args:
        record: The GenerationRecord to persist.
        catalog_path: Override catalog file path (used in tests).
    """
    path = catalog_path or CATALOG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(record.to_dict(), ensure_ascii=False) + "\n"

    with open(path, "a", encoding="utf-8") as fh:
        try:
            import fcntl

            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        except (ImportError, OSError):
            pass
        fh.write(line)
        fh.flush()
        os.fsync(fh.fileno())


def iter_records(catalog_path: Optional[Path] = None) -> Iterator[GenerationRecord]:
    """Iterate over all records in the catalog, oldest first.

    Silently skips malformed lines.

    Args:
        catalog_path: Override catalog file path (used in tests).

    Yields:
        GenerationRecord for each valid line.
    """
    path = catalog_path or CATALOG_FILE
    if not path.exists():
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                yield GenerationRecord.from_dict(data)
            except (json.JSONDecodeError, ValueError):
                continue


def list_records(
    catalog_path: Optional[Path] = None,
    status_filter: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[GenerationRecord]:
    """Return records from the catalog as a list.

    Args:
        catalog_path: Override catalog file path (used in tests).
        status_filter: If set, only return records with this status.
        limit: If set, return only the most recent *limit* records.

    Returns:
        List of GenerationRecord, most recent last (or truncated to limit).
    """
    records = list(iter_records(catalog_path))
    if status_filter is not None:
        records = [r for r in records if r.status == status_filter]
    if limit is not None and limit > 0:
        records = records[-limit:]
    return records


def find_record(job_id: str, catalog_path: Optional[Path] = None) -> Optional[GenerationRecord]:
    """Find a record by job_id. Returns None if not found.

    Scans the catalog from newest to oldest for efficiency when recent
    job IDs are queried most often.
    """
    # Reverse scan: read all then iterate backward
    records = list(iter_records(catalog_path))
    for record in reversed(records):
        if record.job_id == job_id:
            return record
    return None


def catalog_stats(catalog_path: Optional[Path] = None) -> dict:
    """Return summary statistics for the catalog.

    Returns:
        Dict with keys: total, done, failed, pending, running.
    """
    stats: dict = {"total": 0, "done": 0, "failed": 0, "pending": 0, "running": 0}
    for record in iter_records(catalog_path):
        stats["total"] += 1
        key = record.status
        if key in stats:
            stats[key] += 1
    return stats
