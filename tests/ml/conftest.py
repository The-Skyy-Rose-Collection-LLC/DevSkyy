"""
Pytest fixtures for ML module tests.

Per Truth Protocol:
- Rule #5: No secrets in code - all API keys mocked
- Rule #8: Test coverage ≥90%
- Rule #13: Security baseline
"""

import asyncio
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock
import uuid

import numpy as np
import pytest

from ml.agent_finetuning_system import (
    AgentCategory,
    AgentFinetuningSystem,
    AgentPerformanceSnapshot,
    FinetuningConfig,
    FinetuningProvider,
)
from ml.agent_deployment_system import (
    AutomatedDeploymentOrchestrator,
    JobDefinition,
    ResourceType,
    ToolRequirement,
)
from ml.model_registry import ModelMetadata, ModelRegistry, ModelStage
from ml.recommendation_engine import (
    RecommendationEngine,
    RecommendationRequest,
    RecommendationType,
)


# ============================================================================
# MOCK MODELS AND UTILITIES
# ============================================================================


class MockModel:
    """Simple mock model for testing"""

    def __init__(self, name="mock_model"):
        self.name = name
        self.trained = False

    def predict(self, X):
        """Mock prediction"""
        return np.sum(X, axis=1) if isinstance(X, np.ndarray) else [0.5]

    def fit(self, X, y):
        """Mock training"""
        self.trained = True
        return self

    def predict_proba(self, X):
        """Mock probability prediction"""
        n_samples = len(X) if hasattr(X, "__len__") else 1
        return np.random.rand(n_samples, 2)


class MockRedisClient:
    """Mock Redis client for testing"""

    def __init__(self):
        self.data = {}

    async def get(self, key: str):
        """Mock get"""
        return self.data.get(key)

    async def set(self, key: str, value: Any, ex: int = None):
        """Mock set"""
        self.data[key] = value
        return True

    async def lpush(self, key: str, value: str):
        """Mock list push"""
        if key not in self.data:
            self.data[key] = []
        self.data[key].insert(0, value)
        return len(self.data[key])

    async def ltrim(self, key: str, start: int, end: int):
        """Mock list trim"""
        if key in self.data:
            self.data[key] = self.data[key][start : end + 1]
        return True

    async def delete(self, *keys):
        """Mock delete"""
        for key in keys:
            if key in self.data:
                del self.data[key]
        return len(keys)


class MockAsyncSession:
    """Mock SQLAlchemy async session"""

    def __init__(self):
        self.data = {}
        self.committed = False
        self.rolled_back = False

    async def execute(self, query, params=None):
        """Mock execute"""
        result = Mock()
        result.fetchone = Mock(return_value=None)
        result.fetchall = Mock(return_value=[])
        result.scalar = Mock(return_value=None)
        return result

    async def commit(self):
        """Mock commit"""
        self.committed = True

    async def rollback(self):
        """Mock rollback"""
        self.rolled_back = True

    async def close(self):
        """Mock close"""
        pass


# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create temporary directory"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_model():
    """Create mock ML model"""
    return MockModel()


@pytest.fixture
def mock_redis():
    """Create mock Redis client"""
    return MockRedisClient()


@pytest.fixture
def mock_session():
    """Create mock async database session"""
    return MockAsyncSession()


# ============================================================================
# MODEL REGISTRY FIXTURES
# ============================================================================


@pytest.fixture
def temp_registry(temp_dir):
    """Create temporary model registry"""
    registry = ModelRegistry(registry_path=str(temp_dir))
    yield registry


@pytest.fixture
def sample_model_metadata():
    """Sample model metadata"""
    return ModelMetadata(
        model_name="test_model",
        version="1.0.0",
        model_type="classifier",
        framework="scikit-learn",
        created_at=datetime.now(),
        metrics={"accuracy": 0.95, "f1": 0.92},
        parameters={"n_estimators": 100, "max_depth": 10},
        dataset_info={"samples": 1000, "features": 20},
        stage=ModelStage.DEVELOPMENT,
    )


# ============================================================================
# FINETUNING FIXTURES
# ============================================================================


@pytest.fixture
def finetuning_system(temp_dir):
    """Create agent finetuning system"""
    return AgentFinetuningSystem(data_dir=temp_dir / "finetuning")


@pytest.fixture
def sample_performance_snapshot():
    """Sample performance snapshot"""
    return AgentPerformanceSnapshot(
        agent_id="agent_123",
        agent_name="test_agent",
        category=AgentCategory.CORE_SECURITY,
        timestamp=datetime.now(),
        task_type="code_scan",
        input_data={"code": "print('hello')"},
        output_data={"issues": [], "score": 100},
        success=True,
        performance_score=0.95,
        execution_time_ms=123.45,
        tokens_used=150,
        user_feedback=0.9,
        metadata={"version": "1.0"},
    )


