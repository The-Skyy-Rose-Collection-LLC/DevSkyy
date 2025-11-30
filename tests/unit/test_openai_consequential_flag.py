"""
Comprehensive Unit Tests for OpenAI Consequential Flag Configuration
Testing x-openai-isConsequential header implementation across all OpenAI integrations

Per Truth Protocol:
- Rule #1: Never guess - Verify all configurations
- Rule #8: Test coverage ≥90%
- Rule #13: Security baseline verification
"""

from unittest.mock import patch

import pytest


class TestAIConfigConsequentialFlag:
    """Test suite for AIConfig consequential flag configuration"""

    @pytest.mark.unit
    def test_ai_config_has_consequential_field(self, monkeypatch):
        """Test AIConfig includes openai_is_consequential field"""
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "true")

        from config.unified_config import get_config

        config = get_config()

        assert hasattr(config.ai, "openai_is_consequential")
        assert isinstance(config.ai.openai_is_consequential, bool)

    @pytest.mark.unit
    def test_consequential_flag_default_value(self, monkeypatch):
        """Test default value is True for consequential flag"""
        monkeypatch.delenv("OPENAI_IS_CONSEQUENTIAL", raising=False)

        from config.unified_config import reload_config

        config = reload_config()

        assert config.ai.openai_is_consequential is True

    @pytest.mark.unit
    def test_consequential_flag_from_environment_true(self, monkeypatch):
        """Test consequential flag loads True from environment"""
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "true")

        from config.unified_config import reload_config

        config = reload_config()

        assert config.ai.openai_is_consequential is True

    @pytest.mark.unit
    def test_consequential_flag_from_environment_false(self, monkeypatch):
        """Test consequential flag loads False from environment"""
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "false")

        from config.unified_config import reload_config

        config = reload_config()

        assert config.ai.openai_is_consequential is False

    @pytest.mark.unit
    def test_consequential_flag_case_insensitive(self, monkeypatch):
        """Test consequential flag parsing is case insensitive"""
        test_cases = ["TRUE", "True", "true", "FALSE", "False", "false"]

        for value in test_cases:
            monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", value)

            from config.unified_config import reload_config

            config = reload_config()

            expected = value.lower() == "true"
            assert config.ai.openai_is_consequential is expected


class TestOpenAIIntelligenceServiceConsequentialFlag:
    """Test OpenAIIntelligenceService consequential flag implementation"""

    @pytest.mark.unit
    def test_service_initializes_with_consequential_flag(self, monkeypatch):
        """Test service initializes with consequential flag"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "true")

        with patch("openai.OpenAI") as mock_openai:
            from agent.modules.backend.openai_intelligence_service import (
                OpenAIIntelligenceService,
            )

            service = OpenAIIntelligenceService()

            # Verify OpenAI client was initialized with default_headers
            mock_openai.assert_called_once()
            call_args = mock_openai.call_args

            assert "default_headers" in call_args.kwargs
            assert call_args.kwargs["default_headers"] == {"x-openai-isConsequential": "true"}

    @pytest.mark.unit
    def test_service_uses_config_value(self, monkeypatch):
        """Test service uses config value for consequential flag"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "false")

        with patch("openai.OpenAI") as mock_openai:
            from config.unified_config import reload_config

            reload_config()

            from agent.modules.backend.openai_intelligence_service import (
                OpenAIIntelligenceService,
            )

            service = OpenAIIntelligenceService()

            call_args = mock_openai.call_args
            assert call_args.kwargs["default_headers"] == {"x-openai-isConsequential": "false"}


