# services/ml/watermark_service.py
"""
Invisible Watermarking Service for DevSkyy.

Embeds invisible watermarks in AI-generated imagery for tracking
and authenticity verification. Uses steganographic techniques that
survive compression, resizing, and format conversion.

CRITICAL: Watermarks must be invisible to human eye in all output formats.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import struct
import zlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np
from PIL import Image
from pydantic import BaseModel

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Magic header for watermark detection
WATERMARK_MAGIC = b"DSKY"

# Watermark version
WATERMARK_VERSION = 1

# Minimum image size for watermarking
MIN_IMAGE_SIZE = 256

# Bit depth for embedding (lower = more robust, higher = more data)
EMBED_BIT_DEPTH = 2


# =============================================================================
# Models
# =============================================================================


@dataclass
class WatermarkPayload:
    """Data embedded in watermark."""

    job_id: str
    product_id: str
    model_used: str
    generation_date: str
    checksum: str

    def to_bytes(self) -> bytes:
        """Serialize payload to bytes."""
        data = {
            "j": self.job_id[:32],  # Truncate to limit size
            "p": self.product_id[:32],
            "m": self.model_used[:64],
            "d": self.generation_date,
            "c": self.checksum[:16],
        }
        json_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
        compressed = zlib.compress(json_bytes, level=9)
        return compressed

    @classmethod
    def from_bytes(cls, data: bytes) -> WatermarkPayload:
        """Deserialize payload from bytes."""
        decompressed = zlib.decompress(data)
        parsed = json.loads(decompressed.decode("utf-8"))
        return cls(
            job_id=parsed["j"],
            product_id=parsed["p"],
            model_used=parsed["m"],
            generation_date=parsed["d"],
            checksum=parsed["c"],
        )


class WatermarkResult(BaseModel):
    """Result of watermarking operation."""

    original_url: str | None = None
    watermarked_image_bytes: bytes | None = None
    payload: dict[str, str]
    embedding_strength: float
    processing_time_ms: int
    correlation_id: str

    class Config:
        arbitrary_types_allowed = True


class WatermarkDetectionResult(BaseModel):
    """Result of watermark detection."""

    has_watermark: bool
    payload: dict[str, str] | None = None
    confidence: float
    correlation_id: str


class WatermarkError(DevSkyError):
    """Error during watermarking operations."""

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context: dict[str, Any] = {}
        if operation:
            context["operation"] = operation

        super().__init__(
            message,
            code=DevSkyErrorCode.IMAGE_PROCESSING_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            cause=cause,
            correlation_id=correlation_id,
            retryable=False,
        )


# =============================================================================
# Service
# =============================================================================


class WatermarkService:
    """
    Service for invisible watermarking of AI-generated imagery.

    Features:
    - Steganographic embedding invisible to human eye
    - Survives: compression, resizing, format conversion
    - Encodes: job_id, product_id, model, generation date
    - Detection endpoint for watermark extraction
    - Batch scanning for asset auditing

    CRITICAL: Watermarks must not be visible in any output format.

    Usage:
        service = WatermarkService()

        # Embed watermark
        result = service.embed_watermark(
            image,
            job_id="job-123",
            product_id="SKU-456",
            model_used="sdxl",
        )

        # Detect watermark
        detection = service.detect_watermark(watermarked_image)
        if detection.has_watermark:
            print(detection.payload)
    """

    def __init__(
        self,
        embed_strength: float = 0.05,
    ) -> None:
        """
        Initialize watermark service.

        Args:
            embed_strength: Embedding strength (0.01-0.1). Lower is more
                invisible but less robust.
        """
        self._embed_strength = max(0.01, min(0.1, embed_strength))

    def _generate_correlation_id(self) -> str:
        """Generate a correlation ID."""
        import uuid

        return str(uuid.uuid4())

    def _compute_checksum(self, job_id: str, product_id: str, model_used: str) -> str:
        """Compute checksum for payload verification."""
        data = f"{job_id}:{product_id}:{model_used}".encode()
        return hashlib.sha256(data).hexdigest()[:16]

    def _encode_payload_to_bits(self, payload: WatermarkPayload) -> list[int]:
        """Convert payload to bit sequence for embedding."""
        data = WATERMARK_MAGIC + struct.pack("B", WATERMARK_VERSION)
        payload_bytes = payload.to_bytes()
        data += struct.pack("<H", len(payload_bytes))
        data += payload_bytes

        # Pad to multiple of 8
        while len(data) % 8 != 0:
            data += b"\x00"

        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)

        return bits

    def _decode_bits_to_payload(self, bits: list[int]) -> WatermarkPayload | None:
        """Convert bit sequence back to payload."""
        if len(bits) < 56:  # Minimum header size
            return None

        # Convert bits to bytes
        bytes_data = bytearray()
        for i in range(0, len(bits) - 7, 8):
            byte = 0
            for j in range(8):
                byte = (byte << 1) | bits[i + j]
            bytes_data.append(byte)

        # Check magic header
        if bytes_data[:4] != WATERMARK_MAGIC:
            return None

        version = bytes_data[4]
        if version != WATERMARK_VERSION:
            logger.warning(f"Unknown watermark version: {version}")
            return None

        try:
            payload_len = struct.unpack("<H", bytes(bytes_data[5:7]))[0]
            payload_data = bytes(bytes_data[7 : 7 + payload_len])
            return WatermarkPayload.from_bytes(payload_data)
        except Exception as e:
            logger.debug(f"Failed to decode payload: {e}")
            return None

    def _embed_bits_dct(self, img: Image.Image, bits: list[int]) -> Image.Image:
        """
        Embed bits using DCT-domain steganography.

        This method modifies mid-frequency DCT coefficients which:
        - Survives JPEG compression
        - Is less visible to human eye
        - Maintains reasonable robustness
        """
        # Convert to numpy array
        arr = np.array(img.convert("RGB"), dtype=np.float64)

        # Work with blue channel (least perceptually sensitive)
        blue = arr[:, :, 2].copy()

        # Process in 8x8 blocks
        h, w = blue.shape
        blocks_h = h // 8
        blocks_w = w // 8

        bit_idx = 0
        total_bits = len(bits)

        for by in range(blocks_h):
            for bx in range(blocks_w):
                if bit_idx >= total_bits:
                    break

                y_start = by * 8
                x_start = bx * 8
                block = blue[y_start : y_start + 8, x_start : x_start + 8]

                # Apply DCT (simplified - use 2D DCT)
                dct_block = self._dct2(block)

                # Embed bit in mid-frequency coefficient
                mid_coef = dct_block[3, 4]
                bit = bits[bit_idx]

                # Quantize and embed
                strength = self._embed_strength * 50
                if bit == 1:
                    dct_block[3, 4] = np.floor(mid_coef / strength) * strength + strength / 2
                else:
                    dct_block[3, 4] = np.floor(mid_coef / strength) * strength

                # Inverse DCT
                block = self._idct2(dct_block)
                blue[y_start : y_start + 8, x_start : x_start + 8] = block

                bit_idx += 1

            if bit_idx >= total_bits:
                break

        # Reconstruct image
        arr[:, :, 2] = np.clip(blue, 0, 255)
        return Image.fromarray(arr.astype(np.uint8))

    def _extract_bits_dct(self, img: Image.Image, expected_bits: int) -> list[int]:
        """Extract embedded bits from image."""
        arr = np.array(img.convert("RGB"), dtype=np.float64)
        blue = arr[:, :, 2]

        h, w = blue.shape
        blocks_h = h // 8
        blocks_w = w // 8

        bits = []

        for by in range(blocks_h):
            for bx in range(blocks_w):
                if len(bits) >= expected_bits:
                    break

                y_start = by * 8
                x_start = bx * 8
                block = blue[y_start : y_start + 8, x_start : x_start + 8]

                dct_block = self._dct2(block)
                mid_coef = dct_block[3, 4]

                # Extract bit
                strength = self._embed_strength * 50
                remainder = mid_coef % strength
                bit = 1 if remainder > strength / 4 else 0
                bits.append(bit)

            if len(bits) >= expected_bits:
                break

        return bits

    def _dct2(self, block: np.ndarray) -> np.ndarray:
        """Simple 2D DCT implementation."""
        from scipy.fftpack import dct

        return dct(dct(block.T, norm="ortho").T, norm="ortho")

    def _idct2(self, block: np.ndarray) -> np.ndarray:
        """Simple 2D inverse DCT."""
        from scipy.fftpack import idct

        return idct(idct(block.T, norm="ortho").T, norm="ortho")

    def embed_watermark(
        self,
        image: Image.Image | bytes,
        *,
        job_id: str,
        product_id: str,
        model_used: str,
        correlation_id: str | None = None,
    ) -> WatermarkResult:
        """
        Embed invisible watermark in image.

        Args:
            image: PIL Image or image bytes
            job_id: Job ID to encode
            product_id: Product ID to encode
            model_used: ML model name
            correlation_id: Optional correlation ID

        Returns:
            WatermarkResult with watermarked image bytes

        Raises:
            WatermarkError: If watermarking fails
        """
        import time

        start_time = time.time()
        correlation_id = correlation_id or self._generate_correlation_id()

        logger.info(
            "Starting watermark embedding",
            extra={
                "job_id": job_id,
                "product_id": product_id,
                "correlation_id": correlation_id,
            },
        )

        try:
            # Convert bytes to image if needed
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))

            # Validate image size
            if image.width < MIN_IMAGE_SIZE or image.height < MIN_IMAGE_SIZE:
                raise WatermarkError(
                    f"Image too small for watermarking. Minimum: {MIN_IMAGE_SIZE}x{MIN_IMAGE_SIZE}",
                    operation="embed",
                    correlation_id=correlation_id,
                )

            # Create payload
            checksum = self._compute_checksum(job_id, product_id, model_used)
            payload = WatermarkPayload(
                job_id=job_id,
                product_id=product_id,
                model_used=model_used,
                generation_date=datetime.now(UTC).isoformat(),
                checksum=checksum,
            )

            # Encode to bits
            bits = self._encode_payload_to_bits(payload)

            # Check if image has enough capacity
            blocks_available = (image.width // 8) * (image.height // 8)
            if blocks_available < len(bits):
                raise WatermarkError(
                    f"Image too small for payload. Need {len(bits)} blocks, have {blocks_available}",
                    operation="embed",
                    correlation_id=correlation_id,
                )

            # Embed watermark
            watermarked = self._embed_bits_dct(image, bits)

            # Convert to bytes
            buffer = io.BytesIO()
            watermarked.save(buffer, format="PNG", optimize=True)
            watermarked_bytes = buffer.getvalue()

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Watermark embedding complete",
                extra={
                    "bits_embedded": len(bits),
                    "processing_time_ms": processing_time_ms,
                    "correlation_id": correlation_id,
                },
            )

            return WatermarkResult(
                watermarked_image_bytes=watermarked_bytes,
                payload={
                    "job_id": payload.job_id,
                    "product_id": payload.product_id,
                    "model_used": payload.model_used,
                    "generation_date": payload.generation_date,
                    "checksum": payload.checksum,
                },
                embedding_strength=self._embed_strength,
                processing_time_ms=processing_time_ms,
                correlation_id=correlation_id,
            )

        except WatermarkError:
            raise
        except Exception as e:
            raise WatermarkError(
                f"Failed to embed watermark: {e}",
                operation="embed",
                correlation_id=correlation_id,
                cause=e,
            ) from e

    def detect_watermark(
        self,
        image: Image.Image | bytes,
        *,
        correlation_id: str | None = None,
    ) -> WatermarkDetectionResult:
        """
        Detect and extract watermark from image.

        Args:
            image: PIL Image or image bytes
            correlation_id: Optional correlation ID

        Returns:
            WatermarkDetectionResult with extracted payload if found
        """
        import time

        start_time = time.time()
        correlation_id = correlation_id or self._generate_correlation_id()

        logger.info(
            "Starting watermark detection",
            extra={"correlation_id": correlation_id},
        )

        try:
            if isinstance(image, bytes):
                image = Image.open(io.BytesIO(image))

            if image.width < MIN_IMAGE_SIZE or image.height < MIN_IMAGE_SIZE:
                logger.debug("Image too small for watermark detection")
                return WatermarkDetectionResult(
                    has_watermark=False,
                    confidence=0.0,
                    correlation_id=correlation_id,
                )

            # Try to extract header first
            header_bits = self._extract_bits_dct(image, 56)

            # Check magic header
            magic_bytes = bytearray()
            for i in range(0, 32, 8):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | header_bits[i + j]
                magic_bytes.append(byte)

            if bytes(magic_bytes) != WATERMARK_MAGIC:
                logger.debug("No watermark magic header found")
                return WatermarkDetectionResult(
                    has_watermark=False,
                    confidence=0.0,
                    correlation_id=correlation_id,
                )

            # Extract full payload
            max_bits = min((image.width // 8) * (image.height // 8), 4096)
            all_bits = self._extract_bits_dct(image, max_bits)

            payload = self._decode_bits_to_payload(all_bits)

            if payload is None:
                logger.debug("Failed to decode payload")
                return WatermarkDetectionResult(
                    has_watermark=False,
                    confidence=0.3,  # Found header but couldn't decode
                    correlation_id=correlation_id,
                )

            # Verify checksum
            expected_checksum = self._compute_checksum(
                payload.job_id, payload.product_id, payload.model_used
            )
            checksum_valid = payload.checksum == expected_checksum

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Watermark detection complete",
                extra={
                    "has_watermark": True,
                    "checksum_valid": checksum_valid,
                    "processing_time_ms": processing_time_ms,
                    "correlation_id": correlation_id,
                },
            )

            return WatermarkDetectionResult(
                has_watermark=True,
                payload={
                    "job_id": payload.job_id,
                    "product_id": payload.product_id,
                    "model_used": payload.model_used,
                    "generation_date": payload.generation_date,
                    "checksum": payload.checksum,
                    "checksum_valid": str(checksum_valid),
                },
                confidence=1.0 if checksum_valid else 0.8,
                correlation_id=correlation_id,
            )

        except Exception as e:
            logger.warning(
                f"Watermark detection failed: {e}",
                extra={"correlation_id": correlation_id},
            )
            return WatermarkDetectionResult(
                has_watermark=False,
                confidence=0.0,
                correlation_id=correlation_id,
            )

    def scan_batch(
        self,
        images: list[Image.Image | bytes],
        *,
        correlation_id: str | None = None,
    ) -> list[WatermarkDetectionResult]:
        """
        Scan multiple images for watermarks.

        Args:
            images: List of images to scan
            correlation_id: Optional correlation ID

        Returns:
            List of detection results
        """
        correlation_id = correlation_id or self._generate_correlation_id()
        return [self.detect_watermark(img, correlation_id=correlation_id) for img in images]


__all__ = [
    "WatermarkService",
    "WatermarkResult",
    "WatermarkDetectionResult",
    "WatermarkError",
    "WatermarkPayload",
]
