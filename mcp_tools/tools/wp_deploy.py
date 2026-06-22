"""WordPress theme deploy MCP tools — atomic release ritual exposed as 4 tools.

Replaces the 8-step manual ritual that produced v1.5.10→1.5.16 churn (6 patches
in 24h) and let the canonical version drift across `style.css`, `readme.txt`,
and `functions.php` (functions.php=1.5.16 while the other two stayed at 1.3.0).

Tools:
    wp_bump_version      — atomic semver bump across all 3 version surfaces
    wp_verify_live       — read-only HTTP gate (200 + body>=50KB + no PHP fatals)
    wp_release           — orchestrator: bump → lint → deploy → verify → backfill
    wp_backfill_nextgen  — batched AVIF/WebP backfill wrapper

Reuses (no reimplementation):
    scripts/deploy-theme.sh         — atomic hot-swap, verify_live() gate, 5-step pipeline
    scripts/wp-cli-nextgen-backfill.sh — batched backfill loop with session-timeout recovery

Mutations are gated by `confirm: bool = False`. The orchestrator agent is
expected to surface the plan + cost manifest to the user before passing
`confirm=True`.
"""

from __future__ import annotations

import asyncio
import re
import subprocess
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
from pydantic import Field, field_validator

from mcp_tools.api_client import _format_response
from mcp_tools.security import secure_tool
from mcp_tools.server import logger, mcp
from mcp_tools.types import BaseAgentInput

# Allowlist for verify_live targets — closes SSRF surface on a user-controlled
# URL. The MCP layer cannot trust an arbitrary `public_url` field; an attacker
# could pivot to internal metadata services (169.254.169.254), file:// URLs,
# or RFC1918 addresses. See CLAUDE.md Security learnings.
_VERIFY_LIVE_ALLOWED_HOSTS = frozenset({"skyyrose.co", "www.skyyrose.co", "localhost", "127.0.0.1"})
_VERIFY_LIVE_ALLOWED_SCHEMES = frozenset({"http", "https"})

# Regex patterns used by _redact_secrets() when surfacing subprocess output to
# MCP callers. Subprocess stdout from deploy-theme.sh may contain SFTP creds
# loaded from .env.wordpress on error paths. Never return raw.
_REDACT_PATTERNS = [
    # SFTP / SSH host:user combos
    (re.compile(r"([a-z0-9_.-]+)@(sftp\.wp\.com|wordpress\.com)", re.IGNORECASE), r"[REDACTED]@\2"),
    # password= / Password: lines
    (re.compile(r"(password\s*[:=]\s*)\S+", re.IGNORECASE), r"\1[REDACTED]"),
    # Long hex tokens (32+ hex chars — API keys, hashes)
    (re.compile(r"\b[a-f0-9]{32,}\b", re.IGNORECASE), "[REDACTED-HEX-TOKEN]"),
    # JWT-like tokens
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+\b"),
        "[REDACTED-JWT]",
    ),
    # Bearer auth headers
    (re.compile(r"(Authorization:\s*Bearer\s+)\S+", re.IGNORECASE), r"\1[REDACTED]"),
]


def _redact_secrets(text: str) -> str:
    """Scrub credential-like substrings from subprocess output before returning.

    Best-effort regex-based redaction. Not a substitute for designing the
    deploy script to avoid emitting secrets, but a defense against accidental
    echo (e.g., bash `set -x` traces leaking from error paths).
    """
    if not text:
        return text
    for pattern, replacement in _REDACT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


# ---------------------------------------------------------------------------
# Path resolution — same pattern as phpcs-on-write.sh: derive at runtime so
# the module works on every clone and worktree, not just /Users/theceo/DevSkyy/.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_THEME_DIR = _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship"
_DEPLOY_SCRIPT = _REPO_ROOT / "scripts" / "deploy-theme.sh"
_BACKFILL_SCRIPT = _REPO_ROOT / "scripts" / "wp-cli-nextgen-backfill.sh"

_VERSION_FILES = {
    "style.css": _THEME_DIR / "style.css",
    "readme.txt": _THEME_DIR / "readme.txt",
    "functions.php": _THEME_DIR / "functions.php",
}

