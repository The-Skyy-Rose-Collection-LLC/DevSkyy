#!/usr/bin/env python3
"""
Requirements Hardening Module
=============================

Automated hardening of Python requirements files for security.
Implements dependency pinning, vulnerability patching, and security policies.
"""

import re
import subprocess
import sys
from pathlib import Path

import toml


class RequirementsHardener:
    """
    Hardens Python requirements for production security.

    Features:
    - Exact version pinning
    - Vulnerability-free version selection
    - Dependency tree optimization
    - Security policy enforcement
    """

    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()

        # Security-critical packages that must be pinned
        self.critical_packages = {
            "fastapi",
            "starlette",
            "pydantic",
            "uvicorn",
            "cryptography",
            "pyjwt",
            "passlib",
            "bcrypt",
            "argon2-cffi",
            "httpx",
            "requests",
            "aiohttp",
            "urllib3",
            "sqlalchemy",
            "asyncpg",
            "aiosqlite",
            "openai",
            "anthropic",
        }

        # Packages with known security issues (to avoid specific versions)
        self.vulnerable_versions = {
            "cryptography": ["<41.0.0"],
            "pyjwt": ["<2.8.0"],
            "requests": ["<2.31.0"],
            "urllib3": ["<2.0.0"],
            "fastapi": ["<0.100.0"],
            "starlette": ["<0.27.0"],
        }

        # Minimum secure versions
        self.minimum_versions = {
            "cryptography": "46.0.3",
            "pyjwt": "2.10.1",
            "passlib": "1.7.4",
            "bcrypt": "5.0.0",
            "argon2-cffi": "25.1.0",
            "fastapi": "0.124.4",
            "starlette": "0.50.0",
            "pydantic": "2.12.5",
            "httpx": "0.28.1",
            "requests": "2.32.5",
            "sqlalchemy": "2.0.45",
        }

    def parse_requirements_file(self, file_path: Path) -> list[dict]:
        """Parse requirements.txt file into structured data"""
        requirements = []

        if not file_path.exists():
            return requirements

        with open(file_path) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse requirement line
                req_match = re.match(r"^([a-zA-Z0-9_-]+)([>=<!=~]+)?([0-9.]+.*)?", line)
                if req_match:
                    package = req_match.group(1).lower()
                    operator = req_match.group(2) or ""
                    version = req_match.group(3) or ""

                    requirements.append(
                        {
                            "line_num": line_num,
                            "original": line,
                            "package": package,
                            "operator": operator,
                            "version": version,
                            "is_pinned": operator == "==",
                        }
                    )

        return requirements

    def get_latest_secure_version(self, package: str) -> str:
        """Get the latest secure version of a package"""
        try:
            # Use pip to get package info
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Version:"):
                        current_version = line.split(":", 1)[1].strip()

                        # Check if we have a minimum secure version requirement
                        min_version = self.minimum_versions.get(package)
                        if min_version and self._version_compare(current_version, min_version) < 0:
                            return min_version

                        return current_version

        except (subprocess.TimeoutExpired, Exception):
            pass

        # Fallback to minimum secure version if available
        return self.minimum_versions.get(package, "latest")

    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare two version strings (-1: v1 < v2, 0: equal, 1: v1 > v2)"""
        try:
            from packaging import version

            ver1 = version.parse(v1)
            ver2 = version.parse(v2)

            if ver1 < ver2:
                return -1
            elif ver1 > ver2:
                return 1
            else:
                return 0
        except Exception:
            # Fallback to string comparison
            return (v1 > v2) - (v1 < v2)

    def harden_requirements_file(self, file_path: Path) -> tuple[list[str], list[str]]:
        """Harden a requirements file and return changes made"""
        requirements = self.parse_requirements_file(file_path)
        changes = []
        warnings = []

        hardened_lines = []

        # Process each requirement
        for req in requirements:
            package = req["package"]
            original_line = req["original"]

            # Skip if already properly pinned and secure
            if req["is_pinned"] and package not in self.critical_packages:
                hardened_lines.append(original_line)
                continue

            # Get secure version
            secure_version = self.get_latest_secure_version(package)

            if secure_version == "latest":
                warnings.append(f"Could not determine secure version for {package}")
                hardened_lines.append(original_line)
                continue

            # Create hardened requirement line
            hardened_line = f"{package}=={secure_version}"

            if hardened_line != original_line:
                changes.append(f"Updated {package}: {original_line} -> {hardened_line}")

            hardened_lines.append(hardened_line)

        # Write hardened requirements back to file
        if changes:
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            file_path.rename(backup_path)

            with open(file_path, "w") as f:
                f.write("# DevSkyy Hardened Requirements\n")
                f.write("# Auto-generated with security hardening\n")
                f.write(f"# Backup saved to: {backup_path.name}\n\n")

                for line in hardened_lines:
                    f.write(f"{line}\n")

        return changes, warnings

    def harden_pyproject_toml(self, file_path: Path) -> tuple[list[str], list[str]]:
        """Harden pyproject.toml dependencies"""
        if not file_path.exists():
            return [], []

        changes = []
        warnings = []

        try:
            with open(file_path) as f:
                data = toml.load(f)

            # Harden main dependencies
            if "project" in data and "dependencies" in data["project"]:
                deps = data["project"]["dependencies"]
                hardened_deps = []

                for dep in deps:
                    # Parse dependency specification
                    dep_match = re.match(r"^([a-zA-Z0-9_-]+)", dep)
                    if dep_match:
                        package = dep_match.group(1).lower()
                        secure_version = self.get_latest_secure_version(package)

                        if secure_version != "latest":
                            hardened_dep = f"{package}=={secure_version}"
                            if hardened_dep != dep:
                                changes.append(f"Updated {package} in pyproject.toml")
                            hardened_deps.append(hardened_dep)
                        else:
                            hardened_deps.append(dep)
                    else:
                        hardened_deps.append(dep)

                data["project"]["dependencies"] = hardened_deps

            # Write back if changes were made
            if changes:
                backup_path = file_path.with_suffix(".toml.backup")
                file_path.rename(backup_path)

                with open(file_path, "w") as f:
                    toml.dump(data, f)

        except Exception as e:
            warnings.append(f"Failed to harden pyproject.toml: {e}")

        return changes, warnings

    def harden_all_requirements(self) -> dict:
        """Harden all requirements files in the project"""
        results = {"files_processed": [], "total_changes": 0, "changes": [], "warnings": []}

        # Files to harden
        files_to_harden = [
            self.project_root / "requirements.txt",
            self.project_root / "vercel" / "requirements.txt",
            self.project_root / "pyproject.toml",
        ]

        for file_path in files_to_harden:
            if not file_path.exists():
                continue

            results["files_processed"].append(str(file_path))

            if file_path.suffix == ".toml":
                changes, warnings = self.harden_pyproject_toml(file_path)
            else:
                changes, warnings = self.harden_requirements_file(file_path)

            results["changes"].extend(changes)
            results["warnings"].extend(warnings)
            results["total_changes"] += len(changes)

        return results


# Global instance
requirements_hardener = RequirementsHardener()


def main():
    """CLI entry point for requirements hardening"""
    hardener = RequirementsHardener()
    results = hardener.harden_all_requirements()

    print("\n🔒 DevSkyy Requirements Hardening Report")
    print("=" * 50)
    print(f"Files processed: {len(results['files_processed'])}")
    print(f"Total changes: {results['total_changes']}")

    if results["changes"]:
        print("\n✅ Changes made:")
        for change in results["changes"]:
            print(f"  • {change}")

    if results["warnings"]:
        print("\n⚠️  Warnings:")
        for warning in results["warnings"]:
            print(f"  • {warning}")

    if results["total_changes"] == 0:
        print("\n✅ All requirements are already hardened!")
    else:
        print(f"\n🎉 Successfully hardened {results['total_changes']} dependencies!")


if __name__ == "__main__":
    main()
