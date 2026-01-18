"""
Tests for MCP Infrastructure
=============================

Tests for process manager, catalog generator, and orchestrator.
"""

from pathlib import Path

import pytest

from mcp_servers.catalog_generator import (
    ExportFormat,
    ToolCatalogGenerator,
    ToolCategory,
    ToolMetadata,
    ToolSeverity,
    UnifiedToolRegistry,
)
from mcp_servers.orchestrator import MCPOrchestrator
from mcp_servers.process_manager import (
    MCPProcessManager,
    ProcessStatus,
)

# =============================================================================
# Process Manager Tests
# =============================================================================


@pytest.mark.unit
def test_process_manager_register_server(sample_mcp_server_definition):
    """Test server registration."""
    manager = MCPProcessManager()
    manager.register_server(sample_mcp_server_definition)

    assert "test-server" in manager._servers
    assert manager.get_status("test-server") == ProcessStatus.STOPPED


@pytest.mark.unit
def test_process_manager_unregister_server(sample_mcp_server_definition):
    """Test server unregistration."""
    manager = MCPProcessManager()
    manager.register_server(sample_mcp_server_definition)
    manager.unregister_server("test-server")

    assert "test-server" not in manager._servers
    assert manager.get_status("test-server") == ProcessStatus.STOPPED


@pytest.mark.unit
def test_process_manager_list_servers(sample_mcp_server_definition):
    """Test listing registered servers."""
    manager = MCPProcessManager()
    manager.register_server(sample_mcp_server_definition)

    servers = manager.list_servers()
    assert len(servers) == 1
    assert servers[0].server_id == "test-server"


@pytest.mark.unit
def test_process_manager_get_all_status(sample_mcp_server_definition):
    """Test getting status for all servers."""
    manager = MCPProcessManager()
    manager.register_server(sample_mcp_server_definition)

    status_map = manager.get_all_status()
    assert "test-server" in status_map
    assert status_map["test-server"] == ProcessStatus.STOPPED


# =============================================================================
# Tool Registry Tests
# =============================================================================


@pytest.mark.unit
def test_tool_registry_register_tool():
    """Test tool registration."""
    registry = UnifiedToolRegistry()

    tool = ToolMetadata(
        name="test_tool",
        description="Test tool",
        server_id="test-server",
        category=ToolCategory.SYSTEM,
        severity=ToolSeverity.LOW,
        input_schema={"type": "object", "properties": {}},
    )

    registry.register_tool(tool)

    assert registry.get_tool("test_tool") is not None
    assert len(registry.get_all_tools()) == 1


@pytest.mark.unit
def test_tool_registry_get_by_category():
    """Test getting tools by category."""
    registry = UnifiedToolRegistry()

    tools = [
        ToolMetadata(
            name="tool1",
            description="Tool 1",
            server_id="server1",
            category=ToolCategory.COMMERCE,
            severity=ToolSeverity.MEDIUM,
            input_schema={},
        ),
        ToolMetadata(
            name="tool2",
            description="Tool 2",
            server_id="server1",
            category=ToolCategory.COMMERCE,
            severity=ToolSeverity.MEDIUM,
            input_schema={},
        ),
        ToolMetadata(
            name="tool3",
            description="Tool 3",
            server_id="server1",
            category=ToolCategory.CONTENT,
            severity=ToolSeverity.LOW,
            input_schema={},
        ),
    ]

    registry.register_tools(tools)

    commerce_tools = registry.get_tools_by_category(ToolCategory.COMMERCE)
    assert len(commerce_tools) == 2


@pytest.mark.unit
def test_tool_registry_search():
    """Test tool search."""
    registry = UnifiedToolRegistry()

    tool = ToolMetadata(
        name="product_search",
        description="Search for products in the catalog",
        server_id="server1",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.LOW,
        input_schema={},
    )

    registry.register_tool(tool)

    results = registry.search_tools("product")
    assert len(results) == 1
    assert results[0].name == "product_search"


