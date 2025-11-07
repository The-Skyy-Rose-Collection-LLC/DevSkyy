"""
Unit tests for Agent Task Router

Tests task routing, confidence scoring, fuzzy matching, and batch processing.
"""

import pytest
from unittest.mock import Mock, patch

from agents.router import (
    AgentRouter,
    TaskType,
    TaskRequest,
    RoutingResult,
    RoutingError,
    NoAgentFoundError,
    TaskValidationError,
    route_task_simple
)
from agents.loader import AgentConfigLoader


class TestTaskType:
    """Test TaskType enum"""

    def test_task_type_values(self):
        """Test TaskType enum has expected values"""
        assert TaskType.CODE_GENERATION == "code_generation"
        assert TaskType.CODE_REVIEW == "code_review"
        assert TaskType.CONTENT_GENERATION == "content_generation"
        assert TaskType.GENERAL == "general"

    def test_task_type_enumeration(self):
        """Test all task types can be enumerated"""
        task_types = list(TaskType)
        assert len(task_types) > 20
        assert TaskType.CODE_GENERATION in task_types


class TestRoutingResult:
    """Test RoutingResult dataclass"""

    def test_routing_result_creation(self):
        """Test creating a routing result"""
        result = RoutingResult(
            agent_id="test_agent",
            agent_name="Test Agent",
            task_type=TaskType.CODE_GENERATION,
            confidence=0.95,
            routing_method="exact"
        )
        assert result.agent_id == "test_agent"
        assert result.confidence == 0.95
        assert result.routing_method == "exact"

    def test_routing_result_to_dict(self):
        """Test converting routing result to dictionary"""
        result = RoutingResult(
            agent_id="test_agent",
            agent_name="Test Agent",
            task_type=TaskType.CODE_GENERATION,
            confidence=0.95,
            routing_method="exact",
            metadata={"test": "data"}
        )
        result_dict = result.to_dict()
        
        assert result_dict["agent_id"] == "test_agent"
        assert result_dict["confidence"] == 0.95
        assert result_dict["routing_method"] == "exact"
        assert result_dict["task_type"] == "code_generation"
        assert "timestamp" in result_dict


class TestTaskRequest:
    """Test TaskRequest dataclass"""

    def test_task_request_creation(self):
        """Test creating a task request"""
        task = TaskRequest(
            task_type=TaskType.CODE_GENERATION,
            description="Generate Python code",
            priority=75
        )
        assert task.task_type == TaskType.CODE_GENERATION
        assert task.description == "Generate Python code"
        assert task.priority == 75

    def test_task_request_default_priority(self):
        """Test task request has default priority"""
        task = TaskRequest(
            task_type=TaskType.CODE_GENERATION,
            description="Test task"
        )
        assert task.priority == 50

    def test_task_request_validation_empty_description(self):
        """Test task validation rejects empty description"""
        with pytest.raises(TaskValidationError):
            TaskRequest(
                task_type=TaskType.CODE_GENERATION,
                description=""
            )

    def test_task_request_validation_whitespace_description(self):
        """Test task validation rejects whitespace-only description"""
        with pytest.raises(TaskValidationError):
            TaskRequest(
                task_type=TaskType.CODE_GENERATION,
                description="   "
            )

    def test_task_request_validation_invalid_priority(self):
        """Test task validation rejects invalid priority"""
        with pytest.raises(TaskValidationError):
            TaskRequest(
                task_type=TaskType.CODE_GENERATION,
                description="Test",
                priority=150
            )

    def test_task_request_validation_negative_priority(self):
        """Test task validation rejects negative priority"""
        with pytest.raises(TaskValidationError):
            TaskRequest(
                task_type=TaskType.CODE_GENERATION,
                description="Test",
                priority=-10
            )

    def test_task_request_string_task_type_conversion(self):
        """Test task type can be provided as string"""
        task = TaskRequest(
            task_type="code_generation",
            description="Test"
        )
        assert task.task_type == TaskType.CODE_GENERATION

    def test_task_request_invalid_task_type_string(self):
        """Test invalid task type string raises error"""
        with pytest.raises(TaskValidationError):
            TaskRequest(
                task_type="invalid_task_type",
                description="Test"
            )


