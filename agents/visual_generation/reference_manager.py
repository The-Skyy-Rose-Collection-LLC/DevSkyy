"""
Reference Image & Thought Signature Management
==============================================

Manages reference images and thought signatures for consistent character generation
and creative direction in Gemini native image generation.

Features:
- Reference image validation (up to 14 images per Gemini API limit)
- Subject references: Character consistency across generations
- Style references: Artistic style transfer
- Control references: Composition guidance
- Thought signature capture: Reusable creative direction patterns

Use Cases:
- AI model generation with consistent facial features
- Product photography with consistent styling
- Campaign visuals with unified aesthetic
- Sequential art and storyboards

Created: 2026-01-08
Status: Phase 4 - Reference Images & Advanced Features
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog
from PIL import Image

logger = structlog.get_logger(__name__)


# ============================================================================
# Constants
# ============================================================================

# Gemini API limits
MAX_REFERENCE_IMAGES = 14  # Maximum reference images per request
MIN_REFERENCE_IMAGES = 1
MAX_IMAGE_SIZE_MB = 20  # Maximum size per image
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}


# ============================================================================
# Enums
# ============================================================================


class ReferenceType(str, Enum):
    """Types of reference images for generation guidance."""

    SUBJECT = "subject"  # Character/object consistency
    STYLE = "style"  # Artistic style transfer
    CONTROL = "control"  # Composition guidance
    MASK = "mask"  # Region control


# ============================================================================
# Exceptions
# ============================================================================


class ReferenceValidationError(Exception):
    """Raised when reference image validation fails."""

    pass


class ThoughtSignatureError(Exception):
    """Raised when thought signature operations fail."""

    pass


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ReferenceImage:
    """
    Single reference image with metadata.

    Attributes:
        path: Path to image file
        type: Reference type (subject, style, control, mask)
        weight: Influence weight (0.0-1.0)
        description: Optional description of reference
        metadata: Additional metadata
    """

    path: str
    type: ReferenceType
    weight: float = 0.8
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate weight range."""
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {self.weight}")


@dataclass
class ThoughtSignature:
    """
    Reusable thought signature for consistent creative direction.

    Captures reasoning patterns from Gemini Pro's thinking mode
    for reuse across similar generation tasks.

    Attributes:
        signature_id: Unique identifier
        concept: High-level concept (e.g., "luxury streetwear editorial")
        thinking_pattern: Captured thought process
        prompt_template: Resulting prompt template
        metadata: Additional context (collection, style keywords, etc.)
        created_at: Creation timestamp
        usage_count: Number of times signature has been used
    """

    signature_id: str
    concept: str
    thinking_pattern: str
    prompt_template: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    usage_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "signature_id": self.signature_id,
            "concept": self.concept,
            "thinking_pattern": self.thinking_pattern,
            "prompt_template": self.prompt_template,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ThoughtSignature:
        """Create from dictionary."""
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


# ============================================================================
# Reference Image Manager
# ============================================================================


