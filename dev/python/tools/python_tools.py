"""
Python Analysis Tools for Coding Architect Agent (Python SDK)

MCP tools for Python code analysis, type checking,
linting, and project configuration validation.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """Result from a tool execution."""

    content: str
    is_error: bool = False


class PythonTools:
    """
    Python Analysis Tools

    Provides methods for:
    - Type checking with mypy/pyright
    - Linting with ruff/pylint/flake8
    - Dependency analysis
    - Code complexity metrics
    - Virtual environment management
    """

    @staticmethod
    def type_check(
        target: str,
        checker: str = "mypy",
        strict: bool = True,
    ) -> dict[str, Any]:
        """
        Run Python type checking.

        Args:
            target: File path or directory to type check
            checker: Type checker (mypy, pyright, basedpyright)
            strict: Enable strict mode

        Returns:
            Command and configuration for type checking
        """
        commands = {
            "mypy": {
                "cmd": f"mypy {'--strict ' if strict else ''}{target}",
                "install": "pip install mypy",
            },
            "pyright": {
                "cmd": f"pyright {'--strict ' if strict else ''}{target}",
                "install": "pip install pyright",
            },
            "basedpyright": {
                "cmd": f"basedpyright {'--strict ' if strict else ''}{target}",
                "install": "pip install basedpyright",
            },
        }

        selected = commands.get(checker, commands["mypy"])

        return {
            "checker": checker,
            "command": selected["cmd"],
            "install": selected["install"],
            "strictModeSettings": {
                "mypy": [
                    "--disallow-untyped-defs",
                    "--disallow-incomplete-defs",
                    "--check-untyped-defs",
                    "--no-implicit-optional",
                    "--warn-redundant-casts",
                    "--warn-return-any",
                ],
                "pyright": {
                    "typeCheckingMode": "strict",
                    "reportMissingTypeStubs": True,
                },
            },
        }

    @staticmethod
    def lint(
        target: str,
        linter: str = "ruff",
        fix: bool = False,
        output_format: str = "json",
    ) -> dict[str, Any]:
        """
        Run Python linting.

        Args:
            target: File or directory to lint
            linter: Linter to use (ruff, pylint, flake8)
            fix: Auto-fix fixable issues
            output_format: Output format (text, json, github)

        Returns:
            Linting command and recommendations
        """
        commands = {
            "ruff": {
                "check": f"ruff check {target} --output-format {output_format}",
                "fix": f"ruff check {target} --fix",
                "install": "pip install ruff",
            },
            "pylint": {
                "check": f"pylint {target} --output-format={'json' if output_format == 'json' else 'text'}",
                "install": "pip install pylint",
            },
            "flake8": {
                "check": f"flake8 {target} --format={'json' if output_format == 'json' else 'default'}",
                "install": "pip install flake8",
            },
        }

        selected = commands.get(linter, commands["ruff"])
        cmd = selected.get("fix") if fix and "fix" in selected else selected["check"]

        return {
            "linter": linter,
            "command": cmd,
            "install": selected["install"],
            "recommendedRuffRules": {
                "enabled": ["E", "F", "W", "I", "N", "UP", "B", "A", "C4", "SIM"],
                "description": {
                    "E": "pycodestyle errors",
                    "F": "pyflakes",
                    "W": "pycodestyle warnings",
                    "I": "isort",
                    "N": "pep8-naming",
                    "UP": "pyupgrade",
                    "B": "flake8-bugbear",
                    "A": "flake8-builtins",
                    "C4": "flake8-comprehensions",
                    "SIM": "flake8-simplify",
                },
            },
        }

    @staticmethod
    def format_code(
        target: str,
        formatter: str = "ruff",
        check: bool = False,
        line_length: int = 88,
    ) -> dict[str, Any]:
        """
        Format Python code.

        Args:
            target: File or directory to format
            formatter: Formatter (black, ruff, autopep8)
            check: Check only, don't modify files
            line_length: Maximum line length

        Returns:
            Formatting command and configuration
        """
        commands = {
            "black": {
                "cmd": f"black {'--check ' if check else ''}--line-length {line_length} {target}",
                "install": "pip install black",
            },
            "ruff": {
                "cmd": f"ruff format {'--check ' if check else ''}--line-length {line_length} {target}",
                "install": "pip install ruff",
            },
            "autopep8": {
                "cmd": f"autopep8 {'--diff' if check else '--in-place'} --max-line-length {line_length} {target}",
                "install": "pip install autopep8",
            },
        }

        selected = commands.get(formatter, commands["ruff"])

        return {
            "formatter": formatter,
            "command": selected["cmd"],
            "install": selected["install"],
            "isortIntegration": {
                "command": f"isort {'--check-only ' if check else ''}{target}",
                "ruffHasIsort": "Ruff includes isort functionality with the 'I' rule",
            },
        }

    @staticmethod
    def dependency_audit(
        requirements_path: str = "requirements.txt",
        check_security: bool = True,
        check_outdated: bool = True,
    ) -> dict[str, Any]:
        """
        Audit Python project dependencies.

        Args:
            requirements_path: Path to requirements file
            check_security: Run security audit
            check_outdated: Check for outdated packages

        Returns:
            Audit commands and best practices
        """
        commands = []

        if check_outdated:
            commands.append({
                "name": "Check outdated packages",
                "command": "pip list --outdated --format json",
            })

        if check_security:
            commands.append({
                "name": "Security audit (pip-audit)",
                "command": "pip-audit --format json",
                "install": "pip install pip-audit",
            })
            commands.append({
                "name": "Security audit (safety)",
                "command": f"safety check -r {requirements_path} --json",
                "install": "pip install safety",
            })

        commands.append({
            "name": "Dependency tree",
            "command": "pipdeptree --json",
            "install": "pip install pipdeptree",
        })

        return {
            "requirementsPath": requirements_path,
            "commands": commands,
            "bestPractices": [
                "Pin exact versions in production (package==1.2.3)",
                "Use >= for development dependencies",
                "Regularly run pip-audit for security updates",
                "Consider using poetry or pip-tools for lock files",
            ],
        }

    @staticmethod
    def venv_info(python_path: str | None = None) -> dict[str, Any]:
        """
        Get virtual environment information.

        Args:
            python_path: Path to Python interpreter

        Returns:
            Environment commands and creation options
        """
        python = python_path or "python3"

        return {
            "commands": [
                {"name": "Python version", "command": f"{python} --version"},
                {"name": "Pip version", "command": f"{python} -m pip --version"},
                {"name": "Virtual env location", "command": f'{python} -c "import sys; print(sys.prefix)"'},
                {"name": "Installed packages", "command": f"{python} -m pip list --format json"},
            ],
            "venvCreation": {
                "venv": "python3 -m venv .venv",
                "virtualenv": "virtualenv .venv",
                "conda": "conda create -n myenv python=3.11",
                "uv": "uv venv .venv",
            },
            "activation": {
                "unix": "source .venv/bin/activate",
                "windows": ".venv\\Scripts\\activate",
                "fish": "source .venv/bin/activate.fish",
            },
        }

    @staticmethod
    def analyze_complexity(
        target: str,
        metrics: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze Python code complexity.

        Args:
            target: File or directory to analyze
            metrics: Metrics to compute (cc, mi, raw, hal)

        Returns:
            Complexity commands and thresholds
        """
        if metrics is None:
            metrics = ["cc", "mi"]

        metric_commands = {
            "cc": {
                "cmd": f"radon cc {target} -a -j",
                "description": "Cyclomatic Complexity",
            },
            "mi": {
                "cmd": f"radon mi {target} -j",
                "description": "Maintainability Index",
            },
            "raw": {
                "cmd": f"radon raw {target} -j",
                "description": "Raw metrics - LOC, LLOC, SLOC",
            },
            "hal": {
                "cmd": f"radon hal {target} -j",
                "description": "Halstead metrics",
            },
        }

        commands = [
            {"metric": m, **metric_commands[m]}
            for m in metrics
            if m in metric_commands
        ]

        return {
            "target": target,
            "commands": commands,
            "install": "pip install radon",
            "complexityGrades": {
                "A": "1-5: Low complexity, easy to maintain",
                "B": "6-10: Moderate complexity",
                "C": "11-20: High complexity, consider refactoring",
                "D": "21-30: Very high complexity",
                "E": "31-40: Extremely complex",
                "F": "40+: Unmaintainable",
            },
            "maintainabilityIndex": {
                "100-80": "Excellent maintainability",
                "79-50": "Moderate maintainability",
                "49-20": "Poor maintainability",
                "19-0": "Very poor, high risk",
            },
        }

    @staticmethod
    def test_runner(
        target: str = "tests/",
        verbose: bool = True,
        coverage: bool = True,
        markers: str | None = None,
        parallel: bool = False,
    ) -> dict[str, Any]:
        """
        Run Python tests with pytest.

        Args:
            target: Test directory or file
            verbose: Verbose output
            coverage: Run with coverage
            markers: Pytest markers to filter
            parallel: Run tests in parallel

        Returns:
            Test command and configuration
        """
        flags = []
        if verbose:
            flags.append("-v")
        if coverage:
            flags.append("--cov=. --cov-report=term-missing")
        if markers:
            flags.append(f'-m "{markers}"')
        if parallel:
            flags.append("-n auto")

        command = f"pytest {target} {' '.join(flags)}"

        install_deps = ["pytest"]
        if coverage:
            install_deps.append("pytest-cov")
        if parallel:
            install_deps.append("pytest-xdist")

        return {
            "command": command,
            "install": f"pip install {' '.join(install_deps)}",
            "usefulFlags": {
                "-x": "Stop on first failure",
                "-s": "Show print statements",
                "--lf": "Run last failed tests only",
                "--ff": "Run failed tests first",
                "-k 'pattern'": "Run tests matching pattern",
                "--durations=10": "Show 10 slowest tests",
            },
            "pytestIniExample": """[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --tb=short
markers =
    slow: marks tests as slow
    integration: integration tests""",
        }

    @staticmethod
    def generate_stubs(
        package: str,
        output: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate type stubs for Python packages.

        Args:
            package: Package name or path
            output: Output directory for stubs

        Returns:
            Generation commands and options
        """
        return {
            "commands": {
                "stubgen": {
                    "command": f"stubgen {package} {f'-o {output}' if output else ''}",
                    "description": "Generate stubs from source code (mypy)",
                    "install": "pip install mypy",
                },
                "pyright": {
                    "command": f"pyright --createstub {package}",
                    "description": "Generate stubs using pyright",
                    "install": "pip install pyright",
                },
                "monkeytype": {
                    "command": f"monkeytype stub {package}",
                    "description": "Generate stubs from runtime type collection",
                    "install": "pip install monkeytype",
                },
            },
            "typeshed": {
                "description": "Check if stubs exist in typeshed",
                "searchCommand": f"pip install types-{package}",
            },
        }
