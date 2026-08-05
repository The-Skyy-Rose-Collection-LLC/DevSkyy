#!/usr/bin/env python3
"""Generate a deterministic, zero-network marketplace closeout report."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import stat
import subprocess
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any
from zipfile import BadZipFile, ZipFile


def run(command: list[str], cwd: Path) -> tuple[bool, str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    output = (result.stdout + result.stderr).strip()
    return result.returncode == 0, output


def check(condition: bool, severity: str, item: str, evidence: str) -> dict[str, str]:
    return {
        "status": "DONE" if condition else severity,
        "item": item,
        "evidence": evidence,
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_package(
    package: Path,
    repo: Path,
    theme: Path,
    theme_arg: str,
) -> tuple[bool, str]:
    """Verify that a ZIP is safe and byte-identical to tracked theme HEAD."""
    if not package.is_file():
        return False, "package missing"

    tracked_ok, tracked_output = run(
        ["git", "ls-files", "--", theme_arg],
        repo,
    )
    if not tracked_ok:
        return False, f"cannot list tracked theme files: {tracked_output}"

    tracked_paths = [Path(line) for line in tracked_output.splitlines() if line]
    zip_root = theme.name
    expected = {
        f"{zip_root}/{path.relative_to(Path(theme_arg)).as_posix()}": repo / path
        for path in tracked_paths
    }

    try:
        with ZipFile(package) as archive:
            members = [member for member in archive.infolist() if not member.is_dir()]
            unsafe: list[str] = []
            actual: dict[str, Any] = {}
            for member in members:
                path = PurePosixPath(member.filename)
                mode = (member.external_attr >> 16) & 0o170000
                if (
                    member.filename.startswith("/")
                    or "\\" in member.filename
                    or ".." in path.parts
                    or stat.S_ISLNK(mode)
                    or member.flag_bits & 0x1
                ):
                    unsafe.append(member.filename)
                if member.filename in actual:
                    unsafe.append(f"duplicate:{member.filename}")
                actual[member.filename] = member

            if unsafe:
                return False, "unsafe ZIP members=" + ",".join(sorted(unsafe)[:5])

            expected_names = set(expected)
            actual_names = set(actual)
            if expected_names != actual_names:
                missing = sorted(expected_names - actual_names)
                extra = sorted(actual_names - expected_names)
                return False, (
                    f"archive drift: missing={missing[:3]}, extra={extra[:3]}"
                )

            for name, source in expected.items():
                if actual[name].file_size != source.stat().st_size:
                    return False, f"archive size drift={name}"
                source_digest = sha256(source)
                archived_digest = hashlib.sha256(archive.read(actual[name])).hexdigest()
                if not hmac.compare_digest(source_digest, archived_digest):
                    return False, f"archive content drift={name}"
    except (BadZipFile, OSError) as exc:
        return False, f"invalid package: {exc}"

    return True, f"sha256={sha256(package)}, tracked_files={len(expected)}, safe_members=true"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument(
        "--theme",
        default="wordpress-theme/skyyrose-flagship-2",
        help="Theme path relative to repository root",
    )
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    theme = (repo / args.theme).resolve()
    findings: list[dict[str, str]] = []

    required = [
        theme / "functions.php",
        theme / "style.css",
        theme / "inc/product-3d-viewer.php",
        theme / "assets/css/product-3d-viewer.css",
        theme / "assets/css/product-3d-viewer.min.css",
        theme / "assets/js/product-3d-viewer.js",
        theme / "assets/js/product-3d-viewer.min.js",
        theme / "assets/js/lib/model-viewer.min.js",
        theme / "assets/sot/3d/approved-models.json",
        theme / "scripts/package-theme.sh",
    ]
    missing = [str(path.relative_to(repo)) for path in required if not path.is_file()]
    findings.append(
        check(
            not missing,
            "BLOCK",
            "Required release files",
            "all required files present" if not missing else "missing=" + ",".join(missing),
        )
    )

    status_ok, status_output = run(["git", "status", "--porcelain", "--", args.theme], repo)
    clean_theme = status_ok and not status_output
    findings.append(
        check(clean_theme, "BLOCK", "Committed theme source", status_output or "theme worktree clean")
    )

    diff_ok, diff_output = run(["git", "diff", "--check", "--", args.theme], repo)
    findings.append(check(diff_ok, "BLOCK", "Whitespace-safe diff", diff_output or "git diff --check passed"))

    php_files = sorted(theme.rglob("*.php")) if theme.is_dir() else []
    php_failures: list[str] = []
    for path in php_files:
        ok, output = run(["php", "-l", str(path)], repo)
        if not ok:
            php_failures.append(f"{path.relative_to(repo)}: {output}")
    findings.append(
        check(bool(php_files) and not php_failures, "BLOCK", "PHP syntax", "; ".join(php_failures) or f"{len(php_files)} files passed")
    )

    js_paths = [
        theme / "assets/js/product-3d-viewer.js",
        theme / "assets/js/product-3d-viewer.min.js",
        theme / "assets/js/lib/model-viewer.min.js",
    ]
    js_failures: list[str] = []
    for path in js_paths:
        if not path.is_file():
            js_failures.append(f"missing {path.relative_to(repo)}")
            continue
        ok, output = run(["node", "--check", str(path)], repo)
        if not ok:
            js_failures.append(f"{path.relative_to(repo)}: {output}")
    findings.append(check(not js_failures, "BLOCK", "Viewer JavaScript syntax", "; ".join(js_failures) or "3 files passed"))

    style_text = read_text(theme / "style.css")
    functions_text = read_text(theme / "functions.php")
    style_version = re.search(r"^Version:\s*(\S+)", style_text, re.MULTILINE)
    code_version = re.search(r"SKYYROSE2_VERSION',\s*'([^']+)'", functions_text)
    versions_match = bool(style_version and code_version and style_version.group(1) == code_version.group(1))
    version_evidence = f"style={style_version.group(1) if style_version else 'missing'}, code={code_version.group(1) if code_version else 'missing'}"
    findings.append(check(versions_match, "BLOCK", "Theme version sync", version_evidence))

    manifest_path = theme / "assets/sot/3d/approved-models.json"
    try:
        model_manifest = json.loads(read_text(manifest_path))
        models = model_manifest.get("models", {})
        manifest_valid = isinstance(models, dict)
    except json.JSONDecodeError:
        models = {}
        manifest_valid = False
    findings.append(check(manifest_valid, "BLOCK", "Approved-model manifest schema", f"approved_models={len(models)}"))

    resolver_text = read_text(theme / "inc/product-3d-viewer.php")
    local_hash_verified = all(
        token in resolver_text
        for token in ("hash_file(", "hash_equals(", "SKYYROSE2_DIR")
    )
    findings.append(
        check(
            local_hash_verified,
            "BLOCK",
            "Immutable theme-local GLB verification",
            "theme-local path, hash_file, and hash_equals present"
            if local_hash_verified
            else "requires local path plus hash_file and hash_equals before URL generation",
        )
    )

    vendor_text = read_text(theme / "assets/js/lib/model-viewer.min.js")
    external_decoder_hosts = sorted(
        set(re.findall(r"(?:www\.gstatic\.com|cdn\.jsdelivr\.net)", vendor_text))
    )
    findings.append(
        check(
            not external_decoder_hosts,
            "BLOCK",
            "Self-hosted 3D decoder/runtime dependencies",
            "external_hosts=" + ",".join(external_decoder_hosts),
        )
    )

    versioned_rewrite = all(
        token in functions_text
        for token in (
            "skyyrose2_rewrite_schema",
            "get_option(",
            "update_option(",
            "flush_rewrite_rules",
        )
    )
    findings.append(
        check(
            versioned_rewrite,
            "BLOCK",
            "In-place rewrite migration",
            "versioned option migration present"
            if versioned_rewrite
            else "activation-only flush is insufficient for an already-active theme update",
        )
    )
    parent_route = "add_rewrite_rule( '^collections/?$'" in functions_text
    findings.append(
        check(
            parent_route,
            "VERIFY",
            "Collections index availability",
            "virtual parent rewrite present"
            if parent_route
            else "parent route remains a manual WordPress page dependency",
        )
    )

    trust_path = repo / "docs/theme-machine/manifest.json"
    try:
        trust_manifest: dict[str, Any] = json.loads(read_text(trust_path))
    except json.JSONDecodeError:
        trust_manifest = {}
    founder_keys = (
        trust_manifest.get("authority", {})
        .get("approval_verification", {})
        .get("public_keys", [])
    )
    trust_roots = trust_manifest.get("trust_roots", {})
    build_keys = trust_roots.get("build_attestation", {}).get("public_keys", [])
    policy_keys = trust_roots.get("policy_attestation", {}).get("public_keys", [])
    roots_ready = bool(founder_keys and build_keys and policy_keys)
    findings.append(
        check(
            roots_ready,
            "BLOCK",
            "Founder/build/policy public trust roots",
            f"founder={len(founder_keys)}, build={len(build_keys)}, policy={len(policy_keys)}",
        )
    )
    findings.append(
        check(
            False,
            "VERIFY",
            "Signed release evidence",
            "require founder approval, build provenance, and policy snapshot signatures bound to exact commit and ZIP digest",
        )
    )

    package = repo / "dist/skyyrose-flagship-2.zip"
    package_matches, package_evidence = verify_package(
        package,
        repo,
        theme,
        args.theme,
    )
    package_current = clean_theme and package_matches
    findings.append(check(package_current, "BLOCK", "Package built from current committed HEAD", package_evidence))

    findings.append(
        check(
            False,
            "VERIFY",
            "Complete asset redistribution-rights ledger",
            "film authorization exists; all bundled fonts, images, scripts, libraries, and demo/preview assets still need ledger closure",
        )
    )
    findings.append(
        check(
            False,
            "VERIFY",
            "Staging and marketplace QA matrix",
            "install exact ZIP; run WooCommerce funnel, browser, accessibility, responsive, Lighthouse, visual/SOT, Theme Check, WPCS, PHPStan, and clean-site tests",
        )
    )

    priority = {"BLOCK": 0, "VERIFY": 1, "DONE": 2}
    findings.sort(key=lambda item: (priority[item["status"]], item["item"]))
    overall = "BLOCK" if any(item["status"] == "BLOCK" for item in findings) else "VERIFY" if any(item["status"] == "VERIFY" for item in findings) else "DONE"
    report = {
        "schema": "skyyrose.marketplace-closeout.v1",
        "overall": overall,
        "repo": str(repo),
        "theme": args.theme,
        "counts": {status: sum(item["status"] == status for item in findings) for status in ("BLOCK", "VERIFY", "DONE")},
        "findings": findings,
        "plan": [
            "Secure GLB resolution and self-host all required decoder/runtime assets.",
            "Add versioned rewrite migration and guarantee the Collections index route.",
            "Commit the scoped v2.3.3 source, generated assets, provenance, and documentation.",
            "Build twice from clean HEAD; require identical ZIP digests and safe extraction.",
            "Produce policy, build, and founder signatures bound to the exact commit and ZIP.",
            "Install that ZIP on staging and pass the full commerce/browser/accessibility/performance/visual matrix.",
            "Close the asset-rights ledger and marketplace documentation, then request explicit submission approval.",
        ],
    }
    print(json.dumps(report, indent=2))
    return 1 if overall == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