class ReferenceImageManager:
    """
    Manages reference images for character consistency and style transfer.

    Validates reference images against Gemini API limits and provides
    utilities for creating reference configurations.
    """

    @staticmethod
    def validate_references(images: list[str]) -> tuple[bool, str]:
        """
        Validate reference images against Gemini API constraints.

        Args:
            images: List of image file paths

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string
        """
        # Check count
        if len(images) < MIN_REFERENCE_IMAGES:
            return False, f"At least {MIN_REFERENCE_IMAGES} reference image required"

        if len(images) > MAX_REFERENCE_IMAGES:
            return False, f"Maximum {MAX_REFERENCE_IMAGES} reference images allowed, got {len(images)}"

        # Validate each image
        for i, image_path in enumerate(images):
            path = Path(image_path)

            # Check file exists
            if not path.exists():
                return False, f"Image {i + 1} not found: {image_path}"

            # Check format
            if path.suffix.lower() not in SUPPORTED_FORMATS:
                return False, f"Image {i + 1} has unsupported format: {path.suffix}"

            # Check size
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > MAX_IMAGE_SIZE_MB:
                return False, f"Image {i + 1} exceeds {MAX_IMAGE_SIZE_MB}MB: {size_mb:.1f}MB"

            # Validate can be opened
            try:
                with Image.open(image_path) as img:
                    img.verify()
            except Exception as e:
                return False, f"Image {i + 1} is corrupted or invalid: {str(e)}"

        return True, ""

    @staticmethod
    def create_subject_references(
        images: list[str],
        consistency_weight: float = 0.8,
        descriptions: list[str] | None = None,
    ) -> list[ReferenceImage]:
        """
        Create subject references for character consistency.

        Use this for AI model generation where you want consistent
        facial features, body proportions, or object characteristics
        across multiple images.

        Args:
            images: List of reference image paths
            consistency_weight: How strongly to maintain consistency (0.0-1.0)
            descriptions: Optional descriptions for each image

        Returns:
            List of ReferenceImage objects configured for subject consistency

        Raises:
            ReferenceValidationError: If validation fails
        """
        # Validate
        is_valid, error = ReferenceImageManager.validate_references(images)
        if not is_valid:
            raise ReferenceValidationError(error)

        # Create references
        references = []
        for i, image_path in enumerate(images):
            description = descriptions[i] if descriptions and i < len(descriptions) else None
            ref = ReferenceImage(
                path=image_path,
                type=ReferenceType.SUBJECT,
                weight=consistency_weight,
                description=description,
                metadata={"index": i, "purpose": "character_consistency"},
            )
            references.append(ref)

        logger.info(
            "subject_references_created",
            count=len(references),
            consistency_weight=consistency_weight,
        )

        return references

    @staticmethod
    def create_style_references(
        images: list[str],
        style_strength: float = 0.7,
        style_description: str | None = None,
    ) -> list[ReferenceImage]:
        """
        Create style references for artistic style transfer.

        Use this to apply a specific artistic style (photography style,
        illustration style, etc.) to generated images.

        Args:
            images: List of reference image paths showing desired style
            style_strength: How strongly to apply style (0.0-1.0)
            style_description: Optional description of the style

        Returns:
            List of ReferenceImage objects configured for style transfer

        Raises:
            ReferenceValidationError: If validation fails
        """
        # Validate
        is_valid, error = ReferenceImageManager.validate_references(images)
        if not is_valid:
            raise ReferenceValidationError(error)

        # Create references
        references = []
        for i, image_path in enumerate(images):
            ref = ReferenceImage(
                path=image_path,
                type=ReferenceType.STYLE,
                weight=style_strength,
                description=style_description,
                metadata={"index": i, "purpose": "style_transfer"},
            )
            references.append(ref)

        logger.info(
            "style_references_created",
            count=len(references),
            style_strength=style_strength,
        )

        return references

    @staticmethod
    def create_control_references(
        images: list[str],
        control_strength: float = 0.6,
    ) -> list[ReferenceImage]:
        """
        Create control references for composition guidance.

        Use this to guide the composition, layout, or structure
        of generated images without affecting style or subject.

        Args:
            images: List of reference image paths for composition
            control_strength: How strongly to follow composition (0.0-1.0)

        Returns:
            List of ReferenceImage objects configured for composition control

        Raises:
            ReferenceValidationError: If validation fails
        """
        # Validate
        is_valid, error = ReferenceImageManager.validate_references(images)
        if not is_valid:
            raise ReferenceValidationError(error)

        # Create references
        references = []
        for i, image_path in enumerate(images):
            ref = ReferenceImage(
                path=image_path,
                type=ReferenceType.CONTROL,
                weight=control_strength,
                description=None,
                metadata={"index": i, "purpose": "composition_guidance"},
            )
            references.append(ref)

        logger.info(
            "control_references_created",
            count=len(references),
            control_strength=control_strength,
        )

        return references

    @staticmethod
    def combine_references(
        subject_refs: list[ReferenceImage] | None = None,
        style_refs: list[ReferenceImage] | None = None,
        control_refs: list[ReferenceImage] | None = None,
    ) -> list[ReferenceImage]:
        """
        Combine multiple reference types into single list.

        Validates total count against Gemini API limits.

        Args:
            subject_refs: Subject/character references
            style_refs: Style transfer references
            control_refs: Composition control references

        Returns:
            Combined list of references

        Raises:
            ReferenceValidationError: If total exceeds MAX_REFERENCE_IMAGES
        """
        combined = []
        if subject_refs:
            combined.extend(subject_refs)
        if style_refs:
            combined.extend(style_refs)
        if control_refs:
            combined.extend(control_refs)

        if len(combined) > MAX_REFERENCE_IMAGES:
            raise ReferenceValidationError(
                f"Total references exceed limit: {len(combined)} > {MAX_REFERENCE_IMAGES}"
            )

        return combined


