"""Tests for CompositorAgent — 6-stage scene compositing pipeline.

All external dependencies (rembg, Anthropic, fal_client, httpx, Gemini REST,
PIL, libcom) are mocked. Tests verify the pipeline logic, fallback chains,
and data flow between stages.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from skyyrose.elite_studio.agents.compositor_agent import CompositorAgent
from skyyrose.elite_studio.coordinator import NullLogger
from skyyrose.elite_studio.models import CompositorResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_scene(tmp_path):
    """Create a temporary scene image + scene.json."""
    scene_dir = tmp_path / "scenes" / "black-rose"
    scene_dir.mkdir(parents=True)

    # Minimal 1x1 PNG
    import io

    from PIL import Image

    img = Image.new("RGB", (100, 100), (30, 30, 30))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    scene_path = scene_dir / "black-rose-rooftop-garden-depth-enhanced.png"
    scene_path.write_bytes(buf.getvalue())

    # Scene lighting spec
    spec = {
        "lighting": "night, cool tones, silver pendant lights",
        "mood": "luxury rooftop",
        "color_temperature": "5500K",
    }
    (scene_dir / "scene.json").write_text(json.dumps(spec))

    return scene_path


@pytest.fixture
def tmp_model_image(tmp_path):
    """Create a temporary model/product image."""
    import io

    from PIL import Image

    img = Image.new("RGBA", (100, 150), (200, 100, 100, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    model_path = tmp_path / "br-001-render-branding.webp"
    model_path.write_bytes(buf.getvalue())
    return model_path


@pytest.fixture
def compositor(tmp_path):
    """CompositorAgent with silent logger and tmp output."""
    return CompositorAgent(logger=NullLogger())


# ---------------------------------------------------------------------------
# Stage 1: Alpha Matte Extraction
# ---------------------------------------------------------------------------


class TestAlphaExtraction:
    @patch("skyyrose.elite_studio.agents.compositor_agent.remove")
    def test_extract_alpha_returns_path(self, mock_rembg, compositor, tmp_model_image, tmp_path):
        """rembg.remove produces an RGBA image, saved as alpha matte."""
        from PIL import Image

        # Mock rembg to return an RGBA image
        mock_rembg.return_value = Image.new("RGBA", (100, 150), (200, 100, 100, 128))

        alpha_path = compositor._extract_alpha(str(tmp_model_image), "br-001", str(tmp_path))

        assert Path(alpha_path).exists()
        assert "alpha" in alpha_path
        mock_rembg.assert_called_once()

    @patch("skyyrose.elite_studio.agents.compositor_agent.remove")
    def test_extract_alpha_failure_raises(self, mock_rembg, compositor, tmp_model_image, tmp_path):
        mock_rembg.side_effect = RuntimeError("BRIA model failed")

        with pytest.raises(RuntimeError, match="BRIA model failed"):
            compositor._extract_alpha(str(tmp_model_image), "br-001", str(tmp_path))


# ---------------------------------------------------------------------------
# Stage 2: Opus Prompt Engineering
# ---------------------------------------------------------------------------


class TestOpusPromptEngineering:
    @patch("skyyrose.elite_studio.agents.compositor_agent.get_anthropic_client")
    def test_engineer_flux_prompt(self, mock_client_fn, compositor):
        """Opus receives scene + subject images and returns a FLUX prompt."""
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[
                MagicMock(
                    text="A fashion model wearing a black sherpa jacket stands on a luxury rooftop..."
                )
            ]
        )

        prompt = compositor._engineer_flux_prompt(
            scene_b64="SCENE_B64_DATA",
            subject_b64="SUBJECT_B64_DATA",
            collection="black-rose",
            scene_name="black-rose-rooftop-garden",
            lighting_spec={"lighting": "night, cool tones"},
        )

        assert "fashion model" in prompt.lower() or len(prompt) > 20
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-opus-4"

    @patch("skyyrose.elite_studio.agents.compositor_agent.get_anthropic_client")
    def test_opus_failure_raises(self, mock_client_fn, compositor):
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("Opus overloaded")

        with pytest.raises(Exception, match="Opus overloaded"):
            compositor._engineer_flux_prompt(
                scene_b64="x",
                subject_b64="y",
                collection="black-rose",
                scene_name="test-scene",
                lighting_spec={},
            )


# ---------------------------------------------------------------------------
# Stage 3: IC-Light Relighting
# ---------------------------------------------------------------------------


class TestICLightRelighting:
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._run_iclight")
    def test_relight_subject_returns_path(self, mock_iclight, compositor, tmp_path):
        """IC-Light produces a relit image saved to disk."""
        import io

        from PIL import Image

        relit = Image.new("RGBA", (100, 150), (180, 90, 90, 255))
        buf = io.BytesIO()
        relit.save(buf, format="PNG")
        mock_iclight.return_value = buf.getvalue()

        # Create a dummy alpha and scene path
        alpha_path = str(tmp_path / "alpha.png")
        scene_path = str(tmp_path / "scene.png")
        Image.new("RGBA", (100, 150)).save(alpha_path)
        Image.new("RGB", (100, 100)).save(scene_path)

        result = compositor._relight_subject(
            alpha_path, scene_path, "FLUX prompt", "br-001", str(tmp_path)
        )

        assert Path(result).exists()
        assert "relit" in result

    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._run_iclight")
    def test_relight_fallback_to_alpha(self, mock_iclight, compositor, tmp_path):
        """When IC-Light fails, fall back to using the alpha-matted image directly."""
        from PIL import Image

        mock_iclight.side_effect = Exception("IC-Light unavailable")

        alpha_path = str(tmp_path / "alpha.png")
        scene_path = str(tmp_path / "scene.png")
        Image.new("RGBA", (100, 150)).save(alpha_path)
        Image.new("RGB", (100, 100)).save(scene_path)

        result = compositor._relight_subject(
            alpha_path, scene_path, "prompt", "br-001", str(tmp_path)
        )

        # Should fall back to alpha path
        assert result == alpha_path


# ---------------------------------------------------------------------------
# Stage 4: FLUX Compositing (with fallback chain)
# ---------------------------------------------------------------------------


class TestFLUXCompositing:
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._flux_fill_fal")
    def test_fal_fill_success(self, mock_fal, compositor, tmp_path):
        """Primary FLUX Fill succeeds on first try."""
        mock_fal.return_value = b"\x89PNG_COMPOSITE"

        result_bytes, provider = compositor._composite_with_flux(
            scene_url="https://fal.cdn/scene.png",
            subject_url="https://fal.cdn/relit.png",
            mask_url="https://fal.cdn/mask.png",
            prompt="fashion model on rooftop",
        )

        assert result_bytes == b"\x89PNG_COMPOSITE"
        assert provider == "fal-fill"

    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._flux_fill_replicate")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._flux_kontext")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._flux_fill_fal")
    def test_fallback_chain(self, mock_fal, mock_kontext, mock_replicate, compositor):
        """fal Fill fails → Kontext fails → Replicate succeeds."""
        mock_fal.return_value = None
        mock_kontext.return_value = None
        mock_replicate.return_value = b"\x89PNG_REPLICATE"

        result_bytes, provider = compositor._composite_with_flux(
            scene_url="https://fal.cdn/scene.png",
            subject_url="https://fal.cdn/relit.png",
            mask_url="https://fal.cdn/mask.png",
            prompt="fashion model on rooftop",
        )

        assert result_bytes == b"\x89PNG_REPLICATE"
        assert provider == "replicate"

    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._flux_fill_replicate")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._flux_kontext")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._flux_fill_fal")
    def test_all_providers_fail(self, mock_fal, mock_kontext, mock_replicate, compositor):
        """All providers fail → raises."""
        mock_fal.return_value = None
        mock_kontext.return_value = None
        mock_replicate.return_value = None

        with pytest.raises(RuntimeError, match="All FLUX providers failed"):
            compositor._composite_with_flux(
                scene_url="u",
                subject_url="u",
                mask_url="u",
                prompt="p",
            )


class TestFLUXProviders:
    @patch("skyyrose.elite_studio.agents.compositor_agent.fal_client")
    def test_flux_fill_fal(self, mock_fal_mod, compositor):
        mock_fal_mod.run.return_value = {"images": [{"url": "https://fal.cdn/out.png"}]}
        with patch("skyyrose.elite_studio.agents.compositor_agent.httpx") as mock_httpx:
            mock_httpx.get.return_value = MagicMock(content=b"IMAGE", is_success=True)
            mock_httpx.get.return_value.raise_for_status = MagicMock()

            result = compositor._flux_fill_fal("scene_url", "mask_url", "prompt")
            assert result == b"IMAGE"

    @patch("skyyrose.elite_studio.agents.compositor_agent.fal_client")
    def test_flux_kontext(self, mock_fal_mod, compositor):
        mock_fal_mod.run.return_value = {"images": [{"url": "https://fal.cdn/out.png"}]}
        with patch("skyyrose.elite_studio.agents.compositor_agent.httpx") as mock_httpx:
            mock_httpx.get.return_value = MagicMock(content=b"KONTEXT_IMG", is_success=True)
            mock_httpx.get.return_value.raise_for_status = MagicMock()

            result = compositor._flux_kontext("scene_url", "mask_url", "ref_url", "prompt")
            assert result == b"KONTEXT_IMG"

    @patch("skyyrose.elite_studio.agents.compositor_agent.httpx")
    def test_flux_replicate(self, mock_httpx, compositor):
        # Initial prediction response
        predict_resp = MagicMock()
        predict_resp.is_success = True
        predict_resp.json.return_value = {
            "urls": {"get": "https://api.replicate.com/v1/predictions/abc123"},
        }

        # Poll response (succeeded)
        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "status": "succeeded",
            "output": "https://replicate.delivery/out.png",
        }
        poll_resp.raise_for_status = MagicMock()

        # Final image download
        img_resp = MagicMock()
        img_resp.content = b"REPLICATE_IMG"
        img_resp.raise_for_status = MagicMock()

        mock_httpx.post.return_value = predict_resp
        mock_httpx.get.side_effect = [poll_resp, img_resp]

        with patch.dict("os.environ", {"REPLICATE_API_TOKEN": "test-token"}):
            result = compositor._flux_fill_replicate("scene_url", "mask_url", "prompt")

        assert result == b"REPLICATE_IMG"


# ---------------------------------------------------------------------------
# Stage 5: Shadow Generation
# ---------------------------------------------------------------------------


class TestShadowGeneration:
    def test_pil_soft_shadow_fallback(self, compositor, tmp_path):
        """PIL gaussian shadow fallback when GPSDiffusion unavailable."""
        from PIL import Image

        composite_path = str(tmp_path / "composite.png")
        Image.new("RGBA", (200, 300), (100, 80, 80, 255)).save(composite_path)

        result = compositor._generate_shadows(composite_path, "br-001", str(tmp_path))

        assert Path(result).exists()
        assert "shadow" in result or result == composite_path


# ---------------------------------------------------------------------------
# Stage 6: Visual QA
# ---------------------------------------------------------------------------


class TestVisualQA:
    @patch("skyyrose.elite_studio.agents.compositor_agent.analyze_vision")
    def test_qa_pass(self, mock_gemini, compositor, tmp_path):
        from PIL import Image

        composite_path = str(tmp_path / "composite.png")
        Image.new("RGB", (200, 300)).save(composite_path)

        mock_gemini.return_value = {
            "success": True,
            "text": json.dumps(
                {
                    "status": "pass",
                    "lighting_match": {"score": 9, "notes": "Excellent match"},
                    "garment_fidelity": {"score": 8, "notes": "Good"},
                    "scene_coherence": {"score": 9, "notes": "Natural placement"},
                }
            ),
        }

        result = compositor._visual_qa(composite_path, "rooftop-garden", "black-rose")

        assert result["status"] == "pass"
        mock_gemini.assert_called_once()

    @patch("skyyrose.elite_studio.agents.compositor_agent.analyze_vision")
    def test_qa_failure_returns_warn(self, mock_gemini, compositor, tmp_path):
        from PIL import Image

        composite_path = str(tmp_path / "composite.png")
        Image.new("RGB", (200, 300)).save(composite_path)

        mock_gemini.return_value = {"success": False, "error": "Gemini overloaded"}

        result = compositor._visual_qa(composite_path, "scene", "collection")

        assert result["status"] == "warn"
        assert "error" in result


# ---------------------------------------------------------------------------
# Full Pipeline
# ---------------------------------------------------------------------------


class TestFullPipeline:
    @patch("skyyrose.elite_studio.agents.compositor_agent.analyze_vision")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._generate_shadows")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._composite_with_flux")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._relight_subject")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._engineer_flux_prompt")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._extract_alpha")
    @patch("skyyrose.elite_studio.agents.compositor_agent.upload_to_fal")
    def test_full_pipeline_success(
        self,
        mock_upload,
        mock_alpha,
        mock_prompt,
        mock_relight,
        mock_flux,
        mock_shadow,
        mock_qa,
        compositor,
        tmp_path,
        tmp_scene,
        tmp_model_image,
    ):
        # Setup mocks
        alpha_path = str(tmp_path / "alpha.png")
        relit_path = str(tmp_path / "relit.png")
        shadow_path = str(tmp_path / "shadow.png")
        from PIL import Image

        Image.new("RGBA", (100, 150)).save(alpha_path)
        Image.new("RGBA", (100, 150)).save(relit_path)
        Image.new("RGB", (100, 150)).save(shadow_path)

        mock_alpha.return_value = alpha_path
        mock_prompt.return_value = "A fashion model on rooftop..."
        mock_relight.return_value = relit_path
        mock_flux.return_value = (b"\x89PNG_FINAL", "fal-fill")
        mock_shadow.return_value = shadow_path
        mock_upload.return_value = "https://fal.cdn/uploaded.png"
        mock_qa.return_value = {
            "success": True,
            "text": json.dumps({"status": "pass", "details": {}}),
        }

        result = compositor.composite(
            sku="br-001",
            scene_image_path=str(tmp_scene),
            model_image_path=str(tmp_model_image),
            collection="black-rose",
            scene_name="black-rose-rooftop-garden",
            output_dir=str(tmp_path / "output"),
        )

        assert isinstance(result, CompositorResult)
        assert result.success
        assert result.provider == "fal-fill"
        assert result.stages_completed == 6

    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._extract_alpha")
    def test_pipeline_alpha_failure(
        self, mock_alpha, compositor, tmp_scene, tmp_model_image, tmp_path
    ):
        """Pipeline stops gracefully when alpha extraction fails."""
        mock_alpha.side_effect = RuntimeError("BRIA not available")

        result = compositor.composite(
            sku="br-001",
            scene_image_path=str(tmp_scene),
            model_image_path=str(tmp_model_image),
            collection="black-rose",
            scene_name="test-scene",
            output_dir=str(tmp_path / "output"),
        )

        assert not result.success
        assert "BRIA" in result.error
        assert result.stages_completed == 0


class TestCheckpointResume:
    @patch("skyyrose.elite_studio.agents.compositor_agent.analyze_vision")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._generate_shadows")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._composite_with_flux")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._relight_subject")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._engineer_flux_prompt")
    @patch("skyyrose.elite_studio.agents.compositor_agent.CompositorAgent._extract_alpha")
    @patch("skyyrose.elite_studio.agents.compositor_agent.upload_to_fal")
    def test_resume_from_stage_4(
        self,
        mock_upload,
        mock_alpha,
        mock_prompt,
        mock_relight,
        mock_flux,
        mock_shadow,
        mock_qa,
        compositor,
        tmp_path,
        tmp_scene,
        tmp_model_image,
    ):
        """Resuming from stage 4 skips alpha, prompt, and relight stages."""
        shadow_path = str(tmp_path / "shadow.png")
        from PIL import Image

        Image.new("RGB", (100, 150)).save(shadow_path)

        mock_flux.return_value = (b"\x89PNG", "fal-fill")
        mock_shadow.return_value = shadow_path
        mock_upload.return_value = "https://fal.cdn/uploaded.png"
        mock_qa.return_value = {
            "success": True,
            "text": json.dumps({"status": "pass"}),
        }

        # Pre-create checkpoint artifacts
        alpha_path = str(tmp_path / "br-001-alpha.png")
        relit_path = str(tmp_path / "br-001-relit.png")
        Image.new("RGBA", (100, 150)).save(alpha_path)
        Image.new("RGBA", (100, 150)).save(relit_path)

        result = compositor.composite(
            sku="br-001",
            scene_image_path=str(tmp_scene),
            model_image_path=str(tmp_model_image),
            collection="black-rose",
            scene_name="test-scene",
            output_dir=str(tmp_path / "output"),
            resume_from=4,
            checkpoint_alpha=alpha_path,
            checkpoint_relit=relit_path,
            checkpoint_prompt="cached prompt",
        )

        assert result.success
        # Stages 1-3 should NOT have been called
        mock_alpha.assert_not_called()
        mock_prompt.assert_not_called()
        mock_relight.assert_not_called()
        # Stages 4-6 SHOULD have been called
        mock_flux.assert_called_once()


class TestAuditLog:
    def test_audit_log_written(self, compositor, tmp_path):
        stages = {
            "alpha": {"path": "/tmp/alpha.png", "duration_s": 1.2},
            "prompt": {"model": "claude-opus-4", "duration_s": 2.5},
        }
        result = CompositorResult(
            success=True,
            provider="fal-fill",
            scene_name="test-scene",
            stages_completed=6,
        )

        log_path = compositor._write_audit_log(
            "br-001", "test-scene", stages, result, str(tmp_path)
        )

        assert Path(log_path).exists()
        data = json.loads(Path(log_path).read_text())
        assert data["sku"] == "br-001"
        assert data["scene_name"] == "test-scene"
        assert "stages" in data
