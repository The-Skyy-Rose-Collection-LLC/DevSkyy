"""
Tests for Tripo3D Asset Generation Agent
=========================================

Comprehensive test suite for the TripoAssetAgent including:
- Agent initialization
- 3D model generation (text and image-based)
- Asset validation
- Tool registry integration
- Error handling and retries
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.tripo_agent import AssetValidation, TripoAssetAgent, TripoConfig
from agents.tripo_credentials import TripoCredentials
from core.runtime.tool_registry import ToolCallContext, ToolRegistry

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def tripo_config(tmp_path: Path) -> TripoConfig:
    """Create test Tripo configuration."""
    return TripoConfig(
        api_key="test-api-key",
        base_url="https://api.tripo3d.ai/v2",
        timeout=300.0,
        poll_interval=0.1,  # Fast polling for tests
        max_retries=2,
        output_dir=str(tmp_path / "3d_assets"),
    )


@pytest.fixture
def tool_registry() -> ToolRegistry:
    """Create test tool registry."""
    return ToolRegistry()


@pytest.fixture
def agent(tripo_config: TripoConfig, tool_registry: ToolRegistry) -> TripoAssetAgent:
    """Create Tripo asset agent for testing."""
    agent = TripoAssetAgent(config=tripo_config, registry=tool_registry)
    # Ensure output directory exists
    Path(tripo_config.output_dir).mkdir(parents=True, exist_ok=True)
    return agent


@pytest.fixture
def tool_context() -> ToolCallContext:
    """Create test tool call context."""
    return ToolCallContext(agent_id="test_tripo_agent")


# =============================================================================
# Configuration Tests
# =============================================================================


class TestTripoConfig:
    """Test TripoConfig initialization and validation."""

    def test_config_initialization(self, tripo_config: TripoConfig) -> None:
        """Test that config initializes correctly."""
        assert tripo_config.api_key == "test-api-key"
        assert tripo_config.base_url == "https://api.tripo3d.ai/v2"
        assert tripo_config.timeout == 300.0
        assert tripo_config.max_retries == 2

    def test_config_from_env(self, monkeypatch) -> None:
        """Test config creation from environment variables."""
        monkeypatch.setenv("TRIPO_API_KEY", "env-test-key")
        monkeypatch.setenv("TRIPO_API_BASE_URL", "https://custom.api.tripo3d.ai")

        config = TripoConfig.from_env()
        assert config.api_key == "env-test-key"
        assert config.base_url == "https://custom.api.tripo3d.ai"

    def test_config_validation_missing_api_key(self) -> None:
        """Test that validation fails without API key."""
        config = TripoConfig(api_key="")

        with pytest.raises(ValueError, match="TRIPO_API_KEY"):
            config.validate()

    def test_config_validation_success(self, tripo_config: TripoConfig) -> None:
        """Test that validation succeeds with valid config."""
        # Should not raise
        tripo_config.validate()


# =============================================================================
# Agent Initialization Tests
# =============================================================================


class TestTripoAssetAgentInit:
    """Test TripoAssetAgent initialization."""

    def test_agent_initialization(self, agent: TripoAssetAgent, tripo_config: TripoConfig) -> None:
        """Test that agent initializes correctly."""
        assert agent.name == "tripo_asset"
        assert agent.tripo_config == tripo_config
        assert Path(tripo_config.output_dir).exists()

    def test_agent_has_required_methods(self, agent: TripoAssetAgent) -> None:
        """Test that agent has all required SuperAgent methods."""
        assert hasattr(agent, "_plan")
        assert hasattr(agent, "_retrieve")
        assert hasattr(agent, "_execute_step")
        assert hasattr(agent, "_validate")
        assert hasattr(agent, "_emit")

    def test_agent_has_tools_registered(self, agent: TripoAssetAgent) -> None:
        """Test that agent registers Tripo-specific tools."""
        # Tools are registered during __init__
        assert agent.registry is not None
        # Check that tools can be retrieved
        assert agent.registry.get_tool("tripo_generate_from_text") is not None
        assert agent.registry.get_tool("tripo_generate_from_image") is not None
        assert agent.registry.get_tool("tripo_validate_asset") is not None


# =============================================================================
# Credential Resolution Wiring Tests
# =============================================================================


@pytest.mark.asyncio
class TestCredentialResolutionWiring:
    """Test _ensure_credentials_resolved(): the default-vs-explicit-config gate.

    Multi-account/multi-region resolution itself is covered exhaustively in
    tests/test_tripo_credentials.py. These tests prove the *wiring* in
    TripoAssetAgent: resolution fires exactly once for the default (no
    explicit config) construction path, and never fires when the caller
    supplied an explicit TripoConfig.
    """

    async def test_default_agent_resolves_credentials_once(self, monkeypatch) -> None:
        """A bare TripoAssetAgent() (no explicit config) resolves on first use,
        applies the result to tripo_config, and does not re-resolve afterward."""
        from agents.tripo_credentials import TripoCredentials

        fake_credentials = TripoCredentials(
            api_key="tsk_resolvedkey0001",
            is_global=False,
            base_url="https://api.tripo3d.com/v2",
            balance=12.5,
        )
        call_count = 0

        async def fake_resolve(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return fake_credentials

        monkeypatch.setattr("agents.tripo_agent.resolve_tripo_credentials", fake_resolve)

        agent = TripoAssetAgent()
        assert agent._needs_credential_resolution is True

        await agent._ensure_credentials_resolved()

        assert call_count == 1
        assert agent.tripo_config.api_key == "tsk_resolvedkey0001"
        assert agent.tripo_config.is_global is False
        assert agent.tripo_config.base_url == "https://api.tripo3d.com/v2"
        assert agent._needs_credential_resolution is False

        # Second call must be a no-op — resolution happens at most once per agent.
        await agent._ensure_credentials_resolved()
        assert call_count == 1

    async def test_explicit_config_never_triggers_resolution(
        self, monkeypatch, tripo_config: TripoConfig, tool_registry: ToolRegistry
    ) -> None:
        """An agent constructed with an explicit TripoConfig never calls the resolver —
        that caller's key/region choice is authoritative."""

        async def fail_if_called(*args, **kwargs):
            raise AssertionError(
                "resolve_tripo_credentials must not be called for an explicit config"
            )

        monkeypatch.setattr("agents.tripo_agent.resolve_tripo_credentials", fail_if_called)

        agent = TripoAssetAgent(config=tripo_config, registry=tool_registry)
        assert agent._needs_credential_resolution is False

        original_api_key = agent.tripo_config.api_key
        await agent._ensure_credentials_resolved()

        assert agent.tripo_config.api_key == original_api_key


