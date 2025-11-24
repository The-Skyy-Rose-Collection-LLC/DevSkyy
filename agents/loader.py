"""
Agent Configuration Loader

Loads and validates agent configurations from JSON files.
Implements caching for performance (MCP efficiency pattern).

Truth Protocol: Pydantic validation, no placeholders, explicit error handling.
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, validator


class LoaderError(Exception):
    """Base exception for configuration loading errors"""


class ConfigValidationError(LoaderError):
    """Raised when configuration validation fails"""


class ConfigNotFoundError(LoaderError):
    """Raised when configuration file is not found"""


@dataclass
class AgentCapability:
    """Represents a capability of an agent"""

    name: str
    confidence: float
    keywords: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)


class AgentConfig(BaseModel):
    """
    Validated agent configuration model

    Follows Truth Protocol: All fields validated, no optional without defaults
    """

    agent_id: str = Field(..., min_length=1, description="Unique agent identifier")
    agent_name: str = Field(..., min_length=1, description="Human-readable agent name")
    agent_type: str = Field(..., min_length=1, description="Agent type/category")
    capabilities: list[dict[str, Any]] = Field(default_factory=list, description="Agent capabilities")
    priority: int = Field(default=50, ge=0, le=100, description="Agent priority (0-100)")
    max_concurrent_tasks: int = Field(default=10, ge=1, le=1000, description="Max concurrent tasks")
    timeout_seconds: int = Field(default=300, ge=1, le=3600, description="Task timeout in seconds")
    retry_count: int = Field(default=3, ge=0, le=10, description="Number of retries on failure")
    enabled: bool = Field(default=True, description="Whether agent is enabled")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator("agent_type")
    def validate_agent_type(cls, v: str) -> str:
        """Validate agent type is not empty and follows naming convention"""
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid agent_type: {v}. Must contain only alphanumeric, underscore, or hyphen")
        return v.lower()

    @validator("capabilities")
    def validate_capabilities(cls, v: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate capabilities structure"""
        for cap in v:
            if "name" not in cap:
                raise ValueError("Each capability must have a 'name' field")
            if "confidence" in cap:
                conf = cap["confidence"]
                if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
                    raise ValueError(f"Capability confidence must be between 0.0 and 1.0, got {conf}")
        return v

    def to_capability_objects(self) -> list[AgentCapability]:
        """Convert capabilities dict to AgentCapability objects"""
        return [
            AgentCapability(
                name=cap.get("name", ""),
                confidence=cap.get("confidence", 0.5),
                keywords=cap.get("keywords", []),
                dependencies=cap.get("dependencies", []),
            )
            for cap in self.capabilities
        ]

    class Config:
        """Pydantic configuration"""

        validate_assignment = True
        extra = "forbid"  # No extra fields allowed (strict validation)


