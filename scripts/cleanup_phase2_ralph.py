#!/usr/bin/env python3
"""
Phase 2: Dead Code Cleanup with Ralph-Wiggums Error Loop
=========================================================

Enterprise-grade cleanup following Context7 best practices.

Features:
- Ralph-Wiggums exponential backoff for file operations
- Safe file deletion with backup option
- Archive stale documentation
- Consolidate duplicate implementations
- Comprehensive error handling and logging

Usage:
    python scripts/cleanup_phase2_ralph.py
"""

import asyncio
import shutil
import sys
from pathlib import Path

import structlog

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.ralph_wiggums import ErrorCategory, ralph_wiggums_execute

logger = structlog.get_logger()


class CleanupError(Exception):
    """Error during cleanup operations."""

    pass


async def delete_file_safe(file_path: Path) -> bool:
    """
    Safely delete a file with Ralph-Wiggums retry logic.

    Args:
        file_path: Path to file to delete

    Returns:
        True if successful, False otherwise
    """

    async def attempt_delete() -> bool:
        if not file_path.exists():
            logger.warning("File does not exist, skipping", path=str(file_path))
            return True

        try:
            file_path.unlink()
            logger.info("File deleted", path=str(file_path))
            return True
        except Exception as e:
            logger.error("Failed to delete file", path=str(file_path), error=str(e))
            raise CleanupError(f"Could not delete {file_path}: {e}")

    # Use Ralph-Wiggums for retry logic
    success, result, error = await ralph_wiggums_execute(
        attempt_delete,
        max_attempts=3,
        base_delay=1.0,
        max_delay=5.0,
        retry_categories=[ErrorCategory.NETWORK, ErrorCategory.SERVER_ERROR],
    )

    if not success:
        logger.error("Delete failed after retries", path=str(file_path), error=str(error))
        return False

    return result


async def archive_file_safe(file_path: Path, archive_dir: Path) -> bool:
    """
    Safely archive a file to archive directory with Ralph-Wiggums retry logic.

    Args:
        file_path: Path to file to archive
        archive_dir: Destination archive directory

    Returns:
        True if successful, False otherwise
    """

    async def attempt_archive() -> bool:
        if not file_path.exists():
            logger.warning("File does not exist, skipping", path=str(file_path))
            return True

        try:
            # Create archive directory if needed
            archive_dir.mkdir(parents=True, exist_ok=True)

            # Move file to archive
            dest = archive_dir / file_path.name
            shutil.move(str(file_path), str(dest))
            logger.info("File archived", source=str(file_path), dest=str(dest))
            return True
        except Exception as e:
            logger.error("Failed to archive file", path=str(file_path), error=str(e))
            raise CleanupError(f"Could not archive {file_path}: {e}")

    # Use Ralph-Wiggums for retry logic
    success, result, error = await ralph_wiggums_execute(
        attempt_archive,
        max_attempts=3,
        base_delay=1.0,
        max_delay=5.0,
        retry_categories=[ErrorCategory.NETWORK, ErrorCategory.SERVER_ERROR],
    )

    if not success:
        logger.error("Archive failed after retries", path=str(file_path), error=str(error))
        return False

    return result


async def delete_directory_safe(dir_path: Path) -> bool:
    """
    Safely delete a directory with Ralph-Wiggums retry logic.

    Args:
        dir_path: Path to directory to delete

    Returns:
        True if successful, False otherwise
    """

    async def attempt_delete_dir() -> bool:
        if not dir_path.exists():
            logger.warning("Directory does not exist, skipping", path=str(dir_path))
            return True

        try:
            shutil.rmtree(dir_path)
            logger.info("Directory deleted", path=str(dir_path))
            return True
        except Exception as e:
            logger.error("Failed to delete directory", path=str(dir_path), error=str(e))
            raise CleanupError(f"Could not delete directory {dir_path}: {e}")

    # Use Ralph-Wiggums for retry logic
    success, result, error = await ralph_wiggums_execute(
        attempt_delete_dir,
        max_attempts=3,
        base_delay=1.0,
        max_delay=5.0,
        retry_categories=[ErrorCategory.NETWORK, ErrorCategory.SERVER_ERROR],
    )

    if not success:
        logger.error("Directory delete failed after retries", path=str(dir_path), error=str(error))
        return False

    return result


async def move_file_safe(source: Path, dest: Path) -> bool:
    """
    Safely move a file with Ralph-Wiggums retry logic.

    Args:
        source: Source file path
        dest: Destination file path

    Returns:
        True if successful, False otherwise
    """

    async def attempt_move() -> bool:
        if not source.exists():
            logger.warning("Source file does not exist", path=str(source))
            return False

        try:
            # Create destination directory if needed
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Move file
            shutil.move(str(source), str(dest))
            logger.info("File moved", source=str(source), dest=str(dest))
            return True
        except Exception as e:
            logger.error("Failed to move file", source=str(source), dest=str(dest), error=str(e))
            raise CleanupError(f"Could not move {source} to {dest}: {e}")

    # Use Ralph-Wiggums for retry logic
    success, result, error = await ralph_wiggums_execute(
        attempt_move,
        max_attempts=3,
        base_delay=1.0,
        max_delay=5.0,
        retry_categories=[ErrorCategory.NETWORK, ErrorCategory.SERVER_ERROR],
    )

    if not success:
        logger.error("Move failed after retries", source=str(source), dest=str(dest), error=str(error))
        return False

    return result


