"""cli-anything-vercel-config — CLI harness for Vercel project settings.

Wraps the Vercel REST API for settings surfaces not covered by the official
``vercel`` CLI: project metadata, build config, env vars, custom domains,
deployment listing, runtime logs, and integrations.

Default mode: interactive REPL.  Pass a sub-command for one-shot use.

Usage::

    cli-anything-vercel-config                   # REPL
    cli-anything-vercel-config project show myproj
    cli-anything-vercel-config env list myproj
    cli-anything-vercel-config --json env list myproj

Auth::

    cli-anything-vercel-config --token <tok> project show myproj
    VERCEL_TOKEN=<tok> cli-anything-vercel-config project show myproj
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import click
from cli_anything.vercel_config import __version__
from cli_anything.vercel_config.utils.repl_skin import ReplSkin
from cli_anything.vercel_config.utils.vercel_backend import (
    VercelAuthError,
    VercelBackend,
    VercelBackendError,
    VercelNotFoundError,
    VercelRateLimitedError,
    VercelValidationError,
    _confirm,
    resolve_token,
)

# ── Shared context object ─────────────────────────────────────────────


class _Ctx:
    """Shared state threaded through Click's obj mechanism."""

    def __init__(
        self,
        token: str,
        team_id: Optional[str],
        as_json: bool,
        project: Optional[str] = None,
    ) -> None:
        self.token = token
        self.team_id = team_id
        self.as_json = as_json
        self.project = project
        self._backend: Optional[VercelBackend] = None

    def require_project(self, override: Optional[str] = None) -> str:
        """Resolve project id from override → ctx.project. Raise if missing."""
        chosen = override or self.project
        if not chosen:
            raise click.UsageError(
                "Project required. Pass --project <id_or_slug> at the root, "
                "or supply it positionally where supported."
            )
        return chosen

    @property
    def backend(self) -> VercelBackend:
        if self._backend is None:
            self._backend = VercelBackend(
                token=self.token,
                team_id=self.team_id,
            )
        return self._backend


def _get_ctx(ctx: click.Context) -> _Ctx:
    return ctx.obj  # type: ignore[return-value]


def _out(data: object, as_json: bool) -> None:
    """Print data as JSON or pretty text depending on flag."""
    if as_json:
        click.echo(json.dumps(data, indent=2))
    else:
        if isinstance(data, dict):
            for k, v in data.items():
                click.echo(f"  {k}: {v}")
        elif isinstance(data, list):
            for item in data:
                click.echo(f"  - {item}")
        else:
            click.echo(str(data))


def _handle_error(exc: Exception, as_json: bool) -> None:
    """Print a typed error and exit 1."""
    if as_json:
        error_type = type(exc).__name__
        click.echo(json.dumps({"error": error_type, "message": str(exc)}), err=True)
    else:
        click.echo(f"  Error: {exc}", err=True)
    sys.exit(1)


# ── Root group ────────────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.option(
    "--token",
    envvar="VERCEL_TOKEN",
    default=None,
    help="Vercel API token. Defaults to VERCEL_TOKEN env var or CLI auth.",
)
@click.option(
    "--team-id",
    envvar="VERCEL_TEAM_ID",
    default=None,
    help="Vercel team ID for team-scoped projects.",
)
@click.option(
    "--project",
    "project_opt",
    envvar="VERCEL_PROJECT",
    default=None,
    help="Default Vercel project id or slug for subcommands.",
)
@click.option(
    "--json", "as_json", is_flag=True, default=False, help="Output machine-readable JSON."
)
@click.version_option(__version__, prog_name="cli-anything-vercel-config")
@click.pass_context
def main(
    ctx: click.Context,
    token: Optional[str],
    team_id: Optional[str],
    project_opt: Optional[str],
    as_json: bool,
) -> None:
    """cli-anything-vercel-config — Vercel project settings CLI.

    Wraps the Vercel REST API for settings not covered by the official vercel CLI.

    Run without a sub-command to enter the interactive REPL.
    """
    try:
        resolved_token = resolve_token(token)
    except VercelAuthError as exc:
        if as_json:
            click.echo(json.dumps({"error": "VercelAuthError", "message": str(exc)}), err=True)
        else:
            click.echo(str(exc), err=True)
        sys.exit(1)

    ctx.obj = _Ctx(
        token=resolved_token,
        team_id=team_id,
        as_json=as_json,
        project=project_opt,
    )
    ctx.ensure_object(_Ctx)

    if ctx.invoked_subcommand is None:
        _run_repl(ctx.obj)


