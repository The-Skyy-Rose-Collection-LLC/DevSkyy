"""Regression guard for bug-263 layer 5 (macOS multiprocessing fork-SIGSEGV).

conftest.py pre-spawns the multiprocessing resource tracker at import time,
while the pytest process is still single-threaded and Network.framework is
unarmed. Without that guard the tracker is spawned lazily on the first SemLock
registration (e.g. tqdm's create_mp_lock) — mid-suite, after torch/onnxruntime
imports have armed Network.framework — and its fork child can SIGSEGV in
Apple's nw_settings_child_has_forked atfork handler.

This test fails if the guard is removed (no captured pid) or if the tracker
died and was relaunched mid-suite (pid mismatch — the bug-263 crash signature).
"""

import os
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="darwin-only fork-safety guard")


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