class AgentConfigLoader:
    """
    Agent configuration loader with caching

    Features:
    - JSON configuration loading
    - Pydantic validation
    - In-memory caching (MCP efficiency)
    - Comprehensive error handling

    Truth Protocol Compliant: No placeholders, explicit error handling
    """

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize loader

        Args:
            config_dir: Directory containing agent config files.
                       Defaults to ./config/agents/
        """
        self.config_dir = config_dir or Path.cwd() / "config" / "agents"
        self._cache: dict[str, AgentConfig] = {}
        self._cache_timestamps: dict[str, datetime] = {}
        self._cache_ttl_seconds = 300  # 5 minutes cache TTL

    def load_config(self, agent_id: str, force_reload: bool = False) -> AgentConfig:
        """
        Load agent configuration by ID

        Args:
            agent_id: Unique agent identifier
            force_reload: If True, bypass cache and reload from disk

        Returns:
            AgentConfig: Validated agent configuration

        Raises:
            ConfigNotFoundError: If config file not found
            ConfigValidationError: If config validation fails
            LoaderError: For other loading errors
        """
        # Check cache first (MCP efficiency pattern)
        if not force_reload and self._is_cache_valid(agent_id):
            return self._cache[agent_id]

        config_path = self.config_dir / f"{agent_id}.json"

        if not config_path.exists():
            raise ConfigNotFoundError(
                f"Configuration file not found: {config_path}. "
                f"Expected location: {self.config_dir}/{agent_id}.json"
            )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"Invalid JSON in {config_path}: {e!s}")
        except OSError as e:
            raise LoaderError(f"Error reading config file {config_path}: {e!s}")

        # Validate using Pydantic
        try:
            config = AgentConfig(**config_data)
        except ValidationError as e:
            raise ConfigValidationError(f"Configuration validation failed for {agent_id}: {e!s}")

        # Update cache
        self._cache[agent_id] = config
        self._cache_timestamps[agent_id] = datetime.now()

        return config

    def load_all_configs(self, force_reload: bool = False) -> dict[str, AgentConfig]:
        """
        Load all agent configurations from config directory

        MCP Efficiency: Batch loading with single directory scan

        Args:
            force_reload: If True, bypass cache and reload all from disk

        Returns:
            Dict mapping agent_id to AgentConfig

        Raises:
            LoaderError: If directory doesn't exist or no configs found
        """
        if not self.config_dir.exists():
            raise LoaderError(
                f"Config directory not found: {self.config_dir}. " "Create it or specify a valid directory."
            )

        configs = {}
        errors = []

        # Batch load all JSON files (MCP efficiency)
        config_files = list(self.config_dir.glob("*.json"))

        if not config_files:
            raise LoaderError(f"No configuration files found in {self.config_dir}")

        for config_file in config_files:
            agent_id = config_file.stem
            try:
                config = self.load_config(agent_id, force_reload=force_reload)
                configs[agent_id] = config
            except (ConfigNotFoundError, ConfigValidationError) as e:
                errors.append(f"{agent_id}: {e!s}")

        if errors:
            raise ConfigValidationError(f"Failed to load {len(errors)} configs:\n" + "\n".join(errors))

        return configs

    def get_enabled_agents(self) -> list[AgentConfig]:
        """
        Get all enabled agent configurations

        Returns:
            List of enabled AgentConfig objects
        """
        all_configs = self.load_all_configs()
        return [config for config in all_configs.values() if config.enabled]

    def get_agents_by_type(self, agent_type: str) -> list[AgentConfig]:
        """
        Get all agents of a specific type

        Args:
            agent_type: Agent type to filter by

        Returns:
            List of matching AgentConfig objects
        """
        all_configs = self.load_all_configs()
        return [
            config
            for config in all_configs.values()
            if config.agent_type.lower() == agent_type.lower() and config.enabled
        ]

    def clear_cache(self) -> None:
        """Clear configuration cache"""
        self._cache.clear()
        self._cache_timestamps.clear()

    def _is_cache_valid(self, agent_id: str) -> bool:
        """Check if cached config is still valid"""
        if agent_id not in self._cache:
            return False

        timestamp = self._cache_timestamps.get(agent_id)
        if not timestamp:
            return False

        age_seconds = (datetime.now() - timestamp).total_seconds()
        return age_seconds < self._cache_ttl_seconds

    def reload_config(self, agent_id: str) -> AgentConfig:
        """
        Force reload configuration from disk

        Args:
            agent_id: Agent ID to reload

        Returns:
            Reloaded AgentConfig
        """
        return self.load_config(agent_id, force_reload=True)

    def validate_config_file(self, config_path: Path) -> tuple[bool, str | None]:
        """
        Validate a configuration file without loading it into cache

        Args:
            config_path: Path to configuration file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            AgentConfig(**config_data)
            return True, None

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e!s}"
        except ValidationError as e:
            return False, f"Validation error: {e!s}"
        except Exception as e:
            return False, f"Unexpected error: {e!s}"

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_configs": len(self._cache),
            "agent_ids": list(self._cache.keys()),
            "cache_ttl_seconds": self._cache_ttl_seconds,
            "oldest_cache_age_seconds": (
                min((datetime.now() - ts).total_seconds() for ts in self._cache_timestamps.values())
                if self._cache_timestamps
                else 0
            ),
        }


# Export convenience function
def load_agent_config(agent_id: str, config_dir: Path | None = None) -> AgentConfig:
    """
    Convenience function to load a single agent config

    Args:
        agent_id: Agent ID to load
        config_dir: Optional config directory

    Returns:
        AgentConfig object
    """
    loader = AgentConfigLoader(config_dir)
    return loader.load_config(agent_id)
