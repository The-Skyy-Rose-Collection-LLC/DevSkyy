"""ComfyUI history data model.

The /history endpoint returns a dict keyed by prompt_id.  Each value
contains the prompt spec, outputs, and status metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OutputFile:
    """A single output file referenced in a history item."""

    filename: str
    subfolder: str
    file_type: str  # "output", "input", "temp"

    def view_path(self) -> str:
        """URL path fragment for /view?filename=...&subfolder=...&type=..."""
        parts = [f"filename={self.filename}"]
        if self.subfolder:
            parts.append(f"subfolder={self.subfolder}")
        parts.append(f"type={self.file_type}")
        return "?" + "&".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "subfolder": self.subfolder,
            "type": self.file_type,
        }


@dataclass
class HistoryItem:
    """Parsed history entry for one completed prompt."""

    prompt_id: str
    status: str  # "success" | "error" | etc.
    outputs: dict[str, list[OutputFile]] = field(default_factory=dict)
    node_errors: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, prompt_id: str, entry: dict[str, Any]) -> "HistoryItem":
        """Parse a single history entry dict."""
        outputs: dict[str, list[OutputFile]] = {}
        for node_id, node_outputs in entry.get("outputs", {}).items():
            files: list[OutputFile] = []
            for img in node_outputs.get("images", []):
                files.append(
                    OutputFile(
                        filename=img.get("filename", ""),
                        subfolder=img.get("subfolder", ""),
                        file_type=img.get("type", "output"),
                    )
                )
            for vid in node_outputs.get("videos", []):
                files.append(
                    OutputFile(
                        filename=vid.get("filename", ""),
                        subfolder=vid.get("subfolder", ""),
                        file_type=vid.get("type", "output"),
                    )
                )
            if files:
                outputs[node_id] = files

        status_info = entry.get("status", {})
        status_str = (
            status_info.get("status_str", "unknown") if isinstance(status_info, dict) else "unknown"
        )
        node_errors = entry.get("node_errors", {})

        return cls(
            prompt_id=prompt_id,
            status=status_str,
            outputs=outputs,
            node_errors=node_errors,
            raw=entry,
        )

    def all_output_files(self) -> list[OutputFile]:
        """Flatten all output files across all nodes."""
        result: list[OutputFile] = []
        for files in self.outputs.values():
            result.extend(files)
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "status": self.status,
            "outputs": {nid: [f.to_dict() for f in files] for nid, files in self.outputs.items()},
            "node_errors": self.node_errors,
        }


def parse_history_response(data: dict[str, Any]) -> list[HistoryItem]:
    """Parse the full /history response dict into a list of :class:`HistoryItem`."""
    items: list[HistoryItem] = []
    for prompt_id, entry in data.items():
        if not isinstance(entry, dict):
            continue
        try:
            items.append(HistoryItem.from_dict(prompt_id, entry))
        except (KeyError, TypeError, ValueError):
            pass
    return items
