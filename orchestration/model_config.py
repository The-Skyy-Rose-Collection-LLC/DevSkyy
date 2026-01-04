"""
Model Configuration Management
==============================

Centralizes model ID selection with environment variable overrides.
Allows runtime model version updates without code changes.

Usage:
    from orchestration.model_config import get_model_id

    model_id = get_model_id("claude_sonnet", fallback="claude-3-5-sonnet-20241022")
"""

import logging
import os

logger = logging.getLogger(__name__)


# =============================================================================
# Model ID Configuration
# =============================================================================
# Maps config keys to environment variable names and fallback model IDs


MODEL_CONFIG = {
    # OpenAI Models
    "gpt4o": {
        "env_var": "MODEL_GPT4O_ID",
        "fallback": "gpt-4o",
        "description": "OpenAI GPT-4o flagship model",
    },
    "gpt4o_mini": {
        "env_var": "MODEL_GPT4O_MINI_ID",
        "fallback": "gpt-4o-mini",
        "description": "OpenAI GPT-4o Mini efficient model",
    },
    "o1_preview": {
        "env_var": "MODEL_O1_PREVIEW_ID",
        "fallback": "o1-preview",
        "description": "OpenAI o1-preview reasoning model",
    },
    "o1": {
        "env_var": "MODEL_O1_ID",
        "fallback": "o1",
        "description": "OpenAI o1 reasoning model",
    },
    # Anthropic Models
    "claude_sonnet": {
        "env_var": "MODEL_CLAUDE_SONNET_ID",
        "fallback": "claude-3-5-sonnet-20241022",
        "description": "Anthropic Claude 3.5 Sonnet",
    },
    "claude_opus": {
        "env_var": "MODEL_CLAUDE_OPUS_ID",
        "fallback": "claude-3-opus-20240229",
        "description": "Anthropic Claude 3 Opus",
    },
    "claude_haiku": {
        "env_var": "MODEL_CLAUDE_HAIKU_ID",
        "fallback": "claude-3-haiku-20240307",
        "description": "Anthropic Claude 3 Haiku",
    },
    # Google Models
    "gemini_2_flash": {
        "env_var": "MODEL_GEMINI_2_FLASH_ID",
        "fallback": "gemini-2.0-flash",
        "description": "Google Gemini 2.0 Flash",
    },
    "gemini_1_5_pro": {
        "env_var": "MODEL_GEMINI_1_5_PRO_ID",
        "fallback": "gemini-1.5-pro",
        "description": "Google Gemini 1.5 Pro (2M context)",
    },
    "gemini_1_5_flash": {
        "env_var": "MODEL_GEMINI_1_5_FLASH_ID",
        "fallback": "gemini-1.5-flash",
        "description": "Google Gemini 1.5 Flash",
    },
    # Mistral Models
    "mistral_large": {
        "env_var": "MODEL_MISTRAL_LARGE_ID",
        "fallback": "mistral-large-latest",
        "description": "Mistral Large",
    },
    "mistral_small": {
        "env_var": "MODEL_MISTRAL_SMALL_ID",
        "fallback": "mistral-small-latest",
        "description": "Mistral Small",
    },
    # Cohere Models
    "command_r": {
        "env_var": "MODEL_COMMAND_R_ID",
        "fallback": "command-r-08-2024",
        "description": "Cohere Command R",
    },
    "command_r_plus": {
        "env_var": "MODEL_COMMAND_R_PLUS_ID",
        "fallback": "command-r-plus",
        "description": "Cohere Command R+",
    },
    # Groq/Llama Models
    "llama_3_3_70b": {
        "env_var": "MODEL_LLAMA_3_3_70B_ID",
        "fallback": "llama-3.3-70b-versatile",
        "description": "Llama 3.3 70B Versatile",
    },
    "llama_3_1_70b": {
        "env_var": "MODEL_LLAMA_3_1_70B_ID",
        "fallback": "llama-3.1-70b-versatile",
        "description": "Llama 3.1 70B Versatile",
    },
    "llama_3_1_8b": {
        "env_var": "MODEL_LLAMA_3_1_8B_ID",
        "fallback": "llama-3.1-8b-instant",
        "description": "Llama 3.1 8B Instant",
    },
}


def get_model_id(config_key: str, fallback: str | None = None) -> str:
    """
    Get model ID from environment variable with fallback.

    Args:
        config_key: Key in MODEL_CONFIG (e.g., "gpt4o", "claude_sonnet")
        fallback: Optional explicit fallback (overrides config fallback)

    Returns:
        Model ID string

    Raises:
        KeyError: If config_key not found and no fallback provided

    Examples:
        >>> get_model_id("gpt4o")
        "gpt-4o"  # from environment or fallback

        >>> get_model_id("claude_sonnet", fallback="claude-3-opus")
        "claude-3-opus"  # explicit fallback takes precedence
    """
    if config_key not in MODEL_CONFIG:
        raise KeyError(
            f"Unknown model config: {config_key}. Available: {list(MODEL_CONFIG.keys())}"
        )

    config = MODEL_CONFIG[config_key]
    env_var = config["env_var"]
    default_fallback = config["fallback"]

    # Environment variable takes precedence
    env_value = os.getenv(env_var)
    if env_value:
        logger.info(f"Using {env_var} from environment: {env_value}")
        return env_value

    # Explicit fallback parameter takes precedence over config fallback
    if fallback:
        logger.debug(f"Using explicit fallback for {config_key}: {fallback}")
        return fallback

    # Use config fallback
    logger.debug(f"Using config fallback for {config_key}: {default_fallback}")
    return default_fallback


def get_all_model_ids() -> dict[str, str]:
    """
    Get all current model IDs (environment or fallback).

    Returns:
        Dict mapping config_key -> resolved model_id
    """
    result = {}
    for key in MODEL_CONFIG:
        try:
            result[key] = get_model_id(key)
        except KeyError as e:
            logger.error(f"Failed to get model ID for {key}: {e}")
    return result


def log_model_configuration() -> None:
    """Log current model configuration for debugging."""
    logger.info("=" * 80)
    logger.info("Model Configuration Status")
    logger.info("=" * 80)

    for key, config in MODEL_CONFIG.items():
        env_var = config["env_var"]
        fallback = config["fallback"]
        description = config["description"]

        env_value = os.getenv(env_var)
        current = env_value or fallback
        source = "ENVIRONMENT" if env_value else "FALLBACK"

        logger.info(f"{key:25s} | {description:40s} | {source:12s} | {current}")

    logger.info("=" * 80)


# =============================================================================
# Legacy Imports for Backward Compatibility
# =============================================================================
# These maintain compatibility with existing code that uses hard-coded model IDs


def get_claude_sonnet() -> str:
    """Get Claude Sonnet model ID (backward compatible)"""
    return get_model_id("claude_sonnet")


def get_gpt4o() -> str:
    """Get GPT-4o model ID (backward compatible)"""
    return get_model_id("gpt4o")


def get_gemini_2_flash() -> str:
    """Get Gemini 2.0 Flash model ID (backward compatible)"""
    return get_model_id("gemini_2_flash")


def get_llama_3_3_70b() -> str:
    """Get Llama 3.3 70B model ID (backward compatible)"""
    return get_model_id("llama_3_3_70b")
