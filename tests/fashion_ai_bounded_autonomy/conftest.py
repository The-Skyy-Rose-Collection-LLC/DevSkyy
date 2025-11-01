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
    """
    Expose the repository root path for tests.
    
    Returns:
        project_root (Path): Path object pointing to the repository root directory.
    """
    return project_root


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Provide a per-test reset of global singleton instances.
    
    This autouse pytest fixture yields control to the test and performs teardown after the test completes to reset or clean up any singleton state. Add cleanup logic in the post-yield section to clear or reinitialize singletons as needed.
    """
    yield
    # Cleanup code here if needed