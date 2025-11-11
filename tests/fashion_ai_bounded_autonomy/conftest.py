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
    Provide the repository root path to tests.
    
    Returns:
        Path: The Path object pointing to the repository root directory.
    """
    return project_root


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset global singleton instances before and after each test.
    
    Autouse pytest fixture that yields control to the test and then runs teardown so singleton state can be cleared or reinitialized in the post-yield section.
    """
    yield
    # Cleanup code here if needed