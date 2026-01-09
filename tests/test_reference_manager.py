"""
Comprehensive tests for Reference Manager module.

Tests cover:
- ReferenceImage validation (weight range)
- ReferenceImageManager validation (count, format, size, corruption)
- Subject/style/control reference creation
- Reference combination and limits
- ThoughtSignature serialization
- ThoughtSignatureManager capture, search, retrieval, deletion
- ThoughtSignatureManager persistence (JSON save/load)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from agents.visual_generation.reference_manager import (
    MAX_REFERENCE_IMAGES,
    ReferenceImage,
    ReferenceImageManager,
    ReferenceType,
    ReferenceValidationError,
    ThoughtSignature,
    ThoughtSignatureManager,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_image_files(tmp_path: Path) -> list[str]:
    """Create temporary valid image files for testing."""
    image_paths = []
    for i in range(5):
        img_path = tmp_path / f"test_image_{i}.jpg"
        # Create 100x100 RGB image
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(img_path)
        image_paths.append(str(img_path))
    return image_paths


@pytest.fixture
def temp_png_files(tmp_path: Path) -> list[str]:
    """Create temporary PNG files for testing."""
    image_paths = []
    for i in range(3):
        img_path = tmp_path / f"test_image_{i}.png"
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        img.save(img_path)
        image_paths.append(str(img_path))
    return image_paths


@pytest.fixture
def temp_storage_file(tmp_path: Path) -> str:
    """Create temporary storage file for ThoughtSignatureManager."""
    return str(tmp_path / "signatures.json")


# =============================================================================
# ReferenceImage Tests
# =============================================================================


def test_reference_image_valid_weight():
    """Test ReferenceImage accepts valid weight range."""
    ref = ReferenceImage(path="test.jpg", type=ReferenceType.SUBJECT, weight=0.5)
    assert ref.weight == 0.5


def test_reference_image_weight_too_low_raises_error():
    """Test ReferenceImage raises error for weight < 0.0."""
    with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
        ReferenceImage(path="test.jpg", type=ReferenceType.SUBJECT, weight=-0.1)


def test_reference_image_weight_too_high_raises_error():
    """Test ReferenceImage raises error for weight > 1.0."""
    with pytest.raises(ValueError, match="Weight must be between 0.0 and 1.0"):
        ReferenceImage(path="test.jpg", type=ReferenceType.SUBJECT, weight=1.5)


def test_reference_image_edge_weights():
    """Test ReferenceImage accepts edge case weights (0.0, 1.0)."""
    ref_min = ReferenceImage(path="test.jpg", type=ReferenceType.SUBJECT, weight=0.0)
    ref_max = ReferenceImage(path="test.jpg", type=ReferenceType.SUBJECT, weight=1.0)
    assert ref_min.weight == 0.0
    assert ref_max.weight == 1.0


def test_reference_image_default_weight():
    """Test ReferenceImage uses default weight of 0.8."""
    ref = ReferenceImage(path="test.jpg", type=ReferenceType.SUBJECT)
    assert ref.weight == 0.8


def test_reference_image_metadata():
    """Test ReferenceImage stores metadata."""
    ref = ReferenceImage(
        path="test.jpg",
        type=ReferenceType.STYLE,
        metadata={"artist": "Van Gogh", "era": "impressionism"},
    )
    assert ref.metadata["artist"] == "Van Gogh"
    assert ref.metadata["era"] == "impressionism"


# =============================================================================
# ReferenceImageManager.validate_references() Tests
# =============================================================================


def test_validate_references_empty_list():
    """Test validation fails with empty list."""
    is_valid, error = ReferenceImageManager.validate_references([])
    assert is_valid is False
    assert "At least 1 reference image required" in error


def test_validate_references_too_many():
    """Test validation fails with more than MAX_REFERENCE_IMAGES."""
    images = [f"test_{i}.jpg" for i in range(MAX_REFERENCE_IMAGES + 1)]
    is_valid, error = ReferenceImageManager.validate_references(images)
    assert is_valid is False
    assert f"Maximum {MAX_REFERENCE_IMAGES} reference images allowed" in error


def test_validate_references_file_not_found():
    """Test validation fails when file doesn't exist."""
    is_valid, error = ReferenceImageManager.validate_references(["nonexistent.jpg"])
    assert is_valid is False
    assert "not found" in error