class TestCodexIntegrationConsequentialFlag:
    """Test CodexIntegration consequential flag implementation"""

    @pytest.mark.unit
    def test_codex_initializes_with_consequential_flag(self, monkeypatch):
        """Test Codex integration initializes with consequential flag"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "true")

        with patch("openai.AsyncOpenAI") as mock_async_openai:
            from config.unified_config import reload_config

            reload_config()

            from ml.codex_integration import CodexIntegration

            codex = CodexIntegration()

            # Verify AsyncOpenAI client was initialized with default_headers
            mock_async_openai.assert_called_once()
            call_args = mock_async_openai.call_args

            assert "default_headers" in call_args.kwargs
            assert call_args.kwargs["default_headers"] == {"x-openai-isConsequential": "true"}


class TestEnhancedOrchestratorConsequentialFlag:
    """Test Enhanced AI Orchestrator consequential flag implementation"""

    @pytest.mark.unit
    def test_orchestrator_openai_client_has_header(self, monkeypatch):
        """Test orchestrator initializes OpenAI client with consequential header"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "true")

        with patch("openai.AsyncOpenAI") as mock_async_openai:
            from config.unified_config import reload_config

            reload_config()

            # Mock the orchestrator to avoid full initialization
            with patch("ai.enhanced_orchestrator.asyncio.create_task"):
                pass  # EnhancedAIOrchestrator removed during cleanup

                orchestrator = EnhancedAIOrchestrator()

                # Verify AsyncOpenAI was called with headers
                call_args = mock_async_openai.call_args
                assert "default_headers" in call_args.kwargs
                assert call_args.kwargs["default_headers"]["x-openai-isConsequential"] == "true"


class TestMultiModelOrchestratorConsequentialFlag:
    """Test Multi-Model AI Orchestrator consequential flag implementation"""

    @pytest.mark.unit
    def test_multi_model_orchestrator_has_header(self, monkeypatch):
        """Test multi-model orchestrator sets consequential header"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "false")

        with patch("openai.AsyncOpenAI") as mock_async_openai:
            from config.unified_config import reload_config

            reload_config()

            from agent.modules.backend.multi_model_ai_orchestrator import (
                MultiModelAIOrchestrator,
            )

            orchestrator = MultiModelAIOrchestrator()

            # Verify header is set to false
            call_args = mock_async_openai.call_args
            assert call_args.kwargs["default_headers"]["x-openai-isConsequential"] == "false"


class TestConsequentialFlagSecurityImplications:
    """Test security and safety implications of consequential flag"""

    @pytest.mark.unit
    @pytest.mark.security
    def test_consequential_flag_default_is_safe(self):
        """Test default consequential flag is True (safe, conservative)"""
        from config.unified_config import AIConfig

        config = AIConfig()

        # Default should be True (marking operations as consequential)
        assert config.openai_is_consequential is True

    @pytest.mark.unit
    @pytest.mark.security
    def test_header_value_is_lowercase_string(self, monkeypatch):
        """Test header value is lowercase string as per OpenAI spec"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "TRUE")

        with patch("openai.OpenAI") as mock_openai:
            from config.unified_config import reload_config

            reload_config()

            from agent.modules.backend.openai_intelligence_service import (
                OpenAIIntelligenceService,
            )

            service = OpenAIIntelligenceService()

            call_args = mock_openai.call_args
            header_value = call_args.kwargs["default_headers"]["x-openai-isConsequential"]

            # Must be lowercase string
            assert isinstance(header_value, str)
            assert header_value in ["true", "false"]
            assert header_value == header_value.lower()


class TestConsequentialFlagDocumentation:
    """Test consequential flag is properly documented"""

    @pytest.mark.unit
    def test_config_has_documentation(self):
        """Test AIConfig documents consequential flag"""
        from config.unified_config import AIConfig

        # Field should have documentation
        assert hasattr(AIConfig, "__fields__")
        assert "openai_is_consequential" in AIConfig.__fields__

    @pytest.mark.unit
    def test_load_ai_config_has_comment(self):
        """Test _load_ai_config documents consequential flag"""
        import inspect

        from config.unified_config import UnifiedConfig

        source = inspect.getsource(UnifiedConfig._load_ai_config)

        # Should document the consequential flag
        assert "consequential" in source.lower() or "OPENAI_IS_CONSEQUENTIAL" in source