@pytest.mark.unit
def test_tool_registry_conflict_detection():
    """Test conflict detection for duplicate tools."""
    registry = UnifiedToolRegistry()

    tool1 = ToolMetadata(
        name="duplicate_tool",
        description="First version",
        server_id="server1",
        category=ToolCategory.SYSTEM,
        severity=ToolSeverity.LOW,
        input_schema={"type": "object", "properties": {"param1": {"type": "string"}}},
    )

    tool2 = ToolMetadata(
        name="duplicate_tool",
        description="Second version",
        server_id="server2",
        category=ToolCategory.SYSTEM,
        severity=ToolSeverity.LOW,
        input_schema={"type": "object", "properties": {"param2": {"type": "number"}}},
    )

    registry.register_tool(tool1)
    registry.register_tool(tool2)

    conflicts = registry.detect_conflicts()
    assert len(conflicts) > 0
    assert conflicts[0].tool_name == "duplicate_tool"
    assert conflicts[0].conflict_type in ["duplicate_name", "schema_mismatch"]


# =============================================================================
# Catalog Generator Tests
# =============================================================================


@pytest.mark.unit
def test_catalog_generator_openai_format():
    """Test OpenAI function calling format export."""
    registry = UnifiedToolRegistry()

    tool = ToolMetadata(
        name="test_function",
        description="Test function",
        server_id="server1",
        category=ToolCategory.SYSTEM,
        severity=ToolSeverity.LOW,
        input_schema={
            "type": "object",
            "properties": {"param": {"type": "string", "description": "A parameter"}},
            "required": ["param"],
        },
    )

    registry.register_tool(tool)

    generator = ToolCatalogGenerator(registry)
    openai_tools = generator.to_openai_format()

    assert len(openai_tools) == 1
    assert openai_tools[0]["type"] == "function"
    assert openai_tools[0]["function"]["name"] == "test_function"
    assert "parameters" in openai_tools[0]["function"]


@pytest.mark.unit
def test_catalog_generator_anthropic_format():
    """Test Anthropic tool use format export."""
    registry = UnifiedToolRegistry()

    tool = ToolMetadata(
        name="test_tool",
        description="Test tool",
        server_id="server1",
        category=ToolCategory.SYSTEM,
        severity=ToolSeverity.LOW,
        input_schema={"type": "object", "properties": {}},
    )

    registry.register_tool(tool)

    generator = ToolCatalogGenerator(registry)
    anthropic_tools = generator.to_anthropic_format()

    assert len(anthropic_tools) == 1
    assert anthropic_tools[0]["name"] == "test_tool"
    assert "input_schema" in anthropic_tools[0]


@pytest.mark.unit
def test_catalog_generator_markdown_format():
    """Test Markdown documentation generation."""
    registry = UnifiedToolRegistry()

    tool = ToolMetadata(
        name="test_tool",
        description="Test tool for documentation",
        server_id="server1",
        category=ToolCategory.COMMERCE,
        severity=ToolSeverity.MEDIUM,
        input_schema={"type": "object", "properties": {}},
        read_only=True,
    )

    registry.register_tool(tool)

    generator = ToolCatalogGenerator(registry)
    markdown = generator.to_markdown_format()

    assert "# MCP Tool Catalog" in markdown
    assert "test_tool" in markdown
    assert "Commerce Tools" in markdown
    assert "**Read-only**: True" in markdown


@pytest.mark.unit
def test_catalog_generator_export_to_file(temp_catalog_dir):
    """Test exporting catalog to file."""
    registry = UnifiedToolRegistry()

    tool = ToolMetadata(
        name="export_test",
        description="Test export",
        server_id="server1",
        category=ToolCategory.SYSTEM,
        severity=ToolSeverity.LOW,
        input_schema={},
    )

    registry.register_tool(tool)

    generator = ToolCatalogGenerator(registry)
    output_path = Path(temp_catalog_dir) / "test_catalog.json"

    generator.export_to_file(ExportFormat.JSON, output_path)

    assert output_path.exists()
    content = output_path.read_text()
    assert "export_test" in content


