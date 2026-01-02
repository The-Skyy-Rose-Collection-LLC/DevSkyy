"""
Tests for WordPress 3D Viewer Plugin Generator
================================================

Tests for the WordPress 3D viewer plugin generator.

Coverage:
- Plugin file generation (JS, CSS)
- Viewer configuration
- Three.js integration
- WordPress plugin structure
"""

import json
import tempfile
from pathlib import Path

import pytest

from wordpress.threed_viewer_plugin import (
    ViewerConfig,
    WordPressPluginGenerator,
    generate_shortcode_html,
    generate_viewer_css,
    generate_viewer_javascript,
)

# =============================================================================
# ViewerConfig Tests
# =============================================================================


class TestViewerConfig:
    """Tests for ViewerConfig dataclass."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = ViewerConfig()

        assert config.auto_rotate is True
        assert config.enable_zoom is True
        assert config.enable_pan is False
        assert config.camera_fov == 45.0
        assert config.ambient_intensity == 0.5
        assert config.ar_enabled is True

    def test_custom_config(self):
        """Should accept custom values."""
        config = ViewerConfig(
            auto_rotate=False,
            camera_fov=60.0,
            enable_zoom=False,
        )

        assert config.auto_rotate is False
        assert config.camera_fov == 60.0
        assert config.enable_zoom is False

    def test_lighting_config(self):
        """Should configure lighting."""
        config = ViewerConfig(
            ambient_intensity=0.6,
            directional_intensity=0.8,
        )

        assert config.ambient_intensity == 0.6
        assert config.directional_intensity == 0.8

    def test_ar_config(self):
        """Should support AR configuration."""
        config = ViewerConfig(
            ar_enabled=True,
            ar_button_text="View in AR",
            loading_text="Loading SkyyRose 3D Model...",
        )

        assert config.ar_enabled is True
        assert config.ar_button_text == "View in AR"
        assert config.loading_text == "Loading SkyyRose 3D Model..."

    def test_to_dict(self):
        """Should convert to dictionary."""
        config = ViewerConfig(
            auto_rotate=False,
            camera_fov=60.0,
        )

        result = config.to_dict()

        assert result["autoRotate"] is False
        assert result["cameraFov"] == 60.0
        assert "enableZoom" in result
        assert "arEnabled" in result


# =============================================================================
# WordPressPluginGenerator Tests
# =============================================================================


class TestWordPressPluginGenerator:
    """Tests for WordPressPluginGenerator class."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create generator instance with temp directory."""
        return WordPressPluginGenerator(output_dir=tmp_path)

    @pytest.fixture
    def custom_generator(self, tmp_path):
        """Create generator with custom settings."""
        gen = WordPressPluginGenerator(
            output_dir=tmp_path,
            plugin_name="custom-3d-viewer",
            version="2.0.0",
        )
        gen.config = ViewerConfig(
            auto_rotate=True,
            camera_fov=60.0,
        )
        return gen

    def test_generator_initialization(self, generator, tmp_path):
        """Should initialize with output directory."""
        assert generator.output_dir == tmp_path
        assert generator.plugin_name == "skyyrose-3d-viewer"
        assert generator.version == "1.0.0"
        assert generator.config is not None

    def test_generator_custom_settings(self, custom_generator):
        """Should accept custom settings."""
        assert custom_generator.plugin_name == "custom-3d-viewer"
        assert custom_generator.version == "2.0.0"
        assert custom_generator.config.camera_fov == 60.0

    def test_generate_creates_plugin_directory(self, generator, tmp_path):
        """Should create plugin directory structure."""
        plugin_dir = generator.generate()

        assert plugin_dir.exists()
        assert plugin_dir.name == "skyyrose-3d-viewer"
        assert (plugin_dir / "assets" / "js").exists()
        assert (plugin_dir / "assets" / "css").exists()

    def test_generate_creates_javascript_file(self, generator):
        """Should create JavaScript file."""
        plugin_dir = generator.generate()

        js_file = plugin_dir / "assets" / "js" / "3d-viewer.js"
        assert js_file.exists()

        content = js_file.read_text()
        assert "THREE" in content or "three" in content.lower()

    def test_generate_creates_css_file(self, generator):
        """Should create CSS file."""
        plugin_dir = generator.generate()

        css_file = plugin_dir / "assets" / "css" / "3d-viewer.css"
        assert css_file.exists()

        content = css_file.read_text()
        assert "viewer" in content.lower() or "container" in content.lower()

    def test_generate_creates_config_json(self, generator):
        """Should create config.json file."""
        plugin_dir = generator.generate()

        config_file = plugin_dir / "config.json"
        assert config_file.exists()

        config_data = json.loads(config_file.read_text())
        assert "autoRotate" in config_data
        assert "cameraFov" in config_data


