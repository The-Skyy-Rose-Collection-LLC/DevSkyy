"""
Agent Deployment API Endpoints for DevSkyy
RESTful API for managing automated agent deployments with multi-agent approval

Per Truth Protocol:
- Rule #1: Never guess - Validate all job parameters
- Rule #6: RBAC roles - Role-based access control
- Rule #7: Input validation - Schema enforcement
- Rule #9: Document all - Auto-generate OpenAPI
- Rule #12: Performance SLOs - Track token usage

Endpoints:
- POST /api/v1/deployment/jobs - Submit new deployment job
- GET /api/v1/deployment/jobs/{job_id} - Get job status
- GET /api/v1/deployment/jobs - List all jobs
- POST /api/v1/deployment/validate - Validate job without deploying
- GET /api/v1/deployment/approvals/{job_id} - Get approval status
- POST /api/v1/deployment/tools/register - Register available tool
- POST /api/v1/deployment/resources/register - Register available resource
- GET /api/v1/deployment/infrastructure - Get infrastructure status
- GET /api/v1/deployment/statistics - Get system statistics
"""

from datetime import datetime
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from core.dependencies import get_current_user, require_role
from ml.agent_deployment_system import (
    JobDefinition,
    ResourceRequirement,
    ResourceType,
    ToolRequirement,
    get_deployment_orchestrator,
)
from ml.agent_finetuning_system import AgentCategory
from security.rbac import Role


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/deployment", tags=["deployment"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SubmitJobRequest(BaseModel):
    """Request to submit a deployment job"""
    job_name: str
    job_description: str
    category: AgentCategory
    primary_agent: str
    supporting_agents: list[str] = Field(default_factory=list)
    required_tools: list[ToolRequirement] = Field(default_factory=list)
    required_resources: list[ResourceRequirement] = Field(default_factory=list)
    max_execution_time_seconds: int = Field(default=300, ge=1, le=3600)
    max_retries: int = Field(default=3, ge=0, le=10)
    priority: int = Field(default=5, ge=1, le=10)
    max_budget_usd: float = Field(default=1.0, gt=0)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class JobStatusResponse(BaseModel):
    """Response with complete job status"""
    job_id: str
    job_name: str
    category: str
    status: str
    validation_status: dict[str, Any] | None = None
    approval_status: dict[str, Any] | None = None
    deployment_status: dict[str, Any] | None = None
    estimated_tokens: int
    estimated_cost_usd: float
    actual_tokens_used: int = 0
    actual_cost_usd: float = 0.0


class ValidateJobRequest(BaseModel):
    """Request to validate job without deploying"""
    job_definition: JobDefinition


class RegisterToolRequest(BaseModel):
    """Request to register an available tool"""
    tool_name: str
    tool_type: str  # "function", "api", "service"
    rate_limit: int = Field(gt=0, description="Requests per minute")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RegisterResourceRequest(BaseModel):
    """Request to register available resource"""
    resource_type: ResourceType
    amount: float = Field(gt=0)
    unit: str


class InfrastructureStatusResponse(BaseModel):
    """Response with infrastructure status"""
    available_tools: dict[str, Any]
    available_resources: dict[str, Any]
    api_keys_configured: dict[str, bool]
    total_tools: int
    total_resources: int
    readiness_score: float  # 0.0-1.0


# ============================================================================
# JOB MANAGEMENT ENDPOINTS
# ============================================================================

