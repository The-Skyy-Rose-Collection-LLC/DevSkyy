"""Tests for config — paths, constants, and lazy client factories."""

from skyyrose.elite_studio import config


class TestConstants:
    def test_vision_models(self):
        assert config.VISION_GEMINI_MODEL == "gemini-3-flash-preview"
        assert config.VISION_OPENAI_MODEL == "gpt-4o"

    def test_generation_model(self):
        assert config.GENERATION_MODEL == "gemini-3-pro-image-preview"
        assert config.GENERATION_ASPECT_RATIO == "3:4"

    def test_qc_model(self):
        assert "claude" in config.QC_MODEL

    def test_timeouts(self):
        assert config.GEMINI_TIMEOUT > 0
        assert config.OPENAI_TIMEOUT > 0
        assert config.ANTHROPIC_TIMEOUT > 0

    def test_retry_config(self):
        assert config.MAX_RETRIES >= 2
        assert config.RETRY_DELAY_SECONDS > 0


class TestPaths:
    def test_overrides_dir_exists(self):
        assert config.OVERRIDES_DIR.exists()

    def test_source_dir_exists(self):
        assert config.SOURCE_DIR.exists()


class TestLazyClients:
    def test_openai_client_is_cached(self):
        """Verify lru_cache is applied (singleton pattern)."""
        assert hasattr(config.get_openai_client, "cache_clear")
        assert hasattr(config.get_openai_client, "cache_info")

    def test_anthropic_client_is_cached(self):
        """Verify lru_cache is applied (singleton pattern)."""
        assert hasattr(config.get_anthropic_client, "cache_clear")
        assert hasattr(config.get_anthropic_client, "cache_info")
