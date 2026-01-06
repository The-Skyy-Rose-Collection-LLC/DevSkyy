"""
CI/CD Workflow
=============

Continuous Integration workflow for code quality, testing, and security.
"""

import asyncio
import logging
from typing import Any

from orchestration.langgraph_integration import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class CIWorkflowState(WorkflowState):
    """CI Workflow state"""

    python_version: str = "3.11"
    node_version: str = "20"
    test_results: dict[str, Any] = {}
    security_results: dict[str, Any] = {}
    quality_results: dict[str, Any] = {}


class CIWorkflow:
    """
    CI/CD Pipeline Workflow

    Executes:
    - Security scanning
    - Code quality checks
    - Unit and integration tests
    - Build validation
    """

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute CI workflow"""
        ci_state = CIWorkflowState(**state.model_dump())
        ci_state.status = WorkflowStatus.RUNNING
        ci_state.current_node = "security-scan"

        try:
            # Step 1: Security Scan
            logger.info("Running security scans...")
            security_results = await self._run_security_scan(ci_state)
            ci_state.security_results = security_results
            ci_state.node_history.append("security-scan")

            # Step 2: Code Quality
            ci_state.current_node = "code-quality"
            logger.info("Running code quality checks...")
            quality_results = await self._run_quality_checks(ci_state)
            ci_state.quality_results = quality_results
            ci_state.node_history.append("code-quality")

            # Step 3: Tests
            ci_state.current_node = "test"
            logger.info("Running tests...")
            test_results = await self._run_tests(ci_state)
            ci_state.test_results = test_results
            ci_state.node_history.append("test")

            # Step 4: Build
            ci_state.current_node = "build"
            logger.info("Building application...")
            build_results = await self._run_build(ci_state)
            ci_state.node_history.append("build")

            # Mark as completed
            ci_state.status = WorkflowStatus.COMPLETED
            ci_state.current_node = None
            ci_state.outputs = {
                "security": security_results,
                "quality": quality_results,
                "tests": test_results,
                "build": build_results,
            }

            return ci_state

        except Exception as e:
            logger.error(f"CI workflow failed: {e}")
            ci_state.status = WorkflowStatus.FAILED
            ci_state.errors.append({"node": ci_state.current_node, "error": str(e)})
            return ci_state

    async def _run_security_scan(self, state: CIWorkflowState) -> dict[str, Any]:
        """Run security vulnerability scanning"""
        results = {"npm_audit": None, "pip_audit": None, "bandit": None}

        try:
            # NPM audit
            proc = await asyncio.create_subprocess_exec(
                "npm",
                "audit",
                "--audit-level=moderate",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["npm_audit"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["npm_audit"] = {"status": "error", "error": str(e)}

        try:
            # Python security audit
            proc = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "pip-audit",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "pip-audit",
                "--format=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["pip_audit"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["pip_audit"] = {"status": "error", "error": str(e)}

        try:
            # Bandit security linter
            proc = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "bandit",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "bandit",
                "-r",
                ".",
                "-f",
                "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["bandit"] = {
                "status": "passed" if proc.returncode == 0 else "warning",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["bandit"] = {"status": "error", "error": str(e)}

        return results

    async def _run_quality_checks(self, state: CIWorkflowState) -> dict[str, Any]:
        """Run code quality checks"""
        results = {"ruff": None, "mypy": None, "eslint": None, "prettier": None}

        try:
            # Ruff linting
            proc = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "ruff",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "ruff",
                "check",
                ".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["ruff"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["ruff"] = {"status": "error", "error": str(e)}

        try:
            # MyPy type checking
            proc = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "mypy",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "mypy",
                ".",
                "--ignore-missing-imports",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["mypy"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["mypy"] = {"status": "error", "error": str(e)}

        try:
            # ESLint
            proc = await asyncio.create_subprocess_exec(
                "npm",
                "run",
                "lint",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["eslint"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["eslint"] = {"status": "error", "error": str(e)}

        try:
            # Prettier
            proc = await asyncio.create_subprocess_exec(
                "npm",
                "run",
                "format:check",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["prettier"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["prettier"] = {"status": "error", "error": str(e)}

        return results

    async def _run_tests(self, state: CIWorkflowState) -> dict[str, Any]:
        """Run unit and integration tests"""
        results = {"python_tests": None, "js_tests": None}

        try:
            # Python tests with pytest
            proc = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "pytest",
                "pytest-asyncio",
                "pytest-cov",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "pytest",
                "--cov=.",
                "--cov-report=xml",
                "--cov-report=term-missing",
                "-v",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["python_tests"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["python_tests"] = {"status": "error", "error": str(e)}

        try:
            # JavaScript/TypeScript tests
            proc = await asyncio.create_subprocess_exec(
                "npm",
                "run",
                "test:ci",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["js_tests"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["js_tests"] = {"status": "error", "error": str(e)}

        return results

    async def _run_build(self, state: CIWorkflowState) -> dict[str, Any]:
        """Build application"""
        results = {"python_build": None, "frontend_build": None}

        try:
            # Python package build
            proc = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "build",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "python",
                "-m",
                "build",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["python_build"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["python_build"] = {"status": "error", "error": str(e)}

        try:
            # Frontend build
            proc = await asyncio.create_subprocess_exec(
                "npm",
                "run",
                "build",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["frontend_build"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }
        except Exception as e:
            results["frontend_build"] = {"status": "error", "error": str(e)}

        return results
