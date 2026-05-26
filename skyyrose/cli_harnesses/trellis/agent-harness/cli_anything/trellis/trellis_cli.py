"""cli-anything-trellis — Click CLI for Microsoft TRELLIS.2 image-to-3D.

Entry point: `trellis` (or `python -m cli_anything.trellis.trellis_cli`)

Command groups:
    generate    Submit image-to-3D generation jobs
    jobs        List and inspect generation jobs
    catalog     Browse the generation history catalog
    session     Manage REPL session state
    config      Show/set environment configuration
    repl        Drop into interactive REPL (default when called with no args)
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from cli_anything.trellis import __version__
from cli_anything.trellis.core.catalog import (append_record, catalog_stats,
                                               find_record, list_records)
from cli_anything.trellis.core.generation import (DEFAULT_RESOLUTION,
                                                  RESOLUTION_PRESETS,
                                                  GenerationRecord)
from cli_anything.trellis.core.session import Session
from cli_anything.trellis.utils.repl_skin import ReplSkin
from cli_anything.trellis.utils.trellis_backend import (
    BackendError, GPUUnavailableError, RunnerError, RunnerTimeoutError,
    TrellisNotFoundError, TrellisPythonError, discover_trellis_home,
    discover_trellis_python, probe_gpu, run_generation, validate_python,
    validate_trellis_home)

# ── CLI state object ──────────────────────────────────────────────────────────


@dataclass
class CliState:
    """Shared state injected via Click context (ctx.obj)."""

    json_output: bool = False
    session_name: str = "default"
    trellis_home_override: Optional[str] = None
    trellis_python_override: Optional[str] = None

    _session: Optional[Session] = None
    _skin: Optional[ReplSkin] = None

    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = Session.load(self.session_name)
        return self._session

    @session.setter
    def session(self, value: Session) -> None:
        self._session = value

    def save_session(self) -> None:
        if self._session is not None:
            self._session.save()

    @property
    def skin(self) -> ReplSkin:
        if self._skin is None:
            self._skin = ReplSkin("trellis", version=__version__)
        return self._skin

    def resolved_trellis_home(self) -> Optional[Path]:
        return discover_trellis_home(
            explicit=self.trellis_home_override,
            session_value=self.session.trellis_home,
        )

    def resolved_python(self) -> str:
        return discover_trellis_python(
            explicit=self.trellis_python_override,
            session_value=self.session.trellis_python,
        )


# ── Helpers ───────────────────────────────────────────────────────────────────


def emit(state: CliState, data: Any) -> None:
    """Emit data as JSON (--json mode) or human-readable."""
    if state.json_output:
        click.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if isinstance(data, str):
            click.echo(data)
        elif isinstance(data, dict):
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
        elif isinstance(data, list):
            for item in data:
                click.echo(f"  {item}")
        else:
            click.echo(str(data))


def handle_backend_error(state: CliState, exc: Exception) -> None:
    """Print a user-friendly error and exit 1."""
    msg = str(exc)
    if state.json_output:
        click.echo(json.dumps({"error": msg, "type": type(exc).__name__}), err=True)
    else:
        state.skin.error(msg)
    sys.exit(1)


def _record_to_row(r: GenerationRecord) -> List[str]:
    """Convert a GenerationRecord to a table row."""
    duration = ""
    if r.duration_seconds is not None:
        duration = f"{r.duration_seconds:.1f}s"
    return [
        r.job_id[:12],
        r.status,
        r.resolution,
        Path(r.image_path).name if r.image_path else "",
        duration,
        Path(r.glb_path).name if r.glb_path else (r.error or "")[:40],
    ]


# ── Root group ────────────────────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
@click.option(
    "--session",
    "session_name",
    default="default",
    show_default=True,
    help="Session name to load.",
)
@click.option("--trellis-home", "trellis_home", default=None, help="TRELLIS.2 install dir.")
@click.option("--trellis-python", "trellis_python", default=None, help="Python with trellis2.")
@click.version_option(__version__, prog_name="trellis")
@click.pass_context
def cli(
    ctx: click.Context,
    json_output: bool,
    session_name: str,
    trellis_home: Optional[str],
    trellis_python: Optional[str],
) -> None:
    """cli-anything-trellis: Microsoft TRELLIS.2 image-to-3D CLI harness."""
    ctx.ensure_object(dict)
    state = CliState(
        json_output=json_output,
        session_name=session_name,
        trellis_home_override=trellis_home,
        trellis_python_override=trellis_python,
    )
    ctx.obj = state

    if ctx.invoked_subcommand is None:
        # Default to REPL
        ctx.invoke(repl)


# ── generate group ────────────────────────────────────────────────────────────


@cli.group()
@click.pass_context
def generate(ctx: click.Context) -> None:
    """Submit image-to-3D generation jobs."""


@generate.command("run")
@click.argument("image", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output-dir",
    "-o",
    default=None,
    help="Output directory for GLB files. Defaults to session default or ./trellis-output/.",
)
@click.option(
    "--resolution",
    "-r",
    type=click.Choice(list(RESOLUTION_PRESETS.keys())),
    default=None,
    help="Quality preset (low/high). Defaults to session default.",
)
@click.option("--seed", default=-1, show_default=True, help="Random seed (-1 = random).")
@click.option(
    "--decimation-target",
    default=1_000_000,
    show_default=True,
    help="Target polygon count for GLB decimation.",
)
@click.option(
    "--texture-size",
    default=4096,
    show_default=True,
    help="Texture atlas size in pixels.",
)
@click.option(
    "--timeout",
    default=None,
    type=int,
    help="Runner timeout in seconds (default: no limit).",
)
@click.pass_obj
def generate_run(
    state: CliState,
    image: str,
    output_dir: Optional[str],
    resolution: Optional[str],
    seed: int,
    decimation_target: int,
    texture_size: int,
    timeout: Optional[int],
) -> None:
    """Generate a 3D GLB from IMAGE (path to an image file)."""
    resolved_output = output_dir or state.session.default_output_dir or "./trellis-output"
    resolved_resolution = resolution or state.session.default_resolution or DEFAULT_RESOLUTION

    try:
        record = GenerationRecord.new(
            image_path=image,
            output_dir=resolved_output,
            resolution=resolved_resolution,
            seed=seed,
            decimation_target=decimation_target,
            texture_size=texture_size,
        )
    except ValueError as exc:
        handle_backend_error(state, exc)
        return

    python_path = state.resolved_python()
    trellis_home = state.resolved_trellis_home()

    if not state.json_output:
        state.skin.info(f"Starting job {record.job_id} ...")
        state.skin.status("image", record.image_path)
        state.skin.status("resolution", record.resolution)
        state.skin.status("seed", str(record.seed) if record.seed >= 0 else "random")
        state.skin.status("output", record.output_dir)

    try:
        result = run_generation(
            record=record,
            python_path=python_path,
            trellis_home=trellis_home,
            timeout=timeout,
        )
    except (RunnerError, RunnerTimeoutError, BackendError) as exc:
        # Still append failed record to catalog for visibility
        failed = record.mark_failed(str(exc))
        append_record(failed)
        handle_backend_error(state, exc)
        return

    # Persist to catalog and session history
    append_record(result)
    state.session = state.session.push_history(result.job_id)
    state.save_session()

    if state.json_output:
        emit(state, result.to_dict())
    else:
        if result.status == "done":
            state.skin.success(f"GLB saved: {result.glb_path}")
            if result.duration_seconds:
                state.skin.status("duration", f"{result.duration_seconds:.1f}s")
        else:
            state.skin.error(f"Job failed: {result.error}")
            sys.exit(1)


# ── jobs group ────────────────────────────────────────────────────────────────


@cli.group()
@click.pass_context
def jobs(ctx: click.Context) -> None:
    """List and inspect generation jobs from session history."""


@jobs.command("list")
@click.option("--limit", "-n", default=20, show_default=True, help="Max jobs to show.")
@click.pass_obj
def jobs_list(state: CliState, limit: int) -> None:
    """List recent jobs from the session history."""
    history = state.session.history[-limit:]
    if not history:
        if state.json_output:
            emit(state, [])
        else:
            state.skin.info("No jobs in session history.")
        return

    records = []
    for job_id in reversed(history):
        r = find_record(job_id)
        if r:
            records.append(r)

    if state.json_output:
        emit(state, [r.to_dict() for r in records])
        return

    headers = ["JOB ID", "STATUS", "RES", "IMAGE", "TIME", "OUTPUT/ERROR"]
    rows = [_record_to_row(r) for r in records]
    state.skin.table(headers, rows)


@jobs.command("show")
@click.argument("job_id")
@click.pass_obj
def jobs_show(state: CliState, job_id: str) -> None:
    """Show details for a specific JOB_ID."""
    record = find_record(job_id)
    if record is None:
        handle_backend_error(state, BackendError(f"Job not found: {job_id}"))
        return

    if state.json_output:
        emit(state, record.to_dict())
        return

    state.skin.status_block(
        {
            "job_id": record.job_id,
            "status": record.status,
            "resolution": record.resolution,
            "seed": str(record.seed),
            "image": record.image_path,
            "output_dir": record.output_dir,
            "glb": record.glb_path or "(none)",
            "duration": f"{record.duration_seconds:.1f}s" if record.duration_seconds else "(n/a)",
            "error": record.error or "(none)",
        },
        title="Job Details",
    )


# ── catalog group ─────────────────────────────────────────────────────────────


@cli.group()
@click.pass_context
def catalog(ctx: click.Context) -> None:
    """Browse the generation history catalog."""


@catalog.command("list")
@click.option("--status", "status_filter", default=None, help="Filter by status.")
@click.option("--limit", "-n", default=50, show_default=True, help="Max records to show.")
@click.pass_obj
def catalog_list(state: CliState, status_filter: Optional[str], limit: int) -> None:
    """List records from the catalog."""
    records = list_records(status_filter=status_filter, limit=limit)
    if state.json_output:
        emit(state, [r.to_dict() for r in records])
        return

    if not records:
        state.skin.info("Catalog is empty.")
        return

    headers = ["JOB ID", "STATUS", "RES", "IMAGE", "TIME", "OUTPUT/ERROR"]
    rows = [_record_to_row(r) for r in reversed(records)]
    state.skin.table(headers, rows)


@catalog.command("stats")
@click.pass_obj
def catalog_stats_cmd(state: CliState) -> None:
    """Show summary statistics for the catalog."""
    stats = catalog_stats()
    if state.json_output:
        emit(state, stats)
        return
    state.skin.status_block(
        {k: str(v) for k, v in stats.items()},
        title="Catalog Statistics",
    )


# ── session group ─────────────────────────────────────────────────────────────


@cli.group()
@click.pass_context
def session(ctx: click.Context) -> None:
    """Manage REPL session state."""


@session.command("show")
@click.pass_obj
def session_show(state: CliState) -> None:
    """Show current session state."""
    s = state.session
    data = s._to_dict()
    if state.json_output:
        emit(state, data)
        return
    state.skin.status_block(
        {
            "name": s.name,
            "trellis_home": s.trellis_home or "(not set)",
            "trellis_python": s.trellis_python or "(not set)",
            "default_resolution": s.default_resolution,
            "default_output_dir": s.default_output_dir or "(not set)",
            "history_count": str(len(s.history)),
            "settings": str(s.settings) if s.settings else "(empty)",
        },
        title="Session",
    )


@session.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_obj
def session_set(state: CliState, key: str, value: str) -> None:
    """Set a session KEY to VALUE.

    Special keys: trellis_home, trellis_python, default_resolution, default_output_dir.
    Any other key goes into session.settings dict.
    """
    s = state.session
    special_keys = {"trellis_home", "trellis_python", "default_resolution", "default_output_dir"}
    if key in special_keys:
        kwargs = {**s._to_dict_fields(), key: value}
        state.session = Session(**kwargs)
    else:
        state.session = s.set_setting(key, value)
    state.save_session()

    if state.json_output:
        emit(state, {"set": key, "value": value})
    else:
        state.skin.success(f"Set {key} = {value}")


@session.command("unset")
@click.argument("key")
@click.pass_obj
def session_unset(state: CliState, key: str) -> None:
    """Remove KEY from session settings."""
    state.session = state.session.unset_setting(key)
    state.save_session()
    if state.json_output:
        emit(state, {"unset": key})
    else:
        state.skin.success(f"Unset {key}")


@session.command("list")
@click.pass_obj
def session_list(state: CliState) -> None:
    """List all saved sessions."""
    sessions = Session.list_sessions()
    if state.json_output:
        emit(state, sessions)
        return
    if not sessions:
        state.skin.info("No saved sessions.")
        return
    for name in sessions:
        marker = " (active)" if name == state.session_name else ""
        state.skin.info(f"{name}{marker}")


@session.command("delete")
@click.argument("name")
@click.pass_obj
def session_delete(state: CliState, name: str) -> None:
    """Delete a saved session by NAME."""
    s = Session.load(name)
    deleted = s.delete()
    if state.json_output:
        emit(state, {"deleted": deleted, "name": name})
    else:
        if deleted:
            state.skin.success(f"Deleted session: {name}")
        else:
            state.skin.warning(f"Session not found: {name}")


@session.command("clear-history")
@click.pass_obj
def session_clear_history(state: CliState) -> None:
    """Clear job history from the current session."""
    s = state.session
    state.session = Session(**{**s._to_dict_fields(), "history": []})
    state.save_session()
    if state.json_output:
        emit(state, {"cleared": True})
    else:
        state.skin.success("Session history cleared.")


# ── config group ──────────────────────────────────────────────────────────────


@cli.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Show and validate environment configuration."""


