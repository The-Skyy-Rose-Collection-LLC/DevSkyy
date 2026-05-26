"""logs command group — run, build.

NOTE: Log streaming bypasses the public HfApi surface and calls the
HuggingFace SSE endpoint directly via httpx. Requires:
  pip install 'cli-anything-hf-spaces[logs]'
"""

from __future__ import annotations

import sys
from typing import Optional

import click
from cli_anything.hf_spaces.core.space import SpaceRef
from cli_anything.hf_spaces.utils.hf_backend import (HfLogsUnavailableError,
                                                     stream_logs)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("logs", context_settings=CONTEXT_SETTINGS)
def logs() -> None:
    """Log streaming — run (runtime logs), build (build logs).

    Requires httpx: pip install 'cli-anything-hf-spaces[logs]'
    """


def _stream(
    space_id: str,
    log_type: str,
    token: Optional[str],
    lines: int,
    json_output: bool,
) -> None:
    ref = SpaceRef.parse(space_id)
    try:
        for line in stream_logs(
            owner=ref.owner,
            name=ref.name,
            log_type=log_type,
            token=token,
            max_lines=lines,
        ):
            if json_output:
                import json

                click.echo(json.dumps({"type": log_type, "line": line}))
            else:
                click.echo(line)
    except HfLogsUnavailableError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)


@logs.command("run")
@click.argument("space_id")
@click.option(
    "--lines",
    default=200,
    show_default=True,
    help="Maximum log lines to stream.",
)
@click.pass_context
def logs_run(ctx: click.Context, space_id: str, lines: int) -> None:
    """Stream runtime logs for SPACE_ID."""
    state = ctx.obj
    _stream(space_id, "run", state.token, lines, state.json_output)


@logs.command("build")
@click.argument("space_id")
@click.option(
    "--lines",
    default=200,
    show_default=True,
    help="Maximum log lines to stream.",
)
@click.pass_context
def logs_build(ctx: click.Context, space_id: str, lines: int) -> None:
    """Stream build logs for SPACE_ID."""
    state = ctx.obj
    _stream(space_id, "build", state.token, lines, state.json_output)
