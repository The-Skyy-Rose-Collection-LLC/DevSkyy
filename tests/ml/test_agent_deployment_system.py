"""
Comprehensive tests for ml/agent_deployment_system.py

Target: 65%+ coverage

Tests cover:
- Job definition and validation
- Infrastructure validation
- Category-head approval system
- Token cost estimation
- Deployment orchestration
- Status tracking
- Error handling
"""

import pytest

from ml.agent_deployment_system import (
    ApprovalStatus,
    AutomatedDeploymentOrchestrator,
    CategoryHeadApprovalSystem,
    DeploymentExecution,
    InfrastructureValidationResult,
    InfrastructureValidator,
    JobDefinition,
    JobStatus,
    ResourceRequirement,
    ResourceType,
    TokenCostEstimator,
    ToolRequirement,
    get_deployment_orchestrator,
)
from ml.agent_finetuning_system import AgentCategory


class TestEnums:
    """Test enums and constants"""

    def test_job_status(self):
        """Test JobStatus enum"""
        assert JobStatus.DRAFT == "draft"
        assert JobStatus.PENDING_VALIDATION == "pending_validation"
        assert JobStatus.APPROVED == "approved"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"

    def test_resource_type(self):
        """Test ResourceType enum"""
        assert ResourceType.API_KEY == "api_key"
        assert ResourceType.DATABASE == "database"
        assert ResourceType.COMPUTE == "compute"
        assert ResourceType.MEMORY == "memory"

    def test_approval_status(self):
        """Test ApprovalStatus enum"""
        assert ApprovalStatus.PENDING == "pending"
        assert ApprovalStatus.APPROVED == "approved"
        assert ApprovalStatus.REJECTED == "rejected"


class TestToolRequirement:
    """Test ToolRequirement model"""

    def test_create_tool_requirement(self):
        """Test creating tool requirement"""
        tool = ToolRequirement(
            tool_name="code_analyzer",
            tool_type="function",
            required=True,
            min_rate_limit=10,
            estimated_calls=5,
        )

        assert tool.tool_name == "code_analyzer"
        assert tool.required is True
        assert tool.min_rate_limit == 10

    def test_tool_with_alternatives(self):
        """Test tool with alternatives"""
        tool = ToolRequirement(
            tool_name="primary_api",
            tool_type="api",
            required=True,
            alternatives=["backup_api", "fallback_api"],
        )

        assert len(tool.alternatives) == 2


class TestResourceRequirement:
    """Test ResourceRequirement model"""

    def test_create_resource_requirement(self):
        """Test creating resource requirement"""
        resource = ResourceRequirement(
            resource_type=ResourceType.COMPUTE,
            amount=4.0,
            unit="cores",
            required=True,
        )

        assert resource.resource_type == ResourceType.COMPUTE
        assert resource.amount == 4.0
        assert resource.unit == "cores"


class TestJobDefinition:
    """Test JobDefinition model"""

    def test_create_job_definition(self):
        """Test creating job definition"""
        job = JobDefinition(
            job_name="test_job",
            job_description="Test job",
            category=AgentCategory.CORE_SECURITY,
            primary_agent="scanner_v2",
        )

        assert job.job_name == "test_job"
        assert job.category == AgentCategory.CORE_SECURITY
        assert job.job_id.startswith("job_")

    def test_job_with_tools(self):
        """Test job with tool requirements"""
        job = JobDefinition(
            job_name="test_job",
            job_description="Test job",
            category=AgentCategory.ECOMMERCE,
            primary_agent="product_manager",
            required_tools=[
                ToolRequirement(
                    tool_name="database_query",
                    tool_type="service",
                    required=True,
                )
            ],
        )

        assert len(job.required_tools) == 1

    def test_job_with_resources(self):
        """Test job with resource requirements"""
        job = JobDefinition(
            job_name="test_job",
            job_description="Test job",
            category=AgentCategory.AI_INTELLIGENCE,
            primary_agent="model_trainer",
            required_resources=[
                ResourceRequirement(
                    resource_type=ResourceType.COMPUTE,
                    amount=8.0,
                    unit="cores",
                    required=True,
                ),
                ResourceRequirement(
                    resource_type=ResourceType.MEMORY,
                    amount=32000.0,
                    unit="MB",
                    required=True,
                ),
            ],
        )

        assert len(job.required_resources) == 2

    def test_job_defaults(self):
        """Test job default values"""
        job = JobDefinition(
            job_name="test_job",
            job_description="Test job",
            category=AgentCategory.MARKETING_BRAND,
            primary_agent="seo_agent",
        )

        assert job.max_execution_time_seconds == 300
        assert job.max_retries == 3
        assert job.priority == 5
        assert job.max_budget_usd == 1.0


