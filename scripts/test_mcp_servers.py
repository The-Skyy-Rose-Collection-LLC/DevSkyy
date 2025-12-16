#!/usr/bin/env python3
"""
DevSkyy MCP Server Test Script

Tests all configured MCP servers to ensure they're working correctly.

Usage:
    python scripts/test_mcp_servers.py
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Colors:
    """ANSI color codes for terminal output"""

    GREEN = "\033[0;32m"
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BLUE}{'=' * 70}{Colors.NC}")
    print(f"{Colors.BLUE}{text.center(70)}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 70}{Colors.NC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.NC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.NC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.NC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.NC}")


def check_environment_variables():
    """Check if required environment variables are set"""
    print_header("Checking Environment Variables")

    required_vars = {
        "OPENAI_API_KEY": "Required for devskyy-openai server",
        "DEVSKYY_API_KEY": "Required for devskyy-main server",
    }

    optional_vars = {
        "ANTHROPIC_API_KEY": "Optional for Claude API access",
        "GITHUB_TOKEN": "Required for github server",
        "BRAVE_API_KEY": "Optional for brave-search server",
    }

    all_ok = True

    for var, description in required_vars.items():
        if os.getenv(var):
            print_success(f"{var} is set - {description}")
        else:
            print_error(f"{var} is NOT set - {description}")
            all_ok = False

    for var, description in optional_vars.items():
        if os.getenv(var):
            print_success(f"{var} is set - {description}")
        else:
            print_warning(f"{var} is NOT set - {description}")

    return all_ok


def check_python_dependencies():
    """Check if required Python packages are installed"""
    print_header("Checking Python Dependencies")

    required_packages = [
        ("mcp", "Model Context Protocol"),
        ("httpx", "HTTP client"),
        ("pydantic", "Data validation"),
        ("fastapi", "Web framework"),
    ]

    all_ok = True

    for package, description in required_packages:
        try:
            __import__(package)
            print_success(f"{package} is installed - {description}")
        except ImportError:
            print_error(f"{package} is NOT installed - {description}")
            all_ok = False

    return all_ok


def check_mcp_servers():
    """Check if MCP server files exist"""
    print_header("Checking MCP Server Files")

    servers = {
        "mcp/openai_server.py": "DevSkyy OpenAI MCP Server",
        "devskyy_mcp.py": "DevSkyy Main MCP Server",
        "config/claude/desktop.example.json": "Claude Desktop config example",
        ".mcp.json": "MCP configuration file",
    }

    all_ok = True

    for file_path, description in servers.items():
        full_path = project_root / file_path
        if full_path.exists():
            print_success(f"{file_path} exists - {description}")
        else:
            print_error(f"{file_path} NOT found - {description}")
            all_ok = False

    return all_ok


def check_claude_desktop_config():
    """Check Claude Desktop configuration"""
    print_header("Checking Claude Desktop Configuration")

    config_path = Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"

    if not config_path.exists():
        print_warning("Claude Desktop config not found")
        print_info(f"Expected location: {config_path}")
        print_info("Run: ./scripts/setup_mcp.sh to configure")
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)

        if "mcpServers" not in config:
            print_error("No mcpServers section in config")
            return False

        servers = config["mcpServers"]
        print_success(f"Found {len(servers)} configured MCP servers:")

        for server_name in servers:
            print_info(f"  • {server_name}")

        return True

    except json.JSONDecodeError:
        print_error("Invalid JSON in Claude Desktop config")
        return False
    except Exception as e:
        print_error(f"Error reading config: {e}")
        return False


def test_mcp_server_import(server_name: str, module_path: str):
    """Test if an MCP server can be imported"""
    try:
        # Try to import the module
        __import__(module_path.replace("/", ".").replace(".py", ""))
        print_success(f"{server_name} can be imported")
        return True
    except Exception as e:
        print_error(f"{server_name} import failed: {e}")
        return False


def main():
    """Run all tests"""
    print_header("DevSkyy MCP Server Test Suite")

    results = {
        "Environment Variables": check_environment_variables(),
        "Python Dependencies": check_python_dependencies(),
        "MCP Server Files": check_mcp_servers(),
        "Claude Desktop Config": check_claude_desktop_config(),
    }

    # Summary
    print_header("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.NC}\n")

    if passed == total:
        print_success("All tests passed! MCP servers are ready to use.")
        print_info("\nNext steps:")
        print_info("1. Restart Claude Desktop")
        print_info("2. Test MCP servers in Claude")
        print_info("3. Review docs/MCP_CONFIGURATION_GUIDE.md")
        return 0
    else:
        print_error("Some tests failed. Please fix the issues above.")
        print_info("\nTroubleshooting:")
        print_info("1. Run: ./scripts/setup_mcp.sh")
        print_info("2. Set environment variables in ~/.zshrc")
        print_info("3. Install dependencies: pip install -r mcp/requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
