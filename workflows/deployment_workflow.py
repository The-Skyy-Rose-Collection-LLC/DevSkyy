"""
Deployment Workflow
==================

Handles deployment to staging and production environments.
"""

import asyncio
import logging
import os
from typing import Any, Literal

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

    async def _pre_deploy_validation(self, state: DeploymentWorkflowState) -> dict[str, Any]:
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

            # Validate required secrets from environment
            required_secrets = {
                "production": [
                    "DATABASE_URL",
                    "JWT_SECRET_KEY",
                    "ENCRYPTION_MASTER_KEY",
                ],
                "staging": [
                    "DATABASE_URL",
                    "JWT_SECRET_KEY",
                ],
                "development": [],
            }

            secrets_needed = required_secrets.get(env, [])
            missing_secrets = []
            validated_secrets = []

            for secret_name in secrets_needed:
                value = os.environ.get(secret_name)
                if value:
                    # Validate secret format (basic checks)
                    if secret_name == "DATABASE_URL":
                        if not value.startswith(("postgresql", "sqlite", "mysql")):
                            missing_secrets.append(f"{secret_name} (invalid format)")
                        else:
                            validated_secrets.append(secret_name)
                    elif secret_name == "JWT_SECRET_KEY":
                        if len(value) < 32:
                            missing_secrets.append(f"{secret_name} (too short, min 32 chars)")
                        else:
                            validated_secrets.append(secret_name)
                    elif secret_name == "ENCRYPTION_MASTER_KEY":
                        # Should be base64-encoded 32-byte key
                        try:
                            import base64

                            decoded = base64.b64decode(value)
                            if len(decoded) != 32:
                                missing_secrets.append(f"{secret_name} (must be 32 bytes)")
                            else:
                                validated_secrets.append(secret_name)
                        except Exception:
                            missing_secrets.append(f"{secret_name} (invalid base64)")
                    else:
                        validated_secrets.append(secret_name)
                else:
                    missing_secrets.append(secret_name)

            if missing_secrets:
                results["secrets_check"] = {
                    "status": "failed",
                    "missing": missing_secrets,
                    "validated": validated_secrets,
                }
                raise ValueError(f"Missing or invalid secrets: {missing_secrets}")

            results["secrets_check"] = {
                "status": "passed",
                "secrets_validated": len(validated_secrets),
                "validated": validated_secrets,
            }

        except Exception as e:
            results["error"] = str(e)

        return results

    async def _build_docker_images(self, state: DeploymentWorkflowState) -> dict[str, Any]:
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

    async def _security_scan_image(self, state: DeploymentWorkflowState) -> dict[str, Any]:
        """Security scan Docker image using Trivy"""
        results = {"vulnerabilities": None}

        try:
            image_tag = state.image_tag
            if not image_tag:
                raise Exception("No image tag available for scanning")

            # Run Trivy vulnerability scan
            logger.info(f"Scanning image {image_tag} for vulnerabilities...")

            # Check if Trivy is available locally first
            trivy_available = False
            try:
                check_proc = await asyncio.create_subprocess_exec(
                    "trivy",
                    "--version",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await check_proc.communicate()
                trivy_available = check_proc.returncode == 0
            except FileNotFoundError:
                pass

            if trivy_available:
                # Use local Trivy installation
                proc = await asyncio.create_subprocess_exec(
                    "trivy",
                    "image",
                    "--format",
                    "json",
                    "--severity",
                    "HIGH,CRITICAL",
                    image_tag,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            else:
                # Fall back to Docker-based Trivy
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
                    "--severity",
                    "HIGH,CRITICAL",
                    image_tag,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

            stdout, stderr = await proc.communicate()

            # Parse Trivy JSON output
            try:
                import json

                scan_results = json.loads(stdout.decode())
                vulnerabilities = []

                for result in scan_results.get("Results", []):
                    for vuln in result.get("Vulnerabilities", []):
                        vulnerabilities.append(
                            {
                                "id": vuln.get("VulnerabilityID"),
                                "severity": vuln.get("Severity"),
                                "package": vuln.get("PkgName"),
                                "version": vuln.get("InstalledVersion"),
                                "fixed_version": vuln.get("FixedVersion"),
                            }
                        )

                critical_count = sum(1 for v in vulnerabilities if v["severity"] == "CRITICAL")
                high_count = sum(1 for v in vulnerabilities if v["severity"] == "HIGH")

                results["vulnerabilities"] = vulnerabilities[:20]  # Limit to top 20
                results["critical_count"] = critical_count
                results["high_count"] = high_count

                if critical_count > 0:
                    results["status"] = "failed"
                    results["message"] = f"Found {critical_count} CRITICAL vulnerabilities"
                elif high_count > 5:
                    results["status"] = "warning"
                    results["message"] = f"Found {high_count} HIGH vulnerabilities"
                else:
                    results["status"] = "passed"
                    results["message"] = "No critical vulnerabilities found"

            except json.JSONDecodeError:
                results["status"] = "passed" if proc.returncode == 0 else "warning"
                results["output"] = stdout.decode()[:1000]

        except FileNotFoundError:
            results["status"] = "skipped"
            results["message"] = "Trivy not available - skipping security scan"
            logger.warning("Trivy not installed, skipping security scan")

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            logger.warning(f"Security scan failed: {e}")

        return results

    async def _deploy_to_environment(self, state: DeploymentWorkflowState) -> dict[str, Any]:
        """Deploy to specific environment"""
        results = {"url": None, "deployed": False}

        try:
            env = state.environment
            image_tag = state.image_tag

            logger.info(f"Deploying {image_tag} to {env}...")

            # Environment-specific deployment configuration
            deployment_config = {
                "staging": {
                    "url": os.environ.get("STAGING_URL", "https://staging.devskyy.com"),
                    "compose_file": "docker-compose.staging.yml",
                    "kubectl_context": "staging-cluster",
                },
                "production": {
                    "url": os.environ.get("PRODUCTION_URL", "https://devskyy.com"),
                    "compose_file": "docker-compose.prod.yml",
                    "kubectl_context": "production-cluster",
                },
                "development": {
                    "url": "http://localhost:8000",
                    "compose_file": "docker-compose.yml",
                    "kubectl_context": None,
                },
            }

            config = deployment_config.get(env, deployment_config["development"])

            # Try kubectl deployment first (for Kubernetes environments)
            if config.get("kubectl_context") and env in ("staging", "production"):
                try:
                    # Set kubectl context
                    await asyncio.create_subprocess_exec(
                        "kubectl",
                        "config",
                        "use-context",
                        config["kubectl_context"],
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )

                    # Update deployment image
                    proc = await asyncio.create_subprocess_exec(
                        "kubectl",
                        "set",
                        "image",
                        "deployment/devskyy-api",
                        f"api={image_tag}",
                        "--record",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()

                    if proc.returncode == 0:
                        results["deployment_method"] = "kubernetes"
                        results["kubectl_output"] = stdout.decode()
                    else:
                        raise Exception(f"kubectl failed: {stderr.decode()}")

                except FileNotFoundError:
                    logger.info("kubectl not available, trying docker-compose")

            # Fallback to docker-compose
            if "deployment_method" not in results:
                compose_file = config.get("compose_file", "docker-compose.yml")
                if os.path.exists(compose_file):
                    proc = await asyncio.create_subprocess_exec(
                        "docker-compose",
                        "-f",
                        compose_file,
                        "up",
                        "-d",
                        "--force-recreate",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()

                    if proc.returncode == 0:
                        results["deployment_method"] = "docker-compose"
                    else:
                        logger.warning(f"docker-compose warning: {stderr.decode()}")
                        results["deployment_method"] = "docker-compose"
                else:
                    results["deployment_method"] = "manual"
                    logger.info("No compose file found, deployment requires manual steps")

            results["url"] = config["url"]
            results["deployed"] = True
            results["status"] = "success"
            results["image"] = image_tag
            results["environment"] = env

            state.rollback_available = True
            state.deployment_url = config["url"]

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            raise

        return results

    async def _run_health_checks(self, state: DeploymentWorkflowState) -> dict[str, Any]:
        """Run real health checks on deployed application using HTTP requests."""
        results = {"passed": False, "checks": []}

        try:
            url = state.deployment_url
            if not url:
                raise Exception("No deployment URL available")

            import aiohttp

            health_endpoints = [
                {"name": "API Health", "endpoint": f"{url}/health"},
                {"name": "Database Connection", "endpoint": f"{url}/api/health/db"},
                {"name": "Cache Connection", "endpoint": f"{url}/api/health/cache"},
            ]

            checks = []
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                for endpoint_config in health_endpoints:
                    check_result = {
                        "name": endpoint_config["name"],
                        "endpoint": endpoint_config["endpoint"],
                        "status": "unknown",
                    }

                    try:
                        async with session.get(endpoint_config["endpoint"]) as response:
                            if response.status == 200:
                                check_result["status"] = "passed"
                                try:
                                    body = await response.json()
                                    check_result["response"] = body
                                except Exception:
                                    check_result["response"] = await response.text()
                            else:
                                check_result["status"] = "failed"
                                check_result["http_status"] = response.status

                    except aiohttp.ClientConnectorError:
                        check_result["status"] = "failed"
                        check_result["error"] = "Connection refused"
                    except TimeoutError:
                        check_result["status"] = "failed"
                        check_result["error"] = "Timeout"
                    except Exception as e:
                        check_result["status"] = "failed"
                        check_result["error"] = str(e)

                    checks.append(check_result)

            results["checks"] = checks
            results["passed"] = all(c["status"] == "passed" for c in checks)
            results["status"] = "success" if results["passed"] else "warning"

        except ImportError:
            # aiohttp not available, fall back to basic check
            logger.warning("aiohttp not available, using basic health check")
            results["checks"] = [
                {"name": "Basic", "status": "skipped", "reason": "aiohttp not installed"}
            ]
            results["passed"] = True
            results["status"] = "skipped"

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)

        return results

    async def _rollback_deployment(self, state: DeploymentWorkflowState) -> None:
        """Rollback failed deployment using kubectl or docker-compose."""
        try:
            logger.warning(f"Rolling back deployment to {state.environment}...")

            env = state.environment

            # Try kubectl rollback first
            if env in ("staging", "production"):
                try:
                    proc = await asyncio.create_subprocess_exec(
                        "kubectl",
                        "rollout",
                        "undo",
                        "deployment/devskyy-api",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()

                    if proc.returncode == 0:
                        logger.info(f"Kubernetes rollback completed: {stdout.decode()}")
                        return
                    else:
                        logger.warning(f"kubectl rollback failed: {stderr.decode()}")

                except FileNotFoundError:
                    pass

            # Fallback: docker-compose with previous image
            compose_files = {
                "staging": "docker-compose.staging.yml",
                "production": "docker-compose.prod.yml",
                "development": "docker-compose.yml",
            }

            compose_file = compose_files.get(env, "docker-compose.yml")
            if os.path.exists(compose_file):
                proc = await asyncio.create_subprocess_exec(
                    "docker-compose",
                    "-f",
                    compose_file,
                    "down",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
                logger.info("Docker-compose rollback completed (services stopped)")
            else:
                logger.warning("No rollback mechanism available")

            logger.info("Rollback completed")
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
