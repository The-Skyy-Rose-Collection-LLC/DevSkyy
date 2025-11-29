#!/usr/bin/env python3
"""
MCP Health Check Diagnostic Tool for DevSkyy Enterprise

WHY: Comprehensive diagnostics for MCP (Model Context Protocol) server configurations
HOW: Validates system dependencies, config syntax, server startup, and connectivity
IMPACT: Faster debugging, proactive issue detection, reduced downtime

Features:
- System dependency checks (Node.js, Python, npm/npx, uv)
- MCP config JSON validation
- Server command availability testing
- JSON-RPC initialize handshake testing
- WordPress/WooCommerce environment and connectivity checks
- Port availability validation

Truth Protocol Compliance:
- Rule #1: Verified from official MCP and JSON-RPC specs
- Rule #9: Google-style docstrings with type hints
- Rule #10: Errors logged and continue processing
- Rule #15: No placeholders, all code executes

Usage:
    python mcp_health_check.py
    python mcp_health_check.py --config /path/to/config.json
    python mcp_health_check.py --verbose
    python mcp_health_check.py --json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    """Status of a health check."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class CheckResult:
    """Result of a single health check.

    Attributes:
        name: Name of the check
        status: Pass/warn/fail/skip status
        message: Human-readable description
        details: Additional details (optional)
        fix_suggestion: How to fix if failed (optional)
    """

    name: str
    status: CheckStatus
    message: str
    details: str | None = None
    fix_suggestion: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        result: dict[str, Any] = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        if self.fix_suggestion:
            result["fix_suggestion"] = self.fix_suggestion
        return result


@dataclass
class HealthCheckReport:
    """Complete health check report.

    Attributes:
        checks: List of individual check results
        passed: Count of passed checks
        warned: Count of warning checks
        failed: Count of failed checks
        skipped: Count of skipped checks
    """

    checks: list[CheckResult] = field(default_factory=list)
    passed: int = 0
    warned: int = 0
    failed: int = 0
    skipped: int = 0

    def add(self, result: CheckResult) -> None:
        """Add a check result and update counters."""
        self.checks.append(result)
        if result.status == CheckStatus.PASS:
            self.passed += 1
        elif result.status == CheckStatus.WARN:
            self.warned += 1
        elif result.status == CheckStatus.FAIL:
            self.failed += 1
        else:
            self.skipped += 1

    @property
    def success(self) -> bool:
        """Return True if no failures occurred."""
        return self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "summary": {
                "total": len(self.checks),
                "passed": self.passed,
                "warned": self.warned,
                "failed": self.failed,
                "skipped": self.skipped,
                "success": self.success,
            },
            "checks": [check.to_dict() for check in self.checks],
        }


