"""Marvelous Designer subprocess backend for cli-anything-marvelous.

Locates the Marvelous Designer binary on macOS and runs Python scripts
inside MD via the undocumented --script flag.

⚠ HEADLESS CAVEAT: CLO Virtual Fashion's official docs state
"no headless session available" and "command-line/batch options not
currently available" as of MD 12 (https://developer.marvelousdesigner.com/).
The --script flag is asserted by user workflow reports but is NOT
documented in the official scripting API reference.  Build and test
with caution; verify against your installed MD version.

macOS binary glob:
    /Applications/CLO Virtual Fashion/Marvelous Designer*/
        Marvelous Designer.app/Contents/MacOS/Marvelous Designer
"""

from __future__ import annotations

import glob
import os
import subprocess
import tempfile
from pathlib import Path
from string import Template
from typing import Any

# ── Exceptions ────────────────────────────────────────────────────────────


class MarvelousError(Exception):
    """Base exception for all cli-anything-marvelous backend errors."""


class MarvelousNotFoundError(MarvelousError):
    """Marvelous Designer binary not found on this system.

    Install Marvelous Designer from https://www.marvelousdesigner.com/
    and ensure it is in the standard Applications location:
        /Applications/CLO Virtual Fashion/Marvelous Designer*/
    """


class MarvelousScriptError(MarvelousError):
    """A script executed inside Marvelous Designer reported an error."""

    def __init__(self, message: str, returncode: int = 1, stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class MarvelousTimeoutError(MarvelousError):
    """Marvelous Designer did not complete within the allowed timeout."""


# ── Binary discovery ──────────────────────────────────────────────────────

_MD_GLOB = (
    "/Applications/CLO Virtual Fashion/"
    "Marvelous Designer*/"
    "Marvelous Designer.app/Contents/MacOS/Marvelous Designer"
)

_MD_BIN_ENV = "MARVELOUS_DESIGNER_BIN"


def find_marvelous_binary() -> str:
    """Return the path to the Marvelous Designer executable.

    Resolution order:
    1. ``MARVELOUS_DESIGNER_BIN`` environment variable (override).
    2. Glob scan of the standard Applications path.

    Returns:
        Absolute path string to the binary.

    Raises:
        MarvelousNotFoundError: Binary not found by any method.
    """
    env_override = os.environ.get(_MD_BIN_ENV, "").strip()
    if env_override:
        if Path(env_override).is_file():
            return env_override
        raise MarvelousNotFoundError(
            f"MARVELOUS_DESIGNER_BIN='{env_override}' set but file not found."
        )

    matches = sorted(glob.glob(_MD_GLOB))
    if matches:
        # Take newest version (sorted descending puts higher version numbers last
        # for typical "Marvelous Designer 12" naming)
        return matches[-1]

    raise MarvelousNotFoundError(
        "Marvelous Designer binary not found.\n"
        f"Expected location: {_MD_GLOB}\n"
        "Install from https://www.marvelousdesigner.com/ or set "
        f"{_MD_BIN_ENV}=/path/to/binary."
    )


# ── Script runner ─────────────────────────────────────────────────────────


def render_script_template(template_text: str, variables: dict[str, Any]) -> str:
    """Substitute ${var} placeholders in a script template.

    Uses stdlib ``string.Template`` — no Jinja2 dependency.

    Args:
        template_text: Script template with ``${var}`` placeholders.
        variables:     Dict of variable names -> values.

    Returns:
        Rendered script string.

    Raises:
        KeyError: A required placeholder is missing from *variables*.
    """
    return Template(template_text).substitute(variables)


def run_md_script(
    script_text: str,
    binary: str | None = None,
    timeout: int = 300,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Write *script_text* to a temp file and run it inside MD.

    Passes the temp file path via ``--script <path>`` to the MD binary.

    ⚠ See module docstring for --script caveat.

    Args:
        script_text: Python source code to execute inside MD.
        binary:      Path to MD binary (auto-detected if None).
        timeout:     Seconds before raising MarvelousTimeoutError.
        extra_env:   Additional environment variables for the subprocess.

    Returns:
        CompletedProcess with stdout/stderr captured.

    Raises:
        MarvelousNotFoundError: Binary not found.
        MarvelousTimeoutError:  Process exceeded *timeout*.
        MarvelousScriptError:   Process exited non-zero.
    """
    resolved_binary = binary or find_marvelous_binary()

    env = {**os.environ}
    if extra_env:
        env.update(extra_env)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        prefix="cli_anything_md_",
        delete=False,
        encoding="utf-8",
    ) as tmp:
        tmp.write(script_text)
        script_path = tmp.name

    try:
        proc = subprocess.run(
            [resolved_binary, "--script", script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise MarvelousTimeoutError(f"Marvelous Designer timed out after {timeout}s") from exc
    finally:
        try:
            os.unlink(script_path)
        except OSError:
            pass

    if proc.returncode != 0:
        raise MarvelousScriptError(
            f"MD script exited with code {proc.returncode}",
            returncode=proc.returncode,
            stderr=proc.stderr,
        )

    return proc


# ── Script template loader ────────────────────────────────────────────────


def load_script_template(template_name: str) -> str:
    """Load a bundled script template by filename.

    Looks in cli_anything/marvelous/resources/scripts/<template_name>.

    Args:
        template_name: Filename, e.g. ``"export.py.tpl"``.

    Returns:
        Raw template text.

    Raises:
        FileNotFoundError: Template not found in package resources.
    """
    resources_dir = Path(__file__).resolve().parent.parent / "resources" / "scripts"
    path = resources_dir / template_name
    if not path.exists():
        raise FileNotFoundError(f"Script template '{template_name}' not found at {path}")
    return path.read_text(encoding="utf-8")
