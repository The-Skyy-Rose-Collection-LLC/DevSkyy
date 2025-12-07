"""
Test fixtures for agent routing system

Provides reusable test fixtures for pytest
"""

import json
from pathlib import Path
import sys

import pytest


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agent.loader import AgentConfigLoader
from agent.router import AgentRouter, TaskRequest, TaskType


@pytest.fixture
def temp_config_dir(tmp_path):
    """
    Create a temporary config directory with sample agent configs

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Path to temporary config directory
    """
    config_dir = tmp_path / "config" / "agents"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create sample agent configurations
    sample_agents = [
        {
            "agent_id": "code_generator_01",
            "agent_name": "Python Code Generator",
            "agent_type": "code_generator",
            "capabilities": [
                {"name": "python_generation", "confidence": 0.95, "keywords": ["python", "code", "generate"]}
            ],
            "priority": 80,
            "max_concurrent_tasks": 10,
            "enabled": True,
        },
        {
            "agent_id": "content_writer_01",
            "agent_name": "Marketing Content Writer",
            "agent_type": "content_writer",
            "capabilities": [
                {"name": "blog_writing", "confidence": 0.90, "keywords": ["blog", "article", "content"]},
                {"name": "copywriting", "confidence": 0.85, "keywords": ["copy", "marketing", "ad"]},
            ],
            "priority": 70,
            "max_concurrent_tasks": 5,
            "enabled": True,
        },
        {
            "agent_id": "general_agent_01",
            "agent_name": "General Purpose Agent",
            "agent_type": "general",
            "capabilities": [],
            "priority": 30,
            "max_concurrent_tasks": 50,
            "enabled": True,
        },
        {
            "agent_id": "disabled_agent",
            "agent_name": "Disabled Agent",
            "agent_type": "test_agent",
            "capabilities": [],
            "priority": 50,
            "max_concurrent_tasks": 10,
            "enabled": False,
        },
    ]

    for agent in sample_agents:
        config_file = config_dir / f"{agent['agent_id']}.json"
        with open(config_file, "w") as f:
            json.dump(agent, f, indent=2)

    return config_dir


@pytest.fixture
def config_loader(temp_config_dir):
    """
    Create AgentConfigLoader with test configs

    Args:
        temp_config_dir: Temporary config directory fixture

    Returns:
        AgentConfigLoader instance
    """
    return AgentConfigLoader(config_dir=temp_config_dir)


@pytest.fixture
def router(config_loader):
    """
    Create AgentRouter with test config loader

    Args:
        config_loader: AgentConfigLoader fixture

    Returns:
        AgentRouter instance
    """
    return AgentRouter(config_loader=config_loader)


@pytest.fixture
def sample_task():
    """
    Create a sample TaskRequest for testing

    Returns:
        TaskRequest instance
    """
    return TaskRequest(
        task_type=TaskType.CODE_GENERATION,
        description="Generate a Python function to calculate fibonacci numbers",
        priority=75,
    )


@pytest.fixture
def batch_tasks():
    """
    Create a batch of sample tasks for testing

    Returns:
        List of TaskRequest instances
    """
    return [
        TaskRequest(task_type=TaskType.CODE_GENERATION, description="Generate Python code", priority=80),
        TaskRequest(task_type=TaskType.CONTENT_GENERATION, description="Write a blog article", priority=70),
        TaskRequest(task_type=TaskType.CODE_REVIEW, description="Review pull request", priority=60),
        TaskRequest(task_type=TaskType.GENERAL, description="Generic task", priority=50),
    ]


@pytest.fixture
def invalid_config_data():
    """
    Create invalid config data for error testing

    Returns:
        Dictionary with invalid config
    """
    return {
        "agent_id": "",  # Invalid: empty
        "agent_name": "Test Agent",
        "agent_type": "test",
        "priority": 150,  # Invalid: > 100
        "max_concurrent_tasks": 0,  # Invalid: < 1
    }


@pytest.fixture
def valid_config_data():
    """
    Create valid config data for testing

    Returns:
        Dictionary with valid config
    """
    return {
        "agent_id": "test_agent_01",
        "agent_name": "Test Agent",
        "agent_type": "test_type",
        "capabilities": [{"name": "test_capability", "confidence": 0.85, "keywords": ["test", "example"]}],
        "priority": 75,
        "max_concurrent_tasks": 10,
        "timeout_seconds": 300,
        "retry_count": 3,
        "enabled": True,
    }
