"""Configuration management for Fashion AI platform."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Main configuration class."""

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_debug: bool = Field(default=False, env="API_DEBUG")
    api_secret_key: str = Field(default="change-me", env="API_SECRET_KEY")

    # Database Configuration
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT")
    db_name: str = Field(default="fashion_ai", env="DB_NAME")
    db_user: str = Field(default="fashion_user", env="DB_USER")
    db_password: str = Field(default="fashion_password", env="DB_PASSWORD")

    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # Paths
    data_path: Path = Field(default=Path("./data"), env="DATA_PATH")
    log_path: Path = Field(default=Path("./logs"), env="LOG_PATH")
    backup_path: Path = Field(default=Path("./data/backups"), env="BACKUP_PATH")

    # Queue Configuration
    queue_prefix: str = Field(default="fashion_ai", env="QUEUE_PREFIX")
    queue_timeout: int = Field(default=300, env="QUEUE_TIMEOUT")

    # ML Configuration
    ml_model_path: Path = Field(default=Path("./models"), env="ML_MODEL_PATH")
    ml_device: str = Field(default="cpu", env="ML_DEVICE")

    # Agent Configuration
    agent_log_level: str = Field(default="INFO", env="AGENT_LOG_LEVEL")
    agent_retry_attempts: int = Field(default=3, env="AGENT_RETRY_ATTEMPTS")
    agent_timeout: int = Field(default=60, env="AGENT_TIMEOUT")

    # Security
    jwt_secret_key: str = Field(default="change-me-jwt", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, env="JWT_EXPIRATION_MINUTES")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], env="CORS_ORIGINS"
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """
        Builds a PostgreSQL connection URL from the instance's database settings.
        
        Returns:
            str: Connection URL in the form "postgresql://{user}:{password}@{host}:{port}/{dbname}".
        """
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        """
        Constructs a Redis connection URL from the configured host, port, database, and optional password.
        
        Returns:
            redis_url (str): Redis connection URL. If a password is configured, the URL includes the credentials.
        """
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Create a Config instance populated from environment variables, the configured `.env` file, and module defaults.
    
    Parameters:
        config_path (Path | None): Optional path hint for a config file; currently ignored by this implementation.
    
    Returns:
        Config: A configuration object with values resolved from environment, `.env`, and the class defaults.
    """
    return Config()


def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    """
    Load and parse a YAML file into a Python dictionary.
    
    Parameters:
        file_path (Path): Path to the YAML file to read.
    
    Returns:
        dict: Parsed YAML content as a dictionary.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)