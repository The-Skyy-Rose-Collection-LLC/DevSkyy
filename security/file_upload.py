"""
Secure File Upload Handler
===========================

File upload security with validation, scanning, and storage management.

Features:
- File type validation (whitelist-based)
- File size limits
- Malware scanning integration (placeholder)
- Safe filename generation
- Content-Type validation
- MIME type verification

Standards:
- OWASP: Secure File Upload
- CWE-434: Unrestricted Upload of File with Dangerous Type

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import secrets
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FileUploadConfig:
    """File upload security configuration."""

    # Size limits (in bytes)
    max_file_size: int = 100 * 1024 * 1024  # 100 MB default
    max_total_size: int = 10 * 1024 * 1024 * 1024  # 10 GB default

    # Allowed file types (by extension)
    allowed_extensions: set[str] = None  # type: ignore
    blocked_extensions: set[str] = None  # type: ignore

    # Allowed MIME types
    allowed_mime_types: set[str] = None  # type: ignore

    # Unsafe MIME types that could be dangerous
    dangerous_mime_types: set[str] = None  # type: ignore

    # Upload directory
    upload_dir: Path = Path("/tmp/uploads")
    secure_filename: bool = True

    def __post_init__(self) -> None:
        """Initialize defaults."""
        if self.allowed_extensions is None:
            self.allowed_extensions = {
                # Documents
                "pdf",
                "doc",
                "docx",
                "xls",
                "xlsx",
                "ppt",
                "pptx",
                "txt",
                "csv",
                "json",
                "xml",
                # Images
                "jpg",
                "jpeg",
                "png",
                "gif",
                "webp",
                "svg",
                # Archives
                "zip",
                "tar",
                "gz",
                # Media
                "mp4",
                "webm",
                "mp3",
                "wav",
            }

        if self.blocked_extensions is None:
            self.blocked_extensions = {
                # Executables
                "exe",
                "dll",
                "so",
                "dylib",
                "com",
                "msi",
                "app",
                # Scripts
                "js",
                "py",
                "rb",
                "php",
                "jsp",
                "asp",
                "sh",
                "bash",
                # System files
                "bat",
                "cmd",
                "ps1",
                "reg",
                "scr",
                "vbs",
                # Archives with unknown contents
                "rar",
                "7z",
                "iso",
            }

        if self.allowed_mime_types is None:
            self.allowed_mime_types = {
                # Documents
                "application/pdf",
                "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "text/plain",
                "text/csv",
                "application/json",
                "application/xml",
                # Images
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
                "image/svg+xml",
                # Archives
                "application/zip",
                "application/x-tar",
                "application/gzip",
            }

        if self.dangerous_mime_types is None:
            self.dangerous_mime_types = {
                # Executables
                "application/x-msdownload",
                "application/x-msdos-program",
                "application/x-executable",
                "application/x-elf",
                # Scripts
                "application/x-javascript",
                "application/x-python",
                "application/x-bash",
                "application/x-sh",
                # Dangerous office files
                "application/x-msaccess",
            }

        # Create upload directory if needed
        self.upload_dir.mkdir(parents=True, exist_ok=True)


class FileValidator:
    """Validates uploaded files."""

    def __init__(self, config: FileUploadConfig | None = None) -> None:
        """Initialize validator with configuration."""
        self.config = config or FileUploadConfig()

    def validate_filename(self, filename: str) -> bool:
        """
        Validate filename safety.

        Args:
            filename: Original filename

        Returns:
            True if filename is safe
        """
        if not filename or len(filename) == 0:
            return False

        if len(filename) > 255:  # Max filename length
            return False

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            return False

        # Check if filename contains null bytes
        return "\x00" not in filename

    def validate_extension(self, filename: str) -> bool:
        """
        Validate file extension.

        Args:
            filename: Filename to validate

        Returns:
            True if extension is allowed
        """
        if "." not in filename:
            return False

        ext = filename.rsplit(".", 1)[1].lower()

        # Check if blocked
        if ext in self.config.blocked_extensions:
            logger.warning(f"Blocked file extension: {ext}")
            return False

        # Check if allowed (if whitelist is defined)
        if self.config.allowed_extensions and ext not in self.config.allowed_extensions:
            logger.warning(f"File extension not in whitelist: {ext}")
            return False

        return True

    def validate_file_size(
        self,
        file_size: int,
        total_size: int = 0,
    ) -> bool:
        """
        Validate file and total size.

        Args:
            file_size: Size of file in bytes
            total_size: Total size of uploads in bytes

        Returns:
            True if size is acceptable
        """
        if file_size > self.config.max_file_size:
            logger.warning(f"File size exceeds limit: {file_size}")
            return False

        if total_size + file_size > self.config.max_total_size:
            logger.warning(f"Total size exceeds limit: {total_size + file_size}")
            return False

        return True

    def validate_mime_type(
        self,
        filename: str,
        content_type: str,
        file_content: bytes = b"",
    ) -> bool:
        """
        Validate MIME type.

        Args:
            filename: Filename
            content_type: Content-Type header value
            file_content: File bytes (for detection)

        Returns:
            True if MIME type is safe
        """
        # Check against dangerous MIME types
        if content_type in self.config.dangerous_mime_types:
            logger.warning(f"Dangerous MIME type: {content_type}")
            return False

        # Check against whitelist
        if content_type not in self.config.allowed_mime_types:
            logger.warning(f"MIME type not in whitelist: {content_type}")
            return False

        # Verify MIME type matches extension
        filename.rsplit(".", 1)[1].lower() if "." in filename else ""
        expected_types = mimetypes.guess_type(filename)[0]
        if expected_types and content_type not in expected_types:
            logger.warning(f"MIME type mismatch for {filename}: {content_type}")
            # Don't fail, but log warning

        return True


class FileUploader:
    """Secure file upload handler."""

    def __init__(self, config: FileUploadConfig | None = None) -> None:
        """Initialize uploader."""
        self.config = config or FileUploadConfig()
        self.validator = FileValidator(config)

    def generate_safe_filename(
        self,
        original_filename: str,
        user_id: str | None = None,
    ) -> str:
        """
        Generate a safe filename.

        Args:
            original_filename: Original filename
            user_id: User ID for organization

        Returns:
            Safe filename
        """
        # Extract extension
        ext = "" if "." not in original_filename else original_filename.rsplit(".", 1)[1].lower()

        # Generate random filename
        random_part = secrets.token_hex(16)

        filename = f"{user_id}_{random_part}" if user_id else random_part

        if ext:
            filename = f"{filename}.{ext}"

        return filename

    def validate_upload(
        self,
        filename: str,
        content_type: str,
        file_size: int,
        file_content: bytes = b"",
        total_size: int = 0,
    ) -> tuple[bool, str]:
        """
        Validate file upload.

        Args:
            filename: Original filename
            content_type: Content-Type header
            file_size: File size in bytes
            file_content: File content bytes
            total_size: Current total size of uploads

        Returns:
            Tuple of (valid: bool, error_message: str)
        """
        # Validate filename
        if not self.validator.validate_filename(filename):
            return False, "Invalid filename"

        # Validate extension
        if not self.validator.validate_extension(filename):
            return False, "File type not allowed"

        # Validate size
        if not self.validator.validate_file_size(file_size, total_size):
            return False, "File size exceeds limit"

        # Validate MIME type
        if not self.validator.validate_mime_type(filename, content_type, file_content):
            return False, "File MIME type not allowed"

        return True, ""

    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
        user_id: str | None = None,
    ) -> tuple[bool, str]:
        """
        Save uploaded file securely.

        Args:
            file_content: File content bytes
            original_filename: Original filename
            user_id: User ID

        Returns:
            Tuple of (success: bool, stored_filename: str)
        """
        try:
            # Generate safe filename
            safe_filename = self.generate_safe_filename(original_filename, user_id)

            # Create user-specific directory if needed
            if user_id:
                user_dir = self.config.upload_dir / user_id
                user_dir.mkdir(parents=True, exist_ok=True)
                file_path = user_dir / safe_filename
            else:
                file_path = self.config.upload_dir / safe_filename

            # Write file
            file_path.write_bytes(file_content)

            # Verify file was written
            if not file_path.exists():
                logger.error(f"Failed to write file: {file_path}")
                return False, ""

            logger.info(
                "File uploaded successfully",
                extra={
                    "original_filename": original_filename,
                    "stored_filename": safe_filename,
                    "user_id": user_id,
                    "file_size": len(file_content),
                },
            )

            return True, safe_filename

        except Exception as exc:
            logger.error(f"Error saving file: {exc}")
            return False, ""

    def get_file_hash(self, file_content: bytes) -> str:
        """
        Calculate file hash for integrity verification.

        Args:
            file_content: File bytes

        Returns:
            SHA-256 hash (hex-encoded)
        """
        return hashlib.sha256(file_content).hexdigest()
