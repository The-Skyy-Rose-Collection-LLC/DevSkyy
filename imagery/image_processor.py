# imagery/image_processor.py
"""
Image Processing Module for DevSkyy.

Provides image preprocessing, enhancement, and background removal
for optimal 3D model generation from 2D product images.

Reference: Context7 Pillow documentation for image processing patterns.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

# Lazy imports for optional dependencies
try:
    from PIL import Image, ImageEnhance

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None  # type: ignore

from errors.production_errors import ImageProcessingError

logger = logging.getLogger(__name__)


class ImageFormat(str, Enum):
    """Supported image formats."""

    PNG = "PNG"
    JPEG = "JPEG"
    WEBP = "WEBP"
    TIFF = "TIFF"


@dataclass
class ImageMetadata:
    """Metadata about a processed image."""

    width: int
    height: int
    format: str
    mode: str
    has_alpha: bool
    file_size_bytes: int
    dpi: tuple[int, int] | None = None


class ImageProcessor:
    """
    Production-grade image processor for DevSkyy.

    Features:
    - Image resizing and normalization
    - Format conversion
    - Quality enhancement
    - Metadata extraction
    """

    # Standard sizes for 3D generation
    STANDARD_SIZES = {
        "thumbnail": (256, 256),
        "preview": (512, 512),
        "standard": (1024, 1024),
        "high_res": (2048, 2048),
        "ultra": (4096, 4096),
    }

    def __init__(self) -> None:
        """Initialize the image processor."""
        if not PIL_AVAILABLE:
            raise ImportError(
                "Pillow is required for image processing. " "Install with: pip install Pillow"
            )

    def load_image(self, source: str | Path | bytes | io.BytesIO) -> Image.Image:
        """
        Load an image from various sources.

        Args:
            source: File path, bytes, or BytesIO

        Returns:
            PIL Image object
        """
        try:
            if isinstance(source, (str, Path)):
                return Image.open(source)
            elif isinstance(source, bytes):
                return Image.open(io.BytesIO(source))
            elif isinstance(source, io.BytesIO):
                return Image.open(source)
            else:
                raise ImageProcessingError(f"Unsupported image source type: {type(source)}")
        except Exception as e:
            raise ImageProcessingError(
                f"Failed to load image: {e}",
                operation="load",
                cause=e,
            )

    def save_image(
        self,
        image: Image.Image,
        output_path: str | Path,
        format: ImageFormat = ImageFormat.PNG,
        quality: int = 95,
    ) -> Path:
        """
        Save an image to file.

        Args:
            image: PIL Image to save
            output_path: Destination path
            format: Output format
            quality: JPEG quality (1-100)

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            save_kwargs: dict[str, Any] = {"format": format.value}
            if format == ImageFormat.JPEG:
                save_kwargs["quality"] = quality
            elif format == ImageFormat.PNG:
                save_kwargs["optimize"] = True
            elif format == ImageFormat.WEBP:
                save_kwargs["quality"] = quality

            image.save(output_path, **save_kwargs)
            return output_path

        except Exception as e:
            raise ImageProcessingError(
                f"Failed to save image: {e}",
                operation="save",
                cause=e,
            )

    def resize(
        self,
        image: Image.Image,
        size: tuple[int, int] | str,
        maintain_aspect: bool = True,
        resample: int | None = None,
    ) -> Image.Image:
        """
        Resize an image.

        Args:
            image: Image to resize
            size: Target size as (width, height) or preset name
            maintain_aspect: Whether to maintain aspect ratio
            resample: Resampling filter (default: LANCZOS)

        Returns:
            Resized image
        """
        if isinstance(size, str):
            if size not in self.STANDARD_SIZES:
                raise ImageProcessingError(
                    f"Unknown size preset: {size}. "
                    f"Available: {list(self.STANDARD_SIZES.keys())}"
                )
            size = self.STANDARD_SIZES[size]

        if resample is None:
            resample = Image.Resampling.LANCZOS

        try:
            if maintain_aspect:
                image.thumbnail(size, resample)
                return image
            else:
                return image.resize(size, resample)
        except Exception as e:
            raise ImageProcessingError(
                f"Failed to resize image: {e}",
                operation="resize",
                cause=e,
            )

    def normalize(
        self,
        image: Image.Image,
        target_size: tuple[int, int] = (1024, 1024),
        target_mode: str = "RGB",
        background_color: tuple[int, int, int] = (255, 255, 255),
    ) -> Image.Image:
        """
        Normalize an image for consistent processing.

        Args:
            image: Image to normalize
            target_size: Target dimensions
            target_mode: Target color mode
            background_color: Background color for transparency

        Returns:
            Normalized image
        """
        try:
            # Convert mode if needed
            if image.mode != target_mode:
                if image.mode == "RGBA" and target_mode == "RGB":
                    # Handle transparency
                    background = Image.new("RGB", image.size, background_color)
                    background.paste(image, mask=image.split()[3])
                    image = background
                else:
                    image = image.convert(target_mode)

            # Resize while maintaining aspect ratio
            image = self.resize(image, target_size, maintain_aspect=True)

            # Center on canvas if needed
            if image.size != target_size:
                canvas = Image.new(target_mode, target_size, background_color)
                x = (target_size[0] - image.size[0]) // 2
                y = (target_size[1] - image.size[1]) // 2
                canvas.paste(image, (x, y))
                image = canvas

            return image

        except Exception as e:
            raise ImageProcessingError(
                f"Failed to normalize image: {e}",
                operation="normalize",
                cause=e,
            )

    def enhance(
        self,
        image: Image.Image,
        brightness: float = 1.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        sharpness: float = 1.0,
    ) -> Image.Image:
        """
        Enhance image quality.

        Args:
            image: Image to enhance
            brightness: Brightness factor (1.0 = no change)
            contrast: Contrast factor
            saturation: Color saturation factor
            sharpness: Sharpness factor

        Returns:
            Enhanced image
        """
        try:
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(brightness)

            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(contrast)

            if saturation != 1.0:
                enhancer = ImageEnhance.Color(image)
                image = enhancer.enhance(saturation)

            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(sharpness)

            return image

        except Exception as e:
            raise ImageProcessingError(
                f"Failed to enhance image: {e}",
                operation="enhance",
                cause=e,
            )

    def get_metadata(self, image: Image.Image) -> ImageMetadata:
        """Get metadata from an image."""
        return ImageMetadata(
            width=image.width,
            height=image.height,
            format=image.format or "unknown",
            mode=image.mode,
            has_alpha=image.mode in ("RGBA", "LA", "PA"),
            file_size_bytes=0,  # Only available for file sources
            dpi=image.info.get("dpi"),
        )

    def to_bytes(
        self,
        image: Image.Image,
        format: ImageFormat = ImageFormat.PNG,
        quality: int = 95,
    ) -> bytes:
        """Convert image to bytes."""
        buffer = io.BytesIO()
        save_kwargs: dict[str, Any] = {"format": format.value}
        if format == ImageFormat.JPEG:
            save_kwargs["quality"] = quality

        image.save(buffer, **save_kwargs)
        return buffer.getvalue()


