"""
cli-anything-hf-spaces — HuggingFace Spaces administration CLI.

Entry point for the ``cli-anything-hf-spaces`` command and the
``python -m cli_anything.hf_spaces`` module invocation.

Token security:
  - Token supplied via --token is held in-memory only (CliState).
  - It is NEVER written to disk, logged, or included in session JSON.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Optional

import click
from cli_anything.hf_spaces.commands.doctor_cmds import doctor
from cli_anything.hf_spaces.commands.hardware_cmds import hardware
from cli_anything.hf_spaces.commands.logs_cmds import logs
from cli_anything.hf_spaces.commands.manifest_cmds import manifest
from cli_anything.hf_spaces.commands.readme_cmds import readme
from cli_anything.hf_spaces.commands.secrets_cmds import secrets
from cli_anything.hf_spaces.commands.session_cmds import session
from cli_anything.hf_spaces.commands.space_cmds import space
from cli_anything.hf_spaces.commands.vars_cmds import vars as vars_group
from cli_anything.hf_spaces.utils.hf_backend import HfBackendError

VERSION = "1.0.0"
CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


# ---------------------------------------------------------------------------
# CliState — shared context object passed via Click's obj mechanism
# ---------------------------------------------------------------------------


class CliState:
    """Shared state threaded through all Click commands via ``pass_obj``."""

    def __init__(self, json_output: bool = False, token: Optional[str] = None) -> None:
        self.json_output = json_output
        # Token is in-memory only — never written to disk or logged.
        self._token: Optional[str] = token

    @property
    def token(self) -> Optional[str]:
        return self._token

    def __repr__(self) -> str:
        return (
            f"CliState(json_output={self.json_output}, token=<{'set' if self._token else 'unset'}>)"
        )


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def emit(state: CliState, payload: Any, *, human: str) -> None:
    """
    Print output in either JSON or human-readable form.

    Args:
        state: Current CliState (controls --json flag).
        payload: JSON-serialisable object for --json mode.
        human: Pre-formatted string for human mode.
    """
    if state.json_output:
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        click.echo(human)


def handle_backend_error(state: CliState, exc: Exception) -> int:
    """
    Print a backend error and return exit code 1.

    Always returns 1 so callers can ``sys.exit(handle_backend_error(...))``.
    """
    msg = str(exc)
    if state.json_output:
        click.echo(json.dumps({"ok": False, "error": msg}, indent=2), err=True)
    else:
        click.echo(f"  ✗ {msg}", err=True)
    return 1


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group(
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
)
@click.version_option(VERSION, "-V", "--version", prog_name="cli-anything-hf-spaces")
@click.option("--json", "json_output", is_flag=True, default=False, help="Output as JSON.")
@click.option(
    "--token",
    default=None,
    envvar="HF_TOKEN",
    help="HuggingFace token (in-memory only, never written to disk).",
    show_envvar=True,
)
@click.pass_context
def cli(ctx: click.Context, json_output: bool, token: Optional[str]) -> None:
    """cli-anything-hf-spaces — HuggingFace Spaces administration.

    Manage Space hardware tiers, secrets, variables, logs, README, and more.

    Auth resolution order:
      1. --token flag (in-memory only)
      2. HF_TOKEN environment variable
      3. ~/.cache/huggingface/token (huggingface-cli login)
      4. Unauthenticated (public spaces only)

    \b
    Quick start:
      hf-spaces space info owner/my-space
      hf-spaces hardware get owner/my-space
      hf-spaces hardware set owner/my-space cpu-upgrade
      hf-spaces vars list owner/my-space
      hf-spaces secrets set owner/my-space MY_KEY
      hf-spaces logs run owner/my-space
      hf-spaces manifest plan ./hf-space-manifest.json
    """
    ctx.ensure_object(dict)
    ctx.obj = CliState(json_output=json_output, token=token)

    if ctx.invoked_subcommand is None:
        # No subcommand: drop into REPL
        _run_repl(ctx.obj)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------


def _run_repl(state: CliState) -> None:
    """Launch the interactive REPL."""
    from cli_anything.hf_spaces.utils.repl_skin import ReplSkin

    skin = ReplSkin("hf_spaces", version=VERSION)
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    _REPL_HELP = {
        "space info <id>": "Show Space info and runtime status",
        "space list [--author X]": "List spaces",
        "space pause <id>": "Pause a Space",
        "space restart <id>": "Restart a Space",
        "space duplicate <from> <to>": "Duplicate a Space",
        "hardware get <id>": "Get current hardware tier",
        "hardware set <id> <tier>": "Request hardware change (STOP-AND-SHOW)",
        "hardware list-tiers": "List all hardware tiers with pricing",
        "vars list <id>": "List environment variables",
        "vars set <id> KEY VALUE": "Set a variable",
        "vars delete <id> KEY": "Delete a variable",
        "secrets set <id> KEY": "Set a secret (value prompted)",
        "secrets delete <id> KEY": "Delete a secret (STOP-AND-SHOW)",
        "secrets list": "List secrets from local manifest",
        "logs run <id>": "Stream runtime logs",
        "logs build <id>": "Stream build logs",
        "readme get <id>": "Fetch README.md",
        "readme set <id> <file>": "Upload a local README.md",
        "manifest init <id>": "Create a new manifest file",
        "manifest plan <file>": "Show planned changes",
        "manifest apply <file>": "Apply manifest (STOP-AND-SHOW)",
        "doctor": "Check auth and SDK health",
        "session list": "List saved sessions",
        "help": "Show this help",
        "quit / exit": "Exit the REPL",
    }

    while True:
        try:
            raw = skin.get_input(pt_session, context="hf-spaces")
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        line = raw.strip()
        if not line:
            continue
        if line in ("quit", "exit", "q"):
            skin.print_goodbye()
            break
        if line in ("help", "?", "h"):
            skin.help(_REPL_HELP)
            continue

        # Dispatch through Click's CLI parser
        args = line.split()
        try:
            # Standalone mode=False so Click doesn't call sys.exit
            cli.main(
                args=args,
                obj=state,
                standalone_mode=False,
            )
        except click.exceptions.UsageError as exc:
            skin.error(str(exc))
        except click.exceptions.Abort:
            skin.warning("Aborted.")
        except HfBackendError as exc:
            skin.error(str(exc))
        except SystemExit:
            pass
        except Exception as exc:
            skin.error(f"Unexpected error: {exc}")


# ---------------------------------------------------------------------------
# Register command groups
# ---------------------------------------------------------------------------

cli.add_command(space)
cli.add_command(hardware)
cli.add_command(secrets)
cli.add_command(vars_group)
cli.add_command(logs)
cli.add_command(readme)
cli.add_command(manifest)
cli.add_command(session)
cli.add_command(doctor)


# ---------------------------------------------------------------------------
# Module entry point
# ---------------------------------------------------------------------------


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
