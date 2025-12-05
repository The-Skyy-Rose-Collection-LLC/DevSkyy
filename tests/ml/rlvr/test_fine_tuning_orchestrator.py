"""
Tests for ml/rlvr/fine_tuning_orchestrator.py

Target: 60%+ coverage

Tests cover:
- Fine-tuning orchestrator initialization
- OpenAI fine-tuning
- Anthropic prompt optimization
- Job progress tracking
"""

import os
from unittest.mock import Mock, patch
import uuid

import pytest

from ml.rlvr.fine_tuning_orchestrator import FineTuningOrchestrator


class TestFineTuningOrchestrator:
    """Test FineTuningOrchestrator"""

    @pytest.mark.asyncio
    async def test_init(self, mock_session):
        """Test orchestrator initialization"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key", "ANTHROPIC_API_KEY": "test_key"}):
            orchestrator = FineTuningOrchestrator(mock_session)

            assert orchestrator.session is not None
            assert orchestrator.collector is not None

    @pytest.mark.asyncio
    async def test_init_without_api_keys(self, mock_session):
        """Test initialization without API keys"""
        with patch.dict(os.environ, {}, clear=True):
            orchestrator = FineTuningOrchestrator(mock_session)

            # Should initialize but warn about missing keys
            assert orchestrator.openai_client is None
            assert orchestrator.anthropic_client is None

    @pytest.mark.asyncio
    async def test_format_examples(self, mock_session):
        """Test formatting examples for legacy format"""
        orchestrator = FineTuningOrchestrator(mock_session)

        examples = [
            {"input": "test input 1", "output": "test output 1", "score": 0.95},
            {"input": "test input 2", "output": "test output 2", "score": 0.90},
        ]

        formatted = orchestrator._format_examples(examples)

        assert "Example 1" in formatted
        assert "Example 2" in formatted
        assert "0.95" in formatted

    @pytest.mark.asyncio
    async def test_format_examples_xml(self, mock_session):
        """Test formatting examples with XML tags"""
        orchestrator = FineTuningOrchestrator(mock_session)

        examples = [
            {"input": "test input", "output": "test output", "score": 0.95},
        ]

        formatted = orchestrator._format_examples_xml(examples)

        # Should contain XML tags
        assert "<example" in formatted
        assert "<input>" in formatted
        assert "<output>" in formatted
        assert "score=" in formatted

    @pytest.mark.asyncio
    async def test_format_examples_xml_escapes_html(self, mock_session):
        """Test XML formatting escapes HTML characters"""
        orchestrator = FineTuningOrchestrator(mock_session)

        examples = [
            {"input": "<script>alert('xss')</script>", "output": "safe output", "score": 0.95},
        ]

        formatted = orchestrator._format_examples_xml(examples)

        # Should escape HTML
        assert "&lt;script&gt;" in formatted or "script" not in formatted

    @pytest.mark.asyncio
    async def test_estimate_progress(self, mock_session):
        """Test progress estimation from status"""
        orchestrator = FineTuningOrchestrator(mock_session)

        progress_map = {
            "validating_files": 10,
            "queued": 20,
            "running": 50,
            "succeeded": 100,
            "failed": 0,
        }

        for status, expected in progress_map.items():
            progress = orchestrator._estimate_progress(status)
            assert progress == expected

    @pytest.mark.asyncio
    async def test_estimate_progress_unknown(self, mock_session):
        """Test progress estimation for unknown status"""
        orchestrator = FineTuningOrchestrator(mock_session)

        progress = orchestrator._estimate_progress("unknown_status")
        assert progress == 0


class TestFineTuningWithMocks:
    """Test fine-tuning with mocked APIs"""

    @pytest.mark.asyncio
    async def test_start_fine_tuning_insufficient_data(self, mock_session):
        """Test starting fine-tuning without enough data"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            orchestrator = FineTuningOrchestrator(mock_session)

            # Mock collector stats to show insufficient data
            orchestrator.collector.get_collection_stats = Mock(
                return_value={"ready_for_training": False, "total_examples": 10}
            )

            agent_id = uuid.uuid4()

            with pytest.raises(ValueError, match="Not enough training data"):
                await orchestrator.start_fine_tuning(agent_id, provider="openai")

    @pytest.mark.asyncio
    async def test_start_fine_tuning_invalid_provider(self, mock_session):
        """Test starting fine-tuning with invalid provider"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            orchestrator = FineTuningOrchestrator(mock_session)

            # Mock sufficient data
            orchestrator.collector.get_collection_stats = Mock(
                return_value={"ready_for_training": True, "total_examples": 100}
            )

            agent_id = uuid.uuid4()

            with pytest.raises(ValueError, match="Unsupported provider"):
                await orchestrator.start_fine_tuning(agent_id, provider="invalid_provider")

    @pytest.mark.asyncio
    async def test_fine_tune_local_not_implemented(self, mock_session):
        """Test local fine-tuning returns not implemented"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            orchestrator = FineTuningOrchestrator(mock_session)

            run_id = uuid.uuid4()
            agent_id = uuid.uuid4()

            result = await orchestrator._fine_tune_local(run_id, agent_id)

            assert result["status"] == "not_implemented"
            assert "alternatives" in result
