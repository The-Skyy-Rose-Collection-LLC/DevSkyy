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
    """
    Initialize logging for the application.
    
    Ensures the log directory exists. If a readable logging configuration file is provided, loads configuration from it; otherwise applies a default configuration that sets the level from `log_level`, logs to stdout, and writes to `application.log` inside `log_dir`.
    
    Parameters:
        config_file (Optional[Path]): Path to a logging configuration file to load (if it exists).
        log_level (str): Default logging level name used when no config file is loaded (e.g., "INFO", "DEBUG").
        log_dir (Path): Directory where the default file logger will write `application.log`.
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
        """
        Create an agent-scoped logger and optionally attach a file handler for agent-specific logs.
        
        Parameters:
            agent_name (str): Identifier used as the agent's logger namespace (logger name will be "agents.<agent_name>").
            log_file (Optional[Path]): Path to a file where this agent's logs should be written. If provided, a FileHandler with a timestamped, leveled formatter is added to the agent logger.
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
        """
        Log an informational message prefixed with the agent name.
        
        Parameters:
            message (str): The message to log.
            **kwargs: Additional context passed to the logger as the `extra` dictionary.
        """
        self.logger.info(f"[{self.agent_name}] {message}", extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """
        Log an error-level message for this agent including optional contextual fields.
        
        Parameters:
            message (str): The message to log; it will be prefixed with the agent name.
            **kwargs: Additional contextual fields to attach to the log record via the logging `extra` parameter.
        """
        self.logger.error(f"[{self.agent_name}] {message}", extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """
        Log a warning message for the agent, prefixed with the agent name.
        
        Parameters:
            message (str): The warning message to log.
            **kwargs: Additional context passed to the logger via the `extra` parameter.
        """
        self.logger.warning(f"[{self.agent_name}] {message}", extra=kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """
        Log a debug-level message for this agent, including optional structured context.
        
        Parameters:
            message (str): The message to log; it is prefixed with the agent name.
            **kwargs: Additional key-value pairs attached to the log record via the logging `extra` parameter.
        """
        self.logger.debug(f"[{self.agent_name}] {message}", extra=kwargs)