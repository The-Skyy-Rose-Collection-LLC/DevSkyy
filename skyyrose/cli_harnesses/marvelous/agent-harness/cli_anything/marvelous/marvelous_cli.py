"""cli-anything-marvelous — Click CLI entry point for Marvelous Designer.

Defaults to REPL mode when invoked without a subcommand.

Command groups:
    project   — info, new
    garment   — list, add-fabric
    simulate  — run
    export    — (top-level command group)
    library   — list, import
    config    — doctor
    session   — status, save, list, delete
    repl      — interactive shell
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click
from cli_anything.marvelous import __version__
from cli_anything.marvelous.core import garment as garment_mod
from cli_anything.marvelous.core import library as library_mod
from cli_anything.marvelous.core import project as project_mod
from cli_anything.marvelous.core import session as session_mod
from cli_anything.marvelous.utils.marvelous_backend import (
    MarvelousError, MarvelousNotFoundError, MarvelousScriptError,
    MarvelousTimeoutError, find_marvelous_binary, load_script_template,
    render_script_template, run_md_script)
from cli_anything.marvelous.utils.repl_skin import ReplSkin

# ── CLI state ─────────────────────────────────────────────────────────────


class CliState:
    """Shared state threaded through Click context."""

    def __init__(self, json_mode: bool = False, verbose: bool = False):
        self.json_mode = json_mode
        self.verbose = verbose
        self.skin = ReplSkin("marvelous", version=__version__)
        self.session: session_mod.Session | None = None

    def emit(self, data: Any, *, text: str | None = None) -> None:
        """Output data as JSON or human-readable text."""
        if self.json_mode:
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            click.echo(text if text is not None else str(data))

    def emit_error(self, message: str, code: int = 1) -> None:
        """Print error via skin and exit."""
        self.skin.error(message)
        sys.exit(code)


def handle_backend_error(state: CliState, exc: Exception) -> None:
    """Translate backend exceptions to user-friendly messages."""
    if isinstance(exc, MarvelousNotFoundError):
        state.emit_error(
            "Marvelous Designer not found. Install from https://www.marvelousdesigner.com/ "
            "or set MARVELOUS_DESIGNER_BIN=/path/to/binary."
        )
    elif isinstance(exc, MarvelousTimeoutError):
        state.emit_error(f"Timed out: {exc}")
    elif isinstance(exc, MarvelousScriptError):
        state.emit_error(f"Script error (exit {exc.returncode}): {exc}")
    elif isinstance(exc, MarvelousError):
        state.emit_error(f"Marvelous Designer error: {exc}")
    else:
        state.emit_error(f"Unexpected error: {exc}")


# ── Root group ────────────────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.option("--json", "json_mode", is_flag=True, help="Output results as JSON.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.version_option(__version__, prog_name="cli-anything-marvelous")
@click.pass_context
def main(ctx: click.Context, json_mode: bool, verbose: bool) -> None:
    """cli-anything harness for Marvelous Designer.

    Invoke without a subcommand to enter the interactive REPL.
    """
    ctx.ensure_object(dict)
    ctx.obj = CliState(json_mode=json_mode, verbose=verbose)

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── project group ─────────────────────────────────────────────────────────


@main.group()
@click.pass_context
def project(ctx: click.Context) -> None:
    """Manage Marvelous Designer project files (.zpac / .zprj)."""


@project.command("info")
@click.argument("path", type=click.Path(exists=True))
@click.pass_obj
def project_info(state: CliState, path: str) -> None:
    """Show metadata for a .zpac or .zprj project file."""
    try:
        meta = project_mod.read_project_meta(path)
    except (FileNotFoundError, project_mod.ProjectFileError) as exc:
        state.emit_error(str(exc))
        return

    if state.json_mode:
        state.emit(meta.to_dict())
    else:
        state.skin.status_block(
            {
                "Name": meta.name,
                "Format": meta.file_format.upper(),
                "MD Version": meta.md_version or "(unknown)",
                "Created": meta.created_at or "(unknown)",
                "Patterns": str(meta.pattern_count),
                "Fabrics": str(meta.fabric_count),
                "Thumbnail": "yes" if meta.has_thumbnail else "no",
                "Path": meta.path,
            },
            title="Project Info",
        )


@project.command("new")
@click.argument("output", type=click.Path())
@click.option("--name", default="", help="Project name (defaults to filename stem).")
@click.pass_obj
def project_new(state: CliState, output: str, name: str) -> None:
    """Create a new empty session pointing at OUTPUT path.

    Does not create a .zpac file — use Marvelous Designer for that.
    Creates a CLI session pre-configured with the given output path.
    """
    out_path = Path(output)
    project_name = name or out_path.stem
    s = session_mod.new_session(
        project_path=str(out_path),
        garment_name=project_name,
    )
    if state.json_mode:
        state.emit(s.to_dict())
    else:
        state.skin.success(f"Session created: {s.session_id}")
        state.skin.status("Project path", s.project_path)
        state.skin.status("Session ID", s.session_id)


# ── garment group ─────────────────────────────────────────────────────────


@main.group()
@click.pass_context
def garment(ctx: click.Context) -> None:
    """Inspect and modify garments in a project file."""


@garment.command("list")
@click.argument("path", type=click.Path(exists=True))
@click.pass_obj
def garment_list(state: CliState, path: str) -> None:
    """List pattern pieces and fabrics in a .zpac or .zprj file."""
    try:
        g = project_mod.load_garment_from_project(path)
    except (FileNotFoundError, project_mod.ProjectFileError) as exc:
        state.emit_error(str(exc))
        return

    if state.json_mode:
        state.emit(g.to_dict())
        return

    state.skin.section(f"Garment: {g.name}")
    state.skin.info(f"Source: {g.source_file}")
    state.skin.info(f"Simulation frames: {g.simulation_frames}")

    if g.patterns:
        state.skin.section("Pattern Pieces")
        state.skin.table(
            ["Name", "Fabric", "Vertices", "Area (cm²)"],
            [[p.name, p.fabric_name, str(p.vertex_count), f"{p.area_cm2:.1f}"] for p in g.patterns],
        )
    else:
        state.skin.hint("No pattern pieces found in archive.")

    if g.fabrics:
        state.skin.section("Fabrics")
        state.skin.table(
            ["Name", "Color", "Density", "Thickness"],
            [[f.name, f.color_hex, f"{f.density:.2f}", f"{f.thickness:.1f}mm"] for f in g.fabrics],
        )
    else:
        state.skin.hint("No fabrics found in archive.")


@garment.command("add-fabric")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--pattern", required=True, help="Pattern piece name to assign fabric to.")
@click.option("--fabric-name", required=True, help="Name for the new fabric.")
@click.option(
    "--texture",
    required=True,
    type=click.Path(exists=True),
    help="Path to fabric texture image.",
)
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Path to save modified .zpac.",
)
@click.option("--timeout", default=300, show_default=True, help="Script timeout in seconds.")
@click.pass_obj
def garment_add_fabric(
    state: CliState,
    project_path: str,
    pattern: str,
    fabric_name: str,
    texture: str,
    output: str,
    timeout: int,
) -> None:
    """Assign a fabric to a pattern piece inside Marvelous Designer."""
    try:
        template_text = load_script_template("add_fabric.py.tpl")
        script = render_script_template(
            template_text,
            {
                "project_path": project_path,
                "pattern_name": pattern,
                "fabric_name": fabric_name,
                "texture_path": texture,
                "output_path": output,
            },
        )
        if state.verbose:
            state.skin.info("Running add_fabric script inside MD...")
        proc = run_md_script(script, timeout=timeout)
        if state.json_mode:
            state.emit(
                {
                    "ok": True,
                    "output_path": output,
                    "stdout": proc.stdout,
                }
            )
        else:
            state.skin.success(f"Fabric '{fabric_name}' assigned. Saved: {output}")
            if state.verbose:
                click.echo(proc.stdout)
    except Exception as exc:
        handle_backend_error(state, exc)


# ── simulate group ────────────────────────────────────────────────────────


@main.group()
@click.pass_context
def simulate(ctx: click.Context) -> None:
    """Run garment physics simulation in Marvelous Designer."""


@simulate.command("run")
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--frames", default=100, show_default=True, help="Number of sim frames.")
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Path to save the simulated .zpac.",
)
@click.option("--timeout", default=600, show_default=True, help="Script timeout in seconds.")
@click.pass_obj
def simulate_run(
    state: CliState,
    project_path: str,
    frames: int,
    output: str,
    timeout: int,
) -> None:
    """Simulate garment physics and save the result."""
    try:
        template_text = load_script_template("simulate.py.tpl")
        script = render_script_template(
            template_text,
            {
                "project_path": project_path,
                "frames": str(frames),
                "output_path": output,
            },
        )
        if state.verbose:
            state.skin.info(f"Simulating {frames} frames...")
        proc = run_md_script(script, timeout=timeout)
        if state.json_mode:
            state.emit(
                {
                    "ok": True,
                    "frames": frames,
                    "output_path": output,
                    "stdout": proc.stdout,
                }
            )
        else:
            state.skin.success(f"Simulation complete ({frames} frames). Saved: {output}")
            if state.verbose:
                click.echo(proc.stdout)
    except Exception as exc:
        handle_backend_error(state, exc)


# ── export group ──────────────────────────────────────────────────────────


@main.group("export")
@click.pass_context
def export_group(ctx: click.Context) -> None:
    """Export garments from Marvelous Designer projects."""


@export_group.command("run")
@click.argument("project_path", type=click.Path(exists=True))
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["obj", "fbx", "alembic", "usd", "zpac", "zprj"], case_sensitive=False),
    default="obj",
    show_default=True,
    help="Export format. Note: GLB is not supported by MD's API; use usd instead.",
)
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Output path (without extension; extension is added per format).",
)
@click.option("--timeout", default=300, show_default=True, help="Script timeout in seconds.")
@click.pass_obj
def export_run(
    state: CliState,
    project_path: str,
    fmt: str,
    output: str,
    timeout: int,
) -> None:
    """Export a .zpac/.zprj to OBJ, FBX, Alembic, USD, ZPac, or ZPrj."""
    try:
        template_text = load_script_template("export.py.tpl")
        script = render_script_template(
            template_text,
            {
                "project_path": project_path,
                "output_path": output,
                "export_format": fmt,
            },
        )
        if state.verbose:
            state.skin.info(f"Exporting as {fmt.upper()}...")
        proc = run_md_script(script, timeout=timeout)
        if state.json_mode:
            state.emit(
                {
                    "ok": True,
                    "format": fmt,
                    "output_path": output,
                    "stdout": proc.stdout,
                }
            )
        else:
            state.skin.success(f"Export complete ({fmt.upper()}): {output}")
            if state.verbose:
                click.echo(proc.stdout)
    except Exception as exc:
        handle_backend_error(state, exc)


# ── library group ─────────────────────────────────────────────────────────


@main.group()
@click.pass_context
def library(ctx: click.Context) -> None:
    """Manage local garment template library."""


@library.command("list")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON.")
@click.pass_obj
def library_list(state: CliState, json_mode: bool = False) -> None:
    if json_mode:
        state.json_mode = True
    """List all entries in the local garment library."""
    entries = library_mod.list_library()
    if state.json_mode:
        state.emit([e.to_dict() for e in entries])
        return
    if not entries:
        state.skin.hint("Library is empty. Use 'library import' to add templates.")
        return
    state.skin.table(
        ["Slug", "Name", "Tags", "Description"],
        [[e.slug, e.name, ", ".join(e.tags), e.description] for e in entries],
    )


@library.command("import")
@click.argument("source", type=click.Path(exists=True))
@click.option("--slug", required=True, help="Unique identifier (e.g. tshirt-basic).")
@click.option("--name", required=True, help="Human-readable name.")
@click.option("--description", default="", help="Optional description.")
@click.option("--tags", default="", help="Comma-separated tags.")
@click.pass_obj
def library_import(
    state: CliState,
    source: str,
    slug: str,
    name: str,
    description: str,
    tags: str,
) -> None:
    """Import a .zpac or .zprj file into the local library."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    try:
        entry = library_mod.import_project(source, slug, name, description, tag_list)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        state.emit_error(str(exc))
        return
    if state.json_mode:
        state.emit(entry.to_dict())
    else:
        state.skin.success(f"Imported '{entry.name}' as '{entry.slug}'")


