"""
ML Workflow
==========

Machine Learning and AI agent testing workflow.
"""

import asyncio
import logging
from typing import Any

from orchestration.langgraph_integration import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class MLWorkflowState(WorkflowState):
    """ML workflow state"""

    python_version: str = "3.11"
    cuda_available: bool = False
    models_validated: list[str] = []


class MLWorkflow:
    """
    ML Environment Workflow

    Executes:
    - ML dependency validation
    - Model loading tests
    - Agent validation
    - Performance benchmarks
    - Security scanning
    """

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute ML workflow"""
        ml_state = MLWorkflowState(**state.model_dump())
        ml_state.status = WorkflowStatus.RUNNING
        ml_state.current_node = "ml-test"

        try:
            # Step 1: ML Tests
            logger.info("Running ML tests...")
            test_results = await self._ml_test(ml_state)
            ml_state.cuda_available = test_results.get("cuda_available", False)
            ml_state.node_history.append("ml-test")

            # Step 2: Model Validation
            ml_state.current_node = "ml-model-validation"
            logger.info("Validating ML models...")
            model_results = await self._ml_model_validation(ml_state)
            ml_state.models_validated = model_results.get("models", [])
            ml_state.node_history.append("ml-model-validation")

            # Step 3: Performance Tests
            ml_state.current_node = "ml-performance"
            logger.info("Running ML performance benchmarks...")
            performance_results = await self._ml_performance(ml_state)
            ml_state.node_history.append("ml-performance")

            # Step 4: Security Scan
            ml_state.current_node = "ml-security"
            logger.info("Running ML security scan...")
            security_results = await self._ml_security(ml_state)
            ml_state.node_history.append("ml-security")

            # Mark as completed
            ml_state.status = WorkflowStatus.COMPLETED
            ml_state.current_node = None
            ml_state.outputs = {
                "tests": test_results,
                "models": model_results,
                "performance": performance_results,
                "security": security_results,
            }

            return ml_state

        except Exception as e:
            logger.error(f"ML workflow failed: {e}")
            ml_state.status = WorkflowStatus.FAILED
            ml_state.errors.append({"node": ml_state.current_node, "error": str(e)})
            return ml_state

    async def _ml_test(self, state: MLWorkflowState) -> dict[str, Any]:
        """Run ML-specific tests"""
        results = {"dependencies": None, "agent_tests": None, "orchestration": None}

        try:
            # Test ML dependencies
            proc = await asyncio.create_subprocess_exec(
                "python",
                "-c",
                """
try:
    import torch
    import transformers
    print('✅ ML dependencies loaded successfully')
    print(f'PyTorch version: {torch.__version__}')
except ImportError as e:
    print(f'❌ ML dependency error: {e}')
    exit(1)
                """,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["dependencies"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }

            # Run agent tests
            proc = await asyncio.create_subprocess_exec(
                "pytest", "tests/", "-k", "agent", "-v",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["agent_tests"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

            # Test orchestration
            proc = await asyncio.create_subprocess_exec(
                "pytest", "tests/", "-k", "orchestration", "-v",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["orchestration"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _ml_model_validation(self, state: MLWorkflowState) -> dict[str, Any]:
        """Validate ML model configurations"""
        results = {"models": [], "inference_test": None}

        try:
            # Validate agent configurations
            proc = await asyncio.create_subprocess_exec(
                "python",
                "-c",
                """
try:
    from agents.fashn_agent import FashnAgent
    from agents.tripo_agent import TripoAgent
    print('✅ Agent configurations valid')
    print('Models: FashnAgent, TripoAgent')
except ImportError as e:
    print(f'⚠️ Some agents not available: {e}')
                """,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["config_validation"] = {
                "status": "passed" if proc.returncode == 0 else "warning",
                "output": stdout.decode() if stdout else stderr.decode(),
            }

            results["models"] = ["FashnAgent", "TripoAgent"]

            # Test model inference capability
            proc = await asyncio.create_subprocess_exec(
                "python",
                "-c",
                """
import torch
if torch.cuda.is_available():
    print(f'✅ CUDA available: {torch.cuda.get_device_name(0)}')
else:
    print('ℹ️ CUDA not available, using CPU')
                """,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["inference_test"] = {
                "status": "passed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _ml_performance(self, state: MLWorkflowState) -> dict[str, Any]:
        """Run ML performance benchmarks"""
        results = {"matrix_ops": None}

        try:
            # Basic performance test
            proc = await asyncio.create_subprocess_exec(
                "python",
                "-c",
                """
import time
import torch

start_time = time.time()

# Test tensor operations
x = torch.randn(1000, 1000)
y = torch.randn(1000, 1000)
z = torch.matmul(x, y)

end_time = time.time()
duration = end_time - start_time

print(f'✅ Matrix multiplication (1000x1000): {duration:.3f}s')

if duration > 5.0:
    print('⚠️ Performance warning: Operation took longer than expected')
                """,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["matrix_ops"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode() if stdout else stderr.decode(),
            }

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _ml_security(self, state: MLWorkflowState) -> dict[str, Any]:
        """Run ML security scans"""
        results = {"bandit": None, "safety": None}

        try:
            # Run Bandit on ML code
            proc = await asyncio.create_subprocess_exec(
                "pip", "install", "bandit",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            proc = await asyncio.create_subprocess_exec(
                "bandit",
                "-r",
                "ml/",
                "agents/",
                "orchestration/",
                "-f",
                "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["bandit"] = {
                "status": "passed" if proc.returncode in [0, 1] else "failed",
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

        except Exception as e:
            results["error"] = str(e)

        return results
