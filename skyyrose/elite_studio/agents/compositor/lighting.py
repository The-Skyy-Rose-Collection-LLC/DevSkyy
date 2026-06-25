"""Scene lookbook and lighting spec loader.

``SCENE_LOOKBOOK`` is a legacy export that maps scene slugs to collection
prefixes. External callers (coordinator.py, cli.py) import it directly from
``compositor_agent`` — the shim re-exports it from here.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Scene SKU lookbook (legacy export for callers that import it).
SCENE_LOOKBOOK: dict[str, str] = {
    "black-rose-bay-bridge-sf-side-night": "br-",
    "love-hurts-enchanted-rose-cathedral": "lh-",
    "signature-oakland-waterfront-bay-bridge-day": "sg-",
    "kids-capsule-urban-playground": "kids-",
}


def load_lighting_spec(collection: str, scene_name: str) -> dict[str, Any]:
    """Look for ``{scenes_dir}/{collection}/{scene_name}/scene.json``.

    Returns an empty dict if missing — Stage B will infer reasonable
    defaults from the collection.

    Args:
        collection: Collection slug (e.g. ``black-rose``).
        scene_name: Scene identifier used to resolve the ``scene.json`` path.

    Returns:
        Parsed scene lighting spec dict, or ``{}`` if not found / invalid JSON.
    """
    try:
        from ...config import SCENES_DIR
    except ImportError:
        return {}
    candidate = Path(SCENES_DIR) / collection / scene_name / "scene.json"
    if candidate.is_file():
        try:
            return json.loads(candidate.read_text())
        except json.JSONDecodeError:
            return {}
    # Sibling scene.json (when scene_name is the directory itself)
    sibling = Path(SCENES_DIR) / collection / "scene.json"
    if sibling.is_file():
        try:
            return json.loads(sibling.read_text())
        except json.JSONDecodeError:
            return {}
    return {}