@pytest.fixture
def sample_finetuning_config():
    """Sample finetuning configuration"""
    return FinetuningConfig(
        category=AgentCategory.CORE_SECURITY,
        provider=FinetuningProvider.OPENAI,
        base_model="gpt-4o-mini",
        n_epochs=3,
        batch_size=32,
        learning_rate=0.0001,
        min_training_samples=100,
        min_validation_accuracy=0.85,
        max_training_cost_usd=100.0,
        max_training_hours=24,
        model_version="1.0.0",
        description="Test fine-tuning",
        tags=["test"],
    )


# ============================================================================
# DEPLOYMENT FIXTURES
# ============================================================================


@pytest.fixture
def deployment_orchestrator():
    """Create deployment orchestrator"""
    return AutomatedDeploymentOrchestrator()


@pytest.fixture
def sample_job_definition():
    """Sample job definition"""
    return JobDefinition(
        job_name="test_job",
        job_description="Test job for unit testing",
        category=AgentCategory.CORE_SECURITY,
        primary_agent="scanner_v2",
        supporting_agents=["fixer_v2"],
        required_tools=[
            ToolRequirement(
                tool_name="code_analyzer",
                tool_type="function",
                required=True,
                min_rate_limit=10,
                estimated_calls=5,
            )
        ],
        max_execution_time_seconds=300,
        max_retries=3,
        priority=5,
        max_budget_usd=1.0,
    )


# ============================================================================
# RECOMMENDATION ENGINE FIXTURES
# ============================================================================


@pytest.fixture
def recommendation_engine(mock_redis):
    """Create recommendation engine"""
    return RecommendationEngine(redis_client=mock_redis)


@pytest.fixture
def sample_recommendation_request():
    """Sample recommendation request"""
    return RecommendationRequest(
        user_id="user_1",
        item_type="product",
        recommendation_type=RecommendationType.HYBRID,
        limit=10,
        exclude_items=[],
        context={},
    )


# ============================================================================
# MOCK API CLIENTS
# ============================================================================


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    client = Mock()

    # Mock files API
    client.files = Mock()
    client.files.create = Mock(return_value=Mock(id="file-123"))

    # Mock fine-tuning API
    client.fine_tuning = Mock()
    client.fine_tuning.jobs = Mock()
    client.fine_tuning.jobs.create = Mock(
        return_value=Mock(
            id="ft-job-123",
            status="running",
            fine_tuned_model=None,
            trained_tokens=None,
        )
    )
    client.fine_tuning.jobs.retrieve = Mock(
        return_value=Mock(
            id="ft-job-123",
            status="succeeded",
            fine_tuned_model="ft-model-123",
            trained_tokens=10000,
        )
    )

    return client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client"""
    client = Mock()

    # Mock messages API
    client.messages = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Optimized prompt here")]
    client.messages.create = Mock(return_value=mock_response)

    return client


# ============================================================================
# DATA GENERATORS
# ============================================================================


def generate_training_data(n_samples: int = 100) -> list[dict[str, Any]]:
    """Generate synthetic training data"""
    data = []
    for i in range(n_samples):
        data.append(
            {
                "input": f"test input {i}",
                "output": f"test output {i}",
                "score": np.random.uniform(0.7, 1.0),
            }
        )
    return data


def generate_performance_snapshots(
    n_samples: int = 50, category: AgentCategory = AgentCategory.CORE_SECURITY
) -> list[AgentPerformanceSnapshot]:
    """Generate synthetic performance snapshots"""
    snapshots = []
    for i in range(n_samples):
        snapshots.append(
            AgentPerformanceSnapshot(
                agent_id=f"agent_{i % 5}",
                agent_name=f"test_agent_{i % 5}",
                category=category,
                timestamp=datetime.now(),
                task_type=["code_scan", "vulnerability_check", "fix_generation"][i % 3],
                input_data={"code": f"test code {i}"},
                output_data={"result": f"test result {i}"},
                success=i % 10 != 0,  # 90% success rate
                performance_score=np.random.uniform(0.7, 1.0),
                execution_time_ms=np.random.uniform(50, 500),
                tokens_used=int(np.random.uniform(100, 1000)),
                user_feedback=np.random.uniform(0.6, 1.0) if i % 5 == 0 else None,
                metadata={"version": "1.0"},
            )
        )
    return snapshots


# ============================================================================
# PARAMETRIZE HELPERS
# ============================================================================


@pytest.fixture(params=[AgentCategory.CORE_SECURITY, AgentCategory.AI_INTELLIGENCE, AgentCategory.ECOMMERCE])
def agent_category(request):
    """Parametrized agent category"""
    return request.param


@pytest.fixture(params=[ModelStage.DEVELOPMENT, ModelStage.STAGING, ModelStage.PRODUCTION])
def model_stage(request):
    """Parametrized model stage"""
    return request.param


@pytest.fixture(
    params=[RecommendationType.COLLABORATIVE, RecommendationType.CONTENT_BASED, RecommendationType.HYBRID]
)
def recommendation_type(request):
    """Parametrized recommendation type"""
    return request.param