# ── Project commands ──────────────────────────────────────────────────


@main.group()
def project() -> None:
    """Manage Vercel project metadata and build config."""


@project.command("show")
@click.argument("project_id", required=False, default=None)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def project_show(ctx: click.Context, project_id: Optional[str], as_json_flag: bool) -> None:
    """Show project metadata for PROJECT_ID (id or slug)."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    try:
        pid = c.require_project(project_id)
        data = c.backend.get_project(pid)
        _out(data, as_json)
    except click.UsageError:
        raise
    except Exception as exc:
        _handle_error(exc, as_json)


@project.command("list")
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def project_list(ctx: click.Context, as_json_flag: bool) -> None:
    """List projects for the authenticated account / team."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    try:
        resp = c.backend._request("GET", "/v9/projects")
        projects = resp.get("projects", [])
        if as_json:
            click.echo(json.dumps(projects, indent=2))
        else:
            for p in projects:
                click.echo(f"  {p.get('name', '?')}  ({p.get('id', '?')})")
    except Exception as exc:
        _handle_error(exc, as_json)


@project.command("patch")
@click.argument("project_id", required=False, default=None)
@click.option(
    "--set",
    "kv_pairs",
    multiple=True,
    metavar="KEY=VALUE",
    help="Field to update (repeatable). E.g. --set framework=nextjs",
)
@click.option(
    "--confirm",
    "confirmed",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation prompt.",
)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def project_patch(
    ctx: click.Context,
    project_id: Optional[str],
    kv_pairs: tuple[str, ...],
    confirmed: bool,
    as_json_flag: bool,
) -> None:
    """Patch project build config fields for PROJECT_ID."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    pid = c.require_project(project_id)
    updates = {}
    for pair in kv_pairs:
        if "=" not in pair:
            click.echo(f"  Invalid --set value (expected KEY=VALUE): {pair!r}", err=True)
            sys.exit(1)
        k, v = pair.split("=", 1)
        updates[k.strip()] = v.strip()

    if not updates:
        click.echo("  No --set values provided.", err=True)
        sys.exit(1)

    if not confirmed:
        payload_display = {k: v for k, v in updates.items()}
        if not _confirm("PATCH project", pid, payload_display):
            click.echo("  Aborted.")
            return

    try:
        result = c.backend.patch_project(pid, updates)
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"  Updated project {pid}")
    except Exception as exc:
        _handle_error(exc, as_json)


# ── Env var commands ──────────────────────────────────────────────────


@main.group()
def env() -> None:
    """Manage environment variables for a Vercel project."""


@env.command("list")
@click.argument("project_id", required=False, default=None)
@click.option(
    "--reveal", is_flag=True, default=False, help="Show decrypted values (requires --reveal flag)."
)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def env_list(
    ctx: click.Context,
    project_id: Optional[str],
    reveal: bool,
    as_json_flag: bool,
) -> None:
    """List environment variables for PROJECT_ID (or --project from root)."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    try:
        pid = c.require_project(project_id)
        records = c.backend.list_env_vars(pid)
        if as_json:
            if not reveal:
                records = [{**r, "value": "***"} for r in records]
            click.echo(json.dumps(records, indent=2))
        else:
            from cli_anything.vercel_config.core.env_vars import EnvVar

            for r in records:
                ev = EnvVar.from_api(r)
                val = ev.display_value(reveal=reveal)
                targets = ",".join(sorted(ev.targets))
                click.echo(f"  {ev.key:<40} [{targets}]  {val}")
    except click.UsageError:
        raise
    except Exception as exc:
        _handle_error(exc, as_json)


