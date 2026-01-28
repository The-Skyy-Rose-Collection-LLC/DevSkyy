"""
WordPress client wrapper for the wordpress package.

Re-exports the integration client and provides error types.
"""

from __future__ import annotations

from integrations.wordpress_client import WordPressClient


class WordPressError(Exception):
    """WordPress API error."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


__all__ = [
    "WordPressClient",
    "WordPressError",
]
