"""ComfyUI workflow data model.

A workflow is a JSON dict that ComfyUI calls a *prompt* — a mapping of
node-id strings to node-specification dicts.  This module provides:

- :class:`NodeInfo` — lightweight wrapper around a single node spec
- :class:`Workflow` — parsed workflow with validation and inspection helpers
- :func:`load_workflow` / :func:`dump_workflow` — JSON file I/O
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_NODE_ID_RE = re.compile(r"^\d+$")


@dataclass
class NodeInfo:
    """Single node extracted from a ComfyUI workflow prompt."""

    node_id: str
    class_type: str
    inputs: dict[str, Any]

    @classmethod
    def from_dict(cls, node_id: str, spec: dict[str, Any]) -> "NodeInfo":
        if "class_type" not in spec:
            raise ValueError(f"Node {node_id!r} missing 'class_type'")
        return cls(
            node_id=node_id,
            class_type=spec["class_type"],
            inputs=spec.get("inputs", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "class_type": self.class_type,
            "inputs": self.inputs,
        }

    def upstream_ids(self) -> list[str]:
        """Return node IDs referenced by list-typed input values [id, slot]."""
        ids: list[str] = []
        for v in self.inputs.values():
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
                ids.append(v[0])
        return ids


@dataclass
class Workflow:
    """Parsed ComfyUI workflow (prompt dict)."""

    nodes: dict[str, NodeInfo] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # construction
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Workflow":
        """Parse a raw workflow dict into a :class:`Workflow`."""
        nodes: dict[str, NodeInfo] = {}
        for node_id, spec in data.items():
            if not isinstance(spec, dict):
                raise ValueError(
                    f"Node {node_id!r} value must be a dict, got {type(spec).__name__}"
                )
            nodes[node_id] = NodeInfo.from_dict(node_id, spec)
        return cls(nodes=nodes, raw=data)

    @classmethod
    def from_json_string(cls, text: str) -> "Workflow":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Workflow must be a JSON object, got {type(data).__name__}")
        return cls.from_dict(data)

    # ------------------------------------------------------------------
    # serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {nid: node.to_dict() for nid, node in self.nodes.items()}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    # ------------------------------------------------------------------
    # inspection
    # ------------------------------------------------------------------

    def node_ids(self) -> list[str]:
        return list(self.nodes.keys())

    def class_types(self) -> set[str]:
        return {n.class_type for n in self.nodes.values()}

    def find_by_class(self, class_type: str) -> list[NodeInfo]:
        return [n for n in self.nodes.values() if n.class_type == class_type]

    def validate(self) -> list[str]:
        """Return a list of validation error strings (empty = valid)."""
        errors: list[str] = []
        for nid, node in self.nodes.items():
            for ref in node.upstream_ids():
                if ref not in self.nodes:
                    errors.append(f"Node {nid!r} references unknown node {ref!r}")
        return errors

    def summary(self) -> dict[str, Any]:
        return {
            "node_count": len(self.nodes),
            "class_types": sorted(self.class_types()),
            "node_ids": self.node_ids(),
        }


# ---------------------------------------------------------------------------
# file I/O
# ---------------------------------------------------------------------------


def load_workflow(path: Path | str) -> Workflow:
    """Load and parse a workflow JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Workflow file not found: {p}")
    text = p.read_text(encoding="utf-8")
    return Workflow.from_json_string(text)


def dump_workflow(workflow: Workflow, path: Path | str, indent: int = 2) -> None:
    """Write a workflow to a JSON file (overwrites if exists)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(workflow.to_json(indent=indent), encoding="utf-8")