class MCPHealthChecker:
    """MCP Health Check diagnostic utility.

    Provides comprehensive diagnostics for MCP server configurations targeting
    the DevSkyy multi-agent system for skyyrose.co WordPress/WooCommerce.

    Attributes:
        config_path: Path to MCP configuration JSON
        verbose: Enable verbose output
        json_output: Output results as JSON
        config: Parsed MCP configuration
        report: Health check report
    """

    # Default config paths per platform
    DEFAULT_CONFIG_PATHS = {
        "Darwin": Path.home()
        / "Library"
        / "Application Support"
        / "Claude"
        / "claude_desktop_config.json",
        "Windows": Path(os.environ.get("APPDATA", ""))
        / "Claude"
        / "claude_desktop_config.json",
        "Linux": Path.home() / ".config" / "claude" / "claude_desktop_config.json",
    }

    # WordPress/WooCommerce environment variables
    WORDPRESS_ENV_VARS = [
        "WORDPRESS_CLIENT_ID",
        "WORDPRESS_CLIENT_SECRET",
        "WORDPRESS_REDIRECT_URI",
        "WORDPRESS_TOKEN_URL",
        "WORDPRESS_API_BASE",
        "SKYY_ROSE_SITE_URL",
        "SKYY_ROSE_USERNAME",
        "SKYY_ROSE_PASSWORD",
        "SKYY_ROSE_APP_PASSWORD",
    ]

    WOOCOMMERCE_ENV_VARS = [
        "WOOCOMMERCE_CONSUMER_KEY",
        "WOOCOMMERCE_CONSUMER_SECRET",
        "WOOCOMMERCE_STORE_URL",
        "WOOCOMMERCE_API_VERSION",
    ]

    def __init__(
        self,
        config_path: str | Path | None = None,
        verbose: bool = False,
        json_output: bool = False,
    ) -> None:
        """Initialize the health checker.

        Args:
            config_path: Path to MCP config. Auto-detected if not provided.
            verbose: Enable verbose diagnostic output.
            json_output: Output results as JSON instead of text.
        """
        self.verbose = verbose
        self.json_output = json_output
        self.report = HealthCheckReport()
        self.config: dict[str, Any] = {}

        # Resolve config path
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self._detect_config_path()

    def _detect_config_path(self) -> Path:
        """Auto-detect MCP config path based on platform.

        Returns:
            Path to the detected configuration file.
        """
        system = platform.system()
        default_path = self.DEFAULT_CONFIG_PATHS.get(system)

        if default_path and default_path.exists():
            return default_path

        # Check current directory
        local_config = Path("claude_desktop_config.json")
        if local_config.exists():
            return local_config

        # Check project .mcp.json
        mcp_json = Path(".mcp.json")
        if mcp_json.exists():
            return mcp_json

        # Return the platform default even if it doesn't exist
        return default_path or Path("claude_desktop_config.json")

    def _log(self, message: str, level: str = "info") -> None:
        """Log message if not in JSON output mode."""
        if not self.json_output:
            if level == "verbose" and self.verbose:
                logger.info(f"  {message}")
            elif level != "verbose":
                logger.info(message)

    def _log_check(self, result: CheckResult) -> None:
        """Log a check result with appropriate formatting."""
        if self.json_output:
            return

        status_icons = {
            CheckStatus.PASS: "\u2705",
            CheckStatus.WARN: "\u26a0\ufe0f ",
            CheckStatus.FAIL: "\u274c",
            CheckStatus.SKIP: "\u23ed\ufe0f ",
        }

        icon = status_icons.get(result.status, "?")
        logger.info(f"{icon} {result.name}: {result.message}")

        if self.verbose and result.details:
            logger.info(f"   Details: {result.details}")

        if result.status == CheckStatus.FAIL and result.fix_suggestion:
            logger.info(f"   Fix: {result.fix_suggestion}")

    def run_command(
        self, command: list[str], timeout: int = 10
    ) -> tuple[int, str, str]:
        """Run a shell command and return results.

        Args:
            command: Command and arguments to run.
            timeout: Timeout in seconds.

        Returns:
            Tuple of (return_code, stdout, stderr).
        """
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", f"Command timed out after {timeout}s"
        except FileNotFoundError:
            return -1, "", f"Command not found: {command[0]}"
        except Exception as e:
            return -1, "", str(e)

    def check_system_dependency(
        self,
        name: str,
        commands: list[list[str]],
        min_version: str | None = None,
        required: bool = True,
    ) -> CheckResult:
        """Check if a system dependency is installed.

        Args:
            name: Human-readable name of the dependency.
            commands: List of command variants to try (e.g., [["node", "-v"], ["nodejs", "-v"]]).
            min_version: Minimum required version (optional).
            required: Whether this is a required dependency.

        Returns:
            CheckResult with pass/fail status.
        """
        for cmd in commands:
            code, stdout, stderr = self.run_command(cmd)
            if code == 0:
                version = stdout or stderr
                # Extract version number
                version_match = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", version)
                version_str = version_match.group(1) if version_match else version

                if min_version and version_match:
                    # Simple version comparison
                    current_parts = [int(x) for x in version_str.split(".")[:3]]
                    min_parts = [int(x) for x in min_version.split(".")[:3]]

                    # Pad with zeros
                    while len(current_parts) < 3:
                        current_parts.append(0)
                    while len(min_parts) < 3:
                        min_parts.append(0)

                    if current_parts < min_parts:
                        return CheckResult(
                            name=name,
                            status=CheckStatus.WARN,
                            message=f"Version {version_str} below minimum {min_version}",
                            fix_suggestion=f"Upgrade {name} to version {min_version} or higher",
                        )

                return CheckResult(
                    name=name,
                    status=CheckStatus.PASS,
                    message=f"Installed (version {version_str})",
                    details=f"Command: {' '.join(cmd)}",
                )

        # Not found
        install_hints = {
            "Node.js": "Install from https://nodejs.org or via nvm",
            "Python": "Install from https://python.org or via pyenv",
            "npm": "Comes with Node.js installation",
            "npx": "Comes with npm 5.2.0+; run: npm install -g npx",
            "uv": "Install via: pip install uv OR curl -LsSf https://astral.sh/uv/install.sh | sh",
        }

        return CheckResult(
            name=name,
            status=CheckStatus.FAIL if required else CheckStatus.WARN,
            message="Not found",
            fix_suggestion=install_hints.get(name, f"Install {name}"),
        )

    def check_system_dependencies(self) -> None:
        """Check all required system dependencies."""
        self._log("\n=== System Dependencies ===")

        # Node.js
        result = self.check_system_dependency(
            "Node.js",
            [["node", "--version"], ["nodejs", "--version"]],
            min_version="18.0.0",
        )
        self.report.add(result)
        self._log_check(result)

        # Python
        result = self.check_system_dependency(
            "Python",
            [["python3", "--version"], ["python", "--version"]],
            min_version="3.11.0",
        )
        self.report.add(result)
        self._log_check(result)

        # npm
        result = self.check_system_dependency(
            "npm",
            [["npm", "--version"]],
            min_version="8.0.0",
        )
        self.report.add(result)
        self._log_check(result)

        # npx
        result = self.check_system_dependency(
            "npx",
            [["npx", "--version"]],
            required=False,
        )
        self.report.add(result)
        self._log_check(result)

        # uv (Python package manager)
        result = self.check_system_dependency(
            "uv",
            [["uv", "--version"]],
            required=False,
        )
        self.report.add(result)
        self._log_check(result)

    def check_config_exists(self) -> CheckResult:
        """Check if the MCP config file exists.

        Returns:
            CheckResult indicating if config file exists.
        """
        if self.config_path.exists():
            return CheckResult(
                name="Config File Exists",
                status=CheckStatus.PASS,
                message=f"Found at {self.config_path}",
            )
        else:
            return CheckResult(
                name="Config File Exists",
                status=CheckStatus.FAIL,
                message=f"Not found at {self.config_path}",
                fix_suggestion=(
                    f"Create config at {self.config_path} or use --config flag. "
                    "See: https://docs.anthropic.com/mcp/config"
                ),
            )

    def check_config_syntax(self) -> CheckResult:
        """Validate JSON syntax of the MCP config.

        Returns:
            CheckResult indicating if JSON is valid.
        """
        try:
            with open(self.config_path, encoding="utf-8") as f:
                self.config = json.load(f)

            return CheckResult(
                name="Config JSON Syntax",
                status=CheckStatus.PASS,
                message="Valid JSON",
            )
        except json.JSONDecodeError as e:
            return CheckResult(
                name="Config JSON Syntax",
                status=CheckStatus.FAIL,
                message=f"Invalid JSON at line {e.lineno}, column {e.colno}",
                details=str(e.msg),
                fix_suggestion="Fix JSON syntax error. Use a JSON validator like jsonlint.com",
            )
        except FileNotFoundError:
            return CheckResult(
                name="Config JSON Syntax",
                status=CheckStatus.SKIP,
                message="Config file not found",
            )
        except PermissionError:
            return CheckResult(
                name="Config JSON Syntax",
                status=CheckStatus.FAIL,
                message="Permission denied reading config file",
                fix_suggestion=f"Check file permissions: chmod 644 {self.config_path}",
            )

    def check_config_structure(self) -> CheckResult:
        """Validate the structure of the MCP config.

        Returns:
            CheckResult indicating if structure is valid.
        """
        if not self.config:
            return CheckResult(
                name="Config Structure",
                status=CheckStatus.SKIP,
                message="No config loaded",
            )

        # Check for mcpServers key
        if "mcpServers" not in self.config:
            return CheckResult(
                name="Config Structure",
                status=CheckStatus.FAIL,
                message="Missing 'mcpServers' key",
                fix_suggestion='Add "mcpServers": {} to your config',
            )

        servers = self.config.get("mcpServers", {})
        if not servers:
            return CheckResult(
                name="Config Structure",
                status=CheckStatus.WARN,
                message="No servers defined in mcpServers",
                fix_suggestion="Add at least one MCP server configuration",
            )

        # Validate each server
        issues: list[str] = []
        for name, server_config in servers.items():
            if not isinstance(server_config, dict):
                issues.append(f"Server '{name}': config must be an object")
                continue

            if "command" not in server_config:
                issues.append(f"Server '{name}': missing 'command' field")

            # Check for args being a list
            args = server_config.get("args", [])
            if not isinstance(args, list):
                issues.append(f"Server '{name}': 'args' must be an array")

        if issues:
            return CheckResult(
                name="Config Structure",
                status=CheckStatus.FAIL,
                message=f"{len(issues)} structure issue(s) found",
                details="; ".join(issues),
                fix_suggestion="Fix the configuration structure issues",
            )

        return CheckResult(
            name="Config Structure",
            status=CheckStatus.PASS,
            message=f"Valid structure with {len(servers)} server(s)",
        )

    def check_unset_env_references(self) -> CheckResult:
        """Check for unset environment variable references like ${VAR_NAME}.

        Returns:
            CheckResult indicating if any env refs are unset.
        """
        if not self.config:
            return CheckResult(
                name="Environment Variable References",
                status=CheckStatus.SKIP,
                message="No config loaded",
            )

        # Pattern to match ${VAR_NAME} style references
        env_pattern = re.compile(r"\$\{([^}]+)\}")
        unset_vars: list[str] = []
        config_str = json.dumps(self.config)

        for match in env_pattern.finditer(config_str):
            var_name = match.group(1)
            if not os.environ.get(var_name):
                unset_vars.append(var_name)

        if unset_vars:
            return CheckResult(
                name="Environment Variable References",
                status=CheckStatus.FAIL,
                message=f"{len(unset_vars)} unset variable(s) found",
                details=", ".join(unset_vars),
                fix_suggestion=f"Set these environment variables: {', '.join(unset_vars)}",
            )

        return CheckResult(
            name="Environment Variable References",
            status=CheckStatus.PASS,
            message="All referenced environment variables are set",
        )

    def check_mcp_config(self) -> None:
        """Run all MCP config checks."""
        self._log("\n=== MCP Configuration ===")

        # Check config exists
        result = self.check_config_exists()
        self.report.add(result)
        self._log_check(result)

        if result.status == CheckStatus.FAIL:
            return

        # Check JSON syntax
        result = self.check_config_syntax()
        self.report.add(result)
        self._log_check(result)

        if result.status == CheckStatus.FAIL:
            return

        # Check structure
        result = self.check_config_structure()
        self.report.add(result)
        self._log_check(result)

        # Check env var references
        result = self.check_unset_env_references()
        self.report.add(result)
        self._log_check(result)

    def check_server_command(self, name: str, server_config: dict) -> CheckResult:
        """Check if a server's command is available.

        Args:
            name: Server name.
            server_config: Server configuration dict.

        Returns:
            CheckResult indicating if command is available.
        """
        command = server_config.get("command", "")

        # Handle common command patterns
        if command in ("node", "nodejs"):
            executable = shutil.which("node") or shutil.which("nodejs")
        elif command in ("python", "python3"):
            executable = shutil.which("python3") or shutil.which("python")
        elif command == "npx":
            executable = shutil.which("npx")
        elif command == "uvx":
            executable = shutil.which("uvx") or shutil.which("uv")
        else:
            executable = shutil.which(command)

        if executable:
            return CheckResult(
                name=f"Server '{name}' Command",
                status=CheckStatus.PASS,
                message=f"Command '{command}' found at {executable}",
            )
        else:
            return CheckResult(
                name=f"Server '{name}' Command",
                status=CheckStatus.FAIL,
                message=f"Command '{command}' not found",
                fix_suggestion=f"Install {command} or update PATH",
            )

    def check_python_server_env(self, name: str, server_config: dict) -> CheckResult:
        """Check PYTHONUNBUFFERED for Python-based servers.

        Args:
            name: Server name.
            server_config: Server configuration dict.

        Returns:
            CheckResult for PYTHONUNBUFFERED check.
        """
        command = server_config.get("command", "")
        args = server_config.get("args", [])

        # Determine if this is a Python server
        is_python = command in ("python", "python3") or any(
            arg.endswith(".py") for arg in args
        )

        if not is_python:
            return CheckResult(
                name=f"Server '{name}' PYTHONUNBUFFERED",
                status=CheckStatus.SKIP,
                message="Not a Python server",
            )

        # Check env configuration
        env = server_config.get("env", {})
        if env.get("PYTHONUNBUFFERED") == "1":
            return CheckResult(
                name=f"Server '{name}' PYTHONUNBUFFERED",
                status=CheckStatus.PASS,
                message="PYTHONUNBUFFERED=1 configured",
            )
        else:
            return CheckResult(
                name=f"Server '{name}' PYTHONUNBUFFERED",
                status=CheckStatus.WARN,
                message="PYTHONUNBUFFERED not set",
                fix_suggestion=(
                    f'Add "PYTHONUNBUFFERED": "1" to env for server "{name}". '
                    "This ensures proper output buffering for MCP."
                ),
            )

    def check_server_startup(
        self, name: str, server_config: dict, timeout: int = 5
    ) -> CheckResult:
        """Test actual server startup with JSON-RPC initialize.

        Args:
            name: Server name.
            server_config: Server configuration dict.
            timeout: Timeout for startup test in seconds.

        Returns:
            CheckResult indicating if server starts and responds.
        """
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        env_config = server_config.get("env", {})

        # Prepare environment
        env = os.environ.copy()
        for key, value in env_config.items():
            # Expand ${VAR} references
            expanded_value = os.path.expandvars(str(value))
            env[key] = expanded_value

        # Ensure PYTHONUNBUFFERED for Python servers
        if command in ("python", "python3") or any(
            arg.endswith(".py") for arg in args
        ):
            env["PYTHONUNBUFFERED"] = "1"

        # Build full command
        full_command = [command] + args

        # JSON-RPC initialize request per MCP spec
        initialize_request = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-health-check",
                        "version": "1.0.0",
                    },
                },
            }
        )

        try:
            # Start the process
            process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )

            try:
                # Send initialize request
                stdout, stderr = process.communicate(
                    input=initialize_request + "\n", timeout=timeout
                )

                # Check for valid JSON-RPC response
                if stdout:
                    try:
                        response = json.loads(stdout.strip().split("\n")[0])
                        if "result" in response:
                            server_info = response.get("result", {}).get(
                                "serverInfo", {}
                            )
                            server_name = server_info.get("name", "unknown")
                            return CheckResult(
                                name=f"Server '{name}' Startup",
                                status=CheckStatus.PASS,
                                message=f"Server responds (name: {server_name})",
                                details=f"Protocol version: {response.get('result', {}).get('protocolVersion', 'unknown')}",
                            )
                        elif "error" in response:
                            error_msg = response.get("error", {}).get(
                                "message", "Unknown error"
                            )
                            return CheckResult(
                                name=f"Server '{name}' Startup",
                                status=CheckStatus.FAIL,
                                message=f"Server error: {error_msg}",
                                details=stderr if stderr else None,
                            )
                    except json.JSONDecodeError:
                        pass

                # Non-JSON response
                return CheckResult(
                    name=f"Server '{name}' Startup",
                    status=CheckStatus.WARN,
                    message="Server started but response not valid JSON-RPC",
                    details=f"stdout: {stdout[:200]}" if stdout else f"stderr: {stderr[:200]}" if stderr else None,
                )

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                return CheckResult(
                    name=f"Server '{name}' Startup",
                    status=CheckStatus.WARN,
                    message=f"Server did not respond within {timeout}s (may be slow to start)",
                    fix_suggestion="Server might be slow to initialize; increase timeout if needed",
                )

        except FileNotFoundError:
            return CheckResult(
                name=f"Server '{name}' Startup",
                status=CheckStatus.FAIL,
                message=f"Command not found: {command}",
                fix_suggestion=f"Install {command} or update the command path",
            )
        except PermissionError:
            return CheckResult(
                name=f"Server '{name}' Startup",
                status=CheckStatus.FAIL,
                message=f"Permission denied executing {command}",
                fix_suggestion=f"Check execute permissions: chmod +x {command}",
            )
        except Exception as e:
            return CheckResult(
                name=f"Server '{name}' Startup",
                status=CheckStatus.FAIL,
                message=f"Startup failed: {type(e).__name__}",
                details=str(e),
            )

    def check_servers(self) -> None:
        """Run all server-level checks."""
        if not self.config:
            return

        servers = self.config.get("mcpServers", {})
        if not servers:
            return

        self._log("\n=== MCP Servers ===")

        for name, server_config in servers.items():
            self._log(f"\n--- Server: {name} ---")

            # Check command availability
            result = self.check_server_command(name, server_config)
            self.report.add(result)
            self._log_check(result)

            if result.status == CheckStatus.FAIL:
                continue

            # Check PYTHONUNBUFFERED for Python servers
            result = self.check_python_server_env(name, server_config)
            self.report.add(result)
            self._log_check(result)

            # Test actual server startup
            result = self.check_server_startup(name, server_config)
            self.report.add(result)
            self._log_check(result)

    def check_port_available(self, port: int, host: str = "127.0.0.1") -> CheckResult:
        """Check if a port is available for binding.

        Args:
            port: Port number to check.
            host: Host to check on.

        Returns:
            CheckResult indicating port availability.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    # Port is in use (connection succeeded)
                    return CheckResult(
                        name=f"Port {port}",
                        status=CheckStatus.WARN,
                        message=f"Port {port} is in use",
                        fix_suggestion=f"Check what's using port {port}: lsof -i :{port}",
                    )
                else:
                    # Port is available
                    return CheckResult(
                        name=f"Port {port}",
                        status=CheckStatus.PASS,
                        message=f"Port {port} is available",
                    )
        except socket.error as e:
            return CheckResult(
                name=f"Port {port}",
                status=CheckStatus.PASS,
                message=f"Port {port} appears available",
                details=str(e),
            )

    def check_common_ports(self) -> None:
        """Check common MCP/DevSkyy ports."""
        self._log("\n=== Port Availability ===")

        common_ports = [
            8000,  # FastAPI default
            3000,  # Node.js default
            5000,  # Flask default
            8080,  # Alternative HTTP
        ]

        for port in common_ports:
            result = self.check_port_available(port)
            self.report.add(result)
            self._log_check(result)

    def check_wordpress_env(self) -> None:
        """Check WordPress/WooCommerce environment variables."""
        self._log("\n=== WordPress/WooCommerce Environment ===")

        # Load .env if available
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        # WordPress variables
        wp_configured = 0
        for var in self.WORDPRESS_ENV_VARS:
            value = os.environ.get(var)
            if value:
                wp_configured += 1

        if wp_configured == 0:
            result = CheckResult(
                name="WordPress Credentials",
                status=CheckStatus.WARN,
                message="No WordPress credentials configured",
                fix_suggestion=(
                    "Set WORDPRESS_CLIENT_ID/SECRET for WordPress.com or "
                    "SKYY_ROSE_SITE_URL/USERNAME/PASSWORD for self-hosted"
                ),
            )
        elif wp_configured < 3:
            result = CheckResult(
                name="WordPress Credentials",
                status=CheckStatus.WARN,
                message=f"Partial WordPress config ({wp_configured} of {len(self.WORDPRESS_ENV_VARS)} vars set)",
                details=f"Set: {[v for v in self.WORDPRESS_ENV_VARS if os.environ.get(v)]}",
            )
        else:
            result = CheckResult(
                name="WordPress Credentials",
                status=CheckStatus.PASS,
                message=f"WordPress configured ({wp_configured} vars set)",
            )

        self.report.add(result)
        self._log_check(result)

        # WooCommerce variables
        wc_configured = sum(1 for var in self.WOOCOMMERCE_ENV_VARS if os.environ.get(var))

        if wc_configured == 0:
            result = CheckResult(
                name="WooCommerce Credentials",
                status=CheckStatus.WARN,
                message="No WooCommerce credentials configured",
                fix_suggestion="Set WOOCOMMERCE_CONSUMER_KEY and WOOCOMMERCE_CONSUMER_SECRET",
            )
        elif wc_configured < 2:
            result = CheckResult(
                name="WooCommerce Credentials",
                status=CheckStatus.WARN,
                message=f"Partial WooCommerce config ({wc_configured} of {len(self.WOOCOMMERCE_ENV_VARS)} vars set)",
            )
        else:
            result = CheckResult(
                name="WooCommerce Credentials",
                status=CheckStatus.PASS,
                message=f"WooCommerce configured ({wc_configured} vars set)",
            )

        self.report.add(result)
        self._log_check(result)

    def check_wordpress_connectivity(self) -> None:
        """Check connectivity to WordPress/WooCommerce sites."""
        self._log("\n=== WordPress/WooCommerce Connectivity ===")

        # Try to load dotenv
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass

        # Check Skyy Rose site
        site_url = os.environ.get("SKYY_ROSE_SITE_URL")
        if site_url:
            try:
                import urllib.request
                import urllib.error

                # Test REST API endpoint
                api_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/"
                req = urllib.request.Request(api_url, method="HEAD")
                req.add_header("User-Agent", "MCP-Health-Check/1.0")

                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        if response.status == 200:
                            result = CheckResult(
                                name="WordPress Site Connectivity",
                                status=CheckStatus.PASS,
                                message=f"Connected to {site_url}",
                            )
                        else:
                            result = CheckResult(
                                name="WordPress Site Connectivity",
                                status=CheckStatus.WARN,
                                message=f"HTTP {response.status} from {site_url}",
                            )
                except urllib.error.HTTPError as e:
                    if e.code == 401:
                        result = CheckResult(
                            name="WordPress Site Connectivity",
                            status=CheckStatus.PASS,
                            message=f"Site reachable (auth required) at {site_url}",
                        )
                    else:
                        result = CheckResult(
                            name="WordPress Site Connectivity",
                            status=CheckStatus.WARN,
                            message=f"HTTP {e.code} from {site_url}",
                            details=str(e.reason),
                        )
                except urllib.error.URLError as e:
                    result = CheckResult(
                        name="WordPress Site Connectivity",
                        status=CheckStatus.FAIL,
                        message=f"Cannot connect to {site_url}",
                        details=str(e.reason),
                        fix_suggestion="Check network connectivity and site availability",
                    )
            except Exception as e:
                result = CheckResult(
                    name="WordPress Site Connectivity",
                    status=CheckStatus.FAIL,
                    message=f"Connection test failed: {type(e).__name__}",
                    details=str(e),
                )

            self.report.add(result)
            self._log_check(result)
        else:
            result = CheckResult(
                name="WordPress Site Connectivity",
                status=CheckStatus.SKIP,
                message="SKYY_ROSE_SITE_URL not configured",
            )
            self.report.add(result)
            self._log_check(result)

        # Check WooCommerce
        wc_url = os.environ.get("WOOCOMMERCE_STORE_URL")
        if wc_url:
            try:
                import urllib.request
                import urllib.error

                api_url = f"{wc_url.rstrip('/')}/wp-json/wc/v3/"
                req = urllib.request.Request(api_url, method="HEAD")
                req.add_header("User-Agent", "MCP-Health-Check/1.0")

                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        result = CheckResult(
                            name="WooCommerce API Connectivity",
                            status=CheckStatus.PASS,
                            message=f"Connected to WooCommerce at {wc_url}",
                        )
                except urllib.error.HTTPError as e:
                    if e.code in (401, 403):
                        result = CheckResult(
                            name="WooCommerce API Connectivity",
                            status=CheckStatus.PASS,
                            message=f"WooCommerce API reachable (auth required)",
                        )
                    else:
                        result = CheckResult(
                            name="WooCommerce API Connectivity",
                            status=CheckStatus.WARN,
                            message=f"HTTP {e.code} from WooCommerce API",
                        )
                except urllib.error.URLError as e:
                    result = CheckResult(
                        name="WooCommerce API Connectivity",
                        status=CheckStatus.FAIL,
                        message=f"Cannot connect to WooCommerce at {wc_url}",
                        details=str(e.reason),
                    )
            except Exception as e:
                result = CheckResult(
                    name="WooCommerce API Connectivity",
                    status=CheckStatus.FAIL,
                    message=f"Connection test failed: {type(e).__name__}",
                    details=str(e),
                )

            self.report.add(result)
            self._log_check(result)
        else:
            result = CheckResult(
                name="WooCommerce API Connectivity",
                status=CheckStatus.SKIP,
                message="WOOCOMMERCE_STORE_URL not configured",
            )
            self.report.add(result)
            self._log_check(result)

    def run_all_checks(self) -> HealthCheckReport:
        """Run all health checks and return the report.

        Returns:
            HealthCheckReport with all check results.
        """
        if not self.json_output:
            logger.info("=" * 60)
            logger.info("MCP Health Check - DevSkyy Enterprise")
            logger.info("=" * 60)
            logger.info(f"Platform: {platform.system()} {platform.release()}")
            logger.info(f"Config Path: {self.config_path}")

        # Run all check categories
        self.check_system_dependencies()
        self.check_mcp_config()
        self.check_servers()
        self.check_common_ports()
        self.check_wordpress_env()
        self.check_wordpress_connectivity()

        # Print summary
        if not self.json_output:
            logger.info("\n" + "=" * 60)
            logger.info("Summary")
            logger.info("=" * 60)
            logger.info(f"Total Checks: {len(self.report.checks)}")
            logger.info(f"  Passed: {self.report.passed}")
            logger.info(f"  Warnings: {self.report.warned}")
            logger.info(f"  Failed: {self.report.failed}")
            logger.info(f"  Skipped: {self.report.skipped}")
            logger.info("")

            if self.report.success:
                logger.info("Result: All critical checks passed")
            else:
                logger.info("Result: Some checks failed - review issues above")

        return self.report


def main() -> int:
    """Main entry point for the MCP health check tool.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="MCP Health Check Diagnostic Tool for DevSkyy Enterprise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           Run with auto-detected config
  %(prog)s --config ./my-config.json Use specific config file
  %(prog)s --verbose                 Show detailed output
  %(prog)s --json                    Output results as JSON

For DevSkyy multi-agent system targeting skyyrose.co WordPress/WooCommerce.
        """,
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to MCP configuration JSON file",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output with additional details",
    )

    parser.add_argument(
        "--json",
        "-j",
        action="store_true",
        dest="json_output",
        help="Output results as JSON (for programmatic use)",
    )

    args = parser.parse_args()

    # Run health checks
    checker = MCPHealthChecker(
        config_path=args.config,
        verbose=args.verbose,
        json_output=args.json_output,
    )

    report = checker.run_all_checks()

    # Output JSON if requested
    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))

    # Return appropriate exit code
    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
