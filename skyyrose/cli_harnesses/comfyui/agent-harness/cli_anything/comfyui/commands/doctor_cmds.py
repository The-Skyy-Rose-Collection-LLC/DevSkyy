"""doctor command group — dependency and connectivity health check."""

from __future__ import annotations

import importlib
import json
import sys

import click
from cli_anything.comfyui.core.secrets import resolve_secrets
from cli_anything.comfyui.utils.repl_skin import ReplSkin

_REQUIRED_DEPS = ["click", "httpx"]
_OPTIONAL_DEPS = ["prompt_toolkit"]


def _check_import(module: str) -> tuple[bool, str]:
    """Return (ok, version_or_error)."""
    try:
        mod = importlib.import_module(module)
        version = getattr(mod, "__version__", "installed")
        return True, version
    except ImportError as exc:
        return False, str(exc)


@click.group("doctor")
def doctor() -> None:
    """Run health checks on dependencies and server connectivity."""


@doctor.command("check")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def doctor_check(host: str | None, token: str | None, json_out: bool) -> None:
    """Check required deps, optional deps, and server connectivity."""
    skin = ReplSkin(json_mode=json_out)
    checks: list[dict] = []
    all_ok = True

    # Required dependencies
    for dep in _REQUIRED_DEPS:
        ok, info = _check_import(dep)
        checks.append({"name": dep, "required": True, "ok": ok, "info": info})
        if not ok:
            all_ok = False

    # Optional dependencies
    for dep in _OPTIONAL_DEPS:
        ok, info = _check_import(dep)
        checks.append({"name": dep, "required": False, "ok": ok, "info": info})

    # Server connectivity
    secrets = resolve_secrets(host, token)
    server_ok = False
    server_info = ""
    try:
        import httpx

        resp = httpx.get(f"{secrets.base_url}/system_stats", timeout=5.0)
        server_ok = resp.status_code == 200
        server_info = f"HTTP {resp.status_code}"
    except Exception as exc:
        server_info = str(exc)

    checks.append(
        {
            "name": f"comfyui ({secrets.base_url})",
            "required": True,
            "ok": server_ok,
            "info": server_info,
        }
    )
    if not server_ok:
        all_ok = False

    if json_out:
        click.echo(json.dumps({"ok": all_ok, "checks": checks}, indent=2))
        if not all_ok:
            sys.exit(1)
        return

    skin.section("Doctor Check")
    for c in checks:
        req_tag = "[required]" if c["required"] else "[optional]"
        if c["ok"]:
            skin.success(f"{c['name']} {req_tag} — {c['info']}")
        elif c["required"]:
            skin.error(f"{c['name']} {req_tag} — {c['info']}")
        else:
            skin.warning(f"{c['name']} {req_tag} — {c['info']}")

    if all_ok:
        skin.success("All checks passed.")
    else:
        skin.error("One or more required checks failed.")
        sys.exit(1)


@doctor.command("deps")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def doctor_deps(json_out: bool) -> None:
    """Check only Python dependency availability (no server required)."""
    skin = ReplSkin(json_mode=json_out)
    checks: list[dict] = []
    all_ok = True

    for dep in _REQUIRED_DEPS:
        ok, info = _check_import(dep)
        checks.append({"name": dep, "required": True, "ok": ok, "info": info})
        if not ok:
            all_ok = False

    for dep in _OPTIONAL_DEPS:
        ok, info = _check_import(dep)
        checks.append({"name": dep, "required": False, "ok": ok, "info": info})

    if json_out:
        click.echo(json.dumps({"ok": all_ok, "checks": checks}, indent=2))
        if not all_ok:
            sys.exit(1)
        return

    skin.section("Dependency Check")
    for c in checks:
        req_tag = "[required]" if c["required"] else "[optional]"
        if c["ok"]:
            skin.success(f"{c['name']} {req_tag} — {c['info']}")
        elif c["required"]:
            skin.error(f"{c['name']} {req_tag} — {c['info']}")
        else:
            skin.warning(f"{c['name']} {req_tag} — {c['info']}")

    if not all_ok:
        sys.exit(1)
