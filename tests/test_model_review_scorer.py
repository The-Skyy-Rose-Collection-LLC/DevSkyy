"""Tests for imagery/model_review_scorer.py — analytic scorer + branding VLM judge.

Mirrors tests/test_model_fidelity.py's trimesh-mocking pattern and
tests/quality/test_qc_provider_switch.py's judge_fn-injection pattern.
"""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest
from PIL import Image, ImageDraw
from pygltflib import GLTF2, BufferView
from pygltflib import Image as GLTFImage
from pygltflib import Material, PbrMetallicRoughness, Texture, TextureInfo

from imagery.model_review_scorer import (
    _BRANDING_JUDGE_TOOL,
    AnalyticScoreResult,
    BrandingScoreResult,
    _branding_judge_content,
    _call_anthropic_branding_judge,
    _call_with_retries,
    _color_score_from_delta_e,
    _material_range_score,
    score_analytic,
    score_branding_vlm,
)


def _png_bytes(rgb: tuple[int, int, int], size: tuple[int, int] = (4, 4)) -> bytes:
    img = Image.new("RGB", size, rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_gltf(
    *,
    base_color_rgb: tuple[int, int, int] | None,
    roughness: float,
    metalness: float,
    via_texture: bool,
) -> GLTF2:
    """A real (non-file-loaded) GLTF2 instance carrying one material, with the
    base-color/ORM signal embedded either as texture pixels or as bare factors —
    avoids needing an actual .glb file on disk."""
    if via_texture:
        base_color_png = _png_bytes(base_color_rgb)
        orm_png = _png_bytes((0, round(roughness * 255), round(metalness * 255)))
        blob = base_color_png + orm_png
        gltf = GLTF2()
        gltf.bufferViews = [
            BufferView(buffer=0, byteOffset=0, byteLength=len(base_color_png)),
            BufferView(buffer=0, byteOffset=len(base_color_png), byteLength=len(orm_png)),
        ]
        gltf.images = [
            GLTFImage(bufferView=0, mimeType="image/png"),
            GLTFImage(bufferView=1, mimeType="image/png"),
        ]
        gltf.textures = [Texture(source=0), Texture(source=1)]
        pbr = PbrMetallicRoughness(
            baseColorTexture=TextureInfo(index=0),
            metallicRoughnessTexture=TextureInfo(index=1),
            roughnessFactor=1.0,
            metallicFactor=1.0,
        )
        gltf.binary_blob = lambda: blob
    else:
        gltf = GLTF2()
        gltf.bufferViews = []
        gltf.images = []
        gltf.textures = []
        pbr = PbrMetallicRoughness(
            baseColorFactor=(
                [
                    base_color_rgb[0] / 255.0,
                    base_color_rgb[1] / 255.0,
                    base_color_rgb[2] / 255.0,
                    1.0,
                ]
                if base_color_rgb
                else None
            ),
            roughnessFactor=roughness,
            metallicFactor=metalness,
        )
        gltf.binary_blob = lambda: b""
    gltf.materials = [Material(pbrMetallicRoughness=pbr)]
    return gltf


def _make_mock_mesh() -> Mock:
    """Mirrors tests/test_model_fidelity.py's mock_mesh pattern, extended with a
    real bounding_box.bounds needed for this module's proportions scoring."""
    mesh = Mock()
    mesh.is_watertight = True
    mesh.euler_number = 2
    mesh.area_faces = np.array([1.0, 1.0, 1.0])
    mesh.vertices = np.zeros((12000, 3))
    mesh.faces = np.zeros((6000, 3))
    mesh.edges_unique = np.zeros((100, 2))
    mesh.bounding_box = Mock()
    mesh.bounding_box.volume = 10.0
    mesh.bounding_box.bounds = np.array([[0.0, 0.0, 0.0], [2.0, 4.0, 1.0]])
    mesh.volume = 5.0
    mesh.area = 20.0
    mesh.visual = Mock()
    mesh.visual.material = Mock()
    mesh.visual.material.image = None
    mesh.visual.uv = np.array([[0.0, 0.0], [1.0, 1.0]])
    return mesh


def _make_reference_packshot(fg_rgb: tuple[int, int, int]) -> Image.Image:
    """White studio background with a centered dark rectangle, aspect 0.5 (40x80)
    to match the mock mesh's bounding-box aspect ratio (2.0/4.0 = 0.5)."""
    img = Image.new("RGB", (120, 120), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 20, 79, 99], fill=fg_rgb)  # 40w x 80h
    return img