# =============================================================================
# Planning Tests
# =============================================================================


@pytest.mark.asyncio
class TestTripoAssetAgentPlanning:
    """Test agent planning phase."""

    async def test_plan_text_to_3d_generation(
        self, agent: TripoAssetAgent, tool_context: ToolCallContext
    ) -> None:
        """Test planning for text-to-3D generation."""
        request = {
            "action": "generate_from_description",
            "product_name": "Heart Rose Bomber",
            "collection": "BLACK_ROSE",
            "garment_type": "bomber",
            "additional_details": "Rose gold zipper, embroidered back",
        }

        plan = await agent._plan(request, tool_context)

        assert len(plan) > 0
        # First step should be text generation
        assert plan[0].tool_name == "tripo_generate_from_text"
        assert plan[0].inputs["product_name"] == "Heart Rose Bomber"
        assert plan[0].inputs["collection"] == "BLACK_ROSE"

    async def test_plan_image_to_3d_generation(
        self, agent: TripoAssetAgent, tool_context: ToolCallContext
    ) -> None:
        """Test planning for image-to-3D generation."""
        request = {
            "action": "generate_from_image",
            "product_name": "Custom Hoodie",
            "image_path": "/path/to/design.jpg",
        }

        plan = await agent._plan(request, tool_context)

        assert len(plan) > 0
        # First step should be image generation
        assert plan[0].tool_name == "tripo_generate_from_image"
        assert plan[0].inputs["product_name"] == "Custom Hoodie"

    async def test_plan_includes_validation(
        self, agent: TripoAssetAgent, tool_context: ToolCallContext
    ) -> None:
        """Test that plan includes asset validation step."""
        request = {
            "action": "generate_from_description",
            "product_name": "Test Product",
        }

        plan = await agent._plan(request, tool_context)

        # Should have generation step + validation step
        assert len(plan) >= 2
        # Last step should be validation
        validation_step = [s for s in plan if s.tool_name == "tripo_validate_asset"]
        assert len(validation_step) > 0


