"""
File validation tools — existence, JSON validity, secret detection.

Used by the ground truth validator and verification loop to check
that agent outputs reference real files and don't leak secrets.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileValidationResult:
    """Immutable validation result."""

    valid: bool
    message: str
    path: str


# Secret patterns (regex)
_SECRET_PATTERNS = [
    (r'(?:sk-proj-|sk-)[A-Za-z0-9]{20,}', "OpenAI API key"),
    (r'AIza[A-Za-z0-9_-]{35}', "Google API key"),
    (r'sk_live_[A-Za-z0-9]{24,}', "Stripe live key"),
    (r'sk_test_[A-Za-z0-9]{24,}', "Stripe test key"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub personal token"),
    (r'xai-[A-Za-z0-9]{20,}', "xAI API key"),
    (r'AKIA[A-Z0-9]{16}', "AWS access key"),
]


def validate_file_exists(path: str) -> FileValidationResult:
    """Check that a file exists on disk."""
    p = Path(path)
    if p.exists():
        return FileValidationResult(valid=True, message=f"Exists: {path}", path=path)
    return FileValidationResult(valid=False, message=f"Not found: {path}", path=path)


def validate_json_file(path: str) -> FileValidationResult:
    """Check that a file contains valid JSON."""
    p = Path(path)
    if not p.is_file():
        return FileValidationResult(valid=False, message=f"Not a file: {path}", path=path)

    try:
        json.loads(p.read_text(encoding="utf-8"))
        return FileValidationResult(valid=True, message=f"Valid JSON: {path}", path=path)
    except json.JSONDecodeError as exc:
        return FileValidationResult(
            valid=False,
            message=f"Invalid JSON in {path}: {exc}",
            path=path,
        )


def validate_no_secrets(path: str) -> FileValidationResult:
    """Scan a file for hardcoded secrets/API keys."""
    p = Path(path)
    if not p.is_file():
        return FileValidationResult(valid=False, message=f"Not a file: {path}", path=path)

    content = p.read_text(encoding="utf-8")
    found = []

    for pattern, description in _SECRET_PATTERNS:
        if re.search(pattern, content):
            found.append(description)

    if found:
        return FileValidationResult(
            valid=False,
            message=f"Secrets found in {path}: {', '.join(found)}",
            path=path,
        )
    return FileValidationResult(valid=True, message=f"No secrets in {path}", path=path)