@env.command("get")
@click.argument("env_id")
@click.option("--project", "project_override", default=None)
@click.option("--reveal", is_flag=True, default=False, help="Show decrypted value.")
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def env_get(
    ctx: click.Context,
    env_id: str,
    project_override: Optional[str],
    reveal: bool,
    as_json_flag: bool,
) -> None:
    """Get a single env var by ENV_ID (Vercel-assigned ID)."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    try:
        pid = c.require_project(project_override)
        record = c.backend.decrypt_env_var(pid, env_id)
        if not reveal and "value" in record:
            record = {**record, "value": "***"}
        _out(record, as_json)
    except click.UsageError:
        raise
    except Exception as exc:
        _handle_error(exc, as_json)


@env.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--project", "project_override", default=None)
@click.option(
    "--target",
    multiple=True,
    default=["production"],
    show_default=True,
    help="Deployment target (production/preview/development). Repeatable.",
)
@click.option(
    "--type",
    "env_type",
    default="plain",
    show_default=True,
    type=click.Choice(["plain", "secret", "encrypted", "sensitive"]),
    help="Env var type.",
)
@click.option("--git-branch", default=None, help="Git branch for branch-specific preview vars.")
@click.option(
    "--confirm",
    "confirmed",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation prompt.",
)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def env_set(
    ctx: click.Context,
    key: str,
    value: str,
    project_override: Optional[str],
    target: tuple[str, ...],
    env_type: str,
    git_branch: Optional[str],
    confirmed: bool,
    as_json_flag: bool,
) -> None:
    """Set (create or update) an environment variable KEY=VALUE."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    pid = c.require_project(project_override)

    if not confirmed:
        targets_str = ",".join(sorted(target))
        if not _confirm(
            "SET env var",
            f"{key} [{targets_str}] on {pid}",
            {"type": env_type, "value": "***"},
        ):
            click.echo("  Aborted.")
            return

    from cli_anything.vercel_config.core.env_vars import EnvVar

    ev = EnvVar(
        key=key,
        value=value,
        env_type=env_type,
        targets=list(target),
        git_branch=git_branch,
    )
    try:
        result = c.backend.create_env_var(pid, ev.to_create_payload())
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"  Set {key} on {pid}")
    except Exception as exc:
        _handle_error(exc, as_json)


@env.command("remove")
@click.argument("env_id")
@click.option("--project", "project_override", default=None)
@click.option(
    "--confirm",
    "confirmed",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation prompt.",
)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def env_remove(
    ctx: click.Context,
    env_id: str,
    project_override: Optional[str],
    confirmed: bool,
    as_json_flag: bool,
) -> None:
    """Remove an env var by ENV_ID."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    pid = c.require_project(project_override)
    if not confirmed:
        if not _confirm("DELETE env var", f"{env_id} from {pid}"):
            click.echo("  Aborted.")
            return
    try:
        c.backend.delete_env_var(pid, env_id)
        if as_json:
            click.echo(json.dumps({"deleted": env_id}))
        else:
            click.echo(f"  Removed env var {env_id} from {pid}")
    except Exception as exc:
        _handle_error(exc, as_json)


# ── Domain commands ───────────────────────────────────────────────────


@main.group()
def domain() -> None:
    """Manage custom domains for a Vercel project."""


@domain.command("list")
@click.argument("project_id", required=False, default=None)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def domain_list(ctx: click.Context, project_id: Optional[str], as_json_flag: bool) -> None:
    """List custom domains for PROJECT_ID (or --project from root)."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    try:
        pid = c.require_project(project_id)
        records = c.backend.list_domains(pid)
        if as_json:
            click.echo(json.dumps(records, indent=2))
        else:
            from cli_anything.vercel_config.core.domains import Domain

            for r in records:
                d = Domain.from_api(r)
                verified = "✓" if d.verified else "✗"
                redirect = f" → {d.redirect}" if d.redirect else ""
                click.echo(f"  {verified} {d.name}{redirect}")
    except click.UsageError:
        raise
    except Exception as exc:
        _handle_error(exc, as_json)


