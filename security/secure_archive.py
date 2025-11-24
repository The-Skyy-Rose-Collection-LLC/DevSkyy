"""
Secure Archive Extraction Module

Mitigates path traversal vulnerabilities in Python tarfile (CVE-2025-4517, CVE-2025-4138).
Reference: Python Security Advisory 2025, GHSA-6429-3xgn-7wvp

Per Truth Protocol:
- Rule #1: Never guess - Uses filter='data' per PEP 706
- Rule #3: Cite Standards - CVE-2025-4517, GHSA-6429-3xgn-7wvp
- Rule #7: Input Validation - Path validation before extraction
- Rule #13: Security Baseline - Prevents symlink attacks

Author: DevSkyy Team
Version: 1.0.0
Python: >=3.11
"""

import logging
import os
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)

# Python version check for tarfile filter support (PEP 706)
PYTHON_VERSION = sys.version_info
SUPPORTS_TAR_FILTER = PYTHON_VERSION >= (3, 12) or (
    PYTHON_VERSION >= (3, 11, 4)
)


class ArchiveSecurityError(Exception):
    """Raised when archive extraction would violate security constraints."""

    pass


class SecureArchiveExtractor:
    """
    Secure archive extraction with path traversal protection.

    Mitigates:
    - CVE-2025-4517: Path traversal via tarfile
    - CVE-2025-4138: Symlink following in tarfile
    - CVE-2024-12718: Arbitrary file write via tarfile

    Features:
    - Safe path validation before extraction
    - Symlink attack prevention
    - Size limits to prevent DoS
    - Logging for audit trail
    """

    # Default limits (per Truth Protocol - configurable via env vars)
    MAX_FILE_SIZE_BYTES = int(os.getenv("ARCHIVE_MAX_FILE_SIZE", str(100 * 1024 * 1024)))  # 100MB
    MAX_TOTAL_SIZE_BYTES = int(os.getenv("ARCHIVE_MAX_TOTAL_SIZE", str(500 * 1024 * 1024)))  # 500MB
    MAX_FILE_COUNT = int(os.getenv("ARCHIVE_MAX_FILE_COUNT", "1000"))

    def __init__(
        self,
        max_file_size: int | None = None,
        max_total_size: int | None = None,
        max_file_count: int | None = None,
        allow_symlinks: bool = False,
    ):
        """
        Initialize secure archive extractor.

        Args:
            max_file_size: Maximum size per file in bytes
            max_total_size: Maximum total extraction size in bytes
            max_file_count: Maximum number of files to extract
            allow_symlinks: Whether to allow symlinks (default: False for security)
        """
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE_BYTES
        self.max_total_size = max_total_size or self.MAX_TOTAL_SIZE_BYTES
        self.max_file_count = max_file_count or self.MAX_FILE_COUNT
        self.allow_symlinks = allow_symlinks

    def _is_path_safe(self, member_path: str, dest_dir: Path) -> bool:
        """
        Check if extraction path is safe (no path traversal).

        Args:
            member_path: Path from archive member
            dest_dir: Destination directory

        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve the full path
            full_path = (dest_dir / member_path).resolve()

            # Ensure it's within destination directory
            return full_path.is_relative_to(dest_dir.resolve())
        except (ValueError, OSError):
            return False

    def _validate_tarfile_member(
        self, member: tarfile.TarInfo, dest_dir: Path
    ) -> tuple[bool, str]:
        """
        Validate a tarfile member before extraction.

        Args:
            member: TarInfo object
            dest_dir: Destination directory

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check for path traversal
        if not self._is_path_safe(member.name, dest_dir):
            return False, f"Path traversal attempt detected: {member.name}"

        # Check for absolute paths
        if member.name.startswith("/") or member.name.startswith("\\"):
            return False, f"Absolute path not allowed: {member.name}"

        # Check for symlinks (unless explicitly allowed)
        if not self.allow_symlinks and member.issym():
            return False, f"Symlink not allowed: {member.name}"

        # Check for hard links (can reference files outside extraction)
        if member.islnk():
            if not self._is_path_safe(member.linkname, dest_dir):
                return False, f"Hard link to unsafe path: {member.linkname}"

        # Check for device files (security risk)
        if member.ischr() or member.isblk():
            return False, f"Device files not allowed: {member.name}"

        # Check file size
        if member.size > self.max_file_size:
            return (
                False,
                f"File too large: {member.name} ({member.size} > {self.max_file_size})",
            )

        return True, ""

    def extract_tarfile(
        self,
        archive_path: str | Path | BinaryIO,
        dest_dir: str | Path,
        members: list[str] | None = None,
    ) -> dict:
        """
        Safely extract a tarfile with security checks.

        Args:
            archive_path: Path to tarfile or file-like object
            dest_dir: Destination directory
            members: Optional list of specific members to extract

        Returns:
            Dictionary with extraction results

        Raises:
            ArchiveSecurityError: If security violation detected
        """
        dest_dir = Path(dest_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)

        extracted_files = []
        total_size = 0
        file_count = 0

        logger.info(f"Starting secure tarfile extraction to {dest_dir}")

        try:
            with tarfile.open(archive_path, "r:*") as tar:
                # Get members to extract
                tar_members = tar.getmembers()

                if members:
                    tar_members = [m for m in tar_members if m.name in members]

                for member in tar_members:
                    # Validate member
                    is_valid, reason = self._validate_tarfile_member(member, dest_dir)
                    if not is_valid:
                        logger.warning(f"Skipping unsafe member: {reason}")
                        raise ArchiveSecurityError(reason)

                    # Check total size limit
                    if total_size + member.size > self.max_total_size:
                        raise ArchiveSecurityError(
                            f"Total extraction size exceeds limit: {self.max_total_size}"
                        )

                    # Check file count limit
                    if file_count >= self.max_file_count:
                        raise ArchiveSecurityError(
                            f"File count exceeds limit: {self.max_file_count}"
                        )

                    # Extract with filter if supported (Python 3.12+)
                    if SUPPORTS_TAR_FILTER:
                        # Use 'data' filter per PEP 706 for maximum security
                        tar.extract(member, dest_dir, filter="data")
                    else:
                        # Manual safe extraction for older Python
                        target_path = dest_dir / member.name
                        if member.isdir():
                            target_path.mkdir(parents=True, exist_ok=True)
                        elif member.isfile():
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            with tar.extractfile(member) as src:
                                if src:
                                    with open(target_path, "wb") as dst:
                                        dst.write(src.read())
                            # Restore permissions (without setuid/setgid)
                            os.chmod(target_path, member.mode & 0o0777)

                    extracted_files.append(member.name)
                    total_size += member.size
                    file_count += 1

            logger.info(
                f"Successfully extracted {file_count} files ({total_size} bytes)"
            )

            return {
                "success": True,
                "extracted_files": extracted_files,
                "file_count": file_count,
                "total_size": total_size,
                "dest_dir": str(dest_dir),
            }

        except tarfile.TarError as e:
            logger.error(f"Tarfile error: {e}")
            raise ArchiveSecurityError(f"Invalid or corrupted tarfile: {e}") from e

    def extract_zipfile(
        self,
        archive_path: str | Path | BinaryIO,
        dest_dir: str | Path,
        members: list[str] | None = None,
    ) -> dict:
        """
        Safely extract a zipfile with security checks.

        Args:
            archive_path: Path to zipfile or file-like object
            dest_dir: Destination directory
            members: Optional list of specific members to extract

        Returns:
            Dictionary with extraction results

        Raises:
            ArchiveSecurityError: If security violation detected
        """
        dest_dir = Path(dest_dir).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)

        extracted_files = []
        total_size = 0
        file_count = 0

        logger.info(f"Starting secure zipfile extraction to {dest_dir}")

        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                zip_members = zf.infolist()

                if members:
                    zip_members = [m for m in zip_members if m.filename in members]

                for member in zip_members:
                    # Check for path traversal
                    if not self._is_path_safe(member.filename, dest_dir):
                        raise ArchiveSecurityError(
                            f"Path traversal attempt: {member.filename}"
                        )

                    # Check file size
                    if member.file_size > self.max_file_size:
                        raise ArchiveSecurityError(
                            f"File too large: {member.filename} ({member.file_size})"
                        )

                    # Check total size
                    if total_size + member.file_size > self.max_total_size:
                        raise ArchiveSecurityError(
                            f"Total size exceeds limit: {self.max_total_size}"
                        )

                    # Check file count
                    if file_count >= self.max_file_count:
                        raise ArchiveSecurityError(
                            f"File count exceeds limit: {self.max_file_count}"
                        )

                    # Extract file
                    zf.extract(member, dest_dir)

                    extracted_files.append(member.filename)
                    total_size += member.file_size
                    file_count += 1

            logger.info(
                f"Successfully extracted {file_count} files ({total_size} bytes)"
            )

            return {
                "success": True,
                "extracted_files": extracted_files,
                "file_count": file_count,
                "total_size": total_size,
                "dest_dir": str(dest_dir),
            }

        except zipfile.BadZipFile as e:
            logger.error(f"Zipfile error: {e}")
            raise ArchiveSecurityError(f"Invalid or corrupted zipfile: {e}") from e


