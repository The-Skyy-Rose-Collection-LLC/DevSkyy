"""
DevSkyy Settings - Central Configuration
========================================

Loads environment variables from .env.hf and .env files.
Provides typed access to all configuration values.

This module is imported at application startup to ensure
all API keys are available before any services initialize.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# =============================================================================
# Load Environment Files (Order Matters - Later files override earlier ones)
# =============================================================================

# Find the project root (where .env.hf is located)
_PROJECT_ROOT = Path(__file__).parent.parent

# Load .env first (general config)
_env_file = _PROJECT_ROOT / ".env"
if _env_file.exists():
    load_dotenv(_env_file, override=False)

# Load .env.hf second (API keys - takes precedence)
_env_hf_file = _PROJECT_ROOT / ".env.hf"
if _env_hf_file.exists():
    load_dotenv(_env_hf_file, override=True)


# =============================================================================
# Settings Class with Validation
# =============================================================================


class DevSkyySettings(BaseSettings):
    """
    DevSkyy application settings.

    All settings can be overridden via environment variables.
    API keys are loaded from .env.hf file.
    """

    model_config = SettingsConfigDict(
        env_file=".env.hf",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # AI Provider API Keys
    # -------------------------------------------------------------------------
    ANTHROPIC_API_KEY: str = Field(default="", description="Anthropic Claude API key")
    OPENAI_API_KEY: str = Field(default="", description="OpenAI API key")
    GOOGLE_API_KEY: str = Field(default="", description="Google AI API key")
    MISTRAL_API_KEY: str = Field(default="", description="Mistral AI API key")
    COHERE_API_KEY: str = Field(default="", description="Cohere API key")
    GROQ_API_KEY: str = Field(default="", description="Groq API key")
    VERTEX_API_KEY: str = Field(default="", description="Google Vertex AI API key")

    # -------------------------------------------------------------------------
    # HuggingFace
    # -------------------------------------------------------------------------
    HF_TOKEN: str = Field(default="", description="HuggingFace Hub token")
    HUGGINGFACE_ACCESS_TOKEN: str = Field(default="", description="HuggingFace access token")

    # -------------------------------------------------------------------------
    # 3D Generation APIs
    # -------------------------------------------------------------------------
    TRIPO3D_API_KEY: str = Field(default="", description="Tripo3D API key for 3D model generation")
    MESHY_API_KEY: str = Field(default="", description="Meshy AI 3D generation API key")
    FASHN_API_KEY: str = Field(default="", description="FASHN virtual try-on API key")

    # -------------------------------------------------------------------------
    # WordPress & WooCommerce
    # -------------------------------------------------------------------------
    WOOCOMMERCE_KEY: str = Field(default="", description="WooCommerce consumer key")
    WOOCOMMERCE_SECRET: str = Field(default="", description="WooCommerce consumer secret")
    WORDPRESS_CLIENT_ID: str = Field(default="", description="WordPress.com OAuth client ID")
    WORDPRESS_CLIENT_SECRET: str = Field(
        default="", description="WordPress.com OAuth client secret"
    )

    # -------------------------------------------------------------------------
    # Stripe Payment Processing
    # -------------------------------------------------------------------------
    STRIPE_SECRET_ID: str = Field(default="", description="Stripe secret ID")
    STRIPE_SECRET_KEY: str = Field(default="", description="Stripe secret key")

    # -------------------------------------------------------------------------
    # Other Services
    # -------------------------------------------------------------------------
    LANGCHAIN_API_KEY: str = Field(default="", description="LangChain/LangSmith API key")
    CONTEXT7_API_KEY: str = Field(default="", description="Context7 documentation API key")
    ARCADE_API: str = Field(default="", description="Arcade AI API key")
    BYTEZ_MODEL_API_KEY: str = Field(default="", description="Bytez model API key")
    DEVSKYY_RENDER_API_KEY: str = Field(default="", description="Render deployment API key")
    VERCEL_OIDC_TOKEN: str = Field(default="", description="Vercel OIDC authentication token")

    # -------------------------------------------------------------------------
    # Application Settings
    # -------------------------------------------------------------------------
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    DATABASE_URL: str = Field(default="", description="PostgreSQL database URL")

    # -------------------------------------------------------------------------
    # WordPress Site Configuration
    # -------------------------------------------------------------------------
    WORDPRESS_URL: str = Field(default="https://skyyrose.co", description="WordPress site URL")
    WORDPRESS_USERNAME: str = Field(default="", description="WordPress admin username")
    WORDPRESS_APP_PASSWORD: str = Field(default="", description="WordPress application password")

    def get_hf_token(self) -> str:
        """Get the best available HuggingFace token."""
        return self.HF_TOKEN or self.HUGGINGFACE_ACCESS_TOKEN

    def get_fashn_key(self) -> str:
        """Get FASHN API key (handles typo in env file)."""
        # .env.hf has both FASHN_API_KEY and FASNH_API_KEY (typo)
        return self.FASHN_API_KEY or os.getenv("FASNH_API_KEY", "")

    def validate_required_keys(self, keys: list[str]) -> dict[str, bool]:
        """Check which required API keys are configured."""
        return {key: bool(getattr(self, key, "")) for key in keys}

    def __repr__(self) -> str:
        """Safe repr that doesn't expose secrets."""
        keys_status = []
        for key in [
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "HF_TOKEN",
            "TRIPO3D_API_KEY",
            "WOOCOMMERCE_KEY",
        ]:
            val = getattr(self, key, "")
            status = "✓" if val else "✗"
            keys_status.append(f"{key}={status}")
        return f"DevSkyySettings({', '.join(keys_status)})"


