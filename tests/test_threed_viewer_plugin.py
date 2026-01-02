"""
Tests for WordPress 3D Viewer Plugin Generator
================================================

Tests for the WordPress 3D viewer plugin generator.

Coverage:
- Plugin file generation (JS, CSS, PHP)
- Viewer configuration
- Three.js integration
- Shortcode generation
- WooCommerce integration
"""

import tempfile
from pathlib import Path

import pytest

from wordpress.threed_viewer_plugin import (
    PluginGenerator,
    ThreeDViewerPlugin,
    ViewerConfig,
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

    def test_skyyrose_branding(self):
        """Should support AR configuration."""
        config = ViewerConfig(
            ar_enabled=True,
            ar_button_text="View in AR",
            loading_text="Loading SkyyRose 3D Model...",
        )

        assert config.ar_enabled is True
        assert config.ar_button_text == "View in AR"


# =============================================================================
# ThreeDViewerPlugin Tests
# =============================================================================


class TestThreeDViewerPlugin:
    """Tests for ThreeDViewerPlugin class."""

    @pytest.fixture
    def plugin(self):
        """Create plugin instance."""
        return ThreeDViewerPlugin()

    @pytest.fixture
    def custom_plugin(self):
        """Create plugin with custom config."""
        config = ViewerConfig(
            canvas_width=1024,
            canvas_height=768,
            background_color="#000000",
        )
        return ThreeDViewerPlugin(config=config)

    def test_plugin_initialization(self, plugin):
        """Should initialize with defaults."""
        assert plugin.config is not None
        assert plugin.plugin_name == "devskyy-3d-viewer"

    def test_plugin_custom_config(self, custom_plugin):
        """Should use custom config."""
        assert custom_plugin.config.canvas_width == 1024
        assert custom_plugin.config.background_color == "#000000"


# =============================================================================
# PluginGenerator Tests
# =============================================================================


class TestPluginGenerator:
    """Tests for plugin file generation."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return PluginGenerator()

    @pytest.fixture
    def custom_generator(self):
        """Create generator with custom config."""
        config = ViewerConfig(
            background_color="#1A1A1A",
            auto_rotate=True,
        )
        return PluginGenerator(config=config)

    def test_generator_initialization(self, generator):
        """Should initialize generator."""
        assert generator is not None
        assert generator.config is not None

    def test_generate_javascript(self, generator):
        """Should generate JavaScript viewer code."""
        js_code = generator.generate_javascript()

        assert "THREE" in js_code
        assert "GLTFLoader" in js_code
        assert "OrbitControls" in js_code
        assert "renderer" in js_code
        assert "camera" in js_code
        assert "scene" in js_code

    def test_javascript_has_init_function(self, generator):
        """Should have init function."""
        js_code = generator.generate_javascript()

        assert "initViewer" in js_code or "init" in js_code

    def test_javascript_has_load_model(self, generator):
        """Should have model loading function."""
        js_code = generator.generate_javascript()

        assert "loadModel" in js_code or "load" in js_code

    def test_javascript_has_animation_loop(self, generator):
        """Should have animation loop."""
        js_code = generator.generate_javascript()

        assert "animate" in js_code or "render" in js_code

    def test_generate_css(self, generator):
        """Should generate CSS styles."""
        css_code = generator.generate_css()

        assert "viewer" in css_code.lower() or "canvas" in css_code.lower()
        assert "width" in css_code
        assert "height" in css_code

    def test_css_includes_loading_styles(self, generator):
        """Should include loading indicator styles."""
        css_code = generator.generate_css()

        assert "loading" in css_code.lower() or "loader" in css_code.lower()

    def test_generate_php(self, generator):
        """Should generate PHP plugin code."""
        php_code = generator.generate_php()

        assert "<?php" in php_code
        assert "Plugin Name:" in php_code
        assert "function" in php_code

    def test_php_has_shortcode(self, generator):
        """Should register shortcode."""
        php_code = generator.generate_php()

        assert "add_shortcode" in php_code or "shortcode" in php_code.lower()

    def test_php_has_scripts_enqueue(self, generator):
        """Should enqueue scripts."""
        php_code = generator.generate_php()

        assert "wp_enqueue_script" in php_code
        assert "wp_enqueue_style" in php_code

    def test_php_has_woocommerce_integration(self, generator):
        """Should integrate with WooCommerce."""
        php_code = generator.generate_php()

        assert "woocommerce" in php_code.lower() or "product" in php_code.lower()

    def test_generate_config(self, generator):
        """Should generate configuration object."""
        config_json = generator.generate_config()

        assert "canvasWidth" in config_json or "canvas_width" in config_json
        assert "backgroundColor" in config_json or "background_color" in config_json

    def test_config_matches_settings(self, custom_generator):
        """Config should match settings."""
        config_json = custom_generator.generate_config()

        assert "#1A1A1A" in config_json or "1A1A1A" in config_json.upper()


# =============================================================================
# File Output Tests
# =============================================================================


class TestPluginFileOutput:
    """Tests for plugin file output."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return PluginGenerator()

    def test_write_plugin_files(self, generator):
        """Should write all plugin files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator.write_plugin(output_dir)

            # Check JS file
            js_file = output_dir / "js" / "viewer.js"
            assert js_file.exists()
            js_content = js_file.read_text()
            assert "THREE" in js_content

            # Check CSS file
            css_file = output_dir / "css" / "viewer.css"
            assert css_file.exists()

            # Check PHP file
            php_file = output_dir / "devskyy-3d-viewer.php"
            assert php_file.exists()

    def test_create_zip_archive(self, generator):
        """Should create zip archive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "plugin.zip"
            generator.create_zip(output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_generated_files_valid(self, generator):
        """Generated files should be syntactically valid."""
        # JavaScript should be parseable (basic check)
        js_code = generator.generate_javascript()
        assert js_code.count("{") == js_code.count("}")
        assert js_code.count("(") == js_code.count(")")

        # CSS should have balanced braces
        css_code = generator.generate_css()
        assert css_code.count("{") == css_code.count("}")

        # PHP should start correctly
        php_code = generator.generate_php()
        assert php_code.strip().startswith("<?php")


# =============================================================================
# Shortcode Tests
# =============================================================================


class TestShortcodeGeneration:
    """Tests for WordPress shortcode generation."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return PluginGenerator()

    def test_shortcode_structure(self, generator):
        """Should generate proper shortcode structure."""
        php_code = generator.generate_php()

        # Should have shortcode handler function
        assert "function" in php_code
        assert "return" in php_code

    def test_shortcode_accepts_attributes(self, generator):
        """Should accept shortcode attributes."""
        php_code = generator.generate_php()

        # Should parse attributes
        assert "$atts" in php_code or "atts" in php_code.lower()

    def test_shortcode_renders_container(self, generator):
        """Should render viewer container."""
        php_code = generator.generate_php()

        # Should output HTML container
        assert "div" in php_code.lower()
        assert "viewer" in php_code.lower() or "canvas" in php_code.lower()


# =============================================================================
# WooCommerce Integration Tests
# =============================================================================


class TestWooCommerceIntegration:
    """Tests for WooCommerce integration."""

    @pytest.fixture
    def generator(self):
        """Create generator instance."""
        return PluginGenerator()

    def test_product_meta_box(self, generator):
        """Should add product meta box."""
        php_code = generator.generate_php()

        assert "add_meta_box" in php_code or "meta_box" in php_code.lower()

    def test_save_product_meta(self, generator):
        """Should save product meta."""
        php_code = generator.generate_php()

        assert "save" in php_code.lower()
        assert "post" in php_code.lower() or "product" in php_code.lower()

    def test_display_on_product_page(self, generator):
        """Should display viewer on product page."""
        php_code = generator.generate_php()

        # Should hook into WooCommerce product display
        assert (
            "woocommerce" in php_code.lower()
            or "single_product" in php_code.lower()
            or "product" in php_code.lower()
        )


# =============================================================================
# Three.js Configuration Tests
# =============================================================================


class TestThreeJSConfig:
    """Tests for Three.js configuration."""

    @pytest.fixture
    def generator(self):
        """Create generator with specific config."""
        config = ViewerConfig(
            camera_fov=60,
            camera_near=0.1,
            camera_far=2000,
            ambient_light_intensity=0.5,
            directional_light_intensity=1.0,
        )
        return PluginGenerator(config=config)

    def test_camera_settings(self, generator):
        """Should configure camera correctly."""
        js_code = generator.generate_javascript()

        assert "PerspectiveCamera" in js_code
        assert "60" in js_code  # FOV
        assert "2000" in js_code  # Far plane

    def test_lighting_settings(self, generator):
        """Should configure lighting correctly."""
        js_code = generator.generate_javascript()

        assert "AmbientLight" in js_code
        assert "DirectionalLight" in js_code

    def test_controls_settings(self, generator):
        """Should configure OrbitControls."""
        js_code = generator.generate_javascript()

        assert "OrbitControls" in js_code

    def test_renderer_settings(self, generator):
        """Should configure WebGL renderer."""
        js_code = generator.generate_javascript()

        assert "WebGLRenderer" in js_code
        assert "antialias" in js_code.lower()


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.integration
class TestPluginIntegration:
    """Integration tests for plugin generation."""

    def test_full_plugin_generation(self):
        """Test complete plugin generation."""
        config = ViewerConfig(
            canvas_width=1024,
            canvas_height=768,
            background_color="#1A1A1A",
            loader_color="#B76E79",
            auto_rotate=True,
            enable_zoom=True,
        )
        generator = PluginGenerator(config=config)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "devskyy-3d-viewer"
            generator.write_plugin(output_dir)

            # Verify all files exist
            assert (output_dir / "devskyy-3d-viewer.php").exists()
            assert (output_dir / "js" / "viewer.js").exists()
            assert (output_dir / "css" / "viewer.css").exists()

            # Verify JS content
            js_content = (output_dir / "js" / "viewer.js").read_text()
            assert "THREE" in js_content
            assert "GLTFLoader" in js_content

            # Verify PHP content
            php_content = (output_dir / "devskyy-3d-viewer.php").read_text()
            assert "Plugin Name:" in php_content

    def test_zip_creation(self):
        """Test ZIP archive creation."""
        generator = PluginGenerator()

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "plugin.zip"
            generator.create_zip(zip_path)

            assert zip_path.exists()

            # Verify it's a valid ZIP
            import zipfile

            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                assert any("viewer.js" in n for n in names)
                assert any("viewer.css" in n for n in names)
                assert any(".php" in n for n in names)


__all__ = [
    "TestViewerConfig",
    "TestThreeDViewerPlugin",
    "TestPluginGenerator",
    "TestPluginFileOutput",
    "TestShortcodeGeneration",
    "TestWooCommerceIntegration",
    "TestThreeJSConfig",
    "TestPluginIntegration",
]
