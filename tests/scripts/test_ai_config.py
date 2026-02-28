"""Tests for AI CLI configuration."""
import os
from unittest.mock import patch

import pytest


def test_ai_config_defaults():
    from scripts.ai_config import AIConfig
    config = AIConfig()
    assert config.hf_user == "damBruh"
    assert config.base_model == "stabilityai/stable-diffusion-xl-base-1.0"
    assert config.steps == 1000
    assert config.resolution == 1024
    assert config.learning_rate == 1e-4
    assert config.trainer_space == "damBruh/skyyrose-lora-trainer"


def test_ai_config_get_hf_token_from_env():
    from scripts.ai_config import AIConfig
    config = AIConfig()
    with patch.dict(os.environ, {"HF_TOKEN": "hf_test123"}):
        assert config.get_hf_token() == "hf_test123"


def test_ai_config_get_hf_token_missing_raises():
    from scripts.ai_config import AIConfig
    config = AIConfig()
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("HF_TOKEN", None)
        with pytest.raises(ValueError, match="HF_TOKEN"):
            config.get_hf_token()


def test_ai_config_get_replicate_token():
    from scripts.ai_config import AIConfig
    config = AIConfig()
    with patch.dict(os.environ, {"REPLICATE_API_TOKEN": "r8_test456"}):
        assert config.get_replicate_token() == "r8_test456"


def test_ai_config_override():
    from scripts.ai_config import AIConfig
    config = AIConfig(steps=500, resolution=512)
    assert config.steps == 500
    assert config.resolution == 512
    assert config.hf_user == "damBruh"
