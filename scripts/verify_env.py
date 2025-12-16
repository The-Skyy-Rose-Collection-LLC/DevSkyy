#!/usr/bin/env python3
"""
DevSkyy Environment Verification Script
Verifies that all required environment variables and dependencies are properly configured.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def print_header(title: str) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")


def print_success(message: str) -> None:
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str) -> None:
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")


def print_warning(message: str) -> None:
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")


def print_info(message: str) -> None:
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists"""
    return Path(file_path).exists()


def load_env_file() -> dict[str, str]:
    """Load environment variables from .env file"""
    env_vars = {}
    env_file = Path(".env")

    if not env_file.exists():
        print_warning(".env file not found")
        return env_vars

    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
        print_success(f"Loaded {len(env_vars)} variables from .env file")
    except Exception as e:
        print_error(f"Error reading .env file: {e}")

    return env_vars


def check_required_env_vars() -> tuple[list[str], list[str]]:
    """Check required environment variables"""
    required_vars = [
        "NODE_ENV",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "MONGODB_URI",
        "REDIS_HOST",
        "REDIS_PORT",
        "JWT_SECRET",
        "ENCRYPTION_KEY",
        "LOG_LEVEL",
    ]

    optional_vars = [
        "OPENAI_API_KEY",
        "OPENAI_ORG_ID",
        "ANTHROPIC_API_KEY",
        "REDIS_PASSWORD",
        "SESSION_SECRET",
        "CORS_ORIGINS",
    ]

    # Load .env file
    load_dotenv()

    missing_required = []
    missing_optional = []

    print_info("Checking required environment variables...")
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_required.append(var)
            print_error(f"Missing required variable: {var}")
        else:
            # Hide sensitive values
            display_value = "*" * min(len(value), 8) if len(value) > 0 else "(empty)"
            print_success(f"{var} = {display_value}")

    print_info("Checking optional environment variables...")
    for var in optional_vars:
        value = os.getenv(var)
        if not value:
            missing_optional.append(var)
            print_warning(f"Optional variable not set: {var}")
        else:
            display_value = "*" * min(len(value), 8) if len(value) > 0 else "(empty)"
            print_success(f"{var} = {display_value}")

    return missing_required, missing_optional


def check_node_dependencies() -> bool:
    """Check Node.js dependencies"""
    print_info("Checking Node.js dependencies...")

    # Check if package.json exists
    if not check_file_exists("package.json"):
        print_error("package.json not found")
        return False

    # Check if node_modules exists
    if not check_file_exists("node_modules"):
        print_error("node_modules directory not found. Run 'npm install'")
        return False

    try:
        # Check npm list
        result = subprocess.run(
            ["npm", "list", "--depth=0"], capture_output=True, text=True, cwd="."
        )
        if result.returncode == 0:
            print_success("All npm dependencies are installed")
            return True
        else:
            print_warning("Some npm dependencies may be missing")
            print(result.stdout)
            return False
    except Exception as e:
        print_error(f"Error checking npm dependencies: {e}")
        return False


def check_python_dependencies() -> bool:
    """Check Python dependencies"""
    print_info("Checking Python dependencies...")

    try:
        # Check if python-dotenv is available

        print_success("python-dotenv is installed")

        # Check other common Python packages
        try:
            import requests

            print_success("requests is available")
        except ImportError:
            print_warning("requests not available")

        return True
    except Exception as e:
        print_error(f"Error checking Python dependencies: {e}")
        return False


def check_typescript_config() -> bool:
    """Check TypeScript configuration"""
    print_info("Checking TypeScript configuration...")

    if not check_file_exists("tsconfig.json"):
        print_error("tsconfig.json not found")
        return False

    print_success("tsconfig.json found")

    try:
        with open("tsconfig.json") as f:
            ts_config = json.load(f)

        # Check important TypeScript settings
        compiler_options = ts_config.get("compilerOptions", {})

        if compiler_options.get("strict"):
            print_success("Strict mode enabled")
        else:
            print_warning("Strict mode not enabled")

        if compiler_options.get("target") == "ES2022":
            print_success("Target set to ES2022")
        else:
            print_info(f"Target: {compiler_options.get('target', 'not specified')}")

        return True
    except Exception as e:
        print_error(f"Error reading tsconfig.json: {e}")
        return False


def check_build_artifacts() -> bool:
    """Check if build artifacts exist"""
    print_info("Checking build artifacts...")

    if check_file_exists("dist"):
        print_success("dist directory found")

        # Check for key build files
        key_files = ["dist/index.js", "dist/index.d.ts"]
        for file_path in key_files:
            if check_file_exists(file_path):
                print_success(f"✓ {file_path}")
            else:
                print_warning(f"✗ {file_path} not found")
        return True
    else:
        print_warning("dist directory not found. Run 'npm run build'")
        return False


def main():
    """Main verification function"""
    print_header("DevSkyy Environment Verification")

    all_checks_passed = True

    # Check environment variables
    print_header("Environment Variables")
    missing_required, missing_optional = check_required_env_vars()

    if missing_required:
        print_error(f"Missing {len(missing_required)} required environment variables")
        all_checks_passed = False
    else:
        print_success("All required environment variables are set")

    if missing_optional:
        print_info(f"{len(missing_optional)} optional environment variables not set")

    # Check Node.js dependencies
    print_header("Node.js Dependencies")
    if not check_node_dependencies():
        all_checks_passed = False

    # Check Python dependencies
    print_header("Python Dependencies")
    check_python_dependencies()  # Not critical

    # Check TypeScript configuration
    print_header("TypeScript Configuration")
    if not check_typescript_config():
        all_checks_passed = False

    # Check build artifacts
    print_header("Build Artifacts")
    check_build_artifacts()  # Not critical

    # Final summary
    print_header("Verification Summary")
    if all_checks_passed:
        print_success("✅ All critical checks passed! Environment is ready.")
        sys.exit(0)
    else:
        print_error("❌ Some critical checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
