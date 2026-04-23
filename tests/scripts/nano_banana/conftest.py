"""Shared fixtures for nano_banana tests."""

from __future__ import annotations

import csv
import json
import shutil
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

# CSV columns must match the canonical skyyrose-catalog.csv schema exactly (22 columns)
_CSV_COLUMNS = [
    "sku",
    "name",
    "price",
    "collection",
    "description",
    "badge",
    "image",
    "front_model_image",
    "back_image",
    "back_model_image",
    "sizes",
    "color",
    "edition_size",
    "published",
    "is_preorder",
    "branding_spec",
    "render_output_slug",
    "render_source_override",
    "render_back_source_override",
    "render_is_tech_flat",
    "render_is_accessory",
    "garment_type_lock",
]

_SAMPLE_ROWS = [
    {
        "sku": "br-001",
        "name": "BLACK Rose Crewneck",
        "price": "35",
        "collection": "black-rose",
        "description": "Gothic luxury blooms in twilight.",
        "badge": "",
        "image": "",
        "front_model_image": "",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Black",
        "edition_size": "250",
        "published": "1",
        "is_preorder": "0",
        "branding_spec": "",
        "render_output_slug": "black-rose-crewneck",
        "render_source_override": "black-rose-crewneck-techflat-v4.jpg",
        "render_back_source_override": "",
        "render_is_tech_flat": "1",
        "render_is_accessory": "0",
        "garment_type_lock": "crewneck",
    },
    {
        "sku": "lh-004",
        "name": "Love Hurts Bomber Jacket",
        "price": "265",
        "collection": "love-hurts",
        "description": "Oakland street couture.",
        "badge": "",
        "image": "",
        "front_model_image": "",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Black",
        "edition_size": "250",
        "published": "1",
        "is_preorder": "0",
        "branding_spec": "",
        "render_output_slug": "love-hurts-bomber",
        "render_source_override": "",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "bomber jacket",
    },
    {
        "sku": "sg-001",
        "name": "The Bridge Series 'The Bay Bridge' Shorts",
        "price": "195",
        "collection": "signature",
        "description": "Oakland golden hour on your legs.",
        "badge": "Pre-Order",
        "image": "",
        "front_model_image": "",
        "back_image": "",
        "back_model_image": "",
        "sizes": "S|M|L|XL|2XL|3XL",
        "color": "Blue",
        "edition_size": "250",
        "published": "1",
        "is_preorder": "1",
        "branding_spec": "",
        "render_output_slug": "bridge-bay-bridge-shorts",
        "render_source_override": "",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "0",
        "garment_type_lock": "shorts",
    },
    {
        "sku": "sg-007",
        "name": "The Signature Beanie",
        "price": "25",
        "collection": "signature",
        "description": "Classic fitted beanie with embroidered signature rose.",
        "badge": "",
        "image": "",
        "front_model_image": "",
        "back_image": "",
        "back_model_image": "",
        "sizes": "One Size",
        "color": "Black",
        "edition_size": "250",
        "published": "1",
        "is_preorder": "0",
        "branding_spec": "",
        "render_output_slug": "signature-beanie",
        "render_source_override": "",
        "render_back_source_override": "",
        "render_is_tech_flat": "0",
        "render_is_accessory": "1",
        "garment_type_lock": "",
    },
]


@pytest.fixture()
def sample_csv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write a 4-product CSV and patch catalog.CATALOG_CSV to point at it."""
    import nano_banana.catalog as catalog_mod

    csv_path = tmp_path / "product-catalog.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(_SAMPLE_ROWS)

    monkeypatch.setattr(catalog_mod, "CATALOG_CSV", csv_path)
    return csv_path


@pytest.fixture()
def sample_specs_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Write matching product-specs.json and patch catalog.SPECS_JSON."""
    import nano_banana.catalog as catalog_mod

    specs = {
        "products": {
            "br-001": {
                "name": "BLACK Rose Crewneck",
                "collection": "black-rose",
                "branding": "EMBOSSED rose logo on front chest",
                "fabric": "heavyweight cotton fleece",
                "texture": "embossed rose-gold metallic",
                "patch": None,
            },
            "lh-004": {
                "name": "Love Hurts Varsity Jacket",
                "collection": "love-hurts",
                "branding": "Chenille LOVE HURTS script on back",
                "fabric": "wool/leather varsity blend",
                "texture": "chenille lettering on wool body",
                "patch": "leather sleeve patches",
            },
            "sg-001": {
                "name": "The Bay Bridge Shorts",
                "collection": "signature",
                "branding": "Embroidered Bay Bridge silhouette",
                "fabric": "french terry cotton",
                "texture": "brushed interior",
                "patch": None,
            },
            "kids-001": {
                "name": "Kids Red Hoodie Set",
                "collection": "kids-capsule",
                "branding": "Small rose embroidery on chest",
                "fabric": "cotton fleece",
                "texture": "standard fleece",
                "patch": None,
            },
        }
    }
    specs_path = tmp_path / "product-specs.json"
    specs_path.write_text(json.dumps(specs), encoding="utf-8")
    monkeypatch.setattr(catalog_mod, "SPECS_JSON", specs_path)
    return specs_path


@pytest.fixture()
def fake_source_image(tmp_path: Path) -> Path:
    """Create a 200x200 red JPEG file on disk."""
    img = Image.new("RGB", (200, 200), color=(255, 0, 0))
    path = tmp_path / "source-photo.jpg"
    img.save(path, format="JPEG")
    return path


@pytest.fixture()
def fake_webp_bytes() -> bytes:
    """Return valid WebP bytes (100x100 blue)."""
    img = Image.new("RGB", (100, 100), color=(0, 0, 255))
    buf = BytesIO()
    img.save(buf, format="WEBP")
    return buf.getvalue()


@pytest.fixture()
def sample_vision_result() -> dict:
    """Return a representative vision description dict."""
    return {
        "garment_type": "crewneck sweatshirt",
        "colors": [
            {"name": "black", "hex": "#0A0A0A", "area": "body"},
            {"name": "rose gold", "hex": "#B76E79", "area": "logo"},
        ],
        "graphics": [
            {"type": "embossed", "content": "rose logo", "position": "center chest"},
        ],
        "fabric_appearance": "heavyweight cotton fleece with slight texture",
        "construction": "ribbed collar, cuffs, and hem",
    }


@pytest.fixture()
def sample_bundle_dir(tmp_path: Path, fake_source_image: Path) -> Path:
    """Create a bundle directory with manifest.json, logo-ref.png, source-photo.jpg."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    manifest = {
        "sku": "br-001",
        "name": "BLACK Rose Crewneck",
        "collection": "black-rose",
        "views": ["front", "back"],
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    logo = Image.new("RGB", (10, 10), color=(255, 0, 0))
    logo.save(bundle / "logo-ref.png", format="PNG")

    shutil.copy(fake_source_image, bundle / "source-photo.jpg")

    return bundle
