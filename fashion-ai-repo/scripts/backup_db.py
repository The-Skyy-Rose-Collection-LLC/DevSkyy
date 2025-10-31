#!/usr/bin/env python3
"""Backup database and critical data."""

import shutil
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import load_config
from src.core.utils import ensure_directories, format_bytes, save_json


def main():
    """
    Create a timestamped backup of project data and logs, write a manifest, and prune older backups.
    
    Ensures the configured backup directory exists, copies present data subdirectories ("designs", "commerce", "marketing", "finance") and the logs directory into a new timestamped backup folder, computes and records the total size in bytes, and writes a manifest.json describing the backup. After completion, removes older backups leaving the most recent seven.
    
    Returns:
        exit_code (int): `0` on successful completion.
    """
    print("Fashion AI Platform - Backup")
    print("=" * 50)

    # Load configuration
    config = load_config()

    # Ensure backup directory exists
    backup_dir = config.backup_path
    ensure_directories(backup_dir)

    # Create timestamped backup
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}"
    backup_path = backup_dir / backup_name
    backup_path.mkdir(parents=True, exist_ok=True)

    print(f"\nCreating backup: {backup_name}")

    # Backup data directories
    data_dirs = ["designs", "commerce", "marketing", "finance"]
    total_size = 0

    for dir_name in data_dirs:
        source = config.data_path / dir_name
        if source.exists():
            dest = backup_path / dir_name
            print(f"  Backing up {dir_name}...", end="")

            try:
                shutil.copytree(source, dest)
                size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
                total_size += size
                print(f" {format_bytes(size)}")
            except Exception as e:
                print(f" Error: {e}")

    # Backup logs
    log_source = config.log_path
    if log_source.exists():
        log_dest = backup_path / "logs"
        print(f"  Backing up logs...", end="")
        try:
            shutil.copytree(log_source, log_dest)
            size = sum(f.stat().st_size for f in log_dest.rglob("*") if f.is_file())
            total_size += size
            print(f" {format_bytes(size)}")
        except Exception as e:
            print(f" Error: {e}")

    # Create backup manifest
    manifest = {
        "timestamp": timestamp,
        "backup_name": backup_name,
        "total_size_bytes": total_size,
        "directories": data_dirs + ["logs"],
    }

    manifest_path = backup_path / "manifest.json"
    save_json(manifest, manifest_path)

    print(f"\nBackup complete!")
    print(f"Total size: {format_bytes(total_size)}")
    print(f"Location: {backup_path}")

    # Clean old backups (keep last 7)
    backups = sorted(backup_dir.glob("backup_*"))
    if len(backups) > 7:
        print(f"\nCleaning old backups...")
        for old_backup in backups[:-7]:
            print(f"  Removing {old_backup.name}")
            shutil.rmtree(old_backup)

    return 0


if __name__ == "__main__":
    sys.exit(main())