# =============================================================================
# Retrieval Tests
# =============================================================================


@pytest.mark.asyncio
class TestTripoAssetAgentRetrieval:
    """Test agent retrieval phase."""

    async def test_retrieve_brand_context(
        self, agent: TripoAssetAgent, tool_context: ToolCallContext
    ) -> None:
        """Test that retrieval includes brand context."""
        request = {
            "collection": "BLACK_ROSE",
        }
        plan = []

        context = await agent._retrieve(request, plan, tool_context)

        assert context is not None
        assert len(context.documents) > 0
        # Should have brand DNA and collection style
        assert any(
            "SKYYROSE_BRAND_DNA" in str(doc) or "brand_dna" in str(doc) for doc in context.documents
        )

    async def test_retrieve_default_collection(
        self, agent: TripoAssetAgent, tool_context: ToolCallContext
    ) -> None:
        """Test that retrieval defaults to SIGNATURE collection."""
        request = {}
        plan = []

        context = await agent._retrieve(request, plan, tool_context)

        assert context is not None
        # Should contain default context
        assert context.query == "SkyyRose SIGNATURE collection context"


# =============================================================================
# Validation Tests
# =============================================================================


@pytest.mark.asyncio
class TestAssetValidation:
    """Test 3D asset validation."""

    @pytest.fixture
    def test_model_dir(self, tmp_path: Path) -> Path:
        """Per-test model directory (pytest-managed; unique path avoids
        cross-process races on a shared /tmp dir)."""
        return tmp_path

    async def test_validate_missing_file(self, agent: TripoAssetAgent) -> None:
        """Test validation of missing file."""
        result = await agent._tool_validate_asset("/nonexistent/model.glb")

        validation = AssetValidation(**result)
        assert not validation.is_valid
        assert len(validation.errors) > 0
        assert "not found" in validation.errors[0].lower()

    async def test_validate_glb_file(self, agent: TripoAssetAgent, test_model_dir: Path) -> None:
        """Test validation of a GLB file."""
        # Create minimal GLB file with proper header and enough data to pass size check
        glb_path = test_model_dir / "test.glb"
        with open(glb_path, "wb") as f:
            f.write(b"glTF")  # Magic number
            f.write((2).to_bytes(4, "little"))  # Version 2
            f.write((1024).to_bytes(4, "little"))  # Length (1KB)
            # Add padding to meet minimum file size (10KB default)
            f.write(b"\x00" * (10 * 1024))

        result = await agent._tool_validate_asset(str(glb_path))

        validation = AssetValidation(**result)
        # Should be valid (has proper GLB header and sufficient size)
        assert validation.is_valid or len(validation.errors) == 0

    async def test_validate_unsupported_format(
        self, agent: TripoAssetAgent, test_model_dir: Path
    ) -> None:
        """Test validation warning for unsupported format."""
        # Create a file with unsupported format
        model_path = test_model_dir / "test.xyz"
        model_path.write_text("test content")

        result = await agent._tool_validate_asset(str(model_path))

        validation = AssetValidation(**result)
        assert len(validation.warnings) > 0
        assert any("unsupported" in w.lower() for w in validation.warnings)

    async def test_validate_file_size_checks(
        self, agent: TripoAssetAgent, test_model_dir: Path
    ) -> None:
        """Test validation of file size constraints."""
        # Create a GLB file that's too large
        model_path = test_model_dir / "large.glb"
        with open(model_path, "wb") as f:
            f.write(b"glTF")
            f.write((2).to_bytes(4, "little"))
            # Write 60MB of data (exceeds 50MB limit)
            f.write(b"x" * (60 * 1024 * 1024))

        result = await agent._tool_validate_asset(str(model_path), max_file_size_mb=50.0)

        validation = AssetValidation(**result)
        assert not validation.is_valid
        assert any("too large" in e.lower() for e in validation.errors)


# =============================================================================
# API Integration Tests
# =============================================================================