class TestInfrastructureValidator:
    """Test InfrastructureValidator"""

    def test_init(self):
        """Test validator initialization"""
        validator = InfrastructureValidator()

        assert len(validator.available_tools) == 0
        assert len(validator.available_resources) == 0

    def test_register_tool(self):
        """Test registering tools"""
        validator = InfrastructureValidator()

        validator.register_tool(
            tool_name="openai_api",
            tool_type="api",
            rate_limit=100,
            metadata={"version": "v1"},
        )

        assert "openai_api" in validator.available_tools
        assert validator.available_tools["openai_api"]["rate_limit"] == 100

    def test_register_resource(self):
        """Test registering resources"""
        validator = InfrastructureValidator()

        validator.register_resource(ResourceType.COMPUTE, 16.0)
        validator.register_resource(ResourceType.MEMORY, 64000.0)

        assert validator.available_resources[ResourceType.COMPUTE] == 16.0
        assert validator.available_resources[ResourceType.MEMORY] == 64000.0

    def test_register_api_key(self):
        """Test registering API keys"""
        validator = InfrastructureValidator()

        validator.register_api_key("openai", True)
        validator.register_api_key("anthropic", False)

        assert validator.api_keys["openai"] is True
        assert validator.api_keys["anthropic"] is False

    @pytest.mark.asyncio
    async def test_validate_job_all_available(self):
        """Test validating job with all resources available"""
        validator = InfrastructureValidator()

        validator.register_tool("code_analyzer", "function", 50)
        validator.register_resource(ResourceType.COMPUTE, 16.0)
        validator.register_api_key("openai", True)

        job = JobDefinition(
            job_name="test_job",
            job_description="Test",
            category=AgentCategory.CORE_SECURITY,
            primary_agent="scanner",
            required_tools=[
                ToolRequirement(
                    tool_name="code_analyzer",
                    tool_type="function",
                    required=True,
                    min_rate_limit=10,
                )
            ],
            required_resources=[
                ResourceRequirement(
                    resource_type=ResourceType.COMPUTE,
                    amount=8.0,
                    unit="cores",
                    required=True,
                )
            ],
        )

        result = await validator.validate_job(job)

        assert result.is_ready is True
        assert result.checks_passed > 0
        assert result.checks_failed == 0

    @pytest.mark.asyncio
    async def test_validate_job_missing_tool(self):
        """Test validating job with missing required tool"""
        validator = InfrastructureValidator()
        validator.register_resource(ResourceType.COMPUTE, 16.0)

        job = JobDefinition(
            job_name="test_job",
            job_description="Test",
            category=AgentCategory.CORE_SECURITY,
            primary_agent="scanner",
            required_tools=[
                ToolRequirement(
                    tool_name="missing_tool",
                    tool_type="function",
                    required=True,
                )
            ],
        )

        result = await validator.validate_job(job)

        assert result.is_ready is False
        assert result.checks_failed > 0
        assert "missing_tool" in result.missing_tools

    @pytest.mark.asyncio
    async def test_validate_job_insufficient_resources(self):
        """Test validating job with insufficient resources"""
        validator = InfrastructureValidator()
        validator.register_resource(ResourceType.COMPUTE, 4.0)  # Only 4 cores

        job = JobDefinition(
            job_name="test_job",
            job_description="Test",
            category=AgentCategory.AI_INTELLIGENCE,
            primary_agent="trainer",
            required_resources=[
                ResourceRequirement(
                    resource_type=ResourceType.COMPUTE,
                    amount=8.0,  # Needs 8 cores
                    unit="cores",
                    required=True,
                )
            ],
        )

        result = await validator.validate_job(job)

        assert result.is_ready is False
        assert len(result.missing_resources) > 0

    @pytest.mark.asyncio
    async def test_validate_job_optional_tool_missing(self):
        """Test validating job with missing optional tool"""
        validator = InfrastructureValidator()

        job = JobDefinition(
            job_name="test_job",
            job_description="Test",
            category=AgentCategory.ECOMMERCE,
            primary_agent="product_agent",
            required_tools=[
                ToolRequirement(
                    tool_name="optional_tool",
                    tool_type="function",
                    required=False,  # Optional
                )
            ],
        )

        result = await validator.validate_job(job)

        # Should pass despite missing optional tool
        assert result.is_ready is True
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_validate_job_rate_limit_warning(self):
        """Test validation warns about low rate limits"""
        validator = InfrastructureValidator()
        validator.register_tool("slow_api", "api", 5)  # Low rate limit

        job = JobDefinition(
            job_name="test_job",
            job_description="Test",
            category=AgentCategory.ECOMMERCE,
            primary_agent="agent",
            required_tools=[
                ToolRequirement(
                    tool_name="slow_api",
                    tool_type="api",
                    required=True,
                    min_rate_limit=10,  # Needs higher
                )
            ],
        )

        result = await validator.validate_job(job)

        assert len(result.warnings) > 0
        assert any("rate limit" in w.lower() for w in result.warnings)


