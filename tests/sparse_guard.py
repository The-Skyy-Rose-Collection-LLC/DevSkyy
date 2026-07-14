"""Sparse-worktree guards for tests that gate on deliberately excluded trees.

Claude worktrees are sparse checkouts (since 2026-07-12) that exclude ``assets/``,
``archive/``, ``renders/``, and ``screenshots/`` by design. Tests that read those
trees cannot run there — but a FULL checkout (CI, main) with a missing tree must
still fail closed. These helpers therefore skip ONLY when git sparse-checkout is
actually enabled, never on a bare missing path.
"""

from __future__ import annotations

import functools
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@functools.lru_cache(maxsize=1)
def sparse_checkout_enabled() -> bool:
    """True when this checkout has git sparse-checkout enabled."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "config", "--get", "core.sparseCheckout"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == "true"


def tree_missing_by_sparse_checkout(rel: str) -> bool:
    """True only when ``rel`` is absent AND the checkout is sparse.

    A full checkout missing the tree returns False so the calling gate still
    fails closed (bug-230: gates must never pass because their input is absent).
    """
    if (REPO_ROOT / rel).exists():
        return False
    return sparse_checkout_enabled()


def requires_tree(rel: str) -> pytest.MarkDecorator:
    """Skipif marker: skip when ``rel`` is sparse-excluded, run everywhere else."""
    return pytest.mark.skipif(
        tree_missing_by_sparse_checkout(rel),
        reason=f"sparse worktree deliberately excludes {rel}; "
        "this gate runs in full checkouts and CI",
    )
