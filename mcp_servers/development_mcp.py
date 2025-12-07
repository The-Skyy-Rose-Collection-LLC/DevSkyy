"""
DevSkyy Development MCP Server

Code generation, testing, CI/CD, and quality tools for the DevSkyy platform.
Integrates scanner_v2.py, fixer_v2.py, and advanced_code_generation_agent.py.

Tools:
- analyze_code: Syntax/security analysis
- fix_code_issues: Automated code fixes
- generate_code: AI code generation
- run_tests: Test execution + coverage
- generate_tests: AI-generated tests
- lint_and_format: Ruff, Black, isort
- security_scan: Bandit, pip-audit
- git_operations: Commit, branch, PR

Author: DevSkyy Enterprise
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_servers.base_mcp_server import BaseMCPServer


# Optional imports for advanced features
try:
    import ast
    AST_AVAILABLE = True
except ImportError:
    AST_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class CodeAnalyzer:
    """Analyze Python code for issues, security, and quality."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    def analyze_syntax(self, code: str) -> dict[str, Any]:
        """Check Python syntax validity."""
        try:
            ast.parse(code)
            return {"valid": True, "errors": []}
        except SyntaxError as e:
            return {
                "valid": False,
                "errors": [{
                    "line": e.lineno,
                    "offset": e.offset,
                    "message": str(e.msg),
                }]
            }

    def analyze_imports(self, code: str) -> dict[str, Any]:
        """Analyze imports in Python code."""
        try:
            tree = ast.parse(code)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                        })
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.append({
                            "type": "from",
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                        })
            return {"imports": imports, "count": len(imports)}
        except Exception as e:
            return {"imports": [], "count": 0, "error": str(e)}

    def analyze_functions(self, code: str) -> dict[str, Any]:
        """Analyze functions and classes in Python code."""
        try:
            tree = ast.parse(code)
            functions = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "async": isinstance(node, ast.AsyncFunctionDef),
                        "args": [arg.arg for arg in node.args.args],
                        "has_docstring": (
                            len(node.body) > 0 and
                            isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)
                        ),
                        "decorators": [
                            ast.unparse(d) if hasattr(ast, 'unparse') else str(d)
                            for d in node.decorator_list
                        ],
                    }
                    functions.append(func_info)
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "bases": [
                            ast.unparse(b) if hasattr(ast, 'unparse') else str(b)
                            for b in node.bases
                        ],
                        "methods": [],
                    }
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                            class_info["methods"].append(item.name)
                    classes.append(class_info)

            return {
                "functions": functions,
                "classes": classes,
                "function_count": len(functions),
                "class_count": len(classes),
            }
        except Exception as e:
            return {"functions": [], "classes": [], "error": str(e)}

    def check_security_patterns(self, code: str) -> dict[str, Any]:
        """Check for common security issues."""
        issues = []
        lines = code.split('\n')

        # Security patterns to detect
        patterns = [
            (r'eval\s*\(', 'eval() usage - potential code injection', 'HIGH'),
            (r'exec\s*\(', 'exec() usage - potential code injection', 'HIGH'),
            (r'subprocess\..*shell\s*=\s*True', 'shell=True in subprocess - command injection risk', 'HIGH'),
            (r'os\.system\s*\(', 'os.system() usage - prefer subprocess', 'MEDIUM'),
            (r'pickle\.load', 'pickle.load() - potential arbitrary code execution', 'HIGH'),
            (r'yaml\.load\s*\([^,]+\)', 'yaml.load() without Loader - use safe_load()', 'MEDIUM'),
            (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password detected', 'CRITICAL'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key detected', 'CRITICAL'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'Hardcoded secret detected', 'CRITICAL'),
            (r'\.format\s*\([^)]*\)\s*$', 'String formatting - consider f-strings or parameterized queries', 'LOW'),
            (r'%\s*\(', 'Old-style string formatting - consider f-strings', 'LOW'),
        ]

        import re
        for i, line in enumerate(lines, 1):
            for pattern, message, severity in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "line": i,
                        "severity": severity,
                        "message": message,
                        "code": line.strip()[:100],
                    })

        return {
            "issues": issues,
            "issue_count": len(issues),
            "critical": len([i for i in issues if i["severity"] == "CRITICAL"]),
            "high": len([i for i in issues if i["severity"] == "HIGH"]),
            "medium": len([i for i in issues if i["severity"] == "MEDIUM"]),
            "low": len([i for i in issues if i["severity"] == "LOW"]),
        }


