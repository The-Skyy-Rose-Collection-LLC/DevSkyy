"""
cli-anything-skyyrose-theme — main Click CLI entry point.

Default mode: REPL (invoked with no subcommand).
All production-touching commands require --confirm after printing a manifest.
--json flag on every command emits machine-readable output.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click

# ---------------------------------------------------------------------------
# CLI State
# ---------------------------------------------------------------------------


@dataclass
class CliState:
    json_output: bool = False
    theme_root: Path | None = None
    _skin: Any = None  # ReplSkin, lazy

    @property
    def skin(self) -> Any:
        if self._skin is None:
            from cli_anything.skyyrose_theme.utils.repl_skin import ReplSkin

            self._skin = ReplSkin()
        return self._skin


pass_state = click.make_pass_decorator(CliState, ensure=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def emit(state: CliState, payload: dict[str, Any], human: str | None = None) -> None:
    """Print payload as JSON or human-readable depending on state.json_output."""
    if state.json_output:
        click.echo(json.dumps(payload, indent=2, default=str))
    else:
        if human is not None:
            click.echo(human)
        else:
            # Fallback: pretty-print key: value pairs
            for k, v in payload.items():
                click.echo(f"  {k}: {v}")


def handle_error(state: CliState, exc: Exception, exit_code: int = 1) -> None:
    """Print error and exit."""
    msg = str(exc)
    if state.json_output:
        click.echo(json.dumps({"error": msg, "ok": False}, indent=2), err=True)
    else:
        state.skin.error(msg)
    sys.exit(exit_code)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------


@click.group(invoke_without_command=True)
@click.option("--json", "json_output", is_flag=True, help="Emit JSON output.")
@click.option(
    "--theme-root",
    envvar="SKYYROSE_THEME_ROOT",
    type=click.Path(),
    help="Override theme root directory.",
)
@click.version_option(package_name="cli-anything-skyyrose-theme")
@click.pass_context
def cli(ctx: click.Context, json_output: bool, theme_root: str | None) -> None:
    """SkyyRose Theme CLI — meta-CLI for the SkyyRose WordPress theme dev loop."""
    ctx.ensure_object(CliState)
    state: CliState = ctx.obj
    state.json_output = json_output
    if theme_root:
        state.theme_root = Path(theme_root)

    if ctx.invoked_subcommand is None:
        # Default: launch REPL
        ctx.invoke(repl)


# ---------------------------------------------------------------------------
# version group
# ---------------------------------------------------------------------------


@cli.group("version")
def version_group() -> None:
    """Read or bump the theme version across functions.php, style.css, readme.txt."""


@version_group.command("current")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def version_current(state: CliState, json_output: bool) -> None:
    """Show the current version from all three canonical sources."""
    if json_output:
        state.json_output = True
    from cli_anything.skyyrose_theme.core.version import (VersionMismatchError,
                                                          read_version)

    try:
        vs = read_version(state.theme_root)
    except Exception as exc:
        handle_error(state, exc)
        return

    payload = {
        "functions_php": vs.functions_php,
        "style_css": vs.style_css,
        "readme_txt": vs.readme_txt,
        "consistent": vs.consistent,
    }
    human = None
    if not state.json_output:
        skin = state.skin
        if vs.consistent:
            skin.success(f"Version: {vs.functions_php}  (all sources agree)")
        else:
            skin.warning("Version mismatch detected:")
            skin.status("functions.php", vs.functions_php)
            skin.status("style.css", vs.style_css)
            skin.status("readme.txt", vs.readme_txt)
    emit(state, payload, human)


@version_group.command("bump")
@click.option("--to", "new_version", required=True, help="New version string, e.g. 1.5.21")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def version_bump(state: CliState, new_version: str, json_output: bool) -> None:
    """Bump the theme version atomically across all three files."""
    if json_output:
        state.json_output = True
    from cli_anything.skyyrose_theme.core.version import write_version

    try:
        vs = write_version(new_version, state.theme_root)
    except Exception as exc:
        handle_error(state, exc)
        return

    payload = {
        "ok": True,
        "new_version": vs.current,
        "functions_php": vs.functions_php,
        "style_css": vs.style_css,
        "readme_txt": vs.readme_txt,
    }
    if not state.json_output:
        state.skin.success(f"Bumped to {vs.current}")
    emit(state, payload)


# ---------------------------------------------------------------------------
# template group
# ---------------------------------------------------------------------------


@cli.group("template")
def template_group() -> None:
    """Discover and inspect theme templates."""


@template_group.command("list")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def template_list(state: CliState, json_output: bool) -> None:
    """List all template-*.php files and their registered slugs."""
    if json_output:
        state.json_output = True
    from cli_anything.skyyrose_theme.core.template import load_templates

    try:
        tmap = load_templates(state.theme_root)
    except Exception as exc:
        handle_error(state, exc)
        return

    rows = [
        {
            "filename": t.filename,
            "slug": t.slug or "(unregistered)",
            "exists": "yes" if t.exists else "MISSING",
        }
        for t in sorted(tmap.templates, key=lambda x: x.filename)
    ]
    payload = {"templates": rows, "total": len(rows)}
    if not state.json_output:
        state.skin.table(rows, headers=["filename", "slug", "exists"])
        click.echo(f"  {len(rows)} templates found.")
    emit(state, payload)


@template_group.command("render")
@click.argument("slug_or_file")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def template_render(state: CliState, slug_or_file: str, json_output: bool) -> None:
    """Show template metadata for a given slug or filename."""
    if json_output:
        state.json_output = True
    from cli_anything.skyyrose_theme.core.template import load_templates

    try:
        tmap = load_templates(state.theme_root)
    except Exception as exc:
        handle_error(state, exc)
        return

    t = tmap.by_slug(slug_or_file) or tmap.by_filename(slug_or_file)
    if t is None:
        handle_error(state, ValueError(f"Template not found: {slug_or_file!r}"))
        return

    payload = {
        "filename": t.filename,
        "slug": t.slug,
        "path": str(t.path),
        "exists": t.exists,
    }
    if not state.json_output:
        skin = state.skin
        skin.status("filename", t.filename)
        skin.status("slug", t.slug or "(unregistered)")
        skin.status("path", str(t.path))
        skin.status("exists", "yes" if t.exists else "MISSING", ok=t.exists)
    emit(state, payload)


# ---------------------------------------------------------------------------
# deploy command
# ---------------------------------------------------------------------------


@cli.command("deploy")
@click.option("--dry-run", is_flag=True, help="Pass --dry-run to deploy-theme.sh (no upload).")
@click.option(
    "--with-maintenance",
    is_flag=True,
    help="Lock site during deploy (slower, safer for DB migrations).",
)
@click.option(
    "--confirm",
    is_flag=True,
    help="Required to actually deploy. Without this, prints manifest and exits.",
)
@click.option("--json", "json_output", is_flag=True)
@pass_state
def deploy(
    state: CliState,
    dry_run: bool,
    with_maintenance: bool,
    confirm: bool,
    json_output: bool,
) -> None:
    """Deploy the theme to skyyrose.co via deploy-theme.sh.

    Always prints a STOP-AND-SHOW manifest. Requires --confirm to proceed.
    """
    if json_output:
        state.json_output = True

    from cli_anything.skyyrose_theme.core.deploy import (
        DeployNotConfirmedError, DeployScriptNotFoundError,
        build_deploy_manifest, run_deploy)

    try:
        manifest = build_deploy_manifest(
            dry_run=dry_run,
            with_maintenance=with_maintenance,
            theme_root=state.theme_root,
        )
    except DeployScriptNotFoundError as exc:
        handle_error(state, exc)
        return

    manifest_dict = manifest.to_dict()

    if state.json_output:
        emit(state, {"manifest": manifest_dict, "confirmed": confirm})
    else:
        state.skin.print_manifest(manifest_dict)

    if not confirm:
        if not state.json_output:
            click.echo("  Pass --confirm to execute the deploy.")
        sys.exit(0)

    # confirmed=True — execute
    try:
        run_deploy(manifest, confirmed=True)
    except Exception as exc:
        handle_error(state, exc)
        return

    if not state.json_output:
        state.skin.success("Deploy completed.")
    emit(state, {"ok": True, "mode": manifest.mode})


# ---------------------------------------------------------------------------
# verify command
# ---------------------------------------------------------------------------


@cli.command("verify")
@click.option("--url", "base_url", default=None, help="Override PUBLIC_URL.")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def verify(state: CliState, base_url: str | None, json_output: bool) -> None:
    """Run live HTTP checks against skyyrose.co."""
    if json_output:
        state.json_output = True

    from cli_anything.skyyrose_theme.core.verify import (VerifyFailedError,
                                                         verify_live)

    try:
        report = verify_live(base_url=base_url)
    except VerifyFailedError as exc:
        if state.json_output:
            emit(state, {"ok": False, "error": str(exc)})
        else:
            state.skin.error(str(exc))
        sys.exit(1)
    except Exception as exc:
        handle_error(state, exc)
        return

    rows = [
        {
            "url": r.url,
            "status": r.status_code,
            "bytes": r.body_bytes,
            "verdict": r.verdict,
        }
        for r in report.results
    ]
    payload = {"ok": report.passed, "summary": report.summary, "results": rows}

    if not state.json_output:
        state.skin.table(rows, headers=["url", "status", "bytes", "verdict"])
        if report.passed:
            state.skin.success(report.summary)
        else:
            state.skin.error(report.summary)
    emit(state, payload)


# ---------------------------------------------------------------------------
# cache group
# ---------------------------------------------------------------------------


@cli.group("cache")
def cache_group() -> None:
    """Manage server-side caches via wp-cli over SSH."""


@cache_group.command("purge")
@click.option("--confirm", is_flag=True, help="Required to actually purge.")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def cache_purge(state: CliState, confirm: bool, json_output: bool) -> None:
    """Flush all caches on the production server."""
    if json_output:
        state.json_output = True

    manifest_dict = {
        "action": "cache purge (wp cache flush)",
        "target": "skyyrose.co production",
        "method": "wp-cli over SSH",
        "cost": "$0",
        "irreversible": False,
    }

    if not state.json_output:
        state.skin.print_manifest(manifest_dict)

    if not confirm:
        if not state.json_output:
            click.echo("  Pass --confirm to execute.")
        emit(state, {"manifest": manifest_dict, "confirmed": False})
        sys.exit(0)

    from cli_anything.skyyrose_theme.core.deploy import purge_cache

    try:
        result = purge_cache()
    except Exception as exc:
        handle_error(state, exc)
        return

    payload = {"ok": True, "stdout": result.stdout.strip()}
    if not state.json_output:
        state.skin.success("Cache purged.")
    emit(state, payload)


# ---------------------------------------------------------------------------
# lint group
# ---------------------------------------------------------------------------


@cli.group("lint")
def lint_group() -> None:
    """PHP linting via PHPCS and php -l."""


@lint_group.command("php")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def lint_php(state: CliState, json_output: bool) -> None:
    """Run PHPCS against the theme (read-only, no changes)."""
    if json_output:
        state.json_output = True

    from cli_anything.skyyrose_theme.utils.theme_backend import (
        PHPCSNotFoundError, run_phpcs)

    try:
        result = run_phpcs(state.theme_root, fix=False)
    except PHPCSNotFoundError as exc:
        handle_error(state, exc)
        return
    except Exception as exc:
        handle_error(state, exc)
        return

    payload = {"ok": result.ok, "returncode": result.returncode, "output": result.stdout}
    if not state.json_output:
        if result.ok:
            state.skin.success("No PHPCS violations found.")
        else:
            click.echo(result.stdout)
            state.skin.error(f"PHPCS found violations (exit {result.returncode}).")
    emit(state, payload)


@lint_group.command("fix")
@click.option("--confirm", is_flag=True, help="Required to run PHPCBF (modifies files).")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def lint_fix(state: CliState, confirm: bool, json_output: bool) -> None:
    """Run PHPCBF to auto-fix PHPCS violations (modifies PHP files)."""
    if json_output:
        state.json_output = True

    manifest_dict = {
        "action": "phpcbf --standard=.phpcs.xml (auto-fix PHP files)",
        "target": str(state.theme_root or "SKYYROSE_THEME_ROOT"),
        "modifies_files": True,
        "cost": "$0",
    }

    if not state.json_output:
        state.skin.print_manifest(manifest_dict)

    if not confirm:
        if not state.json_output:
            click.echo("  Pass --confirm to run PHPCBF.")
        emit(state, {"manifest": manifest_dict, "confirmed": False})
        sys.exit(0)

    from cli_anything.skyyrose_theme.utils.theme_backend import (
        PHPCSNotFoundError, run_phpcs)

    try:
        result = run_phpcs(state.theme_root, fix=True)
    except PHPCSNotFoundError as exc:
        handle_error(state, exc)
        return
    except Exception as exc:
        handle_error(state, exc)
        return

    payload = {"ok": result.ok, "returncode": result.returncode, "output": result.stdout}
    if not state.json_output:
        if result.returncode == 0:
            state.skin.success("PHPCBF: no fixable violations or all fixed.")
        else:
            click.echo(result.stdout)
            state.skin.warning(f"PHPCBF exited {result.returncode} (some violations may remain).")
    emit(state, payload)


# ---------------------------------------------------------------------------
# doctor command
# ---------------------------------------------------------------------------


@cli.command("doctor")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def doctor(state: CliState, json_output: bool) -> None:
    """Run health checks: theme root, PHPCS, PHP binary, deploy script."""
    if json_output:
        state.json_output = True

    from cli_anything.skyyrose_theme.utils.theme_backend import \
        doctor as run_doctor

    report = run_doctor(state.theme_root)
    payload = {"healthy": report.healthy, "checks": report.checks}

    if not state.json_output:
        for check in report.checks:
            state.skin.status(
                check["name"],
                check.get("detail", ""),
                ok=(check["status"] == "ok"),
            )
        if report.healthy:
            state.skin.success("All checks passed.")
        else:
            state.skin.warning("Some checks failed. See above.")
    emit(state, payload)


# ---------------------------------------------------------------------------
# session group
# ---------------------------------------------------------------------------


@cli.group("session")
def session_group() -> None:
    """Manage named REPL sessions (~/.cli_anything/skyyrose_theme/sessions/)."""


@session_group.command("status")
@click.option("--name", default="default", help="Session name.")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def session_status(state: CliState, name: str, json_output: bool) -> None:
    """Show status of the named session."""
    if json_output:
        state.json_output = True

    from cli_anything.skyyrose_theme.core.session import get_or_create_session

    session = get_or_create_session(name)
    payload = {
        "id": session.id,
        "name": session.name,
        "history_count": len(session.history),
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
    if not state.json_output:
        skin = state.skin
        skin.status("id", session.id)
        skin.status("name", session.name)
        skin.status("history_count", str(len(session.history)))
    emit(state, payload)


@session_group.command("save")
@click.option("--name", default="default")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def session_save(state: CliState, name: str, json_output: bool) -> None:
    """Save (or create) the named session."""
    if json_output:
        state.json_output = True

    from cli_anything.skyyrose_theme.core.session import (
        get_or_create_session, save_session)

    session = get_or_create_session(name)
    path = save_session(session)
    payload = {"ok": True, "path": str(path)}
    if not state.json_output:
        state.skin.success(f"Session saved: {path}")
    emit(state, payload)


@session_group.command("list")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def session_list(state: CliState, json_output: bool) -> None:
    """List all saved sessions."""
    if json_output:
        state.json_output = True

    from cli_anything.skyyrose_theme.core.session import list_sessions

    sessions = list_sessions()
    rows = [{"id": s.id[:8] + "...", "name": s.name, "history": len(s.history)} for s in sessions]
    payload = {"sessions": rows, "total": len(rows)}
    if not state.json_output:
        if rows:
            state.skin.table(rows, headers=["id", "name", "history"])
        else:
            state.skin.info("No sessions found.")
    emit(state, payload)


@session_group.command("delete")
@click.argument("session_id")
@click.option("--json", "json_output", is_flag=True)
@pass_state
def session_delete(state: CliState, session_id: str, json_output: bool) -> None:
    """Delete a session by ID."""
    if json_output:
        state.json_output = True

    from cli_anything.skyyrose_theme.core.session import delete_session

    deleted = delete_session(session_id)
    payload = {"ok": deleted, "session_id": session_id}
    if not state.json_output:
        if deleted:
            state.skin.success(f"Deleted session {session_id}")
        else:
            state.skin.warning(f"Session not found: {session_id}")
    emit(state, payload)


# ---------------------------------------------------------------------------
# repl command
# ---------------------------------------------------------------------------


@cli.command("repl")
@pass_state
def repl(state: CliState) -> None:
    """Launch interactive REPL (default mode when no subcommand given)."""
    from cli_anything.skyyrose_theme.core.session import (
        get_or_create_session, save_session)
    from cli_anything.skyyrose_theme.core.version import read_version
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory

    skin = state.skin

    # Read version for banner
    version_str = ""
    try:
        vs = read_version(state.theme_root)
        version_str = vs.functions_php if vs.consistent else "?"
    except Exception:
        pass

    skin.print_banner(version_str)

    session = get_or_create_session("default")
    pt_session: PromptSession = PromptSession(history=InMemoryHistory())

    while True:
        try:
            raw = pt_session.prompt(skin.prompt())
        except (EOFError, KeyboardInterrupt):
            save_session(session)
            skin.print_goodbye()
            break

        line = raw.strip()
        if not line:
            continue
        if line.lower() in ("exit", "quit", "q"):
            save_session(session)
            skin.print_goodbye()
            break
        if line.lower() in ("help", "?"):
            click.echo(cli.get_help(click.Context(cli)))
            continue

        session.add_history(line)

        # Dispatch the line as a CLI invocation
        args = line.split()
        try:
            standalone_mode_backup = cli.standalone_mode
            cli.standalone_mode = False
            cli.main(args, standalone_mode=False, obj=state)
        except SystemExit:
            pass
        except click.UsageError as exc:
            skin.error(str(exc))
        except Exception as exc:
            skin.error(str(exc))
        finally:
            cli.standalone_mode = True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
