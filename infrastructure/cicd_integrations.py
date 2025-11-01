from datetime import datetime, timedelta
import json
import time

from fastapi import HTTPException, Request, status

            import hmac
from dataclasses import asdict, dataclass
from enum import Enum
from httpx import AsyncClient, RequestError, TimeoutException
from typing import Any, Callable, Dict, List, Optional, Union
from urllib.parse import urljoin
import asyncio
import base64
import hashlib
import httpx
import logging

"""
Enterprise CI/CD Platform Integrations
Implements plugins/integrations for Jenkins, GitLab CI, GitHub Actions, and Azure DevOps
Bidirectional API communication with webhook listeners and pipeline management
"""

logger = logging.getLogger(__name__)

class CICDPlatform(Enum):
    """Supported CI/CD platforms"""

    JENKINS = "jenkins"
    GITLAB_CI = "gitlab_ci"
    GITHUB_ACTIONS = "github_actions"
    AZURE_DEVOPS = "azure_devops"
    BITBUCKET_PIPELINES = "bitbucket_pipelines"

class PipelineStatus(Enum):
    """Pipeline execution status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"

class WebhookEventType(Enum):
    """Webhook event types"""

    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    BUILD_STARTED = "build_started"
    BUILD_COMPLETED = "build_completed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    CODE_QUALITY_UPDATED = "code_quality_updated"
    SECURITY_SCAN_COMPLETED = "security_scan_completed"

@dataclass
class PipelineEvent:
    """Pipeline event data structure"""

    event_id: str
    platform: CICDPlatform
    event_type: WebhookEventType
    pipeline_id: str
    pipeline_name: str
    status: PipelineStatus
    branch: str
    commit_hash: str
    commit_message: str
    author: str
    timestamp: datetime
    duration: Optional[int] = None
    build_number: Optional[int] = None
    environment: Optional[str] = None
    artifacts: List[str] = None
    test_results: Dict[str, Any] = None
    code_quality_metrics: Dict[str, Any] = None
    security_scan_results: Dict[str, Any] = None
    deployment_url: Optional[str] = None
    logs_url: Optional[str] = None
    raw_payload: Dict[str, Any] = None

    def __post_init__(self):
        if self.artifacts is None:
            self.artifacts = []
        if self.test_results is None:
            self.test_results = {}
        if self.code_quality_metrics is None:
            self.code_quality_metrics = {}
        if self.security_scan_results is None:
            self.security_scan_results = {}
        if self.raw_payload is None:
            self.raw_payload = {}

@dataclass
class CICDConnection:
    """CI/CD platform connection configuration"""

    platform: CICDPlatform
    name: str
    base_url: str
    api_token: str
    username: Optional[str] = None
    webhook_secret: Optional[str] = None
    project_id: Optional[str] = None
    organization: Optional[str] = None
    enabled: bool = True
    rate_limit_per_hour: int = 1000
    timeout: int = 30

class CICDIntegrationManager:
    """Manages CI/CD platform integrations and webhook processing"""

    def __init__(self):
        self.connections: Dict[str, CICDConnection] = {}
        self.webhook_handlers: Dict[CICDPlatform, Callable] = {}
        self.event_history: List[PipelineEvent] = []
        self.pipeline_cache: Dict[str, Dict[str, Any]] = {}

        # HTTP client for API requests
        self.http_client = AsyncClient(timeout=30)

        # Metrics
        self.metrics = {
            "total_webhooks_received": 0,
            "total_api_calls": 0,
            "successful_api_calls": 0,
            "failed_api_calls": 0,
            "avg_response_time": 0.0,
            "last_updated": datetime.now(),
        }

        # Setup webhook handlers
        self._setup_webhook_handlers()

        logger.info("CI/CD integration manager initialized")

    def _setup_webhook_handlers(self):
        """Setup webhook handlers for different platforms"""
        self.webhook_handlers = {
            CICDPlatform.JENKINS: self._handle_jenkins_webhook,
            CICDPlatform.GITLAB_CI: self._handle_gitlab_webhook,
            CICDPlatform.GITHUB_ACTIONS: self._handle_github_webhook,
            CICDPlatform.AZURE_DEVOPS: self._handle_azure_webhook,
            CICDPlatform.BITBUCKET_PIPELINES: self._handle_bitbucket_webhook,
        }

    def add_connection(self, connection: CICDConnection):
        """Add CI/CD platform connection"""
        self.connections[connection.name] = connection
        logger.info(
            f"Added CI/CD connection: {connection.name} ({connection.platform.value})"
        )

    def remove_connection(self, connection_name: str):
        """Remove CI/CD platform connection"""
        if connection_name in self.connections:
            del self.connections[connection_name]
            logger.info(f"Removed CI/CD connection: {connection_name}")

    async def process_webhook(
        self,
        platform: CICDPlatform,
        request: Request,
        connection_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process incoming webhook from CI/CD platform"""

        try:
            # Get request payload
            payload = await request.json()
            headers = dict(request.headers)

            # Find connection
            connection = None
            if connection_name:
                connection = self.connections.get(connection_name)
            else:
                # Find first connection for this platform
                for conn in self.connections.values():
                    if conn.platform == platform and conn.enabled:
                        connection = conn
                        break

            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No active connection found for platform: {platform.value}",
                )

            # Verify webhook signature if secret is configured
            if connection.webhook_secret:
                await self._verify_webhook_signature(
                    platform, headers, payload, connection.webhook_secret
                )

            # Process webhook with platform-specific handler
            handler = self.webhook_handlers.get(platform)
            if not handler:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail=f"Webhook handler not implemented for platform: {platform.value}",
                )

            event = await handler(payload, headers, connection)

            # Store event in history
            self.event_history.append(event)

            # Keep only last 1000 events
            if len(self.event_history) > 1000:
                self.event_history = self.event_history[-1000:]

            # Update metrics
            self.metrics["total_webhooks_received"] += 1
            self.metrics["last_updated"] = datetime.now()

            # Trigger event handlers
            await self._trigger_event_handlers(event)

            logger.info(
                f"Processed webhook: {event.event_type.value} from {platform.value}"
            )

            return {
                "status": "processed",
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "platform": platform.value,
                "pipeline_id": event.pipeline_id,
                "timestamp": event.timestamp.isoformat(),
            }

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Webhook processing failed: {str(e)}",
            )

    async def _verify_webhook_signature(
        self,
        platform: CICDPlatform,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        secret: str,
    ):
        """Verify webhook signature for security"""

        if platform == CICDPlatform.GITHUB_ACTIONS:
            signature = headers.get("x-hub-signature-256")
            if not signature:
                raise HTTPException(status_code=401, detail="Missing signature")

            # Verify GitHub signature

            expected = hmac.new(
                secret.encode(),
                json.dumps(payload, separators=(",", ":")).encode(),
                "sha256",
            ).hexdigest()

            if not hmac.compare_digest(f"sha256={expected}", signature):
                raise HTTPException(status_code=401, detail="Invalid signature")

        elif platform == CICDPlatform.GITLAB_CI:
            token = headers.get("x-gitlab-token")
            if token != secret:
                raise HTTPException(status_code=401, detail="Invalid token")

        # Add other platform signature verification as needed

    async def _handle_jenkins_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        connection: CICDConnection,
    ) -> PipelineEvent:
        """Handle Jenkins webhook"""

        build = payload.get("build", {})

        # Map Jenkins status to our enum
        status_mapping = {
            "SUCCESS": PipelineStatus.SUCCESS,
            "FAILURE": PipelineStatus.FAILED,
            "ABORTED": PipelineStatus.CANCELLED,
            "UNSTABLE": PipelineStatus.FAILED,
        }

        status = status_mapping.get(build.get("status"), PipelineStatus.RUNNING)

        # Determine event type
        if build.get("phase") == "STARTED":
            event_type = WebhookEventType.PIPELINE_STARTED
        elif build.get("phase") == "COMPLETED":
            event_type = WebhookEventType.PIPELINE_COMPLETED
        else:
            event_type = WebhookEventType.PIPELINE_STARTED

        return PipelineEvent(
            event_id=f"jenkins_{build.get('number', 'unknown')}_{int(time.time())}",
            platform=CICDPlatform.JENKINS,
            event_type=event_type,
            pipeline_id=build.get("full_url", ""),
            pipeline_name=payload.get("name", "Unknown"),
            status=status,
            branch=build.get("scm", {}).get("branch", "unknown"),
            commit_hash=build.get("scm", {}).get("commit", "unknown"),
            commit_message="",
            author="",
            timestamp=datetime.now(),
            duration=build.get("duration"),
            build_number=build.get("number"),
            logs_url=build.get("log"),
            raw_payload=payload,
        )

    async def _handle_gitlab_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        connection: CICDConnection,
    ) -> PipelineEvent:
        """Handle GitLab CI webhook"""

        object_kind = payload.get("object_kind")

        if object_kind == "pipeline":
            pipeline = payload.get("object_attributes", {})

            # Map GitLab status to our enum
            status_mapping = {
                "success": PipelineStatus.SUCCESS,
                "failed": PipelineStatus.FAILED,
                "canceled": PipelineStatus.CANCELLED,
                "skipped": PipelineStatus.SKIPPED,
                "running": PipelineStatus.RUNNING,
                "pending": PipelineStatus.PENDING,
            }

            status = status_mapping.get(pipeline.get("status"), PipelineStatus.PENDING)

            # Determine event type
            if status == PipelineStatus.RUNNING:
                event_type = WebhookEventType.PIPELINE_STARTED
            elif status in [
                PipelineStatus.SUCCESS,
                PipelineStatus.FAILED,
                PipelineStatus.CANCELLED,
            ]:
                event_type = WebhookEventType.PIPELINE_COMPLETED
            else:
                event_type = WebhookEventType.PIPELINE_STARTED

            commit = payload.get("commit", {})

            return PipelineEvent(
                event_id=f"gitlab_{pipeline.get('id')}_{int(time.time())}",
                platform=CICDPlatform.GITLAB_CI,
                event_type=event_type,
                pipeline_id=str(pipeline.get("id")),
                pipeline_name=payload.get("project", {}).get("name", "Unknown"),
                status=status,
                branch=pipeline.get("ref", "unknown"),
                commit_hash=commit.get("id", "unknown"),
                commit_message=commit.get("message", ""),
                author=commit.get("author", {}).get("name", ""),
                timestamp=datetime.fromisoformat(
                    pipeline.get("created_at", datetime.now().isoformat())
                ),
                duration=pipeline.get("duration"),
                raw_payload=payload,
            )

        # Handle other GitLab webhook types as needed
        return self._create_default_event(CICDPlatform.GITLAB_CI, payload)

    async def _handle_github_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        connection: CICDConnection,
    ) -> PipelineEvent:
        """Handle GitHub Actions webhook"""

        action = payload.get("action")
        workflow_run = payload.get("workflow_run", {})

        if workflow_run:
            # Map GitHub status to our enum
            status_mapping = {
                "completed": (
                    PipelineStatus.SUCCESS
                    if workflow_run.get("conclusion") == "success"
                    else PipelineStatus.FAILED
                ),
                "in_progress": PipelineStatus.RUNNING,
                "queued": PipelineStatus.PENDING,
                "requested": PipelineStatus.PENDING,
            }

            status = status_mapping.get(
                workflow_run.get("status"), PipelineStatus.PENDING
            )

            # Determine event type
            if action == "requested" or workflow_run.get("status") == "in_progress":
                event_type = WebhookEventType.PIPELINE_STARTED
            elif action == "completed":
                event_type = WebhookEventType.PIPELINE_COMPLETED
            else:
                event_type = WebhookEventType.PIPELINE_STARTED

            head_commit = workflow_run.get("head_commit", {})

            return PipelineEvent(
                event_id=f"github_{workflow_run.get('id')}_{int(time.time())}",
                platform=CICDPlatform.GITHUB_ACTIONS,
                event_type=event_type,
                pipeline_id=str(workflow_run.get("id")),
                pipeline_name=workflow_run.get("name", "Unknown"),
                status=status,
                branch=workflow_run.get("head_branch", "unknown"),
                commit_hash=workflow_run.get("head_sha", "unknown"),
                commit_message=head_commit.get("message", ""),
                author=head_commit.get("author", {}).get("name", ""),
                timestamp=datetime.fromisoformat(
                    workflow_run.get("created_at", datetime.now().isoformat())
                ),
                build_number=workflow_run.get("run_number"),
                logs_url=workflow_run.get("logs_url"),
                raw_payload=payload,
            )

        return self._create_default_event(CICDPlatform.GITHUB_ACTIONS, payload)

    async def _handle_azure_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        connection: CICDConnection,
    ) -> PipelineEvent:
        """Handle Azure DevOps webhook"""

        event_type_header = headers.get("x-vss-activityid", "")
        resource = payload.get("resource", {})

        # Map Azure status to our enum
        status_mapping = {
            "succeeded": PipelineStatus.SUCCESS,
            "failed": PipelineStatus.FAILED,
            "canceled": PipelineStatus.CANCELLED,
            "inProgress": PipelineStatus.RUNNING,
            "notStarted": PipelineStatus.PENDING,
        }

        status = status_mapping.get(
            resource.get("result", resource.get("status")), PipelineStatus.PENDING
        )

        # Determine event type based on status
        if status == PipelineStatus.RUNNING:
            event_type = WebhookEventType.PIPELINE_STARTED
        elif status in [
            PipelineStatus.SUCCESS,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED,
        ]:
            event_type = WebhookEventType.PIPELINE_COMPLETED
        else:
            event_type = WebhookEventType.PIPELINE_STARTED

        return PipelineEvent(
            event_id=f"azure_{resource.get('id', 'unknown')}_{int(time.time())}",
            platform=CICDPlatform.AZURE_DEVOPS,
            event_type=event_type,
            pipeline_id=str(resource.get("id", "unknown")),
            pipeline_name=resource.get("definition", {}).get("name", "Unknown"),
            status=status,
            branch=resource.get("sourceBranch", "unknown"),
            commit_hash=resource.get("sourceVersion", "unknown"),
            commit_message="",
            author=resource.get("requestedFor", {}).get("displayName", ""),
            timestamp=datetime.fromisoformat(
                resource.get("startTime", datetime.now().isoformat())
            ),
            build_number=resource.get("buildNumber"),
            logs_url=resource.get("_links", {}).get("web", {}).get("href"),
            raw_payload=payload,
        )

    async def _handle_bitbucket_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        connection: CICDConnection,
    ) -> PipelineEvent:
        """Handle Bitbucket Pipelines webhook"""

        # Bitbucket webhook implementation
        return self._create_default_event(CICDPlatform.BITBUCKET_PIPELINES, payload)

    def _create_default_event(
        self, platform: CICDPlatform, payload: Dict[str, Any]
    ) -> PipelineEvent:
        """Create default pipeline event for unknown webhook formats"""

        return PipelineEvent(
            event_id=f"{platform.value}_{int(time.time())}",
            platform=platform,
            event_type=WebhookEventType.PIPELINE_STARTED,
            pipeline_id="unknown",
            pipeline_name="Unknown Pipeline",
            status=PipelineStatus.PENDING,
            branch="unknown",
            commit_hash="unknown",
            commit_message="",
            author="",
            timestamp=datetime.now(),
            raw_payload=payload,
        )

    async def _trigger_event_handlers(self, event: PipelineEvent):
        """Trigger event handlers for pipeline events"""

        try:
            # Fashion industry specific handling
            if self._is_fashion_related_pipeline(event):
                await self._handle_fashion_pipeline_event(event)

            # General event handling
            if event.event_type == WebhookEventType.PIPELINE_COMPLETED:
                if event.status == PipelineStatus.SUCCESS:
                    await self._handle_successful_pipeline(event)
                elif event.status == PipelineStatus.FAILED:
                    await self._handle_failed_pipeline(event)

            # Code quality and security handling
            if event.code_quality_metrics:
                await self._handle_code_quality_update(event)

            if event.security_scan_results:
                await self._handle_security_scan_results(event)

        except Exception as e:
            logger.error(f"Error in event handler: {e}")

    def _is_fashion_related_pipeline(self, event: PipelineEvent) -> bool:
        """Check if pipeline is related to fashion industry"""
        fashion_keywords = [
            "fashion",
            "trend",
            "style",
            "apparel",
            "clothing",
            "retail",
            "ecommerce",
            "inventory",
            "product-catalog",
        ]

        pipeline_name_lower = event.pipeline_name.lower()
        branch_lower = event.branch.lower()

        return any(
            keyword in pipeline_name_lower or keyword in branch_lower
            for keyword in fashion_keywords
        )

    async def _handle_fashion_pipeline_event(self, event: PipelineEvent):
        """Handle fashion industry specific pipeline events"""

        # Fashion-specific logic
        if "trend" in event.pipeline_name.lower():
            logger.info(f"Fashion trend pipeline event: {event.pipeline_name}")
            # Trigger trend analysis updates

        elif "inventory" in event.pipeline_name.lower():
            logger.info(f"Inventory pipeline event: {event.pipeline_name}")
            # Trigger inventory cache invalidation

        elif "product" in event.pipeline_name.lower():
            logger.info(f"Product pipeline event: {event.pipeline_name}")
            # Trigger product catalog updates

    async def _handle_successful_pipeline(self, event: PipelineEvent):
        """Handle successful pipeline completion"""
        logger.info(
            f"Pipeline succeeded: {event.pipeline_name} ({event.platform.value})"
        )

        # Send success notification
        # Update deployment status
        # Trigger downstream processes

    async def _handle_failed_pipeline(self, event: PipelineEvent):
        """Handle failed pipeline"""
        logger.error(f"Pipeline failed: {event.pipeline_name} ({event.platform.value})")

        # Send failure notification
        # Create incident ticket
        # Trigger rollback if needed

    async def _handle_code_quality_update(self, event: PipelineEvent):
        """Handle code quality metrics update"""
        logger.info(f"Code quality updated: {event.pipeline_name}")

        # Store quality metrics
        # Update quality dashboard
        # Send alerts if quality degraded

    async def _handle_security_scan_results(self, event: PipelineEvent):
        """Handle security scan results"""
        logger.info(f"Security scan completed: {event.pipeline_name}")

        # Store security results
        # Send security alerts
        # Block deployment if critical issues found

    async def trigger_pipeline(
        self,
        connection_name: str,
        pipeline_id: str,
        branch: str = "main",
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Trigger pipeline execution via API"""

        connection = self.connections.get(connection_name)
        if not connection:
            raise ValueError(f"Connection not found: {connection_name}")

        start_time = time.time()

        try:
            if connection.platform == CICDPlatform.JENKINS:
                result = await self._trigger_jenkins_pipeline(
                    connection, pipeline_id, parameters
                )
            elif connection.platform == CICDPlatform.GITLAB_CI:
                result = await self._trigger_gitlab_pipeline(
                    connection, pipeline_id, branch, parameters
                )
            elif connection.platform == CICDPlatform.GITHUB_ACTIONS:
                result = await self._trigger_github_workflow(
                    connection, pipeline_id, branch, parameters
                )
            elif connection.platform == CICDPlatform.AZURE_DEVOPS:
                result = await self._trigger_azure_pipeline(
                    connection, pipeline_id, branch, parameters
                )
            else:
                raise ValueError(
                    f"Pipeline triggering not implemented for {connection.platform.value}"
                )

            # Update metrics
            response_time = (time.time() - start_time) * 1000
            self.metrics["total_api_calls"] += 1
            self.metrics["successful_api_calls"] += 1
            self._update_avg_response_time(response_time)

            logger.info(
                f"Pipeline triggered: {pipeline_id} on {connection.platform.value}"
            )
            return result

        except Exception as e:
            # Update metrics
            response_time = (time.time() - start_time) * 1000
            self.metrics["total_api_calls"] += 1
            self.metrics["failed_api_calls"] += 1
            self._update_avg_response_time(response_time)

            logger.error(f"Failed to trigger pipeline {pipeline_id}: {e}")
            raise

    async def _trigger_jenkins_pipeline(
        self,
        connection: CICDConnection,
        job_name: str,
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Trigger Jenkins pipeline"""

        auth = (
            (connection.username, connection.api_token) if connection.username else None
        )

        if parameters:
            url = f"{connection.base_url}/job/{job_name}/buildWithParameters"
            response = await self.http_client.post(url, data=parameters, auth=auth)
        else:
            url = f"{connection.base_url}/job/{job_name}/build"
            response = await self.http_client.post(url, auth=auth)

        response.raise_for_status()

        return {
            "status": "triggered",
            "platform": "jenkins",
            "job_name": job_name,
            "queue_url": response.headers.get("Location"),
        }

    async def _trigger_gitlab_pipeline(
        self,
        connection: CICDConnection,
        project_id: str,
        branch: str,
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Trigger GitLab CI pipeline"""

        url = f"{connection.base_url}/api/v4/projects/{project_id}/pipeline"

        payload = {"ref": branch}

        if parameters:
            payload["variables"] = [
                {"key": k, "value": str(v)} for k, v in parameters.items()
            ]

        headers = {"PRIVATE-TOKEN": connection.api_token}

        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()

        return {
            "status": "triggered",
            "platform": "gitlab_ci",
            "pipeline_id": result.get("id"),
            "web_url": result.get("web_url"),
        }

    async def _trigger_github_workflow(
        self,
        connection: CICDConnection,
        workflow_id: str,
        branch: str,
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Trigger GitHub Actions workflow"""

        url = f"{connection.base_url}/repos/{connection.organization}/{connection.project_id}/actions/workflows/{workflow_id}/dispatches"

        payload = {"ref": branch}

        if parameters:
            payload["inputs"] = parameters

        headers = {
            "Authorization": f"token {connection.api_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return {
            "status": "triggered",
            "platform": "github_actions",
            "workflow_id": workflow_id,
            "ref": branch,
        }

    async def _trigger_azure_pipeline(
        self,
        connection: CICDConnection,
        pipeline_id: str,
        branch: str,
        parameters: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Trigger Azure DevOps pipeline"""

        url = f"{connection.base_url}/{connection.organization}/{connection.project_id}/_apis/pipelines/{pipeline_id}/runs"

        payload = {
            "resources": {"repositories": {"self": {"refName": f"refs/heads/{branch}"}}}
        }

        if parameters:
            payload["variables"] = {k: {"value": str(v)} for k, v in parameters.items()}

        headers = {
            "Authorization": f'Basic {base64.b64encode(f":{connection.api_token}".encode()).decode()}',
            "Content-Type": "application/json",
        }

        response = await self.http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()

        result = response.json()

        return {
            "status": "triggered",
            "platform": "azure_devops",
            "run_id": result.get("id"),
            "web_url": result.get("_links", {}).get("web", {}).get("href"),
        }

    def _update_avg_response_time(self, response_time: float):
        """Update average API response time"""
        if self.metrics["avg_response_time"] == 0:
            self.metrics["avg_response_time"] = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics["avg_response_time"] = (
                alpha * response_time + (1 - alpha) * self.metrics["avg_response_time"]
            )

        self.metrics["last_updated"] = datetime.now()

    async def get_pipeline_status(
        self, connection_name: str, pipeline_id: str
    ) -> Dict[str, Any]:
        """Get pipeline status via API"""

        connection = self.connections.get(connection_name)
        if not connection:
            raise ValueError(f"Connection not found: {connection_name}")

        # Implementation depends on platform
        # This would query the specific platform's API for pipeline status

        return {
            "pipeline_id": pipeline_id,
            "status": "unknown",
            "platform": connection.platform.value,
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get CI/CD integration metrics"""

        return {
            "api_metrics": self.metrics,
            "connections": {
                name: {
                    "platform": conn.platform.value,
                    "enabled": conn.enabled,
                    "base_url": conn.base_url,
                }
                for name, conn in self.connections.items()
            },
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "platform": event.platform.value,
                    "event_type": event.event_type.value,
                    "pipeline_name": event.pipeline_name,
                    "status": event.status.value,
                    "timestamp": event.timestamp.isoformat(),
                }
                for event in self.event_history[-10:]  # Last 10 events
            ],
            "event_counts": {
                platform.value: len()
                    [e for e in self.event_history if e.platform == platform]
                )
                for platform in CICDPlatform
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""

        try:
            # Test connections
            connection_health = {}
            for name, conn in self.connections.items():
                if conn.enabled:
                    try:
                        # Simple connectivity test
                        response = await self.http_client.get(conn.base_url, timeout=5)
                        connection_health[name] = (
                            "healthy" if response.status_code < 500 else "degraded"
                        )
                    except Exception as e:
                        logger.warning(f"Health check failed for {name}: {e}")
                        connection_health[name] = "unhealthy"
                else:
                    connection_health[name] = "disabled"

            overall_health = (
                "healthy"
                if all(
                    status in ["healthy", "disabled"]
                    for status in connection_health.values()
                )
                else "degraded"
            )

            return {
                "status": overall_health,
                "connections": connection_health,
                "total_connections": len(self.connections),
                "active_connections": len()
                    [c for c in self.connections.values() if c.enabled]
                ),
                "webhook_handlers": len(self.webhook_handlers),
                "recent_events": len(self.event_history),
                "metrics": await self.get_metrics(),
            }

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def close(self):
        """Close HTTP client and cleanup"""
        await self.http_client.aclose()
        logger.info("CI/CD integration manager closed")

# Global CI/CD integration manager instance
cicd_manager = CICDIntegrationManager()
