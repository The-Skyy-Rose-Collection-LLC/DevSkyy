"""
Base Embedder Abstract Class

Defines interface for all image embedding models (CLIP, ResNet, etc.)
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


class BaseEmbedder(ABC):
    """Abstract base class for image embedding models."""

    def __init__(self, model_name: str, device: str = "cpu"):
        """
        Initialize embedder.

        Args:
            model_name: Name/path of the model to use
            device: Device to run model on ('cpu', 'cuda', 'mps')
        """
        self.model_name = model_name
        self.device = device
        self.model: Any = None
        self.processor: Any = None

    @abstractmethod
    def load_model(self) -> None:
        """Load the embedding model and processor."""
        pass

    @abstractmethod
    def encode_image(self, image_path: Path) -> np.ndarray:
        """
        Generate embedding vector for a single image.

        Args:
            image_path: Path to image file

        Returns:
            Embedding vector as numpy array (shape: [embedding_dim])
        """
        pass

    def encode_batch(self, image_paths: list[Path]) -> np.ndarray:
        """
        Generate embeddings for multiple images (batch processing).

        Args:
            image_paths: List of paths to image files

        Returns:
            Embedding matrix as numpy array (shape: [num_images, embedding_dim])
        """
        embeddings = []
        for image_path in image_paths:
            embedding = self.encode_image(image_path)
            embeddings.append(embedding)
        return np.array(embeddings)

    @staticmethod
    def load_image(image_path: Path) -> Image.Image:
        """
        Load and validate image file.

        Args:
            image_path: Path to image file

        Returns:
            PIL Image object (RGB mode)

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If image cannot be opened
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        try:
            image = Image.open(image_path)
            # Convert to RGB (handles RGBA, grayscale, etc.)
            if image.mode != "RGB":
                image = image.convert("RGB")
            return image
        except Exception as e:
            raise ValueError(f"Failed to load image {image_path}: {e}") from e

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """Return the dimensionality of embedding vectors."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name}, device={self.device})"
