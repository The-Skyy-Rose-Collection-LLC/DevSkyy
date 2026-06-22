"""Stage B: FLUX prompt engineering via Claude Opus.

Uses Claude Opus vision to write a single FLUX inpainting prompt grounded
in the scene reference image, subject matte, collection, and lighting spec.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def engineer_flux_prompt(
    *,
    scene_b64: str,
    subject_b64: str,
    collection: str,
    scene_name: str,
    lighting_spec: dict[str, Any],
    get_anthropic_client: Any,
) -> str:
    """Use Claude Opus to write a single FLUX prompt grounded in the dossier.

    Test fixtures patch ``get_anthropic_client`` at the ``compositor_agent``
    namespace and assert the model arg equals ``COMPOSITOR_OPUS_MODEL``.
    Do NOT hardcode the model string — always pull from config.

    Args:
        scene_b64: Base64-encoded JPEG of the scene reference.
        subject_b64: Base64-encoded JPEG of the alpha matte subject.
        collection: Collection slug (e.g. ``black-rose``).
        scene_name: Scene identifier string.
        lighting_spec: Dict loaded from ``scene.json`` (may be empty).
        get_anthropic_client: Callable that returns an Anthropic client
            (injected so tests can patch at the compositor_agent namespace).

    Returns:
        The generated FLUX prompt string.
    """
    from ...config import COMPOSITOR_OPUS_MODEL  # local import — tested with patched module

    client = get_anthropic_client()
    system = (
        "You write FLUX inpainting prompts for SkyyRose luxury fashion scene "
        "composites. Stay grounded in the visible subject and scene; never "
        "invent embellishments not present in the subject. Return ONLY the "
        "prompt text — no preamble, no quotes, no markdown."
    )
    user_text = (
        f"Collection: {collection}\n"
        f"Scene: {scene_name}\n"
        f"Lighting spec: {json.dumps(lighting_spec)}\n\n"
        "Write a single FLUX prompt (≤ 220 words) that places the SUBJECT "
        "naturally into the SCENE. Match scene lighting direction, color "
        "temperature, and mood. Preserve garment identity exactly."
    )

    # Anthropic's strict TypedDicts reject the plain dict literal at type
    # check time but accept it at runtime — cast at the SDK boundary.
    msg = client.messages.create(
        model=COMPOSITOR_OPUS_MODEL,
        max_tokens=512,
        system=system,
        messages=[  # type: ignore[arg-type]
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": scene_b64,
                        },
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": subject_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    # ``msg.content`` is a list of content blocks; first block is the text.
    return msg.content[0].text.strip()
