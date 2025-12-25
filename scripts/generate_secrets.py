#!/usr/bin/env python3
"""
DevSkyy - Secure Key Generator
===============================

Generates cryptographically secure keys for:
- JWT_SECRET_KEY (512-bit for HS512 signing)
- ENCRYPTION_MASTER_KEY (256-bit for AES-256-GCM)

Usage:
    python scripts/generate_secrets.py

Options:
    --show-only     Display keys without updating .env file
    --env-file      Specify custom .env file path (default: .env)

Security Notes:
- Keys are generated using Python's secrets module (CSPRNG)
- JWT_SECRET_KEY: 64 bytes (512 bits) for HS512 algorithm
- ENCRYPTION_MASTER_KEY: 32 bytes (256 bits) for AES-256-GCM
- Never commit these keys to version control
- Regenerate keys for each environment (dev/staging/production)
"""

import argparse
import secrets
import sys
from pathlib import Path


def generate_jwt_secret(bits: int = 512) -> str:
    """
    Generate a cryptographically secure JWT secret key.

    Args:
        bits: Key size in bits (default: 512 for HS512)

    Returns:
        URL-safe base64 encoded secret key
    """
    bytes_needed = bits // 8
    return secrets.token_urlsafe(bytes_needed)


def generate_encryption_key(bits: int = 256) -> str:
    """
    Generate a cryptographically secure encryption master key.

    Args:
        bits: Key size in bits (default: 256 for AES-256)

    Returns:
        Standard base64 encoded encryption key (required by AES-256-GCM)
    """
    import base64

    bytes_needed = bits // 8
    key_bytes = secrets.token_bytes(bytes_needed)
    return base64.b64encode(key_bytes).decode("utf-8")


def update_env_file(env_path: Path, jwt_key: str, encryption_key: str) -> None:
    """
    Update .env file with new secure keys.

    Args:
        env_path: Path to .env file
        jwt_key: New JWT secret key
        encryption_key: New encryption master key
    """
    if not env_path.exists():
        print(f"❌ Error: {env_path} not found!")
        print("💡 Run: cp .env.example .env")
        sys.exit(1)

    # Read current .env content
    content = env_path.read_text()
    lines = content.split("\n")

    # Update keys
    updated_lines = []
    jwt_updated = False
    encryption_updated = False

    for line in lines:
        if line.startswith("JWT_SECRET_KEY="):
            updated_lines.append(f"JWT_SECRET_KEY={jwt_key}")
            jwt_updated = True
        elif line.startswith("ENCRYPTION_MASTER_KEY="):
            updated_lines.append(f"ENCRYPTION_MASTER_KEY={encryption_key}")
            encryption_updated = True
        else:
            updated_lines.append(line)

    # Add keys if they weren't found
    if not jwt_updated:
        print("⚠️  JWT_SECRET_KEY not found in .env, adding it...")
        # Find security section or add at top
        security_index = -1
        for i, line in enumerate(updated_lines):
            if (
                "# Security" in line
                or "# =============================================================================\n# Security"
                in line
            ):
                security_index = i + 1
                break

        if security_index > 0:
            updated_lines.insert(security_index + 1, f"JWT_SECRET_KEY={jwt_key}")
        else:
            updated_lines.insert(0, f"JWT_SECRET_KEY={jwt_key}")

    if not encryption_updated:
        print("⚠️  ENCRYPTION_MASTER_KEY not found in .env, adding it...")
        # Find security section or add at top
        security_index = -1
        for i, line in enumerate(updated_lines):
            if "JWT_SECRET_KEY=" in line:
                security_index = i + 1
                break

        if security_index > 0:
            updated_lines.insert(security_index, f"ENCRYPTION_MASTER_KEY={encryption_key}")
        else:
            updated_lines.insert(1, f"ENCRYPTION_MASTER_KEY={encryption_key}")

    # Write updated content
    env_path.write_text("\n".join(updated_lines))
    print(f"✅ Updated {env_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate secure cryptographic keys for DevSkyy platform"
    )
    parser.add_argument(
        "--show-only", action="store_true", help="Display keys without updating .env file"
    )
    parser.add_argument(
        "--env-file", type=Path, default=Path(".env"), help="Path to .env file (default: .env)"
    )

    args = parser.parse_args()

    # Generate keys
    print("🔐 Generating cryptographically secure keys...\n")

    jwt_key = generate_jwt_secret(512)  # 512-bit for HS512
    encryption_key = generate_encryption_key(256)  # 256-bit for AES-256-GCM

    # Display keys (only if --show-only is set)
    if args.show_only:
        print("=" * 80)
        print("Generated Keys (keep these secure!):")
        print("=" * 80)
        print(f"\nJWT_SECRET_KEY={jwt_key}")
        print(f"\nENCRYPTION_MASTER_KEY={encryption_key}")
        print("\n" + "=" * 80)

    # Security warnings
    print("\n⚠️  SECURITY WARNINGS:")
    print("   • Never commit these keys to version control")
    print("   • Use different keys for dev/staging/production")
    print("   • Store production keys in a secure vault (AWS Secrets Manager, etc.)")
    print("   • Rotate keys periodically (recommended: every 90 days)")
    print("   • If keys are compromised, regenerate immediately")

    # 3D Asset Pipeline API keys reminder
    print("\n📦 3D ASSET PIPELINE CONFIGURATION:")
    print("   The following API keys are required for the asset generation pipeline:")
    print()
    print("   Tripo3D (3D Model Generation):")
    print("   • TRIPO_API_KEY - Get from: https://www.tripo3d.ai/dashboard")
    print("   • TRIPO_API_BASE_URL - Default: https://api.tripo3d.ai/v2")
    print()
    print("   FASHN (Virtual Try-On):")
    print("   • FASHN_API_KEY - Get from: https://fashn.ai/dashboard")
    print("   • FASHN_API_BASE_URL - Default: https://api.fashn.ai/v1")
    print()
    print("   Add these to your .env file manually after obtaining API keys.")

    if args.show_only:
        print("\n💡 To update .env file, run without --show-only flag")
    else:
        print(f"\n📝 Updating {args.env_file}...")
        try:
            update_env_file(args.env_file, jwt_key, encryption_key)
            print("\n✅ Success! Environment variables updated.")
            print("\n🚀 You can now run: uvicorn main_enterprise:app --reload")
        except Exception as e:
            print(f"\n❌ Error updating .env file: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
