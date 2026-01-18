"""
DevSkyy Configuration Module
============================

Central configuration loading from .env.hf and environment variables.
Import this module early in your application to ensure all API keys are loaded.

Usage:
    from config import settings
    print(settings.ANTHROPIC_API_KEY)
    print(settings.HF_TOKEN)

Or import specific keys:
    from config import HF_TOKEN, ANTHROPIC_API_KEY
"""

from config.settings import (  # All API Keys; Settings object
    ANTHROPIC_API_KEY,
    ARCADE_API,
    BYTEZ_MODEL_API_KEY,
    COHERE_API_KEY,
    CONTEXT7_API_KEY,
    DEVSKYY_RENDER_API_KEY,
    FASHN_API_KEY,
    GOOGLE_API_KEY,
    GROQ_API_KEY,
    HF_TOKEN,
    HUGGINGFACE_ACCESS_TOKEN,
    LANGCHAIN_API_KEY,
    MESHY_API_KEY,
    MISTRAL_API_KEY,
    OPENAI_API_KEY,
    STRIPE_SECRET_ID,
    STRIPE_SECRET_KEY,
    TRIPO3D_API_KEY,
    VERCEL_OIDC_TOKEN,
    VERTEX_API_KEY,
    WOOCOMMERCE_KEY,
    WOOCOMMERCE_SECRET,
    WORDPRESS_CLIENT_ID,
    WORDPRESS_CLIENT_SECRET,
    settings,
)

__all__ = [
    "settings",
    # API Keys
    "ANTHROPIC_API_KEY",
    "ARCADE_API",
    "BYTEZ_MODEL_API_KEY",
    "COHERE_API_KEY",
    "CONTEXT7_API_KEY",
    "DEVSKYY_RENDER_API_KEY",
    "FASHN_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "HF_TOKEN",
    "HUGGINGFACE_ACCESS_TOKEN",
    "LANGCHAIN_API_KEY",
    "MESHY_API_KEY",
    "MISTRAL_API_KEY",
    "OPENAI_API_KEY",
    "STRIPE_SECRET_ID",
    "STRIPE_SECRET_KEY",
    "TRIPO3D_API_KEY",
    "VERCEL_OIDC_TOKEN",
    "VERTEX_API_KEY",
    "WOOCOMMERCE_KEY",
    "WOOCOMMERCE_SECRET",
    "WORDPRESS_CLIENT_ID",
    "WORDPRESS_CLIENT_SECRET",
]
