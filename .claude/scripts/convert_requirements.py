#!/usr/bin/env python3
"""
Convert requirements.txt from exact pinning (==) to compatible releases (~=).

Security-critical packages use range constraints (>=,<) to allow patch updates.
"""

import logging
from pathlib import Path
import re
import sys


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# Security-critical packages that need patch updates
SECURITY_PACKAGES = {
    "cryptography",
    "certifi",
    "setuptools",
    "requests",
    "paramiko",
    "PyJWT",
    "bcrypt",
    "argon2-cffi",
    "passlib",
    "python-jose",
    "authlib",
    "itsdangerous",
    "werkzeug",
    "starlette",
}


def convert_requirement(line: str) -> str:
    """Convert a single requirement line."""
    # Skip comments and empty lines
    if line.strip().startswith("#") or not line.strip():
        return line

    # Match package==version pattern
    match = re.match(r"^([a-zA-Z0-9_\-\[\]]+)==([0-9.]+)", line.strip())
    if not match:
        return line  # Already using ~= or >= or other format

    package_name = match.group(1)
    version = match.group(2)

    # Get base package name (without extras like [email])
    base_package = package_name.split("[")[0].lower()

    # Security-critical packages: use range constraints
    if base_package in SECURITY_PACKAGES:
        # e.g., cryptography==46.0.3 → cryptography>=46.0.3,<47.0.0
        major = version.split(".")[0]
        next_major = str(int(major) + 1)
        return line.replace(f"=={version}", f">={version},<{next_major}.0.0")

    # All other packages: use compatible release
    # e.g., fastapi==0.119.0 → fastapi~=0.119.0
    return line.replace(f"=={version}", f"~={version}")


def main() -> int:
    """Convert requirements.txt to compatible releases."""
    req_file = Path("requirements.txt")

    if not req_file.exists():
        logger.error("%s not found", req_file)
        return 1

    # Read original file
    with open(req_file, encoding="utf-8") as f:
        lines = f.readlines()

    # Convert each line
    converted_lines = [convert_requirement(line) for line in lines]

    # Write to new file (backup original)
    backup_file = Path("requirements.txt.backup")
    req_file.rename(backup_file)
    logger.info("Backed up original to %s", backup_file)

    with open(req_file, "w", encoding="utf-8") as f:
        f.writelines(converted_lines)

    logger.info("Converted %s to compatible releases", req_file)

    # Count conversions
    exact_pins = sum(1 for line in lines if "==" in line and not line.strip().startswith("#"))
    compatible = sum(1 for line in converted_lines if "~=" in line)
    ranges = sum(1 for line in converted_lines if ">=" in line and "<" in line)

    logger.info("Conversion Summary:")
    logger.info("  - Original exact pins (==): %d", exact_pins)
    logger.info("  - Compatible releases (~=): %d", compatible)
    logger.info("  - Range constraints (>=,<): %d", ranges)
    logger.info("  - Security-critical packages: %d", len(SECURITY_PACKAGES))

    return 0


if __name__ == "__main__":
    sys.exit(main())