def test_validate_references_unsupported_format(tmp_path: Path):
    """Test validation fails with unsupported format."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not an image")
    is_valid, error = ReferenceImageManager.validate_references([str(txt_file)])
    assert is_valid is False
    assert "unsupported format" in error


def test_validate_references_file_too_large(tmp_path: Path):
    """Test validation fails when file exceeds size limit."""
    # Create image that's too large (simulate with stat mock)
    img_path = tmp_path / "large.jpg"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(img_path)

    # Mock stat to return size > 20MB
    with patch.object(Path, "stat") as mock_stat:
        mock_stat.return_value.st_size = 21 * 1024 * 1024  # 21MB
        is_valid, error = ReferenceImageManager.validate_references([str(img_path)])
        assert is_valid is False
        assert "exceeds 20MB" in error


def test_validate_references_corrupted_image(tmp_path: Path):
    """Test validation fails with corrupted image."""
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"not a valid jpeg")
    is_valid, error = ReferenceImageManager.validate_references([str(corrupt_file)])
    assert is_valid is False
    assert "corrupted or invalid" in error


def test_validate_references_success(temp_image_files: list[str]):
    """Test validation succeeds with valid images."""
    is_valid, error = ReferenceImageManager.validate_references(temp_image_files[:3])
    assert is_valid is True
    assert error == ""


def test_validate_references_max_allowed(temp_image_files: list[str], tmp_path: Path):
    """Test validation succeeds with exactly MAX_REFERENCE_IMAGES."""
    # Create exactly MAX_REFERENCE_IMAGES images
    images = []
    for i in range(MAX_REFERENCE_IMAGES):
        img_path = tmp_path / f"test_{i}.jpg"
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(img_path)
        images.append(str(img_path))

    is_valid, error = ReferenceImageManager.validate_references(images)
    assert is_valid is True
    assert error == ""


# =============================================================================
# ReferenceImageManager.create_subject_references() Tests
# =============================================================================


def test_create_subject_references_basic(temp_image_files: list[str]):
    """Test creating subject references with default parameters."""
    refs = ReferenceImageManager.create_subject_references(temp_image_files[:2])
    assert len(refs) == 2
    assert all(ref.type == ReferenceType.SUBJECT for ref in refs)
    assert all(ref.weight == 0.8 for ref in refs)
    assert all(ref.metadata["purpose"] == "character_consistency" for ref in refs)


def test_create_subject_references_custom_weight(temp_image_files: list[str]):
    """Test creating subject references with custom consistency weight."""
    refs = ReferenceImageManager.create_subject_references(
        temp_image_files[:2], consistency_weight=0.9
    )
    assert all(ref.weight == 0.9 for ref in refs)


def test_create_subject_references_with_descriptions(temp_image_files: list[str]):
    """Test creating subject references with descriptions."""
    descriptions = ["Front view", "Side view", "Back view"]
    refs = ReferenceImageManager.create_subject_references(
        temp_image_files[:3], descriptions=descriptions
    )
    assert refs[0].description == "Front view"
    assert refs[1].description == "Side view"
    assert refs[2].description == "Back view"


def test_create_subject_references_fewer_descriptions(temp_image_files: list[str]):
    """Test creating subject references with fewer descriptions than images."""
    descriptions = ["Front view"]
    refs = ReferenceImageManager.create_subject_references(
        temp_image_files[:3], descriptions=descriptions
    )
    assert refs[0].description == "Front view"
    assert refs[1].description is None
    assert refs[2].description is None


def test_create_subject_references_validation_failure():
    """Test creating subject references fails validation."""
    with pytest.raises(ReferenceValidationError, match="not found"):
        ReferenceImageManager.create_subject_references(["nonexistent.jpg"])


def test_create_subject_references_metadata(temp_image_files: list[str]):
    """Test subject references have correct metadata."""
    refs = ReferenceImageManager.create_subject_references(temp_image_files[:3])
    for i, ref in enumerate(refs):
        assert ref.metadata["index"] == i
        assert ref.metadata["purpose"] == "character_consistency"


# =============================================================================
# ReferenceImageManager.create_style_references() Tests
# =============================================================================


def test_create_style_references_basic(temp_image_files: list[str]):
    """Test creating style references with default parameters."""
    refs = ReferenceImageManager.create_style_references(temp_image_files[:2])
    assert len(refs) == 2
    assert all(ref.type == ReferenceType.STYLE for ref in refs)
    assert all(ref.weight == 0.7 for ref in refs)
    assert all(ref.metadata["purpose"] == "style_transfer" for ref in refs)


def test_create_style_references_custom_strength(temp_image_files: list[str]):
    """Test creating style references with custom style strength."""
    refs = ReferenceImageManager.create_style_references(temp_image_files[:2], style_strength=0.85)
    assert all(ref.weight == 0.85 for ref in refs)


def test_create_style_references_with_description(temp_image_files: list[str]):
    """Test creating style references with style description."""
    refs = ReferenceImageManager.create_style_references(
        temp_image_files[:2], style_description="Art Nouveau, flowing lines"
    )
    assert all(ref.description == "Art Nouveau, flowing lines" for ref in refs)


def test_create_style_references_validation_failure():
    """Test creating style references fails validation."""
    with pytest.raises(ReferenceValidationError):
        ReferenceImageManager.create_style_references([])


# =============================================================================
# ReferenceImageManager.create_control_references() Tests
# =============================================================================


def test_create_control_references_basic(temp_image_files: list[str]):
    """Test creating control references with default parameters."""
    refs = ReferenceImageManager.create_control_references(temp_image_files[:2])
    assert len(refs) == 2
    assert all(ref.type == ReferenceType.CONTROL for ref in refs)
    assert all(ref.weight == 0.6 for ref in refs)
    assert all(ref.metadata["purpose"] == "composition_guidance" for ref in refs)


def test_create_control_references_custom_strength(temp_image_files: list[str]):
    """Test creating control references with custom control strength."""
    refs = ReferenceImageManager.create_control_references(
        temp_image_files[:2], control_strength=0.75
    )
    assert all(ref.weight == 0.75 for ref in refs)


def test_create_control_references_no_description(temp_image_files: list[str]):
    """Test control references have no description by default."""
    refs = ReferenceImageManager.create_control_references(temp_image_files[:2])
    assert all(ref.description is None for ref in refs)


# =============================================================================
# ReferenceImageManager.combine_references() Tests
# =============================================================================


def test_combine_references_all_types(temp_image_files: list[str]):
    """Test combining all reference types."""
    subject_refs = ReferenceImageManager.create_subject_references([temp_image_files[0]])
    style_refs = ReferenceImageManager.create_style_references([temp_image_files[1]])
    control_refs = ReferenceImageManager.create_control_references([temp_image_files[2]])

    combined = ReferenceImageManager.combine_references(
        subject_refs=subject_refs, style_refs=style_refs, control_refs=control_refs
    )

    assert len(combined) == 3
    assert combined[0].type == ReferenceType.SUBJECT
    assert combined[1].type == ReferenceType.STYLE
    assert combined[2].type == ReferenceType.CONTROL


def test_combine_references_partial(temp_image_files: list[str]):
    """Test combining only some reference types."""
    subject_refs = ReferenceImageManager.create_subject_references(temp_image_files[:2])
    control_refs = ReferenceImageManager.create_control_references([temp_image_files[2]])

    combined = ReferenceImageManager.combine_references(
        subject_refs=subject_refs, control_refs=control_refs
    )

    assert len(combined) == 3
    assert sum(1 for ref in combined if ref.type == ReferenceType.SUBJECT) == 2
    assert sum(1 for ref in combined if ref.type == ReferenceType.CONTROL) == 1


def test_combine_references_exceeds_limit(temp_image_files: list[str], tmp_path: Path):
    """Test combining references exceeds MAX_REFERENCE_IMAGES."""
    # Create MAX_REFERENCE_IMAGES + 1 references
    all_images = []
    for i in range(MAX_REFERENCE_IMAGES + 1):
        img_path = tmp_path / f"extra_{i}.jpg"
        img = Image.new("RGB", (100, 100))
        img.save(img_path)
        all_images.append(str(img_path))

    subject_refs = ReferenceImageManager.create_subject_references(all_images[:10])
    style_refs = ReferenceImageManager.create_style_references(all_images[10:15])

    with pytest.raises(ReferenceValidationError, match="Total references exceed limit"):
        ReferenceImageManager.combine_references(subject_refs=subject_refs, style_refs=style_refs)


def test_combine_references_empty():
    """Test combining with no references returns empty list."""
    combined = ReferenceImageManager.combine_references()
    assert combined == []


def test_combine_references_exact_limit(tmp_path: Path):
    """Test combining exactly MAX_REFERENCE_IMAGES references."""
    images = []
    for i in range(MAX_REFERENCE_IMAGES):
        img_path = tmp_path / f"test_{i}.jpg"
        img = Image.new("RGB", (100, 100))
        img.save(img_path)
        images.append(str(img_path))

    refs = ReferenceImageManager.create_subject_references(images)
    combined = ReferenceImageManager.combine_references(subject_refs=refs)
    assert len(combined) == MAX_REFERENCE_IMAGES


# =============================================================================
# ThoughtSignature Tests
# =============================================================================


def test_thought_signature_to_dict():
    """Test ThoughtSignature.to_dict() serialization."""
    sig = ThoughtSignature(
        signature_id="test-123",
        concept="luxury streetwear",
        thinking_pattern="Focus on premium materials...",
        prompt_template="A luxury {item} with...",
        metadata={"collection": "SIGNATURE"},
        usage_count=5,
    )

    data = sig.to_dict()
    assert data["signature_id"] == "test-123"
    assert data["concept"] == "luxury streetwear"
    assert data["usage_count"] == 5
    assert "created_at" in data
    assert isinstance(data["created_at"], str)  # ISO format


def test_thought_signature_from_dict():
    """Test ThoughtSignature.from_dict() deserialization."""
    data = {
        "signature_id": "test-456",
        "concept": "gothic elegance",
        "thinking_pattern": "Dark romantic...",
        "prompt_template": "Gothic {item}...",
        "metadata": {"collection": "BLACK_ROSE"},
        "created_at": "2024-01-01T12:00:00+00:00",
        "usage_count": 10,
    }

    sig = ThoughtSignature.from_dict(data)
    assert sig.signature_id == "test-456"
    assert sig.concept == "gothic elegance"
    assert sig.usage_count == 10
    assert isinstance(sig.created_at, datetime)


def test_thought_signature_roundtrip():
    """Test ThoughtSignature to_dict() → from_dict() roundtrip."""
    original = ThoughtSignature(
        signature_id="roundtrip-test",
        concept="test concept",
        thinking_pattern="test pattern",
        prompt_template="test template",
    )

    data = original.to_dict()
    restored = ThoughtSignature.from_dict(data)

    assert restored.signature_id == original.signature_id
    assert restored.concept == original.concept
    assert restored.thinking_pattern == original.thinking_pattern
    assert restored.prompt_template == original.prompt_template


# =============================================================================
# ThoughtSignatureManager Tests
# =============================================================================


def test_thought_signature_manager_initialization():
    """Test ThoughtSignatureManager initializes with empty signatures."""
    manager = ThoughtSignatureManager()
    assert len(manager.list_signatures()) == 0


def test_thought_signature_manager_initialization_with_storage(temp_storage_file: str):
    """Test ThoughtSignatureManager initializes with storage path."""
    manager = ThoughtSignatureManager(storage_path=temp_storage_file)
    assert manager.storage_path == Path(temp_storage_file)


def test_capture_signature_basic():
    """Test capturing a thought signature."""
    manager = ThoughtSignatureManager()
    sig = manager.capture_signature(
        concept="luxury editorial",
        thinking_response="Consider premium materials, sophisticated lighting...",
        prompt_template="Luxury {product} editorial photograph...",
    )

    assert sig.concept == "luxury editorial"
    assert sig.usage_count == 0
    assert len(sig.signature_id) == 36  # UUID format


def test_capture_signature_with_metadata():
    """Test capturing signature with metadata."""
    manager = ThoughtSignatureManager()
    sig = manager.capture_signature(
        concept="gothic romance",
        thinking_response="Dark, mysterious...",
        prompt_template="Gothic {item}...",
        metadata={"collection": "BLACK_ROSE", "style": "dramatic"},
    )

    assert sig.metadata["collection"] == "BLACK_ROSE"
    assert sig.metadata["style"] == "dramatic"


def test_get_signature_increments_usage_count():
    """Test getting signature increments usage count."""
    manager = ThoughtSignatureManager()
    sig = manager.capture_signature(
        concept="test", thinking_response="test", prompt_template="test"
    )

    assert sig.usage_count == 0
    retrieved = manager.get_signature(sig.signature_id)
    assert retrieved.usage_count == 1

    # Get again
    retrieved2 = manager.get_signature(sig.signature_id)
    assert retrieved2.usage_count == 2


def test_get_signature_not_found():
    """Test getting nonexistent signature returns None."""
    manager = ThoughtSignatureManager()
    result = manager.get_signature("nonexistent-id")
    assert result is None


def test_search_signatures_substring_match():
    """Test searching signatures by concept substring."""
    manager = ThoughtSignatureManager()
    manager.capture_signature("luxury streetwear", "...", "...")
    manager.capture_signature("luxury editorial", "...", "...")
    manager.capture_signature("gothic elegance", "...", "...")

    results = manager.search_signatures("luxury")
    assert len(results) == 2
    assert all("luxury" in sig.concept.lower() for sig in results)


def test_search_signatures_case_insensitive():
    """Test search is case insensitive."""
    manager = ThoughtSignatureManager()
    manager.capture_signature("LUXURY Concept", "...", "...")

    results = manager.search_signatures("luxury")
    assert len(results) == 1


def test_search_signatures_sorted_by_usage():
    """Test search results sorted by usage count descending."""
    manager = ThoughtSignatureManager()
    sig1 = manager.capture_signature("concept A", "...", "...")
    sig2 = manager.capture_signature("concept B", "...", "...")
    sig3 = manager.capture_signature("concept C", "...", "...")

    # Increment usage counts
    manager.get_signature(sig2.signature_id)  # sig2 usage = 1
    manager.get_signature(sig2.signature_id)  # sig2 usage = 2
    manager.get_signature(sig3.signature_id)  # sig3 usage = 1

    results = manager.search_signatures("concept")
    assert len(results) == 3
    assert results[0].signature_id == sig2.signature_id  # Highest usage
    assert results[1].signature_id == sig3.signature_id
    assert results[2].signature_id == sig1.signature_id


def test_list_signatures_sorted_by_usage():
    """Test list_signatures returns all signatures sorted by usage."""
    manager = ThoughtSignatureManager()
    manager.capture_signature("concept A", "...", "...")
    sig2 = manager.capture_signature("concept B", "...", "...")

    manager.get_signature(sig2.signature_id)  # Increment sig2 usage

    all_sigs = manager.list_signatures()
    assert len(all_sigs) == 2
    assert all_sigs[0].signature_id == sig2.signature_id  # Higher usage first


def test_delete_signature_success():
    """Test deleting signature by ID."""
    manager = ThoughtSignatureManager()
    sig = manager.capture_signature("test", "...", "...")

    result = manager.delete_signature(sig.signature_id)
    assert result is True
    assert len(manager.list_signatures()) == 0


def test_delete_signature_not_found():
    """Test deleting nonexistent signature returns False."""
    manager = ThoughtSignatureManager()
    result = manager.delete_signature("nonexistent-id")
    assert result is False


def test_save_signatures_creates_file(temp_storage_file: str):
    """Test saving signatures creates JSON file."""
    manager = ThoughtSignatureManager(storage_path=temp_storage_file)
    manager.capture_signature("test", "...", "...")

    assert Path(temp_storage_file).exists()
    with open(temp_storage_file) as f:
        data = json.load(f)
    assert len(data) == 1


def test_load_signatures_restores_state(temp_storage_file: str):
    """Test loading signatures restores manager state."""
    # Create and save
    manager1 = ThoughtSignatureManager(storage_path=temp_storage_file)
    sig = manager1.capture_signature("test concept", "test pattern", "test template")
    sig_id = sig.signature_id

    # Create new manager, should load from file
    manager2 = ThoughtSignatureManager(storage_path=temp_storage_file)
    loaded_sig = manager2.get_signature(sig_id)
    assert loaded_sig is not None
    assert loaded_sig.concept == "test concept"


def test_persistence_with_usage_counts(temp_storage_file: str):
    """Test persistence maintains usage counts."""
    manager1 = ThoughtSignatureManager(storage_path=temp_storage_file)
    sig = manager1.capture_signature("test", "...", "...")
    manager1.get_signature(sig.signature_id)  # Increment to 1
    manager1.get_signature(sig.signature_id)  # Increment to 2

    # Reload
    manager2 = ThoughtSignatureManager(storage_path=temp_storage_file)
    loaded_sig = manager2.get_signature(sig.signature_id)
    # Should be 3 (2 from before + 1 from this get call)
    assert loaded_sig.usage_count == 3


def test_save_creates_parent_directory(tmp_path: Path):
    """Test save creates parent directories if they don't exist."""
    nested_path = tmp_path / "nested" / "dir" / "signatures.json"
    manager = ThoughtSignatureManager(storage_path=str(nested_path))
    manager.capture_signature("test", "...", "...")

    assert nested_path.exists()


def test_load_handles_missing_file(temp_storage_file: str):
    """Test loading with nonexistent file doesn't crash."""
    # File doesn't exist yet
    manager = ThoughtSignatureManager(storage_path=temp_storage_file)
    assert len(manager.list_signatures()) == 0


def test_load_handles_corrupted_file(temp_storage_file: str):
    """Test loading with corrupted JSON doesn't crash."""
    # Create corrupted JSON
    Path(temp_storage_file).write_text("{ invalid json")

    manager = ThoughtSignatureManager(storage_path=temp_storage_file)
    # Should initialize with empty signatures
    assert len(manager.list_signatures()) == 0
