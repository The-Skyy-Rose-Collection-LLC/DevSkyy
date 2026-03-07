"""
Filesystem output writer — converts LLM text output into real files.

Parses fenced code blocks with file-path annotations from agent responses
and writes them to the target directory (e.g., the WordPress theme folder).

Supported patterns:
    ```php:functions.php
    <?php // code here ?>
    ```

    ```css
    /* file: assets/css/luxury.css */
    body { background: #0A0A0A; }
    ```

    ### File: theme.json
    ```json
    { "version": 3 }
    ```

Security:
- Path traversal protection (no ../ allowed)
- Allowlisted file extensions only
- Writes to isolated output directory
- Tracks all file mutations for DIFF gate

Usage:
    writer = OutputWriter(output_dir=Path("./output/theme"))
    result = writer.extract_and_write(llm_response_text)
    print(result.files_written)  # ["functions.php", "assets/css/luxury.css"]
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Only these extensions may be written (security)
ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".php",
        ".css",
        ".js",
        ".json",
        ".html",
        ".htm",
        ".svg",
        ".txt",
        ".md",
        ".xml",
        ".map",
        ".scss",
        ".less",
        ".ts",
        ".tsx",
        ".jsx",
        ".vue",
        ".liquid",
        ".twig",
        ".hbs",
        ".yml",
        ".yaml",
        ".toml",
        ".sh",
        ".bash",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",  # for base64 decode later
    }
)

# Maximum file size (bytes) — reject absurdly large outputs
MAX_FILE_SIZE: int = 2 * 1024 * 1024  # 2 MB


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ExtractedFile:
    """A single file parsed from LLM output."""

    path: str
    content: str
    language: str


@dataclass(frozen=True)
class WriteResult:
    """Result of writing extracted files to disk."""

    files_written: tuple[str, ...]
    files_skipped: tuple[str, ...]
    errors: tuple[str, ...]
    bytes_written: int


# ---------------------------------------------------------------------------
# Extraction patterns
# ---------------------------------------------------------------------------

# Pattern 1: ```lang:path/to/file.ext
_FENCE_WITH_PATH = re.compile(
    r"```(\w+):([a-zA-Z0-9_\-./]+\.\w+)\s*\n"
    r"(.*?)"
    r"\n```",
    re.DOTALL,
)

# Pattern 2: ```lang\n/* file: path/to/file.ext */  or  // file: path/to/file.ext
_FENCE_WITH_COMMENT = re.compile(
    r"```(\w+)\s*\n"
    r"(?:/\*\s*[Ff]ile:\s*([a-zA-Z0-9_\-./]+\.\w+)\s*\*/|"
    r"//\s*[Ff]ile:\s*([a-zA-Z0-9_\-./]+\.\w+)|"
    r"#\s*[Ff]ile:\s*([a-zA-Z0-9_\-./]+\.\w+)|"
    r"<!--\s*[Ff]ile:\s*([a-zA-Z0-9_\-./]+\.\w+)\s*-->)"
    r"\s*\n"
    r"(.*?)"
    r"\n```",
    re.DOTALL,
)

# Pattern 3: ### File: path/to/file.ext\n```lang\n...\n```
_HEADING_THEN_FENCE = re.compile(
    r"#{1,4}\s*[Ff]ile:\s*([a-zA-Z0-9_\-./]+\.\w+)\s*\n+"
    r"```(\w*)\s*\n"
    r"(.*?)"
    r"\n```",
    re.DOTALL,
)

# Pattern 4: **`path/to/file.ext`**\n```lang\n...\n```
_BOLD_PATH_THEN_FENCE = re.compile(
    r"\*\*`([a-zA-Z0-9_\-./]+\.\w+)`\*\*\s*\n+"
    r"```(\w*)\s*\n"
    r"(.*?)"
    r"\n```",
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Output Writer
# ---------------------------------------------------------------------------


class OutputWriter:
    """
    Parses LLM responses for code blocks with file paths and writes them.

    Security guarantees:
    - Path traversal blocked (no ../)
    - Only allowlisted file extensions
    - Isolated to output_dir
    - All writes tracked for DIFF gate verification
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = Path(output_dir)
        self._written_files: list[str] = []

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    @property
    def written_files(self) -> list[str]:
        """All files written across all calls (for DIFF gate)."""
        return list(self._written_files)

    def reset(self) -> None:
        """Clear the written files tracker."""
        self._written_files.clear()

    # -- Extraction --

    @staticmethod
    def extract_files(content: str) -> list[ExtractedFile]:
        """
        Extract all file blocks from LLM output text.

        Tries multiple patterns in priority order. Deduplicates by path
        (last occurrence wins, matching typical LLM revision behavior).

        Args:
            content: Raw LLM response text

        Returns:
            List of ExtractedFile with path, content, and language
        """
        if not content or not content.strip():
            return []

        found: dict[str, ExtractedFile] = {}

        # Pattern 1: ```lang:path
        for match in _FENCE_WITH_PATH.finditer(content):
            lang, path, code = match.group(1), match.group(2), match.group(3)
            found[path] = ExtractedFile(path=path, content=code.strip(), language=lang)

        # Pattern 2: ```lang\n/* file: path */
        for match in _FENCE_WITH_COMMENT.finditer(content):
            lang = match.group(1)
            # Groups 2-5 are the four comment-style alternatives
            path = match.group(2) or match.group(3) or match.group(4) or match.group(5)
            code = match.group(6)
            if path:
                found[path] = ExtractedFile(path=path, content=code.strip(), language=lang)

        # Pattern 3: ### File: path\n```lang
        for match in _HEADING_THEN_FENCE.finditer(content):
            path, lang, code = match.group(1), match.group(2), match.group(3)
            found[path] = ExtractedFile(path=path, content=code.strip(), language=lang or "text")

        # Pattern 4: **`path`**\n```lang
        for match in _BOLD_PATH_THEN_FENCE.finditer(content):
            path, lang, code = match.group(1), match.group(2), match.group(3)
            found[path] = ExtractedFile(path=path, content=code.strip(), language=lang or "text")

        return list(found.values())

    # -- Validation --

    @staticmethod
    def validate_path(file_path: str) -> str | None:
        """
        Validate a file path for security. Returns error message or None if safe.

        Checks:
        - No path traversal (..)
        - Allowed extension
        - Not absolute path
        - Reasonable length
        """
        if not file_path or not file_path.strip():
            return "Empty file path"

        # Block path traversal
        if ".." in file_path:
            return f"Path traversal blocked: {file_path}"

        # Block absolute paths
        if file_path.startswith("/") or file_path.startswith("\\"):
            return f"Absolute path blocked: {file_path}"

        # Check extension
        suffix = Path(file_path).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            return f"Extension '{suffix}' not in allowlist: {file_path}"

        # Check length
        if len(file_path) > 256:
            return f"Path too long ({len(file_path)} chars): {file_path[:50]}..."

        return None

    @staticmethod
    def validate_content(content: str) -> str | None:
        """Validate file content. Returns error message or None if safe."""
        if len(content.encode("utf-8")) > MAX_FILE_SIZE:
            return f"Content exceeds {MAX_FILE_SIZE} byte limit"
        return None

    # -- Writing --

    def write_file(self, extracted: ExtractedFile) -> str | None:
        """
        Write a single extracted file to the output directory.

        Returns None on success, error message on failure.
        """
        # Validate path
        path_error = self.validate_path(extracted.path)
        if path_error:
            return path_error

        # Validate content
        content_error = self.validate_content(extracted.content)
        if content_error:
            return content_error

        # Resolve and ensure parent directory
        target = self._output_dir / extracted.path
        try:
            # Double-check resolved path is within output_dir
            resolved = target.resolve()
            output_resolved = self._output_dir.resolve()
            if not str(resolved).startswith(str(output_resolved)):
                return f"Path escape detected: {extracted.path}"

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(extracted.content, encoding="utf-8")
            self._written_files.append(extracted.path)

            logger.info(
                "OutputWriter: wrote %s (%d bytes, lang=%s)",
                extracted.path,
                len(extracted.content.encode("utf-8")),
                extracted.language,
            )
            return None

        except OSError as exc:
            return f"Write failed for {extracted.path}: {exc}"

    def extract_and_write(self, content: str) -> WriteResult:
        """
        Parse LLM output, extract all code blocks with paths, write to disk.

        This is the main entry point — call after each agent execution.

        Args:
            content: Full LLM response text

        Returns:
            WriteResult with file lists and byte count
        """
        extracted = self.extract_files(content)

        if not extracted:
            logger.debug("OutputWriter: no file blocks found in response")
            return WriteResult(
                files_written=(),
                files_skipped=(),
                errors=(),
                bytes_written=0,
            )

        written: list[str] = []
        skipped: list[str] = []
        errors: list[str] = []
        total_bytes = 0

        for file in extracted:
            error = self.write_file(file)
            if error:
                errors.append(error)
                skipped.append(file.path)
                logger.warning("OutputWriter: skipped %s — %s", file.path, error)
            else:
                written.append(file.path)
                total_bytes += len(file.content.encode("utf-8"))

        logger.info(
            "OutputWriter: %d written, %d skipped, %d errors, %d bytes total",
            len(written),
            len(skipped),
            len(errors),
            total_bytes,
        )

        return WriteResult(
            files_written=tuple(written),
            files_skipped=tuple(skipped),
            errors=tuple(errors),
            bytes_written=total_bytes,
        )