class ImagePreprocessor:
    """
    Image preprocessor optimized for 3D generation.

    Prepares product images for optimal 3D model generation by:
    - Removing backgrounds
    - Centering products
    - Normalizing lighting
    - Ensuring consistent sizing
    """

    def __init__(self) -> None:
        """Initialize the preprocessor."""
        self.processor = ImageProcessor()

    async def preprocess_for_3d(
        self,
        image_source: str | Path | bytes,
        remove_background: bool = True,
        target_size: tuple[int, int] = (1024, 1024),
        enhance: bool = True,
    ) -> Image.Image:
        """
        Preprocess an image for 3D generation.

        Args:
            image_source: Source image
            remove_background: Whether to remove background
            target_size: Target dimensions
            enhance: Whether to apply enhancements

        Returns:
            Preprocessed image ready for 3D generation
        """
        # Load image
        image = self.processor.load_image(image_source)

        # Remove background if requested
        if remove_background:
            remover = BackgroundRemover()
            image = await remover.remove_background(image)

        # Normalize
        image = self.processor.normalize(
            image,
            target_size=target_size,
            target_mode="RGBA" if remove_background else "RGB",
        )

        # Enhance if requested
        if enhance:
            # Convert to RGB for enhancement
            if image.mode == "RGBA":
                alpha = image.split()[3]
                rgb_image = image.convert("RGB")
                rgb_image = self.processor.enhance(
                    rgb_image,
                    contrast=1.1,
                    sharpness=1.2,
                )
                # Restore alpha
                rgb_image.putalpha(alpha)
                image = rgb_image
            else:
                image = self.processor.enhance(
                    image,
                    contrast=1.1,
                    sharpness=1.2,
                )

        return image


