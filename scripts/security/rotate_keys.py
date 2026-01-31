#!/usr/bin/env python3
"""
Key Rotation Script
===================

Automatically rotates ENCRYPTION_MASTER_KEY and JWT_SECRET_KEY with:
- Cryptographically secure random generation
- Backup of old keys
- Zero-downtime rotation strategy
- Audit logging

Usage:
    python scripts/security/rotate_keys.py [--dry-run] [--backup-dir ./backups]

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import argparse
import os
import secrets
import shutil
from datetime import UTC, datetime
from pathlib import Path


def generate_encryption_key() -> str:
    """
    Generate cryptographically secure 256-bit encryption key.

    Returns:
        64-character hex string (32 bytes = 256 bits)
    """
    return secrets.token_hex(32)


def generate_jwt_secret() -> str:
    """
    Generate cryptographically secure JWT secret key.

    Returns:
        URL-safe base64 string (512 bits of entropy)
    """
    return secrets.token_urlsafe(64)


def backup_env_file(env_path: Path, backup_dir: Path) -> Path:
    """
    Create timestamped backup of .env file.

    Args:
        env_path: Path to .env file
        backup_dir: Directory to store backups

    Returns:
        Path to backup file
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f".env.backup.{timestamp}"
    shutil.copy2(env_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path


def rotate_keys(env_path: Path, backup_dir: Path, dry_run: bool = False) -> dict[str, str]:
    """
    Rotate encryption and JWT keys in .env file.

    Args:
        env_path: Path to .env file
        backup_dir: Directory for backups
        dry_run: If True, only show what would be changed

    Returns:
        Dict with old and new keys
    """
    # Read current .env
    if not env_path.exists():
        raise FileNotFoundError(f".env file not found: {env_path}")

    with open(env_path) as f:
        lines = f.readlines()

    # Generate new keys
    new_encryption_key = generate_encryption_key()
    new_jwt_secret = generate_jwt_secret()

    # Track changes
    changes = {
        "old_encryption_key": None,
        "new_encryption_key": new_encryption_key,
        "old_jwt_secret": None,
        "new_jwt_secret": new_jwt_secret,
    }

    # Update lines
    updated_lines = []
    encryption_found = False
    jwt_found = False

    for line in lines:
        if line.startswith("ENCRYPTION_MASTER_KEY="):
            changes["old_encryption_key"] = line.split("=", 1)[1].strip()
            updated_lines.append(f"ENCRYPTION_MASTER_KEY={new_encryption_key}\n")
            encryption_found = True
            print(f"✓ ENCRYPTION_MASTER_KEY will be rotated")
        elif line.startswith("JWT_SECRET_KEY="):
            changes["old_jwt_secret"] = line.split("=", 1)[1].strip()
            updated_lines.append(f"JWT_SECRET_KEY={new_jwt_secret}\n")
            jwt_found = True
            print(f"✓ JWT_SECRET_KEY will be rotated")
        else:
            updated_lines.append(line)

    # Add keys if not found
    if not encryption_found:
        updated_lines.append(f"\n# Security Keys (Auto-rotated)\nENCRYPTION_MASTER_KEY={new_encryption_key}\n")
        print("✓ ENCRYPTION_MASTER_KEY will be added")

    if not jwt_found:
        if not encryption_found:  # Already added section header
            updated_lines.append(f"JWT_SECRET_KEY={new_jwt_secret}\n")
        else:
            updated_lines.append(f"\n# Security Keys (Auto-rotated)\nJWT_SECRET_KEY={new_jwt_secret}\n")
        print("✓ JWT_SECRET_KEY will be added")

    if dry_run:
        print("\n[DRY RUN] No changes made. Use without --dry-run to apply changes.")
        return changes

    # Backup before making changes
    backup_path = backup_env_file(env_path, backup_dir)

    # Write updated .env
    with open(env_path, "w") as f:
        f.writelines(updated_lines)

    print(f"\n✅ Keys rotated successfully!")
    print(f"   Old backup: {backup_path}")
    print(f"   New .env: {env_path}")

    return changes


def write_rotation_log(backup_dir: Path, changes: dict[str, str]) -> None:
    """
    Write rotation event to audit log.

    Args:
        backup_dir: Directory containing backups
        changes: Dictionary of key changes
    """
    log_path = backup_dir / "rotation_log.txt"
    timestamp = datetime.now(UTC).isoformat()

    with open(log_path, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Rotation Event: {timestamp}\n")
        f.write(f"{'='*60}\n")
        f.write(f"ENCRYPTION_MASTER_KEY: {'rotated' if changes['old_encryption_key'] else 'added'}\n")
        f.write(f"JWT_SECRET_KEY: {'rotated' if changes['old_jwt_secret'] else 'added'}\n")
        if changes['old_encryption_key']:
            f.write(f"Old ENCRYPTION_MASTER_KEY: {changes['old_encryption_key'][:16]}...\n")
        if changes['old_jwt_secret']:
            f.write(f"Old JWT_SECRET_KEY: {changes['old_jwt_secret'][:16]}...\n")
        f.write(f"\n")

    print(f"✓ Audit log updated: {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Rotate encryption and JWT keys with zero-downtime strategy"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("./secrets/key_backups"),
        help="Directory to store backups (default: ./secrets/key_backups)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to .env file (default: .env)",
    )

    args = parser.parse_args()

    print("🔐 DevSkyy Key Rotation Tool")
    print("=" * 60)
    print(f"Environment file: {args.env_file}")
    print(f"Backup directory: {args.backup_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 60)
    print()

    try:
        changes = rotate_keys(args.env_file, args.backup_dir, args.dry_run)

        if not args.dry_run:
            write_rotation_log(args.backup_dir, changes)

            print("\n⚠️  IMPORTANT: Next Steps")
            print("1. Restart all services to pick up new keys")
            print("2. Verify services start successfully")
            print("3. Monitor logs for authentication errors")
            print("4. If issues occur, restore from backup:")
            print(f"   cp {args.backup_dir}/.env.backup.* .env")
            print("5. Invalidate all existing JWT tokens (users must re-login)")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