# ============================================================================
# Thought Signature Manager
# ============================================================================


class ThoughtSignatureManager:
    """
    Manages reusable thought signatures for consistent creative direction.

    Captures reasoning patterns from Gemini Pro's thinking mode and
    allows reuse across similar generation tasks.
    """

    def __init__(self, storage_path: str | None = None):
        """
        Initialize thought signature manager.

        Args:
            storage_path: Optional path to JSON file for persistence
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self._signatures: dict[str, ThoughtSignature] = {}

        # Load existing signatures if storage path provided
        if self.storage_path and self.storage_path.exists():
            self._load_signatures()

        logger.info("thought_signature_manager_initialized", storage_path=storage_path)

    def capture_signature(
        self,
        concept: str,
        thinking_response: str,
        prompt_template: str,
        metadata: dict[str, Any] | None = None,
    ) -> ThoughtSignature:
        """
        Capture thought signature from thinking mode response.

        Args:
            concept: High-level concept (e.g., "luxury streetwear editorial")
            thinking_response: Raw thinking mode output from Gemini Pro
            prompt_template: Resulting prompt template
            metadata: Optional additional context

        Returns:
            ThoughtSignature object with unique ID
        """
        signature = ThoughtSignature(
            signature_id=str(uuid.uuid4()),
            concept=concept,
            thinking_pattern=thinking_response,
            prompt_template=prompt_template,
            metadata=metadata or {},
        )

        self._signatures[signature.signature_id] = signature

        if self.storage_path:
            self._save_signatures()

        logger.info(
            "thought_signature_captured",
            signature_id=signature.signature_id,
            concept=concept,
        )

        return signature

    def get_signature(self, signature_id: str) -> ThoughtSignature | None:
        """
        Get signature by ID.

        Args:
            signature_id: Unique signature identifier

        Returns:
            ThoughtSignature if found, None otherwise
        """
        signature = self._signatures.get(signature_id)
        if signature:
            signature.usage_count += 1
            if self.storage_path:
                self._save_signatures()
        return signature

    def search_signatures(self, concept_query: str) -> list[ThoughtSignature]:
        """
        Search signatures by concept.

        Args:
            concept_query: Search query (substring match)

        Returns:
            List of matching signatures, sorted by usage_count desc
        """
        matches = [
            sig for sig in self._signatures.values() if concept_query.lower() in sig.concept.lower()
        ]

        # Sort by usage count (most used first)
        matches.sort(key=lambda s: s.usage_count, reverse=True)

        return matches

    def list_signatures(self) -> list[ThoughtSignature]:
        """
        List all signatures.

        Returns:
            List of all signatures, sorted by usage_count desc
        """
        signatures = list(self._signatures.values())
        signatures.sort(key=lambda s: s.usage_count, reverse=True)
        return signatures

    def delete_signature(self, signature_id: str) -> bool:
        """
        Delete signature by ID.

        Args:
            signature_id: Unique signature identifier

        Returns:
            True if deleted, False if not found
        """
        if signature_id in self._signatures:
            del self._signatures[signature_id]
            if self.storage_path:
                self._save_signatures()
            logger.info("thought_signature_deleted", signature_id=signature_id)
            return True
        return False

    def _save_signatures(self) -> None:
        """Save signatures to storage file."""
        if not self.storage_path:
            return

        data = {sig_id: sig.to_dict() for sig_id, sig in self._signatures.items()}

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_signatures(self) -> None:
        """Load signatures from storage file."""
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            with open(self.storage_path) as f:
                data = json.load(f)

            self._signatures = {
                sig_id: ThoughtSignature.from_dict(sig_data) for sig_id, sig_data in data.items()
            }

            logger.info("thought_signatures_loaded", count=len(self._signatures))
        except Exception as e:
            logger.error("thought_signatures_load_failed", error=str(e))


# Export
__all__ = [
    "ReferenceType",
    "ReferenceImage",
    "ReferenceImageManager",
    "ThoughtSignature",
    "ThoughtSignatureManager",
    "ReferenceValidationError",
    "ThoughtSignatureError",
    "MAX_REFERENCE_IMAGES",
]
