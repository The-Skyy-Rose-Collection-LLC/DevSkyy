"""Unit test for mcp_tools.http_mount.tool_count.

Does not hard-assert an exact count (brittle against future tool additions) —
only that it's a positive int computed from the live FastMCP registry.
"""

import asyncio

from mcp_tools.http_mount import tool_count


def test_tool_count_is_positive_int():
    n = asyncio.run(tool_count())
    assert isinstance(n, int)
    assert n > 0