# =============================================================================
# JavaScript Generation Tests
# =============================================================================


class TestJavaScriptGeneration:
    """Tests for JavaScript viewer code generation."""

    def test_generate_javascript_with_default_config(self):
        """Should generate JavaScript with default config."""
        config = ViewerConfig()
        js_code = generate_viewer_javascript(config)

        assert "THREE" in js_code or "scene" in js_code.lower()

    def test_javascript_has_viewer_initialization(self):
        """Should have viewer initialization logic."""
        config = ViewerConfig()
        js_code = generate_viewer_javascript(config)

        # Should have initialization or setup code
        assert (
            "init" in js_code.lower() or "setup" in js_code.lower() or "create" in js_code.lower()
        )

    def test_javascript_has_render_loop(self):
        """Should have render/animation loop."""
        config = ViewerConfig()
        js_code = generate_viewer_javascript(config)

        assert "animate" in js_code.lower() or "render" in js_code.lower()


# =============================================================================
# CSS Generation Tests
# =============================================================================


class TestCSSGeneration:
    """Tests for CSS generation."""

    def test_generate_css(self):
        """Should generate CSS styles."""
        css_code = generate_viewer_css()

        assert len(css_code) > 0
        assert "viewer" in css_code.lower() or "container" in css_code.lower()

    def test_css_has_dimensions(self):
        """Should include dimension styles."""
        css_code = generate_viewer_css()

        assert "width" in css_code.lower() or "height" in css_code.lower()

    def test_css_has_balanced_braces(self):
        """CSS should have balanced braces."""
        css_code = generate_viewer_css()

        assert css_code.count("{") == css_code.count("}")


# =============================================================================
# Shortcode HTML Generation Tests
# =============================================================================


class TestShortcodeHTML:
    """Tests for shortcode HTML generation."""

    def test_generate_shortcode_html_default(self):
        """Should generate HTML with model URL."""
        html = generate_shortcode_html(model_url="https://example.com/model.glb")

        assert "div" in html.lower()
        assert "viewer" in html.lower() or "skyyrose" in html.lower()

    def test_generate_shortcode_html_with_model_url(self):
        """Should include model URL in data attribute."""
        html = generate_shortcode_html(model_url="https://example.com/model.glb")

        assert "example.com" in html
        assert "data-model-url" in html

    def test_generate_shortcode_html_with_dimensions(self):
        """Should include custom dimensions."""
        html = generate_shortcode_html(
            model_url="https://example.com/model.glb",
            width="800px",
            height="600px",
        )

        assert "800px" in html
        assert "600px" in html


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
class TestPluginIntegration:
    """Integration tests for plugin generation."""

    def test_full_plugin_generation(self):
        """Test complete plugin generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = WordPressPluginGenerator(
                output_dir=Path(tmpdir),
                plugin_name="test-3d-viewer",
                version="1.0.0",
            )
            generator.config = ViewerConfig(
                auto_rotate=True,
                enable_zoom=True,
                camera_fov=60.0,
            )

            plugin_dir = generator.generate()

            # Verify directory structure
            assert plugin_dir.exists()
            assert (plugin_dir / "assets" / "js" / "3d-viewer.js").exists()
            assert (plugin_dir / "assets" / "css" / "3d-viewer.css").exists()
            assert (plugin_dir / "config.json").exists()

            # Verify config content
            config_data = json.loads((plugin_dir / "config.json").read_text())
            assert config_data["autoRotate"] is True
            assert config_data["cameraFov"] == 60.0

    def test_multiple_plugin_generations(self):
        """Should handle multiple generations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                generator = WordPressPluginGenerator(
                    output_dir=Path(tmpdir),
                    plugin_name=f"plugin-{i}",
                )
                plugin_dir = generator.generate()
                assert plugin_dir.exists()
                assert plugin_dir.name == f"plugin-{i}"


# =============================================================================
# Backwards Compatibility Tests (Aliases)
# =============================================================================


class TestBackwardsCompatibility:
    """Tests for backwards compatible aliases."""

    def test_plugin_generator_alias(self):
        """PluginGenerator should be alias for WordPressPluginGenerator."""
        from wordpress.threed_viewer_plugin import PluginGenerator

        assert PluginGenerator is WordPressPluginGenerator

    def test_threed_viewer_plugin_alias(self):
        """ThreeDViewerPlugin should be alias for WordPressPluginGenerator."""
        from wordpress.threed_viewer_plugin import ThreeDViewerPlugin

        assert ThreeDViewerPlugin is WordPressPluginGenerator


__all__ = [
    "TestViewerConfig",
    "TestWordPressPluginGenerator",
    "TestJavaScriptGeneration",
    "TestCSSGeneration",
    "TestShortcodeHTML",
    "TestPluginIntegration",
    "TestBackwardsCompatibility",
]
