"""Isolated conftest for oai_render tests.

Overrides the root conftest's autouse _reset_rate_limiter fixture (which imports
from security.rate_limiting and requires the full app to be installed) so that
oai_render unit tests can run without the main application stack.
"""

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """No-op override — oai_render tests don't touch the rate limiter."""
    yield
