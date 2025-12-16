"""
Docker Workflow
==============

Docker container build, test, and deployment workflow.
"""

import asyncio
import logging
from typing import Any

from orchestration.langgraph_integration import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class DockerWorkflowState(WorkflowState):
    """Docker workflow state"""

    image_tag: str | None = None
    platforms: list[str] = ["linux/amd64", "linux/arm64"]
    registry: str = "ghcr.io"


class DockerWorkflow:
    """
    Docker Container Workflow

    Executes:
    - Docker build testing
    - Container startup validation
    - Multi-platform builds
    - Container registry push
    - Security scanning
    """

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute Docker workflow"""
        docker_state = DockerWorkflowState(**state.model_dump())
        docker_state.status = WorkflowStatus.RUNNING
        docker_state.current_node = "docker-test"

        try:
            # Step 1: Docker Build Test
            logger.info("Testing Docker build...")
            test_results = await self._docker_test(docker_state)
            docker_state.node_history.append("docker-test")

            # Step 2: Multi-platform Build
            docker_state.current_node = "docker-build"
            logger.info("Building multi-platform Docker images...")
            build_results = await self._docker_build(docker_state)
            docker_state.image_tag = build_results.get("image_tag")
            docker_state.node_history.append("docker-build")

            # Step 3: Security Scan
            docker_state.current_node = "docker-security"
            logger.info("Running security scan on Docker image...")
            security_results = await self._docker_security_scan(docker_state)
            docker_state.node_history.append("docker-security")

            # Mark as completed
            docker_state.status = WorkflowStatus.COMPLETED
            docker_state.current_node = None
            docker_state.outputs = {
                "test": test_results,
                "build": build_results,
                "security": security_results,
            }

            return docker_state

        except Exception as e:
            logger.error(f"Docker workflow failed: {e}")
            docker_state.status = WorkflowStatus.FAILED
            docker_state.errors.append({"node": docker_state.current_node, "error": str(e)})
            return docker_state

    async def _docker_test(self, state: DockerWorkflowState) -> dict[str, Any]:
        """Test Docker build and container startup"""
        results = {"build_test": None, "startup_test": None}

        try:
            # Test Docker build
            proc = await asyncio.create_subprocess_exec(
                "docker", "build", "-t", "test-image", ".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results["build_test"] = {
                "status": "passed" if proc.returncode == 0 else "failed",
                "output": stdout.decode()[:500] if stdout else stderr.decode()[:500],
            }

            # Test container startup
            if proc.returncode == 0:
                proc = await asyncio.create_subprocess_exec(
                    "docker",
                    "run",
                    "-d",
                    "--name",
                    "test-container",
                    "-p",
                    "8000:8000",
                    "test-image",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()

                # Wait for startup
                await asyncio.sleep(5)

                # Test health endpoint
                proc = await asyncio.create_subprocess_exec(
                    "curl", "-f", "http://localhost:8000/health",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()

                results["startup_test"] = {
                    "status": "passed" if proc.returncode == 0 else "failed",
                    "output": stdout.decode() if stdout else stderr.decode(),
                }

                # Cleanup
                await asyncio.create_subprocess_exec(
                    "docker", "stop", "test-container",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.create_subprocess_exec(
                    "docker", "rm", "test-container",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _docker_build(self, state: DockerWorkflowState) -> dict[str, Any]:
        """Build and push multi-platform Docker images"""
        results = {"image_tag": None, "platforms": state.platforms}

        try:
            import uuid

            image_tag = f"{state.registry}/devskyy/devskyy:main-{uuid.uuid4().hex[:8]}"
            results["image_tag"] = image_tag

            # Setup Docker Buildx
            proc = await asyncio.create_subprocess_exec(
                "docker", "buildx", "create", "--use",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            # Build multi-platform image
            platforms = ",".join(state.platforms)
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "buildx",
                "build",
                "--platform",
                platforms,
                "-t",
                image_tag,
                "--push",
                ".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["status"] = "passed" if proc.returncode == 0 else "failed"
            results["output"] = stdout.decode()[:500] if stdout else stderr.decode()[:500]

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)

        return results

    async def _docker_security_scan(self, state: DockerWorkflowState) -> dict[str, Any]:
        """Run Trivy security scan on Docker image"""
        results = {"vulnerabilities": None}

        try:
            if not state.image_tag:
                raise Exception("No image tag available for scanning")

            # Run Trivy scan
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "run",
                "--rm",
                "aquasec/trivy:latest",
                "image",
                "--format",
                "json",
                state.image_tag,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["status"] = "passed" if proc.returncode == 0 else "warning"
            results["output"] = stdout.decode()[:1000]

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)

        return results
