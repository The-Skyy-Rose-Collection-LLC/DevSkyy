#!/usr/bin/env python3
"""Extract all product collection ZIP files from Desktop.

Extracts:
1. Love Hurts X SkyyRose Collection.zip → Love_Hurts_Extracted/
2. Signature Collection.zip → Signature_Collection_Extracted/
"""

import sys
import zipfile
from pathlib import Path


def extract_zip(zip_path: Path, extract_dir: Path) -> bool:
    """Extract ZIP to specified directory.

    Args:
        zip_path: Path to ZIP file
        extract_dir: Target extraction directory

    Returns:
        True if successful, False otherwise
    """
    try:
        if not zip_path.exists():
            print(f"❌ Not found: {zip_path}")
            return False

        extract_dir.mkdir(exist_ok=True, parents=True)

        print(f"Extracting {zip_path.name}...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Count extracted files
        file_count = sum(1 for _ in extract_dir.rglob("*") if _.is_file())
        print(f"✓ Extracted {file_count} files → {extract_dir.name}/")
        return True

    except zipfile.BadZipFile:
        print(f"❌ Corrupted ZIP file: {zip_path}")
        return False
    except PermissionError:
        print(f"❌ Permission denied: {extract_dir}")
        return False
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return False


def main() -> int:
    """Extract all collection ZIP files."""
    desktop = Path.home() / "Desktop"

    zip_configs = [
        {
            "zip_path": desktop / "Love Hurts X SkyyRose Collection.zip",
            "extract_dir": desktop / "Love_Hurts_Extracted",
        },
        {
            "zip_path": desktop / "Signature Collection.zip",
            "extract_dir": desktop / "Signature_Collection_Extracted",
        },
    ]

    print("=" * 60)
    print("SkyyRose Collection Extractor")
    print("=" * 60 + "\n")

    success_count = 0
    for config in zip_configs:
        if extract_zip(config["zip_path"], config["extract_dir"]):
            success_count += 1
        print()

    # Summary
    print("=" * 60)
    if success_count == len(zip_configs):
        print(f"✓ All {success_count} collections extracted successfully")
        return 0
    else:
        print(
            f"⚠ {success_count}/{len(zip_configs)} collections extracted "
            f"({len(zip_configs) - success_count} failed)"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
