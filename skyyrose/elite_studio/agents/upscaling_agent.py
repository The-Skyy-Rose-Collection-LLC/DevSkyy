"""PIL LANCZOS upscaler with optional Replicate Real-ESRGAN primary path."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from PIL import Image

from skyyrose.elite_studio.models import UpscaleResult

logger = logging.getLogger(__name__)


class UpscalingAgent:
    """Upscale an image via Replicate (if key present) or PIL LANCZOS fallback."""

    def upscale(
        self,
        image_path: str,
        target_resolution: tuple[int, int] = (2048, 2048),
    ) -> UpscaleResult:
        """Return an UpscaleResult or a failure result if logic raises."""
        try:
            return self._upscale(image_path, target_resolution)
        except Exception as exc:  # noqa: BLE001
            logger.exception("UpscalingAgent._upscale failed for path=%s", image_path)
            return UpscaleResult(success=False, error=str(exc))

    def _upscale(
        self,
        image_path: str,
        target_resolution: tuple[int, int],
    ) -> UpscaleResult:
        path = Path(image_path)
        if not path.exists():
            return UpscaleResult(success=False, error=f"Image not found: {image_path}")

        with Image.open(path) as img:
            original_resolution: tuple[int, int] = img.size  # (width, height)

        # Try Replicate when a token is available
        if os.environ.get("REPLICATE_API_TOKEN") or os.environ.get("REPLICATE_API_KEY"):
            replicate_result = self._try_replicate(path, original_resolution, target_resolution)
            if replicate_result.success:
                return replicate_result
            logger.warning(
                "Replicate upscaling failed (%s); falling back to PIL LANCZOS",
                replicate_result.error,
            )

        return self._pil_upscale(path, original_resolution, target_resolution)

    def _try_replicate(
        self,
        path: Path,
        original_resolution: tuple[int, int],
        target_resolution: tuple[int, int],
    ) -> UpscaleResult:
        """Attempt Replicate Real-ESRGAN upscaling. Returns failure result on any error."""
        try:
            import replicate  # optional dependency

            with open(path, "rb") as f:
                output = replicate.run(
                    "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
                    input={"image": f, "scale": 2, "face_enhance": False},
                )

            output_path = path.parent / f"{path.stem}-upscaled{path.suffix}"
            if hasattr(output, "read"):
                output_path.write_bytes(output.read())
            else:
                import urllib.request

                urllib.request.urlretrieve(str(output), str(output_path))  # nosec B310 — URL from controlled API response, not user input

            return UpscaleResult(
                success=True,
                output_path=str(output_path),
                original_resolution=original_resolution,
                final_resolution=target_resolution,
                provider="replicate",
            )
        except Exception as exc:  # noqa: BLE001
            return UpscaleResult(success=False, error=str(exc))

    def _pil_upscale(
        self,
        path: Path,
        original_resolution: tuple[int, int],
        target_resolution: tuple[int, int],
    ) -> UpscaleResult:
        output_path = path.parent / f"{path.stem}-upscaled{path.suffix}"
        with Image.open(path) as img:
            resized = img.resize(target_resolution, Image.LANCZOS)
            resized.save(str(output_path))

        return UpscaleResult(
            success=True,
            output_path=str(output_path),
            original_resolution=original_resolution,
            final_resolution=target_resolution,
            provider="pil_lanczos",
        )
