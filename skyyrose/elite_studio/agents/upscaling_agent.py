"""
Upscaling Agent — Real-ESRGAN via Replicate (fallback: PIL LANCZOS)

Upscales generated images to target resolution.
Primary: nightmareai/real-esrgan on Replicate.
Fallback: PIL.Image.resize with LANCZOS filter.
"""

from __future__ import annotations

import os
from pathlib import Path

from ..models import UpscaleResult

_DEFAULT_TARGET: tuple[int, int] = (2048, 2048)


class UpscalingAgent:
    """Image upscaling agent.

    Tries Replicate Real-ESRGAN first; falls back to PIL LANCZOS
    if the Replicate API is unavailable or fails.
    """

    def upscale(
        self,
        image_path: str,
        target_resolution: tuple[int, int] = _DEFAULT_TARGET,
    ) -> UpscaleResult:
        """Upscale an image to target resolution.

        Args:
            image_path: Path to source image.
            target_resolution: (width, height) target in pixels.

        Returns:
            UpscaleResult with output_path, provider, and resolutions.
        """
        try:
            return self._upscale(image_path, target_resolution)
        except Exception as exc:
            return UpscaleResult(
                success=False,
                error=str(exc),
            )

    def _upscale(
        self,
        image_path: str,
        target_resolution: tuple[int, int],
    ) -> UpscaleResult:
        from PIL import Image

        src = Path(image_path)
        if not src.exists():
            return UpscaleResult(
                success=False,
                error=f"Source image not found: {image_path}",
            )

        with Image.open(src) as img:
            original_resolution = (img.width, img.height)

        # Try Replicate first
        replicate_key = os.getenv("REPLICATE_API_TOKEN") or os.getenv("REPLICATE_API_KEY")
        if replicate_key:
            result = self._try_replicate(src, target_resolution, original_resolution)
            if result.success:
                return result

        # Fallback to PIL LANCZOS
        return self._pil_upscale(src, target_resolution, original_resolution)

    def _try_replicate(
        self,
        src: Path,
        target_resolution: tuple[int, int],
        original_resolution: tuple[int, int],
    ) -> UpscaleResult:
        try:
            try:
                import replicate
            except Exception as import_exc:
                return UpscaleResult(
                    success=False,
                    error=f"Replicate import failed: {import_exc}",
                )

            output_path = src.parent / f"{src.stem}-upscaled{src.suffix}"

            with open(src, "rb") as f:
                output = replicate.run(
                    "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
                    input={"image": f, "scale": 4, "face_enhance": False},
                )

            # output is a URL or file-like; download it
            if hasattr(output, "read"):
                image_bytes = output.read()
            else:
                import urllib.request

                with urllib.request.urlopen(str(output)) as resp:
                    image_bytes = resp.read()

            import io

            from PIL import Image

            with Image.open(io.BytesIO(image_bytes)) as img:
                # Resize to exact target if different
                if (img.width, img.height) != target_resolution:
                    img = img.resize(target_resolution, Image.LANCZOS)
                final_resolution = (img.width, img.height)
                img.save(str(output_path))

            return UpscaleResult(
                success=True,
                output_path=str(output_path),
                original_resolution=original_resolution,
                final_resolution=final_resolution,
                provider="replicate",
            )
        except Exception as exc:
            return UpscaleResult(
                success=False,
                error=f"Replicate upscale failed: {exc}",
            )

    def _pil_upscale(
        self,
        src: Path,
        target_resolution: tuple[int, int],
        original_resolution: tuple[int, int],
    ) -> UpscaleResult:
        try:
            from PIL import Image

            output_path = src.parent / f"{src.stem}-upscaled{src.suffix}"

            with Image.open(src) as img:
                upscaled = img.resize(target_resolution, Image.LANCZOS)
                upscaled.save(str(output_path))
                final_resolution = (upscaled.width, upscaled.height)

            return UpscaleResult(
                success=True,
                output_path=str(output_path),
                original_resolution=original_resolution,
                final_resolution=final_resolution,
                provider="pil_lanczos",
            )
        except Exception as exc:
            return UpscaleResult(
                success=False,
                error=f"PIL upscale failed: {exc}",
            )