@config.command("show")
@click.pass_obj
def config_show(state: CliState) -> None:
    """Show resolved configuration (home, python, GPU)."""
    trellis_home = state.resolved_trellis_home()
    python_path = state.resolved_python()

    data: Dict[str, Any] = {
        "trellis_home": str(trellis_home) if trellis_home else None,
        "trellis_python": python_path,
        "session": state.session_name,
        "version": __version__,
    }

    if state.json_output:
        emit(state, data)
        return

    state.skin.status_block(
        {
            "trellis_home": str(trellis_home) if trellis_home else "(not found — set TRELLIS_HOME)",
            "trellis_python": python_path,
            "session": state.session_name,
            "version": __version__,
        },
        title="Configuration",
    )


@config.command("validate")
@click.pass_obj
def config_validate(state: CliState) -> None:
    """Validate that TRELLIS.2 home and python are correctly configured."""
    python_path = state.resolved_python()
    trellis_home = state.resolved_trellis_home()

    errors: List[str] = []

    try:
        validate_python(python_path)
        if not state.json_output:
            state.skin.success(f"Python OK: {python_path}")
    except TrellisPythonError as exc:
        errors.append(str(exc))
        if not state.json_output:
            state.skin.error(str(exc))

    if trellis_home:
        try:
            validate_trellis_home(trellis_home)
            if not state.json_output:
                state.skin.success(f"TRELLIS home OK: {trellis_home}")
        except TrellisNotFoundError as exc:
            errors.append(str(exc))
            if not state.json_output:
                state.skin.error(str(exc))
    else:
        msg = "TRELLIS_HOME not set — set via --trellis-home, TRELLIS_HOME env, or session set trellis_home <path>"
        if not state.json_output:
            state.skin.warning(msg)

    if state.json_output:
        emit(state, {"valid": len(errors) == 0, "errors": errors})
    elif errors:
        sys.exit(1)


