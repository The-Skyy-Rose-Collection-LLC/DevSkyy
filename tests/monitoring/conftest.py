"""
Minimal pytest configuration for monitoring tests
Prevents loading of main conftest that has import issues
"""

import pytest


# Minimal fixtures for monitoring tests
@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