# Regex per file. Captures: (1) prefix, (2) old version, (3) suffix.
# Anchored so a stray "Version: 9.9.9" in a comment elsewhere doesn't match.
_VERSION_PATTERNS = {
    "style.css": re.compile(r"^(Version:\s+)(\d+\.\d+\.\d+)(\s*)$", re.MULTILINE),
    "readme.txt": re.compile(r"^(Stable tag:\s+)(\d+\.\d+\.\d+)(\s*)$", re.MULTILINE),
    "functions.php": re.compile(r"(define\(\s*'SKYYROSE_VERSION',\s*')(\d+\.\d+\.\d+)('\s*\)\s*;)"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_current_versions() -> dict[str, str | None]:
    """Read current version from each surface file. None if file missing or no match."""
    out: dict[str, str | None] = {}
    for label, path in _VERSION_FILES.items():
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            out[label] = None
            continue
        m = _VERSION_PATTERNS[label].search(text)
        out[label] = m.group(2) if m else None
    return out


def _bump_semver(version: str, part: Literal["patch", "minor", "major"]) -> str:
    """Return the next semver after bumping `part`. Pure function — no I/O."""
    try:
        major, minor, patch = (int(x) for x in version.split("."))
    except ValueError as exc:
        raise ValueError(f"not a valid semver: {version!r}") from exc
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "major":
        return f"{major + 1}.0.0"
    raise ValueError(f"unknown bump part: {part!r}")


def _write_version(label: str, new_version: str) -> bool:
    """Replace the version in one surface file. Returns True on change, False on no-op."""
    path = _VERSION_FILES[label]
    pattern = _VERSION_PATTERNS[label]
    text = path.read_text(encoding="utf-8")
    new_text, n = pattern.subn(rf"\g<1>{new_version}\g<3>", text)
    if n == 0:
        raise RuntimeError(f"no version pattern matched in {label} — file structure changed?")
    if n > 1:
        raise RuntimeError(f"multiple version matches in {label} — pattern too loose?")
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def _git_dirty() -> bool:
    """True if working tree has uncommitted changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return bool(result.stdout.strip())


async def _run_subprocess(cmd: list[str], cwd: Path, timeout: float = 600.0) -> dict:
    """Run a subprocess in a worker thread (async-safe). Returns dict with rc/stdout/stderr."""

    def _sync_run() -> subprocess.CompletedProcess:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    try:
        result = await asyncio.to_thread(_sync_run)
    except subprocess.TimeoutExpired as exc:
        return {
            "rc": -1,
            "stdout": exc.stdout or "",
            "stderr": f"timed out after {timeout}s",
            "timed_out": True,
        }
    return {
        "rc": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timed_out": False,
    }


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class BumpVersionInput(BaseAgentInput):
    part: Literal["patch", "minor", "major"] = Field(..., description="Semver part to bump.")
    confirm: bool = Field(
        default=False,
        description=(
            "Must be True to write the bump. False returns a preview of what "
            "would change without modifying any file."
        ),
    )


class VerifyLiveInput(BaseAgentInput):
    public_url: str = Field(
        default="https://skyyrose.co/",
        description="URL to GET. Must resolve to skyyrose.co or localhost.",
        max_length=512,
    )
    min_body_kb: int = Field(
        default=50,
        ge=1,
        le=10_000,
        description="Minimum response body size in KB. Reject smaller as 'coming-soon page'.",
    )

    @field_validator("public_url")
    @classmethod
    def _validate_url_allowlist(cls, v: str) -> str:
        """Reject URLs outside the SkyyRose / localhost allowlist (SSRF defense)."""
        try:
            parsed = urlparse(v)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"invalid URL: {exc}") from exc
        if parsed.scheme not in _VERIFY_LIVE_ALLOWED_SCHEMES:
            raise ValueError(
                f"URL scheme {parsed.scheme!r} not allowed; must be one of {sorted(_VERIFY_LIVE_ALLOWED_SCHEMES)}"
            )
        host = (parsed.hostname or "").lower()
        if host not in _VERIFY_LIVE_ALLOWED_HOSTS:
            raise ValueError(f"host {host!r} not in allowlist {sorted(_VERIFY_LIVE_ALLOWED_HOSTS)}")
        return v


class ReleaseInput(BaseAgentInput):
    version_bump: Literal["patch", "minor", "major"] = Field(
        ..., description="Semver part to bump as part of this release."
    )
    with_backfill: bool = Field(
        default=False,
        description="Run AVIF/WebP backfill after deploy. Adds ~5–10 minutes.",
    )
    with_maintenance: bool = Field(
        default=False,
        description=(
            "Pass --with-maintenance to deploy-theme.sh. Legacy mode that triggers "
            "Jetpack Uptime 503 alerts. Only use for DB migrations or plugin changes."
        ),
    )
    dry_run: bool = Field(
        default=True,
        description="True = preview every stage without touching the remote.",
    )
    confirm: bool = Field(
        default=False,
        description="Must be True to execute a non-dry-run release.",
    )


class BackfillNextgenInput(BaseAgentInput):
    limit: int = Field(
        default=25,
        ge=1,
        le=500,
        description="Max attachments to convert per batch.",
    )
    dry_run: bool = Field(
        default=True,
        description="True = preview without touching production.",
    )
    confirm: bool = Field(
        default=False,
        description="Must be True for non-dry-run.",
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool(
    name="wp_bump_version",
    annotations={
        "title": "SkyyRose Theme Version Bump (atomic across 3 files)",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
@secure_tool("wp_bump_version")
async def wp_bump_version(params: BumpVersionInput) -> str:
    """Atomically bump the SkyyRose theme version across all 3 surface files.

    Surfaces updated:
        - wordpress-theme/skyyrose-flagship/style.css         (Version: header)
        - wordpress-theme/skyyrose-flagship/readme.txt        (Stable tag: field)
        - wordpress-theme/skyyrose-flagship/functions.php     (SKYYROSE_VERSION constant)

    The 3 files MUST stay in sync. Drift causes WordPress.org rejections, broken
    cache-busting (?ver=), and ambiguous "what version is live" questions.
    Manual bumps have produced drift (v1.5.16 in functions.php while
    style.css + readme.txt stayed at v1.3.0). This tool prevents that.

    Args:
        params.part: patch, minor, or major
        params.confirm: must be True to write. False returns a dry-run preview.

    Returns:
        Markdown or JSON report showing old + new versions per file.
    """
    current = _read_current_versions()
    missing = [label for label, v in current.items() if v is None]
    if missing:
        raise RuntimeError(f"could not read version from: {', '.join(missing)}")

    # Use the maximum current version as the source-of-truth — if drift exists,
    # we bump the highest forward, never resurrect a lower one. Drift itself
    # is reported in the response.
    versions = [v for v in current.values() if v is not None]
    base = max(versions, key=lambda v: tuple(int(x) for x in v.split(".")))
    new_version = _bump_semver(base, params.part)

    drift_warning = None
    if len(set(versions)) > 1:
        drift_warning = (
            f"VERSION DRIFT detected before bump: {current}. "
            f"Using max ({base}) as base. New {new_version} will heal the drift."
        )

    if not params.confirm:
        logger.info("wp_bump_version dry-run", extra={"current": current, "new": new_version})
        report = {
            "dry_run": True,
            "current_versions": current,
            "base_version": base,
            "new_version": new_version,
            "files_to_write": list(_VERSION_FILES.keys()),
            "drift_warning": drift_warning,
        }
        return _format_response(report, params.response_format, "Version bump preview")

    # Apply the bump. If any file fails mid-way, restore each file to its
    # ORIGINAL (pre-bump) version — NOT to `base` (which would deepen drift
    # by upgrading files that were already at a lower version).
    originals = {label: ver for label, ver in current.items() if ver is not None}
    written: list[str] = []
    try:
        for label in _VERSION_FILES:
            if _write_version(label, new_version):
                written.append(label)
    except Exception as exc:
        # Per-file rollback. Collect failures explicitly so operators see
        # exactly which files are in an indeterminate state.
        rollback_failures: list[str] = []
        for label in written:
            try:
                _write_version(label, originals[label])
            except Exception as rb_exc:
                logger.exception("rollback failed for %s", label)
                rollback_failures.append(f"{label} (target {originals[label]}): {rb_exc}")
        msg = f"bump failed: {exc}. Attempted rollback for {written}."
        if rollback_failures:
            msg += (
                f" ROLLBACK ALSO FAILED for {len(rollback_failures)} file(s) — "
                f"indeterminate state: {'; '.join(rollback_failures)}"
            )
        raise RuntimeError(msg) from exc

    logger.info("wp_bump_version applied", extra={"from": base, "to": new_version})
    report = {
        "dry_run": False,
        "old_version": base,
        "new_version": new_version,
        "files_written": written,
        "drift_warning": drift_warning,
    }
    return _format_response(report, params.response_format, f"Bumped → {new_version}")


async def _verify_live_impl(public_url: str, min_body_kb: int) -> dict[str, Any]:
    """Pure verification logic — returns structured dict so callers can gate.

    Separated from the @mcp.tool() wrapper so wp_release can inspect the `ok`
    field directly instead of fragile string-parsing the formatted output.
    """
    fatal_markers = [
        "Fatal error",
        "Parse error",
        "Call to undefined",
        "There has been a critical error",
    ]

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.get(public_url)
        except httpx.HTTPError as exc:
            return {
                "ok": False,
                "url": public_url,
                "stage": "http_get",
                "error": str(exc),
            }

    body = response.text
    body_kb = len(body.encode("utf-8")) / 1024.0
    found_markers = [m for m in fatal_markers if m in body]

    gates = {
        "status_200": response.status_code == 200,
        "body_ge_min_kb": body_kb >= min_body_kb,
        "no_php_fatals": not found_markers,
    }
    return {
        "ok": all(gates.values()),
        "url": str(response.url),
        "status_code": response.status_code,
        "body_kb": round(body_kb, 1),
        "min_body_kb": min_body_kb,
        "gates": gates,
        "fatal_markers_found": found_markers,
    }


@mcp.tool(
    name="wp_verify_live",
    annotations={
        "title": "SkyyRose live-site verification gate",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wp_verify_live")
async def wp_verify_live(params: VerifyLiveInput) -> str:
    """Verify the live SkyyRose site by HTTP GET + content assertions.

    Same 3 gates as `verify_live()` in scripts/deploy-theme.sh:
        1. HTTP 200
        2. Body size >= min_body_kb (defaults to 50KB; rejects coming-soon page)
        3. No PHP error markers ("Fatal error", "Parse error", "Call to undefined",
           "There has been a critical error")

    Read-only — safe to call any time. Used as both pre-flight (catch dirty
    state before deploying on top) and post-flight (catch regressions).

    Args:
        params.public_url: URL to GET (default https://skyyrose.co/, allowlist-restricted)
        params.min_body_kb: minimum acceptable body size

    Returns:
        Report showing all 3 gates and the final ok/fail verdict.
    """
    report = await _verify_live_impl(params.public_url, params.min_body_kb)
    return _format_response(
        report,
        params.response_format,
        "Verify OK" if report["ok"] else "Verify FAILED",
    )


@mcp.tool(
    name="wp_release",
    annotations={
        "title": "SkyyRose atomic release: bump + lint + deploy + verify + backfill",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
@secure_tool("wp_release")
async def wp_release(params: ReleaseInput) -> str:
    """Run the full SkyyRose release ritual as one atomic flow.

    Stages (each fails the whole flow on rc != 0):
        1. Pre-flight: refuse if git working tree is dirty.
        2. Pre-verify: GET live site, assert healthy before deploying on top.
        3. Bump version (atomic across 3 files via wp_bump_version logic).
        4. Run deploy-theme.sh (atomic hot-swap, microsecond swap window).
        5. Post-verify: GET live site, assert healthy after deploy.
        6. Optional: backfill nextgen images.

    A `confirm=False` or `dry_run=True` invocation returns the plan without
    touching anything. This is the default. To actually deploy:
        wp_release(version_bump="patch", dry_run=False, confirm=True)

    Args:
        params.version_bump: patch | minor | major
        params.with_backfill: run AVIF/WebP backfill after deploy
        params.with_maintenance: legacy --with-maintenance flag (Jetpack 503 risk)
        params.dry_run: default True
        params.confirm: must be True for a real deploy

    Returns:
        Structured report with per-stage outcome.
    """
    stages: dict = {}

    # Stage 1: Pre-flight git check
    dirty = _git_dirty()
    stages["preflight_git"] = {"clean": not dirty}
    if dirty:
        stages["preflight_git"][
            "error"
        ] = "working tree has uncommitted changes — commit or stash first"
        report = {"ok": False, "blocked_at": "preflight_git", "stages": stages}
        return _format_response(report, params.response_format, "Release blocked")

    # Stage 2: Pre-verify (live site healthy before we deploy on top).
    # Call the structured impl directly so we can gate on the `ok` field.
    pre_verify = await _verify_live_impl("https://skyyrose.co/", min_body_kb=50)
    stages["preverify"] = pre_verify
    if not pre_verify["ok"]:
        report = {"ok": False, "blocked_at": "preverify", "stages": stages}
        return _format_response(
            report, params.response_format, "Pre-verify FAILED — refusing to deploy on broken site"
        )

    if not params.confirm or params.dry_run:
        # Plan-only: show what would happen.
        current = _read_current_versions()
        versions = [v for v in current.values() if v]
        base = max(versions, key=lambda v: tuple(int(x) for x in v.split("."))) if versions else "?"
        next_v = _bump_semver(base, params.version_bump) if versions else "?"
        stages["plan"] = {
            "would_bump": f"{base} → {next_v}",
            "would_run_deploy": str(_DEPLOY_SCRIPT),
            "with_maintenance": params.with_maintenance,
            "with_backfill": params.with_backfill,
        }
        report = {"ok": True, "dry_run": True, "stages": stages}
        return _format_response(report, params.response_format, "Release plan (dry-run)")

    # Stage 3: Bump (atomic)
    bump_input = BumpVersionInput(part=params.version_bump, confirm=True)
    await wp_bump_version(bump_input)
    new_versions = _read_current_versions()
    stages["bump"] = new_versions

    # Stage 4: Deploy (calls existing battle-tested script).
    # Refuse if the deploy script is missing — better than a cryptic rc=127.
    if not _DEPLOY_SCRIPT.exists():
        report = {
            "ok": False,
            "blocked_at": "deploy",
            "error": f"deploy script missing: {_DEPLOY_SCRIPT}",
            "stages": stages,
        }
        return _format_response(report, params.response_format, "Deploy script missing")

    deploy_cmd = ["bash", str(_DEPLOY_SCRIPT)]
    if params.with_maintenance:
        deploy_cmd.append("--with-maintenance")
    deploy_result = await _run_subprocess(deploy_cmd, _REPO_ROOT, timeout=900.0)
    # Redact subprocess output before returning to MCP caller — deploy-theme.sh
    # sources .env.wordpress and may echo SFTP credentials on error paths.
    stages["deploy"] = {
        "rc": deploy_result["rc"],
        "timed_out": deploy_result["timed_out"],
        "stdout_tail": _redact_secrets(deploy_result["stdout"][-1500:]),
        "stderr_tail": _redact_secrets(deploy_result["stderr"][-1500:]),
    }
    if deploy_result["rc"] != 0:
        report = {"ok": False, "blocked_at": "deploy", "stages": stages}
        return _format_response(report, params.response_format, "Deploy FAILED")

    # Stage 5: Post-verify — gate on `ok` field, not string-parse.
    post_verify = await _verify_live_impl("https://skyyrose.co/", min_body_kb=50)
    stages["postverify"] = post_verify
    if not post_verify["ok"]:
        # Critical: deploy succeeded but site is broken. Surface loudly so the
        # operator knows to rollback or investigate.
        report = {
            "ok": False,
            "blocked_at": "postverify",
            "stages": stages,
            "alert": "DEPLOY SUCCEEDED BUT LIVE SITE FAILED VERIFY — INVESTIGATE IMMEDIATELY",
        }
        return _format_response(report, params.response_format, "Post-verify FAILED")

    # Stage 6: Optional backfill
    if params.with_backfill:
        backfill_input = BackfillNextgenInput(limit=25, dry_run=False, confirm=True)
        backfill_str = await wp_backfill_nextgen(backfill_input)
        stages["backfill"] = {"result_summary": backfill_str[:500]}

    report = {"ok": True, "dry_run": False, "stages": stages}
    return _format_response(report, params.response_format, "Release complete")


@mcp.tool(
    name="wp_backfill_nextgen",
    annotations={
        "title": "WP nextgen (AVIF/WebP) image backfill — batched, resumable",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
@secure_tool("wp_backfill_nextgen")
async def wp_backfill_nextgen(params: BackfillNextgenInput) -> str:
    """Run the batched AVIF/WebP backfill against the live media library.

    Wraps scripts/wp-cli-nextgen-backfill.sh — the existing batched loop with
    session-timeout recovery (v1.5.12 hardened against the infinite-reprocess
    bug from May 21). Idempotent: re-running on already-converted attachments
    is a no-op.

    Args:
        params.limit: attachments per batch (default 25)
        params.dry_run: True = preview, default
        params.confirm: must be True for non-dry-run

    Returns:
        Stdout tail and exit code from the wrapper script.
    """
    if not _BACKFILL_SCRIPT.exists():
        raise RuntimeError(f"backfill script missing: {_BACKFILL_SCRIPT}")

    cmd: list[str] = ["bash", str(_BACKFILL_SCRIPT), f"--limit={params.limit}"]

    if params.dry_run or not params.confirm:
        # Preview only — return the command we would run.
        report = {
            "dry_run": True,
            "would_execute": " ".join(cmd),
            "script": str(_BACKFILL_SCRIPT),
        }
        return _format_response(report, params.response_format, "Backfill plan")

    result = await _run_subprocess(cmd, _REPO_ROOT, timeout=3600.0)
    report = {
        "ok": result["rc"] == 0,
        "rc": result["rc"],
        "timed_out": result["timed_out"],
        "stdout_tail": _redact_secrets(result["stdout"][-2000:]),
        "stderr_tail": _redact_secrets(result["stderr"][-2000:]),
    }
    return _format_response(report, params.response_format, "Backfill complete")
