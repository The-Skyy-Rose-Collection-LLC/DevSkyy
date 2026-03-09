"""
Image Embedder Configuration

Controls which embedding model is used for product recognition.

Switch between models:
- CLIP: Fast, pre-trained, no training needed (default)
- ResNet: Fine-tuned on SkyyRose catalog (requires labeled dataset)

Usage:
    from image_embeddings import get_embedder

    embedder = get_embedder()  # Uses configured model
    embedding = embedder.encode_image(image_path)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .base_embedder import BaseEmbedder


@dataclass
class EmbedderConfig:
    """Configuration for image embedder selection."""

    # Model type: "clip" or "resnet"
    embedder_type: Literal["clip", "resnet"] = "clip"

    # CLIP settings
    clip_model_name: str = "openai/clip-vit-base-patch32"
    # Alternatives:
    # - "openai/clip-vit-large-patch14" (better accuracy, slower)
    # - "laion/CLIP-ViT-H-14-laion2B-s32B-b79K" (largest, best quality)

    # ResNet settings
    resnet_model_path: Path | None = None
    # Path to fine-tuned ResNet weights (if None, uses pretrained)
    # Example: Path("data/models/resnet50_skyyrose_finetuned.pth")

    resnet_use_pretrained: bool = True
    # Use ImageNet pretrained weights if resnet_model_path is None

    # Device settings
    device: str | None = None
    # Device to run on (auto-detects if None)
    # Options: "cpu", "cuda", "mps"

    def __post_init__(self):
        """Validate configuration."""
        if self.embedder_type not in ["clip", "resnet"]:
            raise ValueError(
                f"Invalid embedder_type: {self.embedder_type}. Must be 'clip' or 'resnet'."
            )

        if self.embedder_type == "resnet" and self.resnet_model_path:
            self.resnet_model_path = Path(self.resnet_model_path)
            if not self.resnet_model_path.exists():
                raise FileNotFoundError(f"ResNet model not found: {self.resnet_model_path}")


# Default configuration (CLIP active)
DEFAULT_CONFIG = EmbedderConfig(
    embedder_type="clip",
    clip_model_name="openai/clip-vit-base-patch32",
    device=None,  # Auto-detect
)


def get_embedder(config: EmbedderConfig | None = None) -> BaseEmbedder:
    """
    Get configured image embedder.

    Args:
        config: Embedder configuration (uses default if None)

    Returns:
        Initialized embedder instance (CLIP or ResNet)

    Examples:
        >>> # Use default (CLIP)
        >>> embedder = get_embedder()
        >>> embedding = embedder.encode_image(Path("product.jpg"))

        >>> # Use ResNet with custom config
        >>> config = EmbedderConfig(
        ...     embedder_type="resnet",
        ...     resnet_model_path=Path("models/resnet_skyyrose.pth")
        ... )
        >>> embedder = get_embedder(config)
    """
    if config is None:
        config = DEFAULT_CONFIG

    if config.embedder_type == "clip":
        from .clip_embedder import CLIPEmbedder

        return CLIPEmbedder(model_name=config.clip_model_name, device=config.device)

    elif config.embedder_type == "resnet":
        from .resnet_embedder import ResNetEmbedder

        return ResNetEmbedder(
            model_path=config.resnet_model_path,
            device=config.device,
            use_pretrained=config.resnet_use_pretrained,
        )

    else:
        raise ValueError(f"Unsupported embedder type: {config.embedder_type}")


# Example: Switch to fine-tuned ResNet after training
# TRAINED_RESNET_CONFIG = EmbedderConfig(
#     embedder_type="resnet",
#     resnet_model_path=Path("data/models/resnet50_skyyrose_v1.pth"),
#     device="cuda",
# )