@domain.command("add")
@click.argument("hostname")
@click.option("--project", "project_override", default=None)
@click.option("--redirect", default=None, help="Redirect target hostname.")
@click.option("--git-branch", default=None, help="Scope domain to git branch.")
@click.option("--confirm", "confirmed", is_flag=True, default=False)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def domain_add(
    ctx: click.Context,
    hostname: str,
    project_override: Optional[str],
    redirect: Optional[str],
    git_branch: Optional[str],
    confirmed: bool,
    as_json_flag: bool,
) -> None:
    """Add HOSTNAME to the active project."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    pid = c.require_project(project_override)
    if not confirmed:
        payload_display = {}
        if redirect:
            payload_display["redirect"] = redirect
        if git_branch:
            payload_display["gitBranch"] = git_branch
        if not _confirm("ADD domain", f"{hostname} to {pid}", payload_display or None):
            click.echo("  Aborted.")
            return

    from cli_anything.vercel_config.core.domains import Domain

    dom = Domain(name=hostname, redirect=redirect, git_branch=git_branch)
    try:
        result = c.backend.add_domain(pid, dom.to_add_payload())
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"  Added {hostname} to {pid}")
    except Exception as exc:
        _handle_error(exc, as_json)


@domain.command("remove")
@click.argument("hostname")
@click.option("--project", "project_override", default=None)
@click.option("--confirm", "confirmed", is_flag=True, default=False)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def domain_remove(
    ctx: click.Context,
    hostname: str,
    project_override: Optional[str],
    confirmed: bool,
    as_json_flag: bool,
) -> None:
    """Remove HOSTNAME from the active project."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    pid = c.require_project(project_override)
    if not confirmed:
        if not _confirm("REMOVE domain", f"{hostname} from {pid}"):
            click.echo("  Aborted.")
            return
    try:
        c.backend.remove_domain(pid, hostname)
        if as_json:
            click.echo(json.dumps({"removed": hostname}))
        else:
            click.echo(f"  Removed {hostname} from {pid}")
    except Exception as exc:
        _handle_error(exc, as_json)


@domain.command("redirect")
@click.argument("hostname")
@click.argument("redirect_to")
@click.option("--project", "project_override", default=None)
@click.option("--confirm", "confirmed", is_flag=True, default=False)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def domain_redirect(
    ctx: click.Context,
    hostname: str,
    redirect_to: str,
    project_override: Optional[str],
    confirmed: bool,
    as_json_flag: bool,
) -> None:
    """Set redirect on HOSTNAME to REDIRECT_TO."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    pid = c.require_project(project_override)
    if not confirmed:
        if not _confirm(
            "SET domain redirect",
            f"{hostname} → {redirect_to} on {pid}",
        ):
            click.echo("  Aborted.")
            return
    try:
        result = c.backend.update_domain(pid, hostname, {"redirect": redirect_to})
        if as_json:
            click.echo(json.dumps(result, indent=2))
        else:
            click.echo(f"  Set {hostname} → {redirect_to}")
    except Exception as exc:
        _handle_error(exc, as_json)


# ── Deployment commands ───────────────────────────────────────────────


@main.group()
def deployment() -> None:
    """List deployments and view runtime logs."""


@deployment.command("list")
@click.option(
    "--project",
    "project_override",
    default=None,
    help="Filter by project ID (overrides root --project).",
)
@click.option("--limit", default=20, show_default=True, help="Number of deployments to return.")
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def deployment_list(
    ctx: click.Context,
    project_override: Optional[str],
    limit: int,
    as_json_flag: bool,
) -> None:
    """List recent deployments."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    pid = project_override or c.project
    try:
        records = c.backend.list_deployments(project_id=pid, limit=limit)
        if as_json:
            click.echo(json.dumps(records, indent=2))
        else:
            for d in records:
                uid = d.get("uid", "?")
                url = d.get("url", "")
                state = d.get("state", "?")
                created = d.get("created", "")
                click.echo(f"  {uid:<30} {state:<12} {url}  {created}")
    except Exception as exc:
        _handle_error(exc, as_json)