class TestColorScoreFormula:
    def test_delta_e_zero_scores_near_100(self):
        assert _color_score_from_delta_e(0.0) == pytest.approx(100.0)

    def test_delta_e_at_perfect_threshold_scores_100(self):
        assert _color_score_from_delta_e(2.0) == pytest.approx(100.0)

    def test_delta_e_20_scores_near_0(self):
        assert _color_score_from_delta_e(20.0) == pytest.approx(0.0)

    def test_delta_e_at_floor_threshold_scores_0(self):
        assert _color_score_from_delta_e(15.0) == pytest.approx(0.0)

    def test_delta_e_midpoint_scores_50(self):
        midpoint = (2.0 + 15.0) / 2.0
        assert _color_score_from_delta_e(midpoint) == pytest.approx(50.0)


class TestMaterialRangeScore:
    def test_in_range_fabric_scores_100(self):
        score = _material_range_score(roughness=0.94, metalness=0.03)
        assert score == pytest.approx(100.0)

    def test_out_of_range_scores_lower(self):
        score = _material_range_score(roughness=0.1, metalness=0.5)
        assert 0.0 <= score < 50.0


class TestScoreAnalytic:
    def test_all_dimensions_in_range_and_texture_via_factor(self, tmp_path):
        model_path = tmp_path / "model.glb"
        model_path.touch()
        reference_path = tmp_path / "reference.png"
        _make_reference_packshot((32, 30, 29)).save(reference_path)

        fake_gltf = _make_gltf(
            base_color_rgb=(30, 32, 31), roughness=0.94, metalness=0.03, via_texture=False
        )
        mock_mesh = _make_mock_mesh()

        with (
            patch("trimesh.load", return_value=mock_mesh),
            patch.object(GLTF2, "load", return_value=fake_gltf),
        ):
            result = score_analytic(model_path, "br-001", reference_path)

        assert isinstance(result, AnalyticScoreResult)
        for dim in (
            result.geometry,
            result.materials,
            result.colors,
            result.proportions,
            result.texture_detail_floor,
            result.overall_partial,
        ):
            assert isinstance(dim, float)
            assert 0.0 <= dim <= 100.0

        assert result.geometry == pytest.approx(100.0)
        assert result.texture_detail_floor == pytest.approx(60.0)
        assert result.materials == pytest.approx(100.0)
        assert result.colors > 80.0
        assert result.proportions > 90.0
        assert result.overall_partial == pytest.approx(
            (result.geometry + result.materials + result.colors + result.proportions) / 4.0
        )

    def test_materials_extracted_via_orm_texture(self, tmp_path):
        model_path = tmp_path / "model.glb"
        model_path.touch()
        reference_path = tmp_path / "reference.png"
        _make_reference_packshot((32, 30, 29)).save(reference_path)

        fake_gltf = _make_gltf(
            base_color_rgb=(30, 32, 31), roughness=0.94, metalness=0.03, via_texture=True
        )
        mock_mesh = _make_mock_mesh()

        with (
            patch("trimesh.load", return_value=mock_mesh),
            patch.object(GLTF2, "load", return_value=fake_gltf),
        ):
            result = score_analytic(model_path, "br-001", reference_path)

        assert result.materials > 90.0

    def test_no_materials_scores_zero(self, tmp_path):
        model_path = tmp_path / "model.glb"
        model_path.touch()
        reference_path = tmp_path / "reference.png"
        _make_reference_packshot((32, 30, 29)).save(reference_path)

        fake_gltf = GLTF2()
        fake_gltf.materials = []
        fake_gltf.textures = []
        fake_gltf.images = []
        fake_gltf.bufferViews = []
        fake_gltf.binary_blob = lambda: b""
        mock_mesh = _make_mock_mesh()

        with (
            patch("trimesh.load", return_value=mock_mesh),
            patch.object(GLTF2, "load", return_value=fake_gltf),
        ):
            result = score_analytic(model_path, "br-001", reference_path)

        assert result.materials == pytest.approx(0.0)


