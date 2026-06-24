"""
scripts.flux_lora.status — Training run status and history.

Public API:
  get_status(training_id)  -> dict   (Replicate training status response)
  list_runs()              -> list[dict]   (all saved run records, newest first)
  format_status(status_dict) -> str   (human-readable summary)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from scripts.flux_lora import TrainingError
from scripts.flux_lora.config import REPLICATE_BASE_URL, RUNS_DIR, get_api_key

# Replicate training status values
TERMINAL_STATUSES: frozenset[str] = frozenset({"succeeded", "failed", "canceled"})


def get_status(training_id: str) -> dict[str, Any]:
    """
    Fetch current status of a Replicate training job.

    Args:
        training_id: The Replicate training ID (from start_training response).

    Returns:
        Replicate training status dict with keys: id, status, urls, output, error.

    Raises:
        TrainingError: on HTTP error or non-200 response.
    """
    token = get_api_key()
    url = f"{REPLICATE_BASE_URL.rstrip('/')}/v1/trainings/{training_id}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = httpx.get(url, headers=headers, timeout=15.0)
    except httpx.RequestError as exc:
        raise TrainingError(f"HTTP request failed: {exc}") from exc

    if response.status_code != 200:
        raise TrainingError(f"Replicate API returned {response.status_code}: {response.text}")

    return response.json()


def list_runs(runs_dir: Path = RUNS_DIR) -> list[dict[str, Any]]:
    """
    Return all saved training run records from RUNS_DIR, newest first.

    Returns:
        List of run record dicts (may be empty if RUNS_DIR absent or no records).
    """
    if not runs_dir.exists():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(runs_dir.glob("training-run-*.json"), reverse=True):
        try:
            records.append(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue

    return records


def format_status(status_dict: dict[str, Any]) -> str:
    """
    Format a Replicate training status dict as a human-readable string.

    Args:
        status_dict: Output of get_status() or the replicate_response in a run record.

    Returns:
        Multi-line string suitable for terminal display.
    """
    training_id = status_dict.get("id", "unknown")
    status = status_dict.get("status", "unknown")
    created = status_dict.get("created_at", "")
    completed = status_dict.get("completed_at", "")
    error = status_dict.get("error")
    urls = status_dict.get("urls", {})
    output = status_dict.get("output")

    lines: list[str] = [
        f"Training ID : {training_id}",
        f"Status      : {status}",
    ]
    if created:
        lines.append(f"Created     : {created}")
    if completed:
        lines.append(f"Completed   : {completed}")
    if urls.get("get"):
        lines.append(f"URL         : {urls['get']}")
    if output:
        lines.append(f"Output      : {output}")
    if error:
        lines.append(f"Error       : {error}")

    return "\n".join(lines)