@deployment.command("logs")
@click.argument("deployment_id")
@click.option("--limit", default=100, show_default=True, help="Number of log events to return.")
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def deployment_logs(ctx: click.Context, deployment_id: str, limit: int, as_json_flag: bool) -> None:
    """Show runtime logs for DEPLOYMENT_ID."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    try:
        events = c.backend.get_deployment_events(deployment_id, limit=limit)
        if as_json:
            click.echo(json.dumps(events, indent=2))
        else:
            for ev in events:
                ts = ev.get("created", "")
                text = ev.get("text", ev.get("payload", {}).get("text", ""))
                click.echo(f"  [{ts}] {text}")
    except Exception as exc:
        _handle_error(exc, as_json)


# ── Integration commands ──────────────────────────────────────────────


@main.group()
def integration() -> None:
    """List Vercel integration configurations."""


@integration.command("list")
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def integration_list(ctx: click.Context, as_json_flag: bool) -> None:
    """List all integration configurations for the account/team."""
    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    try:
        records = c.backend.list_integrations()
        if as_json:
            click.echo(json.dumps(records, indent=2))
        else:
            for r in records:
                iid = r.get("id", "?")
                slug = r.get("integrationSlug", r.get("slug", "?"))
                click.echo(f"  {iid:<40} {slug}")
    except Exception as exc:
        _handle_error(exc, as_json)


# ── Manifest commands ─────────────────────────────────────────────────


@main.group()
def manifest() -> None:
    """Declarative project settings via vercel-config.json manifest."""


@manifest.command("plan")
@click.option(
    "--file",
    "manifest_file",
    default="vercel-config.json",
    show_default=True,
    help="Path to manifest JSON file.",
)
@click.pass_context
def manifest_plan(ctx: click.Context, manifest_file: str) -> None:
    """Show diff between manifest and live Vercel project state."""
    from pathlib import Path

    from cli_anything.vercel_config.core.domains import Domain
    from cli_anything.vercel_config.core.env_vars import EnvVar
    from cli_anything.vercel_config.core.manifest import build_plan, load_manifest

    c = _get_ctx(ctx)
    try:
        mf = load_manifest(Path(manifest_file))
    except (FileNotFoundError, ValueError) as exc:
        _handle_error(exc, c.as_json)
        return

    try:
        actual_project = c.backend.get_project(mf.project)
        raw_envs = c.backend.list_env_vars(mf.project)
        actual_envs = [EnvVar.from_api(r) for r in raw_envs]
        raw_domains = c.backend.list_domains(mf.project)
        actual_domains = [Domain.from_api(r) for r in raw_domains]
    except Exception as exc:
        _handle_error(exc, c.as_json)
        return

    plan = build_plan(mf, actual_project, actual_envs, actual_domains)

    if c.as_json:
        click.echo(json.dumps(plan.to_dict(), indent=2))
        return

    if not plan.has_changes:
        click.echo("  No changes. Project matches manifest.")
        return

    if plan.project_patch:
        click.echo("\n  Project patch:")
        for k, v in plan.project_patch.items():
            click.echo(f"    ~ {k}: {v}")

    if plan.env_changes:
        click.echo("\n  Env var changes:")
        for d in plan.env_changes:
            targets = ",".join(d.targets)
            click.echo(f"    {d.action:<8} {d.key} [{targets}]")

    if plan.domain_changes:
        click.echo("\n  Domain changes:")
        for d in plan.domain_changes:
            click.echo(f"    {d.action:<8} {d.name}")


@manifest.command("apply")
@click.option("--file", "manifest_file", default="vercel-config.json", show_default=True)
@click.option(
    "--confirm",
    "confirmed",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation prompt.",
)
@click.pass_context
def manifest_apply(ctx: click.Context, manifest_file: str, confirmed: bool) -> None:
    """Apply manifest changes to the live Vercel project."""
    from pathlib import Path

    from cli_anything.vercel_config.core.domains import Domain
    from cli_anything.vercel_config.core.env_vars import EnvVar
    from cli_anything.vercel_config.core.manifest import build_plan, load_manifest

    c = _get_ctx(ctx)
    try:
        mf = load_manifest(Path(manifest_file))
    except (FileNotFoundError, ValueError) as exc:
        _handle_error(exc, c.as_json)
        return

    try:
        actual_project = c.backend.get_project(mf.project)
        raw_envs = c.backend.list_env_vars(mf.project)
        actual_envs = [EnvVar.from_api(r) for r in raw_envs]
        raw_domains = c.backend.list_domains(mf.project)
        actual_domains = [Domain.from_api(r) for r in raw_domains]
    except Exception as exc:
        _handle_error(exc, c.as_json)
        return

    plan = build_plan(mf, actual_project, actual_envs, actual_domains)

    if not plan.has_changes:
        click.echo("  No changes. Project already matches manifest.")
        return

    if not confirmed:
        summary = {
            "project": mf.project,
            "envChanges": len(plan.env_changes),
            "domainChanges": len(plan.domain_changes),
            "projectPatchFields": len(plan.project_patch),
        }
        if not _confirm("APPLY manifest", manifest_file, summary):
            click.echo("  Aborted.")
            return

    errors = []

    # Apply project patch
    if plan.project_patch:
        try:
            c.backend.patch_project(mf.project, plan.project_patch)
            if not c.as_json:
                click.echo(f"  Patched project {mf.project}")
        except Exception as exc:
            errors.append(f"project patch: {exc}")

    # Apply env var changes
    for d in plan.env_changes:
        try:
            if d.action == "add" and d.desired:
                c.backend.create_env_var(mf.project, d.desired.to_create_payload())
            elif d.action == "update" and d.desired and d.current and d.current.id:
                c.backend.update_env_var(mf.project, d.current.id, d.desired.to_update_payload())
            elif d.action == "remove" and d.current and d.current.id:
                c.backend.delete_env_var(mf.project, d.current.id)
            if not c.as_json:
                click.echo(f"  {d.action:<8} env {d.key}")
        except Exception as exc:
            errors.append(f"env {d.key}: {exc}")

    # Apply domain changes
    for d in plan.domain_changes:
        try:
            if d.action == "add" and d.desired:
                c.backend.add_domain(mf.project, d.desired.to_add_payload())
            elif d.action == "update" and d.desired:
                c.backend.update_domain(mf.project, d.name, d.desired.to_update_payload())
            elif d.action == "remove":
                c.backend.remove_domain(mf.project, d.name)
            if not c.as_json:
                click.echo(f"  {d.action:<8} domain {d.name}")
        except Exception as exc:
            errors.append(f"domain {d.name}: {exc}")

    if c.as_json:
        click.echo(
            json.dumps(
                {
                    "applied": True,
                    "errors": errors,
                },
                indent=2,
            )
        )
    elif errors:
        click.echo(f"\n  {len(errors)} error(s):")
        for e in errors:
            click.echo(f"    ✗ {e}", err=True)
        sys.exit(1)
    else:
        click.echo("  Done.")


# ── Doctor command ────────────────────────────────────────────────────


@main.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Run connectivity and auth checks against the Vercel API."""
    c = _get_ctx(ctx)
    checks = {}

    # Auth check
    try:
        resp = c.backend._request("GET", "/v2/user")
        username = resp.get("user", {}).get("username", "?")
        checks["auth"] = f"OK — logged in as {username}"
    except VercelAuthError as exc:
        checks["auth"] = f"FAIL — {exc}"
    except Exception as exc:
        checks["auth"] = f"FAIL — {exc}"

    # Team check
    if c.team_id:
        try:
            resp = c.backend._request("GET", f"/v2/teams/{c.team_id}")
            name = resp.get("name", "?")
            checks["team"] = f"OK — {name}"
        except Exception as exc:
            checks["team"] = f"FAIL — {exc}"

    if c.as_json:
        click.echo(json.dumps(checks, indent=2))
    else:
        for label, result in checks.items():
            icon = "✓" if result.startswith("OK") else "✗"
            click.echo(f"  {icon} {label}: {result}")


