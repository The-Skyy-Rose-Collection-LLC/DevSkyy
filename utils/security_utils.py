"""
Security Utilities for DevSkyy MCP Server
==========================================

Input sanitization, path validation, and security helpers.
Following OWASP Top 10 and NIST guidelines.
"""

import re
from pathlib import Path


class SecurityError(Exception):
    """Base exception for security violations."""

    pass


class PathTraversalError(SecurityError):
    """Raised when path traversal attack is detected."""

    pass


class InjectionError(SecurityError):
    """Raised when injection attack is detected."""

    pass


def sanitize_path(path_input: str, base_dir: str | None = None) -> Path:
    """
    Sanitize and validate file system paths to prevent traversal attacks.

    Args:
        path_input: User-provided path string
        base_dir: Optional base directory to restrict access

    Returns:
        Validated Path object

    Raises:
        PathTraversalError: If path traversal is detected
        ValueError: If path is invalid

    Examples:
        >>> sanitize_path("./src/main.py")
        PosixPath('src/main.py')

        >>> sanitize_path("../../../etc/passwd")  # Raises PathTraversalError
    """
    if not path_input or not isinstance(path_input, str):
        raise ValueError("Path must be a non-empty string")

    # Normalize and resolve path
    try:
        normalized = Path(path_input).resolve()
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid path: {e}")

    # Check for null bytes (injection)
    if "\x00" in path_input:
        raise InjectionError("Null byte detected in path")

    # Check for path traversal patterns
    dangerous_patterns = [
        r"\.\.",  # Parent directory
        r"~",  # Home directory expansion
        r"\$",  # Shell variable expansion
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, path_input):
            raise PathTraversalError(f"Dangerous pattern detected: {pattern}")

    # If base_dir provided, ensure path is within it
    if base_dir:
        base_path = Path(base_dir).resolve()
        try:
            normalized.relative_to(base_path)
        except ValueError:
            raise PathTraversalError(
                f"Path '{normalized}' is outside allowed directory '{base_path}'"
            )

    return normalized


def sanitize_file_types(file_types: list[str]) -> list[str]:
    """
    Validate and sanitize file type extensions.

    Args:
        file_types: List of file extensions (e.g., ['.py', '.js'])

    Returns:
        Sanitized list of extensions

    Raises:
        InjectionError: If invalid characters detected
    """
    if not file_types:
        return []

    sanitized = []
    # Allow only alphanumeric, dot, hyphen
    pattern = re.compile(r"^[\w\-\.]+$")

    for ext in file_types:
        if not isinstance(ext, str):
            continue

        ext = ext.strip()
        if not ext:
            continue

        if not pattern.match(ext):
            raise InjectionError(f"Invalid file type: {ext}")

        # Ensure starts with dot
        if not ext.startswith("."):
            ext = f".{ext}"

        sanitized.append(ext)

    return sanitized


def validate_request_params(params: dict) -> dict:
    """
    Validate and sanitize request parameters.

    Args:
        params: Dictionary of request parameters

    Returns:
        Sanitized parameters dictionary

    Raises:
        InjectionError: If dangerous content detected
    """
    if not isinstance(params, dict):
        raise ValueError("Parameters must be a dictionary")

    sanitized = {}

    for key, value in params.items():
        # Sanitize string values
        if isinstance(value, str):
            # Check for null bytes
            if "\x00" in value:
                raise InjectionError(f"Null byte in parameter '{key}'")

            # Check for script injection patterns
            dangerous_patterns = [
                r"<script",
                r"javascript:",
                r"onerror=",
                r"onload=",
            ]

            value_lower = value.lower()
            for pattern in dangerous_patterns:
                if pattern in value_lower:
                    raise InjectionError(f"Potential script injection in '{key}': {pattern}")

        sanitized[key] = value

    return sanitized
