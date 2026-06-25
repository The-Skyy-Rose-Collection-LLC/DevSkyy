"""models command group — model listing by type."""

from __future__ import annotations

import json
import sys

import click
from cli_anything.comfyui.core.secrets import resolve_secrets
from cli_anything.comfyui.utils.comfyui_backend import ComfyUIBackend, ComfyUIBackendError
from cli_anything.comfyui.utils.repl_skin import ReplSkin

_MODEL_TYPES = [
    "checkpoints",
    "loras",
    "vae",
    "controlnet",
    "embeddings",
    "hypernetworks",
    "upscale_models",
    "clip",
    "clip_vision",
    "diffusers",
    "gligen",
    "style_models",
    "unet",
]


@click.group("models")
def models() -> None:
    """List and inspect ComfyUI models."""


@models.command("list")
@click.argument("model_type", default="checkpoints")
@click.option("--host", envvar="COMFYUI_HOST", default=None, help="ComfyUI base URL")
@click.option("--token", envvar="COMFYUI_AUTH_TOKEN", default=None, help="Bearer token")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def models_list(model_type: str, host: str | None, token: str | None, json_out: bool) -> None:
    """List models of MODEL_TYPE from /models/{model_type}.

    MODEL_TYPE defaults to 'checkpoints'.  Common values: checkpoints,
    loras, vae, controlnet, embeddings, hypernetworks, upscale_models.
    """
    skin = ReplSkin(json_mode=json_out)
    secrets = resolve_secrets(host, token)
    backend = ComfyUIBackend(base_url=secrets.base_url, auth_headers=secrets.auth_headers())
    try:
        data = backend.models(model_type)
    except ComfyUIBackendError as exc:
        if json_out:
            click.echo(json.dumps({"error": str(exc)}))
        else:
            skin.error(str(exc))
        sys.exit(1)

    if json_out:
        click.echo(json.dumps(data, indent=2))
        return

    skin.section(f"Models / {model_type} ({len(data)})")
    if not data:
        skin.hint("No models found.")
        return
    for name in sorted(data):
        click.echo(f"  {name}")


@models.command("types")
@click.option("--json", "json_out", is_flag=True, help="Output raw JSON")
def models_types(json_out: bool) -> None:
    """List well-known model type names (no server required)."""
    if json_out:
        click.echo(json.dumps(_MODEL_TYPES, indent=2))
        return
    skin = ReplSkin()
    skin.section("Known Model Types")
    for t in _MODEL_TYPES:
        click.echo(f"  {t}")