@router.post(
    "/jobs",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Deployment Job",
    description="Submit a new automated agent deployment job"
)
async def submit_job(
    request: SubmitJobRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit a new deployment job.

    Workflow:
    1. Estimate tokens and costs
    2. Validate infrastructure readiness
    3. Request category-head approvals (2 required)
    4. If approved, deploy and execute
    5. Track performance and collect data

    Returns job status with validation and approval results.
    """
    try:
        orchestrator = get_deployment_orchestrator()

        # Create job definition
        job = JobDefinition(
            job_name=request.job_name,
            job_description=request.job_description,
            category=request.category,
            primary_agent=request.primary_agent,
            supporting_agents=request.supporting_agents,
            required_tools=request.required_tools,
            required_resources=request.required_resources,
            max_execution_time_seconds=request.max_execution_time_seconds,
            max_retries=request.max_retries,
            priority=request.priority,
            max_budget_usd=request.max_budget_usd,
            input_schema=request.input_schema,
            output_schema=request.output_schema,
            created_by=current_user.get("sub", "unknown"),
            tags=request.tags
        )

        # Submit job
        result = await orchestrator.submit_job(job)

        return {
            "status": "success",
            "message": f"Job submitted: {result['status']}",
            "job_id": result["job_id"],
            "deployment_id": result.get("deployment_id"),
            "can_proceed": result["can_proceed"],
            "validation": result.get("validation"),
            "approval": result.get("approval"),
            "estimated_tokens": job.estimated_tokens,
            "estimated_cost_usd": job.estimated_cost_usd
        }

    except Exception as e:
        logger.error(f"Failed to submit job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {e!s}"
        )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    summary="Get Job Status",
    description="Get complete status of a deployment job"
)
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get complete status of a deployment job."""
    orchestrator = get_deployment_orchestrator()

    job_status = orchestrator.get_job_status(job_id)
    if not job_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )

    job = job_status["job"]
    deployment = job_status.get("deployment")

    return JobStatusResponse(
        job_id=job["job_id"],
        job_name=job["job_name"],
        category=job["category"],
        status=deployment["status"] if deployment else "pending_validation",
        validation_status=job_status.get("validation"),
        approval_status=job_status.get("approval"),
        deployment_status=deployment,
        estimated_tokens=job["estimated_tokens"],
        estimated_cost_usd=job["estimated_cost_usd"],
        actual_tokens_used=deployment["actual_tokens_used"] if deployment else 0,
        actual_cost_usd=deployment["actual_cost_usd"] if deployment else 0.0
    )


@router.get(
    "/jobs",
    summary="List Jobs",
    description="List all deployment jobs"
)
async def list_jobs(
    category: AgentCategory | None = None,
    current_user: dict = Depends(get_current_user)
):
    """List all deployment jobs, optionally filtered by category."""
    orchestrator = get_deployment_orchestrator()

    jobs = []
    for job_id, job in orchestrator.jobs.items():
        if category and job.category != category:
            continue

        jobs.append({
            "job_id": job.job_id,
            "job_name": job.job_name,
            "category": job.category.value,
            "primary_agent": job.primary_agent,
            "estimated_tokens": job.estimated_tokens,
            "estimated_cost_usd": job.estimated_cost_usd,
            "created_at": job.created_at.isoformat(),
            "created_by": job.created_by
        })

    return {
        "total": len(jobs),
        "jobs": jobs
    }


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================

@router.post(
    "/validate",
    summary="Validate Job",
    description="Validate job without deploying"
)
async def validate_job(
    request: ValidateJobRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Validate a job without deploying.

    Checks:
    - Infrastructure readiness
    - Tool availability
    - Resource allocation
    - Cost estimates

    Returns validation results without executing.
    """
    try:
        orchestrator = get_deployment_orchestrator()

        # Estimate costs
        estimated_tokens, estimated_cost = orchestrator.cost_estimator.estimate_job_cost(
            request.job_definition
        )

        # Validate infrastructure
        validation = await orchestrator.validator.validate_job(request.job_definition)

        return {
            "is_ready": validation.is_ready,
            "checks_passed": validation.checks_passed,
            "checks_failed": validation.checks_failed,
            "missing_tools": validation.missing_tools,
            "missing_resources": validation.missing_resources,
            "warnings": validation.warnings,
            "estimated_tokens": estimated_tokens,
            "estimated_cost_usd": estimated_cost,
            "detailed_results": validation.detailed_results
        }

    except Exception as e:
        logger.error(f"Failed to validate job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate job: {e!s}"
        )


@router.get(
    "/approvals/{job_id}",
    summary="Get Approval Status",
    description="Get multi-agent approval status for a job"
)
async def get_approval_status(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get multi-agent approval status for a job."""
    orchestrator = get_deployment_orchestrator()

    if job_id not in orchestrator.approvals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No approval found for job: {job_id}"
        )

    approval = orchestrator.approvals[job_id]

    return {
        "workflow_id": approval.workflow_id,
        "required_approvals": approval.required_approvals,
        "approved_count": approval.approved_count,
        "rejected_count": approval.rejected_count,
        "final_decision": approval.final_decision.value,
        "consensus_reasoning": approval.consensus_reasoning,
        "individual_approvals": [
            {
                "agent_name": a.agent_name,
                "status": a.approval_status.value,
                "confidence": a.confidence,
                "reasoning": a.reasoning,
                "concerns": a.concerns,
                "recommendations": a.recommendations,
                "timestamp": a.timestamp.isoformat()
            }
            for a in approval.approvals
        ],
        "timestamp": approval.timestamp.isoformat()
    }


