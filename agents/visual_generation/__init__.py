"""
Gemini Native Image Generation Package
========================================

Production-ready integration of Google's Gemini native image generation models
into DevSkyy's visual generation pipeline.

Models:
- gemini-2.5-flash-image ("Nano Banana"): Fast, efficient image generation
- gemini-3-pro-image-preview ("Nano Banana Pro"): Professional quality with 4K support

Features:
- Text-to-image generation
- Multi-turn conversational editing
- Up to 14 reference images for character consistency
- SkyyRose brand DNA injection
- Advanced prompt engineering patterns

Components:
- gemini_native: Core client implementations
- prompt_optimizer: Custom prompt patterns for visual generation
- conversation_editor: Multi-turn editing session management
- reference_manager: Reference image handling for consistency

Created: 2026-01-08
Status: Phase 1 - Core Implementation
"""

from typing import TYPE_CHECKING, Any

# Version info
__version__ = "0.1.0"
__author__ = "SkyyRose LLC"
__status__ = "Development"


# Runtime imports (lazy loading for performance)
def __getattr__(name: str) -> Any:
    """Lazy load modules on attribute access."""
    if name in ("GeminiNativeImageClient", "GeminiFlashImageClient", "GeminiProImageClient"):
        from .gemini_native import (  # noqa: F401
            GeminiFlashImageClient,
            GeminiNativeImageClient,
            GeminiProImageClient,
        )

        return locals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Type checking imports
if TYPE_CHECKING:
    from .conversation_editor import (
        ChatSession,
        ConversationalImageEditor,
    )
    from .gemini_native import (
        GeminiFlashImageClient,
        GeminiNativeImageClient,
        GeminiProImageClient,
    )
    from .prompt_optimizer import (
        CollectionPromptBuilder,
        GeminiNegativePromptEngine,
        GeminiPromptOptimizer,
        GeminiTreeOfThoughtsVisual,
    )
    from .reference_manager import (
        ReferenceImageManager,
        ThoughtSignatureManager,
    )

# Public API
__all__ = [
    # Core clients
    "GeminiNativeImageClient",
    "GeminiFlashImageClient",
    "GeminiProImageClient",
    # Prompt optimization
    "GeminiPromptOptimizer",
    "GeminiTreeOfThoughtsVisual",
    "GeminiNegativePromptEngine",
    "CollectionPromptBuilder",
    # Conversational editing
    "ConversationalImageEditor",
    "ChatSession",
    # Reference management
    "ReferenceImageManager",
    "ThoughtSignatureManager",
    # Version
    "__version__",
]


def get_version() -> str:
    """Get package version."""
    return __version__


def get_supported_models() -> list[str]:
    """Get list of supported Gemini image generation models."""
    return [
        "gemini-2.5-flash-image",  # Nano Banana: Fast, efficient
        "gemini-3-pro-image-preview",  # Nano Banana Pro: Professional, 4K
    ]


def get_capabilities() -> dict[str, list[str]]:
    """Get capabilities by model."""
    return {
        "gemini-2.5-flash-image": [
            "text-to-image",
            "chat-based-editing",
            "aspect-ratio-control",
            "negative-prompting",
            "brand-dna-injection",
        ],
        "gemini-3-pro-image-preview": [
            "text-to-image",
            "chat-based-editing",
            "4k-resolution",
            "thinking-mode",
            "google-search-grounding",
            "reference-images",  # Up to 14
            "aspect-ratio-control",
            "negative-prompting",
            "brand-dna-injection",
        ],
    }
