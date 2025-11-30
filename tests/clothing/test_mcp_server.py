"""
Tests for 3D Clothing Asset MCP Server

Tests the MCP tools for 3D generation, virtual try-on,
and WordPress upload functionality.

Truth Protocol Rule #8: Test coverage ≥90%
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.modules.clothing.schemas.schemas import (
    Model3DFormat,
    Model3DResult,
    PipelineResult,
    PipelineStage,
    TryOnModel,
    TryOnResult,
    WordPressUploadResult,
)


class TestMCPTools:
    """Tests for MCP server tools."""

    @pytest.fixture
    def mock_tripo_client(self) -> MagicMock:
        """Create mock Tripo3D client."""
        client = MagicMock()
        client.initialize = AsyncMock(return_value=True)
        client.text_to_3d = AsyncMock(
            return_value=Model3DResult(
                task_id="task_123",
                status="success",
                model_url="https://api.tripo3d.ai/models/123.glb",
                model_format=Model3DFormat.GLB,
                local_path="/tmp/model.glb",
                thumbnail_url="https://api.tripo3d.ai/thumb/123.png",
                generation_time_seconds=45.0,
            )
        )
        client.image_to_3d = AsyncMock(
            return_value=Model3DResult(
                task_id="task_img_123",
                status="success",
                model_url="https://api.tripo3d.ai/models/img123.glb",
                model_format=Model3DFormat.GLB,
                local_path="/tmp/model_img.glb",
                generation_time_seconds=40.0,
            )
        )
        client.get_task_status = AsyncMock(
            return_value={"status": "success", "progress": 100}
        )
        return client

    @pytest.fixture
    def mock_fashn_client(self) -> MagicMock:
        """Create mock FASHN client."""
        client = MagicMock()
        client.initialize = AsyncMock(return_value=True)
        client.virtual_tryon = AsyncMock(
            return_value=TryOnResult(
                task_id="tryon_123",
                status="completed",
                image_url="https://api.fashn.ai/results/123.png",
                local_path="/tmp/tryon.png",
                model_type=TryOnModel.FEMALE,
                processing_time_seconds=12.0,
            )
        )
        client.batch_tryon = AsyncMock(
            return_value=[
                TryOnResult(
                    task_id="tryon_f",
                    status="completed",
                    image_url="https://api.fashn.ai/results/f.png",
                    local_path="/tmp/tryon_f.png",
                    model_type=TryOnModel.FEMALE,
                    processing_time_seconds=12.0,
                ),
                TryOnResult(
                    task_id="tryon_m",
                    status="completed",
                    image_url="https://api.fashn.ai/results/m.png",
                    local_path="/tmp/tryon_m.png",
                    model_type=TryOnModel.MALE,
                    processing_time_seconds=11.0,
                ),
            ]
        )
        return client

    @pytest.fixture
    def mock_wordpress_client(self) -> MagicMock:
        """Create mock WordPress client."""
        client = MagicMock()
        client.initialize = AsyncMock(return_value=True)
        client.upload_file = AsyncMock(
            return_value=WordPressUploadResult(
                media_id=12345,
                source_url="https://skyyrose.co/uploads/model.glb",
                mime_type="model/gltf-binary",
                title="Test Model",
            )
        )
        client.upload_from_url = AsyncMock(
            return_value=WordPressUploadResult(
                media_id=12346,
                source_url="https://skyyrose.co/uploads/image.png",
                mime_type="image/png",
                title="Test Image",
            )
        )
        return client

    @pytest.mark.asyncio
    async def test_generate_3d_from_text(self, mock_tripo_client: MagicMock) -> None:
        """Test text-to-3D generation tool."""
        from agent.modules.clothing.mcp_server import (
            ClientManager,
            generate_3d_from_text,
        )

        # Patch the client manager
        with patch.object(
            ClientManager, "get_tripo_client", return_value=mock_tripo_client
        ):
            # FastMCP tools are FunctionTool objects, call .fn for the underlying function
            result = await generate_3d_from_text.fn(
                product_name="Black Rose Hoodie",
                description="Luxury black hoodie with embroidered rose pattern",
                collection="black_rose",
                category="hoodie",
                color="black",
            )

        data = json.loads(result)
        assert data["success"] is True
        assert data["task_id"] == "task_123"
        assert data["status"] == "success"
        assert data["model_url"] is not None

    @pytest.mark.asyncio
    async def test_generate_3d_from_image(self, mock_tripo_client: MagicMock) -> None:
        """Test image-to-3D generation tool."""
        from agent.modules.clothing.mcp_server import (
            ClientManager,
            generate_3d_from_image,
        )

        with patch.object(
            ClientManager, "get_tripo_client", return_value=mock_tripo_client
        ):
            result = await generate_3d_from_image.fn(
                image_url="https://example.com/hoodie.png",
                product_name="Test Hoodie",
            )

        data = json.loads(result)
        assert data["success"] is True
        assert data["task_id"] == "task_img_123"

    @pytest.mark.asyncio
    async def test_get_3d_task_status(self, mock_tripo_client: MagicMock) -> None:
        """Test task status retrieval."""
        from agent.modules.clothing.mcp_server import (
            ClientManager,
            get_3d_task_status,
        )

        with patch.object(
            ClientManager, "get_tripo_client", return_value=mock_tripo_client
        ):
            result = await get_3d_task_status.fn("task_123")

        data = json.loads(result)
        assert data["task_id"] == "task_123"
        assert data["status"] == "success"

    @pytest.mark.asyncio
    async def test_virtual_tryon(self, mock_fashn_client: MagicMock) -> None:
        """Test virtual try-on tool."""
        from agent.modules.clothing.mcp_server import ClientManager, virtual_tryon

        with patch.object(
            ClientManager, "get_fashn_client", return_value=mock_fashn_client
        ):
            result = await virtual_tryon.fn(
                garment_image_url="https://example.com/hoodie.png",
                model_type="female",
            )

        data = json.loads(result)
        assert data["success"] is True
        assert data["task_id"] == "tryon_123"
        assert data["model_type"] == "female"

    @pytest.mark.asyncio
    async def test_batch_virtual_tryon(self, mock_fashn_client: MagicMock) -> None:
        """Test batch virtual try-on tool."""
        from agent.modules.clothing.mcp_server import (
            ClientManager,
            batch_virtual_tryon,
        )

        with patch.object(
            ClientManager, "get_fashn_client", return_value=mock_fashn_client
        ):
            result = await batch_virtual_tryon.fn(
                garment_image_url="https://example.com/hoodie.png",
                model_types="female,male",
            )

        data = json.loads(result)
        assert len(data) == 2
        assert data[0]["model_type"] == "female"
        assert data[1]["model_type"] == "male"

    @pytest.mark.asyncio
    async def test_upload_to_wordpress(
        self, mock_wordpress_client: MagicMock
    ) -> None:
        """Test WordPress upload tool."""
        from agent.modules.clothing.mcp_server import (
            ClientManager,
            upload_to_wordpress,
        )

        with patch.object(
            ClientManager, "get_wordpress_client", return_value=mock_wordpress_client
        ):
            result = await upload_to_wordpress.fn(
                file_path="/tmp/model.glb",
                title="Test Model",
                alt_text="A test 3D model",
            )

        data = json.loads(result)
        assert data["success"] is True
        assert data["media_id"] == 12345
        assert "skyyrose.co" in data["source_url"]

    @pytest.mark.asyncio
    async def test_upload_from_url_to_wordpress(
        self, mock_wordpress_client: MagicMock
    ) -> None:
        """Test WordPress upload from URL tool."""
        from agent.modules.clothing.mcp_server import (
            ClientManager,
            upload_from_url_to_wordpress,
        )

        with patch.object(
            ClientManager, "get_wordpress_client", return_value=mock_wordpress_client
        ):
            result = await upload_from_url_to_wordpress.fn(
                url="https://api.tripo3d.ai/models/123.glb",
                title="Test Model",
            )

        data = json.loads(result)
        assert data["success"] is True
        assert data["media_id"] == 12346

    @pytest.mark.asyncio
    async def test_list_skyyrose_collections(self) -> None:
        """Test collections listing tool."""
        from agent.modules.clothing.mcp_server import list_skyyrose_collections

        result = await list_skyyrose_collections.fn()
        data = json.loads(result)

        assert "black_rose" in data
        assert "love_hurts" in data
        assert "signature" in data
        assert data["black_rose"]["name"] == "BLACK_ROSE"

    @pytest.mark.asyncio
    async def test_list_clothing_categories(self) -> None:
        """Test categories listing tool."""
        from agent.modules.clothing.mcp_server import list_clothing_categories

        result = await list_clothing_categories.fn()
        data = json.loads(result)

        assert "hoodie" in data
        assert "t_shirt" in data
        assert data["hoodie"]["fashn_category"] == "tops"
        assert data["pants"]["fashn_category"] == "bottoms"
        assert data["dress"]["fashn_category"] == "one-pieces"

    @pytest.mark.asyncio
    async def test_get_api_status(self) -> None:
        """Test API status check tool."""
        from agent.modules.clothing.mcp_server import get_api_status

        result = await get_api_status.fn()
        data = json.loads(result)

        assert "timestamp" in data
        assert "services" in data
        assert "tripo3d" in data["services"]
        assert "fashn" in data["services"]
        assert "wordpress" in data["services"]

    @pytest.mark.asyncio
    async def test_process_clothing_item(
        self,
        mock_tripo_client: MagicMock,
        mock_fashn_client: MagicMock,
        mock_wordpress_client: MagicMock,
    ) -> None:
        """Test full pipeline processing tool."""
        from agent.modules.clothing.mcp_server import (
            ClientManager,
            process_clothing_item,
        )
        from agent.modules.clothing.pipeline import ClothingAssetPipeline

        # Create mock pipeline
        mock_pipeline = MagicMock(spec=ClothingAssetPipeline)
        mock_pipeline.initialize = AsyncMock(return_value=True)
        mock_pipeline.process_item = AsyncMock(
            return_value=PipelineResult(
                item_id="hoodie-001",
                item_name="Black Rose Hoodie",
                stage=PipelineStage.COMPLETED,
                success=True,
                model_3d=Model3DResult(
                    task_id="task_123",
                    status="success",
                    model_url="https://api.tripo3d.ai/models/123.glb",
                    model_format=Model3DFormat.GLB,
                ),
                try_on_results=[
                    TryOnResult(
                        task_id="tryon_f",
                        status="completed",
                        image_url="https://api.fashn.ai/results/f.png",
                        model_type=TryOnModel.FEMALE,
                    ),
                ],
                wordpress_uploads=[
                    WordPressUploadResult(
                        media_id=12345,
                        source_url="https://skyyrose.co/uploads/model.glb",
                        mime_type="model/gltf-binary",
                        title="Black Rose Hoodie 3D Model",
                    ),
                ],
                total_processing_time_seconds=120.0,
            )
        )

        with patch.object(
            ClientManager, "get_pipeline", return_value=mock_pipeline
        ):
            result = await process_clothing_item.fn(
                item_id="hoodie-001",
                name="Black Rose Hoodie",
                description="Luxury hoodie with rose pattern",
                collection="black_rose",
                category="hoodie",
                color="black",
            )

        data = json.loads(result)
        assert data["success"] is True
        assert data["item_id"] == "hoodie-001"
        assert data["stage"] == "completed"
        assert data["model_3d"] is not None
        assert len(data["try_on_results"]) == 1
        assert len(data["wordpress_uploads"]) == 1


class TestClientManager:
    """Tests for ClientManager lazy initialization."""

    @pytest.mark.asyncio
    async def test_client_singleton_pattern(self) -> None:
        """Test that clients are created only once."""
        from agent.modules.clothing.mcp_server import ClientManager

        # Reset clients
        ClientManager._tripo_client = None
        ClientManager._fashn_client = None
        ClientManager._wordpress_client = None
        ClientManager._pipeline = None

        with patch(
            "agent.modules.clothing.mcp_server.Tripo3DClient"
        ) as mock_tripo:
            mock_instance = MagicMock()
            mock_instance.initialize = AsyncMock(return_value=True)
            mock_tripo.return_value = mock_instance

            # First call creates client
            await ClientManager.get_tripo_client()
            assert mock_tripo.call_count == 1

            # Second call reuses existing
            await ClientManager.get_tripo_client()
            assert mock_tripo.call_count == 1


class TestResponseModels:
    """Tests for response Pydantic models."""

    def test_model_3d_response(self) -> None:
        """Test Model3DResponse model."""
        from agent.modules.clothing.mcp_server import Model3DResponse

        response = Model3DResponse(
            success=True,
            task_id="task_123",
            status="success",
            model_url="https://example.com/model.glb",
        )

        assert response.success is True
        assert response.task_id == "task_123"
        assert response.error is None

    def test_tryon_response(self) -> None:
        """Test TryOnResponse model."""
        from agent.modules.clothing.mcp_server import TryOnResponse

        response = TryOnResponse(
            success=True,
            task_id="tryon_123",
            status="completed",
            model_type="female",
            image_url="https://example.com/tryon.png",
        )

        assert response.success is True
        assert response.model_type == "female"

    def test_upload_response(self) -> None:
        """Test UploadResponse model."""
        from agent.modules.clothing.mcp_server import UploadResponse

        response = UploadResponse(
            success=True,
            media_id=12345,
            source_url="https://example.com/media.glb",
            mime_type="model/gltf-binary",
        )

        assert response.success is True
        assert response.media_id == 12345

    def test_pipeline_response(self) -> None:
        """Test PipelineResponse model."""
        from agent.modules.clothing.mcp_server import PipelineResponse

        response = PipelineResponse(
            success=True,
            item_id="hoodie-001",
            item_name="Test Hoodie",
            stage="completed",
            total_processing_time_seconds=120.0,
        )

        assert response.success is True
        assert response.item_id == "hoodie-001"
        assert len(response.errors) == 0
