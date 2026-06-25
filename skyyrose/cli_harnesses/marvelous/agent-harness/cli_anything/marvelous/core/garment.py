"""Garment domain model for Marvelous Designer projects.

Dataclasses representing garments, fabrics, and patterns as read from
.zpac/.zprj ZIP containers or populated at runtime.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FabricProperty:
    """Physical fabric properties used by MD simulation."""

    name: str
    texture_path: str = ""
    color_hex: str = "#FFFFFF"
    density: float = 0.3  # g/cm²
    thickness: float = 0.5  # mm
    stretch_weft: float = 50.0  # N/m
    stretch_warp: float = 50.0  # N/m
    shear_stiffness: float = 10.0
    bending_weft: float = 0.5
    bending_warp: float = 0.5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FabricProperty":
        valid = {k for k in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class PatternPiece:
    """A single 2D pattern piece within a garment."""

    name: str
    fabric_name: str = ""
    vertex_count: int = 0
    area_cm2: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatternPiece":
        valid = {k for k in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in valid})


@dataclass
class Garment:
    """Full garment definition — patterns + fabrics.

    This is the central domain object passed through commands and sessions.
    Populated by parsing a .zpac/.zprj file or constructed from user input.
    """

    name: str
    source_file: str = ""
    patterns: list[PatternPiece] = field(default_factory=list)
    fabrics: list[FabricProperty] = field(default_factory=list)
    simulation_frames: int = 100
    notes: str = ""

    @property
    def pattern_count(self) -> int:
        return len(self.patterns)

    @property
    def fabric_count(self) -> int:
        return len(self.fabrics)

    def fabric_by_name(self, name: str) -> FabricProperty | None:
        """Return fabric matching *name* (case-insensitive), or None."""
        nl = name.lower()
        return next((f for f in self.fabrics if f.name.lower() == nl), None)

    def pattern_by_name(self, name: str) -> PatternPiece | None:
        """Return pattern piece matching *name* (case-insensitive), or None."""
        nl = name.lower()
        return next((p for p in self.patterns if p.name.lower() == nl), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_file": self.source_file,
            "patterns": [p.to_dict() for p in self.patterns],
            "fabrics": [f.to_dict() for f in self.fabrics],
            "simulation_frames": self.simulation_frames,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Garment":
        patterns = [PatternPiece.from_dict(p) for p in data.get("patterns", [])]
        fabrics = [FabricProperty.from_dict(f) for f in data.get("fabrics", [])]
        return cls(
            name=data.get("name", "Untitled"),
            source_file=data.get("source_file", ""),
            patterns=patterns,
            fabrics=fabrics,
            simulation_frames=int(data.get("simulation_frames", 100)),
            notes=data.get("notes", ""),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Garment":
        return cls.from_dict(json.loads(text))
