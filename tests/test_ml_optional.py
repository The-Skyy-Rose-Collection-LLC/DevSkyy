"""Proves main_enterprise imports without torch-class ML deps (pyproject `ml` extra).

A subprocess is required: the pytest process runs in the shared .venv which HAS
ml installed, so sys.modules already caches transformers/torch/etc — a meta-path
blocker in-process would be defeated by that cache. A fresh interpreter starts
with an empty sys.modules, so the blocker is authoritative there.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

_BLOCKER_SCRIPT = """
import sys
import importlib.abc

BLOCKED = {
    "transformers", "sentence_transformers", "chromadb", "diffusers",
    "torch", "torchvision", "torchaudio",
}


class _MLBlocker(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] in BLOCKED:
            raise ModuleNotFoundError(f"blocked by test: {fullname}")
        return None


sys.meta_path.insert(0, _MLBlocker())
import main_enterprise  # noqa: F401
print("ML_OPTIONAL_IMPORT_OK")
"""


def test_main_enterprise_imports_without_ml_libs() -> None:
    """`import main_enterprise` must succeed with zero torch-class ML libs importable."""
    result = subprocess.run(
        [sys.executable, "-c", _BLOCKER_SCRIPT],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0 and "ML_OPTIONAL_IMPORT_OK" in result.stdout, (
        "import main_enterprise failed without ML libs installed "
        "(transformers/sentence_transformers/chromadb/diffusers/torch/torchvision/torchaudio blocked).\n"
        f"returncode={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
