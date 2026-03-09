#!/usr/bin/env python3
"""Verify all critical dependencies are installed and importable.

This script checks that all required packages for DevSkyy are properly installed
and can be imported without errors.
"""

from __future__ import annotations

import sys
from importlib import import_module

# Critical dependencies for production
CRITICAL_DEPENDENCIES: dict[str, str] = {
    # Core Framework
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    # Database
    "sqlalchemy": "sqlalchemy",
    "asyncpg": "asyncpg",
    "aiosqlite": "aiosqlite",
    # Security
    "jwt": "PyJWT",
    "cryptography": "cryptography",
    "argon2": "argon2-cffi",
    # LLM Providers
    "openai": "openai",
    "anthropic": "anthropic",
    "google.genai": "google-genai",
    "cohere": "cohere",
    "mistralai": "mistralai",
    "groq": "groq",
    # ML/AI - Critical for Round Table
    "numpy": "numpy",
    "scipy": "scipy",
    "transformers": "transformers",
    "sentence_transformers": "sentence-transformers",
    "tiktoken": "tiktoken",
    "chromadb": "chromadb",
    "diffusers": "diffusers",
    # Monitoring
    "prometheus_client": "prometheus-client",
    # HTTP
    "httpx": "httpx",
    "aiohttp": "aiohttp",
}


def verify_dependency(import_name: str, package_name: str) -> tuple[bool, str]:
    """Verify a single dependency can be imported.

    Args:
        import_name: Name to use in import statement (e.g., 'numpy')
        package_name: Package name from pip (e.g., 'numpy>=2.1.3')

    Returns:
        Tuple of (success, message)
    """
    try:
        module = import_module(import_name)
        version = getattr(module, "__version__", "unknown")
        return True, f"✅ {package_name:30} (version: {version})"
    except ImportError as e:
        return False, f"❌ {package_name:30} MISSING: {e}"
    except Exception as e:
        return False, f"⚠️  {package_name:30} ERROR: {e}"


def verify_all() -> int:
    """Verify all critical dependencies.

    Returns:
        Exit code: 0 if all dependencies verified, 1 if any missing
    """
    print("=" * 70)
    print("DevSkyy Dependency Verification")
    print("=" * 70)
    print()

    results: list[tuple[bool, str]] = []
    for import_name, package_name in CRITICAL_DEPENDENCIES.items():
        success, message = verify_dependency(import_name, package_name)
        results.append((success, message))
        print(message)

    print()
    print("=" * 70)

    # Summary
    successful = sum(1 for success, _ in results if success)
    total = len(results)
    failed = total - successful

    print(f"Summary: {successful}/{total} dependencies verified")

    if failed > 0:
        print(f"\n⚠️  {failed} dependencies FAILED verification!")
        print("\nInstall missing dependencies with:")
        print("  pip install -e .")
        print("  # or")
        print("  pip install -r requirements.txt")
        return 1
    else:
        print("\n✅ All critical dependencies verified successfully!")
        print("\nPython version:", sys.version)
        print("\nRecommended: Python 3.11 or 3.12")
        print("⚠️  Python 3.14+ has compatibility issues with some dependencies")
        return 0


if __name__ == "__main__":
    sys.exit(verify_all())
