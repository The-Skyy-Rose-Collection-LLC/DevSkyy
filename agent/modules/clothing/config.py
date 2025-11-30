"""
Configuration for 3D Clothing Asset Automation

Provides settings management for:
- Tripo3D API configuration
- FASHN API configuration
- WordPress integration settings
- Pipeline defaults

Truth Protocol Compliance:
- Rule #5: All secrets via environment variables
- Rule #7: Input validation via Pydantic
- Rule #9: Fully documented
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from agent.modules.clothing.schemas.schemas import Model3DFormat, TryOnModel


class ClothingAssetSettings(BaseSettings):
    """
    Settings for the 3D Clothing Asset automation system.

    All settings can be overridden via environment variables.
    Prefix with CLOTHING_ for namespaced configuration.

    Example:
        # Set via environment
        export TRIPO_API_KEY="your-key"
        export FASHN_API_KEY="your-key"
        export CLOTHING_DEFAULT_FORMAT="glb"
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Tripo3D Configuration
    # ==========================================================================

    tripo_api_key: str = Field(
        default="",
        description="Tripo3D API key for 3D model generation",
    )

    tripo_base_url: str = Field(
        default="https://api.tripo3d.ai/v2/openapi",
        description="Tripo3D API base URL",
    )

    tripo_timeout_seconds: float = Field(
        default=120.0,
        ge=10.0,
        le=600.0,
        description="Tripo3D request timeout in seconds",
    )

    tripo_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for Tripo3D requests",
    )

    tripo_poll_interval_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Interval between status poll requests",
    )

    tripo_max_poll_attempts: int = Field(
        default=60,
        ge=10,
        le=120,
        description="Maximum status poll attempts before timeout",
    )

    tripo_download_dir: str = Field(
        default="/tmp/tripo3d_models",
        description="Directory for downloaded 3D models",
    )

    # ==========================================================================
    # FASHN Configuration
    # ==========================================================================

    fashn_api_key: str = Field(
        default="",
        description="FASHN API key for virtual try-on",
    )

    fashn_base_url: str = Field(
        default="https://api.fashn.ai/v1",
        description="FASHN API base URL",
    )

    fashn_timeout_seconds: float = Field(
        default=120.0,
        ge=10.0,
        le=600.0,
        description="FASHN request timeout in seconds",
    )

    fashn_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for FASHN requests",
    )

    fashn_poll_interval_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="Interval between status poll requests",
    )

    fashn_download_dir: str = Field(
        default="/tmp/fashn_tryon",
        description="Directory for downloaded try-on images",
    )

    # ==========================================================================
    # WordPress Configuration
    # ==========================================================================

    wordpress_site_url: str = Field(
        default="",
        description="WordPress site URL",
    )

    wordpress_username: str = Field(
        default="",
        description="WordPress admin username",
    )

    wordpress_app_password: str = Field(
        default="",
        description="WordPress application password",
    )

    wordpress_timeout_seconds: float = Field(
        default=60.0,
        ge=10.0,
        le=300.0,
        description="WordPress upload timeout in seconds",
    )

    wordpress_max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for WordPress uploads",
    )

    # ==========================================================================
    # Pipeline Configuration
    # ==========================================================================

    default_format: str = Field(
        default="glb",
        description="Default 3D model format (glb, fbx, obj)",
    )

    default_tryon_models: str = Field(
        default="female,male",
        description="Comma-separated list of default try-on model types",
    )

    enable_3d_generation: bool = Field(
        default=True,
        description="Enable 3D model generation by default",
    )

    enable_virtual_tryon: bool = Field(
        default=True,
        description="Enable virtual try-on by default",
    )

    enable_wordpress_upload: bool = Field(
        default=True,
        description="Enable WordPress upload by default",
    )

    batch_max_concurrent: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum concurrent operations in batch processing",
    )

    batch_parallel_processing: bool = Field(
        default=True,
        description="Enable parallel processing for batches",
    )

    # ==========================================================================
    # SkyyRose Brand Configuration
    # ==========================================================================

    brand_name: str = Field(
        default="SkyyRose",
        description="Brand name for metadata",
    )

    brand_tagline: str = Field(
        default="Where Love Meets Luxury",
        description="Brand tagline for metadata",
    )

    brand_website: str = Field(
        default="https://skyyrose.co",
        description="Brand website URL",
    )

    # ==========================================================================
    # Validators
    # ==========================================================================

    @field_validator("default_format")
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate 3D model format."""
        valid_formats = {"glb", "fbx", "obj", "usdz"}
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid format: {v}. Must be one of: {valid_formats}")
        return v.lower()

    @field_validator("default_tryon_models")
    @classmethod
    def validate_tryon_models(cls, v: str) -> str:
        """Validate try-on model types."""
        valid_models = {"female", "male", "unisex"}
        models = [m.strip().lower() for m in v.split(",")]
        for model in models:
            if model not in valid_models:
                raise ValueError(f"Invalid model type: {model}. Must be one of: {valid_models}")
        return ",".join(models)

    # ==========================================================================
    # Computed Properties
    # ==========================================================================

    @property
    def model_format(self) -> Model3DFormat:
        """Get default format as enum."""
        return Model3DFormat(self.default_format)

    @property
    def tryon_model_types(self) -> list[TryOnModel]:
        """Get default try-on models as enum list."""
        return [TryOnModel(m.strip()) for m in self.default_tryon_models.split(",")]

    @property
    def has_tripo_credentials(self) -> bool:
        """Check if Tripo3D credentials are configured."""
        return bool(self.tripo_api_key)

    @property
    def has_fashn_credentials(self) -> bool:
        """Check if FASHN credentials are configured."""
        return bool(self.fashn_api_key)

    @property
    def has_wordpress_credentials(self) -> bool:
        """Check if WordPress credentials are configured."""
        return bool(
            self.wordpress_site_url
            and self.wordpress_username
            and self.wordpress_app_password
        )

    def validate_credentials(self) -> dict[str, bool]:
        """
        Validate all API credentials.

        Returns:
            dict with validation status for each service
        """
        return {
            "tripo3d": self.has_tripo_credentials,
            "fashn": self.has_fashn_credentials,
            "wordpress": self.has_wordpress_credentials,
        }


@lru_cache
def get_clothing_settings() -> ClothingAssetSettings:
    """
    Get cached settings singleton.

    Returns:
        ClothingAssetSettings: Configuration instance

    Example:
        settings = get_clothing_settings()
        if settings.has_tripo_credentials:
            # Initialize Tripo3D client
            pass
    """
    return ClothingAssetSettings()


# Export singleton for convenience
clothing_settings = get_clothing_settings()
