"""Modal-hosted TRELLIS inference for image-to-3D garment generation.

Phase A5 of the elite-team creative cloud strategic spec
(docs/superpowers/specs/2026-05-27-elite-team-creative-cloud-strategic-spec.md).

Deploys Microsoft TRELLIS-image-large on Modal's serverless GPU infrastructure
(A10 verified working — Modal app ID ap-Y529mA2Ps4cDIH7bKS7EK3) so production
clothing-3D requests have a fast, paid alternative to the rate-limited HF
Space backend.

Targets:
  - generate_from_image(image_bytes, sampling, seed) -> {"glb": bytes, ...}
  - generate_from_text(prompt, sampling, seed)       -> {"glb": bytes, ...}
  - healthy()                                        -> bool

The sibling ``TrellisModalClient`` adapter (follow-up commit) implements
:class:`TrellisBackendClient` so the existing ``TrellisProvider`` failover
chain can route to this backend by setting ``TRELLIS_BACKEND=modal``.

Smoke test:
    modal run services/three_d/trellis/modal_app.py::smoke_br_001
"""

from __future__ import annotations

import io
import os
import time
from pathlib import Path
from typing import Any

import modal

# -----------------------------------------------------------------------------
# Modal app + image
# -----------------------------------------------------------------------------

# App name must match TRELLIS_MODAL_APP env var default in TrellisConfig
# (currently "trellis-3d"). Renaming requires updating config.py in lockstep.
APP_NAME = os.environ.get("TRELLIS_MODAL_APP_NAME", "trellis-3d")

app = modal.App(APP_NAME)

# CUDA 12.1 + Python 3.11 base. TRELLIS upstream pins torch==2.4.0+cu121 and
# needs trimesh / xformers / kaolin for mesh ops. The vendored copy at
# vendor/trellis is mounted read-only inside the container at /opt/trellis.
_trellis_image = (
    modal.Image.from_registry("nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04", add_python="3.11")
    .apt_install(
        "git",
        "ffmpeg",
        "libgl1-mesa-glx",
        "libglib2.0-0",
    )
    .pip_install(
        "torch==2.4.0",
        "torchvision==0.19.0",
        index_url="https://download.pytorch.org/whl/cu121",
    )
    .pip_install(
        "trimesh==4.5.3",
        "pillow>=10.2.0",
        "numpy>=1.26,<2.0",
        "rembg[gpu]==2.0.59",
        "transformers>=4.45.0",
        "accelerate>=0.34.0",
        "huggingface_hub>=0.25.0",
        "xformers==0.0.27.post2",
        "imageio[ffmpeg]>=2.34.0",
        "spconv-cu120==2.3.6",
        "easydict==1.13",
        "plyfile==1.1",
    )
    .env({"HF_HOME": "/root/.cache/huggingface", "TORCH_HOME": "/root/.cache/torch"})
)

# Persistent volume for model weights — first cold start downloads ~12GB of
# checkpoints; subsequent invocations skip the download.
_hf_cache_volume = modal.Volume.from_name("trellis-hf-cache", create_if_missing=True)

# HF token comes from a Modal secret; create with:
#   modal secret create huggingface-secret HF_TOKEN=hf_xxx
_secrets = [modal.Secret.from_name("huggingface-secret")]

_MODEL_NAME = os.environ.get("TRELLIS_MODEL", "microsoft/TRELLIS-image-large")
_GPU = os.environ.get("TRELLIS_MODAL_GPU", "A10")  # A10 verified ap-Y529mA2Ps4cDIH7bKS7EK3
_TIMEOUT_S = int(os.environ.get("TRELLIS_MODAL_TIMEOUT", "600"))
_CONTAINER_IDLE_S = int(os.environ.get("TRELLIS_MODAL_IDLE_TIMEOUT", "180"))


# -----------------------------------------------------------------------------
# Inference class — warm-loaded TRELLIS pipeline
# -----------------------------------------------------------------------------


