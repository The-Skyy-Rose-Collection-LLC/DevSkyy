#!/usr/bin/env python3
"""Fail closed unless the pinned next-install theme archive is exact and safe."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path, PurePosixPath


RELEASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = RELEASE_DIR.parents[1]
MANIFEST_PATH = RELEASE_DIR / "next-install.json"


def fail(message: str) -> None:
    raise SystemExit(f"Next-install preflight: FAIL — {message}")


manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
if manifest.get("schema") != "skyyrose.theme-next-install.v1":
    fail("unsupported manifest schema")
if manifest.get("status") != "pinned_for_next_install":
    fail("candidate is not pinned")

theme = manifest.get("theme", {})
source = manifest.get("source", {})
artifact = manifest.get("artifact", {})
policy = manifest.get("install_policy", {})

slug = theme.get("slug")
version = theme.get("version")
source_commit = source.get("commit")
theme_path = source.get("theme_path")
artifact_path = REPO_ROOT / str(artifact.get("path", ""))

if not all(isinstance(value, str) and value for value in (slug, version, source_commit, theme_path)):
    fail("theme or source identity is incomplete")
if policy.get("activate_automatically") is not False:
    fail("automatic activation must remain disabled before execution smoke")
if policy.get("first_gate") != "execution_smoke":
    fail("execution smoke is not the first install gate")
if not artifact_path.is_file():
    fail(f"artifact is missing: {artifact_path}")

digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
if digest != artifact.get("sha256"):
    fail(f"SHA-256 mismatch: expected {artifact.get('sha256')}, got {digest}")
if artifact_path.stat().st_size != artifact.get("bytes"):
    fail("artifact byte count does not match the manifest")

with zipfile.ZipFile(artifact_path) as archive:
    members = archive.namelist()
    if not members:
        fail("artifact is empty")

    for member in members:
        member_path = PurePosixPath(member)
        if member_path.is_absolute() or ".." in member_path.parts:
            fail(f"unsafe archive member: {member}")
        if not member_path.parts or member_path.parts[0] != slug:
            fail(f"archive member escapes the expected theme root: {member}")

    style_name = f"{slug}/style.css"
    functions_name = f"{slug}/functions.php"
    if style_name not in members or functions_name not in members:
        fail("artifact is missing style.css or functions.php")

    style = archive.read(style_name).decode("utf-8")
    functions = archive.read(functions_name).decode("utf-8")

style_version = re.search(r"^Version:\s*(\S+)", style, re.MULTILINE)
runtime_version = re.search(r"define\(\s*'SKYYROSE2_VERSION',\s*'([^']+)'\s*\)", functions)
if not style_version or style_version.group(1) != version:
    fail("style.css version does not match the manifest")
if not runtime_version or runtime_version.group(1) != version:
    fail("runtime asset version does not match the manifest")

commit_check = subprocess.run(
    ["git", "cat-file", "-e", f"{source_commit}^{{commit}}"],
    cwd=REPO_ROOT,
    check=False,
    capture_output=True,
    text=True,
)
if commit_check.returncode:
    fail("source commit is unavailable in this repository")

theme_diff = subprocess.run(
    ["git", "diff", "--quiet", source_commit, "--", theme_path],
    cwd=REPO_ROOT,
    check=False,
)
if theme_diff.returncode:
    fail("theme source has changed since the pinned candidate commit")

print(f"Next-install preflight: PASS — {slug} {version}")
print(f"Artifact: {artifact_path}")
print(f"SHA-256: {digest}")
print("Install only: wp theme install <artifact> --force")
print("Activation remains a separate, explicitly authorized execution-smoke step.")
