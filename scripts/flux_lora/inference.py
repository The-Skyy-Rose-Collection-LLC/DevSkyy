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

import time
from typing import Any

import httpx

from scripts.flux_lora import InferenceError, RequiresConfirmationError
from scripts.flux_lora.config import (
    REPLICATE_BASE_URL,
    get_api_key,
    is_https_url,
)
from scripts.flux_lora.status import TERMINAL_STATUSES, list_runs

# ---------------------------------------------------------------------------
# Default inference params
# ---------------------------------------------------------------------------
DEFAULT_NUM_OUTPUTS: int = 1
DEFAULT_ASPECT_RATIO: str = "1:1"
DEFAULT_OUTPUT_FORMAT: str = "png"
DEFAULT_GUIDANCE: float = 3.5
DEFAULT_NUM_INFERENCE_STEPS: int = 28

# Polling: a prediction created with `Prefer: wait` may still return non-terminal
# (Replicate caps the synchronous wait at ~60s). We then poll urls.get until done.
POLL_INTERVAL_S: float = 3.0
POLL_TIMEOUT_S: float = 300.0

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


def _extract_output_urls(data: dict[str, Any]) -> list[str]:
    """Return the image URL list from a SUCCEEDED prediction, else raise."""
    output = data.get("output")
    if isinstance(output, str):
        return [output]
    if isinstance(output, list):
        return [str(u) for u in output]
    raise InferenceError(
        f"Prediction succeeded but output was {type(output).__name__}, "
        "expected a URL string or list."
    )


def _poll_prediction(get_url: str, token: str) -> dict[str, Any]:
    """
    Poll a prediction's urls.get until it reaches a terminal status, then return
    the final prediction dict. Checks status BEFORE sleeping so a prediction that
    is already terminal returns immediately (and tests never sleep).
    """
    headers = {"Authorization": f"Bearer {token}"}
    elapsed = 0.0
    while True:
        try:
            resp = httpx.get(get_url, headers=headers, timeout=15.0)
        except httpx.RequestError as exc:
            raise InferenceError(f"Prediction poll request failed: {exc}") from exc
        if resp.status_code != 200:
            raise InferenceError(f"Prediction poll returned {resp.status_code}: {resp.text}")
        data = resp.json()
        if data.get("status") in TERMINAL_STATUSES:
            return data
        if elapsed >= POLL_TIMEOUT_S:
            raise InferenceError(
                f"Prediction did not complete within {POLL_TIMEOUT_S:.0f}s "
                f"(last status: {data.get('status')!r})."
            )
        time.sleep(POLL_INTERVAL_S)
        elapsed += POLL_INTERVAL_S


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
    seed: int | None = None,
) -> list[str]:
    """
    Run FLUX inference with a trained LoRA and return the output image URLs.

    SECURITY: confirmed MUST be True. If False, raises RequiresConfirmationError
    without making any HTTP call.

    The prediction is created with `Prefer: wait` (synchronous up to ~60s). If it
    has not finished in that window, we poll urls.get until it reaches a terminal
    status, then return the output (or raise InferenceError on failed/canceled).

    Args:
        prompt:               Text prompt (trigger word should be included).
        lora_url:             https URL to the trained LoRA weights.
        confirmed:            Must be True (set only after user typed 'y').
        num_outputs:          Number of images to generate (1-4).
        aspect_ratio:         Image aspect ratio (e.g. "1:1", "2:3", "3:4").
        output_format:        "png" | "webp" | "jpg".
        guidance:             FLUX guidance value (the model's `guidance` field).
        num_inference_steps:  Denoising steps.
        lora_scale:           Trained-LoRA weight scale (0.0-1.0).
        seed:                 Optional fixed seed for reproducible output.

    Returns:
        List of output image URLs (from a succeeded prediction).

    Raises:
        RequiresConfirmationError: if confirmed is False.
        InferenceError:            on API error, failed/canceled prediction, or timeout.
        ValueError:                if lora_url is not an https URL.
    """
    if not confirmed:
        _show_inference_stopandshow(prompt, lora_url, num_outputs)
        raise RequiresConfirmationError(
            "Inference requires explicit confirmation. "
            "Call generate(..., confirmed=True) only after user types 'y'."
        )

    if not is_https_url(lora_url):
        raise ValueError(f"lora_url must be an https:// URL, got: {lora_url!r}")

    token = get_api_key()
    base = REPLICATE_BASE_URL.rstrip("/")
    url = f"{base}/v1/models/{FLUX_INFERENCE_MODEL}/predictions"

    model_input: dict[str, Any] = {
        "prompt": prompt,
        "lora_weights": lora_url,
        "lora_scale": lora_scale,
        "num_outputs": num_outputs,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
        "guidance": guidance,
        "num_inference_steps": num_inference_steps,
    }
    if seed is not None:
        model_input["seed"] = seed

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }

    try:
        response = httpx.post(url, json={"input": model_input}, headers=headers, timeout=90.0)
    except httpx.RequestError as exc:
        raise InferenceError(f"HTTP request failed: {exc}") from exc

    if response.status_code not in (200, 201):
        raise InferenceError(f"Replicate API returned {response.status_code}: {response.text}")

    data = response.json()
    # Prefer: wait may still hand back a non-terminal prediction — poll until done.
    if data.get("status") not in TERMINAL_STATUSES:
        get_url = (data.get("urls") or {}).get("get")
        if not get_url:
            raise InferenceError(
                "Replicate response has no terminal status and no urls.get to poll."
            )
        data = _poll_prediction(get_url, token)

    status = data.get("status")
    if status != "succeeded":
        raise InferenceError(f"Inference {status}: {data.get('error') or 'no output produced'}")

    return _extract_output_urls(data)
