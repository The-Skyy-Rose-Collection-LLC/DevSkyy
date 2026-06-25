"""doctor command — health check for auth, SDK, and optional deps."""

from __future__ import annotations

import json
import sys

import click

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("doctor", invoke_without_command=True, context_settings=CONTEXT_SETTINGS)
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """Check auth, SDK availability, and optional dependencies."""
    if ctx.invoked_subcommand is None:
        _run_doctor(ctx)


def _run_doctor(ctx: click.Context) -> None:
    state = ctx.obj
    results: dict = {}

    # 1. huggingface_hub availability
    try:
        import huggingface_hub

        hf_version = getattr(huggingface_hub, "__version__", "unknown")
        results["huggingface_hub"] = {"ok": True, "version": hf_version}
    except ImportError:
        results["huggingface_hub"] = {
            "ok": False,
            "error": "not installed — run: pip install huggingface_hub",
        }

    # 2. Auth token resolution
    try:
        from cli_anything.hf_spaces.utils.hf_backend import resolve_token

        token = resolve_token(state.token if state else None)
        if token:
            # Show only first 4 + last 4 chars for safety
            masked = token[:4] + "..." + token[-4:] if len(token) > 8 else "***"
            results["auth"] = {"ok": True, "token_source": _token_source(state), "masked": masked}
        else:
            results["auth"] = {
                "ok": False,
                "error": "No token found. Use --token, HF_TOKEN, or huggingface-cli login.",
            }
    except Exception as exc:
        results["auth"] = {"ok": False, "error": str(exc)}

    # 3. httpx (optional — for log streaming)
    try:
        import httpx

        results["httpx"] = {"ok": True, "version": getattr(httpx, "__version__", "unknown")}
    except ImportError:
        results["httpx"] = {
            "ok": False,
            "warning": "optional — log streaming unavailable. Install: pip install 'cli-anything-hf-spaces[logs]'",
        }

    # 4. prompt_toolkit (optional — for REPL)
    try:
        import prompt_toolkit

        results["prompt_toolkit"] = {
            "ok": True,
            "version": getattr(prompt_toolkit, "__version__", "unknown"),
        }
    except ImportError:
        results["prompt_toolkit"] = {
            "ok": False,
            "warning": "optional — REPL history/autocomplete unavailable. Install: pip install prompt-toolkit",
        }

    # 5. Factory reset notice
    results["factory_reset"] = {
        "ok": True,
        "note": "Factory reset is a web-UI only operation — not exposed by HfApi and not available in this CLI.",
    }

    # 6. Secrets API notice
    results["secrets_api"] = {
        "ok": True,
        "note": "HfApi does not support reading secret names or values (write-only by design). Use local manifests to track deployed secret keys.",
    }

    all_ok = all(
        v.get("ok", False)
        for k, v in results.items()
        if k not in ("factory_reset", "secrets_api", "httpx", "prompt_toolkit")
    )

    if state and state.json_output:
        click.echo(json.dumps({"ok": all_ok, "checks": results}, indent=2))
        if not all_ok:
            sys.exit(1)
        return

    click.echo()
    for check, info in results.items():
        ok = info.get("ok", False)
        icon = "✓" if ok else ("⚠" if "warning" in info else "✗")
        color_open = (
            "\033[38;5;78m" if ok else ("\033[38;5;220m" if "warning" in info else "\033[38;5;196m")
        )
        reset = "\033[0m"
        label = f"  {color_open}{icon}{reset} {check}"
        detail = (
            info.get("version") or info.get("note") or info.get("error") or info.get("warning", "")
        )
        click.echo(f"{label:<40} {detail}")
    click.echo()

    if not all_ok:
        sys.exit(1)


def _token_source(state) -> str:
    import os
    from pathlib import Path

    if state and state.token:
        return "--token flag"
    if os.environ.get("HF_TOKEN"):
        return "HF_TOKEN env"
    cache = Path.home() / ".cache" / "huggingface" / "token"
    if cache.exists():
        return str(cache)
    return "none"
