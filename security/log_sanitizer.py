"""
Log Sanitization Utilities
Prevents log injection attacks by sanitizing user input before logging
"""

import re
from typing import Any, Optional


def sanitize_for_log(value: Any, max_length: int = 200) -> str:
    """
    Sanitize a value for safe logging.

    Prevents log injection by:
    - Removing newlines and carriage returns
    - Removing ANSI escape sequences
    - Truncating long strings
    - Converting to string safely

    Args:
        value: The value to sanitize
        max_length: Maximum length of the output string

    Returns:
        Sanitized string safe for logging
    """
    if value is None:
        return "None"

    # Convert to string
    str_value = str(value)

    # Remove newlines and carriage returns
    str_value = str_value.replace("\n", " ").replace("\r", " ")

    # Remove ANSI escape sequences
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    str_value = ansi_escape.sub("", str_value)

    # Remove other control characters
    str_value = "".join(char if ord(char) >= 32 or char in ("\t",) else " " for char in str_value)

    # Truncate if too long
    if len(str_value) > max_length:
        str_value = str_value[:max_length] + "..."

    return str_value


def sanitize_user_identifier(user_id: Any) -> str:
    """
    Sanitize user identifier for logging.

    Args:
        user_id: User identifier (email, username, ID, etc.)

    Returns:
        Sanitized identifier safe for logging
    """
    return sanitize_for_log(user_id, max_length=100)


def sanitize_log_data(data: dict) -> dict:
    """
    Recursively sanitize all values in a dictionary for logging.

    Args:
        data: Dictionary with potentially unsafe values

    Returns:
        Dictionary with sanitized values
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        elif isinstance(value, (list, tuple)):
            sanitized[key] = [sanitize_for_log(item) for item in value]
        else:
            sanitized[key] = sanitize_for_log(value)
    return sanitized


class SafeLogger:
    """
    Wrapper for logger that automatically sanitizes log messages.
    """

    def __init__(self, logger):
        self.logger = logger

    def info(self, message: str, **kwargs):
        """Log info message with sanitized content."""
        safe_message = sanitize_for_log(message)
        safe_kwargs = {k: sanitize_for_log(v) for k, v in kwargs.items()}
        self.logger.info(safe_message, extra=safe_kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with sanitized content."""
        safe_message = sanitize_for_log(message)
        safe_kwargs = {k: sanitize_for_log(v) for k, v in kwargs.items()}
        self.logger.warning(safe_message, extra=safe_kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with sanitized content."""
        safe_message = sanitize_for_log(message)
        safe_kwargs = {k: sanitize_for_log(v) for k, v in kwargs.items()}
        self.logger.error(safe_message, extra=safe_kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message with sanitized content."""
        safe_message = sanitize_for_log(message)
        safe_kwargs = {k: sanitize_for_log(v) for k, v in kwargs.items()}
        self.logger.debug(safe_message, extra=safe_kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with sanitized content."""
        safe_message = sanitize_for_log(message)
        safe_kwargs = {k: sanitize_for_log(v) for k, v in kwargs.items()}
        self.logger.critical(safe_message, extra=safe_kwargs)
