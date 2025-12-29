"""
Asset Tagging Agent
==================

Provides automated image tagging using configurable vision services.

Supports:
- Google Vision API (label detection)
- OpenAI Vision (GPT-4 Vision)
- Local fallback (returns empty tags when no API configured)
"""

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any

import httpx
import yaml

logger = logging.getLogger(__name__)


class VisionServiceError(Exception):
    """Error calling vision service."""

    pass


class AssetTaggingAgent:
    """
    Agent for automatically tagging images using vision AI services.

    Supports multiple vision providers:
    - google-vision: Google Cloud Vision API
    - openai-vision: OpenAI GPT-4 Vision
    - local: Local fallback (no API calls)

    Example:
        agent = AssetTaggingAgent()
        tags = agent.tag_image("path/to/image.jpg")
    """

    # Supported vision service providers
    SUPPORTED_PROVIDERS = {"google-vision", "openai-vision", "local"}

    def __init__(self, config_path: str = "config/asset_tagging.yaml"):
        """
        Initialize the asset tagging agent.

        Args:
            config_path: Path to YAML config with taxonomy and vision service settings.
        """
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file) as f:
                self.config = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self.config = {}

        self.taxonomy: dict[str, list[str]] = self.config.get("taxonomy", {})
        self.vision_service: dict[str, Any] = self.config.get("vision_service", {})
        tagging_cfg = self.config.get("tagging", {})
        self.threshold: float = tagging_cfg.get("threshold", 0.5)
        self.assign_multiple: bool = tagging_cfg.get("assign_multiple", True)

        # Determine provider
        self._provider = self.vision_service.get("name", "local")
        if self._provider not in self.SUPPORTED_PROVIDERS:
            logger.warning(f"Unknown vision provider '{self._provider}', falling back to local")
            self._provider = "local"

    def _get_api_key(self) -> str | None:
        """
        Retrieve API key from environment variable.

        Returns:
            API key string or None if not configured.
        """
        env_var = self.vision_service.get("api_key_env")
        if not env_var:
            return None
        return os.getenv(env_var)

    def _read_image_as_base64(self, image_path: str) -> str:
        """Read image file and encode as base64."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _get_image_mime_type(self, image_path: str) -> str:
        """Determine MIME type from file extension."""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
        }
        return mime_types.get(ext, "image/jpeg")

    def _call_google_vision(self, image_path: str) -> dict[str, float]:
        """
        Call Google Cloud Vision API for label detection.

        Args:
            image_path: Path to image file.

        Returns:
            Dictionary mapping detected labels to confidence scores.
        """
        api_key = self._get_api_key()
        if not api_key:
            logger.warning("GOOGLE_AI_API_KEY not set, returning empty tags")
            return {}

        image_data = self._read_image_as_base64(image_path)

        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        payload = {
            "requests": [
                {
                    "image": {"content": image_data},
                    "features": [{"type": "LABEL_DETECTION", "maxResults": 20}],
                }
            ]
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()

            # Extract labels and scores
            tag_scores: dict[str, float] = {}
            responses = result.get("responses", [])
            if responses:
                labels = responses[0].get("labelAnnotations", [])
                for label in labels:
                    tag_name = label.get("description", "").lower()
                    score = label.get("score", 0.0)
                    tag_scores[tag_name] = score

            return tag_scores

        except httpx.HTTPStatusError as e:
            logger.error(f"Google Vision API error: {e.response.status_code}")
            raise VisionServiceError(f"Google Vision API returned {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error calling Google Vision: {e}")
            raise VisionServiceError(str(e))

    def _call_openai_vision(self, image_path: str) -> dict[str, float]:
        """
        Call OpenAI GPT-4 Vision for image analysis.

        Args:
            image_path: Path to image file.

        Returns:
            Dictionary mapping detected tags to confidence scores.
        """
        api_key = self._get_api_key()
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, returning empty tags")
            return {}

        image_data = self._read_image_as_base64(image_path)
        mime_type = self._get_image_mime_type(image_path)

        # Build tag list from taxonomy
        all_tags = []
        for tags in self.taxonomy.values():
            all_tags.extend(tags)

        prompt = f"""Analyze this image and identify which of these tags apply.
Return a JSON object where keys are tag names and values are confidence scores (0.0 to 1.0).

Available tags: {', '.join(all_tags)}

Only include tags that are relevant to the image. Return valid JSON only."""

        url = "https://api.openai.com/v1/chat/completions"
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                        },
                    ],
                }
            ],
            "max_tokens": 500,
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                response.raise_for_status()
                result = response.json()

            # Parse response
            content = result["choices"][0]["message"]["content"]

            # Extract JSON from response (may be wrapped in markdown)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            tag_scores = json.loads(content.strip())
            return {k.lower(): float(v) for k, v in tag_scores.items()}

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI Vision API error: {e.response.status_code}")
            raise VisionServiceError(f"OpenAI API returned {e.response.status_code}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            raise VisionServiceError("Invalid JSON response from OpenAI")
        except Exception as e:
            logger.error(f"Error calling OpenAI Vision: {e}")
            raise VisionServiceError(str(e))

    def _call_local_fallback(self, image_path: str) -> dict[str, float]:
        """
        Local fallback when no vision API is configured.

        Returns empty dict - no tags assigned.
        """
        logger.info(f"Local fallback: no vision API configured for {image_path}")
        return {}

    def _call_vision_service(self, image_path: str) -> dict[str, float]:
        """
        Call the configured vision service to detect tags for an image.

        Args:
            image_path: Path to the image file.

        Returns:
            Dictionary mapping tag names to confidence scores.

        Raises:
            VisionServiceError: If the vision service call fails.
        """
        if self._provider == "google-vision":
            return self._call_google_vision(image_path)
        elif self._provider == "openai-vision":
            return self._call_openai_vision(image_path)
        else:
            return self._call_local_fallback(image_path)

    def tag_image(self, image_path: str) -> list[str]:
        """
        Assign tags to an image based on the vision service outputs and the taxonomy defined in the config.
        :param image_path: Path to the image file to be tagged
        :return: List of tags assigned to the image
        """
        tag_scores = self._call_vision_service(image_path)
        assigned_tags: list[str] = []
        for _, tags in self.taxonomy.items():
            if self.assign_multiple:
                # Assign all tags in this category that exceed the confidence threshold
                for tag in tags:
                    if tag_scores.get(tag, 0.0) >= self.threshold:
                        assigned_tags.append(tag)
            else:
                # Assign only the single highest-scoring tag in this category
                best_tag = None
                best_score = 0.0
                for tag in tags:
                    score = tag_scores.get(tag, 0.0)
                    if score > best_score:
                        best_score = score
                        best_tag = tag
                if best_tag is not None:
                    assigned_tags.append(best_tag)
        return assigned_tags
