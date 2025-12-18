#!/usr/bin/env python3
"""
DevSkyy - Environment Variables Verification Script
====================================================

Verifies that environment variables are properly configured.

Usage:
    python scripts/verify_env.py
"""

import os
import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()


def check_env_var(var_name: str, required: bool = True) -> tuple[bool, str]:
    """
    Check if an environment variable is set.

    Returns:
        Tuple of (is_set, value_or_message)
    """
    value = os.getenv(var_name)
    if value:
        # Don't show full value for security
        return True, f"Set ({len(value)} chars)"
    else:
        return False, "Not set" + (" (REQUIRED)" if required else " (optional)")


def main():
    print("=" * 80)
    print("DevSkyy Environment Variables Verification")
    print("=" * 80)
    print()

    # Check if .env file exists
    print("📁 File Check:")
    env_exists = check_file_exists(".env")
    env_example_exists = check_file_exists(".env.example")

    print(f"   .env file: {'✓ Found' if env_exists else '✗ Missing'}")
    print(f"   .env.example file: {'✓ Found' if env_example_exists else '✗ Missing'}")

    if not env_exists:
        print()
        print("❌ ERROR: .env file not found!")
        print()
        print("To create .env file:")
        print("   1. If .env was deleted, restore it or run:")
        print("      cp .env.example .env")
        print("      python scripts/generate_secrets.py")
        print()
        print("   2. Or the .env file exists but you're in wrong directory")
        print("      Make sure you're in the project root directory")
        sys.exit(1)

    print()

    # Load .env file
    try:
        from dotenv import load_dotenv

        load_dotenv(".env")
        print("✅ .env file loaded successfully")
    except ImportError:
        print("⚠️  python-dotenv not installed")
        print("   Installing: pip install python-dotenv")
        print("   Continuing with system environment variables...")
    except Exception as e:
        print(f"⚠️  Warning loading .env: {e}")

    print()
    print("=" * 80)
    print("Required Variables:")
    print("=" * 80)

    required_vars = [
        ("JWT_SECRET_KEY", True, "JWT token signing (should be 512-bit)"),
        ("ENCRYPTION_MASTER_KEY", True, "AES-256-GCM encryption (should be 256-bit)"),
        ("ENVIRONMENT", True, "Runtime environment (development/staging/production)"),
    ]

    all_required_set = True
    for var_name, required, description in required_vars:
        is_set, message = check_env_var(var_name, required)
        status = "✓" if is_set else "✗"
        print(f"   [{status}] {var_name}: {message}")
        print(f"       → {description}")
        if required and not is_set:
            all_required_set = False

    print()
    print("=" * 80)
    print("Optional Variables:")
    print("=" * 80)

    optional_vars = [
        ("OPENAI_API_KEY", "OpenAI GPT-4 API"),
        ("ANTHROPIC_API_KEY", "Anthropic Claude API"),
        ("GOOGLE_AI_API_KEY", "Google AI API"),
        ("WORDPRESS_URL", "WordPress site URL"),
        ("WOOCOMMERCE_KEY", "WooCommerce consumer key"),
        ("REDIS_URL", "Redis cache connection"),
        ("DATABASE_URL", "Database connection (defaults to SQLite)"),
    ]

    print()
    print("=" * 80)
    print("3D Asset Pipeline Variables:")
    print("=" * 80)

    asset_pipeline_vars = [
        ("TRIPO_API_KEY", "Tripo3D API key for 3D model generation"),
        ("TRIPO_API_BASE_URL", "Tripo3D API base URL (default: https://api.tripo3d.ai/v2)"),
        ("FASHN_API_KEY", "FASHN API key for virtual try-on"),
        ("FASHN_API_BASE_URL", "FASHN API base URL (default: https://api.fashn.ai/v1)"),
    ]

    for var_name, description in asset_pipeline_vars:
        is_set, message = check_env_var(var_name, required=False)
        status = "✓" if is_set else "-"
        print(f"   [{status}] {var_name}: {message}")
        print(f"       → {description}")

    for var_name, description in optional_vars:
        is_set, message = check_env_var(var_name, required=False)
        status = "✓" if is_set else "-"
        print(f"   [{status}] {var_name}: {message}")
        print(f"       → {description}")

    print()
    print("=" * 80)

    if all_required_set:
        print("✅ All required environment variables are configured!")
        print()
        print("Next steps:")
        print("   1. Add optional API keys to .env if needed")
        print("   2. Run: uvicorn main_enterprise:app --reload")
        print()
        sys.exit(0)
    else:
        print("❌ Some required environment variables are missing!")
        print()
        print("To fix:")
        print("   python scripts/generate_secrets.py")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
