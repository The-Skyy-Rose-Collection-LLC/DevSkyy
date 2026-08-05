#!/usr/bin/env python3
"""Rebuild the exact next-install ZIP from its immutable source commit."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


RELEASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = RELEASE_DIR.parents[1]
MANIFEST_PATH = RELEASE_DIR / "next-install.json"


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
theme = manifest["theme"]
source = manifest["source"]
artifact = manifest["artifact"]

slug = theme["slug"]
source_commit = source["commit"]
theme_path = source["theme_path"]
artifact_path = REPO_ROOT / artifact["path"]
temporary_path = artifact_path.with_suffix(artifact_path.suffix + ".tmp")

theme_diff = subprocess.run(
    ["git", "diff", "--quiet", source_commit, "--", theme_path],
    cwd=REPO_ROOT,
    check=False,
)
if theme_diff.returncode:
    raise SystemExit("Next-install rebuild: FAIL — current theme differs from pinned source")

for verifier in (
    "verify-builder-compat.php",
    "verify-commerce-truth.php",
    "verify-product-3d-resolver.php",
    "verify-woocommerce-contracts.php",
):
    result = run(["php", f"{theme_path}/scripts/{verifier}"])
    print(result.stdout.strip())

commit_time = run(["git", "show", "-s", "--format=%cI", source_commit]).stdout.strip()
artifact_path.parent.mkdir(parents=True, exist_ok=True)

try:
    run(
        [
            "git",
            "archive",
            "--format=zip",
            f"--prefix={slug}/",
            f"--mtime={commit_time}",
            f"--output={temporary_path}",
            f"{source_commit}:{theme_path}",
        ]
    )
    digest = hashlib.sha256(temporary_path.read_bytes()).hexdigest()
    size = temporary_path.stat().st_size
    if digest != artifact["sha256"] or size != artifact["bytes"]:
        raise SystemExit(
            "Next-install rebuild: FAIL — rebuilt archive does not match the pinned digest"
        )
    temporary_path.replace(artifact_path)
finally:
    if temporary_path.exists():
        temporary_path.unlink()

print(f"Next-install rebuild: PASS — {artifact_path}")
print(f"SHA-256: {digest}")
