"""Utility functions for the Fashion AI platform."""

import json
from pathlib import Path
from typing import Any, Dict

import yaml


def ensure_directories(*paths: Path) -> None:
    """
    Ensure each given directory path exists by creating any missing directories, including parent directories.
    
    Parameters:
        *paths (Path): One or more directory paths to ensure exist.
    """
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """
    Load YAML content from the given file and return it as a dictionary.
    
    Parameters:
        file_path (Path): Path to the YAML file to read.
    
    Returns:
        Dict[str, Any]: Parsed YAML content as a dictionary.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict[str, Any], file_path: Path) -> None:
    """
    Save a mapping as YAML to the specified file.
    
    Writes the provided mapping to the target path as YAML (overwriting any existing file). The file is created if it does not exist and is written using UTF-8 encoding.
    
    Parameters:
        data (Dict[str, Any]): Mapping serializable to YAML.
        file_path (Path): Destination path for the YAML file.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False)


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load JSON content from the given file path.
    
    Returns:
        dict: Parsed JSON content as native Python objects.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: Path, indent: int = 2) -> None:
    """
    Save a dictionary to a JSON file at the specified path.
    
    Parameters:
        data (Dict[str, Any]): Dictionary to serialize to JSON.
        file_path (Path): Destination file path to write.
        indent (int): Number of spaces used for indentation in the output (default 2).
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def format_bytes(size: int) -> str:
    """
    Convert a byte count into a human-readable string with a unit suffix.
    
    Parameters:
        size (int): Number of bytes.
    
    Returns:
        str: Formatted string with two decimal places and unit (B, KB, MB, GB, TB, PB), e.g. "1.50 MB".
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def get_project_root() -> Path:
    """
    Get the project's root directory.
    
    Returns:
        Path: Path to the project's root directory.
    """
    return Path(__file__).parent.parent.parent


def validate_file_exists(file_path: Path, description: str = "File") -> None:
    """
    Ensure the specified path exists.
    
    Parameters:
        file_path (Path): Path of the file or directory to verify.
        description (str): Human-readable name used in the error message if the path is missing.
    
    Raises:
        FileNotFoundError: If the given path does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{description} not found: {file_path}")


def get_disk_usage(path: Path) -> Dict[str, Any]:
    """
    Return disk usage statistics for the filesystem containing the given path.
    
    Parameters:
        path (Path): Path located on the filesystem to inspect.
    
    Returns:
        dict: Dictionary with keys:
            - total (int): Total size in bytes.
            - used (int): Used space in bytes.
            - free (int): Free space in bytes.
            - percent (float): Percentage of used space (0 to 100).
    """
    import shutil

    usage = shutil.disk_usage(path)
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "percent": (usage.used / usage.total) * 100 if usage.total > 0 else 0,
    }