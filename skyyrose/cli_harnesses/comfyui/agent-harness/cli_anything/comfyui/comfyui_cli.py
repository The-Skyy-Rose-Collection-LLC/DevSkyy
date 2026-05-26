"""cli-anything-comfyui — root Click group and REPL entry point.

Entry points (setup.py):
  comfyui                 → main()
  cli-anything-comfyui   → main()
"""

from __future__ import annotations

import json
import sys
from typing import Any

import click
from cli_anything.comfyui import __version__
from cli_anything.comfyui.commands.doctor_cmds import doctor
from cli_anything.comfyui.commands.history_cmds import history
from cli_anything.comfyui.commands.manifest_cmds import manifest
from cli_anything.comfyui.commands.models_cmds import models
from cli_anything.comfyui.commands.nodes_cmds import nodes
from cli_anything.comfyui.commands.queue_cmds import queue
from cli_anything.comfyui.commands.session_cmds import session
from cli_anything.comfyui.commands.system_cmds import system
from cli_anything.comfyui.commands.workflow_cmds import workflow
from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackendError
from cli_anything.comfyui.utils.repl_skin import ReplSkin

# ---------------------------------------------------------------------------
# CLI state object
# ---------------------------------------------------------------------------


class CliState:
    """Shared state passed via Click context object."""

    def __init__(
        self, json_mode: bool = False, host: str | None = None, token: str | None = None
    ) -> None:
        self.json_mode = json_mode
        self.host = host
        self.token = token
        self.skin = ReplSkin(json_mode=json_mode)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def emit(ctx: click.Context, data: Any) -> None:
    """Emit data honouring json_mode from CliState."""
    state: CliState = ctx.obj
    if state.json_mode:
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(str(data))


def handle_backend_error(exc: ComfyUIBackendError, ctx: click.Context) -> None:
    state: CliState = ctx.obj
    if state.json_mode:
        click.echo(json.dumps({"error": str(exc), "status_code": exc.status_code}))
    else:
        state.skin.error(str(exc))
    sys.exit(1)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"], "max_content_width": 100}


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, "-V", "--version")
@click.option(
    "--json", "json_mode", is_flag=True, envvar="COMFYUI_JSON", help="Output machine-readable JSON"
)
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token for auth")
@click.pass_context
def cli(ctx: click.Context, json_mode: bool, host: str | None, token: str | None) -> None:
    """cli-anything-comfyui — manage ComfyUI from the command line.

    \b
    Command groups:
      system    Server stats and embeddings
      nodes     Node registry browser
      models    Model listing by type
      queue     Submit and manage the execution queue
      history   Inspect completed prompts and outputs
      workflow  Load, validate, and render workflow JSON
      session   Persistent session management
      manifest  Plan/apply batched operations
      doctor    Health checks for deps and connectivity

    \b
    Environment variables:
      COMFYUI_HOST        Base URL (default: http://127.0.0.1:8188)
      COMFYUI_AUTH_TOKEN  Bearer token (optional)
      COMFYUI_JSON        Set to 1 for JSON output mode
    """
    ctx.ensure_object(CliState)
    ctx.obj = CliState(json_mode=json_mode, host=host, token=token)


# ---------------------------------------------------------------------------
# Register subgroups
# ---------------------------------------------------------------------------

cli.add_command(system)
cli.add_command(nodes)
cli.add_command(models)
cli.add_command(queue)
cli.add_command(history)
cli.add_command(workflow)
cli.add_command(session)
cli.add_command(manifest)
cli.add_command(doctor)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------


@cli.command("repl")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.pass_context
def repl_cmd(ctx: click.Context, host: str | None, token: str | None) -> None:
    """Start an interactive REPL (type 'help' or 'exit')."""
    from cli_anything.comfyui.core.secrets import resolve_secrets

    state: CliState = ctx.obj
    skin = state.skin
    skin.print_banner()

    secrets = resolve_secrets(host, token)
    skin.info(f"Connected to: {secrets.base_url}")
    skin.hint("Type a subcommand (e.g. 'system stats') or 'exit' to quit.")

    pt_session = skin.create_prompt_session()

    while True:
        try:
            line = skin.get_input(pt_session)
        except (EOFError, KeyboardInterrupt):
            skin.info("Bye.")
            break

        line = line.strip()
        if not line:
            continue
        if line in ("exit", "quit", "q"):
            skin.info("Bye.")
            break
        if line in ("help", "?"):
            click.echo(ctx.get_help())
            continue

        # Tokenise and invoke via Click's standalone_mode=False
        args = line.split()
        try:
            cli.main(args=args, standalone_mode=False, obj=ctx.obj)
        except SystemExit:
            pass
        except Exception as exc:  # noqa: BLE001
            skin.error(str(exc))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
