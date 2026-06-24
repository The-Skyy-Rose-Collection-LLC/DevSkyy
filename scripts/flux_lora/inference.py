"""
scripts.flux_lora.inference — FLUX LoRA inference via Replicate API.

SECURITY CONTRACT (ABSOLUTE):
  Any code path that reaches a Replicate POST without a prior STOP-AND-SHOW
  print + user 'y' is a bug. confirmed=False MUST raise RequiresConfirmationError.

Public API:
  load_latest_lora()             -> str | None   (Replicate output URL from latest run)
  generate(prompt, lora_url, confirmed, **kwargs) -> list[str]  (output image URLs)
"""

from __future__ import annotations

from typing import Any

import httpx

from scripts.flux_lora import RequiresConfirmationError, TrainingError
from scripts.flux_lora.config import (
    REPLICATE_BASE_URL,
    get_api_key,
)
from scripts.flux_lora.status import list_runs

# ---------------------------------------------------------------------------
# Default inference params
# ---------------------------------------------------------------------------
DEFAULT_NUM_OUTPUTS: int = 1
DEFAULT_ASPECT_RATIO: str = "1:1"
DEFAULT_OUTPUT_FORMAT: str = "png"
DEFAULT_GUIDANCE: float = 3.5
DEFAULT_NUM_INFERENCE_STEPS: int = 28

# Replicate model for FLUX.1-dev inference WITH LoRA support.
# Field names (lora_weights, lora_scale, guidance, ...) verified against this
# model's live Input schema on 2026-06-24. The base black-forest-labs/flux-dev
# model has NO lora_weights/extra_lora fields — it must be the -lora variant.
FLUX_INFERENCE_MODEL: str = "black-forest-labs/flux-dev-lora"


# ---------------------------------------------------------------------------
# Latest LoRA loader
# ---------------------------------------------------------------------------


def load_latest_lora() -> str | None:
    """
    Return the Replicate output URL (trained weights) from the most recent
    succeeded training run, or None if no succeeded run exists.
    """
    runs = list_runs()
    for run in runs:
        resp = run.get("replicate_response", {})
        if resp.get("status") == "succeeded":
            output = resp.get("output")
            if isinstance(output, str):
                return output
            if isinstance(output, list) and output:
                return output[0]
    return None


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------


def _show_inference_stopandshow(
    prompt: str,
    lora_url: str,
    num_outputs: int,
) -> None:
    print()
    print("=" * 60)
    print("STOP — Confirm before proceeding:")
    print()
    print("  Action   : Replicate FLUX inference")
    print(f"  Model    : {FLUX_INFERENCE_MODEL}")
    print(f"  LoRA     : {lora_url}")
    print(f"  Prompt   : {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    print(f"  Outputs  : {num_outputs}")
    print(f"  Cost     : ~${num_outputs * 0.055:.3f}  (est. $0.055/image)")
    print()
    print("Proceed? [y/N]")
    print("=" * 60)


def generate(
    prompt: str,
    lora_url: str,
    *,
    confirmed: bool,
    num_outputs: int = DEFAULT_NUM_OUTPUTS,
    aspect_ratio: str = DEFAULT_ASPECT_RATIO,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    guidance: float = DEFAULT_GUIDANCE,
    num_inference_steps: int = DEFAULT_NUM_INFERENCE_STEPS,
    lora_scale: float = 1.0,
) -> list[str]:
    """
    Run FLUX inference with a trained LoRA.

    SECURITY: confirmed MUST be True. If False, raises RequiresConfirmationError
    without making any HTTP call.

    Args:
        prompt:               Text prompt (trigger word should be included).
        lora_url:             Replicate output URL from a succeeded training run.
        confirmed:            Must be True (set only after user typed 'y').
        num_outputs:          Number of images to generate (1-4).
        aspect_ratio:         Image aspect ratio (e.g. "1:1", "2:3", "3:4").
        output_format:        "png" | "webp" | "jpg".
        guidance:             FLUX guidance value (the model's `guidance` field).
        num_inference_steps:  Denoising steps.
        lora_scale:           Trained-LoRA weight scale (0.0-1.0).

    Returns:
        List of output image URLs.

    Raises:
        RequiresConfirmationError: if confirmed is False.
        TrainingError:             on API error or non-201 response.
    """
    if not confirmed:
        _show_inference_stopandshow(prompt, lora_url, num_outputs)
        raise RequiresConfirmationError(
            "Inference requires explicit confirmation. "
            "Call generate(..., confirmed=True) only after user types 'y'."
        )

    token = get_api_key()
    base = REPLICATE_BASE_URL.rstrip("/")
    url = f"{base}/v1/models/{FLUX_INFERENCE_MODEL}/predictions"

    payload: dict[str, Any] = {
        "input": {
            "prompt": prompt,
            "lora_weights": lora_url,
            "lora_scale": lora_scale,
            "num_outputs": num_outputs,
            "aspect_ratio": aspect_ratio,
            "output_format": output_format,
            "guidance": guidance,
            "num_inference_steps": num_inference_steps,
        }
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

    data = response.json()
    output = data.get("output") or []
    if isinstance(output, str):
        return [output]
    return list(output)