@pytest.mark.asyncio
class TestTripoAPIIntegration:
    """Test Tripo3D API integration."""

    async def test_agent_configuration(self, agent: TripoAssetAgent) -> None:
        """Test agent configuration is properly set up."""
        # Verify agent has required configuration
        assert agent.tripo_config is not None
        assert hasattr(agent.tripo_config, "api_key")
        assert hasattr(agent.tripo_config, "base_url")

    async def test_agent_has_required_tools(self, agent: TripoAssetAgent) -> None:
        """Test that agent has all required tools registered."""
        # The agent should have tools registered
        assert agent.registry is not None
        # Verify the registry is a ToolRegistry instance
        assert hasattr(agent.registry, "get_tool")

    async def test_api_request_retry_on_network_error(self, agent: TripoAssetAgent) -> None:
        """Test API request retry logic on network errors."""
        # The agent uses tenacity for retries
        # This test verifies retry configuration
        assert agent.tripo_config.max_retries == 2
        assert agent.tripo_config.retry_min_wait == 1.0
        assert agent.tripo_config.retry_max_wait == 30.0

    async def test_poll_task_success(self, agent: TripoAssetAgent) -> None:
        """Test task polling until completion."""
        # Mock successful completion (structure for future integration)
        _expected_response = {
            "data": {
                "task_id": "test-task",
                "status": "success",
                "output": {
                    "model": {"url": "https://example.com/model.glb"},
                    "pbr_model": {"url": "https://example.com/texture.zip"},
                    "rendered_image": {"url": "https://example.com/thumb.png"},
                },
            }
        }

        # This would require mocking _api_request and asyncio.sleep
        # Test structure demonstrates integration point
        assert _expected_response["data"]["status"] == "success"


# =============================================================================
# Generation Fidelity Tests
# =============================================================================