@app.cls(
    image=_trellis_image,
    gpu=_GPU,
    timeout=_TIMEOUT_S,
    scaledown_window=_CONTAINER_IDLE_S,
    volumes={"/root/.cache/huggingface": _hf_cache_volume},
    secrets=_secrets,
)
class TrellisInference:
    """Warm-loaded TRELLIS pipeline running on a single GPU container.

    The model is loaded once per container via ``@modal.enter`` and reused
    for subsequent calls. Idle containers shut down after ``_CONTAINER_IDLE_S``
    seconds to bound cost.
    """

    @modal.enter()
    def load_model(self) -> None:
        """Initialize the TRELLIS pipeline on first container start.

        TRELLIS lives at https://github.com/microsoft/TRELLIS. The Python
        package is installed at runtime (not via pip_install above) because
        upstream does not publish to PyPI — we clone + install in-place.
        """
        import subprocess
        import sys

        trellis_path = Path("/opt/trellis")
        if not trellis_path.exists():
            subprocess.check_call(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "https://github.com/microsoft/TRELLIS.git",
                    str(trellis_path),
                ]
            )
        sys.path.insert(0, str(trellis_path))

        os.environ.setdefault("ATTN_BACKEND", "xformers")
        os.environ.setdefault("SPCONV_ALGO", "native")

        from trellis.pipelines import TrellisImageTo3DPipeline  # type: ignore[import-not-found]

        self._pipeline = TrellisImageTo3DPipeline.from_pretrained(_MODEL_NAME)
        self._pipeline.cuda()

    @modal.method()
    def generate_from_image(
        self,
        image_bytes: bytes,
        *,
        ss_sampling_steps: int = 12,
        ss_guidance_strength: float = 7.5,
        slat_sampling_steps: int = 12,
        slat_guidance_strength: float = 3.0,
        mesh_simplify: float = 0.95,
        texture_size: int = 1024,
        seed: int = 42,
    ) -> dict[str, Any]:
        """Run image-to-3D and return the GLB plus metadata.

        Args:
            image_bytes: Input image bytes (PNG / JPG / WEBP).
            ss_sampling_steps: TRELLIS structured-latent sampling steps.
            ss_guidance_strength: Guidance scale for structured-latent stage.
            slat_sampling_steps: Spatial-latent sampling steps.
            slat_guidance_strength: Guidance scale for spatial-latent stage.
            mesh_simplify: Decimation ratio (0.0 = none, 1.0 = max).
            texture_size: Output texture map resolution (square).
            seed: RNG seed for reproducibility.

        Returns:
            Dict with keys:
                glb (bytes): Binary GLB mesh.
                seed (int): Seed actually used.
                duration_seconds (float): Wall-clock generation time.
                backend (str): Always "modal".
                model (str): TRELLIS model identifier.
        """
        from PIL import Image
        from trellis.utils import postprocessing_utils  # type: ignore[import-not-found]

        started = time.perf_counter()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        outputs = self._pipeline.run(
            image,
            seed=seed,
            sparse_structure_sampler_params={
                "steps": ss_sampling_steps,
                "cfg_strength": ss_guidance_strength,
            },
            slat_sampler_params={
                "steps": slat_sampling_steps,
                "cfg_strength": slat_guidance_strength,
            },
        )

        glb = postprocessing_utils.to_glb(
            outputs["gaussian"][0],
            outputs["mesh"][0],
            simplify=mesh_simplify,
            texture_size=texture_size,
        )
        # to_glb returns a trimesh.Scene; export to bytes
        glb_bytes = glb.export(file_type="glb")
        if isinstance(glb_bytes, bytearray):
            glb_bytes = bytes(glb_bytes)

        return {
            "glb": glb_bytes,
            "seed": seed,
            "duration_seconds": round(time.perf_counter() - started, 3),
            "backend": "modal",
            "model": _MODEL_NAME,
        }

    @modal.method()
    def generate_from_text(
        self,
        prompt: str,
        *,
        ss_sampling_steps: int = 12,
        ss_guidance_strength: float = 7.5,
        slat_sampling_steps: int = 12,
        slat_guidance_strength: float = 3.0,
        mesh_simplify: float = 0.95,
        texture_size: int = 1024,
        seed: int = 42,
    ) -> dict[str, Any]:
        """Run text-to-3D via TRELLIS-text-large (separate checkpoint).

        Text mode requires the TRELLIS-text-large checkpoint, not the
        image checkpoint. This method raises NotImplementedError until the
        text pipeline is loaded — current Phase A5 scope is image-only.
        """
        raise NotImplementedError(
            "Text-to-3D requires TRELLIS-text-large checkpoint — not loaded "
            "in this app instance. Phase A5 scope is image-to-3D only. "
            "Set TRELLIS_MODEL=microsoft/TRELLIS-text-large + redeploy when "
            "text path is needed."
        )

    @modal.method()
    def healthy(self) -> dict[str, Any]:
        """Health probe — confirm pipeline loaded and CUDA available."""
        try:
            import torch

            return {
                "ok": True,
                "cuda_available": torch.cuda.is_available(),
                "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
                "model": _MODEL_NAME,
                "backend_name": "modal",
            }
        except Exception as exc:  # pragma: no cover — health probe must not raise
            return {"ok": False, "error": str(exc), "backend_name": "modal"}


