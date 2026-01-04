"""
Training Progress Reporter Module
===================================

Real-time training progress tracking and JSON log output for HuggingFace Spaces monitoring.

This module provides:
- Live metrics tracking (epoch, loss, step, ETA)
- JSON progress files for polling
- Training status updates
- Checkpoint notifications

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = [
    "TrainingProgress",
    "TrainingStatus",
    "ProgressReporter",
    "create_progress_reporter",
]


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class TrainingProgress:
    """Current training progress metrics.

    Tracks real-time training state for monitoring dashboards.
    """

    # Status
    status: str = "idle"  # idle, preparing, training, completed, failed
    version: str = ""

    # Progress
    current_epoch: int = 0
    total_epochs: int = 0
    current_step: int = 0
    total_steps: int = 0
    progress_percentage: float = 0.0

    # Metrics
    loss: float = 0.0
    learning_rate: float = 0.0
    avg_loss: float = 0.0
    best_loss: float = float("inf")

    # Timing
    started_at: str = ""
    updated_at: str = ""
    estimated_completion: str = ""
    elapsed_seconds: float = 0.0
    remaining_seconds: float = 0.0

    # Dataset info
    total_images: int = 0
    total_products: int = 0
    collections: dict[str, int] = field(default_factory=dict)

    # Checkpoints
    latest_checkpoint: str = ""
    checkpoint_step: int = 0

    # Messages
    message: str = ""
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TrainingProgress:
        """Create from dictionary."""
        return cls(**data)


@dataclass
class TrainingStatus:
    """Training run status record.

    Permanent record of a training run for history tracking.
    """

    version: str
    status: str  # completed, failed, cancelled
    started_at: str
    completed_at: str
    total_epochs: int
    final_loss: float
    total_images: int
    total_products: int
    collections: dict[str, int] = field(default_factory=dict)
    error: str = ""
    model_path: str = ""


# =============================================================================
# Progress Reporter
# =============================================================================


class ProgressReporter:
    """Real-time training progress reporter.

    Writes progress updates to JSON files for polling by monitoring dashboards.

    Example:
        reporter = ProgressReporter(
            version="v1.1.0",
            output_dir=Path("models/training-runs/v1.1.0"),
            total_epochs=100,
            total_steps=1000,
        )

        await reporter.start()

        # During training
        await reporter.update(
            current_epoch=10,
            current_step=100,
            loss=0.5,
            learning_rate=1e-4,
        )

        await reporter.checkpoint_saved("checkpoint-500", step=500)

        await reporter.complete(final_loss=0.3)
    """

    def __init__(
        self,
        version: str,
        output_dir: Path,
        total_epochs: int,
        total_steps: int,
        total_images: int = 0,
        total_products: int = 0,
        collections: dict[str, int] | None = None,
    ):
        """Initialize progress reporter.

        Args:
            version: LoRA version being trained
            output_dir: Directory to write progress files
            total_epochs: Total number of epochs
            total_steps: Total number of steps
            total_images: Number of training images
            total_products: Number of products in dataset
            collections: Collection breakdown
        """
        self.version = version
        self.output_dir = output_dir
        self.progress_file = output_dir / "progress.json"
        self.status_file = output_dir / "status.json"

        # Initialize progress
        self.progress = TrainingProgress(
            version=version,
            total_epochs=total_epochs,
            total_steps=total_steps,
            total_images=total_images,
            total_products=total_products,
            collections=collections or {},
        )

        # Timing
        self._start_time: datetime | None = None
        self._last_update_time: datetime | None = None
        self._steps_history: list[tuple[datetime, int]] = []  # (time, step)
        self._loss_history: list[float] = []

    async def start(self, dataset_info: dict[str, Any] | None = None) -> None:
        """Start training and initialize progress tracking.

        Args:
            dataset_info: Optional dataset information to include
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._start_time = datetime.now()
        self._last_update_time = self._start_time

        self.progress.status = "training"
        self.progress.started_at = self._start_time.isoformat()
        self.progress.updated_at = self._start_time.isoformat()
        self.progress.message = f"Training started for version {self.version}"

        if dataset_info:
            self.progress.total_images = dataset_info.get(
                "total_images", self.progress.total_images
            )
            self.progress.total_products = dataset_info.get(
                "total_products", self.progress.total_products
            )
            self.progress.collections = dataset_info.get("collections", self.progress.collections)

        await self._write_progress()

        logger.info(f"Progress reporter started for {self.version}")

    async def update(
        self,
        current_epoch: int | None = None,
        current_step: int | None = None,
        loss: float | None = None,
        learning_rate: float | None = None,
        message: str | None = None,
    ) -> None:
        """Update training progress.

        Args:
            current_epoch: Current epoch number
            current_step: Current step number
            loss: Current loss value
            learning_rate: Current learning rate
            message: Optional status message
        """
        now = datetime.now()
        self._last_update_time = now

        # Update metrics
        if current_epoch is not None:
            self.progress.current_epoch = current_epoch
        if current_step is not None:
            self.progress.current_step = current_step
            self._steps_history.append((now, current_step))
        if loss is not None:
            self.progress.loss = loss
            self._loss_history.append(loss)
            self.progress.avg_loss = sum(self._loss_history) / len(self._loss_history)
            self.progress.best_loss = min(self.progress.best_loss, loss)
        if learning_rate is not None:
            self.progress.learning_rate = learning_rate
        if message is not None:
            self.progress.message = message

        # Calculate progress
        if self.progress.total_steps > 0:
            self.progress.progress_percentage = (
                self.progress.current_step / self.progress.total_steps * 100.0
            )

        # Calculate timing
        if self._start_time:
            elapsed = now - self._start_time
            self.progress.elapsed_seconds = elapsed.total_seconds()

            # Estimate remaining time based on recent progress
            if len(self._steps_history) >= 2:
                # Use last 10 steps for ETA calculation
                recent_history = self._steps_history[-10:]
                if len(recent_history) >= 2:
                    time_diff = (recent_history[-1][0] - recent_history[0][0]).total_seconds()
                    step_diff = recent_history[-1][1] - recent_history[0][1]
                    if step_diff > 0:
                        seconds_per_step = time_diff / step_diff
                        remaining_steps = self.progress.total_steps - self.progress.current_step
                        self.progress.remaining_seconds = remaining_steps * seconds_per_step

                        estimated_completion = now + timedelta(
                            seconds=self.progress.remaining_seconds
                        )
                        self.progress.estimated_completion = estimated_completion.isoformat()

        self.progress.updated_at = now.isoformat()

        # Write progress every update
        await self._write_progress()

    async def checkpoint_saved(self, checkpoint_path: str, step: int) -> None:
        """Report checkpoint saved.

        Args:
            checkpoint_path: Path to saved checkpoint
            step: Step number of checkpoint
        """
        self.progress.latest_checkpoint = checkpoint_path
        self.progress.checkpoint_step = step
        self.progress.message = f"Checkpoint saved at step {step}"

        await self._write_progress()

        logger.info(f"Checkpoint saved: {checkpoint_path} (step {step})")

    async def complete(self, final_loss: float | None = None) -> None:
        """Mark training as completed.

        Args:
            final_loss: Final training loss
        """
        now = datetime.now()

        self.progress.status = "completed"
        self.progress.updated_at = now.isoformat()
        self.progress.message = f"Training completed for version {self.version}"

        if final_loss is not None:
            self.progress.loss = final_loss

        # Calculate final timing
        if self._start_time:
            elapsed = now - self._start_time
            self.progress.elapsed_seconds = elapsed.total_seconds()
            self.progress.remaining_seconds = 0.0

        await self._write_progress()

        # Write final status
        if self._start_time:
            status = TrainingStatus(
                version=self.version,
                status="completed",
                started_at=self._start_time.isoformat(),
                completed_at=now.isoformat(),
                total_epochs=self.progress.total_epochs,
                final_loss=self.progress.loss,
                total_images=self.progress.total_images,
                total_products=self.progress.total_products,
                collections=self.progress.collections,
                model_path=str(self.output_dir),
            )
            await self._write_status(status)

        logger.info(f"Training completed: {self.version}")

    async def fail(self, error: str) -> None:
        """Mark training as failed.

        Args:
            error: Error message
        """
        now = datetime.now()

        self.progress.status = "failed"
        self.progress.error = error
        self.progress.updated_at = now.isoformat()
        self.progress.message = f"Training failed: {error}"

        await self._write_progress()

        # Write final status
        if self._start_time:
            status = TrainingStatus(
                version=self.version,
                status="failed",
                started_at=self._start_time.isoformat(),
                completed_at=now.isoformat(),
                total_epochs=self.progress.total_epochs,
                final_loss=self.progress.loss,
                total_images=self.progress.total_images,
                total_products=self.progress.total_products,
                collections=self.progress.collections,
                error=error,
            )
            await self._write_status(status)

        logger.error(f"Training failed: {error}")

    async def _write_progress(self) -> None:
        """Write progress to JSON file."""
        try:
            with open(self.progress_file, "w") as f:
                json.dump(self.progress.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write progress file: {e}")

    async def _write_status(self, status: TrainingStatus) -> None:
        """Write status to JSON file."""
        try:
            with open(self.status_file, "w") as f:
                json.dump(asdict(status), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write status file: {e}")


# =============================================================================
# Factory Function
# =============================================================================


def create_progress_reporter(
    version: str,
    base_dir: Path = Path("models/training-runs"),
    **kwargs: Any,
) -> ProgressReporter:
    """Create a progress reporter for a training run.

    Args:
        version: LoRA version being trained
        base_dir: Base directory for training runs
        **kwargs: Additional arguments for ProgressReporter

    Returns:
        Initialized ProgressReporter instance
    """
    output_dir = base_dir / version
    output_dir.mkdir(parents=True, exist_ok=True)

    return ProgressReporter(
        version=version,
        output_dir=output_dir,
        **kwargs,
    )