class CodeFixer:
    """Automated code fixes and improvements."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    async def run_ruff_fix(self, file_path: str) -> dict[str, Any]:
        """Run Ruff linter with auto-fix."""
        try:
            result = subprocess.run(
                ["ruff", "check", "--fix", file_path],
                check=False, capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "fixed": "--fix" in result.stdout or result.returncode == 0,
            }
        except FileNotFoundError:
            return {"success": False, "error": "Ruff not installed. Run: pip install ruff"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_black_format(self, file_path: str) -> dict[str, Any]:
        """Run Black formatter."""
        try:
            result = subprocess.run(
                ["black", "--line-length", "119", file_path],
                check=False, capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "formatted": "reformatted" in result.stderr or result.returncode == 0,
            }
        except FileNotFoundError:
            return {"success": False, "error": "Black not installed. Run: pip install black"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_isort_fix(self, file_path: str) -> dict[str, Any]:
        """Run isort to sort imports."""
        try:
            result = subprocess.run(
                ["isort", "--profile", "black", file_path],
                check=False, capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except FileNotFoundError:
            return {"success": False, "error": "isort not installed. Run: pip install isort"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class TestRunner:
    """Run tests and generate coverage reports."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    async def run_pytest(
        self,
        test_path: str | None = None,
        coverage: bool = True,
        verbose: bool = True,
        markers: str | None = None,
    ) -> dict[str, Any]:
        """Run pytest with optional coverage."""
        cmd = ["pytest"]

        if test_path:
            cmd.append(test_path)
        else:
            cmd.append(str(self.project_root / "tests"))

        if verbose:
            cmd.append("-v")

        if coverage:
            cmd.extend(["--cov=.", "--cov-report=json", "--cov-report=term"])

        if markers:
            cmd.extend(["-m", markers])

        try:
            result = subprocess.run(
                cmd,
                check=False, capture_output=True,
                text=True,
                timeout=300,  # 5 minutes max
                cwd=str(self.project_root),
            )

            # Parse coverage if available
            coverage_data = {}
            coverage_file = self.project_root / "coverage.json"
            if coverage and coverage_file.exists():
                try:
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                except Exception:
                    pass

            # Parse test results
            passed = result.stdout.count(" passed")
            failed = result.stdout.count(" failed")
            errors = result.stdout.count(" error")
            skipped = result.stdout.count(" skipped")

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "summary": {
                    "passed": passed,
                    "failed": failed,
                    "errors": errors,
                    "skipped": skipped,
                },
                "coverage": coverage_data.get("totals", {}) if coverage_data else None,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timed out (5 min limit)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_mypy(self, path: str | None = None) -> dict[str, Any]:
        """Run MyPy type checking."""
        cmd = ["mypy"]

        if path:
            cmd.append(path)
        else:
            cmd.append(str(self.project_root))

        cmd.extend(["--ignore-missing-imports", "--no-error-summary"])

        try:
            result = subprocess.run(
                cmd,
                check=False, capture_output=True,
                text=True,
                timeout=120,
            )

            # Count errors
            error_lines = [l for l in result.stdout.split('\n') if 'error:' in l]

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
                "error_count": len(error_lines),
                "error_lines": error_lines[:20],  # First 20 errors
            }
        except FileNotFoundError:
            return {"success": False, "error": "MyPy not installed. Run: pip install mypy"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class SecurityScanner:
    """Security scanning tools."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    async def run_bandit(self, path: str | None = None) -> dict[str, Any]:
        """Run Bandit security scanner."""
        target = path or str(self.project_root)

        try:
            result = subprocess.run(
                ["bandit", "-r", "-f", "json", target],
                check=False, capture_output=True,
                text=True,
                timeout=120,
            )

            try:
                report = json.loads(result.stdout)
                return {
                    "success": True,
                    "results": report.get("results", [])[:20],  # First 20 issues
                    "metrics": report.get("metrics", {}),
                    "issue_count": len(report.get("results", [])),
                }
            except json.JSONDecodeError:
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "errors": result.stderr,
                }
        except FileNotFoundError:
            return {"success": False, "error": "Bandit not installed. Run: pip install bandit"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run_pip_audit(self) -> dict[str, Any]:
        """Run pip-audit for dependency vulnerabilities."""
        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                check=False, capture_output=True,
                text=True,
                timeout=120,
            )

            try:
                vulnerabilities = json.loads(result.stdout)
                return {
                    "success": result.returncode == 0,
                    "vulnerabilities": vulnerabilities[:20],  # First 20
                    "count": len(vulnerabilities),
                    "has_critical": any(
                        v.get("severity", "").upper() == "CRITICAL"
                        for v in vulnerabilities
                    ),
                }
            except json.JSONDecodeError:
                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "errors": result.stderr,
                }
        except FileNotFoundError:
            return {"success": False, "error": "pip-audit not installed. Run: pip install pip-audit"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class CodeGenerator:
    """AI-powered code generation."""

    def __init__(self):
        self.anthropic = Anthropic() if ANTHROPIC_AVAILABLE else None

    async def generate_code(
        self,
        description: str,
        language: str = "python",
        context: str | None = None,
    ) -> dict[str, Any]:
        """Generate code using Claude."""
        if not self.anthropic:
            return {"success": False, "error": "Anthropic SDK not available"}

        prompt = f"""Generate {language} code for the following requirement:

{description}

{f"Context: {context}" if context else ""}

Requirements:
1. Follow best practices for {language}
2. Include type hints (for Python)
3. Include docstrings with Google-style format
4. Handle errors appropriately
5. Be production-ready

Return only the code, no explanations."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            code = response.content[0].text

            # Extract code from markdown blocks if present
            if "```" in code:
                import re
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', code, re.DOTALL)
                if code_blocks:
                    code = code_blocks[0]

            return {
                "success": True,
                "code": code.strip(),
                "language": language,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def generate_tests(
        self,
        code: str,
        test_framework: str = "pytest",
    ) -> dict[str, Any]:
        """Generate tests for given code."""
        if not self.anthropic:
            return {"success": False, "error": "Anthropic SDK not available"}

        prompt = f"""Generate {test_framework} tests for the following Python code:

```python
{code}
```

Requirements:
1. Test all public functions and methods
2. Include edge cases and error conditions
3. Use fixtures where appropriate
4. Include docstrings for test functions
5. Aim for high coverage
6. Follow pytest best practices

Return only the test code, no explanations."""

        try:
            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            test_code = response.content[0].text

            # Extract code from markdown blocks if present
            if "```" in test_code:
                import re
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', test_code, re.DOTALL)
                if code_blocks:
                    test_code = code_blocks[0]

            return {
                "success": True,
                "test_code": test_code.strip(),
                "framework": test_framework,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class GitOperations:
    """Git operations for version control."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent

    async def get_status(self) -> dict[str, Any]:
        """Get git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                check=False, capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )

            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    status = line[:2].strip()
                    filename = line[3:].strip()
                    files.append({"status": status, "file": filename})

            return {
                "success": True,
                "files": files,
                "changed_count": len(files),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_diff(self, staged: bool = False) -> dict[str, Any]:
        """Get git diff."""
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")

            result = subprocess.run(
                cmd,
                check=False, capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )

            return {
                "success": True,
                "diff": result.stdout[:10000],  # Limit output size
                "truncated": len(result.stdout) > 10000,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def create_branch(self, branch_name: str) -> dict[str, Any]:
        """Create and switch to a new branch."""
        try:
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=False, capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )

            return {
                "success": result.returncode == 0,
                "branch": branch_name,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def commit(self, message: str, files: list[str] | None = None) -> dict[str, Any]:
        """Stage and commit files."""
        try:
            # Stage files
            if files:
                for f in files:
                    subprocess.run(
                        ["git", "add", f],
                        check=False, cwd=str(self.project_root),
                    )
            else:
                subprocess.run(
                    ["git", "add", "-A"],
                    check=False, cwd=str(self.project_root),
                )

            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                check=False, capture_output=True,
                text=True,
                cwd=str(self.project_root),
            )

            return {
                "success": result.returncode == 0,
                "message": message,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class DevelopmentMCPServer(BaseMCPServer):
    """
    Development MCP Server for DevSkyy.

    Provides code generation, testing, CI/CD, and quality tools.
    """

    def __init__(self):
        super().__init__(
            name="devskyy-development",
            version="1.0.0",
        )
        self.analyzer = CodeAnalyzer()
        self.fixer = CodeFixer()
        self.test_runner = TestRunner()
        self.security_scanner = SecurityScanner()
        self.code_generator = CodeGenerator()
        self.git = GitOperations()

    def _register_tools(self) -> None:
        """Register all development tools."""

        # Code Analysis
        self._register_tool(
            name="analyze_code",
            description="Analyze Python code for syntax, imports, functions, and security issues",
            handler=self._analyze_code,
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to analyze",
                    },
                    "checks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Checks to run: syntax, imports, functions, security",
                        "default": ["syntax", "imports", "functions", "security"],
                    },
                },
                "required": ["code"],
            },
        )

        # Code Fixing
        self._register_tool(
            name="fix_code_issues",
            description="Automatically fix code issues using Ruff, Black, and isort",
            handler=self._fix_code_issues,
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to fix",
                    },
                    "fixers": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Fixers to run: ruff, black, isort",
                        "default": ["ruff", "black", "isort"],
                    },
                },
                "required": ["file_path"],
            },
        )

        # Code Generation
        self._register_tool(
            name="generate_code",
            description="Generate code using Claude AI",
            handler=self._generate_code,
            input_schema={
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "Description of code to generate",
                    },
                    "language": {
                        "type": "string",
                        "description": "Programming language",
                        "default": "python",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for generation",
                    },
                },
                "required": ["description"],
            },
        )

        # Test Running
        self._register_tool(
            name="run_tests",
            description="Run pytest with optional coverage",
            handler=self._run_tests,
            input_schema={
                "type": "object",
                "properties": {
                    "test_path": {
                        "type": "string",
                        "description": "Path to test file or directory",
                    },
                    "coverage": {
                        "type": "boolean",
                        "description": "Enable coverage reporting",
                        "default": True,
                    },
                    "markers": {
                        "type": "string",
                        "description": "Pytest markers to filter tests",
                    },
                },
            },
        )

        # Test Generation
        self._register_tool(
            name="generate_tests",
            description="Generate pytest tests for code using AI",
            handler=self._generate_tests,
            input_schema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to generate tests for",
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to file to generate tests for",
                    },
                },
            },
        )

        # Lint and Format
        self._register_tool(
            name="lint_and_format",
            description="Run linting (Ruff) and formatting (Black) on code",
            handler=self._lint_and_format,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to file or directory",
                    },
                    "fix": {
                        "type": "boolean",
                        "description": "Auto-fix issues",
                        "default": True,
                    },
                },
            },
        )

        # Security Scan
        self._register_tool(
            name="security_scan",
            description="Run security scans using Bandit and pip-audit",
            handler=self._security_scan,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to scan",
                    },
                    "include_dependencies": {
                        "type": "boolean",
                        "description": "Include pip-audit for dependency scan",
                        "default": True,
                    },
                },
            },
        )

        # Type Checking
        self._register_tool(
            name="type_check",
            description="Run MyPy type checking",
            handler=self._type_check,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to check",
                    },
                },
            },
        )

        # Git Operations
        self._register_tool(
            name="git_operations",
            description="Perform Git operations: status, diff, branch, commit",
            handler=self._git_operations,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "enum": ["status", "diff", "branch", "commit"],
                        "description": "Git operation to perform",
                    },
                    "branch_name": {
                        "type": "string",
                        "description": "Branch name (for branch operation)",
                    },
                    "message": {
                        "type": "string",
                        "description": "Commit message (for commit operation)",
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Files to commit",
                    },
                    "staged": {
                        "type": "boolean",
                        "description": "Show staged diff only",
                        "default": False,
                    },
                },
                "required": ["operation"],
            },
        )

        # Full Quality Check
        self._register_tool(
            name="full_quality_check",
            description="Run complete quality check: lint, type check, security, tests",
            handler=self._full_quality_check,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to check",
                    },
                    "skip_tests": {
                        "type": "boolean",
                        "description": "Skip test execution",
                        "default": False,
                    },
                },
            },
        )

    async def _analyze_code(self, args: dict[str, Any]) -> dict[str, Any]:
        """Analyze Python code."""
        code = args["code"]
        checks = args.get("checks", ["syntax", "imports", "functions", "security"])

        results = {}

        if "syntax" in checks:
            results["syntax"] = self.analyzer.analyze_syntax(code)

        if "imports" in checks:
            results["imports"] = self.analyzer.analyze_imports(code)

        if "functions" in checks:
            results["functions"] = self.analyzer.analyze_functions(code)

        if "security" in checks:
            results["security"] = self.analyzer.check_security_patterns(code)

        return {
            "success": True,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    async def _fix_code_issues(self, args: dict[str, Any]) -> dict[str, Any]:
        """Fix code issues in a file."""
        file_path = args["file_path"]
        fixers = args.get("fixers", ["ruff", "black", "isort"])

        results = {}

        if "isort" in fixers:
            results["isort"] = await self.fixer.run_isort_fix(file_path)

        if "black" in fixers:
            results["black"] = await self.fixer.run_black_format(file_path)

        if "ruff" in fixers:
            results["ruff"] = await self.fixer.run_ruff_fix(file_path)

        all_success = all(r.get("success", False) for r in results.values())

        return {
            "success": all_success,
            "results": results,
            "file": file_path,
        }

    async def _generate_code(self, args: dict[str, Any]) -> dict[str, Any]:
        """Generate code using AI."""
        return await self.code_generator.generate_code(
            description=args["description"],
            language=args.get("language", "python"),
            context=args.get("context"),
        )

    async def _run_tests(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run tests."""
        return await self.test_runner.run_pytest(
            test_path=args.get("test_path"),
            coverage=args.get("coverage", True),
            markers=args.get("markers"),
        )

    async def _generate_tests(self, args: dict[str, Any]) -> dict[str, Any]:
        """Generate tests for code."""
        code = args.get("code")

        if not code and args.get("file_path"):
            file_path = Path(args["file_path"])
            if file_path.exists():
                code = file_path.read_text()

        if not code:
            return {"success": False, "error": "No code provided"}

        return await self.code_generator.generate_tests(code)

    async def _lint_and_format(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run linting and formatting."""
        path = args.get("path", ".")
        fix = args.get("fix", True)

        results = {}

        # Run Ruff
        try:
            cmd = ["ruff", "check", path]
            if fix:
                cmd.append("--fix")

            result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
            results["ruff"] = {
                "success": result.returncode == 0,
                "output": result.stdout[:2000],
                "errors": result.stderr[:500],
            }
        except Exception as e:
            results["ruff"] = {"success": False, "error": str(e)}

        # Run Black
        if fix:
            try:
                result = subprocess.run(
                    ["black", "--line-length", "119", path],
                    check=False, capture_output=True,
                    text=True,
                    timeout=60,
                )
                results["black"] = {
                    "success": result.returncode == 0,
                    "output": result.stderr[:2000],
                }
            except Exception as e:
                results["black"] = {"success": False, "error": str(e)}

        return {
            "success": all(r.get("success", False) for r in results.values()),
            "results": results,
        }

    async def _security_scan(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run security scans."""
        path = args.get("path")
        include_deps = args.get("include_dependencies", True)

        results = {}

        # Run Bandit
        results["bandit"] = await self.security_scanner.run_bandit(path)

        # Run pip-audit
        if include_deps:
            results["pip_audit"] = await self.security_scanner.run_pip_audit()

        # Calculate overall security status
        has_critical = (
            results["bandit"].get("issue_count", 0) > 0 or
            (include_deps and results.get("pip_audit", {}).get("has_critical", False))
        )

        return {
            "success": not has_critical,
            "results": results,
            "has_critical_issues": has_critical,
        }

    async def _type_check(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run type checking."""
        return await self.test_runner.run_mypy(args.get("path"))

    async def _git_operations(self, args: dict[str, Any]) -> dict[str, Any]:
        """Perform Git operations."""
        operation = args["operation"]

        if operation == "status":
            return await self.git.get_status()
        elif operation == "diff":
            return await self.git.get_diff(staged=args.get("staged", False))
        elif operation == "branch":
            if not args.get("branch_name"):
                return {"success": False, "error": "branch_name required"}
            return await self.git.create_branch(args["branch_name"])
        elif operation == "commit":
            if not args.get("message"):
                return {"success": False, "error": "message required"}
            return await self.git.commit(args["message"], args.get("files"))
        else:
            return {"success": False, "error": f"Unknown operation: {operation}"}

    async def _full_quality_check(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run full quality check."""
        path = args.get("path", ".")
        skip_tests = args.get("skip_tests", False)

        results = {}

        # Lint
        results["lint"] = await self._lint_and_format({"path": path, "fix": False})

        # Type check
        results["type_check"] = await self._type_check({"path": path})

        # Security
        results["security"] = await self._security_scan({"path": path})

        # Tests
        if not skip_tests:
            results["tests"] = await self._run_tests({})

        # Calculate overall status
        all_passed = all(
            r.get("success", False)
            for r in results.values()
            if r  # Skip None results
        )

        return {
            "success": all_passed,
            "results": results,
            "summary": {
                "lint": results["lint"].get("success", False),
                "types": results["type_check"].get("success", False),
                "security": results["security"].get("success", False),
                "tests": results.get("tests", {}).get("success", "skipped"),
            },
        }


# Module entry point
def main():
    """Run the Development MCP server."""

    server = DevelopmentMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