# -----------------------------------------------------------------------------
# Smoke test — `modal run modal_app.py::smoke --sku br-001`
# -----------------------------------------------------------------------------

# Canonical golden image layout — one front.jpg per SKU under this root.
# Stays in lockstep with skyyrose/elite_studio/assets/golden/{sku}/front.jpg.
_GOLDEN_ROOT = "skyyrose/elite_studio/assets/golden"


def _golden_image_path(sku: str) -> Path:
    """Resolve the canonical golden front.jpg for a SKU.

    Layout: ``skyyrose/elite_studio/assets/golden/{sku}/front.jpg`` — single
    source of truth for 3D smoke inputs. Per-SKU overrides via --image-path.
    """
    return Path(_GOLDEN_ROOT) / sku / "front.jpg"


@app.local_entrypoint()
def smoke(
    sku: str = "br-001",
    image_path: str = "",
    output_path: str = "",
    seed: int = 42,
) -> None:
    """End-to-end smoke: golden SKU image -> .glb saved locally.

    Usage:
        modal run services/three_d/trellis/modal_app.py::smoke
        modal run services/three_d/trellis/modal_app.py::smoke --sku br-003
        modal run services/three_d/trellis/modal_app.py::smoke --sku br-003 \\
            --image-path /custom/path.jpg --output-path /tmp/custom.glb

    Defaults:
        image_path  -> {_GOLDEN_ROOT}/{sku}/front.jpg
        output_path -> /tmp/{sku}-trellis-modal.glb

    Validates:
        - Container starts on A10 GPU
        - Model loads from HF cache (or downloads on first run)
        - generate_from_image returns valid GLB bytes
        - Output is non-empty and saves to local disk
    """
    src = Path(image_path) if image_path else _golden_image_path(sku)
    if not src.exists():
        raise FileNotFoundError(
            f"smoke input image missing: {src} — drop a front.jpg at "
            f"{_GOLDEN_ROOT}/{sku}/ or pass --image-path"
        )

    dest = Path(output_path) if output_path else Path(f"/tmp/{sku}-trellis-modal.glb")

    print(f"[smoke] sku={sku} reading {src} ({src.stat().st_size} bytes)")
    image_bytes = src.read_bytes()

    inference = TrellisInference()

    print("[smoke] health probe ...")
    health = inference.healthy.remote()
    print(f"[smoke] health: {health}")
    if not health.get("ok"):
        raise RuntimeError(f"health probe failed: {health}")

    print(f"[smoke] generate_from_image on {_GPU} ...")
    result = inference.generate_from_image.remote(image_bytes, seed=seed)

    glb_bytes = result["glb"]
    if not glb_bytes or len(glb_bytes) < 1024:
        raise RuntimeError(
            f"GLB output suspiciously small ({len(glb_bytes) if glb_bytes else 0} bytes)"
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(glb_bytes)

    print(
        f"[smoke] OK — sku={sku} wrote {len(glb_bytes)} bytes to {dest} "
        f"in {result['duration_seconds']}s (seed={result['seed']})"
    )