class TestScoreBrandingVlm:
    def test_injected_judge_fn_never_touches_network_or_disk(self):
        calls = {}

        def fake_judge(req):
            calls["req"] = req
            return (
                {
                    "visual_analysis": "The rose-cluster graphic is present on the left "
                    "chest panel, matching the reference artwork and colorway.",
                    "graphic_present": True,
                    "artwork_matches_reference": True,
                    "placement_correct": True,
                    "branding": 92.0,
                    "reason": "pass",
                },
                0.05,
            )

        preview_path = Path("/nonexistent/preview.webp")
        reference_path = Path("/nonexistent/reference.jpg")

        result = score_branding_vlm(preview_path, reference_path, "br-001", judge_fn=fake_judge)

        assert isinstance(result, BrandingScoreResult)
        assert result.branding == pytest.approx(92.0)
        assert result.visual_analysis  # non-empty, forced-observation field present
        assert result.judge_cost_usd == pytest.approx(0.05)
        assert "req" in calls

    def test_missing_api_key_and_no_judge_fn_raises(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            score_branding_vlm(
                Path("/nonexistent/preview.webp"),
                Path("/nonexistent/reference.jpg"),
                "br-001",
                judge_fn=None,
            )

    def test_judge_fn_error_propagates_not_swallowed(self):
        def boom(req):
            raise RuntimeError("network down")

        with pytest.raises(RuntimeError, match="network down"):
            score_branding_vlm(
                Path("/nonexistent/preview.webp"),
                Path("/nonexistent/reference.jpg"),
                "br-001",
                judge_fn=boom,
            )


class TestBrandingJudgeContent:
    """The content builder must put the rendered preview FIRST and the reference
    SECOND — the judge's own instructions call image 1 the candidate and image 2
    the reference, so swapping them silently inverts every verdict."""

    def test_order_and_media_types(self, tmp_path):
        preview = tmp_path / "preview.webp"
        preview.write_bytes(_png_bytes((10, 10, 10)))
        reference = tmp_path / "ref.jpg"
        reference.write_bytes(_png_bytes((200, 200, 200)))

        content = _branding_judge_content(preview, reference, "INSTRUCTIONS")

        assert len(content) == 3
        assert content[0] == {"type": "text", "text": "INSTRUCTIONS"}
        assert content[1]["type"] == "image"
        assert content[1]["source"]["media_type"] == "image/webp"  # preview FIRST
        assert content[2]["type"] == "image"
        assert content[2]["source"]["media_type"] == "image/jpeg"  # reference SECOND


class TestAnthropicBrandingJudge:
    """Covers the REAL paid-call path (mocked SDK, no network) — request/content
    construction + tool_use verdict extraction — which every judge_fn-injection
    test in TestScoreBrandingVlm bypasses entirely."""

    @staticmethod
    def _files(tmp_path):
        preview = tmp_path / "preview.webp"
        preview.write_bytes(_png_bytes((10, 10, 10)))
        reference = tmp_path / "ref.jpg"
        reference.write_bytes(_png_bytes((200, 200, 200)))
        return preview, reference

    def test_builds_message_and_extracts_verdict(self, tmp_path, monkeypatch):
        anthropic = pytest.importorskip("anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        preview, reference = self._files(tmp_path)

        tool_block = Mock()
        tool_block.type = "tool_use"
        tool_block.name = _BRANDING_JUDGE_TOOL["name"]
        tool_block.input = {"branding": 88.0, "visual_analysis": "graphic present", "reason": "ok"}
        fake_resp = Mock(content=[tool_block])

        captured = {}

        def fake_create(**kwargs):
            captured.update(kwargs)
            return fake_resp

        fake_client = Mock()
        fake_client.messages.create = fake_create
        monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: fake_client)

        verdict, cost = _call_anthropic_branding_judge(
            {
                "instructions": "judge this",
                "rendered_preview_path": preview,
                "reference_image_path": reference,
            }
        )

        assert verdict["branding"] == 88.0
        assert cost == pytest.approx(0.05)
        content = captured["messages"][0]["content"]
        assert content[0]["text"] == "judge this"
        assert content[1]["source"]["media_type"] == "image/webp"  # preview FIRST
        assert content[2]["source"]["media_type"] == "image/jpeg"  # reference SECOND
        assert captured["tools"] == [_BRANDING_JUDGE_TOOL]
        assert captured["tool_choice"] == {"type": "any"}  # forces exactly one verdict call

    def test_no_tool_use_block_raises(self, tmp_path, monkeypatch):
        anthropic = pytest.importorskip("anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        preview, reference = self._files(tmp_path)

        text_block = Mock()
        text_block.type = "text"  # not a tool_use block
        fake_client = Mock()
        fake_client.messages.create = lambda **kw: Mock(content=[text_block])
        monkeypatch.setattr(anthropic, "Anthropic", lambda **kw: fake_client)

        with pytest.raises(RuntimeError, match="no branding_qc_verdict"):
            _call_anthropic_branding_judge(
                {
                    "instructions": "x",
                    "rendered_preview_path": preview,
                    "reference_image_path": reference,
                }
            )


class TestCallWithRetries:
    def test_retries_then_succeeds(self):
        calls = {"n": 0}

        def send():
            calls["n"] += 1
            if calls["n"] < 2:
                raise RuntimeError("transient")
            return "ok"

        with patch("imagery.model_review_scorer.time.sleep"):
            assert _call_with_retries(send, retries=2) == "ok"
        assert calls["n"] == 2

    def test_raises_after_exhausting_retries(self):
        def send():
            raise RuntimeError("always down")

        with patch("imagery.model_review_scorer.time.sleep"):
            with pytest.raises(RuntimeError, match="always down"):
                _call_with_retries(send, retries=2)
