"""
Per-stage telemetry for the compositor pipeline.

Phase 1 of the commercial compositor audit: read-only instrumentation.
Emits one JSON line per stage invocation to
`skyyrose/elite_studio/logs/compositor-telemetry-YYYY-MM-DD.jsonl`.

Event schema (all keys present, null when unknown):
    run_id        str    # groups all stages of one composite() call
    stage         str    # alpha | prompt | relight | flux | shadows | qa
    sku           str
    scene_name    str
    collection    str
    started_at    str    # ISO-8601 UTC, millisecond precision
    duration_ms   int
    status        str    # ok | error
    error_type    str?   # exception class name when status=error
    provider      str?   # e.g. fal, replicate, libcom, iclight, bria
    model         str?   # e.g. claude-opus-4-6, gemini-3-pro-image-preview
    tokens_in     int?
    tokens_out    int?
    bytes_in      int?
    bytes_out     int?
    input_hash    str?   # sha256[:16] of stable inputs (for idempotent cache later)
    meta          dict   # stage-specific free-form fields

Failure to record is swallowed — telemetry MUST NOT break the pipeline.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_DEFAULT_LOG_DIR = Path(__file__).parent / "logs"
STAGE_NAMES = ("alpha", "prompt", "relight", "flux", "shadows", "qa")


def _log_dir() -> Path:
    override = os.environ.get("COMPOSITOR_TELEMETRY_DIR")
    return Path(override) if override else _DEFAULT_LOG_DIR


def _log_path() -> Path:
    d = _log_dir()
    d.mkdir(parents=True, exist_ok=True)
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    return d / f"compositor-telemetry-{day}.jsonl"


def new_run_id() -> str:
    """Short, collision-safe identifier grouping one composite() invocation."""
    return uuid.uuid4().hex[:12]


def hash_inputs(*parts: str | bytes | None) -> str:
    """Stable 16-char SHA256 prefix of the given inputs. None parts are skipped."""
    h = hashlib.sha256()
    for p in parts:
        if p is None:
            continue
        h.update(b"\0")
        h.update(p.encode() if isinstance(p, str) else p)
    return h.hexdigest()[:16]


def emit(event: dict[str, Any]) -> None:
    """Append a single JSONL record. Never raises."""
    try:
        path = _log_path()
        line = json.dumps(event, default=str, separators=(",", ":"))
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _run_summary_dir() -> Path:
    """Directory where per-run summary JSON files land.

    Override via ELITE_STUDIO_RUN_SUMMARY_DIR. Defaults to
    ``skyyrose/elite_studio/logs/runs/`` so it sits next to the existing
    stage-event JSONL.
    """
    override = os.environ.get("ELITE_STUDIO_RUN_SUMMARY_DIR")
    if override:
        return Path(override)
    return _log_dir() / "runs"


def write_run_summary(run_id: str, summary: dict[str, Any]) -> Path | None:
    """Persist a per-SKU run summary to disk for downstream auditing.

    Called by ``finalize_node`` (and equivalent terminal nodes) once a
    pipeline run completes — success OR failure. The summary should
    contain at minimum: sku, view, status, generation_engine, qa_score,
    cost rollup (from RunBudget.snapshot), top_issues, infra_failures.

    Returns the written path on success, None on any I/O failure (never
    raises — telemetry must not break a finished run).
    """
    try:
        out_dir = _run_summary_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{run_id}.json"
        out_path.write_text(
            json.dumps(summary, default=str, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return out_path
    except Exception:
        return None


_FIELDS = ("provider", "model", "tokens_in", "tokens_out", "bytes_in", "bytes_out")


class _StageContext:
    """Handle passed to the stage() caller — lets them attach metadata."""

    __slots__ = ("_fields", "_meta")

    def __init__(self) -> None:
        self._fields: dict[str, Any] = dict.fromkeys(_FIELDS)
        self._meta: dict[str, Any] = {}

    def set(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            if k in _FIELDS:
                self._fields[k] = v
            else:
                self._meta[k] = v


@contextmanager
def stage(
    *,
    run_id: str,
    stage_name: str,
    sku: str,
    scene_name: str = "",
    collection: str = "",
    input_hash: str | None = None,
) -> Iterator[_StageContext]:
    """Time a stage, capture metadata, emit exactly one telemetry event on exit."""
    if stage_name not in STAGE_NAMES:
        # Don't fail on typos — log anyway with the name given.
        pass
    ctx = _StageContext()
    started_mono = time.monotonic()
    started_iso = datetime.now(UTC).isoformat(timespec="milliseconds")
    status = "ok"
    error_type: str | None = None
    try:
        yield ctx
    except BaseException as e:
        status = "error"
        error_type = type(e).__name__
        raise
    finally:
        duration_ms = int((time.monotonic() - started_mono) * 1000)
        event = {
            "run_id": run_id,
            "stage": stage_name,
            "sku": sku,
            "scene_name": scene_name,
            "collection": collection,
            "started_at": started_iso,
            "duration_ms": duration_ms,
            "status": status,
            "error_type": error_type,
            "input_hash": input_hash,
            **ctx._fields,
            "meta": ctx._meta,
        }
        emit(event)
