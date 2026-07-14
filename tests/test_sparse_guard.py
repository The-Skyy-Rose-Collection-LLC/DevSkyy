"""The sparse-worktree guard must FAIL CLOSED.

These tests pin the exact property that keeps the guard trustworthy: it may
suppress a tree-dependent test ONLY when the tree is deliberately sparse-excluded
(absent AND git sparse-checkout enabled). A full checkout or CI — where a missing
tree is a real breakage — must still run the test (bug-230: absent input blocks,
never passes).
"""

from __future__ import annotations

from tests import sparse_guard


def test_present_tree_always_runs():
    """An existing tree is never suppressed, regardless of sparse state."""
    # `security` exists in every checkout (sparse excludes only assets/archive/...).
    assert sparse_guard.tree_missing_by_sparse_checkout("security") is False


def test_absent_tree_skips_only_in_sparse_checkout(monkeypatch):
    monkeypatch.setattr(sparse_guard, "sparse_checkout_enabled", lambda: True)
    assert sparse_guard.tree_missing_by_sparse_checkout("no_such_tree_xyz") is True


def test_absent_tree_fails_closed_in_full_checkout(monkeypatch):
    """The critical assertion: absent tree + NON-sparse checkout => test still runs."""
    monkeypatch.setattr(sparse_guard, "sparse_checkout_enabled", lambda: False)
    assert sparse_guard.tree_missing_by_sparse_checkout("no_such_tree_xyz") is False
