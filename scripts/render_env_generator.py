#!/usr/bin/env python3
"""
Render Environment Variables Generator
========================================

Generates a formatted list of environment variables ready to copy-paste
into Render's dashboard. Reads from .env.production and formats for easy input.

Usage:
    python scripts/render_env_generator.py
    python scripts/render_env_generator.py --output render_env.txt
    python scripts/render_env_generator.py --validate-only

Features:
- Validates environment variable format
- Separates required vs optional variables
- Flags placeholder values that need replacement
- Generates secure secrets for required security variables
- Outputs in Render-compatible format

"""

import argparse
import base64
import re
import secrets
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    NC = "\033[0m"  # No Color


def generate_jwt_secret() -> str:
    """Generate a cryptographically secure JWT secret (512-bit)."""
    return secrets.token_urlsafe(64)


def generate_encryption_key() -> str:
    """Generate AES-256-GCM encryption key (base64 encoded 32 bytes)."""
    return base64.b64encode(secrets.token_bytes(32)).decode()


def generate_api_key() -> str:
    """Generate API key for internal services."""
    return secrets.token_urlsafe(64)


def parse_env_file(filepath: Path) -> dict[str, str]:
    """Parse .env file and return key-value pairs.

    Args:
        filepath: Path to .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}

    if not filepath.exists():
        print(f"{Colors.RED}Error: {filepath} not found{Colors.NC}")
        sys.exit(1)

    with open(filepath) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if (
                    value.startswith('"')
                    and value.endswith('"')
                    or value.startswith("'")
                    and value.endswith("'")
                ):
                    value = value[1:-1]

                env_vars[key] = value
            else:
                print(f"{Colors.YELLOW}Warning: Line {line_num} invalid format{Colors.NC}")

    return env_vars


def categorize_variables(env_vars: dict[str, str]) -> dict[str, list[tuple[str, str, str]]]:
    """Categorize environment variables by importance and type.

    Returns:
        Dictionary with categories: required_security, required_db, required_llm, optional
    """
    categories = {
        "required_security": [],
        "required_db": [],
        "required_app": [],
        "required_llm": [],
        "optional_3d": [],
        "optional_commerce": [],
        "optional_monitoring": [],
        "optional_other": [],
    }

    # Required security variables
    security_vars = [
        "JWT_SECRET_KEY",
        "ENCRYPTION_MASTER_KEY",
        "SECRET_KEY",
        "SESSION_SECRET",
    ]

    # Required database variables
    db_vars = ["DATABASE_URL", "REDIS_URL"]

    # Required application variables
    app_vars = ["ENVIRONMENT", "DEBUG", "LOG_LEVEL", "CORS_ORIGINS", "PYTHON_VERSION"]

    # LLM providers (at least one required)
    llm_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_AI_API_KEY",
        "MISTRAL_API_KEY",
        "COHERE_API_KEY",
        "GROQ_API_KEY",
    ]

    # 3D generation
    three_d_vars = ["TRIPO_API_KEY", "FASHN_API_KEY", "HUGGINGFACE_ACCESS_TOKEN"]

    # Commerce
    commerce_vars = ["WORDPRESS_URL", "WOOCOMMERCE_KEY", "WOOCOMMERCE_SECRET"]

    # Monitoring
    monitoring_vars = ["SENTRY_DSN", "DD_API_KEY", "NEW_RELIC_LICENSE_KEY"]

    # Categorize each variable
    for key, value in env_vars.items():
        # Determine status
        if not value or value in [
            "REPLACE_WITH_PRODUCTION_KEY",
            "CHANGE_THIS_PASSWORD",
            "GENERATE_NEW_SECRET_KEY_64_CHARS_MINIMUM",
            "GENERATE_NEW_JWT_SECRET_64_CHARS_MINIMUM",
            "GENERATE_NEW_BASE64_32_BYTE_KEY",
        ]:
            status = "placeholder"
        else:
            status = "set"

        entry = (key, value, status)

        # Assign to category
        if key in security_vars:
            categories["required_security"].append(entry)
        elif key in db_vars:
            categories["required_db"].append(entry)
        elif key in app_vars:
            categories["required_app"].append(entry)
        elif key in llm_vars:
            categories["required_llm"].append(entry)
        elif key in three_d_vars:
            categories["optional_3d"].append(entry)
        elif key in commerce_vars:
            categories["optional_commerce"].append(entry)
        elif key in monitoring_vars:
            categories["optional_monitoring"].append(entry)
        else:
            categories["optional_other"].append(entry)

    return categories


def generate_render_format(
    categories: dict[str, list[tuple[str, str, str]]], auto_generate: bool = True
) -> str:
    """Generate environment variables in Render dashboard format.

    Args:
        categories: Categorized environment variables
        auto_generate: Whether to auto-generate secure secrets

    Returns:
        Formatted string ready for Render
    """
    output = []

    output.append("=" * 80)
    output.append("DEVSKYY BACKEND - RENDER ENVIRONMENT VARIABLES")
    output.append("=" * 80)
    output.append("")
    output.append("Copy and paste these into Render Dashboard > Environment tab")
    output.append("Each variable should be added individually using 'Add Environment Variable'")
    output.append("")

    # Security variables (auto-generate if needed)
    output.append("=" * 80)
    output.append("REQUIRED - Security (Auto-Generated)")
    output.append("=" * 80)

    if auto_generate:
        output.append(f"JWT_SECRET_KEY={generate_jwt_secret()}")
        output.append(f"ENCRYPTION_MASTER_KEY={generate_encryption_key()}")
        output.append(f"SECRET_KEY={generate_jwt_secret()}")
    else:
        for key, value, status in categories["required_security"]:
            output.append(f"{key}={value}")

    output.append("")

    # Database variables
    output.append("=" * 80)
    output.append("REQUIRED - Database & Cache")
    output.append("=" * 80)
    output.append("# ⚠️  Replace with your actual Render PostgreSQL and Redis URLs")
    output.append("# Get these from Render Dashboard after creating database/redis instances")
    output.append("#")
    output.append("# Example:")
    output.append("# DATABASE_URL=postgresql://devskyy:password@dpg-abc123/devskyy_production")
    output.append("# REDIS_URL=redis://red-xyz789:6379")
    output.append("")

    for key, value, status in categories["required_db"]:
        if status == "placeholder":
            output.append(f"{key}=REPLACE_WITH_RENDER_URL")
        else:
            output.append(f"{key}={value}")

    output.append("")

    # Application settings
    output.append("=" * 80)
    output.append("REQUIRED - Application Settings")
    output.append("=" * 80)

    for key, value, status in categories["required_app"]:
        output.append(f"{key}={value}")

    output.append("")

    # LLM providers
    output.append("=" * 80)
    output.append("REQUIRED - LLM Provider (At Least ONE Required)")
    output.append("=" * 80)
    output.append("# ⚠️  Add at least one LLM API key")
    output.append("# Get keys from respective provider dashboards")
    output.append("")

    for key, value, status in categories["required_llm"]:
        if status == "placeholder" or not value:
            output.append(f"# {key}=ADD_YOUR_API_KEY_HERE")
        else:
            output.append(f"{key}={value}")

    output.append("")

    # Optional - 3D Generation
    if categories["optional_3d"]:
        output.append("=" * 80)
        output.append("OPTIONAL - 3D & Visual Generation")
        output.append("=" * 80)
        output.append("# Only add if you plan to use 3D generation features")
        output.append("")

        for key, value, status in categories["optional_3d"]:
            if status == "placeholder" or not value:
                output.append(f"# {key}=ADD_IF_NEEDED")
            else:
                output.append(f"{key}={value}")

        output.append("")

    # Optional - Commerce
    if categories["optional_commerce"]:
        output.append("=" * 80)
        output.append("OPTIONAL - WordPress/WooCommerce Integration")
        output.append("=" * 80)
        output.append("# Only add if you're integrating with WordPress/WooCommerce")
        output.append("")

        for key, value, status in categories["optional_commerce"]:
            if status == "placeholder" or not value:
                output.append(f"# {key}=ADD_IF_NEEDED")
            else:
                output.append(f"{key}={value}")

        output.append("")

    # Optional - Monitoring
    if categories["optional_monitoring"]:
        output.append("=" * 80)
        output.append("OPTIONAL - Monitoring & Observability")
        output.append("=" * 80)
        output.append("# Recommended for production")
        output.append("")

        for key, value, status in categories["optional_monitoring"]:
            if status == "placeholder" or not value:
                output.append(f"# {key}=ADD_IF_NEEDED")
            else:
                output.append(f"{key}={value}")

        output.append("")

    # Summary
    output.append("=" * 80)
    output.append("DEPLOYMENT CHECKLIST")
    output.append("=" * 80)
    output.append("")
    output.append("1. Create PostgreSQL database in Render")
    output.append("2. Create Redis instance in Render")
    output.append("3. Update DATABASE_URL with actual PostgreSQL Internal URL")
    output.append("4. Update REDIS_URL with actual Redis Internal URL")
    output.append("5. Add at least one LLM provider API key")
    output.append("6. Copy all environment variables to Render dashboard")
    output.append("7. Deploy web service")
    output.append("8. Verify health check: curl https://your-service.onrender.com/health")
    output.append("")
    output.append("=" * 80)

    return "\n".join(output)


def validate_environment(
    categories: dict[str, list[tuple[str, str, str]]],
) -> tuple[bool, list[str]]:
    """Validate environment variables for common issues.

    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []

    # Check required security variables
    security_vars = categories["required_security"]
    if not security_vars:
        issues.append("Missing required security variables")

    for key, value, status in security_vars:
        if status == "placeholder":
            issues.append(f"Security variable '{key}' has placeholder value")

    # Check database variables
    db_vars = categories["required_db"]
    if not db_vars:
        issues.append("Missing database connection variables")

    # Check for at least one LLM provider
    llm_vars = categories["required_llm"]
    has_llm = any(status != "placeholder" and value for _, value, status in llm_vars)

    if not has_llm:
        issues.append("No LLM provider API key configured (at least one required)")

    # Check CORS origins format
    app_vars = {key: value for key, value, _ in categories["required_app"]}
    if "CORS_ORIGINS" in app_vars:
        cors = app_vars["CORS_ORIGINS"]
        if not re.match(r"^https?://", cors):
            issues.append("CORS_ORIGINS should start with http:// or https://")

    return len(issues) == 0, issues


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate Render environment variables")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env.production"),
        help="Path to .env file (default: .env.production)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate environment variables, don't generate output",
    )
    parser.add_argument(
        "--no-auto-generate",
        action="store_true",
        help="Don't auto-generate security secrets",
    )

    args = parser.parse_args()

    # Parse environment file
    print(f"{Colors.BLUE}Reading {args.env_file}...{Colors.NC}")
    env_vars = parse_env_file(args.env_file)
    print(f"{Colors.GREEN}✓ Found {len(env_vars)} environment variables{Colors.NC}\n")

    # Categorize variables
    categories = categorize_variables(env_vars)

    # Validate
    is_valid, issues = validate_environment(categories)

    if args.validate_only:
        print(f"{Colors.BLUE}Validation Results:{Colors.NC}\n")
        if is_valid:
            print(f"{Colors.GREEN}✓ All checks passed{Colors.NC}")
            sys.exit(0)
        else:
            print(f"{Colors.RED}✗ Validation failed:{Colors.NC}")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)

    # Display validation warnings
    if not is_valid:
        print(f"{Colors.YELLOW}⚠️  Validation Warnings:{Colors.NC}")
        for issue in issues:
            print(f"  - {issue}")
        print()

    # Generate output
    output = generate_render_format(categories, auto_generate=not args.no_auto_generate)

    # Write to file or stdout
    if args.output:
        args.output.write_text(output)
        print(
            f"{Colors.GREEN}✓ Generated environment variables written to {args.output}{Colors.NC}"
        )
        print(f"\n{Colors.BLUE}Next steps:{Colors.NC}")
        print(f"1. Review the file: {args.output}")
        print("2. Create database and Redis in Render")
        print("3. Update DATABASE_URL and REDIS_URL with actual values")
        print("4. Copy variables to Render Dashboard > Environment")
    else:
        print(output)


if __name__ == "__main__":
    main()