# Global instance for convenience
_secure_extractor: SecureArchiveExtractor | None = None


def get_secure_extractor() -> SecureArchiveExtractor:
    """Get global secure archive extractor instance."""
    global _secure_extractor
    if _secure_extractor is None:
        _secure_extractor = SecureArchiveExtractor()
    return _secure_extractor


def extract_tarfile_safely(
    archive_path: str | Path,
    dest_dir: str | Path,
    members: list[str] | None = None,
) -> dict:
    """
    Convenience function for safe tarfile extraction.

    Args:
        archive_path: Path to tarfile
        dest_dir: Destination directory
        members: Optional list of specific members

    Returns:
        Extraction results dictionary
    """
    return get_secure_extractor().extract_tarfile(archive_path, dest_dir, members)


def extract_zipfile_safely(
    archive_path: str | Path,
    dest_dir: str | Path,
    members: list[str] | None = None,
) -> dict:
    """
    Convenience function for safe zipfile extraction.

    Args:
        archive_path: Path to zipfile
        dest_dir: Destination directory
        members: Optional list of specific members

    Returns:
        Extraction results dictionary
    """
    return get_secure_extractor().extract_zipfile(archive_path, dest_dir, members)


__all__ = [
    "SecureArchiveExtractor",
    "ArchiveSecurityError",
    "get_secure_extractor",
    "extract_tarfile_safely",
    "extract_zipfile_safely",
]
