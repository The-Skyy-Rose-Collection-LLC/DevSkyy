"""Tests for config — paths, constants, and lazy client factories."""

from skyyrose.elite_studio import config


class TestConstants:
    def test_vision_models(self):
        assert config.VISION_GEMINI_MODEL == "gemini-3-flash-preview"
        assert config.VISION_OPENAI_MODEL == "gpt-4o"

    def test_generation_model(self):
        # Per Context7 + project policy: Nano Banana 2 (gemini-3.1-flash-
        # image-preview) is the recommended go-to image-generation default.
        # Nano Banana Pro (gemini-3-pro-image-preview) is reserved for
        # explicit pro-asset workflows via NANO_BANANA_PRO_MODEL.
        assert config.GENERATION_MODEL == "gemini-3.1-flash-image-preview"
        assert config.GENERATION_ASPECT_RATIO == "3:4"

    def test_qc_model(self):
        # Policy: vision is OpenAI + Gemini, never Claude. QC_MODEL is the
        # OpenAI side of the dual-vision QC panel; the Gemini side is
        # COMPOSITOR_QA_MODEL.
        assert config.QC_MODEL == "gpt-4o"

    def test_timeouts(self):
        assert config.GEMINI_TIMEOUT > 0
        assert config.OPENAI_TIMEOUT > 0
        assert config.ANTHROPIC_TIMEOUT > 0

    def test_retry_config(self):
        assert config.MAX_RETRIES >= 2
        assert config.RETRY_DELAY_SECONDS > 0


class TestPaths:
    def test_overrides_dir_is_optional_path(self):
        """OVERRIDES_DIR points at the retired per-SKU prompt-override location.

        The directory was intentionally removed (overrides retired 2026-04-25,
        commit 292ccc027); the constant remains as an OPTIONAL enrichment path
        that consumers (utils.get_override, skyyrose_production_studio) tolerate
        when absent. So we assert the constant is correctly located, not that the
        directory exists on disk.
        """
        assert hasattr(config.OVERRIDES_DIR, "is_dir")
        assert str(config.OVERRIDES_DIR).replace("\\", "/").endswith("prompts/overrides")

    def test_source_dir_is_path(self):
        """SOURCE_DIR is a Path object pointing to the expected location."""
        assert hasattr(config.SOURCE_DIR, "is_dir")
        assert "source-products" in str(config.SOURCE_DIR)


class TestLazyClients:
    def test_openai_client_is_cached(self):
        """Verify lru_cache is applied (singleton pattern)."""
        assert hasattr(config.get_openai_client, "cache_clear")
        assert hasattr(config.get_openai_client, "cache_info")

    def test_anthropic_client_is_cached(self):
        """Verify lru_cache is applied (singleton pattern)."""
        assert hasattr(config.get_anthropic_client, "cache_clear")
        assert hasattr(config.get_anthropic_client, "cache_info")
