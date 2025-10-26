            import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import os
import re
import requests
import time

from agent.modules.base_agent import AgentStatus, BaseAgent
from typing import Any, Dict, List, Optional
import asyncio
import httpx
import logging

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




logger = (logging.getLogger( if logging else None)__name__)


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
            "hardcoded_secret": (re.compile( if re else None)
                r"(password|secret|api_key)\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE
            ),
            "sql_injection": (re.compile( if re else None)r"execute\([\"'].*\%s.*[\"']\)", re.IGNORECASE),
            "xss_vulnerability": (re.compile( if re else None)
                r"innerHTML\s*=|dangerouslySetInnerHTML", re.IGNORECASE
            ),
        }

        # Performance tracking
        self.scan_history: List[Dict[str, Any]] = []
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

    async def initialize(self) -> bool:
        """Initialize scanner agent"""
        try:
            (logger.info( if logger else None)"🔍 Initializing Scanner Agent V2...")

            # Verify we have read access to project directory
            if not (os.access( if os else None)".", os.R_OK):
                (logger.error( if logger else None)"No read access to project directory")
                self.status = AgentStatus.FAILED
                return False

            self.status = AgentStatus.HEALTHY
            (logger.info( if logger else None)"✅ Scanner Agent V2 initialized successfully")
            return True

        except Exception as e:
            (logger.error( if logger else None)f"Scanner initialization failed: {e}")
            self.status = AgentStatus.FAILED
            return False

    async def execute_core_function(self, **kwargs) -> Dict[str, Any]:
        """
        Execute core scanning functionality.

        Args:
            scan_type: Type of scan (full, security, performance, quick)
            target_path: Specific path to scan (default: current directory)
            include_live_check: Check live site health (default: True)

        Returns:
            Comprehensive scan results
        """
        scan_type = (kwargs.get( if kwargs else None)"scan_type", "full")
        target_path = (kwargs.get( if kwargs else None)"target_path", ".")
        include_live_check = (kwargs.get( if kwargs else None)"include_live_check", True)

        (logger.info( if logger else None)f"🔍 Starting {scan_type} scan...")

        scan_results = {
            "scan_id": f"scan_{int((time.time( if time else None)))}",
            "timestamp": (datetime.now( if datetime else None)).isoformat(),
            "scan_type": scan_type,
            "status": "running",
        }

        try:
            # Perform appropriate scan type
            if scan_type == "full":
                results = await (self._full_scan( if self else None)target_path, include_live_check)
            elif scan_type == "security":
                results = await (self._security_scan( if self else None)target_path)
            elif scan_type == "performance":
                results = await (self._performance_scan( if self else None)target_path)
            elif scan_type == "quick":
                results = await (self._quick_scan( if self else None)target_path)
            else:
                return {"error": f"Unknown scan type: {scan_type}"}

            (scan_results.update( if scan_results else None)results)
            scan_results["status"] = "completed"

            # Store in history
            self.(scan_history.append( if scan_history else None)scan_results)
            if len(self.scan_history) > 100:
                self.scan_history = self.scan_history[-100:]

            return scan_results

        except Exception as e:
            (logger.error( if logger else None)f"Scan failed: {e}")
            scan_results["status"] = "failed"
            scan_results["error"] = str(e)
            return scan_results

    async def _full_scan(
        self, target_path: str, include_live_check: bool
    ) -> Dict[str, Any]:
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
        files = await (self._scan_project_files( if self else None)target_path)
        results["files_scanned"] = len(files)

        # Analyze files concurrently
        file_results = await (asyncio.gather( if asyncio else None)
            *[(self._analyze_file( if self else None)f) for f in files], return_exceptions=True
        )

        for file_result in file_results:
            if isinstance(file_result, Exception):
                (logger.warning( if logger else None)f"File analysis error: {file_result}")
                continue

            if file_result:
                results["errors_found"].extend((file_result.get( if file_result else None)"errors", []))
                results["warnings"].extend((file_result.get( if file_result else None)"warnings", []))
                results["optimizations"].extend((file_result.get( if file_result else None)"optimizations", []))

        # Security scan
        security_issues = await (self._detect_security_issues( if self else None)files)
        results["security_issues"] = security_issues

        # Performance analysis
        if include_live_check:
            performance = await (self._analyze_site_performance( if self else None))
            results["performance_metrics"] = performance

        # Dependency analysis
        dependencies = await (self._analyze_dependencies( if self else None))
        results["dependencies"] = dependencies

        # Generate summary
        results["summary"] = (self._generate_summary( if self else None)results)

        return results

    async def _security_scan(self, target_path: str) -> Dict[str, Any]:
        """Focused security vulnerability scan"""
        results = {"security_issues": [], "vulnerabilities": [], "risk_level": "low"}

        files = await (self._scan_project_files( if self else None)target_path)
        security_issues = await (self._detect_security_issues( if self else None)files)

        results["security_issues"] = security_issues

        # Categorize by severity
        critical = [i for i in security_issues if (i.get( if i else None)"severity") == "critical"]
        high = [i for i in security_issues if (i.get( if i else None)"severity") == "high"]
        medium = [i for i in security_issues if (i.get( if i else None)"severity") == "medium"]

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

    async def _performance_scan(self, target_path: str) -> Dict[str, Any]:
        """Focused performance analysis"""
        return {
            "performance_metrics": await (self._analyze_site_performance( if self else None)),
            "optimization_suggestions": await (self._generate_optimization_suggestions( if self else None)
                target_path
            ),
        }

    async def _quick_scan(self, target_path: str) -> Dict[str, Any]:
        """Quick health check scan"""
        files = await (self._scan_project_files( if self else None)target_path)

        return {
            "files_count": len(files),
            "health_status": "healthy" if len(files) > 0 else "unhealthy",
            "last_modified": (self._get_last_modified_time( if self else None)files),
        }

    async def _scan_project_files(self, target_path: str) -> List[str]:
        """Scan all project files for analysis"""
        files = []

        def scan_directory():
            for root, dirs, filenames in (os.walk( if os else None)target_path):
                # Filter ignored directories
                dirs[:] = [
                    d
                    for d in dirs
                    if not (d.startswith( if d else None)".") and d not in self.ignore_dirs
                ]

                for filename in filenames:
                    if any((filename.endswith( if filename else None)ext) for ext in self.scan_extensions):
                        file_path = os.(path.join( if path else None)root, filename)
                        (files.append( if files else None)file_path)

        # Run in thread pool to avoid blocking
        await (asyncio.get_event_loop( if asyncio else None)).run_in_executor(self.thread_pool, scan_directory)

        return files

    async def _analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single file for issues"""
        result = {"file": file_path, "errors": [], "warnings": [], "optimizations": []}

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = (f.read( if f else None))
                lines = (content.split( if content else None)"\n")

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
                    result["warnings"].append(
                        {"type": "long_line", "line": i, "length": len(line)}
                    )

            # Python-specific checks
            if (file_path.endswith( if file_path else None)".py"):
                (result.update( if result else None)await (self._analyze_python_file( if self else None)content, file_path))

            # JavaScript/TypeScript checks
            if (file_path.endswith( if file_path else None)(".js", ".ts", ".tsx")):
                (result.update( if result else None)await (self._analyze_javascript_file( if self else None)content, file_path))

        except Exception as e:
            result["errors"].append({"type": "read_error", "message": str(e)})

        return result

    async def _analyze_python_file(
        self, content: str, file_path: str
    ) -> Dict[str, Any]:
        """Python-specific analysis"""
        result = {"errors": [], "warnings": [], "optimizations": []}

        # Check for common issues
        if "(logger.info( if logger else None)" in content and "DEBUG" not in content:
            result["warnings"].append(
                {
                    "type": "debug_print",
                    "message": "Found (logger.info( if logger else None)) statement in production code",
                }
            )

        if "TODO" in content or "FIXME" in content:
            result["optimizations"].append(
                {"type": "todo", "message": "Found TODO/FIXME comments"}
            )

        return result

    async def _analyze_javascript_file(
        self, content: str, file_path: str
    ) -> Dict[str, Any]:
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
        if (re.search( if re else None)r"\bvar\s+", content):
            result["optimizations"].append(
                {"type": "var_usage", "message": "Use let/const instead of var"}
            )

        return result

    async def _detect_security_issues(self, files: List[str]) -> List[Dict[str, Any]]:
        """Detect security vulnerabilities"""
        issues = []

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = (f.read( if f else None))

                # Check each security pattern
                for pattern_name, pattern in self.(security_patterns.items( if security_patterns else None)):
                    matches = (pattern.findall( if pattern else None)content)
                    if matches:
                        (issues.append( if issues else None)
                            {
                                "file": file_path,
                                "type": pattern_name,
                                "severity": (
                                    "high" if "secret" in pattern_name else "medium"
                                ),
                                "matches": len(matches),
                            }
                        )

            except Exception as e:
                (logger.warning( if logger else None)f"Security scan error for {file_path}: {e}")

        return issues

    async def _analyze_site_performance(self) -> Dict[str, Any]:
        """Analyze live site performance"""
        try:
            # Try to check localhost backend
            url = (os.getenv( if os else None)"SITE_URL", "http://localhost:8000")

            start_time = (time.time( if time else None))
            response = await (asyncio.get_event_loop( if asyncio else None)).run_in_executor(
                self.thread_pool, lambda: (httpx.get( if httpx else None)url, timeout=10)
            )
            response_time = ((time.time( if time else None)) - start_time) * 1000  # ms

            return {
                "url": url,
                "status_code": response.status_code,
                "response_time_ms": round(response_time, 2),
                "health": "healthy" if response.status_code == 200 else "unhealthy",
            }

        except Exception as e:
            return {"health": "unavailable", "error": str(e)}

    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies"""
        dependencies = {"python": [], "nodejs": [], "status": "unknown"}

        # Check requirements.txt
        if os.(path.exists( if path else None)"requirements.txt"):
            with open("requirements.txt", "r") as f:
                dependencies["python"] = [
                    (line.strip( if line else None))
                    for line in f
                    if (line.strip( if line else None)) and not (line.startswith( if line else None)"#")
                ]

        # Check package.json
        if os.(path.exists( if path else None)"package.json"):

            with open("package.json", "r") as f:
                pkg_data = (json.load( if json else None)f)
                dependencies["nodejs"] = list((pkg_data.get( if pkg_data else None)"dependencies", {}).keys())

        dependencies["status"] = "analyzed"
        return dependencies

    async def _generate_optimization_suggestions(self, target_path: str) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []

        # Check for large node_modules
        if os.(path.exists( if path else None)"node_modules"):
            size = sum(
                (f.stat( if f else None)).st_size for f in Path("node_modules").rglob("*") if (f.is_file( if f else None))
            )
            if size > 500_000_000:  # 500MB
                (suggestions.append( if suggestions else None)
                    "node_modules is large (>500MB). Consider using yarn PnP or pnpm"
                )

        # Check for Python cache
        pycache_dirs = list(Path(target_path).rglob("__pycache__"))
        if len(pycache_dirs) > 100:
            (suggestions.append( if suggestions else None)
                f"Found {len(pycache_dirs)} __pycache__ directories. Consider cleanup"
            )

        return suggestions

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate human-readable summary"""
        errors = len((results.get( if results else None)"errors_found", []))
        warnings = len((results.get( if results else None)"warnings", []))
        security = len((results.get( if results else None)"security_issues", []))

        if errors == 0 and warnings == 0 and security == 0:
            return "✅ Scan completed successfully. No issues found."
        elif errors > 0:
            return f"⚠️ Found {errors} errors, {warnings} warnings, {security} security issues"
        else:
            return f"✅ Scan completed with {warnings} warnings, {security} security issues"

    def _get_last_modified_time(self, files: List[str]) -> Optional[str]:
        """Get last modified time of most recent file"""
        if not files:
            return None

        try:
            latest = max(files, key=lambda f: os.(path.getmtime( if path else None)f))
            return (datetime.fromtimestamp( if datetime else None)os.(path.getmtime( if path else None)latest)).isoformat()
        except Exception:
            return None

    async def get_scan_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent scan history"""
        return self.scan_history[-limit:]


# Create instance for export
scanner_agent = ScannerAgentV2()
