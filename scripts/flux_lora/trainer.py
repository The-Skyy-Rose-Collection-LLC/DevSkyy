"""
scripts.flux_lora.trainer — FLUX LoRA training via Replicate API.

SECURITY CONTRACT (ABSOLUTE):
  Any code path that reaches a Replicate POST without a prior STOP-AND-SHOW
  print + user 'y' is a bug. confirmed=False MUST raise RequiresConfirmationError.

Public API:
  build_manifest(dataset_zip, ...)  -> dict   (training params + cost estimate)
  show_stopandshow(manifest)        -> None   (prints the confirmation block)
  start_training(manifest, confirmed, input_images_url)
                                    -> dict   (Replicate training response)
  save_run_record(training_resp, manifest) -> Path
"""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import httpx

from scripts.flux_lora import (
    RequiresConfirmationError,
    TrainingError,
)
from scripts.flux_lora.config import (
    DEFAULT_AUTOCAPTION,
    DEFAULT_AUTOCAPTION_PREFIX,
    DEFAULT_BATCH_SIZE,
    DEFAULT_LEARNING_RATE,
    DEFAULT_LORA_RANK,
    DEFAULT_OPTIMIZER,
    DEFAULT_RESOLUTION,
    DEFAULT_STEPS,
    DEFAULT_TRIGGER_WORD,
    EST_COST_PER_RUN_USD,
    HARD_COST_CAP_USD,
    REPLICATE_BASE_URL,
    REPLICATE_MODEL_NAME,
    REPLICATE_MODEL_OWNER,
    REPLICATE_VERSION,
    RUNS_DIR,
    get_api_key,
)

# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


def build_manifest(
    dataset_zip: Path,
    *,
    trigger_word: str = DEFAULT_TRIGGER_WORD,
    steps: int = DEFAULT_STEPS,
    lora_rank: int = DEFAULT_LORA_RANK,
    optimizer: str = DEFAULT_OPTIMIZER,
    batch_size: int = DEFAULT_BATCH_SIZE,
    resolution: str = DEFAULT_RESOLUTION,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    autocaption: bool = DEFAULT_AUTOCAPTION,
    autocaption_prefix: str = DEFAULT_AUTOCAPTION_PREFIX,
    destination_model: str | None = None,
) -> dict[str, Any]:
    """
    Build a training manifest (params + cost estimate) without making any API call.

    Args:
        dataset_zip:       Local path to the packed dataset zip (for reference only;
                           the caller must upload it and supply the URL separately).
        destination_model: REQUIRED. Replicate model slug to push the trained LoRA
                           to, in "{owner}/{name}" form (e.g. "skyyrose/skyyrose-lora").
                           Replicate's create-training endpoint requires `destination`;
                           omitting it returns HTTP 422.

    Returns:
        Manifest dict with keys: model_owner, model_name, version, training_input,
        destination_model, cost_usd, dataset_zip.

    Raises:
        ValueError: if estimated cost exceeds HARD_COST_CAP_USD, or if
                    destination_model is missing/malformed.
    """
    estimated_cost = EST_COST_PER_RUN_USD
    if estimated_cost > HARD_COST_CAP_USD:
        raise ValueError(
            f"Estimated cost ${estimated_cost:.2f} exceeds hard cap "
            f"${HARD_COST_CAP_USD:.2f}. Aborting."
        )

    if not destination_model or "/" not in destination_model:
        raise ValueError(
            "destination_model is required and must be '{owner}/{name}' "
            "(Replicate pushes the trained LoRA there; the API rejects trainings "
            f"without a destination). Got: {destination_model!r}"
        )

    # Field names verified against the live ostris/flux-dev-lora-trainer
    # TrainingInput schema on 2026-06-24. Do NOT add fields absent from that
    # schema (e.g. lr_scheduler) — Replicate 422s on unknown input keys.
    training_input: dict[str, Any] = {
        "trigger_word": trigger_word,
        "steps": steps,
        "lora_rank": lora_rank,
        "optimizer": optimizer,
        "batch_size": batch_size,
        "resolution": resolution,
        "learning_rate": learning_rate,
        "autocaption": autocaption,
        "autocaption_prefix": autocaption_prefix,
    }

    manifest: dict[str, Any] = {
        "model_owner": REPLICATE_MODEL_OWNER,
        "model_name": REPLICATE_MODEL_NAME,
        "version": REPLICATE_VERSION,
        "training_input": training_input,
        "destination_model": destination_model,
        "cost_usd": estimated_cost,
        "dataset_zip": str(dataset_zip),
    }
    return manifest


