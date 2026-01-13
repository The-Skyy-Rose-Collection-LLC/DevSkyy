"""
MCP Tool Catalog Generator
===========================

Generates multi-format tool catalogs from MCP server definitions.

Features:
- Unified tool registry across all servers
- Export to OpenAI, Anthropic, MCP, Markdown, JSON formats
- Automatic changelog generation
- Schema validation and compatibility checks
- Tool deduplication and conflict detection

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ExportFormat(str, Enum):
    """Supported export formats."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MCP = "mcp"
    MARKDOWN = "markdown"
    JSON = "json"


class ToolCategory(str, Enum):
    """Tool categories for organization."""

    CONTENT = "content"
    COMMERCE = "commerce"
    MEDIA = "media"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    INTEGRATION = "integration"
    SYSTEM = "system"
    AI = "ai"
    OPERATIONS = "operations"
    SECURITY = "security"


class ToolSeverity(str, Enum):
    """Tool severity levels for permission management."""

    READ_ONLY = "read_only"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    DESTRUCTIVE = "destructive"


# =============================================================================
# Models
# =============================================================================


class ToolMetadata(BaseModel):
    """Metadata about a tool."""

    model_config = {"extra": "forbid"}

    # Identity
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    server_id: str = Field(..., description="Source MCP server")

    # Classification
    category: ToolCategory = Field(default=ToolCategory.SYSTEM)
    severity: ToolSeverity = Field(default=ToolSeverity.MEDIUM)
    tags: list[str] = Field(default_factory=list)

    # Schema
    input_schema: dict[str, Any] = Field(..., description="JSON Schema for inputs")
    output_schema: dict[str, Any] | None = Field(default=None)

    # Permissions & Features
    required_permissions: list[str] = Field(default_factory=list)
    read_only: bool = Field(default=False)
    idempotent: bool = Field(default=False)

    # Metadata
    version: str = Field(default="1.0.0")
    deprecated: bool = Field(default=False)
    deprecation_message: str | None = Field(default=None)


@dataclass
class ToolConflict:
    """Represents a conflict between tools."""

    tool_name: str
    server_ids: list[str]
    conflict_type: str  # "duplicate_name", "schema_mismatch", "version_conflict"
    details: str


@dataclass
class CatalogStats:
    """Statistics about the tool catalog."""

    total_tools: int = 0
    total_servers: int = 0
    tools_by_category: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    tools_by_severity: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    conflicts: list[ToolConflict] = field(default_factory=list)
    deprecated_tools: int = 0


# =============================================================================
# Unified Tool Registry
# =============================================================================


