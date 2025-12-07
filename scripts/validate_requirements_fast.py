#!/usr/bin/env python3
"""
DevSkyy Requirements Validation Script (Python version)
Fast validation of requirements files for CI/CD
"""

from pathlib import Path
import re
import sys


# ANSI color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"  # No Color

REQUIREMENTS_FILES = [
    "requirements.txt",
    "requirements-dev.txt",
    "requirements-test.txt",
    "requirements-production.txt",
    "requirements.minimal.txt",
    "requirements.vercel.txt",
    "requirements_mcp.txt",
    "requirements-luxury-automation.txt",
    "wordpress-mastery/docker/ai-services/requirements.txt",
]


def print_header(title: str):
    """Print section header"""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def check_files_exist() -> bool:
    """Check if all requirements files exist"""
    print_header("Step 1: Checking files exist...")
    all_exist = True

    for req_file in REQUIREMENTS_FILES:
        path = Path(req_file)
        if path.exists():
            print(f"{GREEN}✓{NC} Found: {req_file}")
        else:
            print(f"{RED}✗{NC} Missing: {req_file}")
            all_exist = False

    return all_exist


def parse_requirement(line: str) -> tuple[str, str, str]:
    """Parse a requirement line into (package, operator, version)"""
    line = line.strip()

    # Skip comments and empty lines
    if not line or line.startswith("#") or line.startswith("-r"):
        return None, None, None

    # Handle extras like pydantic[email]
    line_no_extras = re.sub(r"\[.*?\]", "", line)

    # Extract package name and version specifier
    match = re.match(r"^([a-zA-Z0-9_\-]+)\s*([=<>~!]+)\s*(.+)", line_no_extras)
    if match:
        package = match.group(1)
        operator = match.group(2)
        version = match.group(3).split(";")[0].strip()  # Remove platform markers
        return package.lower(), operator, version

    return None, None, None


def check_version_pinning(file_path: str) -> tuple[bool, list[str]]:
    """Check if versions are properly pinned"""
    issues = []

    with open(file_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            package, operator, version = parse_requirement(line.strip())

            if package and operator:
                # Allow >= for setuptools (build tool exception)
                if package == "setuptools" and operator == ">=":
                    continue

                # Main requirements should use ==
                if file_path == "requirements.txt" and operator != "==":
                    issues.append(f"Line {line_num}: {package} uses {operator} instead of ==")

                # Dev/test files should also use == after our refactor
                if file_path in ["requirements-dev.txt", "requirements-test.txt"]:
                    if operator != "==" and package != "setuptools":
                        issues.append(f"Line {line_num}: {package} uses {operator} instead of ==")

    return len(issues) == 0, issues


def check_duplicates(file_path: str) -> tuple[bool, list[str]]:
    """Check for duplicate package entries"""
    packages = {}
    duplicates = []

    with open(file_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            package, operator, version = parse_requirement(line.strip())

            if package:
                if package in packages:
                    duplicates.append(f"Line {line_num}: '{package}' already defined at line {packages[package]}")
                else:
                    packages[package] = line_num

    return len(duplicates) == 0, duplicates


def check_inheritance(file_path: str) -> tuple[bool, list[str]]:
    """Check if file uses proper -r inheritance where expected"""
    issues = []

    # Files that should inherit from requirements.txt
    should_inherit = ["requirements-dev.txt", "requirements-test.txt"]

    if file_path in should_inherit:
        with open(file_path, "r") as f:
            content = f.read()
            if "-r requirements.txt" not in content:
                issues.append(f"{file_path} should inherit from requirements.txt using '-r requirements.txt'")

    return len(issues) == 0, issues


def validate_all() -> int:
    """Run all validations"""
    print_header("DevSkyy Requirements Validation (Fast Mode)")
    validation_failed = 0

    # Step 1: Check files exist
    if not check_files_exist():
        validation_failed = 1

    # Step 2: Check version pinning
    print_header("Step 2: Checking version pinning standards...")
    for req_file in REQUIREMENTS_FILES:
        if Path(req_file).exists():
            success, issues = check_version_pinning(req_file)
            if success:
                print(f"{GREEN}✓{NC} {req_file} - versions properly pinned")
            else:
                print(f"{YELLOW}⚠{NC} {req_file} - pinning issues:")
                for issue in issues[:5]:  # Show first 5 issues
                    print(f"  {issue}")
                if len(issues) > 5:
                    print(f"  ... and {len(issues) - 5} more")
                # Don't fail on this, just warn

    # Step 3: Check for duplicates
    print_header("Step 3: Checking for duplicate packages...")
    for req_file in REQUIREMENTS_FILES:
        if Path(req_file).exists():
            success, duplicates = check_duplicates(req_file)
            if success:
                print(f"{GREEN}✓{NC} {req_file} - no duplicates")
            else:
                print(f"{RED}✗{NC} {req_file} - duplicates found:")
                for dup in duplicates:
                    print(f"  {dup}")
                validation_failed = 1

    # Step 4: Check inheritance
    print_header("Step 4: Checking inheritance structure...")
    for req_file in REQUIREMENTS_FILES:
        if Path(req_file).exists():
            success, issues = check_inheritance(req_file)
            if success or not issues:
                print(f"{GREEN}✓{NC} {req_file} - inheritance correct")
            else:
                print(f"{RED}✗{NC} {req_file} - inheritance issues:")
                for issue in issues:
                    print(f"  {issue}")
                validation_failed = 1

    # Final summary
    print_header("Validation Summary")
    if validation_failed == 0:
        print(f"{GREEN}✓ All validations passed!{NC}")
        return 0
    else:
        print(f"{RED}✗ Some validations failed!{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(validate_all())
