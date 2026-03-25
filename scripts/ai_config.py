"""AI CLI configuration and constants."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class AIConfig:
    """Central configuration for the AI CLI."""

    # HuggingFace
    hf_user: str = "damBruh"
    hf_token_env: str = "HF_TOKEN"

    # Replicate
    replicate_token_env: str = "REPLICATE_API_TOKEN"

    # Training defaults
    base_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    vae_model: str = "madebyollin/sdxl-vae-fp16-fix"
    dataset: str = "damBruh/skyyrose-lora-dataset-v5"
    output_repo: str = "damBruh/skyyrose-lora-v1"
    trigger_word: str = "skyyrose luxury fashion"

    # Training hyperparams
    steps: int = 1000
    resolution: int = 1024
    learning_rate: float = 1e-4
    batch_size: int = 1
    gradient_accumulation: int = 3
    seed: int = 0

    # Spaces
    trainer_space: str = "damBruh/skyyrose-lora-trainer"
    default_gpu: str = "t4-medium"

    def get_hf_token(self) -> str:
        """Retrieve HuggingFace token from environment."""
        token = os.environ.get(self.hf_token_env)
        if not token:
            raise ValueError(f"{self.hf_token_env} not set. Run: export HF_TOKEN=hf_...")
        return token

    def get_replicate_token(self) -> str:
        """Retrieve Replicate API token from environment."""
        token = os.environ.get(self.replicate_token_env)
        if not token:
            raise ValueError(
                f"{self.replicate_token_env} not set. Run: export REPLICATE_API_TOKEN=r8_..."
            )
        return token
