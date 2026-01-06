"""
Quality Check Workflow
=====================

Code quality and standards verification workflow.
"""

import asyncio
import logging
from typing import Any

from orchestration.langgraph_integration import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class QualityWorkflowState(WorkflowState):
    """Quality workflow state"""

    linting_passed: bool = False
    formatting_passed: bool = False
    type_checking_passed: bool = False


class QualityWorkflow:
    """
    Quality Check Workflow

    Executes:
    - Code linting (Python and JavaScript)
    - Code formatting checks
    - Type checking
    - Import validation
    - Complexity analysis
    """

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute quality workflow"""
        quality_state = QualityWorkflowState(**state.model_dump())
        quality_state.status = WorkflowStatus.RUNNING
        quality_state.current_node = "linting"

        try:
            # Step 1: Linting
            logger.info("Running linting checks...")
            linting_results = await self._run_linting(quality_state)
            quality_state.linting_passed = linting_results.get("passed", False)
            quality_state.node_history.append("linting")

            # Step 2: Formatting
            quality_state.current_node = "formatting"
            logger.info("Running formatting checks...")
            formatting_results = await self._run_formatting(quality_state)
            quality_state.formatting_passed = formatting_results.get("passed", False)
            quality_state.node_history.append("formatting")

            # Step 3: Type Checking
            quality_state.current_node = "type-checking"
            logger.info("Running type checking...")
            type_results = await self._run_type_checking(quality_state)
            quality_state.type_checking_passed = type_results.get("passed", False)
            quality_state.node_history.append("type-checking")

            # Step 4: Complexity Analysis
            quality_state.current_node = "complexity"
            logger.info("Running complexity analysis...")
            complexity_results = await self._run_complexity_analysis(quality_state)
            quality_state.node_history.append("complexity")

            # Mark as completed
            quality_state.status = WorkflowStatus.COMPLETED
            quality_state.current_node = None
            quality_state.outputs = {
                "linting": linting_results,
                "formatting": formatting_results,
                "type_checking": type_results,
                "complexity": complexity_results,
            }

            return quality_state

        except Exception as e:
            logger.error(f"Quality workflow failed: {e}")
            quality_state.status = WorkflowStatus.FAILED
            quality_state.errors.append({"node": quality_state.current_node, "error": str(e)})
            return quality_state

    async def _run_linting(self, state: QualityWorkflowState) -> dict[str, Any]:
        """Run code linting checks"""
        results = {"ruff": None, "eslint": None, "passed": False}

        try:
            # Install ruff if not available
            # Note: In production, these tools should be pre-installed in the environment
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
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

            # ESLint for JavaScript/TypeScript
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
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

            # Overall pass status
            results["passed"] = all(
                r.get("status") == "passed" for r in [results["ruff"], results["eslint"]]
            )

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _run_formatting(self, state: QualityWorkflowState) -> dict[str, Any]:
        """Run code formatting checks"""
        results = {"ruff_format": None, "prettier": None, "passed": False}

        try:
            # Ruff formatting for Python
            proc = await asyncio.create_subprocess_exec(
                "ruff",
                "format",
                "--check",
                ".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["ruff_format"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

            # Prettier for JavaScript/TypeScript
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
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

            # Overall pass status
            results["passed"] = all(
                r.get("status") == "passed" for r in [results["ruff_format"], results["prettier"]]
            )

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _run_type_checking(self, state: QualityWorkflowState) -> dict[str, Any]:
        """Run type checking"""
        results = {"mypy": None, "typescript": None, "passed": False}

        try:
            # Install mypy if not available
            # Note: In production, these tools should be pre-installed in the environment
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
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

            # TypeScript type checking
            proc = await asyncio.create_subprocess_exec(
                "npm",
                "run",
                "type-check",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["typescript"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

            # Overall pass status
            results["passed"] = all(
                r.get("status") == "passed" for r in [results["mypy"], results["typescript"]]
            )

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _run_complexity_analysis(self, state: QualityWorkflowState) -> dict[str, Any]:
        """Run code complexity analysis"""
        results = {"radon": None}

        try:
            # Install radon if not available
            # Note: In production, these tools should be pre-installed in the environment
            proc = await asyncio.create_subprocess_exec(
                "pip",
                "install",
                "radon",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "radon",
                "cc",
                ".",
                "-a",
                "-nb",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["radon"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

        except Exception as e:
            results["error"] = str(e)

        return results
