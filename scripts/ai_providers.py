"""Training providers for AI CLI — HuggingFace and Replicate."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Iterator

from scripts.ai_config import AIConfig

# Module-level imports for patchability.
# These are optional dependencies; they are imported eagerly so that
# unittest.mock.patch("scripts.ai_providers.replicate") can find the
# attribute.  If the library is not installed (or broken on this
# Python version), we set a sentinel that will produce a clear error
# at *call* time rather than *import* time.

try:
    import replicate
except Exception:  # noqa: BLE001
    replicate: Any = None  # type: ignore[no-redef]

try:
    from gradio_client import Client
except Exception:  # noqa: BLE001
    Client: Any = None  # type: ignore[no-redef]

try:
    from huggingface_hub import HfApi
except Exception:  # noqa: BLE001
    HfApi: Any = None  # type: ignore[no-redef]


class TrainingProvider(ABC):
    """Abstract base for training compute providers."""

    @abstractmethod
    def start_training(self, config: AIConfig) -> str:
        """Start training, return job ID."""

    @abstractmethod
    def get_status(self, job_id: str) -> dict:
        """Return {status, progress, logs, hardware}."""

    @abstractmethod
    def get_logs(self, job_id: str) -> Iterator[str]:
        """Stream training log lines."""


class ReplicateProvider(TrainingProvider):
    """Fast A100 training via Replicate API."""

    def start_training(self, config: AIConfig) -> str:
        os.environ["REPLICATE_API_TOKEN"] = config.get_replicate_token()

        training = replicate.trainings.create(
            model="stability-ai/sdxl",
            version="39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "input_images": f"https://huggingface.co/datasets/{config.dataset}/resolve/main/data.zip",
                "token_string": "TOK",
                "caption_prefix": f"{config.trigger_word} ",
                "max_train_steps": config.steps,
                "use_face_detection_instead": False,
                "resolution": config.resolution,
                "seed": config.seed,
            },
            destination=f"{config.hf_user}/skyyrose-lora-replicate",
        )
        return training.id

    def get_status(self, job_id: str) -> dict:
        training = replicate.trainings.get(job_id)
        return {
            "status": training.status,
            "logs": training.logs or "",
        }

    def get_logs(self, job_id: str) -> Iterator[str]:
        training = replicate.trainings.get(job_id)
        if training.logs:
            yield from training.logs.splitlines()


class HuggingFaceProvider(TrainingProvider):
    """Managed training via HF Spaces + gradio_client."""

    def start_training(self, config: AIConfig) -> str:
        token = config.get_hf_token()
        api = HfApi(token=token)

        runtime = api.get_space_runtime(config.trainer_space)
        if runtime.stage != "RUNNING":
            api.restart_space(config.trainer_space)

        client = Client(config.trainer_space, hf_token=token)
        client.predict(api_name="/predict")

        return config.trainer_space

    def get_status(self, job_id: str) -> dict:
        token = os.environ.get("HF_TOKEN", "")
        api = HfApi(token=token)
        runtime = api.get_space_runtime(job_id)

        return {
            "status": runtime.stage,
            "hardware": getattr(runtime, "hardware", "unknown"),
        }

    def get_logs(self, job_id: str) -> Iterator[str]:
        token = os.environ.get("HF_TOKEN", "")
        api = HfApi(token=token)

        for log_entry in api.get_space_runtime(job_id).raw.get("logs", []):
            yield log_entry


PROVIDERS: dict[str, TrainingProvider] = {
    "replicate": ReplicateProvider(),
    "hf": HuggingFaceProvider(),
}
