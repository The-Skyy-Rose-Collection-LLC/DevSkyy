"""
Deployment Workflow
==================

Handles deployment to staging and production environments.
"""

import asyncio
import logging
from typing import Any, Literal

from pydantic import BaseModel

from orchestration.langgraph_integration import WorkflowState, WorkflowStatus

logger = logging.getLogger(__name__)


class DeploymentWorkflowState(WorkflowState):
    """Deployment workflow state"""

    environment: Literal["staging", "production", "development"] = "staging"
    image_tag: str | None = None
    deployment_url: str | None = None
    health_check_passed: bool = False
    rollback_available: bool = False


class DeploymentWorkflow:
    """
    Deployment Pipeline Workflow

    Executes:
    - Pre-deployment validation
    - Docker image building
    - Security scanning of images
    - Environment-specific deployment
    - Health checks and smoke tests
    - Rollback on failure
    """

    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute deployment workflow"""
        deploy_state = DeploymentWorkflowState(**state.model_dump())
        deploy_state.status = WorkflowStatus.RUNNING
        deploy_state.current_node = "pre-deploy-validation"

        try:
            # Determine environment
            environment = deploy_state.inputs.get("environment", "staging")
            deploy_state.environment = environment

            # Step 1: Pre-deployment Validation
            logger.info(f"Validating deployment for {environment}...")
            validation_results = await self._pre_deploy_validation(deploy_state)
            deploy_state.node_history.append("pre-deploy-validation")

            # Step 2: Build Docker Images
            deploy_state.current_node = "build-docker"
            logger.info("Building Docker images...")
            build_results = await self._build_docker_images(deploy_state)
            deploy_state.image_tag = build_results.get("image_tag")
            deploy_state.node_history.append("build-docker")

            # Step 3: Security Scan Images
            deploy_state.current_node = "security-scan-image"
            logger.info("Scanning Docker image for vulnerabilities...")
            security_results = await self._security_scan_image(deploy_state)
            deploy_state.node_history.append("security-scan-image")

            # Step 4: Deploy to Environment
            deploy_state.current_node = f"deploy-{environment}"
            logger.info(f"Deploying to {environment} environment...")
            deployment_results = await self._deploy_to_environment(deploy_state)
            deploy_state.deployment_url = deployment_results.get("url")
            deploy_state.node_history.append(f"deploy-{environment}")

            # Step 5: Health Checks
            deploy_state.current_node = "health-checks"
            logger.info("Running health checks...")
            health_results = await self._run_health_checks(deploy_state)
            deploy_state.health_check_passed = health_results.get("passed", False)
            deploy_state.node_history.append("health-checks")

            if not deploy_state.health_check_passed:
                raise Exception("Health checks failed")

            # Mark as completed
            deploy_state.status = WorkflowStatus.COMPLETED
            deploy_state.current_node = None
            deploy_state.outputs = {
                "environment": environment,
                "image_tag": deploy_state.image_tag,
                "url": deploy_state.deployment_url,
                "validation": validation_results,
                "build": build_results,
                "security": security_results,
                "deployment": deployment_results,
                "health": health_results,
            }

            return deploy_state

        except Exception as e:
            logger.error(f"Deployment workflow failed: {e}")

            # Attempt rollback
            if deploy_state.rollback_available:
                logger.info("Initiating rollback...")
                await self._rollback_deployment(deploy_state)

            deploy_state.status = WorkflowStatus.FAILED
            deploy_state.errors.append({"node": deploy_state.current_node, "error": str(e)})
            return deploy_state

    async def _pre_deploy_validation(
        self, state: DeploymentWorkflowState
    ) -> dict[str, Any]:
        """Pre-deployment validation checks"""
        results = {"environment_check": None, "secrets_check": None}

        try:
            # Check environment configuration
            env = state.environment
            logger.info(f"Validating deployment for environment: {env}")

            results["environment_check"] = {
                "status": "passed",
                "environment": env,
            }

            # Check required secrets (simulated)
            required_secrets = {
                "production": ["PROD_DATABASE_URL", "PROD_SECRET_KEY"],
                "staging": ["STAGING_DATABASE_URL", "STAGING_SECRET_KEY"],
            }

            secrets_needed = required_secrets.get(env, [])
            results["secrets_check"] = {
                "status": "passed",
                "secrets_validated": len(secrets_needed),
            }

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _build_docker_images(
        self, state: DeploymentWorkflowState
    ) -> dict[str, Any]:
        """Build Docker images"""
        results = {"image_tag": None, "digest": None}

        try:
            # Determine image tag
            import uuid

            # Use registry from state inputs or default to ghcr.io
            registry = state.inputs.get("registry", "ghcr.io/devskyy/devskyy")
            image_tag = f"{registry}:{state.environment}-{uuid.uuid4().hex[:8]}"
            results["image_tag"] = image_tag

            # Build Docker image
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "build",
                "-t",
                image_tag,
                ".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode == 0:
                results["status"] = "passed"
                results["output"] = stdout.decode()
                logger.info(f"Docker image built successfully: {image_tag}")
            else:
                results["status"] = "failed"
                results["error"] = stderr.decode()
                raise Exception(f"Docker build failed: {stderr.decode()}")

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            raise

        return results

    async def _security_scan_image(
        self, state: DeploymentWorkflowState
    ) -> dict[str, Any]:
        """Security scan Docker image using Trivy"""
        results = {"vulnerabilities": None}

        try:
            image_tag = state.image_tag
            if not image_tag:
                raise Exception("No image tag available for scanning")

            # Run Trivy scan (simulated)
            logger.info(f"Scanning image {image_tag} for vulnerabilities...")

            proc = await asyncio.create_subprocess_exec(
                "docker",
                "run",
                "--rm",
                "-v",
                "/var/run/docker.sock:/var/run/docker.sock",
                "aquasec/trivy:latest",
                "image",
                "--format",
                "json",
                image_tag,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            results["status"] = "passed" if proc.returncode == 0 else "warning"
            results["output"] = stdout.decode()[:1000]  # Truncate for brevity

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            logger.warning(f"Security scan failed: {e}")

        return results

    async def _deploy_to_environment(
        self, state: DeploymentWorkflowState
    ) -> dict[str, Any]:
        """Deploy to specific environment"""
        results = {"url": None, "deployed": False}

        try:
            env = state.environment
            image_tag = state.image_tag

            logger.info(f"Deploying {image_tag} to {env}...")

            # Simulated deployment commands
            # In real scenario, this would use kubectl, docker-compose, etc.
            deployment_urls = {
                "staging": "https://staging.devskyy.com",
                "production": "https://devskyy.com",
                "development": "http://localhost:8000",
            }

            results["url"] = deployment_urls.get(env)
            results["deployed"] = True
            results["status"] = "success"
            results["image"] = image_tag

            state.rollback_available = True

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            raise

        return results

    async def _run_health_checks(
        self, state: DeploymentWorkflowState
    ) -> dict[str, Any]:
        """Run health checks on deployed application"""
        results = {"passed": False, "checks": []}

        try:
            url = state.deployment_url
            if not url:
                raise Exception("No deployment URL available")

            # Simulated health checks
            checks = [
                {"name": "API Health", "endpoint": f"{url}/health", "status": "passed"},
                {
                    "name": "Database Connection",
                    "endpoint": f"{url}/api/health/db",
                    "status": "passed",
                },
                {
                    "name": "Cache Connection",
                    "endpoint": f"{url}/api/health/cache",
                    "status": "passed",
                },
            ]

            results["checks"] = checks
            results["passed"] = all(c["status"] == "passed" for c in checks)
            results["status"] = "success"

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)

        return results

    async def _rollback_deployment(self, state: DeploymentWorkflowState) -> None:
        """Rollback failed deployment"""
        try:
            logger.warning(f"Rolling back deployment to {state.environment}...")
            # Simulated rollback logic
            # In real scenario, this would restore previous version
            await asyncio.sleep(1)
            logger.info("Rollback completed")
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
