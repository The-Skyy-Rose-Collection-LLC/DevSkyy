"""
Image Embedding Modules for Visual Product Recognition

Provides multiple embedding strategies:
- CLIP: Pre-trained OpenAI model (fast, no training)
- ResNet: Fine-tuned on SkyyRose catalog (higher accuracy, requires labels)
"""

from .base_embedder import BaseEmbedder
from .clip_embedder import CLIPEmbedder
from .config import EmbedderConfig, get_embedder

__all__ = ["BaseEmbedder", "CLIPEmbedder", "EmbedderConfig", "get_embedder"]