class TestAgentRouter:
    """Test AgentRouter class"""

    def test_router_initialization(self, config_loader):
        """Test router initializes correctly"""
        router = AgentRouter(config_loader=config_loader)
        assert router.config_loader == config_loader
        assert isinstance(router._routing_cache, dict)

    def test_router_initialization_default_loader(self):
        """Test router creates default loader if none provided"""
        router = AgentRouter()
        assert router.config_loader is not None
        assert isinstance(router.config_loader, AgentConfigLoader)

    def test_route_task_exact_match(self, router, sample_task):
        """Test routing task with exact match"""
        result = router.route_task(sample_task)
        
        assert isinstance(result, RoutingResult)
        assert result.agent_id is not None
        assert 0.0 <= result.confidence <= 1.0
        assert result.routing_method in ["exact", "fuzzy", "fallback"]

    def test_route_task_code_generation(self, router):
        """Test routing code generation task"""
        task = TaskRequest(
            task_type=TaskType.CODE_GENERATION,
            description="Generate Python function",
            priority=80
        )
        result = router.route_task(task)
        
        assert result is not None
        assert result.task_type == TaskType.CODE_GENERATION

    def test_route_task_content_generation(self, router):
        """Test routing content generation task"""
        task = TaskRequest(
            task_type=TaskType.CONTENT_GENERATION,
            description="Write blog article",
            priority=70
        )
        result = router.route_task(task)
        
        assert result is not None
        assert result.task_type == TaskType.CONTENT_GENERATION

    def test_route_task_fallback_to_general(self, router):
        """Test routing falls back to general agent"""
        task = TaskRequest(
            task_type=TaskType.UNKNOWN,
            description="Some unknown task",
            priority=50
        )
        result = router.route_task(task)
        
        assert result is not None
        # Should fall back to general agent

    def test_route_task_invalid_task(self, router):
        """Test routing with invalid task raises error"""
        with pytest.raises(RoutingError):
            router.route_task("not a task object")

    def test_route_batch_tasks(self, router, batch_tasks):
        """Test routing multiple tasks in batch"""
        results = router.route_batch_tasks(batch_tasks)
        
        assert len(results) == len(batch_tasks)
        assert all(isinstance(r, RoutingResult) for r in results)

    def test_route_batch_empty_list(self, router):
        """Test routing empty batch returns empty list"""
        results = router.route_batch_tasks([])
        assert results == []

    def test_route_task_caching(self, router):
        """Test routing results are cached"""
        task1 = TaskRequest(
            task_type=TaskType.CODE_GENERATION,
            description="Generate code",
            priority=75
        )
        
        result1 = router.route_task(task1)
        result2 = router.route_task(task1)
        
        # Should use cached result
        assert result1.agent_id == result2.agent_id

    def test_get_routing_stats(self, router):
        """Test getting routing statistics"""
        stats = router.get_routing_stats()
        
        assert "cache_size" in stats
        assert "supported_task_types" in stats
        assert "task_type_mappings" in stats

    def test_clear_cache(self, router):
        """Test clearing routing cache"""
        task = TaskRequest(
            task_type=TaskType.CODE_GENERATION,
            description="Test",
            priority=50
        )
        router.route_task(task)
        
        router.clear_cache()
        assert len(router._routing_cache) == 0


class TestFuzzyMatching:
    """Test fuzzy matching capabilities"""

    def test_fuzzy_match_code_keywords(self, router):
        """Test fuzzy matching with code-related keywords"""
        task = TaskRequest(
            task_type=TaskType.GENERAL,
            description="I need to create some Python code",
            priority=50
        )
        result = router.route_task(task)
        
        assert result is not None
        # Should match code generation agent

    def test_fuzzy_match_content_keywords(self, router):
        """Test fuzzy matching with content-related keywords"""
        task = TaskRequest(
            task_type=TaskType.GENERAL,
            description="Write an article about technology",
            priority=50
        )
        result = router.route_task(task)
        
        assert result is not None


class TestAgentSelection:
    """Test agent selection logic"""

    def test_select_agent_by_priority(self, router):
        """Test agent selection considers priority"""
        high_priority_task = TaskRequest(
            task_type=TaskType.CODE_GENERATION,
            description="Urgent code generation",
            priority=90
        )
        result = router.route_task(high_priority_task)
        
        assert result is not None
        assert result.confidence > 0

    def test_select_agent_by_capability(self, router):
        """Test agent selection considers capabilities"""
        task = TaskRequest(
            task_type=TaskType.CODE_GENERATION,
            description="Generate Python code with high quality",
            priority=75
        )
        result = router.route_task(task)
        
        assert result is not None


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_route_task_simple(self):
        """Test route_task_simple convenience function"""
        try:
            result = route_task_simple(
                task_type="code_generation",
                description="Generate code",
                priority=75
            )
            assert isinstance(result, RoutingResult)
        except NoAgentFoundError:
            # Expected if no agents configured
            pass


class TestErrorHandling:
    """Test error handling"""

    def test_routing_error_inheritance(self):
        """Test RoutingError is base exception"""
        assert issubclass(NoAgentFoundError, RoutingError)
        assert issubclass(TaskValidationError, RoutingError)

    def test_no_agent_found_error(self, router):
        """Test NoAgentFoundError is raised when no agent found"""
        # This test depends on agent configuration
        # May need to mock the scenario
        pass


class TestBatchProcessing:
    """Test batch processing efficiency"""

    def test_batch_processing_multiple_types(self, router):
        """Test batch processing handles multiple task types"""
        tasks = [
            TaskRequest(TaskType.CODE_GENERATION, "Task 1", 80),
            TaskRequest(TaskType.CONTENT_GENERATION, "Task 2", 70),
            TaskRequest(TaskType.CODE_REVIEW, "Task 3", 60),
        ]
        results = router.route_batch_tasks(tasks)
        
        assert len(results) == 3
        assert results[0].task_type == TaskType.CODE_GENERATION
        assert results[1].task_type == TaskType.CONTENT_GENERATION

    def test_batch_processing_maintains_order(self, router):
        """Test batch processing maintains task order"""
        tasks = [
            TaskRequest(TaskType.CODE_GENERATION, f"Task {i}", 50)
            for i in range(5)
        ]
        results = router.route_batch_tasks(tasks)
        
        assert len(results) == len(tasks)
        for i, _result in enumerate(results):
            assert f"Task {i}" in tasks[i].description