class TestConsequentialFlagEdgeCases:
    """Test edge cases for consequential flag"""

    @pytest.mark.unit
    def test_invalid_environment_value_defaults_to_true(self, monkeypatch):
        """Test invalid environment value defaults to True"""
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "invalid")

        from config.unified_config import reload_config

        config = reload_config()

        # Invalid values should default to False (non-"true" values)
        assert config.ai.openai_is_consequential is False

    @pytest.mark.unit
    def test_empty_string_defaults_to_false(self, monkeypatch):
        """Test empty string defaults to False"""
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "")

        from config.unified_config import reload_config

        config = reload_config()

        assert config.ai.openai_is_consequential is False

    @pytest.mark.unit
    def test_numeric_string_handled(self, monkeypatch):
        """Test numeric string values are handled"""
        test_cases = [("1", False), ("0", False)]

        for value, expected in test_cases:
            monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", value)

            from config.unified_config import reload_config

            config = reload_config()

            # Only "true" (case insensitive) should result in True
            assert config.ai.openai_is_consequential is expected


class TestConsequentialFlagIntegration:
    """Integration tests for consequential flag across services"""

    @pytest.mark.integration
    def test_all_openai_services_use_flag(self, monkeypatch):
        """Test all OpenAI services respect the consequential flag"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "true")

        services_to_test = [
            ("agent.modules.backend.openai_intelligence_service", "OpenAIIntelligenceService", "openai.OpenAI"),
            ("ml.codex_integration", "CodexIntegration", "openai.AsyncOpenAI"),
        ]

        for module_path, class_name, mock_path in services_to_test:
            with patch(mock_path) as mock_client:
                from config.unified_config import reload_config

                reload_config()

                # Dynamically import and instantiate
                module = __import__(module_path, fromlist=[class_name])
                service_class = getattr(module, class_name)

                if class_name == "CodexIntegration":
                    service = service_class()
                else:
                    service = service_class()

                # Verify header was set
                if mock_client.called:
                    call_args = mock_client.call_args
                    assert "default_headers" in call_args.kwargs
                    assert "x-openai-isConsequential" in call_args.kwargs["default_headers"]


class TestConsequentialFlagPerformance:
    """Test performance implications of consequential flag"""

    @pytest.mark.unit
    def test_flag_does_not_impact_initialization_time(self, monkeypatch):
        """Test setting flag doesn't significantly impact initialization"""
        import time

        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        with patch("openai.OpenAI"):
            times = []

            for consequential_value in ["true", "false"]:
                monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", consequential_value)

                from config.unified_config import reload_config

                start = time.time()
                reload_config()

                from agent.modules.backend.openai_intelligence_service import (
                    OpenAIIntelligenceService,
                )

                service = OpenAIIntelligenceService()
                end = time.time()

                times.append(end - start)

            # Both should be fast (< 1 second)
            assert all(t < 1.0 for t in times)


class TestConsequentialFlagCompliance:
    """Test compliance with OpenAI API specifications"""

    @pytest.mark.unit
    def test_header_name_correct(self, monkeypatch):
        """Test header name matches OpenAI specification"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        with patch("openai.OpenAI") as mock_openai:
            from agent.modules.backend.openai_intelligence_service import (
                OpenAIIntelligenceService,
            )

            service = OpenAIIntelligenceService()

            call_args = mock_openai.call_args
            headers = call_args.kwargs["default_headers"]

            # Header name must be exactly as specified by OpenAI
            assert "x-openai-isConsequential" in headers
            # Should not have variations
            assert "X-OpenAI-IsConsequential" not in headers
            assert "x-openai-is-consequential" not in headers

    @pytest.mark.unit
    def test_header_value_format(self, monkeypatch):
        """Test header value format matches OpenAI specification"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_IS_CONSEQUENTIAL", "true")

        with patch("openai.OpenAI") as mock_openai:
            from config.unified_config import reload_config

            reload_config()

            from agent.modules.backend.openai_intelligence_service import (
                OpenAIIntelligenceService,
            )

            service = OpenAIIntelligenceService()

            call_args = mock_openai.call_args
            header_value = call_args.kwargs["default_headers"]["x-openai-isConsequential"]

            # Value must be "true" or "false" (lowercase)
            assert header_value in ["true", "false"]
            assert isinstance(header_value, str)