@pytest.mark.unit
def test_catalog_generator_changelog():
    """Test changelog generation between catalog versions."""
    # Old catalog
    old_catalog = {
        "catalog": {
            "tools": [
                {
                    "name": "old_tool",
                    "category": "system",
                    "description": "Old tool",
                    "input_schema": {},
                }
            ]
        }
    }

    # New catalog
    registry = UnifiedToolRegistry()
    registry.register_tool(
        ToolMetadata(
            name="new_tool",
            description="New tool",
            server_id="server1",
            category=ToolCategory.SYSTEM,
            severity=ToolSeverity.LOW,
            input_schema={},
        )
    )

    generator = ToolCatalogGenerator(registry)
    changelog = generator.generate_changelog(old_catalog)

    assert "Added Tools" in changelog
    assert "new_tool" in changelog
    assert "Removed Tools" in changelog
    assert "old_tool" in changelog


# =============================================================================
# Orchestrator Tests
# =============================================================================


@pytest.mark.unit
def test_orchestrator_singleton():
    """Test orchestrator singleton pattern."""
    orch1 = MCPOrchestrator.get_instance()
    orch2 = MCPOrchestrator.get_instance()

    assert orch1 is orch2


@pytest.mark.unit
def test_orchestrator_register_local_server(sample_mcp_server_definition):
    """Test registering a local server."""
    orchestrator = MCPOrchestrator()
    orchestrator.register_local_server(sample_mcp_server_definition)

    servers = orchestrator.process_manager.list_servers()
    assert len(servers) == 1
    assert servers[0].server_id == "test-server"


@pytest.mark.unit
def test_orchestrator_register_remote_server():
    """Test registering a remote server."""
    orchestrator = MCPOrchestrator()
    orchestrator.register_remote_server(
        server_id="remote-server",
        server_url="https://api.example.com/mcp",
        api_key="test-key",
    )

    assert "remote-server" in orchestrator._remote_servers
    assert orchestrator.get_status("remote-server") == "remote"


@pytest.mark.unit
def test_orchestrator_get_all_status(sample_mcp_server_definition):
    """Test getting status for all servers (local + remote)."""
    orchestrator = MCPOrchestrator()
    orchestrator.register_local_server(sample_mcp_server_definition)
    orchestrator.register_remote_server(
        server_id="remote-server",
        server_url="https://api.example.com/mcp",
    )

    status_map = orchestrator.get_all_status()

    assert "test-server" in status_map
    assert "remote-server" in status_map
    assert status_map["remote-server"] == "remote"


@pytest.mark.unit
def test_orchestrator_export_catalog_formats():
    """Test exporting catalog in multiple formats."""
    orchestrator = MCPOrchestrator()

    # Add a test tool
    orchestrator.tool_registry.register_tool(
        ToolMetadata(
            name="test_tool",
            description="Test",
            server_id="server1",
            category=ToolCategory.SYSTEM,
            severity=ToolSeverity.LOW,
            input_schema={},
        )
    )

    # Test each format
    openai = orchestrator.export_catalog(ExportFormat.OPENAI)
    assert isinstance(openai, list)

    anthropic = orchestrator.export_catalog(ExportFormat.ANTHROPIC)
    assert isinstance(anthropic, list)

    mcp = orchestrator.export_catalog(ExportFormat.MCP)
    assert isinstance(mcp, dict)
    assert "tools" in mcp

    json_export = orchestrator.export_catalog(ExportFormat.JSON)
    assert isinstance(json_export, dict)
    assert "catalog" in json_export

    markdown = orchestrator.export_catalog(ExportFormat.MARKDOWN)
    assert isinstance(markdown, str)
    assert "# MCP Tool Catalog" in markdown