# ── Session commands ──────────────────────────────────────────────────


@main.group()
def session() -> None:
    """Manage saved REPL sessions."""


@session.command("status")
@click.argument("name")
@click.pass_context
def session_status(ctx: click.Context, name: str) -> None:
    """Show details of a saved session by NAME."""
    from cli_anything.vercel_config.core import session as sess_mod

    c = _get_ctx(ctx)
    try:
        s = sess_mod.load(name)
        _out(s.to_dict(), c.as_json)
    except FileNotFoundError as exc:
        _handle_error(exc, c.as_json)


@session.command("save")
@click.option("--name", required=True, help="Session name.")
@click.option(
    "--project",
    "project_override",
    default=None,
    help="Project id or slug (defaults to root --project).",
)
@click.option("--team-id", default=None)
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def session_save(
    ctx: click.Context,
    name: str,
    project_override: Optional[str],
    team_id: Optional[str],
    as_json_flag: bool,
) -> None:
    """Save a session NAME pointing at the active project."""
    from cli_anything.vercel_config.core import session as sess_mod

    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    pid = c.require_project(project_override)
    s = sess_mod.Session(name=name, project=pid, team_id=team_id or c.team_id)
    path = sess_mod.save(s)
    if as_json:
        click.echo(json.dumps({"saved": name, "path": str(path)}))
    else:
        click.echo(f"  Saved session {name!r} → {path}")