class BackgroundRemover:
    """
    Background removal for product images.

    Uses multiple strategies:
    1. AI-based removal (rembg if available)
    2. Color-based removal
    3. Edge detection
    """

    def __init__(self) -> None:
        """Initialize the background remover."""
        self._rembg_available = False
        try:
            import rembg

            self._rembg_available = True
            self._rembg = rembg
        except ImportError:
            pass

    async def remove_background(
        self,
        image: Image.Image,
        method: str = "auto",
    ) -> Image.Image:
        """
        Remove background from an image.

        Args:
            image: Image to process
            method: Method to use ("auto", "ai", "color", "edge")

        Returns:
            Image with transparent background
        """
        if method == "auto":
            method = "ai" if self._rembg_available else "color"

        if method == "ai" and self._rembg_available:
            return await self._remove_with_rembg(image)
        elif method == "color":
            return self._remove_by_color(image)
        elif method == "edge":
            return self._remove_by_edge(image)
        else:
            logger.warning(f"Unknown method {method}, using color-based removal")
            return self._remove_by_color(image)

    async def _remove_with_rembg(self, image: Image.Image) -> Image.Image:
        """Remove background using rembg AI model."""
        try:
            output = self._rembg.remove(image)
            return output
        except Exception as e:
            logger.warning(f"AI background removal failed: {e}, falling back to color")
            return self._remove_by_color(image)

    def _remove_by_color(
        self,
        image: Image.Image,
        bg_color: tuple[int, int, int] = (255, 255, 255),
        tolerance: int = 30,
    ) -> Image.Image:
        """Remove background by color similarity."""
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        data = np.array(image)

        # Calculate distance from background color
        r, g, b = bg_color
        distance = np.sqrt(
            (data[:, :, 0].astype(float) - r) ** 2
            + (data[:, :, 1].astype(float) - g) ** 2
            + (data[:, :, 2].astype(float) - b) ** 2
        )

        # Create alpha mask
        alpha = np.where(distance < tolerance, 0, 255).astype(np.uint8)
        data[:, :, 3] = alpha

        return Image.fromarray(data)

    def _remove_by_edge(self, image: Image.Image) -> Image.Image:
        """Remove background using edge detection."""
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not available, using color-based removal")
            return self._remove_by_color(image)

        # Convert to numpy array
        if image.mode != "RGB":
            image = image.convert("RGB")

        img_array = np.array(image)

        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)

        # Dilate edges to close gaps
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=2)

        # Find contours and create mask
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        mask = np.zeros(gray.shape, dtype=np.uint8)
        if contours:
            # Fill the largest contour
            largest = max(contours, key=cv2.contourArea)
            cv2.drawContours(mask, [largest], -1, 255, -1)

        # Apply mask
        result = np.dstack([img_array, mask])

        return Image.fromarray(result)
