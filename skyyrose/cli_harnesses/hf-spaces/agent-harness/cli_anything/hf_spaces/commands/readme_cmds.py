"""readme command group — get, set, sync."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from cli_anything.hf_spaces.core.space import SpaceRef
from cli_anything.hf_spaces.utils.hf_backend import (HfBackendError,
                                                     get_readme, upload_readme)

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("readme", context_settings=CONTEXT_SETTINGS)
def readme() -> None:
    """README.md management — get, set, sync."""


@readme.command("get")
@click.argument("space_id")
@click.option(
    "--out", default=None, type=click.Path(dir_okay=False), help="Write to file instead of stdout."
)
@click.pass_context
def readme_get(ctx: click.Context, space_id: str, out: Optional[str]) -> None:
    """Fetch README.md from SPACE_ID."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)

    content = get_readme(ref.repo_id, token=state.token)
    if content is None:
        click.echo(f"  ✗ README.md not found on {ref.repo_id}.", err=True)
        sys.exit(1)

    if out:
        Path(out).write_text(content, encoding="utf-8")
        if state.json_output:
            click.echo(
                json.dumps({"ok": True, "repo_id": ref.repo_id, "written_to": out}, indent=2)
            )
        else:
            click.echo(f"  ✓ README.md written to {out}")
    else:
        if state.json_output:
            click.echo(
                json.dumps({"ok": True, "repo_id": ref.repo_id, "content": content}, indent=2)
            )
        else:
            click.echo(content)


@readme.command("set")
@click.argument("space_id")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--message", default="Update README.md via cli-anything-hf-spaces", help="Commit message."
)
@click.pass_context
def readme_set(ctx: click.Context, space_id: str, file: str, message: str) -> None:
    """Upload local FILE as README.md to SPACE_ID."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)
    content = Path(file).read_text(encoding="utf-8")

    try:
        upload_readme(ref.repo_id, content=content, token=state.token, commit_message=message)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(json.dumps({"ok": True, "repo_id": ref.repo_id, "source": file}, indent=2))
    else:
        click.echo(f"  ✓ README.md uploaded to {ref.repo_id} from {file}")


@readme.command("sync")
@click.argument("space_id")
@click.argument("file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--message", default="Sync README.md via cli-anything-hf-spaces", help="Commit message."
)
@click.option("--force", is_flag=True, default=False, help="Upload even if content matches remote.")
@click.pass_context
def readme_sync(ctx: click.Context, space_id: str, file: str, message: str, force: bool) -> None:
    """Sync local FILE to README.md on SPACE_ID (no-op if identical)."""
    state = ctx.obj
    ref = SpaceRef.parse(space_id)
    local_content = Path(file).read_text(encoding="utf-8")

    if not force:
        remote_content = get_readme(ref.repo_id, token=state.token)
        if remote_content is not None and remote_content == local_content:
            if state.json_output:
                click.echo(
                    json.dumps(
                        {
                            "ok": True,
                            "repo_id": ref.repo_id,
                            "synced": False,
                            "reason": "identical",
                        },
                        indent=2,
                    )
                )
            else:
                click.echo(f"  ✓ README.md already up-to-date on {ref.repo_id} (no upload needed)")
            return

    try:
        upload_readme(ref.repo_id, content=local_content, token=state.token, commit_message=message)
    except HfBackendError as exc:
        click.echo(f"  ✗ {exc}", err=True)
        sys.exit(1)

    if state.json_output:
        click.echo(
            json.dumps(
                {"ok": True, "repo_id": ref.repo_id, "synced": True, "source": file}, indent=2
            )
        )
    else:
        click.echo(f"  ✓ README.md synced to {ref.repo_id} from {file}")
