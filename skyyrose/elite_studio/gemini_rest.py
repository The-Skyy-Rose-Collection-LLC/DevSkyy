"""
Direct REST client for Gemini API — bypasses the Python SDK.

The google-genai SDK uses httpx internally with connection pooling.
After heavy batch usage, the httpx pool can enter a broken state
where SSL handshakes timeout even though the API is responsive.
This module uses the `requests` library with fresh connections
for reliable access.

Supports:
  - Text generation (gemini-2.0-flash, gemini-3-flash-preview)
  - Vision analysis (image + text)
  - Image generation (gemini-3-pro-image-preview)
"""

from __future__ import annotations

import base64
import os
from typing import Any

import requests

from .config import GEMINI_TIMEOUT

# Gemini REST API base URL
_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _get_key() -> str:
    """Get the active Gemini API key."""
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""


def _endpoint(model: str, method: str = "generateContent") -> str:
    """Build API endpoint URL."""
    key = _get_key()
    return f"{_API_BASE}/models/{model}:{method}?key={key}"


def generate_text(model: str, prompt: str) -> dict[str, Any]:
    """Generate text content.

    Returns:
        {"success": True, "text": "..."} or
        {"success": False, "error": "..."}
    """
    url = _endpoint(model)
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(url, json=payload, timeout=GEMINI_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"success": True, "text": text}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def analyze_vision(
    model: str,
    prompt: str,
    image_b64: str,
    mime_type: str = "image/jpeg",
) -> dict[str, Any]:
    """Analyze image with vision model.

    Args:
        model: Model name (e.g., 'gemini-3-flash-preview')
        prompt: Analysis prompt
        image_b64: Base64-encoded image data
        mime_type: Image MIME type

    Returns:
        {"success": True, "text": "..."} or
        {"success": False, "error": "..."}
    """
    url = _endpoint(model)
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

    try:
        resp = requests.post(url, json=payload, timeout=GEMINI_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"success": True, "text": text}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def generate_image(
    model: str,
    prompt: str,
    reference_b64: str,
    aspect_ratio: str = "3:4",
    mime_type: str = "image/jpeg",
) -> dict[str, Any]:
    """Generate image using Gemini image model.

    Args:
        model: Model name (e.g., 'gemini-3-pro-image-preview')
        prompt: Generation prompt
        reference_b64: Base64-encoded reference image
        aspect_ratio: Output aspect ratio
        mime_type: Reference image MIME type

    Returns:
        {"success": True, "image_data": bytes} or
        {"success": False, "error": "..."}
    """
    url = _endpoint(model)
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": reference_b64,
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": aspect_ratio},
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=GEMINI_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        # Extract image from response
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "inlineData" in part:
                image_b64_str = part["inlineData"]["data"]
                return {
                    "success": True,
                    "image_data": base64.b64decode(image_b64_str),
                    "mime_type": part["inlineData"].get("mimeType", "image/jpeg"),
                }

        # No image — return what we got
        part_types = []
        for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
            if "text" in part:
                part_types.append(f"text({len(part['text'])} chars)")
            elif "inlineData" in part:
                part_types.append(f"image({part['inlineData'].get('mimeType')})")

        return {"success": False, "error": f"No image in response. Parts: {part_types}"}

    except Exception as exc:
        return {"success": False, "error": str(exc)}