# ── config group ──────────────────────────────────────────────────────────


@main.group()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Configuration and environment diagnostics."""


@config.command("doctor")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON.")
@click.pass_obj
def config_doctor(state: CliState, json_mode: bool = False) -> None:
    if json_mode:
        state.json_mode = True
    """Check that Marvelous Designer is installed and discoverable."""
    issues: list[str] = []
    md_bin: str | None = None

    try:
        md_bin = find_marvelous_binary()
        bin_ok = True
    except MarvelousNotFoundError as exc:
        bin_ok = False
        issues.append(str(exc))

    session_dir_ok = True
    try:
        session_mod.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        session_dir_ok = False
        issues.append(f"Cannot create sessions dir: {exc}")

    library_dir_ok = True
    try:
        library_mod.LIBRARY_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        library_dir_ok = False
        issues.append(f"Cannot create library dir: {exc}")

    if state.json_mode:
        state.emit(
            {
                "md_binary": md_bin,
                "md_binary_found": bin_ok,
                "sessions_dir": str(session_mod.SESSIONS_DIR),
                "sessions_dir_ok": session_dir_ok,
                "library_dir": str(library_mod.LIBRARY_DIR),
                "library_dir_ok": library_dir_ok,
                "issues": issues,
                "ok": len(issues) == 0,
            }
        )
        return

    state.skin.section("Marvelous Designer Doctor")
    _ok = state.skin.success
    _fail = state.skin.error

    if bin_ok:
        _ok(f"MD binary: {md_bin}")
    else:
        _fail("MD binary: not found")

    if session_dir_ok:
        _ok(f"Sessions dir: {session_mod.SESSIONS_DIR}")
    else:
        _fail(f"Sessions dir: {session_mod.SESSIONS_DIR} (not writable)")

    if library_dir_ok:
        _ok(f"Library dir: {library_mod.LIBRARY_DIR}")
    else:
        _fail(f"Library dir: {library_mod.LIBRARY_DIR} (not writable)")

    if issues:
        state.skin.section("Issues")
        for issue in issues:
            state.skin.warning(issue)
    else:
        state.skin.info("All checks passed.")


# ── session group ─────────────────────────────────────────────────────────


@main.group()
@click.pass_context
def session(ctx: click.Context) -> None:
    """Manage CLI sessions (persistent work context)."""


@session.command("status")
@click.argument("session_id", required=False)
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON.")
@click.pass_obj
def session_status(state: CliState, session_id: str | None, json_mode: bool = False) -> None:
    if json_mode:
        state.json_mode = True
    """Show status of SESSION_ID or the most recent session."""
    try:
        if session_id:
            s = session_mod.load_session(session_id)
        else:
            sessions = session_mod.list_sessions()
            if not sessions:
                state.emit_error("No sessions found.")
                return
            s = sessions[0]
    except (FileNotFoundError, ValueError) as exc:
        state.emit_error(str(exc))
        return

    if state.json_mode:
        state.emit(s.to_dict())
    else:
        import time

        state.skin.status_block(
            {
                "ID": s.session_id,
                "Project": s.project_path or "(none)",
                "Garment": s.garment_name or "(none)",
                "Sim frames": str(s.simulation_frames),
                "Last export": s.last_export_path or "(none)",
                "Updated": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.updated_at)),
                "Notes": s.notes or "(none)",
            },
            title="Session Status",
        )


@session.command("save")
@click.argument("session_id", required=False)
@click.option("--project", default=None, help="Project file path.")
@click.option("--garment", default=None, help="Garment name.")
@click.option("--frames", default=None, type=int, help="Simulation frames.")
@click.option("--notes", default=None, help="Session notes.")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON.")
@click.pass_obj
def session_save(
    state: CliState,
    session_id: str | None,
    project: str | None,
    garment: str | None,
    frames: int | None,
    notes: str | None,
    json_mode: bool = False,
) -> None:
    if json_mode:
        state.json_mode = True
    """Create or update a session. Creates new if SESSION_ID is omitted."""
    if session_id:
        try:
            s = session_mod.load_session(session_id)
        except (FileNotFoundError, ValueError):
            s = session_mod.Session(session_id=session_id)
    else:
        s = session_mod.Session(session_id=f"md-{int(__import__('time').time() * 1000)}")

    if project is not None:
        s.project_path = project
    if garment is not None:
        s.garment_name = garment
    if frames is not None:
        s.simulation_frames = frames
    if notes is not None:
        s.notes = notes

    path = session_mod.save_session(s)
    if state.json_mode:
        state.emit(s.to_dict())
    else:
        state.skin.success(f"Session saved: {s.session_id}")
        state.skin.hint(f"Path: {path}")


@session.command("list")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON.")
@click.pass_obj
def session_list(state: CliState, json_mode: bool = False) -> None:
    if json_mode:
        state.json_mode = True
    """List all saved sessions, newest first."""
    sessions = session_mod.list_sessions()
    if state.json_mode:
        state.emit([s.to_dict() for s in sessions])
        return
    if not sessions:
        state.skin.hint("No sessions found.")
        return
    import time

    state.skin.table(
        ["ID", "Project", "Garment", "Updated"],
        [
            [
                s.session_id,
                Path(s.project_path).name if s.project_path else "(none)",
                s.garment_name or "(none)",
                time.strftime("%Y-%m-%d %H:%M", time.localtime(s.updated_at)),
            ]
            for s in sessions
        ],
    )


@session.command("delete")
@click.argument("session_id")
@click.option("--json", "json_mode", is_flag=True, help="Output as JSON.")
@click.pass_obj
def session_delete(state: CliState, session_id: str, json_mode: bool = False) -> None:
    if json_mode:
        state.json_mode = True
    """Delete a session by ID."""
    deleted = session_mod.delete_session(session_id)
    if state.json_mode:
        state.emit({"deleted": deleted, "session_id": session_id})
    elif deleted:
        state.skin.success(f"Deleted session: {session_id}")
    else:
        state.emit_error(f"Session not found: {session_id}")


# ── repl ──────────────────────────────────────────────────────────────────


@main.command("repl")
@click.pass_obj
def repl(state: CliState) -> None:
    """Launch interactive REPL shell for Marvelous Designer."""
    skin = state.skin
    skin.print_banner()

    pt_session = skin.create_prompt_session()

    project_name = ""
    modified = False

    while True:
        try:
            line = skin.get_input(pt_session, project_name=project_name, modified=modified)
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        if not line:
            continue

        parts = line.split()
        cmd = parts[0].lower()

        if cmd in ("quit", "exit", "q"):
            skin.print_goodbye()
            break

        if cmd == "help":
            skin.help(
                {
                    "project info <path>": "Show project metadata",
                    "project new <output>": "Create a new session",
                    "garment list <path>": "List garment patterns and fabrics",
                    "garment add-fabric": "Assign fabric inside MD",
                    "simulate run": "Run physics simulation",
                    "export run": "Export to OBJ/FBX/Alembic/USD",
                    "library list": "Show garment template library",
                    "library import": "Import .zpac into library",
                    "config doctor": "Check MD installation",
                    "session status": "Show current session",
                    "session list": "List all sessions",
                    "session save": "Save session state",
                    "session delete <id>": "Delete a session",
                    "quit": "Exit the REPL",
                }
            )
            continue

        # Dispatch to Click commands via main
        try:
            main.main(
                args=parts,
                obj=state,
                standalone_mode=False,
            )
        except SystemExit:
            pass
        except click.exceptions.UsageError as exc:
            skin.error(str(exc))
        except Exception as exc:
            skin.error(f"Error: {exc}")
