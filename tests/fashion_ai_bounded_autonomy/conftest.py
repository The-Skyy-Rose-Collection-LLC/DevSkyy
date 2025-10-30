"""
Pytest configuration for bounded autonomy tests
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Provide project root path"""
    return project_root


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests"""
    yield
    # Cleanup code here if needed