@session.command("list")
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def session_list(ctx: click.Context, as_json_flag: bool) -> None:
    """List all saved sessions."""
    from cli_anything.vercel_config.core import session as sess_mod

    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    sessions = sess_mod.list_sessions()
    if as_json:
        click.echo(json.dumps([s.to_dict() for s in sessions], indent=2))
    else:
        if not sessions:
            click.echo("  No saved sessions.")
            return
        for s in sessions:
            click.echo(f"  {s.name:<30} {s.project}  (updated {s.updated_at})")


@session.command("delete")
@click.argument("name")
@click.option("--json", "as_json_flag", is_flag=True, default=False)
@click.pass_context
def session_delete(ctx: click.Context, name: str, as_json_flag: bool) -> None:
    """Delete saved session NAME.

    Sessions are local files only; no remote state is touched, so no --confirm gate.
    """
    from cli_anything.vercel_config.core import session as sess_mod

    c = _get_ctx(ctx)
    as_json = as_json_flag or c.as_json
    deleted = sess_mod.delete(name)
    if as_json:
        click.echo(json.dumps({"deleted": deleted, "name": name}))
    else:
        if deleted:
            click.echo(f"  Deleted session {name!r}")
        else:
            click.echo(f"  Session {name!r} not found.")


# ── REPL command ──────────────────────────────────────────────────────


@main.command()
@click.pass_context
def repl(ctx: click.Context) -> None:
    """Enter the interactive REPL."""
    _run_repl(_get_ctx(ctx))


# ── REPL implementation ───────────────────────────────────────────────


def _run_repl(app_ctx: _Ctx) -> None:
    """Run the interactive REPL loop."""
    skin = ReplSkin("vercel_config", version=__version__)
    skin.print_banner()
    pt_session = skin.create_prompt_session()

    current_project: Optional[str] = None

    while True:
        try:
            line = skin.get_input(
                pt_session,
                project_name=current_project or "",
                context=current_project or "",
            )
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        if not line:
            continue

        if line in ("quit", "exit", "q"):
            skin.print_goodbye()
            break

        if line in ("help", "?"):
            skin.help(
                {
                    "project show <id>": "Show project metadata",
                    "project list": "List all projects",
                    "project patch <id>": "Patch project fields",
                    "env list <id>": "List env vars",
                    "env set <id> K V": "Set env var",
                    "env remove <id> eid": "Remove env var",
                    "domain list <id>": "List domains",
                    "domain add <id> host": "Add domain",
                    "domain remove <id> h": "Remove domain",
                    "deployment list": "List deployments",
                    "deployment logs <id>": "Show deployment logs",
                    "integration list": "List integrations",
                    "manifest plan": "Show manifest diff",
                    "manifest apply": "Apply manifest",
                    "doctor": "Auth + connectivity check",
                    "session list": "List saved sessions",
                    "quit": "Exit REPL",
                }
            )
            continue

        # Parse and dispatch via Click's standalone_mode=False
        args = line.split()
        try:
            result = main.main(
                args=args,
                standalone_mode=False,
                obj=app_ctx,
            )
            if result is not None and result != 0:
                skin.error(f"Command returned: {result}")
        except SystemExit:
            pass
        except click.ClickException as exc:
            skin.error(exc.format_message())
        except click.Abort:
            skin.warning("Aborted.")
        except Exception as exc:
            skin.error(str(exc))


if __name__ == "__main__":
    main()
