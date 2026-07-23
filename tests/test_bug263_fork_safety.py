"""Regression guard for bug-263 layers 5 and 6 (macOS fork-SIGSEGV).

conftest.py pre-spawns the multiprocessing resource tracker at import time,
while the pytest process is still single-threaded and Network.framework is
unarmed. Without that guard the tracker is spawned lazily on the first SemLock
registration (e.g. tqdm's create_mp_lock) — mid-suite, after torch/onnxruntime
imports have armed Network.framework — and its fork child can SIGSEGV in
Apple's nw_settings_child_has_forked atfork handler.

This test fails if the guard is removed (no captured pid) or if the tracker
died and was relaunched mid-suite (pid mismatch — the bug-263 crash signature).

Layer 6 protects long-running production entrypoints (devskyy_mcp.py,
main_enterprise.py, grpc_server/product_service.py) the same way, via a
darwin-only `os.environ.setdefault("no_proxy", "*")` guard placed before any
heavy import. That guard is order-dependent and undetectable by ruff (E402 is
globally ignored), so a refactor could silently move it below a third-party
import and reintroduce the crash without any test noticing — the AST check
below pins the ordering on every platform, not just darwin.
"""

import ast
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

NO_PROXY_GUARDED_ENTRYPOINTS = [
    "devskyy_mcp.py",
    "main_enterprise.py",
    "grpc_server/product_service.py",
]


def _is_darwin_platform_guard(node: ast.stmt) -> bool:
    if not isinstance(node, ast.If):
        return False
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Attribute)
        and test.left.attr == "platform"
    )


def _first_non_stdlib_import_index(body: list[ast.stmt]) -> int | None:
    stdlib = sys.stdlib_module_names
    for index, node in enumerate(body):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [(node.module or "").split(".")[0]]
        else:
            continue
        if any(name not in stdlib for name in names):
            return index
    return None


@pytest.mark.parametrize("relpath", NO_PROXY_GUARDED_ENTRYPOINTS)
def test_no_proxy_guard_precedes_first_third_party_import(relpath):
    """The bug-263 layer-6 darwin guard must run before any import that could
    arm Network.framework — verified by source order, not by executing the
    file (these entrypoints have side effects unsafe to run in a test)."""
    path = REPO_ROOT / relpath
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    guard_index = next(
        (i for i, node in enumerate(tree.body) if _is_darwin_platform_guard(node)), None
    )
    assert guard_index is not None, (
        f"{relpath}: bug-263 layer-6 no_proxy guard (`if sys.platform == 'darwin':`) "
        "not found — was it removed?"
    )

    before_guard_third_party = _first_non_stdlib_import_index(tree.body[:guard_index])
    assert before_guard_third_party is None, (
        f"{relpath}: a non-stdlib import at body index {before_guard_third_party} runs "
        f"BEFORE the no_proxy guard (index {guard_index}) — it could arm Network.framework "
        "before the guard sets no_proxy, defeating the bug-263 fix"
    )


@pytest.mark.skipif(sys.platform != "darwin", reason="darwin-only fork-safety guard")
def test_resource_tracker_prespawned_and_stable():
    from multiprocessing.resource_tracker import _resource_tracker

    import conftest

    startup_pid = getattr(conftest, "_BUG263_TRACKER_PID", None)
    assert startup_pid is not None, (
        "conftest darwin guard did not pre-spawn the multiprocessing resource "
        "tracker (bug-263 layer 5 removed?)"
    )
    assert _resource_tracker._pid == startup_pid, (
        "resource tracker was relaunched mid-suite — its first child died, "
        "which is the bug-263 fork-SIGSEGV signature"
    )
    os.kill(startup_pid, 0)  # raises ProcessLookupError if the tracker is gone