# ============================================================================
# INFRASTRUCTURE MANAGEMENT ENDPOINTS
# ============================================================================

@router.post(
    "/tools/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register Tool",
    description="Register an available tool",
    dependencies=[Depends(require_role(Role.ADMIN))]
)
async def register_tool(
    request: RegisterToolRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Register an available tool for deployment.

    Requires ADMIN role.
    """
    orchestrator = get_deployment_orchestrator()

    orchestrator.validator.register_tool(
        tool_name=request.tool_name,
        tool_type=request.tool_type,
        rate_limit=request.rate_limit,
        metadata=request.metadata
    )

    return {
        "status": "success",
        "message": f"Tool registered: {request.tool_name}",
        "tool_name": request.tool_name,
        "rate_limit": request.rate_limit
    }


@router.post(
    "/resources/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register Resource",
    description="Register available resource",
    dependencies=[Depends(require_role(Role.ADMIN))]
)
async def register_resource(
    request: RegisterResourceRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Register available resource for deployment.

    Requires ADMIN role.
    """
    orchestrator = get_deployment_orchestrator()

    orchestrator.validator.register_resource(
        resource_type=request.resource_type,
        amount=request.amount
    )

    return {
        "status": "success",
        "message": f"Resource registered: {request.resource_type.value}",
        "resource_type": request.resource_type.value,
        "amount": request.amount,
        "unit": request.unit
    }


@router.get(
    "/infrastructure",
    response_model=InfrastructureStatusResponse,
    summary="Get Infrastructure Status",
    description="Get current infrastructure status and readiness"
)
async def get_infrastructure_status(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive infrastructure status."""
    orchestrator = get_deployment_orchestrator()

    available_tools = orchestrator.validator.available_tools
    available_resources = orchestrator.validator.available_resources
    api_keys = orchestrator.validator.api_keys

    # Calculate readiness score
    total_checks = len(available_tools) + len(available_resources) + len(api_keys)
    passed_checks = (
        sum(1 for t in available_tools.values() if t.get("available")) +
        len(available_resources) +
        sum(1 for configured in api_keys.values() if configured)
    )

    readiness_score = passed_checks / max(total_checks, 1)

    return InfrastructureStatusResponse(
        available_tools=available_tools,
        available_resources={
            rt.value: amount
            for rt, amount in available_resources.items()
        },
        api_keys_configured=api_keys,
        total_tools=len(available_tools),
        total_resources=len(available_resources),
        readiness_score=readiness_score
    )


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get(
    "/statistics",
    summary="Get System Statistics",
    description="Get comprehensive deployment system statistics"
)
async def get_statistics(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive deployment system statistics."""
    orchestrator = get_deployment_orchestrator()
    return orchestrator.get_statistics()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    summary="Health Check",
    description="Check deployment system health"
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "agent_deployment",
        "timestamp": datetime.now().isoformat()
    }