@config.command("probe-gpu")
@click.pass_obj
def config_probe_gpu(state: CliState) -> None:
    """Probe GPU availability via the runner subprocess."""
    python_path = state.resolved_python()
    trellis_home = state.resolved_trellis_home()

    try:
        info = probe_gpu(python_path=python_path, trellis_home=trellis_home)
    except (GPUUnavailableError, TrellisPythonError, BackendError) as exc:
        handle_backend_error(state, exc)
        return

    if state.json_output:
        emit(state, info)
        return

    if info.get("available"):
        state.skin.success(f"CUDA available — {info.get('device_count', 0)} device(s)")
        for dev in info.get("devices", []):
            state.skin.status(
                f"  GPU {dev['index']}", f"{dev['name']} ({dev['total_memory_gb']} GB)"
            )
    else:
        state.skin.error("CUDA not available")
        if "error" in info:
            state.skin.hint(info["error"])


# ── repl command ──────────────────────────────────────────────────────────────


@cli.command("repl")
@click.pass_obj
def repl(state: CliState) -> None:
    """Drop into an interactive REPL (default when no subcommand given)."""
    skin = state.skin
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    _REPL_HELP: Dict[str, str] = {
        "generate run <image>": "Generate 3D GLB from image file",
        "jobs list": "List recent jobs from session history",
        "jobs show <id>": "Show job details",
        "catalog list": "Browse all generation history",
        "catalog stats": "Show catalog statistics",
        "session show": "Show current session",
        "session set <k> <v>": "Set session key",
        "config show": "Show resolved configuration",
        "config validate": "Validate TRELLIS home + python",
        "config probe-gpu": "Probe GPU availability",
        "help": "Show this help",
        "quit / exit": "Exit REPL",
    }

    while True:
        try:
            raw = skin.get_input(
                pt_session,
                context=state.session_name,
            )
        except (KeyboardInterrupt, EOFError):
            skin.print_goodbye()
            break

        if not raw:
            continue

        line = raw.strip()
        lower = line.lower()

        if lower in {"quit", "exit", "q"}:
            skin.print_goodbye()
            break

        if lower in {"help", "h", "?"}:
            skin.help(_REPL_HELP)
            continue

        # Parse and dispatch via Click in standalone_mode=False
        args = line.split()
        try:
            cli.main(args=args, obj=state, standalone_mode=False)
        except SystemExit:
            pass
        except click.exceptions.UsageError as exc:
            skin.error(str(exc))
        except click.exceptions.Abort:
            pass
        except Exception as exc:
            skin.error(f"Unexpected error: {exc}")


# ── Module entry point ────────────────────────────────────────────────────────


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
