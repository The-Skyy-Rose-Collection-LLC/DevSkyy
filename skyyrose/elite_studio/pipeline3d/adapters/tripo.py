"""Tripo adapter — image-to-3D, texture, remesh via the tripo3d SDK 0.4.1.

Stage -> SDK call mapping (all return a task_id, then wait_for_task + download):
  IMAGE_TO_3D -> client.image_to_model(image=<src>, texture=False, pbr=False)  (base mesh)
  TEXTURE     -> client.texture_model(original_model_task_id=<prior>, texture=True, pbr=True)
  REMESH      -> client.smart_lowpoly(original_model_task_id=<prior>, face_limit=N, quad=False)

Note: convert_model does NOT accept 'GLB' (GLB is the native output); it is for
USDZ/FBX/etc. and is deferred to a later phase. GLB remesh uses smart_lowpoly.

Same-provider chaining uses the prior stage's Tripo task_id (carried on
ctx.last_artifact.task_id). The artifact is also downloaded to a local path each
stage so a stale 24h artifact URL never breaks a resume.
"""

from __future__ import annotations

import os
from pathlib import Path

try:  # tripo3d is an optional, API-key-gated SDK; a soft import keeps test
    from tripo3d import TripoClient  # collection and non-3D paths from hard-requiring it.
except ImportError:  # pragma: no cover - exercised only when the SDK is absent
    TripoClient = None  # type: ignore[assignment,misc]

from ..models import Artifact, Stage
from .base import StageContext

# Rough USD estimates (provider credits -> USD). These are ESTIMATES sourced from
# provider docs; tune via env overrides. See spec §10 (Risks).
_DEFAULT_COST = {
    Stage.IMAGE_TO_3D: float(os.getenv("PIPELINE3D_TRIPO_IMAGE_USD", "0.40")),
    Stage.TEXTURE: float(os.getenv("PIPELINE3D_TRIPO_TEXTURE_USD", "0.20")),
    Stage.REMESH: float(os.getenv("PIPELINE3D_TRIPO_REMESH_USD", "0.15")),
}
_SUPPORTED = (Stage.IMAGE_TO_3D, Stage.TEXTURE, Stage.REMESH)
#: Extensions that count as a 3D mesh (never a texture/preview PNG).
_MESH_EXTS = (".glb", ".gltf", ".obj", ".fbx", ".usdz", ".stl")


def _pick_mesh(downloaded: dict) -> str | None:
    """Select the mesh file from a tripo download dict — never a texture/preview.

    The SDK's ``download_task_models`` returns a dict that may include texture
    PNGs, normal maps, and previews alongside the mesh. Prefer the explicit
    ``model`` key; otherwise fall back to the first value with a mesh extension.
    Returns ``None`` if no mesh-like file is present so the caller can fail loud
    instead of copying a PNG to ``<sku>.glb``.
    """
    model = downloaded.get("model")
    if isinstance(model, str) and model:
        return model
    for value in downloaded.values():
        if isinstance(value, str) and value.lower().endswith(_MESH_EXTS):
            return value
    return None


class TripoAdapter:
    """Wraps the tripo3d SDK behind the Adapter port."""

    name = "tripo"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        output_dir: str | Path = Path("renders/3d/_tripo"),
        timeout: float = 300.0,
        default_polycount: int = 30000,
    ) -> None:
        self._api_key = (
            api_key
            if api_key is not None
            else (os.getenv("TRIPO_API_KEY") or os.getenv("TRIPO3D_API_KEY") or "")
        )
        self._output_dir = Path(output_dir)
        self._timeout = timeout
        self._default_polycount = default_polycount

    def supports(self, stage: Stage) -> bool:
        return stage in _SUPPORTED

    def available(self) -> bool:
        return bool(self._api_key)

    def estimate_cost(self, stage: Stage, params: dict) -> float:
        return _DEFAULT_COST.get(stage, 0.0)

    async def run_stage(self, stage: Stage, ctx: StageContext) -> Artifact:
        if stage not in _SUPPORTED:
            raise ValueError(f"tripo adapter does not support stage={stage.value!r}")
        if stage in (Stage.TEXTURE, Stage.REMESH):
            prior = ctx.last_artifact
            if prior is None or prior.task_id is None:
                raise ValueError(f"{stage.value} requires a prior Tripo task_id to chain")

        self._output_dir.mkdir(parents=True, exist_ok=True)

        if TripoClient is None:  # SDK absent — fail loud with an install hint, never silently.
            raise RuntimeError(
                "tripo3d SDK not installed; run `pip install tripo3d>=0.4.1` to use the Tripo adapter"
            )

        async with TripoClient(api_key=self._api_key) as client:
            if stage == Stage.IMAGE_TO_3D:
                task_id = await client.image_to_model(
                    image=str(ctx.source_image), texture=False, pbr=False
                )
            elif stage == Stage.TEXTURE:
                task_id = await client.texture_model(
                    original_model_task_id=ctx.last_artifact.task_id, texture=True, pbr=True
                )
            else:  # Stage.REMESH
                face_limit = int(ctx.params.get("target_polycount", self._default_polycount))
                task_id = await client.smart_lowpoly(
                    original_model_task_id=ctx.last_artifact.task_id,
                    face_limit=face_limit,
                    quad=False,
                )

            task = await client.wait_for_task(task_id, timeout=self._timeout)
            downloaded = await client.download_task_models(task, str(self._output_dir))
            model_path = _pick_mesh(downloaded)
            if model_path is None:
                raise RuntimeError(
                    f"tripo {stage.value} returned no mesh file (download keys={list(downloaded)})"
                )
            output = getattr(task, "output", None)
            model_url = getattr(output, "model", None) if output is not None else None

        # model_path is guaranteed non-None here — the RuntimeError above fires otherwise.
        path = Path(model_path)
        return Artifact(
            provider="tripo",
            fmt="glb",
            task_id=task_id,
            model_url=model_url,
            path=path,
            bytes=path.stat().st_size if path.is_file() else None,
            meta={"tripo_status": str(getattr(task, "status", "")), "stage": stage.value},
        )


__all__ = ["TripoAdapter"]
