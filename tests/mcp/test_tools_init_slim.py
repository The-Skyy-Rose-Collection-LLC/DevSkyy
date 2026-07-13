"""Unit tests for the slim-image module-exclusion split in mcp_tools.tools.

Pure logic only — importing mcp_tools.tools triggers the real tool-module
registration loop as an import side effect, so these tests exercise the
extracted `_resolve_modules` function directly rather than re-importing the
package under different env-var states.
"""

from mcp_tools.tools import SLIM_EXCLUDED_MODULES, _resolve_modules


def test_full_image_imports_everything():
    to_import, skipped = _resolve_modules(("a", "b", "oai_render"), slim=False)
    assert to_import == ["a", "b", "oai_render"]
    assert skipped == []


def test_slim_image_excludes_declared_modules_only():
    to_import, skipped = _resolve_modules(("a", "oai_render", "lora_generation", "b"), slim=True)
    assert to_import == ["a", "b"]
    assert set(skipped) == SLIM_EXCLUDED_MODULES


def test_slim_excluded_set_is_exactly_two():
    assert frozenset({"oai_render", "lora_generation"}) == SLIM_EXCLUDED_MODULES
