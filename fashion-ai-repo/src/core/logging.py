"""Logging configuration and utilities."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    config_file: Optional[Path] = None,
    log_level: str = "INFO",
    log_dir: Path = Path("./logs"),
) -> None:
    """Setup logging configuration.

    Args:
        config_file: Path to logging configuration file
        log_level: Default log level if config file not provided
        log_dir: Directory for log files
    """
    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    if config_file and config_file.exists():
        logging.config.fileConfig(config_file)
    else:
        # Default configuration
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(log_dir / "application.log"),
            ],
        )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class AgentLogger:
    """Logger wrapper for agents with structured logging."""

    def __init__(self, agent_name: str, log_file: Optional[Path] = None):
        """Initialize agent logger.

        Args:
            agent_name: Name of the agent
            log_file: Optional specific log file for this agent
        """
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agents.{agent_name}")

        if log_file:
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(
                f"%(asctime)s - {agent_name} - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self.logger.info(f"[{self.agent_name}] {message}", extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message with context."""
        self.logger.error(f"[{self.agent_name}] {message}", extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context."""
        self.logger.warning(f"[{self.agent_name}] {message}", extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        self.logger.debug(f"[{self.agent_name}] {message}", extra=kwargs)
