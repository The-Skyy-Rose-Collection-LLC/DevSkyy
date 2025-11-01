"""Utility functions for the Fashion AI platform."""

import json
from pathlib import Path
from typing import Any, Dict

import yaml


def ensure_directories(*paths: Path) -> None:
    """Ensure directories exist, create if they don't.

    Args:
        *paths: Variable number of Path objects
    """
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load YAML file.

    Args:
        file_path: Path to YAML file

    Returns:
        Dictionary with YAML contents
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict[str, Any], file_path: Path) -> None:
    """Save data to YAML file.

    Args:
        data: Dictionary to save
        file_path: Path to save to
    """
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)


def load_json(file_path: Path) -> Dict[str, Any]:
    """Load JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary with JSON contents
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """Save data to JSON file.

    Args:
        data: Dictionary to save
        file_path: Path to save to
        indent: Indentation level
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def format_bytes(size: int) -> str:
    """Format bytes to human-readable string.

    Args:
        size: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def get_project_root() -> Path:
    """Get project root directory.

    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent.parent


def validate_file_exists(file_path: Path, description: str = "File") -> None:
    """Validate that a file exists.

    Args:
        file_path: Path to check
        description: Description of the file

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{description} not found: {file_path}")


def get_disk_usage(path: Path) -> Dict[str, Any]:
    """Get disk usage statistics for a path.

    Args:
        path: Path to check

    Returns:
        Dictionary with total, used, and free space
    """
    import shutil

    usage = shutil.disk_usage(path)
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "percent": (usage.used / usage.total) * 100 if usage.total > 0 else 0,
    }