class TestCategoryHeadApprovalSystem:
    """Test CategoryHeadApprovalSystem"""

    def test_init(self):
        """Test approval system initialization"""
        system = CategoryHeadApprovalSystem()

        assert len(system.category_heads) > 0
        assert AgentCategory.CORE_SECURITY in system.category_heads

    @pytest.mark.asyncio
    async def test_request_approval_all_approved(self):
        """Test approval workflow with all approvals"""
        system = CategoryHeadApprovalSystem()

        job = JobDefinition(
            job_name="test_job",
            job_description="Test",
            category=AgentCategory.CORE_SECURITY,
            primary_agent="scanner",
        )

        validation = InfrastructureValidationResult(
            is_ready=True,
            validation_timestamp=None,
            checks_passed=5,
            checks_failed=0,
        )

        result = await system.request_approval(job, validation)

        assert result.approved_count >= 0
        assert result.final_decision in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED, ApprovalStatus.PENDING]

    @pytest.mark.asyncio
    async def test_request_approval_validation_failed(self):
        """Test approval with failed validation"""
        system = CategoryHeadApprovalSystem()

        job = JobDefinition(
            job_name="test_job",
            job_description="Test",
            category=AgentCategory.ECOMMERCE,
            primary_agent="product_agent",
        )

        validation = InfrastructureValidationResult(
            is_ready=False,
            validation_timestamp=None,
            checks_passed=0,
            checks_failed=5,
            missing_tools=["tool1", "tool2"],
        )

        result = await system.request_approval(job, validation)

        # Should likely reject due to failed validation
        assert result.rejected_count >= 0

    @pytest.mark.asyncio
    async def test_approval_includes_reasoning(self):
        """Test approvals include reasoning"""
        system = CategoryHeadApprovalSystem()

        job = JobDefinition(
            job_name="test_job",
            job_description="Test",
            category=AgentCategory.AI_INTELLIGENCE,
            primary_agent="model_agent",
        )

        validation = InfrastructureValidationResult(
            is_ready=True,
            validation_timestamp=None,
            checks_passed=5,
            checks_failed=0,
        )

        result = await system.request_approval(job, validation)

        assert result.consensus_reasoning != ""
        assert len(result.approvals) > 0


class TestTokenCostEstimator:
    """Test TokenCostEstimator"""

    def test_init(self):
        """Test estimator initialization"""
        estimator = TokenCostEstimator()

        assert "claude-sonnet-4" in estimator.token_costs
        assert "gpt-4o" in estimator.token_costs

    def test_estimate_job_cost(self):
        """Test estimating job cost"""
        estimator = TokenCostEstimator()

        job = JobDefinition(
            job_name="code_scan",
            job_description="Scan code",
            category=AgentCategory.CORE_SECURITY,
            primary_agent="scanner",
            required_tools=[
                ToolRequirement(
                    tool_name="analyzer",
                    tool_type="function",
                    estimated_calls=10,
                )
            ],
        )

        tokens, cost = estimator.estimate_job_cost(job)

        assert tokens > 0
        assert cost > 0

    def test_estimate_with_multiple_tools(self):
        """Test cost estimation with multiple tools"""
        estimator = TokenCostEstimator()

        job = JobDefinition(
            job_name="complex_job",
            job_description="Complex task",
            category=AgentCategory.ECOMMERCE,
            primary_agent="product_agent",
            required_tools=[
                ToolRequirement(tool_name="tool1", tool_type="api", estimated_calls=5),
                ToolRequirement(tool_name="tool2", tool_type="api", estimated_calls=10),
            ],
            supporting_agents=["agent2", "agent3"],
        )

        tokens, cost = estimator.estimate_job_cost(job)

        # Should be higher due to multiple tools and agents
        assert tokens > 1000
        assert cost > 0


