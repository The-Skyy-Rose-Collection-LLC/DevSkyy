# mcp/serena_client.py
"""
Serena MCP Client for DevSkyy.

Provides code analysis and validation capabilities for:
- Code quality analysis
- Security scanning
- Refactoring suggestions
- Symbol-level operations

Usage:
    from mcp.serena_client import serena_client

    analysis = await serena_client.analyze_file("api/endpoints.py")
    issues = await serena_client.find_issues(code_snippet)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from mcp.server_manager import mcp_manager

logger = logging.getLogger(__name__)


class SerenaClient:
    """
    Serena MCP client for code analysis and validation.

    Used for:
    - Code quality analysis
    - Security scanning
    - Refactoring suggestions
    - Symbol-level code operations
    """

    SERVER_ID = "serena"

    async def analyze_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Analyze a single file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Analysis results
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "analyze_file",
            {"path": str(file_path)},
        )
        return result.data if result.success else {"error": result.error}

    async def analyze_directory(
        self,
        directory: str | Path,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze all files in a directory.

        Args:
            directory: Path to the directory
            include_patterns: File patterns to include
            exclude_patterns: File patterns to exclude

        Returns:
            Analysis results
        """
        args: dict[str, Any] = {"path": str(directory)}

        if include_patterns:
            args["include"] = include_patterns
        if exclude_patterns:
            args["exclude"] = exclude_patterns

        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "analyze_directory",
            args,
        )
        return result.data if result.success else {"error": result.error}

    async def find_issues(
        self,
        code: str,
        language: str = "python",
    ) -> list[dict[str, Any]]:
        """
        Find issues in a code snippet.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            List of issues found
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "find_issues",
            {
                "code": code,
                "language": language,
            },
        )
        return result.data.get("issues", []) if result.success else []

    async def suggest_refactoring(
        self,
        code: str,
        language: str = "python",
    ) -> list[dict[str, Any]]:
        """
        Get refactoring suggestions for code.

        Args:
            code: Code to analyze
            language: Programming language

        Returns:
            List of refactoring suggestions
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "suggest_refactoring",
            {
                "code": code,
                "language": language,
            },
        )
        return result.data.get("suggestions", []) if result.success else []

    async def validate_security(self, file_path: str | Path) -> dict[str, Any]:
        """
        Run security validation on a file.

        Args:
            file_path: Path to the file

        Returns:
            Security scan results
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "security_scan",
            {"path": str(file_path)},
        )
        return result.data if result.success else {"error": result.error}

    async def get_symbols(self, file_path: str | Path) -> list[dict[str, Any]]:
        """
        Get symbols (functions, classes, etc.) from a file.

        Args:
            file_path: Path to the file

        Returns:
            List of symbols
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "get_symbols",
            {"path": str(file_path)},
        )
        return result.data.get("symbols", []) if result.success else []

    async def find_references(
        self,
        symbol_name: str,
        file_path: str | Path | None = None,
    ) -> list[dict[str, Any]]:
        """
        Find all references to a symbol.

        Args:
            symbol_name: Name of the symbol
            file_path: Optional file to search in

        Returns:
            List of references
        """
        args: dict[str, Any] = {"symbol": symbol_name}
        if file_path:
            args["path"] = str(file_path)

        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "find_references",
            args,
        )
        return result.data.get("references", []) if result.success else []

    async def full_project_audit(
        self,
        project_root: str | Path,
    ) -> dict[str, Any]:
        """
        Run full project audit.

        Args:
            project_root: Root directory of the project

        Returns:
            Comprehensive audit results
        """
        results: dict[str, Any] = {
            "files_analyzed": 0,
            "total_issues": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "files": [],
        }

        project_path = Path(project_root)

        # Find all Python files
        py_files = list(project_path.rglob("*.py"))

        for py_file in py_files:
            # Skip cache and venv directories
            if any(
                part in str(py_file) for part in ["__pycache__", ".venv", "node_modules", ".git"]
            ):
                continue

            try:
                analysis = await self.analyze_file(py_file)
                results["files_analyzed"] += 1

                issues = analysis.get("issues", [])
                results["total_issues"] += len(issues)

                for issue in issues:
                    severity = issue.get("severity", "low").lower()
                    if severity in results:
                        results[severity] += 1

                if issues:
                    results["files"].append(
                        {
                            "path": str(py_file),
                            "issues": issues,
                        }
                    )

            except Exception as e:
                results["files"].append(
                    {
                        "path": str(py_file),
                        "error": str(e),
                    }
                )

        return results

    async def check_code_style(
        self,
        code: str,
        style_guide: str = "pep8",
    ) -> list[dict[str, Any]]:
        """
        Check code against a style guide.

        Args:
            code: Code to check
            style_guide: Style guide to use (pep8, google, etc.)

        Returns:
            List of style violations
        """
        result = await mcp_manager.call_tool(
            self.SERVER_ID,
            "check_style",
            {
                "code": code,
                "style": style_guide,
            },
        )
        return result.data.get("violations", []) if result.success else []


# Singleton instance
serena_client = SerenaClient()
