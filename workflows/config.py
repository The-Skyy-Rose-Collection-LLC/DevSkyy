"""
Workflow Configuration
=====================

Configuration for code-based workflows.
"""

from typing import Any

# Workflow triggers and schedules
WORKFLOW_TRIGGERS = {
    "ci": {
        "branches": ["main", "develop", "bundle-update"],
        "paths": [
            "api/**",
            "database/**",
            "security/**",
            "orchestration/**",
            "workflows/**",
            "tests/**",
        ],
        "schedule": "0 2 * * *",  # Daily at 2 AM UTC
    },
    "deployment": {
        "branches": ["main"],
        "tags": ["v*"],
        "manual": True,
    },
    "docker": {
        "branches": ["main", "develop"],
        "paths": [
            "docker/**",
            "Dockerfile",
            "main_enterprise.py",
            "api/**",
        ],
    },
    "mcp": {
        "branches": ["main", "develop"],
        "paths": [
            "mcp/**",
            "server.py",
            "devskyy_mcp.py",
        ],
    },
    "ml": {
        "branches": ["main", "develop"],
        "paths": [
            "ml/**",
            "agents/**",
            "orchestration/**",
        ],
    },
    "quality": {
        "branches": ["main", "develop"],
        "paths": ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"],
    },
}

# Environment configurations
ENVIRONMENTS = {
    "staging": {
        "url": "https://staging.devskyy.com",
        "requires_approval": False,
        "auto_deploy": True,
    },
    "production": {
        "url": "https://devskyy.com",
        "requires_approval": True,
        "auto_deploy": False,
    },
    "development": {
        "url": "http://localhost:8000",
        "requires_approval": False,
        "auto_deploy": False,
    },
}

# Python and Node.js versions
VERSIONS = {
    "python": "3.11",
    "node": "20",
    "poetry": "1.7.1",
}

# Workflow dependencies
WORKFLOW_DEPENDENCIES = {
    "ci": [],  # No dependencies
    "quality": [],  # No dependencies
    "mcp": ["ci"],  # Depends on CI
    "ml": ["ci"],  # Depends on CI
    "docker": ["ci", "quality"],  # Depends on CI and quality
    "deployment": ["ci", "quality", "docker"],  # Depends on CI, quality, and docker
}

# Timeout configurations (in seconds)
TIMEOUTS = {
    "ci": 3600,  # 1 hour
    "quality": 1800,  # 30 minutes
    "mcp": 1200,  # 20 minutes
    "ml": 2400,  # 40 minutes
    "docker": 2400,  # 40 minutes
    "deployment": 3600,  # 1 hour
}

# Retry configurations
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 60,  # seconds
    "exponential_backoff": True,
}


def get_workflow_config(workflow_name: str) -> dict[str, Any]:
    """Get configuration for a specific workflow"""
    return {
        "triggers": WORKFLOW_TRIGGERS.get(workflow_name, {}),
        "dependencies": WORKFLOW_DEPENDENCIES.get(workflow_name, []),
        "timeout": TIMEOUTS.get(workflow_name, 3600),
        "retry": RETRY_CONFIG,
        "versions": VERSIONS,
    }
