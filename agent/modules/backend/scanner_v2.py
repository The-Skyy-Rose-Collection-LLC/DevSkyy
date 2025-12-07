"""
Scanner Agent V2 - Enterprise Edition
Comprehensive site scanning with self-healing, orchestration, and advanced security

Features:
- Inherits from BaseAgent for enterprise capabilities
- Multi-threaded scanning for performance
- Integration with orchestrator for multi-agent workflows
- Security and compliance scanning
- Real-time health monitoring
- Automated remediation suggestions
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import logging
import os
from pathlib import Path
import re
import time
from typing import Any

import requests

from agent.modules.base_agent import AgentStatus, BaseAgent


logger = logging.getLogger(__name__)


class ScannerAgentV2(BaseAgent):
    """
    Enterprise scanner agent with self-healing and orchestration.

    Capabilities:
    - Code quality scanning
    - Security vulnerability detection
    - Performance analysis
    - Dependency analysis
    - Live site health checks
    - Automated fix suggestions
    """

    def __init__(self):
        super().__init__(agent_name="Scanner", version="2.0.0")

        # Scanning configuration
        self.scan_extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".html",
            ".css",
            ".php",
            ".json",
            ".yaml",
            ".yml",
        }
        self.ignore_dirs = {
            "node_modules",
            "__pycache__",
            "venv",
            ".git",
            "dist",
            "build",
            ".next",
        }

        # Security patterns
        self.security_patterns = {
            "hardcoded_secret": re.compile(r"(password|secret|api_key)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
            "sql_injection": re.compile(r"execute\([\"'].*\%s.*[\"']\)", re.IGNORECASE),
            "xss_vulnerability": re.compile(r"innerHTML\s*=|dangerouslySetInnerHTML", re.IGNORECASE),
        }

        # Performance tracking
        self.scan_history: list[dict[str, Any]] = []
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

    async def initialize(self) -> bool:
        """Initialize scanner agent"""
        try:
            logger.info("🔍 Initializing Scanner Agent V2...")

            # Verify we have read access to project directory
            if not os.access(".", os.R_OK):
                logger.error("No read access to project directory")
                self.status = AgentStatus.FAILED
                return False

            self.status = AgentStatus.HEALTHY
            logger.info("✅ Scanner Agent V2 initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Scanner initialization failed: {e}")
            self.status = AgentStatus.FAILED
            return False

    async def execute_core_function(self, **kwargs) -> dict[str, Any]:
        """
        Execute core scanning functionality.

        Args:
            scan_type: Type of scan (full, security, performance, quick)
            target_path: Specific path to scan (default: current directory)
            include_live_check: Check live site health (default: True)

        Returns:
            Comprehensive scan results
        """
        scan_type = kwargs.get("scan_type", "full")
        target_path = kwargs.get("target_path", ".")
        include_live_check = kwargs.get("include_live_check", True)

        logger.info(f"🔍 Starting {scan_type} scan...")

        scan_results = {
            "scan_id": f"scan_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "scan_type": scan_type,
            "status": "running",
        }

        try:
            # Perform appropriate scan type
            if scan_type == "full":
                results = await self._full_scan(target_path, include_live_check)
            elif scan_type == "security":
                results = await self._security_scan(target_path)
            elif scan_type == "performance":
                results = await self._performance_scan(target_path)
            elif scan_type == "quick":
                results = await self._quick_scan(target_path)
            else:
                return {"error": f"Unknown scan type: {scan_type}"}

            scan_results.update(results)
            scan_results["status"] = "completed"

            # Store in history
            self.scan_history.append(scan_results)
            if len(self.scan_history) > 100:
                self.scan_history = self.scan_history[-100:]

            return scan_results

        except Exception as e:
            logger.error(f"Scan failed: {e}")
            scan_results["status"] = "failed"
            scan_results["error"] = str(e)
            return scan_results

    async def _full_scan(self, target_path: str, include_live_check: bool) -> dict[str, Any]:
        """Perform comprehensive full scan"""
        results = {
            "files_scanned": 0,
            "errors_found": [],
            "warnings": [],
            "optimizations": [],
            "security_issues": [],
            "performance_metrics": {},
            "dependencies": {},
        }

        # Scan project files
        files = await self._scan_project_files(target_path)
        results["files_scanned"] = len(files)

        # Analyze files concurrently
        file_results = await asyncio.gather(*[self._analyze_file(f) for f in files], return_exceptions=True)

        for file_result in file_results:
            if isinstance(file_result, Exception):
                logger.warning(f"File analysis error: {file_result}")
                continue

            if file_result:
                results["errors_found"].extend(file_result.get("errors", []))
                results["warnings"].extend(file_result.get("warnings", []))
                results["optimizations"].extend(file_result.get("optimizations", []))

        # Security scan
        security_issues = await self._detect_security_issues(files)
        results["security_issues"] = security_issues

        # Performance analysis
        if include_live_check:
            performance = await self._analyze_site_performance()
            results["performance_metrics"] = performance

        # Dependency analysis
        dependencies = await self._analyze_dependencies()
        results["dependencies"] = dependencies

        # Generate summary
        results["summary"] = self._generate_summary(results)

        return results

    async def _security_scan(self, target_path: str) -> dict[str, Any]:
        """Focused security vulnerability scan"""
        results = {"security_issues": [], "vulnerabilities": [], "risk_level": "low"}

        files = await self._scan_project_files(target_path)
        security_issues = await self._detect_security_issues(files)

        results["security_issues"] = security_issues

        # Categorize by severity
        critical = [i for i in security_issues if i.get("severity") == "critical"]
        high = [i for i in security_issues if i.get("severity") == "high"]
        medium = [i for i in security_issues if i.get("severity") == "medium"]

        if critical:
            results["risk_level"] = "critical"
        elif high:
            results["risk_level"] = "high"
        elif medium:
            results["risk_level"] = "medium"

        results["vulnerabilities"] = {
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(security_issues) - len(critical) - len(high) - len(medium),
        }

        return results

    async def _performance_scan(self, target_path: str) -> dict[str, Any]:
        """Focused performance analysis"""
        return {
            "performance_metrics": await self._analyze_site_performance(),
            "optimization_suggestions": await self._generate_optimization_suggestions(target_path),
        }

    async def _quick_scan(self, target_path: str) -> dict[str, Any]:
        """Quick health check scan"""
        files = await self._scan_project_files(target_path)

        return {
            "files_count": len(files),
            "health_status": "healthy" if len(files) > 0 else "unhealthy",
            "last_modified": self._get_last_modified_time(files),
        }

    async def _scan_project_files(self, target_path: str) -> list[str]:
        """Scan all project files for analysis"""
        files = []

        def scan_directory():
            for root, dirs, filenames in os.walk(target_path):
                # Filter ignored directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in self.ignore_dirs]

                for filename in filenames:
                    if any(filename.endswith(ext) for ext in self.scan_extensions):
                        file_path = os.path.join(root, filename)
                        files.append(file_path)

        # Run in thread pool to avoid blocking
        await asyncio.get_event_loop().run_in_executor(self.thread_pool, scan_directory)

        return files

    async def _analyze_file(self, file_path: str) -> dict[str, Any]:
        """Analyze a single file for issues"""
        result = {"file": file_path, "errors": [], "warnings": [], "optimizations": []}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")

            # Check file size
            if len(content) > 100000:  # 100KB
                result["warnings"].append(
                    {
                        "type": "large_file",
                        "message": f"File is large: {len(content)} bytes",
                    }
                )

            # Check line length
            for i, line in enumerate(lines, 1):
                if len(line) > 200:
                    result["warnings"].append({"type": "long_line", "line": i, "length": len(line)})

            # Python-specific checks
            if file_path.endswith(".py"):
                result.update(await self._analyze_python_file(content, file_path))

            # JavaScript/TypeScript checks
            if file_path.endswith((".js", ".ts", ".tsx")):
                result.update(await self._analyze_javascript_file(content, file_path))

        except Exception as e:
            result["errors"].append({"type": "read_error", "message": str(e)})

        return result

    async def _analyze_python_file(self, content: str, file_path: str) -> dict[str, Any]:
        """Python-specific analysis"""
        result = {"errors": [], "warnings": [], "optimizations": []}

        # Check for common issues
        if "print(" in content and "DEBUG" not in content:
            result["warnings"].append(
                {
                    "type": "debug_print",
                    "message": "Found print() statement in production code",
                }
            )

        if "TODO" in content or "FIXME" in content:
            result["optimizations"].append({"type": "todo", "message": "Found TODO/FIXME comments"})

        return result

    async def _analyze_javascript_file(self, content: str, file_path: str) -> dict[str, Any]:
        """JavaScript/TypeScript specific analysis"""
        result = {"errors": [], "warnings": [], "optimizations": []}

        # Check for console.log
        if "console.log" in content:
            result["warnings"].append(
                {
                    "type": "console_log",
                    "message": "Found console.log in production code",
                }
            )

        # Check for var usage (should use let/const)
        if re.search(r"\bvar\s+", content):
            result["optimizations"].append({"type": "var_usage", "message": "Use let/const instead of var"})

        return result

    async def _detect_security_issues(self, files: list[str]) -> list[dict[str, Any]]:
        """Detect security vulnerabilities"""
        issues = []

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Check each security pattern
                for pattern_name, pattern in self.security_patterns.items():
                    matches = pattern.findall(content)
                    if matches:
                        issues.append(
                            {
                                "file": file_path,
                                "type": pattern_name,
                                "severity": ("high" if "secret" in pattern_name else "medium"),
                                "matches": len(matches),
                            }
                        )

            except Exception as e:
                logger.warning(f"Security scan error for {file_path}: {e}")

        return issues

    async def _analyze_site_performance(self) -> dict[str, Any]:
        """Analyze live site performance"""
        try:
            # Try to check localhost backend
            url = os.getenv("SITE_URL", "http://localhost:8000")

            start_time = time.time()
            response = await asyncio.get_event_loop().run_in_executor(
                self.thread_pool, lambda: requests.get(url, timeout=10)
            )
            response_time = (time.time() - start_time) * 1000  # ms

            return {
                "url": url,
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "health": "healthy" if response.status_code == 200 else "unhealthy",
            }

        except Exception as e:
            return {"health": "unavailable", "error": str(e)}

    async def _analyze_dependencies(self) -> dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {"python": [], "nodejs": [], "status": "unknown"}

        # Check requirements.txt
        if os.path.exists("requirements.txt"):
            with open("requirements.txt", "r") as f:
                dependencies["python"] = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        # Check package.json
        if os.path.exists("package.json"):
            import json

            with open("package.json", "r") as f:
                pkg_data = json.load(f)
                dependencies["nodejs"] = list(pkg_data.get("dependencies", {}).keys())

        dependencies["status"] = "analyzed"
        return dependencies

    async def _generate_optimization_suggestions(self, target_path: str) -> list[str]:
        """Generate optimization suggestions"""
        suggestions = []

        # Check for large node_modules
        if os.path.exists("node_modules"):
            size = sum(f.stat().st_size for f in Path("node_modules").rglob("*") if f.is_file())
            if size > 500_000_000:  # 500MB
                suggestions.append("node_modules is large (>500MB). Consider using yarn PnP or pnpm")

        # Check for Python cache
        pycache_dirs = list(Path(target_path).rglob("__pycache__"))
        if len(pycache_dirs) > 100:
            suggestions.append(f"Found {len(pycache_dirs)} __pycache__ directories. Consider cleanup")

        return suggestions

    def _generate_summary(self, results: dict[str, Any]) -> str:
        """Generate human-readable summary"""
        errors = len(results.get("errors_found", []))
        warnings = len(results.get("warnings", []))
        security = len(results.get("security_issues", []))

        if errors == 0 and warnings == 0 and security == 0:
            return "✅ Scan completed successfully. No issues found."
        elif errors > 0:
            return f"⚠️ Found {errors} errors, {warnings} warnings, {security} security issues"
        else:
            return f"✅ Scan completed with {warnings} warnings, {security} security issues"

    def _get_last_modified_time(self, files: list[str]) -> str | None:
        """Get last modified time of most recent file"""
        if not files:
            return None

        try:
            latest = max(files, key=lambda f: os.path.getmtime(f))
            return datetime.fromtimestamp(os.path.getmtime(latest)).isoformat()
        except Exception:
            return None

    async def get_scan_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent scan history"""
        return self.scan_history[-limit:]


# Create instance for export
scanner_agent = ScannerAgentV2()
