"""Isolated conftest for character_pipeline tests.

Overrides the root conftest's autouse `_reset_rate_limiter` fixture (which
imports `security.rate_limiting` and requires the full app stack) so these
pure-numpy/glTF unit tests run without pulling in unrelated dependencies.
"""

import pytest


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """No-op override — character_pipeline tests don't touch the rate limiter."""
    yield
