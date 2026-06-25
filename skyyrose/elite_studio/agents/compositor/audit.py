"""Audit log writer for the compositor pipeline.

Persists a JSON audit log alongside the pipeline output after every run,
whether successful or not.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def write_audit_log(
    sku: str,
    scene_name: str,
    stages: dict[str, Any],
    result: Any,
    output_dir: str,
) -> str:
    """Persist a JSON audit log alongside the output.

    Args:
        sku: Canonical SKU string.
        scene_name: Scene identifier.
        stages: Dict of per-stage metadata accumulated during the run.
        result: ``CompositorResult`` instance (success or partial failure).
        output_dir: Directory where the audit JSON is written.

    Returns:
        Absolute path to the written audit JSON file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / f"audit-{sku}-{scene_name}.json"
    body = {
        "sku": sku,
        "scene_name": scene_name,
        "collection": result.collection,
        "stages": stages,
        "result": {
            "success": result.success,
            "provider": result.provider,
            "model": result.model,
            "output_path": result.output_path,
            "alpha_path": result.alpha_path,
            "qa_status": result.qa_status,
            "qa_details": result.qa_details,
            "stages_completed": result.stages_completed,
            "used_fallback": result.used_fallback,
            "fallback_provider": result.fallback_provider,
            "error": result.error,
        },
        "pipeline_version": "compositor-v2-2026-04-30",
    }
    log_path.write_text(json.dumps(body, indent=2))
    return str(log_path)
