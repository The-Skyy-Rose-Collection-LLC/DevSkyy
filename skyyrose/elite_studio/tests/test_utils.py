"""Tests for shared utilities — pure functions with no side effects."""

import base64
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from skyyrose.elite_studio.models import ProductData
from skyyrose.elite_studio import utils


class TestLoadProductData:
    def test_loads_existing_override(self, tmp_path):
        override_data = {
            "collection": "black-rose",
            "garmentTypeLock": "crewneck",
            "brandingTech": {"technique": "embroidered"},
            "referenceImages": ["black-rose/br-001-front.png"],
        }
        override_file = tmp_path / "br-001.json"
        override_file.write_text(json.dumps(override_data))

        with patch.object(utils, "OVERRIDES_DIR", tmp_path):
            result = utils.load_product_data("br-001")

        assert isinstance(result, ProductData)
        assert result.sku == "br-001"
        assert result.collection == "black-rose"
        assert result.garment_type_lock == "crewneck"
        assert result.reference_images == ("black-rose/br-001-front.png",)

    def test_missing_override_returns_unknown(self, tmp_path):
        with patch.object(utils, "OVERRIDES_DIR", tmp_path):
            result = utils.load_product_data("nonexistent-999")

        assert result.sku == "nonexistent-999"
        assert result.collection == "unknown"

    def test_strips_and_lowercases_sku(self, tmp_path):
        with patch.object(utils, "OVERRIDES_DIR", tmp_path):
            result = utils.load_product_data("  BR-001  ")

        assert result.sku == "br-001"


class TestGetReferenceImagePath:
    def test_exact_match(self, tmp_path):
        col_dir = tmp_path / "black-rose"
        col_dir.mkdir()
        exact = col_dir / "br-001-front.jpg"
        exact.write_bytes(b"\xff\xd8")  # JPEG magic bytes

        product = ProductData(sku="br-001", collection="black-rose")
        with patch.object(utils, "SOURCE_DIR", tmp_path):
            with patch.object(utils, "load_product_data", return_value=product):
                result = utils.get_reference_image_path("br-001", "front")

        assert result == str(exact)

    def test_glob_descriptive_name(self, tmp_path):
        col_dir = tmp_path / "black-rose"
        col_dir.mkdir()
        descriptive = col_dir / "br-001-crewneck-front.png"
        descriptive.write_bytes(b"\x89PNG")

        product = ProductData(sku="br-001", collection="black-rose")
        with patch.object(utils, "SOURCE_DIR", tmp_path):
            with patch.object(utils, "load_product_data", return_value=product):
                result = utils.get_reference_image_path("br-001", "front")

        assert result == str(descriptive)

    def test_front_fallback_excludes_back(self, tmp_path):
        col_dir = tmp_path / "black-rose"
        col_dir.mkdir()
        # Only a "detail" image (no explicit "front")
        detail = col_dir / "br-001-detail.jpg"
        detail.write_bytes(b"\xff\xd8")
        # A "back" image that should be excluded
        back = col_dir / "br-001-back.jpg"
        back.write_bytes(b"\xff\xd8")

        product = ProductData(sku="br-001", collection="black-rose")
        with patch.object(utils, "SOURCE_DIR", tmp_path):
            with patch.object(utils, "load_product_data", return_value=product):
                result = utils.get_reference_image_path("br-001", "front")

        # Check filename only — tmp_path dirs can contain "back" as substring
        from pathlib import Path
        filename = Path(result).name
        assert "detail" in filename
        assert "back" not in filename

    def test_override_reference_images(self, tmp_path):
        col_dir = tmp_path / "black-rose"
        col_dir.mkdir()
        ref_img = col_dir / "custom-ref.jpg"
        ref_img.write_bytes(b"\xff\xd8")

        product = ProductData(
            sku="br-001",
            collection="black-rose",
            reference_images=("black-rose/custom-ref.jpg",),
        )
        with patch.object(utils, "SOURCE_DIR", tmp_path):
            with patch.object(utils, "load_product_data", return_value=product):
                result = utils.get_reference_image_path("br-001", "side")

        assert result == str(ref_img)

    def test_no_image_found(self, tmp_path):
        product = ProductData(sku="br-999", collection="nonexistent")
        with patch.object(utils, "SOURCE_DIR", tmp_path):
            with patch.object(utils, "load_product_data", return_value=product):
                result = utils.get_reference_image_path("br-999", "front")

        assert result == ""


class TestImageToBase64:
    def test_encodes_file(self, tmp_path):
        img_file = tmp_path / "test.jpg"
        img_file.write_bytes(b"FAKE_IMAGE_DATA")

        result = utils.image_to_base64(str(img_file))
        decoded = base64.b64decode(result)
        assert decoded == b"FAKE_IMAGE_DATA"


class TestResizeForClaude:
    def test_small_rgb_image(self, tmp_path):
        """Small RGB image should be returned as JPEG base64 without resizing."""
        from PIL import Image

        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        path = tmp_path / "small.png"
        img.save(str(path))

        result = utils.resize_for_claude(str(path))
        decoded = base64.b64decode(result)
        # Should be valid JPEG
        assert decoded[:2] == b"\xff\xd8"

    def test_large_image_resized(self, tmp_path):
        """Image larger than max_size should be resized."""
        from PIL import Image

        img = Image.new("RGB", (3000, 3000), color=(0, 0, 255))
        path = tmp_path / "large.png"
        img.save(str(path))

        result = utils.resize_for_claude(str(path), max_size=500)
        decoded = base64.b64decode(result)
        # Verify it's valid JPEG
        assert decoded[:2] == b"\xff\xd8"
        # Verify it was actually resized
        import io

        resized = Image.open(io.BytesIO(decoded))
        assert max(resized.size) <= 500

    def test_rgba_image_converted(self, tmp_path):
        """RGBA image should be composited onto white background."""
        from PIL import Image

        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        path = tmp_path / "transparent.png"
        img.save(str(path))

        result = utils.resize_for_claude(str(path))
        decoded = base64.b64decode(result)
        assert decoded[:2] == b"\xff\xd8"

    def test_p_mode_image_converted(self, tmp_path):
        """Palette mode image should be handled."""
        from PIL import Image

        img = Image.new("P", (100, 100))
        path = tmp_path / "palette.png"
        img.save(str(path))

        result = utils.resize_for_claude(str(path))
        decoded = base64.b64decode(result)
        assert decoded[:2] == b"\xff\xd8"


class TestDiscoverAllSkus:
    def test_discovers_json_files(self, tmp_path):
        (tmp_path / "br-001.json").write_text("{}")
        (tmp_path / "br-002.json").write_text("{}")
        (tmp_path / "sg-001.json").write_text("{}")
        (tmp_path / "not-json.txt").write_text("ignore")

        with patch.object(utils, "OVERRIDES_DIR", tmp_path):
            result = utils.discover_all_skus()

        assert result == ["br-001", "br-002", "sg-001"]

    def test_empty_directory(self, tmp_path):
        with patch.object(utils, "OVERRIDES_DIR", tmp_path):
            result = utils.discover_all_skus()

        assert result == []