class UnifiedToolRegistry:
    """
    Unified registry for all MCP tools across servers.

    Usage:
        registry = UnifiedToolRegistry()
        registry.register_tool(tool_metadata)
        tools = registry.get_tools_by_category(ToolCategory.COMMERCE)
        conflicts = registry.detect_conflicts()
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolMetadata] = {}
        self._tools_by_server: dict[str, list[str]] = defaultdict(list)
        self._tools_by_category: dict[ToolCategory, list[str]] = defaultdict(list)

    # -------------------------------------------------------------------------
    # Registration
    # -------------------------------------------------------------------------

    def register_tool(self, tool: ToolMetadata) -> None:
        """Register a tool in the unified registry."""
        # Check for duplicates
        if tool.name in self._tools:
            existing = self._tools[tool.name]
            if existing.server_id != tool.server_id:
                logger.warning(
                    f"Tool '{tool.name}' already registered from server "
                    f"'{existing.server_id}', now also from '{tool.server_id}'"
                )

        self._tools[tool.name] = tool
        self._tools_by_server[tool.server_id].append(tool.name)
        self._tools_by_category[tool.category].append(tool.name)

        logger.info(f"Registered tool: {tool.name} (server: {tool.server_id})")

    def register_tools(self, tools: list[ToolMetadata]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)

    def unregister_tool(self, tool_name: str) -> None:
        """Unregister a tool."""
        if tool_name not in self._tools:
            return

        tool = self._tools.pop(tool_name)
        self._tools_by_server[tool.server_id].remove(tool_name)
        self._tools_by_category[tool.category].remove(tool_name)

    # -------------------------------------------------------------------------
    # Retrieval
    # -------------------------------------------------------------------------

    def get_tool(self, tool_name: str) -> ToolMetadata | None:
        """Get tool by name."""
        return self._tools.get(tool_name)

    def get_all_tools(self) -> list[ToolMetadata]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_tools_by_server(self, server_id: str) -> list[ToolMetadata]:
        """Get all tools from a specific server."""
        tool_names = self._tools_by_server.get(server_id, [])
        return [self._tools[name] for name in tool_names]

    def get_tools_by_category(self, category: ToolCategory) -> list[ToolMetadata]:
        """Get all tools in a category."""
        tool_names = self._tools_by_category.get(category, [])
        return [self._tools[name] for name in tool_names]

    def get_tools_by_severity(self, severity: ToolSeverity) -> list[ToolMetadata]:
        """Get all tools with a specific severity."""
        return [tool for tool in self._tools.values() if tool.severity == severity]

    def search_tools(self, query: str) -> list[ToolMetadata]:
        """Search tools by name or description."""
        query_lower = query.lower()
        return [
            tool
            for tool in self._tools.values()
            if query_lower in tool.name.lower() or query_lower in tool.description.lower()
        ]

    # -------------------------------------------------------------------------
    # Conflict Detection
    # -------------------------------------------------------------------------

    def detect_conflicts(self) -> list[ToolConflict]:
        """Detect conflicts between tools."""
        conflicts = []

        # Group tools by name
        tools_by_name: dict[str, list[ToolMetadata]] = defaultdict(list)
        for tool in self._tools.values():
            tools_by_name[tool.name].append(tool)

        # Check for duplicates and schema mismatches
        for tool_name, tools in tools_by_name.items():
            if len(tools) > 1:
                server_ids = [t.server_id for t in tools]

                # Check if schemas match
                schemas = [self._normalize_schema(t.input_schema) for t in tools]
                if len(set(schemas)) > 1:
                    conflicts.append(
                        ToolConflict(
                            tool_name=tool_name,
                            server_ids=server_ids,
                            conflict_type="schema_mismatch",
                            details=f"Tool '{tool_name}' has different schemas across servers",
                        )
                    )
                else:
                    conflicts.append(
                        ToolConflict(
                            tool_name=tool_name,
                            server_ids=server_ids,
                            conflict_type="duplicate_name",
                            details=f"Tool '{tool_name}' registered by multiple servers",
                        )
                    )

        return conflicts

    def get_statistics(self) -> CatalogStats:
        """Get statistics about the catalog."""
        stats = CatalogStats(
            total_tools=len(self._tools),
            total_servers=len(self._tools_by_server),
        )

        for tool in self._tools.values():
            stats.tools_by_category[tool.category.value] += 1
            stats.tools_by_severity[tool.severity.value] += 1
            if tool.deprecated:
                stats.deprecated_tools += 1

        stats.conflicts = self.detect_conflicts()

        return stats

    @staticmethod
    def _normalize_schema(schema: dict[str, Any]) -> str:
        """Normalize schema for comparison."""
        # Sort keys and hash for comparison
        normalized = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()


# =============================================================================
# Tool Catalog Generator
# =============================================================================


class ToolCatalogGenerator:
    """
    Generates tool catalogs in multiple formats.

    Usage:
        generator = ToolCatalogGenerator(registry)
        openai_tools = generator.to_openai_format()
        generator.export_to_file(ExportFormat.MARKDOWN, "catalog.md")
    """

    def __init__(self, registry: UnifiedToolRegistry) -> None:
        self.registry = registry

    # -------------------------------------------------------------------------
    # Format Conversion
    # -------------------------------------------------------------------------

    def to_openai_format(self) -> list[dict[str, Any]]:
        """Convert to OpenAI function calling format."""
        tools = []
        for tool in self.registry.get_all_tools():
            if tool.deprecated:
                continue

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
            )
        return tools

    def to_anthropic_format(self) -> list[dict[str, Any]]:
        """Convert to Anthropic tool use format."""
        tools = []
        for tool in self.registry.get_all_tools():
            if tool.deprecated:
                continue

            tools.append(
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                }
            )
        return tools

    def to_mcp_format(self) -> dict[str, Any]:
        """Convert to MCP protocol format."""
        tools = []
        for tool in self.registry.get_all_tools():
            tool_def = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }

            # Add optional annotations
            if tool.read_only or tool.idempotent:
                tool_def["annotations"] = {}
                if tool.read_only:
                    tool_def["annotations"]["readOnlyHint"] = True
                if tool.idempotent:
                    tool_def["annotations"]["idempotentHint"] = True

            tools.append(tool_def)

        return {
            "tools": tools,
            "version": "1.0.0",
            "generated_at": datetime.now(UTC).isoformat(),
        }

    def to_json_format(self) -> dict[str, Any]:
        """Convert to structured JSON format."""
        return {
            "catalog": {
                "version": "1.0.0",
                "generated_at": datetime.now(UTC).isoformat(),
                "statistics": self.registry.get_statistics().__dict__,
                "tools": [tool.model_dump() for tool in self.registry.get_all_tools()],
            }
        }

    def to_markdown_format(self) -> str:
        """Generate Markdown documentation."""
        lines = [
            "# MCP Tool Catalog",
            "",
            f"**Generated**: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
        ]

        # Statistics
        stats = self.registry.get_statistics()
        lines.extend(
            [
                "## Statistics",
                "",
                f"- **Total Tools**: {stats.total_tools}",
                f"- **Total Servers**: {stats.total_servers}",
                f"- **Deprecated Tools**: {stats.deprecated_tools}",
                "",
            ]
        )

        # Tools by category
        lines.extend(["### Tools by Category", ""])
        for category, count in sorted(stats.tools_by_category.items()):
            lines.append(f"- **{category.title()}**: {count}")
        lines.append("")

        # Conflicts
        if stats.conflicts:
            lines.extend(["### ⚠️ Conflicts Detected", ""])
            for conflict in stats.conflicts:
                lines.append(
                    f"- **{conflict.tool_name}**: {conflict.conflict_type} "
                    f"(servers: {', '.join(conflict.server_ids)})"
                )
            lines.append("")

        # Tools by category
        for category in ToolCategory:
            tools = self.registry.get_tools_by_category(category)
            if not tools:
                continue

            lines.extend([f"## {category.value.title()} Tools", ""])

            for tool in sorted(tools, key=lambda t: t.name):
                # Tool header
                deprecated = " ⚠️ DEPRECATED" if tool.deprecated else ""
                lines.append(f"### `{tool.name}`{deprecated}")
                lines.append("")
                lines.append(f"**Description**: {tool.description}")
                lines.append("")
                lines.append(f"- **Server**: `{tool.server_id}`")
                lines.append(f"- **Severity**: {tool.severity.value}")
                lines.append(f"- **Read-only**: {tool.read_only}")
                lines.append(f"- **Idempotent**: {tool.idempotent}")

                if tool.tags:
                    lines.append(f"- **Tags**: {', '.join(tool.tags)}")

                if tool.required_permissions:
                    lines.append(f"- **Permissions**: {', '.join(tool.required_permissions)}")

                # Input schema
                if tool.input_schema:
                    lines.extend(["", "**Input Schema**:", "```json"])
                    lines.append(json.dumps(tool.input_schema, indent=2))
                    lines.append("```")

                lines.append("")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    def export_to_file(self, format: ExportFormat, output_path: str | Path) -> None:
        """Export catalog to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == ExportFormat.OPENAI:
            data = self.to_openai_format()
            output_path.write_text(json.dumps(data, indent=2))
        elif format == ExportFormat.ANTHROPIC:
            data = self.to_anthropic_format()
            output_path.write_text(json.dumps(data, indent=2))
        elif format == ExportFormat.MCP:
            data = self.to_mcp_format()
            output_path.write_text(json.dumps(data, indent=2))
        elif format == ExportFormat.JSON:
            data = self.to_json_format()
            output_path.write_text(json.dumps(data, indent=2))
        elif format == ExportFormat.MARKDOWN:
            content = self.to_markdown_format()
            output_path.write_text(content)

        logger.info(f"Exported catalog to: {output_path} (format: {format.value})")

    def export_all_formats(self, output_dir: str | Path) -> dict[ExportFormat, Path]:
        """Export catalog to all formats."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exports = {}
        for format in ExportFormat:
            ext = "json" if format != ExportFormat.MARKDOWN else "md"
            output_path = output_dir / f"catalog.{format.value}.{ext}"
            self.export_to_file(format, output_path)
            exports[format] = output_path

        return exports

    # -------------------------------------------------------------------------
    # Changelog Generation
    # -------------------------------------------------------------------------

    def generate_changelog(
        self,
        old_catalog: dict[str, Any],
        new_catalog: dict[str, Any] | None = None,
    ) -> str:
        """Generate changelog between catalog versions."""
        if new_catalog is None:
            new_catalog = self.to_json_format()

        old_tools = {t["name"]: t for t in old_catalog.get("catalog", {}).get("tools", [])}
        new_tools = {t["name"]: t for t in new_catalog["catalog"]["tools"]}

        lines = [
            "# Tool Catalog Changelog",
            "",
            f"**Generated**: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
        ]

        # Added tools
        added = set(new_tools.keys()) - set(old_tools.keys())
        if added:
            lines.extend(["## Added Tools", ""])
            for tool_name in sorted(added):
                tool = new_tools[tool_name]
                lines.append(f"- **{tool_name}** ({tool['category']}) - {tool['description']}")
            lines.append("")

        # Removed tools
        removed = set(old_tools.keys()) - set(new_tools.keys())
        if removed:
            lines.extend(["## Removed Tools", ""])
            for tool_name in sorted(removed):
                tool = old_tools[tool_name]
                lines.append(f"- **{tool_name}** ({tool['category']}) - {tool['description']}")
            lines.append("")

        # Modified tools
        modified = []
        for tool_name in set(old_tools.keys()) & set(new_tools.keys()):
            old_tool = old_tools[tool_name]
            new_tool = new_tools[tool_name]

            changes = []
            if old_tool["description"] != new_tool["description"]:
                changes.append("description")
            if old_tool["input_schema"] != new_tool["input_schema"]:
                changes.append("schema")
            if old_tool.get("version") != new_tool.get("version"):
                changes.append("version")

            if changes:
                modified.append((tool_name, changes))

        if modified:
            lines.extend(["## Modified Tools", ""])
            for tool_name, changes in sorted(modified):
                lines.append(f"- **{tool_name}**: {', '.join(changes)} updated")
            lines.append("")

        if not added and not removed and not modified:
            lines.append("*No changes detected*")

        return "\n".join(lines)


__all__ = [
    "ExportFormat",
    "ToolCategory",
    "ToolSeverity",
    "ToolMetadata",
    "ToolConflict",
    "CatalogStats",
    "UnifiedToolRegistry",
    "ToolCatalogGenerator",
]
