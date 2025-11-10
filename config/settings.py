"""
Application Settings Configuration

WHY: Centralized configuration management for environment variables
HOW: Simple class with environment variable parsing
IMPACT: Secure credential management, easy configuration across environments

Truth Protocol: All secrets from environment, no hardcoded values
"""

import os


class Settings:
    """Application settings loaded from environment variables"""

    def __init__(self):
        """Initialize settings from environment variables"""

        # WooCommerce Configuration
        self.WOOCOMMERCE_URL: str = os.getenv("WOOCOMMERCE_URL", "")
        self.WOOCOMMERCE_CONSUMER_KEY: str = os.getenv("WOOCOMMERCE_CONSUMER_KEY", "")
        self.WOOCOMMERCE_CONSUMER_SECRET: str = os.getenv("WOOCOMMERCE_CONSUMER_SECRET", "")

        # Google Configuration
        self.GOOGLE_CREDENTIALS_PATH: str = os.getenv("GOOGLE_CREDENTIALS_PATH", "")

        # Telegram Configuration
        self.TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

        # AI Providers Configuration
        self.ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

        # Service Configuration
        self.WOOCOMMERCE_BATCH_SIZE: int = int(os.getenv("WOOCOMMERCE_BATCH_SIZE", "10"))
        self.WOOCOMMERCE_MAX_RETRIES: int = int(os.getenv("WOOCOMMERCE_MAX_RETRIES", "3"))

        # AI Model Configuration
        self.ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")
        self.AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
        self.AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "500"))


# Global settings instance
settings = Settings()
