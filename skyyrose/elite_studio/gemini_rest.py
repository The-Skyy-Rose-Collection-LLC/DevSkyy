"""
Direct REST client for Gemini API — bypasses the Python SDK.

Enhanced with OpenTelemetry for "Back Data" observability.
"""

from __future__ import annotations

import base64
import os
import threading
import time
from typing import Any

import requests

from core.telemetry.tracer import get_tracer

from .config import GEMINI_TIMEOUT

# Gemini REST API base URL
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# API Key Rotation state
_KEY_INDEX = 0
_KEY_LOCK = threading.Lock()

tracer = get_tracer(__name__)


def _get_keys() -> list[str]:
    """Get all available Gemini API keys from environment."""
    keys = []
    # Check for primary keys
    for primary in ["GEMINI_API_KEY", "GOOGLE_AI_API_KEY", "GOOGLE_API_KEY"]:
        val = os.getenv(primary)
        if val:
            keys.append(val)

    # Check for numbered keys (GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.)
    for i in range(1, 11):
        for fmt in ["GEMINI_API_KEY_{}", "GOOGLE_AI_API_KEY_{}", "GOOGLE_API_KEY_{}"]:
            val = os.getenv(fmt.format(i))
            if val:
                keys.append(val)

    return sorted(set(keys))  # Unique keys


def _get_active_key() -> str:
    """Get the next key in the rotation."""
    global _KEY_INDEX
    keys = _get_keys()
    if not keys:
        return ""

    with _KEY_LOCK:
        key = keys[_KEY_INDEX % len(keys)]
        _KEY_INDEX += 1
    return key


def _endpoint(model: str, method: str = "generateContent") -> str:
    """Build API endpoint URL."""
    key = _get_active_key()
    return f"{_API_BASE}/models/{model}:{method}?key={key}"


def _post_with_retry(model: str, method: str, payload: dict) -> dict[str, Any]:
    """Post to Gemini with automatic key rotation on 429 and OTel tracing."""
    with tracer.start_as_current_span(f"gemini_api_{method}") as span:
        span.set_attribute("model", model)
        span.set_attribute("method", method)

        keys = _get_keys()
        max_attempts = len(keys) if keys else 1

        for attempt in range(max_attempts):
            url = _endpoint(model, method)
            try:
                start_time = time.monotonic()
                resp = requests.post(url, json=payload, timeout=GEMINI_TIMEOUT)
                duration = time.monotonic() - start_time

                span.add_event(
                    f"api_attempt_{attempt}",
                    attributes={"status_code": resp.status_code, "duration_s": duration},
                )

                if resp.status_code == 429 and attempt < max_attempts - 1:
                    continue

                resp.raise_for_status()
                data = resp.json()

                # Record token usage if available
                usage = data.get("usageMetadata", {})
                if usage:
                    span.set_attribute("prompt_tokens", usage.get("promptTokenCount", 0))
                    span.set_attribute("candidates_tokens", usage.get("candidatesTokenCount", 0))

                return {"success": True, "data": data}
            except Exception as exc:
                if attempt < max_attempts - 1:
                    continue
                span.record_exception(exc)
                return {"success": False, "error": str(exc)}

        return {"success": False, "error": "All API keys exhausted or rate limited."}


def generate_text(model: str, prompt: str) -> dict[str, Any]:
    """Generate text content."""
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    result = _post_with_retry(model, "generateContent", payload)

    if not result["success"]:
        return result

    try:
        text = result["data"]["candidates"][0]["content"]["parts"][0]["text"]
        return {"success": True, "text": text}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def analyze_vision(
    model: str,
    prompt: str,
    image_b64: str,
    mime_type: str = "image/jpeg",
) -> dict[str, Any]:
    """Analyze image with vision model."""
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64,
                        }
                    },
                ]
            }
        ]
    }
    result = _post_with_retry(model, "generateContent", payload)

    if not result["success"]:
        return result

    try:
        text = result["data"]["candidates"][0]["content"]["parts"][0]["text"]
        return {"success": True, "text": text}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def generate_image(
    model: str,
    prompt: str,
    reference_images_b64: list[str] | str,
    aspect_ratio: str = "3:4",
    mime_type: str = "image/jpeg",
) -> dict[str, Any]:
    """Generate image using Gemini image model with one or more reference images."""
    parts = [{"text": prompt}]

    if isinstance(reference_images_b64, str):
        # Backward compatibility for single string
        if reference_images_b64:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": reference_images_b64,
                    }
                }
            )
    else:
        # Support for list of base64 images
        for b64 in reference_images_b64:
            if b64:
                parts.append(
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": b64,
                        }
                    }
                )

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        },
    }

    result = _post_with_retry(model, "generateContent", payload)

    if not result["success"]:
        return result

    try:
        data = result["data"]
        # Extract image from response
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                image_b64_str = part["inlineData"]["data"]
                return {
                    "success": True,
                    "image_data": base64.b64decode(image_b64_str),
                    "mime_type": part["inlineData"].get("mimeType", "image/jpeg"),
                }

        return {"success": False, "error": "No image in response."}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
