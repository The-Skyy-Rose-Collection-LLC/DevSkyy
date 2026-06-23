"""cli_anything.comfyui.commands — Click command groups."""

from cli_anything.comfyui.commands.doctor_cmds import doctor
from cli_anything.comfyui.commands.history_cmds import history
from cli_anything.comfyui.commands.manifest_cmds import manifest
from cli_anything.comfyui.commands.models_cmds import models
from cli_anything.comfyui.commands.nodes_cmds import nodes
from cli_anything.comfyui.commands.queue_cmds import queue
from cli_anything.comfyui.commands.session_cmds import session
from cli_anything.comfyui.commands.system_cmds import system
from cli_anything.comfyui.commands.workflow_cmds import workflow

__all__ = [
    "doctor",
    "history",
    "manifest",
    "models",
    "nodes",
    "queue",
    "session",
    "system",
    "workflow",
]
