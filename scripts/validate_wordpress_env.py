#!/usr/bin/env python3
"""
Validate WordPress environment configuration.

Checks:
- Required environment variables
- WordPress installation integrity
- Database connectivity
- Theme activation status
- Plugin requirements
- Memory settings
- Page deployment status

Usage:
    python scripts/validate_wordpress_env.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    print("Installing python-dotenv...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

# Load environment
load_dotenv("/Users/coreyfoster/DevSkyy/.env.wordpress.local")
load_dotenv("/Users/coreyfoster/DevSkyy/.env")


class Colors:
    """ANSI color codes."""
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def run_wp_cli(command: str) -> tuple[bool, str]:
    """Run WP-CLI command and return (success, output)."""
    wp_path = os.getenv("WORDPRESS_LOCAL_PATH")
    wp_cli = os.getenv("WP_CLI_PATH")

    if not wp_path or not wp_cli:
        return False, "WP-CLI path not configured"

    full_command = f'cd {wp_path} && php {wp_cli} {command} --allow-root 2>&1 | grep -v "Deprecated:"'

    try:
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def print_check(name: str, passed: bool, details: str = ""):
    """Print a check result."""
    status = f"{Colors.GREEN}✓{Colors.NC}" if passed else f"{Colors.RED}✗{Colors.NC}"
    print(f"  {status} {name}")
    if details:
        indent = "    "
        for line in details.split("\n"):
            print(f"{indent}{line}")


def validate_environment_variables() -> dict[str, Any]:
    """Validate required environment variables."""
    print(f"\n{Colors.BLUE}[1/7] Environment Variables{Colors.NC}")

    required_vars = {
        "WORDPRESS_LOCAL_URL": "WordPress URL",
        "WORDPRESS_LOCAL_PATH": "WordPress installation path",
        "WP_CLI_PATH": "WP-CLI executable path",
        "THEME_NAME": "Theme name",
        "WP_MEMORY_LIMIT": "Memory limit",
    }

    results = {}
    for var, description in required_vars.items():
        value = os.getenv(var)
        passed = bool(value)
        results[var] = value
        detail = f"{var}={value}" if passed else f"{var} not set"
        print_check(description, passed, detail)

    return results


def validate_wordpress_installation(env: dict) -> bool:
    """Validate WordPress installation."""
    print(f"\n{Colors.BLUE}[2/7] WordPress Installation{Colors.NC}")

    # Check WordPress path exists
    wp_path = Path(env.get("WORDPRESS_LOCAL_PATH", ""))
    if not wp_path.exists():
        print_check("Installation path", False, f"Path not found: {wp_path}")
        return False

    print_check("Installation path", True, str(wp_path))

    # Check wp-config.php
    wp_config = wp_path / "wp-config.php"
    config_exists = wp_config.exists()
    print_check("wp-config.php", config_exists)

    # Check WordPress version
    success, version = run_wp_cli("core version")
    if success:
        print_check("WordPress version", True, f"v{version}")
    else:
        print_check("WordPress version", False, version)

    # Verify core integrity
    success, output = run_wp_cli("core verify-checksums")
    checksum_valid = "Success" in output
    print_check("Core file integrity", checksum_valid)

    return config_exists and success


def validate_theme() -> bool:
    """Validate theme installation and activation."""
    print(f"\n{Colors.BLUE}[3/7] Theme Configuration{Colors.NC}")

    theme_name = os.getenv("THEME_NAME", "skyyrose-2025")

    # Check theme status
    success, output = run_wp_cli(f"theme status {theme_name}")
    is_active = "active" in output.lower()
    print_check(f"Theme '{theme_name}' active", is_active)

    # Get theme version
    success, version = run_wp_cli(f"eval 'echo wp_get_theme(\"{theme_name}\")->get(\"Version\");'")
    if success:
        expected_version = os.getenv("THEME_VERSION", "2.0.0")
        version_match = version == expected_version
        print_check("Theme version", version_match, f"v{version}")

    return is_active


def validate_plugins() -> bool:
    """Validate required plugins."""
    print(f"\n{Colors.BLUE}[4/7] Required Plugins{Colors.NC}")

    required_plugins = ["woocommerce", "elementor"]
    all_active = True

    for plugin in required_plugins:
        success, output = run_wp_cli(f"plugin status {plugin}")
        is_active = "active" in output.lower() and "inactive" not in output.lower()
        all_active = all_active and is_active
        print_check(plugin.title(), is_active)

    return all_active


def validate_pages() -> bool:
    """Validate deployed pages."""
    print(f"\n{Colors.BLUE}[5/7] Deployed Pages{Colors.NC}")

    pages = {
        "Home": os.getenv("PAGE_ID_HOME"),
        "Black Rose": os.getenv("PAGE_ID_BLACK_ROSE"),
        "Love Hurts": os.getenv("PAGE_ID_LOVE_HURTS"),
        "Signature": os.getenv("PAGE_ID_SIGNATURE"),
        "Collections": os.getenv("PAGE_ID_COLLECTIONS"),
        "The Vault": os.getenv("PAGE_ID_THE_VAULT"),
    }

    all_exist = True
    for name, page_id in pages.items():
        if not page_id:
            print_check(name, False, "Page ID not set")
            all_exist = False
            continue

        success, output = run_wp_cli(f"post get {page_id} --field=post_status")
        is_published = output == "publish"
        all_exist = all_exist and is_published
        print_check(name, is_published, f"ID: {page_id}")

    return all_exist


def validate_memory() -> bool:
    """Validate memory settings."""
    print(f"\n{Colors.BLUE}[6/7] Memory Settings{Colors.NC}")

    success, memory_limit = run_wp_cli("eval 'echo WP_MEMORY_LIMIT;'")
    if success:
        is_512m = "512M" in memory_limit
        print_check("WP_MEMORY_LIMIT", is_512m, memory_limit)
        return is_512m

    return False


def validate_database() -> bool:
    """Validate database connectivity."""
    print(f"\n{Colors.BLUE}[7/7] Database{Colors.NC}")

    # Check database connection
    success, db_name = run_wp_cli("db check")
    db_connected = success
    print_check("Database connection", db_connected)

    if db_connected:
        # Get database size
        success, output = run_wp_cli('db query "SELECT COUNT(*) FROM wordpress.wp_posts WHERE post_type=\'page\' AND post_status=\'publish\';"')
        if success:
            try:
                page_count = int(output.split('\n')[-1])
                has_pages = page_count > 0
                print_check("Published pages", has_pages, f"{page_count} pages")
            except:
                print_check("Published pages", False, "Could not count pages")

    return db_connected


def main():
    """Main validation function."""
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}  SkyyRose WordPress Environment Validation{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

    # Run all validations
    env = validate_environment_variables()
    wp_valid = validate_wordpress_installation(env)
    theme_valid = validate_theme()
    plugins_valid = validate_plugins()
    pages_valid = validate_pages()
    memory_valid = validate_memory()
    db_valid = validate_database()

    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}  Summary{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")

    all_checks = [
        ("Environment Variables", bool(env)),
        ("WordPress Installation", wp_valid),
        ("Theme Configuration", theme_valid),
        ("Required Plugins", plugins_valid),
        ("Deployed Pages", pages_valid),
        ("Memory Settings", memory_valid),
        ("Database", db_valid),
    ]

    passed_count = sum(1 for _, passed in all_checks if passed)
    total_count = len(all_checks)

    for name, passed in all_checks:
        print_check(name, passed)

    print(f"\n{Colors.BLUE}Result: {passed_count}/{total_count} checks passed{Colors.NC}\n")

    if passed_count == total_count:
        print(f"{Colors.GREEN}✓ Environment configuration is valid!{Colors.NC}")
        print(f"\n{Colors.BLUE}Ready URLs:{Colors.NC}")
        print(f"  • Homepage: http://localhost:8881")
        print(f"  • Admin: http://localhost:8881/wp-admin/")
        print(f"  • Edit with Elementor: http://localhost:8881/wp-admin/post.php?post={os.getenv('PAGE_ID_HOME', '12')}&action=elementor")
        return 0
    else:
        print(f"{Colors.RED}✗ Environment configuration has issues{Colors.NC}")
        print(f"\n{Colors.YELLOW}Fix the issues above and run validation again.{Colors.NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