# =============================================================================
# Singleton Settings Instance
# =============================================================================


@lru_cache
def get_settings() -> DevSkyySettings:
    """Get cached settings instance (singleton pattern)."""
    return DevSkyySettings()


# Create the singleton instance
settings = get_settings()

# =============================================================================
# Direct Exports for Convenience
# =============================================================================

# AI Providers
ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
OPENAI_API_KEY = settings.OPENAI_API_KEY
GOOGLE_API_KEY = settings.GOOGLE_API_KEY
MISTRAL_API_KEY = settings.MISTRAL_API_KEY
COHERE_API_KEY = settings.COHERE_API_KEY
GROQ_API_KEY = settings.GROQ_API_KEY
VERTEX_API_KEY = settings.VERTEX_API_KEY

# HuggingFace
HF_TOKEN = settings.HF_TOKEN
HUGGINGFACE_ACCESS_TOKEN = settings.HUGGINGFACE_ACCESS_TOKEN

# 3D Generation
TRIPO3D_API_KEY = settings.TRIPO3D_API_KEY
MESHY_API_KEY = settings.MESHY_API_KEY
FASHN_API_KEY = settings.FASHN_API_KEY

# WordPress & WooCommerce
WOOCOMMERCE_KEY = settings.WOOCOMMERCE_KEY
WOOCOMMERCE_SECRET = settings.WOOCOMMERCE_SECRET
WORDPRESS_CLIENT_ID = settings.WORDPRESS_CLIENT_ID
WORDPRESS_CLIENT_SECRET = settings.WORDPRESS_CLIENT_SECRET

# Stripe
STRIPE_SECRET_ID = settings.STRIPE_SECRET_ID
STRIPE_SECRET_KEY = settings.STRIPE_SECRET_KEY

# Other Services
LANGCHAIN_API_KEY = settings.LANGCHAIN_API_KEY
CONTEXT7_API_KEY = settings.CONTEXT7_API_KEY
ARCADE_API = settings.ARCADE_API
BYTEZ_MODEL_API_KEY = settings.BYTEZ_MODEL_API_KEY
DEVSKYY_RENDER_API_KEY = settings.DEVSKYY_RENDER_API_KEY
VERCEL_OIDC_TOKEN = settings.VERCEL_OIDC_TOKEN


# =============================================================================
# Startup Validation (Optional)
# =============================================================================


def print_config_status() -> None:
    """Print configuration status for debugging."""
    print("\n" + "=" * 70)
    print("DevSkyy Configuration Status")
    print("=" * 70)

    categories = {
        "AI Providers": [
            ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
            ("OPENAI_API_KEY", OPENAI_API_KEY),
            ("GOOGLE_API_KEY", GOOGLE_API_KEY),
            ("MISTRAL_API_KEY", MISTRAL_API_KEY),
            ("COHERE_API_KEY", COHERE_API_KEY),
            ("GROQ_API_KEY", GROQ_API_KEY),
        ],
        "HuggingFace": [
            ("HF_TOKEN", HF_TOKEN),
            ("HUGGINGFACE_ACCESS_TOKEN", HUGGINGFACE_ACCESS_TOKEN),
        ],
        "3D Generation": [
            ("TRIPO3D_API_KEY", TRIPO3D_API_KEY),
            ("MESHY_API_KEY", MESHY_API_KEY),
            ("FASHN_API_KEY", FASHN_API_KEY),
        ],
        "WordPress/WooCommerce": [
            ("WOOCOMMERCE_KEY", WOOCOMMERCE_KEY),
            ("WOOCOMMERCE_SECRET", WOOCOMMERCE_SECRET),
            ("WORDPRESS_CLIENT_ID", WORDPRESS_CLIENT_ID),
        ],
        "Payments": [
            ("STRIPE_SECRET_KEY", STRIPE_SECRET_KEY),
        ],
    }

    for category, keys in categories.items():
        print(f"\n{category}:")
        for name, value in keys:
            status = "✓ Configured" if value else "✗ MISSING"
            # Show first/last 4 chars of key for verification
            preview = f"{value[:4]}...{value[-4:]}" if value and len(value) > 12 else "N/A"
            print(f"  {name:30s} {status:15s} {preview}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    print_config_status()