# ---------------------------------------------------------------------------
# STOP-AND-SHOW
# ---------------------------------------------------------------------------


def show_stopandshow(manifest: dict[str, Any]) -> None:
    """
    Print the STOP-AND-SHOW confirmation block to stdout.

    This MUST be called and the user MUST type 'y' before start_training()
    is called with confirmed=True.
    """
    inp = manifest["training_input"]
    print()
    print("=" * 60)
    print("STOP — Confirm before proceeding:")
    print()
    print("  Action  : Replicate FLUX LoRA training")
    print(f"  Model   : {manifest['model_owner']}/{manifest['model_name']}")
    if manifest.get("version"):
        print(f"  Version : {manifest['version']}")
    else:
        print("  Version : latest")
    print(f"  Dataset : {manifest['dataset_zip']}")
    print(f"  Trigger : {inp['trigger_word']}")
    print(f"  Steps   : {inp['steps']}")
    print(f"  LoRA rank: {inp['lora_rank']}")
    if manifest.get("destination_model"):
        print(f"  Dest    : {manifest['destination_model']}")
    print(f"  Cost    : ~${manifest['cost_usd']:.2f}")
    print()
    print("Proceed? [y/N]")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------


def _build_training_url(version: str | None) -> str:
    """
    Build the Replicate create-training URL.

    Replicate REQUIRES the version id in the path:
      POST /v1/models/{owner}/{model}/versions/{version_id}/trainings
    There is no version-less trainings endpoint — omitting the version yields a
    404. We therefore refuse to construct an invalid URL.
    """
    if not version:
        raise TrainingError(
            "REPLICATE_VERSION is not set. Replicate trainings require a pinned "
            "version id in the URL path; set config.REPLICATE_VERSION to the "
            "trainer's version SHA (GET /v1/models/{owner}/{model} → latest_version.id)."
        )
    owner = REPLICATE_MODEL_OWNER
    model = REPLICATE_MODEL_NAME
    base = REPLICATE_BASE_URL.rstrip("/")
    return f"{base}/v1/models/{owner}/{model}/versions/{version}/trainings"


def start_training(
    manifest: dict[str, Any],
    *,
    confirmed: bool,
    input_images_url: str,
) -> dict[str, Any]:
    """
    Submit a training job to Replicate.

    SECURITY: confirmed MUST be True. If False, raises RequiresConfirmationError
    without making any HTTP call.

    Args:
        manifest:         Output of build_manifest().
        confirmed:        Must be True (set only after user typed 'y').
        input_images_url: Public URL to the uploaded dataset zip.

    Returns:
        Replicate training response dict (includes 'id', 'status', 'urls').

    Raises:
        RequiresConfirmationError: if confirmed is False.
        TrainingError:             on API error or non-201 response.
    """
    if not confirmed:
        raise RequiresConfirmationError(
            "Training requires explicit confirmation. "
            "Call show_stopandshow(manifest), get 'y' from the user, "
            "then call start_training(..., confirmed=True)."
        )

    token = get_api_key()
    url = _build_training_url(manifest.get("version"))

    destination = manifest.get("destination_model")
    if not destination:
        raise TrainingError(
            "manifest is missing destination_model; Replicate trainings require a "
            "destination. Build the manifest via build_manifest(..., destination_model=...)."
        )

    payload: dict[str, Any] = {
        "destination": destination,
        "input": {
            **manifest["training_input"],
            "input_images": input_images_url,
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "respond-async",
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
    except httpx.RequestError as exc:
        raise TrainingError(f"HTTP request failed: {exc}") from exc

    if response.status_code not in (200, 201):
        raise TrainingError(f"Replicate API returned {response.status_code}: {response.text}")

    return response.json()


# ---------------------------------------------------------------------------
# Run record persistence
# ---------------------------------------------------------------------------


def save_run_record(
    training_resp: dict[str, Any],
    manifest: dict[str, Any],
) -> Path:
    """
    Save a JSON record of the training run to RUNS_DIR.

    Filename: training-run-{training_id}-{timestamp}.json

    Returns:
        Path to the saved file.
    """
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    training_id: str = training_resp.get("id", "unknown")
    ts = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = f"training-run-{training_id}-{ts}.json"
    dest = RUNS_DIR / filename

    record: dict[str, Any] = {
        "training_id": training_id,
        "timestamp": ts,
        "manifest": manifest,
        "replicate_response": training_resp,
    }

    dest.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
    return dest