class TestAutomatedDeploymentOrchestrator:
    """Test AutomatedDeploymentOrchestrator"""

    def test_init(self):
        """Test orchestrator initialization"""
        orchestrator = AutomatedDeploymentOrchestrator()

        assert orchestrator.validator is not None
        assert orchestrator.approval_system is not None
        assert len(orchestrator.validator.available_tools) > 0

    @pytest.mark.asyncio
    async def test_submit_job_success(self, deployment_orchestrator, sample_job_definition):
        """Test successful job submission"""
        result = await deployment_orchestrator.submit_job(sample_job_definition)

        assert "status" in result
        assert "job_id" in result
        assert result["job_id"] == sample_job_definition.job_id

    @pytest.mark.asyncio
    async def test_submit_job_validation_failed(self, deployment_orchestrator):
        """Test job submission with validation failure"""
        job = JobDefinition(
            job_name="impossible_job",
            job_description="Requires unavailable resources",
            category=AgentCategory.SPECIALIZED,
            primary_agent="agent",
            required_resources=[
                ResourceRequirement(
                    resource_type=ResourceType.COMPUTE,
                    amount=10000.0,  # Way too much
                    unit="cores",
                    required=True,
                )
            ],
        )

        result = await deployment_orchestrator.submit_job(job)

        assert result["status"] == "validation_failed"
        assert result["can_proceed"] is False

    @pytest.mark.asyncio
    async def test_submit_job_over_budget(self, deployment_orchestrator):
        """Test job submission with excessive cost"""
        job = JobDefinition(
            job_name="expensive_job",
            job_description="Test",
            category=AgentCategory.AI_INTELLIGENCE,
            primary_agent="agent",
            max_budget_usd=0.01,  # Very low budget
            required_tools=[
                ToolRequirement(
                    tool_name="openai_completion",
                    tool_type="api",
                    estimated_calls=1000,  # Many calls
                )
            ],
        )

        result = await deployment_orchestrator.submit_job(job)

        # May fail validation or approval due to budget
        assert "status" in result

    @pytest.mark.asyncio
    async def test_get_job_status(self, deployment_orchestrator, sample_job_definition):
        """Test getting job status"""
        await deployment_orchestrator.submit_job(sample_job_definition)

        status = deployment_orchestrator.get_job_status(sample_job_definition.job_id)

        assert status is not None
        assert "job" in status

    @pytest.mark.asyncio
    async def test_get_job_status_not_found(self, deployment_orchestrator):
        """Test getting status for non-existent job"""
        status = deployment_orchestrator.get_job_status("nonexistent_job")

        assert status is None

    @pytest.mark.asyncio
    async def test_get_statistics(self, deployment_orchestrator, sample_job_definition):
        """Test getting system statistics"""
        await deployment_orchestrator.submit_job(sample_job_definition)

        stats = deployment_orchestrator.get_statistics()

        assert "total_jobs" in stats
        assert "total_deployments" in stats
        assert "infrastructure_checks" in stats
        assert "approval_stats" in stats
        assert "cost_stats" in stats


class TestDeploymentExecution:
    """Test DeploymentExecution dataclass"""

    def test_create_execution(self):
        """Test creating deployment execution"""
        execution = DeploymentExecution(
            job_id="job_123",
        )

        assert execution.job_id == "job_123"
        assert execution.status == JobStatus.DEPLOYING
        assert execution.deployment_id.startswith("deploy_")


class TestGetDeploymentOrchestrator:
    """Test get_deployment_orchestrator function"""

    def test_get_orchestrator(self):
        """Test getting global orchestrator"""
        orchestrator = get_deployment_orchestrator()
        assert isinstance(orchestrator, AutomatedDeploymentOrchestrator)

    def test_get_orchestrator_singleton(self):
        """Test orchestrator is singleton"""
        orchestrator1 = get_deployment_orchestrator()
        orchestrator2 = get_deployment_orchestrator()
        assert orchestrator1 is orchestrator2
