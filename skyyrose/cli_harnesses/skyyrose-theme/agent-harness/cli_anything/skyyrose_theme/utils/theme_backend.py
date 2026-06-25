"""
Theme backend — typed wrappers for external tools:
  - PHPCS / PHPCBF (local vendor/bin)
  - wp-cli over SSH
  - PHP syntax lint (php -l)

All subprocess calls use args-as-lists, capture_output=True, never shell=True.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Defaults (all overridable via env)
# ---------------------------------------------------------------------------

_DEFAULT_THEME_ROOT = Path(
    os.environ.get(
        "SKYYROSE_THEME_ROOT",
        str(Path.home() / "DevSkyy/wordpress-theme/skyyrose-flagship"),
    )
)
_SSH_HOST = os.environ.get("SKYYROSE_SSH_HOST", "skyyrose.wordpress.com@ssh.wp.com")
_WP_ROOT = os.environ.get("SKYYROSE_WP_ROOT", "/srv/htdocs")
_WP_CLI = os.environ.get("SKYYROSE_WP_CLI", "/usr/local/bin/wp")


def _theme_root() -> Path:
    return Path(os.environ.get("SKYYROSE_THEME_ROOT", str(_DEFAULT_THEME_ROOT)))


# ---------------------------------------------------------------------------
# Typed exceptions
# ---------------------------------------------------------------------------


class BackendError(RuntimeError):
    """Base class for backend errors."""


class PHPCSNotFoundError(BackendError):
    """Raised when vendor/bin/phpcs is not found."""


class PHPNotFoundError(BackendError):
    """Raised when the php binary is not on PATH."""


class SSHNotReachableError(BackendError):
    """Raised when SSH connection to the WP host fails."""


class WPCliError(BackendError):
    """Raised when a wp-cli command exits non-zero."""


# ---------------------------------------------------------------------------
# Context / doctor
# ---------------------------------------------------------------------------


@dataclass
class ThemeContext:
    theme_root: Path
    phpcs_path: Path | None
    php_binary: str | None
    ssh_host: str
    wp_root: str
    wp_cli: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme_root": str(self.theme_root),
            "phpcs_available": self.phpcs_path is not None,
            "phpcs_path": str(self.phpcs_path) if self.phpcs_path else None,
            "php_binary": self.php_binary,
            "ssh_host": self.ssh_host,
            "wp_root": self.wp_root,
            "wp_cli": self.wp_cli,
        }


def build_context(
    theme_root: Path | None = None,
    ssh_host: str | None = None,
    wp_root: str | None = None,
    wp_cli: str | None = None,
) -> ThemeContext:
    """Build a ThemeContext from the environment and filesystem."""
    import shutil

    root = theme_root or _theme_root()
    phpcs_candidate = root / "vendor" / "bin" / "phpcs"
    phpcs = phpcs_candidate if phpcs_candidate.exists() else None
    php = shutil.which("php")

    return ThemeContext(
        theme_root=root,
        phpcs_path=phpcs,
        php_binary=php,
        ssh_host=ssh_host or _SSH_HOST,
        wp_root=wp_root or _WP_ROOT,
        wp_cli=wp_cli or _WP_CLI,
    )


@dataclass
class DoctorReport:
    checks: list[dict[str, Any]] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(c.get("status") == "ok" for c in self.checks)

    def add(self, name: str, status: str, detail: str = "") -> None:
        self.checks.append({"name": name, "status": status, "detail": detail})


def doctor(theme_root: Path | None = None) -> DoctorReport:
    """
    Run all health checks and return a DoctorReport.

    Checks:
      - Theme root exists
      - style.css present (theme marker)
      - PHPCS vendor binary present
      - PHP binary on PATH
      - deploy-theme.sh exists
    """
    import shutil

    root = theme_root or _theme_root()
    report = DoctorReport()

    # 1. Theme root
    if root.exists():
        report.add("theme_root", "ok", str(root))
    else:
        report.add("theme_root", "fail", f"Not found: {root}")

    # 2. style.css
    style_css = root / "style.css"
    if style_css.exists():
        report.add("style_css", "ok", str(style_css))
    else:
        report.add("style_css", "fail", f"Not found: {style_css}")

    # 3. functions.php
    functions_php = root / "functions.php"
    if functions_php.exists():
        report.add("functions_php", "ok", str(functions_php))
    else:
        report.add("functions_php", "fail", f"Not found: {functions_php}")

    # 4. PHPCS
    phpcs = root / "vendor" / "bin" / "phpcs"
    if phpcs.exists():
        report.add("phpcs", "ok", str(phpcs))
    else:
        report.add(
            "phpcs",
            "warn",
            f"Not found: {phpcs}. Run: cd {root} && composer install",
        )

    # 5. PHP binary
    php = shutil.which("php")
    if php:
        report.add("php_binary", "ok", php)
    else:
        report.add("php_binary", "fail", "php not found on PATH")

    # 6. deploy-theme.sh
    deploy_script = Path(
        os.environ.get(
            "SKYYROSE_DEPLOY_SCRIPT",
            str(Path.home() / "DevSkyy/scripts/deploy-theme.sh"),
        )
    )
    if deploy_script.exists():
        report.add("deploy_script", "ok", str(deploy_script))
    else:
        report.add("deploy_script", "fail", f"Not found: {deploy_script}")

    return report


# ---------------------------------------------------------------------------
# PHPCS / PHPCBF
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LintResult:
    returncode: int
    stdout: str
    stderr: str
    fixed: bool = False  # True when running phpcbf

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_phpcs(
    theme_root: Path | None = None,
    fix: bool = False,
) -> LintResult:
    """
    Run PHPCS (or PHPCBF if fix=True) against the theme.

    Raises:
        PHPCSNotFoundError: if vendor/bin/phpcs not found.
    """
    root = theme_root or _theme_root()
    binary_name = "phpcbf" if fix else "phpcs"
    binary = root / "vendor" / "bin" / binary_name

    if not binary.exists():
        raise PHPCSNotFoundError(
            f"{binary_name} not found at {binary}. Run: cd {root} && composer install"
        )

    config = root / ".phpcs.xml"
    cmd: list[str] = [str(binary)]
    if config.exists():
        cmd += [f"--standard={config}"]
    cmd += ["-s", "."]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    return LintResult(
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        fixed=fix,
    )


def run_php_lint(
    theme_root: Path | None = None,
) -> LintResult:
    """
    Run `php -l` on every .php file in the theme root.

    Raises:
        PHPNotFoundError: if php not on PATH.
    """
    import shutil

    php = shutil.which("php")
    if not php:
        raise PHPNotFoundError("php not found on PATH")

    root = theme_root or _theme_root()
    php_files = sorted(root.rglob("*.php"))

    errors: list[str] = []
    for php_file in php_files:
        r = subprocess.run(
            [php, "-l", str(php_file)],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            errors.append(f"{php_file.relative_to(root)}: {r.stdout.strip()}")

    stdout = "\n".join(errors) if errors else "No syntax errors detected."
    return LintResult(
        returncode=1 if errors else 0,
        stdout=stdout,
        stderr="",
    )


# ---------------------------------------------------------------------------
# wp-cli over SSH
# ---------------------------------------------------------------------------


def run_wp_ssh(
    *wp_args: str,
    ssh_host: str | None = None,
    wp_root: str | None = None,
    wp_cli: str | None = None,
) -> subprocess.CompletedProcess:
    """
    Run a wp-cli command on the production server via SSH.

    Example:
        run_wp_ssh("cache", "flush")
        run_wp_ssh("theme", "status")

    Raises:
        SSHNotReachableError: if SSH exits with connection error.
        WPCliError: if wp-cli exits non-zero.
    """
    host = ssh_host or _SSH_HOST
    root = wp_root or _WP_ROOT
    cli = wp_cli or _WP_CLI

    remote_cmd_parts = [cli] + list(wp_args) + [f"--path={root}", "--allow-root"]
    remote_cmd = " ".join(remote_cmd_parts)

    cmd = ["ssh", host, remote_cmd]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    # Distinguish SSH connection failures from wp-cli failures
    if result.returncode == 255 or "Connection refused" in result.stderr:
        raise SSHNotReachableError(f"SSH connection to {host} failed: {result.stderr.strip()}")

    if result.returncode != 0:
        raise WPCliError(
            f"wp {' '.join(wp_args)} failed (exit {result.returncode}): {result.stderr.strip()}"
        )

    return result