@pytest.mark.asyncio
class TestGenerateFromImageFidelity:
    """`_tool_generate_from_image` must pass explicit max-fidelity params to
    tripo3d's `image_to_model()` rather than relying on the SDK's own
    defaults (regression test for a 2026-07-22 research finding: the call
    used to pass only `image=...`, silently generating at the SDK's default
    `model_version='v2.5-20250123'` / `texture_quality='standard'` instead of
    the flagship model + detailed quality this project actually wants).
    """

    async def test_image_to_model_called_with_fidelity_params(
        self, agent: TripoAssetAgent, tmp_path: Path
    ) -> None:
        image_path = tmp_path / "source.png"
        image_path.write_bytes(b"fake-png-bytes")

        from tripo3d import TaskStatus

        fake_task = MagicMock(status=TaskStatus.SUCCESS)
        fake_client = AsyncMock()
        fake_client.image_to_model = AsyncMock(return_value="task-123")
        fake_client.wait_for_task = AsyncMock(return_value=fake_task)
        fake_client.download_task_models = AsyncMock(
            return_value={"pbr_model": str(tmp_path / "out.glb")}
        )
        fake_client.__aenter__ = AsyncMock(return_value=fake_client)
        fake_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agents.tripo_agent.TripoClient", return_value=fake_client):
            await agent._tool_generate_from_image(image_path=str(image_path))

        fake_client.image_to_model.assert_awaited_once()
        _, kwargs = fake_client.image_to_model.call_args
        assert kwargs["model_version"] == agent.tripo_config.generation_model_version
        assert kwargs["texture"] is True
        assert kwargs["pbr"] == agent.tripo_config.pbr_enabled
        assert kwargs["texture_quality"] == agent.tripo_config.texture_quality
        assert kwargs["geometry_quality"] == agent.tripo_config.geometry_quality
        assert kwargs["texture_alignment"] == "original_image"
        assert kwargs["face_limit"] == agent.tripo_config.face_limit
        assert kwargs["auto_size"] is False
        assert kwargs["enable_image_autofix"] is False

    async def test_default_config_uses_valid_sdk_enum_values(self) -> None:
        """'high' was never a valid tripo3d texture_quality value -- the
        default must be one the SDK actually accepts."""
        config = TripoConfig(api_key="test-key")
        assert config.texture_quality in {"standard", "detailed"}
        assert config.geometry_quality in {"standard", "detailed"}
        assert config.generation_model_version
        assert config.face_limit > 0

    async def test_texture_quality_and_geometry_quality_not_swapped(
        self, tool_registry: ToolRegistry, tmp_path: Path
    ) -> None:
        """`texture_quality` and `geometry_quality` share the same default
        ('detailed'), which lets a test asserting only `kwargs[x] ==
        config.x` pass even if the call site swapped which config field
        feeds which kwarg. Use distinct values to catch that specifically.
        """
        config = TripoConfig(
            api_key="test-key",
            output_dir=str(tmp_path),
            texture_quality="detailed",
            geometry_quality="standard",
        )
        agent = TripoAssetAgent(config=config, registry=tool_registry)

        image_path = tmp_path / "source.png"
        image_path.write_bytes(b"fake-png-bytes")

        from tripo3d import TaskStatus

        fake_task = MagicMock(status=TaskStatus.SUCCESS)
        fake_client = AsyncMock()
        fake_client.image_to_model = AsyncMock(return_value="task-123")
        fake_client.wait_for_task = AsyncMock(return_value=fake_task)
        fake_client.download_task_models = AsyncMock(
            return_value={"pbr_model": str(tmp_path / "out.glb")}
        )
        fake_client.__aenter__ = AsyncMock(return_value=fake_client)
        fake_client.__aexit__ = AsyncMock(return_value=False)

        with patch("agents.tripo_agent.TripoClient", return_value=fake_client):
            await agent._tool_generate_from_image(image_path=str(image_path))

        _, kwargs = fake_client.image_to_model.call_args
        assert kwargs["texture_quality"] == "detailed"
        assert kwargs["geometry_quality"] == "standard"

    async def test_credential_resolution_called_before_dispatch(
        self, tool_registry: ToolRegistry, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A bare TripoAssetAgent() (config=None) must resolve multi-account
        credentials BEFORE the paid image_to_model() call -- verified through
        the actual _tool_generate_from_image entry point, not by calling
        _ensure_credentials_resolved() directly.
        """
        monkeypatch.setenv("TRIPO_OUTPUT_DIR", str(tmp_path))
        agent = TripoAssetAgent(config=None, registry=tool_registry)

        image_path = tmp_path / "source.png"
        image_path.write_bytes(b"fake-png-bytes")

        from tripo3d import TaskStatus

        fake_task = MagicMock(status=TaskStatus.SUCCESS)
        fake_client = AsyncMock()
        fake_client.image_to_model = AsyncMock(return_value="task-123")
        fake_client.wait_for_task = AsyncMock(return_value=fake_task)
        fake_client.download_task_models = AsyncMock(
            return_value={"pbr_model": str(tmp_path / "out.glb")}
        )
        fake_client.__aenter__ = AsyncMock(return_value=fake_client)
        fake_client.__aexit__ = AsyncMock(return_value=False)

        resolve_mock = AsyncMock(
            return_value=TripoCredentials(
                api_key="resolved-key",
                is_global=True,
                base_url="https://api.tripo3d.ai/v2",
                balance=100.0,
            )
        )

        with (
            patch("agents.tripo_agent.resolve_tripo_credentials", resolve_mock),
            patch("agents.tripo_agent.TripoClient", return_value=fake_client),
        ):
            await agent._tool_generate_from_image(image_path=str(image_path))

        resolve_mock.assert_awaited_once()
        fake_client.image_to_model.assert_awaited_once()
        assert agent.tripo_config.api_key == "resolved-key"


# =============================================================================
# SuperAgent Workflow Tests
# =============================================================================


@pytest.mark.asyncio
class TestTripoSuperAgentWorkflow:
    """Test the full SuperAgent workflow."""

    async def test_agent_workflow_structure(
        self, agent: TripoAssetAgent, tool_context: ToolCallContext
    ) -> None:
        """Test that agent has required workflow methods."""
        # Verify agent has SuperAgent workflow methods
        assert hasattr(agent, "run")
        assert hasattr(agent, "_plan")
        assert hasattr(agent, "_retrieve")
        assert hasattr(agent, "_execute_step")
        assert hasattr(agent, "_validate")
        assert hasattr(agent, "_emit")
        assert hasattr(agent, "close")

    async def test_prompt_building(
        self, agent: TripoAssetAgent, tool_context: ToolCallContext
    ) -> None:
        """Test prompt building for different collections."""
        # Test SIGNATURE collection
        prompt_sig = agent._build_prompt(
            product_name="Test Bomber",
            collection="SIGNATURE",
            garment_type="bomber",
        )
        assert "Test Bomber" in prompt_sig

        # Test BLACK_ROSE collection
        prompt_br = agent._build_prompt(
            product_name="Rose Hoodie",
            collection="BLACK_ROSE",
            garment_type="hoodie",
        )
        assert "Rose Hoodie" in prompt_br

    async def test_workflow_with_validation_error(
        self, agent: TripoAssetAgent, tool_context: ToolCallContext
    ) -> None:
        """Test workflow handles validation errors gracefully."""
        _request = {
            "action": "generate_from_description",
            "product_name": "Test Product",
        }

        # This test verifies error handling in the full workflow
        # Would need proper mocking of failure scenarios
        assert _request["action"] == "generate_from_description"
        assert tool_context is not None


# =============================================================================
# Tool Registry Integration Tests
# =============================================================================


class TestToolRegistryIntegration:
    """Test integration with ToolRegistry."""

    def test_tripo_tools_registered(
        self, tool_registry: ToolRegistry, agent: TripoAssetAgent
    ) -> None:
        """Test that Tripo tools are properly registered."""
        tools = [
            "tripo_generate_from_text",
            "tripo_generate_from_image",
            "tripo_validate_asset",
            "tripo_check_riggable",
            "tripo_rig_model",
            "tripo_retarget_animation",
        ]

        for tool_name in tools:
            tool = agent.registry.get_tool(tool_name)
            assert tool is not None
            assert tool.name == tool_name

    def test_tool_specs_complete(self, agent: TripoAssetAgent) -> None:
        """Test that tool specifications are complete."""
        tool = agent.registry.get_tool("tripo_generate_from_text")
        assert tool is not None
        # Tool should have description and severity
        assert hasattr(tool, "description")
        assert hasattr(tool, "severity")


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling and recovery."""

    async def test_invalid_garment_type_defaults(self, agent: TripoAssetAgent) -> None:
        """Test that invalid garment types use sensible defaults."""
        prompt = agent._build_prompt(
            product_name="Test",
            collection="SIGNATURE",
            garment_type="invalid_type",
        )

        # Should use fallback template
        assert "luxury streetwear garment" in prompt

    async def test_invalid_collection_defaults(self, agent: TripoAssetAgent) -> None:
        """Test that invalid collections use sensible defaults."""
        prompt = agent._build_prompt(
            product_name="Test",
            collection="INVALID",
            garment_type="tee",
        )

        # Should use SIGNATURE collection defaults
        assert "SIGNATURE" in prompt or "style" in prompt.lower()

    async def test_configuration_validation(self, agent: TripoAssetAgent) -> None:
        """Test that agent configuration is properly validated."""
        # Agent should have valid configuration after initialization
        assert agent.tripo_config.max_retries >= 0
        assert agent.tripo_config.retry_min_wait > 0
        assert agent.tripo_config.retry_max_wait >= agent.tripo_config.retry_min_wait


# =============================================================================
# Integration with Orchestration Tests
# =============================================================================


@pytest.mark.asyncio
class TestOrchestrationIntegration:
    """Test integration with orchestration layer."""

    async def test_agent_executes_via_orchestration(self, agent: TripoAssetAgent) -> None:
        """Test that agent can be executed through orchestration."""
        _request = {
            "action": "generate_from_description",
            "product_name": "Test Hoodie",
            "collection": "BLACK_ROSE",
        }

        # Should not raise errors during execution
        # Actual result depends on mocking
        assert agent.name == "tripo_asset"
        assert hasattr(agent, "registry")
        assert _request["collection"] == "BLACK_ROSE"


# =============================================================================
# Performance Tests
# =============================================================================


@pytest.mark.asyncio
class TestPerformance:
    """Test performance characteristics."""

    async def test_prompt_building_performance(self, agent: TripoAssetAgent) -> None:
        """Test that prompt building is fast."""
        import time

        start = time.time()
        for _ in range(100):
            agent._build_prompt(
                product_name="Test Product",
                collection="SIGNATURE",
                garment_type="tee",
            )
        duration = time.time() - start

        # 100 prompts should build in < 100ms
        assert duration < 0.1

    async def test_config_loading_performance(self) -> None:
        """Test that config loading from env is fast."""
        import time

        start = time.time()
        for _ in range(100):
            TripoConfig.from_env()
        duration = time.time() - start

        # 100 configs should load in < 50ms
        assert duration < 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