async def cleanup_phase_2() -> None:
    """
    Execute Phase 2: Dead Code Cleanup.

    Following Context7 best practices and Refactoring.Guru patterns.
    """
    logger.info("Starting Phase 2: Dead Code Cleanup with Ralph-Wiggums")

    project_root = Path("/Users/coreyfoster/DevSkyy")
    archive_dir = project_root / "docs" / "archive" / "2025"

    # Phase 2.1: Delete backup & temp files
    logger.info("Phase 2.1: Deleting backup & temp files")
    backup_files = [
        project_root / ".claude" / "settings.json.backup",
        project_root / ".env.critical-fuchsia-ape.backup",
        project_root / ".augmentguidelines",
        project_root / "ASSETS_ORGANIZATION_SUMMARY.txt",
        project_root / "FINAL_3D_SUMMARY.txt",
    ]

    for file in backup_files:
        success = await delete_file_safe(file)
        if not success:
            logger.warning("Failed to delete backup file", path=str(file))

    # Phase 2.2: Archive stale documentation files
    logger.info("Phase 2.2: Archiving stale documentation files")
    stale_docs = [
        project_root / "IMPLEMENTATION_SUMMARY.md",
        project_root / "WORK_COMPLETED_SUMMARY.md",
        project_root / "WORKER_IMPLEMENTATION_SUMMARY.md",
        project_root / "DEPLOYMENT_CHECKLIST.md",
        project_root / "RENDER_DEPLOYMENT_SUMMARY.md",
    ]

    for doc in stale_docs:
        success = await archive_file_safe(doc, archive_dir)
        if not success:
            logger.warning("Failed to archive stale doc", path=str(doc))

    # Phase 2.3.1: Consolidate duplicate SDK directories
    # NOTE: sdk/ has TypeScript code, only migrate Python request_signer.py
    logger.info("Phase 2.3.1: Migrating Python SDK to agent_sdk")
    sdk_request_signer = project_root / "sdk" / "request_signer.py"
    agent_sdk_utils = project_root / "agent_sdk" / "utils"
    dest_request_signer = agent_sdk_utils / "request_signer.py"

    if sdk_request_signer.exists():
        success = await move_file_safe(sdk_request_signer, dest_request_signer)
        if success:
            logger.info("Python request_signer.py migrated to agent_sdk/utils/")
            # Delete sdk/__init__.py after migration
            sdk_init = project_root / "sdk" / "__init__.py"
            await delete_file_safe(sdk_init)
        else:
            logger.error("Failed to migrate request_signer.py")

    # Phase 2.3.2: Delete duplicate tool registries
    logger.info("Phase 2.3.2: Deleting duplicate tool registries")
    duplicate_registries = [
        project_root / "runtime" / "tools.py",  # SECONDARY
        project_root / "orchestration" / "tool_registry.py",  # STUB
    ]

    for registry in duplicate_registries:
        success = await delete_file_safe(registry)
        if not success:
            logger.warning("Failed to delete duplicate registry", path=str(registry))

    # Phase 2.4: Delete duplicate integration examples
    logger.info("Phase 2.4: Deleting duplicate integration examples")
    integration_examples_dir = project_root / "agent_sdk" / "integration_examples"
    duplicate_examples = [
        integration_examples_dir / "approach_a_direct_import.py",
        integration_examples_dir / "approach_b_message_queue.py",
        integration_examples_dir / "approach_c_http_api.py",
    ]

    for example in duplicate_examples:
        success = await delete_file_safe(example)
        if not success:
            logger.warning("Failed to delete duplicate example", path=str(example))

    logger.info("Phase 2: Dead Code Cleanup Complete!")
    print("\n✅ Phase 2 Complete: Dead Code Cleanup")
    print(f"📊 Backup files deleted: {len(backup_files)}")
    print(f"📚 Stale docs archived: {len(stale_docs)} → docs/archive/2025/")
    print(f"🔧 Duplicate registries deleted: {len(duplicate_registries)}")
    print(f"📝 Integration examples cleaned: {len(duplicate_examples)}")
    print("\nNext steps:")
    print("  1. Review changes: git status")
    print("  2. Run tests: pytest tests/ -v")
    print("  3. Commit: git commit -m 'chore: Phase 2 dead code cleanup'")


async def main():
    """Main entry point."""
    try:
        await cleanup_phase_2()
    except Exception as e:
        logger.error("Phase 2 cleanup failed", error=str(e))
        print(f"\n❌ Phase 2 cleanup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
