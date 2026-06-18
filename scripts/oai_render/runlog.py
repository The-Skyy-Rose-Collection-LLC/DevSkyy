"""Append-only JSONL event log for one render batch — the monitor's data source.

Every paid run writes structured events to ``renders/oai/_runs/run-<ts>.jsonl``:
what was planned, each render attempt, each QC verdict (including the judge's
forced ``visual_analysis`` reasoning), every acceptance/quarantine, and the
running spend against the hard cap. The live dashboard
(``scripts/oai-render-monitor.py``) polls this file; afterwards it is the
permanent forensic record of where the money went.

Monitoring must never break a paid batch: every write failure is logged and
swallowed — a dead disk for the event log costs observability, not renders.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from . import config

log = logging.getLogger(__name__)

RUNS_DIR = config.OUTPUT_DIR / "_runs"


class RunLog:
    """One instance per batch run. ``emit()`` appends one JSON object per line.

    Fields are written verbatim — size discipline is the emitter's job (e.g.
    ``QCVerdict`` caps ``analysis`` at construction), not this layer's.
    """

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            RUNS_DIR.mkdir(parents=True, exist_ok=True)
            path = RUNS_DIR / f"run-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
        self.path = path

    def emit(self, event: str, **fields) -> None:
        """Append one event. Never raises — observability must not kill the run."""
        record = {"ts": round(time.time(), 3), "event": event, **fields}
        try:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        except OSError as exc:
            log.error("RunLog write failed (%s): %s — continuing unlogged", self.path, exc)


def newest_run_file(runs_dir: Path = RUNS_DIR) -> Path | None:
    """Most recently modified run-*.jsonl, or None when no runs exist."""
    try:
        candidates = sorted(runs_dir.glob("run-*.jsonl"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return None
    return candidates[-1] if candidates else None


def load_events(path: Path) -> list[dict]:
    """Parse a run file, skipping torn/partial lines (the writer may be mid-append)."""
    events: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return events
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except ValueError:
            continue  # torn tail line from a concurrent append
    return events
